from __future__ import annotations

from domain.scenario import LEGACY, Scenario, ScenarioBound

from dataclasses import replace
import hashlib
from typing import Literal, cast

from contracts.errors import CandidateError, ReadOnlyViolation, SchemaError
from contracts.dialogue import QuestContent
from contracts.npc_gate_aid import GateAidCue, GateAssisted
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
from domain.state_types import ComponentRecord, CoreSnapshot, StoredRoot
from domain.trial import CellPositionRecord, TrialMapRecord, cell_coordinates
from domain.watch import WAKE_PERIOD
from orchestration.serialization import key_document
from orchestration.trial import CellReducer, CellPositionAdapter, TrialMapAdapter, TrialPayloadCodec
from orchestration.npc_gate_aid import GateAidPayloadCodec


def _free(cell: int, layout: Scenario = LEGACY) -> None:
    cell_coordinates(cell)
    if cell in layout.blocked_cells:
        raise ValueError("wall cell")


def _subjects(actor: EntityId, space: EntityId, layout: Scenario = LEGACY) -> None:
    require_namespace(actor)
    require_namespace(space)
    if actor != layout.actor_id or space != layout.space_id:
        raise ValueError("invalid encounter subjects")


def _pair(actor: EntityId, target: EntityId, expected: EntityId, layout: Scenario = LEGACY) -> None:
    require_namespace(actor)
    require_namespace(target)
    if actor != layout.actor_id or target != expected:
        raise ValueError("invalid encounter pair")


def _defeat(entity: EntityId, killer: EntityId, layout: Scenario = LEGACY) -> None:
    require_namespace(entity)
    require_namespace(killer)
    if (entity, killer) not in ((layout.enemy_id, layout.actor_id), (layout.actor_id, layout.enemy_id)):
        raise ValueError("invalid defeat pair")


def _attack_result(actor_hp: int, target_hp: int) -> Literal["hit", "actor_defeated", "target_defeated"]:
    return "target_defeated" if target_hp == 0 else "actor_defeated" if actor_hp == 0 else "hit"


def scenario_record[T: ComponentRecord](core: CoreSnapshot, kind: type[T], entity: EntityId) -> T:
    records = tuple(c for c in core.components if type(c) is kind and c.entity_id == entity)
    if len(records) != 1:
        raise ValueError("invalid scenario record identity/class")
    return records[0]


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


class GateAdapter(ScenarioBound):
    @property
    def key(self) -> ComponentKey[GateRead]:
        return GATE

    def validate(self, record: ComponentRecord) -> None:
        if type(record) is not GateRecord or record.schema != self.key.schema:
            raise ValueError("invalid Gate class/schema")
        require_namespace(record.entity_id)
        require_namespace(record.space_id)
        require_integer(record.cell, self._layout.gate_cell, self._layout.gate_cell)
        require_integer(record.is_open, 0, 1)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> GateRead:
        self.validate(record)
        assert isinstance(record, GateRecord)
        return _GateView(record, access)


class GateCodec(ScenarioBound):
    @property
    def schema(self) -> TypeKey:
        return GATE.schema

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        d = exact_fields(fields, ('space_id', 'cell', 'is_open'))
        record = GateRecord(entity_id, EntityId(text_value(d["space_id"])), int_value(d["cell"]), int_value(d["is_open"]))
        GateAdapter(layout=self._layout).validate(record)
        return record

    def encode(self, record: ComponentRecord) -> JsonObject:
        GateAdapter(layout=self._layout).validate(record)
        assert isinstance(record, GateRecord)
        return {"space_id": record.space_id, "cell": record.cell, "is_open": record.is_open}


class _HitPointsView(_View):
    __slots__ = ()

    @property
    def hp(self) -> int:
        self._read("hp")
        assert isinstance(self._record, HitPointsRecord)
        return self._record.hp


class HitPointsAdapter(ScenarioBound):
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


class HitPointsCodec(ScenarioBound):
    @property
    def schema(self) -> TypeKey:
        return HIT_POINTS.schema

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        d = exact_fields(fields, ('hp',))
        record = HitPointsRecord(entity_id, int_value(d["hp"]))
        HitPointsAdapter(layout=self._layout).validate(record)
        return record

    def encode(self, record: ComponentRecord) -> JsonObject:
        HitPointsAdapter(layout=self._layout).validate(record)
        assert isinstance(record, HitPointsRecord)
        return {"hp": record.hp}


