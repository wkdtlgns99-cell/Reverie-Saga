"""Strict saved local/inventory codecs and same-owner materialization staging."""

from dataclasses import asdict, replace

from contracts.errors import CandidateError, ReadOnlyViolation
from contracts.read_views import ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.messages import StateDelta
from contracts.turn import ProtocolSnapshot
from contracts.world_population import (
    INVENTORY,
    INVENTORY_FAMILY,
    MATERIALIZER,
    SETTLEMENT,
    SETTLEMENT_FAMILY,
    InventoryRead,
    SettlementDelta,
    SettlementPatch,
    SettlementRead,
)
from domain.canonical import (
    JsonObject,
    array_value,
    exact_fields,
    int_value,
    object_value,
    seal,
    text_value,
)
from domain.primitives import (
    ComponentAddress,
    EntityId,
    FieldAddress,
    FieldFamily,
    FrozenPayload,
    TypeKey,
)
from domain.state_types import ComponentRecord, CoreSnapshot
from domain.world import LocalDetail, Resident, WorldCatalog
from domain.world_population import (
    INVENTORY_SCHEMA,
    SETTLEMENT_SCHEMA,
    InventoryRecord,
    InventoryState,
    SettlementRecord,
    validate_settlement,
)
from domain.world_travel import WORLD_ACTOR, TravelerRecord
from orchestration.world_travel import WorldCheckpointPolicy


def encode_local(state: LocalDetail | None) -> JsonObject | None:
    return None if state is None else object_value(seal(asdict(state)))


def decode_local(value: JsonObject) -> LocalDetail:
    row = exact_fields(value, ("place_id", "sites", "residents"))
    residents = []
    for raw in array_value(row["residents"]):
        r = exact_fields(
            raw,
            (
                "id",
                "name",
                "occupation",
                "disposition",
                "workplace",
                "work_start_hour",
                "work_end_hour",
            ),
        )
        residents.append(
            Resident(
                text_value(r["id"]),
                text_value(r["name"]),
                text_value(r["occupation"]),
                text_value(r["disposition"]),
                text_value(r["workplace"]),
                int_value(r["work_start_hour"]),
                int_value(r["work_end_hour"]),
            )
        )
    return LocalDetail(
        text_value(row["place_id"]),
        tuple(text_value(v) for v in array_value(row["sites"])),
        tuple(residents),
    )


class _StateView[StateT]:
    __slots__ = ("_state", "_address", "_access")
    _state: StateT
    _address: FieldAddress
    _access: ViewAccess

    def __init__(
        self, state: StateT, family: FieldFamily, entity_id: EntityId, access: ViewAccess
    ) -> None:
        object.__setattr__(self, "_state", state)
        object.__setattr__(self, "_address", FieldAddress(family, entity_id))
        object.__setattr__(self, "_access", access)

    @property
    def state(self) -> StateT:
        self._access.observe(self._address, (), "read")
        return self._state

    def __setattr__(self, name: str, value: object) -> None:
        self._access.observe(self._address, (), "write")
        raise ReadOnlyViolation(name)

    def __delattr__(self, name: str) -> None:
        self.__setattr__(name, None)


class SettlementAdapter:
    key = SETTLEMENT

    def __init__(self, world: WorldCatalog) -> None:
        self.world = world

    def validate(self, record: ComponentRecord) -> None:
        if type(record) is not SettlementRecord or not isinstance(record, SettlementRecord):
            raise ValueError("WORLD_SETTLEMENT_RECORD")
        validate_settlement(self.world, record)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> SettlementRead:
        self.validate(record)
        if not isinstance(record, SettlementRecord):
            raise ValueError("WORLD_SETTLEMENT_RECORD")
        return _StateView(record.state, SETTLEMENT_FAMILY, record.entity_id, access)


class InventoryAdapter:
    key = INVENTORY

    def validate(self, record: ComponentRecord) -> None:
        if (
            type(record) is not InventoryRecord
            or not isinstance(record, InventoryRecord)
            or type(record.entity_id) is not str
            or record.entity_id != WORLD_ACTOR
            or type(record.state) is not InventoryState
        ):
            raise ValueError("WORLD_INVENTORY_RECORD")
        InventoryState(record.state.gold, record.state.items)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> InventoryRead:
        self.validate(record)
        if not isinstance(record, InventoryRecord):
            raise ValueError("WORLD_INVENTORY_RECORD")
        return _StateView(record.state, INVENTORY_FAMILY, record.entity_id, access)


class SettlementCodec:
    schema = SETTLEMENT_SCHEMA

    def __init__(self, world: WorldCatalog) -> None:
        self.adapter = SettlementAdapter(world)

    def encode(self, record: ComponentRecord) -> JsonObject:
        self.adapter.validate(record)
        if not isinstance(record, SettlementRecord):
            raise ValueError("WORLD_SETTLEMENT_RECORD")
        return {"state": encode_local(record.state)}

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        row = exact_fields(fields, ("state",))
        raw = row["state"]
        record = SettlementRecord(
            entity_id, None if raw is None else decode_local(object_value(raw))
        )
        self.adapter.validate(record)
        return record


