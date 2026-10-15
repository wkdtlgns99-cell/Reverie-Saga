from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3
from typing import Literal, cast

import pytest

from adapters.sqlite_store import SqliteCommitStore, validate_save
from app.client import PlayWindow
from app.client_session import ClientSession
from app.client_worker import ClientWorker
from app.headless import state_io
from app.watch_registry import watch_bundle
from contracts.client import ClientUpdate
from contracts.persistence import WorldUnavailable
from contracts.turn import GameCommand, TurnPublication
from domain.canonical import JsonObject
from orchestration.serialization import RegisteredStateIO
from tests.integration.test_client import _click, _pump, _view, tk_host as tk_host, window as window
from tests.integration.test_memory_client_route import approved_content
from tests.unit.durability_fixtures import checkpoint, io


@pytest.mark.parametrize("memory", [False, True])
def test_postcommit_projection_error_reads_current_state_and_exact_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, memory: bool
) -> None:
    path = tmp_path / "committed.sqlite"
    content = approved_content()
    worker = (
        ClientWorker(path, content.definition.layout, quest_content=content, npc_memory=True)
        if memory
        else ClientWorker(path)
    )
    original = ClientSession._publication

    def fail_after_projection(
        self: ClientSession, publication: TurnPublication, *, wait_seconds: int | None = None
    ) -> ClientUpdate:
        original(self, publication, wait_seconds=wait_seconds)
        raise ArithmeticError("publication delivery failed after real commit")

    try:
        before = worker.request("attach").result(timeout=30)
        with monkeypatch.context() as patch:
            patch.setattr(ClientSession, "_publication", fail_after_projection)
            failed = worker.request("wait").result(timeout=30)
        assert failed.status == "CLIENT_ERROR" and _view(failed).tick == 1
        assert _view(failed).revision == 1 and not failed.reset_log
        assert failed.attachment_id == before.attachment_id
        assert not any("기다렸" in message for message in failed.messages)
        retried = worker.request("retry").result(timeout=30)
        assert retried.status == "COMMITTED" and retried.view == failed.view
        assert retried.notices == ()
        assert _view(worker.request("wait").result(timeout=30)).tick == 2
    finally:
        worker.join()
    resumed = (
        ClientSession(path, content.definition.layout, quest_content=content, npc_memory=True)
        if memory
        else ClientSession(path)
    )
    try:
        assert _view(resumed.update()).tick == 2
    finally:
        resumed.close()


@pytest.mark.parametrize("point", ["before", "after"])
def test_load_close_fault_publishes_actual_attachment_and_releases_retired_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, point: str
) -> None:
    path = tmp_path / "load.sqlite"
    worker = ClientWorker(path)
    original = SqliteCommitStore.close
    attempts: list[SqliteCommitStore] = []

    def fail_once(self: SqliteCommitStore) -> None:
        if self.path == path.resolve():
            attempts.append(self)
            if len(attempts) == 1:
                if point == "after":
                    original(self)
                raise sqlite3.OperationalError("retired close failed")
        original(self)

    try:
        worker.request("attach").result(timeout=30)
        saved = worker.request("wait").result(timeout=30)
        worker.request("save").result(timeout=30)
        advanced = worker.request("wait").result(timeout=30)
        source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        with monkeypatch.context() as patch:
            patch.setattr(SqliteCommitStore, "close", fail_once)
            failed = worker.request("load").result(timeout=30)
            assert failed.status == "CLIENT_ERROR" and failed.view == saved.view
            assert failed.attachment_id != advanced.attachment_id
            assert failed.working_path != advanced.working_path and failed.reset_log
            assert worker.request("retry").result(timeout=30).status == "NO_RETRY"
            assert _view(worker.request("wait").result(timeout=30)).tick == 2
            active = Path(failed.working_path)
            worker.join()
        assert len(attempts) == 2 and attempts[0] is attempts[1]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source_hash
        assert validate_save(active, io=state_io((watch_bundle(),))).core.tick == 2
        reopened = SqliteCommitStore.open(path, io=state_io((watch_bundle(),)))
        reopened.close()
    finally:
        worker.join()


def test_failed_fresh_projection_keeps_explicit_error_then_reconciles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    worker = ClientWorker(tmp_path / "projection.sqlite")

    def broken(self: ClientSession, *args: object, **kwargs: object) -> ClientUpdate:
        raise ArithmeticError("projection unavailable")

    try:
        before = worker.request("attach").result(timeout=30)
        with monkeypatch.context() as patch:
            patch.setattr(ClientSession, "update", broken)
            failed = worker.request("wait").result(timeout=30)
        assert failed.status == "CLIENT_ERROR" and failed.view == before.view
        assert not failed.reset_log and "client error reconciliation failed" in caplog.text
        current = worker.request("attach").result(timeout=30)
        assert _view(current).tick == 1 and _view(current).revision == 1
        assert worker.request("retry").result(timeout=30).view == current.view
        assert _view(worker.request("wait").result(timeout=30)).tick == 2
    finally:
        worker.join()


