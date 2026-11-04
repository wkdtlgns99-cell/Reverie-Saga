"""Authoritative on-foot route progress,independent of presentation and IO."""

from dataclasses import dataclass

from domain.primitives import EntityId, TypeKey, require_integer
from domain.state_types import ComponentRecord
from domain.world import WorldCatalog

TRAVEL_SCHEMA = TypeKey("world.traveler", 1)
WORLD_ACTOR = EntityId("actor:world-player")


@dataclass(frozen=True, slots=True)
class TravelState:
    place_id: str
    destination_id: str
    offset_m: int
    visited: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.place_id) is not str or type(self.destination_id) is not str:
            raise ValueError("WORLD_TRAVEL_PLACE")
        require_integer(self.offset_m, 0, 100_000_000)
        if (
            type(self.visited) is not tuple
            or not 1 <= len(self.visited) <= 256
            or any(type(p) is not str for p in self.visited)
            or self.visited != tuple(sorted(set(self.visited)))
            or self.place_id not in self.visited
        ):
            raise ValueError("WORLD_VISITED")
        if bool(self.destination_id) != bool(self.offset_m):
            raise ValueError("WORLD_TRAVEL_OFFSET")


@dataclass(frozen=True, slots=True)
class TravelerRecord(ComponentRecord):
    entity_id: EntityId
    state: TravelState

    @property
    def schema(self) -> TypeKey:
        return TRAVEL_SCHEMA


def validate_traveler(world: WorldCatalog, state: TravelState) -> None:
    if type(state) is not TravelState:
        raise ValueError("WORLD_TRAVEL_STATE")
    TravelState(state.place_id, state.destination_id, state.offset_m, state.visited)
    for identifier in state.visited:
        world.place(identifier)
    if state.destination_id:
        routes = tuple(
            r for p, r in world.neighbors(state.place_id) if p.id == state.destination_id
        )
        if not routes or routes[0].kind != "road" or state.offset_m >= routes[0].distance_km * 1000:
            raise ValueError("WORLD_TRAVEL_ROUTE")


def footstep(
    world: WorldCatalog, before: TravelState, destination: str, direction: int
) -> TravelState:
    validate_traveler(world, before)
    if type(destination) is not str or type(direction) is not int or direction not in (-1, 1):
        raise ValueError("INVALID_COMMAND")
    if before.destination_id and destination != before.destination_id:
        raise ValueError("WORLD_ROUTE_ACTIVE")
    if not before.destination_id and direction != 1:
        raise ValueError("WORLD_NOT_ON_ROUTE")
    routes = tuple(r for p, r in world.neighbors(before.place_id) if p.id == destination)
    if not routes:
        raise ValueError("WORLD_NOT_ADJACENT")
    route = routes[0]
    if route.kind != "road":
        raise ValueError("TRANSPORT_REQUIRED")
    offset = before.offset_m + direction
    if offset == 0:
        return TravelState(before.place_id, "", 0, before.visited)
    if offset == route.distance_km * 1000:
        return TravelState(destination, "", 0, tuple(sorted(set((*before.visited, destination)))))
    return TravelState(before.place_id, destination, offset, before.visited)
