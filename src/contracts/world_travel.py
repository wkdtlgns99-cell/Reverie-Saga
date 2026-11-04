"""Typed foot commands and same-owner travel state changes."""

from dataclasses import dataclass
from typing import Protocol

from contracts.messages import CommandPayload, FactPayload, PresentationPayload, StateDelta
from contracts.read_views import ComponentKey, ComponentPatch
from domain.primitives import EntityId, FieldAddress, FieldFamily, TypeKey
from domain.world_travel import TRAVEL_SCHEMA, TravelState

TRAVEL_FAMILY = FieldFamily(TRAVEL_SCHEMA.kind, "state")
TRAVEL_OWNER = "world.walk"


class TravelerRead(Protocol):
    @property
    def state(self) -> TravelState: ...


TRAVELER = ComponentKey[TravelerRead](TRAVEL_SCHEMA)


@dataclass(frozen=True, slots=True)
class Footstep(CommandPayload):
    destination_id: str
    direction: int
    SCHEMA = TypeKey("world.footstep", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class TravelDelta(StateDelta):
    entity_id: EntityId
    before: TravelState
    after: TravelState
    SCHEMA = TypeKey("world.travel-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(TRAVEL_FAMILY, self.entity_id)


@dataclass(frozen=True, slots=True)
class TravelPatch(ComponentPatch):
    state: TravelState
    SCHEMA = TypeKey("world.travel-patch", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class Walked(FactPayload):
    actor_id: EntityId
    before: TravelState
    after: TravelState
    SCHEMA = TypeKey("world.walked", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class WalkCue(PresentationPayload):
    actor_id: EntityId
    before: TravelState
    after: TravelState
    SCHEMA = TypeKey("world.walk-cue", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


TRAVEL_PAYLOADS = (Footstep, TravelDelta, TravelPatch, Walked, WalkCue)
