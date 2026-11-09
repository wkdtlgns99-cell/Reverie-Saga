"""Admission, durable codecs and ownership for village combat."""

from dataclasses import replace

from contracts.errors import CandidateError, SchemaError
from contracts.messages import StateDelta
from contracts.read_views import ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.skeleton import CommandRoute
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
from contracts.world_combat import (
    COMBAT,
    COMBAT_FAMILY,
    COMBAT_OWNER,
    CombatAction,
    CombatDelta,
    CombatPatch,
    CombatRead,
)
from contracts.world_conversation import CONVERSATION_FAMILY, KNOWLEDGE
from contracts.world_population import SETTLEMENT, SETTLEMENT_FAMILY
from contracts.world_transport import JOURNEY, JOURNEY_FAMILY
from contracts.world_travel import TRAVELER, TRAVEL_FAMILY
from contracts.world_village import VILLAGE, VILLAGE_FAMILY
from domain.canonical import JsonObject, array_value, exact_fields, hash_document, int_value
from domain.canonical import object_value, text_value
from domain.primitives import ComponentAddress, EntityId, FrozenPayload, Tick, TypeKey
from domain.state_types import ComponentRecord, CoreSnapshot
from domain.world_combat import (
    ACTION_SECONDS,
    COMBAT_SCHEMA,
    CombatRecord,
    CombatState,
    can_attack,
)
from domain.world_travel import WORLD_ACTOR
from orchestration.world_population import _StateView


def _encode(state: CombatState) -> JsonObject:
    return {
        "order": state.order,
        "player_hp": state.player_hp,
        "bandit_hp": state.bandit_hp,
        "last_actor": state.last_actor,
        "last_action": state.last_action,
    }


def _decode(document: JsonObject) -> CombatState:
    row = exact_fields(document, ("order", "player_hp", "bandit_hp", "last_actor", "last_action"))
    return CombatState(
        tuple(EntityId(text_value(actor)) for actor in array_value(row["order"])),
        int_value(row["player_hp"]),
        int_value(row["bandit_hp"]),
        EntityId(text_value(row["last_actor"])),
        text_value(row["last_action"]),
    )


class CombatAdapter:
    key = COMBAT
    schema = COMBAT_SCHEMA

    def validate(self, record: ComponentRecord) -> None:
        if (
            type(record) is not CombatRecord
            or record.entity_id != WORLD_ACTOR
            or type(record.state) is not CombatState
        ):
            raise ValueError("COMBAT_RECORD")

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> CombatRead:
        self.validate(record)
        if not isinstance(record, CombatRecord):
            raise ValueError("COMBAT_RECORD")
        return _StateView(record.state, COMBAT_FAMILY, record.entity_id, access)

    def encode(self, record: ComponentRecord) -> JsonObject:
        self.validate(record)
        if not isinstance(record, CombatRecord):
            raise ValueError("COMBAT_RECORD")
        return {"state": _encode(record.state)}

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        record = CombatRecord(
            entity_id, _decode(object_value(exact_fields(fields, ("state",))["state"]))
        )
        self.validate(record)
        return record


class CombatPayloadCodec:
    def __init__(self, schema: TypeKey) -> None:
        self.schema = schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if payload.schema == self.schema:
            if type(payload) is CombatAction:
                return {"operation": text_value(payload.operation)}
            if type(payload) is CombatPatch:
                return {"state": _encode(payload.state)}
            if type(payload) is CombatDelta:
                return {"before": _encode(payload.before), "after": _encode(payload.after)}
        raise SchemaError("UNSUPPORTED_SCHEMA", "combat payload")

    def decode(self, document: JsonObject) -> FrozenPayload:
        if self.schema == CombatAction.SCHEMA:
            return CombatAction(text_value(exact_fields(document, ("operation",))["operation"]))
        if self.schema == CombatPatch.SCHEMA:
            return CombatPatch(_decode(object_value(exact_fields(document, ("state",))["state"])))
        if self.schema == CombatDelta.SCHEMA:
            row = exact_fields(document, ("before", "after"))
            return CombatDelta(
                _decode(object_value(row["before"])), _decode(object_value(row["after"]))
            )
        raise SchemaError("UNSUPPORTED_SCHEMA", "combat payload")


