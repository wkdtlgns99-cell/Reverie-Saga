"""Explain existing supply-prioritized aid from actual committed NPC state."""

from pathlib import Path
from collections.abc import Callable
from dataclasses import replace
import tkinter as tk

from app import npc_activity as activity
from app.client import PlayWindow
from app.durable import create_durable
from app.npc_cycle import cycle_bundle
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.replay import ReplaySession
from contracts.turn import ProtocolSnapshot
from domain.canonical import array_value, object_value, text_value
from domain.primitives import EntityId
from domain.state_types import CoreSnapshot
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_gate_aid import session as old_aid_session
from tests.integration.test_npc_cycle import session as old_cycle_session
from tests.integration.test_npc_supply_aid import supply_pipe

from app.client_session import ClientSession

import pytest

from contracts.client import ClientUpdate
from tests.integration.test_cycle_slot_comparison import inventory
from tests.integration.test_npc_gate_aid import aided
from tests.integration.test_npc_supply_aid import session

PREFIX = "NPC 지원 계획 · "
UNHEARD = PREFIX + "의뢰를 직접 들은 뒤 통행 지원을 준비합니다."
FINISHED = PREFIX + "완료 보고를 들어 통행 지원을 마쳤습니다."
OPEN = PREFIX + "통행문이 열려 있어 공동 물자 준비를 이어갑니다."
READY = PREFIX + "공동 물자가 확보되어 통행 지원을 준비하고 있습니다."
SHORT_ZERO = PREFIX + "공동 물자 2개를 더 확보하면 통행 지원을 준비합니다. (현재 0/3개)."
SHORT_ONE = PREFIX + "공동 물자 1개를 더 확보하면 통행 지원을 준비합니다. (현재 1/3개)."


def plans(update: ClientUpdate) -> tuple[str, ...]:
    return tuple(line for line in update.messages if line.startswith(PREFIX))


@pytest.mark.parametrize(("tick", "expected"), ((2, SHORT_ZERO), (4, SHORT_ONE), (8, READY)))
def test_real_talk_plan_uses_committed_stock_and_heard_acceptance(
    tmp_path: Path, tick: int, expected: str
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        update = owner.act("talk")
        if tick != 2:
            owner.act("wait", seconds=tick - 3)
            update = owner.act("talk")
        assert update.status == "COMMITTED" and update.view is not None
        assert update.view.tick == tick and not update.view.gate_open and not aided(update)
        assert plans(update) == (expected,)
    finally:
        owner.close()


@pytest.mark.parametrize("manual_open", (False, True))
def test_unheard_activity_is_read_only_and_never_infers_acceptance(
    tmp_path: Path, manual_open: bool
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        if manual_open:
            owner.act("down")
            owner.act("open")
        owner.act("wait", seconds=8)
        before = owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)
        assert plans(owner.inspect_activity()) == (UNHEARD,)
        assert (owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)) == before
    finally:
        owner.close()


def test_manual_gate_and_real_help_share_current_open_plan_without_invented_history(
    tmp_path: Path,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("open")
        update = owner.act("talk")
        assert plans(update) == (OPEN,) and not aided(update)
        assert "현재 저장 구간에 새로 확인된 의뢰 지원 기록이 없습니다." in update.messages
    finally:
        owner.close()


def test_low_stock_reopening_plan_tracks_current_preparation_not_past_help(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        assert aided(owner.act("wait", seconds=8))
        assert plans(owner.inspect_activity()) == (OPEN,)
        owner.act("close")
        assert plans(owner.inspect_activity()) == (SHORT_ONE,)
        update = owner.act("wait")
        assert not aided(update) and plans(owner.inspect_activity()) == (READY,)
        assert aided(owner.act("wait", seconds=2))
        assert plans(owner.inspect_activity()) == (OPEN,)
    finally:
        owner.close()


def test_heard_completion_finishes_plan_with_gate_closed_and_stock_full(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=8)
        for action in ("right", "down", "attack", "attack", "rest", "attack", "up", "left", "talk"):
            update = owner.act(action)
            assert update.status == "COMMITTED"
        assert update.quest_reward == 1 and plans(update) == (FINISHED,)
        owner.act("close")
        owner.act("wait", seconds=16)
        before = owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)
        assert plans(owner.inspect_activity()) == (FINISHED,)
        assert (owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)) == before
        assert plans(owner.act("talk")) == (FINISHED,)
    finally:
        owner.close()


def test_retry_query_one_verified_replay_and_no_repeated_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        original = activity._ActivityFactory.restore
        calls: list[int] = []

        def counted(
            factory: activity._ActivityFactory, core: CoreSnapshot, protocol: ProtocolSnapshot
        ) -> ReplaySession:
            calls.append(1)
            return original(factory, core, protocol)

        monkeypatch.setattr(activity._ActivityFactory, "restore", counted)
        assert plans(owner.act("talk")) == (SHORT_ZERO,) and calls == [1]
        before = owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)
        assert not plans(owner.retry()) and calls == [1]
        assert plans(owner.inspect_activity()) == (SHORT_ZERO,) and calls == [1, 1]
        assert (owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)) == before
    finally:
        owner.close()


