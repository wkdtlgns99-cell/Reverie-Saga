from __future__ import annotations

from dataclasses import replace
import hashlib
from typing import cast

from contracts.errors import CandidateError, ReadOnlyViolation, SchemaError
from contracts.messages import EventHeader, PresentationEvent, StateDelta, WorldEvent
from contracts.read_views import ComponentKey, ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.skeleton import (
    COUNTER, POSITION, CounterDelta, CounterPatch, CounterRead, PositionDelta, PositionPatch,
    PositionRead, StepCommand, StepCue, Stepped,
)
from contracts.turn import (
    AdmittedAction, AdmittedCommand, AdmissionOutcome, CommitReceipt, GameCommand,
    ProtocolSnapshot, TurnPlan, TurnRejected, failure,
)
from domain.canonical import (
    JsonObject, JsonValue, exact_fields, hash_document, int_value,
    pack, text_value,
)
from domain.primitives import (
    ComponentAddress, EntityId, EventId, FieldAddress, FieldFamily, FrozenPayload, MIN_INT, Phase, Tick, TypeKey, require_integer, require_namespace,
)
from domain.state_types import ComponentRecord, CoreSnapshot, CounterRecord, PositionRecord
from orchestration.serialization import key_document


class _ScalarView:
    def __init__(self, record: PositionRecord | CounterRecord, access: ViewAccess) -> None:
        object.__setattr__(self, "_record", record)
        object.__setattr__(self, "_access", access)
    _record: PositionRecord | CounterRecord
    _access: ViewAccess

    def __setattr__(self, name: str, value: object) -> None:
        self._access.observe(FieldAddress(FieldFamily(self._record.schema.kind, name),
                                         self._record.entity_id), (), "write")
        raise ReadOnlyViolation(name)

    def __delattr__(self, name: str) -> None:
        self.__setattr__(name, None)

    def _read(self, name: str) -> None:
        self._access.observe(FieldAddress(FieldFamily(self._record.schema.kind, name),
                                         self._record.entity_id), (), "read")


class _PositionView(_ScalarView):
    @property
    def x(self) -> int:
        self._read("x")
        assert isinstance(self._record, PositionRecord)
        return self._record.x


class _CounterView(_ScalarView):
    @property
    def visits(self) -> int:
        self._read("visits")
        assert isinstance(self._record, CounterRecord)
        return self._record.visits


class PositionAdapter:
    @property
    def key(self) -> ComponentKey[PositionRead]:
        return POSITION

    def validate(self, record: ComponentRecord) -> None:
        if not isinstance(record, PositionRecord):
            raise ValueError("invalid position record")
        require_namespace(record.entity_id)
        require_integer(record.x, MIN_INT)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> PositionRead:
        self.validate(record)
        assert isinstance(record, PositionRecord)
        return _PositionView(record, access)


class CounterAdapter:
    @property
    def key(self) -> ComponentKey[CounterRead]:
        return COUNTER

    def validate(self, record: ComponentRecord) -> None:
        if not isinstance(record, CounterRecord):
            raise ValueError("invalid counter record")
        require_namespace(record.entity_id)
        require_integer(record.visits)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> CounterRead:
        self.validate(record)
        assert isinstance(record, CounterRecord)
        return _CounterView(record, access)


class StepAdmission:
    def __init__(self, actor_id: EntityId) -> None:
        self._actor_id = actor_id

    @property
    def schema(self) -> TypeKey:
        return TypeKey("skeleton.step", 1)

    @property
    def reads(self) -> tuple[FieldFamily, ...]:
        return (FieldFamily("skeleton.position", "x"),)

    def admit(self, command: GameCommand, state: ReadPort, *,
              start_tick: Tick, world_id: str) -> AdmissionOutcome:
        if command.actor_id != self._actor_id:
            return TurnRejected(failure("UNAUTHORIZED_ACTOR"), command.expected_revision)
        if not isinstance(command.payload, StepCommand) or type(command.payload.dx) is not int or command.payload.dx not in (-1, 0, 1):
            return TurnRejected(failure("INVALID_COMMAND"), command.expected_revision)
        state.component(POSITION, command.actor_id).x
        target = Tick(start_tick + 1)
        payload_hash = hash_document("payload/v1", {
            "schema": key_document(command.payload.schema), "payload": payload_document(command.payload)})
        key = "a1-" + hashlib.sha256(pack(("action-key/v1", world_id, str(target),
                                          command.actor_id, payload_hash))).hexdigest()
        return AdmittedCommand(TurnPlan(command, start_tick, target),
                               AdmittedAction(command.actor_id, command.payload, key))


