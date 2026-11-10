"""Bounded starter equipment and isolated dungeon sparring opponents."""

from dataclasses import dataclass

from domain.primitives import EntityId
from domain.world_combat import BANDIT_DAMAGE, PLAYER_DAMAGE, POMMEL

SWORD = "sword"
SPEAR = "spear"
HAMMER = "hammer"
THRUST = "thrust"
CRUSH = "crush"
ORC = EntityId("actor:mulbeodeul-orc")
SWITCH_USES_TURN = True


@dataclass(frozen=True, slots=True)
class DungeonWeapon:
    id: str
    name: str
    attack_name: str
    damage: int
    skill_id: str
    skill_name: str
    skill_damage: int
    staggers: bool = False
    switch_ticks: int = 1


WEAPONS = (
    DungeonWeapon(SWORD, "짧은 검", "베기", PLAYER_DAMAGE, POMMEL, "칼자루 치기", 1, True),
    DungeonWeapon(SPEAR, "연습용 창", "찌르기", 2, THRUST, "정밀 찌르기", 3),
    DungeonWeapon(HAMMER, "전투 망치", "내려치기", 1, CRUSH, "충격 강타", 2, True),
)


def weapon_by_id(weapon_id: str) -> DungeonWeapon | None:
    return next((weapon for weapon in WEAPONS if weapon.id == weapon_id), None)


def weapon_for_skill(skill_id: str) -> DungeonWeapon | None:
    return next((weapon for weapon in WEAPONS if weapon.skill_id == skill_id), None)


@dataclass(frozen=True, slots=True)
class DungeonOpponent:
    kind: str
    actor: EntityId
    name: str
    speed: int
    damage: int


ORC_ENCOUNTER = DungeonOpponent("orc", ORC, "오크", 3, BANDIT_DAMAGE)
TRIAL_OPPONENTS = (
    DungeonOpponent("slime", EntityId("actor:trial-slime"), "이끼 슬라임", 5, 1),
    DungeonOpponent("guard", EntityId("actor:trial-guard"), "경비병 견습생", 3, 2),
)


def opponent_by_kind(kind: str) -> DungeonOpponent:
    return next(opponent for opponent in (ORC_ENCOUNTER, *TRIAL_OPPONENTS) if opponent.kind == kind)
