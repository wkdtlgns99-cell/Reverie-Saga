"""Saved/current goals remain visible when physical positions alone cannot distinguish them."""

from pathlib import Path

from tests.integration.test_quest_patrol import (
    ACCEPTED,
    HOME,
    RETURNING,
    report_blocked,
    session,
    state,
)
from dataclasses import replace
import tkinter as tk

import pytest

from app.client import PlayWindow
from app.client_worker import ClientWorker
from app.npc_patrol_status import quest_patrol_slot_messages
from contracts.persistence import SaveError
from contracts.client import ClientRequest
from domain.canonical import array_value, object_value, text_value
from domain.scenario import Scenario
from domain.state_types import CoreSnapshot
from domain.watch import WatchNpcRecord
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_cycle_slot_comparison import inventory
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_quest_patrol import quest_pipe


UNHEARD = "NPC 의뢰 순찰 계획 · 수락을 직접 듣기 전에는 원래 작업 지점에서 기다립니다."


def expected(current: int, saved: int, live: str, selected: str) -> tuple[str, ...]:
    return (
        f"NPC 의뢰 순찰 계획 비교 · 현재 {current}초 / 선택 저장 {saved}초",
        "현재 " + live,
        "선택 저장 " + selected,
    )


def test_same_home_pose_different_own_knowledge_in_previous_save(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.save("slot01")
        owner.act("down")
        owner.act("talk")
        owner.save("slot01")
        before = state(owner)
        preview = owner.inspect_slot("slot01", previous=True)
        assert preview.messages[-6:-3] == expected(2, 0, ACCEPTED, UNHEARD)
        assert preview.messages[-3:] == (
            "NPC 순찰 위치 비교 · 현재 2초 / 선택 저장 0초",
            "현재 NPC 위치 · 원래 작업 지점입니다.",
            "선택 저장 NPC 위치 · 원래 작업 지점입니다.",
        )
        assert state(owner) == before
    finally:
        owner.close()


def test_saved_pending_return_differs_from_current_arrived_goal(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        report_blocked(owner)
        owner.save("slot01")
        owner.act("up")
        owner.act("wait")
        before = state(owner)
        assert owner.inspect_slot("slot01").messages[-6:-3] == expected(24, 22, HOME, RETURNING)
        assert state(owner) == before
    finally:
        owner.close()


def test_previous_load_reconnect_and_quiet_retry_use_labeled_current_branch(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    owner = session(path)
    try:
        owner.save("slot01")
        owner.act("down")
        owner.act("talk")
        owner.save("slot01")
        before = state(owner)
        assert owner.inspect_slot("slot01", previous=True).messages[-6:-3] == expected(
            2, 0, ACCEPTED, UNHEARD
        )
        assert not any("순찰 계획 비교" in line for line in owner.retry().messages)
        assert state(owner) == before
        owner.load("slot01", previous=True)
        assert owner.inspect_slot("slot01").messages[-6:-3] == expected(0, 2, UNHEARD, ACCEPTED)
        branch = owner.owner.working_path
        original = path.read_bytes()
    finally:
        owner.close()
    owner = session(branch)
    try:
        before_files = inventory(tmp_path)
        assert owner.inspect_slot("slot01").messages[-6:-3] == expected(0, 2, UNHEARD, ACCEPTED)
        assert inventory(tmp_path) == before_files
    finally:
        owner.close()
    assert path.read_bytes() == original


def test_missing_or_corrupt_previous_never_falls_back_to_latest(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    owner = session(path)
    try:
        owner.save("slot01")
        with pytest.raises(SaveError) as caught:
            owner.inspect_slot("slot01", previous=True)
        assert caught.value.code == "PREVIOUS_SAVE_NOT_FOUND"
        previous = tmp_path / "slots/slot01.previous.sqlite"
        previous.write_bytes(b"F75 corrupt selected previous")
        before = state(owner), inventory(tmp_path)
        with pytest.raises(SaveError) as caught:
            owner.inspect_slot("slot01", previous=True)
        assert caught.value.code == "SAVE_CORRUPT"
        assert (state(owner), inventory(tmp_path)) == before
        assert owner.inspect_slot("slot01").messages[-6:-3] == expected(0, 0, UNHEARD, UNHEARD)
    finally:
        owner.close()


def test_actual_invalid_projection_logs_error_without_mutation_or_lost_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import app.client_session as projection

    original = quest_patrol_slot_messages

    def invalid(saved: CoreSnapshot, current: CoreSnapshot, layout: Scenario) -> tuple[str, ...]:
        records = tuple(
            replace(r, space_id=layout.actor_id) if type(r) is WatchNpcRecord else r
            for r in saved.components
        )
        return original(replace(saved, components=records), current, layout)

    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.save("slot01")
        before = state(owner), inventory(tmp_path)
        with monkeypatch.context() as patch:
            patch.setattr(projection, "quest_patrol_slot_messages", invalid)
            with pytest.raises(SaveError) as caught:
                owner.inspect_slot("slot01")
        assert caught.value.code == "SAVE_INSPECT_FAILED"
        assert "NPC quest patrol slot plan comparison failed" in caplog.text
        assert (state(owner), inventory(tmp_path)) == before
        assert not any("순찰 계획 비교" in line for line in owner.retry().messages)
        assert (state(owner), inventory(tmp_path)) == before
    finally:
        owner.close()


def test_real_framed_selected_previous_and_reconnected_current_goal(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with quest_pipe(path) as pipe:
        for action in ("save", "down", "talk", "save"):
            pipe.send(action)
        before = path.read_bytes()
        result = object_value(pipe.send("slot_previous_inspect")["update"])
        assert tuple(text_value(x) for x in array_value(result["messages"]))[-6:-3] == expected(
            2, 0, ACCEPTED, UNHEARD
        )
        assert path.read_bytes() == before
        loaded = object_value(pipe.send("load_previous")["update"])
        branch = Path(text_value(loaded["working_path"]))
    with quest_pipe(branch) as pipe:
        before = branch.read_bytes()
        result = object_value(pipe.send("slot_inspect")["update"])
        assert tuple(text_value(x) for x in array_value(result["messages"]))[-6:-3] == expected(
            0, 2, UNHEARD, ACCEPTED
        )
        assert branch.read_bytes() == before


def test_actual_worker_and_hidden_tk_render_paired_goal_without_loading(
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
    )
    try:
        actions: tuple[ClientRequest, ...] = ("save", "down", "talk", "save")
        for action in actions:
            worker.request(action).result(timeout=10)
        before = inventory(tmp_path)
        result = worker.inspect_previous_slot().result(timeout=10)
        assert result.messages[-6:-3] == expected(2, 0, ACCEPTED, UNHEARD)
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
    )
    try:
        _pump(panel, lambda: not screen.busy)
        for action in ("save", "down", "talk"):
            _click(screen, action)
        before = inventory(tmp_path)
        screen.slot_preview_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None
        assert screen.last_update.messages[-6:-3] == expected(2, 0, ACCEPTED, UNHEARD)
        assert all(
            line in screen.log_text.get("1.0", "end") for line in expected(2, 0, ACCEPTED, UNHEARD)
        )
        assert inventory(tmp_path) == before
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
