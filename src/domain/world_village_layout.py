"""Versioned decoration of the walkable Mulbeodeul map from world data."""

from dataclasses import dataclass
from hashlib import sha256

from domain.canonical import JsonObject
from domain.world import WorldCatalog
from domain.world_village import DIRECTIONS, VILLAGE_ROWS

LAYOUT_VERSION = 1
ROOM_SIZE = 5


@dataclass(frozen=True, slots=True)
class Placement:
    kind: str
    x: int
    y: int
    variant: int = 0
    facing: int = 0

    def wire(self) -> JsonObject:
        return {
            "kind": self.kind,
            "x": self.x,
            "y": self.y,
            "variant": self.variant,
            "facing": self.facing,
        }


@dataclass(frozen=True, slots=True)
class DungeonBlueprint:
    gate_x: int
    gate_y: int
    orc_x: int
    orc_y: int = 2


def _layout_key(world: WorldCatalog, place_id: str) -> tuple[str, str]:
    place = world.place(place_id)
    country = next(country for country in world.countries if country.id == place.country_id)
    terrain = next(
        region.environment for region in world.continents if region.id == country.continent_id
    )
    return f"village-art/v{LAYOUT_VERSION}:{world.seed_hex}:{place.id}:{terrain}", terrain


def _choose(key: str, label: str, count: int) -> int:
    return int.from_bytes(sha256(f"{key}:{label}".encode()).digest()[:8]) % count


def dungeon_blueprint(world: WorldCatalog, place_id: str) -> DungeonBlueprint:
    key, _ = _layout_key(world, place_id)
    # Side lanes leave the entrance, the authored ambush and its attacker unobstructed.
    candidates = (2, 3, 4, 5, 10, 11)
    return DungeonBlueprint(
        candidates[_choose(key, "dungeon-entry", len(candidates))],
        len(VILLAGE_ROWS) - 1,
        1 + _choose(key, "orc", ROOM_SIZE - 2),
    )


def village_layout(world: WorldCatalog, place_id: str) -> JsonObject:
    key, terrain = _layout_key(world, place_id)
    blueprint = dungeon_blueprint(world, place_id)

    def choose(label: str, count: int) -> int:
        return _choose(key, label, count)

    width, height = len(VILLAGE_ROWS[0]), len(VILLAGE_ROWS)
    village = []
    for y, row in enumerate(VILLAGE_ROWS):
        for x, cell in enumerate(row):
            if y == blueprint.gate_y and 0 < x < width - 1:
                kind = (
                    "gate"
                    if x == blueprint.gate_x
                    else ("tree" if choose(f"edge:{x}", 3) == 0 else "rock")
                )
                village.append(Placement(kind, x, y))
            elif 0 < x < width - 1 and 0 < y < height - 1:
                kind = "road" if cell == "." else "wall" if cell == "#" else "house"
                facing = 0
                if kind == "house":
                    for rotation, direction in enumerate(("down", "right", "up", "left")):
                        dx, dy = DIRECTIONS[direction]
                        if VILLAGE_ROWS[y + dy][x + dx] == ".":
                            facing = rotation
                            break
                village.append(Placement(kind, x, y, choose(f"{kind}:{x}:{y}", 3), facing))

    room = tuple(
        Placement(
            "dungeon-wall"
            if x in (0, ROOM_SIZE - 1) or y in (0, ROOM_SIZE - 1)
            else "dungeon-floor",
            x,
            y,
            choose(f"room:{x}:{y}", 2),
        )
        for y in range(ROOM_SIZE)
        for x in range(ROOM_SIZE)
        if (x, y) != (2, ROOM_SIZE - 1)
    )
    return {
        "version": LAYOUT_VERSION,
        "seed": world.seed_hex,
        "terrain": terrain,
        "gate_x": blueprint.gate_x,
        "gate_y": blueprint.gate_y,
        "village": tuple(item.wire() for item in village),
        "dungeon": (
            *(item.wire() for item in room),
            Placement("orc", blueprint.orc_x, blueprint.orc_y).wire(),
        ),
    }
