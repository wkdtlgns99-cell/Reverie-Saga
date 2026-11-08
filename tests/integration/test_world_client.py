"""Actual Tk map selection over the shared,unchanged development world."""

from collections.abc import Iterator
import os
from pathlib import Path
import gc
import sqlite3
import tkinter as tk
from tkinter import ttk
import time

import pytest

from app.world_catalog import DEVELOPMENT_WORLD, load_world
from app.world_client import WorldMapWindow, launch_world
from app.world_worker import WorldUpdate, WorldWorker
from adapters.sqlite_store import SqliteCommitStore
from adapters.world_attachment import current_world
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


def test_failed_load_reference_replace_preserves_the_active_working_clone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "world.sqlite"
    world = load_world()
    worker = WorldWorker(path, world)
    try:
        worker.request("walk", "place:p0-b").result(timeout=10)
        worker.request("save").result(timeout=10)
        worker.request("load").result(timeout=10)
        advanced = worker.request("walk", "place:p0-b").result(timeout=10)
        active = current_world(path)
        assert active != path and advanced.state.offset_m == 2
        reference = path.with_name(path.name + ".active.json")
        before = active.read_bytes(), reference.read_bytes(), set(tmp_path.iterdir())
        replace = os.replace

        def reject_reference(source: str | Path, target: str | Path) -> None:
            if target == reference:
                raise PermissionError("working reference replace denied")
            replace(source, target)

        with monkeypatch.context() as patch:
            patch.setattr("adapters.world_attachment.os.replace", reject_reference)
            with pytest.raises((OSError, SaveError)) as failed:
                worker.request("load").result(timeout=10)
        assert current_world(path) == active
        assert (active.read_bytes(), reference.read_bytes(), set(tmp_path.iterdir())) == before
        assert worker.request("inspect").result(timeout=10).protocol == advanced.protocol
        assert isinstance(failed.value, SaveError) and failed.value.code == "SAVE_LOAD_FAILED"

        continued = worker.request("walk", "place:p0-b").result(timeout=10)
        assert continued.state.offset_m == 3
        loaded = worker.request("load").result(timeout=10)
        assert loaded.state.offset_m == 1 and current_world(path) != active
    finally:
        worker.close()

    resumed = WorldWorker(path, world)
    try:
        actual = resumed.request("inspect").result(timeout=10)
        assert (actual.state, actual.tick, actual.protocol) == (
            loaded.state,
            loaded.tick,
            loaded.protocol,
        )
    finally:
        resumed.close()


def test_failed_retired_store_close_preserves_the_new_working_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "world.sqlite"
    world = load_world()
    worker = WorldWorker(path, world)
    try:
        worker.request("walk", "place:p0-b").result(timeout=10)
        worker.request("save").result(timeout=10)
        worker.request("walk", "place:p0-b").result(timeout=10)
        close = SqliteCommitStore.close
        calls: list[Path] = []

        def fail_retired_close(store: SqliteCommitStore) -> None:
            if store.path == path and not calls:
                calls.append(current_world(path))
                raise sqlite3.OperationalError("retired close failed")
            close(store)

        with monkeypatch.context() as patch:
            patch.setattr(SqliteCommitStore, "close", fail_retired_close)
            with pytest.raises(sqlite3.OperationalError, match="retired close failed"):
                worker.request("load").result(timeout=10)
            active = current_world(path)
            assert active != path and calls == [active]
            loaded = worker.request("inspect").result(timeout=10)
            assert loaded.state.offset_m == 1 and loaded.tick == 1
            continued = worker.request("walk", "place:p0-b", -1).result(timeout=10)
            assert continued.state.offset_m == 0 and continued.tick == 2
    finally:
        worker.close()

    resumed = WorldWorker(path, world)
    try:
        actual = resumed.request("inspect").result(timeout=10)
        assert actual.protocol == continued.protocol and actual.state == continued.state
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


