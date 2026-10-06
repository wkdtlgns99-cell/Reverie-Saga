from __future__ import annotations

from dataclasses import replace
import hashlib
from contracts.errors import CandidateError, ReadOnlyViolation, SchemaError
from contracts.watch import (WATCH_NPC, LANTERN, REPLY, WatchNpcRead, LanternRead, ReplyRead,
    WaitCommand, BellCommand, WatchWake, WatchRequested, WatchEcho, NpcActed, BellRung, WatchReplied, NpcCue, BellCue, ReplyCue, ChargeDelta, ChargePatch, BellsDelta, BellsPatch, ReplyDelta, ReplyPatch)
from contracts.encounter import HIT_POINTS
from contracts.trial import CELL_POSITION
from contracts.messages import EventHeader, PresentationEvent, PresentationPayload, StateDelta, WorldEvent
from contracts.read_views import ComponentKey, ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.turn import AdmittedAction, AdmittedCommand, AdmissionOutcome, CommitReceipt, GameCommand, ProtocolSnapshot, TurnPlan, TurnRejected, failure
from domain.canonical import JsonObject, decode_json, exact_fields, hash_document, int_value, object_value, pack, text_value
from domain.primitives import ComponentAddress, EntityId, EventId, FieldAddress, FieldFamily, FrozenPayload, MAX_INT, Phase, Tick, TypeKey, require_integer, require_namespace
from domain.state_types import ComponentRecord, CoreSnapshot
from domain.trial import ACTOR_ID, SPACE_ID
from domain.watch import NPC_ID, LANTERN_ID, NPC_CELL, WatchNpcRecord, LanternRecord, ReplyRecord, next_wake
from orchestration.encounter import EncounterCheckpointPolicy
from orchestration.serialization import key_document


class _View:
    __slots__ = ("_record", "_access")
    _record: WatchNpcRecord | LanternRecord | ReplyRecord
    _access: ViewAccess

    def __init__(self, record: WatchNpcRecord | LanternRecord | ReplyRecord, access: ViewAccess) -> None:
        object.__setattr__(self, "_record", record)
        object.__setattr__(self, "_access", access)

    def __setattr__(self, name: str, value: object) -> None:
        self._access.observe(FieldAddress(FieldFamily(self._record.schema.kind, name), self._record.entity_id), (), "write")
        raise ReadOnlyViolation(name)

    def __delattr__(self, name: str) -> None:
        self.__setattr__(name, None)

    def _read(self, name: str) -> None:
        self._access.observe(FieldAddress(FieldFamily(self._record.schema.kind, name), self._record.entity_id), (), "read")


class _WatchNpcView(_View):
    __slots__ = ()

    @property
    def space_id(self) -> EntityId:
        self._read("space_id")
        assert isinstance(self._record, WatchNpcRecord)
        return self._record.space_id

    @property
    def cell(self) -> int:
        self._read("cell")
        assert isinstance(self._record, WatchNpcRecord)
        return self._record.cell

    @property
    def bells(self) -> int:
        self._read("bells")
        assert isinstance(self._record, WatchNpcRecord)
        return self._record.bells


class WatchNpcAdapter:
    @property
    def key(self) -> ComponentKey[WatchNpcRead]:
        return WATCH_NPC

    def validate(self, record: ComponentRecord) -> None:
        if type(record) is not WatchNpcRecord or record.schema != self.key.schema:
            raise ValueError("invalid WatchNpc record")
        require_namespace(record.entity_id)
        require_namespace(record.space_id)
        require_integer(record.cell, 6, 6)
        require_integer(record.bells, 0, MAX_INT)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> WatchNpcRead:
        self.validate(record)
        assert isinstance(record, WatchNpcRecord)
        return _WatchNpcView(record, access)


