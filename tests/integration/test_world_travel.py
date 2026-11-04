"""Exercise real registered world commands,COMMIT and SQLite restart/slots."""

from dataclasses import replace
from pathlib import Path

import pytest

from app.durable import create_durable
from app.headless import restore_checkpoint, state_io
from app.world_catalog import load_world
from app.world_registry import world_bundle
from app.world_session import foot_command, open_world_session, world_checkpoint
from contracts.turn import TurnCommitted, TurnRejected
from domain.primitives import WorldRevision
from domain.world_travel import TravelState, TravelerRecord, validate_traveler


def test_actual_footstep_commits_position_time_fact_and_cue_then_restarts(tmp_path: Path) -> None:
    world = load_world()
    path = tmp_path / "world.sqlite"
    with open_world_session(path, world) as session:
        command = foot_command(session.protocol(), "place:p0-b")
        result = session.submit(command, attachment_id=session.attachment_id)
        assert isinstance(result.outcome, TurnCommitted), result
        assert session.snapshot().tick == 1
        assert session.snapshot().components == (
            TravelerRecord(
                command.actor_id, TravelState("place:p0-a", "place:p0-b", 1, ("place:p0-a",))
            ),
        )
        assert len(result.facts) == len(result.cues) == 1
        core = session.snapshot()
        assert (
            session.submit(command, attachment_id=session.attachment_id).outcome == result.outcome
        )
        assert session.snapshot() == core
    with open_world_session(path, world) as resumed:
        assert resumed.snapshot() == core
        reverse = foot_command(resumed.protocol(), "place:p0-b", -1)
        result = resumed.submit(reverse, attachment_id=resumed.attachment_id)
        assert isinstance(result.outcome, TurnCommitted), result
        assert resumed.snapshot().tick == 2
        record = resumed.snapshot().components[0]
        assert isinstance(record, TravelerRecord)
        assert record.state == TravelState("place:p0-a", "", 0, ("place:p0-a",))


@pytest.mark.parametrize(
    "destination,direction,code",
    [
        ("place:p1-a", 1, "WORLD_NOT_ADJACENT"),
        ("place:p0-a", 1, "WORLD_NOT_ADJACENT"),
        ("place:p0-b", -1, "WORLD_NOT_ON_ROUTE"),
        ("place:p0-b", 0, "INVALID_COMMAND"),
    ],
)
def test_rejected_walk_preserves_entire_checkpoint(
    tmp_path: Path, destination: str, direction: int, code: str
) -> None:
    with open_world_session(tmp_path / "world.sqlite", load_world()) as session:
        before = session.snapshot(), session.protocol()
        result = session.submit(
            foot_command(session.protocol(), destination, direction),
            attachment_id=session.attachment_id,
        )
        assert isinstance(result.outcome, TurnRejected), result
        assert result.outcome.failure.code == code
        assert (session.snapshot(), session.protocol()) == before


def test_arrival_adds_visit_at_exact_road_end_and_water_is_not_walkable(tmp_path: Path) -> None:
    world = load_world()
    checkpoint = world_checkpoint(world)
    route = next(r for r in world.routes if r.origin == "place:p0-a")
    actor = checkpoint.core.components[0].entity_id
    near_end = TravelerRecord(
        actor,
        TravelState("place:p0-a", "place:p0-b", route.distance_km * 1000 - 1, ("place:p0-a",)),
    )
    checkpoint = replace(checkpoint, core=replace(checkpoint.core, components=(near_end,)))
    with create_durable(
        tmp_path / "world.sqlite", checkpoint, bundles=(world_bundle(world),)
    ) as session:
        result = session.submit(
            foot_command(session.protocol(), "place:p0-b"), attachment_id=session.attachment_id
        )
        assert isinstance(result.outcome, TurnCommitted), result
        record = session.snapshot().components[0]
        assert isinstance(record, TravelerRecord)
        assert record.state == TravelState("place:p0-b", "", 0, ("place:p0-a", "place:p0-b"))
        destination = next(p.id for p, r in world.neighbors("place:p0-b") if r.kind == "sea")
        before = session.snapshot(), session.protocol()
        result = session.submit(
            foot_command(session.protocol(), destination), attachment_id=session.attachment_id
        )
        assert isinstance(result.outcome, TurnRejected), result
        assert result.outcome.failure.code == "TRANSPORT_REQUIRED"
        assert (session.snapshot(), session.protocol()) == before


def test_midroute_save_load_creates_private_working_copy_and_preserves_progress(
    tmp_path: Path,
) -> None:
    with open_world_session(tmp_path / "world.sqlite", load_world()) as session:
        command = foot_command(session.protocol(), "place:p0-b")
        session.submit(command, attachment_id=session.attachment_id)
        saved = session.snapshot()
        session.export("slot01")
        command = foot_command(session.protocol(), "place:p0-b")
        session.submit(command, attachment_id=session.attachment_id)
        old_path = session.working_path
        old_token = session.attachment_id
        session.load("slot01")
        assert session.snapshot().components == saved.components
        assert session.snapshot().tick == saved.tick
        assert session.working_path != old_path
        assert session.attachment_id != old_token
        result = session.submit(
            foot_command(session.protocol(), "place:p0-b"), attachment_id=session.attachment_id
        )
        assert isinstance(result.outcome, TurnCommitted), result


def test_same_commands_replay_identically_through_existing_driver() -> None:
    world = load_world()
    checkpoint = world_checkpoint(world)
    bundles = (world_bundle(world),)
    io = state_io(bundles)
    first = restore_checkpoint(checkpoint.core, checkpoint.protocol, bundles=bundles)
    second = restore_checkpoint(checkpoint.core, checkpoint.protocol, bundles=bundles)
    for direction in (1, 1, -1, 1, -1, -1):
        command = foot_command(first.protocol(), "place:p0-b", direction)
        a = first.driver.submit(command)
        b = second.driver.submit(command)
        assert a == b
        assert io.hash_core(first.snapshot()) == io.hash_core(second.snapshot())
        assert first.last_publication() == second.last_publication()


def test_stale_revision_does_not_walk(tmp_path: Path) -> None:
    with open_world_session(tmp_path / "world.sqlite", load_world()) as session:
        command = foot_command(session.protocol(), "place:p0-b")
        result = session.submit(
            replace(command, expected_revision=WorldRevision(1)),
            attachment_id=session.attachment_id,
        )
        assert isinstance(result.outcome, TurnRejected)
        assert session.snapshot().tick == 0


@pytest.mark.parametrize("offset", [-1, True, 10_000])
def test_invalid_route_checkpoint_is_rejected(offset: int) -> None:
    with pytest.raises(ValueError, match="integer outside declared range|WORLD_TRAVEL_ROUTE"):
        validate_traveler(
            load_world(), TravelState("place:p0-a", "place:p0-b", offset, ("place:p0-a",))
        )
