from __future__ import annotations

from collections.abc import Callable, Iterator
from concurrent.futures import Future
import gc
from pathlib import Path
import sqlite3
import threading
import time
import tkinter as tk
from tkinter import ttk

import pytest

from app.client import PlayWindow
from app.client_session import ClientSession
from app.client_worker import ClientWorker
from contracts.client import ClientAction, ClientRequest, ClientUpdate, ClientView
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
    # Failed render traces can retain old Tk variables;collect them on their owner thread
    # before the next worker starts allocating,not from that worker's cyclic GC.
    gc.collect()
    root = tk.Toplevel(tk_host)
    root.withdraw()
    screen = PlayWindow(root, tmp_path / "ui.sqlite")
    try:
        _pump(root, lambda: not screen.busy)
        assert screen.view is not None, screen.last_update
        yield screen
    finally:
        screen.close()
        _pump(root, lambda: screen.closed)
        screen.worker.close().result(timeout=15)
        screen.worker.join()


def _click(window: PlayWindow, action: ClientRequest) -> None:
    window.buttons[action].invoke()
    _pump(window.root, lambda: not window.busy)


def test_real_tk_quest_button_state_and_dialogue(tmp_path: Path, tk_host: tk.Tk) -> None:
    from tests.unit.quest_fixtures import content
    from tests.integration.test_quest import GOAL

    selected = content()
    gc.collect()
    root = tk.Toplevel(tk_host)
    root.withdraw()
    screen = PlayWindow(
        root, tmp_path / "quest-ui.sqlite", selected.definition.layout, quest_content=selected
    )
    try:
        _pump(root, lambda: not screen.busy)
        assert "talk" in screen.buttons
        for action in (*GOAL, "left", "talk"):
            _click(screen, action)
        assert screen.last_update is not None and screen.last_update.quest_reward == 1
        assert "임무 완료" in screen.stats.get() and "호의 1" in screen.stats.get()
        assert selected.dialogue.text("completion") in "\n".join(screen.history)
    finally:
        screen.close()
        _pump(root, lambda: screen.closed)
        screen.worker.join()


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


@pytest.mark.parametrize("count,extra,top", ((80, 1, 40), (200, 2, 40), (200, 2, 1)))
def test_real_tk_new_log_preserves_reading_record(
    window: PlayWindow, count: int, extra: int, top: int
) -> None:
    window.root.geometry("900x950")
    window.root.deiconify()
    window.root.update()
    window.history.clear()
    window._append_messages(tuple(f"읽는 기록 {index}" for index in range(count)))
    window.root.update()
    window.log_text.yview(f"{top}.0")
    window.root.update()
    before = window.log_text.get("@0,0 linestart", "@0,0 lineend")
    if count == 200 and top == 1:
        before = window.log_text.get("3.0", "3.end")  # First two records will be evicted.
    view = window.view
    saved = window.worker.request("save").result(timeout=15)
    data = Path(saved.working_path).read_bytes()
    window._append_messages(tuple(f"새 기록 {index}" for index in range(extra)))
    window.root.update()
    assert window.log_text.get("@0,0 linestart", "@0,0 lineend") == before
    assert window.log_text.yview()[1] < 1
    assert window.view == view and Path(saved.working_path).read_bytes() == data
    window._append_messages(())
    window.root.update()
    assert window.log_text.get("@0,0 linestart", "@0,0 lineend") == before


def test_real_tk_log_follows_tail_and_load_resets_reading(window: PlayWindow) -> None:
    window.root.geometry("900x950")
    window.root.deiconify()
    window.root.update()
    _click(window, "save")
    window._append_messages(tuple(f"기록 {index}" for index in range(80)))
    window.root.update()
    window.log_text.see("end")
    window._append_messages(("마지막 기록",))
    window.root.update()
    assert window.log_text.yview()[1] == 1
    window.log_text.yview("20.0")
    window.root.update()
    assert window.log_text.yview()[1] < 1
    _click(window, "load")
    window.root.update()
    assert window.status.get() == "LOADED"
    assert window.log_text.yview()[1] == 1
    assert "마지막 기록" not in window.log_text.get("1.0", "end")


