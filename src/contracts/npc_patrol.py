"""Additive opt-in patrol payloads;no new persistent component or wire envelope."""

from dataclasses import dataclass
from typing import ClassVar

from contracts.messages import FactPayload, PresentationPayload, StateDelta
from contracts.read_views import ComponentPatch
from domain.primitives import EntityId, FieldAddress, FieldFamily, Tick, TypeKey


@dataclass(frozen=True, slots=True)
class NpcCellDelta(StateDelta):
    entity_id: EntityId
    before_cell: int
    after_cell: int
    SCHEMA: ClassVar[TypeKey] = TypeKey("watch.npc-cell-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(FieldFamily("watch.npc", "cell"), self.entity_id)


@dataclass(frozen=True, slots=True)
class NpcCellPatch(ComponentPatch):
    cell: int
    SCHEMA: ClassVar[TypeKey] = TypeKey("watch.npc-cell-patch", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class NpcPatrolled(FactPayload):
    npc_id: EntityId
    space_id: EntityId
    before_cell: int
    after_cell: int
    SCHEMA: ClassVar[TypeKey] = TypeKey("watch.npc-patrolled", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class NpcPatrolCue(PresentationPayload):
    npc_id: EntityId
    logical_tick: Tick
    before_cell: int
    after_cell: int
    x_mm: int
    z_mm: int
    SCHEMA: ClassVar[TypeKey] = TypeKey("watch.npc-patrol-cue", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


PATROL_PAYLOADS = NpcCellDelta, NpcCellPatch, NpcPatrolled, NpcPatrolCue
