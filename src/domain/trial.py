from __future__ import annotations

from dataclasses import dataclass

from domain.primitives import EntityId, TypeKey, require_integer
from domain.state_types import ComponentRecord

ACTOR_ID = EntityId("actor:trial")
SPACE_ID = EntityId("space:trial")
WIDTH = 3
HEIGHT = 3
CELL_MM = 1000
BLOCKED_CELLS = (1,)


@dataclass(frozen=True, slots=True)
class TrialMapRecord(ComponentRecord):
    entity_id: EntityId
    width: int
    height: int
    cell_mm: int
    blocked_cells: tuple[int, ...]

    @property
    def schema(self) -> TypeKey:
        return TypeKey("trial.map", 1)


@dataclass(frozen=True, slots=True)
class CellPositionRecord(ComponentRecord):
    entity_id: EntityId
    space_id: EntityId
    cell: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("trial.position", 1)


def cell_coordinates(cell: int) -> tuple[int, int]:
    require_integer(cell, 0, WIDTH * HEIGHT - 1)
    return cell % WIDTH * CELL_MM, cell // WIDTH * CELL_MM