def _focus_wait_field(window: PlayWindow) -> None:
    window.root.geometry("1000x1000")
    window.root.deiconify()
    window.wait_input.focus_force()
    window.root.update()
    assert window.root.focus_get() is window.wait_input


def test_real_tk_latest_button_is_readonly_and_resumes_following(window: PlayWindow) -> None:
    _focus_wait_field(window)
    window._append_messages(tuple(f"과거 기록 {index}" for index in range(80)))
    window.root.update()
    window.log_text.yview("20.0")
    window.root.update()
    assert window.log_text.yview()[1] < 1
    assert window.last_update is not None
    path = Path(window.last_update.working_path)
    before = (window.view, window.last_update, tuple(window.history), path.read_bytes())
    for _ in range(2):
        window.log_latest_button.invoke()
    window.root.update()
    assert window.log_text.yview()[1] == 1
    assert (window.view, window.last_update, tuple(window.history), path.read_bytes()) == before
    window._send("wait")
    pending = window._pending
    assert pending is not None and window.log_latest_button.instate(["!disabled"])
    window.log_latest_button.invoke()
    assert window._pending is pending
    _pump(window.root, lambda: not window.busy)
    window.root.update()
    assert window.view is not None and window.view.tick == 1
    assert window.log_text.yview()[1] == 1


def test_real_tk_latest_button_preserves_history_heading_height(window: PlayWindow) -> None:
    _focus_wait_field(window)
    heading = window.log_latest_button.master
    label = next(child for child in heading.winfo_children() if isinstance(child, ttk.Label))
    assert window.log_latest_button.winfo_ismapped()
    assert heading.winfo_reqheight() == label.winfo_reqheight()


@pytest.mark.parametrize("seconds", (1, 4, 16))
def test_real_tk_wait_enter_submits_once(window: PlayWindow, seconds: int) -> None:
    _focus_wait_field(window)
    window.wait_seconds.set(str(seconds))
    window.wait_input.event_generate("<Return>")
    pending = window._pending
    assert pending is not None
    window.wait_input.event_generate("<Return>")
    assert window._pending is pending
    _pump(window.root, lambda: not window.busy)
    assert window.status.get() == "COMMITTED"
    assert window.view is not None and window.view.tick == seconds


def test_real_tk_keypad_enter_binding_submits_once(window: PlayWindow) -> None:
    _focus_wait_field(window)
    window.wait_seconds.set("4")
    binding = window.wait_input.bind("<KP_Enter>")
    assert binding
    if window.root.tk.call("tk", "windowingsystem") == "win32":
        # Windows Tk has no synthetic keycode for KP_Enter;invoke its registered callback.
        command = binding.split("[", 1)[1].split(" ", 1)[0]
        window.root.tk.call(command, "")
        pending = window._pending
        window.root.tk.call(command, "")
    else:
        window.wait_input.event_generate("<KP_Enter>")
        pending = window._pending
        window.wait_input.event_generate("<KP_Enter>")
    assert pending is not None and window._pending is pending
    _pump(window.root, lambda: not window.busy)
    assert window.status.get() == "COMMITTED"
    assert window.view is not None and window.view.tick == 4


@pytest.mark.parametrize(
    "value,code",
    (
        ("", "INVALID_INPUT"),
        ("abc", "INVALID_INPUT"),
        ("0", "INVALID_COMMAND"),
        ("-1", "INVALID_COMMAND"),
        ("17", "INVALID_COMMAND"),
    ),
)
def test_real_tk_wait_enter_rejection_preserves_input_and_save(
    window: PlayWindow, value: str, code: str
) -> None:
    _focus_wait_field(window)
    assert window.last_update is not None
    path = Path(window.last_update.working_path)
    before = (window.view, path.read_bytes())
    window.wait_seconds.set(value)
    window.wait_input.event_generate("<Return>")
    _pump(window.root, lambda: not window.busy)
    assert window.status.get().startswith(code)
    assert (window.view, path.read_bytes()) == before
    assert window.wait_seconds.get() == value


