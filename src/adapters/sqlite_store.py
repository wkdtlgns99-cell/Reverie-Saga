from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import stat
from typing import cast

from contracts.persistence import (
    CommitUncertain, DurableCheckpoint, DurableTurn, RecoveryAbsent, RecoveryCommitted,
    RecoveryResult, SaveError, SaveSegment, SaveUnavailable, WorldUnavailable,
)
from contracts.state_io import StateIO
from contracts.turn import CommitReceipt
from domain.canonical import canonical_json, hash_document, object_value
from orchestration.persistence import (
    RowProjection, SaveRowPlan, canonical_object, checkpoint_document, decode_checkpoint,
    decode_segment, prepare_turn, project_rows,
)


APPLICATION_ID = 0x52535632
MAX_FILE = 1024 * 1024 * 1024
MAX_ROW = 64 * 1024 * 1024
MAX_CHECKPOINT = 128 * 1024 * 1024
MAX_BODIES = 256 * 1024 * 1024
type SqlValue = None | int | float | str | bytes
type SqlRow = tuple[SqlValue, ...]
DDL = (
    "CREATE TABLE save_head(singleton INTEGER PRIMARY KEY CHECK(singleton=1),format_version INTEGER NOT NULL CHECK(format_version=1),core_meta BLOB NOT NULL,protocol_meta BLOB NOT NULL,core_hash TEXT NOT NULL CHECK(length(core_hash)=64),protocol_hash TEXT NOT NULL CHECK(length(protocol_hash)=64),checkpoint_revision INTEGER NOT NULL CHECK(checkpoint_revision>=0)) STRICT",
    "CREATE TABLE components(kind TEXT NOT NULL,version INTEGER NOT NULL CHECK(version>=1),entity_id TEXT NOT NULL,body BLOB NOT NULL,sha256 TEXT NOT NULL CHECK(length(sha256)=64),PRIMARY KEY(kind,version,entity_id)) STRICT",
    "CREATE TABLE pending(event_id TEXT PRIMARY KEY,ordinal INTEGER NOT NULL UNIQUE CHECK(ordinal>=0),body BLOB NOT NULL,sha256 TEXT NOT NULL CHECK(length(sha256)=64)) STRICT",
    "CREATE TABLE streams(stream_id TEXT PRIMARY KEY,body BLOB NOT NULL) STRICT",
    "CREATE TABLE receipts(command_id TEXT PRIMARY KEY,revision INTEGER NOT NULL UNIQUE CHECK(revision>=1),body BLOB NOT NULL) STRICT",
    "CREATE TABLE checkpoint(singleton INTEGER PRIMARY KEY CHECK(singleton=1),body BLOB NOT NULL,sha256 TEXT NOT NULL CHECK(length(sha256)=64)) STRICT",
    "CREATE TABLE replay(revision INTEGER PRIMARY KEY CHECK(revision>=1),body BLOB NOT NULL,sha256 TEXT NOT NULL CHECK(length(sha256)=64)) STRICT",
)
TABLE_CAPS = (("save_head", 1), ("components", 32768), ("pending", 4096),
              ("streams", 16), ("receipts", 1024), ("checkpoint", 1), ("replay", 4096))


