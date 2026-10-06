from __future__ import annotations

from dataclasses import dataclass
from domain.primitives import EntityId, Tick, TypeKey, require_integer
from domain.state_types import ComponentRecord

NPC_ID = EntityId("actor:watcher")
LANTERN_ID = EntityId("object:lantern")
NPC_CELL = 6
WAKE_PERIOD = 2
CHARGE_MAX = 3
WAIT_MAX = 16
ECHO_DEPTH = 1


def next_wake(tick: int) -> Tick:
    require_integer(tick)
    result = (tick // WAKE_PERIOD + 1) * WAKE_PERIOD
    require_integer(result)
    return Tick(result)


def recover_charge(charge: int) -> int:
    require_integer(charge, 0, CHARGE_MAX)
    return min(CHARGE_MAX, charge + 1)


def increment_count(value: int, amount: int = 1) -> int:
    require_integer(value)
    require_integer(amount, 1, 512)
    result = value + amount
    require_integer(result)
    return result


@dataclass(frozen=True, slots=True)
class WatchNpcRecord(ComponentRecord):
    entity_id: EntityId
    space_id: EntityId
    cell: int
    bells: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.npc", 1)


@dataclass(frozen=True, slots=True)
class LanternRecord(ComponentRecord):
    entity_id: EntityId
    charge: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.lantern", 1)


@dataclass(frozen=True, slots=True)
class ReplyRecord(ComponentRecord):
    entity_id: EntityId
    count: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.reply", 1)
