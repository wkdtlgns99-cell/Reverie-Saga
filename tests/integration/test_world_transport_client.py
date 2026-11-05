"""Actual worker/Tk journey choices and exact durable segment recovery."""

from collections.abc import Iterator
from pathlib import Path
import gc
import sqlite3
import time
import tkinter as tk
from typing import Never

import pytest

from adapters.sqlite_store import SqliteCommitStore
from app.world_catalog import load_social, load_transport, load_world
from app.world_client import WorldMapWindow
from app.world_worker import WorldUpdate, WorldWorker
from contracts.persistence import DurableTurn, RecoveryResult, SaveError
from contracts.turn import CommitReceipt
from contracts.world_transport import TransportAction


@pytest.fixture
def root() -> Iterator[tk.Tk]:
    window = tk.Tk()
    try:
        yield window
    finally:
        window.destroy()
        gc.collect()


def settle(root: tk.Tk, window: WorldMapWindow) -> None:
    deadline = time.monotonic() + 20
    while window.pending is not None and time.monotonic() < deadline:
        root.update()
        time.sleep(0.002)
    assert window.pending is None


def worker_at(path: Path) -> WorldWorker:
    world = load_world()
    return WorldWorker(path, world, social=load_social(world), transport=load_transport(world))


def test_actual_gui_stops_waits_for_player_and_returns(root: tk.Tk, tmp_path: Path) -> None:
    worker = worker_at(tmp_path / "ui.sqlite")
    clock = [0]
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: clock[0])
        settle(root, window)
        window.show_transport()
        panel = window.transport_panel
        assert panel is not None and window.update is not None
        assert not str(root.tk.call("grab", "current"))
        panel.buttons["board"].invoke()
        assert "요금 0금" in panel.terms.get() and "2000초" in panel.terms.get()
        assert window.update.tick == 0
        clock[0] = 20_000_000_000
        panel.confirm.invoke()
        clock[0] = 920_000_000_000
        settle(root, window)
        assert window.update.tick == 503 and window.update.journey is not None
        assert window.update.journey.phase == "blocked" and window.update.journey.progress_m == 2500
        assert not window.transport_running and window.pending is None
        assert not window.update.residents and not window.update.offers
        assert "통행 제한" in panel.status.get()
        assert window.road.find_withtag("journey")
        assert str(panel.buttons["resume"]["state"]) == "disabled"
        panel.buttons["wait"].invoke()
        panel.confirm.invoke()
        settle(root, window)
        assert window.update.tick == 800 and window.update.journey.phase == "blocked"
        assert "통제 해제" in panel.status.get() and not window.transport_running
        assert str(panel.buttons["wait"]["state"]) == "disabled"
        panel.buttons["return"].invoke()
        panel.confirm.invoke()
        settle(root, window)
        assert window.update.tick == 1301 and window.update.journey.phase == "idle"
        assert window.update.state.place_id == "place:p0-a" and window.update.state.visited == (
            "place:p0-a",
        )
        assert window.update.inventory.gold == 0 and window.update.inventory.items == ()
        window.dispose()
    finally:
        worker.close()


def test_gui_board_ack_failure_recovers_then_continues_same_intent(
    root: tk.Tk, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worker = worker_at(tmp_path / "ack.sqlite")
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: 0)
        settle(root, window)
        window.show_transport()
        panel = window.transport_panel
        assert panel is not None
        original = WorldMapWindow.render
        failed = [False]

        def render(view: WorldMapWindow, update: WorldUpdate) -> None:
            if view.pending_action == "transport" and update.tick == 1 and not failed[0]:
                failed[0] = True
                raise ValueError("injected board acknowledgement failure")
            original(view, update)

        monkeypatch.setattr(WorldMapWindow, "render", render)
        panel.buttons["board"].invoke()
        panel.confirm.invoke()
        settle(root, window)
        assert failed[0] and window.transport_error
        panel.retry.invoke()
        settle(root, window)
        assert not window.transport_error and window.update is not None
        assert window.update.tick == 501 and window.update.journey is not None
        assert window.update.journey.phase == "blocked"
        window.dispose()
    finally:
        worker.close()


