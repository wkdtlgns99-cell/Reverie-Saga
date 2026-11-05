"""Physical journey arithmetic and catch-up checked against literal second stepping."""

from dataclasses import replace

import pytest

from app.world_catalog import load_transport, load_world
from domain.world_supply import SupplyScenario, SupplyState, advance_supply, advance_supply_interval
from domain.world_transport import (
    JourneyState,
    plan_journey,
    validate_journey,
    validate_journey_binding,
)
from domain.world_travel import TravelState


def test_carriage_stops_at_exact_checkpoint_waits_for_choice_then_arrives() -> None:
    world = load_world()
    rules = load_transport(world)
    travel = TravelState("place:p0-a", "", 0, ("place:p0-a",))
    boarded = plan_journey(world, rules, JourneyState(), travel, 0, "board", "place:p0-b")
    assert boarded.seconds == 1 and boarded.journey.started_tick == 1
    blocked = plan_journey(world, rules, boarded.journey, travel, 1, "advance")
    assert blocked.seconds == 500 and blocked.journey.progress_m == 2500
    assert blocked.journey.phase == "blocked" and blocked.travel == travel
    with pytest.raises(ValueError, match="^JOURNEY_BLOCKED$"):
        plan_journey(world, rules, blocked.journey, travel, 501, "resume")
    waited = plan_journey(world, rules, blocked.journey, travel, 501, "wait")
    assert waited.seconds == 299 and waited.journey == blocked.journey
    resumed = plan_journey(world, rules, waited.journey, travel, 800, "resume")
    assert resumed.seconds == 1 and resumed.journey.phase == "outbound"
    arrival = plan_journey(world, rules, resumed.journey, travel, 801, "advance")
    assert arrival.seconds == 1500 and arrival.journey == JourneyState()
    assert arrival.travel == TravelState("place:p0-b", "", 0, ("place:p0-a", "place:p0-b"))


def test_return_traverses_real_distance_without_new_visit() -> None:
    world = load_world()
    rules = load_transport(world)
    travel = TravelState("place:p0-a", "", 0, ("place:p0-a",))
    state = plan_journey(world, rules, JourneyState(), travel, 0, "board", "place:p0-b").journey
    state = plan_journey(world, rules, state, travel, 1, "advance").journey
    returning = plan_journey(world, rules, state, travel, 501, "return")
    assert returning.seconds == 1 and returning.journey.progress_m == 2500
    result = plan_journey(world, rules, returning.journey, travel, 502, "advance")
    assert result.seconds == 500 and result.journey.phase == "idle" and result.travel == travel


def test_closure_open_at_crossing_reverse_route_and_ship_rounding() -> None:
    world = load_world()
    rules = load_transport(world)
    travel = TravelState("place:p0-a", "", 0, ("place:p0-a",))
    boarded = plan_journey(world, rules, JourneyState(), travel, 299, "board", "place:p0-b")
    # Crosses2500m at800,the exclusive closure end;no stop.
    result = plan_journey(world, rules, boarded.journey, travel, 300, "advance")
    assert result.seconds == 2000 and result.journey.phase == "idle"
    reverse = TravelState("place:p0-b", "", 0, ("place:p0-b",))
    boarded = plan_journey(world, rules, JourneyState(), reverse, 0, "board", "place:p0-a")
    result = plan_journey(world, rules, boarded.journey, reverse, 1, "advance")
    assert result.seconds == 2000 and result.journey.phase == "idle"
    ship = plan_journey(world, rules, JourneyState(), reverse, 0, "board", "place:p5-b")
    assert ship.journey.mode == "ship"
    state, tick = ship.journey, 1
    while state.phase != "idle":
        step = plan_journey(world, rules, state, reverse, tick, "advance")
        tick += step.seconds
        state = step.journey
    assert tick == 1 + (179000 + 7) // 8
    assert step.travel.place_id == "place:p5-b"


@pytest.mark.parametrize(
    "start,end", [(0, 0), (0, 1), (0, 29), (29, 30), (19, 60), (20, 630), (600, 650), (100, 3700)]
)
@pytest.mark.parametrize("place", ["place:p0-a", "place:p1-a"])
def test_supply_catchup_matches_literal_seconds(start: int, end: int, place: str) -> None:
    scenario = SupplyScenario()
    before = SupplyState()
    for tick in range(1, start + 1):
        before = advance_supply(before, scenario, place, tick)
    expected = before
    for tick in range(start + 1, end + 1):
        expected = advance_supply(expected, scenario, place, tick)
    assert advance_supply_interval(before, scenario, place, start, end) == expected


def test_malformed_idle_mode_and_binding_are_rejected() -> None:
    with pytest.raises(ValueError, match="^JOURNEY_IDLE$"):
        validate_journey(replace(JourneyState(), progress_m=1))
    with pytest.raises(ValueError, match="integer outside declared range"):
        validate_journey(replace(JourneyState(), progress_m=True))
    world = load_world()
    rules = load_transport(world)
    travel = TravelState("place:p0-a", "", 0, ("place:p0-a",))
    with pytest.raises(ValueError, match="^JOURNEY_BINDING$"):
        validate_journey_binding(
            world,
            rules,
            JourneyState("place:p0-a", "place:p0-b", "ship", 0, "outbound", 1),
            travel,
            1,
        )


@pytest.mark.parametrize("resolved", (False, True))
def test_catchup_varied_intervals_and_nonperiodic_expiry(resolved: bool) -> None:
    scenario = SupplyScenario("place:p0-a", 17, 637)
    state = (
        SupplyState(stage=2, claimed=2, repair_used=2, warehouse=4, treasury=10, resolved_tick=10)
        if resolved
        else SupplyState(stage=1)
    )
    start = 10
    # Independently step every second,including expiry637 (neither20nor30boundary),
    # empty intervals and successive summaries spanning several periodic collisions.
    for duration in (0, 1, 7, 59, 560, 1, 29, 3600, 43):
        expected = state
        for tick in range(start + 1, start + duration + 1):
            expected = advance_supply(expected, scenario, scenario.place_id, tick)
        actual = advance_supply_interval(
            state, scenario, scenario.place_id, start, start + duration
        )
        assert actual == expected
        assert actual.stage == (2 if resolved else 3 if start + duration >= 637 else 1)
        state, start = actual, start + duration
