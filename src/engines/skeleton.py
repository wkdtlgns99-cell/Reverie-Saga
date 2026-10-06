from __future__ import annotations

from dataclasses import dataclass

from contracts.errors import CandidateError
from contracts.messages import EmittedFact
from contracts.skeleton import COUNTER, POSITION, CounterDelta, PositionDelta, StepCommand, Stepped
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from domain.primitives import EntityId, FieldFamily, Phase


@dataclass(frozen=True, slots=True)
class Stepper:
    @property
    def manifest(self) -> CapabilityManifest:
        access = PhaseAccess(Phase.RESOLVE, FieldFamily("skeleton.position", "x"))
        return CapabilityManifest("skeleton.stepper", (Phase.RESOLVE,), (access,), (access,), (),
                                  (Stepped(0, 0).schema,), (), "constant")

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        action = invocation.action
        if action is None or not isinstance(action.payload, StepCommand):
            raise CandidateError("INVALID_COMMAND", "Stepper requires an admitted step")
        old = invocation.state.component(POSITION, action.actor_id).x
        new = old + action.payload.dx
        return EngineResult((PositionDelta(action.actor_id, old, new),),
                            (EmittedFact(Stepped(old, new), invocation.logical_tick, ()),), ())


@dataclass(frozen=True, slots=True)
class Counter:
    actor_id: EntityId

    @property
    def manifest(self) -> CapabilityManifest:
        access = PhaseAccess(Phase.POST_TICK, FieldFamily("skeleton.counter", "visits"))
        return CapabilityManifest("skeleton.counter", (Phase.POST_TICK,), (access,), (access,),
                                  (), (), (), "constant")

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        old = invocation.state.component(COUNTER, self.actor_id).visits
        return EngineResult((CounterDelta(self.actor_id, old, old + 1),), (), ())
