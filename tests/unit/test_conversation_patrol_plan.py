"""Bounded derived conversation-plan rendering;real snapshots are integration-tested."""

import pytest

from app.npc_activity import _ActivityFactory, _conversation_plan_messages
from contracts.persistence import SaveError
from tests.integration.test_conversation_patrol_plan import previous, recorded
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_patrol_next_step import BLOCKED, FREE_NEIGHBOR, IDLE


def factory(*, ready: bool = True) -> _ActivityFactory:
    content = approved_content()
    return _ActivityFactory(
        content,
        content.definition.layout.npc_id,
        npc_work=False,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
        npc_ready_patrol=ready,
    )


def test_empty_activity_and_first_talk_have_no_inferred_older_plan() -> None:
    owner = factory()
    assert _conversation_plan_messages(owner, 0) == (
        "NPC 대화 계획 기록 · 0초 이후 저장 구간의 최근 최대 2회입니다.",
        "NPC 대화 계획 기록 · 현재 저장 구간에 대화 종료 상태가 없습니다. "
        "현재 상태로 과거 계획을 추정하지 않습니다.",
    )
    owner.conversations = [(2, "talk2")]
    owner.conversation_plans = [(2, IDLE)]
    assert _conversation_plan_messages(owner, 0, recollection=True) == (
        "NPC 지난 대화 계획 · 현재 저장 구간에 이전 대화 종료 상태가 없습니다. "
        "현재 상태로 과거 계획을 추정하지 않습니다.",
    )
    assert _conversation_plan_messages(owner, 0)[1:] == (recorded(2, IDLE),)


def test_previous_and_activity_keep_their_original_projected_text() -> None:
    owner = factory()
    owner.conversations = [(9, "talk9"), (12, "talk12")]
    owner.conversation_plans = [(9, FREE_NEIGHBOR), (12, BLOCKED)]
    assert _conversation_plan_messages(owner, 2, recollection=True) == (previous(9, FREE_NEIGHBOR),)
    assert _conversation_plan_messages(owner, 2)[1:] == (
        recorded(9, FREE_NEIGHBOR),
        recorded(12, BLOCKED),
    )


@pytest.mark.parametrize("recollection", (False, True))
@pytest.mark.parametrize(
    "damage", ("missing", "foreign_tick", "older", "checkpoint", "reversed", "overflow")
)
def test_invalid_derived_window_rejects_the_actual_caller_code(
    damage: str,
    recollection: bool,
) -> None:
    owner = factory()
    owner.conversations = [(9, "talk9"), (12, "talk12")]
    owner.conversation_plans = [(9, FREE_NEIGHBOR), (12, BLOCKED)]
    if damage == "missing":
        owner.conversation_plans.pop()
    elif damage == "foreign_tick":
        owner.conversation_plans[0] = (8, FREE_NEIGHBOR)
    elif damage == "older":
        owner.conversations[0] = (1, "talk1")
        owner.conversation_plans[0] = (1, IDLE)
    elif damage == "checkpoint":
        owner.conversations[0] = (2, "talk2")
        owner.conversation_plans[0] = (2, IDLE)
    elif damage == "reversed":
        owner.conversations.reverse()
        owner.conversation_plans.reverse()
    else:
        owner.conversations.insert(0, (3, "talk3"))
        owner.conversation_plans.insert(0, (3, IDLE))
    expected = "NPC_RECOLLECTION_SOURCE" if recollection else "NPC_ACTIVITY_SOURCE"
    with pytest.raises(SaveError) as caught:
        _conversation_plan_messages(owner, 2, recollection=recollection)
    assert caught.value.code == expected
    assert "retained window differs" in str(caught.value)


@pytest.mark.parametrize("recollection", (False, True))
def test_older_modes_do_not_observe_new_derived_state(recollection: bool) -> None:
    owner = factory(ready=False)
    owner.conversations = [(2, "old")]
    assert _conversation_plan_messages(owner, 10, recollection=recollection) == ()
