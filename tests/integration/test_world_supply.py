"""Supply commands through registered admission,simulation,durability and replay."""

from pathlib import Path
import time
from dataclasses import replace

import pytest

from app.headless import restore_checkpoint, state_io
from app.world_catalog import load_world
from app.world_session import open_world_session, world_checkpoint, world_command
from app.world_supply_registry import supply_world_bundle
from contracts.turn import TurnCommitted, TurnRejected
from contracts.world_supply import SupplyAction, SupplyActed
from contracts.world_time import WorldWait
from domain.world import elaborate_place
from domain.world_population import InventoryRecord
from domain.world_supply import SupplyRecord, SupplyScenario
from domain.world_supply import SupplyState, scenario_from_seed


def action(operation: str, *, npc_id: str = "", place_id: str = "place:p0-a") -> SupplyAction:
    local = elaborate_place(load_world(), place_id)
    npc = local.residents[0 if operation == "collect" else 1].id
    return SupplyAction(place_id, npc_id or npc, operation)


def test_supply_live_flow_exact_retry_save_restart_and_timing(tmp_path: Path) -> None:
    world = load_world()
    scenario = SupplyScenario()
    path = tmp_path / "supply.sqlite"
    with open_world_session(path, world, supply=scenario) as session:
        for seconds in (16, 14):
            result = session.submit(
                world_command(session.protocol(), WorldWait(seconds)),
                attachment_id=session.attachment_id,
            )
            assert isinstance(result.outcome, TurnCommitted), result
        state = next(
            c.state
            for c in session.snapshot().components
            if isinstance(c, SupplyRecord) and c.entity_id == scenario.place_id
        )
        assert state.stock == 2
        for operation in ("accept", "collect", "collect", "deliver"):
            command = world_command(session.protocol(), action(operation))
            start = time.perf_counter()
            result = session.submit(command, attachment_id=session.attachment_id)
            assert time.perf_counter() - start < 2
            assert isinstance(result.outcome, TurnCommitted), result
            assert result.facts[-1].payload == SupplyActed(
                command.actor_id, scenario.place_id, action(operation).npc_id, operation
            )
            before = session.snapshot()
            assert (
                session.submit(command, attachment_id=session.attachment_id).outcome
                == result.outcome
            )
            assert session.snapshot() == before
        core = session.snapshot()
        assert core.tick == 34
        inventory = next(c.state for c in core.components if isinstance(c, InventoryRecord))
        assert (inventory.gold, inventory.items) == (5, ())
        state = next(
            c.state
            for c in core.components
            if isinstance(c, SupplyRecord) and c.entity_id == scenario.place_id
        )
        assert (state.stage, state.treasury, state.repair_used) == (2, 10, 2)
        session.export("slot01")
        session.load("slot01")
        assert session.snapshot().components == core.components
        saved_path = session.working_path
    with open_world_session(saved_path, world, supply=scenario) as resumed:
        assert resumed.snapshot().components == core.components


def test_confirm_revalidates_deadline_role_and_missing_resources(tmp_path: Path) -> None:
    scenario = SupplyScenario(start_tick=1, end_tick=6)
    with open_world_session(tmp_path / "world.sqlite", load_world(), supply=scenario) as session:
        for payload, code in (
            (action("accept", npc_id="resident:wrong"), "SUPPLY_WRONG_NPC"),
            (action("accept", place_id="place:p0-b"), "SUPPLY_OUT_OF_REACH"),
        ):
            before = session.snapshot(), session.protocol()
            result = session.submit(
                world_command(session.protocol(), payload), attachment_id=session.attachment_id
            )
            assert isinstance(result.outcome, TurnRejected)
            assert result.outcome.failure.code == code
            assert (session.snapshot(), session.protocol()) == before
        result = session.submit(
            world_command(session.protocol(), action("accept")), attachment_id=session.attachment_id
        )
        assert isinstance(result.outcome, TurnCommitted), result
        before = session.snapshot(), session.protocol()
        result = session.submit(
            world_command(session.protocol(), action("deliver")),
            attachment_id=session.attachment_id,
        )
        assert isinstance(result.outcome, TurnRejected)
        assert result.outcome.failure.code == "SUPPLY_ITEMS_MISSING"
        assert (session.snapshot(), session.protocol()) == before
        session.submit(
            world_command(session.protocol(), WorldWait(4)), attachment_id=session.attachment_id
        )
        before = session.snapshot(), session.protocol()
        result = session.submit(
            world_command(session.protocol(), action("collect")),
            attachment_id=session.attachment_id,
        )
        assert isinstance(result.outcome, TurnRejected)
        assert result.outcome.failure.code == "SUPPLY_INACTIVE"
        assert (session.snapshot(), session.protocol()) == before


