"""Next patrol action must reflect actual current and selected saved occupancy."""

from pathlib import Path
from app.client_session import ClientSession
from contracts.client import ClientAction
from tests.integration.test_call_pause_patrol import session, ready
from dataclasses import replace
import tkinter as tk
import pytest
from app.client import PlayWindow
from app.client_worker import ClientWorker
from app.npc_patrol_status import quest_patrol_step_slot_messages
from contracts.persistence import SaveError
from contracts.client import ClientRequest
from domain.canonical import array_value, object_value
from domain.scenario import Scenario
from domain.state_types import CoreSnapshot
from domain.trial import CellPositionRecord
from tests.integration.test_call_pause_patrol import call_pipe, replay
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_cycle_slot_comparison import inventory
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_quest_patrol import report_blocked, state, view


BLOCKED = "NPC 다음 순찰 행동 · 원래 작업 지점을 플레이어가 점유 중입니다. 현재 상태에서는 이동을 기다립니다."
FREE_HOME = (
    "NPC 다음 순찰 행동 · 다음 행동 시점에 원래 작업 지점으로 이동을 시도합니다. (현재 상태 기준)"
)
FREE_NEIGHBOR = (
    "NPC 다음 순찰 행동 · 다음 행동 시점에 옆 작업 지점으로 이동을 시도합니다. (현재 상태 기준)"
)
IDLE = "NPC 다음 순찰 행동 · 현재 작업 지점에서 기다립니다. (현재 상태 기준)"


def blocked(owner: ClientSession) -> None:
    ready(owner)
    actions: tuple[ClientAction, ...] = ("wait", "down", "down")
    for action in actions:
        assert owner.act(action).status == "COMMITTED"
    from tests.integration.test_quest_patrol import view

    assert (view(owner.update()).tick, view(owner.update()).npc_cell) == (6, 7)


