"""Produce a committed-time fact for an admitted duration;no wall-clock access."""

from contracts.errors import CandidateError
from contracts.messages import EmittedFact
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult
from contracts.world_time import TimePassed, WorldWait
from domain.primitives import Phase


class WorldTime:
    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            "world.time", (Phase.RESOLVE,), (), (), (), (TimePassed.SCHEMA,), (), "constant"
        )

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        action = invocation.action
        if (
            invocation.phase != Phase.RESOLVE
            or action is None
            or type(action.payload) is not WorldWait
            or not isinstance(action.payload, WorldWait)
        ):
            raise CandidateError("INVALID_COMMAND", "world time invocation")
        end = invocation.logical_tick
        payload = TimePassed(end - action.payload.seconds, end)
        return EngineResult((), (EmittedFact(payload, end, ()),), ())