class _StaminaView(_View):
    __slots__ = ()

    @property
    def value(self) -> int:
        self._read("value")
        assert isinstance(self._record, StaminaRecord)
        return self._record.value


class StaminaAdapter(ScenarioBound):
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


class StaminaCodec(ScenarioBound):
    @property
    def schema(self) -> TypeKey:
        return STAMINA.schema

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        d = exact_fields(fields, ('value',))
        record = StaminaRecord(entity_id, int_value(d["value"]))
        StaminaAdapter(layout=self._layout).validate(record)
        return record

    def encode(self, record: ComponentRecord) -> JsonObject:
        StaminaAdapter(layout=self._layout).validate(record)
        assert isinstance(record, StaminaRecord)
        return {"value": record.value}


def _validate_payload(payload: FrozenPayload, layout: Scenario = LEGACY) -> None:
    if isinstance(payload, InteractCommand):
        require_namespace(payload.target_id)
        if type(payload.option) is not str or payload.option not in ("open", "close"):
            raise ValueError("invalid gate option")
    elif isinstance(payload, AttackCommand):
        require_namespace(payload.target_id)
        require_namespace(payload.profile_id)
    elif isinstance(payload, GateDelta):
        require_namespace(payload.entity_id)
        if payload.entity_id != layout.gate_id:
            raise ValueError("invalid gate delta subject")
        require_integer(payload.before_open, 0, 1)
        require_integer(payload.after_open, 0, 1)
    elif isinstance(payload, HitPointsDelta):
        require_namespace(payload.entity_id)
        if payload.entity_id not in (layout.actor_id, layout.enemy_id):
            raise ValueError("invalid HP delta subject")
        maximum = 3 if payload.entity_id == layout.actor_id else 5
        require_integer(payload.before_hp, 0, maximum)
        require_integer(payload.after_hp, 0, maximum)
    elif isinstance(payload, StaminaDelta):
        require_namespace(payload.entity_id)
        if payload.entity_id != layout.actor_id:
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
        _subjects(payload.actor_id, payload.space_id, layout=layout)
        _free(payload.from_cell, layout=layout)
        if isinstance(payload, EncounterMoveBlocked):
            TrialPayloadCodec(TypeKey("trial.move", 1), layout=layout).encode(MoveCommand(payload.dx, payload.dz))
            x, z = payload.from_cell % 3 + payload.dx, payload.from_cell // 3 + payload.dz
            bounded = 0 <= x < 3 and 0 <= z < 3
            targets = {"wall": layout.blocked_cells[0], "door": layout.gate_cell,
                       "occupied": layout.enemy_cell}
            if type(payload.reason) is not str or (payload.reason == "boundary" and bounded or
                payload.reason != "boundary" and (not bounded or targets.get(payload.reason) != z * 3 + x)):
                raise ValueError("inconsistent movement blockage")
        else:
            _free(payload.to_cell, layout=layout)
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
        _pair(payload.actor_id, payload.target_id, layout.gate_id, layout=layout)
        require_integer(payload.before_open, 0, 1)
        require_integer(payload.after_open, 0, 1)
        if isinstance(payload, GateCue):
            require_integer(payload.cell, layout.gate_cell, layout.gate_cell)
            x, z = cell_coordinates(layout.gate_cell)
            require_integer(payload.x_mm, x, x)
            require_integer(payload.z_mm, z, z)
    elif isinstance(payload, (AttackResolved, AttackCue)):
        _pair(payload.actor_id, payload.target_id, layout.enemy_id, layout=layout)
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
            _free(payload.actor_cell, layout=layout)
            require_integer(payload.target_cell, layout.enemy_cell, layout.enemy_cell)
            if not adjacent_cells(payload.actor_cell, payload.target_cell) or payload.result != _attack_result(expected[0], expected[1]):
                raise ValueError("attack cue geometry/result")
    elif isinstance(payload, (Rested, RestCue)):
        require_namespace(payload.actor_id)
        if payload.actor_id != layout.actor_id:
            raise ValueError("invalid resting actor")
        require_integer(payload.before_stamina, 0, 2)
        require_integer(payload.after_stamina, 0, 2)
        if payload.after_stamina != min(2, payload.before_stamina + 1):
            raise ValueError("rest arithmetic")
    elif isinstance(payload, (Defeated, DefeatCue)):
        _defeat(payload.entity_id, payload.killer_id, layout=layout)
        if isinstance(payload, DefeatCue):
            _free(payload.cell, layout=layout)
            if payload.entity_id == layout.enemy_id and payload.cell != layout.enemy_cell:
                raise ValueError("enemy defeat cell")
            require_integer(payload.x_mm)
            require_integer(payload.z_mm)
            if (payload.x_mm, payload.z_mm) != cell_coordinates(payload.cell):
                raise ValueError("defeat geometry")


