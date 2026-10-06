from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from contracts.messages import CommandPayload, FactPayload, PresentationPayload, StateDelta
from contracts.read_views import ComponentKey, ComponentPatch
from domain.primitives import EntityId, FieldAddress, FieldFamily, TypeKey


class TrialMapRead(Protocol):
    @property
    def width(self) -> int: ...
    @property
    def height(self) -> int: ...
    @property
    def cell_mm(self) -> int: ...
    def is_blocked(self, cell: int) -> bool: ...


class CellPositionRead(Protocol):
    @property
    def space_id(self) -> EntityId: ...
    @property
    def cell(self) -> int: ...


TRIAL_MAP = ComponentKey[TrialMapRead](TypeKey("trial.map", 1))
CELL_POSITION = ComponentKey[CellPositionRead](TypeKey("trial.position", 1))


@dataclass(frozen=True, slots=True)
class MoveCommand(CommandPayload):
    dx: int
    dz: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("trial.move", 1)


@dataclass(frozen=True, slots=True)
class CellDelta(StateDelta):
    entity_id: EntityId
    before_cell: int
    after_cell: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("trial.position-delta", 1)

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(FieldFamily(CELL_POSITION.schema.kind, "cell"), self.entity_id)


@dataclass(frozen=True, slots=True)
class CellPatch(ComponentPatch):
    cell: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("trial.position-patch", 1)


@dataclass(frozen=True, slots=True)
class Moved(FactPayload):
    actor_id: EntityId
    space_id: EntityId
    from_cell: int
    to_cell: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("trial.moved", 1)


@dataclass(frozen=True, slots=True)
class MoveBlocked(FactPayload):
    actor_id: EntityId
    space_id: EntityId
    from_cell: int
    dx: int
    dz: int
    reason: Literal["boundary", "occupied"]

    @property
    def schema(self) -> TypeKey:
        return TypeKey("trial.move-blocked", 1)


@dataclass(frozen=True, slots=True)
class MoveCue(PresentationPayload):
    actor_id: EntityId
    space_id: EntityId
    from_cell: int
    to_cell: int
    from_x_mm: int
    from_z_mm: int
    to_x_mm: int
    to_z_mm: int
    result: Literal["moved", "boundary", "occupied"]

    @property
    def schema(self) -> TypeKey:
        return TypeKey("trial.move-cue", 1)
