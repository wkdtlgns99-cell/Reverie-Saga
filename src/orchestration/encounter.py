from __future__ import annotations

from domain.scenario import LEGACY_SCENARIO, Scenario

from dataclasses import replace
import hashlib
from typing import Literal, cast

from contracts.errors import CandidateError, ReadOnlyViolation, SchemaError
from contracts.encounter import (
    GATE, HIT_POINTS, STAMINA, GateRead, HitPointsRead, StaminaRead,
    InteractCommand, AttackCommand, RestCommand, GateDelta, HitPointsDelta, StaminaDelta,
    GatePatch, HitPointsPatch, StaminaPatch, EncounterMoved, EncounterMoveBlocked,
    GateChanged, AttackResolved, Rested, Defeated, EncounterMoveCue, GateCue,
    AttackCue, RestCue, DefeatCue,
)
from contracts.messages import EventHeader, PresentationEvent, PresentationPayload, StateDelta, WorldEvent
from contracts.read_views import ComponentKey, ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.trial import CELL_POSITION, TRIAL_MAP, CellDelta, MoveCommand
from contracts.turn import (
    AdmittedAction, AdmittedCommand, AdmissionOutcome, CommitReceipt, GameCommand,
    ProtocolSnapshot, TurnPlan, TurnRejected, failure,
)
from domain.canonical import JsonObject, exact_fields, hash_document, int_value, pack, text_value
from domain.encounter import (
    ATTACK_PROFILE_ID, GateRecord, HitPointsRecord, StaminaRecord, adjacent_cells, resolve_basic_attack,
)
from domain.primitives import (
    ComponentAddress, EntityId, EventId, FieldAddress, FieldFamily, FrozenPayload,
    Phase, Tick, TypeKey, require_integer, require_namespace,
)
from domain.state_types import ComponentRecord, CoreSnapshot
from domain.trial import CellPositionRecord, TrialMapRecord, cell_coordinates
from orchestration.serialization import key_document
from orchestration.trial import CellReducer, CellPositionAdapter, TrialMapAdapter, TrialPayloadCodec


def _free(cell: int, scenario: Scenario = LEGACY_SCENARIO) -> None:
    cell_coordinates(cell)
    if cell in scenario.blocked_cells:
        raise ValueError("wall cell")


def _subjects(actor: EntityId, space: EntityId, scenario: Scenario = LEGACY_SCENARIO) -> None:
    require_namespace(actor)
    require_namespace(space)
    if actor != scenario.actor_id or space != scenario.space_id:
        raise ValueError("invalid encounter subjects")


def _pair(actor: EntityId, target: EntityId, expected: EntityId, scenario: Scenario = LEGACY_SCENARIO) -> None:
    require_namespace(actor)
    require_namespace(target)
    if actor != scenario.actor_id or target != expected:
        raise ValueError("invalid encounter pair")


def _defeat(entity: EntityId, killer: EntityId, scenario: Scenario = LEGACY_SCENARIO) -> None:
    require_namespace(entity)
    require_namespace(killer)
    if (entity, killer) not in ((scenario.enemy_id, scenario.actor_id), (scenario.actor_id, scenario.enemy_id)):
        raise ValueError("invalid defeat pair")


def _attack_result(actor_hp: int, target_hp: int) -> Literal["hit", "actor_defeated", "target_defeated"]:
    return "target_defeated" if target_hp == 0 else "actor_defeated" if actor_hp == 0 else "hit"


class _View:
    __slots__ = ("_record", "_access")
    _record: GateRecord | HitPointsRecord | StaminaRecord
    _access: ViewAccess

    def __init__(self, record: GateRecord | HitPointsRecord | StaminaRecord, access: ViewAccess) -> None:
        object.__setattr__(self, "_record", record)
        object.__setattr__(self, "_access", access)

    def __setattr__(self, name: str, value: object) -> None:
        self._access.observe(FieldAddress(FieldFamily(self._record.schema.kind, name), self._record.entity_id), (), "write")
        raise ReadOnlyViolation(name)

    def __delattr__(self, name: str) -> None:
        self.__setattr__(name, None)

    def _read(self, name: str) -> None:
        self._access.observe(FieldAddress(FieldFamily(self._record.schema.kind, name), self._record.entity_id), (), "read")


class _GateView(_View):
    __slots__ = ()

    @property
    def space_id(self) -> EntityId:
        self._read("space_id")
        assert isinstance(self._record, GateRecord)
        return self._record.space_id

    @property
    def cell(self) -> int:
        self._read("cell")
        assert isinstance(self._record, GateRecord)
        return self._record.cell

    @property
    def is_open(self) -> int:
        self._read("is_open")
        assert isinstance(self._record, GateRecord)
        return self._record.is_open


class GateAdapter:
    _scenario: Scenario = LEGACY_SCENARIO

    def __init__(self, scenario: Scenario = LEGACY_SCENARIO) -> None:
        self._scenario = scenario

    @property
    def key(self) -> ComponentKey[GateRead]:
        return GATE

    def validate(self, record: ComponentRecord) -> None:
        if type(record) is not GateRecord or record.schema != self.key.schema:
            raise ValueError("invalid Gate class/schema")
        require_namespace(record.entity_id)
        require_namespace(record.space_id)
        require_integer(record.cell, self._scenario.gate_cell, self._scenario.gate_cell)
        require_integer(record.is_open, 0, 1)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> GateRead:
        self.validate(record)
        assert isinstance(record, GateRecord)
        return _GateView(record, access)


class GateCodec:
    _scenario: Scenario = LEGACY_SCENARIO

    def __init__(self, scenario: Scenario = LEGACY_SCENARIO) -> None:
        self._scenario = scenario

    @property
    def schema(self) -> TypeKey:
        return GATE.schema

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        d = exact_fields(fields, ('space_id', 'cell', 'is_open'))
        record = GateRecord(entity_id, EntityId(text_value(d["space_id"])), int_value(d["cell"]), int_value(d["is_open"]))
        GateAdapter(self._scenario).validate(record)
        return record

    def encode(self, record: ComponentRecord) -> JsonObject:
        GateAdapter(self._scenario).validate(record)
        assert isinstance(record, GateRecord)
        return {"space_id": record.space_id, "cell": record.cell, "is_open": record.is_open}


