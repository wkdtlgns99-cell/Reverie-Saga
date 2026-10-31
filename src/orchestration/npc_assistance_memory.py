"""Strict codecs, observed reads and same-owner transactional memory updates."""

from dataclasses import replace
from typing import cast

from contracts.dialogue import QuestBound, QuestContent
from contracts.errors import CandidateError, ReadOnlyViolation
from contracts.messages import StateDelta
from contracts.npc_assistance_memory import (
    ASSISTANCE_FAMILY,
    ASSISTANCE_MEMORY,
    ASSISTANCE_OWNER,
    ASSISTANCE_PAYLOADS,
    AssistanceMemoryDelta,
    AssistanceMemoryPatch,
    AssistanceMemoryRead,
)
from contracts.read_views import ComponentKey, ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.state_io import CheckpointPolicy
from contracts.turn import ProtocolSnapshot
from domain.canonical import (
    JsonObject,
    array_value,
    exact_fields,
    int_value,
    object_value,
    text_value,
)
from domain.npc_assistance_memory import (
    AssistanceEntry,
    AssistanceMemory,
    AssistanceMemoryRecord,
    AssistanceSource,
    validate_checkpoint,
    validate_transition,
)
from domain.npc_memory import NpcQuestMemoryRecord
from domain.primitives import (
    ComponentAddress,
    EntityId,
    FieldAddress,
    FieldFamily,
    FrozenPayload,
    TypeKey,
)
from domain.state_types import ComponentRecord, CoreSnapshot


def encode_state(state: AssistanceMemory) -> JsonObject:
    if type(state) is not AssistanceMemory:
        raise ValueError("NPC_ASSISTANCE_MEMORY_INPUT")
    AssistanceMemory(state.total_assists, state.entries)
    return {
        "total_assists": state.total_assists,
        "entries": tuple(
            {
                "tick": entry.tick,
                "target_id": entry.target_id,
                "source_kind": entry.source_kind,
                "cause_event_id": entry.cause_event_id,
            }
            for entry in state.entries
        ),
    }


def decode_state(data: JsonObject) -> AssistanceMemory:
    row = exact_fields(data, ("total_assists", "entries"))
    entries = []
    for raw in array_value(row["entries"]):
        item = exact_fields(raw, ("tick", "target_id", "source_kind", "cause_event_id"))
        kind = text_value(item["source_kind"])
        if kind not in ("wake", "answered_call"):
            raise ValueError("NPC_ASSISTANCE_MEMORY_SOURCE")
        entries.append(
            AssistanceEntry(
                int_value(item["tick"]),
                EntityId(text_value(item["target_id"])),
                cast(AssistanceSource, kind),
                text_value(item["cause_event_id"]),
            )
        )
    return AssistanceMemory(int_value(row["total_assists"]), tuple(entries))


class _AssistanceView:
    __slots__ = ("_record", "_access")
    _record: AssistanceMemoryRecord
    _access: ViewAccess

    def __init__(self, record: AssistanceMemoryRecord, access: ViewAccess) -> None:
        object.__setattr__(self, "_record", record)
        object.__setattr__(self, "_access", access)

    @property
    def state(self) -> AssistanceMemory:
        self._access.observe(FieldAddress(ASSISTANCE_FAMILY, self._record.entity_id), (), "read")
        return self._record.state

    def __setattr__(self, name: str, value: object) -> None:
        self._access.observe(FieldAddress(ASSISTANCE_FAMILY, self._record.entity_id), (), "write")
        raise ReadOnlyViolation(name)

    def __delattr__(self, name: str) -> None:
        self.__setattr__(name, None)


class AssistanceAdapter(QuestBound):
    @property
    def key(self) -> ComponentKey[AssistanceMemoryRead]:
        return ASSISTANCE_MEMORY

    def validate(self, record: ComponentRecord) -> None:
        if type(record) is not AssistanceMemoryRecord:
            raise ValueError("NPC_ASSISTANCE_MEMORY_INPUT")
        AssistanceMemoryRecord(record.entity_id, record.state)
        layout = self.quest_content.definition.layout
        if record.entity_id != layout.npc_id or any(
            entry.target_id != layout.gate_id for entry in record.state.entries
        ):
            raise ValueError("NPC_ASSISTANCE_MEMORY_OWNER")

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> AssistanceMemoryRead:
        self.validate(record)
        return _AssistanceView(cast(AssistanceMemoryRecord, record), access)


class AssistanceCodec(QuestBound):
    @property
    def schema(self) -> TypeKey:
        return ASSISTANCE_MEMORY.schema

    def encode(self, record: ComponentRecord) -> JsonObject:
        AssistanceAdapter(self.quest_content).validate(record)
        return {"memory": encode_state(cast(AssistanceMemoryRecord, record).state)}

    def decode(self, entity_id: EntityId, fields: JsonObject) -> AssistanceMemoryRecord:
        outer = exact_fields(fields, ("memory",))
        record = AssistanceMemoryRecord(entity_id, decode_state(object_value(outer["memory"])))
        AssistanceAdapter(self.quest_content).validate(record)
        return record


