"""Resolve one admitted footstep through the shared deterministic turn pipeline."""

from dataclasses import dataclass

from contracts.errors import CandidateError
from contracts.messages import EmittedFact, StateDelta
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
from contracts.world_transport import (
    JOURNEY,
    JOURNEY_FAMILY,
    JourneyDelta,
    TransportAction,
    TransportArrivalDelta,
)
from domain.world_transport import TransportRules, plan_journey


@dataclass(frozen=True, slots=True)
class WorldWalker:
    world: WorldCatalog
    transport: TransportRules | None = None

    @property
    def manifest(self) -> CapabilityManifest:
        access = PhaseAccess(Phase.RESOLVE, TRAVEL_FAMILY)
        accesses = (access,) + (
            (PhaseAccess(Phase.RESOLVE, JOURNEY_FAMILY),) if self.transport is not None else ()
        )
        return CapabilityManifest(
            TRAVEL_OWNER,
            (Phase.RESOLVE,),
            accesses,
            accesses,
            (),
            (Walked.SCHEMA,),
            (),
            "constant",
        )

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        action = invocation.action
        if (
            invocation.phase == Phase.RESOLVE
            and action is not None
            and type(action.payload) is TransportAction
            and isinstance(action.payload, TransportAction)
        ):
            return self._transport(invocation, action.payload)
        if (
            invocation.phase != Phase.RESOLVE
            or action is None
            or type(action.payload) is not Footstep
            or not isinstance(action.payload, Footstep)
        ):
            raise CandidateError("INVALID_COMMAND", "world walker invocation")
        if (
            self.transport is not None
            and invocation.state.component(JOURNEY, action.actor_id).state.phase != "idle"
        ):
            raise CandidateError("INVALID_COMMAND", "walking during transport")
        before = invocation.state.component(TRAVELER, action.actor_id).state
        after = footstep(
            self.world, before, action.payload.destination_id, action.payload.direction
        )
        return EngineResult(
            (TravelDelta(action.actor_id, before, after),),
            (EmittedFact(Walked(action.actor_id, before, after), invocation.logical_tick, ()),),
            (),
        )

    def _transport(self, invocation: EngineInvocation, payload: TransportAction) -> EngineResult:
        action = invocation.action
        if self.transport is None or action is None:
            raise CandidateError("INVALID_COMMAND", "transport profile required")
        before = invocation.state.component(TRAVELER, action.actor_id).state
        journey = invocation.state.component(JOURNEY, action.actor_id).state
        plan = plan_journey(
            self.world,
            self.transport,
            journey,
            before,
            invocation.logical_tick - payload.duration_seconds,
            payload.operation,
            payload.destination_id,
        )
        if plan.seconds != payload.duration_seconds:
            raise CandidateError("INVALID_COMMAND", "transport admission duration drift")
        changes: list[StateDelta] = []
        if plan.journey != journey:
            changes.append(JourneyDelta(action.actor_id, journey, plan.journey))
        if plan.travel != before:
            changes.append(TransportArrivalDelta(action.actor_id, before, plan.travel))
        return EngineResult(tuple(changes), (), ())
