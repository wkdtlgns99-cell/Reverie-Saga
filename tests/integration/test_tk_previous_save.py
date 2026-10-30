"""Drive explicit previous-generation recovery through the actual Tk controls."""

from concurrent.futures import Future
from collections.abc import Callable
from pathlib import Path
import time

import pytest

from app.client import PlayWindow
from app.client_session import ClientSession
from contracts.client import ClientUpdate
from tests.integration.test_client import _click, _pump, window as window, tk_host as tk_host
from tests.integration import test_pending_query_feedback


reach_window = test_pending_query_feedback.window


def _previous_info(window: PlayWindow) -> None:
    window.previous_slot_preview_button.invoke()
    _pump(window.root, lambda: not window.busy)


@pytest.mark.parametrize("slot", ("slot01", "slot08"))
def test_selected_previous_recovers_corrupt_latest_without_replacing_sources(
    window: PlayWindow, slot: str
) -> None:
    window.slot.set(slot)
    _click(window, "wait")
    _click(window, "save")
    window.wait_seconds.set("2")
    _click(window, "wait")
    _click(window, "save")
    _click(window, "wait")
    before = window.last_update
    assert before is not None and before.view is not None and before.view.tick == 5
    working = Path(before.working_path)
    latest = working.parent / "slots" / f"{slot}.sqlite"
    previous = working.parent / "slots" / f"{slot}.previous.sqlite"
    latest.write_bytes(b"damaged-latest")
    sources = {p: p.read_bytes() for p in (working, latest, previous)}
    _click(window, "load")
    assert window.status.get() == "SAVE_CORRUPT" and window.view == before.view
    started = time.perf_counter()
    _previous_info(window)
    print(f"previous_preview_seconds={time.perf_counter() - started:.6f}")
    assert window.status.get() == "SLOT_INSPECTED" and window.view == before.view
    assert window.last_update is not None
    assert window.last_update.attachment_id == before.attachment_id
    assert window.last_update.working_path == before.working_path
    assert f"{slot} 이전 저장 정보 · 1초 · 진행 1" in window.last_update.messages
    assert all(p.read_bytes() == raw for p, raw in sources.items())
    started = time.perf_counter()
    _click(window, "load_previous")
    print(f"previous_load_seconds={time.perf_counter() - started:.6f}")
    loaded = window.last_update
    assert loaded is not None and loaded.view is not None
    assert loaded.status == "LOADED" and loaded.view.tick == 1 and loaded.reset_log
    assert loaded.attachment_id != before.attachment_id
    assert Path(loaded.working_path).name.startswith(".loaded-")
    assert loaded.working_path != before.working_path and window.slot.get() == slot
    assert len(window.history) == len(loaded.messages)
    assert all(line.startswith("[1초 · 턴 1] ") for line in window.history)
    assert any("이전 저장" in line for line in window.history)
    assert all(p.read_bytes() == raw for p, raw in sources.items())
    _click(window, "retry")
    assert window.status.get() == "NO_RETRY" and window.view == loaded.view
    _click(window, "wait")
    assert window.view is not None and window.view.tick == 3
    assert all(p.read_bytes() == raw for p, raw in sources.items())
    branch = Path(loaded.working_path)
    window.close()
    _pump(window.root, lambda: window.closed)
    window.worker.join()
    resumed = ClientSession(branch)
    try:
        assert resumed.update().view == window.view
        assert all(p.read_bytes() == raw for p, raw in sources.items())
    finally:
        resumed.close()


@pytest.mark.parametrize("corrupt", (False, True))
def test_missing_or_corrupt_previous_never_loads_latest(window: PlayWindow, corrupt: bool) -> None:
    _click(window, "save")
    if corrupt:
        _click(window, "wait")
        _click(window, "save")
    _click(window, "wait")
    before = window.last_update
    assert before is not None
    path = Path(before.working_path)
    previous = path.parent / "slots/slot01.previous.sqlite"
    if corrupt:
        previous.write_bytes(b"damaged-backup")
    sources = {p: p.read_bytes() for p in path.parent.rglob("*.sqlite")}
    expected = "SAVE_CORRUPT" if corrupt else "PREVIOUS_SAVE_NOT_FOUND"
    operations: tuple[Callable[[], None], ...] = (
        lambda: _previous_info(window),
        lambda: _click(window, "load_previous"),
    )
    for operation in operations:
        operation()
        assert window.status.get() == expected and window.view == before.view
        assert window.last_update is not None
        assert window.last_update.working_path == before.working_path
        assert window.last_update.attachment_id == before.attachment_id
        assert all(p.read_bytes() == raw for p, raw in sources.items())
        assert not tuple(path.parent.glob(".loaded-*.sqlite"))
    _click(window, "retry")
    assert window.status.get() == "COMMITTED" and window.view == before.view
    _click(window, "wait")
    assert window.status.get() == "COMMITTED"


