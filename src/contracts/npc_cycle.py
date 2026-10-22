"""One atomic owner for supply and bounded factual memory."""

from dataclasses import dataclass
from typing import Protocol

from contracts.messages import FactPayload, PresentationPayload, StateDelta
from contracts.read_views import ComponentKey, ComponentPatch
from domain.npc_cycle import CYCLE_SCHEMA, CycleRecord, Supply, SupplyEvidence
from domain.primitives import EntityId, FieldAddress, FieldFamily, TypeKey

CYCLE_FAMILY = FieldFamily(CYCLE_SCHEMA.kind, "cycle")


class CycleRead(Protocol):
    @property
    def state(self) -> Supply: ...
    @property
    def entries(self) -> tuple[SupplyEvidence, ...]: ...


CYCLE = ComponentKey[CycleRead](CYCLE_SCHEMA)


@dataclass(frozen=True, slots=True)
class CycleDelta(StateDelta):
    before: CycleRecord
    after: CycleRecord
    SCHEMA = TypeKey("quest.cycle-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(CYCLE_FAMILY, self.before.entity_id)


@dataclass(frozen=True, slots=True)
class CyclePatch(ComponentPatch):
    value: CycleRecord
    SCHEMA = TypeKey("quest.cycle-patch", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class CycleChanged(FactPayload):
    npc_id: EntityId
    evidence: SupplyEvidence
    SCHEMA = TypeKey("quest.cycle-changed", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class CycleCue(PresentationPayload):
    npc_id: EntityId
    evidence: SupplyEvidence
    SCHEMA = TypeKey("quest.cycle-cue", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


CYCLE_PAYLOADS = (CycleDelta, CyclePatch, CycleChanged, CycleCue)
