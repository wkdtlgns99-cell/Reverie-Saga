"""Immutable role bindings for the bounded, shipped 3x3 room scenarios."""

from __future__ import annotations

from dataclasses import dataclass

from domain.encounter import ENEMY_CELL, ENEMY_ID, GATE_CELL, GATE_ID
from domain.primitives import EntityId, require_integer, require_namespace
from domain.trial import ACTOR_ID, BLOCKED_CELLS, SPACE_ID
from domain.watch import LANTERN_ID, NPC_CELL, NPC_ID


@dataclass(frozen=True, slots=True)
class Scenario:
    scenario_id: str
    actor_id: EntityId
    space_id: EntityId
    gate_id: EntityId
    enemy_id: EntityId
    npc_id: EntityId
    lantern_id: EntityId
    initial_cell: int
    wall_cell: int
    gate_cell: int
    enemy_cell: int
    npc_cell: int

    def __post_init__(self) -> None:
        for code, values in (
            ("SCENARIO_ID", (self.scenario_id,)),
            (
                "SCENARIO_ROLE_ID",
                (
                    self.actor_id,
                    self.space_id,
                    self.gate_id,
                    self.enemy_id,
                    self.npc_id,
                    self.lantern_id,
                ),
            ),
        ):
            for value in values:
                try:
                    if type(value) is not str:
                        raise ValueError("exact string required")
                    require_namespace(value)
                except ValueError as error:
                    raise ValueError(code) from error
        if (
            len(
                {
                    self.actor_id,
                    self.space_id,
                    self.gate_id,
                    self.enemy_id,
                    self.npc_id,
                    self.lantern_id,
                }
            )
            != 6
        ):
            raise ValueError("SCENARIO_DUPLICATE_ID")
        try:
            for cell in (
                self.initial_cell,
                self.wall_cell,
                self.gate_cell,
                self.enemy_cell,
                self.npc_cell,
            ):
                require_integer(cell, 0, 8)
        except ValueError as error:
            raise ValueError("SCENARIO_CELL") from error
        if len(
            {self.wall_cell, self.gate_cell, self.enemy_cell, self.npc_cell}
        ) != 4 or self.initial_cell in (self.wall_cell, self.gate_cell, self.enemy_cell):
            raise ValueError("SCENARIO_OCCUPANCY")

    @property
    def blocked_cells(self) -> tuple[int, ...]:
        return (self.wall_cell,)


LEGACY_SCENARIO = Scenario(
    "scenario:legacy",
    ACTOR_ID,
    SPACE_ID,
    GATE_ID,
    ENEMY_ID,
    NPC_ID,
    LANTERN_ID,
    0,
    BLOCKED_CELLS[0],
    GATE_CELL,
    ENEMY_CELL,
    NPC_CELL,
)
COURTYARD_SCENARIO = Scenario(
    "scenario:courtyard",
    EntityId("actor:courtyard-player"),
    EntityId("space:courtyard"),
    EntityId("object:courtyard-door"),
    EntityId("actor:courtyard-guard"),
    EntityId("actor:courtyard-bellkeeper"),
    EntityId("object:courtyard-lamp"),
    6,
    7,
    2,
    0,
    8,
)


def require_scenario(scenario: Scenario) -> None:
    if type(scenario) is not Scenario:
        raise ValueError("SCENARIO_TYPE")


def scenario_by_id(identifier: str) -> Scenario:
    if type(identifier) is str:
        for scenario in (LEGACY_SCENARIO, COURTYARD_SCENARIO):
            if identifier == scenario.scenario_id:
                return scenario
    raise ValueError("UNKNOWN_SCENARIO")
