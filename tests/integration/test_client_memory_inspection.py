from __future__ import annotations

import gc
from pathlib import Path
import threading
import tkinter as tk

import pytest

from app.client import PlayWindow
from app.client_session import ClientSession
from app.client_worker import ClientWorker
from contracts.client import ClientUpdate
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_quest import GOAL


@pytest.mark.parametrize(
    "steps,ticks",
    ((0, ()), (2, (2,)), (9, (2,)), (11, (2, 11))),
)
def test_inspection_uses_only_committed_conversations_without_mutation(
    tmp_path: Path, steps: int, ticks: tuple[int, ...]
) -> None:
    selected = approved_content()
    path = tmp_path / "game.sqlite"
    session = ClientSession(
        path, selected.definition.layout, quest_content=selected, npc_memory=True
    )
    try:
        for action in (*GOAL, "left", "talk")[:steps]:
            assert session.act(action).status == "COMMITTED"
        before = (
            session.owner.snapshot(),
            session.owner.protocol(),
            session.owner.retained_segment(),
            session.update(),
            path.read_bytes(),
        )
        update = session.inspect_memory()
        assert update.status == "MEMORY_INSPECTED" and not update.reset_log
        assert update.view == before[3].view
        assert (update.attachment_id, update.working_path, update.quest_reward) == (
            before[3].attachment_id,
            before[3].working_path,
            before[3].quest_reward,
        )
        if not ticks:
            assert update.messages == ("NPC에게 아직 기록된 플레이어와의 의뢰 대화가 없습니다.",)
        else:
            assert len(update.messages) == len(ticks)
            assert all(
                f"{tick}초:" in line for tick, line in zip(ticks, update.messages, strict=True)
            )
            assert "의뢰를 맡겠다는 말을 직접 들었습니다" in update.messages[0]
            if len(ticks) == 2:
                assert "완료 보고를 받았습니다" in update.messages[1]
                assert "직접 본 기억은 아닙니다" in update.messages[1]
        # Do not expose private engine/source identity or invent a witnessed death at tick9.
        text = "\n".join(update.messages)
        for private in (str(path), "e1-", "m1-", "world_seed", selected.definition.layout.enemy_id):
            assert private not in text
        assert (
            session.owner.snapshot(),
            session.owner.protocol(),
            session.owner.retained_segment(),
            session.update(),
            path.read_bytes(),
        ) == before
        if steps:
            retried = session.retry()
            assert retried.status == "COMMITTED" and retried.notices == ()
            assert len(retried.messages) == 1
            assert "다시 실행하지 않았습니다." in retried.messages[0]
            assert (session.owner.snapshot(), session.owner.protocol(), path.read_bytes()) == (
                before[0],
                before[1],
                before[4],
            )
        else:
            with pytest.raises(ValueError, match="^NO_RETRY$"):
                session.retry()
    finally:
        session.close()


def test_load_and_new_worker_resume_query_the_actual_branch(tmp_path: Path) -> None:
    selected = approved_content()
    worker = ClientWorker(
        tmp_path / "original.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
    )
    try:
        worker.request("attach").result(timeout=15)
        for action in GOAL[:2]:
            worker.request(action).result(timeout=15)
        accepted = worker.inspect_memory().result(timeout=15)
        assert len(accepted.messages) == 1 and "2초:" in accepted.messages[0]
        worker.request("save").result(timeout=15)
        for action in (*GOAL[2:], "left", "talk"):
            worker.request(action).result(timeout=15)
        reported = worker.inspect_memory().result(timeout=15)
        assert len(reported.messages) == 2 and "11초:" in reported.messages[1]
        assert reported.quest_reward == 1
        loaded = worker.request("load").result(timeout=15)
        restored = worker.inspect_memory().result(timeout=15)
        assert restored.messages == accepted.messages and restored.quest_reward == 0
        assert restored.working_path == loaded.working_path != reported.working_path
        assert restored.attachment_id == loaded.attachment_id != reported.attachment_id
        assert worker.request("retry").result(timeout=15).status == "NO_RETRY"
        active_path = Path(restored.working_path)
    finally:
        worker.join()
    resumed = ClientWorker(
        active_path, selected.definition.layout, quest_content=selected, npc_memory=True
    )
    try:
        resumed.request("attach").result(timeout=15)
        assert resumed.inspect_memory().result(timeout=15).messages == accepted.messages
    finally:
        resumed.join()


