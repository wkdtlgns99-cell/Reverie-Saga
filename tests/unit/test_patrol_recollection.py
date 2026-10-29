"""Independent bounded patrol-context rendering and source-window guards."""

from dataclasses import replace
from typing import cast

import pytest

from app.npc_activity import _ActivityFactory, _patrol_messages
from contracts.messages import EventHeader, WorldEvent
from contracts.npc_patrol import NpcPatrolled
from contracts.persistence import SaveError
from contracts.watch import NpcActed
from domain.primitives import EntityId, EventId, Phase, Tick
from tests.unit.quest_fixtures import content

EMPTY = "현재 확인 범위에 남은 순찰 이동이 없습니다. 현재 위치로 과거 이동을 추정하지 않습니다."


def factory(*, enabled: bool = True) -> _ActivityFactory:
    selected = content()
    return _ActivityFactory(
        selected,
        selected.definition.layout.npc_id,
        npc_work=False,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=enabled,
    )


def movement(tick: int, before: int = 6, after: int = 7) -> WorldEvent:
    layout = content().definition.layout
    payload = NpcPatrolled(layout.npc_id, layout.space_id, before, after)
    header = EventHeader(
        EventId("e1-" + str(tick).zfill(64)),
        payload.schema,
        "watch.npc",
        Tick(tick),
        Phase.POST_TICK,
        0,
        0,
        0,
        (EventId("e1-" + "f" * 64),),
        (),
    )
    return WorldEvent(header, Tick(tick), payload)


@pytest.mark.parametrize("total", (0, 1, 2, 3, 4, 8))
def test_recent_three_is_bounded_but_count_includes_all_retained(total: int) -> None:
    own = factory()
    events = tuple(
        movement(2 * (index + 1), 6 if index % 2 == 0 else 7, 7 if index % 2 == 0 else 6)
        for index in range(total)
    )
    own.observe_patrol(events)
    text = _patrol_messages(own, 0)
    assert len(own.patrols) == min(3, total) and own.patrol_count == total
    assert text[0] == "NPC 순찰 활동 · 0초 이후 저장 구간의 최근 최대 3건입니다."
    if not total:
        assert text == (text[0], EMPTY)
    else:
        assert text[1] == f"확인한 순찰 이동 {total}건 중 최근 {min(3, total)}건입니다."
        assert tuple(int(line.split(" · ", 1)[1].split("초:", 1)[0]) for line in text[2:]) == tuple(
            range(max(2, 2 * total - 4), 2 * total + 1, 2)
        )


def test_factual_endpoints_not_clock_parity_choose_description() -> None:
    own = factory()
    own.observe_patrol(
        (movement(28), movement(20, 7, 6), movement(14), movement(6, 7, 6), movement(2))
    )
    assert _patrol_messages(own, 0)[1:] == (
        "확인한 순찰 이동 5건 중 최근 3건입니다.",
        "NPC 순찰 기록 · 14초: 옆 작업 지점으로 이동했습니다.",
        "NPC 순찰 기록 · 20초: 원래 자리로 돌아왔습니다.",
        "NPC 순찰 기록 · 28초: 옆 작업 지점으로 이동했습니다.",
    )


def test_previous_post_publication_snapshot_excludes_current_turn_from_next_window() -> None:
    own = factory()
    own.observe_patrol((movement(2), movement(4, 7, 6)))
    own.conversation_patrols = [1, 2]
    assert _patrol_messages(own, 0, previous=2, recollection=True) == (
        "NPC 순찰 회상 · 지난 대화(2초) 뒤에 이동한 기록입니다.",
        "확인한 순찰 이동 1건 중 최근 1건입니다.",
        "NPC 순찰 회상 · 4초: 원래 자리로 돌아왔습니다.",
    )
    own.conversation_patrols = [2, 2]
    assert _patrol_messages(own, 0, previous=4, recollection=True)[1:] == (EMPTY,)


def test_other_npc_and_nonmovement_facts_are_not_self_patrol() -> None:
    own = factory()
    event = movement(2)
    foreign = replace(
        event, payload=replace(cast(NpcPatrolled, event.payload), npc_id=EntityId("actor:other"))
    )
    ordinary = replace(event, payload=NpcActed(content().definition.layout.npc_id, 0, 1))
    own.observe_patrol((foreign, ordinary, event))
    assert own.patrols == [event] and own.patrol_count == 1


@pytest.mark.parametrize("recollection", (False, True))
@pytest.mark.parametrize(
    "damage", ("negative", "missing_rows", "missing_count", "missing_snapshot", "old_snapshot")
)
def test_inconsistent_context_never_becomes_fabricated_history(
    damage: str, recollection: bool
) -> None:
    own = factory()
    own.observe_patrol((movement(2),))
    previous = None
    if damage == "negative":
        own.patrol_count = -1
    elif damage == "missing_rows":
        own.patrols = []
    elif damage == "missing_count":
        own.patrol_count = 0
    elif damage == "missing_snapshot":
        previous = 2
    else:
        previous = 2
        own.conversation_patrols = [0, 1]
    code = "NPC_RECOLLECTION_SOURCE" if recollection else "NPC_ACTIVITY_SOURCE"
    with pytest.raises(SaveError, match="^" + code + ":"):
        _patrol_messages(own, 0, previous=previous, recollection=recollection)


@pytest.mark.parametrize("recollection", (False, True))
@pytest.mark.parametrize("damage", ("owner", "space", "identity", "endpoint", "type"))
def test_wrong_scope_or_endpoints_fail_explicitly(damage: str, recollection: bool) -> None:
    own = factory()
    event = movement(2)
    payload = cast(NpcPatrolled, event.payload)
    if damage == "owner":
        event = replace(event, payload=replace(payload, npc_id=EntityId("actor:other")))
    elif damage == "space":
        event = replace(event, payload=replace(payload, space_id=EntityId("space:other")))
    elif damage == "identity":
        event = replace(event, payload=replace(payload, after_cell=6))
    elif damage == "endpoint":
        event = replace(event, payload=replace(payload, after_cell=8))
    else:
        event = replace(event, payload=NpcActed(content().definition.layout.npc_id, 0, 1))
    own.patrols = [event]
    own.patrol_count = 1
    code = "NPC_RECOLLECTION_SOURCE" if recollection else "NPC_ACTIVITY_SOURCE"
    with pytest.raises(SaveError, match="^" + code + ":"):
        _patrol_messages(own, 0, recollection=recollection)


def test_older_modes_have_no_observation_or_new_section() -> None:
    own = factory(enabled=False)
    own.observe_patrol((movement(2),))
    assert own.patrols == [] and own.patrol_count == 0
    assert _patrol_messages(own, 0) == ()
    assert _patrol_messages(own, 0, previous=2, recollection=True) == ()
