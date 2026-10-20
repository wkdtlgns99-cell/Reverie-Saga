"""Strict codecs, read views, staging and checkpoint invariants for provisions."""

from dataclasses import replace
import hashlib
from typing import cast

from contracts.dialogue import QuestBound, QuestContent
from contracts.errors import CandidateError, ReadOnlyViolation
from contracts.messages import EventHeader, PresentationEvent, StateDelta, WorldEvent
from contracts.npc_work import (
    PROVISIONS,
    STOCK_FAMILY,
    ProvisionPrepared,
    ProvisionsCue,
    ProvisionsDelta,
    ProvisionsPatch,
    ProvisionsRead,
)
from contracts.read_views import (
    ComponentKey,
    ComponentPatch,
    ReadPort,
    StagingEditor,
    ViewAccess,
)
from contracts.turn import CommitReceipt, ProtocolSnapshot
from domain.canonical import JsonObject, exact_fields, int_value, pack, text_value
from domain.npc_work import WORK_PERIOD, ProvisionsRecord, stock_at
from domain.primitives import (
    ComponentAddress,
    EntityId,
    EventId,
    FieldAddress,
    FieldFamily,
    FrozenPayload,
    Phase,
    TypeKey,
    require_integer,
)
from domain.state_types import ComponentRecord, CoreSnapshot
from orchestration.npc_memory import MemoryCheckpointPolicy


class _StockView:
    __slots__ = ("_record", "_access")

    def __init__(self, record: ProvisionsRecord, access: ViewAccess) -> None:
        object.__setattr__(self, "_record", record)
        object.__setattr__(self, "_access", access)

    _record: ProvisionsRecord
    _access: ViewAccess

    @property
    def stock(self) -> int:
        self._access.observe(FieldAddress(STOCK_FAMILY, self._record.entity_id), (), "read")
        return self._record.stock

    def __setattr__(self, name: str, value: object) -> None:
        self._access.observe(FieldAddress(STOCK_FAMILY, self._record.entity_id), (), "write")
        raise ReadOnlyViolation(name)

    def __delattr__(self, name: str) -> None:
        self.__setattr__(name, None)


class ProvisionsAdapter(QuestBound):
    @property
    def key(self) -> ComponentKey[ProvisionsRead]:
        return PROVISIONS

    def validate(self, record: ComponentRecord) -> None:
        if (
            type(record) is not ProvisionsRecord
            or record.entity_id != self.quest_content.definition.layout.npc_id
        ):
            raise ValueError("NPC_WORK_OWNER")
        ProvisionsRecord(record.entity_id, record.stock)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> ProvisionsRead:
        self.validate(record)
        return _StockView(cast(ProvisionsRecord, record), access)


class ProvisionsCodec(QuestBound):
    @property
    def schema(self) -> TypeKey:
        return PROVISIONS.schema

    def encode(self, record: ComponentRecord) -> JsonObject:
        ProvisionsAdapter(self.quest_content).validate(record)
        return {"stock": cast(ProvisionsRecord, record).stock}

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        row = exact_fields(fields, ("stock",))
        record = ProvisionsRecord(entity_id, int_value(row["stock"]))
        ProvisionsAdapter(self.quest_content).validate(record)
        return record


class ProvisionsPayloadCodec(QuestBound):
    def __init__(self, schema: TypeKey, content: QuestContent) -> None:
        super().__init__(content)
        if schema not in (
            ProvisionsDelta.SCHEMA,
            ProvisionsPatch.SCHEMA,
            ProvisionPrepared.SCHEMA,
            ProvisionsCue.SCHEMA,
        ):
            raise ValueError("NPC_WORK_SCHEMA")
        self._schema = schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if type(payload) is ProvisionsCue and self.schema == ProvisionsCue.SCHEMA:
            data: JsonObject = {
                "npc_id": payload.npc_id,
                "stock": payload.stock,
                "tick": payload.tick,
            }
        elif type(payload) is ProvisionsPatch and self.schema == ProvisionsPatch.SCHEMA:
            data = {"stock": payload.stock}
        elif type(payload) is ProvisionsDelta and self.schema == ProvisionsDelta.SCHEMA:
            data = {
                "entity_id": payload.entity_id,
                "before": payload.before,
                "after": payload.after,
            }
        elif type(payload) is ProvisionPrepared and self.schema == ProvisionPrepared.SCHEMA:
            data = {"npc_id": payload.npc_id, "before": payload.before, "after": payload.after}
        else:
            raise ValueError("NPC_WORK_PAYLOAD")
        self.decode(data)
        return data

    def decode(self, data: JsonObject) -> FrozenPayload:
        owner = self.quest_content.definition.layout.npc_id
        if self.schema == ProvisionsCue.SCHEMA:
            row = exact_fields(data, ("npc_id", "stock", "tick"))
            record = ProvisionsRecord(EntityId(text_value(row["npc_id"])), int_value(row["stock"]))
            ProvisionsAdapter(self.quest_content).validate(record)
            tick = int_value(row["tick"])
            require_integer(tick, 1)
            if record.stock == 0 or tick != record.stock * WORK_PERIOD:
                raise ValueError("NPC_WORK_SOURCE")
            return ProvisionsCue(record.entity_id, record.stock, tick)
        if self.schema == ProvisionsPatch.SCHEMA:
            row = exact_fields(data, ("stock",))
            return ProvisionsPatch(ProvisionsRecord(owner, int_value(row["stock"])).stock)
        key = "npc_id" if self.schema == ProvisionPrepared.SCHEMA else "entity_id"
        row = exact_fields(data, (key, "before", "after"))
        entity = EntityId(text_value(row[key]))
        before, after = int_value(row["before"]), int_value(row["after"])
        ProvisionsAdapter(self.quest_content).validate(ProvisionsRecord(entity, before))
        ProvisionsRecord(entity, after)
        if after <= before or self.schema == ProvisionPrepared.SCHEMA and after != before + 1:
            raise ValueError("NPC_WORK_TRANSITION")
        if self.schema == ProvisionPrepared.SCHEMA:
            return ProvisionPrepared(entity, before, after)
        return ProvisionsDelta(entity, before, after)


