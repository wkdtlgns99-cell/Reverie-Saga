"""Supply admission,strict codecs,observed reads and COMMIT resource staging."""

from dataclasses import asdict, replace
import hashlib

from contracts.errors import CandidateError, SchemaError
from contracts.messages import EventHeader, PresentationEvent, StateDelta, WorldEvent
from contracts.read_views import ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.turn import (
    AdmittedAction,
    AdmittedCommand,
    AdmissionOutcome,
    CommitReceipt,
    GameCommand,
    ProtocolSnapshot,
    TurnPlan,
    TurnRejected,
    failure,
)
from contracts.world_population import INVENTORY, INVENTORY_FAMILY, SETTLEMENT, SETTLEMENT_FAMILY
from contracts.world_supply import (
    SUPPLY,
    SUPPLY_FAMILY,
    SUPPLY_OWNER,
    InventoryDelta,
    InventoryPatch,
    SupplyAction,
    SupplyActed,
    SupplyCue,
    SupplyDelta,
    SupplyPatch,
    SupplyRead,
)
from contracts.world_travel import TRAVELER, TRAVEL_FAMILY
from domain.canonical import (
    JsonObject,
    exact_fields,
    int_value,
    object_value,
    pack,
    seal,
    text_value,
)
from domain.primitives import (
    ComponentAddress,
    EntityId,
    EventId,
    FrozenPayload,
    Phase,
    Tick,
    TypeKey,
)
from domain.state_types import ComponentRecord, CoreSnapshot
from domain.world import WorldCatalog
from domain.world_population import INVENTORY_SCHEMA, InventoryRecord
from domain.world_supply import (
    CONSUMPTION_INTERVAL_SECONDS,
    DELIVERY_REWARD,
    SUPPLY_SCHEMA,
    SUPPLY_INTERVAL_SECONDS,
    SupplyRecord,
    SupplyScenario,
    SupplyState,
    supply_action,
    supply_item,
)
from domain.world_travel import WORLD_ACTOR
from orchestration.world_population import InventoryCodec, PopulationCheckpointPolicy, _StateView

SUPPLY_FIELDS = tuple(SupplyState.__dataclass_fields__)
ACTION_FIELDS = ("place_id", "npc_id", "operation")
SUPPLY_REJECTIONS = (
    "SUPPLY_INACTIVE",
    "INVALID_COMMAND",
    "SUPPLY_QUEST_STAGE",
    "SUPPLY_ALREADY_COLLECTED",
    "SUPPLY_WAREHOUSE_EMPTY",
    "SUPPLY_ITEMS_MISSING",
)


def encode_supply(state: SupplyState) -> JsonObject:
    SupplyState(**asdict(state))
    return object_value(seal(asdict(state)))


def decode_supply(data: JsonObject) -> SupplyState:
    row = exact_fields(data, SUPPLY_FIELDS)
    return SupplyState(**{name: int_value(row[name]) for name in SUPPLY_FIELDS})


class SupplyAdapter:
    key = SUPPLY

    def __init__(self, world: WorldCatalog) -> None:
        self.world = world

    def validate(self, record: ComponentRecord) -> None:
        if (
            type(record) is not SupplyRecord
            or not isinstance(record, SupplyRecord)
            or type(record.entity_id) is not str
            or type(record.state) is not SupplyState
        ):
            raise ValueError("WORLD_SUPPLY_RECORD")
        self.world.place(record.entity_id)
        encode_supply(record.state)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> SupplyRead:
        self.validate(record)
        if not isinstance(record, SupplyRecord):
            raise ValueError("WORLD_SUPPLY_RECORD")
        return _StateView(record.state, SUPPLY_FAMILY, record.entity_id, access)


class SupplyCodec:
    schema = SUPPLY_SCHEMA

    def __init__(self, world: WorldCatalog) -> None:
        self.adapter = SupplyAdapter(world)

    def encode(self, record: ComponentRecord) -> JsonObject:
        self.adapter.validate(record)
        if not isinstance(record, SupplyRecord):
            raise ValueError("WORLD_SUPPLY_RECORD")
        return {"state": encode_supply(record.state)}

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        row = exact_fields(fields, ("state",))
        record = SupplyRecord(entity_id, decode_supply(object_value(row["state"])))
        self.adapter.validate(record)
        return record