class _HitPointsView(_View):
    __slots__ = ()

    @property
    def hp(self) -> int:
        self._read("hp")
        assert isinstance(self._record, HitPointsRecord)
        return self._record.hp


class HitPointsAdapter:
    @property
    def key(self) -> ComponentKey[HitPointsRead]:
        return HIT_POINTS

    def validate(self, record: ComponentRecord) -> None:
        if type(record) is not HitPointsRecord or record.schema != self.key.schema:
            raise ValueError("invalid HitPoints class/schema")
        require_namespace(record.entity_id)
        require_integer(record.hp, 0, 5)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> HitPointsRead:
        self.validate(record)
        assert isinstance(record, HitPointsRecord)
        return _HitPointsView(record, access)


class HitPointsCodec:
    @property
    def schema(self) -> TypeKey:
        return HIT_POINTS.schema

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        d = exact_fields(fields, ('hp',))
        record = HitPointsRecord(entity_id, int_value(d["hp"]))
        HitPointsAdapter().validate(record)
        return record

    def encode(self, record: ComponentRecord) -> JsonObject:
        HitPointsAdapter().validate(record)
        assert isinstance(record, HitPointsRecord)
        return {"hp": record.hp}


class _StaminaView(_View):
    __slots__ = ()

    @property
    def value(self) -> int:
        self._read("value")
        assert isinstance(self._record, StaminaRecord)
        return self._record.value


class StaminaAdapter:
    @property
    def key(self) -> ComponentKey[StaminaRead]:
        return STAMINA

    def validate(self, record: ComponentRecord) -> None:
        if type(record) is not StaminaRecord or record.schema != self.key.schema:
            raise ValueError("invalid Stamina class/schema")
        require_namespace(record.entity_id)
        require_integer(record.value, 0, 2)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> StaminaRead:
        self.validate(record)
        assert isinstance(record, StaminaRecord)
        return _StaminaView(record, access)


class StaminaCodec:
    @property
    def schema(self) -> TypeKey:
        return STAMINA.schema

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        d = exact_fields(fields, ('value',))
        record = StaminaRecord(entity_id, int_value(d["value"]))
        StaminaAdapter().validate(record)
        return record

    def encode(self, record: ComponentRecord) -> JsonObject:
        StaminaAdapter().validate(record)
        assert isinstance(record, StaminaRecord)
        return {"value": record.value}


def _validate_payload(payload: FrozenPayload, scenario: Scenario = LEGACY_SCENARIO) -> None:
    if isinstance(payload, InteractCommand):
        require_namespace(payload.target_id)
        if type(payload.option) is not str or payload.option not in ("open", "close"):
            raise ValueError("invalid gate option")
    elif isinstance(payload, AttackCommand):
        require_namespace(payload.target_id)
        require_namespace(payload.profile_id)
    elif isinstance(payload, GateDelta):
        require_namespace(payload.entity_id)
        if payload.entity_id != scenario.gate_id:
            raise ValueError("invalid gate delta subject")
        require_integer(payload.before_open, 0, 1)
        require_integer(payload.after_open, 0, 1)
    elif isinstance(payload, HitPointsDelta):
        require_namespace(payload.entity_id)
        if payload.entity_id not in (scenario.actor_id, scenario.enemy_id):
            raise ValueError("invalid HP delta subject")
        maximum = 3 if payload.entity_id == scenario.actor_id else 5
        require_integer(payload.before_hp, 0, maximum)
        require_integer(payload.after_hp, 0, maximum)
    elif isinstance(payload, StaminaDelta):
        require_namespace(payload.entity_id)
        if payload.entity_id != scenario.actor_id:
            raise ValueError("invalid stamina delta subject")
        require_integer(payload.before_stamina, 0, 2)
        require_integer(payload.after_stamina, 0, 2)
    elif isinstance(payload, GatePatch):
        require_integer(payload.is_open, 0, 1)
    elif isinstance(payload, HitPointsPatch):
        require_integer(payload.hp, 0, 5)
    elif isinstance(payload, StaminaPatch):
        require_integer(payload.value, 0, 2)
    elif isinstance(payload, (EncounterMoved, EncounterMoveBlocked, EncounterMoveCue)):
        _subjects(payload.actor_id, payload.space_id, scenario)
        _free(payload.from_cell, scenario)
        if isinstance(payload, EncounterMoveBlocked):
            TrialPayloadCodec(TypeKey("trial.move", 1)).encode(MoveCommand(payload.dx, payload.dz))
            x, z = payload.from_cell % 3 + payload.dx, payload.from_cell // 3 + payload.dz
            bounded = 0 <= x < 3 and 0 <= z < 3
            targets = {"wall": scenario.wall_cell, "door": scenario.gate_cell, "occupied": scenario.enemy_cell}
            if type(payload.reason) is not str or (payload.reason == "boundary" and bounded or
                payload.reason != "boundary" and (not bounded or targets.get(payload.reason) != z * 3 + x)):
                raise ValueError("inconsistent movement blockage")
        else:
            _free(payload.to_cell, scenario)
            if isinstance(payload, EncounterMoved) or payload.result == "moved":
                if not adjacent_cells(payload.from_cell, payload.to_cell):
                    raise ValueError("nonadjacent movement")
            elif payload.result not in ("boundary", "wall", "door", "occupied") or payload.to_cell != payload.from_cell:
                raise ValueError("invalid blocked cue")
            if isinstance(payload, EncounterMoveCue):
                for value in (payload.from_x_mm, payload.from_z_mm, payload.to_x_mm, payload.to_z_mm):
                    require_integer(value)
                if ((payload.from_x_mm, payload.from_z_mm) != cell_coordinates(payload.from_cell) or
                    (payload.to_x_mm, payload.to_z_mm) != cell_coordinates(payload.to_cell)):
                    raise ValueError("movement cue geometry")
    elif isinstance(payload, (GateChanged, GateCue)):
        _pair(payload.actor_id, payload.target_id, scenario.gate_id, scenario)
        require_integer(payload.before_open, 0, 1)
        require_integer(payload.after_open, 0, 1)
        if isinstance(payload, GateCue):
            require_integer(payload.cell, scenario.gate_cell, scenario.gate_cell)
            x, z = cell_coordinates(scenario.gate_cell)
            require_integer(payload.x_mm, x, x)
            require_integer(payload.z_mm, z, z)
    elif isinstance(payload, (AttackResolved, AttackCue)):
        _pair(payload.actor_id, payload.target_id, scenario.enemy_id, scenario)
        expected = resolve_basic_attack(payload.actor_hp_before, payload.target_hp_before, payload.stamina_before)
        require_integer(payload.actor_hp_after, 0, 3)
        require_integer(payload.target_hp_after, 0, 5)
        require_integer(payload.stamina_after, 0, 2)
        if (payload.actor_hp_after, payload.target_hp_after, payload.stamina_after) != expected:
            raise ValueError("attack arithmetic")
        if isinstance(payload, AttackResolved):
            require_namespace(payload.profile_id)
            if payload.profile_id != ATTACK_PROFILE_ID:
                raise ValueError("attack profile")
        else:
            _free(payload.actor_cell, scenario)
            require_integer(payload.target_cell, scenario.enemy_cell, scenario.enemy_cell)
            if not adjacent_cells(payload.actor_cell, payload.target_cell) or payload.result != _attack_result(expected[0], expected[1]):
                raise ValueError("attack cue geometry/result")
    elif isinstance(payload, (Rested, RestCue)):
        require_namespace(payload.actor_id)
        if payload.actor_id != scenario.actor_id:
            raise ValueError("invalid resting actor")
        require_integer(payload.before_stamina, 0, 2)
        require_integer(payload.after_stamina, 0, 2)
        if payload.after_stamina != min(2, payload.before_stamina + 1):
            raise ValueError("rest arithmetic")
    elif isinstance(payload, (Defeated, DefeatCue)):
        _defeat(payload.entity_id, payload.killer_id, scenario)
        if isinstance(payload, DefeatCue):
            _free(payload.cell, scenario)
            if payload.entity_id == scenario.enemy_id and payload.cell != scenario.enemy_cell:
                raise ValueError("enemy defeat cell")
            require_integer(payload.x_mm)
            require_integer(payload.z_mm)
            if (payload.x_mm, payload.z_mm) != cell_coordinates(payload.cell):
                raise ValueError("defeat geometry")


