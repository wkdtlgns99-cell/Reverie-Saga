from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from typing import cast

import pytest

from app.headless import state_io
from app.watch_registry import watch_bundle
from contracts.encounter import GateCue
from contracts.watch import NpcCue
from domain.primitives import EntityId, Tick
from domain.scenario import COURTYARD_SCENARIO, LEGACY_SCENARIO, Scenario, scenario_by_id
from orchestration.encounter import EncounterPayloadCodec
from orchestration.watch import WatchPayloadCodec


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("scenario_id", "", "SCENARIO_ID"),
        ("actor_id", "bad value", "SCENARIO_ROLE_ID"),
        ("actor_id", COURTYARD_SCENARIO.enemy_id, "SCENARIO_DUPLICATE_ID"),
        ("gate_cell", True, "SCENARIO_CELL"),
        ("wall_cell", -1, "SCENARIO_CELL"),
        ("enemy_cell", 9, "SCENARIO_CELL"),
        ("initial_cell", 7, "SCENARIO_OCCUPANCY"),
        ("npc_cell", 0, "SCENARIO_OCCUPANCY"),
    ],
)
def test_invalid_scenario(field: str, value: object, code: str) -> None:
    # Deliberately malformed external construction,without relaxing domain annotations.
    with pytest.raises(ValueError, match=f"^{code}$"):
        replace(COURTYARD_SCENARIO, **{field: value})  # type: ignore[arg-type]


def test_registered_selection_and_immutable_values() -> None:
    assert scenario_by_id("scenario:legacy") is LEGACY_SCENARIO
    assert scenario_by_id("scenario:courtyard") is COURTYARD_SCENARIO
    assert COURTYARD_SCENARIO.blocked_cells == (7,)
    with pytest.raises(ValueError, match="^UNKNOWN_SCENARIO$"):
        scenario_by_id("scenario:missing")
    with pytest.raises(FrozenInstanceError):
        setattr(COURTYARD_SCENARIO, "enemy_cell", 4)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("scenario_id", "scenario:changed"),
        ("actor_id", "actor:changed"),
        ("space_id", "space:changed"),
        ("gate_id", "object:changed"),
        ("enemy_id", "actor:changed"),
        ("npc_id", "actor:changed"),
        ("lantern_id", "object:changed"),
        ("initial_cell", 3),
        ("wall_cell", 5),
        ("gate_cell", 4),
        ("enemy_cell", 1),
        ("npc_cell", 4),
    ],
)
def test_every_binding_is_pinned(field: str, value: str | int) -> None:
    selected = COURTYARD_SCENARIO
    changed = replace(selected, **{field: value})  # type: ignore[arg-type]
    assert (
        state_io((watch_bundle(selected),)).pins.rules_fingerprint
        != state_io((watch_bundle(changed),)).pins.rules_fingerprint
    )


def test_exact_scenario_type_before_registry() -> None:
    with pytest.raises(ValueError, match="^SCENARIO_TYPE$"):
        watch_bundle(cast(Scenario, object()))


def test_configured_cue_coordinates_are_validated() -> None:
    selected = COURTYARD_SCENARIO
    gate = GateCue(selected.actor_id, selected.gate_id, 2, 2000, 0, 0, 1)
    gate_codec = EncounterPayloadCodec(gate.schema, selected)
    assert gate_codec.decode(gate_codec.encode(gate)) == gate
    with pytest.raises(ValueError, match="integer outside declared range"):
        gate_codec.encode(replace(gate, x_mm=1000))
    npc = NpcCue(selected.npc_id, Tick(2), 0, 1, 8, 2000, 2000)
    npc_codec = WatchPayloadCodec(npc.schema, selected)
    assert npc_codec.decode(npc_codec.encode(npc)) == npc
    with pytest.raises(ValueError, match="integer outside declared range"):
        npc_codec.encode(replace(npc, cell=6))
    # Registered names from the old room remain invalid facts in the selected room.
    with pytest.raises(ValueError, match="invalid encounter pair"):
        gate_codec.encode(replace(gate, target_id=EntityId("object:gate")))