def test_all_offscreen_cities_and_supply_actions_replay_identically() -> None:
    world = load_world()
    scenario = SupplyScenario(start_tick=1, end_tick=50)
    bundle = (supply_world_bundle(world, scenario),)
    cp = world_checkpoint(world, supply=scenario)
    a = restore_checkpoint(cp.core, cp.protocol, bundles=bundle)
    b = restore_checkpoint(cp.core, cp.protocol, bundles=bundle)
    io = state_io(bundle)
    for payload in (
        action("accept"),
        action("collect"),
        action("collect"),
        action("deliver"),
        WorldWait(16),
        WorldWait(16),
    ):
        command = world_command(a.protocol(), payload)
        outcome = a.driver.submit(command)
        assert isinstance(outcome, TurnCommitted), outcome
        assert outcome == b.driver.submit(command)
        assert io.hash_core(a.snapshot()) == io.hash_core(b.snapshot())
    supplies = tuple(c for c in a.snapshot().components if isinstance(c, SupplyRecord))
    assert len(supplies) == 12
    assert all(s.state.consumed == 1 for s in supplies)
    assert all(s.state.stock == 2 for s in supplies)


@pytest.mark.parametrize(
    "corruption,code",
    [
        ("period", "WORLD_SUPPLY_PERIOD_BINDING"),
        ("gold", "WORLD_SUPPLY_RESOURCE_BINDING"),
        ("city", "WORLD_SUPPLY_CHECKPOINT"),
    ],
)
def test_checkpoint_rejects_impossible_period_goods_or_reward(corruption: str, code: str) -> None:
    world = load_world()
    scenario = SupplyScenario()
    cp = world_checkpoint(world, supply=scenario)
    components = tuple(
        c
        for c in cp.core.components
        if not (
            corruption == "city" and isinstance(c, SupplyRecord) and c.entity_id == "place:p5-b"
        )
    )
    if corruption == "period":
        components = tuple(
            replace(c, state=SupplyState(stock=2, consumed=1))
            if isinstance(c, SupplyRecord) and c.entity_id == "place:p0-a"
            else c
            for c in components
        )
    if corruption == "gold":
        components = tuple(
            replace(c, state=replace(c.state, gold=5)) if isinstance(c, InventoryRecord) else c
            for c in components
        )
    with pytest.raises(ValueError, match=code):
        state_io((supply_world_bundle(world, scenario),)).validate_checkpoint(
            replace(cp.core, components=components), cp.protocol
        )


def test_seed_variant_changes_distant_city_without_materializing_its_residents(
    tmp_path: Path,
) -> None:
    from app.world_worker import WorldWorker

    world = load_world()
    scenario = scenario_from_seed(world, "1" * 64)
    assert scenario.place_id != "place:p0-a"
    worker = WorldWorker(tmp_path / "variant.sqlite", world, scenario=scenario)
    try:
        remaining = scenario.start_tick + 60
        while remaining:
            seconds = min(16, remaining)
            update = worker.request("wait", seconds=seconds).result(timeout=10)
            remaining -= seconds
        assert update.state.place_id == "place:p0-a"
        assert len(update.residents) == 4
    finally:
        worker.close()
    from domain.world_population import SettlementRecord

    with open_world_session(tmp_path / "variant.sqlite", world, supply=scenario) as session:
        core = session.snapshot()
        affected = next(
            c
            for c in core.components
            if isinstance(c, SupplyRecord) and c.entity_id == scenario.place_id
        )
        distant = next(
            c
            for c in core.components
            if isinstance(c, SettlementRecord) and c.entity_id == scenario.place_id
        )
        assert affected.state.stock <= 1
        assert distant.state is None
