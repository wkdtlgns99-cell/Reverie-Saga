from __future__ import annotations

import gc
from pathlib import Path
import threading
import tkinter as tk
from typing import cast

import pytest

from app.client import PlayWindow
from app.client_session import ClientSession
from app.client_worker import ClientWorker
from app.engine_bridge import REQUEST_NAMES, SCHEMA_HASH
from app.engine_project import generate_wire
from app.npc_memory_query import recent_evidence
from contracts.client import ClientUpdate
from contracts.dialogue import GenerationError
from domain.canonical import JsonObject, array_value, object_value, text_value
from domain.npc_memory import NpcQuestMemoryRecord
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_engine_bridge import PipeClient, pipe as pipe, view
from tests.integration.test_memory_client_route import approved_content, memory_pipe
from tests.integration.test_quest import GOAL


@pytest.mark.parametrize("steps,tick", ((0, None), (2, 2), (9, 2), (11, 11)))
def test_recent_owner_snapshot_preserves_state_and_full_inspection(
    tmp_path: Path, steps: int, tick: int | None
) -> None:
    selected = approved_content()
    path = tmp_path / "game.sqlite"
    owner = ClientSession(path, selected.definition.layout, quest_content=selected, npc_memory=True)
    try:
        for action in (*GOAL, "left", "talk")[:steps]:
            assert owner.act(action).status == "COMMITTED"
        before = owner.owner.snapshot(), owner.owner.protocol(), owner.owner.retained_segment()
        original = path.read_bytes()
        all_memories = owner.inspect_memory()
        recent = owner.inspect_recent_memory()
        assert recent.status == "MEMORY_INSPECTED" and recent.reset_log is False
        assert recent.view == all_memories.view and recent.quest_reward == all_memories.quest_reward
        assert len(recent.messages) == 1
        if tick is None:
            assert recent.messages == ("NPC에게 아직 기록된 플레이어와의 의뢰 대화가 없습니다.",)
        else:
            assert recent.messages[0].startswith(f"최근 NPC 대화 기억 · {tick}초:")
            if tick == 11:
                assert "완료 보고를 받았습니다" in recent.messages[0]
                assert "직접 본 기억은 아닙니다" in recent.messages[0]
                assert "직접 들었습니다" not in recent.messages[0]
            else:
                assert "직접 들었습니다" in recent.messages[0]
                assert "완료 보고" not in recent.messages[0]
        assert owner.inspect_memory() == all_memories
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.retained_segment(),
        ) == before
        assert path.read_bytes() == original
        if steps:
            assert "다시 실행하지 않았습니다" in owner.retry().messages[0]
            assert (owner.owner.snapshot(), owner.owner.protocol()) == before[:2]
            assert path.read_bytes() == original
        else:
            with pytest.raises(ValueError, match="^NO_RETRY$"):
                owner.retry()
    finally:
        owner.close()


def test_recent_selector_rejects_unvalidated_input() -> None:
    for value in (None, True, ()):
        with pytest.raises(GenerationError, match="^NPC_CONTEXT_INPUT$"):
            recent_evidence(cast(NpcQuestMemoryRecord, value))


@pytest.mark.parametrize("enabled", (False, True))
def test_recent_before_attach_disabled_and_closing_keep_worker_contract(
    tmp_path: Path, enabled: bool
) -> None:
    selected, path = approved_content(), tmp_path / "game.sqlite"
    worker = ClientWorker(
        path, selected.definition.layout, quest_content=selected, npc_memory=enabled
    )
    try:
        failed = worker.inspect_recent_memory().result(timeout=15)
        assert failed.status == "NPC_MEMORY_UNAVAILABLE" and failed.view is None
        assert not path.exists()
        worker.request("attach").result(timeout=15)
        before = path.read_bytes()
        update = worker.inspect_recent_memory().result(timeout=15)
        assert update.status == ("MEMORY_INSPECTED" if enabled else "NPC_MEMORY_UNAVAILABLE")
        assert path.read_bytes() == before
        assert worker.request("wait").result(timeout=15).status == "COMMITTED"
    finally:
        worker.join()
    with pytest.raises(ValueError, match="^CLIENT_CLOSING$"):
        worker.inspect_recent_memory()


def test_recent_owner_thread_error_and_fatal_propagation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    selected = approved_content()
    worker = ClientWorker(
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
    )
    original = ClientSession.inspect_recent_memory
    threads: list[int] = []

    def inspected(owner: ClientSession) -> ClientUpdate:
        threads.append(threading.get_ident())
        return original(owner)

    def failed(owner: ClientSession) -> ClientUpdate:
        raise OSError("recent projection failed")

    def fatal(owner: ClientSession) -> ClientUpdate:
        raise KeyboardInterrupt("recent interrupted")

    try:
        before = worker.request("attach").result(timeout=15)
        with monkeypatch.context() as patch:
            patch.setattr(ClientSession, "inspect_recent_memory", inspected)
            assert worker.inspect_recent_memory().result(timeout=15).status == "MEMORY_INSPECTED"
        assert len(threads) == 1 and threads[0] != threading.get_ident()
        with monkeypatch.context() as patch:
            patch.setattr(ClientSession, "inspect_recent_memory", failed)
            update = worker.inspect_recent_memory().result(timeout=15)
        assert update.status == "CLIENT_ERROR" and update.view == before.view
        assert "recent projection failed" in caplog.text
        with monkeypatch.context() as patch:
            patch.setattr(ClientSession, "inspect_recent_memory", fatal)
            with pytest.raises(KeyboardInterrupt, match="recent interrupted"):
                worker.inspect_recent_memory().result(timeout=15)
        assert worker.inspect_recent_memory().result(timeout=15).status == "MEMORY_INSPECTED"
        assert worker.request("wait").result(timeout=15).status == "COMMITTED"
    finally:
        worker.join()


