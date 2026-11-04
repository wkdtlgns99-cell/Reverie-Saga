"""Real visited-local COMMIT and saved routine/inventory invariants."""

from dataclasses import replace
from pathlib import Path

import pytest

from app.durable import create_durable
from app.world_catalog import load_world
from app.world_population_registry import population_world_bundle
from app.world_session import foot_command, open_world_session, world_checkpoint
from contracts.turn import TurnCommitted
from domain.primitives import EntityId
from domain.world import Resident, elaborate_place
from domain.world_population import (
    DAY_SECONDS,
    InventoryRecord,
    InventoryState,
    SettlementRecord,
    resident_activity,
)
from domain.world_travel import TravelerRecord, TravelState
from orchestration.world_population import InventoryCodec, SettlementCodec


def test_bootstrap_only_starting_city_is_detailed_and_inventory_is_saved() -> None:
    checkpoint = world_checkpoint(load_world(), living=True)
    assert len(checkpoint.core.components) == 14
    settlements = tuple(c for c in checkpoint.core.components if isinstance(c, SettlementRecord))
    assert len(settlements) == 12
    assert [c.entity_id for c in settlements if c.state is not None] == ["place:p0-a"]
    inventory = next(c for c in checkpoint.core.components if isinstance(c, InventoryRecord))
    assert inventory.state == InventoryState(0, ())


def test_actual_arrival_atomically_commits_local_definitions_and_visits(tmp_path: Path) -> None:
    world = load_world()
    checkpoint = world_checkpoint(world, living=True)
    route = next(r for r in world.routes if r.origin == "place:p0-a")
    components = tuple(
        replace(
            c,
            state=TravelState(
                "place:p0-a", "place:p0-b", route.distance_km * 1000 - 1, ("place:p0-a",)
            ),
        )
        if isinstance(c, TravelerRecord)
        else c
        for c in checkpoint.core.components
    )
    near_end = replace(checkpoint, core=replace(checkpoint.core, components=components))
    bundle = (population_world_bundle(world),)
    path = tmp_path / "world.sqlite"
    with create_durable(path, near_end, bundles=bundle) as session:
        command = foot_command(session.protocol(), "place:p0-b")
        result = session.submit(command, attachment_id=session.attachment_id)
        assert isinstance(result.outcome, TurnCommitted), result
        core = session.snapshot()
        traveler = next(c for c in core.components if isinstance(c, TravelerRecord))
        local = next(
            c
            for c in core.components
            if isinstance(c, SettlementRecord) and c.entity_id == "place:p0-b"
        )
        assert traveler.state.visited == ("place:p0-a", "place:p0-b")
        assert local.state == elaborate_place(world, "place:p0-b")
        assert result.diff is not None
        assert {d.target.family.component for d in result.diff.changes} == {
            "world.traveler",
            "world.settlement",
        }
        # Exact retry must neither regenerate residents nor append another visit.
        assert (
            session.submit(command, attachment_id=session.attachment_id).outcome == result.outcome
        )
        assert session.snapshot() == core
        session.export("slot01")
        session.load("slot01")
        assert session.snapshot().components == core.components
        loaded_path = session.working_path
    with open_world_session(loaded_path, world, living=True) as resumed:
        assert resumed.snapshot().components == core.components


@pytest.mark.parametrize(
    "tick,activity,site",
    [
        (0, "일하는 중", "가게"),
        (8 * 3600 - 1, "일하는 중", "가게"),
        (8 * 3600, "자유 시간", "시장"),
        (14 * 3600, "잠자는 중", "주거지"),
        (22 * 3600, "자유 시간", "시장"),
        (24 * 3600, "일하는 중", "가게"),
    ],
)
def test_saved_routine_boundaries_and_next_day(tick: int, activity: str, site: str) -> None:
    resident = Resident("resident:example", "나루", "상인", "신중함", "가게", 8, 16)
    actual = resident_activity(resident, tick)
    assert (actual.activity, actual.site) == (activity, site)
    assert resident_activity(resident, tick + DAY_SECONDS) == actual


def test_inventory_and_local_strict_codec_roundtrips() -> None:
    world = load_world()
    inventory = InventoryRecord(
        EntityId("actor:world-player"), InventoryState(7, (("item:grain", 2), ("item:water", 1)))
    )
    codec = InventoryCodec()
    assert codec.decode(inventory.entity_id, codec.encode(inventory)) == inventory
    local = SettlementRecord(EntityId("place:p0-a"), elaborate_place(world, "place:p0-a"))
    local_codec = SettlementCodec(world)
    assert local_codec.decode(local.entity_id, local_codec.encode(local)) == local
    invalid = (
        replace(local, state=replace(local.state, place_id="place:p5-a")) if local.state else local
    )
    with pytest.raises(ValueError, match="WORLD_LOCAL_DEFINITION"):
        local_codec.encode(invalid)


@pytest.mark.parametrize(
    "gold,items",
    [
        (-1, ()),
        (True, ()),
        (0, (("item:grain", 0),)),
        (0, (("item:grain", True),)),
        (0, (("item:grain", 1), ("item:grain", 2))),
    ],
)
def test_invalid_inventory_never_enters_saved_state(
    gold: int, items: tuple[tuple[str, int], ...]
) -> None:
    with pytest.raises(ValueError, match="integer outside declared range|WORLD_INVENTORY_ORDER"):
        InventoryState(gold, items)
