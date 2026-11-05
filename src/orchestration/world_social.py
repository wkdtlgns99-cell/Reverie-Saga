"""Strict social persistence,admission/access gates and COMMIT staging."""

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
from contracts.world_social import (
    SOCIAL,
    SOCIAL_FAMILY,
    SOCIAL_OWNER,
    SocialAction,
    SocialDelta,
    SocialPatch,
    SocialRead,
)
from contracts.world_supply import SupplyAction
from contracts.world_travel import TRAVELER, TRAVEL_FAMILY, Footstep
from domain.canonical import (
    JsonObject,
    array_value,
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
from domain.world_social import (
    HOSTILE_THRESHOLD,
    SOCIAL_DURATIONS,
    SOCIAL_SCHEMA,
    SocialCatalog,
    SocialRecord,
    SocialState,
    reaction,
    social_action,
    validate_social,
)
from domain.world_supply import SupplyRecord, SupplyScenario
from domain.world_travel import WORLD_ACTOR
from orchestration.world_conversation import ConversationCheckpointPolicy
from orchestration.world_population import _StateView


class SocialStateCodec:
    def __init__(self, catalog: SocialCatalog) -> None:
        self.catalog = catalog

    def encode(self, state: SocialState) -> JsonObject:
        validate_social(state, self.catalog)
        return object_value(seal(asdict(state)))

    def decode(self, data: JsonObject) -> SocialState:
        row = exact_fields(data, ("ancestry_id", "country_id", "reputation", "credited_places"))
        reputation = []
        for raw in array_value(row["reputation"]):
            entry = array_value(raw)
            if len(entry) != 2:
                raise ValueError("SOCIAL_REPUTATION")
            reputation.append((text_value(entry[0]), int_value(entry[1])))
        state = SocialState(
            text_value(row["ancestry_id"]),
            text_value(row["country_id"]),
            tuple(reputation),
            tuple(text_value(p) for p in array_value(row["credited_places"])),
        )
        validate_social(state, self.catalog)
        return state


class SocialAdapter:
    key = SOCIAL

    def __init__(self, catalog: SocialCatalog) -> None:
        self.codec = SocialStateCodec(catalog)

    def validate(self, record: ComponentRecord) -> None:
        if (
            type(record) is not SocialRecord
            or not isinstance(record, SocialRecord)
            or type(record.entity_id) is not str
            or record.entity_id != WORLD_ACTOR
        ):
            raise ValueError("SOCIAL_RECORD")
        self.codec.encode(record.state)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> SocialRead:
        self.validate(record)
        if not isinstance(record, SocialRecord):
            raise ValueError("SOCIAL_RECORD")
        return _StateView(record.state, SOCIAL_FAMILY, record.entity_id, access)


class SocialCodec:
    schema = SOCIAL_SCHEMA

    def __init__(self, catalog: SocialCatalog) -> None:
        self.adapter = SocialAdapter(catalog)

    def encode(self, record: ComponentRecord) -> JsonObject:
        self.adapter.validate(record)
        if not isinstance(record, SocialRecord):
            raise ValueError("SOCIAL_RECORD")
        return {"state": self.adapter.codec.encode(record.state)}

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        row = exact_fields(fields, ("state",))
        record = SocialRecord(entity_id, self.adapter.codec.decode(object_value(row["state"])))
        self.adapter.validate(record)
        return record


class SocialAdmission:
    schema = SocialAction.SCHEMA
    reads = (SOCIAL_FAMILY, TRAVEL_FAMILY)

    def __init__(self, catalog: SocialCatalog) -> None:
        self.catalog = catalog

    def admit(
        self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str
    ) -> AdmissionOutcome:
        if command.actor_id != WORLD_ACTOR:
            return TurnRejected(failure("UNAUTHORIZED_ACTOR"), command.expected_revision)
        payload = command.payload
        if type(payload) is not SocialAction or not isinstance(payload, SocialAction):
            return TurnRejected(failure("INVALID_COMMAND"), command.expected_revision)
        travel = state.component(TRAVELER, WORLD_ACTOR).state
        if travel.destination_id:
            return TurnRejected(failure("SOCIAL_OUT_OF_REACH"), command.expected_revision)
        try:
            social_action(
                state.component(SOCIAL, WORLD_ACTOR).state,
                self.catalog,
                travel.place_id,
                payload.operation,
                payload.ancestry_id,
                payload.country_id,
            )
        except ValueError as error:
            if str(error) not in (
                "INVALID_COMMAND",
                "SOCIAL_IDENTITY",
                "SOCIAL_IDENTITY_LOCKED",
                "SOCIAL_NOTHING_TO_REPAIR",
            ):
                raise
            return TurnRejected(failure(str(error)), command.expected_revision)
        target = Tick(start_tick + SOCIAL_DURATIONS[payload.operation])
        key = (
            "a1-"
            + hashlib.sha256(pack(("world-social/v1", world_id, command.command_id))).hexdigest()
        )
        return AdmittedCommand(
            TurnPlan(command, start_tick, target), AdmittedAction(command.actor_id, payload, key)
        )


class SocialGate:
    def __init__(self, inner: CommandRoute, catalog: SocialCatalog) -> None:
        self.inner, self.catalog = inner, catalog
        self.schema = inner.schema
        self.reads = tuple(dict.fromkeys((*inner.reads, SOCIAL_FAMILY, TRAVEL_FAMILY)))

    def admit(
        self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str
    ) -> AdmissionOutcome:
        outcome = self.inner.admit(command, state, start_tick=start_tick, world_id=world_id)
        if not isinstance(outcome, AdmittedCommand):
            return outcome
        payload = command.payload
        place = code = ""
        if type(payload) is Footstep and isinstance(payload, Footstep):
            if (
                payload.direction == 1
                and not state.component(TRAVELER, WORLD_ACTOR).state.destination_id
            ):
                place, code = payload.destination_id, "SOCIAL_ENTRY_DENIED"
        elif (
            type(payload) is SupplyAction
            and isinstance(payload, SupplyAction)
            and payload.operation == "accept"
        ):
            place, code = payload.place_id, "SOCIAL_CONTRACT_DENIED"
        if (
            place
            and reaction(state.component(SOCIAL, WORLD_ACTOR).state, self.catalog, place)
            <= HOSTILE_THRESHOLD
        ):
            return TurnRejected(failure(code), command.expected_revision)
        return outcome


class SocialPayloadCodec:
    def __init__(self, schema: TypeKey, catalog: SocialCatalog) -> None:
        self._schema, self.state_codec = schema, SocialStateCodec(catalog)

    @property
    def schema(self) -> TypeKey:
        return self._schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if payload.schema != self.schema:
            raise SchemaError("UNSUPPORTED_SCHEMA", "social payload")
        if type(payload) is SocialAction and isinstance(payload, SocialAction):
            if any(
                type(v) is not str
                for v in (payload.operation, payload.ancestry_id, payload.country_id)
            ):
                raise ValueError("INVALID_COMMAND")
            return object_value(seal(asdict(payload)))
        if type(payload) is SocialPatch and isinstance(payload, SocialPatch):
            return {"state": self.state_codec.encode(payload.state)}
        if type(payload) is SocialDelta and isinstance(payload, SocialDelta):
            if payload.entity_id != WORLD_ACTOR or type(payload.entity_id) is not str:
                raise ValueError("SOCIAL_RECORD")
            return {
                "entity_id": payload.entity_id,
                "before": self.state_codec.encode(payload.before),
                "after": self.state_codec.encode(payload.after),
            }
        raise SchemaError("UNSUPPORTED_SCHEMA", "social payload class")

    def decode(self, data: JsonObject) -> FrozenPayload:
        result: FrozenPayload
        if self.schema == SocialAction.SCHEMA:
            row = exact_fields(data, ("operation", "ancestry_id", "country_id"))
            result = SocialAction(
                *(text_value(row[k]) for k in ("operation", "ancestry_id", "country_id"))
            )
        elif self.schema == SocialPatch.SCHEMA:
            result = SocialPatch(
                self.state_codec.decode(object_value(exact_fields(data, ("state",))["state"]))
            )
        elif self.schema == SocialDelta.SCHEMA:
            row = exact_fields(data, ("entity_id", "before", "after"))
            result = SocialDelta(
                EntityId(text_value(row["entity_id"])),
                self.state_codec.decode(object_value(row["before"])),
                self.state_codec.decode(object_value(row["after"])),
            )
        else:
            raise SchemaError("UNSUPPORTED_SCHEMA", "social payload schema")
        self.encode(result)
        return result


class SocialReducer:
    schema = SocialDelta.SCHEMA
    owner_id = SOCIAL_OWNER

    def __init__(self, catalog: SocialCatalog) -> None:
        self.codec = SocialPayloadCodec(self.schema, catalog)

    def _delta(self, delta: StateDelta) -> SocialDelta:
        if type(delta) is not SocialDelta or not isinstance(delta, SocialDelta):
            raise CandidateError("INVALID_DELTA", "social class")
        self.codec.encode(delta)
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._delta(delta)
        if before.component(SOCIAL, value.entity_id).state != value.before:
            raise CandidateError("INVALID_DELTA", "social before mismatch")
        editor.apply_patch(
            ComponentAddress(SOCIAL_SCHEMA, value.entity_id), SocialPatch(value.after)
        )

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "empty social composition")
        values = tuple(self._delta(d) for d in changes)
        for first, second in zip(values, values[1:]):
            if first.entity_id != second.entity_id or first.after != second.before:
                raise CandidateError("INVALID_DELTA", "noncontiguous social composition")
        return replace(values[0], after=values[-1].after)

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._delta(delta)
        return value.before == value.after

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._delta(delta)
        if after.component(SOCIAL, value.entity_id).state != value.after:
            raise CandidateError("INVALID_DELTA", "social net mismatch")


