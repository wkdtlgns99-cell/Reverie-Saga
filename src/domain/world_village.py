"""Fixed walkable district of the authored quest city."""

from dataclasses import dataclass

from domain.primitives import EntityId, TypeKey, require_integer
from domain.state_types import ComponentRecord

VILLAGE_SCHEMA = TypeKey("world.village-position", 1)
VILLAGE_ROWS = (
    "#############",
    "#HH...M..AAA#",
    "#HH......AAA#",
    "#...........#",
    "#...##......#",
    "#...##..WWW.#",
    "#.......WWW.#",
    "#...........#",
    "#############",
)
VILLAGE_LANDMARKS = (
    ("H", "주거지", 1, 1),
    ("M", "시장", 6, 1),
    ("A", "행정청", 9, 1),
    ("W", "작업장", 8, 5),
)
DIRECTIONS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
STEP_SECONDS = 1


@dataclass(frozen=True, slots=True)
class VillagePosition:
    x: int
    y: int

    def __post_init__(self) -> None:
        require_integer(self.x, 0, len(VILLAGE_ROWS[0]) - 1)
        require_integer(self.y, 0, len(VILLAGE_ROWS) - 1)
        if VILLAGE_ROWS[self.y][self.x] != ".":
            raise ValueError("VILLAGE_BLOCKED")


ENTRANCE = VillagePosition(1, 7)


def step(position: VillagePosition, direction: str) -> VillagePosition:
    if type(direction) is not str or direction not in DIRECTIONS:
        raise ValueError("INVALID_COMMAND")
    dx, dy = DIRECTIONS[direction]
    x, y = position.x + dx, position.y + dy
    if not (0 <= y < len(VILLAGE_ROWS) and 0 <= x < len(VILLAGE_ROWS[y])):
        raise ValueError("VILLAGE_BLOCKED")
    return VillagePosition(x, y)


@dataclass(frozen=True, slots=True)
class VillageRecord(ComponentRecord):
    entity_id: EntityId
    state: VillagePosition

    @property
    def schema(self) -> TypeKey:
        return VILLAGE_SCHEMA
