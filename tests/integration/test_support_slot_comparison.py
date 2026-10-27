"""Selected support-plan comparison is factual,read-only and branch-specific."""

from pathlib import Path
import tkinter as tk

from app.client import PlayWindow
from app.client_worker import ClientWorker
from contracts.persistence import SaveError
from domain.canonical import array_value, object_value, text_value
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_supply_aid import supply_pipe

import pytest

from contracts.client import ClientUpdate
from tests.integration.test_cycle_slot_comparison import inventory
from tests.integration.test_npc_supply_aid import session

ZERO = "NPC 지원 계획 · 공동 물자 2개를 더 확보하면 통행 지원을 준비합니다. (현재 0/3개)."
READY = "NPC 지원 계획 · 공동 물자가 확보되어 통행 지원을 준비하고 있습니다."
OPEN = "NPC 지원 계획 · 통행문이 열려 있어 공동 물자 준비를 이어갑니다."
FINISHED = "NPC 지원 계획 · 완료 보고를 들어 통행 지원을 마쳤습니다."


def comparison(update: ClientUpdate) -> tuple[str, ...]:
    return tuple(
        line
        for line in update.messages
        if line.startswith(
            ("NPC 지원 계획 비교 · ", "현재 NPC 지원 계획 · ", "선택 저장 NPC 지원 계획 · ")
        )
    )


def expected(current: int, saved: int, live: str, old: str) -> tuple[str, ...]:
    return (
        f"NPC 지원 계획 비교 · 현재 {current}초 / 선택 저장 {saved}초",
        "현재 " + live,
        "선택 저장 " + old,
    )


@pytest.mark.parametrize(
    ("saved", "current", "old", "live"),
    ((2, 8, ZERO, READY), (8, 10, READY, OPEN), (2, 2, ZERO, ZERO)),
)
def test_real_selected_slot_plans_are_labeled_and_read_only(
    tmp_path: Path, saved: int, current: int, old: str, live: str
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        if saved > 2:
            owner.act("wait", seconds=saved - 2)
        owner.save("slot01")
        if current > saved:
            owner.act("wait", seconds=current - saved)
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.attachment_id,
            owner.owner.retained_segment(),
            inventory(tmp_path),
        )
        update = owner.inspect_slot("slot01")
        assert update.status == "SLOT_INSPECTED" and not update.reset_log
        assert comparison(update) == expected(current, saved, live, old)
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.attachment_id,
            owner.owner.retained_segment(),
            inventory(tmp_path),
        ) == before
        retry = owner.retry()
        assert not comparison(retry) and retry.view == update.view
        assert inventory(tmp_path) == before[-1]
    finally:
        owner.close()


def test_previous_future_rewind_and_restart_use_each_selected_branch(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.save("slot01")
        owner.act("wait", seconds=6)
        owner.save("slot01")
        owner.save("slot02")
        owner.act("wait", seconds=2)
        assert comparison(owner.inspect_slot("slot01", previous=True)) == expected(
            10, 2, OPEN, ZERO
        )
        owner.load("slot01", previous=True)
        before = inventory(tmp_path)
        update = owner.inspect_slot("slot02")
        assert comparison(update) == expected(2, 8, ZERO, READY)
        assert inventory(tmp_path) == before
        path = owner.owner.working_path
    finally:
        owner.close()
    owner = session(path)
    try:
        assert comparison(owner.inspect_slot("slot02")) == expected(2, 8, ZERO, READY)
    finally:
        owner.close()


def test_saved_completion_is_not_replaced_by_unreported_live_branch(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.save("slot01")
        owner.act("wait", seconds=8)
        for action in ("right", "down", "attack", "attack", "rest", "attack", "up", "left", "talk"):
            assert owner.act(action).status == "COMMITTED"
        owner.save("slot02")
        owner.load("slot01")
        assert comparison(owner.inspect_slot("slot02")) == expected(2, 19, ZERO, FINISHED)
    finally:
        owner.close()


def test_logged_projection_error_preserves_live_slot_and_retry_then_recovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.save("slot01")
        owner.act("wait", seconds=6)
        before = owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)

        def fail(*args: object, npc_call_aid: bool = False) -> tuple[str, ...]:
            raise SaveError("SAVE_INSPECT_FAILED", "projection source rejected")

        with monkeypatch.context() as patch:
            patch.setattr("app.client_session.support_slot_messages", fail)
            with pytest.raises(SaveError, match="SAVE_INSPECT_FAILED") as caught:
                owner.inspect_slot("slot01")
        assert caught.value.code == "SAVE_INSPECT_FAILED"
        assert "NPC support slot plan comparison failed" in caplog.text
        assert (owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)) == before
        assert not comparison(owner.retry()) and inventory(tmp_path) == before[-1]
        assert comparison(owner.inspect_slot("slot01")) == expected(8, 2, READY, ZERO)
    finally:
        owner.close()


