"""Authoritative one-quest rules;no prose/provider or sibling engine dependency."""

from __future__ import annotations

from contracts.dialogue import QuestBound
from contracts.encounter import HIT_POINTS
from contracts.errors import CandidateError
from contracts.messages import EmittedFact, FactPayload, StateDelta
from contracts.quest import (
    QUEST,
    STAGE_FAMILY,
    GoalMet,
    QuestAccepted,
    QuestCompleted,
    QuestSpoken,
    QuestStageDelta,
    QuestTalkCommand,
)
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from domain.primitives import EntityId, FieldFamily, Phase


class QuestRules(QuestBound):
    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            "quest.rules",
            (Phase.RESOLVE, Phase.POST_TICK),
            (
                PhaseAccess(Phase.RESOLVE, STAGE_FAMILY),
                PhaseAccess(Phase.POST_TICK, STAGE_FAMILY),
                PhaseAccess(Phase.POST_TICK, FieldFamily("encounter.hp", "hp")),
            ),
            tuple(PhaseAccess(phase, STAGE_FAMILY) for phase in (Phase.RESOLVE, Phase.POST_TICK)),
            (),
            (QuestAccepted.SCHEMA, GoalMet.SCHEMA, QuestCompleted.SCHEMA, QuestSpoken.SCHEMA),
            (),
            "local",
        )

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        definition = self.quest_content.definition
        entity = EntityId(definition.quest_id)
        if invocation.wave != 0 or invocation.incoming:
            raise CandidateError("INVALID_FACT", "quest invocation scope")
        stage = invocation.state.component(QUEST, entity).stage
        deltas: tuple[StateDelta, ...] = ()
        facts: list[FactPayload] = []
        if invocation.phase == Phase.RESOLVE:
            action = invocation.action
            if (
                action is None
                or type(action.payload) is not QuestTalkCommand
                or action.actor_id != definition.layout.actor_id
                or action.payload.npc_id != definition.layout.npc_id
            ):
                raise CandidateError("INVALID_ACTION", "quest talk binding")
            intent = ("offer", "reminder", "completion", "gratitude")[stage]
            after = 1 if stage == 0 else 3 if stage == 2 else stage
            if after != stage:
                deltas = (QuestStageDelta(entity, stage, after),)
                if stage == 0:
                    facts.append(
                        QuestAccepted(definition.quest_id, action.actor_id, action.payload.npc_id)
                    )
                else:
                    facts.append(
                        QuestCompleted(
                            definition.quest_id,
                            action.actor_id,
                            action.payload.npc_id,
                            definition.reward_id,
                            1,
                        )
                    )
            facts.append(QuestSpoken(definition.quest_id, definition.layout.npc_id, intent))
        elif invocation.phase == Phase.POST_TICK:
            if invocation.action is not None:
                raise CandidateError("INVALID_ACTION", "quest observation action")
            hp = invocation.state.component(HIT_POINTS, definition.layout.enemy_id).hp
            if stage == 1 and hp == 0:
                deltas = (QuestStageDelta(entity, 1, 2),)
                facts.append(GoalMet(definition.quest_id, definition.layout.enemy_id))
            elif stage >= 2 and hp > 0:
                raise CandidateError("INVALID_FACT", "quest objective contradicts progress")
        else:
            raise CandidateError("INVALID_FACT", "quest phase")
        return EngineResult(
            deltas, tuple(EmittedFact(f, invocation.logical_tick, ()) for f in facts), ()
        )
