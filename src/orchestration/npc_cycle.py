"""Strict cycle serialization, observed reads and transactional ownership."""

from dataclasses import replace
import hashlib
from typing import cast

from domain.npc_patrol import patrol_cells

from contracts.dialogue import QuestBound, QuestContent
from contracts.errors import CandidateError, ReadOnlyViolation
from contracts.messages import EventHeader, PresentationEvent, StateDelta, WorldEvent
from contracts.npc_cycle import (
    CYCLE,
    CYCLE_FAMILY,
    CYCLE_PAYLOADS,
    CycleChanged,
    CycleCue,
    CycleDelta,
    CyclePatch,
    CycleRead,
)
from contracts.read_views import ComponentKey, ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.turn import CommitReceipt, ProtocolSnapshot
from domain.canonical import (
    JsonObject,
    array_value,
    exact_fields,
    int_value,
    object_value,
    pack,
    text_value,
)
from domain.npc_cycle import (
    CycleRecord,
    Supply,
    SupplyEvidence,
    validate_chain,
    validate_checkpoint,
    actions_at,
    state_at,
)
from domain.primitives import (
    ComponentAddress,
    EntityId,
    EventId,
    FieldAddress,
    FieldFamily,
    FrozenPayload,
    Phase,
    TypeKey,
)
from domain.state_types import ComponentRecord, CoreSnapshot
from orchestration.npc_memory import MemoryCheckpointPolicy


def encode_supply(value: Supply) -> JsonObject:
    return {"stock": value.stock, "produced": value.produced, "consumed": value.consumed}


def decode_supply(raw: JsonObject) -> Supply:
    row = exact_fields(raw, ("stock", "produced", "consumed"))
    return Supply(int_value(row["stock"]), int_value(row["produced"]), int_value(row["consumed"]))


def encode_evidence(value: SupplyEvidence) -> JsonObject:
    return {
        "tick": value.tick,
        "sequence": value.sequence,
        "source_event_id": value.source_event_id,
        "before": encode_supply(value.before),
        "after": encode_supply(value.after),
    }


def decode_evidence(raw: JsonObject) -> SupplyEvidence:
    row = exact_fields(raw, ("tick", "sequence", "source_event_id", "before", "after"))
    entry = SupplyEvidence(
        int_value(row["tick"]),
        int_value(row["sequence"]),
        text_value(row["source_event_id"]),
        decode_supply(object_value(row["before"])),
        decode_supply(object_value(row["after"])),
    )
    before = state_at(entry.tick - 1)
    actions = actions_at(entry.tick, before)
    if (
        entry.sequence >= len(actions)
        or entry.after != actions[entry.sequence]
        or (entry.before != (before if entry.sequence == 0 else actions[entry.sequence - 1]))
    ):
        raise ValueError("NPC_CYCLE_SOURCE")
    return entry


class _CycleView:
    __slots__ = ("_record", "_access")
    _record: CycleRecord
    _access: ViewAccess

    def __init__(self, record: CycleRecord, access: ViewAccess) -> None:
        object.__setattr__(self, "_record", record)
        object.__setattr__(self, "_access", access)

    @property
    def state(self) -> Supply:
        self._access.observe(FieldAddress(CYCLE_FAMILY, self._record.entity_id), (), "read")
        return self._record.state

    @property
    def entries(self) -> tuple[SupplyEvidence, ...]:
        self._access.observe(FieldAddress(CYCLE_FAMILY, self._record.entity_id), (), "read")
        return self._record.entries

    def __setattr__(self, name: str, value: object) -> None:
        self._access.observe(FieldAddress(CYCLE_FAMILY, self._record.entity_id), (), "write")
        raise ReadOnlyViolation(name)

    def __delattr__(self, name: str) -> None:
        self.__setattr__(name, None)


class CycleAdapter(QuestBound):
    @property
    def key(self) -> ComponentKey[CycleRead]:
        return CYCLE

    def validate(self, record: ComponentRecord) -> None:
        if (
            type(record) is not CycleRecord
            or record.entity_id != self.quest_content.definition.layout.npc_id
        ):
            raise ValueError("NPC_CYCLE_OWNER")
        CycleRecord(record.entity_id, record.state, record.entries)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> CycleRead:
        self.validate(record)
        return _CycleView(cast(CycleRecord, record), access)