class EncounterPayloadCodec:
    _scenario: Scenario = LEGACY_SCENARIO

    def __init__(self, schema: TypeKey, scenario: Scenario = LEGACY_SCENARIO) -> None:
        self._scenario = scenario
        if schema.version != 1 or schema.kind not in (
            'encounter.interact',
            'encounter.attack',
            'encounter.rest',
            'encounter.gate-delta',
            'encounter.hp-delta',
            'encounter.stamina-delta',
            'encounter.gate-patch',
            'encounter.hp-patch',
            'encounter.stamina-patch',
            'encounter.moved',
            'encounter.move-blocked',
            'encounter.gate-changed',
            'encounter.attack-resolved',
            'encounter.rested',
            'encounter.defeated',
            'encounter.move-cue',
            'encounter.gate-cue',
            'encounter.attack-cue',
            'encounter.rest-cue',
            'encounter.defeat-cue',
):
            raise SchemaError("UNSUPPORTED_SCHEMA", "encounter payload codec")
        self._schema = schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if payload.schema != self.schema:
            raise SchemaError("UNSUPPORTED_SCHEMA", "payload.schema")
        if type(payload) is InteractCommand:
            _validate_payload(payload, self._scenario)
            return {"target_id": payload.target_id, "option": payload.option}
        if type(payload) is AttackCommand:
            _validate_payload(payload, self._scenario)
            return {"target_id": payload.target_id, "profile_id": payload.profile_id}
        if type(payload) is RestCommand:
            _validate_payload(payload, self._scenario)
            return {}
        if type(payload) is GateDelta:
            _validate_payload(payload, self._scenario)
            return {"entity_id": payload.entity_id, "before_open": payload.before_open, "after_open": payload.after_open}
        if type(payload) is HitPointsDelta:
            _validate_payload(payload, self._scenario)
            return {"entity_id": payload.entity_id, "before_hp": payload.before_hp, "after_hp": payload.after_hp}
        if type(payload) is StaminaDelta:
            _validate_payload(payload, self._scenario)
            return {"entity_id": payload.entity_id, "before_stamina": payload.before_stamina, "after_stamina": payload.after_stamina}
        if type(payload) is GatePatch:
            _validate_payload(payload, self._scenario)
            return {"is_open": payload.is_open}
        if type(payload) is HitPointsPatch:
            _validate_payload(payload, self._scenario)
            return {"hp": payload.hp}
        if type(payload) is StaminaPatch:
            _validate_payload(payload, self._scenario)
            return {"value": payload.value}
        if type(payload) is EncounterMoved:
            _validate_payload(payload, self._scenario)
            return {"actor_id": payload.actor_id, "space_id": payload.space_id, "from_cell": payload.from_cell, "to_cell": payload.to_cell}
        if type(payload) is EncounterMoveBlocked:
            _validate_payload(payload, self._scenario)
            return {"actor_id": payload.actor_id, "space_id": payload.space_id, "from_cell": payload.from_cell, "dx": payload.dx, "dz": payload.dz, "reason": payload.reason}
        if type(payload) is GateChanged:
            _validate_payload(payload, self._scenario)
            return {"actor_id": payload.actor_id, "target_id": payload.target_id, "before_open": payload.before_open, "after_open": payload.after_open}
        if type(payload) is AttackResolved:
            _validate_payload(payload, self._scenario)
            return {"actor_id": payload.actor_id, "target_id": payload.target_id, "profile_id": payload.profile_id, "actor_hp_before": payload.actor_hp_before, "actor_hp_after": payload.actor_hp_after, "target_hp_before": payload.target_hp_before, "target_hp_after": payload.target_hp_after, "stamina_before": payload.stamina_before, "stamina_after": payload.stamina_after}
        if type(payload) is Rested:
            _validate_payload(payload, self._scenario)
            return {"actor_id": payload.actor_id, "before_stamina": payload.before_stamina, "after_stamina": payload.after_stamina}
        if type(payload) is Defeated:
            _validate_payload(payload, self._scenario)
            return {"entity_id": payload.entity_id, "killer_id": payload.killer_id}
        if type(payload) is EncounterMoveCue:
            _validate_payload(payload, self._scenario)
            return {"actor_id": payload.actor_id, "space_id": payload.space_id, "from_cell": payload.from_cell, "to_cell": payload.to_cell, "from_x_mm": payload.from_x_mm, "from_z_mm": payload.from_z_mm, "to_x_mm": payload.to_x_mm, "to_z_mm": payload.to_z_mm, "result": payload.result}
        if type(payload) is GateCue:
            _validate_payload(payload, self._scenario)
            return {"actor_id": payload.actor_id, "target_id": payload.target_id, "cell": payload.cell, "x_mm": payload.x_mm, "z_mm": payload.z_mm, "before_open": payload.before_open, "after_open": payload.after_open}
        if type(payload) is AttackCue:
            _validate_payload(payload, self._scenario)
            return {"actor_id": payload.actor_id, "target_id": payload.target_id, "actor_cell": payload.actor_cell, "target_cell": payload.target_cell, "actor_hp_before": payload.actor_hp_before, "actor_hp_after": payload.actor_hp_after, "target_hp_before": payload.target_hp_before, "target_hp_after": payload.target_hp_after, "stamina_before": payload.stamina_before, "stamina_after": payload.stamina_after, "result": payload.result}
        if type(payload) is RestCue:
            _validate_payload(payload, self._scenario)
            return {"actor_id": payload.actor_id, "before_stamina": payload.before_stamina, "after_stamina": payload.after_stamina}
        if type(payload) is DefeatCue:
            _validate_payload(payload, self._scenario)
            return {"entity_id": payload.entity_id, "killer_id": payload.killer_id, "cell": payload.cell, "x_mm": payload.x_mm, "z_mm": payload.z_mm}
        raise SchemaError("UNSUPPORTED_SCHEMA", "encounter payload class")

    def decode(self, data: JsonObject) -> FrozenPayload:
        value: FrozenPayload
        if self.schema.kind == "encounter.interact":
            d = exact_fields(data, ('target_id', 'option'))
            value = InteractCommand(EntityId(text_value(d["target_id"])), cast(Literal['open', 'close'], text_value(d["option"])))
        elif self.schema.kind == "encounter.attack":
            d = exact_fields(data, ('target_id', 'profile_id'))
            value = AttackCommand(EntityId(text_value(d["target_id"])), text_value(d["profile_id"]))
        elif self.schema.kind == "encounter.rest":
            exact_fields(data, ())
            value = RestCommand()
        elif self.schema.kind == "encounter.gate-delta":
            d = exact_fields(data, ('entity_id', 'before_open', 'after_open'))
            value = GateDelta(EntityId(text_value(d["entity_id"])), int_value(d["before_open"]), int_value(d["after_open"]))
        elif self.schema.kind == "encounter.hp-delta":
            d = exact_fields(data, ('entity_id', 'before_hp', 'after_hp'))
            value = HitPointsDelta(EntityId(text_value(d["entity_id"])), int_value(d["before_hp"]), int_value(d["after_hp"]))
        elif self.schema.kind == "encounter.stamina-delta":
            d = exact_fields(data, ('entity_id', 'before_stamina', 'after_stamina'))
            value = StaminaDelta(EntityId(text_value(d["entity_id"])), int_value(d["before_stamina"]), int_value(d["after_stamina"]))
        elif self.schema.kind == "encounter.gate-patch":
            d = exact_fields(data, ('is_open',))
            value = GatePatch(int_value(d["is_open"]))
        elif self.schema.kind == "encounter.hp-patch":
            d = exact_fields(data, ('hp',))
            value = HitPointsPatch(int_value(d["hp"]))
        elif self.schema.kind == "encounter.stamina-patch":
            d = exact_fields(data, ('value',))
            value = StaminaPatch(int_value(d["value"]))
        elif self.schema.kind == "encounter.moved":
            d = exact_fields(data, ('actor_id', 'space_id', 'from_cell', 'to_cell'))
            value = EncounterMoved(EntityId(text_value(d["actor_id"])), EntityId(text_value(d["space_id"])), int_value(d["from_cell"]), int_value(d["to_cell"]))
        elif self.schema.kind == "encounter.move-blocked":
            d = exact_fields(data, ('actor_id', 'space_id', 'from_cell', 'dx', 'dz', 'reason'))
            value = EncounterMoveBlocked(EntityId(text_value(d["actor_id"])), EntityId(text_value(d["space_id"])), int_value(d["from_cell"]), int_value(d["dx"]), int_value(d["dz"]), cast(Literal['boundary', 'wall', 'door', 'occupied'], text_value(d["reason"])))
        elif self.schema.kind == "encounter.gate-changed":
            d = exact_fields(data, ('actor_id', 'target_id', 'before_open', 'after_open'))
            value = GateChanged(EntityId(text_value(d["actor_id"])), EntityId(text_value(d["target_id"])), int_value(d["before_open"]), int_value(d["after_open"]))
        elif self.schema.kind == "encounter.attack-resolved":
            d = exact_fields(data, ('actor_id', 'target_id', 'profile_id', 'actor_hp_before', 'actor_hp_after', 'target_hp_before', 'target_hp_after', 'stamina_before', 'stamina_after'))
            value = AttackResolved(EntityId(text_value(d["actor_id"])), EntityId(text_value(d["target_id"])), text_value(d["profile_id"]), int_value(d["actor_hp_before"]), int_value(d["actor_hp_after"]), int_value(d["target_hp_before"]), int_value(d["target_hp_after"]), int_value(d["stamina_before"]), int_value(d["stamina_after"]))
        elif self.schema.kind == "encounter.rested":
            d = exact_fields(data, ('actor_id', 'before_stamina', 'after_stamina'))
            value = Rested(EntityId(text_value(d["actor_id"])), int_value(d["before_stamina"]), int_value(d["after_stamina"]))
        elif self.schema.kind == "encounter.defeated":
            d = exact_fields(data, ('entity_id', 'killer_id'))
            value = Defeated(EntityId(text_value(d["entity_id"])), EntityId(text_value(d["killer_id"])))
        elif self.schema.kind == "encounter.move-cue":
            d = exact_fields(data, ('actor_id', 'space_id', 'from_cell', 'to_cell', 'from_x_mm', 'from_z_mm', 'to_x_mm', 'to_z_mm', 'result'))
            value = EncounterMoveCue(EntityId(text_value(d["actor_id"])), EntityId(text_value(d["space_id"])), int_value(d["from_cell"]), int_value(d["to_cell"]), int_value(d["from_x_mm"]), int_value(d["from_z_mm"]), int_value(d["to_x_mm"]), int_value(d["to_z_mm"]), cast(Literal['moved', 'boundary', 'wall', 'door', 'occupied'], text_value(d["result"])))
        elif self.schema.kind == "encounter.gate-cue":
            d = exact_fields(data, ('actor_id', 'target_id', 'cell', 'x_mm', 'z_mm', 'before_open', 'after_open'))
            value = GateCue(EntityId(text_value(d["actor_id"])), EntityId(text_value(d["target_id"])), int_value(d["cell"]), int_value(d["x_mm"]), int_value(d["z_mm"]), int_value(d["before_open"]), int_value(d["after_open"]))
        elif self.schema.kind == "encounter.attack-cue":
            d = exact_fields(data, ('actor_id', 'target_id', 'actor_cell', 'target_cell', 'actor_hp_before', 'actor_hp_after', 'target_hp_before', 'target_hp_after', 'stamina_before', 'stamina_after', 'result'))
            value = AttackCue(EntityId(text_value(d["actor_id"])), EntityId(text_value(d["target_id"])), int_value(d["actor_cell"]), int_value(d["target_cell"]), int_value(d["actor_hp_before"]), int_value(d["actor_hp_after"]), int_value(d["target_hp_before"]), int_value(d["target_hp_after"]), int_value(d["stamina_before"]), int_value(d["stamina_after"]), cast(Literal['hit', 'actor_defeated', 'target_defeated'], text_value(d["result"])))
        elif self.schema.kind == "encounter.rest-cue":
            d = exact_fields(data, ('actor_id', 'before_stamina', 'after_stamina'))
            value = RestCue(EntityId(text_value(d["actor_id"])), int_value(d["before_stamina"]), int_value(d["after_stamina"]))
        elif self.schema.kind == "encounter.defeat-cue":
            d = exact_fields(data, ('entity_id', 'killer_id', 'cell', 'x_mm', 'z_mm'))
            value = DefeatCue(EntityId(text_value(d["entity_id"])), EntityId(text_value(d["killer_id"])), int_value(d["cell"]), int_value(d["x_mm"]), int_value(d["z_mm"]))
        else:
            raise SchemaError("UNSUPPORTED_SCHEMA", "encounter decode")
        self.encode(value)
        return value


