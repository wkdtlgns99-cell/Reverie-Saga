from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from contracts.encounter import (
    GATE,
    HIT_POINTS,
    STAMINA,
    AttackCommand,
    AttackResolved,
    Defeated,
    EncounterMoveBlocked,
    EncounterMoved,
    GateChanged,
    GateDelta,
    HitPointsDelta,
    InteractCommand,
    RestCommand,
    Rested,
    StaminaDelta,
)
from contracts.errors import CandidateError
from contracts.messages import EmittedFact, FactPayload, StateDelta
from contracts.trial import CELL_POSITION, TRIAL_MAP, CellDelta, MoveCommand
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from domain.encounter import (
    ATTACK_PROFILE_ID,
    ENEMY_CELL,
    ENEMY_ID,
    GATE_CELL,
    GATE_ID,
    REST_RECOVERY,
    STAMINA_MAX,
    adjacent_cells,
    resolve_basic_attack,
)
from domain.primitives import EntityId, FieldFamily, Phase
from domain.trial import ACTOR_ID, SPACE_ID


_ACTIONS_MANIFEST = CapabilityManifest(
    "encounter.actions",
    (Phase.RESOLVE,),
    tuple(
        PhaseAccess(Phase.RESOLVE, FieldFamily(key.schema.kind, field))
        for key, field in (
            (GATE, "cell"),
            (GATE, "is_open"),
            (GATE, "space_id"),
            (HIT_POINTS, "hp"),
            (STAMINA, "value"),
            (CELL_POSITION, "cell"),
            (CELL_POSITION, "space_id"),
        )
    ),
    tuple(
        PhaseAccess(Phase.RESOLVE, FieldFamily(key.schema.kind, field))
        for key, field in ((GATE, "is_open"), (HIT_POINTS, "hp"), (STAMINA, "value"))
    ),
    (),
    (AttackResolved.SCHEMA, Defeated.SCHEMA, GateChanged.SCHEMA, Rested.SCHEMA),
    (),
    "local",
)

_MOVEMENT_MANIFEST = CapabilityManifest(
    "trial.movement",
    (Phase.RESOLVE,),
    tuple(
        PhaseAccess(Phase.RESOLVE, FieldFamily(key.schema.kind, field))
        for key, field in (
            (GATE, "cell"),
            (GATE, "is_open"),
            (GATE, "space_id"),
            (HIT_POINTS, "hp"),
            (TRIAL_MAP, "blocked_cells"),
            (TRIAL_MAP, "height"),
            (TRIAL_MAP, "width"),
            (CELL_POSITION, "cell"),
            (CELL_POSITION, "space_id"),
        )
    ),
    (PhaseAccess(Phase.RESOLVE, FieldFamily(CELL_POSITION.schema.kind, "cell")),),
    (),
    (EncounterMoveBlocked.SCHEMA, EncounterMoved.SCHEMA),
    (),
    "local",
)


def _result(
    invocation: EngineInvocation, deltas: tuple[StateDelta, ...], facts: tuple[FactPayload, ...]
) -> EngineResult:
    return EngineResult(
        deltas, tuple(EmittedFact(f, invocation.logical_tick, ()) for f in facts), ()
    )


def _location(invocation: EngineInvocation) -> tuple[int, EntityId]:
    position = invocation.state.component(CELL_POSITION, ACTOR_ID)
    cell, space = position.cell, position.space_id
    if space != SPACE_ID:
        raise CandidateError("INVALID_ACTION", "actor space")
    return cell, space