def test_compact_ready_checkpoint_and_restart_keep_current_plan_without_inferred_help(
    tmp_path: Path,
) -> None:
    selected = approved_content()
    owner = session(tmp_path / "source/game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=6)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    compact = tmp_path / "compact/game.sqlite"
    create_durable(
        compact, checkpoint, bundles=(cycle_bundle(selected, npc_aid=True, npc_supply_aid=True),)
    ).close()
    owner = session(compact)
    try:
        assert not owner.owner.retained_segment().trace.steps
        before = owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)
        update = owner.inspect_activity()
        assert plans(update) == (READY,)
        assert (
            "현재 저장 구간에 남은 의뢰 지원 기록이 없습니다. 문 상태로 과거 도움을 추정하지 않습니다."
            in update.messages
        )
        assert (owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)) == before
        assert plans(owner.act("talk")) == (READY,)
        update = owner.act("talk")
        assert aided(update) and plans(update) == (OPEN,)
        assert "NPC 의뢰 지원 회상 · 10초: 통행문을 열었습니다." in update.messages
    finally:
        owner.close()
    owner = session(compact)
    try:
        assert plans(owner.inspect_activity()) == (OPEN,)
    finally:
        owner.close()


def test_saved_previous_branch_plan_is_loaded_from_own_current_state(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.save("slot01")
        owner.act("wait", seconds=8)
        owner.save("slot01")
        assert plans(owner.inspect_activity()) == (OPEN,)
        owner.load("slot01", previous=True)
        path = owner.owner.working_path
        assert plans(owner.inspect_activity()) == (SHORT_ZERO,)
    finally:
        owner.close()
    owner = session(path)
    try:
        assert plans(owner.inspect_activity()) == (SHORT_ZERO,)
        owner.act("wait", seconds=6)
        assert plans(owner.inspect_activity()) == (READY,)
    finally:
        owner.close()


@pytest.mark.parametrize("damage", ("owner", "core", "protocol", "trace", "mode"))
def test_invalid_verified_source_does_not_return_a_plan_or_mutate_state(
    tmp_path: Path, damage: str
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        segment = owner.owner.retained_segment()
        current = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        selected = approved_content()
        npc = selected.definition.layout.npc_id
        supply = True
        if damage == "owner":
            npc = EntityId("actor:other")
        elif damage == "core":
            current = replace(current, core=segment.checkpoint.core)
        elif damage == "protocol":
            current = replace(current, protocol=replace(current.protocol, branch_id="f" * 32))
        elif damage == "trace":
            segment = replace(
                segment,
                trace=replace(
                    segment.trace,
                    steps=(
                        replace(segment.trace.steps[0], expected_facts_hash="f" * 64),
                        *segment.trace.steps[1:],
                    ),
                ),
            )
        else:
            supply = False
        before = owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)
        with pytest.raises(SaveError, match="NPC_ACTIVITY_SOURCE") as caught:
            activity.cycle_activity_messages(
                segment, npc, content=selected, current=current, npc_aid=True, npc_supply_aid=supply
            )
        assert caught.value.code == "NPC_ACTIVITY_SOURCE"
        assert (owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)) == before
    finally:
        owner.close()


@pytest.mark.parametrize("factory", (old_aid_session, old_cycle_session))
def test_unselected_modes_never_append_the_new_plan(
    tmp_path: Path, factory: Callable[[Path], ClientSession]
) -> None:
    owner = factory(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        assert not plans(owner.act("talk"))
        assert not plans(owner.inspect_activity())
    finally:
        owner.close()


def test_actual_framed_worker_load_restart_and_read_only_query(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with supply_pipe(path) as pipe:
        pipe.send("down")
        response = pipe.send("talk")
        assert response["error"] == ""
        update = object_value(response["update"])
        assert tuple(
            x for x in array_value(update["messages"]) if text_value(x).startswith(PREFIX)
        ) == (SHORT_ZERO,)
        pipe.send("save")
        for _ in range(6):
            pipe.send("wait")
        before = path.read_bytes()
        response = pipe.send("activity")
        assert READY in array_value(object_value(response["update"])["messages"])
        assert path.read_bytes() == before
        response = pipe.send("retry")
        assert not any(
            text_value(x).startswith(PREFIX)
            for x in array_value(object_value(response["update"])["messages"])
        )
        assert path.read_bytes() == before
        loaded = object_value(pipe.send("load")["update"])
        path = Path(text_value(loaded["working_path"]))
    with supply_pipe(path) as pipe:
        response = pipe.send("activity")
        assert SHORT_ZERO in array_value(object_value(response["update"])["messages"])


def test_actual_tk_buttons_show_single_current_plan(tk_host: tk.Tk, tmp_path: Path) -> None:
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
        _click(screen, "down")
        _click(screen, "talk")
        assert screen.last_update is not None and plans(screen.last_update) == (SHORT_ZERO,)
        assert SHORT_ZERO in screen.log_text.get("1.0", "end")
        _click(screen, "save")
        for _ in range(6):
            _click(screen, "wait")
        assert screen.activity_button is not None
        screen.activity_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None and plans(screen.last_update) == (READY,)
        assert READY in screen.log_text.get("1.0", "end")
        _click(screen, "load")
        assert screen.activity_button is not None
        screen.activity_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None and plans(screen.last_update) == (SHORT_ZERO,)
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
