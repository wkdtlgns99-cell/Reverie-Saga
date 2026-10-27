"""Answered calls use prior-barrier stock and one authoritative passage writer."""

from pathlib import Path
from contextlib import contextmanager
import hashlib
import os
import sqlite3
import subprocess
import sys
import tkinter as tk
from typing import Iterator, cast

import pytest

from app.client import PlayWindow, main as client_main
from app.client_session import ClientSession
from app.client_worker import ClientWorker
from app.durable import create_durable
from app.headless import replay_runner
from app.npc_cycle import cycle_bundle
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.replay import ReplayFixture
from domain.canonical import array_value, object_value, text_value
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_cycle_slot_comparison import inventory
from tests.integration.test_durable_turn import UncertainPort
from tests.integration.test_engine_bridge import PipeClient
from tests.integration.test_npc_gate_aid import state
from tests.integration.test_npc_supply_aid import session as supply_session
from contracts.npc_gate_aid import GateAssisted
from contracts.watch import WatchReplied
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_cycle import cycle
from tests.integration.test_npc_gate_aid import aided


def session(path: Path) -> ClientSession:
    content = approved_content()
    return ClientSession(
        path,
        content.definition.layout,
        quest_content=content,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
    )


@pytest.mark.parametrize("tick,opens,stock", ((8, False, 2), (9, True, 2), (10, True, 1)))
def test_answered_call_uses_existing_prior_barrier_stock(
    tmp_path: Path,
    tick: int,
    opens: bool,
    stock: int,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=tick - 3)
        update = owner.act("bell")
        assert update.status == "COMMITTED"
        assert update.view is not None and update.view.tick == tick
        assert update.view.gate_open is opens and aided(update) is opens
        assert cycle(owner).state.stock == stock
        facts = owner.owner.last_publication().facts
        assists = [event for event in facts if isinstance(event.payload, GateAssisted)]
        replies = [event for event in facts if isinstance(event.payload, WatchReplied)]
        assert len(replies) == 1 and len(assists) == int(opens)
        if opens:
            assert assists[0].header.caused_by == (replies[0].header.event_id,)
            assert assists[0].due_tick == tick
            assert update.messages.count("NPC가 의뢰를 돕기 위해 통행문을 열었습니다.") == 1
    finally:
        owner.close()


def ready(owner: ClientSession) -> None:
    assert owner.act("down").status == "COMMITTED"
    assert owner.act("talk").status == "COMMITTED"
    assert owner.act("wait", seconds=6).status == "COMMITTED"


def replay(owner: ClientSession) -> None:
    segment = owner.owner.retained_segment()
    assert (
        replay_runner(
            ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace),
            bundles=(
                cycle_bundle(
                    approved_content(), npc_aid=True, npc_supply_aid=True, npc_call_aid=True
                ),
            ),
        ).run(segment.trace)
        == ()
    )


@pytest.mark.parametrize("opened", (False, True))
def test_unheard_or_manual_open_never_invents_help(tmp_path: Path, opened: bool) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        if opened:
            owner.act("open")
        owner.act("wait", seconds=8 if not opened else 7)
        update = owner.act("bell")
        assert update.view is not None and update.view.tick == 10
        assert update.view.gate_open is opened and not aided(update)
        assert not any("통행문을 열었습니다." in m for m in owner.inspect_activity().messages)
        replay(owner)
    finally:
        owner.close()


