"""Canonical bounded prose job from validated persisted conversation evidence."""

from __future__ import annotations

from app.dialogue_prepare import harbor_brief
from app.npc_memory_query import EvidenceQuery, select_evidence
from app.quest_definition import harbor_definition
from contracts.dialogue import DialogueBrief, GenerationError
from contracts.npc_memory import NpcMemoryContext
from domain.canonical import array_value, canonical_json, object_value


def memory_brief(context: NpcMemoryContext) -> DialogueBrief:
    if type(context) is not NpcMemoryContext:
        raise GenerationError("NPC_CONTEXT_INPUT")
    source = context.source
    definition = harbor_definition()
    if (source.npc_id, source.actor_id, source.quest_id) != (
        definition.layout.npc_id,
        definition.layout.actor_id,
        definition.quest_id,
    ):
        raise GenerationError("NPC_CONTEXT_OWNER")
    # All two scoped records fit;rank newest first without dropping required evidence.
    documents = {
        object_value(value)["memory_id"]: value
        for value in array_value(context.document()["evidence"])
    }
    evidence = tuple(
        documents[entry.memory_id(source.npc_id)]
        for entry in select_evidence(context, EvidenceQuery())
    )
    return DialogueBrief(
        harbor_brief().text
        + "\nPersisted NPC conversation evidence: "
        + canonical_json(
            {
                "npc_id": source.npc_id,
                "actor_id": source.actor_id,
                "quest_id": source.quest_id,
                "known_phase": source.known_phase,
                "recorded_favor": source.recorded_favor,
                "evidence": evidence,
            }
        ).decode()
        + "\nUse only these remembered conversations. Acceptance is observed;completion is a player report,"
        "not witnessed enemy death. No invented conversations,timestamps,places or extra rewards. "
        "Generate four conditional branches;completion/gratitude apply only after a report. "
        "Name the single recorded reward 포구의 호의. Logical ticks are game time,not calendar dates."
    )
