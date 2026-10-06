from __future__ import annotations

from dataclasses import replace
import hashlib
from typing import Literal, cast

from contracts.errors import CandidateError, ReadOnlyViolation, SchemaError
from contracts.messages import EventHeader, PresentationEvent, StateDelta, WorldEvent
from contracts.read_views import ComponentKey, ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.trial import (
    CELL_POSITION, TRIAL_MAP, CellDelta, CellPatch, CellPositionRead,
    MoveBlocked, MoveCommand, MoveCue, Moved, TrialMapRead,
)
from contracts.turn import (
    AdmittedAction, AdmittedCommand, AdmissionOutcome, CommitReceipt, GameCommand,
    ProtocolSnapshot, TurnPlan, TurnRejected, failure,
)
from domain.canonical import (
    JsonObject, array_value, exact_fields, hash_document, int_value, pack, text_value,
)
from domain.primitives import (
    ComponentAddress, EntityId, EventId, FieldAddress, FieldFamily, FrozenPayload,
    Phase, Tick, TypeKey, require_integer, require_namespace,
)
from domain.state_types import ComponentRecord, CoreSnapshot
from domain.trial import (
    ACTOR_ID, BLOCKED_CELLS, CELL_MM, HEIGHT, SPACE_ID, WIDTH,
    CellPositionRecord, TrialMapRecord, cell_coordinates,
)
from orchestration.serialization import key_document


def _cell(value: int) -> None:
    require_integer(value, 0, WIDTH * HEIGHT - 1)


def _free(value: int) -> None:
    _cell(value)
    if value in BLOCKED_CELLS:
        raise ValueError("actor cannot occupy wall")


def _cardinal(dx: int, dz: int) -> None:
    require_integer(dx, -1, 1)
    require_integer(dz, -1, 1)
    if abs(dx) + abs(dz) != 1:
        raise ValueError("exact cardinal direction required")


def _adjacent(before: int, after: int) -> None:
    _free(before)
    _free(after)
    x, z = cell_coordinates(before)
    tx, tz = cell_coordinates(after)
    if abs(tx - x) + abs(tz - z) != CELL_MM:
        raise ValueError("distinct adjacent free cells required")


def _subjects(actor: EntityId, space: EntityId) -> None:
    require_namespace(actor)
    require_namespace(space)
    if actor != ACTOR_ID or space != SPACE_ID:
        raise ValueError("invalid trial subjects")


class _View:
    __slots__ = ("_record", "_access")
    _record: TrialMapRecord | CellPositionRecord
    _access: ViewAccess

    def __init__(self, record: TrialMapRecord | CellPositionRecord, access: ViewAccess) -> None:
        object.__setattr__(self, "_record", record)
        object.__setattr__(self, "_access", access)

    def __setattr__(self, name: str, value: object) -> None:
        self._access.observe(FieldAddress(FieldFamily(self._record.schema.kind, name),
                                         self._record.entity_id), (), "write")
        raise ReadOnlyViolation(name)

    def __delattr__(self, name: str) -> None:
        self.__setattr__(name, None)

    def _read(self, name: str) -> None:
        self._access.observe(FieldAddress(FieldFamily(self._record.schema.kind, name),
                                         self._record.entity_id), (), "read")


class _MapView(_View):
    __slots__ = ()

    @property
    def width(self) -> int:
        self._read("width")
        assert isinstance(self._record, TrialMapRecord)
        return self._record.width

    @property
    def height(self) -> int:
        self._read("height")
        assert isinstance(self._record, TrialMapRecord)
        return self._record.height

    @property
    def cell_mm(self) -> int:
        self._read("cell_mm")
        assert isinstance(self._record, TrialMapRecord)
        return self._record.cell_mm

    def is_blocked(self, cell: int) -> bool:
        self._access.observe(FieldAddress(FieldFamily(TRIAL_MAP.schema.kind, "blocked_cells"),
                                         self._record.entity_id), (), "membership")
        _cell(cell)
        assert isinstance(self._record, TrialMapRecord)
        return cell in self._record.blocked_cells


class _PositionView(_View):
    __slots__ = ()

    @property
    def space_id(self) -> EntityId:
        self._read("space_id")
        assert isinstance(self._record, CellPositionRecord)
        return self._record.space_id

    @property
    def cell(self) -> int:
        self._read("cell")
        assert isinstance(self._record, CellPositionRecord)
        return self._record.cell


