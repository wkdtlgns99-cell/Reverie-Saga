"""Registered replay and parent compatibility use real commands and state IO."""

from dataclasses import replace
from pathlib import Path

import pytest

from app.headless import replay_runner, state_io
from app.npc_cycle import cycle_bundle
from contracts.persistence import DurableCheckpoint
from contracts.replay import ReplayFixture
from domain.npc_assistance_memory import AssistanceMemoryRecord
from tests.integration.test_assistance_memory_clients import session, prepare, memory
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_assistance_memory import CHILD_FLAGS
from tests.integration.test_reach_gate_aid import FLAGS


def test_selected_child_replays_actual_causal_records(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        prepare(owner, 15)
        owner.act("bell")
        expected = memory(owner)
        assert expected.total_assists == 1 and expected.entries[0].source_kind == "answered_call"
        segment = owner.owner.retained_segment()
        fixture = ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace)
        selected = (cycle_bundle(approved_content(), **CHILD_FLAGS),)
        assert replay_runner(fixture, bundles=selected).run(segment.trace) == ()
        current = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        selected[0].checkpoint_policy.validate(current.core, current.protocol)
        record = next(r for r in current.core.components if type(r) is AssistanceMemoryRecord)
        variants = (
            replace(
                record,
                state=replace(
                    record.state,
                    entries=(replace(record.state.entries[0], cause_event_id="e1-" + "f" * 64),),
                ),
            ),
            replace(
                record,
                state=replace(
                    record.state, entries=(replace(record.state.entries[0], source_kind="wake"),)
                ),
            ),
        )
        for invalid in variants:
            core = replace(
                current.core,
                components=tuple(invalid if r is record else r for r in current.core.components),
            )
            with pytest.raises(ValueError, match="^NPC_ASSISTANCE_MEMORY_SOURCE$"):
                selected[0].checkpoint_policy.validate(core, current.protocol)
        with pytest.raises(ValueError, match="^NPC_ASSISTANCE_MEMORY_INPUT$"):
            selected[0].checkpoint_policy.validate(
                replace(
                    current.core,
                    components=tuple(r for r in current.core.components if r is not record),
                ),
                current.protocol,
            )
    finally:
        owner.close()


def test_all_parent_cycle_selections_false_keep_exact_bundle_documents() -> None:
    names = tuple(k for k in FLAGS if k not in ("npc_memory", "npc_cycle"))
    content = approved_content()
    for length in range(len(names) + 1):
        flags = dict.fromkeys(names[:length], True)
        original = cycle_bundle(content, **flags)
        explicit = cycle_bundle(content, **flags, npc_assistance_memory=False)
        assert original.feature_id == explicit.feature_id
        assert original.schema_document == explicit.schema_document
        assert original.rules_document == explicit.rules_document
        assert tuple(b.engine.manifest for b in original.bindings) == tuple(
            b.engine.manifest for b in explicit.bindings
        )
        assert state_io((original,)).pins == state_io((explicit,)).pins