def test_no_call_keeps_routine_and_report_stops_later_calls(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        ready(owner)
        update = owner.act("wait", seconds=2)
        assert aided(update) and update.view is not None and update.view.tick == 10
        for action in ("right", "down", "attack", "attack", "rest", "attack", "up", "left", "talk"):
            update = owner.act(action)
            assert update.status == "COMMITTED"
        assert update.quest_reward == 1
        owner.act("close")
        update = owner.act("bell")
        assert update.view is not None and not update.view.gate_open and not aided(update)
        owner.act("wait", seconds=16)
        assert not aided(owner.act("bell"))
        replay(owner)
    finally:
        owner.close()


def test_call_lineage_read_only_queries_saved_branches_restart_and_retry(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        ready(owner)
        owner.save("slot01")
        assert aided(owner.act("bell"))
        facts = owner.owner.last_publication().facts
        by_id = {e.header.event_id: e for e in facts}
        event = next(e for e in facts if isinstance(e.payload, GateAssisted))
        kinds = []
        while event.header.caused_by:
            event = by_id[event.header.caused_by[0]]
            kinds.append(event.payload.schema.kind)
        assert kinds == ["watch.replied", "watch.echo", "watch.echo", "watch.requested"]
        owner.save("slot01")
        before = state(owner)
        assert not aided(owner.retry()) and state(owner) == before
        assert "NPC 의뢰 지원 기록 · 9초: 통행문을 열었습니다." in owner.inspect_activity().messages
        assert owner.inspect_slot("slot01", previous=True).status == "SLOT_INSPECTED"
        assert state(owner) == before
        talked = owner.act("talk")
        assert "NPC 의뢰 지원 회상 · 9초: 통행문을 열었습니다." in talked.messages
        replay(owner)
        owner.load("slot01", previous=True)
        path = owner.owner.working_path
    finally:
        owner.close()
    owner = session(path)
    try:
        assert cycle(owner).state.stock == 2
        assert aided(owner.act("bell"))
        assert "NPC 의뢰 지원 기록 · 9초: 통행문을 열었습니다." in owner.inspect_activity().messages
        replay(owner)
    finally:
        owner.close()


def test_checkpoint_only_ready_source_generates_new_odd_tick_aid(tmp_path: Path) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        ready(owner)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    path = tmp_path / "clone/game.sqlite"
    create_durable(
        path,
        checkpoint,
        bundles=(
            cycle_bundle(approved_content(), npc_aid=True, npc_supply_aid=True, npc_call_aid=True),
        ),
    ).close()
    owner = session(path)
    try:
        assert not owner.owner.retained_segment().trace.steps
        assert not any("통행문을 열었습니다." in m for m in owner.inspect_activity().messages)
        assert aided(owner.act("bell"))
        assert "NPC 의뢰 지원 회상 · 9초: 통행문을 열었습니다." in owner.act("talk").messages
        replay(owner)
    finally:
        owner.close()


@pytest.mark.parametrize("commit", (False, True))
def test_uncertain_call_preserves_atomic_truth(tmp_path: Path, commit: bool) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        ready(owner)
        before = state(owner)
        store = owner.owner._attachment.store
        port = UncertainPort(store, commit=commit)
        owner.owner._attachment.owner._driver._commit_port = port
        update = owner.act("bell")
        assert port.persist_calls == port.recover_calls == 1
        assert update.status == ("COMMITTED" if commit else "SAVE_UNAVAILABLE")
        assert update.view is not None and update.view.gate_open is commit
        assert aided(update) is commit
        if commit:
            after = state(owner)
            assert not aided(owner.retry()) and state(owner) == after
        else:
            assert state(owner) == before
        assert store.load() == DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()


def test_sql_rollback_then_exact_call_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        ready(owner)
        before = state(owner)
        store = owner.owner._attachment.store
        original = store._execute

        def fail(
            query: str, values: tuple[None | int | float | str | bytes, ...] = ()
        ) -> sqlite3.Cursor:
            result = original(query, values)
            if query.startswith("INSERT INTO replay"):
                raise sqlite3.IntegrityError("F65 actual answered-call rollback")
            return result

        with monkeypatch.context() as patch:
            patch.setattr(store, "_execute", fail)
            assert owner.act("bell").status == "SAVE_UNAVAILABLE"
        assert state(owner) == before
        assert aided(owner.retry())
        view = owner.update().view
        assert view is not None and view.tick == 9
        replay(owner)
    finally:
        owner.close()


@pytest.mark.parametrize("new_source", (False, True))
def test_pinned_modes_reject_cross_load_without_source_mutation(
    tmp_path: Path, new_source: bool
) -> None:
    path = tmp_path / "game.sqlite"
    owner = (session if new_source else supply_session)(path)
    try:
        ready(owner)
    finally:
        owner.close()
    before = inventory(tmp_path)
    with pytest.raises(SaveError, match="^UNSUPPORTED_RULESET:"):
        (supply_session if new_source else session)(path)
    assert inventory(tmp_path) == before


@pytest.mark.parametrize("factory", (ClientSession, ClientWorker))
@pytest.mark.parametrize("flag", (True, 0, 1, None, "1", 2.0))
def test_invalid_selection_before_file_thread_allocation(
    factory: type[ClientSession] | type[ClientWorker],
    flag: object,
    tmp_path: Path,
) -> None:
    selected = approved_content()
    path = tmp_path / "missing/game.sqlite"
    with pytest.raises(ValueError, match="^NPC_CALL_AID_CONTENT$"):
        factory(
            path,
            selected.definition.layout,
            quest_content=selected,
            npc_memory=True,
            npc_cycle=True,
            npc_aid=True,
            npc_supply_aid=flag is not True,
            npc_call_aid=cast(bool, flag),
        )
    assert not path.parent.exists()


def test_client_cli_rejects_call_without_supply_before_tk() -> None:
    with pytest.raises(ValueError, match="^NPC_CALL_AID_CONTENT$"):
        client_main(["--npc-call-aid"])


@contextmanager
def call_pipe(path: Path) -> Iterator[PipeClient]:
    root = Path(__file__).resolve().parents[2]
    catalog = root / "content/narratives.json"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "app.engine_bridge",
            "--working",
            str(path),
            "--catalog",
            str(catalog),
            "--catalog-sha256",
            hashlib.sha256(catalog.read_bytes()).hexdigest(),
            "--scenario",
            "harbor",
            "--quest-catalog",
            str(root / "content/dialogue/harbor-memory-v1.json"),
            "--quest-sha256",
            approved_content().catalog_sha256,
            "--npc-memory",
            "--npc-cycle",
            "--npc-aid",
            "--npc-supply-aid",
            "--npc-call-aid",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=root,
        env=dict(os.environ, PYTHONPATH=str(root / "src"), PYTHONUTF8="1"),
    )
    try:
        yield PipeClient(process)
    finally:
        if process.stdin is not None:
            process.stdin.close()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=15)
            pytest.fail("owned call-aid Brain did not stop on EOF")
        if process.stdout is not None:
            process.stdout.close()
        errors = b"" if process.stderr is None else process.stderr.read()
        if process.stderr is not None:
            process.stderr.close()
        assert process.returncode == 0, errors.decode("utf-8", errors="replace")