class WatchNpcCodec:
    @property
    def schema(self) -> TypeKey:
        return WATCH_NPC.schema

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        d = exact_fields(fields, ('space_id', 'cell', 'bells'))
        record = WatchNpcRecord(entity_id, EntityId(text_value(d["space_id"])), int_value(d["cell"]), int_value(d["bells"]))
        WatchNpcAdapter().validate(record)
        return record

    def encode(self, record: ComponentRecord) -> JsonObject:
        WatchNpcAdapter().validate(record)
        assert isinstance(record, WatchNpcRecord)
        return {"space_id": record.space_id, "cell": record.cell, "bells": record.bells}


class _LanternView(_View):
    __slots__ = ()

    @property
    def charge(self) -> int:
        self._read("charge")
        assert isinstance(self._record, LanternRecord)
        return self._record.charge


class LanternAdapter:
    @property
    def key(self) -> ComponentKey[LanternRead]:
        return LANTERN

    def validate(self, record: ComponentRecord) -> None:
        if type(record) is not LanternRecord or record.schema != self.key.schema:
            raise ValueError("invalid Lantern record")
        require_namespace(record.entity_id)
        require_integer(record.charge, 0, 3)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> LanternRead:
        self.validate(record)
        assert isinstance(record, LanternRecord)
        return _LanternView(record, access)


class LanternCodec:
    @property
    def schema(self) -> TypeKey:
        return LANTERN.schema

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        d = exact_fields(fields, ('charge',))
        record = LanternRecord(entity_id, int_value(d["charge"]))
        LanternAdapter().validate(record)
        return record

    def encode(self, record: ComponentRecord) -> JsonObject:
        LanternAdapter().validate(record)
        assert isinstance(record, LanternRecord)
        return {"charge": record.charge}


class _ReplyView(_View):
    __slots__ = ()

    @property
    def count(self) -> int:
        self._read("count")
        assert isinstance(self._record, ReplyRecord)
        return self._record.count


class ReplyAdapter:
    @property
    def key(self) -> ComponentKey[ReplyRead]:
        return REPLY

    def validate(self, record: ComponentRecord) -> None:
        if type(record) is not ReplyRecord or record.schema != self.key.schema:
            raise ValueError("invalid Reply record")
        require_namespace(record.entity_id)
        require_integer(record.count, 0, MAX_INT)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> ReplyRead:
        self.validate(record)
        assert isinstance(record, ReplyRecord)
        return _ReplyView(record, access)


class ReplyCodec:
    @property
    def schema(self) -> TypeKey:
        return REPLY.schema

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        d = exact_fields(fields, ('count',))
        record = ReplyRecord(entity_id, int_value(d["count"]))
        ReplyAdapter().validate(record)
        return record

    def encode(self, record: ComponentRecord) -> JsonObject:
        ReplyAdapter().validate(record)
        assert isinstance(record, ReplyRecord)
        return {"count": record.count}


