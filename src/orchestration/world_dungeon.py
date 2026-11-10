"""Registered dungeon admission and owner-local serialization."""

from dataclasses import replace

from contracts.errors import CandidateError, SchemaError
from contracts.messages import StateDelta
from contracts.read_views import ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.skeleton import CommandRoute
from contracts.state_io import CheckpointPolicy
from contracts.turn import (
    AdmittedAction,
    AdmittedCommand,
    AdmissionOutcome,
    GameCommand,
    ProtocolSnapshot,
    TurnPlan,
    TurnRejected,
    failure,
)
from contracts.world_combat import COMBAT, COMBAT_FAMILY
from contracts.world_dungeon import (
    DUNGEON,
    DUNGEON_FAMILY,
    DUNGEON_OWNER,
    DungeonAction,
    DungeonDelta,
    DungeonPatch,
    DungeonRead,
)
from contracts.world_travel import TRAVELER, TRAVEL_FAMILY
from contracts.world_village import VILLAGE, VILLAGE_FAMILY
from domain.canonical import JsonObject, array_value, exact_fields, hash_document, int_value
from domain.canonical import object_value, text_value
from domain.primitives import ComponentAddress, EntityId, FrozenPayload, Tick, TypeKey
from domain.state_types import ComponentRecord, CoreSnapshot
from domain.world_combat import ACTION_SECONDS, POMMEL
from domain.world_dungeon import (
    DUNGEON_SCHEMA,
    ENTRY,
    DungeonRecord,
    DungeonState,
    dungeon_step,
    in_melee_range,
)
from domain.world_dungeon_loadout import ORC, SWORD, weapon_by_id, weapon_for_skill
from domain.world_travel import WORLD_ACTOR
from domain.world_village import DIRECTIONS
from domain.world_village_layout import DungeonBlueprint
from orchestration.world_combat import decode_combat, encode_combat
from orchestration.world_population import _StateView


def _encode(state: DungeonState) -> JsonObject:
    combat = encode_combat(state.combat)
    if state.pommel_used:
        combat = {**combat, "pommel_used": True}
    if state.weapon_id != SWORD or state.other_skills_used:
        combat = {**combat, "loadout": (state.weapon_id, state.other_skills_used, state.last_other_skill)}
    return {"tile": state.tile, "combat": combat}


def _decode(value: JsonObject, opponent: EntityId) -> DungeonState:
    row = exact_fields(value, ("tile", "combat"))
    combat = dict(object_value(row["combat"]))
    used = "pommel_used" in combat
    if used and combat.pop("pommel_used") is not True:
        raise ValueError("DUNGEON_SKILL")
    weapon, spent, last = array_value(combat.pop("loadout", (SWORD, (), "")))
    tile = None
    if row["tile"] is not None:
        x, y = array_value(row["tile"])
        tile = int_value(x), int_value(y)
    return DungeonState(
        tile, decode_combat(combat, opponent), used, text_value(weapon),
        tuple(text_value(skill) for skill in array_value(spent)), text_value(last),
    )


class DungeonAdapter:
    key = DUNGEON
    schema = DUNGEON_SCHEMA

    def __init__(self, opponent: EntityId = ORC, *, loadouts: bool = False) -> None:
        self.opponent, self.loadouts = opponent, loadouts

    def _record(self, record: ComponentRecord) -> DungeonRecord:
        if (
            type(record) is not DungeonRecord
            or record.entity_id != WORLD_ACTOR
            or type(record.state) is not DungeonState
            or record.state.combat.opponent != self.opponent
            or (not self.loadouts and (record.state.weapon_id != SWORD or record.state.other_skills_used))
        ):
            raise ValueError("DUNGEON_RECORD")
        return record

    def validate(self, record: ComponentRecord) -> None:
        self._record(record)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> DungeonRead:
        row = self._record(record)
        return _StateView(row.state, DUNGEON_FAMILY, row.entity_id, access)

    def encode(self, record: ComponentRecord) -> JsonObject:
        return {"state": _encode(self._record(record).state)}

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        record = DungeonRecord(
            entity_id, _decode(object_value(exact_fields(fields, ("state",))["state"]), self.opponent)
        )
        self.validate(record)
        return record


