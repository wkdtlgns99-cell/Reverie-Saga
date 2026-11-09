"""The first durable dungeon room and its movement rules."""

from dataclasses import dataclass

from domain.primitives import EntityId, TypeKey, require_integer
from domain.state_types import ComponentRecord
from domain.world_combat import POMMEL, STAGGER, CombatState
from domain.world_village import DIRECTIONS
from domain.world_village_layout import ROOM_SIZE, DungeonBlueprint

DUNGEON_SCHEMA = TypeKey("world.dungeon", 1)
ORC = EntityId("actor:mulbeodeul-orc")
ENTRY = (2, ROOM_SIZE - 2)
STARTER_SWORD_NAME = "짧은 검"
POMMEL_NAME = "칼자루 치기"
POMMEL_DAMAGE = 1


@dataclass(frozen=True, slots=True)
class DungeonState:
    tile: tuple[int, int] | None = None
    combat: CombatState = CombatState(opponent=ORC)
    pommel_used: bool = False

    def __post_init__(self) -> None:
        if self.tile is not None:
            if type(self.tile) is not tuple or len(self.tile) != 2:
                raise ValueError("DUNGEON_TILE")
            for coordinate in self.tile:
                require_integer(coordinate, 1, ROOM_SIZE - 2)
        if self.combat.opponent != ORC or (self.combat.order and self.tile is None):
            raise ValueError("DUNGEON_COMBAT")
        if type(self.pommel_used) is not bool or (
            self.combat.last_action in (POMMEL, STAGGER) and not self.pommel_used
        ):
            raise ValueError("DUNGEON_SKILL")


@dataclass(frozen=True, slots=True)
class DungeonRecord(ComponentRecord):
    entity_id: EntityId
    state: DungeonState

    @property
    def schema(self) -> TypeKey:
        return DUNGEON_SCHEMA


def dungeon_step(
    tile: tuple[int, int], direction: str, blueprint: DungeonBlueprint, *, orc_alive: bool
) -> tuple[int, int]:
    dx, dy = DIRECTIONS[direction]
    target = (tile[0] + dx, tile[1] + dy)
    if not all(1 <= coordinate <= ROOM_SIZE - 2 for coordinate in target):
        raise ValueError("DUNGEON_WALL")
    if orc_alive and target == (blueprint.orc_x, blueprint.orc_y):
        raise ValueError("DUNGEON_OCCUPIED")
    return target


def in_melee_range(tile: tuple[int, int], blueprint: DungeonBlueprint) -> bool:
    return abs(tile[0] - blueprint.orc_x) + abs(tile[1] - blueprint.orc_y) == 1
