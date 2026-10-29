"""Pending text describes the actual operation without publishing its result early."""

from collections.abc import Callable, Iterator
from concurrent.futures import Future
from pathlib import Path
from typing import cast
import gc
import tkinter as tk
import pytest

from app.client import PlayWindow
from contracts.client import ClientUpdate
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_reach_gate_aid import FLAGS
from tests.integration.test_memory_client_route import approved_content


@pytest.fixture
def window(tmp_path: Path, tk_host: tk.Tk) -> Iterator[PlayWindow]:
    gc.collect()
    content = approved_content()
    panel = tk.Toplevel(tk_host)
    panel.withdraw()
    screen = PlayWindow(
        panel,
        tmp_path / "game.sqlite",
        content.definition.layout,
        quest_content=content,
        **FLAGS,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        _click(screen, "down")
        _click(screen, "talk")
        _click(screen, "save")
        yield screen
    finally:
        if screen._pending is not None and not screen._pending.done():
            screen._pending.cancel()
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: screen.closed)


@pytest.mark.parametrize(
    "kind,expected,status",
    (
        ("talk", "대화 결과를 확인하는 중입니다.", "COMMITTED"),
        ("wait", "처리 중…", "COMMITTED"),
        (
            "activity",
            "NPC 활동 기록을 확인하는 중입니다. 게임 시간은 흐르지 않습니다.",
            "ACTIVITY_INSPECTED",
        ),
        (
            "memory",
            "NPC 대화 기억을 확인하는 중입니다. 게임 시간은 흐르지 않습니다.",
            "MEMORY_INSPECTED",
        ),
        (
            "recent_memory",
            "최근 NPC 대화 기억을 확인하는 중입니다. 게임 시간은 흐르지 않습니다.",
            "MEMORY_INSPECTED",
        ),
        ("slot", "저장 슬롯 정보를 확인하는 중입니다. 현재 진행은 유지됩니다.", "SLOT_INSPECTED"),
    ),
)
def test_actual_pending_callback_keeps_result_private_until_delivery(
    window: PlayWindow,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    expected: str,
    status: str,
) -> None:
    previous = window.last_update
    assert previous is not None and previous.view is not None
    path = Path(previous.working_path)
    raw, history = path.read_bytes(), tuple(window.history)
    gate: Future[ClientUpdate] = Future()
    actual: list[Future[ClientUpdate]] = []
    name = "request" if kind in ("talk", "wait") else "inspect_" + kind
    request = window.worker.request
    inspect_slot = window.worker.inspect_slot
    operations: dict[str, Callable[[], Future[ClientUpdate]]] = {
        "talk": lambda: request("talk"),
        "wait": lambda: request("wait"),
        "activity": window.worker.inspect_activity,
        "memory": window.worker.inspect_memory,
        "recent_memory": window.worker.inspect_recent_memory,
        "slot": lambda: inspect_slot(window.slot.get()),
    }
    real = operations[kind]

    def delayed(*args: object, **kwargs: object) -> Future[ClientUpdate]:
        actual.append(real())
        return gate

    with monkeypatch.context() as patch:
        patch.setattr(window.worker, name, delayed)
        if kind in ("talk", "wait"):
            window._send("talk" if kind == "talk" else "wait")
        else:
            cast(Callable[[], None], getattr(window, "_inspect_" + kind))()
        assert window.status_text.get() == window.status.get() == expected
        assert window.busy and window._pending is gate
        assert window.last_update is previous and tuple(window.history) == history
        assert all(button.instate(["disabled"]) for button in window.buttons.values())
        window._send("wait")
        window._inspect_activity()
        assert window._pending is gate and len(actual) == 1
    result = actual[0].result(timeout=15)
    assert result.status == status and result.view is not None
    assert result.view.tick == previous.view.tick + (1 if kind in ("talk", "wait") else 0)
    if kind not in ("talk", "wait"):
        assert path.read_bytes() == raw
    gate.set_result(result)
    _pump(window.root, lambda: not window.busy)
    assert window.last_update is result and window.view == result.view
    assert window.status.get() == status and window.status_text.get() != expected
    assert all(button.instate(["!disabled"]) for button in window.buttons.values())


@pytest.mark.parametrize("cancelled", (False, True))
def test_pending_query_error_or_cancellation_restores_input_and_poll(
    window: PlayWindow,
    cancelled: bool,
    caplog: pytest.LogCaptureFixture,
) -> None:
    previous = window.last_update
    assert previous is not None
    raw = Path(previous.working_path).read_bytes()
    gate: Future[ClientUpdate] = Future()
    window._begin_request(gate, message="NPC 활동 기록을 확인하는 중입니다.")
    if cancelled:
        assert gate.cancel()
    else:
        gate.set_exception(OSError("delivery unavailable"))
    _pump(window.root, lambda: not window.busy)
    assert window.status.get() == "CLIENT_ERROR" and window.view == previous.view
    assert Path(previous.working_path).read_bytes() == raw
    assert "client request Future failed" in caplog.text
    window._inspect_activity()
    _pump(window.root, lambda: not window.busy)
    assert window.status.get() == "ACTIVITY_INSPECTED"
    _click(window, "wait")
    assert window.view is not None and previous.view is not None
    assert window.view.tick == previous.view.tick + 1