class InventoryCodec:
    schema = INVENTORY_SCHEMA

    def encode(self, record: ComponentRecord) -> JsonObject:
        InventoryAdapter().validate(record)
        if not isinstance(record, InventoryRecord):
            raise ValueError("WORLD_INVENTORY_RECORD")
        return {"state": {"gold": record.state.gold, "items": record.state.items}}

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        row = exact_fields(fields, ("state",))
        state = exact_fields(row["state"], ("gold", "items"))
        items = []
        for raw in array_value(state["items"]):
            pair = array_value(raw)
            if len(pair) != 2:
                raise ValueError("WORLD_INVENTORY_ITEMS")
            items.append((text_value(pair[0]), int_value(pair[1])))
        record = InventoryRecord(entity_id, InventoryState(int_value(state["gold"]), tuple(items)))
        InventoryAdapter().validate(record)
        return record


class SettlementPayloadCodec:
    def __init__(self, world: WorldCatalog, schema: TypeKey) -> None:
        self.world, self._schema = world, schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if payload.schema != self.schema:
            raise ValueError("WORLD_SETTLEMENT_PAYLOAD")
        if type(payload) is SettlementDelta and isinstance(payload, SettlementDelta):
            validate_settlement(self.world, SettlementRecord(payload.entity_id, payload.before))
            validate_settlement(self.world, SettlementRecord(payload.entity_id, payload.after))
            return {
                "entity_id": payload.entity_id,
                "before": encode_local(payload.before),
                "after": encode_local(payload.after),
            }
        if type(payload) is SettlementPatch and isinstance(payload, SettlementPatch):
            validate_settlement(
                self.world, SettlementRecord(EntityId(payload.state.place_id), payload.state)
            )
            return {"state": encode_local(payload.state)}
        raise ValueError("WORLD_SETTLEMENT_PAYLOAD")

    def decode(self, data: JsonObject) -> FrozenPayload:
        payload: FrozenPayload
        if self.schema == SettlementDelta.SCHEMA:
            row = exact_fields(data, ("entity_id", "before", "after"))
            before = None if row["before"] is None else decode_local(object_value(row["before"]))
            payload = SettlementDelta(
                EntityId(text_value(row["entity_id"])),
                before,
                decode_local(object_value(row["after"])),
            )
        elif self.schema == SettlementPatch.SCHEMA:
            row = exact_fields(data, ("state",))
            payload = SettlementPatch(decode_local(object_value(row["state"])))
        else:
            raise ValueError("WORLD_SETTLEMENT_PAYLOAD")
        self.encode(payload)
        return payload


class SettlementReducer:
    schema = SettlementDelta.SCHEMA
    owner_id = MATERIALIZER

    def __init__(self, world: WorldCatalog) -> None:
        self.world = world

    def _delta(self, delta: StateDelta) -> SettlementDelta:
        if (
            type(delta) is not SettlementDelta
            or not isinstance(delta, SettlementDelta)
            or delta.before is not None
            or delta.after is None
        ):
            raise CandidateError("INVALID_DELTA", "local materialization transition")
        validate_settlement(self.world, SettlementRecord(delta.entity_id, delta.after))
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._delta(delta)
        if before.component(SETTLEMENT, value.entity_id).state is not None:
            raise CandidateError("INVALID_DELTA", "local detail already exists")
        editor.apply_patch(
            ComponentAddress(SETTLEMENT_SCHEMA, value.entity_id), SettlementPatch(value.after)
        )

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if len(changes) != 1:
            raise CandidateError("INVALID_DELTA", "local detail cannot be rematerialized")
        return self._delta(changes[0])

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._delta(delta)
        return value.before == value.after

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._delta(delta)
        if after.component(SETTLEMENT, value.entity_id).state != value.after:
            raise CandidateError("INVALID_DELTA", "local materialization net mismatch")


class SettlementPatchRoute:
    schema = SettlementPatch.SCHEMA
    component_schema = SETTLEMENT_SCHEMA
    family = SETTLEMENT_FAMILY

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        if (
            type(before) is not SettlementRecord
            or not isinstance(before, SettlementRecord)
            or before.state is not None
            or type(patch) is not SettlementPatch
            or not isinstance(patch, SettlementPatch)
        ):
            raise ValueError("WORLD_SETTLEMENT_PATCH")
        return replace(before, state=patch.state)


class PopulationCheckpointPolicy:
    def __init__(self, world: WorldCatalog) -> None:
        self.world = world

    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        travelers = tuple(c for c in core.components if type(c) is TravelerRecord)
        settlements = tuple(c for c in core.components if type(c) is SettlementRecord)
        inventories = tuple(c for c in core.components if type(c) is InventoryRecord)
        if (
            len(travelers) != 1
            or len(inventories) != 1
            or len(settlements) != len(self.world.places)
            or len(core.components) != len(settlements) + 2
        ):
            raise ValueError("WORLD_POPULATION_CHECKPOINT")
        WorldCheckpointPolicy(self.world).validate(replace(core, components=travelers), protocol)
        InventoryAdapter().validate(inventories[0])
        if {c.entity_id for c in settlements} != {p.id for p in self.world.places}:
            raise ValueError("WORLD_POPULATION_CHECKPOINT")
        for record in settlements:
            validate_settlement(self.world, record)
            if (record.state is not None) != (record.entity_id in travelers[0].state.visited):
                raise ValueError("WORLD_LOCAL_VISIT_BINDING")