def _validate_payload(payload: FrozenPayload) -> None:
    if isinstance(payload, WaitCommand):
        require_integer(payload.seconds, 1, 16)
    elif isinstance(payload, BellCommand):
        require_namespace(payload.npc_id)
    elif isinstance(payload, WatchWake):
        require_namespace(payload.npc_id)
        if payload.npc_id != NPC_ID:
            raise ValueError("invalid wake subject")
    elif isinstance(payload, WatchRequested):
        require_namespace(payload.actor_id)
        if payload.actor_id != ACTOR_ID:
            raise ValueError("invalid requested subject")
        require_namespace(payload.npc_id)
        if payload.npc_id != NPC_ID:
            raise ValueError("invalid requested subject")
    elif isinstance(payload, WatchEcho):
        require_namespace(payload.npc_id)
        if payload.npc_id != NPC_ID:
            raise ValueError("invalid echo subject")
        require_integer(payload.remaining, 0, 7)
    elif isinstance(payload, NpcActed):
        require_namespace(payload.npc_id)
        if payload.npc_id != NPC_ID:
            raise ValueError("invalid npc-acted subject")
        require_integer(payload.before_bells, 0, MAX_INT)
        require_integer(payload.after_bells, 0, MAX_INT)
        if payload.after_bells != payload.before_bells + 1:
            raise ValueError("invalid count step")
    elif isinstance(payload, BellRung):
        require_namespace(payload.actor_id)
        if payload.actor_id != ACTOR_ID:
            raise ValueError("invalid bell-rung subject")
        require_namespace(payload.npc_id)
        if payload.npc_id != NPC_ID:
            raise ValueError("invalid bell-rung subject")
    elif isinstance(payload, WatchReplied):
        require_namespace(payload.npc_id)
        if payload.npc_id != NPC_ID:
            raise ValueError("invalid replied subject")
        require_integer(payload.before_count, 0, MAX_INT)
        require_integer(payload.after_count, 0, MAX_INT)
        if payload.after_count != payload.before_count + 1:
            raise ValueError("invalid count step")
    elif isinstance(payload, NpcCue):
        require_namespace(payload.npc_id)
        if payload.npc_id != NPC_ID:
            raise ValueError("invalid npc-cue subject")
        require_integer(payload.logical_tick, 1, MAX_INT)
        require_integer(payload.before_bells, 0, MAX_INT)
        require_integer(payload.after_bells, 0, MAX_INT)
        require_integer(payload.cell, 6, 6)
        require_integer(payload.x_mm, 0, 0)
        require_integer(payload.z_mm, 2000, 2000)
        if payload.after_bells != payload.before_bells + 1:
            raise ValueError("invalid count step")
        if payload.logical_tick % 2 or payload.after_bells != payload.logical_tick // 2:
            raise ValueError("invalid NPC cue time")
    elif isinstance(payload, BellCue):
        require_namespace(payload.actor_id)
        if payload.actor_id != ACTOR_ID:
            raise ValueError("invalid bell-cue subject")
        require_namespace(payload.npc_id)
        if payload.npc_id != NPC_ID:
            raise ValueError("invalid bell-cue subject")
        require_integer(payload.logical_tick, 1, MAX_INT)
    elif isinstance(payload, ReplyCue):
        require_namespace(payload.npc_id)
        if payload.npc_id != NPC_ID:
            raise ValueError("invalid reply-cue subject")
        require_integer(payload.logical_tick, 1, MAX_INT)
        require_integer(payload.before_count, 0, MAX_INT)
        require_integer(payload.after_count, 0, MAX_INT)
        if payload.after_count != payload.before_count + 1:
            raise ValueError("invalid count step")
    elif isinstance(payload, ChargeDelta):
        require_namespace(payload.entity_id)
        if payload.entity_id != LANTERN_ID:
            raise ValueError("invalid charge-delta subject")
        require_integer(payload.before_charge, 0, 3)
        require_integer(payload.after_charge, 0, 3)
    elif isinstance(payload, ChargePatch):
        require_integer(payload.charge, 0, 3)
    elif isinstance(payload, BellsDelta):
        require_namespace(payload.entity_id)
        if payload.entity_id != NPC_ID:
            raise ValueError("invalid bells-delta subject")
        require_integer(payload.before_bells, 0, MAX_INT)
        require_integer(payload.after_bells, 0, MAX_INT)
    elif isinstance(payload, BellsPatch):
        require_integer(payload.bells, 0, MAX_INT)
    elif isinstance(payload, ReplyDelta):
        require_namespace(payload.entity_id)
        if payload.entity_id != NPC_ID:
            raise ValueError("invalid reply-delta subject")
        require_integer(payload.before_count, 0, MAX_INT)
        require_integer(payload.after_count, 0, MAX_INT)
    elif isinstance(payload, ReplyPatch):
        require_integer(payload.count, 0, MAX_INT)
    else:
        raise SchemaError("UNSUPPORTED_SCHEMA", "watch payload class")