class EncounterPayloadCodec(ScenarioBound):
    def __init__(self, schema: TypeKey, layout: Scenario = LEGACY) -> None:
        super().__init__(layout)
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
            _validate_payload(payload, layout=self._layout)
            return {"target_id": payload.target_id, "option": payload.option}
        if type(payload) is AttackCommand:
            _validate_payload(payload, layout=self._layout)
            return {"target_id": payload.target_id, "profile_id": payload.profile_id}
        if type(payload) is RestCommand:
            _validate_payload(payload, layout=self._layout)
            return {}
        if type(payload) is GateDelta:
            _validate_payload(payload, layout=self._layout)
            return {"entity_id": payload.entity_id, "before_open": payload.before_open, "after_open": payload.after_open}
        if type(payload) is HitPointsDelta:
            _validate_payload(payload, layout=self._layout)
            return {"entity_id": payload.entity_id, "before_hp": payload.before_hp, "after_hp": payload.after_hp}
        if type(payload) is StaminaDelta:
            _validate_payload(payload, layout=self._layout)
            return {"entity_id": payload.entity_id, "before_stamina": payload.before_stamina, "after_stamina": payload.after_stamina}
        if type(payload) is GatePatch:
            _validate_payload(payload, layout=self._layout)
            return {"is_open": payload.is_open}
        if type(payload) is HitPointsPatch:
            _validate_payload(payload, layout=self._layout)
            return {"hp": payload.hp}
        if type(payload) is StaminaPatch:
            _validate_payload(payload, layout=self._layout)
            return {"value": payload.value}
        if type(payload) is EncounterMoved:
            _validate_payload(payload, layout=self._layout)
            return {"actor_id": payload.actor_id, "space_id": payload.space_id, "from_cell": payload.from_cell, "to_cell": payload.to_cell}
        if type(payload) is EncounterMoveBlocked:
            _validate_payload(payload, layout=self._layout)
            return {"actor_id": payload.actor_id, "space_id": payload.space_id, "from_cell": payload.from_cell, "dx": payload.dx, "dz": payload.dz, "reason": payload.reason}
        if type(payload) is GateChanged:
            _validate_payload(payload, layout=self._layout)
            return {"actor_id": payload.actor_id, "target_id": payload.target_id, "before_open": payload.before_open, "after_open": payload.after_open}
        if type(payload) is AttackResolved:
            _validate_payload(payload, layout=self._layout)
            return {"actor_id": payload.actor_id, "target_id": payload.target_id, "profile_id": payload.profile_id, "actor_hp_before": payload.actor_hp_before, "actor_hp_after": payload.actor_hp_after, "target_hp_before": payload.target_hp_before, "target_hp_after": payload.target_hp_after, "stamina_before": payload.stamina_before, "stamina_after": payload.stamina_after}
        if type(payload) is Rested:
            _validate_payload(payload, layout=self._layout)
            return {"actor_id": payload.actor_id, "before_stamina": payload.before_stamina, "after_stamina": payload.after_stamina}
        if type(payload) is Defeated:
            _validate_payload(payload, layout=self._layout)
            return {"entity_id": payload.entity_id, "killer_id": payload.killer_id}
        if type(payload) is EncounterMoveCue:
            _validate_payload(payload, layout=self._layout)
            return {"actor_id": payload.actor_id, "space_id": payload.space_id, "from_cell": payload.from_cell, "to_cell": payload.to_cell, "from_x_mm": payload.from_x_mm, "from_z_mm": payload.from_z_mm, "to_x_mm": payload.to_x_mm, "to_z_mm": payload.to_z_mm, "result": payload.result}
        if type(payload) is GateCue:
            _validate_payload(payload, layout=self._layout)
            return {"actor_id": payload.actor_id, "target_id": payload.target_id, "cell": payload.cell, "x_mm": payload.x_mm, "z_mm": payload.z_mm, "before_open": payload.before_open, "after_open": payload.after_open}
        if type(payload) is AttackCue:
            _validate_payload(payload, layout=self._layout)
            return {"actor_id": payload.actor_id, "target_id": payload.target_id, "actor_cell": payload.actor_cell, "target_cell": payload.target_cell, "actor_hp_before": payload.actor_hp_before, "actor_hp_after": payload.actor_hp_after, "target_hp_before": payload.target_hp_before, "target_hp_after": payload.target_hp_after, "stamina_before": payload.stamina_before, "stamina_after": payload.stamina_after, "result": payload.result}
        if type(payload) is RestCue:
            _validate_payload(payload, layout=self._layout)
            return {"actor_id": payload.actor_id, "before_stamina": payload.before_stamina, "after_stamina": payload.after_stamina}
        if type(payload) is DefeatCue:
            _validate_payload(payload, layout=self._layout)
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