def test_actual_framed_worker_restore_and_query_new_mode(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with call_pipe(path) as pipe:
        for action in ("down", "talk", *("wait",) * 6, "save", "bell"):
            response = pipe.send(action)
        update = object_value(response["update"])
        assert object_value(update["view"])["tick"] == "9"
        assert object_value(update["view"])["gate_open"] is True
        messages = tuple(
            map(text_value, array_value(object_value(pipe.send("activity")["update"])["messages"]))
        )
        assert "NPC 의뢰 지원 기록 · 9초: 통행문을 열었습니다." in messages
        before = path.read_bytes()
        pipe.send("retry")
        assert object_value(pipe.send("slot_inspect")["update"])["status"] == "SLOT_INSPECTED"
        assert path.read_bytes() == before
        loaded = object_value(pipe.send("load")["update"])
        path = Path(text_value(loaded["working_path"]))
    with call_pipe(path) as pipe:
        update = object_value(pipe.send("bell")["update"])
        assert object_value(update["view"])["gate_open"] is True
        messages = tuple(
            map(text_value, array_value(object_value(pipe.send("talk")["update"])["messages"]))
        )
        assert "NPC 의뢰 지원 회상 · 9초: 통행문을 열었습니다." in messages


def test_actual_hidden_tk_mode_button_and_worker_load(tk_host: tk.Tk, tmp_path: Path) -> None:
    selected = approved_content()
    panel = tk.Toplevel(tk_host)
    panel.withdraw()
    screen = PlayWindow(
        panel,
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        assert screen.mode_label == "NPC 호출 지원·물자·반복 작업·기억 모드"
        for action in ("down", "talk", *("wait",) * 6, "save", "bell", "talk"):
            _click(screen, action)
        assert "NPC 의뢰 지원 회상 · 9초: 통행문을 열었습니다." in screen.log_text.get("1.0", "end")
        _click(screen, "load")
        assert screen.last_update is not None and screen.last_update.view is not None
        assert screen.last_update.view.tick == 8 and not screen.last_update.view.gate_open
        _click(screen, "bell")
        assert aided(screen.last_update)
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