class EncounterAdmission:
    _scenario: Scenario = LEGACY_SCENARIO

    def __init__(self, schema: TypeKey, scenario: Scenario = LEGACY_SCENARIO) -> None:
        self._scenario = scenario
        if schema not in tuple(TypeKey(kind, 1) for kind in ("trial.move", "encounter.attack", "encounter.interact", "encounter.rest")):
            raise SchemaError("UNSUPPORTED_SCHEMA", "encounter admission")
        self._schema = schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    @property
    def reads(self) -> tuple[FieldFamily, ...]:
        pairs = [("encounter.hp", "hp")]
        if self.schema.kind != "encounter.rest":
            pairs += [("trial.position", "cell"), ("trial.position", "space_id")]
        if self.schema.kind in ("encounter.attack", "encounter.rest"):
            pairs += [("encounter.stamina", "value")]
        if self.schema.kind == "encounter.interact":
            pairs += [("encounter.gate", "cell"), ("encounter.gate", "is_open"), ("encounter.gate", "space_id")]
        return tuple(FieldFamily(k, f) for k, f in pairs)

    def admit(self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str) -> AdmissionOutcome:
        if command.actor_id != self._scenario.actor_id:
            return TurnRejected(failure("UNAUTHORIZED_ACTOR"), command.expected_revision)
        body = (TrialPayloadCodec(self.schema) if self.schema.kind == "trial.move" else EncounterPayloadCodec(self.schema, self._scenario)).encode(command.payload)
        if state.component(HIT_POINTS, self._scenario.actor_id).hp == 0:
            return TurnRejected(failure("ACTOR_DEFEATED"), command.expected_revision)
        payload = command.payload
        code: str | None = None
        if isinstance(payload, (MoveCommand, InteractCommand, AttackCommand)):
            position = state.component(CELL_POSITION, self._scenario.actor_id)
            space, cell = position.space_id, position.cell
            if space != self._scenario.space_id:
                raise CandidateError("INVALID_ACTION", "actor space")
            _free(cell, self._scenario)
            if isinstance(payload, InteractCommand):
                gate = state.component(GATE, self._scenario.gate_id)
                gate_cell, gate_space = gate.cell, gate.space_id
                gate.is_open
                if gate_cell != self._scenario.gate_cell or gate_space != space:
                    raise CandidateError("INVALID_ACTION", "gate reference")
                if payload.target_id != self._scenario.gate_id:
                    code = "INVALID_TARGET"
                elif payload.option == "close" and cell == gate_cell:
                    code = "TARGET_OCCUPIED"
                elif not adjacent_cells(cell, gate_cell):
                    code = "OUT_OF_RANGE"
            elif isinstance(payload, AttackCommand):
                enemy = state.component(CELL_POSITION, self._scenario.enemy_id)
                if enemy.cell != self._scenario.enemy_cell or enemy.space_id != space:
                    raise CandidateError("INVALID_ACTION", "enemy reference")
                if payload.target_id != self._scenario.enemy_id:
                    code = "INVALID_TARGET"
                elif payload.profile_id != ATTACK_PROFILE_ID:
                    code = "INVALID_ATTACK_PROFILE"
                elif state.component(HIT_POINTS, self._scenario.enemy_id).hp == 0:
                    code = "TARGET_DEFEATED"
                elif not adjacent_cells(cell, self._scenario.enemy_cell):
                    code = "OUT_OF_RANGE"
                elif state.component(STAMINA, self._scenario.actor_id).value == 0:
                    code = "INSUFFICIENT_STAMINA"
        elif isinstance(payload, RestCommand):
            state.component(STAMINA, self._scenario.actor_id).value
        else:
            raise CandidateError("INVALID_ACTION", "unsupported admitted payload")
        if code is not None:
            return TurnRejected(failure(code), command.expected_revision)
        target = Tick(start_tick + 1)
        payload_hash = hash_document("payload/v1", {"schema": key_document(payload.schema), "payload": body})
        key = "a1-" + hashlib.sha256(pack(("action-key/v1", world_id, str(target), command.actor_id, payload_hash))).hexdigest()
        return AdmittedCommand(TurnPlan(command, start_tick, target), AdmittedAction(command.actor_id, payload, key))


