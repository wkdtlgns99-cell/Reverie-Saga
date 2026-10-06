from __future__ import annotations

from pathlib import Path
import sqlite3
import subprocess
import sys
import os
from threading import Timer

import pytest

from adapters.sqlite_store import SqliteCommitStore, validate_save
from contracts.persistence import RecoveryAbsent, RecoveryCommitted, SaveError, SaveUnavailable
from contracts.turn import TurnCommitted
from tests.unit.durability_fixtures import checkpoint, io, turn
from tests.unit.durability_fixtures import ROOT


def test_sqlite_real_sparse_turn_and_backup(tmp_path: Path) -> None:
    selected, initial = io(), checkpoint()
    store = SqliteCommitStore.create(tmp_path / "work.sqlite", initial, io=selected)
    request = turn()
    try:
        assert store.load() == initial
        assert isinstance(request.publication.outcome, TurnCommitted)
        assert store.persist(request) == request.publication.outcome.receipt
        assert store.load() == request.next
        segment = store.retained_segment()
        assert len(segment.trace.steps) == 1
        store.backup_to(tmp_path / "copy.sqlite")
        assert validate_save(tmp_path / "copy.sqlite", io=selected) == request.next
    finally:
        store.close()
    reopened = SqliteCommitStore.open(tmp_path / "work.sqlite", io=selected)
    try:
        assert reopened.load() == request.next
        assert isinstance(reopened.recover(request), RecoveryCommitted)
    finally:
        reopened.close()


def test_second_attachment_and_released_lock(tmp_path: Path) -> None:
    selected = io()
    store = SqliteCommitStore.create(tmp_path / "work.sqlite", checkpoint(), io=selected)
    with pytest.raises(SaveError, match="SAVE_LOCKED"):
        SqliteCommitStore.open(store.path, io=selected)
    store.close()
    reopened = SqliteCommitStore.open(store.path, io=selected)
    reopened.close()


def test_confirmed_constraint_rollback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = SqliteCommitStore.create(tmp_path / "work.sqlite", checkpoint(), io=io())
    execute = store._execute

    def failing(query: str, values: tuple[None | int | float | str | bytes, ...] = ()) -> sqlite3.Cursor:
        result = execute(query, values)
        if query.startswith("INSERT INTO receipts"):
            raise sqlite3.IntegrityError("injected after real receipt write")
        return result

    request = turn()
    monkeypatch.setattr(store, "_execute", failing)
    try:
        with pytest.raises(SaveUnavailable):
            store.persist(request)
        assert store.load() == request.previous
        assert isinstance(store.recover(request), RecoveryAbsent)
    finally:
        store.close()


def test_sparse_sql_trace(tmp_path: Path) -> None:
    store = SqliteCommitStore.create(tmp_path / "work.sqlite", checkpoint(), io=io())
    log: list[str] = []
    store._con.set_trace_callback(log.append)
    try:
        store.persist(turn())
        writes = [q for q in log if q.startswith(("INSERT", "UPDATE", "DELETE"))]
        assert len([q for q in writes if q.startswith("INSERT INTO components")]) == 1
        assert all("watch.lantern" in q for q in writes if q.startswith("INSERT INTO components"))
        assert not any(q.startswith(("UPDATE checkpoint", "DELETE FROM replay", "DELETE FROM receipts", "DELETE FROM streams")) for q in writes)
        assert not any(q.startswith(("INSERT INTO pending", "DELETE FROM pending")) for q in writes)
    finally:
        store.close()


def test_pending_ordinal_swap_on_exact_ddl(tmp_path: Path) -> None:
    from dataclasses import replace
    from contracts.watch import WaitCommand
    from orchestration.persistence import prepare_turn
    from tests.unit.watch_fixtures import command
    store = SqliteCommitStore.create(tmp_path / "swap.sqlite", checkpoint(), io=io())
    plan = prepare_turn(turn(command(WaitCommand(2))), io=io())
    first, second = plan.previous.pending[0], replace(plan.next.pending[0], ordinal=1)
    swapped = (replace(second, ordinal=0), replace(first, ordinal=1))
    # DDL conformance only: two real policy-encoded events, not a watch checkpoint.
    row_plan = replace(plan, previous=replace(plan.previous, pending=(first, second)),
                       components_upserts=(), components_deletes=(), pending_deletes=(),
                       pending_upserts=swapped, streams_upserts=(), receipts_deletes=(), receipts_upserts=())
    try:
        store._con.execute("BEGIN IMMEDIATE")
        store._con.execute("INSERT INTO pending VALUES(?,?,?,?)", (second.event_id, 1, second.body, second.sha256))
        store._write_plan(row_plan)
        actual = store._con.execute("SELECT event_id,ordinal,body,sha256 FROM pending ORDER BY ordinal").fetchall()
        assert actual == [(r.event_id, r.ordinal, r.body, r.sha256) for r in swapped]
    finally:
        if store._con.in_transaction:
            store._con.execute("ROLLBACK")
        assert store.load() == checkpoint()
        store.close()


