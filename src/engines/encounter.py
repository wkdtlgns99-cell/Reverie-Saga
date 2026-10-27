from __future__ import annotations

from domain.scenario import LEGACY, Scenario

from dataclasses import dataclass, replace
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
from contracts.npc_gate_aid import GateAssisted
from contracts.npc_cycle import CYCLE, CYCLE_FAMILY
from contracts.npc_memory import MEMORY, MEMORY_FAMILY, read_record
from contracts.messages import EmittedFact, FactPayload, StateDelta, WorldEvent
from contracts.trial import CELL_POSITION, TRIAL_MAP, CellDelta, MoveCommand
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from contracts.watch import REPLY, NpcActed, WatchReplied
from domain.encounter import (
    ATTACK_PROFILE_ID,
    REST_RECOVERY,
    STAMINA_MAX,
    adjacent_cells,
    resolve_basic_attack,
)
from domain.primitives import EntityId, FieldFamily, Phase
from domain.watch import ECHO_DEPTH, WAKE_PERIOD
from domain.npc_work import SUPPORT_STOCK_MIN


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


def _location(invocation: EngineInvocation, layout: Scenario = LEGACY) -> tuple[int, EntityId]:
    position = invocation.state.component(CELL_POSITION, layout.actor_id)
    cell, space = position.cell, position.space_id
    if space != layout.space_id:
        raise CandidateError("INVALID_ACTION", "actor space")
    return cell, space


