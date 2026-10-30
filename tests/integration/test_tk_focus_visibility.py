"""Keyboard focus reveals real scrollable controls without submitting commands."""

from pathlib import Path
from concurrent.futures import Future
import time
import tkinter as tk
from tkinter import ttk
import pytest

from app.client import PlayWindow
from contracts.client import ClientUpdate
from tests.integration.test_client import _click, _pump, window as window, tk_host as tk_host
from tests.integration.test_tk_compact_viewport import _show, _inside, reach_window as reach_window


def inside(widget: tk.Misc, container: tk.Misc) -> bool:
    return (
        _inside(widget, container)
        and widget.winfo_rootx() >= container.winfo_rootx()
        and widget.winfo_rootx() + widget.winfo_width()
        <= container.winfo_rootx() + container.winfo_width()
    )


@pytest.mark.parametrize("mode", ("basic", "reach"))
@pytest.mark.parametrize("height", (600, 768))
def test_focus_reveals_previous_load_and_preserves_committed_state(
    request: pytest.FixtureRequest, mode: str, height: int
) -> None:
    screen: PlayWindow = request.getfixturevalue("window" if mode == "basic" else "reach_window")
    _show(screen, height)
    screen.play_viewport.yview_moveto(0)
    screen.play_viewport.xview_moveto(0)
    screen.root.update()
    button = screen.buttons["load_previous"]
    assert not inside(button, screen.play_viewport)
    before = screen.last_update
    assert before is not None
    raw, history = Path(before.working_path).read_bytes(), tuple(screen.history)
    button.focus_force()
    screen.root.update()
    assert screen.root.focus_get() is button
    assert inside(button, screen.play_viewport)
    assert screen.last_update is before and tuple(screen.history) == history
    assert Path(before.working_path).read_bytes() == raw and not screen.busy


def test_real_tab_reverse_tab_and_previous_save_recovery(window: PlayWindow) -> None:
    _show(window, 600)
    _click(window, "save")
    _click(window, "wait")
    _click(window, "save")
    before = window.last_update
    assert before is not None
    path = Path(before.working_path)
    originals = {p: p.read_bytes() for p in path.parent.rglob("*.sqlite")}
    preview = window.previous_slot_preview_button
    preview.focus_force()
    window.root.update()
    preview.event_generate("<Tab>")
    window.root.update()
    target = window.buttons["load_previous"]
    assert window.root.focus_get() is target and inside(target, window.play_viewport)
    target.event_generate("<Shift-Tab>")
    window.root.update()
    assert window.root.focus_get() is preview and inside(preview, window.play_viewport)
    preview.invoke()
    _pump(window.root, lambda: not window.busy)
    assert window.status.get() == "SLOT_INSPECTED" and window.view == before.view
    preview.event_generate("<Tab>")
    window.root.update()
    assert window.root.focus_get() is target
    target.event_generate("<KeyPress-space>")
    target.event_generate("<KeyRelease-space>")
    _pump(window.root, lambda: window.status.get() == "LOADED" and not window.busy)
    assert window.view is not None and window.view.tick == 0
    assert window.last_update is not None and window.last_update.working_path != str(path)
    assert all(p.read_bytes() == raw for p, raw in originals.items())


def test_focus_reveals_both_axes_and_returns_to_upper_control(window: PlayWindow) -> None:
    _show(window, 600)
    window.root.geometry("600x600")
    window.root.update()
    lower = window.buttons["load_previous"]
    lower.focus_force()
    window.root.update()
    assert inside(lower, window.play_viewport)
    assert window.play_viewport.xview()[0] > 0 and window.play_viewport.yview()[0] > 0
    upper = window.buttons["up"]
    upper.focus_force()
    window.root.update()
    assert inside(upper, window.play_viewport)
    assert not window.busy


