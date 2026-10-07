from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path
import threading
import time
import tkinter as tk

import pytest

from app.client import PlayWindow
from app.client_session import ClientSession
from app.client_worker import ClientWorker
from contracts.client import ClientAction, ClientUpdate, ClientView
from contracts.persistence import SaveError, WorldUnavailable
from contracts.turn import GameCommand
from contracts.watch import WaitCommand
from domain.primitives import CommandId
from domain.trial import ACTOR_ID


def _view(update: ClientUpdate) -> ClientView:
    assert update.view is not None
    return update.view


@pytest.fixture
def client(tmp_path: Path) -> Iterator[ClientSession]:
    owner = ClientSession(tmp_path / "work.sqlite")
    try:
        yield owner
    finally:
        owner.close()


def _reach_enemy(client: ClientSession) -> None:
    actions: tuple[ClientAction, ...] = ("down", "open", "right", "down")
    for action in actions:
        assert client.act(action).status == "COMMITTED"
    assert _view(client.update()).actor_cell == 7


def test_play_combat_save_load_retry_and_resume(client: ClientSession) -> None:
    blocked = _view(client.act("right"))
    assert (blocked.actor_cell, blocked.tick) == (0, 1)
    _reach_enemy(client)
    attacked = client.act("attack")
    state = _view(attacked)
    assert (state.actor_hp, state.enemy_hp, state.stamina, state.tick) == (2, 3, 1, 6)
    assert "encounter.attack-cue" in attacked.notices
    saved = client.save("slot01")
    old_token = client.owner.attachment_id
    assert _view(client.act("attack")).stamina == 0
    before = client.owner.snapshot(), client.owner.protocol()
    assert client.act("attack").status == "INSUFFICIENT_STAMINA"
    assert (client.owner.snapshot(), client.owner.protocol()) == before
    assert client.act("rest").status == "COMMITTED"
    defeated = _view(client.act("attack"))
    assert (defeated.actor_hp, defeated.enemy_hp, defeated.stamina) == (1, 0, 0)
    assert _view(client.act("right")).actor_cell == 8
    loaded = client.load("slot01")
    assert loaded.view == saved.view
    assert loaded.attachment_id != old_token
    assert loaded.working_path != saved.working_path
    with pytest.raises(ValueError, match="^NO_RETRY$"):
        client.retry()
    first = client.act("attack")
    retried = client.retry()
    assert retried.view == first.view and retried.status == "COMMITTED"
    assert retried.notices == ()  # Exact retry does not replay presentation cues.
    assert len(client.owner.retained_segment().trace.steps) == 7
    active_path = Path(first.working_path)
    client.close()
    resumed = ClientSession(active_path)
    try:
        assert resumed.update().view == first.view
        assert _view(resumed.act("rest")).stamina == 1
    finally:
        resumed.close()


@pytest.mark.parametrize(
    ("action", "seconds", "code"),
    [
        ("open", 1, "OUT_OF_RANGE"),
        ("attack", 1, "OUT_OF_RANGE"),
        ("wait", 0, "INVALID_COMMAND"),
        ("wait", -1, "INVALID_COMMAND"),
        ("wait", 17, "INVALID_COMMAND"),
        ("wait", True, "INVALID_COMMAND"),
    ],
    ids=["far-door", "far-enemy", "zero-wait", "negative-wait", "long-wait", "bool-wait"],
)
def test_invalid_intent_preserves_head(
    client: ClientSession, action: ClientAction, seconds: int, code: str
) -> None:
    before = client.owner.snapshot(), client.owner.protocol()
    assert client.act(action, seconds=seconds).status == code
    assert (client.owner.snapshot(), client.owner.protocol()) == before


def test_door_occupancy_and_specified_noops(client: ClientSession) -> None:
    client.act("down")
    opened = client.act("open")
    repeated = client.act("open")
    assert _view(repeated).tick == _view(opened).tick + 1
    assert "encounter.gate-cue" in repeated.notices
    client.act("right")
    before = client.update()
    assert client.act("close").status == "TARGET_OCCUPIED"
    assert client.update().view == before.view
    rested = client.act("rest")
    assert _view(rested).stamina == 2
    assert _view(rested).tick == _view(before).tick + 1
    assert "encounter.rest-cue" in rested.notices


def test_npc_wait_and_stale_attachment(client: ClientSession) -> None:
    waited = _view(client.act("wait", seconds=2))
    assert (waited.tick, waited.npc_bells, waited.charge) == (2, 1, 2)
    rang = _view(client.act("bell"))
    assert (rang.npc_bells, rang.npc_replies) == (1, 1)
    old_token = client.owner.attachment_id
    client.save("slot01")
    client.load("slot01")
    protocol = client.owner.protocol()
    stream = protocol.streams[0]
    command = GameCommand(
        CommandId(f"c1:{protocol.branch_id}:{stream.stream_id}:3"),
        ACTOR_ID,
        protocol.revision,
        WaitCommand(1),
    )
    before = client.owner.snapshot(), protocol
    with pytest.raises(SaveError, match="^STALE_ATTACHMENT:"):
        client.owner.submit(command, attachment_id=old_token)
    assert (client.owner.snapshot(), client.owner.protocol()) == before


