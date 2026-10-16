"""Strict registered read,codec,staging and checkpoint memory boundaries."""

from __future__ import annotations

from dataclasses import asdict, replace
from typing import cast

from contracts.dialogue import QuestBound, QuestContent
from contracts.messages import StateDelta
from contracts.errors import CandidateError, ReadOnlyViolation
from contracts.npc_memory import (
    MEMORY,
    MEMORY_FAMILY,
    MemoryDelta,
    MemoryPatch,
    NpcMemoryRead,
    read_record,
)
from contracts.read_views import (
    AttributePath,
    ComponentKey,
    ComponentPatch,
    ReadPort,
    StagingEditor,
    ViewAccess,
)
from contracts.turn import ProtocolSnapshot
from domain.canonical import (
    JsonObject,
    array_value,
    exact_fields,
    int_value,
    object_value,
    seal,
    text_value,
)
from domain.npc_memory import (
    MEMORY_CAPACITY,
    EvidenceKind,
    NpcQuestMemoryRecord,
    QuestEvidence,
    source_identity,
)
from domain.primitives import (
    ComponentAddress,
    EntityId,
    FieldAddress,
    FieldFamily,
    FrozenPayload,
    TypeKey,
)
from domain.quest import QuestRecord
from domain.state_types import ComponentRecord, CoreSnapshot
from orchestration.quest import QuestCheckpointPolicy


class _MemoryView:
    __slots__ = ("_record", "_access")

    def __init__(self, record: NpcQuestMemoryRecord, access: ViewAccess) -> None:
        object.__setattr__(self, "_record", record)
        object.__setattr__(self, "_access", access)

    _record: NpcQuestMemoryRecord
    _access: ViewAccess

    def __setattr__(self, name: str, value: object) -> None:
        self._access.observe(FieldAddress(MEMORY_FAMILY, self._record.entity_id), (), "write")
        raise ReadOnlyViolation(name)

    def __delattr__(self, name: str) -> None:
        self.__setattr__(name, None)

    def _entry(self, index: int, name: str) -> QuestEvidence | None:
        self._access.observe(
            FieldAddress(MEMORY_FAMILY, self._record.entity_id), (AttributePath(name),), "read"
        )
        return self._record.entries[index] if len(self._record.entries) > index else None

    @property
    def accepted_at(self) -> int:
        entry = self._entry(0, "accepted_at")
        return 0 if entry is None else entry.observed_at

    @property
    def acceptance_source(self) -> str:
        entry = self._entry(0, "acceptance_source")
        return "" if entry is None else entry.source_event_id

    @property
    def reported_at(self) -> int:
        entry = self._entry(1, "reported_at")
        return 0 if entry is None else entry.observed_at

    @property
    def report_source(self) -> str:
        entry = self._entry(1, "report_source")
        return "" if entry is None else entry.source_event_id


class MemoryAdapter(QuestBound):
    @property
    def key(self) -> ComponentKey[NpcMemoryRead]:
        return MEMORY

    def validate(self, record: ComponentRecord) -> None:
        if (
            type(record) is not NpcQuestMemoryRecord
            or record.entity_id != self.quest_content.definition.layout.npc_id
        ):
            raise ValueError("NPC_MEMORY_OWNER")
        # Revalidate immutable shape even for an object fabricated outside its constructor.
        if NpcQuestMemoryRecord(record.entity_id, record.entries) != record:
            raise ValueError("NPC_MEMORY_ENTRIES")
        for entry in record.entries:
            QuestEvidence(entry.kind, entry.observed_at, entry.source_event_id)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> NpcMemoryRead:
        self.validate(record)
        return _MemoryView(cast(NpcQuestMemoryRecord, record), access)


class MemoryCodec(QuestBound):
    @property
    def schema(self) -> TypeKey:
        return MEMORY.schema

    def encode(self, record: ComponentRecord) -> JsonObject:
        MemoryAdapter(self.quest_content).validate(record)
        return object_value(
            seal(
                {
                    "entries": tuple(
                        asdict(entry) for entry in cast(NpcQuestMemoryRecord, record).entries
                    )
                }
            )
        )

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        row = exact_fields(fields, ("entries",))
        entries = []
        values = array_value(row["entries"])
        if len(values) > MEMORY_CAPACITY:
            raise ValueError("NPC_MEMORY_ENTRIES")
        for value in values:
            data = exact_fields(value, ("kind", "observed_at", "source_event_id"))
            kind = text_value(data["kind"])
            if kind not in ("accepted", "completion_reported"):
                raise ValueError("NPC_MEMORY_KIND")
            entries.append(
                QuestEvidence(
                    cast(EvidenceKind, kind),
                    int_value(data["observed_at"]),
                    text_value(data["source_event_id"]),
                )
            )
        record = NpcQuestMemoryRecord(entity_id, tuple(entries))
        MemoryAdapter(self.quest_content).validate(record)
        return record