@dataclass(frozen=True, slots=True)
class EncounterActions:
    layout: Scenario = LEGACY
    npc_aid: bool = False
    npc_supply_aid: bool = False
    npc_call_aid: bool = False

    def __post_init__(self) -> None:
        if type(self.layout) is not Scenario:
            raise ValueError("SCENARIO_TYPE")
        if type(self.npc_aid) is not bool:
            raise ValueError("NPC_AID_CONTENT")
        if type(self.npc_supply_aid) is not bool or self.npc_supply_aid and not self.npc_aid:
            raise ValueError("NPC_SUPPLY_AID_CONTENT")
        if type(self.npc_call_aid) is not bool or self.npc_call_aid and not self.npc_supply_aid:
            raise ValueError("NPC_CALL_AID_CONTENT")

    @property
    def scenario_layout(self) -> Scenario:
        return self.layout

    @property
    def manifest(self) -> CapabilityManifest:
        if not self.npc_aid:
            return _ACTIONS_MANIFEST
        return replace(
            _ACTIONS_MANIFEST,
            phases=(*_ACTIONS_MANIFEST.phases, Phase.POST_TICK),
            reads=(
                *_ACTIONS_MANIFEST.reads,
                PhaseAccess(Phase.POST_TICK, MEMORY_FAMILY),
                *((PhaseAccess(Phase.POST_TICK, CYCLE_FAMILY),) if self.npc_supply_aid else ()),
                *(
                    (PhaseAccess(Phase.POST_TICK, FieldFamily(REPLY.schema.kind, "count")),)
                    if self.npc_call_aid
                    else ()
                ),
                *(
                    PhaseAccess(Phase.POST_TICK, FieldFamily(GATE.schema.kind, field))
                    for field in ("is_open", "cell", "space_id")
                ),
            ),
            writes=(
                *_ACTIONS_MANIFEST.writes,
                PhaseAccess(Phase.POST_TICK, FieldFamily(GATE.schema.kind, "is_open")),
            ),
            emits=(*_ACTIONS_MANIFEST.emits, GateAssisted.SCHEMA),
            consumes=(
                NpcActed(self.layout.npc_id, 0, 1).schema,
                *((WatchReplied(self.layout.npc_id, 0, 1).schema,) if self.npc_call_aid else ()),
            ),
        )

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        if self.npc_aid and invocation.phase == Phase.POST_TICK:
            return self._assist_gate(invocation)
        action = invocation.action
        if action is None or action.actor_id != self.layout.actor_id:
            raise CandidateError("INVALID_ACTION", "encounter actor")
        payload = action.payload
        actor_hp = invocation.state.component(HIT_POINTS, self.layout.actor_id).hp
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

    def _assist_gate(self, invocation: EngineInvocation) -> EngineResult:
        event = self._aid_source(invocation)
        header, tick = event.header, invocation.logical_tick
        try:
            memory = read_record(
                self.layout.npc_id, invocation.state.component(MEMORY, self.layout.npc_id)
            )
        except ValueError as error:
            raise CandidateError("INVALID_FACT", "gate aid memory") from error
        if any(entry.observed_at >= tick for entry in memory.entries):
            raise CandidateError("INVALID_FACT", "gate aid memory timing")
        if len(memory.entries) != 1:
            return EngineResult((), (), ())
        gate = invocation.state.component(GATE, self.layout.gate_id)
        if gate.cell != self.layout.gate_cell or gate.space_id != self.layout.space_id:
            raise CandidateError("INVALID_FACT", "gate aid passage binding")
        if gate.is_open:
            return EngineResult((), (), ())
        # POST_TICK views contain prior-barrier stock,not this phase's preparation/use.
        if (
            self.npc_supply_aid
            and invocation.state.component(CYCLE, self.layout.npc_id).state.stock
            < SUPPORT_STOCK_MIN
        ):
            return EngineResult((), (), ())
        return EngineResult(
            (GateDelta(self.layout.gate_id, 0, 1),),
            (
                EmittedFact(
                    GateAssisted(self.layout.npc_id, self.layout.gate_id), tick, (header.event_id,)
                ),
            ),
            (),
        )

    def _aid_source(self, invocation: EngineInvocation) -> WorldEvent:
        incoming, tick = invocation.incoming, invocation.logical_tick
        limit = 2 if self.npc_call_aid else 1
        if invocation.wave != 0 or invocation.action is not None or not 1 <= len(incoming) <= limit:
            raise CandidateError("INVALID_FACT", "gate aid invocation")
        selected = incoming[0]
        seen: set[type[FactPayload]] = set()
        for event in incoming:
            payload, header = event.payload, event.header
            if (
                type(payload) in seen
                or header.type_key != payload.schema
                or event.due_tick != tick
                or header.occurred_at != tick
                or type(tick) is not int
                or tick <= 0
                or header.sequence != 0
            ):
                raise CandidateError("INVALID_FACT", "gate aid source binding")
            seen.add(type(payload))
            if type(payload) is NpcActed:
                if (
                    payload.npc_id != self.layout.npc_id
                    or header.producer_id != "watch.npc"
                    or header.phase != Phase.PRE_TICK
                    or header.wave != 0
                    or tick % WAKE_PERIOD
                    or type(payload.before_bells) is not int
                    or type(payload.after_bells) is not int
                    or (payload.before_bells, payload.after_bells)
                    != (tick // WAKE_PERIOD - 1, tick // WAKE_PERIOD)
                ):
                    raise CandidateError("INVALID_FACT", "gate aid source binding")
            elif self.npc_call_aid and type(payload) is WatchReplied:
                if (
                    payload.npc_id != self.layout.npc_id
                    or header.producer_id != "watch.echo"
                    or header.phase != Phase.CASCADE
                    or type(header.wave) is not int
                    or header.wave != ECHO_DEPTH
                    or type(header.sequence) is not int
                    or len(header.caused_by) != 1
                    or type(payload.before_count) is not int
                    or payload.before_count < 0
                    or type(payload.after_count) is not int
                    or payload.after_count != payload.before_count + 1
                    or invocation.state.component(REPLY, self.layout.npc_id).count
                    != payload.after_count
                ):
                    raise CandidateError("INVALID_FACT", "gate aid reply binding")
                selected = event
            else:
                raise CandidateError("INVALID_FACT", "gate aid source binding")
        return selected

    def _rest(self, invocation: EngineInvocation) -> EngineResult:
        old = invocation.state.component(STAMINA, self.layout.actor_id).value
        new = min(STAMINA_MAX, old + REST_RECOVERY)
        deltas = (StaminaDelta(self.layout.actor_id, old, new),) if new != old else ()
        # A consuming no-op still records the accepted action, as required by CORE-03.
        return _result(invocation, deltas, (Rested(self.layout.actor_id, old, new),))

    def _interact(self, invocation: EngineInvocation, payload: InteractCommand) -> EngineResult:
        cell, space = _location(invocation, layout=self.layout)
        gate = invocation.state.component(GATE, self.layout.gate_id)
        gate_cell, gate_space, old = gate.cell, gate.space_id, gate.is_open
        if payload.target_id != self.layout.gate_id:
            raise CandidateError("INVALID_ACTION", "admitted gate target")
        if payload.option not in ("open", "close"):
            raise CandidateError("INVALID_ACTION", "admitted gate option")
        if gate_cell != self.layout.gate_cell or gate_space != space:
            raise CandidateError("INVALID_ACTION", "admitted gate reference")
        if payload.option == "close" and cell == gate_cell:
            raise CandidateError("INVALID_ACTION", "admitted gate occupied")
        if not adjacent_cells(cell, gate_cell):
            raise CandidateError("INVALID_ACTION", "admitted gate range")
        new = 1 if payload.option == "open" else 0
        deltas = (GateDelta(self.layout.gate_id, old, new),) if new != old else ()
        return _result(
            invocation, deltas, (GateChanged(self.layout.actor_id, self.layout.gate_id, old, new),)
        )

    def _attack(
        self, invocation: EngineInvocation, payload: AttackCommand, actor_hp: int
    ) -> EngineResult:
        cell, space = _location(invocation, layout=self.layout)
        enemy = invocation.state.component(CELL_POSITION, self.layout.enemy_id)
        target_hp = invocation.state.component(HIT_POINTS, self.layout.enemy_id).hp
        stamina = invocation.state.component(STAMINA, self.layout.actor_id).value
        if payload.target_id != self.layout.enemy_id:
            raise CandidateError("INVALID_ACTION", "admitted attack target")
        if payload.profile_id != ATTACK_PROFILE_ID:
            raise CandidateError("INVALID_ACTION", "admitted attack profile")
        if enemy.cell != self.layout.enemy_cell or enemy.space_id != space:
            raise CandidateError("INVALID_ACTION", "admitted attack reference")
        if target_hp == 0:
            raise CandidateError("INVALID_ACTION", "admitted attack defeated target")
        if stamina == 0:
            raise CandidateError("INVALID_ACTION", "admitted attack stamina")
        if not adjacent_cells(cell, self.layout.enemy_cell):
            raise CandidateError("INVALID_ACTION", "admitted attack range")
        actor_after, target_after, stamina_after = resolve_basic_attack(
            actor_hp, target_hp, stamina
        )
        deltas: list[StateDelta] = [HitPointsDelta(self.layout.enemy_id, target_hp, target_after)]
        if actor_after != actor_hp:
            deltas.append(HitPointsDelta(self.layout.actor_id, actor_hp, actor_after))
        deltas.append(StaminaDelta(self.layout.actor_id, stamina, stamina_after))
        facts: list[FactPayload] = [
            AttackResolved(
                self.layout.actor_id,
                self.layout.enemy_id,
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
            facts.append(Defeated(self.layout.enemy_id, self.layout.actor_id))
        elif actor_after == 0:
            facts.append(Defeated(self.layout.actor_id, self.layout.enemy_id))
        return _result(invocation, tuple(deltas), tuple(facts))


@dataclass(frozen=True, slots=True)
class EncounterMovement:
    layout: Scenario = LEGACY

    def __post_init__(self) -> None:
        if type(self.layout) is not Scenario:
            raise ValueError("SCENARIO_TYPE")

    @property
    def scenario_layout(self) -> Scenario:
        return self.layout

    @property
    def manifest(self) -> CapabilityManifest:
        return _MOVEMENT_MANIFEST

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        action = invocation.action
        if (
            action is None
            or action.actor_id != self.layout.actor_id
            or type(action.payload) is not MoveCommand
        ):
            raise CandidateError("INVALID_ACTION", "encounter move payload")
        state = invocation.state
        if state.component(HIT_POINTS, self.layout.actor_id).hp == 0:
            raise CandidateError("INVALID_ACTION", "admitted actor defeated")
        position = state.component(CELL_POSITION, self.layout.actor_id)
        old, space = position.cell, position.space_id
        gate = state.component(GATE, self.layout.gate_id)
        gate_cell, gate_open, gate_space = gate.cell, gate.is_open, gate.space_id
        enemy = state.component(CELL_POSITION, self.layout.enemy_id)
        enemy_cell, enemy_space = enemy.cell, enemy.space_id
        enemy_hp = state.component(HIT_POINTS, self.layout.enemy_id).hp
        if (
            space != self.layout.space_id
            or gate_space != space
            or gate_cell != self.layout.gate_cell
            or enemy_space != space
            or enemy_cell != self.layout.enemy_cell
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
                deltas = (CellDelta(self.layout.actor_id, old, target),)
        if reason is not None:
            fact = EncounterMoveBlocked(
                self.layout.actor_id, space, old, action.payload.dx, action.payload.dz, reason
            )
        else:
            fact = EncounterMoved(self.layout.actor_id, space, old, z * width + x)
        return EngineResult(deltas, (EmittedFact(fact, invocation.logical_tick, ()),), ())
