"""Transport admission,strict state IO and single-owner journey staging."""

from dataclasses import asdict, replace
import hashlib

from contracts.errors import CandidateError, SchemaError
from contracts.messages import StateDelta
from contracts.read_views import ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.skeleton import CommandRoute
from contracts.turn import (
    AdmittedAction,
    AdmittedCommand,
    AdmissionOutcome,
    GameCommand,
    ProtocolSnapshot,
    TurnPlan,
    TurnRejected,
    failure,
)
from contracts.world_social import SOCIAL, SOCIAL_FAMILY
from contracts.world_time import WorldWait
from contracts.world_transport import (
    JOURNEY,
    JOURNEY_FAMILY,
    JOURNEY_OWNER,
    JourneyDelta,
    JourneyPatch,
    JourneyRead,
    TransportAction,
    TransportArrivalDelta,
)
from contracts.world_travel import TRAVELER, TRAVEL_FAMILY, TravelPatch
from domain.canonical import (
    JsonObject,
    exact_fields,
    int_value,
    object_value,
    pack,
    seal,
    text_value,
)
from domain.primitives import ComponentAddress, EntityId, FrozenPayload, Tick, TypeKey
from domain.state_types import ComponentRecord, CoreSnapshot
from domain.world import WorldCatalog
from domain.world_social import HOSTILE_THRESHOLD, SocialCatalog, reaction
from domain.world_supply import SupplyScenario
from domain.world_transport import (
    JOURNEY_SCHEMA,
    JourneyRecord,
    JourneyState,
    SupplyProgressRecord,
    TransportRules,
    plan_journey,
    validate_journey,
    validate_journey_binding,
)
from domain.world_travel import TRAVEL_SCHEMA, WORLD_ACTOR, TravelerRecord, validate_traveler
from orchestration.world_population import _StateView
from orchestration.world_social import SocialCheckpointPolicy
from orchestration.world_supply_progress import SupplyProgressAdapter
from orchestration.world_travel import decode_travel, encode_travel

JOURNEY_ERRORS = (
    "INVALID_COMMAND",
    "JOURNEY_ACTIVE",
    "JOURNEY_NOT_ACTIVE",
    "WORLD_ROUTE_ACTIVE",
    "WORLD_NOT_ADJACENT",
    "JOURNEY_BLOCKED",
    "JOURNEY_CLEAR",
    "JOURNEY_NOT_BLOCKED",
    "INTEGER_OVERFLOW",
)


def encode_journey(state: JourneyState) -> JsonObject:
    validate_journey(state)
    return object_value(seal(asdict(state)))


def decode_journey(data: JsonObject) -> JourneyState:
    row = exact_fields(
        data,
        ("origin_id", "destination_id", "mode", "progress_m", "phase", "started_tick", "block_id"),
    )
    state = JourneyState(
        text_value(row["origin_id"]),
        text_value(row["destination_id"]),
        text_value(row["mode"]),
        int_value(row["progress_m"]),
        text_value(row["phase"]),
        int_value(row["started_tick"]),
        text_value(row["block_id"]),
    )
    validate_journey(state)
    return state


class JourneyAdapter:
    key = JOURNEY

    def validate(self, record: ComponentRecord) -> None:
        if (
            type(record) is not JourneyRecord
            or not isinstance(record, JourneyRecord)
            or type(record.entity_id) is not str
            or record.entity_id != WORLD_ACTOR
        ):
            raise ValueError("JOURNEY_RECORD")
        validate_journey(record.state)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> JourneyRead:
        self.validate(record)
        if not isinstance(record, JourneyRecord):
            raise ValueError("JOURNEY_RECORD")
        return _StateView(record.state, JOURNEY_FAMILY, record.entity_id, access)


class JourneyCodec:
    schema = JOURNEY_SCHEMA

    def encode(self, record: ComponentRecord) -> JsonObject:
        JourneyAdapter().validate(record)
        if not isinstance(record, JourneyRecord):
            raise ValueError("JOURNEY_RECORD")
        return {"state": encode_journey(record.state)}

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        record = JourneyRecord(
            entity_id, decode_journey(object_value(exact_fields(fields, ("state",))["state"]))
        )
        self.encode(record)
        return record