class MemoryPayloadCodec(QuestBound):
    def __init__(self, schema: TypeKey, content: QuestContent) -> None:
        if type(content) is not QuestContent:
            raise ValueError("QUEST_CONTENT")
        super().__init__(content)
        if schema not in (MemoryDelta.SCHEMA, MemoryPatch.SCHEMA):
            raise ValueError("NPC_MEMORY_SCHEMA")
        self._schema = schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    def _encode(self, record: NpcQuestMemoryRecord) -> JsonObject:
        return {"entity_id": record.entity_id, **MemoryCodec(self.quest_content).encode(record)}

    def _decode(self, document: object) -> NpcQuestMemoryRecord:
        # Boundary documents are canonical JSON objects;validate all fields before construction.
        row = exact_fields(seal(document), ("entity_id", "entries"))
        return cast(
            NpcQuestMemoryRecord,
            MemoryCodec(self.quest_content).decode(
                EntityId(text_value(row["entity_id"])), {"entries": row["entries"]}
            ),
        )

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if type(payload) is MemoryDelta and self.schema == MemoryDelta.SCHEMA:
            body: JsonObject = {
                "before": self._encode(payload.before),
                "after": self._encode(payload.after),
            }
        elif type(payload) is MemoryPatch and self.schema == MemoryPatch.SCHEMA:
            body = {"value": self._encode(payload.value)}
        else:
            raise ValueError("NPC_MEMORY_PAYLOAD")
        self.decode(body)
        return body

    def decode(self, data: JsonObject) -> FrozenPayload:
        if self.schema == MemoryPatch.SCHEMA:
            row = exact_fields(data, ("value",))
            return MemoryPatch(self._decode(row["value"]))
        row = exact_fields(data, ("before", "after"))
        before, after = self._decode(row["before"]), self._decode(row["after"])
        validate_append(before, after)
        return MemoryDelta(before, after)


def validate_append(before: NpcQuestMemoryRecord, after: NpcQuestMemoryRecord) -> None:
    if (
        before.entity_id != after.entity_id
        or not len(before.entries) < len(after.entries) <= MEMORY_CAPACITY
        or after.entries[: len(before.entries)] != before.entries
    ):
        raise ValueError("NPC_MEMORY_APPEND")


class MemoryReducer(QuestBound):
    @property
    def schema(self) -> TypeKey:
        return MemoryDelta.SCHEMA

    @property
    def owner_id(self) -> str:
        return "quest.memory"

    def _value(self, delta: object) -> MemoryDelta:
        if type(delta) is not MemoryDelta:
            raise CandidateError("INVALID_DELTA", "memory type")
        try:
            MemoryPayloadCodec(self.schema, self.quest_content).encode(delta)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "memory append") from error
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._value(delta)
        if (
            len(value.after.entries) != len(value.before.entries) + 1
            or read_record(value.before.entity_id, before.component(MEMORY, value.before.entity_id))
            != value.before
        ):
            raise CandidateError("INVALID_DELTA", "memory endpoint")
        editor.apply_patch(
            ComponentAddress(MEMORY.schema, value.before.entity_id), MemoryPatch(value.after)
        )

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "memory empty composition")
        values = tuple(self._value(change) for change in changes)
        if any(len(value.after.entries) != len(value.before.entries) + 1 for value in values):
            raise CandidateError("INVALID_DELTA", "memory composition step")
        if any(first.after != second.before for first, second in zip(values, values[1:])):
            raise CandidateError("INVALID_DELTA", "memory discontinuity")
        return self._value(MemoryDelta(values[0].before, values[-1].after))

    def is_identity(self, delta: StateDelta) -> bool:
        self._value(delta)
        return False

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._value(delta)
        if (
            read_record(value.after.entity_id, after.component(MEMORY, value.after.entity_id))
            != value.after
        ):
            raise CandidateError("INVALID_DELTA", "memory net endpoint")


class MemoryPatchRoute(QuestBound):
    @property
    def schema(self) -> TypeKey:
        return MemoryPatch.SCHEMA

    @property
    def component_schema(self) -> TypeKey:
        return MEMORY.schema

    @property
    def family(self) -> FieldFamily:
        return MEMORY_FAMILY

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        MemoryAdapter(self.quest_content).validate(before)
        if type(patch) is not MemoryPatch:
            raise ValueError("NPC_MEMORY_PATCH")
        MemoryAdapter(self.quest_content).validate(patch.value)
        validate_append(cast(NpcQuestMemoryRecord, before), patch.value)
        return patch.value


class MemoryCheckpointPolicy(QuestBound):
    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        matches = tuple(record for record in core.components if record.schema == MEMORY.schema)
        if len(matches) != 1:
            raise ValueError("NPC_MEMORY_CHECKPOINT")
        record = matches[0]
        MemoryAdapter(self.quest_content).validate(record)
        memory = cast(NpcQuestMemoryRecord, record)
        remaining = tuple(item for item in core.components if item is not record)
        QuestCheckpointPolicy(self.quest_content).validate(
            replace(core, components=remaining), protocol
        )
        quest = next(item for item in remaining if type(item) is QuestRecord)
        expected = 0 if quest.stage == 0 else 2 if quest.stage == 3 else 1
        if len(memory.entries) != expected or any(
            entry.observed_at > core.tick
            or entry.source_event_id != source_identity(core.world_id, entry.observed_at)
            for entry in memory.entries
        ):
            raise ValueError("NPC_MEMORY_CHECKPOINT")
