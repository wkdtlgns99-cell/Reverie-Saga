from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import threading
import tkinter as tk

import pytest

from app.client import PlayWindow
from app.client_session import ClientSession
from app.client_worker import ClientWorker
from app.headless import replay_runner, restore_checkpoint
from app.npc_activity import recent_activity
from app.npc_memory import memory_bundle
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.client import ClientUpdate
from contracts.replay import ReplayFixture
from domain.canonical import object_value, text_value
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_memory_client_route import approved_content, memory_pipe
from tests.integration.test_quest import GOAL
from tests.integration.test_unity_wait_duration import send_seconds


def bell(tick: int) -> str:
    return f"NPC 활동 기록 · {tick}초: 종을 울렸습니다. (누적 {tick // 2}회)"


def test_retained_activity_real_timestamps_cap_identity_rewind_and_replay(tmp_path: Path) -> None:
    selected = approved_content()
    owner = ClientSession(
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
    )
    try:
        assert owner.inspect_activity().messages == (
            "현재 저장 구간에 남은 NPC 자기 활동이 없습니다.",
        )
        owner.act("wait", seconds=16)
        segment = owner.owner.retained_segment()
        records = recent_activity(
            segment,
            selected.definition.layout.npc_id,
            content=selected,
            current=DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol()),
        )
        assert [r.tick for r in records] == list(range(16, 0, -2))
        assert len({r.event_id for r in records}) == 8
        replayed = restore_checkpoint(
            segment.checkpoint.core, segment.checkpoint.protocol, bundles=(memory_bundle(selected),)
        )
        replayed.driver.submit(segment.trace.steps[0].command)
        source_ids = {event.header.event_id for event in replayed.last_publication().facts}
        assert {r.event_id for r in records} <= source_ids
        with pytest.raises(SaveError, match="activity source differs from live attachment"):
            recent_activity(
                segment,
                selected.definition.layout.npc_id,
                content=selected,
                current=segment.checkpoint,
            )
        assert (
            recent_activity(
                segment,
                "npc:unknown",
                content=selected,
                current=DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol()),
            )
            == ()
        )
        original = owner.owner.working_path.read_bytes()
        before = owner.owner.snapshot(), owner.owner.protocol(), segment
        update = owner.inspect_activity()
        assert update.status == "ACTIVITY_INSPECTED"
        assert update.messages == tuple(bell(tick) for tick in range(2, 17, 2))
        assert owner.owner.working_path.read_bytes() == original
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.retained_segment(),
        ) == before
        assert owner.retry().view == update.view
        owner.save("slot01")
        owner.act("wait", seconds=4)
        assert owner.inspect_activity().messages == tuple(bell(t) for t in range(6, 21, 2))
        owner.load("slot01")
        assert owner.inspect_activity().messages == update.messages
        loaded = owner.owner.working_path
        segment = owner.owner.retained_segment()
        fixture = ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace)
        assert replay_runner(fixture, bundles=(memory_bundle(selected),)).run(segment.trace) == ()
        malformed = replace(
            segment,
            trace=replace(
                segment.trace,
                steps=(replace(segment.trace.steps[0], expected_facts_hash="0" * 64),),
            ),
        )
        with pytest.raises(SaveError, match="NPC_ACTIVITY_SOURCE"):
            recent_activity(
                malformed,
                selected.definition.layout.npc_id,
                content=selected,
                current=DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol()),
            )
    finally:
        owner.close()
    resumed = ClientSession(
        loaded, selected.definition.layout, quest_content=selected, npc_memory=True
    )
    try:
        assert resumed.inspect_activity().messages == update.messages
    finally:
        resumed.close()


def test_self_replies_and_unobserved_combat_remain_separate(tmp_path: Path) -> None:
    selected = approved_content()
    owner = ClientSession(
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
    )
    try:
        owner.act("down")
        assert owner.act("bell").status == "COMMITTED"
        records = recent_activity(
            owner.owner.retained_segment(),
            selected.definition.layout.npc_id,
            content=selected,
            current=DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol()),
        )
        assert sorted((r.kind, r.tick, r.count) for r in records) == [
            ("bell", 2, 1),
            ("reply", 2, 1),
        ]
        assert (
            "NPC 활동 기록 · 2초: 호출에 응답했습니다. (누적 1회)"
            in owner.inspect_activity().messages
        )
        assert [(r.tick, r.event_id) for r in records] == sorted(
            ((r.tick, r.event_id) for r in records), key=lambda item: (-item[0], item[1])
        )
        assert all(r.kind in ("bell", "reply") for r in records)
    finally:
        owner.close()
    owner = ClientSession(
        tmp_path / "combat.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
    )
    try:
        for action in GOAL:
            assert owner.act(action).status == "COMMITTED"
        assert owner.inspect_activity().messages == tuple(bell(t) for t in (2, 4, 6, 8))
        assert len(owner.inspect_memory().messages) == 1
        assert "직접 들었습니다" in owner.inspect_memory().messages[0]
    finally:
        owner.close()