class SupplyAdmission:
    schema = SupplyAction.SCHEMA
    reads = (TRAVEL_FAMILY, SETTLEMENT_FAMILY, INVENTORY_FAMILY, SUPPLY_FAMILY)

    def __init__(self, scenario: SupplyScenario) -> None:
        self.scenario = scenario

    def admit(
        self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str
    ) -> AdmissionOutcome:
        payload = command.payload
        code = ""
        if command.actor_id != WORLD_ACTOR:
            code = "UNAUTHORIZED_ACTOR"
        elif (
            type(payload) is not SupplyAction
            or not isinstance(payload, SupplyAction)
            or any(
                type(v) is not str for v in (payload.place_id, payload.npc_id, payload.operation)
            )
            or payload.operation not in ("accept", "collect", "deliver")
        ):
            code = "INVALID_COMMAND"
        else:
            traveler = state.component(TRAVELER, WORLD_ACTOR).state
            if traveler.destination_id or traveler.place_id != payload.place_id:
                code = "SUPPLY_OUT_OF_REACH"
            else:
                entity = EntityId(payload.place_id)
                local = state.component(SETTLEMENT, entity).state
                index = 0 if payload.operation == "collect" else 1
                if local is None or local.residents[index].id != payload.npc_id:
                    code = "SUPPLY_WRONG_NPC"
                else:
                    try:
                        supply_action(
                            state.component(SUPPLY, entity).state,
                            state.component(INVENTORY, WORLD_ACTOR).state,
                            self.scenario,
                            payload.place_id,
                            payload.operation,
                            start_tick + 1,
                        )
                    except ValueError as error:
                        if str(error) not in SUPPLY_REJECTIONS:
                            raise
                        code = str(error)
        if code:
            return TurnRejected(failure(code), command.expected_revision)
        target = Tick(start_tick + 1)
        key = (
            "a1-"
            + hashlib.sha256(
                pack(("world-supply/v1", world_id, str(target), command.command_id))
            ).hexdigest()
        )
        return AdmittedCommand(
            TurnPlan(command, start_tick, target),
            AdmittedAction(command.actor_id, command.payload, key),
        )


class SupplyPayloadCodec:
    def __init__(self, schema: TypeKey) -> None:
        self._schema = schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if payload.schema != self.schema:
            raise SchemaError("UNSUPPORTED_SCHEMA", "supply payload")
        if type(payload) is SupplyAction and isinstance(payload, SupplyAction):
            if any(
                type(v) is not str for v in (payload.place_id, payload.npc_id, payload.operation)
            ):
                raise ValueError("INVALID_COMMAND")
            return {
                "place_id": payload.place_id,
                "npc_id": payload.npc_id,
                "operation": payload.operation,
            }
        if type(payload) in (SupplyActed, SupplyCue) and isinstance(
            payload, (SupplyActed, SupplyCue)
        ):
            return object_value(seal(asdict(payload)))
        if type(payload) is SupplyPatch and isinstance(payload, SupplyPatch):
            return {"state": encode_supply(payload.state)}
        if type(payload) is InventoryPatch and isinstance(payload, InventoryPatch):
            return InventoryCodec().encode(InventoryRecord(WORLD_ACTOR, payload.state))
        if type(payload) is SupplyDelta and isinstance(payload, SupplyDelta):
            return {
                "entity_id": payload.entity_id,
                "before": encode_supply(payload.before),
                "after": encode_supply(payload.after),
            }
        if type(payload) is InventoryDelta and isinstance(payload, InventoryDelta):
            codec = InventoryCodec()
            return {
                "entity_id": payload.entity_id,
                "before": codec.encode(InventoryRecord(payload.entity_id, payload.before)),
                "after": codec.encode(InventoryRecord(payload.entity_id, payload.after)),
            }
        raise SchemaError("UNSUPPORTED_SCHEMA", "supply payload class")

    def decode(self, data: JsonObject) -> FrozenPayload:
        result: FrozenPayload
        if self.schema in (SupplyAction.SCHEMA, SupplyActed.SCHEMA, SupplyCue.SCHEMA):
            names = (
                ACTION_FIELDS
                if self.schema == SupplyAction.SCHEMA
                else ("actor_id", *ACTION_FIELDS)
            )
            row = exact_fields(data, names)
            values = tuple(text_value(row[name]) for name in ACTION_FIELDS)
            result = (
                SupplyAction(*values)
                if self.schema == SupplyAction.SCHEMA
                else (SupplyActed if self.schema == SupplyActed.SCHEMA else SupplyCue)(
                    EntityId(text_value(row["actor_id"])), *values
                )
            )
        elif self.schema in (SupplyPatch.SCHEMA, InventoryPatch.SCHEMA):
            row = exact_fields(data, ("state",))
            if self.schema == SupplyPatch.SCHEMA:
                result = SupplyPatch(decode_supply(object_value(row["state"])))
            else:
                record = InventoryCodec().decode(WORLD_ACTOR, data)
                if not isinstance(record, InventoryRecord):
                    raise ValueError("WORLD_INVENTORY_RECORD")
                result = InventoryPatch(record.state)
        elif self.schema in (SupplyDelta.SCHEMA, InventoryDelta.SCHEMA):
            row = exact_fields(data, ("entity_id", "before", "after"))
            entity = EntityId(text_value(row["entity_id"]))
            if self.schema == SupplyDelta.SCHEMA:
                result = SupplyDelta(
                    entity,
                    decode_supply(object_value(row["before"])),
                    decode_supply(object_value(row["after"])),
                )
            else:
                a = InventoryCodec().decode(entity, object_value(row["before"]))
                b = InventoryCodec().decode(entity, object_value(row["after"]))
                if not isinstance(a, InventoryRecord) or not isinstance(b, InventoryRecord):
                    raise ValueError("WORLD_INVENTORY_RECORD")
                result = InventoryDelta(entity, a.state, b.state)
        else:
            raise SchemaError("UNSUPPORTED_SCHEMA", "supply schema")
        self.encode(result)
        return result