class WatchPayloadCodec:
    def __init__(self, schema: TypeKey) -> None:
        if schema not in tuple(TypeKey("watch." + k, 1) for k in ('wait', 'bell', 'wake', 'requested', 'echo', 'npc-acted', 'bell-rung', 'replied', 'npc-cue', 'bell-cue', 'reply-cue', 'charge-delta', 'charge-patch', 'bells-delta', 'bells-patch', 'reply-delta', 'reply-patch')):
            raise SchemaError("UNSUPPORTED_SCHEMA", "watch codec")
        self._schema = schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if payload.schema != self.schema:
            raise SchemaError("UNSUPPORTED_SCHEMA", "watch payload schema")
        if type(payload) is WaitCommand:
            _validate_payload(payload)
            return {"seconds": payload.seconds}
        if type(payload) is BellCommand:
            _validate_payload(payload)
            return {"npc_id": payload.npc_id}
        if type(payload) is WatchWake:
            _validate_payload(payload)
            return {"npc_id": payload.npc_id}
        if type(payload) is WatchRequested:
            _validate_payload(payload)
            return {"actor_id": payload.actor_id, "npc_id": payload.npc_id}
        if type(payload) is WatchEcho:
            _validate_payload(payload)
            return {"npc_id": payload.npc_id, "remaining": payload.remaining}
        if type(payload) is NpcActed:
            _validate_payload(payload)
            return {"npc_id": payload.npc_id, "before_bells": payload.before_bells, "after_bells": payload.after_bells}
        if type(payload) is BellRung:
            _validate_payload(payload)
            return {"actor_id": payload.actor_id, "npc_id": payload.npc_id}
        if type(payload) is WatchReplied:
            _validate_payload(payload)
            return {"npc_id": payload.npc_id, "before_count": payload.before_count, "after_count": payload.after_count}
        if type(payload) is NpcCue:
            _validate_payload(payload)
            return {"npc_id": payload.npc_id, "logical_tick": payload.logical_tick, "before_bells": payload.before_bells, "after_bells": payload.after_bells, "cell": payload.cell, "x_mm": payload.x_mm, "z_mm": payload.z_mm}
        if type(payload) is BellCue:
            _validate_payload(payload)
            return {"actor_id": payload.actor_id, "npc_id": payload.npc_id, "logical_tick": payload.logical_tick}
        if type(payload) is ReplyCue:
            _validate_payload(payload)
            return {"npc_id": payload.npc_id, "logical_tick": payload.logical_tick, "before_count": payload.before_count, "after_count": payload.after_count}
        if type(payload) is ChargeDelta:
            _validate_payload(payload)
            return {"entity_id": payload.entity_id, "before_charge": payload.before_charge, "after_charge": payload.after_charge}
        if type(payload) is ChargePatch:
            _validate_payload(payload)
            return {"charge": payload.charge}
        if type(payload) is BellsDelta:
            _validate_payload(payload)
            return {"entity_id": payload.entity_id, "before_bells": payload.before_bells, "after_bells": payload.after_bells}
        if type(payload) is BellsPatch:
            _validate_payload(payload)
            return {"bells": payload.bells}
        if type(payload) is ReplyDelta:
            _validate_payload(payload)
            return {"entity_id": payload.entity_id, "before_count": payload.before_count, "after_count": payload.after_count}
        if type(payload) is ReplyPatch:
            _validate_payload(payload)
            return {"count": payload.count}
        raise SchemaError("UNSUPPORTED_SCHEMA", "watch payload class")

    def decode(self, data: JsonObject) -> FrozenPayload:
        value: FrozenPayload
        if self.schema.kind == "watch.wait":
            d = exact_fields(data, ('seconds',))
            value = WaitCommand(int_value(d["seconds"]))
        elif self.schema.kind == "watch.bell":
            d = exact_fields(data, ('npc_id',))
            value = BellCommand(EntityId(text_value(d["npc_id"])))
        elif self.schema.kind == "watch.wake":
            d = exact_fields(data, ('npc_id',))
            value = WatchWake(EntityId(text_value(d["npc_id"])))
        elif self.schema.kind == "watch.requested":
            d = exact_fields(data, ('actor_id', 'npc_id'))
            value = WatchRequested(EntityId(text_value(d["actor_id"])), EntityId(text_value(d["npc_id"])))
        elif self.schema.kind == "watch.echo":
            d = exact_fields(data, ('npc_id', 'remaining'))
            value = WatchEcho(EntityId(text_value(d["npc_id"])), int_value(d["remaining"]))
        elif self.schema.kind == "watch.npc-acted":
            d = exact_fields(data, ('npc_id', 'before_bells', 'after_bells'))
            value = NpcActed(EntityId(text_value(d["npc_id"])), int_value(d["before_bells"]), int_value(d["after_bells"]))
        elif self.schema.kind == "watch.bell-rung":
            d = exact_fields(data, ('actor_id', 'npc_id'))
            value = BellRung(EntityId(text_value(d["actor_id"])), EntityId(text_value(d["npc_id"])))
        elif self.schema.kind == "watch.replied":
            d = exact_fields(data, ('npc_id', 'before_count', 'after_count'))
            value = WatchReplied(EntityId(text_value(d["npc_id"])), int_value(d["before_count"]), int_value(d["after_count"]))
        elif self.schema.kind == "watch.npc-cue":
            d = exact_fields(data, ('npc_id', 'logical_tick', 'before_bells', 'after_bells', 'cell', 'x_mm', 'z_mm'))
            value = NpcCue(EntityId(text_value(d["npc_id"])), Tick(int_value(d["logical_tick"])), int_value(d["before_bells"]), int_value(d["after_bells"]), int_value(d["cell"]), int_value(d["x_mm"]), int_value(d["z_mm"]))
        elif self.schema.kind == "watch.bell-cue":
            d = exact_fields(data, ('actor_id', 'npc_id', 'logical_tick'))
            value = BellCue(EntityId(text_value(d["actor_id"])), EntityId(text_value(d["npc_id"])), Tick(int_value(d["logical_tick"])))
        elif self.schema.kind == "watch.reply-cue":
            d = exact_fields(data, ('npc_id', 'logical_tick', 'before_count', 'after_count'))
            value = ReplyCue(EntityId(text_value(d["npc_id"])), Tick(int_value(d["logical_tick"])), int_value(d["before_count"]), int_value(d["after_count"]))
        elif self.schema.kind == "watch.charge-delta":
            d = exact_fields(data, ('entity_id', 'before_charge', 'after_charge'))
            value = ChargeDelta(EntityId(text_value(d["entity_id"])), int_value(d["before_charge"]), int_value(d["after_charge"]))
        elif self.schema.kind == "watch.charge-patch":
            d = exact_fields(data, ('charge',))
            value = ChargePatch(int_value(d["charge"]))
        elif self.schema.kind == "watch.bells-delta":
            d = exact_fields(data, ('entity_id', 'before_bells', 'after_bells'))
            value = BellsDelta(EntityId(text_value(d["entity_id"])), int_value(d["before_bells"]), int_value(d["after_bells"]))
        elif self.schema.kind == "watch.bells-patch":
            d = exact_fields(data, ('bells',))
            value = BellsPatch(int_value(d["bells"]))
        elif self.schema.kind == "watch.reply-delta":
            d = exact_fields(data, ('entity_id', 'before_count', 'after_count'))
            value = ReplyDelta(EntityId(text_value(d["entity_id"])), int_value(d["before_count"]), int_value(d["after_count"]))
        elif self.schema.kind == "watch.reply-patch":
            d = exact_fields(data, ('count',))
            value = ReplyPatch(int_value(d["count"]))
        else:
            raise SchemaError("UNSUPPORTED_SCHEMA", "watch decode")
        self.encode(value)
        return value