@pytest.mark.parametrize("quest", (False, True))
def test_disabled_memory_is_explicit_and_worker_remains_usable(tmp_path: Path, quest: bool) -> None:
    selected = approved_content()
    worker = (
        ClientWorker(tmp_path / "legacy.sqlite")
        if not quest
        else ClientWorker(
            tmp_path / "quest.sqlite", selected.definition.layout, quest_content=selected
        )
    )
    try:
        before = worker.request("attach").result(timeout=15)
        original = Path(before.working_path).read_bytes()
        failed = worker.inspect_memory().result(timeout=15)
        assert failed.status == "NPC_MEMORY_UNAVAILABLE" and failed.view == before.view
        assert failed.messages == (
            "현재 게임에서는 NPC 대화 기억을 확인할 수 없습니다. (NPC_MEMORY_UNAVAILABLE)",
        )
        assert Path(before.working_path).read_bytes() == original
        assert worker.request("wait").result(timeout=15).status == "COMMITTED"
    finally:
        worker.join()
    with pytest.raises(ValueError, match="^CLIENT_CLOSING$"):
        worker.inspect_memory()


@pytest.mark.parametrize("memory", (False, True))
def test_inspection_before_attach_does_not_create_a_game(tmp_path: Path, memory: bool) -> None:
    selected, path = approved_content(), tmp_path / "unattached.sqlite"
    worker = ClientWorker(
        path, selected.definition.layout, quest_content=selected, npc_memory=memory
    )
    try:
        failed = worker.inspect_memory().result(timeout=15)
        assert failed.status == "NPC_MEMORY_UNAVAILABLE" and failed.view is None
        assert not path.exists()
        assert worker.request("attach").result(timeout=15).status == "ATTACHED"
        if memory:
            assert worker.inspect_memory().result(timeout=15).status == "MEMORY_INSPECTED"
    finally:
        worker.join()


def test_inspection_runs_on_owner_thread_and_failure_remains_recoverable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    selected = approved_content()
    worker = ClientWorker(
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
    )
    original = ClientSession.inspect_memory
    calls: list[int] = []

    def inspect(owner: ClientSession) -> ClientUpdate:
        calls.append(threading.get_ident())
        return original(owner)

    def fail(owner: ClientSession) -> ClientUpdate:
        raise OSError("inspection display failure")

    try:
        before = worker.request("attach").result(timeout=15)
        with monkeypatch.context() as patched:
            patched.setattr(ClientSession, "inspect_memory", inspect)
            assert worker.inspect_memory().result(timeout=15).status == "MEMORY_INSPECTED"
        assert len(calls) == 1 and calls[0] != threading.get_ident()
        with monkeypatch.context() as patched:
            patched.setattr(ClientSession, "inspect_memory", fail)
            failed = worker.inspect_memory().result(timeout=15)
        assert failed.status == "CLIENT_ERROR" and failed.view == before.view
        assert "inspection display failure" in caplog.text
        assert worker.inspect_memory().result(timeout=15).status == "MEMORY_INSPECTED"
        assert worker.request("wait").result(timeout=15).status == "COMMITTED"
    finally:
        worker.join()


