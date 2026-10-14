"""Immutable embedded role/topology bindings;selected feature fingerprints own identity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from domain.encounter import ENEMY_CELL, ENEMY_ID, GATE_CELL, GATE_ID
from domain.primitives import EntityId, require_integer, require_namespace
from domain.trial import ACTOR_ID, BLOCKED_CELLS, SPACE_ID
from domain.watch import LANTERN_ID, NPC_CELL, NPC_ID


@dataclass(frozen=True, slots=True)
class Scenario:
    scenario_id: str = "scenario:legacy"
    actor_id: EntityId = ACTOR_ID
    space_id: EntityId = SPACE_ID
    gate_id: EntityId = GATE_ID
    enemy_id: EntityId = ENEMY_ID
    npc_id: EntityId = NPC_ID
    lantern_id: EntityId = LANTERN_ID
    initial_cell: int = 0
    gate_cell: int = GATE_CELL
    enemy_cell: int = ENEMY_CELL
    npc_cell: int = NPC_CELL
    blocked_cells: tuple[int, ...] = BLOCKED_CELLS

    def __post_init__(self) -> None:
        identifiers = (
            (self.scenario_id, "scenario:"),
            (self.actor_id, "actor:"),
            (self.space_id, "space:"),
            (self.gate_id, "object:"),
            (self.enemy_id, "actor:"),
            (self.npc_id, "actor:"),
            (self.lantern_id, "object:"),
        )
        for identifier, prefix in identifiers:
            if type(identifier) is not str or not identifier.startswith(prefix):
                raise ValueError("SCENARIO_ID")
            try:
                require_namespace(identifier)
            except ValueError as error:
                raise ValueError("SCENARIO_ID") from error
        if len({value for value, _ in identifiers}) != len(identifiers):
            raise ValueError("SCENARIO_DUPLICATE_ID")
        if type(self.blocked_cells) is not tuple or len(self.blocked_cells) != 1:
            raise ValueError("SCENARIO_WALLS")
        occupied = (self.initial_cell, self.gate_cell, self.enemy_cell, self.npc_cell)
        for cell in (*occupied, *self.blocked_cells):
            try:
                require_integer(cell, 0, 8)
            except ValueError as error:
                raise ValueError("SCENARIO_CELL") from error
        if len(set(occupied)) != 4 or set(occupied).intersection(self.blocked_cells):
            raise ValueError("SCENARIO_OVERLAP")


LEGACY = Scenario()


@runtime_checkable
class ScenarioConsumer(Protocol):
    @property
    def scenario_layout(self) -> Scenario: ...


class ScenarioBound:
    """Boot-only binding;the definition itself is frozen and contains no mutable state."""

    # Existing legacy extensions may define their own constructor without super().
    # An explicit selected binding is still installed by the ordinary boot path.
    _layout: Scenario = LEGACY

    @property
    def scenario_layout(self) -> Scenario:
        return self._layout

    def __init__(self, layout: Scenario = LEGACY) -> None:
        if type(layout) is not Scenario:
            raise ValueError("SCENARIO_TYPE")
        self._layout = layout