class ChargeReducer:
    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.charge-delta", 1)

    @property
    def owner_id(self) -> str:
        return "watch.passive"

    def _validate(self, delta: StateDelta) -> ChargeDelta:
        if type(delta) is not ChargeDelta:
            raise CandidateError("INVALID_DELTA", "watch delta class")
        try:
            WatchPayloadCodec(self.schema).encode(delta)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "watch delta payload") from error
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._validate(delta)
        if not 1 <= value.after_charge - value.before_charge <= 1:
            raise CandidateError("INVALID_DELTA", "watch delta step")
        if before.component(LANTERN, value.entity_id).charge != value.before_charge:
            raise CandidateError("INVALID_DELTA", "watch old value")
        editor.apply_patch(ComponentAddress(LANTERN.schema, value.entity_id), ChargePatch(value.after_charge))

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "empty watch composition")
        values = tuple(self._validate(d) for d in changes)
        for first, second in zip(values, values[1:]):
            if first.target != second.target or first.after_charge != second.before_charge:
                raise CandidateError("INVALID_DELTA", "noncontiguous watch composition")
        return replace(values[0], after_charge=values[-1].after_charge)

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._validate(delta)
        return value.before_charge == value.after_charge

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._validate(delta)
        if self.is_identity(value) or after.component(LANTERN, value.entity_id).charge != value.after_charge:
            raise CandidateError("INVALID_DELTA", "watch net mismatch")


