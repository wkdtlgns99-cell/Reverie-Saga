from __future__ import annotations

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
from contracts.persistence import SaveError, SaveExportReceipt
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


class SqliteSlots:
    def __init__(self, store: SqliteCommitStore, root: Path, *, io: StateIO) -> None:
        # Validate ancestors using a nonexistent file; a directory itself is not a save file.
        self.root = safe_path(root / ".slot-path-check").parent
        self.root.mkdir(parents=True, exist_ok=True)
        self._store, self._io = store, io
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
        try:
            pinned = self._store.load()
            if current.exists():
                validate_save(current, io=self._io)
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
                _backup_file_reserved(current, retained, io=self._io)
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
                absent = not replaced and bool(temporaries) and temporaries[0].exists()
                if absent and old_sha is not None:
                    absent = current.exists() and file_sha256(current) == old_sha
                elif absent:
                    absent = not current.exists()
                if not absent:
                    if current.exists():
                        try:
                            validate_save(current, io=self._io)
                        except SaveError:
                            self._logger.error("slot validation failed after possible replacement", exc_info=True)
                    raise SaveError("SAVE_EXPORT_UNCERTAIN", "replacement or directory durability unresolved") from error
            if isinstance(error, SaveError):
                raise
            raise SaveError("SAVE_EXPORT_FAILED", str(error)) from error
        finally:
            self._cleanup(tuple(temporaries))
            self._busy = False

    def stage_load(self, slot_id: str) -> SqliteCommitStore:
        current, _ = self._paths(slot_id)
        if self._busy:
            raise SaveError("SAVE_BUSY", "slot operation active")
        self._busy = True
        path: Path | None = None
        try:
            self._store.load()
            validate_save(current, io=self._io)
            root = self._store.path.parent
            # Count working clones, not their SQLite lock sidecars or unrelated entries.
            if sum(
                1 for child in root.glob(".loaded-*.sqlite")
                if re.fullmatch(r"\.loaded-[0-9a-f]{32}\.sqlite", child.name)
                and child.is_file() and not child.is_symlink()
            ) >= 8:
                raise SaveError("SAVE_LIMIT", "managed working clone count")
            path = self._reserve(root, ".loaded-")
            _backup_file_reserved(current, path, io=self._io)
            store = SqliteCommitStore.open(path, io=self._io)
            self._owned.remove(path)
            return store
        except (sqlite3.Error, OSError, ValueError, TypeError, RuntimeError) as error:
            if path is not None:
                self._owned.add(Path(str(path) + ".lock.sqlite"))
                self._cleanup((path, Path(str(path) + ".lock.sqlite")))
            if isinstance(error, SaveError):
                raise
            raise SaveError("SAVE_LOAD_FAILED", str(error)) from error
        finally:
            self._busy = False