class EncounterAdmission(ScenarioBound):
    def __init__(self, schema: TypeKey, layout: Scenario = LEGACY) -> None:
        super().__init__(layout)
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
        if command.actor_id != self._layout.actor_id:
            return TurnRejected(failure("UNAUTHORIZED_ACTOR"), command.expected_revision)
        body = (TrialPayloadCodec(self.schema, layout=self._layout) if self.schema.kind == "trial.move" else EncounterPayloadCodec(self.schema, layout=self._layout)).encode(command.payload)
        if state.component(HIT_POINTS, self._layout.actor_id).hp == 0:
            return TurnRejected(failure("ACTOR_DEFEATED"), command.expected_revision)
        payload = command.payload
        code: str | None = None
        if isinstance(payload, (MoveCommand, InteractCommand, AttackCommand)):
            position = state.component(CELL_POSITION, self._layout.actor_id)
            space, cell = position.space_id, position.cell
            if space != self._layout.space_id:
                raise CandidateError("INVALID_ACTION", "actor space")
            _free(cell, layout=self._layout)
            if isinstance(payload, InteractCommand):
                gate = state.component(GATE, self._layout.gate_id)
                gate_cell, gate_space = gate.cell, gate.space_id
                gate.is_open
                if gate_cell != self._layout.gate_cell or gate_space != space:
                    raise CandidateError("INVALID_ACTION", "gate reference")
                if payload.target_id != self._layout.gate_id:
                    code = "INVALID_TARGET"
                elif payload.option == "close" and cell == gate_cell:
                    code = "TARGET_OCCUPIED"
                elif not adjacent_cells(cell, gate_cell):
                    code = "OUT_OF_RANGE"
            elif isinstance(payload, AttackCommand):
                enemy = state.component(CELL_POSITION, self._layout.enemy_id)
                if enemy.cell != self._layout.enemy_cell or enemy.space_id != space:
                    raise CandidateError("INVALID_ACTION", "enemy reference")
                if payload.target_id != self._layout.enemy_id:
                    code = "INVALID_TARGET"
                elif payload.profile_id != ATTACK_PROFILE_ID:
                    code = "INVALID_ATTACK_PROFILE"
                elif state.component(HIT_POINTS, self._layout.enemy_id).hp == 0:
                    code = "TARGET_DEFEATED"
                elif not adjacent_cells(cell, self._layout.enemy_cell):
                    code = "OUT_OF_RANGE"
                elif state.component(STAMINA, self._layout.actor_id).value == 0:
                    code = "INSUFFICIENT_STAMINA"
        elif isinstance(payload, RestCommand):
            state.component(STAMINA, self._layout.actor_id).value
        else:
            raise CandidateError("INVALID_ACTION", "unsupported admitted payload")
        if code is not None:
            return TurnRejected(failure(code), command.expected_revision)
        target = Tick(start_tick + 1)
        payload_hash = hash_document("payload/v1", {"schema": key_document(payload.schema), "payload": body})
        key = "a1-" + hashlib.sha256(pack(("action-key/v1", world_id, str(target), command.actor_id, payload_hash))).hexdigest()
        return AdmittedCommand(TurnPlan(command, start_tick, target), AdmittedAction(command.actor_id, payload, key))