def test_real_worker_error_retains_view_and_allows_next_query_and_action(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selected = approved_content()
    worker = ClientWorker(
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
    )
    try:
        worker.request("attach").result(timeout=30)
        worker.request("down").result(timeout=30)
        worker.request("talk").result(timeout=30)
        worker.request("save").result(timeout=30)
        live = worker.request("wait", seconds=6).result(timeout=30)
        before = inventory(tmp_path)

        def fail(*args: object, npc_call_aid: bool = False) -> tuple[str, ...]:
            raise SaveError("SAVE_INSPECT_FAILED", "projection source rejected")

        with monkeypatch.context() as patch:
            patch.setattr("app.client_session.support_slot_messages", fail)
            update = worker.inspect_slot().result(timeout=30)
        assert update.status == "SAVE_INSPECT_FAILED" and update.view == live.view
        assert inventory(tmp_path) == before
        update = worker.inspect_slot().result(timeout=30)
        assert comparison(update) == expected(8, 2, READY, ZERO) and update.view == live.view
        assert worker.request("wait").result(timeout=30).status == "COMMITTED"
    finally:
        worker.close().result(timeout=30)
        worker.join()


def test_actual_framed_slot_query_and_previous_restore(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with supply_pipe(path) as pipe:
        pipe.send("down")
        pipe.send("talk")
        pipe.send("save")
        for _ in range(6):
            pipe.send("wait")
        before = path.read_bytes()
        response = pipe.send("slot_inspect")
        lines = tuple(
            text_value(x) for x in array_value(object_value(response["update"])["messages"])
        )
        assert lines[-3:] == expected(8, 2, READY, ZERO) and response["error"] == ""
        assert path.read_bytes() == before
        pipe.send("save")
        response = pipe.send("slot_previous_inspect")
        lines = tuple(
            text_value(x) for x in array_value(object_value(response["update"])["messages"])
        )
        assert lines[-3:] == expected(8, 2, READY, ZERO)
        loaded = object_value(pipe.send("load_previous")["update"])
        path = Path(text_value(loaded["working_path"]))
    with supply_pipe(path) as pipe:
        response = pipe.send("slot_inspect")
        lines = tuple(
            text_value(x) for x in array_value(object_value(response["update"])["messages"])
        )
        assert lines[-3:] == expected(2, 8, ZERO, READY)


def test_actual_hidden_tk_preview_displays_comparison_without_changing_view(
    tk_host: tk.Tk, tmp_path: Path
) -> None:
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
        for action in ("down", "talk", "save", *("wait",) * 6):
            _click(screen, action)
        assert screen.last_update is not None
        view = screen.last_update.view
        before = inventory(tmp_path)
        screen.slot_preview_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None and screen.last_update.view == view
        assert comparison(screen.last_update) == expected(8, 2, READY, ZERO)
        assert inventory(tmp_path) == before
        assert all(
            line in screen.log_text.get("1.0", "end") for line in expected(8, 2, READY, ZERO)
        )
        _click(screen, "load")
        screen.slot_preview_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None
        assert comparison(screen.last_update) == expected(2, 2, ZERO, ZERO)
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
