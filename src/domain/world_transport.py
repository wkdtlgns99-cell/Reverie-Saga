"""Physical time-summary journeys and explicit responses to checkpoint closures."""

from dataclasses import asdict, dataclass, replace
import unicodedata

from domain.canonical import (
    JsonObject,
    array_value,
    exact_fields,
    int_value,
    object_value,
    seal,
    text_value,
)
from domain.primitives import EntityId, MAX_INT, TypeKey, require_integer, require_namespace
from domain.state_types import ComponentRecord
from domain.world import Route, WorldCatalog
from domain.world_travel import TravelState

JOURNEY_SCHEMA = TypeKey("world.journey", 1)
SUPPLY_PROGRESS_SCHEMA = TypeKey("world.supply-progress", 1)


@dataclass(frozen=True, slots=True)
class TransitClosure:
    id: str
    origin_id: str
    destination_id: str
    checkpoint_m: int
    start_tick: int
    end_tick: int
    reason: str


def route_between(world: WorldCatalog, origin: str, destination: str) -> Route:
    for place, route in world.neighbors(origin):
        if place.id == destination:
            return route
    raise ValueError("WORLD_NOT_ADJACENT")


@dataclass(frozen=True, slots=True)
class TransportRules:
    world_seed: str
    carriage_mps: int
    ship_mps: int
    segment_seconds: int
    closures: tuple[TransitClosure, ...]

    def validate(self, world: WorldCatalog) -> None:
        if type(self.world_seed) is not str or self.world_seed != world.seed_hex:
            raise ValueError("TRANSPORT_WORLD_BINDING")
        require_integer(self.carriage_mps, 1, 50)
        require_integer(self.ship_mps, 1, 50)
        require_integer(self.segment_seconds, 1, 3600)
        if (
            type(self.closures) is not tuple
            or len(self.closures) > 32
            or any(type(c) is not TransitClosure for c in self.closures)
        ):
            raise ValueError("TRANSPORT_CLOSURES")
        ids = tuple(c.id for c in self.closures)
        if ids != tuple(sorted(set(ids))):
            raise ValueError("TRANSPORT_CLOSURE_ORDER")
        pairs = []
        for closure in self.closures:
            if any(
                type(v) is not str
                for v in (closure.id, closure.origin_id, closure.destination_id, closure.reason)
            ):
                raise ValueError("TRANSPORT_CLOSURE")
            require_namespace(closure.id)
            if closure.origin_id >= closure.destination_id:
                raise ValueError("TRANSPORT_CLOSURE_ROUTE")
            route = route_between(world, closure.origin_id, closure.destination_id)
            require_integer(closure.checkpoint_m, 1, route.distance_km * 1000 - 1)
            require_integer(closure.start_tick)
            require_integer(closure.end_tick, closure.start_tick + 1)
            if (
                not closure.reason.strip()
                or len(closure.reason) > 256
                or unicodedata.normalize("NFC", closure.reason) != closure.reason
            ):
                raise ValueError("TRANSPORT_CLOSURE_REASON")
            pairs.append((closure.origin_id, closure.destination_id))
        if len(set(pairs)) != len(pairs):
            raise ValueError("TRANSPORT_CLOSURE_DUPLICATE_ROUTE")

    def speed(self, mode: str) -> int:
        if mode not in ("carriage", "ship"):
            raise ValueError("JOURNEY_MODE")
        return self.carriage_mps if mode == "carriage" else self.ship_mps

    def closure(self, origin: str, destination: str) -> TransitClosure | None:
        pair = tuple(sorted((origin, destination)))
        return next((c for c in self.closures if (c.origin_id, c.destination_id) == pair), None)

    def document(self) -> JsonObject:
        return object_value(seal({"format": "reverie-transport/v1", **asdict(self)}))


def decode_transport(document: JsonObject, world: WorldCatalog) -> TransportRules:
    row = exact_fields(
        document,
        ("format", "world_seed", "carriage_mps", "ship_mps", "segment_seconds", "closures"),
    )
    if row["format"] != "reverie-transport/v1":
        raise ValueError("TRANSPORT_FORMAT")
    closures = []
    for raw in array_value(row["closures"]):
        keys = (
            "id",
            "origin_id",
            "destination_id",
            "checkpoint_m",
            "start_tick",
            "end_tick",
            "reason",
        )
        c = exact_fields(raw, keys)
        closures.append(
            TransitClosure(
                text_value(c["id"]),
                text_value(c["origin_id"]),
                text_value(c["destination_id"]),
                int_value(c["checkpoint_m"]),
                int_value(c["start_tick"]),
                int_value(c["end_tick"]),
                text_value(c["reason"]),
            )
        )
    rules = TransportRules(
        text_value(row["world_seed"]),
        int_value(row["carriage_mps"]),
        int_value(row["ship_mps"]),
        int_value(row["segment_seconds"]),
        tuple(closures),
    )
    rules.validate(world)
    return rules


@dataclass(frozen=True, slots=True)
class JourneyState:
    origin_id: str = ""
    destination_id: str = ""
    mode: str = ""
    progress_m: int = 0
    phase: str = "idle"
    started_tick: int = 0
    block_id: str = ""


@dataclass(frozen=True, slots=True)
class JourneyRecord(ComponentRecord):
    entity_id: EntityId
    state: JourneyState

    @property
    def schema(self) -> TypeKey:
        return JOURNEY_SCHEMA


@dataclass(frozen=True, slots=True)
class SupplyProgressRecord(ComponentRecord):
    entity_id: EntityId
    state: int

    @property
    def schema(self) -> TypeKey:
        return SUPPLY_PROGRESS_SCHEMA


