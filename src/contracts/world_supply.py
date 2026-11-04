"""Confirmed supply commands and atomic city/player resource changes."""

from dataclasses import dataclass
from typing import Protocol

from contracts.messages import CommandPayload, FactPayload, PresentationPayload, StateDelta
from contracts.read_views import ComponentKey, ComponentPatch
from contracts.world_population import INVENTORY_FAMILY
from domain.primitives import EntityId, FieldAddress, FieldFamily, TypeKey
from domain.world_population import InventoryState
from domain.world_supply import SUPPLY_SCHEMA, SupplyState

SUPPLY_OWNER = "world.supply"
SUPPLY_FAMILY = FieldFamily(SUPPLY_SCHEMA.kind, "state")


class SupplyRead(Protocol):
    @property
    def state(self) -> SupplyState: ...


SUPPLY = ComponentKey[SupplyRead](SUPPLY_SCHEMA)


@dataclass(frozen=True, slots=True)
class SupplyAction(CommandPayload):
    place_id: str
    npc_id: str
    operation: str
    SCHEMA = TypeKey("world.supply-action", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class SupplyDelta(StateDelta):
    entity_id: EntityId
    before: SupplyState
    after: SupplyState
    SCHEMA = TypeKey("world.supply-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(SUPPLY_FAMILY, self.entity_id)


@dataclass(frozen=True, slots=True)
class InventoryDelta(StateDelta):
    entity_id: EntityId
    before: InventoryState
    after: InventoryState
    SCHEMA = TypeKey("world.inventory-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(INVENTORY_FAMILY, self.entity_id)


@dataclass(frozen=True, slots=True)
class SupplyPatch(ComponentPatch):
    state: SupplyState
    SCHEMA = TypeKey("world.supply-patch", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class InventoryPatch(ComponentPatch):
    state: InventoryState
    SCHEMA = TypeKey("world.inventory-patch", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class SupplyActed(FactPayload):
    actor_id: EntityId
    place_id: str
    npc_id: str
    operation: str
    SCHEMA = TypeKey("world.supply-acted", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class SupplyCue(PresentationPayload):
    actor_id: EntityId
    place_id: str
    npc_id: str
    operation: str
    SCHEMA = TypeKey("world.supply-cue", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


SUPPLY_PAYLOADS = (
    SupplyAction,
    SupplyDelta,
    InventoryDelta,
    SupplyPatch,
    InventoryPatch,
    SupplyActed,
    SupplyCue,
)