def test_worker_serializes_io_and_drains_before_close(tmp_path: Path) -> None:
    path = tmp_path / "worker.sqlite"
    worker = ClientWorker(path)
    try:
        attach = worker.request("attach")
        wait = worker.request("wait", seconds=2)
        save = worker.request("save")
        close = worker.close()
        assert attach.result(timeout=15).status == "ATTACHED"
        assert _view(wait.result(timeout=15)).tick == 2
        assert save.result(timeout=15).status == "SAVED"
        close.result(timeout=15)
        assert worker.close() is close
        with pytest.raises(ValueError, match="^CLIENT_CLOSING$"):
            worker.request("wait")
    finally:
        worker.close().result(timeout=15)
        worker.join()
    assert not any(t.name.startswith("reverie-brain") for t in threading.enumerate())
    resumed = ClientSession(path)
    try:
        assert _view(resumed.update()).tick == 2
    finally:
        resumed.close()


def test_worker_reports_save_errors_without_mutation(tmp_path: Path) -> None:
    worker = ClientWorker(tmp_path / "errors.sqlite")
    try:
        before = worker.request("attach").result(timeout=15)
        failed = worker.request("save", slot_id="../invalid").result(timeout=15)
        assert failed.status == "INVALID_SLOT" and failed.view == before.view
        assert "INVALID_SLOT" in failed.notices[0]
        assert worker.request("wait").result(timeout=15).status == "COMMITTED"
    finally:
        worker.close().result(timeout=15)


def _pump(root: tk.Tk | tk.Toplevel, finished: Callable[[], bool]) -> None:
    deadline = time.monotonic() + 15
    while not finished():
        if time.monotonic() >= deadline:
            pytest.fail("real Tk/Brain operation did not complete in 15 seconds")
        root.update()
        time.sleep(0.005)


@pytest.fixture(scope="module")
def tk_host() -> Iterator[tk.Tk]:
    # Keep one interpreter alive;each test still owns fresh widgets,worker and save.
    # Retained Python/Tcl callbacks from destroyed Tk instances share an event queue.
    root = tk.Tk()
    root.withdraw()
    try:
        yield root
    finally:
        root.destroy()


@pytest.fixture
def window(tmp_path: Path, tk_host: tk.Tk) -> Iterator[PlayWindow]:
    root = tk.Toplevel(tk_host)
    root.withdraw()
    screen = PlayWindow(root, tmp_path / "ui.sqlite")
    try:
        _pump(root, lambda: not screen.busy)
        assert screen.view is not None
        yield screen
    finally:
        screen.close()
        _pump(root, lambda: screen.closed)
        screen.worker.close().result(timeout=15)
        screen.worker.join()


def _click(window: PlayWindow, action: ClientAction) -> None:
    window.buttons[action].invoke()
    _pump(window.root, lambda: not window.busy)


def test_real_tk_buttons_render_combat_save_load(window: PlayWindow) -> None:
    assert window.view is not None and window.view.actor_cell == 0
    assert window.canvas.find_all()
    for action in ("down", "open", "right", "down", "attack"):
        _click(window, action)
    assert window.view.actor_cell == 7
    assert window.canvas.coords("actor") == [183.0, 327.0, 249.0, 393.0]
    assert "체력 2/3" in window.stats.get()
    window.buttons["save"].invoke()
    _pump(window.root, lambda: not window.busy)
    saved = window.view
    _click(window, "attack")
    assert window.view.enemy_hp == 1
    window.buttons["load"].invoke()
    _pump(window.root, lambda: not window.busy)
    assert window.status.get() == "LOADED" and window.view == saved
    assert ".loaded-" in window.path_text.get()


def test_real_tk_invalid_text_and_shutdown_pending(window: PlayWindow) -> None:
    before = window.view
    window.wait_seconds.set("not-an-integer")
    window.buttons["wait"].invoke()
    assert window.status.get().startswith("INVALID_INPUT")
    assert not window.busy and window.view == before
    window.wait_seconds.set("2")
    window.buttons["wait"].invoke()
    window.close()
    _pump(window.root, lambda: window.closed)
    window.worker.join()
    assert window.view is not None and window.view.tick == 2
    assert not any(t.name.startswith("reverie-brain") for t in threading.enumerate())


def test_controller_close_blocks_authoritative_calls(client: ClientSession) -> None:
    client.close()
    with pytest.raises(WorldUnavailable, match="^SESSION_CLOSED:"):
        client.update()


def test_existing_invalid_file_is_not_replaced(tmp_path: Path) -> None:
    path = tmp_path / "not-a-save.sqlite"
    body = b"owned invalid save must survive"
    path.write_bytes(body)
    worker = ClientWorker(path)
    try:
        failed = worker.request("attach").result(timeout=15)
        assert failed.view is None and failed.status == "SAVE_CORRUPT"
        assert path.read_bytes() == body
    finally:
        worker.close().result(timeout=15)


