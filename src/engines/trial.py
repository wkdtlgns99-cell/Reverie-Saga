from __future__ import annotations

from dataclasses import dataclass

from contracts.errors import CandidateError
from contracts.messages import EmittedFact, FactPayload, StateDelta
from contracts.trial import CELL_POSITION, TRIAL_MAP, CellDelta, MoveBlocked, MoveCommand, Moved
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from domain.primitives import FieldFamily, Phase, TypeKey


@dataclass(frozen=True, slots=True)
class Movement:
    @property
    def manifest(self) -> CapabilityManifest:
        reads = tuple(PhaseAccess(Phase.RESOLVE, FieldFamily(kind, field)) for kind, field in (
            ("trial.map", "blocked_cells"), ("trial.map", "height"), ("trial.map", "width"),
            ("trial.position", "cell"), ("trial.position", "space_id"),
        ))
        return CapabilityManifest("trial.movement", (Phase.RESOLVE,), reads,
                                  (PhaseAccess(Phase.RESOLVE, FieldFamily("trial.position", "cell")),),
                                  (), (TypeKey("trial.move-blocked", 1), TypeKey("trial.moved", 1)),
                                  (), "local")

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        action = invocation.action
        if action is None or type(action.payload) is not MoveCommand:
            raise CandidateError("INVALID_COMMAND", "Movement requires an admitted move")
        position = invocation.state.component(CELL_POSITION, action.actor_id)
        space = position.space_id
        old = position.cell
        grid = invocation.state.component(TRIAL_MAP, space)
        width, height = grid.width, grid.height
        x, z = old % width + action.payload.dx, old // width + action.payload.dz
        deltas: tuple[StateDelta, ...] = ()
        fact: FactPayload
        if not (0 <= x < width and 0 <= z < height):
            fact = MoveBlocked(action.actor_id, space, old, action.payload.dx,
                               action.payload.dz, "boundary")
        else:
            target = z * width + x
            if grid.is_blocked(target):
                fact = MoveBlocked(action.actor_id, space, old, action.payload.dx,
                                   action.payload.dz, "occupied")
            else:
                deltas = (CellDelta(action.actor_id, old, target),)
                fact = Moved(action.actor_id, space, old, target)
        return EngineResult(deltas, (EmittedFact(fact, invocation.logical_tick, ()),), ())
