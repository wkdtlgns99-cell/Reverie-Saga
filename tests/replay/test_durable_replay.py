from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.durable import create_durable, resume_durable
from app.headless import _CheckpointFactory
from app.watch_registry import watch_bundle
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.watch import WaitCommand
from domain.canonical import array_value, object_value
from orchestration.replay import Runner
from tests.unit.durability_fixtures import checkpoint, io, requirements
from tests.unit.watch_fixtures import command


def test_retained_segment_runner_and_fresh_repeat(tmp_path: Path) -> None:
    selected = io()
    with create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        for value in array_value(object_value(requirements()["trace"])["steps"]):
            request = selected.decode_command(object_value(object_value(value)["command"]))
            owner.submit(request, attachment_id=owner.attachment_id)
        segment = owner.retained_segment()
        runner = Runner(segment.checkpoint.core, segment.checkpoint.protocol,
                        factory=_CheckpointFactory((watch_bundle(),)), io=selected)
        assert runner.run(segment.trace) == ()
        assert runner.run(segment.trace) == ()
        changed = replace(segment.trace.steps[1], expected_facts_hash="0" * 64)
        bad = replace(segment.trace, steps=(segment.trace.steps[0], changed, *segment.trace.steps[2:]))
        mismatch = runner.run(bad)
        assert len(mismatch) == 1 and mismatch[0].step_index == 1 and mismatch[0].path == "$facts_hash"


def test_reopen_next_wake_and_protocol_identity(tmp_path: Path) -> None:
    selected = io()
    with create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        owner.submit(command(WaitCommand(16)), attachment_id=owner.attachment_id)
        saved = DurableCheckpoint(owner.snapshot(), owner.protocol())
    with resume_durable(tmp_path / "work.sqlite", bundles=(watch_bundle(),)) as resumed:
        assert DurableCheckpoint(resumed.snapshot(), resumed.protocol()) == saved
        assert selected.decode_pending(resumed.snapshot().pending[0]).event.due_tick == 18
        resumed.submit(command(WaitCommand(2), revision=1, sequence=2), attachment_id=resumed.attachment_id)
        assert selected.decode_pending(resumed.snapshot().pending[0]).event.due_tick == 20
        segment = resumed.retained_segment()
        runner = Runner(segment.checkpoint.core, segment.checkpoint.protocol,
                        factory=_CheckpointFactory((watch_bundle(),)), io=selected)
        assert runner.run(segment.trace) == ()


def test_corrupt_segment_before_restore(tmp_path: Path) -> None:
    import sqlite3
    with create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        owner.submit(command(), attachment_id=owner.attachment_id)
    con = sqlite3.connect(tmp_path / "work.sqlite", autocommit=True)
    con.execute("UPDATE replay SET sha256=?", ("1" * 64,))
    con.close()
    with pytest.raises(SaveError, match="SAVE_CORRUPT"):
        resume_durable(tmp_path / "work.sqlite", bundles=(watch_bundle(),))
