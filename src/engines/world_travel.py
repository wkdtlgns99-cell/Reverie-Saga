"""Resolve one admitted footstep through the shared deterministic turn pipeline."""

from dataclasses import dataclass

from contracts.errors import CandidateError
from contracts.messages import EmittedFact
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from contracts.world_travel import (
    TRAVELER,
    TRAVEL_FAMILY,
    TRAVEL_OWNER,
    Footstep,
    TravelDelta,
    Walked,
)
from domain.primitives import Phase
from domain.world import WorldCatalog
from domain.world_travel import footstep


@dataclass(frozen=True, slots=True)
class WorldWalker:
    world: WorldCatalog

    @property
    def manifest(self) -> CapabilityManifest:
        access = PhaseAccess(Phase.RESOLVE, TRAVEL_FAMILY)
        return CapabilityManifest(
            TRAVEL_OWNER,
            (Phase.RESOLVE,),
            (access,),
            (access,),
            (),
            (Walked.SCHEMA,),
            (),
            "constant",
        )

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        action = invocation.action
        if (
            invocation.phase != Phase.RESOLVE
            or action is None
            or type(action.payload) is not Footstep
            or not isinstance(action.payload, Footstep)
        ):
            raise CandidateError("INVALID_COMMAND", "world walker invocation")
        before = invocation.state.component(TRAVELER, action.actor_id).state
        after = footstep(
            self.world, before, action.payload.destination_id, action.payload.direction
        )
        return EngineResult(
            (TravelDelta(action.actor_id, before, after),),
            (EmittedFact(Walked(action.actor_id, before, after), invocation.logical_tick, ()),),
            (),
        )
