"""Actual Tk map selection over the shared,unchanged development world."""

from collections.abc import Iterator
from pathlib import Path
import gc
import tkinter as tk
import time

import pytest

from app.world_catalog import DEVELOPMENT_WORLD, load_world
from app.world_client import WorldMapWindow, launch_world
from app.world_worker import WorldWorker
from adapters.sqlite_store import SqliteCommitStore
from contracts.persistence import DurableTurn, RecoveryResult
from contracts.persistence import SaveError
from contracts.turn import CommitReceipt


@pytest.fixture
def root() -> Iterator[tk.Tk]:
    window = tk.Tk()
    try:
        yield window
    finally:
        window.destroy()
        gc.collect()


def test_actual_world_map_has_all_cities_routes_and_regional_details(root: tk.Tk) -> None:
    before = DEVELOPMENT_WORLD.read_bytes()
    window = WorldMapWindow(root, load_world())
    root.update()
    assert len(window.map.canvas.find_withtag("continent")) == 6
    assert len(window.map.canvas.find_withtag("city")) == 12
    assert len(window.map.canvas.find_withtag("route")) == 12
    for place in window.catalog.places:
        window.map.select_place(place.id)
        root.update()
        assert window.map.selected == place.id
        assert place.name in window.details.get()
        country = next(c for c in window.catalog.countries if c.id == place.country_id)
        assert country.export in window.details.get()
        assert country.need in window.details.get()
    assert DEVELOPMENT_WORLD.read_bytes() == before


def test_actual_canvas_click_selects_city_without_travel(root: tk.Tk) -> None:
    window = WorldMapWindow(root, load_world())
    root.update()
    target = "place:p3-b"
    x, y = window.map.positions[target]
    window.map.canvas.event_generate("<Motion>", x=int(x), y=int(y))
    root.update()
    window.map.canvas.event_generate("<Button-1>", x=int(x), y=int(y))
    root.update()
    assert window.map.selected == target
    assert window.catalog.place(target).name in window.details.get()


def test_invalid_world_file_startup_has_explicit_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "broken.json"
    path.write_bytes(b"{}")
    assert launch_world(path) == 2
    assert "세계를 불러오지 못했습니다" in capsys.readouterr().err
    assert path.read_bytes() == b"{}"


def test_world_mode_does_not_silently_ignore_legacy_options() -> None:
    from app.client import main

    with pytest.raises(SystemExit, match="2"):
        main(["--world", "--npc-memory"])


def _settle(root: tk.Tk, window: WorldMapWindow) -> None:
    deadline = time.monotonic() + 10
    while window.pending is not None and time.monotonic() < deadline:
        root.update()
        time.sleep(0.005)
    assert window.pending is None, "world UI request did not settle"


def test_actual_gui_walk_save_load_restart_and_error_recovery(root: tk.Tk, tmp_path: Path) -> None:
    path = tmp_path / "world.sqlite"
    worker = WorldWorker(path, load_world())
    try:
        window = WorldMapWindow(root, load_world(), worker)
        _settle(root, window)
        assert window.update is not None
        assert window.update.tick == 0
        window.buttons[3].invoke()  # Missing slot must not stop polling or future commands.
        _settle(root, window)
        assert "처리하지 못했습니다" in window.status.get()
        window.buttons[0].invoke()
        _settle(root, window)
        assert window.update is not None
        assert (window.update.state.offset_m, window.update.tick) == (1, 1)
        assert "1m" in window.status.get()
        assert len(window.road.find_withtag("player")) == 1
        window.buttons[2].invoke()
        _settle(root, window)
        window.buttons[0].invoke()
        _settle(root, window)
        assert window.update.state.offset_m == 2
        window.buttons[3].invoke()
        _settle(root, window)
        assert (window.update.state.offset_m, window.update.tick) == (1, 1)
        # Inspecting an unrelated map city must not move the player.
        window.map.select_place("place:p5-a")
        assert window.update.state.place_id == "place:p0-a"
        window.buttons[1].invoke()
        _settle(root, window)
        assert window.update.state.offset_m == 0
        assert window.update.tick == 2
        window.road.focus_force()
        root.update()
        window.road.event_generate("<KeyPress-Right>")
        _settle(root, window)
        assert (window.update.state.offset_m, window.update.tick) == (1, 3)
        window.road.event_generate("<KeyPress-Left>", state=0x0004)
        root.update()
        assert window.pending is None
        assert (window.update.state.offset_m, window.update.tick) == (1, 3)
    finally:
        worker.close()


