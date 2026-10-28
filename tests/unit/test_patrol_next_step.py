"""Independent target truth table and snapshot-local movement condition boundaries."""

from dataclasses import replace
from typing import cast

import pytest

from app.npc_patrol_status import quest_patrol_next_step, quest_patrol_step_slot_messages
from contracts.persistence import SaveError
from domain.npc_memory import NpcQuestMemoryRecord, QuestEvidence, source_identity
from domain.npc_patrol import QuestPatrolPhase, quest_patrol_target
from domain.primitives import Tick
from domain.state_types import CoreSnapshot
from domain.trial import CellPositionRecord
from domain.watch import WatchNpcRecord
from tests.integration.test_patrol_next_step import BLOCKED, FREE_HOME, FREE_NEIGHBOR, IDLE
from tests.unit.quest_fixtures import content
from tests.unit.test_quest_patrol_slot import source


@pytest.mark.parametrize(
    "phase,current,expected",
    (
        ("available", 6, 6),
        ("accepted", 6, 7),
        ("accepted", 7, 6),
        ("reported", 7, 6),
        ("reported", 6, 6),
    ),
)
def test_target_uses_own_knowledge_and_existing_two_cells(
    phase: QuestPatrolPhase, current: int, expected: int
) -> None:
    assert quest_patrol_target(content().definition.layout, current, phase) == expected


@pytest.mark.parametrize("value", (True, False, -1, 0, 5, 8, 9, 6.0, "6", None))
def test_target_rejects_invalid_cell_types_or_non_patrol_cells(value: object) -> None:
    with pytest.raises(ValueError, match="^NPC_QUEST_PATROL_TARGET$"):
        quest_patrol_target(content().definition.layout, cast(int, value), "accepted")


@pytest.mark.parametrize("phase", (True, False, 0, None, "", "completed", "ACCEPTED"))
def test_target_rejects_unaccepted_phase_values(phase: object) -> None:
    with pytest.raises(ValueError, match="^NPC_QUEST_PATROL_TARGET$"):
        quest_patrol_target(content().definition.layout, 6, cast(QuestPatrolPhase, phase))


def test_unheard_npc_cannot_start_from_neighbor() -> None:
    with pytest.raises(ValueError, match="^NPC_QUEST_PATROL_TARGET$"):
        quest_patrol_target(content().definition.layout, 7, "available")


def core(phase: str, actor_cell: int = 0, *, tick: int = 4) -> CoreSnapshot:
    value = source(phase, tick)
    layout = content().definition.layout
    return replace(
        value,
        components=(
            *value.components,
            CellPositionRecord(layout.actor_id, layout.space_id, actor_cell),
        ),
    )


@pytest.mark.parametrize(
    "phase,actor,expected",
    (
        ("available", 6, IDLE),
        (
            "accepted",
            7,
            "NPC 다음 순찰 행동 · 옆 작업 지점을 플레이어가 점유 중입니다. 현재 상태에서는 이동을 기다립니다.",
        ),
        ("returning", 6, BLOCKED),
        ("returning", 0, FREE_HOME),
        ("home", 6, IDLE),
    ),
)
def test_step_uses_current_snapshot_conditions(phase: str, actor: int, expected: str) -> None:
    assert quest_patrol_next_step(
        core(phase, actor), content().definition.layout, error_code="NPC_ACTIVITY_SOURCE"
    ) == (expected,)


def test_zero_time_and_same_pose_can_have_different_goals() -> None:
    idle = core("available", tick=0)
    accepted = core("accepted", tick=2)
    rows = quest_patrol_step_slot_messages(idle, accepted, content().definition.layout)
    assert rows == (
        "NPC 다음 순찰 행동 비교 · 현재 2초 / 선택 저장 0초",
        "현재 " + FREE_NEIGHBOR,
        "선택 저장 " + IDLE,
    )


def test_saved_and_current_occupancy_are_independent_when_time_rewinds() -> None:
    live, saved = core("returning", 0, tick=2), core("returning", 6, tick=8)
    assert quest_patrol_step_slot_messages(saved, live, content().definition.layout) == (
        "NPC 다음 순찰 행동 비교 · 현재 2초 / 선택 저장 8초",
        "현재 " + FREE_HOME,
        "선택 저장 " + BLOCKED,
    )


def broken(kind: str) -> CoreSnapshot:
    good = core("returning", 6)
    records = list(good.components)
    actor = next(r for r in records if type(r) is CellPositionRecord)
    npc = next(r for r in records if type(r) is WatchNpcRecord)
    memory = next(r for r in records if type(r) is NpcQuestMemoryRecord)
    layout = content().definition.layout
    if kind.startswith("tick_"):
        value = {"tick_bool": True, "tick_negative": -1, "tick_overflow": 2**63}[kind]
        return replace(good, tick=cast(Tick, value))
    if kind == "missing_actor":
        records.remove(actor)
    elif kind == "duplicate_actor":
        records.append(actor)
    elif kind == "foreign_actor":
        records[records.index(actor)] = replace(actor, entity_id=layout.npc_id)
    elif kind == "actor_space":
        records[records.index(actor)] = replace(actor, space_id=layout.npc_id)
    elif kind in ("actor_bool", "actor_negative", "actor_high"):
        value = {"actor_bool": True, "actor_negative": -1, "actor_high": 9}[kind]
        records[records.index(actor)] = replace(actor, cell=value)
    elif kind == "missing_npc":
        records.remove(npc)
    elif kind == "duplicate_npc":
        records.append(npc)
    elif kind == "npc_space":
        records[records.index(npc)] = replace(npc, space_id=layout.actor_id)
    elif kind == "npc_bool":
        records[records.index(npc)] = replace(npc, cell=True)
    elif kind == "missing_memory":
        records.remove(memory)
    elif kind == "duplicate_memory":
        records.append(memory)
    elif kind == "future_memory":
        records[records.index(memory)] = replace(
            memory, entries=(QuestEvidence("accepted", 5, source_identity(good.world_id, 5)),)
        )
    else:
        assert kind == "unheard_neighbor"
        records[records.index(memory)] = replace(memory, entries=())
    return replace(good, components=tuple(records))


BAD = (
    "tick_bool",
    "tick_negative",
    "tick_overflow",
    "missing_actor",
    "duplicate_actor",
    "foreign_actor",
    "actor_space",
    "actor_bool",
    "actor_negative",
    "actor_high",
    "missing_npc",
    "duplicate_npc",
    "npc_space",
    "npc_bool",
    "missing_memory",
    "duplicate_memory",
    "future_memory",
    "unheard_neighbor",
)


@pytest.mark.parametrize("kind", BAD)
@pytest.mark.parametrize("error_code", ("NPC_ACTIVITY_SOURCE", "NPC_RECOLLECTION_SOURCE"))
def test_invalid_projection_retains_exact_callers_error_code(kind: str, error_code: str) -> None:
    with pytest.raises(SaveError) as caught:
        quest_patrol_next_step(broken(kind), content().definition.layout, error_code=error_code)
    assert caught.value.code == error_code


@pytest.mark.parametrize("kind", BAD)
@pytest.mark.parametrize("saved_side", (False, True))
def test_invalid_either_slot_snapshot_rejects_without_cross_borrowing(
    kind: str, saved_side: bool
) -> None:
    good, invalid = core("returning"), broken(kind)
    with pytest.raises(SaveError) as caught:
        quest_patrol_step_slot_messages(
            invalid if saved_side else good,
            good if saved_side else invalid,
            content().definition.layout,
        )
    assert caught.value.code == "SAVE_INSPECT_FAILED"
