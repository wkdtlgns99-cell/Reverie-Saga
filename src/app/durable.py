from __future__ import annotations

import argparse
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import logging
from pathlib import Path
import secrets
import sys

from adapters.save_slots import SqliteSlots, cleanup_owned_clone
from adapters.sqlite_store import SqliteCommitStore
from app.feature_registry import rng_purposes
from app.headless import _Session, _restore, state_io
from app.watch import WatchBootstrapSpec, bootstrap_watch
from app.watch_registry import watch_bundle
from contracts.persistence import (
    DurableCheckpoint, SaveError, SaveExportReceipt, SaveLoadReceipt, SaveSegment, WorldUnavailable,
)
from contracts.skeleton import FeatureBundle
from contracts.state_io import StateIO
from contracts.turn import GameCommand, ProtocolSnapshot, TurnPublication
from domain.canonical import (
    JsonObject, canonical_json, decode_json, exact_fields, hash_document, object_value, seal, text_value,
)
from domain.state_types import CoreSnapshot
from orchestration.rng import CounterRngService


@dataclass(frozen=True, slots=True)
class _Attachment:
    owner: _Session
    store: SqliteCommitStore
    slots: SqliteSlots
    token: str


def _owner(store: SqliteCommitStore, bundles: tuple[FeatureBundle, ...], io: StateIO) -> _Session:
    checkpoint = store.load()
    core = checkpoint.core
    return _restore(core, checkpoint.protocol, bundles,
                    CounterRngService(core.world_seed_hex, core.world_id, rng_purposes()),
                    io=io, commit_port=store)


class DurableSession:
    def __init__(self, store: SqliteCommitStore, bundles: tuple[FeatureBundle, ...], io: StateIO) -> None:
        self._bundles, self._io = bundles, io
        self._attachment = _Attachment(_owner(store, bundles, io), store,
                                       SqliteSlots(store, store.path.parent / "slots", io=io),
                                       secrets.token_hex(16))
        self._busy = False
        self._closed = False
        self._owned_clones: set[Path] = set()
        self._logger = logging.getLogger(__name__)

    def _guard(self, *, recovery: bool = False) -> None:
        if self._closed:
            raise WorldUnavailable("SESSION_CLOSED", "durable session closed")
        if not recovery:
            self._attachment.owner._driver._active()

    @contextmanager
    def _operation(self, *, recovery: bool = False) -> Iterator[None]:
        self._guard(recovery=recovery)
        if self._busy:
            raise SaveError("SAVE_BUSY", "attachment operation active")
        self._busy = True
        try:
            yield
        finally:
            self._busy = False

    @property
    def attachment_id(self) -> str:
        self._guard()
        return self._attachment.token

    @property
    def working_path(self) -> Path:
        self._guard()
        return self._attachment.store.path

    def snapshot(self) -> CoreSnapshot:
        self._guard()
        return self._attachment.owner.snapshot()

    def protocol(self) -> ProtocolSnapshot:
        self._guard()
        return self._attachment.owner.protocol()

    def last_publication(self) -> TurnPublication:
        self._guard()
        return self._attachment.owner.last_publication()

    def _token(self, token: str) -> None:
        if token != self._attachment.token:
            raise SaveError("STALE_ATTACHMENT", "request belongs to previous attachment")

    def submit(self, command: GameCommand, *, attachment_id: str) -> TurnPublication:
        with self._operation():
            self._token(attachment_id)
            self._attachment.owner._driver.submit(command)
            return self._attachment.owner.last_publication()

    def submit_json(self, body: bytes, *, attachment_id: str) -> TurnPublication:
        with self._operation():
            self._token(attachment_id)
            return self._attachment.owner.submit_json(body)

    def export(self, slot_id: str) -> SaveExportReceipt:
        with self._operation():
            return self._attachment.slots.export(slot_id)

    def load(self, slot_id: str) -> SaveLoadReceipt:
        with self._operation():
            previous = self._attachment
            store = previous.slots.stage_load(slot_id)
            try:
                prepared = _Attachment(_owner(store, self._bundles, self._io), store,
                                       SqliteSlots(store, previous.slots.root, io=self._io),
                                       secrets.token_hex(16))
                checkpoint = store.load()
                receipt = SaveLoadReceipt(slot_id, checkpoint.protocol.revision,
                                          self._io.hash_core(checkpoint.core),
                                          hash_document("protocol/v1", self._io.encode_protocol(checkpoint.protocol)),
                                          prepared.token)
            except (ValueError, TypeError, RuntimeError, OSError) as error:
                store.close()
                cleanup_owned_clone(store.path, previous.store.path.parent)
                raise SaveError("SAVE_LOAD_FAILED", "prepared attachment failed") from error
            self._attachment = prepared  # Single app owner/token/driver/store swap.
            self._owned_clones.add(store.path)
            previous.owner._driver.detach()
            previous.store.close()
            if previous.store.path in self._owned_clones:
                try:
                    cleanup_owned_clone(previous.store.path, previous.store.path.parent)
                    self._owned_clones.remove(previous.store.path)
                except (OSError, SaveError):
                    self._logger.warning("superseded owned working clone cleanup failed", exc_info=True)
            return receipt

    def recover(self) -> TurnPublication:
        with self._operation(recovery=True):
            return self._attachment.owner._driver.recover_pending()

    def retained_segment(self) -> SaveSegment:
        with self._operation():
            return self._attachment.store.retained_segment()

    def close(self) -> None:
        if not self._closed:
            if self._busy:
                raise SaveError("SAVE_BUSY", "active attachment operation")
            self._attachment.owner._driver.detach()
            self._attachment.store.close()
            self._closed = True

    def __enter__(self) -> DurableSession:
        self._guard()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()