@pytest.mark.parametrize("committed", (True, False))
def test_real_gui_can_confirm_uncertain_footstep_without_resubmitting(
    root: tk.Tk, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, committed: bool
) -> None:
    path = tmp_path / "walk.sqlite"
    world = load_world()
    original_persist = SqliteCommitStore.persist
    original_recover = SqliteCommitStore.recover
    writes: list[DurableTurn] = []
    attempts: list[DurableTurn] = []

    def persist(store: SqliteCommitStore, turn: DurableTurn) -> CommitReceipt:
        writes.append(turn)
        if len(writes) != 1:
            return original_persist(store, turn)
        if committed:
            original_persist(store, turn)
        raise OSError("injected footstep write acknowledgement failure")

    def recover(store: SqliteCommitStore, turn: DurableTurn) -> RecoveryResult:
        attempts.append(turn)
        if len(attempts) <= 2:
            raise OSError("injected unavailable footstep recovery read")
        return original_recover(store, turn)

    monkeypatch.setattr(SqliteCommitStore, "persist", persist)
    monkeypatch.setattr(SqliteCommitStore, "recover", recover)
    sample = [0]
    worker = WorldWorker(path, world)
    try:
        window = WorldMapWindow(root, world, worker, now_ns=lambda: sample[0])
        _settle(root, window)
        window.buttons[0].invoke()
        _settle(root, window)
        assert len(writes) == len(attempts) == 1
        assert "이동 결과 확인" in window.status.get()
        assert window.retry_walk.winfo_ismapped()

        sample[0] = 30_000_000_000
        window.advance_clock()
        window.buttons[0].invoke()
        assert window.pending is None and window.reserved_seconds == 0
        with pytest.raises(SaveError, match="^WORLD_WALK_PENDING"):
            worker.request("wait", seconds=1).result(timeout=10)

        window.retry_walk.invoke()
        _settle(root, window)
        assert window.retry_walk.winfo_ismapped() and len(attempts) == 2
        window.retry_walk.invoke()
        _settle(root, window)
        assert not window.retry_walk.winfo_ismapped() and attempts == [writes[0]] * 3
        assert window.update is not None
        expected = int(committed)
        assert (window.update.tick, window.update.state.offset_m) == (expected, expected)
        assert ("저장된 것을 확인" if committed else "반영되지 않았습니다") in window.status.get()
        assert len(writes) == 1
        repeated = worker.request("recover_walk").result(timeout=10)
        assert repeated.protocol == window.update.protocol and len(attempts) == 3

        window.buttons[0].invoke()
        _settle(root, window)
        assert (window.update.tick, window.update.state.offset_m) == (expected + 1, expected + 1)
        assert len(writes) == 2
        final = window.update
    finally:
        worker.close()

    resumed = WorldWorker(path, world)
    try:
        restored = resumed.request("inspect").result(timeout=10)
        assert (restored.state, restored.protocol) == (final.state, final.protocol)
    finally:
        resumed.close()


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


def _offer_button(window: WorldMapWindow, text: str) -> ttk.Button:
    panel = window.offer_panel
    assert panel is not None
    return next(
        child
        for child in panel.winfo_children()
        if isinstance(child, ttk.Button) and child.cget("text") == text
    )


def test_real_supply_offer_refusal_slow_consideration_and_confirmed_delivery(
    root: tk.Tk, tmp_path: Path
) -> None:
    sample = [0]
    worker = WorldWorker(tmp_path / "supply.sqlite", load_world())
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: sample[0])
        _settle(root, window)
        sample[0] = 900_000_000_000
        window.advance_clock()
        _settle(root, window)
        # Drain all90logical seconds through the real16-second batching path.
        assert window.update is not None
        # advance_clock submits one batch per idle callback;drive callbacks explicitly.
        while window.update.tick < 90:
            window.advance_clock()
            _settle(root, window)
        assert "시장 재고 0/3" in window.supply_text.get()
        assert "배급 대기 중" in window.resident_text.get()
        before = window.update.inventory
        window.offer_button.invoke()
        root.update()
        assert window.offer_panel is not None and window.offer_panel.winfo_ismapped()
        _offer_button(window, "거절 / 닫기").invoke()
        root.update()
        assert window.update.inventory == before
        assert window.pending is None
        window.offer_button.invoke()
        sample[0] += 10_000_000_000
        window.advance_clock()
        _settle(root, window)
        assert window.update.tick == 91
        for operation in ("accept", "collect", "collect", "deliver"):
            if window.offer_panel is None or not window.offer_panel.winfo_exists():
                window.offer_button.invoke()
            assert window.update.offers[0].action.operation == operation
            _offer_button(window, "확인하고 진행").invoke()
            _settle(root, window)
        assert window.update.tick == 95
        assert window.update.inventory.gold == 5 and window.update.inventory.items == ()
        assert "복구 완료" in window.supply_text.get()
        assert not window.update.offers
        assert "대체 보급로 찾는 중" not in window.resident_text.get()
    finally:
        worker.close()


