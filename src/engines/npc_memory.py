"""Conversation evidence owner;no inference from objective enemy state."""

from __future__ import annotations

from contracts.dialogue import QuestBound
from contracts.errors import CandidateError
from contracts.npc_memory import MEMORY, MEMORY_FAMILY, MemoryDelta, read_record
from contracts.quest import QuestAccepted, QuestCompleted
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from domain.npc_memory import QuestEvidence, append_evidence
from domain.primitives import Phase


class NpcQuestMemory(QuestBound):
    @property
    def manifest(self) -> CapabilityManifest:
        access = PhaseAccess(Phase.POST_TICK, MEMORY_FAMILY)
        return CapabilityManifest(
            "quest.memory",
            (Phase.POST_TICK,),
            (access,),
            (access,),
            (),
            (),
            (QuestAccepted.SCHEMA, QuestCompleted.SCHEMA),
            "constant",
        )

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        if (
            invocation.phase != Phase.POST_TICK
            or invocation.wave != 0
            or invocation.action is not None
        ):
            raise CandidateError("INVALID_FACT", "memory invocation")
        definition = self.quest_content.definition
        owner = definition.layout.npc_id
        before = read_record(owner, invocation.state.component(MEMORY, owner))
        after = before
        for event in invocation.incoming:
            payload, header = event.payload, event.header
            if (
                type(payload) not in (QuestAccepted, QuestCompleted)
                or header.producer_id != "quest.rules"
                or header.phase != Phase.RESOLVE
                or header.wave != 0
                or header.sequence != 0
                or event.due_tick != invocation.logical_tick
                or header.occurred_at != invocation.logical_tick
                or header.type_key != payload.schema
                or not isinstance(payload, (QuestAccepted, QuestCompleted))
                or (payload.quest_id, payload.actor_id, payload.npc_id)
                != (definition.quest_id, definition.layout.actor_id, owner)
            ):
                raise CandidateError("INVALID_FACT", "memory source binding")
            if isinstance(payload, QuestCompleted) and (
                payload.reward_id != definition.reward_id
                or type(payload.amount) is not int
                or payload.amount != 1
            ):
                raise CandidateError("INVALID_FACT", "memory report reward")
            try:
                after = append_evidence(
                    after,
                    QuestEvidence(
                        "accepted" if type(payload) is QuestAccepted else "completion_reported",
                        invocation.logical_tick,
                        header.event_id,
                    ),
                )
            except ValueError as error:
                raise CandidateError("INVALID_FACT", "memory append") from error
        return EngineResult(() if after == before else (MemoryDelta(before, after),), (), ())
