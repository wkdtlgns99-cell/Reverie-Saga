from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import gc
from pathlib import Path
import tkinter as tk

from adapters.sqlite_store import SqliteCommitStore
from app.client import PlayWindow
from app.client_session import ClientSession
from app.headless import replay_runner, state_io
from app.npc_memory import memory_bundle, read_memory
from contracts.replay import ReplayFixture
from domain.canonical import array_value, object_value, text_value
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_memory_client_route import approved_content, memory_pipe
from tests.integration.test_quest import GOAL
from tests.integration.test_unity_wait_duration import send_seconds


def test_talk_activity_uses_committed_view_and_exact_retry_is_quiet(tmp_path: Path) -> None:
    selected = approved_content()
    owner = ClientSession(
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
    )
    try:
        before = owner.owner.snapshot(), owner.owner.protocol()
        rejected = owner.act("talk")
        assert rejected.status == "OUT_OF_RANGE"
        assert not any(line.startswith("NPC 활동 현황") for line in rejected.messages)
        assert (owner.owner.snapshot(), owner.owner.protocol()) == before
        owner.act("down")
        accepted = owner.act("talk")
        assert accepted.messages[-1] == "NPC 활동 현황 · 2초 · 종 1회 · 호출 응답 0회."
        assert accepted.view is not None and accepted.view.tick == 2
        assert (accepted.quest_stage, accepted.quest_reward) == (1, 0)
        before = owner.owner.snapshot(), owner.owner.protocol()
        retried = owner.retry()
        assert retried.view == accepted.view
        assert not any(line.startswith("NPC 활동 현황") for line in retried.messages)
        assert (owner.owner.snapshot(), owner.owner.protocol()) == before
        reminder = owner.act("talk")
        assert selected.dialogue.text("reminder") in "\n".join(reminder.messages)
        assert reminder.messages[-1] == "NPC 활동 현황 · 3초 · 종 1회 · 호출 응답 0회."
        unrelated = owner.act("wait")
        assert unrelated.status == "COMMITTED"
        assert not any(line.startswith("NPC 활동 현황") for line in unrelated.messages)
    finally:
        owner.close()


@contextmanager
def _play_window(host: tk.Tk, path: Path) -> Iterator[PlayWindow]:
    selected = approved_content()
    gc.collect()
    panel = tk.Toplevel(host)
    panel.withdraw()
    screen = PlayWindow(
        panel, path, selected.definition.layout, quest_content=selected, npc_memory=True
    )
    try:
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None, screen.last_update
        assert screen.last_update.status == "ATTACHED", screen.last_update
        yield screen
    finally:
        screen.close()
        _pump(panel, lambda: screen.closed)
        screen.worker.join()