def test_real_tk_return_outside_wait_field_does_not_act(window: PlayWindow) -> None:
    _focus_wait_field(window)
    before = window.view
    for widget in (window.log_text, window.slot_input):
        widget.focus_force()
        window.root.update()
        widget.event_generate("<Return>")
        window.root.update()
        assert window._pending is None and window.view == before


def test_real_tk_repeated_invalid_return_retains_gameplay_log(window: PlayWindow) -> None:
    _focus_wait_field(window)
    _click(window, "wait")
    gameplay = tuple(window.history)
    window.wait_seconds.set("")
    for _ in range(205):
        window.wait_input.event_generate("<Return>")
    assert tuple(window.history)[:-1] == gameplay
    assert len(window.history) == len(gameplay) + 1
    assert window.status.get().startswith("INVALID_INPUT")
    error = window.history[-1].split("] ", 1)[-1]
    window.wait_seconds.set("1")
    _click(window, "wait")
    window.wait_seconds.set("")
    window.wait_input.event_generate("<Return>")
    assert window.history[-1].endswith(error)
    assert sum(line.endswith(error) for line in window.history) == 2


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


@pytest.mark.parametrize("fault", ["sqlite", "unlisted"])
def test_worker_fault_projects_error_and_next_request_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, fault: str
) -> None:
    from adapters.sqlite_store import SqliteCommitStore

    worker = ClientWorker(tmp_path / "boundary-fault.sqlite")
    try:
        worker.request("attach").result(timeout=15)
        before = worker.request("wait").result(timeout=15)

        def failed_backup(self: SqliteCommitStore, path: Path) -> None:
            raise sqlite3.OperationalError("database or disk is full")

        def failed_save(self: ClientSession, slot_id: str) -> ClientUpdate:
            raise ArithmeticError("unlisted boundary fault")

        with monkeypatch.context() as patched:
            if fault == "sqlite":
                patched.setattr(SqliteCommitStore, "_backup_reserved", failed_backup)
            else:
                patched.setattr(ClientSession, "save", failed_save)
            failed = worker.request("save").result(timeout=15)
        expected = "SAVE_EXPORT_FAILED" if fault == "sqlite" else "CLIENT_ERROR"
        assert failed.status == expected and failed.view == before.view
        assert failed.attachment_id == before.attachment_id and not failed.reset_log
        assert not any("기다렸" in line for line in failed.messages)
        if fault == "unlisted":
            assert "client boundary operation failed" in caplog.text
        after = worker.request("wait").result(timeout=15)
        assert after.status == "COMMITTED" and _view(after).tick == _view(before).tick + 1
    finally:
        worker.join()


@pytest.mark.parametrize("closing,cancelled", [(False, False), (True, False), (False, True)])
def test_real_tk_failed_future_keeps_input_and_close_alive(
    window: PlayWindow, closing: bool, cancelled: bool
) -> None:
    previous = window.view
    failed: Future[ClientUpdate] = Future()
    if cancelled:
        assert failed.cancel()
    else:
        failed.set_exception(ArithmeticError("unlisted Future failure"))
    window._pending = failed
    window._enable(False)
    if closing:
        window.close()
    try:
        window._poll()
    finally:
        # Preserve teardown even against the original failing callback.
        window._pending = None
    if not closing:
        assert not window.busy and window.view == previous
        assert window.status.get() == "CLIENT_ERROR"
        assert "오류" in window.log_text.get("1.0", "end-1c")
        assert all(str(button.cget("state")) == "normal" for button in window.buttons.values())
        window.buttons["wait"].invoke()
        _pump(window.root, lambda: not window.busy)
        assert window.view is not None and previous is not None
        assert window.view.tick == previous.tick + 1
        window.close()
    _pump(window.root, lambda: window.closed)
    window.worker.join()
    assert window.closed