class CycleCodec(QuestBound):
    @property
    def schema(self) -> TypeKey:
        return CYCLE.schema

    def encode(self, record: ComponentRecord) -> JsonObject:
        CycleAdapter(self.quest_content).validate(record)
        value = cast(CycleRecord, record)
        return {
            "cycle": {
                "state": encode_supply(value.state),
                "entries": tuple(encode_evidence(e) for e in value.entries),
            }
        }

    def decode(self, entity_id: EntityId, fields: JsonObject) -> CycleRecord:
        outer = exact_fields(fields, ("cycle",))
        row = exact_fields(object_value(outer["cycle"]), ("state", "entries"))
        record = CycleRecord(
            entity_id,
            decode_supply(object_value(row["state"])),
            tuple(decode_evidence(object_value(e)) for e in array_value(row["entries"])),
        )
        CycleAdapter(self.quest_content).validate(record)
        return record


class CyclePayloadCodec(QuestBound):
    def __init__(self, schema: TypeKey, content: QuestContent) -> None:
        super().__init__(content)
        if schema not in tuple(k.SCHEMA for k in CYCLE_PAYLOADS):
            raise ValueError("NPC_CYCLE_SCHEMA")
        self._schema = schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    def _record(self, raw: JsonObject) -> CycleRecord:
        row = exact_fields(raw, ("entity_id", "cycle"))
        return CycleCodec(self.quest_content).decode(
            EntityId(text_value(row["entity_id"])), {"cycle": row["cycle"]}
        )

    def _encode_record(self, value: CycleRecord) -> JsonObject:
        return {"entity_id": value.entity_id, **CycleCodec(self.quest_content).encode(value)}

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if type(payload) is CycleDelta and self.schema == CycleDelta.SCHEMA:
            data: JsonObject = {
                "before": self._encode_record(payload.before),
                "after": self._encode_record(payload.after),
            }
        elif type(payload) is CyclePatch and self.schema == CyclePatch.SCHEMA:
            data = {"value": self._encode_record(payload.value)}
        elif type(payload) is CycleChanged and self.schema == CycleChanged.SCHEMA:
            data = {"npc_id": payload.npc_id, "evidence": encode_evidence(payload.evidence)}
        elif type(payload) is CycleCue and self.schema == CycleCue.SCHEMA:
            data = {"npc_id": payload.npc_id, "evidence": encode_evidence(payload.evidence)}
        else:
            raise ValueError("NPC_CYCLE_PAYLOAD")
        self.decode(data)
        return data

    def decode(self, data: JsonObject) -> FrozenPayload:
        if self.schema == CycleDelta.SCHEMA:
            row = exact_fields(data, ("before", "after"))
            before, after = (
                self._record(object_value(row["before"])),
                self._record(object_value(row["after"])),
            )
            validate_chain(before, after, staged=False)
            return CycleDelta(before, after)
        if self.schema == CyclePatch.SCHEMA:
            row = exact_fields(data, ("value",))
            return CyclePatch(self._record(object_value(row["value"])))
        row = exact_fields(data, ("npc_id", "evidence"))
        owner = EntityId(text_value(row["npc_id"]))
        if owner != self.quest_content.definition.layout.npc_id:
            raise ValueError("NPC_CYCLE_OWNER")
        entry = decode_evidence(object_value(row["evidence"]))
        return (
            CycleChanged(owner, entry)
            if self.schema == CycleChanged.SCHEMA
            else CycleCue(owner, entry)
        )


