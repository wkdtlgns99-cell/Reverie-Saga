"""Readiness changes actual aid timing without spending communal stock."""

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

from app.client import PlayWindow
from app.client_worker import ClientWorker
from app.durable import create_durable
from app.headless import replay_runner
from app.npc_cycle import cycle_bundle
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.replay import ReplayFixture
from domain.canonical import array_value, object_value, text_value
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_durable_turn import UncertainPort
from tests.integration.test_engine_bridge import PipeClient
from tests.integration.test_cycle_slot_comparison import inventory
from tests.integration.test_npc_gate_aid import session as prior_aid_session, state

from app.client_session import ClientSession
from contracts.npc_gate_aid import GateAssisted
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_cycle import cycle
from tests.integration.test_npc_gate_aid import aided


def session(path: Path) -> ClientSession:
    selected = approved_content()
    return ClientSession(
        path,
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
    )


def test_new_preparation_is_not_available_until_next_barrier(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        for tick, stock in ((4, 1), (6, 1), (8, 2)):
            update = owner.act("wait", seconds=2)
            assert update.view is not None and update.view.tick == tick
            assert not update.view.gate_open and not aided(update)
            assert cycle(owner).state.stock == stock
        update = owner.act("wait", seconds=2)
        assert update.view is not None and update.view.tick == 10 and update.view.gate_open
        assert aided(update)
        assert (
            cycle(owner).state.stock,
            cycle(owner).state.produced,
            cycle(owner).state.consumed,
        ) == (1, 2, 1)
        facts = [
            e for e in owner.owner.last_publication().facts if isinstance(e.payload, GateAssisted)
        ]
        assert len(facts) == 1 and facts[0].due_tick == 10
    finally:
        owner.close()


def test_low_stock_after_consumption_delays_reopening(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=8)
        assert aided(owner.act("close")) is False  # 11,one remaining communal item
        update = owner.act("wait")  # 12,prepares second item after prior-barrier decision
        assert update.view is not None and update.view.tick == 12 and not update.view.gate_open
        assert cycle(owner).state.stock == 2 and not aided(update)
        assert not aided(owner.act("wait"))
        update = owner.act("wait")
        assert update.view is not None and update.view.tick == 14 and update.view.gate_open
        assert aided(update) and cycle(owner).state.stock == 2
    finally:
        owner.close()


def test_current_talk_retrieves_only_actual_supply_ready_opening(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=7)
        update = owner.act("talk")
        assert update.view is not None and update.view.tick == 10 and update.view.gate_open
        assert "NPC 의뢰 지원 회상 · 10초: 통행문을 열었습니다." in update.messages
        assert "확인한 문 열기 1건 중 최근 1건입니다." in update.messages
        assert not any(m.startswith("NPC 의뢰 지원 회상 · 4초:") for m in update.messages)
        assert (
            "현재 저장 구간에 새로 확인된 의뢰 지원 기록이 없습니다." in owner.act("talk").messages
        )
    finally:
        owner.close()


def replay(owner: ClientSession) -> None:
    segment = owner.owner.retained_segment()
    assert (
        replay_runner(
            ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace),
            bundles=(cycle_bundle(approved_content(), npc_aid=True, npc_supply_aid=True),),
        ).run(segment.trace)
        == ()
    )


def accept(owner: ClientSession) -> None:
    assert owner.act("down").status == "COMMITTED"
    assert owner.act("talk").status == "COMMITTED"


def test_long_and_split_waits_have_same_real_state_and_one_opening(tmp_path: Path) -> None:
    long, split = session(tmp_path / "long/game.sqlite"), session(tmp_path / "split/game.sqlite")
    try:
        for owner in (long, split):
            accept(owner)
        update = long.act("wait", seconds=16)
        for _ in range(16):
            split.act("wait")
        assert long.owner.snapshot() == split.owner.snapshot()
        assert cycle(long).state == cycle(split).state
        assert (
            cycle(long).state.stock,
            cycle(long).state.produced,
            cycle(long).state.consumed,
        ) == (3, 4, 1)
        assert (
            sum(isinstance(e.payload, GateAssisted) for e in long.owner.last_publication().facts)
            == 1
        )
        assert update.messages.count("NPC가 의뢰를 돕기 위해 통행문을 열었습니다.") == 1
        replay(long)
        replay(split)
    finally:
        long.close()
        split.close()


@pytest.mark.parametrize("accepted", (False, True))
def test_manual_open_is_not_invented_as_supply_aid(tmp_path: Path, accepted: bool) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("open")
        if accepted:
            owner.act("talk")
        update = owner.act("wait", seconds=16)
        assert not aided(update)
        assert update.view is not None and update.view.gate_open
        assert (
            "현재 저장 구간에 남은 의뢰 지원 기록이 없습니다. 문 상태로 과거 도움을 추정하지 않습니다."
            in owner.inspect_activity().messages
        )
    finally:
        owner.close()