def test_real_stale_offer_is_rejected_at_confirmation(root: tk.Tk, tmp_path: Path) -> None:
    sample = [0]
    worker = WorldWorker(tmp_path / "stale.sqlite", load_world())
    try:
        for seconds in (16, 14):
            worker.request("wait", seconds=seconds).result(timeout=10)
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: sample[0])
        _settle(root, window)
        window.offer_button.invoke()
        assert window.offer_panel is not None
        # Actual recorded waiting expires the offer;the still-open panel retains its terms.
        for _ in range(38):
            worker.request("wait", seconds=16).result(timeout=10)
        _offer_button(window, "확인하고 진행").invoke()
        _settle(root, window)
        assert window.update is not None and window.update.tick == 638
        assert "기한이 끝났거나" in window.status.get()
        assert window.update.inventory.gold == 0 and window.update.inventory.items == ()
    finally:
        worker.close()


def test_real_uncertain_exchange_retry_cannot_duplicate_cargo(
    root: tk.Tk, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worker = WorldWorker(tmp_path / "retry.sqlite", load_world())
    try:
        worker.request("wait", seconds=16).result(timeout=10)
        worker.request("wait", seconds=14).result(timeout=10)
        first = worker.request("inspect").result(timeout=10).offers[0]
        worker.request("supply", supply=first.action, request_key="accept").result(timeout=10)
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: 0)
        _settle(root, window)
        original_persist = SqliteCommitStore.persist
        original_recover = SqliteCommitStore.recover
        persisted = [False]
        recovery_failed = [False]

        def persist(store: SqliteCommitStore, turn: DurableTurn) -> CommitReceipt:
            result = original_persist(store, turn)
            if not persisted[0]:
                persisted[0] = True
                raise OSError("injected after actual supply SQLite commit")
            return result

        def recover(store: SqliteCommitStore, turn: DurableTurn) -> RecoveryResult:
            if not recovery_failed[0]:
                recovery_failed[0] = True
                raise OSError("injected supply recovery unavailable")
            return original_recover(store, turn)

        monkeypatch.setattr(SqliteCommitStore, "persist", persist)
        monkeypatch.setattr(SqliteCommitStore, "recover", recover)
        window.offer_button.invoke()
        _offer_button(window, "확인하고 진행").invoke()
        _settle(root, window)
        assert window.supply_error and window.supply_command is not None
        window.buttons[0].invoke()
        assert window.pending is None
        key = window.supply_request_key
        window.retry_supply.invoke()
        _settle(root, window)
        assert not window.supply_error and window.supply_request_key == key
        assert window.update is not None and window.update.tick == 32
        assert window.update.inventory.items == (("item:supply-p0-a", 1),)
        window.offer_button.invoke()
        _offer_button(window, "확인하고 진행").invoke()
        _settle(root, window)
        assert window.update.tick == 33
        assert window.update.inventory.items == (("item:supply-p0-a", 2),)
    finally:
        worker.close()


def test_supply_presentation_failure_retains_confirmation_for_exact_retry(
    root: tk.Tk, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worker = WorldWorker(tmp_path / "ack.sqlite", load_world())
    try:
        worker.request("wait", seconds=16).result(timeout=10)
        worker.request("wait", seconds=14).result(timeout=10)
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: 0)
        _settle(root, window)
        original = WorldMapWindow.render
        failed = [False]

        def render(w: WorldMapWindow, update: WorldUpdate) -> None:
            if not failed[0]:
                failed[0] = True
                raise ValueError("injected presentation acknowledgement failure")
            original(w, update)

        monkeypatch.setattr(WorldMapWindow, "render", render)
        window.offer_button.invoke()
        _offer_button(window, "확인하고 진행").invoke()
        _settle(root, window)
        assert window.supply_error and window.supply_command is not None
        window.retry_supply.invoke()
        _settle(root, window)
        assert not window.supply_error and window.supply_command is None
        assert window.update is not None and window.update.tick == 31
        assert window.update.offers[0].action.operation == "collect"
    finally:
        worker.close()


def test_supply_controls_remain_reachable_at_minimum_window_width(root: tk.Tk) -> None:
    window = WorldMapWindow(root, load_world())
    root.geometry("780x560")
    root.update()
    for button in (*window.buttons, window.offer_button, window.retry_time):
        assert button.winfo_rootx() >= root.winfo_rootx()
        assert (
            button.winfo_rootx() + button.winfo_width() <= root.winfo_rootx() + root.winfo_width()
        )
        assert (
            button.winfo_rooty() + button.winfo_height() <= root.winfo_rooty() + root.winfo_height()
        )