class PositionReducer:
    @property
    def schema(self) -> TypeKey:
        return TypeKey("skeleton.position-delta", 1)
    @property
    def owner_id(self) -> str:
        return "skeleton.stepper"

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        if not isinstance(delta, PositionDelta):
            raise CandidateError("INVALID_DELTA", "wrong position delta class")
        try:
            require_integer(delta.expected_old, MIN_INT)
            require_integer(delta.new, MIN_INT)
        except ValueError as error:
            raise CandidateError("INTEGER_OVERFLOW", "position bounds") from error
        if before.component(POSITION, delta.entity_id).x != delta.expected_old:
            raise CandidateError("INVALID_DELTA", "position old value")
        editor.apply_patch(ComponentAddress(POSITION.schema, delta.entity_id), PositionPatch(delta.new))

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes or any(not isinstance(d, PositionDelta) for d in changes):
            raise CandidateError("INVALID_DELTA", "position composition")
        values = cast(tuple[PositionDelta, ...], changes)
        for first, second in zip(values, values[1:]):
            if first.target != second.target or first.new != second.expected_old:
                raise CandidateError("INVALID_DELTA", "noncontiguous position changes")
        return replace(values[0], new=values[-1].new)

    def is_identity(self, delta: StateDelta) -> bool:
        if not isinstance(delta, PositionDelta):
            raise CandidateError("INVALID_DELTA", "wrong delta class")
        require_integer(delta.expected_old, MIN_INT)
        require_integer(delta.new, MIN_INT)
        require_namespace(delta.entity_id)
        return delta.expected_old == delta.new

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        if self.is_identity(delta) or not isinstance(delta, PositionDelta):
            raise CandidateError("INVALID_DELTA", "identity net delta")
        if after.component(POSITION, delta.entity_id).x != delta.new:
            raise CandidateError("INVALID_DELTA", "net delta does not match head")


class CounterReducer:
    @property
    def schema(self) -> TypeKey:
        return TypeKey("skeleton.counter-delta", 1)
    @property
    def owner_id(self) -> str:
        return "skeleton.counter"

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        if not isinstance(delta, CounterDelta):
            raise CandidateError("INVALID_DELTA", "wrong counter delta class")
        try:
            require_integer(delta.expected_old)
            require_integer(delta.new)
        except ValueError as error:
            raise CandidateError("INTEGER_OVERFLOW", "counter bounds") from error
        if before.component(COUNTER, delta.entity_id).visits != delta.expected_old:
            raise CandidateError("INVALID_DELTA", "counter old value")
        editor.apply_patch(ComponentAddress(COUNTER.schema, delta.entity_id), CounterPatch(delta.new))

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes or any(not isinstance(d, CounterDelta) for d in changes):
            raise CandidateError("INVALID_DELTA", "counter composition")
        values = cast(tuple[CounterDelta, ...], changes)
        for first, second in zip(values, values[1:]):
            if first.target != second.target or first.new != second.expected_old:
                raise CandidateError("INVALID_DELTA", "noncontiguous counter changes")
        return replace(values[0], new=values[-1].new)

    def is_identity(self, delta: StateDelta) -> bool:
        if not isinstance(delta, CounterDelta):
            raise CandidateError("INVALID_DELTA", "wrong delta class")
        require_integer(delta.expected_old, 0)
        require_integer(delta.new, 0)
        require_namespace(delta.entity_id)
        return delta.expected_old == delta.new

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        if self.is_identity(delta) or not isinstance(delta, CounterDelta):
            raise CandidateError("INVALID_DELTA", "identity net delta")
        if after.component(COUNTER, delta.entity_id).visits != delta.new:
            raise CandidateError("INVALID_DELTA", "net delta does not match head")


def payload_document(payload: FrozenPayload) -> JsonObject:
    if isinstance(payload, StepCommand):
        require_integer(payload.dx, -1, 1)
        return {"dx": payload.dx}
    if isinstance(payload, (Stepped, StepCue)):
        require_integer(payload.from_x, MIN_INT)
        require_integer(payload.to_x, MIN_INT)
        data: dict[str, JsonValue] = {"from_x": payload.from_x, "to_x": payload.to_x}
        if isinstance(payload, StepCue):
            require_namespace(payload.actor_id)
            data["actor_id"] = payload.actor_id
        return data
    if isinstance(payload, (PositionDelta, CounterDelta)):
        require_namespace(payload.entity_id)
        minimum = MIN_INT if isinstance(payload, PositionDelta) else 0
        require_integer(payload.expected_old, minimum)
        require_integer(payload.new, minimum)
        return {"entity_id": payload.entity_id, "expected_old": payload.expected_old, "new": payload.new}
    if isinstance(payload, PositionPatch):
        require_integer(payload.x, MIN_INT)
        return {"x": payload.x}
    if isinstance(payload, CounterPatch):
        require_integer(payload.visits)
        return {"visits": payload.visits}
    raise SchemaError("UNSUPPORTED_SCHEMA", "payload")