class AssistancePayloadCodec(QuestBound):
    def __init__(self, schema: TypeKey, content: QuestContent) -> None:
        super().__init__(content)
        if schema not in tuple(kind.SCHEMA for kind in ASSISTANCE_PAYLOADS):
            raise ValueError("NPC_ASSISTANCE_MEMORY_INPUT")
        self._schema = schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    def _validate(self, owner: EntityId, state: AssistanceMemory) -> None:
        AssistanceAdapter(self.quest_content).validate(AssistanceMemoryRecord(owner, state))

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if type(payload) is AssistanceMemoryDelta and self.schema == payload.schema:
            self._validate(payload.entity_id, payload.before)
            self._validate(payload.entity_id, payload.after)
            validate_transition(payload.before, payload.after)
            data: JsonObject = {
                "entity_id": payload.entity_id,
                "before": encode_state(payload.before),
                "after": encode_state(payload.after),
            }
        elif type(payload) is AssistanceMemoryPatch and self.schema == payload.schema:
            self._validate(self.quest_content.definition.layout.npc_id, payload.state)
            data = {"state": encode_state(payload.state)}
        else:
            raise ValueError("NPC_ASSISTANCE_MEMORY_INPUT")
        self.decode(data)
        return data

    def decode(self, data: JsonObject) -> FrozenPayload:
        if self.schema == AssistanceMemoryDelta.SCHEMA:
            row = exact_fields(data, ("entity_id", "before", "after"))
            owner = EntityId(text_value(row["entity_id"]))
            before, after = (
                decode_state(object_value(row["before"])),
                decode_state(object_value(row["after"])),
            )
            self._validate(owner, before)
            self._validate(owner, after)
            validate_transition(before, after)
            return AssistanceMemoryDelta(owner, before, after)
        row = exact_fields(data, ("state",))
        state = decode_state(object_value(row["state"]))
        self._validate(self.quest_content.definition.layout.npc_id, state)
        return AssistanceMemoryPatch(state)


class AssistanceReducer(QuestBound):
    @property
    def schema(self) -> TypeKey:
        return AssistanceMemoryDelta.SCHEMA

    @property
    def owner_id(self) -> str:
        return ASSISTANCE_OWNER

    def _value(self, delta: object) -> AssistanceMemoryDelta:
        if type(delta) is not AssistanceMemoryDelta:
            raise CandidateError("INVALID_DELTA", "assistance memory type")
        try:
            AssistancePayloadCodec(self.schema, self.quest_content).encode(delta)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "assistance memory transition") from error
        return delta

    def _read(self, state: ReadPort) -> AssistanceMemory:
        return state.component(ASSISTANCE_MEMORY, self.quest_content.definition.layout.npc_id).state

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._value(delta)
        try:
            validate_transition(value.before, value.after, single=True)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "assistance memory staged append") from error
        if self._read(before) != value.before:
            raise CandidateError("INVALID_DELTA", "assistance memory endpoint")
        editor.apply_patch(
            ComponentAddress(ASSISTANCE_MEMORY.schema, value.entity_id),
            AssistanceMemoryPatch(value.after),
        )

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "assistance memory empty composition")
        values = tuple(self._value(change) for change in changes)
        if any(
            a.after != b.before or a.entity_id != b.entity_id for a, b in zip(values, values[1:])
        ):
            raise CandidateError("INVALID_DELTA", "assistance memory discontinuity")
        return self._value(
            AssistanceMemoryDelta(values[0].entity_id, values[0].before, values[-1].after)
        )

    def is_identity(self, delta: StateDelta) -> bool:
        self._value(delta)
        return False

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._value(delta)
        if self._read(after) != value.after:
            raise CandidateError("INVALID_DELTA", "assistance memory net endpoint")


class AssistancePatchRoute(QuestBound):
    @property
    def schema(self) -> TypeKey:
        return AssistanceMemoryPatch.SCHEMA

    @property
    def component_schema(self) -> TypeKey:
        return ASSISTANCE_MEMORY.schema

    @property
    def family(self) -> FieldFamily:
        return ASSISTANCE_FAMILY

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        adapter = AssistanceAdapter(self.quest_content)
        adapter.validate(before)
        if type(patch) is not AssistanceMemoryPatch:
            raise ValueError("NPC_ASSISTANCE_MEMORY_INPUT")
        record = cast(AssistanceMemoryRecord, before)
        after = AssistanceMemoryRecord(record.entity_id, patch.state)
        adapter.validate(after)
        validate_transition(record.state, after.state, single=True)
        return after


class AssistanceCheckpointPolicy(QuestBound):
    def __init__(self, content: QuestContent, base: CheckpointPolicy) -> None:
        super().__init__(content)
        self._base = base

    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        matches = tuple(r for r in core.components if r.schema == ASSISTANCE_MEMORY.schema)
        self._base.validate(
            replace(
                core,
                components=tuple(
                    r for r in core.components if r.schema != ASSISTANCE_MEMORY.schema
                ),
            ),
            protocol,
        )
        if len(matches) != 1:
            raise ValueError("NPC_ASSISTANCE_MEMORY_INPUT")
        AssistanceAdapter(self.quest_content).validate(matches[0])
        memories = tuple(r for r in core.components if type(r) is NpcQuestMemoryRecord)
        if len(memories) != 1:
            raise ValueError("NPC_ASSISTANCE_MEMORY_SOURCE")
        known = memories[0].entries
        validate_checkpoint(
            cast(AssistanceMemoryRecord, matches[0]),
            core.world_id,
            core.tick,
            accepted_at=known[0].observed_at if known else None,
            reported_at=known[1].observed_at if len(known) == 2 else None,
        )
