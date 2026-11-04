"""Independent supply timelines,conservation and deterministic scenario variation."""

from dataclasses import replace

import pytest

from app.world_catalog import load_world
from domain.world import elaborate_place
from domain.world_population import InventoryState
from domain.world_supply import (
    SupplyScenario,
    SupplyState,
    advance_supply,
    scenario_from_seed,
    supply_action,
    supply_activity,
)


def advance(end: int, *, scenario: SupplyScenario = SupplyScenario()) -> SupplyState:
    state = SupplyState()
    for tick in range(1, end + 1):
        state = advance_supply(state, scenario, scenario.place_id, tick)
    return state


@pytest.mark.parametrize(
    "tick,stock,missed", [(29, 3, 0), (30, 2, 0), (60, 1, 0), (90, 0, 0), (120, 0, 1)]
)
def test_blocked_market_exhausts_without_regenerating_goods(
    tick: int, stock: int, missed: int
) -> None:
    state = advance(tick)
    assert (state.stock, state.missed) == (stock, missed)
    assert state.warehouse == 6
    assert 9 + state.received == state.stock + state.warehouse + state.consumed + state.claimed


def test_delivery_consumes_cargo_pays_once_and_reopens_route() -> None:
    scenario = SupplyScenario()
    state = advance(90)
    inventory = InventoryState(0, ())
    state, inventory = supply_action(state, inventory, scenario, scenario.place_id, "accept", 91)
    for tick in (92, 93):
        state, inventory = supply_action(
            state, inventory, scenario, scenario.place_id, "collect", tick
        )
    assert state.warehouse == 4
    assert inventory.items == (("item:supply-p0-a", 2),)
    state, inventory = supply_action(state, inventory, scenario, scenario.place_id, "deliver", 94)
    assert (state.stage, state.stock, state.repair_used, state.treasury, state.resolved_tick) == (
        2,
        0,
        2,
        10,
        94,
    )
    assert inventory == InventoryState(5, ())
    state = advance_supply(state, scenario, scenario.place_id, 100)
    assert (state.stock, state.warehouse) == (1, 4)
    with pytest.raises(ValueError, match="SUPPLY_INACTIVE"):
        supply_action(state, inventory, scenario, scenario.place_id, "deliver", 101)


def test_expiry_retains_collected_items_but_never_pays() -> None:
    scenario = SupplyScenario(end_tick=34)
    state, inventory = supply_action(
        advance(30), InventoryState(0, ()), scenario, scenario.place_id, "accept", 31
    )
    state, inventory = supply_action(state, inventory, scenario, scenario.place_id, "collect", 32)
    expired = advance_supply(state, scenario, scenario.place_id, 34)
    assert (expired.stage, expired.claimed, expired.treasury) == (3, 1, 15)
    assert inventory == InventoryState(0, (("item:supply-p0-a", 1),))
    with pytest.raises(ValueError, match="SUPPLY_INACTIVE"):
        supply_action(expired, inventory, scenario, scenario.place_id, "deliver", 34)


def test_routines_change_from_actual_shortage_but_sleep_is_preserved() -> None:
    local = elaborate_place(load_world(), "place:p0-a")
    scenario = SupplyScenario(end_tick=86400)
    empty = advance(90)
    activities = tuple(
        supply_activity(r, i, 90, scenario, local.place_id, empty)
        for i, r in enumerate(local.residents)
    )
    assert tuple(a.activity for a in activities) == (
        "대체 보급로 찾는 중",
        "물자 부족으로 판매 제한",
        "배급 대기 중",
        "배급 대기 중",
    )
    assert activities[0].site == local.residents[0].workplace
    assert (
        supply_activity(local.residents[0], 0, 14 * 3600, scenario, local.place_id, empty).activity
        == "잠자는 중"
    )


def test_seed_variants_reuse_identical_world_and_are_repeatable() -> None:
    world = load_world()
    scenarios = {scenario_from_seed(world, f"{seed:064x}") for seed in range(30)}
    assert len(scenarios) > 20
    assert len({s.place_id for s in scenarios}) > 6
    for scenario in scenarios:
        world.place(scenario.place_id)
        assert 30 <= scenario.start_tick <= 90
        assert 300 <= scenario.end_tick - scenario.start_tick <= 900
    assert scenario_from_seed(world, "1" * 64) == scenario_from_seed(world, "1" * 64)
    with pytest.raises(ValueError, match="SUPPLY_SCENARIO_SEED"):
        scenario_from_seed(world, "invalid")


def test_supply_rejects_invalid_conservation_and_boolean_counters() -> None:
    with pytest.raises(ValueError, match="SUPPLY_CONSERVATION"):
        replace(SupplyState(), stock=2)
    with pytest.raises(ValueError, match="integer outside declared range"):
        replace(SupplyState(), claimed=True)
