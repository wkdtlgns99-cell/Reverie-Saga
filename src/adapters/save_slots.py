from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import secrets
import hashlib
import sqlite3

from adapters.sqlite_store import (
    SqliteCommitStore, _backup_file_reserved, safe_path, validate_save,
)
from contracts.persistence import DurableCheckpoint, SaveError, SaveExportReceipt
from contracts.state_io import StateIO
from domain.canonical import hash_document


def file_sha256(path: Path) -> str:
    descriptor = os.open(safe_path(path), os.O_RDONLY)
    try:
        result = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            result.update(chunk)
        return result.hexdigest()
    finally:
        os.close(descriptor)


def sync_file(path: Path) -> None:
    descriptor = os.open(safe_path(path), os.O_RDWR)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def sync_directory(path: Path) -> bool:
    if os.name == "nt":
        return False
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
        return True
    finally:
        os.close(descriptor)


def cleanup_owned_clone(path: Path, root: Path) -> None:
    """Caller must possess the live-session exclusive-creation ownership record."""
    absolute = safe_path(path)
    approved = root.resolve()
    if absolute.parent != approved:
        raise SaveError("INVALID_PATH", "clone cleanup outside approved directory")
    for child in (absolute, Path(str(absolute) + ".lock.sqlite")):
        target = safe_path(child)
        if target.parent != approved:
            raise SaveError("INVALID_PATH", "clone sidecar cleanup outside approved directory")
        target.unlink(missing_ok=True)


@dataclass(frozen=True, slots=True)
class LegacySlotProfile:
    io: StateIO
    upgrade: Callable[[DurableCheckpoint], DurableCheckpoint]
    older: "LegacySlotProfile | None" = None