@dataclass(frozen=True, slots=True)
class EncounterActions:
    @property
    def manifest(self) -> CapabilityManifest:
        return _ACTIONS_MANIFEST

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        action = invocation.action
        if action is None or action.actor_id != ACTOR_ID:
            raise CandidateError("INVALID_ACTION", "encounter actor")
        payload = action.payload
        actor_hp = invocation.state.component(HIT_POINTS, ACTOR_ID).hp
        if actor_hp == 0:
            raise CandidateError("INVALID_ACTION", "admitted actor defeated")
        # Exact classes are intentional: codec dispatch rejects subclasses too.
        if type(payload) is RestCommand:
            return self._rest(invocation)
        if type(payload) is InteractCommand:
            return self._interact(invocation, payload)
        if type(payload) is AttackCommand:
            return self._attack(invocation, payload, actor_hp)
        raise CandidateError("INVALID_ACTION", "encounter action payload")

    def _rest(self, invocation: EngineInvocation) -> EngineResult:
        old = invocation.state.component(STAMINA, ACTOR_ID).value
        new = min(STAMINA_MAX, old + REST_RECOVERY)
        deltas = (StaminaDelta(ACTOR_ID, old, new),) if new != old else ()
        # A consuming no-op still records the accepted action, as required by CORE-03.
        return _result(invocation, deltas, (Rested(ACTOR_ID, old, new),))

    def _interact(self, invocation: EngineInvocation, payload: InteractCommand) -> EngineResult:
        cell, space = _location(invocation)
        gate = invocation.state.component(GATE, GATE_ID)
        gate_cell, gate_space, old = gate.cell, gate.space_id, gate.is_open
        if payload.target_id != GATE_ID:
            raise CandidateError("INVALID_ACTION", "admitted gate target")
        if payload.option not in ("open", "close"):
            raise CandidateError("INVALID_ACTION", "admitted gate option")
        if gate_cell != GATE_CELL or gate_space != space:
            raise CandidateError("INVALID_ACTION", "admitted gate reference")
        if payload.option == "close" and cell == gate_cell:
            raise CandidateError("INVALID_ACTION", "admitted gate occupied")
        if not adjacent_cells(cell, gate_cell):
            raise CandidateError("INVALID_ACTION", "admitted gate range")
        new = 1 if payload.option == "open" else 0
        deltas = (GateDelta(GATE_ID, old, new),) if new != old else ()
        return _result(invocation, deltas, (GateChanged(ACTOR_ID, GATE_ID, old, new),))

    def _attack(
        self, invocation: EngineInvocation, payload: AttackCommand, actor_hp: int
    ) -> EngineResult:
        cell, space = _location(invocation)
        enemy = invocation.state.component(CELL_POSITION, ENEMY_ID)
        target_hp = invocation.state.component(HIT_POINTS, ENEMY_ID).hp
        stamina = invocation.state.component(STAMINA, ACTOR_ID).value
        if payload.target_id != ENEMY_ID:
            raise CandidateError("INVALID_ACTION", "admitted attack target")
        if payload.profile_id != ATTACK_PROFILE_ID:
            raise CandidateError("INVALID_ACTION", "admitted attack profile")
        if enemy.cell != ENEMY_CELL or enemy.space_id != space:
            raise CandidateError("INVALID_ACTION", "admitted attack reference")
        if target_hp == 0:
            raise CandidateError("INVALID_ACTION", "admitted attack defeated target")
        if stamina == 0:
            raise CandidateError("INVALID_ACTION", "admitted attack stamina")
        if not adjacent_cells(cell, ENEMY_CELL):
            raise CandidateError("INVALID_ACTION", "admitted attack range")
        actor_after, target_after, stamina_after = resolve_basic_attack(
            actor_hp, target_hp, stamina
        )
        deltas: list[StateDelta] = [HitPointsDelta(ENEMY_ID, target_hp, target_after)]
        if actor_after != actor_hp:
            deltas.append(HitPointsDelta(ACTOR_ID, actor_hp, actor_after))
        deltas.append(StaminaDelta(ACTOR_ID, stamina, stamina_after))
        facts: list[FactPayload] = [
            AttackResolved(
                ACTOR_ID,
                ENEMY_ID,
                ATTACK_PROFILE_ID,
                actor_hp,
                actor_after,
                target_hp,
                target_after,
                stamina,
                stamina_after,
            )
        ]
        if target_after == 0:
            facts.append(Defeated(ENEMY_ID, ACTOR_ID))
        elif actor_after == 0:
            facts.append(Defeated(ACTOR_ID, ENEMY_ID))
        return _result(invocation, tuple(deltas), tuple(facts))


@dataclass(frozen=True, slots=True)
class EncounterMovement:
    @property
    def manifest(self) -> CapabilityManifest:
        return _MOVEMENT_MANIFEST

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        action = invocation.action
        if action is None or action.actor_id != ACTOR_ID or type(action.payload) is not MoveCommand:
            raise CandidateError("INVALID_ACTION", "encounter move payload")
        state = invocation.state
        if state.component(HIT_POINTS, ACTOR_ID).hp == 0:
            raise CandidateError("INVALID_ACTION", "admitted actor defeated")
        position = state.component(CELL_POSITION, ACTOR_ID)
        old, space = position.cell, position.space_id
        gate = state.component(GATE, GATE_ID)
        gate_cell, gate_open, gate_space = gate.cell, gate.is_open, gate.space_id
        enemy = state.component(CELL_POSITION, ENEMY_ID)
        enemy_cell, enemy_space = enemy.cell, enemy.space_id
        enemy_hp = state.component(HIT_POINTS, ENEMY_ID).hp
        if (
            space != SPACE_ID
            or gate_space != space
            or gate_cell != GATE_CELL
            or enemy_space != space
            or enemy_cell != ENEMY_CELL
        ):
            raise CandidateError("INVALID_ACTION", "movement references")
        grid = state.component(TRIAL_MAP, space)
        width, height = grid.width, grid.height
        x, z = old % width + action.payload.dx, old // width + action.payload.dz
        reason: Literal["boundary", "wall", "door", "occupied"] | None = None
        deltas: tuple[StateDelta, ...] = ()
        fact: FactPayload
        if not (0 <= x < width and 0 <= z < height):
            reason = "boundary"
        else:
            target = z * width + x
            if grid.is_blocked(target):
                reason = "wall"
            elif target == gate_cell and gate_open == 0:
                reason = "door"
            elif target == enemy_cell and enemy_hp > 0:
                reason = "occupied"
            if reason is None:
                deltas = (CellDelta(ACTOR_ID, old, target),)
        if reason is not None:
            fact = EncounterMoveBlocked(
                ACTOR_ID, space, old, action.payload.dx, action.payload.dz, reason
            )
        else:
            fact = EncounterMoved(ACTOR_ID, space, old, z * width + x)
        return EngineResult(deltas, (EmittedFact(fact, invocation.logical_tick, ()),), ())
