"""Recall only the own plan at retained committed conversation ends."""

from pathlib import Path
from dataclasses import replace
import tkinter as tk
import pytest
import app.npc_activity as activity
from app.client_session import ClientSession
from app.client_worker import ClientWorker
from app.client import PlayWindow
from app.durable import create_durable
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.quest import QuestSpoken
from contracts.client import ClientAction
from domain.canonical import object_value
from tests.integration.test_call_native_scenario import lines
from contracts.replay import ReplaySession
from contracts.turn import ProtocolSnapshot
from domain.state_types import CoreSnapshot
from domain.primitives import EntityId, Tick
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_quest_patrol import state
from tests.integration.test_client import _click, _pump, tk_host as tk_host

from tests.integration.test_ready_patrol import session, ready_pipe, ready_bundle
from tests.integration.test_patrol_next_step import BLOCKED, FREE_NEIGHBOR, IDLE


def previous(tick: int, step: str) -> str:
    return f"NPC 지난 대화 계획 · {tick}초 대화 종료 상태: {step}"


def recorded(tick: int, step: str) -> str:
    return f"NPC 대화 계획 기록 · {tick}초 대화 종료 상태: {step}"


def test_previous_plan_uses_its_own_completed_conversation_context(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=6)
        update = owner.act("talk")
        assert update.status == "COMMITTED"
        assert update.view is not None and (update.view.tick, update.view.npc_cell) == (9, 6)
        assert FREE_NEIGHBOR in update.messages
        assert previous(2, IDLE) in update.messages
    finally:
        owner.close()