class SupplyReducer:
    schema = SupplyDelta.SCHEMA
    owner_id = SUPPLY_OWNER

    def _delta(self, delta: StateDelta) -> SupplyDelta:
        if type(delta) is not SupplyDelta or not isinstance(delta, SupplyDelta):
            raise CandidateError("INVALID_DELTA", "supply delta class")
        encode_supply(delta.before)
        encode_supply(delta.after)
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._delta(delta)
        if before.component(SUPPLY, value.entity_id).state != value.before:
            raise CandidateError("INVALID_DELTA", "supply before mismatch")
        editor.apply_patch(
            ComponentAddress(SUPPLY_SCHEMA, value.entity_id), SupplyPatch(value.after)
        )

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "empty supply composition")
        values = tuple(self._delta(d) for d in changes)
        for a, b in zip(values, values[1:]):
            if a.entity_id != b.entity_id or a.after != b.before:
                raise CandidateError("INVALID_DELTA", "noncontiguous supply composition")
        return replace(values[0], after=values[-1].after)

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._delta(delta)
        return value.before == value.after

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._delta(delta)
        if after.component(SUPPLY, value.entity_id).state != value.after:
            raise CandidateError("INVALID_DELTA", "supply net mismatch")


class InventoryReducer:
    schema = InventoryDelta.SCHEMA
    owner_id = SUPPLY_OWNER

    def _delta(self, delta: StateDelta) -> InventoryDelta:
        if (
            type(delta) is not InventoryDelta
            or not isinstance(delta, InventoryDelta)
            or delta.entity_id != WORLD_ACTOR
        ):
            raise CandidateError("INVALID_DELTA", "inventory delta class/actor")
        codec = InventoryCodec()
        codec.encode(InventoryRecord(delta.entity_id, delta.before))
        codec.encode(InventoryRecord(delta.entity_id, delta.after))
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._delta(delta)
        if before.component(INVENTORY, value.entity_id).state != value.before:
            raise CandidateError("INVALID_DELTA", "inventory before mismatch")
        editor.apply_patch(
            ComponentAddress(INVENTORY_SCHEMA, value.entity_id), InventoryPatch(value.after)
        )

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "empty inventory composition")
        values = tuple(self._delta(d) for d in changes)
        for a, b in zip(values, values[1:]):
            if a.entity_id != b.entity_id or a.after != b.before:
                raise CandidateError("INVALID_DELTA", "noncontiguous inventory composition")
        return replace(values[0], after=values[-1].after)

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._delta(delta)
        return value.before == value.after

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._delta(delta)
        if after.component(INVENTORY, value.entity_id).state != value.after:
            raise CandidateError("INVALID_DELTA", "inventory net mismatch")


