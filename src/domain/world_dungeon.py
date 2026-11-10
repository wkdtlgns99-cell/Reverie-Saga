"""The first durable dungeon room and its movement rules."""

from dataclasses import dataclass

from domain.primitives import EntityId, TypeKey, require_integer
from domain.state_types import ComponentRecord
from domain.world_combat import POMMEL, STAGGER, CombatState
from domain.world_dungeon_loadout import ORC, SWORD, WEAPONS, DungeonWeapon, weapon_by_id
from domain.world_village import DIRECTIONS
from domain.world_village_layout import ROOM_SIZE, DungeonBlueprint

DUNGEON_SCHEMA = TypeKey("world.dungeon", 1)
ENTRY = (2, ROOM_SIZE - 2)


@dataclass(frozen=True, slots=True)
class DungeonState:
    tile: tuple[int, int] | None = None
    combat: CombatState = CombatState(opponent=ORC)
    pommel_used: bool = False
    weapon_id: str = SWORD
    other_skills_used: tuple[str, ...] = ()
    last_other_skill: str = ""

    def __post_init__(self) -> None:
        if self.tile is not None:
            if type(self.tile) is not tuple or len(self.tile) != 2:
                raise ValueError("DUNGEON_TILE")
            for coordinate in self.tile:
                require_integer(coordinate, 1, ROOM_SIZE - 2)
        if self.combat.order and self.tile is None:
            raise ValueError("DUNGEON_COMBAT")
        if type(self.pommel_used) is not bool or (
            self.combat.last_action == POMMEL and not self.pommel_used
            or self.combat.last_action == STAGGER and not (self.pommel_used or self.other_skills_used)
        ):
            raise ValueError("DUNGEON_SKILL")
        if weapon_by_id(self.weapon_id) is None:
            raise ValueError("DUNGEON_WEAPON")
        known = tuple(weapon.skill_id for weapon in WEAPONS if weapon.skill_id != POMMEL)
        if (
            type(self.other_skills_used) is not tuple
            or any(skill not in known for skill in self.other_skills_used)
            or tuple(sorted(set(self.other_skills_used))) != self.other_skills_used
            or (self.last_other_skill and (
                self.last_other_skill not in self.other_skills_used or self.combat.last_action != "attack"
            ))
        ):
            raise ValueError("DUNGEON_SKILL")

    @property
    def weapon(self) -> DungeonWeapon:
        weapon = weapon_by_id(self.weapon_id)
        if weapon is None:
            raise ValueError("DUNGEON_WEAPON")
        return weapon

    def skill_used(self, skill_id: str) -> bool:
        return self.pommel_used if skill_id == POMMEL else skill_id in self.other_skills_used

    @property
    def last_skill(self) -> str:
        return POMMEL if self.combat.last_action == POMMEL else self.last_other_skill


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