def test_action_messages_cover_damage_retry_and_rejection(client: ClientSession) -> None:
    _reach_enemy(client)
    first = client.act("attack")
    assert any("플레이어 → 적: 공격, 피해 2" in line for line in first.messages)
    assert any("적 → 플레이어: 반격, 피해 1" in line for line in first.messages)
    before = client.owner.snapshot(), client.owner.protocol()
    retried = client.retry()
    assert (client.owner.snapshot(), client.owner.protocol()) == before
    assert not any("공격," in line or "반격," in line for line in retried.messages)
    assert any("다시 실행하지" in line for line in retried.messages)
    client.act("attack")
    before = client.owner.snapshot(), client.owner.protocol()
    refused = client.act("attack")
    assert (client.owner.snapshot(), client.owner.protocol()) == before
    assert any("스태미나가 부족" in line for line in refused.messages)


def test_wait_npc_and_load_reset_messages(client: ClientSession) -> None:
    waited = client.act("wait", seconds=2)
    assert waited.messages[0] == "플레이어가 2초 동안 기다렸습니다."
    assert any("NPC가 종" in line for line in waited.messages)
    called = client.act("bell")
    assert any("플레이어가 NPC를 호출" in line for line in called.messages)
    assert any("NPC가 호출에 응답" in line for line in called.messages)
    assert "slot01" in client.save("slot01").messages[0]
    loaded = client.load("slot01")
    assert loaded.reset_log and any("별도 진행" in line for line in loaded.messages)


def test_worker_error_does_not_repeat_previous_success(tmp_path: Path) -> None:
    worker = ClientWorker(tmp_path / "message-errors.sqlite")
    try:
        worker.request("attach").result(timeout=15)
        successful = worker.request("wait").result(timeout=15)
        failed = worker.request("load", slot_id="../invalid").result(timeout=15)
        assert failed.view == successful.view and not failed.reset_log
        assert not any("기다렸" in line for line in failed.messages)
        assert any("저장 슬롯" in line for line in failed.messages)
    finally:
        worker.close().result(timeout=15)
        worker.join()


def test_real_tk_history_load_and_duplicate_render(window: PlayWindow) -> None:
    for action in ("down", "open", "right", "down", "attack"):
        _click(window, action)
    body = window.log_text.get("1.0", "end-1c")
    assert "플레이어 → 적: 공격, 피해 2" in body
    assert "적 → 플레이어: 반격, 피해 1" in body
    assert window.log_text.cget("state") == "disabled"
    assert window.last_update is not None
    window._render(window.last_update)
    assert window.log_text.get("1.0", "end-1c") == body
    window.buttons["save"].invoke()
    _pump(window.root, lambda: not window.busy)
    _click(window, "attack")
    assert "체력 3 → 1" in window.log_text.get("1.0", "end-1c")
    window.buttons["load"].invoke()
    _pump(window.root, lambda: not window.busy)
    restored = window.log_text.get("1.0", "end-1c")
    assert "별도 진행" in restored and "공격," not in restored


def test_real_tk_history_is_bounded_and_invalid_wait_is_explained(window: PlayWindow) -> None:
    from app.client import LOG_LINE_LIMIT

    for index in range(LOG_LINE_LIMIT + 2):
        window._append_messages((f"기록 {index}",))
    body = window.log_text.get("1.0", "end-1c")
    assert len(body.splitlines()) == LOG_LINE_LIMIT
    assert "기록 0\n" not in body and f"기록 {LOG_LINE_LIMIT + 1}" in body
    before = window.view
    window.wait_seconds.set("not-an-integer")
    window.buttons["wait"].invoke()
    assert window.view == before
    assert "정수를 입력" in window.log_text.get("1.0", "end-1c")


def test_finishing_attack_message_has_no_counter(client: ClientSession) -> None:
    _reach_enemy(client)
    client.act("attack")
    client.act("attack")
    client.act("rest")
    final = client.act("attack")
    assert any("공격, 피해 1" in line for line in final.messages)
    assert any("쓰러졌" in line for line in final.messages)
    assert not any("반격" in line for line in final.messages)


def test_worker_no_retry_after_load_is_explained(tmp_path: Path) -> None:
    worker = ClientWorker(tmp_path / "retry-messages.sqlite")
    try:
        worker.request("attach").result(timeout=15)
        worker.request("save").result(timeout=15)
        worker.request("load").result(timeout=15)
        result = worker.request("retry").result(timeout=15)
        assert result.status == "NO_RETRY" and not result.reset_log
        assert any("재전송할 명령이 없" in line for line in result.messages)
    finally:
        worker.close().result(timeout=15)
        worker.join()


def test_real_tk_log_focus_and_line_length(window: PlayWindow) -> None:
    from app.client import LOG_TEXT_LIMIT

    event: tk.Event[tk.Misc] = tk.Event()
    event.widget, event.keysym = window.log_text, "Right"
    before = window.view
    window._key(event)
    assert not window.busy and window.view == before
    window._append_messages(("긴 기록\r\n" + "가" * LOG_TEXT_LIMIT,))
    assert len(window.history[-1]) <= LOG_TEXT_LIMIT
    assert "\r" not in window.history[-1] and "\n" not in window.history[-1]
    assert window.log_scrollbar.cget("command")