def inspect_recent(pipe: PipeClient) -> JsonObject:
    before = object_value(pipe.latest["update"])
    path = Path(text_value(before["working_path"]))
    body = path.read_bytes()
    reply = pipe.send("memory_recent")
    after = object_value(reply["update"])
    assert reply["error"] == "" and after["status"] == "MEMORY_INSPECTED"
    for key in (
        "view",
        "working_path",
        "attachment_id",
        "quest_stage",
        "quest_reward",
        "dialogue_sha256",
    ):
        assert after[key] == before[key]
    assert after["reset_log"] is False and path.read_bytes() == body
    return after


def test_real_pipe_recent_rechecks_load_resume_and_stale_identity(tmp_path: Path) -> None:
    with memory_pipe(tmp_path, tmp_path / "game.sqlite") as client:
        assert "아직 기록된" in text_value(array_value(inspect_recent(client)["messages"])[0])
        for action in GOAL[:2]:
            client.send(action)
        accepted = inspect_recent(client)
        assert "2초:" in text_value(array_value(accepted["messages"])[0])
        client.send("save")
        for action in GOAL[2:]:
            client.send(action)
        assert inspect_recent(client)["messages"] == accepted["messages"]
        client.send("left")
        client.send("talk")
        reported = inspect_recent(client)
        lines = array_value(reported["messages"])
        assert len(lines) == 1 and "11초:" in text_value(lines[0])
        assert "직접 본 기억은 아닙니다" in text_value(lines[0])
        assert view(client.send("retry")) == reported["view"]
        token = client.token
        loaded = client.send("load")
        loaded_path = Path(text_value(object_value(loaded["update"])["working_path"]))
        assert client.send("memory_recent", token=token)["error"] == "STALE_ATTACHMENT"
        restored = inspect_recent(client)
        assert restored["messages"] == accepted["messages"] and restored["quest_reward"] == "0"
        assert client.send("memory_recent", sequence=client.id)["error"] == "STALE_REQUEST"
    with memory_pipe(tmp_path, loaded_path) as resumed:
        assert inspect_recent(resumed)["messages"] == accepted["messages"]
        assert view(resumed.send("wait"))["tick"] == "3"


def test_recent_legacy_pipe_and_canonical_wire(pipe: PipeClient) -> None:
    before = view(pipe.latest)
    reply = pipe.send("memory_recent")
    assert object_value(reply["update"])["status"] == "NPC_MEMORY_UNAVAILABLE"
    assert view(reply) == before and view(pipe.send("wait"))["tick"] == "1"
    assert REQUEST_NAMES.count("memory_recent") == 1
    assert SCHEMA_HASH != "188504954814f58c87dba6dad0f63e996a4267c3fa8de15b2f35d7e86c5c1416"
    assert (
        Path("clients/unity/Assets/Reverie/Scripts/Wire.Generated.cs").read_text(encoding="utf-8")
        == generate_wire()
    )


@pytest.mark.parametrize("enabled", (False, True))
def test_real_tk_recent_control_busy_load_and_continued_input(
    tmp_path: Path, tk_host: tk.Tk, enabled: bool
) -> None:
    selected = approved_content()
    gc.collect()
    root = tk.Toplevel(tk_host)
    root.withdraw()
    screen = PlayWindow(
        root,
        tmp_path / "ui.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=enabled,
    )
    try:
        _pump(root, lambda: not screen.busy)
        if not enabled:
            assert screen.recent_memory_button is None
            _click(screen, "wait")
            return
        button = screen.recent_memory_button
        assert button is not None and screen.memory_button is not None
        assert int(button.grid_info()["row"]) < int(screen.wait_input.grid_info()["row"])
        before = screen.view
        button.invoke()
        assert screen.busy and str(button.cget("state")) == "disabled"
        assert str(screen.memory_button.cget("state")) == "disabled"
        screen._inspect_memory()
        _pump(root, lambda: not screen.busy)
        assert screen.view == before and str(button.cget("state")) == "normal"
        for action in GOAL[:2]:
            _click(screen, action)
        screen.buttons["save"].invoke()
        _pump(root, lambda: not screen.busy)
        for action in (*GOAL[2:], "left", "talk"):
            _click(screen, action)
        button.invoke()
        _pump(root, lambda: not screen.busy)
        assert screen.last_update is not None
        assert len(screen.last_update.messages) == 1
        assert "최근 NPC 대화 기억 · 11초:" in screen.log_text.get("1.0", "end")
        screen.buttons["load"].invoke()
        _pump(root, lambda: not screen.busy)
        button.invoke()
        _pump(root, lambda: not screen.busy)
        assert "최근 NPC 대화 기억 · 2초:" in screen.log_text.get("1.0", "end")
        assert "11초:" not in screen.log_text.get("1.0", "end")
        _click(screen, "wait")
        assert screen.last_update.status == "COMMITTED"
    finally:
        screen.close()
        if screen.recent_memory_button is not None:
            assert str(screen.recent_memory_button.cget("state")) == "disabled"
        _pump(root, lambda: screen.closed)
        screen.worker.join()
