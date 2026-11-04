"""Registered travel admission,observed views,codecs and COMMIT staging."""

from dataclasses import replace
import hashlib

from contracts.errors import CandidateError, ReadOnlyViolation, SchemaError
from contracts.messages import EventHeader, PresentationEvent, StateDelta, WorldEvent
from contracts.read_views import ComponentKey, ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.turn import (
    AdmittedAction,
    AdmittedCommand,
    AdmissionOutcome,
    GameCommand,
    CommitReceipt,
    ProtocolSnapshot,
    TurnPlan,
    TurnRejected,
    failure,
)
from contracts.world_travel import (
    TRAVELER,
    TRAVEL_FAMILY,
    TRAVEL_OWNER,
    Footstep,
    TravelDelta,
    TravelPatch,
    TravelerRead,
    Walked,
    WalkCue,
)
from domain.canonical import (
    JsonObject,
    array_value,
    exact_fields,
    int_value,
    object_value,
    pack,
    text_value,
)
from domain.primitives import (
    ComponentAddress,
    EntityId,
    FieldAddress,
    FieldFamily,
    EventId,
    Phase,
    FrozenPayload,
    Tick,
    TypeKey,
)
from domain.state_types import ComponentRecord, CoreSnapshot
from domain.world import WorldCatalog
from domain.world_travel import (
    TRAVEL_SCHEMA,
    WORLD_ACTOR,
    TravelState,
    TravelerRecord,
    footstep,
    validate_traveler,
)


def encode_travel(state: TravelState) -> JsonObject:
    TravelState(state.place_id, state.destination_id, state.offset_m, state.visited)
    return {
        "place_id": state.place_id,
        "destination_id": state.destination_id,
        "offset_m": state.offset_m,
        "visited": state.visited,
    }


def decode_travel(row: JsonObject) -> TravelState:
    d = exact_fields(row, ("place_id", "destination_id", "offset_m", "visited"))
    return TravelState(
        text_value(d["place_id"]),
        text_value(d["destination_id"]),
        int_value(d["offset_m"]),
        tuple(text_value(v) for v in array_value(d["visited"])),
    )


class _TravelerView:
    __slots__ = ("_record", "_access")
    _record: TravelerRecord
    _access: ViewAccess

    def __init__(self, record: TravelerRecord, access: ViewAccess) -> None:
        object.__setattr__(self, "_record", record)
        object.__setattr__(self, "_access", access)

    @property
    def state(self) -> TravelState:
        self._access.observe(FieldAddress(TRAVEL_FAMILY, self._record.entity_id), (), "read")
        return self._record.state

    def __setattr__(self, name: str, value: object) -> None:
        self._access.observe(FieldAddress(TRAVEL_FAMILY, self._record.entity_id), (), "write")
        raise ReadOnlyViolation(name)

    def __delattr__(self, name: str) -> None:
        self.__setattr__(name, None)


class TravelerAdapter:
    def __init__(self, world: WorldCatalog) -> None:
        self.world = world

    @property
    def key(self) -> ComponentKey[TravelerRead]:
        return TRAVELER

    def validate(self, record: ComponentRecord) -> None:
        if type(record) is not TravelerRecord or not isinstance(record, TravelerRecord):
            raise ValueError("WORLD_TRAVEL_RECORD")
        if type(record.entity_id) is not str or record.entity_id != WORLD_ACTOR:
            raise ValueError("WORLD_TRAVEL_ACTOR")
        validate_traveler(self.world, record.state)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> TravelerRead:
        self.validate(record)
        if not isinstance(record, TravelerRecord):
            raise ValueError("WORLD_TRAVEL_RECORD")
        return _TravelerView(record, access)