def test_actual_worker_restart_keeps_midroute_position(tmp_path: Path) -> None:
    path = tmp_path / "world.sqlite"
    worker = WorldWorker(path, load_world())
    try:
        result = worker.request("walk", "place:p0-b").result(timeout=10)
        assert result.state.offset_m == 1
    finally:
        worker.close()
    resumed = WorldWorker(path, load_world())
    try:
        restored = resumed.request("inspect").result(timeout=10)
        assert restored.state == result.state
        assert restored.tick == result.tick
    finally:
        resumed.close()


def test_actual_worker_restart_after_slot_load_follows_loaded_progress(tmp_path: Path) -> None:
    path = tmp_path / "world.sqlite"
    worker = WorldWorker(path, load_world())
    try:
        worker.request("walk", "place:p0-b").result(timeout=10)
        worker.request("save").result(timeout=10)
        worker.request("walk", "place:p0-b").result(timeout=10)
        worker.request("load").result(timeout=10)
        # Returning to the city distinguishes loaded progress from the pre-load file.
        expected = worker.request("walk", "place:p0-b", -1).result(timeout=10)
        assert expected.state.offset_m == 0
    finally:
        worker.close()
    resumed = WorldWorker(path, load_world())
    try:
        actual = resumed.request("inspect").result(timeout=10)
        assert (actual.state, actual.tick) == (expected.state, expected.tick)
    finally:
        resumed.close()


def test_real_gui_idle_pause_map_provider_wait_and_action_accounting(
    root: tk.Tk, tmp_path: Path
) -> None:
    sample = [0]

    def now() -> int:
        return sample[0] * 1_000_000_000

    worker = WorldWorker(tmp_path / "clock.sqlite", load_world())
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=now)
        _settle(root, window)
        sample[0] = 10
        window.advance_clock()
        _settle(root, window)
        assert window.update is not None and window.update.tick == 1
        sample[0] = 15
        root.focus_force()
        root.event_generate("<Escape>")
        root.update()
        assert window.paused
        assert window.pause_panel.winfo_ismapped()
        sample[0] = 45
        window.advance_clock()
        window.buttons[0].invoke()
        assert window.pending is None and window.update.tick == 1
        root.event_generate("<Escape>")
        root.update()
        sample[0] = 50
        window.advance_clock()
        _settle(root, window)
        assert window.update.tick == 2  # Two5-second idle intervals,not the paused30seconds.
        window.map.select_place("place:p5-b")
        sample[0] = 60
        window.advance_clock()
        _settle(root, window)
        assert window.update.tick == 3  # Map selection did not pause.
        window.set_ai_waiting(True)
        sample[0] = 90
        window.advance_clock()
        assert window.pending is None and window.update.tick == 3
        window.set_ai_waiting(False)
        sample[0] = 100
        window.advance_clock()
        _settle(root, window)
        assert window.update.tick == 4
        window.buttons[0].invoke()
        sample[0] = 120  # Simulate a slow action processing interval;not additional idle time.
        _settle(root, window)
        assert window.update.tick == 5
        sample[0] = 130
        window.advance_clock()
        _settle(root, window)
        assert window.update.tick == 6
        assert window.update.state.offset_m == 1
    finally:
        worker.close()


def test_pending_idle_time_commits_before_user_walk(root: tk.Tk, tmp_path: Path) -> None:
    sample = [0]
    worker = WorldWorker(tmp_path / "clock.sqlite", load_world())
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: sample[0])
        _settle(root, window)
        sample[0] = 200_000_000_000
        window.buttons[0].invoke()
        window.toggle_pause()
        window.toggle_pause()  # Resume while the wait Future is still pending.
        assert window.deferred is not None
        _settle(root, window)
        assert window.update is not None
        assert (
            window.update.tick == 21
        )  # 20elapsed+one footstep,including the16-second batch boundary.
        assert window.update.state.offset_m == 1
        assert window.reserved_seconds == 0 and window.deferred is None
    finally:
        worker.close()