class EncounterCellReducer(CellReducer):
    _scenario: Scenario = LEGACY_SCENARIO

    def __init__(self, scenario: Scenario = LEGACY_SCENARIO) -> None:
        self._scenario = scenario
        super().__init__(scenario.blocked_cells)

    def _subject(self, delta: StateDelta) -> None:
        if type(delta) is not CellDelta or delta.entity_id != self._scenario.actor_id:
            raise CandidateError("INVALID_DELTA", "encounter movement subject")

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        self._subject(delta)
        super().stage(delta, before, editor)

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        for delta in changes:
            self._subject(delta)
        return super().compose(changes)

    def is_identity(self, delta: StateDelta) -> bool:
        self._subject(delta)
        return super().is_identity(delta)

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        self._subject(delta)
        super().validate_net(delta, after)


class GateReducer:
    _scenario: Scenario = LEGACY_SCENARIO

    def __init__(self, scenario: Scenario = LEGACY_SCENARIO) -> None:
        self._scenario = scenario

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.gate-delta", 1)

    @property
    def owner_id(self) -> str:
        return "encounter.actions"

    def _validate(self, delta: StateDelta) -> GateDelta:
        if type(delta) is not GateDelta:
            raise CandidateError("INVALID_DELTA", "wrong Gate delta class")
        try:
            EncounterPayloadCodec(self.schema, self._scenario).encode(delta)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "invalid Gate delta") from error
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._validate(delta)
        if abs(value.after_open - value.before_open) != 1:
            raise CandidateError("INVALID_DELTA", "illegal Gate step")
        if before.component(GATE, value.entity_id).is_open != value.before_open:
            raise CandidateError("INVALID_DELTA", "Gate old value")
        editor.apply_patch(ComponentAddress(GATE.schema, value.entity_id), GatePatch(value.after_open))

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "empty Gate composition")
        values = tuple(self._validate(d) for d in changes)
        for first, second in zip(values, values[1:]):
            if first.target != second.target or first.after_open != second.before_open:
                raise CandidateError("INVALID_DELTA", "noncontiguous Gate composition")
        return replace(values[0], after_open=values[-1].after_open)

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._validate(delta)
        return value.before_open == value.after_open

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._validate(delta)
        if self.is_identity(value) or after.component(GATE, value.entity_id).is_open != value.after_open:
            raise CandidateError("INVALID_DELTA", "Gate net mismatch")