class FootAdmission:
    def __init__(self, world: WorldCatalog) -> None:
        self.world = world

    @property
    def schema(self) -> TypeKey:
        return Footstep.SCHEMA

    @property
    def reads(self) -> tuple[FieldFamily, ...]:
        return (TRAVEL_FAMILY,)

    def admit(
        self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str
    ) -> AdmissionOutcome:
        if command.actor_id != WORLD_ACTOR:
            return TurnRejected(failure("UNAUTHORIZED_ACTOR"), command.expected_revision)
        payload = command.payload
        if type(payload) is not Footstep or not isinstance(payload, Footstep):
            return TurnRejected(failure("INVALID_COMMAND"), command.expected_revision)
        before = state.component(TRAVELER, command.actor_id).state
        try:
            footstep(self.world, before, payload.destination_id, payload.direction)
        except ValueError as error:
            code = str(error)
            if code not in (
                "INVALID_COMMAND",
                "WORLD_ROUTE_ACTIVE",
                "WORLD_NOT_ON_ROUTE",
                "WORLD_NOT_ADJACENT",
                "TRANSPORT_REQUIRED",
            ):
                raise
            return TurnRejected(failure(code), command.expected_revision)
        target = Tick(start_tick + 1)
        key = (
            "a1-"
            + hashlib.sha256(
                pack(
                    (
                        "world-footstep/v1",
                        world_id,
                        str(target),
                        payload.destination_id,
                        str(payload.direction),
                    )
                )
            ).hexdigest()
        )
        return AdmittedCommand(
            TurnPlan(command, start_tick, target), AdmittedAction(command.actor_id, payload, key)
        )


class TravelReducer:
    def __init__(self, world: WorldCatalog) -> None:
        self.world = world

    @property
    def schema(self) -> TypeKey:
        return TravelDelta.SCHEMA

    @property
    def owner_id(self) -> str:
        return TRAVEL_OWNER

    def _delta(self, delta: StateDelta) -> TravelDelta:
        if type(delta) is not TravelDelta or not isinstance(delta, TravelDelta):
            raise CandidateError("INVALID_DELTA", "travel delta class")
        if delta.entity_id != WORLD_ACTOR:
            raise CandidateError("INVALID_DELTA", "travel owner")
        validate_traveler(self.world, delta.before)
        validate_traveler(self.world, delta.after)
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._delta(delta)
        if before.component(TRAVELER, value.entity_id).state != value.before:
            raise CandidateError("INVALID_DELTA", "travel before mismatch")
        destination = value.before.destination_id or value.after.destination_id
        candidates = [footstep(self.world, value.before, destination, 1)]
        if value.before.destination_id:
            candidates.append(footstep(self.world, value.before, destination, -1))
        if value.after not in candidates:
            raise CandidateError("INVALID_DELTA", "travel is not one footstep")
        editor.apply_patch(
            ComponentAddress(TRAVEL_SCHEMA, value.entity_id), TravelPatch(value.after)
        )

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "empty travel composition")
        values = tuple(self._delta(d) for d in changes)
        for a, b in zip(values, values[1:]):
            if a.entity_id != b.entity_id or a.after != b.before:
                raise CandidateError("INVALID_DELTA", "noncontiguous travel composition")
        return replace(values[0], after=values[-1].after)

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._delta(delta)
        return value.before == value.after

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._delta(delta)
        if (
            self.is_identity(value)
            or after.component(TRAVELER, value.entity_id).state != value.after
        ):
            raise CandidateError("INVALID_DELTA", "travel net mismatch")