class SocialPatchRoute:
    schema = SocialPatch.SCHEMA
    component_schema = SOCIAL_SCHEMA
    family = SOCIAL_FAMILY

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        if (
            type(before) is not SocialRecord
            or not isinstance(before, SocialRecord)
            or type(patch) is not SocialPatch
            or not isinstance(patch, SocialPatch)
        ):
            raise ValueError("SOCIAL_PATCH")
        return replace(before, state=patch.state)


class SocialCheckpointPolicy:
    def __init__(
        self, world: WorldCatalog, scenario: SupplyScenario, catalog: SocialCatalog
    ) -> None:
        self.base = ConversationCheckpointPolicy(world, scenario)
        self.adapter = SocialAdapter(catalog)

    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        records = tuple(c for c in core.components if isinstance(c, SocialRecord))
        if len(records) != 1:
            raise ValueError("SOCIAL_CHECKPOINT")
        self.adapter.validate(records[0])
        self.base.validate(
            replace(
                core,
                components=tuple(c for c in core.components if not isinstance(c, SocialRecord)),
            ),
            protocol,
        )
        completed = tuple(
            sorted(
                c.entity_id
                for c in core.components
                if isinstance(c, SupplyRecord) and c.state.stage == 2
            )
        )
        if records[0].state.credited_places != completed:
            raise ValueError("SOCIAL_DELIVERY_BINDING")