class ToyCodec:
    def __init__(self, schema: TypeKey) -> None:
        self._schema = schema
    @property
    def schema(self) -> TypeKey:
        return self._schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if payload.schema != self.schema:
            raise SchemaError("UNSUPPORTED_SCHEMA", "payload.schema")
        return payload_document(payload)

    def decode(self, data: JsonObject) -> FrozenPayload:
        kind = self.schema.kind
        value: FrozenPayload
        if kind == "skeleton.step":
            d = exact_fields(data, ("dx",))
            value = StepCommand(int_value(d["dx"]))
        elif kind == "skeleton.stepped":
            d = exact_fields(data, ("from_x", "to_x"))
            value = Stepped(int_value(d["from_x"]), int_value(d["to_x"]))
        elif kind == "skeleton.step-cue":
            d = exact_fields(data, ("actor_id", "from_x", "to_x"))
            value = StepCue(EntityId(text_value(d["actor_id"])), int_value(d["from_x"]), int_value(d["to_x"]))
        elif kind in ("skeleton.position-delta", "skeleton.counter-delta"):
            d = exact_fields(data, ("entity_id", "expected_old", "new"))
            cls = PositionDelta if kind == "skeleton.position-delta" else CounterDelta
            value = cls(EntityId(text_value(d["entity_id"])), int_value(d["expected_old"]), int_value(d["new"]))
        elif kind == "skeleton.position-patch":
            value = PositionPatch(int_value(exact_fields(data, ("x",))["x"]))
        elif kind == "skeleton.counter-patch":
            value = CounterPatch(int_value(exact_fields(data, ("visits",))["visits"]))
        else:
            raise SchemaError("UNSUPPORTED_SCHEMA", "payload.schema")
        self.encode(value)
        return value


class StepPresenter:
    def map(self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt,
            committed: ReadPort) -> tuple[PresentationEvent, ...]:
        cues: list[PresentationEvent] = []
        for event in facts:
            if not isinstance(event.payload, Stepped):
                raise SchemaError("UNSUPPORTED_SCHEMA", "presenter")
            actor = EntityId("actor:toy")
            committed.component(POSITION, actor).x
            identifier = "p1-" + hashlib.sha256(pack(("cue-id/v1", event.header.event_id,
                                                     "skeleton.presenter", str(len(cues))))).hexdigest()
            payload = StepCue(actor, event.payload.from_x, event.payload.to_x)
            header = EventHeader(EventId(identifier), payload.schema, "skeleton.presenter",
                                 receipt.tick, Phase.PRESENT, 0, 0, len(cues),
                                 (event.header.event_id,), ())
            cues.append(PresentationEvent(header, payload, "important", "keep_all", ""))
        return tuple(cues)


class PositionCodec:
    @property
    def schema(self) -> TypeKey:
        return POSITION.schema

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        return PositionRecord(entity_id, int_value(exact_fields(fields, ("x",))["x"]))

    def encode(self, record: ComponentRecord) -> JsonObject:
        PositionAdapter().validate(record)
        assert isinstance(record, PositionRecord)
        return {"x": record.x}


class CounterCodec:
    @property
    def schema(self) -> TypeKey:
        return COUNTER.schema

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        return CounterRecord(entity_id, int_value(exact_fields(fields, ("visits",))["visits"]))

    def encode(self, record: ComponentRecord) -> JsonObject:
        CounterAdapter().validate(record)
        assert isinstance(record, CounterRecord)
        return {"visits": record.visits}


class PositionPatchRoute:
    @property
    def schema(self) -> TypeKey:
        return TypeKey("skeleton.position-patch", 1)

    @property
    def component_schema(self) -> TypeKey:
        return POSITION.schema

    @property
    def family(self) -> FieldFamily:
        return FieldFamily(POSITION.schema.kind, "x")

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        if not isinstance(before, PositionRecord) or not isinstance(patch, PositionPatch):
            raise ValueError("position patch class")
        return replace(before, x=patch.x)


class CounterPatchRoute:
    @property
    def schema(self) -> TypeKey:
        return TypeKey("skeleton.counter-patch", 1)

    @property
    def component_schema(self) -> TypeKey:
        return COUNTER.schema

    @property
    def family(self) -> FieldFamily:
        return FieldFamily(COUNTER.schema.kind, "visits")

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        if not isinstance(before, CounterRecord) or not isinstance(patch, CounterPatch):
            raise ValueError("counter patch class")
        return replace(before, visits=patch.visits)


class SkeletonCheckpointPolicy:
    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        if len(core.components) != 2 or {c.entity_id for c in core.components} != {EntityId("actor:toy")}:
            raise ValueError("invalid toy component set")
        if tuple(c.schema for c in core.components) != (COUNTER.schema, POSITION.schema):
            raise ValueError("missing toy component")
        if any(s.actor_id != "actor:toy" for s in protocol.streams):
            raise ValueError("invalid toy stream actor")