def test_real_tk_return_activity_reward_rewind_restart_and_replay(
    tmp_path: Path, tk_host: tk.Tk
) -> None:
    selected, working = approved_content(), tmp_path / "village.sqlite"
    npc = selected.definition.layout.npc_id
    with _play_window(tk_host, working) as screen:
        for action in GOAL[:5]:
            _click(screen, action)
        assert screen.view is not None
        assert (screen.view.actor_cell, screen.view.npc_cell, screen.view.tick) == (7, 6, 5)
        screen.wait_seconds.set("16")
        _click(screen, "wait")
        assert (screen.view.tick, screen.view.npc_bells) == (21, 10)
        assert screen.last_update is not None
        # Eight wakes at6,8,...20;do not substitute one aggregate tick21 action.
        bells = tuple(line for line in screen.last_update.messages if "종을 울렸습니다" in line)
        assert bells == tuple(f"NPC가 종을 울렸습니다. (누적 {count}회)" for count in range(3, 11))
        for action in GOAL[5:]:
            _click(screen, action)
        assert (
            screen.view.tick,
            screen.view.revision,
            screen.view.actor_hp,
            screen.view.enemy_hp,
            screen.view.npc_bells,
        ) == (25, 10, 1, 0, 12)
        before_report = read_memory(working, selected, npc)
        assert [(entry.kind, entry.observed_at) for entry in before_report.entries] == [
            ("accepted", 2)
        ]
        assert before_report.source.known_phase == "accepted"
        _click(screen, "save")
        _click(screen, "left")
        _click(screen, "talk")
        assert (screen.last_update.quest_stage, screen.last_update.quest_reward) == (3, 1)
        assert "NPC 활동 현황 · 27초 · 종 13회 · 호출 응답 0회." in screen.history[-1]
        assert selected.dialogue.text("completion") in screen.log_text.get("1.0", "end")
        completed = read_memory(working, selected, npc)
        assert [(entry.kind, entry.observed_at) for entry in completed.entries] == [
            ("accepted", 2),
            ("completion_reported", 27),
        ]
        assert (
            object_value(array_value(completed.document()["evidence"])[1])["certainty"]
            == "reported"
        )
        committed_bytes, committed_view = working.read_bytes(), screen.view
        _click(screen, "retry")
        assert screen.view == committed_view and working.read_bytes() == committed_bytes
        assert not any(line.startswith("NPC 활동 현황") for line in screen.last_update.messages)
        _click(screen, "talk")
        assert screen.last_update.quest_reward == 1
        assert screen.last_update.messages[-1] == "NPC 활동 현황 · 28초 · 종 14회 · 호출 응답 0회."
        assert read_memory(working, selected, npc).entries == completed.entries
        original_bytes = working.read_bytes()
        _click(screen, "load")
        assert (screen.view.tick, screen.view.npc_bells, screen.last_update.quest_reward) == (
            25,
            12,
            0,
        )
        branch = Path(screen.last_update.working_path)
        assert branch != working and working.read_bytes() == original_bytes
        assert read_memory(branch, selected, npc).entries == before_report.entries
    with _play_window(tk_host, branch) as resumed:
        assert resumed.view is not None and resumed.last_update is not None
        assert (resumed.view.tick, resumed.view.npc_bells, resumed.last_update.quest_stage) == (
            25,
            12,
            2,
        )
        _click(resumed, "left")
        _click(resumed, "talk")
        assert resumed.last_update.messages[-1] == "NPC 활동 현황 · 27초 · 종 13회 · 호출 응답 0회."
        assert resumed.last_update.quest_reward == 1
    bundle = memory_bundle(selected)
    store = SqliteCommitStore.open(branch, io=state_io((bundle,)))
    try:
        segment = store.retained_segment()
    finally:
        store.close()
    fixture = ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace)
    assert replay_runner(fixture, bundles=(bundle,)).run(segment.trace) == ()
    assert working.read_bytes() == original_bytes


def test_real_binary_pipe_return_and_new_process_restore(tmp_path: Path) -> None:
    selected, working = approved_content(), tmp_path / "pipe.sqlite"
    with memory_pipe(tmp_path, working) as pipe:
        for action in GOAL[:5]:
            pipe.send(action)
        send_seconds(pipe, "wait", "16")
        for action in GOAL[5:]:
            pipe.send(action)
        pipe.send("save")
        pipe.send("left")
        reported = object_value(pipe.send("talk")["update"])
        assert (
            array_value(reported["messages"])[-1]
            == "NPC 활동 현황 · 27초 · 종 13회 · 호출 응답 0회."
        )
        assert (reported["quest_stage"], reported["quest_reward"]) == ("3", "1")
        loaded = object_value(pipe.send("load")["update"])
        branch = Path(text_value(loaded["working_path"]))
        original_bytes = working.read_bytes()
    with memory_pipe(tmp_path, branch) as resumed:
        update = object_value(resumed.latest["update"])
        view = object_value(update["view"])
        assert (view["tick"], view["npc_bells"], update["quest_reward"]) == ("25", "12", "0")
        resumed.send("left")
        report = object_value(resumed.send("talk")["update"])
        assert (
            array_value(report["messages"])[-1] == "NPC 활동 현황 · 27초 · 종 13회 · 호출 응답 0회."
        )
        assert report["quest_reward"] == "1"
    assert working.read_bytes() == original_bytes
    assert [
        (entry.kind, entry.observed_at)
        for entry in read_memory(branch, selected, selected.definition.layout.npc_id).entries
    ] == [("accepted", 2), ("completion_reported", 27)]
