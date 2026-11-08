"""Resolve an admitted local step in the normal turn pipeline."""

from contracts.errors import CandidateError
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from contracts.world_village import (
    VILLAGE,
    VILLAGE_FAMILY,
    VILLAGE_OWNER,
    VillageDelta,
    VillageStep,
)
from domain.primitives import Phase
from domain.world_village import step


class VillageWalker:
    @property
    def manifest(self) -> CapabilityManifest:
        access = (PhaseAccess(Phase.RESOLVE, VILLAGE_FAMILY),)
        return CapabilityManifest(
            VILLAGE_OWNER, (Phase.RESOLVE,), access, access, (), (), (), "constant"
        )

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        action = invocation.action
        if (
            invocation.phase != Phase.RESOLVE
            or action is None
            or not isinstance(action.payload, VillageStep)
        ):
            raise CandidateError("INVALID_COMMAND", "village invocation")
        before = invocation.state.component(VILLAGE, action.actor_id).state
        after = step(before, action.payload.direction)
        return EngineResult((VillageDelta(action.actor_id, before, after),), (), ())