class JourneyPayloadCodec:
    def __init__(self, schema: TypeKey) -> None:
        self._schema = schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if payload.schema != self.schema:
            raise SchemaError("UNSUPPORTED_SCHEMA", "journey payload")
        if type(payload) is TransportAction and isinstance(payload, TransportAction):
            if (
                type(payload.operation) is not str
                or type(payload.destination_id) is not str
                or type(payload.duration_seconds) is not int
                or not 1 <= payload.duration_seconds <= 3600
            ):
                raise ValueError("INVALID_COMMAND")
            return object_value(seal(asdict(payload)))
        if type(payload) is JourneyPatch and isinstance(payload, JourneyPatch):
            return {"state": encode_journey(payload.state)}
        if type(payload) is JourneyDelta and isinstance(payload, JourneyDelta):
            if type(payload.entity_id) is not str or payload.entity_id != WORLD_ACTOR:
                raise ValueError("JOURNEY_RECORD")
            return {
                "entity_id": payload.entity_id,
                "before": encode_journey(payload.before),
                "after": encode_journey(payload.after),
            }
        if type(payload) is TransportArrivalDelta and isinstance(payload, TransportArrivalDelta):
            if type(payload.entity_id) is not str or payload.entity_id != WORLD_ACTOR:
                raise ValueError("JOURNEY_RECORD")
            return {
                "entity_id": payload.entity_id,
                "before": encode_travel(payload.before),
                "after": encode_travel(payload.after),
            }
        raise SchemaError("UNSUPPORTED_SCHEMA", "journey payload class")

    def decode(self, data: JsonObject) -> FrozenPayload:
        result: FrozenPayload
        if self.schema == TransportAction.SCHEMA:
            row = exact_fields(data, ("operation", "destination_id", "duration_seconds"))
            result = TransportAction(
                text_value(row["operation"]),
                text_value(row["destination_id"]),
                int_value(row["duration_seconds"]),
            )
        elif self.schema == JourneyPatch.SCHEMA:
            result = JourneyPatch(
                decode_journey(object_value(exact_fields(data, ("state",))["state"]))
            )
        elif self.schema == JourneyDelta.SCHEMA:
            row = exact_fields(data, ("entity_id", "before", "after"))
            result = JourneyDelta(
                EntityId(text_value(row["entity_id"])),
                decode_journey(object_value(row["before"])),
                decode_journey(object_value(row["after"])),
            )
        elif self.schema == TransportArrivalDelta.SCHEMA:
            row = exact_fields(data, ("entity_id", "before", "after"))
            result = TransportArrivalDelta(
                EntityId(text_value(row["entity_id"])),
                decode_travel(object_value(row["before"])),
                decode_travel(object_value(row["after"])),
            )
        else:
            raise SchemaError("UNSUPPORTED_SCHEMA", "journey schema")
        self.encode(result)
        return result


class TransportAdmission:
    schema = TransportAction.SCHEMA
    reads = (JOURNEY_FAMILY, TRAVEL_FAMILY, SOCIAL_FAMILY)

    def __init__(self, world: WorldCatalog, rules: TransportRules, social: SocialCatalog) -> None:
        self.world, self.rules, self.social = world, rules, social

    def admit(
        self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str
    ) -> AdmissionOutcome:
        if command.actor_id != WORLD_ACTOR:
            return TurnRejected(failure("UNAUTHORIZED_ACTOR"), command.expected_revision)
        payload = command.payload
        if (
            type(payload) is not TransportAction
            or not isinstance(payload, TransportAction)
            or type(payload.duration_seconds) is not int
        ):
            return TurnRejected(failure("INVALID_COMMAND"), command.expected_revision)
        travel = state.component(TRAVELER, WORLD_ACTOR).state
        try:
            plan = plan_journey(
                self.world,
                self.rules,
                state.component(JOURNEY, WORLD_ACTOR).state,
                travel,
                start_tick,
                payload.operation,
                payload.destination_id,
            )
        except ValueError as error:
            if str(error) not in JOURNEY_ERRORS:
                raise
            return TurnRejected(failure(str(error)), command.expected_revision)
        code = ""
        if plan.seconds != payload.duration_seconds:
            code = "JOURNEY_DURATION"
        elif payload.operation == "board" or plan.travel.place_id != travel.place_id:
            destination = (
                payload.destination_id if payload.operation == "board" else plan.travel.place_id
            )
            if (
                reaction(state.component(SOCIAL, WORLD_ACTOR).state, self.social, destination)
                <= HOSTILE_THRESHOLD
            ):
                code = "SOCIAL_ENTRY_DENIED"
        if code:
            return TurnRejected(failure(code), command.expected_revision)
        key = (
            "a1-"
            + hashlib.sha256(pack(("world-transport/v1", world_id, command.command_id))).hexdigest()
        )
        return AdmittedCommand(
            TurnPlan(command, start_tick, Tick(start_tick + plan.seconds)),
            AdmittedAction(command.actor_id, payload, key),
        )


class JourneyGate:
    def __init__(self, inner: CommandRoute) -> None:
        self.inner, self.schema = inner, inner.schema
        self.reads = tuple(dict.fromkeys((*inner.reads, JOURNEY_FAMILY)))

    def admit(
        self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str
    ) -> AdmissionOutcome:
        outcome = self.inner.admit(command, state, start_tick=start_tick, world_id=world_id)
        if (
            isinstance(outcome, AdmittedCommand)
            and not isinstance(command.payload, WorldWait)
            and state.component(JOURNEY, WORLD_ACTOR).state.phase != "idle"
        ):
            return TurnRejected(failure("JOURNEY_ACTIVE"), command.expected_revision)
        return outcome