class ProvisionsReducer(QuestBound):
    @property
    def schema(self) -> TypeKey:
        return ProvisionsDelta.SCHEMA

    @property
    def owner_id(self) -> str:
        return "quest.provisioner"

    def _value(self, delta: object) -> ProvisionsDelta:
        if type(delta) is not ProvisionsDelta:
            raise CandidateError("INVALID_DELTA", "provision type")
        try:
            ProvisionsPayloadCodec(self.schema, self.quest_content).encode(delta)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "provision transition") from error
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._value(delta)
        if (
            value.after != value.before + 1
            or before.component(PROVISIONS, value.entity_id).stock != value.before
        ):
            raise CandidateError("INVALID_DELTA", "provision endpoint")
        editor.apply_patch(
            ComponentAddress(PROVISIONS.schema, value.entity_id), ProvisionsPatch(value.after)
        )

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "provision empty composition")
        values = tuple(self._value(change) for change in changes)
        if any(v.after != v.before + 1 for v in values) or any(
            a.entity_id != b.entity_id or a.after != b.before for a, b in zip(values, values[1:])
        ):
            raise CandidateError("INVALID_DELTA", "provision discontinuity")
        return self._value(ProvisionsDelta(values[0].entity_id, values[0].before, values[-1].after))

    def is_identity(self, delta: StateDelta) -> bool:
        self._value(delta)
        return False

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._value(delta)
        if after.component(PROVISIONS, value.entity_id).stock != value.after:
            raise CandidateError("INVALID_DELTA", "provision net endpoint")


class ProvisionsPatchRoute(QuestBound):
    @property
    def schema(self) -> TypeKey:
        return ProvisionsPatch.SCHEMA

    @property
    def component_schema(self) -> TypeKey:
        return PROVISIONS.schema

    @property
    def family(self) -> FieldFamily:
        return STOCK_FAMILY

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        ProvisionsAdapter(self.quest_content).validate(before)
        if type(patch) is not ProvisionsPatch:
            raise ValueError("NPC_WORK_PATCH")
        value = ProvisionsRecord(before.entity_id, patch.stock)
        if value.stock != cast(ProvisionsRecord, before).stock + 1:
            raise ValueError("NPC_WORK_TRANSITION")
        return value


class ProvisionsCheckpointPolicy(QuestBound):
    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        matches = tuple(r for r in core.components if r.schema == PROVISIONS.schema)
        if len(matches) != 1:
            raise ValueError("NPC_WORK_CHECKPOINT")
        record = matches[0]
        ProvisionsAdapter(self.quest_content).validate(record)
        if cast(ProvisionsRecord, record).stock != stock_at(core.tick):
            raise ValueError("NPC_WORK_CHECKPOINT")
        MemoryCheckpointPolicy(self.quest_content).validate(
            replace(core, components=tuple(r for r in core.components if r is not record)), protocol
        )


class ProvisionsPresenter(QuestBound):
    def map(
        self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt, committed: ReadPort
    ) -> tuple[PresentationEvent, ...]:
        owner = self.quest_content.definition.layout.npc_id
        stock = committed.component(PROVISIONS, owner).stock
        cues: list[PresentationEvent] = []
        for event in facts:
            ProvisionsPayloadCodec(ProvisionPrepared.SCHEMA, self.quest_content).encode(
                event.payload
            )
            if not isinstance(event.payload, ProvisionPrepared):
                raise ValueError("NPC_WORK_PAYLOAD")
            tick = event.due_tick
            if (
                event.header.producer_id != "quest.provisioner"
                or event.header.phase != Phase.POST_TICK
                or tick != event.header.occurred_at
                or not 1 <= tick <= receipt.tick
                or tick % WORK_PERIOD
                or event.payload.after != stock_at(tick)
                or event.payload.after > stock
            ):
                raise ValueError("NPC_WORK_SOURCE")
            identifier = EventId(
                "p1-"
                + hashlib.sha256(
                    pack(
                        (
                            "cue-id/v1",
                            event.header.event_id,
                            "quest.provisions-presenter",
                            str(len(cues)),
                        )
                    )
                ).hexdigest()
            )
            cue = ProvisionsCue(owner, event.payload.after, tick)
            cues.append(
                PresentationEvent(
                    EventHeader(
                        identifier,
                        cue.schema,
                        "quest.provisions-presenter",
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