@pytest.mark.parametrize("enabled", (False, True))
def test_worker_inspection_attachment_thread_errors_and_close(
    tmp_path: Path, enabled: bool, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    selected, path = approved_content(), tmp_path / "game.sqlite"
    worker = ClientWorker(
        path, selected.definition.layout, quest_content=selected, npc_memory=enabled
    )
    try:
        assert worker.inspect_activity().result(15).status == "NPC_MEMORY_UNAVAILABLE"
        assert not path.exists()
        attached = worker.request("attach").result(15)
        before = path.read_bytes()
        result = worker.inspect_activity().result(15)
        assert result.status == ("ACTIVITY_INSPECTED" if enabled else "NPC_MEMORY_UNAVAILABLE")
        assert result.view == attached.view and path.read_bytes() == before
        original = ClientSession.inspect_activity
        threads: list[int] = []

        def inspected(owner: ClientSession) -> ClientUpdate:
            threads.append(threading.get_ident())
            return original(owner)

        def failed(owner: ClientSession) -> ClientUpdate:
            raise OSError("activity read failed")

        def fatal(owner: ClientSession) -> ClientUpdate:
            raise KeyboardInterrupt("activity interrupted")

        with monkeypatch.context() as patch:
            patch.setattr(ClientSession, "inspect_activity", inspected)
            worker.inspect_activity().result(15)
        assert len(threads) == 1 and threads[0] != threading.get_ident()
        with monkeypatch.context() as patch:
            patch.setattr(ClientSession, "inspect_activity", failed)
            result = worker.inspect_activity().result(15)
        assert result.status == "CLIENT_ERROR" and result.view == attached.view
        assert "activity read failed" in caplog.text
        with monkeypatch.context() as patch:
            patch.setattr(ClientSession, "inspect_activity", fatal)
            with pytest.raises(KeyboardInterrupt, match="activity interrupted"):
                worker.inspect_activity().result(15)
        assert path.read_bytes() == before
        assert worker.request("wait").result(15).status == "COMMITTED"
    finally:
        worker.join()
    with pytest.raises(ValueError, match="^CLIENT_CLOSING$"):
        worker.inspect_activity()


def test_actual_pipe_activity_load_restart_stale_and_retry(tmp_path: Path) -> None:
    with memory_pipe(tmp_path, tmp_path / "game.sqlite") as pipe:
        empty = pipe.send("activity")
        assert object_value(empty["update"])["status"] == "ACTIVITY_INSPECTED"
        send_seconds(pipe, "wait", "16")
        before = object_value(pipe.latest["update"])
        path = Path(text_value(before["working_path"]))
        body = path.read_bytes()
        inspected = object_value(pipe.send("activity")["update"])
        assert inspected["messages"] == tuple(bell(t) for t in range(2, 17, 2))
        for key in ("view", "attachment_id", "working_path", "quest_stage", "quest_reward"):
            assert inspected[key] == before[key]
        assert path.read_bytes() == body
        pipe.send("retry")
        pipe.send("save")
        send_seconds(pipe, "wait", "4")
        assert object_value(pipe.send("activity")["update"])["messages"] != inspected["messages"]
        token = pipe.token
        loaded = object_value(pipe.send("load")["update"])
        assert pipe.send("activity", token=token)["error"] == "STALE_ATTACHMENT"
        assert object_value(pipe.send("activity")["update"])["messages"] == inspected["messages"]
        assert pipe.send("activity", sequence=pipe.id)["error"] == "STALE_REQUEST"
        loaded_path = Path(text_value(loaded["working_path"]))
    with memory_pipe(tmp_path, loaded_path) as pipe:
        assert object_value(pipe.send("activity")["update"])["messages"] == inspected["messages"]


@pytest.mark.parametrize("enabled", (False, True))
def test_actual_tk_activity_busy_rewind_and_continued_input(
    tmp_path: Path, tk_host: tk.Tk, enabled: bool
) -> None:
    selected = approved_content()
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
        button = screen.activity_button
        if not enabled:
            assert button is None
            _click(screen, "wait")
            return
        assert button is not None
        screen.wait_seconds.set("16")
        _click(screen, "wait")
        before = screen.view
        button.invoke()
        assert screen.busy and str(button.cget("state")) == "disabled"
        pending = screen._pending
        screen._inspect_activity()
        screen._inspect_memory()
        assert screen._pending is pending
        _pump(root, lambda: not screen.busy)
        assert screen.view == before and screen.last_update is not None
        assert screen.last_update.messages == tuple(bell(t) for t in range(2, 17, 2))
        _click(screen, "save")
        screen.wait_seconds.set("4")
        _click(screen, "wait")
        _click(screen, "load")
        button.invoke()
        _pump(root, lambda: not screen.busy)
        assert screen.last_update.messages == tuple(bell(t) for t in range(2, 17, 2))
        assert "20초:" not in screen.log_text.get("1.0", "end")
        _click(screen, "wait")
        assert screen.last_update.status == "COMMITTED"
    finally:
        screen.close()
        if screen.activity_button is not None:
            assert str(screen.activity_button.cget("state")) == "disabled"
        _pump(root, lambda: screen.closed)
        screen.worker.join()
