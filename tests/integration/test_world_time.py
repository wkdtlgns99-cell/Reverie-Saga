"""Explicit recorded duration through real world admission,COMMIT and restart."""

from pathlib import Path

import pytest

from app.headless import restore_checkpoint, state_io
from app.world_catalog import load_world
from app.world_session import foot_command, open_world_session, world_checkpoint, world_command
from app.world_time_registry import timed_world_bundle
from contracts.turn import TurnCommitted, TurnRejected
from contracts.world_time import TimeCue, TimePassed, WorldWait


def test_wait_then_walk_commits_exact_elapsed_seconds_and_restarts(tmp_path: Path) -> None:
    path = tmp_path / "clock.sqlite"
    world = load_world()
    with open_world_session(path, world, timed=True) as session:
        original = session.snapshot().components
        command = world_command(session.protocol(), WorldWait(2))
        result = session.submit(command, attachment_id=session.attachment_id)
        assert isinstance(result.outcome, TurnCommitted), result
        assert session.snapshot().tick == 2
        assert session.snapshot().components == original
        assert len(result.facts) == len(result.cues) == 1
        assert result.facts[0].payload == TimePassed(0, 2)
        assert result.cues[0].payload == TimeCue(0, 2)
        assert (
            session.submit(command, attachment_id=session.attachment_id).outcome == result.outcome
        )
        result = session.submit(
            foot_command(session.protocol(), "place:p0-b"), attachment_id=session.attachment_id
        )
        assert isinstance(result.outcome, TurnCommitted), result
        assert session.snapshot().tick == 3
        expected = session.snapshot()
    with open_world_session(path, world, timed=True) as resumed:
        assert resumed.snapshot() == expected


def test_recorded_time_replays_identically_without_real_clock() -> None:
    world = load_world()
    bundle = (timed_world_bundle(world),)
    checkpoint = world_checkpoint(world, timed=True)
    a = restore_checkpoint(checkpoint.core, checkpoint.protocol, bundles=bundle)
    b = restore_checkpoint(checkpoint.core, checkpoint.protocol, bundles=bundle)
    io = state_io(bundle)
    for duration in (1, 16, 3):
        command = world_command(a.protocol(), WorldWait(duration))
        assert a.driver.submit(command) == b.driver.submit(command)
        assert a.last_publication() == b.last_publication()
        assert io.hash_core(a.snapshot()) == io.hash_core(b.snapshot())
    assert a.snapshot().tick == 20


@pytest.mark.parametrize("seconds", [0, -1, 17, True])
def test_invalid_time_command_preserves_state(tmp_path: Path, seconds: int) -> None:
    with open_world_session(tmp_path / "clock.sqlite", load_world(), timed=True) as session:
        before = session.snapshot(), session.protocol()
        result = session.submit(
            world_command(session.protocol(), WorldWait(seconds)),
            attachment_id=session.attachment_id,
        )
        assert isinstance(result.outcome, TurnRejected)
        assert result.outcome.failure.code == "INVALID_COMMAND"
        assert (session.snapshot(), session.protocol()) == before