class TrialMapAdapter:
    @property
    def key(self) -> ComponentKey[TrialMapRead]:
        return TRIAL_MAP

    def validate(self, record: ComponentRecord) -> None:
        if type(record) is not TrialMapRecord or record.schema != self.key.schema:
            raise ValueError("invalid trial map class/schema")
        require_namespace(record.entity_id)
        require_integer(record.width, WIDTH, WIDTH)
        require_integer(record.height, HEIGHT, HEIGHT)
        require_integer(record.cell_mm, CELL_MM, CELL_MM)
        if type(record.blocked_cells) is not tuple:
            raise ValueError("immutable blocks required")
        for cell in record.blocked_cells:
            _cell(cell)
        if record.blocked_cells != BLOCKED_CELLS:
            raise ValueError("fixed sorted unique wall required")

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> TrialMapRead:
        self.validate(record)
        assert isinstance(record, TrialMapRecord)
        return _MapView(record, access)


class CellPositionAdapter:
    @property
    def key(self) -> ComponentKey[CellPositionRead]:
        return CELL_POSITION

    def validate(self, record: ComponentRecord) -> None:
        if type(record) is not CellPositionRecord or record.schema != self.key.schema:
            raise ValueError("invalid cell position class/schema")
        require_namespace(record.entity_id)
        require_namespace(record.space_id)
        _cell(record.cell)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> CellPositionRead:
        self.validate(record)
        assert isinstance(record, CellPositionRecord)
        return _PositionView(record, access)


class TrialMapCodec:
    @property
    def schema(self) -> TypeKey:
        return TRIAL_MAP.schema

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        d = exact_fields(fields, ("width", "height", "cell_mm", "blocked_cells"))
        record = TrialMapRecord(entity_id, int_value(d["width"]), int_value(d["height"]),
                                int_value(d["cell_mm"]),
                                tuple(int_value(c) for c in array_value(d["blocked_cells"])))
        TrialMapAdapter().validate(record)
        return record

    def encode(self, record: ComponentRecord) -> JsonObject:
        TrialMapAdapter().validate(record)
        assert isinstance(record, TrialMapRecord)
        return {"width": record.width, "height": record.height, "cell_mm": record.cell_mm,
                "blocked_cells": record.blocked_cells}


class CellPositionCodec:
    @property
    def schema(self) -> TypeKey:
        return CELL_POSITION.schema

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        d = exact_fields(fields, ("space_id", "cell"))
        record = CellPositionRecord(entity_id, EntityId(text_value(d["space_id"])),
                                    int_value(d["cell"]))
        CellPositionAdapter().validate(record)
        return record

    def encode(self, record: ComponentRecord) -> JsonObject:
        CellPositionAdapter().validate(record)
        assert isinstance(record, CellPositionRecord)
        return {"space_id": record.space_id, "cell": record.cell}


