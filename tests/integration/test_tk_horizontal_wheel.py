"""Drive horizontal scrolling through real Tk events and existing save controls."""

from concurrent.futures import Future
from pathlib import Path
import time
import tkinter as tk
from tkinter import ttk

import pytest

from app.client import PlayWindow
from contracts.client import ClientUpdate
from tests.integration.test_client import _click, _pump, window as window, tk_host as tk_host
from tests.integration.test_tk_compact_viewport import _show, reach_window as reach_window


def narrow(screen: PlayWindow) -> None:
    _show(screen, 600)
    screen.root.geometry("600x600+10000+10000")
    screen.root.update()


@pytest.mark.parametrize("mode", ("basic", "reach"))
@pytest.mark.parametrize("delta", (-1, -120, -240, 120))
def test_shift_wheel_moves_only_horizontal_axis(
    request: pytest.FixtureRequest, mode: str, delta: int
) -> None:
    screen: PlayWindow = request.getfixturevalue("window" if mode == "basic" else "reach_window")
    narrow(screen)
    screen.play_viewport.xview_moveto(1 if delta > 0 else 0)
    screen.play_viewport.yview_moveto(0.5)
    screen.root.update()
    x, y = screen.play_viewport.xview(), screen.play_viewport.yview()
    before = screen.last_update
    assert before is not None
    raw, history = Path(before.working_path).read_bytes(), tuple(screen.history)
    screen.canvas.event_generate("<Shift-MouseWheel>", delta=delta)
    screen.root.update()
    after_x = screen.play_viewport.xview()[0]
    assert after_x < x[0] if delta > 0 else after_x > x[0]
    assert screen.play_viewport.yview() == y
    assert screen.last_update is before and tuple(screen.history) == history and not screen.busy
    assert Path(before.working_path).read_bytes() == raw


def test_ordinary_zero_and_clamped_wheels_leave_other_axis_alone(window: PlayWindow) -> None:
    narrow(window)
    viewport = window.play_viewport
    viewport.xview_moveto(0)
    viewport.yview_moveto(0)
    before = viewport.xview(), viewport.yview()
    window.canvas.event_generate("<Shift-MouseWheel>", delta=0)
    window.canvas.event_generate("<Shift-MouseWheel>", delta=120)
    window.root.update()
    assert (viewport.xview(), viewport.yview()) == before
    window.canvas.event_generate("<MouseWheel>", delta=-120)
    window.root.update()
    assert viewport.xview() == before[0] and viewport.yview()[0] > before[1][0]
    viewport.xview_moveto(1)
    right, y = viewport.xview(), viewport.yview()
    window.play_viewport.event_generate("<Shift-MouseWheel>", delta=-240)
    window.root.update()
    assert viewport.xview() == right and viewport.yview() == y


def test_inputs_history_and_other_window_keep_wheel_ownership(window: PlayWindow) -> None:
    narrow(window)
    window.play_viewport.xview_moveto(0.5)
    window.play_viewport.yview_moveto(0.5)
    window._append_messages(tuple(f"읽는 기록 {i}" for i in range(100)))
    window.log_text.yview("30.0")
    other = tk.Toplevel(window.root)
    label = ttk.Label(other, text="other window")
    label.pack()
    try:
        other.geometry("200x100+10000+10000")
        window.root.update()
        play = window.play_viewport.xview(), window.play_viewport.yview()
        for control in (window.wait_input, window.slot_input, window.log_text, label):
            control.event_generate("<Shift-MouseWheel>", delta=-120)
            window.root.update()
            assert (window.play_viewport.xview(), window.play_viewport.yview()) == play
        assert not window.busy
    finally:
        other.destroy()


def test_shift_navigation_then_real_previous_save_restore(window: PlayWindow) -> None:
    narrow(window)
    _click(window, "save")
    _click(window, "wait")
    _click(window, "save")
    before = window.last_update
    assert before is not None
    originals = {p: p.read_bytes() for p in Path(before.working_path).parent.rglob("*.sqlite")}
    window.play_viewport.xview_moveto(0)
    window.play_viewport.yview_moveto(1)
    for _ in range(20):
        window.canvas.event_generate("<Shift-MouseWheel>", delta=-120)
    window.root.update()
    target = window.buttons["load_previous"]
    assert target.winfo_rootx() >= window.play_viewport.winfo_rootx()
    assert target.winfo_rootx() + target.winfo_width() <= (
        window.play_viewport.winfo_rootx() + window.play_viewport.winfo_width()
    )
    window.previous_slot_preview_button.invoke()
    _pump(window.root, lambda: not window.busy)
    assert window.status.get() == "SLOT_INSPECTED" and window.view == before.view
    _click(window, "load_previous")
    assert window.status.get() == "LOADED" and window.view is not None and window.view.tick == 0
    assert window.last_update is not None and window.last_update.working_path != before.working_path
    assert all(p.read_bytes() == raw for p, raw in originals.items())


def test_wheel_burst_preserves_pending_failure_recovery_and_close(window: PlayWindow) -> None:
    narrow(window)
    before = window.last_update
    assert before is not None
    raw, history = Path(before.working_path).read_bytes(), tuple(window.history)
    gate: Future[ClientUpdate] = Future()
    window._begin_request(gate)
    window.canvas.focus_force()
    window.root.update()
    focus = window.root.focus_get()
    started = time.monotonic()
    for delta in (-120, 120) * 20:
        window.canvas.event_generate("<Shift-MouseWheel>", delta=delta)
        window.root.update()
    elapsed = time.monotonic() - started
    print(f"40 Shift-wheel callbacks: {elapsed:.6f}s")
    assert elapsed < 2
    assert window._pending is gate and window.last_update is before
    assert window.root.focus_get() is focus and tuple(window.history) == history
    assert Path(before.working_path).read_bytes() == raw
    gate.set_exception(OSError("horizontal wheel pending failure"))
    _pump(window.root, lambda: not window.busy)
    assert window.status.get() == "CLIENT_ERROR" and window.view == before.view
    _click(window, "wait")
    assert window.status.get() == "COMMITTED"
    window.close()
    _pump(window.root, lambda: window.closed)
