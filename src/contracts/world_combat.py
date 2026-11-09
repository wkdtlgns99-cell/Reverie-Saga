"""Durable village combat commands and owner-local state changes."""

from dataclasses import dataclass
from typing import Protocol

from contracts.messages import CommandPayload, StateDelta
from contracts.read_views import ComponentKey, ComponentPatch
from domain.primitives import FieldAddress, FieldFamily, TypeKey
from domain.world_combat import COMBAT_SCHEMA, CombatState
from domain.world_travel import WORLD_ACTOR

COMBAT_OWNER = "world.combat"
COMBAT_FAMILY = FieldFamily(COMBAT_SCHEMA.kind, "state")


class CombatRead(Protocol):
    @property
    def state(self) -> CombatState: ...


COMBAT = ComponentKey[CombatRead](COMBAT_SCHEMA)


@dataclass(frozen=True, slots=True)
class CombatAction(CommandPayload):
    operation: str
    SCHEMA = TypeKey("world.village-combat-action", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class CombatDelta(StateDelta):
    before: CombatState
    after: CombatState
    SCHEMA = TypeKey("world.village-combat-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(COMBAT_FAMILY, WORLD_ACTOR)


@dataclass(frozen=True, slots=True)
class CombatPatch(ComponentPatch):
    state: CombatState
    SCHEMA = TypeKey("world.village-combat-patch", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


COMBAT_PAYLOADS = (CombatAction, CombatDelta, CombatPatch)