class CombatGate:
    def __init__(self, inner: CommandRoute, place_id: EntityId) -> None:
        self.inner = inner
        self.place_id = place_id
        self.schema = inner.schema
        self.reads = tuple(
            dict.fromkeys(
                (
                    *inner.reads,
                    COMBAT_FAMILY,
                    VILLAGE_FAMILY,
                    TRAVEL_FAMILY,
                    CONVERSATION_FAMILY,
                    JOURNEY_FAMILY,
                )
            )
        )

    def admit(
        self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str
    ) -> AdmissionOutcome:
        combat = state.component(COMBAT, WORLD_ACTOR).state
        if combat.order:
            return TurnRejected(failure("VILLAGE_COMBAT_ACTIVE"), command.expected_revision)
        if combat.ambush_due(state.component(VILLAGE, WORLD_ACTOR).state):
            travel = state.component(TRAVELER, WORLD_ACTOR).state
            if (
                travel.place_id == self.place_id
                and not travel.destination_id
                and state.component(JOURNEY, WORLD_ACTOR).state.phase == "idle"
                and not state.component(KNOWLEDGE, WORLD_ACTOR).state.remaining
            ):
                return TurnRejected(failure("VILLAGE_AMBUSH_PENDING"), command.expected_revision)
        return self.inner.admit(command, state, start_tick=start_tick, world_id=world_id)


class CombatAdmission:
    schema = CombatAction.SCHEMA
    reads = (COMBAT_FAMILY, VILLAGE_FAMILY, TRAVEL_FAMILY, SETTLEMENT_FAMILY)

    def __init__(self, place_id: EntityId) -> None:
        self.place_id = place_id

    def _rejection(self, command: GameCommand, state: ReadPort) -> str:
        if command.actor_id != WORLD_ACTOR:
            return "UNAUTHORIZED_ACTOR"
        payload = command.payload
        if type(payload) is not CombatAction:
            return "INVALID_COMMAND"
        combat = state.component(COMBAT, WORLD_ACTOR).state
        operation = payload.operation
        if operation == "ambush":
            travel = state.component(TRAVELER, WORLD_ACTOR).state
            position = state.component(VILLAGE, WORLD_ACTOR).state
            local = state.component(SETTLEMENT, self.place_id).state
            if combat.order or combat.resolved:
                return "COMBAT_ALREADY_OPENED"
            if travel.place_id != self.place_id or travel.destination_id or local is None:
                return "VILLAGE_OUT_OF_REACH"
            return "" if combat.ambush_due(position) and can_attack(position) else "OUT_OF_RANGE"
        if operation not in ("advance", "attack", "hold"):
            return "INVALID_COMMAND"
        if not combat.order:
            return "COMBAT_NOT_ACTIVE"
        if (operation == "advance") == (combat.current == WORLD_ACTOR):
            return "COMBAT_WRONG_TURN"
        return ""

    def admit(
        self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str
    ) -> AdmissionOutcome:
        error = self._rejection(command, state)
        if error:
            return TurnRejected(failure(error), command.expected_revision)
        key = "a1-" + hash_document("village-combat-action/v1", (world_id, command.command_id))
        return AdmittedCommand(
            TurnPlan(command, start_tick, Tick(start_tick + ACTION_SECONDS)),
            AdmittedAction(command.actor_id, command.payload, key),
        )


class CombatReducer:
    schema = CombatDelta.SCHEMA
    owner_id = COMBAT_OWNER

    def _delta(self, delta: StateDelta) -> CombatDelta:
        if type(delta) is not CombatDelta:
            raise CandidateError("INVALID_DELTA", "combat delta")
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._delta(delta)
        if before.component(COMBAT, WORLD_ACTOR).state != value.before:
            raise CandidateError("INVALID_DELTA", "combat before")
        editor.apply_patch(ComponentAddress(COMBAT_SCHEMA, WORLD_ACTOR), CombatPatch(value.after))

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if len(changes) != 1:
            raise CandidateError("INVALID_DELTA", "one combat action per command")
        return self._delta(changes[0])

    def is_identity(self, delta: StateDelta) -> bool:
        value = self._delta(delta)
        return value.before == value.after

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        if after.component(COMBAT, WORLD_ACTOR).state != self._delta(delta).after:
            raise CandidateError("INVALID_DELTA", "combat after")


class CombatPatchRoute:
    schema = CombatPatch.SCHEMA
    component_schema = COMBAT_SCHEMA
    family = COMBAT_FAMILY

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        if type(before) is not CombatRecord or type(patch) is not CombatPatch:
            raise ValueError("COMBAT_PATCH")
        return replace(before, state=patch.state)


class CombatCheckpointPolicy:
    def __init__(self, base: CheckpointPolicy) -> None:
        self.base = base

    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        rows = tuple(row for row in core.components if isinstance(row, CombatRecord))
        if len(rows) != 1:
            raise ValueError("COMBAT_CHECKPOINT")
        CombatAdapter().validate(rows[0])
        self.base.validate(
            replace(core, components=tuple(row for row in core.components if row is not rows[0])),
            protocol,
        )