class GatePatchRoute:
    _scenario: Scenario = LEGACY_SCENARIO

    def __init__(self, scenario: Scenario = LEGACY_SCENARIO) -> None:
        self._scenario = scenario

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.gate-patch", 1)

    @property
    def component_schema(self) -> TypeKey:
        return GATE.schema

    @property
    def family(self) -> FieldFamily:
        return FieldFamily("encounter.gate", "is_open")

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        GateAdapter(self._scenario).validate(before)
        EncounterPayloadCodec(self.schema, self._scenario).encode(patch)
        assert isinstance(before, GateRecord) and isinstance(patch, GatePatch)
        return replace(before, is_open=patch.is_open)


class HitPointsReducer:
    _scenario: Scenario = LEGACY_SCENARIO

    def __init__(self, scenario: Scenario = LEGACY_SCENARIO) -> None:
        self._scenario = scenario

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.hp-delta", 1)

    @property
    def owner_id(self) -> str:
        return "encounter.actions"

    def _validate(self, delta: StateDelta) -> HitPointsDelta:
        if type(delta) is not HitPointsDelta:
            raise CandidateError("INVALID_DELTA", "wrong HitPoints delta class")
        try:
            EncounterPayloadCodec(self.schema, self._scenario).encode(delta)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "invalid HitPoints delta") from error
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._validate(delta)
        if value.before_hp - value.after_hp not in ((1,) if value.entity_id == self._scenario.actor_id else (1, 2)):
            raise CandidateError("INVALID_DELTA", "illegal HitPoints step")
        if before.component(HIT_POINTS, value.entity_id).hp != value.before_hp:
            raise CandidateError("INVALID_DELTA", "HitPoints old value")
        editor.apply_patch(ComponentAddress(HIT_POINTS.schema, value.entity_id), HitPointsPatch(value.after_hp))

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "empty HitPoints composition")
        values = tuple(self._validate(d) for d in changes)
        for first, second in zip(values, values[1:]):
            if first.target != second.target or first.after_hp != second.before_hp:
                raise CandidateError("INVALID_DELTA", "noncontiguous HitPoints composition")
        return replace(values[0], after_hp=values[-1].after_hp)

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._validate(delta)
        return value.before_hp == value.after_hp

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._validate(delta)
        if self.is_identity(value) or after.component(HIT_POINTS, value.entity_id).hp != value.after_hp:
            raise CandidateError("INVALID_DELTA", "HitPoints net mismatch")