class DungeonPayloadCodec:
    def __init__(self, schema: TypeKey, opponent: EntityId = ORC) -> None:
        self.schema = schema
        self.opponent = opponent

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if payload.schema == self.schema:
            if type(payload) is DungeonAction:
                return {"operation": text_value(payload.operation)}
            if type(payload) is DungeonPatch:
                return {"state": _encode(payload.state)}
            if type(payload) is DungeonDelta:
                return {"before": _encode(payload.before), "after": _encode(payload.after)}
        raise SchemaError("UNSUPPORTED_SCHEMA", "dungeon payload")

    def decode(self, document: JsonObject) -> FrozenPayload:
        if self.schema == DungeonAction.SCHEMA:
            return DungeonAction(text_value(exact_fields(document, ("operation",))["operation"]))
        if self.schema == DungeonPatch.SCHEMA:
            row = exact_fields(document, ("state",))
            return DungeonPatch(_decode(object_value(row["state"]), self.opponent))
        if self.schema == DungeonDelta.SCHEMA:
            row = exact_fields(document, ("before", "after"))
            return DungeonDelta(
                _decode(object_value(row["before"]), self.opponent),
                _decode(object_value(row["after"]), self.opponent),
            )
        raise SchemaError("UNSUPPORTED_SCHEMA", "dungeon payload")


class DungeonGate:
    def __init__(self, inner: CommandRoute) -> None:
        self.inner = inner
        self.schema = inner.schema
        self.reads = (*inner.reads, DUNGEON_FAMILY)

    def admit(
        self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str
    ) -> AdmissionOutcome:
        if state.component(DUNGEON, WORLD_ACTOR).state.tile is not None:
            return TurnRejected(failure("DUNGEON_INSIDE"), command.expected_revision)
        return self.inner.admit(command, state, start_tick=start_tick, world_id=world_id)