@pytest.mark.parametrize("fault", [KeyboardInterrupt, SystemExit])
def test_reconciliation_process_control_propagates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: type[BaseException]
) -> None:
    worker = ClientWorker(tmp_path / "control.sqlite")
    calls = 0

    def interrupted(self: ClientSession, *args: object, **kwargs: object) -> ClientUpdate:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ArithmeticError("projection failed")
        raise fault("reconciliation interrupted")

    try:
        worker.request("attach").result(timeout=30)
        with monkeypatch.context() as patch:
            patch.setattr(ClientSession, "update", interrupted)
            with pytest.raises(fault, match="reconciliation interrupted"):
                worker.request("wait").result(timeout=30)
        assert _view(worker.request("attach").result(timeout=30)).tick == 1
    finally:
        worker.join()


def test_actual_connection_close_failure_can_retry_without_reopening_writes(tmp_path: Path) -> None:
    store = SqliteCommitStore.create(tmp_path / "store.sqlite", checkpoint(), io=io())
    native = store._con

    class FailOnce:
        calls = 0

        def close(self) -> None:
            self.calls += 1
            if self.calls == 1:
                raise sqlite3.OperationalError("actual close boundary failed")
            native.close()

    proxy = FailOnce()
    store._con = cast(sqlite3.Connection, proxy)
    try:
        with pytest.raises(sqlite3.OperationalError, match="actual close boundary"):
            store.close()
        with pytest.raises(WorldUnavailable):
            store.load()
        store.close()
        assert proxy.calls == 2
        with pytest.raises(sqlite3.ProgrammingError):
            native.execute("SELECT 1")
    finally:
        store._con = native
        store.close()


def test_shutdown_attempts_active_store_when_retired_close_still_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = ClientSession(tmp_path / "retired.sqlite")
    previous = session.owner._attachment.store
    original = SqliteCommitStore.close
    attempts: list[SqliteCommitStore] = []

    def failed(self: SqliteCommitStore) -> None:
        attempts.append(self)
        if self is previous:
            raise sqlite3.OperationalError("persistent retired close failure")
        original(self)

    try:
        session.act("wait")
        session.save("slot01")
        with monkeypatch.context() as patch:
            patch.setattr(SqliteCommitStore, "close", failed)
            with pytest.raises(sqlite3.OperationalError, match="persistent retired"):
                session.load("slot01")
            active = session.owner._attachment.store
            assert session.owner._retired_stores == [previous]
            attempts.clear()
            with pytest.raises(sqlite3.OperationalError, match="persistent retired"):
                session.close()
            assert attempts == [previous, active]
            assert session.owner._retired_stores == [previous] and not session.owner._closed
            with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
                active._con.execute("SELECT 1")
        session.close()
        assert session.owner._retired_stores == [] and session.owner._closed
        with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
            previous._con.execute("SELECT 1")
    finally:
        session.close()


def test_registered_codec_bug_preserves_precommit_state_and_next_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = ClientSession(tmp_path / "codec.sqlite")
    original = RegisteredStateIO.encode_command

    def broken(self: RegisteredStateIO, command: GameCommand) -> JsonObject:
        original(self, command)
        raise RuntimeError("registered command encoder bug")

    try:
        before = session.owner.snapshot(), session.owner.protocol()
        raw = Path(session.update().working_path).read_bytes()
        with monkeypatch.context() as patch:
            patch.setattr(RegisteredStateIO, "encode_command", broken)
            with pytest.raises(RuntimeError, match="registered command encoder bug"):
                session.act("wait")
        assert (session.owner.snapshot(), session.owner.protocol()) == before
        assert Path(session.update().working_path).read_bytes() == raw
        assert _view(session.act("wait")).tick == 1
    finally:
        session.close()


def test_real_tk_load_error_resets_history_to_actual_loaded_state(
    window: PlayWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    _click(window, "wait")
    saved = window.view
    _control(window, "save")
    _click(window, "wait")
    assert window.last_update is not None
    old_path = Path(window.last_update.working_path)
    original = SqliteCommitStore.close

    def failed(self: SqliteCommitStore) -> None:
        original(self)
        if self.path == old_path:
            raise sqlite3.OperationalError("retired Tk store close failed")

    with monkeypatch.context() as patch:
        patch.setattr(SqliteCommitStore, "close", failed)
        _control(window, "load")
    assert window.status.get() == "CLIENT_ERROR" and window.view == saved
    assert window.last_update is not None and window.last_update.reset_log
    assert Path(window.last_update.working_path) != old_path
    assert all("기다렸" not in line for line in window.history)
    _control(window, "retry")
    assert window.status.get() == "NO_RETRY"
    _click(window, "wait")
    assert window.view is not None and window.view.tick == 2


def _control(window: PlayWindow, request: Literal["save", "load", "retry"]) -> None:
    window.buttons[request].invoke()
    _pump(window.root, lambda: not window.busy)