@pytest.mark.parametrize("fault", [KeyboardInterrupt, SystemExit])
def test_worker_process_control_exception_propagates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: type[BaseException]
) -> None:
    from adapters.sqlite_store import SqliteCommitStore

    worker = ClientWorker(tmp_path / "process-control.sqlite")
    try:
        before = worker.request("attach").result(timeout=15)

        def failed_backup(self: SqliteCommitStore, path: Path) -> None:
            raise fault("process-control signal")

        with monkeypatch.context() as patched:
            patched.setattr(SqliteCommitStore, "_backup_reserved", failed_backup)
            with pytest.raises(fault, match="^process-control signal$"):
                worker.request("save").result(timeout=15)
        assert worker._last is before
        assert not tuple((tmp_path / "slots").glob(".export-*"))
        after = worker.request("wait").result(timeout=15)
        assert after.status == "COMMITTED" and _view(after).tick == _view(before).tick + 1
    finally:
        worker.join()


@pytest.mark.parametrize("stage", ["early", "draw"])
@pytest.mark.parametrize("closing", [False, True])
def test_real_tk_render_failure_rearms_poll_and_restores_input(
    window: PlayWindow,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    stage: str,
    closing: bool,
) -> None:
    previous = window.last_update
    assert previous is not None
    committed = window.worker.request("wait").result(timeout=15)
    assert committed.view is not None and previous.view is not None
    assert committed.status == "COMMITTED" and committed.view.tick == previous.view.tick + 1
    completed: Future[ClientUpdate] = Future()
    completed.set_result(committed)
    window._pending = completed
    window._enable(False)
    before_callbacks = set(window.root.tk.splitlist(window.root.tk.call("after", "info")))

    def failed_render(self: PlayWindow, update: ClientUpdate) -> None:
        raise ArithmeticError("renderer failed")

    def failed_draw(self: PlayWindow, view: ClientView) -> None:
        raise ArithmeticError("renderer failed")

    if closing:
        window.close()
    with monkeypatch.context() as patched:
        if stage == "early":
            patched.setattr(PlayWindow, "_render", failed_render)
        else:
            patched.setattr(PlayWindow, "_draw_map", failed_draw)
        window._poll()
    after_callbacks = set(window.root.tk.splitlist(window.root.tk.call("after", "info")))
    if not window.closed:
        assert after_callbacks - before_callbacks, "Failed callback must schedule the next poll"
    assert window._pending is None and window.view == committed.view
    assert window.status.get() == "CLIENT_ERROR" and "오류" in window.status_text.get()
    assert window.notices.get() == "renderer failed"
    assert window.last_update is not None and window.last_update.status == "CLIENT_ERROR"
    assert window.last_update.view == committed.view
    assert window.last_update.attachment_id == committed.attachment_id
    assert window.last_update.working_path == committed.working_path
    records = [record for record in caplog.records if record.message == "client rendering failed"]
    assert len(records) == 1 and records[0].exc_info is not None
    assert isinstance(records[0].exc_info[1], ArithmeticError)
    if closing:
        assert window.busy  # Closing intentionally blocks new input after pending work drains.
        _pump(window.root, lambda: window.closed)
        assert window.closed
        return
    assert not window.busy
    assert all(str(button.cget("state")) == "normal" for button in window.buttons.values())
    attached = window.worker.request("attach").result(timeout=15)
    assert attached.view == committed.view  # Reporting the failure never reruns the committed wait.
    _click(window, "wait")
    assert window.view is not None
    assert window.view.tick == committed.view.tick + 1
    window.close()
    _pump(window.root, lambda: window.closed)
    assert window.closed


@pytest.mark.parametrize("fault", [KeyboardInterrupt, SystemExit])
def test_real_tk_render_process_control_propagates(
    window: PlayWindow, monkeypatch: pytest.MonkeyPatch, fault: type[BaseException]
) -> None:
    previous = window.last_update
    assert previous is not None
    completed: Future[ClientUpdate] = Future()
    completed.set_result(previous)
    window._pending = completed

    def interrupted_render(self: PlayWindow, update: ClientUpdate) -> None:
        raise fault("render process-control signal")

    with monkeypatch.context() as patched:
        patched.setattr(PlayWindow, "_render", interrupted_render)
        with pytest.raises(fault, match="^render process-control signal$"):
            window._poll()
    assert not window.busy and window.last_update is previous
