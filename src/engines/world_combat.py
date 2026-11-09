"""Resolve one village combat action in the registered simulation."""

from dataclasses import dataclass

from contracts.errors import CandidateError
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from contracts.world_combat import COMBAT, COMBAT_FAMILY, COMBAT_OWNER, CombatAction, CombatDelta
from contracts.world_population import SETTLEMENT, SETTLEMENT_FAMILY
from contracts.world_village import VILLAGE, VILLAGE_FAMILY
from domain.primitives import EntityId, Phase
from domain.world_combat import BANDIT, perform_action, resolve_ambush
from domain.world_travel import WORLD_ACTOR


@dataclass(frozen=True, slots=True)
class VillageCombat:
    place_id: EntityId

    @property
    def manifest(self) -> CapabilityManifest:
        reads = tuple(
            PhaseAccess(Phase.RESOLVE, family)
            for family in (COMBAT_FAMILY, VILLAGE_FAMILY, SETTLEMENT_FAMILY)
        )
        return CapabilityManifest(
            COMBAT_OWNER, (Phase.RESOLVE,), reads, reads[:1], (), (), (), "local"
        )

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        action = invocation.action
        if (
            invocation.phase != Phase.RESOLVE
            or action is None
            or not isinstance(action.payload, CombatAction)
        ):
            raise CandidateError("INVALID_COMMAND", "combat invocation")
        before = invocation.state.component(COMBAT, WORLD_ACTOR).state
        operation = action.payload.operation
        if operation == "ambush":
            local = invocation.state.component(SETTLEMENT, self.place_id).state
            if local is None:
                raise CandidateError("INVALID_COMMAND", "combat settlement missing")
            position = invocation.state.component(VILLAGE, WORLD_ACTOR).state
            after = resolve_ambush(position, local)
        else:
            if operation == "advance":
                operation = "attack" if before.current == BANDIT else "hold"
            after = perform_action(before, operation)
        return EngineResult((CombatDelta(before, after),), (), ())