class SqliteSlots:
    def __init__(
        self, store: SqliteCommitStore, root: Path, *, io: StateIO,
        legacy: LegacySlotProfile | None = None,
    ) -> None:
        # Validate ancestors using a nonexistent file; a directory itself is not a save file.
        self.root = safe_path(root / ".slot-path-check").parent
        self.root.mkdir(parents=True, exist_ok=True)
        self._store, self._io = store, io
        self._legacy = legacy
        self._busy = False
        self._owned: set[Path] = set()
        self._logger = logging.getLogger(__name__)

    def _paths(self, slot_id: str) -> tuple[Path, Path]:
        if type(slot_id) is not str or re.fullmatch("slot0[1-8]", slot_id) is None:
            raise SaveError("INVALID_SLOT", "slot ID")
        current = safe_path(self.root / (slot_id + ".sqlite"))
        previous = safe_path(self.root / (slot_id + ".previous.sqlite"))
        if current == self._store.path or previous == self._store.path:
            raise SaveError("INVALID_PATH", "slot aliases working file")
        return current, previous

    def _reserve(self, root: Path, prefix: str) -> Path:
        for _ in range(16):
            path = safe_path(root / (prefix + secrets.token_hex(16) + ".sqlite"))
            if Path(str(path) + ".lock.sqlite").exists():
                continue
            try:
                descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                continue
            os.close(descriptor)
            self._owned.add(path)
            return path
        raise SaveError("SAVE_EXPORT_FAILED", "temporary file collision")

    def _cleanup(self, paths: tuple[Path, ...]) -> None:
        for path in paths:
            if path not in self._owned:
                continue
            try:
                target = safe_path(path)
                if target.parent not in (self.root, self._store.path.parent):
                    raise SaveError("INVALID_PATH", "temporary cleanup boundary")
                target.unlink(missing_ok=True)
                self._owned.remove(path)
            except (OSError, SaveError):
                self._logger.warning("owned save temporary cleanup failed", exc_info=True)

    def export(self, slot_id: str) -> SaveExportReceipt:
        current, previous = self._paths(slot_id)
        if self._busy:
            raise SaveError("SAVE_BUSY", "slot operation active")
        self._busy = True
        temporaries: list[Path] = []
        replaced = False
        attempted = False
        old_sha: str | None = None
        old_io = self._io
        try:
            pinned = self._store.load()
            if current.exists():
                _, old_io = self._read_profile(current)
                old_sha = file_sha256(current)
            temp = self._reserve(self.root, ".export-")
            temporaries.append(temp)
            self._store._backup_reserved(temp)
            if validate_save(temp, io=self._io) != pinned:
                raise SaveError("SAVE_CORRUPT", "export did not preserve pinned head")
            sync_file(temp)
            if current.exists():
                retained = self._reserve(self.root, ".previous-")
                temporaries.append(retained)
                _backup_file_reserved(current, retained, io=old_io)
                sync_file(retained)
                os.replace(retained, previous)
            attempted = True
            os.replace(temp, current)
            replaced = True
            directory_synced = sync_directory(self.root)
            if validate_save(current, io=self._io) != pinned:
                raise SaveError("SAVE_CORRUPT", "replaced slot validation")
            return SaveExportReceipt(slot_id, pinned.protocol.revision, self._io.hash_core(pinned.core),
                                     hash_document("protocol/v1", self._io.encode_protocol(pinned.protocol)),
                                     file_sha256(current), directory_synced)
        except (sqlite3.Error, OSError, ValueError, TypeError, RuntimeError) as error:
            if attempted:
                # A failed syscall with an unchanged old file AND still-present temp proves absence.
                try:
                    absent = not replaced and bool(temporaries) and temporaries[0].exists()
                    if absent and old_sha is not None:
                        absent = current.exists() and file_sha256(current) == old_sha
                    elif absent:
                        absent = not current.exists()
                except (OSError, SaveError):
                    self._logger.warning("slot replacement proof unavailable", exc_info=True)
                    absent = False
                if not absent:
                    try:
                        if current.exists():
                            validate_save(current, io=self._io)
                    except (OSError, SaveError):
                        self._logger.error("slot validation failed after possible replacement", exc_info=True)
                    raise SaveError("SAVE_EXPORT_UNCERTAIN", "replacement or directory durability unresolved") from error
            if isinstance(error, SaveError):
                raise
            raise SaveError("SAVE_EXPORT_FAILED", str(error)) from error
        finally:
            self._cleanup(tuple(temporaries))
            self._busy = False

    def _source(self, slot_id: str, previous: bool) -> Path:
        if type(previous) is not bool:
            raise SaveError("INVALID_SLOT_VERSION", "slot version must be exact bool")
        current, backup = self._paths(slot_id)
        return backup if previous else current

    def _read_profile(self, path: Path) -> tuple[DurableCheckpoint, StateIO]:
        try:
            return validate_save(path, io=self._io), self._io
        except SaveError as error:
            if error.code != "UNSUPPORTED_RULESET" or self._legacy is None:
                raise
        profile = self._legacy
        while profile.older is not None:
            try:
                return validate_save(path, io=profile.io), profile.io
            except SaveError as error:
                if error.code != "UNSUPPORTED_RULESET":
                    raise
            profile = profile.older
        return validate_save(path, io=profile.io), profile.io

    def _validate_source(self, path: Path, previous: bool) -> tuple[DurableCheckpoint, StateIO]:
        try:
            return self._read_profile(path)
        except SaveError as error:
            if previous and error.code == "SAVE_NOT_FOUND":
                raise SaveError(
                    "PREVIOUS_SAVE_NOT_FOUND", "selected slot has no previous save"
                ) from error
            raise

    def inspect(self, slot_id: str, *, previous: bool = False) -> DurableCheckpoint:
        current = self._source(slot_id, previous)
        if self._busy:
            raise SaveError("SAVE_BUSY", "slot operation active")
        self._busy = True
        try:
            self._store.load()
            return self._validate_source(current, previous)[0]
        except (sqlite3.Error, OSError) as error:
            raise SaveError("SAVE_INSPECT_FAILED", str(error)) from error
        finally:
            self._busy = False

    def _reserve_clone(self) -> Path:
        root = self._store.path.parent
        if sum(
            1 for child in root.glob(".loaded-*.sqlite")
            if re.fullmatch(r"\.loaded-[0-9a-f]{32}\.sqlite", child.name)
            and child.is_file() and not child.is_symlink()
        ) >= 8:
            raise SaveError("SAVE_LIMIT", "managed working clone count")
        return self._reserve(root, ".loaded-")

    def stage_checkpoint(self, checkpoint: DurableCheckpoint) -> SqliteCommitStore:
        path = self._reserve_clone()
        try:
            store = SqliteCommitStore._create(path, checkpoint, io=self._io, reserved=True)
        except (sqlite3.Error, OSError, ValueError, TypeError, RuntimeError):
            self._cleanup_clone(path)
            raise
        self._owned.remove(path)
        return store

    def _cleanup_clone(self, path: Path) -> None:
        sidecar = Path(str(path) + ".lock.sqlite")
        self._owned.add(sidecar)
        self._cleanup((path, sidecar))

    def stage_load(self, slot_id: str, *, previous: bool = False) -> SqliteCommitStore:
        current = self._source(slot_id, previous)
        if self._busy:
            raise SaveError("SAVE_BUSY", "slot operation active")
        self._busy = True
        path: Path | None = None
        try:
            self._store.load()
            checkpoint, source_io = self._validate_source(current, previous)
            profile = self._legacy
            while profile is not None:
                if source_io is profile.io:
                    return self.stage_checkpoint(profile.upgrade(checkpoint))
                profile = profile.older
            path = self._reserve_clone()
            _backup_file_reserved(current, path, io=self._io)
            store = SqliteCommitStore.open(path, io=self._io)
            self._owned.remove(path)
            return store
        except (sqlite3.Error, OSError, ValueError, TypeError, RuntimeError) as error:
            if path is not None:
                self._cleanup_clone(path)
            if isinstance(error, SaveError):
                raise
            raise SaveError("SAVE_LOAD_FAILED", str(error)) from error
        finally:
            self._busy = False