@pytest.mark.parametrize("fatal", (KeyboardInterrupt, SystemExit))
def test_memory_query_propagates_process_control(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fatal: type[BaseException]
) -> None:
    selected = approved_content()
    worker = ClientWorker(
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
    )

    def interrupt(owner: ClientSession) -> ClientUpdate:
        raise fatal("stop inspection")

    try:
        worker.request("attach").result(timeout=15)
        with monkeypatch.context() as patched:
            patched.setattr(ClientSession, "inspect_memory", interrupt)
            with pytest.raises(fatal, match="^stop inspection$"):
                worker.inspect_memory().result(timeout=15)
        assert worker.inspect_memory().result(timeout=15).status == "MEMORY_INSPECTED"
    finally:
        worker.join()


def test_native_tk_memory_failure_keeps_input_polling_and_close(
    tmp_path: Path,
    tk_host: tk.Tk,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    gc.collect()
    selected = approved_content()
    root = tk.Toplevel(tk_host)
    root.withdraw()
    screen = PlayWindow(
        root,
        tmp_path / "screen.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
    )

    def fail(owner: ClientSession) -> ClientUpdate:
        raise OSError("memory display unavailable")

    try:
        _pump(root, lambda: not screen.busy)
        before = screen.view
        button = screen.memory_button
        assert button is not None
        with monkeypatch.context() as patched:
            patched.setattr(ClientSession, "inspect_memory", fail)
            button.invoke()
            _pump(root, lambda: not screen.busy)
        assert screen.status.get() == "CLIENT_ERROR" and screen.view == before
        assert "memory display unavailable" in caplog.text
        assert str(button.cget("state")) == "normal"
        button.invoke()
        _pump(root, lambda: not screen.busy)
        assert screen.status.get() == "MEMORY_INSPECTED" and screen.view == before
        assert "MEMORY_INSPECTED" not in screen.status_text.get()
        _click(screen, "down")
        assert screen.view is not None and screen.view.tick == 1
    finally:
        screen.close()
        _pump(root, lambda: screen.closed)
        screen.worker.join()


@pytest.mark.parametrize("memory", (False, True))
def test_native_tk_memory_button_visibility_input_and_loaded_history(
    tmp_path: Path, tk_host: tk.Tk, memory: bool
) -> None:
    gc.collect()
    selected = approved_content()
    root = tk.Toplevel(tk_host)
    root.withdraw()
    screen = PlayWindow(
        root,
        tmp_path / "screen.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=memory,
    )
    try:
        _pump(root, lambda: not screen.busy)
        button = screen.memory_button
        if not memory:
            assert button is None
            return
        assert button is not None and str(button.cget("text")) == "NPC 대화 기억"
        assert button.grid_info()["row"] == 8 and button.grid_info()["column"] == 1
        before = screen.view
        button.invoke()
        assert screen.busy and str(button.cget("state")) == "disabled"
        _pump(root, lambda: not screen.busy)
        assert screen.view == before and str(button.cget("state")) == "normal"
        assert "아직 기록된" in screen.log_text.get("1.0", "end")
        for action in GOAL[:2]:
            _click(screen, action)
        screen._send("save")
        _pump(root, lambda: not screen.busy)
        for action in (*GOAL[2:], "left", "talk"):
            _click(screen, action)
        reported = screen.view
        button.invoke()
        _pump(root, lambda: not screen.busy)
        assert screen.view == reported
        assert "11초: 플레이어에게 의뢰 완료 보고" in screen.log_text.get("1.0", "end")
        screen._send("load")
        _pump(root, lambda: not screen.busy)
        button.invoke()
        _pump(root, lambda: not screen.busy)
        text = screen.log_text.get("1.0", "end")
        assert "2초: 플레이어가 의뢰를 맡겠다는 말" in text
        assert "11초:" not in text
        _click(screen, "wait")
        assert screen.last_update is not None and screen.last_update.status == "COMMITTED"
    finally:
        screen.close()
        if screen.memory_button is not None:
            assert str(screen.memory_button.cget("state")) == "disabled"
        _pump(root, lambda: screen.closed)
        screen.worker.join()
