"""Patrol recall is reconstructed only from verified retained movement facts."""

from pathlib import Path
from dataclasses import replace
import tkinter as tk

import pytest

import app.npc_activity as activity
from app.client import PlayWindow
from app.client_worker import ClientWorker
from contracts.quest import QuestSpoken
from contracts.messages import WorldEvent
from contracts.replay import ReplaySession
from contracts.turn import ProtocolSnapshot
from domain.canonical import array_value, object_value, text_value
from domain.primitives import EntityId, Tick
from domain.state_types import CoreSnapshot
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_patrol import patrol_pipe

from app.durable import create_durable
from contracts.client import ClientUpdate
from contracts.persistence import DurableCheckpoint, SaveError
from tests.integration.test_npc_patrol import bundle, session

EMPTY = "현재 확인 범위에 남은 순찰 이동이 없습니다. 현재 위치로 과거 이동을 추정하지 않습니다."


def rows(update: ClientUpdate, *, recollection: bool = True) -> tuple[str, ...]:
    prefix = "NPC 순찰 회상 · " if recollection else "NPC 순찰 기록 · "
    return tuple(line for line in update.messages if line.startswith(prefix) and "초: " in line)


def row(tick: int, returned: bool = False, *, recollection: bool = True) -> str:
    prefix = "NPC 순찰 회상" if recollection else "NPC 순찰 기록"
    description = "원래 자리로 돌아왔습니다." if returned else "옆 작업 지점으로 이동했습니다."
    return f"{prefix} · {tick}초: {description}"