class TrialPayloadCodec:
    def __init__(self, schema: TypeKey) -> None:
        if schema.version != 1 or schema.kind not in (
            "trial.move", "trial.position-delta", "trial.position-patch",
            "trial.moved", "trial.move-blocked", "trial.move-cue",
        ):
            raise SchemaError("UNSUPPORTED_SCHEMA", "trial payload codec")
        self._schema = schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if payload.schema != self.schema:
            raise SchemaError("UNSUPPORTED_SCHEMA", "payload.schema")
        if type(payload) is MoveCommand:
            _cardinal(payload.dx, payload.dz)
            return {"dx": payload.dx, "dz": payload.dz}
        if type(payload) is CellDelta:
            require_namespace(payload.entity_id)
            _cell(payload.before_cell)
            _cell(payload.after_cell)
            return {"entity_id": payload.entity_id, "before_cell": payload.before_cell,
                    "after_cell": payload.after_cell}
        if type(payload) is CellPatch:
            _cell(payload.cell)
            return {"cell": payload.cell}
        if type(payload) is Moved:
            _subjects(payload.actor_id, payload.space_id)
            _adjacent(payload.from_cell, payload.to_cell)
            return {"actor_id": payload.actor_id, "space_id": payload.space_id,
                    "from_cell": payload.from_cell, "to_cell": payload.to_cell}
        if type(payload) is MoveBlocked:
            _subjects(payload.actor_id, payload.space_id)
            _free(payload.from_cell)
            _cardinal(payload.dx, payload.dz)
            x = payload.from_cell % WIDTH + payload.dx
            z = payload.from_cell // WIDTH + payload.dz
            expected = "boundary" if not (0 <= x < WIDTH and 0 <= z < HEIGHT) else "occupied"
            if (payload.reason != expected or
                (expected == "occupied" and z * WIDTH + x not in BLOCKED_CELLS)):
                raise ValueError("inconsistent blockage")
            return {"actor_id": payload.actor_id, "space_id": payload.space_id,
                    "from_cell": payload.from_cell, "dx": payload.dx, "dz": payload.dz,
                    "reason": payload.reason}
        if type(payload) is MoveCue:
            _subjects(payload.actor_id, payload.space_id)
            _free(payload.from_cell)
            _free(payload.to_cell)
            for value in (payload.from_x_mm, payload.from_z_mm,
                          payload.to_x_mm, payload.to_z_mm):
                require_integer(value)
            if ((payload.from_x_mm, payload.from_z_mm) != cell_coordinates(payload.from_cell) or
                (payload.to_x_mm, payload.to_z_mm) != cell_coordinates(payload.to_cell)):
                raise ValueError("cue coordinate mismatch")
            if payload.result == "moved":
                _adjacent(payload.from_cell, payload.to_cell)
            elif payload.result in ("boundary", "occupied"):
                if payload.from_cell != payload.to_cell:
                    raise ValueError("blocked cue endpoints differ")
            else:
                raise ValueError("unsupported cue result")
            return {"actor_id": payload.actor_id, "space_id": payload.space_id,
                    "from_cell": payload.from_cell, "to_cell": payload.to_cell,
                    "from_x_mm": payload.from_x_mm, "from_z_mm": payload.from_z_mm,
                    "to_x_mm": payload.to_x_mm, "to_z_mm": payload.to_z_mm,
                    "result": payload.result}
        raise SchemaError("UNSUPPORTED_SCHEMA", "trial payload class")

    def decode(self, data: JsonObject) -> FrozenPayload:
        value: FrozenPayload
        kind = self.schema.kind
        if kind == "trial.move":
            d = exact_fields(data, ("dx", "dz"))
            value = MoveCommand(int_value(d["dx"]), int_value(d["dz"]))
        elif kind == "trial.position-delta":
            d = exact_fields(data, ("entity_id", "before_cell", "after_cell"))
            value = CellDelta(EntityId(text_value(d["entity_id"])), int_value(d["before_cell"]),
                              int_value(d["after_cell"]))
        elif kind == "trial.position-patch":
            value = CellPatch(int_value(exact_fields(data, ("cell",))["cell"]))
        elif kind == "trial.moved":
            d = exact_fields(data, ("actor_id", "space_id", "from_cell", "to_cell"))
            value = Moved(EntityId(text_value(d["actor_id"])), EntityId(text_value(d["space_id"])),
                          int_value(d["from_cell"]), int_value(d["to_cell"]))
        elif kind == "trial.move-blocked":
            d = exact_fields(data, ("actor_id", "space_id", "from_cell", "dx", "dz", "reason"))
            value = MoveBlocked(EntityId(text_value(d["actor_id"])),
                                EntityId(text_value(d["space_id"])), int_value(d["from_cell"]),
                                int_value(d["dx"]), int_value(d["dz"]),
                                cast(Literal["boundary", "occupied"], text_value(d["reason"])))
        else:
            d = exact_fields(data, ("actor_id", "space_id", "from_cell", "to_cell",
                                   "from_x_mm", "from_z_mm", "to_x_mm", "to_z_mm", "result"))
            value = MoveCue(EntityId(text_value(d["actor_id"])), EntityId(text_value(d["space_id"])),
                            int_value(d["from_cell"]), int_value(d["to_cell"]),
                            int_value(d["from_x_mm"]), int_value(d["from_z_mm"]),
                            int_value(d["to_x_mm"]), int_value(d["to_z_mm"]),
                            cast(Literal["moved", "boundary", "occupied"], text_value(d["result"])))
        self.encode(value)
        return value


class MoveAdmission:
    @property
    def schema(self) -> TypeKey:
        return TypeKey("trial.move", 1)

    @property
    def reads(self) -> tuple[FieldFamily, ...]:
        return (FieldFamily("trial.position", "cell"), FieldFamily("trial.position", "space_id"))

    def admit(self, command: GameCommand, state: ReadPort, *,
              start_tick: Tick, world_id: str) -> AdmissionOutcome:
        if command.actor_id != ACTOR_ID:
            return TurnRejected(failure("UNAUTHORIZED_ACTOR"), command.expected_revision)
        try:
            payload = TrialPayloadCodec(self.schema).encode(command.payload)
            position = state.component(CELL_POSITION, command.actor_id)
            _free(position.cell)
            if position.space_id != SPACE_ID:
                raise ValueError("invalid space reference")
        except ValueError:
            return TurnRejected(failure("INVALID_COMMAND"), command.expected_revision)
        target = Tick(start_tick + 1)
        payload_hash = hash_document("payload/v1", {
            "schema": key_document(command.payload.schema), "payload": payload})
        key = "a1-" + hashlib.sha256(pack(("action-key/v1", world_id, str(target),
                                          command.actor_id, payload_hash))).hexdigest()
        return AdmittedCommand(TurnPlan(command, start_tick, target),
                               AdmittedAction(command.actor_id, command.payload, key))