class CycleReducer(QuestBound):
    @property
    def schema(self) -> TypeKey:
        return CycleDelta.SCHEMA

    @property
    def owner_id(self) -> str:
        return "quest.cycle"

    def _value(self, delta: object) -> CycleDelta:
        if type(delta) is not CycleDelta:
            raise CandidateError("INVALID_DELTA", "cycle type")
        try:
            CyclePayloadCodec(self.schema, self.quest_content).encode(delta)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "cycle transition") from error
        return delta

    def _read(self, state: ReadPort) -> CycleRecord:
        owner = self.quest_content.definition.layout.npc_id
        view = state.component(CYCLE, owner)
        return CycleRecord(owner, view.state, view.entries)

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._value(delta)
        try:
            validate_chain(value.before, value.after, staged=True)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "cycle staged chain") from error
        if self._read(before) != value.before:
            raise CandidateError("INVALID_DELTA", "cycle endpoint")
        editor.apply_patch(
            ComponentAddress(CYCLE.schema, value.before.entity_id), CyclePatch(value.after)
        )

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "cycle empty composition")
        values = tuple(self._value(change) for change in changes)
        try:
            for value in values:
                validate_chain(value.before, value.after, staged=True)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "cycle staged chain") from error
        if any(a.after != b.before for a, b in zip(values, values[1:])):
            raise CandidateError("INVALID_DELTA", "cycle discontinuity")
        return self._value(CycleDelta(values[0].before, values[-1].after))

    def is_identity(self, delta: StateDelta) -> bool:
        self._value(delta)
        return False

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._value(delta)
        if self._read(after) != value.after:
            raise CandidateError("INVALID_DELTA", "cycle net endpoint")


class CyclePatchRoute(QuestBound):
    @property
    def schema(self) -> TypeKey:
        return CyclePatch.SCHEMA

    @property
    def component_schema(self) -> TypeKey:
        return CYCLE.schema

    @property
    def family(self) -> FieldFamily:
        return CYCLE_FAMILY

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        CycleAdapter(self.quest_content).validate(before)
        if type(patch) is not CyclePatch:
            raise ValueError("NPC_CYCLE_PATCH")
        CycleAdapter(self.quest_content).validate(patch.value)
        validate_chain(cast(CycleRecord, before), patch.value, staged=True)
        return patch.value


class CycleCheckpointPolicy(QuestBound):
    def __init__(self, content: QuestContent, *, npc_patrol: bool = False) -> None:
        super().__init__(content)
        self._npc_cells = patrol_cells(content.definition.layout, npc_patrol)
        self._npc_patrol = npc_patrol

    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        matches = tuple(r for r in core.components if r.schema == CYCLE.schema)
        if len(matches) != 1:
            raise ValueError("NPC_CYCLE_CHECKPOINT")
        record = matches[0]
        CycleAdapter(self.quest_content).validate(record)
        validate_checkpoint(cast(CycleRecord, record), core.world_id, core.tick)
        MemoryCheckpointPolicy(self.quest_content, npc_patrol=self._npc_patrol).validate(
            replace(core, components=tuple(r for r in core.components if r is not record)), protocol
        )


class CyclePresenter(QuestBound):
    def map(
        self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt, committed: ReadPort
    ) -> tuple[PresentationEvent, ...]:
        owner = self.quest_content.definition.layout.npc_id
        state = committed.component(CYCLE, owner).state
        cues: list[PresentationEvent] = []
        for event in facts:
            CyclePayloadCodec(CycleChanged.SCHEMA, self.quest_content).encode(event.payload)
            if not isinstance(event.payload, CycleChanged):
                raise ValueError("NPC_CYCLE_PAYLOAD")
            entry = event.payload.evidence
            if (
                event.header.producer_id != "quest.cycle"
                or event.header.type_key != event.payload.schema
                or event.header.phase != Phase.POST_TICK
                or (
                    event.header.wave != 0
                    or event.header.sequence != entry.sequence
                    or event.due_tick != entry.tick
                    or event.header.occurred_at != entry.tick
                    or event.header.caused_by != (entry.source_event_id,)
                    or entry.tick > receipt.tick
                    or entry.after.produced > state.produced
                    or entry.after.consumed > state.consumed
                )
            ):
                raise ValueError("NPC_CYCLE_SOURCE")
            identifier = EventId(
                "p1-"
                + hashlib.sha256(
                    pack(
                        (
                            "cue-id/v1",
                            event.header.event_id,
                            "quest.cycle-presenter",
                            str(len(cues)),
                        )
                    )
                ).hexdigest()
            )
            cue = CycleCue(owner, entry)
            cues.append(
                PresentationEvent(
                    EventHeader(
                        identifier,
                        cue.schema,
                        "quest.cycle-presenter",
                        receipt.tick,
                        Phase.PRESENT,
                        0,
                        0,
                        len(cues),
                        (event.header.event_id,),
                        (),
                    ),
                    cue,
                    "important",
                    "keep_all",
                    "",
                )
            )
        return tuple(cues)