class ChargePatchRoute:
    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.charge-patch", 1)

    @property
    def component_schema(self) -> TypeKey:
        return LANTERN.schema

    @property
    def family(self) -> FieldFamily:
        return FieldFamily("watch.lantern", "charge")

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        LanternAdapter().validate(before)
        WatchPayloadCodec(self.schema).encode(patch)
        assert isinstance(before, LanternRecord) and isinstance(patch, ChargePatch)
        return replace(before, charge=patch.charge)


class BellsReducer:
    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.bells-delta", 1)

    @property
    def owner_id(self) -> str:
        return "watch.npc"

    def _validate(self, delta: StateDelta) -> BellsDelta:
        if type(delta) is not BellsDelta:
            raise CandidateError("INVALID_DELTA", "watch delta class")
        try:
            WatchPayloadCodec(self.schema).encode(delta)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "watch delta payload") from error
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._validate(delta)
        if not 1 <= value.after_bells - value.before_bells <= 1:
            raise CandidateError("INVALID_DELTA", "watch delta step")
        if before.component(WATCH_NPC, value.entity_id).bells != value.before_bells:
            raise CandidateError("INVALID_DELTA", "watch old value")
        editor.apply_patch(ComponentAddress(WATCH_NPC.schema, value.entity_id), BellsPatch(value.after_bells))

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "empty watch composition")
        values = tuple(self._validate(d) for d in changes)
        for first, second in zip(values, values[1:]):
            if first.target != second.target or first.after_bells != second.before_bells:
                raise CandidateError("INVALID_DELTA", "noncontiguous watch composition")
        return replace(values[0], after_bells=values[-1].after_bells)

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._validate(delta)
        return value.before_bells == value.after_bells

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._validate(delta)
        if self.is_identity(value) or after.component(WATCH_NPC, value.entity_id).bells != value.after_bells:
            raise CandidateError("INVALID_DELTA", "watch net mismatch")


class BellsPatchRoute:
    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.bells-patch", 1)

    @property
    def component_schema(self) -> TypeKey:
        return WATCH_NPC.schema

    @property
    def family(self) -> FieldFamily:
        return FieldFamily("watch.npc", "bells")

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        WatchNpcAdapter().validate(before)
        WatchPayloadCodec(self.schema).encode(patch)
        assert isinstance(before, WatchNpcRecord) and isinstance(patch, BellsPatch)
        return replace(before, bells=patch.bells)


