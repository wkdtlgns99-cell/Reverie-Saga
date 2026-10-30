"""Historical support text belongs to its own verified conversation-end snapshot."""

from pathlib import Path
from dataclasses import replace
import pytest

import app.npc_activity as activity
from app.client import PlayWindow
from app.client_session import ClientSession
from app.durable import create_durable
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.quest import QuestSpoken
from contracts.replay import ReplaySession
from contracts.turn import ProtocolSnapshot
from domain.canonical import array_value, object_value
from domain.state_types import CoreSnapshot
from tests.integration.test_reach_gate_aid import driver, session, bundle
from tests.integration.test_ready_patrol import session as old_session
from tests.integration.test_quest_patrol import state
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_client import _click, _pump
from tests.integration.test_pending_query_feedback import window as window, tk_host as tk_host


SHORT = "NPC 지원 계획 · 공동 물자 2개를 더 확보하면 통행 지원을 준비합니다. (현재 0/3개)."
SHORT_ONE = "NPC 지원 계획 · 공동 물자 1개를 더 확보하면 통행 지원을 준비합니다. (현재 1/3개)."
FAR = "NPC 지원 계획 · 공동 물자가 확보되어 통행문 옆 작업 지점에 도착해야 통행을 도울 수 있습니다."
NEAR = "NPC 지원 계획 · 공동 물자가 확보되어 가까이 있는 NPC에게 통행 지원을 요청할 수 있습니다."
OPEN = "NPC 지원 계획 · 통행문이 열려 있어 공동 물자 준비를 이어갑니다."
PREVIOUS = "NPC 지난 대화 지원 계획 · "
RECORD = "NPC 대화 지원 계획 기록 · "
NO_PREVIOUS = (
    PREVIOUS + "현재 저장 구간에 이전 대화 종료 상태가 없습니다. "
    "현재 상태로 과거 계획을 추정하지 않습니다."
)


def previous(tick: int, text: str) -> str:
    return f"{PREVIOUS}{tick}초 대화 종료 상태: {text}"


def recorded(tick: int, text: str) -> str:
    return f"{RECORD}{tick}초 대화 종료 상태: {text}"


def until_nine(owner: ClientSession) -> None:
    assert owner.act("down").status == "COMMITTED"
    assert owner.act("talk").status == "COMMITTED"
    assert owner.act("wait", seconds=6).status == "COMMITTED"
    assert owner.act("talk").status == "COMMITTED"


@pytest.mark.parametrize("framed", (False, True), ids=("direct", "real-pipe"))
def test_retained_support_uses_own_stock_pose_gate_and_readonly_history(
    tmp_path: Path, framed: bool
) -> None:
    path = tmp_path / "game.sqlite"
    with driver(path, framed) as send:
        send("down")
        first = send("talk")
        assert NO_PREVIOUS in array_value(first["messages"])
        for _ in range(6):
            send("wait")
        second = send("talk")
        assert object_value(second["view"])["tick"] == "9"
        assert previous(2, SHORT) in array_value(second["messages"])
        send("wait")
        send("down")
        third = send("talk")
        assert object_value(third["view"])["tick"] == "12"
        assert previous(9, FAR) in array_value(third["messages"])
        send("up")
        send("wait")
        raw = path.read_bytes()
        activity = send("activity")
        assert object_value(activity["view"])["tick"] == "14"
        rows = array_value(activity["messages"])
        assert OPEN in rows and recorded(9, FAR) in rows and recorded(12, NEAR) in rows
        assert recorded(2, SHORT) not in rows
        assert path.read_bytes() == raw
        retry = send("retry")
        assert not any(
            isinstance(line, str) and line.startswith((PREVIOUS, RECORD))
            for line in array_value(retry["messages"])
        )
        assert path.read_bytes() == raw


def test_previous_save_restart_and_rejected_talk_keep_own_window(tmp_path: Path) -> None:
    path = tmp_path / "source/game.sqlite"
    owner = session(path)
    try:
        until_nine(owner)
        assert owner.save("slot01").status == "SAVED"
        owner.act("wait")
        before = state(owner)
        assert owner.act("talk").status == "OUT_OF_RANGE"
        assert state(owner) == before
        owner.act("down")
        assert previous(9, FAR) in owner.act("talk").messages
        owner.save("slot01")
        raw = path.read_bytes()
        owner.load("slot01", previous=True)
        branch = owner.owner.working_path
        assert branch != path
        before = state(owner)
        rows = owner.inspect_activity().messages
        assert recorded(2, SHORT) in rows and recorded(9, FAR) in rows
        assert recorded(12, NEAR) not in rows
        assert state(owner) == before and path.read_bytes() == raw
    finally:
        owner.close()
    owner = session(branch)
    try:
        assert recorded(9, FAR) in owner.inspect_activity().messages
        assert previous(9, FAR) in owner.act("talk").messages
        assert path.read_bytes() == raw
    finally:
        owner.close()


def test_compact_checkpoint_has_no_invented_support_history(tmp_path: Path) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        until_nine(owner)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    path = tmp_path / "compact/game.sqlite"
    create_durable(path, checkpoint, bundles=(bundle(),)).close()
    owner = session(path)
    try:
        raw, before = path.read_bytes(), state(owner)
        rows = owner.inspect_activity().messages
        assert (
            RECORD
            + "현재 저장 구간에 대화 종료 상태가 없습니다. "
            + ("현재 상태로 과거 계획을 추정하지 않습니다.")
            in rows
        )
        assert not any(line.startswith(RECORD + "9초 대화 종료 상태:") for line in rows)
        assert state(owner) == before and path.read_bytes() == raw
        assert NO_PREVIOUS in owner.act("talk").messages
    finally:
        owner.close()


