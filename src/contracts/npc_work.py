"""Typed registered stock boundary;no player inventory or reward grant."""

from dataclasses import dataclass
from typing import Protocol

from contracts.messages import FactPayload, PresentationPayload, StateDelta
from contracts.read_views import ComponentKey, ComponentPatch
from domain.npc_work import STOCK_SCHEMA
from domain.primitives import EntityId, FieldAddress, FieldFamily, TypeKey

STOCK_FAMILY = FieldFamily(STOCK_SCHEMA.kind, "stock")


class ProvisionsRead(Protocol):
    @property
    def stock(self) -> int: ...


PROVISIONS = ComponentKey[ProvisionsRead](STOCK_SCHEMA)


@dataclass(frozen=True, slots=True)
class ProvisionsDelta(StateDelta):
    entity_id: EntityId
    before: int
    after: int
    SCHEMA = TypeKey("quest.provisions-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(STOCK_FAMILY, self.entity_id)


@dataclass(frozen=True, slots=True)
class ProvisionsPatch(ComponentPatch):
    stock: int
    SCHEMA = TypeKey("quest.provisions-patch", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class ProvisionPrepared(FactPayload):
    npc_id: EntityId
    before: int
    after: int
    SCHEMA = TypeKey("quest.provision-prepared", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class ProvisionsCue(PresentationPayload):
    npc_id: EntityId
    stock: int
    tick: int
    SCHEMA = TypeKey("quest.provisions-cue", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


WORK_PAYLOADS = (ProvisionsDelta, ProvisionsPatch, ProvisionPrepared, ProvisionsCue)
