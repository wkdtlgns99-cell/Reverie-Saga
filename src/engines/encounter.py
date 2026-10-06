from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from contracts.encounter import (
    GATE, HIT_POINTS, STAMINA, AttackCommand, AttackResolved, Defeated,
    EncounterMoveBlocked, EncounterMoved, GateChanged, GateDelta, HitPointsDelta,
    InteractCommand, RestCommand, Rested, StaminaDelta,
)
from contracts.errors import CandidateError
from contracts.messages import EmittedFact, FactPayload, StateDelta
from contracts.trial import CELL_POSITION, TRIAL_MAP, CellDelta, MoveCommand
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from domain.encounter import (
    ATTACK_PROFILE_ID, ENEMY_CELL, ENEMY_ID, GATE_CELL, GATE_ID,
    adjacent_cells, resolve_basic_attack,
)
from domain.primitives import FieldFamily, Phase, TypeKey
from domain.trial import ACTOR_ID, SPACE_ID


@dataclass(frozen=True, slots=True)
class EncounterActions:
    @property
    def manifest(self) -> CapabilityManifest:
        reads = tuple(PhaseAccess(Phase.RESOLVE, FieldFamily(kind, field)) for kind, field in (
            ("encounter.gate", "cell"), ("encounter.gate", "is_open"),
            ("encounter.gate", "space_id"), ("encounter.hp", "hp"),
            ("encounter.stamina", "value"), ("trial.position", "cell"),
            ("trial.position", "space_id"),
        ))
        writes = tuple(PhaseAccess(Phase.RESOLVE, FieldFamily(kind, field)) for kind, field in (
            ("encounter.gate", "is_open"), ("encounter.hp", "hp"),
            ("encounter.stamina", "value"),
        ))
        emits = tuple(TypeKey("encounter." + kind, 1) for kind in (
            "attack-resolved", "defeated", "gate-changed", "rested"))
        return CapabilityManifest("encounter.actions", (Phase.RESOLVE,), reads, writes,
                                  (), emits, (), "local")

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        action = invocation.action
        if action is None or action.actor_id != ACTOR_ID:
            raise CandidateError("INVALID_ACTION", "encounter actor")
        payload = action.payload
        actor_hp = invocation.state.component(HIT_POINTS, ACTOR_ID).hp
        if actor_hp == 0:
            raise CandidateError("INVALID_ACTION", "admitted actor defeated")
        deltas: list[StateDelta] = []
        facts: list[FactPayload] = []
        if type(payload) is RestCommand:
            old = invocation.state.component(STAMINA, ACTOR_ID).value
            new = min(2, old + 1)
            if new != old:
                deltas.append(StaminaDelta(ACTOR_ID, old, new))
            facts.append(Rested(ACTOR_ID, old, new))
        elif type(payload) in (InteractCommand, AttackCommand):
            assert isinstance(payload, (InteractCommand, AttackCommand))
            position = invocation.state.component(CELL_POSITION, ACTOR_ID)
            cell, space = position.cell, position.space_id
            if space != SPACE_ID:
                raise CandidateError("INVALID_ACTION", "actor space")
            if isinstance(payload, InteractCommand):
                gate = invocation.state.component(GATE, GATE_ID)
                gate_cell, gate_space, old = gate.cell, gate.space_id, gate.is_open
                if (payload.target_id != GATE_ID or payload.option not in ("open", "close") or
                    gate_cell != GATE_CELL or gate_space != space or
                    payload.option == "close" and cell == gate_cell or
                    not adjacent_cells(cell, gate_cell)):
                    raise CandidateError("INVALID_ACTION", "admitted gate interaction")
                new = 1 if payload.option == "open" else 0
                if new != old:
                    deltas.append(GateDelta(GATE_ID, old, new))
                facts.append(GateChanged(ACTOR_ID, GATE_ID, old, new))
            else:
                enemy = invocation.state.component(CELL_POSITION, ENEMY_ID)
                target_hp = invocation.state.component(HIT_POINTS, ENEMY_ID).hp
                stamina = invocation.state.component(STAMINA, ACTOR_ID).value
                if (payload.target_id != ENEMY_ID or payload.profile_id != ATTACK_PROFILE_ID or
                    enemy.cell != ENEMY_CELL or enemy.space_id != space or target_hp == 0 or
                    stamina == 0 or not adjacent_cells(cell, ENEMY_CELL)):
                    raise CandidateError("INVALID_ACTION", "admitted attack conditions")
                new_hp, new_target, new_stamina = resolve_basic_attack(actor_hp, target_hp, stamina)
                deltas.append(HitPointsDelta(ENEMY_ID, target_hp, new_target))
                if new_hp != actor_hp:
                    deltas.append(HitPointsDelta(ACTOR_ID, actor_hp, new_hp))
                deltas.append(StaminaDelta(ACTOR_ID, stamina, new_stamina))
                facts.append(AttackResolved(ACTOR_ID, ENEMY_ID, ATTACK_PROFILE_ID,
                                            actor_hp, new_hp, target_hp, new_target,
                                            stamina, new_stamina))
                if new_target == 0:
                    facts.append(Defeated(ENEMY_ID, ACTOR_ID))
                elif new_hp == 0:
                    facts.append(Defeated(ACTOR_ID, ENEMY_ID))
        else:
            raise CandidateError("INVALID_ACTION", "encounter action payload")
        return EngineResult(tuple(deltas), tuple(EmittedFact(f, invocation.logical_tick, ())
                                                for f in facts), ())


@dataclass(frozen=True, slots=True)
class EncounterMovement:
    @property
    def manifest(self) -> CapabilityManifest:
        reads = tuple(PhaseAccess(Phase.RESOLVE, FieldFamily(kind, field)) for kind, field in (
            ("encounter.gate", "cell"), ("encounter.gate", "is_open"),
            ("encounter.gate", "space_id"), ("encounter.hp", "hp"),
            ("trial.map", "blocked_cells"), ("trial.map", "height"),
            ("trial.map", "width"), ("trial.position", "cell"),
            ("trial.position", "space_id"),
        ))
        return CapabilityManifest("trial.movement", (Phase.RESOLVE,), reads,
                                  (PhaseAccess(Phase.RESOLVE, FieldFamily("trial.position", "cell")),),
                                  (), (TypeKey("encounter.move-blocked", 1), TypeKey("encounter.moved", 1)),
                                  (), "local")

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
        if space != SPACE_ID or gate_space != space or gate_cell != GATE_CELL or enemy_space != space or enemy_cell != ENEMY_CELL:
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
            fact = EncounterMoveBlocked(ACTOR_ID, space, old, action.payload.dx, action.payload.dz, reason)
        else:
            fact = EncounterMoved(ACTOR_ID, space, old, z * width + x)
        return EngineResult(deltas, (EmittedFact(fact, invocation.logical_tick, ()),), ())