class DungeonAdmission:
    schema = DungeonAction.SCHEMA
    reads = (DUNGEON_FAMILY, COMBAT_FAMILY, VILLAGE_FAMILY, TRAVEL_FAMILY)

    def __init__(self, blueprint: DungeonBlueprint, place_id: EntityId, *, loadouts: bool = False) -> None:
        self.blueprint, self.place_id = blueprint, place_id
        self.loadouts = loadouts

    def _enter(self, state: ReadPort, room: DungeonState) -> str:
        if room.tile is not None:
            return "DUNGEON_INSIDE"
        town_combat = state.component(COMBAT, WORLD_ACTOR).state
        if town_combat.order:
            return "VILLAGE_COMBAT_ACTIVE"
        travel = state.component(TRAVELER, WORLD_ACTOR).state
        if travel.place_id != self.place_id or travel.destination_id:
            return "VILLAGE_OUT_OF_REACH"
        position = state.component(VILLAGE, WORLD_ACTOR).state
        gate = self.blueprint
        return "" if (position.x, position.y) == (gate.gate_x, gate.gate_y - 1) else "DUNGEON_GATE"

    def _rejection(self, command: GameCommand, state: ReadPort) -> str:
        if command.actor_id != WORLD_ACTOR:
            return "UNAUTHORIZED_ACTOR"
        payload = command.payload
        if type(payload) is not DungeonAction:
            return "INVALID_COMMAND"
        operation = payload.operation
        room = state.component(DUNGEON, WORLD_ACTOR).state
        if operation == "enter":
            return self._enter(state, room)
        if room.tile is None:
            return "DUNGEON_OUTSIDE"
        fight = room.combat
        if self.loadouts and operation.startswith("equip:"):
            if fight.order and fight.current != WORLD_ACTOR:
                return "COMBAT_WRONG_TURN"
            target = weapon_by_id(operation.removeprefix("equip:"))
            if target is None:
                return "DUNGEON_WEAPON_UNKNOWN"
            return "DUNGEON_ALREADY_EQUIPPED" if target.id == room.weapon_id else ""
        if fight.order:
            skill = weapon_for_skill(operation) if self.loadouts or operation == POMMEL else None
            if skill is None and operation not in ("advance", "attack", "hold"):
                return "DUNGEON_COMBAT_ACTIVE"
            if (operation == "advance") == (fight.current == WORLD_ACTOR):
                return "COMBAT_WRONG_TURN"
            if skill is not None and skill.id != room.weapon_id:
                return "DUNGEON_SKILL_WRONG_WEAPON"
            return "DUNGEON_SKILL_SPENT" if room.skill_used(operation) else ""
        if operation == "exit":
            return "" if room.tile == ENTRY else "DUNGEON_GATE"
        if operation == "wait":
            return ""
        if operation == "engage":
            if fight.resolved:
                return "COMBAT_ALREADY_OPENED"
            return "" if in_melee_range(room.tile, self.blueprint) else "OUT_OF_RANGE"
        if operation not in DIRECTIONS:
            return "INVALID_COMMAND"
        try:
            dungeon_step(room.tile, operation, self.blueprint, orc_alive=fight.bandit_hp > 0)
        except ValueError as error:
            return str(error)
        return ""

    def admit(
        self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str
    ) -> AdmissionOutcome:
        error = self._rejection(command, state)
        if error:
            return TurnRejected(failure(error), command.expected_revision)
        key = "a1-" + hash_document("dungeon-action/v1", (world_id, command.command_id))
        payload = command.payload
        target = weapon_by_id(payload.operation.removeprefix("equip:")) if (
            type(payload) is DungeonAction and payload.operation.startswith("equip:")
        ) else None
        seconds = ACTION_SECONDS if target is None else target.switch_ticks
        return AdmittedCommand(
            TurnPlan(command, start_tick, Tick(start_tick + seconds)),
            AdmittedAction(command.actor_id, command.payload, key),
        )


class DungeonReducer:
    schema = DungeonDelta.SCHEMA
    owner_id = DUNGEON_OWNER

    def _delta(self, delta: StateDelta) -> DungeonDelta:
        if type(delta) is not DungeonDelta:
            raise CandidateError("INVALID_DELTA", "dungeon delta")
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._delta(delta)
        if before.component(DUNGEON, WORLD_ACTOR).state != value.before:
            raise CandidateError("INVALID_DELTA", "dungeon before")
        editor.apply_patch(ComponentAddress(DUNGEON_SCHEMA, WORLD_ACTOR), DungeonPatch(value.after))

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if len(changes) != 1:
            raise CandidateError("INVALID_DELTA", "one dungeon action per command")
        return self._delta(changes[0])

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._delta(delta)
        return value.before == value.after

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        if after.component(DUNGEON, WORLD_ACTOR).state != self._delta(delta).after:
            raise CandidateError("INVALID_DELTA", "dungeon after")


class DungeonPatchRoute:
    schema = DungeonPatch.SCHEMA
    component_schema = DUNGEON_SCHEMA
    family = DUNGEON_FAMILY

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        if type(before) is not DungeonRecord or type(patch) is not DungeonPatch:
            raise ValueError("DUNGEON_PATCH")
        return replace(before, state=patch.state)


class DungeonCheckpointPolicy:
    def __init__(self, base: CheckpointPolicy, adapter: DungeonAdapter) -> None:
        self.base = base
        self.adapter = adapter

    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        rows = tuple(row for row in core.components if isinstance(row, DungeonRecord))
        if len(rows) != 1:
            raise ValueError("DUNGEON_CHECKPOINT")
        self.adapter.validate(rows[0])
        self.base.validate(
            replace(core, components=tuple(row for row in core.components if row is not rows[0])),
            protocol,
        )