class TravelPayloadCodec:
    def __init__(self, schema: TypeKey) -> None:
        self._schema = schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if payload.schema != self.schema:
            raise SchemaError("UNSUPPORTED_SCHEMA", "world payload")
        if type(payload) is Footstep and isinstance(payload, Footstep):
            if type(payload.destination_id) is not str or type(payload.direction) is not int:
                raise ValueError("INVALID_COMMAND")
            return {"destination_id": payload.destination_id, "direction": payload.direction}
        if type(payload) is TravelPatch and isinstance(payload, TravelPatch):
            return {"state": encode_travel(payload.state)}
        if type(payload) is TravelDelta and isinstance(payload, TravelDelta):
            return {
                "entity_id": payload.entity_id,
                "before": encode_travel(payload.before),
                "after": encode_travel(payload.after),
            }
        if type(payload) in (Walked, WalkCue) and isinstance(payload, (Walked, WalkCue)):
            return {
                "actor_id": payload.actor_id,
                "before": encode_travel(payload.before),
                "after": encode_travel(payload.after),
            }
        raise SchemaError("UNSUPPORTED_SCHEMA", "world payload class")

    def decode(self, data: JsonObject) -> FrozenPayload:
        payload: FrozenPayload
        if self.schema == Footstep.SCHEMA:
            d = exact_fields(data, ("destination_id", "direction"))
            payload = Footstep(text_value(d["destination_id"]), int_value(d["direction"]))
        elif self.schema == TravelPatch.SCHEMA:
            d = exact_fields(data, ("state",))
            payload = TravelPatch(decode_travel(object_value(d["state"])))
        elif self.schema in (TravelDelta.SCHEMA, Walked.SCHEMA, WalkCue.SCHEMA):
            owner = "entity_id" if self.schema == TravelDelta.SCHEMA else "actor_id"
            d = exact_fields(data, (owner, "before", "after"))
            cls = (
                TravelDelta
                if self.schema == TravelDelta.SCHEMA
                else Walked
                if self.schema == Walked.SCHEMA
                else WalkCue
            )
            payload = cls(
                EntityId(text_value(d[owner])),
                decode_travel(object_value(d["before"])),
                decode_travel(object_value(d["after"])),
            )
        else:
            raise SchemaError("UNSUPPORTED_SCHEMA", "world payload schema")
        self.encode(payload)
        return payload


class TravelerCodec:
    def __init__(self, world: WorldCatalog) -> None:
        self.adapter = TravelerAdapter(world)

    @property
    def schema(self) -> TypeKey:
        return TRAVEL_SCHEMA

    def encode(self, record: ComponentRecord) -> JsonObject:
        self.adapter.validate(record)
        if not isinstance(record, TravelerRecord):
            raise ValueError("WORLD_TRAVEL_RECORD")
        return {"state": encode_travel(record.state)}

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        row = exact_fields(fields, ("state",))
        record = TravelerRecord(entity_id, decode_travel(object_value(row["state"])))
        self.adapter.validate(record)
        return record


class TravelPatchRoute:
    schema = TravelPatch.SCHEMA
    component_schema = TRAVEL_SCHEMA
    family = TRAVEL_FAMILY

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        if (
            type(before) is not TravelerRecord
            or not isinstance(before, TravelerRecord)
            or type(patch) is not TravelPatch
            or not isinstance(patch, TravelPatch)
        ):
            raise ValueError("WORLD_TRAVEL_PATCH")
        return replace(before, state=patch.state)


class WorldCheckpointPolicy:
    def __init__(self, world: WorldCatalog) -> None:
        self.adapter = TravelerAdapter(world)
        self.seed_hex = world.seed_hex

    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        if len(core.components) != 1 or core.world_seed_hex != self.seed_hex or core.pending:
            raise ValueError("WORLD_CHECKPOINT")
        self.adapter.validate(core.components[0])
        if any(s.actor_id != WORLD_ACTOR for s in protocol.streams):
            raise ValueError("WORLD_TRAVEL_ACTOR")


class WalkPresenter:
    def map(
        self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt, committed: ReadPort
    ) -> tuple[PresentationEvent, ...]:
        cues: list[PresentationEvent] = []
        for event in facts:
            if type(event.payload) is not Walked or not isinstance(event.payload, Walked):
                raise SchemaError("UNSUPPORTED_SCHEMA", "world presenter")
            payload = event.payload
            if committed.component(TRAVELER, payload.actor_id).state != payload.after:
                raise ValueError("WORLD_PRESENTATION_STATE")
            identifier = (
                "p1-"
                + hashlib.sha256(
                    pack(
                        (
                            "cue-id/v1",
                            event.header.event_id,
                            "world.presenter",
                            str(len(cues)),
                        )
                    )
                ).hexdigest()
            )
            cue = WalkCue(payload.actor_id, payload.before, payload.after)
            header = EventHeader(
                EventId(identifier),
                cue.schema,
                "world.presenter",
                receipt.tick,
                Phase.PRESENT,
                0,
                0,
                len(cues),
                (event.header.event_id,),
                (),
            )
            cues.append(PresentationEvent(header, cue, "important", "keep_all", ""))
        return tuple(cues)