def test_one_replay_keeps_only_two_support_snapshots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        until_nine(owner)
        owner.act("wait")
        owner.act("down")
        owner.act("talk")
        original = activity._ActivityFactory.restore
        factories: list[activity._ActivityFactory] = []

        def counted(
            self: activity._ActivityFactory, core: CoreSnapshot, protocol: ProtocolSnapshot
        ) -> ReplaySession:
            factories.append(self)
            return original(self, core, protocol)

        monkeypatch.setattr(activity._ActivityFactory, "restore", counted)
        owner.inspect_activity()
        assert len(factories) == 1
        assert factories[0].conversation_support_plans == [(9, FAR), (12, NEAR)]
    finally:
        owner.close()


@pytest.mark.parametrize("recollection", (False, True))
@pytest.mark.parametrize(
    "damage", ("missing", "duplicate", "before_checkpoint", "misaligned", "trace")
)
def test_invalid_retained_support_source_is_explicit_and_preserves_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recollection: bool, damage: str
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        until_nine(owner)
        original = activity._conversation_plan_messages

        def observed(
            factory: activity._ActivityFactory,
            checkpoint_tick: int,
            *,
            recollection: bool = False,
            support: bool = False,
        ) -> tuple[str, ...]:
            # Alter derived history only after the real replay has verified its source.
            if support:
                if damage == "missing":
                    factory.conversation_support_plans.pop()
                elif damage == "duplicate":
                    factory.conversation_support_plans[-1] = factory.conversation_support_plans[0]
                elif damage == "before_checkpoint":
                    factory.conversation_support_plans[0] = (0, SHORT)
                elif damage == "misaligned":
                    factory.conversation_support_plans[-1] = (8, FAR)
            return original(factory, checkpoint_tick, recollection=recollection, support=support)

        before = state(owner)
        segment = owner.owner.retained_segment()
        if damage == "trace":
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
        flags = dict(
            npc_aid=True,
            npc_supply_aid=True,
            npc_call_aid=True,
            npc_patrol=True,
            npc_talk_pause=True,
            npc_quest_patrol=True,
            npc_call_pause=True,
            npc_ready_patrol=True,
            npc_reach_aid=True,
        )
        content = approved_content()
        with monkeypatch.context() as patch:
            patch.setattr(activity, "_conversation_plan_messages", observed)
            with pytest.raises(SaveError) as caught:
                if recollection:
                    # The real last QuestSpoken identity comes from the retained memory.
                    conversation = next(
                        event.header.event_id
                        for event in owner.owner.last_publication().facts
                        if isinstance(event.payload, QuestSpoken)
                    )
                    activity.cycle_return_recollection(
                        segment,
                        content.definition.layout.npc_id,
                        content=content,
                        current=DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol()),
                        conversation_id=conversation,
                        **flags,
                    )
                else:
                    activity.cycle_activity_messages(
                        segment,
                        content.definition.layout.npc_id,
                        content=content,
                        current=DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol()),
                        **flags,
                    )
            expected = "NPC_RECOLLECTION_SOURCE" if recollection else "NPC_ACTIVITY_SOURCE"
            assert caught.value.code == expected
        assert state(owner) == before
        assert recorded(9, FAR) in owner.inspect_activity().messages
    finally:
        owner.close()


def test_old_ready_mode_does_not_add_support_history(tmp_path: Path) -> None:
    owner = old_session(tmp_path / "game.sqlite")
    try:
        until_nine(owner)
        for update in (owner.act("talk"), owner.inspect_activity()):
            assert not any(line.startswith((PREVIOUS, RECORD)) for line in update.messages)
    finally:
        owner.close()


def test_actual_worker_tk_history_and_input_remain_usable(window: PlayWindow) -> None:
    _click(window, "talk")
    assert previous(2, SHORT) in window.log_text.get("1.0", "end")
    assert window.view is not None
    before = window.view
    window._inspect_activity()
    _pump(window.root, lambda: not window.busy)
    assert window.status.get() == "ACTIVITY_INSPECTED" and window.view == before
    assert recorded(3, SHORT) in window.log_text.get("1.0", "end")
    _click(window, "wait")
    assert window.view is not None and window.view.tick == before.tick + 1


def test_support_projection_failure_after_commit_preserves_truth_and_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        until_nine(owner)

        def fail(*args: object, **kwargs: object) -> tuple[str, ...]:
            raise SaveError("NPC_RECOLLECTION_SOURCE", "support snapshot unavailable")

        with monkeypatch.context() as patch:
            patch.setattr(activity, "supply_support_plan", fail)
            with pytest.raises(SaveError, match="talk committed;recollection unavailable"):
                owner.act("talk")
        assert owner.owner.snapshot().tick == 10
        before = state(owner)
        assert owner.retry().status == "COMMITTED" and state(owner) == before
        assert "recollection" in caplog.text
        assert recorded(10, SHORT_ONE) in owner.inspect_activity().messages
        assert owner.act("wait").status == "COMMITTED"
    finally:
        owner.close()
