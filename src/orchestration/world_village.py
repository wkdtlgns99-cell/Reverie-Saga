"""Admit, serialize and stage a local position through the registered pipeline."""

from dataclasses import replace
import hashlib

from contracts.errors import CandidateError, SchemaError
from contracts.messages import StateDelta
from contracts.read_views import ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.state_io import CheckpointPolicy
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
from contracts.world_travel import TRAVELER, TRAVEL_FAMILY
from contracts.world_village import (
    VILLAGE,
    VILLAGE_FAMILY,
    VILLAGE_OWNER,
    VillageDelta,
    VillagePatch,
    VillageRead,
    VillageStep,
)
from domain.canonical import JsonObject, exact_fields, int_value, object_value, pack, text_value
from domain.primitives import ComponentAddress, EntityId, FrozenPayload, Tick, TypeKey
from domain.state_types import ComponentRecord, CoreSnapshot
from domain.world_travel import WORLD_ACTOR
from domain.world_village import (
    DIRECTIONS,
    STEP_SECONDS,
    VILLAGE_SCHEMA,
    VillagePosition,
    VillageRecord,
    step,
)
from orchestration.world_population import _StateView


def _encode(position: VillagePosition) -> JsonObject:
    if type(position) is not VillagePosition:
        raise ValueError("VILLAGE_POSITION")
    VillagePosition(position.x, position.y)
    return {"x": position.x, "y": position.y}


def _decode(document: JsonObject) -> VillagePosition:
    row = exact_fields(document, ("x", "y"))
    return VillagePosition(int_value(row["x"]), int_value(row["y"]))


class VillageAdapter:
    key = VILLAGE

    def validate(self, record: ComponentRecord) -> None:
        if type(record) is not VillageRecord or record.entity_id != WORLD_ACTOR:
            raise ValueError("VILLAGE_RECORD")
        _encode(record.state)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> VillageRead:
        self.validate(record)
        if not isinstance(record, VillageRecord):
            raise ValueError("VILLAGE_RECORD")
        return _StateView(record.state, VILLAGE_FAMILY, record.entity_id, access)


class VillageCodec:
    schema = VILLAGE_SCHEMA

    def encode(self, record: ComponentRecord) -> JsonObject:
        VillageAdapter().validate(record)
        if not isinstance(record, VillageRecord):
            raise ValueError("VILLAGE_RECORD")
        return {"state": _encode(record.state)}

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        state = _decode(object_value(exact_fields(fields, ("state",))["state"]))
        record = VillageRecord(entity_id, state)
        VillageAdapter().validate(record)
        return record


class VillagePayloadCodec:
    def __init__(self, schema: TypeKey) -> None:
        self.schema = schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if payload.schema == self.schema:
            if type(payload) is VillageStep:
                return {"direction": text_value(payload.direction)}
            if type(payload) is VillagePatch:
                return {"state": _encode(payload.state)}
            if type(payload) is VillageDelta and payload.entity_id == WORLD_ACTOR:
                return {
                    "entity_id": payload.entity_id,
                    "before": _encode(payload.before),
                    "after": _encode(payload.after),
                }
        raise SchemaError("UNSUPPORTED_SCHEMA", "village payload")

    def decode(self, document: JsonObject) -> FrozenPayload:
        result: FrozenPayload
        if self.schema == VillageStep.SCHEMA:
            result = VillageStep(text_value(exact_fields(document, ("direction",))["direction"]))
        elif self.schema == VillagePatch.SCHEMA:
            result = VillagePatch(
                _decode(object_value(exact_fields(document, ("state",))["state"]))
            )
        elif self.schema == VillageDelta.SCHEMA:
            row = exact_fields(document, ("entity_id", "before", "after"))
            result = VillageDelta(
                EntityId(text_value(row["entity_id"])),
                _decode(object_value(row["before"])),
                _decode(object_value(row["after"])),
            )
        else:
            raise SchemaError("UNSUPPORTED_SCHEMA", "village payload")
        self.encode(result)
        return result


class VillageAdmission:
    schema = VillageStep.SCHEMA
    reads = (TRAVEL_FAMILY, VILLAGE_FAMILY)

    def __init__(self, place_id: str) -> None:
        self.place_id = place_id

    def admit(
        self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str
    ) -> AdmissionOutcome:
        if command.actor_id != WORLD_ACTOR:
            return TurnRejected(failure("UNAUTHORIZED_ACTOR"), command.expected_revision)
        travel = state.component(TRAVELER, WORLD_ACTOR).state
        if travel.place_id != self.place_id or travel.destination_id:
            return TurnRejected(failure("VILLAGE_OUT_OF_REACH"), command.expected_revision)
        payload = command.payload
        if type(payload) is not VillageStep:
            return TurnRejected(failure("INVALID_COMMAND"), command.expected_revision)
        try:
            step(state.component(VILLAGE, WORLD_ACTOR).state, payload.direction)
        except ValueError as error:
            if str(error) not in ("VILLAGE_BLOCKED", "INVALID_COMMAND"):
                raise
            return TurnRejected(failure(str(error)), command.expected_revision)
        key = (
            "a1-"
            + hashlib.sha256(pack(("village-step/v1", world_id, command.command_id))).hexdigest()
        )
        return AdmittedCommand(
            TurnPlan(command, start_tick, Tick(start_tick + STEP_SECONDS)),
            AdmittedAction(command.actor_id, payload, key),
        )


class VillageReducer:
    schema = VillageDelta.SCHEMA
    owner_id = VILLAGE_OWNER

    def _delta(self, delta: StateDelta) -> VillageDelta:
        if type(delta) is not VillageDelta or delta.entity_id != WORLD_ACTOR:
            raise CandidateError("INVALID_DELTA", "village delta")
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._delta(delta)
        dx, dy = value.after.x - value.before.x, value.after.y - value.before.y
        direction = next((key for key, offset in DIRECTIONS.items() if offset == (dx, dy)), None)
        if (
            direction is None
            or before.component(VILLAGE, value.entity_id).state != value.before
            or step(value.before, direction) != value.after
        ):
            raise CandidateError("INVALID_DELTA", "village step")
        editor.apply_patch(
            ComponentAddress(VILLAGE_SCHEMA, value.entity_id), VillagePatch(value.after)
        )

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if len(changes) != 1:
            raise CandidateError("INVALID_DELTA", "one village step per command")
        return self._delta(changes[0])

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._delta(delta)
        return value.before == value.after

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._delta(delta)
        if (
            self.is_identity(value)
            or after.component(VILLAGE, value.entity_id).state != value.after
        ):
            raise CandidateError("INVALID_DELTA", "village after")


class VillagePatchRoute:
    schema = VillagePatch.SCHEMA
    component_schema = VILLAGE_SCHEMA
    family = VILLAGE_FAMILY

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        if type(before) is not VillageRecord or type(patch) is not VillagePatch:
            raise ValueError("VILLAGE_PATCH")
        return replace(before, state=patch.state)


class VillageCheckpointPolicy:
    def __init__(self, base: CheckpointPolicy) -> None:
        self.base = base

    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        positions = tuple(record for record in core.components if isinstance(record, VillageRecord))
        if len(positions) != 1:
            raise ValueError("VILLAGE_CHECKPOINT")
        VillageAdapter().validate(positions[0])
        self.base.validate(
            replace(
                core,
                components=tuple(
                    record for record in core.components if record is not positions[0]
                ),
            ),
            protocol,
        )
