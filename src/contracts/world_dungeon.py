from dataclasses import dataclass
from typing import Protocol

from contracts.messages import CommandPayload, StateDelta
from contracts.read_views import ComponentKey, ComponentPatch
from domain.primitives import FieldAddress, FieldFamily, TypeKey
from domain.world_dungeon import DUNGEON_SCHEMA, DungeonState
from domain.world_travel import WORLD_ACTOR

DUNGEON_OWNER = "world.dungeon"
DUNGEON_FAMILY = FieldFamily(DUNGEON_SCHEMA.kind, "state")


class DungeonRead(Protocol):
    @property
    def state(self) -> DungeonState: ...


DUNGEON = ComponentKey[DungeonRead](DUNGEON_SCHEMA)


@dataclass(frozen=True, slots=True)
class DungeonAction(CommandPayload):
    operation: str
    SCHEMA = TypeKey("world.dungeon-action", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class DungeonDelta(StateDelta):
    before: DungeonState
    after: DungeonState
    SCHEMA = TypeKey("world.dungeon-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(DUNGEON_FAMILY, WORLD_ACTOR)


@dataclass(frozen=True, slots=True)
class DungeonPatch(ComponentPatch):
    state: DungeonState
    SCHEMA = TypeKey("world.dungeon-patch", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


DUNGEON_PAYLOADS = (DungeonAction, DungeonDelta, DungeonPatch)
