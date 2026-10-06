from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from domain.primitives import EntityId, TypeKey, require_integer
from domain.state_types import ComponentRecord
from domain.trial import cell_coordinates

ENEMY_ID = EntityId("actor:sentinel")
GATE_ID = EntityId("object:gate")
ATTACK_PROFILE_ID = "attack:basic"
GATE_CELL = 4
ENEMY_CELL = 8
ACTOR_HP_MAX = 3
ENEMY_HP_MAX = 5
STAMINA_MAX = 2
ATTACK_DAMAGE = 2
COUNTER_DAMAGE = 1
ATTACK_COST = 1
REST_RECOVERY = 1


@dataclass(frozen=True, slots=True)
class GateRecord(ComponentRecord):
    entity_id: EntityId
    space_id: EntityId
    cell: int
    is_open: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.gate", 1)


@dataclass(frozen=True, slots=True)
class HitPointsRecord(ComponentRecord):
    entity_id: EntityId
    hp: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.hp", 1)


@dataclass(frozen=True, slots=True)
class StaminaRecord(ComponentRecord):
    entity_id: EntityId
    value: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.stamina", 1)


def adjacent_cells(first: int, second: int) -> bool:
    x, z = cell_coordinates(first)
    tx, tz = cell_coordinates(second)
    return abs(x - tx) + abs(z - tz) == 1000


def resolve_basic_attack(actor_hp: int, target_hp: int, stamina: int) -> tuple[int, int, int]:
    require_integer(actor_hp, 1, ACTOR_HP_MAX)
    require_integer(target_hp, 1, ENEMY_HP_MAX)
    require_integer(stamina, 1, STAMINA_MAX)
    target_after = max(0, target_hp - ATTACK_DAMAGE)
    actor_after = max(0, actor_hp - (COUNTER_DAMAGE if target_after > 0 else 0))
    return actor_after, target_after, stamina - ATTACK_COST


def life_status(hp: int) -> Literal["alive", "defeated"]:
    require_integer(hp, 0, ENEMY_HP_MAX)
    return "defeated" if hp == 0 else "alive"


def stamina_status(value: int) -> Literal["ready", "exhausted"]:
    require_integer(value, 0, STAMINA_MAX)
    return "exhausted" if value == 0 else "ready"