class ReplyReducer:
    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.reply-delta", 1)

    @property
    def owner_id(self) -> str:
        return "watch.echo"

    def _validate(self, delta: StateDelta) -> ReplyDelta:
        if type(delta) is not ReplyDelta:
            raise CandidateError("INVALID_DELTA", "watch delta class")
        try:
            WatchPayloadCodec(self.schema).encode(delta)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "watch delta payload") from error
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._validate(delta)
        if not 1 <= value.after_count - value.before_count <= 512:
            raise CandidateError("INVALID_DELTA", "watch delta step")
        if before.component(REPLY, value.entity_id).count != value.before_count:
            raise CandidateError("INVALID_DELTA", "watch old value")
        editor.apply_patch(ComponentAddress(REPLY.schema, value.entity_id), ReplyPatch(value.after_count))

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "empty watch composition")
        values = tuple(self._validate(d) for d in changes)
        for first, second in zip(values, values[1:]):
            if first.target != second.target or first.after_count != second.before_count:
                raise CandidateError("INVALID_DELTA", "noncontiguous watch composition")
        return replace(values[0], after_count=values[-1].after_count)

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._validate(delta)
        return value.before_count == value.after_count

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._validate(delta)
        if self.is_identity(value) or after.component(REPLY, value.entity_id).count != value.after_count:
            raise CandidateError("INVALID_DELTA", "watch net mismatch")


class ReplyPatchRoute:
    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.reply-patch", 1)

    @property
    def component_schema(self) -> TypeKey:
        return REPLY.schema

    @property
    def family(self) -> FieldFamily:
        return FieldFamily("watch.reply", "count")

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        ReplyAdapter().validate(before)
        WatchPayloadCodec(self.schema).encode(patch)
        assert isinstance(before, ReplyRecord) and isinstance(patch, ReplyPatch)
        return replace(before, count=patch.count)


class WatchAdmission:
    def __init__(self, schema: TypeKey) -> None:
        if schema not in (TypeKey("watch.wait", 1), TypeKey("watch.bell", 1)):
            raise SchemaError("UNSUPPORTED_SCHEMA", "watch admission")
        self._schema = schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    @property
    def reads(self) -> tuple[FieldFamily, ...]:
        fields = [("encounter.hp", "hp")]
        if self.schema.kind == "watch.bell":
            fields += [("watch.npc", "cell"), ("watch.npc", "space_id"), ("trial.position", "space_id")]
        return tuple(FieldFamily(k, f) for k, f in fields)

    def admit(self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str) -> AdmissionOutcome:
        if command.actor_id != ACTOR_ID:
            return TurnRejected(failure("UNAUTHORIZED_ACTOR"), command.expected_revision)
        body = WatchPayloadCodec(self.schema).encode(command.payload)
        if state.component(HIT_POINTS, ACTOR_ID).hp == 0:
            return TurnRejected(failure("ACTOR_DEFEATED"), command.expected_revision)
        payload = command.payload
        if type(payload) is BellCommand:
            npc = state.component(WATCH_NPC, NPC_ID)
            if npc.cell != NPC_CELL or npc.space_id != SPACE_ID or state.component(CELL_POSITION, ACTOR_ID).space_id != SPACE_ID:
                raise CandidateError("INVALID_ACTION", "watch references")
            if payload.npc_id != NPC_ID:
                return TurnRejected(failure("INVALID_TARGET"), command.expected_revision)
            duration = 1
        elif type(payload) is WaitCommand:
            duration = payload.seconds
        else:
            raise CandidateError("INVALID_ACTION", "watch admission payload")
        target = Tick(start_tick + duration)
        if target > MAX_INT:
            raise CandidateError("INTEGER_OVERFLOW", "watch target")
        payload_hash = hash_document("payload/v1", {"schema": key_document(payload.schema), "payload": body})
        key = "a1-" + hashlib.sha256(pack(("action-key/v1", world_id, str(target), command.actor_id, payload_hash))).hexdigest()
        return AdmittedCommand(TurnPlan(command, start_tick, target), AdmittedAction(command.actor_id, payload, key))