class JourneyReducer:
    schema = JourneyDelta.SCHEMA
    owner_id = JOURNEY_OWNER

    def _delta(self, delta: StateDelta) -> JourneyDelta:
        if type(delta) is not JourneyDelta or not isinstance(delta, JourneyDelta):
            raise CandidateError("INVALID_DELTA", "journey class")
        JourneyPayloadCodec(self.schema).encode(delta)
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._delta(delta)
        if before.component(JOURNEY, value.entity_id).state != value.before:
            raise CandidateError("INVALID_DELTA", "journey before")
        editor.apply_patch(
            ComponentAddress(JOURNEY_SCHEMA, value.entity_id), JourneyPatch(value.after)
        )

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "empty journey composition")
        values = tuple(self._delta(d) for d in changes)
        for first, second in zip(values, values[1:]):
            if first.entity_id != second.entity_id or first.after != second.before:
                raise CandidateError("INVALID_DELTA", "noncontiguous journey composition")
        return replace(values[0], after=values[-1].after)

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._delta(delta)
        return value.before == value.after

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._delta(delta)
        if after.component(JOURNEY, value.entity_id).state != value.after:
            raise CandidateError("INVALID_DELTA", "journey after")


class JourneyPatchRoute:
    schema = JourneyPatch.SCHEMA
    component_schema = JOURNEY_SCHEMA
    family = JOURNEY_FAMILY

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        if (
            type(before) is not JourneyRecord
            or not isinstance(before, JourneyRecord)
            or type(patch) is not JourneyPatch
            or not isinstance(patch, JourneyPatch)
        ):
            raise ValueError("JOURNEY_PATCH")
        return replace(before, state=patch.state)


class TransportArrivalReducer:
    owner_id = JOURNEY_OWNER

    def __init__(self, world: WorldCatalog) -> None:
        self.world = world

    @property
    def schema(self) -> TypeKey:
        return TransportArrivalDelta.SCHEMA

    def _arrival(self, delta: StateDelta) -> TransportArrivalDelta:
        if (
            type(delta) is not TransportArrivalDelta
            or not isinstance(delta, TransportArrivalDelta)
            or type(delta.entity_id) is not str
            or delta.entity_id != WORLD_ACTOR
        ):
            raise CandidateError("INVALID_DELTA", "transport arrival class/actor")
        validate_traveler(self.world, delta.before)
        validate_traveler(self.world, delta.after)
        if (
            delta.before.destination_id
            or delta.after.destination_id
            or delta.before.place_id == delta.after.place_id
            or delta.after.visited
            != tuple(sorted(set((*delta.before.visited, delta.after.place_id))))
            or delta.after.place_id
            not in {p.id for p, _ in self.world.neighbors(delta.before.place_id)}
        ):
            raise CandidateError("INVALID_DELTA", "transport arrival endpoints/visits")
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._arrival(delta)
        if before.component(TRAVELER, value.entity_id).state != value.before:
            raise CandidateError("INVALID_DELTA", "transport arrival before")
        editor.apply_patch(
            ComponentAddress(TRAVEL_SCHEMA, value.entity_id), TravelPatch(value.after)
        )

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if len(changes) != 1:
            raise CandidateError("INVALID_DELTA", "one transport arrival per command")
        return self._arrival(changes[0])

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._arrival(delta)
        return value.before == value.after

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._arrival(delta)
        if after.component(TRAVELER, value.entity_id).state != value.after:
            raise CandidateError("INVALID_DELTA", "transport arrival after")


class TransportCheckpointPolicy:
    def __init__(
        self,
        world: WorldCatalog,
        rules: TransportRules,
        social: SocialCatalog,
        scenario: SupplyScenario,
    ) -> None:
        self.world, self.rules = world, rules
        self.base = SocialCheckpointPolicy(world, scenario, social)

    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        journeys = tuple(c for c in core.components if isinstance(c, JourneyRecord))
        progress = tuple(c for c in core.components if isinstance(c, SupplyProgressRecord))
        if len(journeys) != 1 or len(progress) != 1:
            raise ValueError("TRANSPORT_CHECKPOINT")
        JourneyAdapter().validate(journeys[0])
        SupplyProgressAdapter().validate(progress[0])
        if progress[0].state != core.tick:
            raise ValueError("SUPPLY_PROGRESS_BINDING")
        travel = next(c.state for c in core.components if isinstance(c, TravelerRecord))
        validate_journey_binding(self.world, self.rules, journeys[0].state, travel, core.tick)
        self.base.validate(
            replace(
                core,
                components=tuple(
                    c
                    for c in core.components
                    if not isinstance(c, (JourneyRecord, SupplyProgressRecord))
                ),
            ),
            protocol,
        )