def safe_path(path: Path) -> Path:
    try:
        absolute = path.absolute()
        for child in (absolute, *absolute.parents):
            if child.is_symlink() or (child.exists() and getattr(child.stat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                raise SaveError("INVALID_PATH", "indirect save path")
        resolved = absolute.resolve()
        if resolved.exists() and not resolved.is_file():
            raise SaveError("INVALID_PATH", "not a regular save file")
        if resolved.exists() and resolved.stat().st_nlink > 1:
            raise SaveError("INVALID_PATH", "hardlinked save breaks attachment identity")
        return resolved
    except OSError as error:
        raise SaveError("INVALID_PATH", str(error)) from error


def _integer(value: SqlValue) -> int:
    if type(value) is not int or value < 0:
        raise SaveError("SAVE_CORRUPT", "SQL integer")
    return value


def _text(value: SqlValue) -> str:
    if not isinstance(value, str):
        raise SaveError("SAVE_CORRUPT", "SQL text")
    return value


def _blob(value: SqlValue, cap: int = MAX_ROW) -> bytes:
    if not isinstance(value, bytes):
        raise SaveError("SAVE_CORRUPT", "SQL BLOB")
    if len(value) > cap:
        raise SaveError("SAVE_LIMIT", "row byte cap")
    return value


def _rows(con: sqlite3.Connection, query: str) -> tuple[SqlRow, ...]:
    return tuple(cast(list[SqlRow], con.execute(query).fetchall()))


def _one(con: sqlite3.Connection, query: str) -> SqlRow:
    values = _rows(con, query)
    if len(values) != 1:
        raise SaveError("SAVE_CORRUPT", "singleton query")
    return values[0]


def classify_file(path: Path) -> None:
    if not path.exists():
        raise SaveError("SAVE_NOT_FOUND", "save missing")
    if path.stat().st_size > MAX_FILE:
        raise SaveError("SAVE_LIMIT", "file byte cap")
    descriptor = os.open(path, os.O_RDONLY)
    try:
        header = os.read(descriptor, 100)
    finally:
        os.close(descriptor)
    if len(header) != 100 or header[:16] != b"SQLite format 3\0":
        raise SaveError("SAVE_CORRUPT", "SQLite file header")
    if int.from_bytes(header[68:72], "big") != APPLICATION_ID:
        raise SaveError("UNSUPPORTED_LEGACY_SAVE", "foreign save application")
    version = int.from_bytes(header[60:64], "big")
    if version > 1:
        raise SaveError("NEWER_SAVE_VERSION", "future save version")
    if version != 1:
        raise SaveError("UNSUPPORTED_SAVE_VERSION", "unsupported save version")
    if int.from_bytes(header[16:18], "big") != 4096:
        raise SaveError("SAVE_CORRUPT", "save page profile")


def _connect(path: Path, *, readonly: bool = False) -> sqlite3.Connection:
    if sqlite3.sqlite_version_info < (3, 37, 0):
        raise SaveError("SAVE_UNAVAILABLE", "SQLite STRICT unavailable")
    con = sqlite3.connect(path.as_uri() + "?mode=ro" if readonly else path,
                          uri=readonly, autocommit=True, timeout=0, detect_types=0,
                          check_same_thread=True)
    try:
        con.execute("PRAGMA trusted_schema=OFF")
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=0")
    except sqlite3.Error:
        con.close()
        raise
    return con


def _configure(con: sqlite3.Connection) -> None:
    if _one(con, "PRAGMA journal_mode=DELETE")[0] != "delete":
        raise SaveError("SAVE_UNAVAILABLE", "journal mode unavailable")
    con.execute("PRAGMA synchronous=FULL")
    con.execute("PRAGMA max_page_count=262144")
    if (_one(con, "PRAGMA synchronous")[0], _one(con, "PRAGMA foreign_keys")[0],
        _one(con, "PRAGMA trusted_schema")[0], _one(con, "PRAGMA page_size")[0]) != (2, 1, 0, 4096):
        raise SaveError("SAVE_UNAVAILABLE", "SQLite profile")


def _schema(con: sqlite3.Connection) -> None:
    tables = _rows(con, "SELECT type,name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' ORDER BY name")
    expected = sorted(("table", sql.split("(", 1)[0].split()[-1], sql) for sql in DDL)
    actual = [(row[0], row[1], " ".join(_text(row[2]).split()).lower()) for row in tables]
    normalized = [(kind, name, " ".join(sql.split()).lower()) for kind, name, sql in expected]
    if actual != normalized:
        raise SaveError("SAVE_CORRUPT", "save schema differs")
    if _one(con, "PRAGMA application_id")[0] != APPLICATION_ID or _one(con, "PRAGMA user_version")[0] != 1:
        raise SaveError("SAVE_CORRUPT", "save format metadata")
    if _one(con, "PRAGMA journal_mode")[0] != "delete" or _one(con, "PRAGMA page_size")[0] != 4096:
        raise SaveError("SAVE_CORRUPT", "journal/page profile")


def _limits(con: sqlite3.Connection) -> None:
    if _integer(_one(con, "PRAGMA page_count")[0]) * 4096 > MAX_FILE:
        raise SaveError("SAVE_LIMIT", "database page cap")
    total = 0
    for table, cap in TABLE_CAPS:
        if _integer(_one(con, f"SELECT count(*) FROM {table}")[0]) > cap:
            raise SaveError("SAVE_LIMIT", "save row count")
        columns = ("core_meta", "protocol_meta") if table == "save_head" else ("body",)
        for column in columns:
            amount, maximum = _one(con, f"SELECT coalesce(sum(length({column})),0),coalesce(max(length({column})),0) FROM {table}")
            total += _integer(amount)
            if _integer(maximum) > (MAX_CHECKPOINT if table == "checkpoint" else MAX_ROW):
                raise SaveError("SAVE_LIMIT", "row bytes")
    if total > MAX_BODIES:
        raise SaveError("SAVE_LIMIT", "aggregate body bytes")


def _read(con: sqlite3.Connection, io: StateIO) -> tuple[DurableCheckpoint, SaveSegment]:
    _schema(con)
    _limits(con)
    if _rows(con, "PRAGMA integrity_check") != (("ok",),) or _rows(con, "PRAGMA foreign_key_check"):
        raise SaveError("SAVE_CORRUPT", "SQLite integrity")
    head = _one(con, "SELECT singleton,format_version,core_meta,protocol_meta,core_hash,protocol_hash,checkpoint_revision FROM save_head")
    if head[:2] != (1, 1):
        raise SaveError("SAVE_CORRUPT", "head singleton/version")
    cp = _one(con, "SELECT singleton,body,sha256 FROM checkpoint")
    document = canonical_object(_blob(cp[1], MAX_CHECKPOINT))
    if cp[0] != 1 or hash_document("save-checkpoint/v1", document) != cp[2]:
        raise SaveError("SAVE_CORRUPT", "checkpoint checksum")
    initial = decode_checkpoint(document, io=io)
    if initial.protocol.revision != _integer(head[6]):
        raise SaveError("SAVE_CORRUPT", "checkpoint revision")
    components = []
    for row in _rows(con, "SELECT kind,version,entity_id,body,sha256 FROM components ORDER BY kind,version,entity_id"):
        child = canonical_object(_blob(row[3]))
        schema = object_value(child["schema"])
        if (schema["kind"], schema["version"], child["entity_id"]) != row[:3] or hash_document("component/v1", child) != row[4]:
            raise SaveError("SAVE_CORRUPT", "component key/checksum")
        components.append(child)
    pending = []
    for index, row in enumerate(_rows(con, "SELECT event_id,ordinal,body,sha256 FROM pending ORDER BY ordinal")):
        child = canonical_object(_blob(row[2]))
        header = object_value(object_value(child["event"])["header"])
        if header["event_id"] != row[0] or row[1] != index or hash_document("pending-event/v1", child) != row[3]:
            raise SaveError("SAVE_CORRUPT", "pending key/order/checksum")
        pending.append(child)
    streams = []
    for row in _rows(con, "SELECT stream_id,body FROM streams ORDER BY stream_id"):
        child = canonical_object(_blob(row[1]))
        if child["stream_id"] != row[0]:
            raise SaveError("SAVE_CORRUPT", "stream key")
        streams.append(child)
    receipts = []
    for row in _rows(con, "SELECT command_id,revision,body FROM receipts ORDER BY revision,command_id"):
        child = canonical_object(_blob(row[2]))
        if object_value(child["command"])["command_id"] != row[0] or object_value(child["receipt"])["revision"] != row[1]:
            raise SaveError("SAVE_CORRUPT", "receipt key/revision")
        receipts.append(child)
    core = {**canonical_object(_blob(head[2])), "components": tuple(components), "pending": tuple(pending)}
    protocol = {**canonical_object(_blob(head[3])), "streams": tuple(streams), "receipts": tuple(receipts)}
    # Meta documents may not shadow the row arrays with duplicate authorities.
    if set(canonical_object(_blob(head[2]))) != set(core) - {"components", "pending"} or set(canonical_object(_blob(head[3]))) != set(protocol) - {"streams", "receipts"}:
        raise SaveError("SAVE_CORRUPT", "metadata row arrays")
    header = {**object_value(document["header"]), "initial_core_hash": _text(head[4]), "initial_protocol_hash": _text(head[5])}
    current = decode_checkpoint({"core": core, "protocol": protocol, "header": header}, io=io)
    if current.protocol.branch_id != initial.protocol.branch_id:
        raise SaveError("SAVE_CORRUPT", "checkpoint branch differs")
    bodies = []
    for index, row in enumerate(_rows(con, "SELECT revision,body,sha256 FROM replay ORDER BY revision")):
        body = _blob(row[1])
        if row[0] != initial.protocol.revision + index + 1 or hash_document("save-step/v1", canonical_object(body)) != row[2]:
            raise SaveError("SAVE_CORRUPT", "retained replay key/checksum")
        bodies.append(body)
    segment = decode_segment(initial, tuple(bodies), io=io)
    if initial.protocol.revision + len(segment.trace.steps) != current.protocol.revision:
        raise SaveError("SAVE_CORRUPT", "replay/header revision chain")
    if segment.trace.steps:
        last = segment.trace.steps[-1]
        if (last.expected_core_hash, last.expected_protocol_hash) != (head[4], head[5]):
            raise SaveError("SAVE_CORRUPT", "last replay hashes/header")
        if not hasattr(last.expected_outcome, "receipt"):
            raise SaveError("SAVE_CORRUPT", "last replay outcome")
        from contracts.turn import TurnCommitted
        if not isinstance(last.expected_outcome, TurnCommitted) or last.expected_outcome.receipt.tick != current.core.tick:
            raise SaveError("SAVE_CORRUPT", "last replay tick/header")
    elif current != initial:
        raise SaveError("SAVE_CORRUPT", "empty segment/head differs")
    # Verify high-water and receipt retention using compact commands, without evaluating gameplay.
    from dataclasses import replace
    from contracts.turn import StoredReceipt, TurnCommitted
    expected = initial.protocol
    for step in segment.trace.steps:
        outcome = step.expected_outcome
        if not isinstance(outcome, TurnCommitted):
            raise SaveError("SAVE_CORRUPT", "retained outcome")
        parts = step.command.command_id.split(":")
        cursor = next((s for s in expected.streams if s.stream_id == parts[2]), None)
        sequence = int(parts[3])
        if cursor is None or cursor.actor_id != step.command.actor_id or cursor.status != "active" or sequence <= cursor.highest_committed_sequence:
            raise SaveError("SAVE_CORRUPT", "retained stream/sequence")
        command = io.encode_command(step.command)
        fingerprint = hash_document("command/v1", {k: v for k, v in command.items() if k != "command_id"})
        expected = replace(expected, revision=outcome.receipt.revision,
                           streams=tuple(replace(s, highest_committed_sequence=sequence) if s.stream_id == cursor.stream_id else s for s in expected.streams),
                           receipts=(*expected.receipts, StoredReceipt(step.command, fingerprint, outcome.receipt))[-1024:])
    if expected != current.protocol:
        raise SaveError("SAVE_CORRUPT", "retained protocol differs")
    return current, segment


def _read_file(path: Path, io: StateIO) -> tuple[DurableCheckpoint, SaveSegment]:
    try:
        target = safe_path(path)
        classify_file(target)
        con = _connect(target, readonly=True)
        try:
            con.execute("BEGIN")
            return _read(con, io)
        finally:
            con.close()
    except (sqlite3.Error, OSError, ValueError, TypeError, KeyError) as error:
        raise SaveError("SAVE_CORRUPT", str(error)) from error


def validate_save(path: Path, *, io: StateIO) -> DurableCheckpoint:
    return _read_file(path, io)[0]


def read_segment(path: Path, *, io: StateIO) -> SaveSegment:
    return _read_file(path, io)[1]


def _attachment(path: Path) -> sqlite3.Connection:
    sidecar = safe_path(Path(str(path) + ".lock.sqlite"))
    con = _connect(sidecar)
    try:
        con.execute("CREATE TABLE IF NOT EXISTS attachment(singleton INTEGER PRIMARY KEY CHECK(singleton=1)) STRICT")
        con.execute("BEGIN EXCLUSIVE")
        return con
    except sqlite3.Error as error:
        con.close()
        code = "SAVE_LOCKED" if getattr(error, "sqlite_errorcode", 0) in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) else "SAVE_UNAVAILABLE"
        raise SaveError(code, str(error)) from error


class SqliteCommitStore:
    def __init__(self, path: Path, io: StateIO, con: sqlite3.Connection,
                 lock: sqlite3.Connection) -> None:
        self.path = path
        self._io = io
        self._con = con
        self._lock = lock
        self._closed = False

    @classmethod
    def create(cls, path: Path, checkpoint: DurableCheckpoint, *, io: StateIO) -> SqliteCommitStore:
        projection = project_rows(checkpoint, io=io)
        body = canonical_json(checkpoint_document(checkpoint, io=io))
        target = safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise SaveError("SAVE_EXISTS", "working file exists") from error
        except OSError as error:
            raise SaveError("SAVE_UNAVAILABLE", str(error)) from error
        os.close(descriptor)
        lock: sqlite3.Connection | None = None
        con: sqlite3.Connection | None = None
        try:
            lock = _attachment(target)
            con = _connect(target)
            con.execute("PRAGMA page_size=4096")
            _configure(con)
            con.execute(f"PRAGMA application_id={APPLICATION_ID}")
            con.execute("PRAGMA user_version=1")
            con.execute("BEGIN IMMEDIATE")
            for statement in DDL:
                con.execute(statement)
            store = cls(target, io, con, lock)
            store._insert_initial(projection, checkpoint.protocol.revision, body)
            _limits(con)
            con.execute("COMMIT")
            store.load()
            return store
        except (sqlite3.Error, OSError, ValueError, TypeError, RuntimeError) as error:
            if con is not None:
                con.close()
            if lock is not None:
                lock.close()
            if isinstance(error, SaveError):
                raise
            raise SaveError("SAVE_UNAVAILABLE", str(error)) from error

    @classmethod
    def open(cls, path: Path, *, io: StateIO) -> SqliteCommitStore:
        target = safe_path(path)
        classify_file(target)
        lock = _attachment(target)
        con: sqlite3.Connection | None = None
        try:
            con = _connect(target)
            store = cls(target, io, con, lock)
            store.load()
            _configure(con)
            return store
        except (sqlite3.Error, OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
            if con is not None:
                con.close()
            lock.close()
            if isinstance(error, SaveError):
                raise
            raise SaveError("SAVE_CORRUPT", str(error)) from error

    def _guard(self) -> None:
        if self._closed:
            raise WorldUnavailable("SESSION_CLOSED", "closed durable store")

    def _execute(self, query: str, values: tuple[SqlValue, ...] = ()) -> sqlite3.Cursor:
        self._guard()
        return self._con.execute(query, values)

    def _insert_initial(self, rows: RowProjection, revision: int, checkpoint: bytes) -> None:
        self._execute("INSERT INTO save_head VALUES(1,1,?,?,?,?,?)", (rows.core_meta, rows.protocol_meta, rows.core_hash, rows.protocol_hash, revision))
        for row in rows.components:
            self._execute("INSERT INTO components VALUES(?,?,?,?,?)", (row.kind, row.version, row.entity_id, row.body, row.sha256))
        for pending in rows.pending:
            self._execute("INSERT INTO pending VALUES(?,?,?,?)", (pending.event_id, pending.ordinal, pending.body, pending.sha256))
        for stream in rows.streams:
            self._execute("INSERT INTO streams VALUES(?,?)", (stream.stream_id, stream.body))
        for receipt in rows.receipts:
            self._execute("INSERT INTO receipts VALUES(?,?,?)", (receipt.command_id, receipt.revision, receipt.body))
        self._execute("INSERT INTO checkpoint VALUES(1,?,?)", (checkpoint, hash_document("save-checkpoint/v1", canonical_object(checkpoint))))

    def _read_all(self) -> tuple[DurableCheckpoint, SaveSegment]:
        self._guard()
        try:
            self._con.execute("BEGIN")
            return _read(self._con, self._io)
        except (sqlite3.Error, OSError, ValueError, TypeError, KeyError) as error:
            raise SaveError("SAVE_CORRUPT", str(error)) from error
        finally:
            if self._con.in_transaction:
                self._con.execute("ROLLBACK")

    def load(self) -> DurableCheckpoint:
        return self._read_all()[0]

    def retained_segment(self) -> SaveSegment:
        return self._read_all()[1]

    def _write_plan(self, plan: SaveRowPlan) -> None:
        for key in plan.components_deletes:
            self._execute("DELETE FROM components WHERE kind=? AND version=? AND entity_id=?", key)
        for row in plan.components_upserts:
            self._execute("INSERT INTO components VALUES(?,?,?,?,?) ON CONFLICT(kind,version,entity_id) DO UPDATE SET body=excluded.body,sha256=excluded.sha256", (row.kind, row.version, row.entity_id, row.body, row.sha256))
        for identifier in plan.pending_deletes:
            self._execute("DELETE FROM pending WHERE event_id=?", (identifier,))
        previous = {row.event_id: row.ordinal for row in plan.previous.pending}
        for pending in plan.pending_upserts:
            old = previous.get(pending.event_id)
            if old is not None and old != pending.ordinal:
                self._execute("UPDATE pending SET ordinal=? WHERE event_id=?", (old + 4096, pending.event_id))
        for pending in plan.pending_upserts:
            self._execute("INSERT INTO pending VALUES(?,?,?,?) ON CONFLICT(event_id) DO UPDATE SET ordinal=excluded.ordinal,body=excluded.body,sha256=excluded.sha256", (pending.event_id, pending.ordinal, pending.body, pending.sha256))
        for stream in plan.streams_upserts:
            self._execute("INSERT INTO streams VALUES(?,?) ON CONFLICT(stream_id) DO UPDATE SET body=excluded.body", (stream.stream_id, stream.body))
        for identifier in plan.receipts_deletes:
            self._execute("DELETE FROM receipts WHERE command_id=?", (identifier,))
        for receipt in plan.receipts_upserts:
            self._execute("INSERT INTO receipts VALUES(?,?,?)", (receipt.command_id, receipt.revision, receipt.body))

    def persist(self, turn: DurableTurn) -> CommitReceipt:
        self._guard()
        plan = prepare_turn(turn, io=self._io)
        commit_started = False
        try:
            self._execute("BEGIN IMMEDIATE")
            head = _one(self._con, "SELECT core_meta,protocol_meta,core_hash,protocol_hash,checkpoint_revision FROM save_head")
            if (_blob(head[0]), _blob(head[1]), head[2], head[3]) != (plan.previous.core_meta, plan.previous.protocol_meta, plan.previous.core_hash, plan.previous.protocol_hash):
                self._con.execute("ROLLBACK")
                raise WorldUnavailable("SAVE_STALE", "durable base differs")
            checkpoint_revision = _integer(head[4])
            count = _integer(_one(self._con, "SELECT count(*) FROM replay")[0])
            if count == 4096:
                body = canonical_json(checkpoint_document(turn.previous, io=self._io))
                self._execute("UPDATE checkpoint SET body=?,sha256=? WHERE singleton=1", (body, hash_document("save-checkpoint/v1", canonical_object(body))))
                checkpoint_revision = turn.previous.protocol.revision
                self._execute("DELETE FROM replay")
            self._write_plan(plan)
            self._execute("INSERT INTO replay VALUES(?,?,?)", (plan.receipt.revision, plan.step_body, plan.step_sha256))
            self._execute("UPDATE save_head SET core_meta=?,protocol_meta=?,core_hash=?,protocol_hash=?,checkpoint_revision=? WHERE singleton=1", (plan.next.core_meta, plan.next.protocol_meta, plan.next.core_hash, plan.next.protocol_hash, checkpoint_revision))
            _limits(self._con)
            ordinals = _rows(self._con, "SELECT ordinal FROM pending ORDER BY ordinal")
            if ordinals != tuple((i,) for i in range(len(ordinals))):
                raise SaveError("SAVE_CORRUPT", "final pending ordinals")
            commit_started = True
            self._execute("COMMIT")
            return plan.receipt
        except WorldUnavailable:
            raise
        except (sqlite3.Error, OSError, ValueError, TypeError, RuntimeError) as error:
            if commit_started:
                raise CommitUncertain("SAVE_UNCERTAIN", str(error)) from error
            try:
                if self._con.in_transaction:
                    self._con.execute("ROLLBACK")
                if self.load() != turn.previous:
                    raise CommitUncertain("SAVE_UNCERTAIN", "rollback head differs")
            except (sqlite3.Error, OSError, ValueError, TypeError, RuntimeError) as recovery_error:
                raise CommitUncertain("SAVE_UNCERTAIN", str(recovery_error)) from error
            raise SaveUnavailable("SAVE_UNAVAILABLE", str(error)) from error

    def recover(self, turn: DurableTurn) -> RecoveryResult:
        self._guard()
        try:
            self._con.close()
            classify_file(self.path)
            self._con = _connect(self.path)
            current = self.load()
            _configure(self._con)
            prepared = prepare_turn(turn, io=self._io)
            if current == turn.next:
                stored = next((r for r in current.protocol.receipts if r.command.command_id == turn.command.command_id), None)
                if stored is not None and stored.command == turn.command and stored.receipt == prepared.receipt:
                    return RecoveryCommitted(current, stored.receipt)
            if current == turn.previous and not any(r.command.command_id == turn.command.command_id for r in current.protocol.receipts):
                return RecoveryAbsent(current)
            raise WorldUnavailable("SAVE_UNCERTAIN", "recovered head is neither exact previous nor next")
        except (sqlite3.Error, OSError, ValueError, TypeError, RuntimeError) as error:
            raise WorldUnavailable("SAVE_UNCERTAIN", str(error)) from error

    def backup_to(self, destination: Path) -> None:
        self._guard()
        target = safe_path(destination)
        descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(descriptor)
        self._backup_reserved(target)

    def _backup_reserved(self, destination: Path) -> None:
        """Destination was exclusively reserved by this adapter or its slot owner."""
        self._guard()
        self.load()
        target = safe_path(destination)
        con = _connect(target)
        try:
            self._con.backup(con, pages=128)
        finally:
            con.close()
        validate_save(target, io=self._io)

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            try:
                self._con.close()
            finally:
                self._lock.close()


def backup_file(source: Path, destination: Path, *, io: StateIO) -> None:
    original, target = safe_path(source), safe_path(destination)
    validate_save(original, io=io)
    descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    _backup_file_reserved(original, target, io=io)


def _backup_file_reserved(source: Path, destination: Path, *, io: StateIO) -> None:
    original, target = safe_path(source), safe_path(destination)
    validate_save(original, io=io)
    source_con = _connect(original, readonly=True)
    target_con: sqlite3.Connection | None = None
    try:
        target_con = _connect(target)
        source_con.backup(target_con, pages=128)
    finally:
        source_con.close()
        if target_con is not None:
            target_con.close()
    validate_save(target, io=io)