@pytest.mark.parametrize("defect", ["component_key", "component_checksum", "noncanonical", "float", "bool", "unknown", "pending_ordinal", "pending_rank", "pending_cause", "pending_due", "missing_stream", "receipt_key", "head_hash", "replay_revision", "meta_authority"])
def test_corrupt_rows_rejected_before_owner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str) -> None:
    from app import durable
    from app.headless import _Session
    from app.watch_registry import watch_bundle
    from contracts.skeleton import FeatureBundle
    from contracts.state_io import StateIO
    from contracts.watch import WaitCommand
    from domain.canonical import canonical_json, hash_document, object_value
    from orchestration.persistence import canonical_object
    from tests.unit.watch_fixtures import command
    from adapters.save_slots import file_sha256
    path = tmp_path / "bad.sqlite"
    store = SqliteCommitStore.create(path, checkpoint(), io=io())
    store.persist(turn(command(WaitCommand(2))))
    store.close()
    con = sqlite3.connect(path, autocommit=True)
    try:
        if defect == "component_key":
            con.execute("UPDATE components SET entity_id='actor:wrong' WHERE kind='watch.lantern'")
        elif defect == "component_checksum":
            con.execute("UPDATE components SET sha256=?", ("0" * 64,))
        elif defect in ("noncanonical", "float", "bool", "unknown"):
            key, raw = con.execute("SELECT kind,body FROM components WHERE kind='watch.lantern'").fetchone()
            if defect == "noncanonical":
                body = raw + b" "
                checksum = "0" * 64
            else:
                document = dict(canonical_object(raw))
                data = dict(object_value(document["fields"]))
                if defect == "unknown":
                    data["extra"] = 1
                else:
                    data["charge"] = True if defect == "bool" else 1
                document["fields"] = data
                body = canonical_json(document)
                if defect == "float":
                    body = body.replace(b'"charge":1', b'"charge":1.0')
                    checksum = "0" * 64
                else:
                    checksum = hash_document("component/v1", document)
            con.execute("UPDATE components SET body=?,sha256=? WHERE kind=?", (body, checksum, key))
        elif defect.startswith("pending_"):
            if defect == "pending_ordinal":
                con.execute("UPDATE pending SET ordinal=1")
            else:
                raw = con.execute("SELECT body FROM pending").fetchone()[0]
                document = dict(canonical_object(raw))
                event = dict(object_value(document["event"]))
                header = dict(object_value(event["header"]))
                if defect == "pending_rank":
                    header["producer_rank"] = 99
                elif defect == "pending_cause":
                    header["caused_by"] = ("e1-" + "0" * 64,)
                else:
                    event["due_tick"] = 2
                event["header"] = header
                document["event"] = event
                con.execute("UPDATE pending SET body=?,sha256=?", (canonical_json(document), hash_document("pending-event/v1", document)))
        elif defect == "missing_stream":
            con.execute("DELETE FROM streams")
        elif defect == "receipt_key":
            con.execute("UPDATE receipts SET command_id=?", ("c1:" + "0" * 32 + ":" + "1" * 32 + ":9",))
        elif defect == "head_hash":
            con.execute("UPDATE save_head SET core_hash=?", ("0" * 64,))
        elif defect == "replay_revision":
            con.execute("UPDATE replay SET revision=2")
        else:
            raw = con.execute("SELECT core_meta FROM save_head").fetchone()[0]
            document = {**canonical_object(raw), "components": ()}
            con.execute("UPDATE save_head SET core_meta=?", (canonical_json(document),))
    finally:
        con.close()
    sha = file_sha256(path)

    def forbidden_owner(store: SqliteCommitStore, bundles: tuple[FeatureBundle, ...], selected: StateIO) -> _Session:
        raise AssertionError("corruption reached Driver restore")

    monkeypatch.setattr(durable, "_owner", forbidden_owner)
    with pytest.raises(SaveError, match="SAVE_CORRUPT"):
        durable.resume_durable(path, bundles=(watch_bundle(),))
    assert file_sha256(path) == sha


def test_limits_checked_before_body_collection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from adapters import sqlite_store
    store = SqliteCommitStore.create(tmp_path / "limit.sqlite", checkpoint(), io=io())
    try:
        monkeypatch.setattr(sqlite_store, "MAX_ROW", 1)
        with pytest.raises(SaveError, match="SAVE_LIMIT"):
            store.load()
    finally:
        store.close()


