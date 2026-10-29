"""Both snapshot goals delegate the established own-memory/physical-pose projection."""

from dataclasses import replace

import pytest

from app.npc_cycle import bootstrap_cycle
from app.npc_patrol_status import quest_patrol_slot_messages
from app.watch import WatchBootstrapSpec
from contracts.persistence import SaveError
from domain.npc_memory import NpcQuestMemoryRecord, QuestEvidence, source_identity
from domain.primitives import Tick
from domain.state_types import CoreSnapshot
from domain.watch import WatchNpcRecord
from tests.integration.test_quest_patrol_slot import UNHEARD, expected
from tests.integration.test_quest_patrol import ACCEPTED, RETURNING, HOME
from tests.unit.quest_fixtures import content


TEXT = {"available": UNHEARD, "accepted": ACCEPTED, "returning": RETURNING, "home": HOME}


def source(phase: str, tick: int = 4) -> CoreSnapshot:
    selected = content()
    core = bootstrap_cycle(
        WatchBootstrapSpec("0" * 64, "1" * 32, "2" * 32),
        selected,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
    ).snapshot()
    count = {"available": 0, "accepted": 1, "returning": 2, "home": 2}[phase]
    entries = (
        QuestEvidence("accepted", 1, source_identity(core.world_id, 1)),
        QuestEvidence("completion_reported", 2, source_identity(core.world_id, 2)),
    )[:count]
    layout = selected.definition.layout
    return replace(
        core,
        tick=Tick(tick),
        components=(
            NpcQuestMemoryRecord(layout.npc_id, entries),
            WatchNpcRecord(layout.npc_id, layout.space_id, 7 if phase == "returning" else 6, 0),
        ),
    )


@pytest.mark.parametrize("current", tuple(TEXT))
@pytest.mark.parametrize("saved", tuple(TEXT))
def test_all_goal_pairs_keep_selected_identity_when_time_is_rewound(
    current: str, saved: str
) -> None:
    live, old = source(current, 2), source(saved, 4)
    assert quest_patrol_slot_messages(old, live, content().definition.layout) == expected(
        2, 4, TEXT[current], TEXT[saved]
    )


def test_zero_time_equal_pose_and_empty_knowledge_are_valid() -> None:
    core = source("available", 0)
    assert quest_patrol_slot_messages(core, core, content().definition.layout) == expected(
        0, 0, UNHEARD, UNHEARD
    )


@pytest.mark.parametrize("saved_side", (False, True))
@pytest.mark.parametrize(
    "bad",
    (
        "missing_memory",
        "missing_npc",
        "duplicate_memory",
        "duplicate_npc",
        "other_owner",
        "future",
        "unheard_neighbor",
        "wrong_space",
        "bool_cell",
    ),
)
def test_invalid_either_snapshot_preserves_save_inspect_error(saved_side: bool, bad: str) -> None:
    good = source("available")
    records = list(good.components)
    memory = next(r for r in records if type(r) is NpcQuestMemoryRecord)
    npc = next(r for r in records if type(r) is WatchNpcRecord)
    layout = content().definition.layout
    if bad == "missing_memory":
        records.remove(memory)
    elif bad == "missing_npc":
        records.remove(npc)
    elif bad == "duplicate_memory":
        records.append(memory)
    elif bad == "duplicate_npc":
        records.append(npc)
    elif bad == "other_owner":
        records[records.index(memory)] = replace(memory, entity_id=layout.actor_id)
    elif bad == "future":
        records[records.index(memory)] = replace(
            memory, entries=(QuestEvidence("accepted", 5, source_identity(good.world_id, 5)),)
        )
    else:
        records[records.index(npc)] = replace(
            npc,
            cell=True if bad == "bool_cell" else 7 if bad == "unheard_neighbor" else 6,
            space_id=layout.actor_id if bad == "wrong_space" else layout.space_id,
        )
    broken = replace(good, components=tuple(records))
    with pytest.raises(SaveError) as caught:
        quest_patrol_slot_messages(
            broken if saved_side else good, good if saved_side else broken, layout
        )
    assert caught.value.code == "SAVE_INSPECT_FAILED"