def test_actual_occupied_goal_explains_current_wait(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        blocked(owner)
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        assert BLOCKED in owner.inspect_activity().messages
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
    finally:
        owner.close()


def test_selected_save_keeps_its_own_occupancy_when_current_actor_moves(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        blocked(owner)
        owner.save("slot01")
        owner.act("up")
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        rows = owner.inspect_slot("slot01").messages
        assert "NPC 다음 순찰 행동 비교 · 현재 7초 / 선택 저장 6초" in rows
        assert "현재 " + FREE_HOME in rows and "선택 저장 " + BLOCKED in rows
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
    finally:
        owner.close()


def test_talk_and_actual_call_hold_do_not_create_a_future_pause(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        assert IDLE in owner.inspect_activity().messages
        owner.act("down")
        assert FREE_NEIGHBOR in owner.act("talk").messages
        owner.act("up")
        result = owner.act("bell")
        assert (view(result).tick, view(result).npc_cell, view(result).npc_replies) == (4, 6, 1)
        before = state(owner)
        assert FREE_NEIGHBOR in owner.inspect_activity().messages
        assert view(owner.retry()).npc_replies == 1
        assert state(owner) == before
        assert (view(owner.act("wait", seconds=2)).tick, view(owner.update()).npc_cell) == (6, 7)
        assert FREE_HOME in owner.inspect_activity().messages
        replay(owner)
    finally:
        owner.close()


def test_reported_blocked_return_and_arrival_follow_the_same_goal(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        report_blocked(owner)
        assert BLOCKED in owner.inspect_activity().messages
        owner.act("up")
        assert FREE_HOME in owner.inspect_activity().messages
        owner.act("wait")
        assert view(owner.update()).npc_cell == 6
        assert IDLE in owner.inspect_activity().messages
        assert owner.update().quest_reward == 1
        replay(owner)
    finally:
        owner.close()


def test_previous_load_rewind_and_restart_keep_each_branch_occupancy(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    owner = session(path)
    try:
        owner.save("slot01")
        blocked(owner)
        owner.save("slot01")
        saved_before = inventory(tmp_path), state(owner)
        rows = owner.inspect_slot("slot01", previous=True).messages
        assert "현재 " + BLOCKED in rows and "선택 저장 " + IDLE in rows
        assert (inventory(tmp_path), state(owner)) == saved_before
        slot = tmp_path / "slots/slot01.sqlite"
        previous = tmp_path / "slots/slot01.previous.sqlite"
        source_bytes = slot.read_bytes(), previous.read_bytes()
        owner.load("slot01", previous=True)
        branch = owner.owner.working_path
        assert view(owner.update()).tick == 0
        before = state(owner)
        rows = owner.inspect_slot("slot01").messages
        assert "NPC 다음 순찰 행동 비교 · 현재 0초 / 선택 저장 6초" in rows
        assert "현재 " + IDLE in rows and "선택 저장 " + BLOCKED in rows
        assert state(owner) == before
        replay(owner)
    finally:
        owner.close()
    restarted = session(branch)
    try:
        before = state(restarted)
        assert "선택 저장 " + BLOCKED in restarted.inspect_slot("slot01").messages
        assert IDLE in restarted.inspect_activity().messages
        assert state(restarted) == before
        assert (slot.read_bytes(), previous.read_bytes()) == source_bytes
    finally:
        restarted.close()


def test_real_framed_activity_and_slot_preserve_own_snapshot_targets(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with call_pipe(path) as pipe:
        actions: tuple[ClientRequest, ...] = (
            "down",
            "talk",
            "up",
            "wait",
            "down",
            "down",
            "save",
            "up",
        )
        for action in actions:
            assert pipe.send(action)["error"] == ""
        before = inventory(tmp_path)
        activity = object_value(pipe.send("activity")["update"])
        assert FREE_HOME in array_value(activity["messages"])
        slot = object_value(pipe.send("slot_inspect")["update"])
        rows = array_value(slot["messages"])
        assert "현재 " + FREE_HOME in rows and "선택 저장 " + BLOCKED in rows
        assert inventory(tmp_path) == before
        result = object_value(pipe.send("wait")["update"])
        assert object_value(result["view"])["npc_cell"] == "6"


def test_actual_worker_and_withdrawn_tk_show_saved_occupancy_without_loading(
    tk_host: tk.Tk, tmp_path: Path
) -> None:
    selected = approved_content()
    worker = ClientWorker(
        tmp_path / "worker/game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
    )
    try:
        requests: tuple[ClientRequest, ...] = (
            "down",
            "talk",
            "up",
            "wait",
            "down",
            "down",
            "save",
            "up",
        )
        for request in requests:
            assert worker.request(request).result(timeout=10).status in ("COMMITTED", "SAVED")
        before = inventory(tmp_path)
        result = worker.inspect_slot().result(timeout=10)
        assert "현재 " + FREE_HOME in result.messages and "선택 저장 " + BLOCKED in result.messages
        assert FREE_HOME in worker.inspect_activity().result(timeout=10).messages
        assert inventory(tmp_path) == before
    finally:
        worker.join()
    panel = tk.Toplevel(tk_host)
    panel.withdraw()
    screen = PlayWindow(
        panel,
        tmp_path / "tk/game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        actions: tuple[ClientAction, ...] = ("down", "talk", "up", "wait", "down", "down")
        for action in actions:
            _click(screen, action)
        _click(screen, "save")
        _click(screen, "up")
        before = inventory(tmp_path)
        screen.slot_preview_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None
        assert "현재 " + FREE_HOME in screen.last_update.messages
        assert "선택 저장 " + BLOCKED in screen.last_update.messages
        assert "선택 저장 " + BLOCKED in screen.log_text.get("1.0", "end")
        assert inventory(tmp_path) == before
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())


def test_invalid_selected_actor_logs_specific_failure_and_preserves_live_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import app.client_session as projection

    def invalid(saved: CoreSnapshot, current: CoreSnapshot, layout: Scenario) -> tuple[str, ...]:
        records = tuple(
            replace(record, space_id=layout.npc_id)
            if type(record) is CellPositionRecord and record.entity_id == layout.actor_id
            else record
            for record in saved.components
        )
        return quest_patrol_step_slot_messages(replace(saved, components=records), current, layout)

    owner = session(tmp_path / "game.sqlite")
    try:
        ready(owner)
        owner.save("slot01")
        before = state(owner), inventory(tmp_path)
        monkeypatch.setattr(projection, "quest_patrol_step_slot_messages", invalid)
        with pytest.raises(SaveError) as caught:
            owner.inspect_slot("slot01")
        assert caught.value.code == "SAVE_INSPECT_FAILED"
        assert "NPC next patrol step slot comparison failed" in caplog.text
        assert (state(owner), inventory(tmp_path)) == before
        monkeypatch.setattr(
            projection, "quest_patrol_step_slot_messages", quest_patrol_step_slot_messages
        )
        assert "현재 " + FREE_NEIGHBOR in owner.inspect_slot("slot01").messages
        assert owner.act("wait").status == "COMMITTED"
    finally:
        owner.close()
