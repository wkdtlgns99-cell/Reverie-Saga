"""Measure compact Tk geometry and drive scrolling through real widgets."""

from concurrent.futures import Future
from pathlib import Path
import tkinter as tk
from tkinter import ttk

import pytest

from app.client import PlayWindow
from contracts.client import ClientUpdate
from tests.integration.test_client import _click, _pump, window as window, tk_host as tk_host
from tests.integration import test_pending_query_feedback


reach_window = test_pending_query_feedback.window


def _show(window: PlayWindow, height: int) -> None:
    window.root.maxsize(2000, 2000)
    window.root.geometry(f"900x{height}+10000+10000")
    window.root.deiconify()
    window.root.update()


def _inside(widget: tk.Misc, container: tk.Misc) -> bool:
    return (
        widget.winfo_ismapped()
        and widget.winfo_rooty() >= container.winfo_rooty()
        and widget.winfo_rooty() + widget.winfo_height()
        <= container.winfo_rooty() + container.winfo_height()
    )


@pytest.mark.parametrize("mode", ("basic", "reach"))
@pytest.mark.parametrize("height", (600, 768))
def test_compact_history_status_and_path_are_inside_the_client(
    request: pytest.FixtureRequest, mode: str, height: int
) -> None:
    screen: PlayWindow = request.getfixturevalue("window" if mode == "basic" else "reach_window")
    _show(screen, height)
    print(
        f"{mode}/{height}: history_y={screen.log_text.winfo_rooty() - screen.root.winfo_rooty()} "
        f"height={screen.log_text.winfo_height()}"
    )
    assert screen.log_text.winfo_height() >= 60
    assert _inside(screen.log_text, screen.root)
    log_panel = screen.log_text.master
    assert log_panel is not None and log_panel.master is not None
    labels = [child for child in log_panel.master.winfo_children() if isinstance(child, ttk.Label)]
    for variable in (screen.status_text, screen.path_text):
        label = next(child for child in labels if str(child.cget("textvariable")) == str(variable))
        assert _inside(label, screen.root)


def test_scrolled_controls_restore_previous_save_and_keep_source_bytes(window: PlayWindow) -> None:
    _show(window, 600)
    _click(window, "save")
    _click(window, "wait")
    _click(window, "save")
    before = window.last_update
    assert before is not None
    path = Path(before.working_path)
    originals = {p: p.read_bytes() for p in path.parent.rglob("*.sqlite")}
    for scrollbar in (window.play_vertical_scrollbar, window.play_horizontal_scrollbar):
        scrollbar.tk.call(*scrollbar.tk.splitlist(scrollbar.cget("command")), "moveto", 1)
    window.root.update()
    button = window.buttons["load_previous"]
    assert _inside(button, window.play_viewport)
    assert button.winfo_rootx() >= window.play_viewport.winfo_rootx()
    assert (
        button.winfo_rootx() + button.winfo_width()
        <= window.play_viewport.winfo_rootx() + window.play_viewport.winfo_width()
    )
    window.previous_slot_preview_button.invoke()
    _pump(window.root, lambda: not window.busy)
    assert window.status.get() == "SLOT_INSPECTED" and window.view == before.view
    assert all(p.read_bytes() == data for p, data in originals.items())
    _click(window, "load_previous")
    assert window.status.get() == "LOADED" and window.view is not None and window.view.tick == 0
    assert _inside(window.log_text, window.root)
    assert all(p.read_bytes() == data for p, data in originals.items())


def test_play_and_history_wheels_are_local_and_readonly(window: PlayWindow) -> None:
    _show(window, 600)
    window._append_messages(tuple(f"읽는 기록 {i}" for i in range(100)))
    window.log_text.yview("30.0")
    window.play_viewport.yview_moveto(0)
    window.root.update()
    before = window.last_update
    assert before is not None
    raw = Path(before.working_path).read_bytes()
    history = tuple(window.history)
    log_y = window.log_text.yview()
    window.canvas.event_generate("<MouseWheel>", delta=-120)
    window.root.update()
    assert window.play_viewport.yview()[0] > 0
    assert window.log_text.yview() == log_y
    play_y = window.play_viewport.yview()
    window.log_text.event_generate("<MouseWheel>", delta=-120)
    window.root.update()
    assert window.log_text.yview() != log_y
    assert window.play_viewport.yview() == play_y
    assert window.last_update is before and tuple(window.history) == history
    assert Path(before.working_path).read_bytes() == raw


@pytest.mark.parametrize("widget", ("wait_input", "slot_input"))
def test_input_wheels_do_not_scroll_the_play_region(window: PlayWindow, widget: str) -> None:
    _show(window, 600)
    window.play_viewport.yview_moveto(0.5)
    window.root.update()
    before = window.play_viewport.yview()
    control: tk.Misc = getattr(window, widget)
    control.event_generate("<MouseWheel>", delta=-120)
    window.root.update()
    assert window.play_viewport.yview() == before and window._pending is None


@pytest.mark.parametrize("delta", (0, -1, -240))
def test_zero_and_subnotch_wheels_preserve_committed_state(window: PlayWindow, delta: int) -> None:
    _show(window, 600)
    window.play_viewport.yview_moveto(0)
    before = window.last_update
    assert before is not None
    raw = Path(before.working_path).read_bytes()
    window.canvas.event_generate("<MouseWheel>", delta=delta)
    window.root.update()
    assert (window.play_viewport.yview()[0] > 0) == (delta < 0)
    assert window.last_update is before and Path(before.working_path).read_bytes() == raw


def test_resize_and_scroll_preserve_pending_result_and_close(window: PlayWindow) -> None:
    _show(window, 600)
    before = window.last_update
    assert before is not None
    raw = Path(before.working_path).read_bytes()
    gate: Future[ClientUpdate] = Future()
    window._begin_request(gate)
    for height in (768, 600):
        window.root.geometry(f"900x{height}")
        window.play_viewport.yview_moveto(1)
        window.root.update()
        assert _inside(window.log_text, window.root)
        assert window._pending is gate and window.last_update is before
        assert all(button.instate(["disabled"]) for button in window.buttons.values())
    gate.set_exception(OSError("viewport pending failure"))
    _pump(window.root, lambda: not window.busy)
    assert window.status.get() == "CLIENT_ERROR" and window.view == before.view
    assert Path(before.working_path).read_bytes() == raw
    _click(window, "wait")
    assert window.status.get() == "COMMITTED"
    window.close()
    _pump(window.root, lambda: window.closed)