def test_report_stops_supply_ready_help_and_repeated_talk_stays_empty(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        accept(owner)
        owner.act("wait", seconds=8)
        for action in ("right", "down", "attack", "attack", "rest", "attack", "up", "left", "talk"):
            update = owner.act(action)
            assert update.status == "COMMITTED"
        assert update.view is not None and update.view.tick == 19 and update.quest_reward == 1
        assert "NPC 의뢰 지원 회상 · 10초: 통행문을 열었습니다." in update.messages
        owner.act("close")
        update = owner.act("wait", seconds=16)
        assert update.view is not None and update.view.tick == 36 and not update.view.gate_open
        assert cycle(owner).state.stock == 3 and not aided(update)
        assert (
            "현재 저장 구간에 새로 확인된 의뢰 지원 기록이 없습니다." in owner.act("talk").messages
        )
        assert owner.update().quest_reward == 1
        replay(owner)
    finally:
        owner.close()


def test_compact_ready_checkpoint_drives_new_help_without_past_inference(tmp_path: Path) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        accept(owner)
        owner.act("wait", seconds=6)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        view = owner.update().view
        assert view is not None and not view.gate_open
    finally:
        owner.close()
    clone = tmp_path / "compact/game.sqlite"
    create_durable(
        clone,
        checkpoint,
        bundles=(cycle_bundle(approved_content(), npc_aid=True, npc_supply_aid=True),),
    ).close()
    owner = session(clone)
    try:
        assert owner.owner.retained_segment().trace.steps == ()
        assert not any("통행문을 열었습니다." in m for m in owner.inspect_activity().messages)
        assert aided(owner.act("wait", seconds=2))
        talked = owner.act("talk")
        assert "NPC 의뢰 지원 회상 · 10초: 통행문을 열었습니다." in talked.messages
        assert "NPC 의뢰 지원 회상 · 8초 이후 저장 구간의 도움입니다." in talked.messages
        replay(owner)
    finally:
        owner.close()


def test_previous_saved_branch_restart_query_recollection_and_retry(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        accept(owner)
        owner.save("slot01")
        owner.act("wait", seconds=8)
        owner.save("slot01")
        original = inventory(tmp_path)
        before = state(owner)
        assert owner.inspect_slot("slot01", previous=True).status == "SLOT_INSPECTED"
        assert owner.inspect_activity().status == "ACTIVITY_INSPECTED" and state(owner) == before
        assert (
            "NPC 의뢰 지원 기록 · 10초: 통행문을 열었습니다." in owner.inspect_activity().messages
        )
        owner.load("slot01", previous=True)
        path = owner.owner.working_path
    finally:
        owner.close()
    owner = session(path)
    try:
        view = owner.update().view
        assert view is not None and view.tick == 2
        owner.act("wait", seconds=6)
        view = owner.update().view
        assert view is not None and not view.gate_open
        assert aided(owner.act("wait", seconds=2))
        before = state(owner)
        assert not aided(owner.retry()) and state(owner) == before
        assert all((tmp_path / name).read_bytes() == raw for name, raw in original.items())
        replay(owner)
    finally:
        owner.close()


@pytest.mark.parametrize("new_source", (False, True))
def test_old_and_supply_aid_saves_reject_cross_mode_without_mutation(
    tmp_path: Path, new_source: bool
) -> None:
    path = tmp_path / "game.sqlite"
    owner = (session if new_source else prior_aid_session)(path)
    try:
        accept(owner)
    finally:
        owner.close()
    before = inventory(tmp_path)
    with pytest.raises(SaveError, match="^UNSUPPORTED_RULESET:"):
        (prior_aid_session if new_source else session)(path)
    assert inventory(tmp_path) == before


@pytest.mark.parametrize("factory", (ClientSession, ClientWorker))
@pytest.mark.parametrize("flag", (True, 0, 1, None, "1", 2.0))
def test_invalid_mode_before_file_or_worker_allocation(
    factory: type[ClientSession] | type[ClientWorker], flag: object, tmp_path: Path
) -> None:
    selected = approved_content()
    path = tmp_path / "missing/game.sqlite"
    with pytest.raises(ValueError, match="^NPC_SUPPLY_AID_CONTENT$"):
        factory(
            path,
            selected.definition.layout,
            quest_content=selected,
            npc_memory=True,
            npc_cycle=True,
            npc_aid=flag is not True,
            npc_supply_aid=cast(bool, flag),
        )
    assert not path.parent.exists()


@pytest.mark.parametrize("commit", (False, True))
def test_uncertain_threshold_opening_keeps_truth_and_quiet_retry(
    tmp_path: Path, commit: bool
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        accept(owner)
        owner.act("wait", seconds=6)
        before = state(owner)
        store = owner.owner._attachment.store
        port = UncertainPort(store, commit=commit)
        owner.owner._attachment.owner._driver._commit_port = port
        update = owner.act("wait", seconds=2)
        assert port.persist_calls == port.recover_calls == 1
        assert update.status == ("COMMITTED" if commit else "SAVE_UNAVAILABLE")
        assert update.view is not None and update.view.gate_open == commit
        assert aided(update) == commit
        if commit:
            current = state(owner)
            assert not aided(owner.retry()) and state(owner) == current
        else:
            assert state(owner) == before
        assert store.load() == DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()


def test_actual_sql_rollback_at_threshold_preserves_source_then_exact_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        accept(owner)
        owner.act("wait", seconds=6)
        before = state(owner)
        store = owner.owner._attachment.store
        original = store._execute

        def fail(
            query: str, values: tuple[None | int | float | str | bytes, ...] = ()
        ) -> sqlite3.Cursor:
            result = original(query, values)
            if query.startswith("INSERT INTO pending"):
                raise sqlite3.IntegrityError("F59 actual threshold-open rollback")
            return result

        with monkeypatch.context() as patch:
            patch.setattr(store, "_execute", fail)
            assert owner.act("wait", seconds=2).status == "SAVE_UNAVAILABLE"
        assert state(owner) == before
        assert aided(owner.retry())
        view = owner.update().view
        assert view is not None and view.tick == 10
    finally:
        owner.close()


@contextmanager
def supply_pipe(path: Path) -> Iterator[PipeClient]:
    root = Path(__file__).resolve().parents[2]
    selected = approved_content()
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
            selected.catalog_sha256,
            "--npc-memory",
            "--npc-cycle",
            "--npc-aid",
            "--npc-supply-aid",
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
            pytest.fail("owned supply-aid Brain did not stop on EOF")
        if process.stdout is not None:
            process.stdout.close()
        errors = b"" if process.stderr is None else process.stderr.read()
        if process.stderr is not None:
            process.stderr.close()
        assert process.returncode == 0, errors.decode("utf-8", errors="replace")


def test_actual_framed_worker_reconnect_and_load_keep_selection(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with supply_pipe(path) as pipe:
        pipe.send("down")
        pipe.send("talk")
        pipe.send("save")
        for _ in range(6):
            update = object_value(pipe.send("wait")["update"])
            assert object_value(update["view"])["gate_open"] is False
        for _ in range(2):
            update = object_value(pipe.send("wait")["update"])
        assert object_value(update["view"])["gate_open"] is True
        messages = tuple(
            map(text_value, array_value(object_value(pipe.send("talk")["update"])["messages"]))
        )
        assert "NPC 의뢰 지원 회상 · 10초: 통행문을 열었습니다." in messages
        before = path.read_bytes()
        pipe.send("activity")
        pipe.send("retry")
        assert path.read_bytes() == before
        loaded = object_value(pipe.send("load")["update"])
        path = Path(text_value(loaded["working_path"]))
    with supply_pipe(path) as pipe:
        for _ in range(6):
            update = object_value(pipe.send("wait")["update"])
        assert object_value(update["view"])["gate_open"] is False
        for _ in range(2):
            update = object_value(pipe.send("wait")["update"])
        assert object_value(update["view"])["gate_open"] is True


def test_actual_tk_mode_button_and_worker_restore_selection(tk_host: tk.Tk, tmp_path: Path) -> None:
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
    )
    try:
        _pump(panel, lambda: not screen.busy)
        assert screen.mode_label == "NPC 물자 2개 확보 후 지원·반복 작업·기억 모드"
        for action in ("down", "talk", "save", *("wait",) * 6):
            _click(screen, action)
        assert (
            screen.last_update is not None
            and screen.last_update.view is not None
            and not screen.last_update.view.gate_open
        )
        _click(screen, "wait")
        _click(screen, "wait")
        assert (
            screen.last_update.view is not None
            and screen.last_update.view.gate_open
            and aided(screen.last_update)
        )
        _click(screen, "talk")
        assert "NPC 의뢰 지원 회상 · 10초: 통행문을 열었습니다." in screen.log_text.get(
            "1.0", "end"
        )
        _click(screen, "load")
        assert (
            screen.last_update.view is not None
            and screen.last_update.view.tick == 2
            and not screen.last_update.view.gate_open
        )
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())


def test_even_close_keeps_real_player_fact_when_new_stock_is_not_yet_visible(
    tmp_path: Path,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        accept(owner)
        owner.act("wait", seconds=9)
        update = owner.act("close")
        assert update.view is not None and update.view.tick == 12 and not update.view.gate_open
        assert "플레이어가 문을 닫았습니다." in update.messages and not aided(update)
        assert cycle(owner).state.stock == 2 and not owner.owner.last_publication().diagnostics
        replay(owner)
    finally:
        owner.close()


def test_report_same_barrier_uses_prior_heard_memory_and_recollection_tracks_real_open(
    tmp_path: Path,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        accept(owner)
        owner.act("wait", seconds=8)
        for action in (
            "right",
            "down",
            "attack",
            "attack",
            "rest",
            "attack",
            "up",
            "left",
            "close",
        ):
            assert owner.act(action).status == "COMMITTED"
        update = owner.act("talk")
        assert update.view is not None and update.view.tick == 20 and update.view.gate_open
        assert update.quest_reward == 1 and aided(update)
        assert "NPC 의뢰 지원 회상 · 20초: 통행문을 열었습니다." in update.messages
        assert "확인한 문 열기 2건 중 최근 2건입니다." in update.messages
        owner.act("close")
        assert not aided(owner.act("wait"))
        view = owner.update().view
        assert view is not None and not view.gate_open
        replay(owner)
    finally:
        owner.close()
