"""Exercise native modifier delivery through the real Tk/worker input boundary."""

from concurrent.futures import Future
from pathlib import Path
import time

import pytest

from app.client import PlayWindow
from contracts.client import ClientUpdate
from tests.integration.test_client import _click, _pump, window as window, tk_host as tk_host
from tests.integration.test_tk_compact_viewport import _show, reach_window as reach_window


def focus_map(screen: PlayWindow) -> None:
    _show(screen, 768)
    screen.canvas.focus_force()
    screen.root.update()
    assert screen.root.focus_get() is screen.canvas


@pytest.mark.parametrize("mode", ("basic", "reach"))
@pytest.mark.parametrize("chord", ("Control-s", "Control-Right", "Alt-s", "Alt-Right"))
def test_shortcut_chords_never_issue_movement(
    request: pytest.FixtureRequest, mode: str, chord: str
) -> None:
    screen: PlayWindow = request.getfixturevalue("window" if mode == "basic" else "reach_window")
    focus_map(screen)
    seen: list[tuple[str, int | str]] = []
    screen.canvas.bind(
        "<KeyPress>", lambda event: seen.append((event.keysym, event.state)), add="+"
    )
    before = screen.last_update
    assert before is not None
    raw, history = Path(before.working_path).read_bytes(), tuple(screen.history)
    screen.canvas.event_generate(f"<{chord}>")
    screen.root.update()
    assert len(seen) == 1
    print(f"{mode}/{chord}: native key/state={seen[0]}")
    assert screen._pending is None and screen.last_update is before
    assert tuple(screen.history) == history and screen.root.focus_get() is screen.canvas
    assert Path(before.working_path).read_bytes() == raw


@pytest.mark.parametrize("state", (1, 2))
@pytest.mark.parametrize("key,cell", (("W", 4), ("S", 7), ("A", 3), ("D", 5)))
def test_uppercase_wasd_uses_existing_moves(
    window: PlayWindow, state: int, key: str, cell: int
) -> None:
    _click(window, "down")
    _click(window, "open")
    _click(window, "right")
    assert window.view is not None and (window.view.actor_cell, window.view.tick) == (4, 3)
    focus_map(window)
    seen: list[tuple[str, int | str]] = []
    window.canvas.bind(
        "<KeyPress>", lambda event: seen.append((event.keysym, event.state)), add="+"
    )
    window.canvas.event_generate("<KeyPress>", keysym=key, state=state)
    window.root.update()
    assert len(seen) == 1 and seen[0][0] == key
    assert isinstance(seen[0][1], int) and seen[0][1] & state
    print(f"{key}/{state}: native key/state={seen[0]}")
    _pump(window.root, lambda: not window.busy)
    assert window.status.get() == "COMMITTED"
    assert window.view is not None
    assert (window.view.actor_cell, window.view.tick, window.view.revision) == (cell, 4, 4)


def test_ordinary_numlock_arrows_retry_save_and_load(window: PlayWindow) -> None:
    focus_map(window)
    window.canvas.event_generate("<KeyPress-s>", state=0x10)
    _pump(window.root, lambda: not window.busy)
    assert window.view is not None and (window.view.actor_cell, window.view.tick) == (3, 1)
    _click(window, "retry")
    assert (window.view.actor_cell, window.view.tick) == (3, 1)
    _click(window, "save")
    saved = window.last_update
    assert saved is not None
    # Locate the actual exported generation without assuming the worker's directory layout.
    working = Path(saved.working_path)
    sources = {p: p.read_bytes() for p in working.parent.rglob("*.sqlite") if p != working}
    assert sources
    window.canvas.event_generate("<KeyPress-Up>")
    _pump(window.root, lambda: not window.busy)
    assert window.view.actor_cell == 0 and window.view.tick == 2
    _click(window, "load")
    assert window.status.get() == "LOADED" and window.view == saved.view
    assert (
        window.last_update is not None and window.last_update.attachment_id != saved.attachment_id
    )
    assert all(p.read_bytes() == raw for p, raw in sources.items())


def test_entry_slot_history_and_modified_uppercase_keep_ownership(window: PlayWindow) -> None:
    focus_map(window)
    before = window.last_update
    assert before is not None
    raw = Path(before.working_path).read_bytes()
    window.wait_input.focus_force()
    window.root.update()
    window.wait_seconds.set("1")
    window.wait_input.icursor("end")
    window.wait_input.event_generate("<KeyPress-D>")
    window.root.update()
    assert window.wait_seconds.get() == "1D"
    for widget in (window.wait_input, window.slot_input, window.log_text):
        widget.focus_force()
        window.root.update()
        widget.event_generate("<Control-KeyPress-s>")
        window.root.update()
        assert window._pending is None and window.last_update is before
    window.canvas.focus_force()
    window.root.update()
    for chord in ("Control-Shift-S", "Alt-Shift-D", "Escape", "F8"):
        window.canvas.event_generate(f"<{chord}>")
        window.root.update()
        assert window._pending is None and window.last_update is before
    assert Path(before.working_path).read_bytes() == raw


def test_shortcut_burst_pending_error_next_move_and_close(window: PlayWindow) -> None:
    focus_map(window)
    before = window.last_update
    assert before is not None
    raw, history = Path(before.working_path).read_bytes(), tuple(window.history)
    started = time.monotonic()
    for chord in ("Control-s", "Alt-Down") * 20:
        window.canvas.event_generate(f"<{chord}>")
        window.root.update()
    elapsed = time.monotonic() - started
    print(f"40 ignored shortcut chords: {elapsed:.6f}s")
    assert elapsed < 2 and window._pending is None and window.last_update is before
    assert tuple(window.history) == history and Path(before.working_path).read_bytes() == raw
    gate: Future[ClientUpdate] = Future()
    window._begin_request(gate)
    window.canvas.event_generate("<KeyPress-S>")
    window.root.update()
    assert window._pending is gate and window.last_update is before
    gate.set_exception(OSError("keyboard pending failure"))
    _pump(window.root, lambda: not window.busy)
    assert window.status.get() == "CLIENT_ERROR" and window.view == before.view
    window.canvas.event_generate("<KeyPress-S>")
    _pump(window.root, lambda: not window.busy)
    assert window.view is not None and (window.view.actor_cell, window.view.tick) == (3, 1)
    window.close()
    _pump(window.root, lambda: window.closed)