class HitPointsPatchRoute:
    _scenario: Scenario = LEGACY_SCENARIO

    def __init__(self, scenario: Scenario = LEGACY_SCENARIO) -> None:
        self._scenario = scenario

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.hp-patch", 1)

    @property
    def component_schema(self) -> TypeKey:
        return HIT_POINTS.schema

    @property
    def family(self) -> FieldFamily:
        return FieldFamily("encounter.hp", "hp")

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        HitPointsAdapter().validate(before)
        EncounterPayloadCodec(self.schema, self._scenario).encode(patch)
        assert isinstance(before, HitPointsRecord) and isinstance(patch, HitPointsPatch)
        return replace(before, hp=patch.hp)


class StaminaReducer:
    _scenario: Scenario = LEGACY_SCENARIO

    def __init__(self, scenario: Scenario = LEGACY_SCENARIO) -> None:
        self._scenario = scenario

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.stamina-delta", 1)

    @property
    def owner_id(self) -> str:
        return "encounter.actions"

    def _validate(self, delta: StateDelta) -> StaminaDelta:
        if type(delta) is not StaminaDelta:
            raise CandidateError("INVALID_DELTA", "wrong Stamina delta class")
        try:
            EncounterPayloadCodec(self.schema, self._scenario).encode(delta)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "invalid Stamina delta") from error
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._validate(delta)
        if abs(value.after_stamina - value.before_stamina) != 1:
            raise CandidateError("INVALID_DELTA", "illegal Stamina step")
        if before.component(STAMINA, value.entity_id).value != value.before_stamina:
            raise CandidateError("INVALID_DELTA", "Stamina old value")
        editor.apply_patch(ComponentAddress(STAMINA.schema, value.entity_id), StaminaPatch(value.after_stamina))

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "empty Stamina composition")
        values = tuple(self._validate(d) for d in changes)
        for first, second in zip(values, values[1:]):
            if first.target != second.target or first.after_stamina != second.before_stamina:
                raise CandidateError("INVALID_DELTA", "noncontiguous Stamina composition")
        return replace(values[0], after_stamina=values[-1].after_stamina)

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._validate(delta)
        return value.before_stamina == value.after_stamina

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._validate(delta)
        if self.is_identity(value) or after.component(STAMINA, value.entity_id).value != value.after_stamina:
            raise CandidateError("INVALID_DELTA", "Stamina net mismatch")


class StaminaPatchRoute:
    _scenario: Scenario = LEGACY_SCENARIO

    def __init__(self, scenario: Scenario = LEGACY_SCENARIO) -> None:
        self._scenario = scenario

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.stamina-patch", 1)

    @property
    def component_schema(self) -> TypeKey:
        return STAMINA.schema

    @property
    def family(self) -> FieldFamily:
        return FieldFamily("encounter.stamina", "value")

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        StaminaAdapter().validate(before)
        EncounterPayloadCodec(self.schema, self._scenario).encode(patch)
        assert isinstance(before, StaminaRecord) and isinstance(patch, StaminaPatch)
        return replace(before, value=patch.value)


class EncounterCheckpointPolicy:
    _scenario: Scenario = LEGACY_SCENARIO

    def __init__(self, scenario: Scenario = LEGACY_SCENARIO) -> None:
        self._scenario = scenario

    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        if len(core.components) != 7:
            raise ValueError("exact seven encounter records required")
        records = {(r.schema.kind, r.entity_id): r for r in core.components}
        expected = (
            ("encounter.gate", self._scenario.gate_id),
            ("encounter.hp", self._scenario.enemy_id),
            ("encounter.hp", self._scenario.actor_id),
            ("encounter.stamina", self._scenario.actor_id),
            ("trial.map", self._scenario.space_id),
            ("trial.position", self._scenario.enemy_id),
            ("trial.position", self._scenario.actor_id),
        )
        if set(records) != set(expected):
            raise ValueError("invalid encounter identities/order")
        gate, enemy_hp, actor_hp, stamina, grid, enemy, actor = (records[key] for key in expected)
        GateAdapter(self._scenario).validate(gate)
        HitPointsAdapter().validate(enemy_hp)
        HitPointsAdapter().validate(actor_hp)
        StaminaAdapter().validate(stamina)
        TrialMapAdapter(self._scenario.blocked_cells).validate(grid)
        CellPositionAdapter().validate(enemy)
        CellPositionAdapter().validate(actor)
        assert isinstance(gate, GateRecord)
        assert isinstance(enemy_hp, HitPointsRecord) and isinstance(actor_hp, HitPointsRecord)
        assert isinstance(stamina, StaminaRecord) and isinstance(grid, TrialMapRecord)
        assert isinstance(enemy, CellPositionRecord) and isinstance(actor, CellPositionRecord)
        if (gate.entity_id != self._scenario.gate_id or enemy_hp.entity_id != self._scenario.enemy_id or actor_hp.entity_id != self._scenario.actor_id or
            stamina.entity_id != self._scenario.actor_id or grid.entity_id != self._scenario.space_id or enemy.entity_id != self._scenario.enemy_id or actor.entity_id != self._scenario.actor_id):
            raise ValueError("invalid encounter identities/order")
        require_integer(actor_hp.hp, 0, 3)
        _subjects(actor.entity_id, actor.space_id, self._scenario)
        _free(actor.cell, self._scenario)
        if gate.space_id != self._scenario.space_id or enemy.space_id != self._scenario.space_id or enemy.cell != self._scenario.enemy_cell:
            raise ValueError("invalid encounter references")
        if actor.cell == self._scenario.gate_cell and gate.is_open == 0 or actor.cell == self._scenario.enemy_cell and enemy_hp.hp > 0:
            raise ValueError("occupied actor placement")
        if any(s.actor_id != self._scenario.actor_id for s in protocol.streams) or core.pending or core.pins.gameplay_packages:
            raise ValueError("invalid encounter streams/pending/packages")