class WatchCheckpointPolicy:
    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        if len(core.components) != 10:
            raise ValueError("exact ten watch records required")
        EncounterCheckpointPolicy().validate(replace(core, components=core.components[:7], pending=()), protocol)
        lantern, npc, reply = core.components[7:]
        LanternAdapter().validate(lantern)
        WatchNpcAdapter().validate(npc)
        ReplyAdapter().validate(reply)
        assert isinstance(lantern, LanternRecord) and isinstance(npc, WatchNpcRecord) and isinstance(reply, ReplyRecord)
        if lantern.entity_id != LANTERN_ID or npc.entity_id != NPC_ID or reply.entity_id != NPC_ID or npc.space_id != SPACE_ID or npc.cell != NPC_CELL:
            raise ValueError("watch identities/references")
        if npc.bells != core.tick // 2 or lantern.charge != min(3, core.tick) or len(core.pending) != 1:
            raise ValueError("watch clock/count/queue invariants")
        q = exact_fields(decode_json(core.pending[0].canonical_event_json), ("event", "delivery_phase", "priority"))
        e = exact_fields(q["event"], ("header", "due_tick", "payload"))
        h = exact_fields(e["header"], ("event_id", "type_key", "producer_id", "occurred_at", "phase", "wave", "producer_rank", "sequence", "caused_by", "degraded"))
        if q["delivery_phase"] != "PRE_TICK" or q["priority"] != 10 or e["due_tick"] != next_wake(core.tick) or object_value(e["payload"]) != {"npc_id": NPC_ID} or object_value(h["type_key"]) != {"kind": "watch.wake", "version": 1}:
            raise ValueError("watch wake routing")
        previous = core.tick // 2 * 2
        if h["occurred_at"] != previous or h["sequence"] != (1 if previous else 0) or h["producer_id"] != "watch.npc" or h["phase"] != "PRE_TICK" or h["wave"] != 0 or h["producer_rank"] != 0 or h["degraded"] != ():
            raise ValueError("watch wake provenance")
        from domain.canonical import array_value
        if len(array_value(h["caused_by"])) != (1 if previous else 0):
            raise ValueError("watch wake cause count")


class WatchPresenter:
    def map(self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt, committed: ReadPort) -> tuple[PresentationEvent, ...]:
        if not facts:
            return ()
        npc = committed.component(WATCH_NPC, NPC_ID)
        cell, space, bells = npc.cell, npc.space_id, npc.bells
        charge = committed.component(LANTERN, LANTERN_ID).charge
        replies = committed.component(REPLY, NPC_ID).count
        if cell != NPC_CELL or space != SPACE_ID or charge != min(3, receipt.tick):
            raise ValueError("watch presentation references")
        last_bells: int | None = None
        last_reply: int | None = None
        last_tick = -1
        cues: list[PresentationEvent] = []
        for event in facts:
            fact = event.payload
            WatchPayloadCodec(fact.schema).encode(fact)
            tick = event.header.occurred_at
            if not 1 <= tick <= receipt.tick or tick < last_tick or event.due_tick != tick:
                raise ValueError("watch source timing/order")
            last_tick = tick
            payload: PresentationPayload
            if type(fact) is NpcActed:
                if tick % 2 or fact.after_bells != tick // 2 or last_bells is not None and fact.before_bells != last_bells:
                    raise ValueError("watch bell history")
                last_bells = fact.after_bells
                payload = NpcCue(NPC_ID, tick, fact.before_bells, fact.after_bells, cell, 0, 2000)
            elif type(fact) is BellRung:
                payload = BellCue(ACTOR_ID, NPC_ID, tick)
            elif type(fact) is WatchReplied:
                if last_reply is not None and fact.before_count != last_reply:
                    raise ValueError("watch reply history")
                last_reply = fact.after_count
                payload = ReplyCue(NPC_ID, tick, fact.before_count, fact.after_count)
            else:
                raise ValueError("watch presenter fact kind")
            index = len(cues)
            source = event.header.event_id
            identifier = "p1-" + hashlib.sha256(pack(("cue-id/v1", source, "watch.presenter", str(index)))).hexdigest()
            cues.append(PresentationEvent(EventHeader(EventId(identifier), payload.schema, "watch.presenter", receipt.tick, Phase.PRESENT, 0, 0, index, (source,), ()), payload, "important", "keep_all", ""))
        if last_bells is not None and last_bells != bells or last_reply is not None and last_reply != replies:
            raise ValueError("watch presentation endpoint")
        return tuple(cues)
