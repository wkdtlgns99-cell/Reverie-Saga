"""Observed,strict supply processing watermark and its single-owner COMMIT delta."""

from dataclasses import replace

from contracts.errors import CandidateError, SchemaError
from contracts.messages import StateDelta
from contracts.read_views import ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.world_transport import (
    PROGRESS_OWNER,
    SUPPLY_PROGRESS,
    SUPPLY_PROGRESS_FAMILY,
    SupplyProgressDelta,
    SupplyProgressPatch,
    SupplyProgressRead,
)
from domain.canonical import JsonObject, exact_fields, int_value, text_value
from domain.primitives import ComponentAddress, EntityId, FrozenPayload, TypeKey, require_integer
from domain.state_types import ComponentRecord
from domain.world_transport import SUPPLY_PROGRESS_SCHEMA, SupplyProgressRecord
from domain.world_travel import WORLD_ACTOR
from orchestration.world_population import _StateView


class SupplyProgressAdapter:
    key = SUPPLY_PROGRESS

    def validate(self, record: ComponentRecord) -> None:
        if (
            type(record) is not SupplyProgressRecord
            or not isinstance(record, SupplyProgressRecord)
            or type(record.entity_id) is not str
            or record.entity_id != WORLD_ACTOR
        ):
            raise ValueError("SUPPLY_PROGRESS_RECORD")
        require_integer(record.state)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> SupplyProgressRead:
        self.validate(record)
        if not isinstance(record, SupplyProgressRecord):
            raise ValueError("SUPPLY_PROGRESS_RECORD")
        return _StateView(record.state, SUPPLY_PROGRESS_FAMILY, record.entity_id, access)


class SupplyProgressCodec:
    schema = SUPPLY_PROGRESS_SCHEMA

    def encode(self, record: ComponentRecord) -> JsonObject:
        SupplyProgressAdapter().validate(record)
        if not isinstance(record, SupplyProgressRecord):
            raise ValueError("SUPPLY_PROGRESS_RECORD")
        return {"state": record.state}

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        record = SupplyProgressRecord(
            entity_id, int_value(exact_fields(fields, ("state",))["state"])
        )
        self.encode(record)
        return record


class SupplyProgressPayloadCodec:
    def __init__(self, schema: TypeKey) -> None:
        self._schema = schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if payload.schema != self.schema:
            raise SchemaError("UNSUPPORTED_SCHEMA", "supply progress payload")
        if type(payload) is SupplyProgressPatch and isinstance(payload, SupplyProgressPatch):
            require_integer(payload.state)
            return {"state": payload.state}
        if type(payload) is SupplyProgressDelta and isinstance(payload, SupplyProgressDelta):
            if type(payload.entity_id) is not str or payload.entity_id != WORLD_ACTOR:
                raise ValueError("SUPPLY_PROGRESS_RECORD")
            require_integer(payload.before)
            require_integer(payload.after, payload.before)
            return {
                "entity_id": payload.entity_id,
                "before": payload.before,
                "after": payload.after,
            }
        raise SchemaError("UNSUPPORTED_SCHEMA", "supply progress class")

    def decode(self, data: JsonObject) -> FrozenPayload:
        result: FrozenPayload
        if self.schema == SupplyProgressPatch.SCHEMA:
            result = SupplyProgressPatch(int_value(exact_fields(data, ("state",))["state"]))
        elif self.schema == SupplyProgressDelta.SCHEMA:
            row = exact_fields(data, ("entity_id", "before", "after"))
            result = SupplyProgressDelta(
                EntityId(text_value(row["entity_id"])),
                int_value(row["before"]),
                int_value(row["after"]),
            )
        else:
            raise SchemaError("UNSUPPORTED_SCHEMA", "supply progress schema")
        self.encode(result)
        return result


class SupplyProgressReducer:
    schema = SupplyProgressDelta.SCHEMA
    owner_id = PROGRESS_OWNER

    def _delta(self, delta: StateDelta) -> SupplyProgressDelta:
        if type(delta) is not SupplyProgressDelta or not isinstance(delta, SupplyProgressDelta):
            raise CandidateError("INVALID_DELTA", "supply progress class")
        SupplyProgressPayloadCodec(self.schema).encode(delta)
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._delta(delta)
        if before.component(SUPPLY_PROGRESS, value.entity_id).state != value.before:
            raise CandidateError("INVALID_DELTA", "supply progress before")
        editor.apply_patch(
            ComponentAddress(SUPPLY_PROGRESS_SCHEMA, value.entity_id),
            SupplyProgressPatch(value.after),
        )

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "empty supply progress composition")
        values = tuple(self._delta(d) for d in changes)
        for first, second in zip(values, values[1:]):
            if first.entity_id != second.entity_id or first.after != second.before:
                raise CandidateError("INVALID_DELTA", "noncontiguous supply progress")
        return replace(values[0], after=values[-1].after)

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._delta(delta)
        return value.before == value.after

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._delta(delta)
        if after.component(SUPPLY_PROGRESS, value.entity_id).state != value.after:
            raise CandidateError("INVALID_DELTA", "supply progress after")


class SupplyProgressPatchRoute:
    schema = SupplyProgressPatch.SCHEMA
    component_schema = SUPPLY_PROGRESS_SCHEMA
    family = SUPPLY_PROGRESS_FAMILY

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        if (
            type(before) is not SupplyProgressRecord
            or not isinstance(before, SupplyProgressRecord)
            or type(patch) is not SupplyProgressPatch
            or not isinstance(patch, SupplyProgressPatch)
        ):
            raise ValueError("SUPPLY_PROGRESS_PATCH")
        return replace(before, state=patch.state)