class EncounterPresenter:
    _scenario: Scenario = LEGACY_SCENARIO

    def __init__(self, scenario: Scenario = LEGACY_SCENARIO) -> None:
        self._scenario = scenario

    def map(self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt,
            committed: ReadPort) -> tuple[PresentationEvent, ...]:
        cues: list[PresentationEvent] = []
        for event in facts:
            fact = event.payload
            EncounterPayloadCodec(fact.schema, self._scenario).encode(fact)
            actor = committed.component(CELL_POSITION, self._scenario.actor_id)
            enemy = committed.component(CELL_POSITION, self._scenario.enemy_id)
            gate = committed.component(GATE, self._scenario.gate_id)
            grid = committed.component(TRIAL_MAP, self._scenario.space_id)
            cell, space = actor.cell, actor.space_id
            gate_cell, gate_open, gate_space = gate.cell, gate.is_open, gate.space_id
            enemy_cell, enemy_space = enemy.cell, enemy.space_id
            actor_hp = committed.component(HIT_POINTS, self._scenario.actor_id).hp
            enemy_hp = committed.component(HIT_POINTS, self._scenario.enemy_id).hp
            stamina = committed.component(STAMINA, self._scenario.actor_id).value
            if (space != self._scenario.space_id or enemy_space != space or gate_space != space or
                enemy_cell != self._scenario.enemy_cell or gate_cell != self._scenario.gate_cell or
                grid.width != 3 or grid.height != 3 or grid.cell_mm != 1000 or
                grid.is_blocked(cell) or cell == gate_cell and gate_open == 0 or
                cell == enemy_cell and enemy_hp > 0):
                raise ValueError("presenter committed topology")
            payload: PresentationPayload
            if isinstance(fact, (EncounterMoved, EncounterMoveBlocked)):
                target = fact.to_cell if isinstance(fact, EncounterMoved) else fact.from_cell
                result: Literal["moved", "boundary", "wall", "door", "occupied"]
                result = "moved" if isinstance(fact, EncounterMoved) else fact.reason
                if cell != target or actor_hp == 0:
                    raise ValueError("presenter movement state")
                if isinstance(fact, EncounterMoveBlocked):
                    proposed = (fact.from_cell // 3 + fact.dz) * 3 + fact.from_cell % 3 + fact.dx
                    if (fact.reason == "wall" and not grid.is_blocked(proposed) or
                        fact.reason == "door" and gate_open != 0 or
                        fact.reason == "occupied" and enemy_hp == 0):
                        raise ValueError("presenter dynamic blockage")
                fx, fz = cell_coordinates(fact.from_cell)
                tx, tz = cell_coordinates(target)
                payload = EncounterMoveCue(self._scenario.actor_id, space, fact.from_cell, target,
                                           fx, fz, tx, tz, result)
            elif isinstance(fact, GateChanged):
                if gate_open != fact.after_open or not adjacent_cells(cell, gate_cell) or actor_hp == 0:
                    raise ValueError("presenter gate state")
                x, z = cell_coordinates(gate_cell)
                payload = GateCue(self._scenario.actor_id, self._scenario.gate_id, gate_cell, x, z,
                                  fact.before_open, fact.after_open)
            elif isinstance(fact, AttackResolved):
                if ((actor_hp, enemy_hp, stamina) !=
                    (fact.actor_hp_after, fact.target_hp_after, fact.stamina_after) or
                    not adjacent_cells(cell, enemy_cell)):
                    raise ValueError("presenter attack state")
                payload = AttackCue(self._scenario.actor_id, self._scenario.enemy_id, cell, enemy_cell,
                                    fact.actor_hp_before, fact.actor_hp_after,
                                    fact.target_hp_before, fact.target_hp_after,
                                    fact.stamina_before, fact.stamina_after,
                                    _attack_result(actor_hp, enemy_hp))
            elif isinstance(fact, Rested):
                if stamina != fact.after_stamina or actor_hp == 0:
                    raise ValueError("presenter rest state")
                payload = RestCue(self._scenario.actor_id, fact.before_stamina, fact.after_stamina)
            elif isinstance(fact, Defeated):
                defeated_hp = enemy_hp if fact.entity_id == self._scenario.enemy_id else actor_hp
                killer_hp = actor_hp if fact.killer_id == self._scenario.actor_id else enemy_hp
                if defeated_hp != 0 or killer_hp == 0 or not adjacent_cells(cell, enemy_cell):
                    raise ValueError("presenter defeat state")
                defeat_cell = enemy_cell if fact.entity_id == self._scenario.enemy_id else cell
                x, z = cell_coordinates(defeat_cell)
                payload = DefeatCue(fact.entity_id, fact.killer_id, defeat_cell, x, z)
            else:
                raise SchemaError("UNSUPPORTED_SCHEMA", "encounter presenter fact")
            EncounterPayloadCodec(payload.schema, self._scenario).encode(payload)
            identifier = "p1-" + hashlib.sha256(pack(("cue-id/v1", event.header.event_id,
                                                     "encounter.presenter", str(len(cues))))).hexdigest()
            header = EventHeader(EventId(identifier), payload.schema, "encounter.presenter",
                                 receipt.tick, Phase.PRESENT, 0, 0, len(cues),
                                 (event.header.event_id,), ())
            cues.append(PresentationEvent(header, payload, "important", "keep_all", ""))
        return tuple(cues)