def create_durable(path: Path, checkpoint: DurableCheckpoint, *, bundles: tuple[FeatureBundle, ...]) -> DurableSession:
    io = state_io(bundles)
    store = SqliteCommitStore.create(path, checkpoint, io=io)
    try:
        return DurableSession(store, bundles, io)
    except (ValueError, TypeError, RuntimeError, OSError):
        store.close()
        raise


def resume_durable(path: Path, *, bundles: tuple[FeatureBundle, ...]) -> DurableSession:
    io = state_io(bundles)
    store = SqliteCommitStore.open(path, io=io)
    try:
        return DurableSession(store, bundles, io)
    except (ValueError, TypeError, RuntimeError, OSError):
        store.close()
        raise


def _emit(document: JsonObject) -> None:
    sys.stdout.buffer.write(canonical_json(document) + b"\n")
    sys.stdout.buffer.flush()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--working", type=Path, required=True)
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args(argv)
    try:
        bundles = (watch_bundle(),)
        if args.create:
            initial = bootstrap_watch(WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32))
            session = create_durable(args.working, DurableCheckpoint(initial.snapshot(), initial.protocol()), bundles=bundles)
        else:
            session = resume_durable(args.working, bundles=bundles)
    except (SaveError, ValueError, OSError) as error:
        _emit({"kind": "save_error", "code": error.code if isinstance(error, SaveError) else "SAVE_UNAVAILABLE"})
        return 1
    io = session._io
    with session:
        _emit({"kind": "attached", "attachment_id": session.attachment_id,
               "working_path": str(session.working_path), "revision": session.protocol().revision,
               "core_hash": io.hash_core(session.snapshot()),
               "protocol_hash": hash_document("protocol/v1", io.encode_protocol(session.protocol()))})
        while line := sys.stdin.buffer.readline(32770):
            if not line.strip():
                continue
            if not line.endswith(b"\n") and len(line) >= 32770:
                while tail := sys.stdin.buffer.readline(32770):
                    if tail.endswith(b"\n"):
                        break
                _emit({"kind": "save_error", "code": "INVALID_REQUEST"})
                continue
            try:
                body = line.rstrip(b"\r\n")
                if not 1 <= len(body) <= 32768:
                    raise ValueError("request size")
                document = object_value(decode_json(body))
                kind = text_value(document["kind"])
                if kind == "command":
                    d = exact_fields(document, ("kind", "attachment_id", "command"))
                    publication = session.submit_json(canonical_json(d["command"]), attachment_id=text_value(d["attachment_id"]))
                    _emit(io.encode_publication(publication))
                elif kind == "export":
                    d = exact_fields(document, ("kind", "slot_id"))
                    receipt = session.export(text_value(d["slot_id"]))
                    _emit({"kind": "exported", "receipt": seal(asdict(receipt))})
                elif kind == "load":
                    d = exact_fields(document, ("kind", "slot_id"))
                    loaded = session.load(text_value(d["slot_id"]))
                    _emit({"kind": "loaded", "working_path": str(session.working_path), "receipt": seal(asdict(loaded))})
                elif kind == "recover":
                    exact_fields(document, ("kind",))
                    _emit(io.encode_publication(session.recover()))
                else:
                    raise ValueError("request kind")
            except SaveError as error:
                _emit({"kind": "save_error", "code": error.code})
            except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
                _emit({"kind": "save_error", "code": "INVALID_REQUEST"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