def test_first_talk_recalls_its_actual_post_tick_move(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        update = owner.act("talk")
        assert rows(update) == (row(2),)
        assert "NPC 순찰 회상 · 0초 이후 저장 구간의 이동입니다." in update.messages
        assert "확인한 순찰 이동 1건 중 최근 1건입니다." in update.messages
    finally:
        owner.close()


def test_activity_uses_recent_three_actual_moves_and_readonly_state(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=6)
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        update = owner.inspect_activity()
        assert rows(update, recollection=False) == (
            row(4, True, recollection=False),
            row(6, recollection=False),
            row(8, True, recollection=False),
        )
        assert "NPC 순찰 활동 · 0초 이후 저장 구간의 최근 최대 3건입니다." in update.messages
        assert "확인한 순찰 이동 4건 중 최근 3건입니다." in update.messages
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
    finally:
        owner.close()


def test_checkpoint_only_moved_position_does_not_invent_past(tmp_path: Path) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    path = tmp_path / "checkpoint/game.sqlite"
    create_durable(path, checkpoint, bundles=(bundle(),)).close()
    owner = session(path)
    try:
        view = owner.update().view
        assert view is not None and view.npc_cell == 7
        update = owner.inspect_activity()
        assert EMPTY in update.messages and rows(update, recollection=False) == ()
        assert "NPC 순찰 활동 · 2초 이후 저장 구간의 최근 최대 3건입니다." in update.messages
    finally:
        owner.close()


def test_conversation_windows_include_current_move_once_and_exclude_blocked_wake(
    tmp_path: Path,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        assert rows(owner.act("talk")) == (row(2),)
        owner.act("wait", seconds=6)
        talked = owner.act("talk")
        assert rows(talked) == (row(4, True), row(6), row(8, True))
        assert "확인한 순찰 이동 3건 중 최근 3건입니다." in talked.messages
        assert "NPC 순찰 회상 · 지난 대화(2초) 뒤에 이동한 기록입니다." in talked.messages
        talked = owner.act("talk")
        assert rows(talked) == (row(10),)
        assert "확인한 순찰 이동 1건 중 최근 1건입니다." in talked.messages
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        assert rows(owner.retry()) == ()
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
        rejected = owner.act("talk")
        assert rejected.status == "OUT_OF_RANGE" and rows(rejected) == ()
        owner.act("down")
        talked = owner.act("talk")
        assert talked.view is not None and talked.view.tick == 12 and talked.view.npc_cell == 7
        assert EMPTY in talked.messages and rows(talked) == ()
        assert "NPC 순찰 회상 · 지난 대화(10초) 뒤에 이동한 기록입니다." in talked.messages
        owner.act("up")
        owner.act("wait")
        assert rows(owner.act("talk")) == (row(14, True),)
    finally:
        owner.close()


def test_blocked_wakes_are_not_reported_as_moves_or_wait_memories(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("down")
        owner.act("wait", seconds=2)
        update = owner.inspect_activity()
        assert rows(update, recollection=False) == (row(2, recollection=False),)
        assert "확인한 순찰 이동 1건 중 최근 1건입니다." in update.messages
        owner.act("up")
        owner.act("wait")
        update = owner.inspect_activity()
        assert rows(update, recollection=False) == (
            row(2, recollection=False),
            row(6, True, recollection=False),
        )
    finally:
        owner.close()


def test_long_wait_count_is_complete_but_rows_and_repeated_query_are_bounded(
    tmp_path: Path,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("wait", seconds=16)
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        update = owner.inspect_activity()
        assert rows(update, recollection=False) == (
            row(12, True, recollection=False),
            row(14, recollection=False),
            row(16, True, recollection=False),
        )
        assert "확인한 순찰 이동 8건 중 최근 3건입니다." in update.messages
        assert owner.inspect_activity().messages == update.messages
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
    finally:
        owner.close()


def test_previous_saved_branch_restart_uses_only_its_retained_motion(tmp_path: Path) -> None:
    source = tmp_path / "game.sqlite"
    owner = session(source)
    try:
        owner.act("down")
        owner.act("talk")
        owner.save("slot01")
        owner.act("wait", seconds=6)
        owner.save("slot01")
        owner.act("talk")
        before = source.read_bytes()
        owner.load("slot01", previous=True)
        branch = owner.owner.working_path
        assert rows(owner.inspect_activity(), recollection=False) == (row(2, recollection=False),)
    finally:
        owner.close()
    owner = session(branch)
    try:
        assert rows(owner.inspect_activity(), recollection=False) == (row(2, recollection=False),)
        owner.act("wait", seconds=2)
        assert rows(owner.inspect_activity(), recollection=False) == (
            row(2, recollection=False),
            row(4, True, recollection=False),
        )
        talked = owner.act("talk")
        assert rows(talked) == (row(4, True),)
        assert "NPC 순찰 회상 · 지난 대화(2초) 뒤에 이동한 기록입니다." in talked.messages
        assert source.read_bytes() == before
    finally:
        owner.close()


def test_one_existing_replay_and_post_publication_conversation_snapshots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=6)
        original = activity._ActivityFactory.restore
        factories: list[activity._ActivityFactory] = []

        def counted(
            self: activity._ActivityFactory, core: CoreSnapshot, protocol: ProtocolSnapshot
        ) -> ReplaySession:
            factories.append(self)
            return original(self, core, protocol)

        monkeypatch.setattr(activity._ActivityFactory, "restore", counted)
        owner.inspect_activity()
        assert (
            len(factories) == 1
            and factories[0].patrol_count == 4
            and len(factories[0].patrols) == 3
        )
        factories.clear()
        owner.act("talk")
        assert len(factories) == 1 and factories[0].conversation_patrols == [1, 4]
        factories.clear()
        owner.act("talk")
        assert len(factories) == 1 and factories[0].conversation_patrols == [4, 5]
        assert len(factories[0].patrols) == 3
    finally:
        owner.close()


@pytest.mark.parametrize("recollection", (False, True))
@pytest.mark.parametrize("damage", ("owner", "trace", "core", "protocol", "mode"))
def test_corrupt_source_rejected_without_changing_truth(
    tmp_path: Path, damage: str, recollection: bool
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=6)
        owner.act("talk")
        segment = owner.owner.retained_segment()
        current = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        npc_id = approved_content().definition.layout.npc_id
        patrol = True
        if damage == "owner":
            npc_id = EntityId("actor:other")
        elif damage == "trace":
            segment = replace(
                segment,
                trace=replace(
                    segment.trace,
                    steps=(
                        replace(segment.trace.steps[0], expected_facts_hash="f" * 64),
                        *segment.trace.steps[1:],
                    ),
                ),
            )
        elif damage == "core":
            current = replace(current, core=replace(current.core, tick=Tick(current.core.tick + 1)))
        elif damage == "protocol":
            current = replace(current, protocol=replace(current.protocol, branch_id="f" * 32))
        else:
            patrol = False
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        code = "NPC_RECOLLECTION_SOURCE" if recollection else "NPC_ACTIVITY_SOURCE"
        with pytest.raises(SaveError, match="^" + code + ":"):
            if recollection:
                spoken = next(
                    event
                    for event in owner.owner.last_publication().facts
                    if isinstance(event.payload, QuestSpoken)
                )
                activity.cycle_return_recollection(
                    segment,
                    npc_id,
                    conversation_id=spoken.header.event_id,
                    content=approved_content(),
                    current=current,
                    npc_aid=True,
                    npc_supply_aid=True,
                    npc_call_aid=True,
                    npc_patrol=patrol,
                )
            else:
                activity.cycle_activity_messages(
                    segment,
                    npc_id,
                    content=approved_content(),
                    current=current,
                    npc_aid=True,
                    npc_supply_aid=True,
                    npc_call_aid=True,
                    npc_patrol=patrol,
                )
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
    finally:
        owner.close()


def test_wrong_current_conversation_does_not_become_a_fake_window(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        segment = owner.owner.retained_segment()
        current = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        before = owner.owner.working_path.read_bytes()
        with pytest.raises(SaveError, match="^NPC_RECOLLECTION_SOURCE:"):
            activity.cycle_return_recollection(
                segment,
                approved_content().definition.layout.npc_id,
                content=approved_content(),
                current=current,
                conversation_id="e1-" + "f" * 64,
                npc_aid=True,
                npc_supply_aid=True,
                npc_call_aid=True,
                npc_patrol=True,
            )
        assert owner.owner.working_path.read_bytes() == before
    finally:
        owner.close()


def test_context_failure_after_talk_retains_commit_and_retry_truth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=6)
        owner.act("talk")

        def fail(self: activity._ActivityFactory, facts: tuple[WorldEvent, ...]) -> None:
            raise SaveError("NPC_RECOLLECTION_SOURCE", "injected patrol context boundary failure")

        with monkeypatch.context() as patch:
            patch.setattr(activity._ActivityFactory, "observe_patrol", fail)
            with pytest.raises(SaveError, match="talk committed;recollection unavailable"):
                owner.act("talk")
        view = owner.update().view
        assert view is not None and view.tick == 10 and view.npc_cell == 7
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        assert rows(owner.retry()) == ()
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
        assert "committed cycle call recollection failed" in caplog.text
    finally:
        owner.close()


def test_worker_reads_actual_patrol_context(tmp_path: Path) -> None:
    selected = approved_content()
    worker = ClientWorker(
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
    )
    try:
        worker.request("down").result(timeout=10)
        assert rows(worker.request("talk").result(timeout=10)) == (row(2),)
        assert rows(worker.inspect_activity().result(timeout=10), recollection=False) == (
            row(2, recollection=False),
        )
    finally:
        worker.join()


def test_actual_framed_query_talk_and_retry_keep_source(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with patrol_pipe(path) as pipe:
        pipe.send("down")
        update = object_value(pipe.send("talk")["update"])
        text = tuple(text_value(line) for line in array_value(update["messages"]))
        assert row(2) in text
        before = path.read_bytes()
        update = object_value(pipe.send("activity")["update"])
        assert row(2, recollection=False) in array_value(update["messages"])
        update = object_value(pipe.send("retry")["update"])
        assert not any(
            text_value(line).startswith("NPC 순찰 회상 · ")
            for line in array_value(update["messages"])
        )
        assert path.read_bytes() == before


def test_actual_hidden_tk_talk_and_activity_display_context(tk_host: tk.Tk, tmp_path: Path) -> None:
    selected = approved_content()
    panel = tk.Toplevel(tk_host)
    panel.withdraw()
    screen = PlayWindow(
        panel,
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        _click(screen, "down")
        _click(screen, "talk")
        assert row(2) in screen.log_text.get("1.0", "end")
        assert screen.activity_button is not None
        screen.activity_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert row(2, recollection=False) in screen.log_text.get("1.0", "end")
    finally:
        screen.close()