@pytest.mark.parametrize("uncertain", (False, True), ids=("rollback", "uncertain"))
def test_worker_segment_retry_keeps_original_duration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, uncertain: bool
) -> None:
    worker = worker_at(tmp_path / "retry.sqlite")
    try:
        board = worker.request(
            "transport", "place:p0-b", transport_operation="board", request_key="board"
        ).result(10)
        assert board.tick == 1
        failed = [False]
        if uncertain:
            persist_original, recover_original = (
                SqliteCommitStore.persist,
                SqliteCommitStore.recover,
            )
            recovery_failed = [False]

            def persist(store: SqliteCommitStore, turn: DurableTurn) -> CommitReceipt:
                receipt = persist_original(store, turn)
                if isinstance(turn.command.payload, TransportAction) and not failed[0]:
                    failed[0] = True
                    raise OSError("after real segment commit")
                return receipt

            def recover(store: SqliteCommitStore, turn: DurableTurn) -> RecoveryResult:
                if not recovery_failed[0]:
                    recovery_failed[0] = True
                    raise OSError("segment recovery unavailable once")
                return recover_original(store, turn)

            monkeypatch.setattr(SqliteCommitStore, "persist", persist)
            monkeypatch.setattr(SqliteCommitStore, "recover", recover)
        else:
            execute_original = SqliteCommitStore._execute

            def execute(
                store: SqliteCommitStore,
                query: str,
                values: tuple[None | int | float | str | bytes, ...] = (),
            ) -> sqlite3.Cursor:
                result = execute_original(store, query, values)
                if query.startswith("INSERT INTO replay") and not failed[0]:
                    failed[0] = True
                    raise sqlite3.IntegrityError("segment replay rollback")
                return result

            monkeypatch.setattr(SqliteCommitStore, "_execute", execute)
        with pytest.raises(
            SaveError, match="^SAVE_UNCERTAIN:" if uncertain else "^SAVE_UNAVAILABLE:"
        ):
            worker.request(
                "transport", transport_operation="advance", request_key="advance"
            ).result(10)
        with pytest.raises(SaveError, match="WORLD_TRANSPORT_PENDING"):
            worker.request("transport", transport_operation="return", request_key="advance").result(
                10
            )
        update = worker.request(
            "transport", transport_operation="advance", request_key="advance"
        ).result(10)
        assert update.tick == 501 and update.transport_committed and update.journey is not None
        assert update.journey.progress_m == 2500 and update.journey.phase == "blocked"
        assert (
            worker.request(
                "transport", transport_operation="advance", request_key="advance"
            ).result(10)
            == update
        )
    finally:
        worker.close()


def test_escape_between_board_and_segment_stops_until_explicit_unpause(
    root: tk.Tk, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worker = worker_at(tmp_path / "pause.sqlite")
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: 0)
        settle(root, window)
        original = WorldMapWindow.render
        paused = [False]

        def render(view: WorldMapWindow, update: WorldUpdate) -> None:
            original(view, update)
            if update.tick == 1 and view.pending_action == "transport" and not paused[0]:
                paused[0] = True
                view.toggle_pause()

        monkeypatch.setattr(WorldMapWindow, "render", render)
        window.confirm_transport("board", "place:p0-b")
        settle(root, window)
        assert paused[0] and window.paused and window.transport_next
        assert window.update is not None and window.update.tick == 1
        window.resume_deferred()
        assert window.pending is None and window.update.tick == 1
        window.toggle_pause()
        settle(root, window)
        assert not window.paused and window.update.tick == 501
        assert window.update.journey is not None and window.update.journey.phase == "blocked"
        window.dispose()
    finally:
        worker.close()


def test_restart_active_journey_requires_choice_and_never_initializes_provider(
    root: tk.Tk, tmp_path: Path
) -> None:
    path = tmp_path / "restart.sqlite"
    worker = worker_at(path)
    try:
        board = worker.request(
            "transport", "place:p0-b", transport_operation="board", request_key="board"
        ).result(10)
        assert board.tick == 1
        worker.request("save").result(10)
    finally:
        worker.close()

    def forbidden_provider() -> Never:
        pytest.fail("in-transit generation must reject before provider initialization")

    world = load_world()
    worker = WorldWorker(
        path,
        world,
        social=load_social(world),
        transport=load_transport(world),
        generator_factory=forbidden_provider,
    )
    try:
        window = WorldMapWindow(root, world, worker, now_ns=lambda: 0)
        settle(root, window)
        assert window.update is not None and window.update.tick == 1
        assert window.update.journey is not None and window.update.journey.phase == "outbound"
        assert not window.transport_running and not window.transport_next
        window.resume_deferred()
        assert window.pending is None
        with pytest.raises(ValueError, match="^DIALOGUE_OUT_OF_REACH$"):
            worker.request("generate", request_key="forbidden").result(10)
        assert worker.request("inspect").result(10).tick == 1
        window.confirm_transport("advance", "")
        settle(root, window)
        assert window.update.tick == 501 and window.update.journey.phase == "blocked"
        window.dispose()
    finally:
        worker.close()