@pytest.mark.parametrize("load", (False, True))
def test_pending_previous_operation_disables_controls_and_submits_once(
    window: PlayWindow, monkeypatch: pytest.MonkeyPatch, load: bool
) -> None:
    _click(window, "save")
    _click(window, "wait")
    _click(window, "save")
    previous = window.last_update
    assert previous is not None
    history = tuple(window.history)
    gate: Future[ClientUpdate] = Future()
    actual: list[Future[ClientUpdate]] = []
    request, inspect = window.worker.request, window.worker.inspect_previous_slot

    def delayed(*args: object, **kwargs: object) -> Future[ClientUpdate]:
        actual.append(
            request("load_previous", slot_id=window.slot.get())
            if load
            else inspect(window.slot.get())
        )
        return gate

    with monkeypatch.context() as patch:
        patch.setattr(window.worker, "request" if load else "inspect_previous_slot", delayed)
        if load:
            window.buttons["load_previous"].invoke()
        else:
            window.previous_slot_preview_button.invoke()
        expected = (
            "이전 저장을 별도 진행 파일로 불러오는 중입니다."
            if load
            else "이전 저장 정보를 확인하는 중입니다. 현재 진행은 유지됩니다."
        )
        assert window.status.get() == window.status_text.get() == expected
        assert window.busy and window.last_update is previous and tuple(window.history) == history
        assert window.previous_slot_preview_button.instate(["disabled"])
        assert all(button.instate(["disabled"]) for button in window.buttons.values())
        window._inspect_previous_slot()
        window._send("load_previous")
        window._send("wait")
        assert len(actual) == 1 and window._pending is gate
    result = actual[0].result(timeout=15)
    gate.set_result(result)
    _pump(window.root, lambda: not window.busy)
    assert window.last_update is result
    assert result.status == ("LOADED" if load else "SLOT_INSPECTED")
    assert window.previous_slot_preview_button.instate(["!disabled"])
    assert window.buttons["load_previous"].instate(["!disabled"])


@pytest.mark.parametrize("cancelled", (False, True))
def test_previous_preview_delivery_failure_keeps_input_and_close_alive(
    window: PlayWindow, monkeypatch: pytest.MonkeyPatch, cancelled: bool
) -> None:
    before = window.last_update
    assert before is not None
    raw = Path(before.working_path).read_bytes()
    gate: Future[ClientUpdate] = Future()
    with monkeypatch.context() as patch:
        patch.setattr(window.worker, "inspect_previous_slot", lambda slot: gate)
        window.previous_slot_preview_button.invoke()
    if cancelled:
        gate.cancel()
    else:
        gate.set_exception(OSError("previous-preview delivery failed"))
    _pump(window.root, lambda: not window.busy)
    assert window.status.get() == "CLIENT_ERROR" and window.view == before.view
    assert Path(before.working_path).read_bytes() == raw
    assert window.previous_slot_preview_button.instate(["!disabled"])
    _click(window, "wait")
    assert window.status.get() == "COMMITTED"
    window.close()
    assert window.previous_slot_preview_button.instate(["disabled"])
    assert window.buttons["load_previous"].instate(["disabled"])
    _pump(window.root, lambda: window.closed)


def test_reach_mode_previous_preview_uses_saved_support_state(reach_window: PlayWindow) -> None:
    window = reach_window
    _click(window, "wait")
    _click(window, "wait")
    _click(window, "save")
    before = window.last_update
    _previous_info(window)
    assert window.status.get() == "SLOT_INSPECTED" and window.last_update is not None
    assert before is not None and window.view == before.view
    assert "slot01 이전 저장 정보 · 2초 · 진행 2" in window.last_update.messages
    assert any(
        line.startswith("선택 저장 NPC 지원 계획 · ") for line in window.last_update.messages
    )
    _click(window, "load_previous")
    assert window.status.get() == "LOADED" and window.view is not None and window.view.tick == 2


def test_previous_controls_have_distinct_nonoverlapping_grid_cells(window: PlayWindow) -> None:
    preview = window.previous_slot_preview_button
    restore = window.buttons["load_previous"]
    window.root.update_idletasks()
    assert preview.cget("text") == "이전 저장 정보"
    assert restore.cget("text") == "이전 저장 불러오기"
    preview_grid, restore_grid = preview.grid_info(), restore.grid_info()
    assert preview_grid["row"] == restore_grid["row"]
    assert preview_grid["column"] != restore_grid["column"]
    assert int(preview_grid["row"]) > int(window.slot_preview_button.grid_info()["row"])
    assert preview.winfo_x() + preview.winfo_width() <= restore.winfo_x()
