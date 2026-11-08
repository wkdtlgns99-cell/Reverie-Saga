"""Typed local movement command and committed position."""

from dataclasses import dataclass
from typing import Protocol

from contracts.messages import CommandPayload, StateDelta
from contracts.read_views import ComponentKey, ComponentPatch
from domain.primitives import EntityId, FieldAddress, FieldFamily, TypeKey
from domain.world_village import VILLAGE_SCHEMA, VillagePosition

VILLAGE_OWNER = "world.village"
VILLAGE_FAMILY = FieldFamily(VILLAGE_SCHEMA.kind, "state")


class VillageRead(Protocol):
    @property
    def state(self) -> VillagePosition: ...


VILLAGE = ComponentKey[VillageRead](VILLAGE_SCHEMA)


@dataclass(frozen=True, slots=True)
class VillageStep(CommandPayload):
    direction: str
    SCHEMA = TypeKey("world.village-step", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class VillageDelta(StateDelta):
    entity_id: EntityId
    before: VillagePosition
    after: VillagePosition
    SCHEMA = TypeKey("world.village-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(VILLAGE_FAMILY, self.entity_id)


@dataclass(frozen=True, slots=True)
class VillagePatch(ComponentPatch):
    state: VillagePosition
    SCHEMA = TypeKey("world.village-patch", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


VILLAGE_PAYLOADS = (VillageStep, VillageDelta, VillagePatch)