class EncounterCellReducer(CellReducer):
    def _subject(self, delta: StateDelta) -> None:
        if type(delta) is not CellDelta or delta.entity_id != self._layout.actor_id:
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


class GateReducer(ScenarioBound):
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
            EncounterPayloadCodec(self.schema, layout=self._layout).encode(delta)
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


class GatePatchRoute(ScenarioBound):
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
        GateAdapter(layout=self._layout).validate(before)
        EncounterPayloadCodec(self.schema, layout=self._layout).encode(patch)
        assert isinstance(before, GateRecord) and isinstance(patch, GatePatch)
        return replace(before, is_open=patch.is_open)


class HitPointsReducer(ScenarioBound):
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
            EncounterPayloadCodec(self.schema, layout=self._layout).encode(delta)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "invalid HitPoints delta") from error
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._validate(delta)
        if value.before_hp - value.after_hp not in ((1,) if value.entity_id == self._layout.actor_id else (1, 2)):
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


class HitPointsPatchRoute(ScenarioBound):
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
        HitPointsAdapter(layout=self._layout).validate(before)
        EncounterPayloadCodec(self.schema, layout=self._layout).encode(patch)
        assert isinstance(before, HitPointsRecord) and isinstance(patch, HitPointsPatch)
        return replace(before, hp=patch.hp)


class StaminaReducer(ScenarioBound):
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
            EncounterPayloadCodec(self.schema, layout=self._layout).encode(delta)
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


class StaminaPatchRoute(ScenarioBound):
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
        StaminaAdapter(layout=self._layout).validate(before)
        EncounterPayloadCodec(self.schema, layout=self._layout).encode(patch)
        assert isinstance(before, StaminaRecord) and isinstance(patch, StaminaPatch)
        return replace(before, value=patch.value)


class EncounterCheckpointPolicy(ScenarioBound):
    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        if len(core.components) != 7:
            raise ValueError("exact seven encounter records required")
        StoredRoot(core.components, 0)
        gate = scenario_record(core, GateRecord, self._layout.gate_id)
        enemy_hp = scenario_record(core, HitPointsRecord, self._layout.enemy_id)
        actor_hp = scenario_record(core, HitPointsRecord, self._layout.actor_id)
        stamina = scenario_record(core, StaminaRecord, self._layout.actor_id)
        grid = scenario_record(core, TrialMapRecord, self._layout.space_id)
        enemy = scenario_record(core, CellPositionRecord, self._layout.enemy_id)
        actor = scenario_record(core, CellPositionRecord, self._layout.actor_id)
        GateAdapter(layout=self._layout).validate(gate)
        HitPointsAdapter(layout=self._layout).validate(enemy_hp)
        HitPointsAdapter(layout=self._layout).validate(actor_hp)
        StaminaAdapter(layout=self._layout).validate(stamina)
        TrialMapAdapter(layout=self._layout).validate(grid)
        CellPositionAdapter(layout=self._layout).validate(enemy)
        CellPositionAdapter(layout=self._layout).validate(actor)
        assert isinstance(gate, GateRecord)
        assert isinstance(enemy_hp, HitPointsRecord) and isinstance(actor_hp, HitPointsRecord)
        assert isinstance(stamina, StaminaRecord) and isinstance(grid, TrialMapRecord)
        assert isinstance(enemy, CellPositionRecord) and isinstance(actor, CellPositionRecord)
        if (gate.entity_id != self._layout.gate_id or enemy_hp.entity_id != self._layout.enemy_id or actor_hp.entity_id != self._layout.actor_id or
            stamina.entity_id != self._layout.actor_id or grid.entity_id != self._layout.space_id or enemy.entity_id != self._layout.enemy_id or actor.entity_id != self._layout.actor_id):
            raise ValueError("invalid encounter identities/order")
        require_integer(actor_hp.hp, 0, 3)
        _subjects(actor.entity_id, actor.space_id, layout=self._layout)
        _free(actor.cell, layout=self._layout)
        if gate.space_id != self._layout.space_id or enemy.space_id != self._layout.space_id or enemy.cell != self._layout.enemy_cell:
            raise ValueError("invalid encounter references")
        if actor.cell == self._layout.gate_cell and gate.is_open == 0 or actor.cell == self._layout.enemy_cell and enemy_hp.hp > 0:
            raise ValueError("occupied actor placement")
        if any(s.actor_id != self._layout.actor_id for s in protocol.streams) or core.pending or core.pins.gameplay_packages:
            raise ValueError("invalid encounter streams/pending/packages")


