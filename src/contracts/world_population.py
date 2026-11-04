"""Observed local-definition/inventory access and atomic materialization changes."""

from dataclasses import dataclass
from typing import Protocol

from contracts.messages import StateDelta
from contracts.read_views import ComponentKey, ComponentPatch
from domain.primitives import EntityId, FieldAddress, FieldFamily, TypeKey
from domain.world import LocalDetail
from domain.world_population import INVENTORY_SCHEMA, SETTLEMENT_SCHEMA, InventoryState

SETTLEMENT_FAMILY = FieldFamily(SETTLEMENT_SCHEMA.kind, "state")
INVENTORY_FAMILY = FieldFamily(INVENTORY_SCHEMA.kind, "state")
MATERIALIZER = "world.materialize"


class SettlementRead(Protocol):
    @property
    def state(self) -> LocalDetail | None: ...


class InventoryRead(Protocol):
    @property
    def state(self) -> InventoryState: ...


SETTLEMENT = ComponentKey[SettlementRead](SETTLEMENT_SCHEMA)
INVENTORY = ComponentKey[InventoryRead](INVENTORY_SCHEMA)


@dataclass(frozen=True, slots=True)
class SettlementDelta(StateDelta):
    entity_id: EntityId
    before: LocalDetail | None
    after: LocalDetail
    SCHEMA = TypeKey("world.settlement-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(SETTLEMENT_FAMILY, self.entity_id)


@dataclass(frozen=True, slots=True)
class SettlementPatch(ComponentPatch):
    state: LocalDetail
    SCHEMA = TypeKey("world.settlement-patch", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA
