"""Small embedded scenarios;their complete definitions join existing feature pins."""

from __future__ import annotations

from dataclasses import dataclass

from domain.canonical import JsonObject, array_value, object_value, seal
from domain.primitives import EntityId
from domain.scenario import COURTYARD_SCENARIO, LEGACY, Scenario, scenario_document


@dataclass(frozen=True, slots=True)
class ScenarioChoice:
    key: str
    name_ko: str
    layout: Scenario
    narrative_id: str


def _sample(key: str, initial: int, wall: int, enemy: int, npc: int) -> Scenario:
    return Scenario(
        scenario_id=f"scenario:{key}",
        actor_id=EntityId(f"actor:{key}-player"),
        space_id=EntityId(f"space:{key}"),
        gate_id=EntityId(f"object:{key}-gate"),
        enemy_id=EntityId(f"actor:{key}-enemy"),
        npc_id=EntityId(f"actor:{key}-watcher"),
        lantern_id=EntityId(f"object:{key}-lantern"),
        initial_cell=initial,
        gate_cell=4,
        enemy_cell=enemy,
        npc_cell=npc,
        blocked_cells=(wall,),
    )


SCENARIOS = (
    ScenarioChoice("legacy", "기본 연습 방", LEGACY, ""),
    ScenarioChoice("courtyard", "안뜰", COURTYARD_SCENARIO, ""),
    ScenarioChoice(
        "harbor",
        "소금눈물 포구",
        _sample("harbor", 0, 1, 8, 6),
        "narrative:settlement-06db229b88e2df71",
    ),
    ScenarioChoice(
        "grove",
        "빈뿌리 쉼터",
        _sample("grove", 6, 7, 2, 0),
        "narrative:settlement-d72c8ca84cee4ea9",
    ),
)


def select_scenario(key: str) -> ScenarioChoice:
    if type(key) is not str:
        raise ValueError("SCENARIO_SELECTION")
    matches = tuple(
        choice for choice in SCENARIOS if key in (choice.key, choice.layout.scenario_id)
    )
    if len(matches) != 1:
        raise ValueError("SCENARIO_SELECTION")
    return matches[0]


def scenario_name(layout: Scenario) -> str:
    return next((choice.name_ko for choice in SCENARIOS if choice.layout == layout), "연습 구간")


def bind_documents(
    schema: JsonObject, rules: JsonObject, layout: Scenario
) -> tuple[JsonObject, JsonObject]:
    if type(layout) is not Scenario:
        raise ValueError("SCENARIO_TYPE")
    if layout == LEGACY:
        return schema, rules
    # Copy before specialization;never mutate a registered legacy descriptor.
    next_schema = dict(schema)
    next_rules = dict(rules)
    components = list(array_value(schema["components"]))
    for index, raw in enumerate(components):
        component = dict(object_value(raw))
        kind = object_value(component["schema"])["kind"]
        if kind in ("encounter.gate", "watch.npc"):
            fields = dict(object_value(component["fields"]))
            cell = dict(object_value(fields["cell"]))
            value = layout.gate_cell if kind == "encounter.gate" else layout.npc_cell
            cell["minimum"] = cell["maximum"] = value
            fields["cell"] = cell
            component["fields"] = fields
            components[index] = component
    next_schema["components"] = tuple(components)
    document = scenario_document(layout)
    next_rules["scenario"] = document
    encounter = dict(object_value(rules["encounter"])) if "encounter" in rules else next_rules
    for field in (
        "actor_id",
        "space_id",
        "gate_id",
        "enemy_id",
        "gate_cell",
        "enemy_cell",
        "blocked_cells",
    ):
        encounter[field] = layout.blocked_cells if field == "blocked_cells" else document[field]
    encounter["initial_cell"] = layout.initial_cell
    if layout.wall_cell is not None and "encounter" in rules:
        del next_rules["scenario"]
        encounter["scenario"] = document
    if "encounter" in rules:
        next_rules["encounter"] = encounter
    for field in ("npc_id", "npc_cell", "lantern_id"):
        if field in rules:
            next_rules[field] = document[field]
    return object_value(seal(next_schema)), object_value(seal(next_rules))