def validate_journey(state: JourneyState) -> None:
    if type(state) is not JourneyState or any(
        type(v) is not str
        for v in (state.origin_id, state.destination_id, state.mode, state.phase, state.block_id)
    ):
        raise ValueError("JOURNEY_STATE")
    require_integer(state.progress_m, 0, 100_000_000)
    require_integer(state.started_tick)
    if state.phase == "idle":
        if state != JourneyState():
            raise ValueError("JOURNEY_IDLE")
    elif (
        state.phase not in ("outbound", "blocked", "returning")
        or state.mode not in ("carriage", "ship")
        or not state.origin_id
        or not state.destination_id
        or not state.started_tick
        or (state.phase == "blocked") != bool(state.block_id)
    ):
        raise ValueError("JOURNEY_STATE")


def checkpoint_position(closure: TransitClosure, route: Route, origin: str) -> int:
    return (
        closure.checkpoint_m
        if origin == closure.origin_id
        else route.distance_km * 1000 - closure.checkpoint_m
    )


def validate_journey_binding(
    world: WorldCatalog, rules: TransportRules, state: JourneyState, travel: TravelState, tick: int
) -> None:
    validate_journey(state)
    require_integer(tick)
    if state.phase == "idle":
        return
    route = route_between(world, state.origin_id, state.destination_id)
    if (
        travel.destination_id
        or travel.place_id != state.origin_id
        or state.mode != ("carriage" if route.kind == "road" else "ship")
        or state.progress_m >= route.distance_km * 1000
        or state.started_tick > tick
        or state.progress_m > rules.speed(state.mode) * (tick - state.started_tick)
    ):
        raise ValueError("JOURNEY_BINDING")
    if state.phase == "returning" and not state.progress_m:
        raise ValueError("JOURNEY_BINDING")
    if state.block_id:
        closure = rules.closure(state.origin_id, state.destination_id)
        if (
            closure is None
            or closure.id != state.block_id
            or state.progress_m != checkpoint_position(closure, route, state.origin_id)
        ):
            raise ValueError("JOURNEY_BLOCK_BINDING")


@dataclass(frozen=True, slots=True)
class JourneyPlan:
    seconds: int
    journey: JourneyState
    travel: TravelState


def _future(tick: int, seconds: int) -> int:
    if tick > MAX_INT - seconds:
        raise ValueError("INTEGER_OVERFLOW")
    return tick + seconds


def plan_journey(
    world: WorldCatalog,
    rules: TransportRules,
    state: JourneyState,
    travel: TravelState,
    tick: int,
    operation: str,
    destination: str = "",
) -> JourneyPlan:
    validate_journey_binding(world, rules, state, travel, tick)
    if (
        type(operation) is not str
        or type(destination) is not str
        or operation not in ("board", "advance", "wait", "resume", "return")
        or (operation != "board" and destination)
    ):
        raise ValueError("INVALID_COMMAND")
    if operation == "board":
        if state.phase != "idle":
            raise ValueError("JOURNEY_ACTIVE")
        if travel.destination_id:
            raise ValueError("WORLD_ROUTE_ACTIVE")
        route = route_between(world, travel.place_id, destination)
        return JourneyPlan(
            1,
            JourneyState(
                travel.place_id,
                destination,
                "carriage" if route.kind == "road" else "ship",
                0,
                "outbound",
                _future(tick, 1),
            ),
            travel,
        )
    if state.phase == "idle":
        raise ValueError("JOURNEY_NOT_ACTIVE")
    route = route_between(world, state.origin_id, state.destination_id)
    closure = rules.closure(state.origin_id, state.destination_id)
    if operation == "return":
        _future(tick, 1)
        return JourneyPlan(
            1,
            replace(state, phase="returning", block_id="") if state.progress_m else JourneyState(),
            travel,
        )
    if operation in ("wait", "resume"):
        if state.phase != "blocked" or closure is None:
            raise ValueError("JOURNEY_NOT_BLOCKED")
        if operation == "wait":
            if not closure.start_tick <= tick < closure.end_tick:
                raise ValueError("JOURNEY_CLEAR")
            return JourneyPlan(min(rules.segment_seconds, closure.end_tick - tick), state, travel)
        if closure.start_tick <= _future(tick, 1) < closure.end_tick:
            raise ValueError("JOURNEY_BLOCKED")
        return JourneyPlan(1, replace(state, phase="outbound", block_id=""), travel)
    if state.phase == "blocked":
        raise ValueError("JOURNEY_BLOCKED")
    speed = rules.speed(state.mode)
    remaining = (
        state.progress_m
        if state.phase == "returning"
        else route.distance_km * 1000 - state.progress_m
    )
    seconds = min(rules.segment_seconds, (remaining + speed - 1) // speed)
    target = _future(tick, seconds)
    if closure is not None and state.phase == "outbound":
        point = checkpoint_position(closure, route, state.origin_id)
        if state.progress_m <= point:
            crossing = max(1, (point - state.progress_m + speed - 1) // speed)
            at_crossing = _future(tick, crossing)
            if crossing <= seconds and closure.start_tick <= at_crossing < closure.end_tick:
                return JourneyPlan(
                    crossing,
                    replace(state, progress_m=point, phase="blocked", block_id=closure.id),
                    travel,
                )
    if seconds * speed >= remaining:
        arrived = state.origin_id if state.phase == "returning" else state.destination_id
        return JourneyPlan(
            seconds,
            JourneyState(),
            TravelState(arrived, "", 0, tuple(sorted(set((*travel.visited, arrived))))),
        )
    distance = state.progress_m + seconds * speed * (-1 if state.phase == "returning" else 1)
    if target <= tick:
        raise ValueError("INTEGER_OVERFLOW")
    return JourneyPlan(seconds, replace(state, progress_m=distance), travel)