@pytest.mark.parametrize("point", ["begin", "components", "pending", "receipt", "header", "before_commit", "after_commit", "after_head"])
def test_process_kill_matrix(tmp_path: Path, point: str) -> None:
    selected = io()
    path = tmp_path / "work.sqlite"
    initial = checkpoint()
    store = SqliteCommitStore.create(path, initial, io=selected)
    store.close()
    source = r'''
import sys
sys.path.insert(0,sys.argv[3])
from app.durable import resume_durable
from app.watch_registry import watch_bundle
from contracts.turn import GameCommand
from contracts.watch import WaitCommand
from domain.primitives import CommandId,EntityId,WorldRevision
owner=resume_durable(__import__('pathlib').Path(sys.argv[1]),bundles=(watch_bundle(),))
store=owner._attachment.store
point=sys.argv[2]
execute=store._execute
def pause():
    print('READY',flush=True)
    sys.stdin.read(1)
def staged(query,values=()):
    if point=='before_commit' and query=='COMMIT':pause()
    result=execute(query,values)
    matches={'begin':query=='BEGIN IMMEDIATE','components':query.startswith('INSERT INTO components'),
      'pending':query.startswith('INSERT INTO pending'),'receipt':query.startswith('INSERT INTO receipts'),
      'header':query.startswith('UPDATE save_head'),'after_commit':query=='COMMIT'}
    if matches.get(point,False):pause()
    return result
store._execute=staged
command=GameCommand(CommandId('c1:'+'0'*32+':'+'1'*32+':1'),EntityId('actor:trial'),WorldRevision(0),WaitCommand(2))
owner.submit(command,attachment_id=owner.attachment_id)
if point=='after_head':pause()
owner.close()
'''
    process = subprocess.Popen([sys.executable, "-c", source, str(path), point, str(ROOT / "src")],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    timer = Timer(20, process.kill)
    timer.start()
    try:
        assert process.stdout is not None
        line = process.stdout.readline()
        if line.strip() != "READY":
            _, errors = process.communicate(timeout=10)
            pytest.fail(errors)
        process.kill()
        process.communicate(timeout=10)
    finally:
        timer.cancel()
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=10)
    reopened = SqliteCommitStore.open(path, io=selected)
    try:
        actual = reopened.load()
        committed = point in ("after_commit", "after_head")
        assert actual.protocol.revision == (1 if committed else 0)
        assert actual.core.tick == (2 if committed else 0)
        assert len(reopened.retained_segment().trace.steps) == (1 if committed else 0)
        if not committed:
            assert actual == initial
        assert selected.decode_pending(actual.core.pending[0]).event.due_tick == (4 if committed else 2)
    finally:
        reopened.close()
    from app.durable import resume_durable
    from app.watch_registry import watch_bundle
    from tests.unit.watch_fixtures import command
    from contracts.watch import WaitCommand
    with resume_durable(path, bundles=(watch_bundle(),)) as owner:
        retried = owner.submit(command(WaitCommand(2)), attachment_id=owner.attachment_id)
        assert isinstance(retried.outcome, TurnCommitted)
        assert owner.snapshot().tick == 2 and owner.protocol().revision == 1
        assert bool(retried.facts) is (not committed)
        assert len(owner.retained_segment().trace.steps) == 1