class EncounterPresenter(ScenarioBound):
    def __init__(self, layout: Scenario = LEGACY, *, aid_content: QuestContent | None = None, npc_call_aid: bool = False) -> None:
        super().__init__(layout)
        if aid_content is not None and (type(aid_content) is not QuestContent or aid_content.definition.layout != layout):
            raise ValueError("NPC_AID_CONTENT")
        if type(npc_call_aid) is not bool or npc_call_aid and aid_content is None:
            raise ValueError("NPC_CALL_AID_CONTENT")
        self._npc_call_aid = npc_call_aid
        self._aid_content = aid_content

    def _aid_gate_chain(self, facts: tuple[WorldEvent, ...], final_open: int,
                        receipt: CommitReceipt) -> set[EventId]:
        gates = tuple(e for e in facts if isinstance(e.payload, (GateChanged, GateAssisted)))
        current = final_open
        if gates:
            first = gates[0].payload
            current = first.before_open if isinstance(first, GateChanged) else 0
        blocked: set[EventId] = set()
        previous: tuple[int, int] | None = None
        for event in facts:
            fact, header = event.payload, event.header
            if isinstance(fact, (GateChanged, GateAssisted)):
                expected_phase = Phase.RESOLVE if isinstance(fact, GateChanged) else Phase.POST_TICK
                order = (header.occurred_at, tuple(Phase).index(header.phase))
                if (header.producer_id != "encounter.actions" or header.phase != expected_phase
                        or header.type_key != fact.schema
                        or header.wave != 0 or header.sequence != 0
                        or event.due_tick != header.occurred_at or header.occurred_at > receipt.tick
                        or previous is not None and order <= previous
                        or isinstance(fact, GateChanged) and header.caused_by):
                    raise ValueError("NPC_AID_SOURCE")
                previous = order
                before, after = (fact.before_open, fact.after_open) if isinstance(fact, GateChanged) else (0, 1)
                if isinstance(fact, GateAssisted) and (len(header.caused_by) != 1 or header.occurred_at <= 0 or not self._npc_call_aid and header.occurred_at % WAKE_PERIOD):
                    raise ValueError("NPC_AID_SOURCE")
                if current != before:
                    raise ValueError("NPC_AID_GATE_CHAIN")
                current = after
            elif isinstance(fact, EncounterMoveBlocked) and fact.reason == "door":
                if current != 0:
                    raise ValueError("NPC_AID_GATE_CHAIN")
                blocked.add(header.event_id)
        if current != final_open:
            raise ValueError("NPC_AID_GATE_CHAIN")
        return blocked

    def map(self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt,
            committed: ReadPort) -> tuple[PresentationEvent, ...]:
        cues: list[PresentationEvent] = []
        closed_door_blocks = (self._aid_gate_chain(facts, committed.component(GATE, self._layout.gate_id).is_open, receipt)
                              if self._aid_content is not None else set())
        for event in facts:
            fact = event.payload
            if self._aid_content is not None and isinstance(fact, GateAssisted):
                GateAidPayloadCodec(GateAssisted.SCHEMA, self._aid_content, npc_call_aid=self._npc_call_aid).encode(fact)
            else:
                EncounterPayloadCodec(fact.schema, layout=self._layout).encode(fact)
            actor = committed.component(CELL_POSITION, self._layout.actor_id)
            enemy = committed.component(CELL_POSITION, self._layout.enemy_id)
            gate = committed.component(GATE, self._layout.gate_id)
            grid = committed.component(TRIAL_MAP, self._layout.space_id)
            cell, space = actor.cell, actor.space_id
            gate_cell, gate_open, gate_space = gate.cell, gate.is_open, gate.space_id
            enemy_cell, enemy_space = enemy.cell, enemy.space_id
            actor_hp = committed.component(HIT_POINTS, self._layout.actor_id).hp
            enemy_hp = committed.component(HIT_POINTS, self._layout.enemy_id).hp
            stamina = committed.component(STAMINA, self._layout.actor_id).value
            if (space != self._layout.space_id or enemy_space != space or gate_space != space or
                enemy_cell != self._layout.enemy_cell or gate_cell != self._layout.gate_cell or
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
                        fact.reason == "door" and gate_open != 0 and event.header.event_id not in closed_door_blocks or
                        fact.reason == "occupied" and enemy_hp == 0):
                        raise ValueError("presenter dynamic blockage")
                fx, fz = cell_coordinates(fact.from_cell)
                tx, tz = cell_coordinates(target)
                payload = EncounterMoveCue(self._layout.actor_id, space, fact.from_cell, target,
                                           fx, fz, tx, tz, result)
            elif isinstance(fact, GateChanged):
                if (gate_open != fact.after_open and self._aid_content is None) or not adjacent_cells(cell, gate_cell) or actor_hp == 0:
                    raise ValueError("presenter gate state")
                x, z = cell_coordinates(gate_cell)
                payload = GateCue(self._layout.actor_id, self._layout.gate_id, gate_cell, x, z,
                                  fact.before_open, fact.after_open)
            elif isinstance(fact, GateAssisted) and self._aid_content is not None:
                payload = GateAidCue(self._layout.npc_id, self._layout.gate_id, event.header.occurred_at)
            elif isinstance(fact, AttackResolved):
                if ((actor_hp, enemy_hp, stamina) !=
                    (fact.actor_hp_after, fact.target_hp_after, fact.stamina_after) or
                    not adjacent_cells(cell, enemy_cell)):
                    raise ValueError("presenter attack state")
                payload = AttackCue(self._layout.actor_id, self._layout.enemy_id, cell, enemy_cell,
                                    fact.actor_hp_before, fact.actor_hp_after,
                                    fact.target_hp_before, fact.target_hp_after,
                                    fact.stamina_before, fact.stamina_after,
                                    _attack_result(actor_hp, enemy_hp))
            elif isinstance(fact, Rested):
                if stamina != fact.after_stamina or actor_hp == 0:
                    raise ValueError("presenter rest state")
                payload = RestCue(self._layout.actor_id, fact.before_stamina, fact.after_stamina)
            elif isinstance(fact, Defeated):
                defeated_hp = enemy_hp if fact.entity_id == self._layout.enemy_id else actor_hp
                killer_hp = actor_hp if fact.killer_id == self._layout.actor_id else enemy_hp
                if defeated_hp != 0 or killer_hp == 0 or not adjacent_cells(cell, enemy_cell):
                    raise ValueError("presenter defeat state")
                defeat_cell = enemy_cell if fact.entity_id == self._layout.enemy_id else cell
                x, z = cell_coordinates(defeat_cell)
                payload = DefeatCue(fact.entity_id, fact.killer_id, defeat_cell, x, z)
            else:
                raise SchemaError("UNSUPPORTED_SCHEMA", "encounter presenter fact")
            if isinstance(payload, GateAidCue) and self._aid_content is not None:
                GateAidPayloadCodec(GateAidCue.SCHEMA, self._aid_content, npc_call_aid=self._npc_call_aid).encode(payload)
            else:
                EncounterPayloadCodec(payload.schema, layout=self._layout).encode(payload)
            identifier = "p1-" + hashlib.sha256(pack(("cue-id/v1", event.header.event_id,
                                                     "encounter.presenter", str(len(cues))))).hexdigest()
            header = EventHeader(EventId(identifier), payload.schema, "encounter.presenter",
                                 receipt.tick, Phase.PRESENT, 0, 0, len(cues),
                                 (event.header.event_id,), ())
            cues.append(PresentationEvent(header, payload, "important", "keep_all", ""))
        return tuple(cues)