class CellReducer:
    @property
    def schema(self) -> TypeKey:
        return TypeKey("trial.position-delta", 1)

    @property
    def owner_id(self) -> str:
        return "trial.movement"

    def _validate(self, delta: StateDelta) -> CellDelta:
        if type(delta) is not CellDelta:
            raise CandidateError("INVALID_DELTA", "wrong cell delta class")
        try:
            TrialPayloadCodec(self.schema).encode(delta)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "invalid cell delta shape") from error
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._validate(delta)
        try:
            _adjacent(value.before_cell, value.after_cell)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "illegal cell movement") from error
        if before.component(CELL_POSITION, value.entity_id).cell != value.before_cell:
            raise CandidateError("INVALID_DELTA", "cell old value")
        editor.apply_patch(ComponentAddress(CELL_POSITION.schema, value.entity_id),
                           CellPatch(value.after_cell))

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "empty cell composition")
        values = tuple(self._validate(d) for d in changes)
        for first, second in zip(values, values[1:]):
            if first.target != second.target or first.after_cell != second.before_cell:
                raise CandidateError("INVALID_DELTA", "noncontiguous cell changes")
        return replace(values[0], after_cell=values[-1].after_cell)

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._validate(delta)
        return value.before_cell == value.after_cell

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._validate(delta)
        if self.is_identity(value):
            raise CandidateError("INVALID_DELTA", "identity net delta")
        if after.component(CELL_POSITION, value.entity_id).cell != value.after_cell:
            raise CandidateError("INVALID_DELTA", "net delta does not match head")


class CellPatchRoute:
    @property
    def schema(self) -> TypeKey:
        return TypeKey("trial.position-patch", 1)

    @property
    def component_schema(self) -> TypeKey:
        return CELL_POSITION.schema

    @property
    def family(self) -> FieldFamily:
        return FieldFamily("trial.position", "cell")

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        CellPositionAdapter().validate(before)
        TrialPayloadCodec(self.schema).encode(patch)
        assert isinstance(before, CellPositionRecord) and isinstance(patch, CellPatch)
        return replace(before, cell=patch.cell)


class TrialCheckpointPolicy:
    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        if len(core.components) != 2:
            raise ValueError("exact trial map and actor required")
        grid, position = core.components
        TrialMapAdapter().validate(grid)
        CellPositionAdapter().validate(position)
        assert isinstance(grid, TrialMapRecord) and isinstance(position, CellPositionRecord)
        if grid.entity_id != SPACE_ID:
            raise ValueError("invalid trial map identity")
        _subjects(position.entity_id, position.space_id)
        _free(position.cell)
        if any(s.actor_id != ACTOR_ID for s in protocol.streams):
            raise ValueError("invalid trial stream actor")
        if core.pending or core.pins.gameplay_packages:
            raise ValueError("trial has no pending or gameplay packages")


class MovePresenter:
    def map(self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt,
            committed: ReadPort) -> tuple[PresentationEvent, ...]:
        cues: list[PresentationEvent] = []
        for event in facts:
            fact = event.payload
            if type(fact) not in (Moved, MoveBlocked):
                raise SchemaError("UNSUPPORTED_SCHEMA", "trial presenter fact")
            assert isinstance(fact, (Moved, MoveBlocked))
            TrialPayloadCodec(fact.schema).encode(fact)
            position = committed.component(CELL_POSITION, fact.actor_id)
            space, cell = position.space_id, position.cell
            grid = committed.component(TRIAL_MAP, space)
            width, height, mm = grid.width, grid.height, grid.cell_mm
            if (space != fact.space_id or width != WIDTH or height != HEIGHT or mm != CELL_MM or
                grid.is_blocked(cell)):
                raise ValueError("presenter committed topology mismatch")
            result: Literal["moved", "boundary", "occupied"]
            if isinstance(fact, Moved):
                target, result = fact.to_cell, "moved"
            else:
                target, result = fact.from_cell, fact.reason
                x, z = fact.from_cell % width + fact.dx, fact.from_cell // width + fact.dz
                if fact.reason == "occupied" and not grid.is_blocked(z * width + x):
                    raise ValueError("presenter wall mismatch")
            if cell != target:
                raise ValueError("presenter committed cell mismatch")
            fx, fz = cell_coordinates(fact.from_cell)
            tx, tz = cell_coordinates(target)
            payload = MoveCue(fact.actor_id, space, fact.from_cell, target, fx, fz, tx, tz, result)
            identifier = "p1-" + hashlib.sha256(pack(("cue-id/v1", event.header.event_id,
                                                     "trial.presenter", str(len(cues))))).hexdigest()
            header = EventHeader(EventId(identifier), payload.schema, "trial.presenter", receipt.tick,
                                 Phase.PRESENT, 0, 0, len(cues), (event.header.event_id,), ())
            cues.append(PresentationEvent(header, payload, "important", "keep_all", ""))
        return tuple(cues)