def test_activity_retains_then_blocked_plan_after_live_actor_moves(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        actions: tuple[tuple[ClientAction, int], ...] = (
            ("down", 1),
            ("talk", 1),
            ("wait", 6),
            ("talk", 1),
            ("wait", 1),
            ("down", 1),
            ("talk", 1),
            ("up", 1),
            ("wait", 1),
        )
        for action, seconds in actions:
            assert owner.act(action, seconds=seconds).status == "COMMITTED"
        update = owner.inspect_activity()
        assert update.status == "ACTIVITY_INSPECTED"
        assert update.view is not None and (update.view.tick, update.view.npc_cell) == (14, 6)
        assert FREE_NEIGHBOR in update.messages
        assert recorded(9, FREE_NEIGHBOR) in update.messages
        assert recorded(12, BLOCKED) in update.messages
        assert recorded(2, IDLE) not in update.messages
    finally:
        owner.close()


NO_PREVIOUS = (
    "NPC 지난 대화 계획 · 현재 저장 구간에 이전 대화 종료 상태가 없습니다. "
    "현재 상태로 과거 계획을 추정하지 않습니다."
)


def until_nine(owner: ClientSession) -> None:
    owner.act("down")
    first = owner.act("talk")
    assert NO_PREVIOUS in first.messages
    owner.act("wait", seconds=6)
    assert previous(2, IDLE) in owner.act("talk").messages


def test_empty_first_talk_rejected_talk_and_retry_do_not_fabricate_history(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        assert "현재 저장 구간에 대화 종료 상태가 없습니다." in " ".join(
            owner.inspect_activity().messages
        )
        until_nine(owner)
        before = state(owner)
        assert recorded(9, FREE_NEIGHBOR) in owner.inspect_activity().messages
        assert state(owner) == before
        owner.retry()
        assert state(owner) == before
        owner.act("wait")
        before = state(owner)
        assert owner.act("talk").status == "OUT_OF_RANGE"
        assert state(owner) == before
        rows = owner.inspect_activity().messages
        assert recorded(2, IDLE) in rows and recorded(9, FREE_NEIGHBOR) in rows
        owner.save("slot01")
        assert not any(
            line.startswith(("NPC 지난 대화 계획", "NPC 대화 계획 기록"))
            for line in owner.inspect_slot("slot01").messages
        )
    finally:
        owner.close()


def test_previous_save_branch_restart_and_rewind_restore_their_own_history(tmp_path: Path) -> None:
    path = tmp_path / "source/game.sqlite"
    owner = session(path)
    try:
        until_nine(owner)
        owner.save("slot01")
        owner.act("wait")
        owner.act("down")
        assert previous(9, FREE_NEIGHBOR) in owner.act("talk").messages
        owner.save("slot01")
        owner.act("up")
        owner.act("wait")
        source = path.read_bytes()
        owner.load("slot01", previous=True)
        branch = owner.owner.working_path
        assert branch != path
        before = state(owner)
        assert recorded(2, IDLE) in owner.inspect_activity().messages
        assert recorded(9, FREE_NEIGHBOR) in owner.inspect_activity().messages
        assert recorded(12, BLOCKED) not in owner.inspect_activity().messages
        assert state(owner) == before and path.read_bytes() == source
    finally:
        owner.close()
    owner = session(branch)
    try:
        before = state(owner)
        assert recorded(9, FREE_NEIGHBOR) in owner.inspect_activity().messages
        assert state(owner) == before
        assert owner.act("wait").view is not None
        assert path.read_bytes() == source
    finally:
        owner.close()


def test_compact_checkpoint_keeps_authoritative_memory_but_no_lost_plan_snapshot(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source/game.sqlite"
    owner = session(path)
    try:
        until_nine(owner)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        before_source = path.read_bytes()
    finally:
        owner.close()
    compact = tmp_path / "compact/game.sqlite"
    create_durable(compact, checkpoint, bundles=(ready_bundle(),)).close()
    owner = session(compact)
    try:
        assert not owner.owner.retained_segment().trace.steps
        rows = owner.inspect_activity().messages
        assert not any("9초 대화 종료 상태:" in line for line in rows)
        assert "현재 저장 구간에 대화 종료 상태가 없습니다." in " ".join(rows)
        update = owner.act("talk")
        assert NO_PREVIOUS in update.messages
        assert recorded(10, FREE_NEIGHBOR) in owner.inspect_activity().messages
        assert path.read_bytes() == before_source
    finally:
        owner.close()


@pytest.mark.parametrize("recollection", (False, True))
@pytest.mark.parametrize("damage", ("owner", "trace", "core", "protocol", "conversation"))
def test_damaged_sources_reject_without_publishing_history_or_changing_live_state(
    tmp_path: Path,
    damage: str,
    recollection: bool,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        until_nine(owner)
        segment = owner.owner.retained_segment()
        current = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        content = approved_content()
        npc_id = content.definition.layout.npc_id
        conversation: str = next(
            e.header.event_id
            for e in owner.owner.last_publication().facts
            if type(e.payload) is QuestSpoken
        )
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
        elif recollection:
            conversation = "missing-conversation"
        else:
            current = replace(current, core=replace(current.core, tick=Tick(current.core.tick - 1)))
        before = state(owner)
        code = "NPC_RECOLLECTION_SOURCE" if recollection else "NPC_ACTIVITY_SOURCE"
        flags = dict(
            npc_aid=True,
            npc_supply_aid=True,
            npc_call_aid=True,
            npc_patrol=True,
            npc_talk_pause=True,
            npc_quest_patrol=True,
            npc_call_pause=True,
            npc_ready_patrol=True,
        )
        with pytest.raises(SaveError) as caught:
            if recollection:
                activity.cycle_return_recollection(
                    segment,
                    npc_id,
                    content=content,
                    current=current,
                    conversation_id=conversation,
                    **flags,
                )
            else:
                activity.cycle_activity_messages(
                    segment, npc_id, content=content, current=current, **flags
                )
        assert caught.value.code == code and state(owner) == before
        assert recorded(9, FREE_NEIGHBOR) in owner.inspect_activity().messages
    finally:
        owner.close()


def test_one_existing_replay_captures_at_most_two_immutable_conversation_plans(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        until_nine(owner)
        owner.act("talk")
        original = activity._ActivityFactory.restore
        factories: list[activity._ActivityFactory] = []

        def counted(
            self: activity._ActivityFactory, core: CoreSnapshot, protocol: ProtocolSnapshot
        ) -> ReplaySession:
            factories.append(self)
            return original(self, core, protocol)

        monkeypatch.setattr(activity._ActivityFactory, "restore", counted)
        rows = owner.inspect_activity().messages
        assert len(factories) == 1
        assert factories[0].conversation_plans == [(9, FREE_NEIGHBOR), (10, FREE_NEIGHBOR)]
        assert recorded(9, FREE_NEIGHBOR) in rows and recorded(10, FREE_NEIGHBOR) in rows
        assert recorded(2, IDLE) not in rows
    finally:
        owner.close()


def test_real_worker_and_withdrawn_tk_display_prior_conversation_plan(
    tk_host: tk.Tk,
    tmp_path: Path,
) -> None:
    content = approved_content()
    worker = ClientWorker(
        tmp_path / "worker/game.sqlite",
        content.definition.layout,
        quest_content=content,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
        npc_ready_patrol=True,
    )
    try:
        for request in ("down", "talk"):
            worker.request(request).result(timeout=10)
        worker.request("wait", seconds=6).result(timeout=10)
        assert previous(2, IDLE) in worker.request("talk").result(timeout=10).messages
        assert recorded(9, FREE_NEIGHBOR) in worker.inspect_activity().result(timeout=10).messages
    finally:
        worker.join()
    panel = tk.Toplevel(tk_host)
    panel.withdraw()
    screen = PlayWindow(
        panel,
        tmp_path / "tk/game.sqlite",
        content.definition.layout,
        quest_content=content,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
        npc_ready_patrol=True,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        _click(screen, "down")
        _click(screen, "talk")
        assert NO_PREVIOUS in screen.log_text.get("1.0", "end")
        for _ in range(6):
            _click(screen, "wait")
        _click(screen, "talk")
        assert previous(2, IDLE) in screen.log_text.get("1.0", "end")
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())


def test_actual_framed_player_messages_recall_previous_goal_and_current_history(
    tmp_path: Path,
) -> None:
    with ready_pipe(tmp_path / "game.sqlite") as pipe:
        for action in ("attach", "down", "talk", *(["wait"] * 6)):
            pipe.send(action)
        result = object_value(pipe.send("talk")["update"])
        assert previous(2, IDLE) in lines(result)
        result = object_value(pipe.send("activity")["update"])
        assert recorded(9, FREE_NEIGHBOR) in lines(result)


def test_context_failure_after_commit_preserves_retry_and_logged_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        until_nine(owner)
        original = activity._conversation_plan_messages

        def fail(
            factory: activity._ActivityFactory, checkpoint_tick: int, *, recollection: bool = False
        ) -> tuple[str, ...]:
            if recollection:
                raise SaveError("NPC_RECOLLECTION_SOURCE", "injected display-context failure")
            return original(factory, checkpoint_tick, recollection=recollection)

        with monkeypatch.context() as patch:
            patch.setattr(activity, "_conversation_plan_messages", fail)
            with pytest.raises(SaveError, match="talk committed;recollection unavailable"):
                owner.act("talk")
        assert owner.owner.snapshot().tick == 10
        after = state(owner)
        retry = owner.retry()
        assert retry.status == "COMMITTED" and state(owner) == after
        assert not any(line.startswith("NPC 지난 대화 계획") for line in retry.messages)
        assert "recollection" in caplog.text
        assert recorded(10, FREE_NEIGHBOR) in owner.inspect_activity().messages
    finally:
        owner.close()