def test_second_process_attachment(tmp_path: Path) -> None:
    store = SqliteCommitStore.create(tmp_path / "work.sqlite", checkpoint(), io=io())
    code = """import sys
sys.path.insert(0,sys.argv[2])
from app.durable import resume_durable
from app.watch_registry import watch_bundle
from pathlib import Path
from contracts.persistence import SaveError
try:
    owner=resume_durable(Path(sys.argv[1]),bundles=(watch_bundle(),))
    owner.close()
    print('ATTACHED')
except SaveError as error:print(error.code)
"""
    try:
        blocked = subprocess.run([sys.executable, "-c", code, str(store.path), str(ROOT / "src")],
                                 capture_output=True, text=True, timeout=15,
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        assert blocked.returncode == 0 and blocked.stdout.strip() == "SAVE_LOCKED"
    finally:
        store.close()
    released = subprocess.run([sys.executable, "-c", code, str(store.path), str(ROOT / "src")],
                              capture_output=True, text=True, timeout=15,
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    assert released.returncode == 0 and released.stdout.strip() == "ATTACHED"


def test_receipt_eviction_after_resume(tmp_path: Path) -> None:
    from app.durable import create_durable, resume_durable
    from app.feature_registry import feature_bundles
    from contracts.skeleton import StepCommand
    from contracts.turn import GameCommand, TurnRejected
    from domain.primitives import CommandId, EntityId, WorldRevision
    from tests.unit.durability_fixtures import toy_segment_input
    bundles = feature_bundles(EntityId("actor:toy"))
    sample = toy_segment_input(1024, with_segment=False)
    path = tmp_path / "retention.sqlite"
    with create_durable(path, sample.current, bundles=bundles) as owner:
        for n in range(1025, 1031):
            request = GameCommand(CommandId("c1:" + "0" * 32 + ":" + "1" * 32 + ":" + str(n)),
                                  EntityId("actor:toy"), WorldRevision(n - 1), StepCommand(0))
            result = owner.submit(request, attachment_id=owner.attachment_id)
            assert isinstance(result.outcome, TurnCommitted)
        assert len(owner.protocol().receipts) == 1024
        assert owner.protocol().receipts[0].receipt.revision == 7
        assert owner.protocol().streams[0].highest_committed_sequence == 1030
    with resume_durable(path, bundles=bundles) as restored:
        expired = GameCommand(CommandId("c1:" + "0" * 32 + ":" + "1" * 32 + ":1"),
                              EntityId("actor:toy"), WorldRevision(0), StepCommand(0))
        outcome = restored.submit(expired, attachment_id=restored.attachment_id).outcome
        assert isinstance(outcome, TurnRejected) and outcome.failure.code == "RETRY_WINDOW_EXPIRED"
        retained = restored.protocol().receipts[0]
        duplicate = restored.submit(retained.command, attachment_id=restored.attachment_id)
        assert isinstance(duplicate.outcome, TurnCommitted) and duplicate.outcome.receipt == retained.receipt
        assert not duplicate.facts and restored.protocol().revision == 1030


@pytest.mark.parametrize("start", [0, 4096])
def test_segment_rotation_atomic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, start: int) -> None:
    from app.durable import create_durable
    from app.feature_registry import feature_bundles
    from app.headless import _CheckpointFactory, state_io
    from contracts.skeleton import StepCommand
    from contracts.turn import GameCommand, TurnAborted
    from domain.canonical import canonical_json
    from domain.primitives import CommandId, EntityId, WorldRevision
    from orchestration.persistence import checkpoint_document
    from orchestration.replay import Runner
    from tests.unit.durability_fixtures import independent_hash, toy_segment_input
    count = start + 4096
    sample = toy_segment_input(count, start)
    bundles = feature_bundles(EntityId("actor:toy"))
    selected = state_io(bundles)
    with create_durable(tmp_path / "rotation.sqlite", sample.current, bundles=bundles) as owner:
        store = owner._attachment.store
        body = canonical_json(checkpoint_document(sample.initial, io=selected))
        # Install independently derived VALID inputs; this is not an engine/mock outcome.
        store._con.execute("BEGIN IMMEDIATE")
        store._con.execute("UPDATE checkpoint SET body=?,sha256=?", (body, independent_hash("save-checkpoint/v1", body)))
        store._con.execute("UPDATE save_head SET checkpoint_revision=?", (start,))
        store._con.executemany("INSERT INTO replay VALUES(?,?,?)", [(start + i + 1, b, independent_hash("save-step/v1", b)) for i, b in enumerate(sample.bodies)])
        store._con.execute("COMMIT")
        assert store.load() == sample.current
        assert len(owner.retained_segment().trace.steps) == 4096
        request = GameCommand(CommandId("c1:" + "0" * 32 + ":" + "1" * 32 + ":" + str(count + 1)),
                              EntityId("actor:toy"), WorldRevision(count), StepCommand(0))
        execute = store._execute

        def fail_after_new_step(query: str, values: tuple[None | int | float | str | bytes, ...] = ()) -> sqlite3.Cursor:
            result = execute(query, values)
            if query.startswith("INSERT INTO replay"):
                raise sqlite3.OperationalError("after rotated checkpoint and new step")
            return result

        with monkeypatch.context() as patched:
            patched.setattr(store, "_execute", fail_after_new_step)
            aborted = owner.submit(request, attachment_id=owner.attachment_id)
            assert isinstance(aborted.outcome, TurnAborted)
            assert store.load() == sample.current
            assert store.retained_segment().checkpoint.protocol.revision == start
            assert len(store.retained_segment().trace.steps) == 4096
        committed = owner.submit(request, attachment_id=owner.attachment_id)
        assert isinstance(committed.outcome, TurnCommitted)
        segment = store.retained_segment()
        assert segment.checkpoint == sample.current and len(segment.trace.steps) == 1
        assert segment.checkpoint.protocol.revision == count
        assert Runner(segment.checkpoint.core, segment.checkpoint.protocol,
                      factory=_CheckpointFactory(bundles), io=selected).run(segment.trace) == ()
        store.backup_to(tmp_path / "rotation-copy.sqlite")
        assert validate_save(tmp_path / "rotation-copy.sqlite", io=selected) == store.load()
