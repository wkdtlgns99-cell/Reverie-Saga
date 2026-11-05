"""Journey commands and field ownership for the isolated transport profile."""

from dataclasses import dataclass
from typing import Protocol

from contracts.messages import CommandPayload, StateDelta
from contracts.read_views import ComponentKey, ComponentPatch
from contracts.world_supply import SUPPLY_OWNER
from contracts.world_travel import TRAVEL_FAMILY, TRAVEL_OWNER
from domain.primitives import EntityId, FieldAddress, FieldFamily, TypeKey
from domain.world_transport import JOURNEY_SCHEMA, SUPPLY_PROGRESS_SCHEMA, JourneyState
from domain.world_travel import TravelState

JOURNEY_FAMILY = FieldFamily(JOURNEY_SCHEMA.kind, "state")
SUPPLY_PROGRESS_FAMILY = FieldFamily(SUPPLY_PROGRESS_SCHEMA.kind, "state")


class JourneyRead(Protocol):
    @property
    def state(self) -> JourneyState: ...


class SupplyProgressRead(Protocol):
    @property
    def state(self) -> int: ...


JOURNEY = ComponentKey[JourneyRead](JOURNEY_SCHEMA)
SUPPLY_PROGRESS = ComponentKey[SupplyProgressRead](SUPPLY_PROGRESS_SCHEMA)


@dataclass(frozen=True, slots=True)
class TransportAction(CommandPayload):
    operation: str
    destination_id: str = ""
    duration_seconds: int = 1
    SCHEMA = TypeKey("world.transport-action", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class JourneyDelta(StateDelta):
    entity_id: EntityId
    before: JourneyState
    after: JourneyState
    SCHEMA = TypeKey("world.journey-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(JOURNEY_FAMILY, self.entity_id)


@dataclass(frozen=True, slots=True)
class JourneyPatch(ComponentPatch):
    state: JourneyState
    SCHEMA = TypeKey("world.journey-patch", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class SupplyProgressDelta(StateDelta):
    entity_id: EntityId
    before: int
    after: int
    SCHEMA = TypeKey("world.supply-progress-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(SUPPLY_PROGRESS_FAMILY, self.entity_id)


@dataclass(frozen=True, slots=True)
class SupplyProgressPatch(ComponentPatch):
    state: int
    SCHEMA = TypeKey("world.supply-progress-patch", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class TransportArrivalDelta(StateDelta):
    entity_id: EntityId
    before: TravelState
    after: TravelState
    SCHEMA = TypeKey("world.transport-arrival-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(TRAVEL_FAMILY, self.entity_id)


TRANSPORT_PAYLOADS = (
    TransportAction,
    JourneyDelta,
    JourneyPatch,
    SupplyProgressDelta,
    SupplyProgressPatch,
    TransportArrivalDelta,
)
# These ownership aliases keep registry/reducer consumers on the canonical owner constants.
JOURNEY_OWNER = TRAVEL_OWNER
PROGRESS_OWNER = SUPPLY_OWNER