def test_visible_focus_does_not_jump_or_steal_history_reading_position(window: PlayWindow) -> None:
    _show(window, 600)
    target = window.buttons["load_previous"]
    target.focus_force()
    window.root.update()
    play = window.play_viewport.xview(), window.play_viewport.yview()
    window._append_messages(tuple(f"기록 {index}" for index in range(100)))
    window.log_text.yview("30.0")
    window.log_text.focus_force()
    window.root.update()
    history_y = window.log_text.yview()
    assert (window.play_viewport.xview(), window.play_viewport.yview()) == play
    target.focus_force()
    window.root.update()
    assert (window.play_viewport.xview(), window.play_viewport.yview()) == play
    assert window.log_text.yview() == history_y and window.root.focus_get() is target


def test_other_window_and_unmapped_control_do_not_scroll(window: PlayWindow) -> None:
    _show(window, 600)
    target = window.buttons["load_previous"]
    target.focus_force()
    window.root.update()
    play = window.play_viewport.xview(), window.play_viewport.yview()
    other = tk.Toplevel(window.root)
    try:
        entry = ttk.Entry(other)
        entry.pack()
        other.geometry("200x100+10000+10000")
        other.update()
        entry.focus_force()
        other.update()
        assert (window.play_viewport.xview(), window.play_viewport.yview()) == play
        upper = window.buttons["up"]
        upper.grid_remove()
        upper.event_generate("<FocusIn>")
        window.root.update()
        assert (window.play_viewport.xview(), window.play_viewport.yview()) == play
    finally:
        other.destroy()


def test_oversized_focus_keeps_leading_edge_visible(window: PlayWindow) -> None:
    _show(window, 600)
    target = ttk.Entry(window.play_content, width=200)
    target.grid(row=1, column=0, columnspan=2)
    window.root.update()
    window.play_viewport.xview_moveto(1)
    target.focus_force()
    window.root.update()
    assert target.winfo_width() > window.play_viewport.winfo_width()
    assert target.winfo_rootx() == window.play_viewport.winfo_rootx()
    assert _inside(target, window.play_viewport)


def test_focus_preserves_entry_input_pending_error_recovery_and_close(window: PlayWindow) -> None:
    _show(window, 600)
    window.wait_input.focus_force()
    window.root.update()
    assert inside(window.wait_input, window.play_viewport)
    window.wait_seconds.set("12")
    window.wait_input.icursor("end")
    window.wait_input.event_generate("<KeyPress-a>")
    window.root.update()
    assert not window.busy and window.wait_seconds.get() == "12a"
    before = window.last_update
    assert before is not None
    raw = Path(before.working_path).read_bytes()
    gate: Future[ClientUpdate] = Future()
    window._begin_request(gate)
    window.canvas.focus_force()
    window.root.update()
    assert window._pending is gate and window.last_update is before
    gate.set_exception(OSError("focused operation failure"))
    _pump(window.root, lambda: not window.busy)
    assert window.status.get() == "CLIENT_ERROR" and Path(before.working_path).read_bytes() == raw
    window.wait_seconds.set("1")
    _click(window, "wait")
    assert window.view is not None and before.view is not None
    assert window.view.tick == before.view.tick + 1
    window.close()
    window.root.event_generate("<FocusIn>")
    _pump(window.root, lambda: window.closed)


def test_repeated_focus_is_presentation_only(window: PlayWindow) -> None:
    _show(window, 600)
    before = window.last_update
    assert before is not None
    raw, history = Path(before.working_path).read_bytes(), tuple(window.history)
    started = time.perf_counter()
    for _ in range(20):
        for target in (window.buttons["load_previous"], window.buttons["up"]):
            target.focus_force()
            window.root.update()
            assert inside(target, window.play_viewport)
    print(f"forty_native_focus_updates_seconds={time.perf_counter() - started:.6f}")
    assert window.last_update is before and tuple(window.history) == history and not window.busy
    assert Path(before.working_path).read_bytes() == raw