class SupplyPatchRoute:
    schema = SupplyPatch.SCHEMA
    component_schema = SUPPLY_SCHEMA
    family = SUPPLY_FAMILY

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        if (
            type(before) is not SupplyRecord
            or not isinstance(before, SupplyRecord)
            or type(patch) is not SupplyPatch
            or not isinstance(patch, SupplyPatch)
        ):
            raise ValueError("WORLD_SUPPLY_PATCH")
        return replace(before, state=patch.state)


class InventoryPatchRoute:
    schema = InventoryPatch.SCHEMA
    component_schema = INVENTORY_SCHEMA
    family = INVENTORY_FAMILY

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        if (
            type(before) is not InventoryRecord
            or not isinstance(before, InventoryRecord)
            or type(patch) is not InventoryPatch
            or not isinstance(patch, InventoryPatch)
        ):
            raise ValueError("WORLD_INVENTORY_PATCH")
        return replace(before, state=patch.state)


class SupplyCheckpointPolicy:
    def __init__(self, world: WorldCatalog, scenario: SupplyScenario) -> None:
        world.place(scenario.place_id)
        self.world, self.scenario = world, scenario

    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        supplies = tuple(c for c in core.components if isinstance(c, SupplyRecord))
        population = tuple(c for c in core.components if not isinstance(c, SupplyRecord))
        PopulationCheckpointPolicy(self.world).validate(
            replace(core, components=population), protocol
        )
        if len(supplies) != len(self.world.places) or {s.entity_id for s in supplies} != {
            p.id for p in self.world.places
        }:
            raise ValueError("WORLD_SUPPLY_CHECKPOINT")
        expected_items = []
        expected_gold = 0
        for supply in supplies:
            SupplyAdapter(self.world).validate(supply)
            state = supply.state
            if (
                state.consumed + state.missed != core.tick // CONSUMPTION_INTERVAL_SECONDS
                or state.received > core.tick // SUPPLY_INTERVAL_SECONDS
            ):
                raise ValueError("WORLD_SUPPLY_PERIOD_BINDING")
            if supply.entity_id != self.scenario.place_id and (state.stage or state.claimed):
                raise ValueError("WORLD_SUPPLY_SCENARIO_BINDING")
            if (
                (core.tick < self.scenario.start_tick and (state.stage or state.claimed))
                or state.resolved_tick > core.tick
                or (
                    state.stage == 2
                    and not self.scenario.start_tick <= state.resolved_tick < self.scenario.end_tick
                )
                or (
                    supply.entity_id == self.scenario.place_id
                    and core.tick >= self.scenario.end_tick
                    and state.stage not in (2, 3)
                )
                or (state.stage == 3 and core.tick < self.scenario.end_tick)
                or (state.stage == 0 and state.claimed)
            ):
                raise ValueError("WORLD_SUPPLY_STAGE_BINDING")
            count = state.claimed - state.repair_used
            if count:
                expected_items.append((supply_item(supply.entity_id), count))
            expected_gold += DELIVERY_REWARD if state.stage == 2 else 0
        inventory = next(c for c in population if isinstance(c, InventoryRecord)).state
        if inventory.gold != expected_gold or inventory.items != tuple(sorted(expected_items)):
            raise ValueError("WORLD_SUPPLY_RESOURCE_BINDING")


class SupplyPresenter:
    def map(
        self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt, committed: ReadPort
    ) -> tuple[PresentationEvent, ...]:
        cues: list[PresentationEvent] = []
        for fact in facts:
            payload = fact.payload
            if type(payload) is not SupplyActed or not isinstance(payload, SupplyActed):
                raise SchemaError("UNSUPPORTED_SCHEMA", "supply presenter")
            identifier = (
                "p1-"
                + hashlib.sha256(
                    pack(
                        (
                            "cue-id/v1",
                            fact.header.event_id,
                            "world.supply-presenter",
                            str(len(cues)),
                        )
                    )
                ).hexdigest()
            )
            cue = SupplyCue(payload.actor_id, payload.place_id, payload.npc_id, payload.operation)
            cues.append(
                PresentationEvent(
                    EventHeader(
                        EventId(identifier),
                        cue.schema,
                        "world.supply-presenter",
                        receipt.tick,
                        Phase.PRESENT,
                        0,
                        0,
                        len(cues),
                        (fact.header.event_id,),
                        (),
                    ),
                    cue,
                    "important",
                    "keep_all",
                    "",
                )
            )
        return tuple(cues)
