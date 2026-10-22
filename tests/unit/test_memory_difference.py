from dataclasses import replace
from typing import cast

import pytest

from app.npc_memory_compare import memory_difference, slot_memory_messages
from contracts.dialogue import GenerationError
from domain.npc_memory import NpcQuestMemoryRecord, QuestEvidence
from domain.primitives import EntityId
from tests.unit.durability_fixtures import checkpoint

NPC = EntityId("actor:sentinel")
ACCEPTED = QuestEvidence("accepted", 2, "e1-" + "a" * 64)
REPORTED = QuestEvidence("completion_reported", 11, "e1-" + "b" * 64)


@pytest.mark.parametrize(
    "old,new,added,removed,retained",
    (
        ((), (), (), (), ()),
        ((), (ACCEPTED, REPORTED), (REPORTED, ACCEPTED), (), ()),
        ((ACCEPTED,), (ACCEPTED, REPORTED), (REPORTED,), (), (ACCEPTED,)),
        ((ACCEPTED, REPORTED), (ACCEPTED,), (), (REPORTED,), (ACCEPTED,)),
        ((ACCEPTED, REPORTED), (ACCEPTED, REPORTED), (), (), (REPORTED, ACCEPTED)),
    ),
)
def test_memory_identity_sets_are_exact_and_newest_first(
    old: tuple[QuestEvidence, ...],
    new: tuple[QuestEvidence, ...],
    added: tuple[QuestEvidence, ...],
    removed: tuple[QuestEvidence, ...],
    retained: tuple[QuestEvidence, ...],
) -> None:
    result = memory_difference(NpcQuestMemoryRecord(NPC, old), NpcQuestMemoryRecord(NPC, new))
    assert (result.added, result.removed, result.retained) == (added, removed, retained)


def test_same_kind_and_time_with_different_sources_is_not_shared() -> None:
    other = replace(ACCEPTED, source_event_id="e1-" + "c" * 64)
    result = memory_difference(
        NpcQuestMemoryRecord(NPC, (ACCEPTED,)), NpcQuestMemoryRecord(NPC, (other,))
    )
    assert result.added == (other,) and result.removed == (ACCEPTED,) and not result.retained


def test_memory_difference_rejects_identity_collision_and_owner() -> None:
    old = NpcQuestMemoryRecord(NPC, (ACCEPTED,))
    with pytest.raises(GenerationError, match="^NPC_MEMORY_COMPARISON_IDENTITY$"):
        memory_difference(old, NpcQuestMemoryRecord(NPC, (replace(ACCEPTED, observed_at=3),)))
    with pytest.raises(GenerationError, match="^NPC_MEMORY_COMPARISON_OWNER$"):
        memory_difference(old, NpcQuestMemoryRecord(EntityId("actor:other"), ()))
    with pytest.raises(GenerationError, match="^NPC_CONTEXT_INPUT$"):
        memory_difference(old, cast(NpcQuestMemoryRecord, None))


def test_slot_comparison_rejects_foreign_world_and_missing_memory() -> None:
    current = checkpoint()
    with pytest.raises(GenerationError, match="^NPC_MEMORY_COMPARISON_OWNER$"):
        slot_memory_messages(
            replace(current, core=replace(current.core, world_id="w1-" + "f" * 64)),
            current,
            NPC,
        )
    with pytest.raises(GenerationError, match="^NPC_CONTEXT_INPUT$"):
        slot_memory_messages(current, current, NPC)
