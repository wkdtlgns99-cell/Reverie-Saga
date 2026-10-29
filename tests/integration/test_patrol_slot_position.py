"""Selected saves expose their actual NPC pose without moving either branch."""

from pathlib import Path
import tkinter as tk

from app.client import PlayWindow
from app.client_worker import ClientWorker
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_cycle_slot_comparison import inventory

import pytest

from domain.canonical import array_value, object_value, text_value
from tests.integration.test_npc_patrol import patrol_pipe, session


def expected(current: int, saved: int, live: str, old: str) -> tuple[str, ...]:
    return (
        f"NPC 순찰 위치 비교 · 현재 {current}초 / 선택 저장 {saved}초",
        f"현재 NPC 위치 · {live} 작업 지점입니다.",
        f"선택 저장 NPC 위치 · {old} 작업 지점입니다.",
    )


def test_direct_selected_previous_and_rewound_positions(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    owner = session(path)
    try:
        owner.act("down")
        owner.act("talk")
        owner.save("slot01")
        owner.act("wait", seconds=2)
        owner.save("slot01")
        before = owner.owner.snapshot(), owner.owner.protocol(), path.read_bytes()
        preview = owner.inspect_slot("slot01", previous=True)
        assert preview.messages[-3:] == expected(4, 2, "원래", "옆")
        assert (owner.owner.snapshot(), owner.owner.protocol(), path.read_bytes()) == before
        assert owner.inspect_slot("slot01").messages[-3:] == expected(4, 4, "원래", "원래")
        assert not any("NPC 위치 ·" in line for line in owner.retry().messages)
        owner.load("slot01", previous=True)
        assert owner.inspect_slot("slot01").messages[-3:] == expected(2, 4, "옆", "원래")
        branch = owner.owner.working_path
        source_bytes = path.read_bytes()
        with pytest.raises(ValueError, match="NO_RETRY"):
            owner.retry()
    finally:
        owner.close()
    owner = session(branch)
    try:
        restarted_before = owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)
        assert owner.inspect_slot("slot01").messages[-3:] == expected(2, 4, "옆", "원래")
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            inventory(tmp_path),
        ) == restarted_before
    finally:
        owner.close()
    assert path.read_bytes() == source_bytes


def test_real_framed_previous_position_is_read_only(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with patrol_pipe(path) as pipe:
        for action in ("down", "talk", "save", "wait", "wait", "save"):
            pipe.send(action)
        before = path.read_bytes()
        result = object_value(pipe.send("slot_previous_inspect")["update"])
        assert result["status"] == "SLOT_INSPECTED"
        lines = tuple(text_value(x) for x in array_value(result["messages"]))
        assert lines[-3:] == expected(4, 2, "원래", "옆")
        assert path.read_bytes() == before
        loaded = object_value(pipe.send("load_previous")["update"])
        branch = Path(text_value(loaded["working_path"]))
        assert path.read_bytes() == before
    with patrol_pipe(branch) as pipe:
        before_branch = branch.read_bytes()
        result = object_value(pipe.send("slot_inspect")["update"])
        assert tuple(text_value(x) for x in array_value(result["messages"]))[-3:] == expected(
            2, 4, "옆", "원래"
        )
        assert branch.read_bytes() == before_branch
    assert path.read_bytes() == before


def test_blocked_pose_is_not_inferred_from_even_tick(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("down")
        owner.save("slot01")
        owner.act("wait", seconds=2)
        assert owner.inspect_slot("slot01").messages[-3:] == expected(4, 2, "옆", "옆")
    finally:
        owner.close()


def test_stationary_call_mode_adds_no_position_comparison(tmp_path: Path) -> None:
    from tests.integration.test_npc_call_aid import session as stationary

    owner = stationary(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.save("slot01")
        assert not any(
            "NPC 위치 ·" in line or "NPC 순찰 위치 비교" in line
            for line in owner.inspect_slot("slot01").messages
        )
    finally:
        owner.close()


def test_actual_worker_and_hidden_tk_slot_position(tk_host: tk.Tk, tmp_path: Path) -> None:
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
    )
    try:
        worker.request("down").result(timeout=10)
        worker.request("talk").result(timeout=10)
        worker.request("save").result(timeout=10)
        worker.request("wait").result(timeout=10)
        live = worker.request("wait").result(timeout=10)
        before = inventory(tmp_path)
        update = worker.inspect_slot().result(timeout=10)
        assert update.view == live.view and update.messages[-3:] == expected(4, 2, "원래", "옆")
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
    )
    try:
        _pump(panel, lambda: not screen.busy)
        for action in ("down", "talk", "save", "wait", "wait"):
            _click(screen, action)
        assert screen.last_update is not None
        view = screen.last_update.view
        before = inventory(tmp_path)
        screen.slot_preview_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None and screen.last_update.view == view
        assert screen.last_update.messages[-3:] == expected(4, 2, "원래", "옆")
        assert all(
            line in screen.log_text.get("1.0", "end") for line in expected(4, 2, "원래", "옆")
        )
        assert inventory(tmp_path) == before
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())


def test_projection_source_error_is_logged_and_preserves_state_and_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    from dataclasses import replace
    import app.client_session as projection
    from contracts.persistence import SaveError
    from domain.primitives import EntityId
    from domain.scenario import Scenario
    from domain.state_types import CoreSnapshot
    from domain.watch import WatchNpcRecord

    owner = session(tmp_path / "game.sqlite")
    original = projection._patrol_slot_messages

    def invalid(saved: CoreSnapshot, current: CoreSnapshot, layout: Scenario) -> tuple[str, ...]:
        records = tuple(
            replace(record, space_id=EntityId("space:foreign"))
            if type(record) is WatchNpcRecord
            else record
            for record in saved.components
        )
        return original(replace(saved, components=records), current, layout)

    try:
        owner.act("down")
        owner.act("talk")
        owner.save("slot01")
        owner.act("wait", seconds=2)
        before = owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)
        with monkeypatch.context() as patch:
            patch.setattr(projection, "_patrol_slot_messages", invalid)
            with pytest.raises(SaveError) as caught:
                owner.inspect_slot("slot01")
        assert caught.value.code == "SAVE_INSPECT_FAILED"
        assert "NPC patrol slot position comparison failed" in caplog.text
        assert (owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)) == before
        assert not any("NPC 위치 ·" in line for line in owner.retry().messages)
        assert owner.inspect_slot("slot01").messages[-3:] == expected(4, 2, "원래", "옆")
    finally:
        owner.close()