def test_real_gui_uncertain_time_commit_retry_is_not_charged_twice(
    root: tk.Tk, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_persist = SqliteCommitStore.persist
    original_recover = SqliteCommitStore.recover
    persisted = [False]
    recovery_failed = [False]

    def persist(store: SqliteCommitStore, turn: DurableTurn) -> CommitReceipt:
        receipt = original_persist(store, turn)
        if not persisted[0]:
            persisted[0] = True
            raise OSError("injected after actual SQLite commit")
        return receipt

    def recover(store: SqliteCommitStore, turn: DurableTurn) -> RecoveryResult:
        if not recovery_failed[0]:
            recovery_failed[0] = True
            raise OSError("injected unavailable recovery read")
        return original_recover(store, turn)

    monkeypatch.setattr(SqliteCommitStore, "persist", persist)
    monkeypatch.setattr(SqliteCommitStore, "recover", recover)
    sample = [0]
    worker = WorldWorker(tmp_path / "clock.sqlite", load_world())
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: sample[0])
        _settle(root, window)
        sample[0] = 10_000_000_000
        window.advance_clock()
        _settle(root, window)
        assert persisted[0] and recovery_failed[0]
        assert window.wait_error and window.reserved_seconds == 1
        key = window.reservation_key
        window.buttons[0].invoke()
        assert window.pending is None  # Do not accept a new action before resolving uncertain time.
        window.retry_time.invoke()
        _settle(root, window)
        assert window.update is not None and window.update.tick == 1
        assert window.reservation_key == key
        assert window.reserved_seconds == 0 and not window.wait_error
        window.buttons[0].invoke()
        _settle(root, window)
        assert window.update.tick == 2 and window.update.state.offset_m == 1
    finally:
        worker.close()


def test_real_timer_callback_advances_clock_and_disposes_owned_handles(
    root: tk.Tk, tmp_path: Path
) -> None:
    sample = [0]
    worker = WorldWorker(tmp_path / "clock.sqlite", load_world())
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: sample[0])
        _settle(root, window)
        sample[0] = 10_000_000_000
        deadline = time.monotonic() + 3
        while (window.update is None or window.update.tick < 1) and time.monotonic() < deadline:
            root.update()
            time.sleep(0.005)
        assert window.update is not None and window.update.tick == 1
        handle = window.clock_after
        assert handle is not None
        window.close()
        assert window.closed
        assert handle not in root.tk.call("after", "info")
    finally:
        worker.close()


def test_wait_retry_key_is_idempotent_and_cannot_change_duration(tmp_path: Path) -> None:
    worker = WorldWorker(tmp_path / "clock.sqlite", load_world())
    try:
        first = worker.request("wait", seconds=2, request_key="one").result(timeout=10)
        again = worker.request("wait", seconds=2, request_key="one").result(timeout=10)
        assert first == again and first.tick == 2
        with pytest.raises(SaveError, match="WORLD_TIME_PENDING"):
            worker.request("wait", seconds=3, request_key="one").result(timeout=10)
        next_time = worker.request("wait", seconds=2, request_key="two").result(timeout=10)
        assert next_time.tick == 4
    finally:
        worker.close()


def test_real_inventory_panel_keeps_slow_clock_and_respects_esc(
    root: tk.Tk, tmp_path: Path
) -> None:
    sample = [0]
    worker = WorldWorker(tmp_path / "living.sqlite", load_world())
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: sample[0])
        _settle(root, window)
        assert window.update is not None
        assert len(window.update.residents) == 4
        assert all(r.name in window.resident_text.get() for r in window.update.residents)
        window.show_inventory()
        root.update()
        assert window.inventory_panel is not None and window.inventory_panel.winfo_ismapped()
        assert "소지금: 0" in window.inventory_text.get()
        assert "소지품이 없습니다" in window.inventory_text.get()
        sample[0] = 10_000_000_000
        window.advance_clock()
        _settle(root, window)
        assert window.update.tick == 1
        window.inventory_panel.focus_force()
        window.inventory_panel.event_generate("<Escape>")
        root.update()
        assert window.paused
        sample[0] = 30_000_000_000
        window.advance_clock()
        assert window.update.tick == 1 and window.pending is None
        window.toggle_pause()
        sample[0] = 40_000_000_000
        window.advance_clock()
        _settle(root, window)
        assert window.update.tick == 2
        assert window.update.inventory.gold == 0
    finally:
        worker.close()
