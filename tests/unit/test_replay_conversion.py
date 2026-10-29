"""Canonical-byte replay comparison preserves detailed mismatches and witness forms."""

from dataclasses import replace
import json
from app.headless import replay_runner
from tests.replay.test_golden import fixture
from contracts.replay import ReplayWitness


def test_noncanonical_witness_spacing_still_replays() -> None:
    source = fixture()
    steps = []
    for step in source.trace.steps:
        witness = step.expected_witness
        assert witness is not None
        fields = (
            witness.canonical_core_json,
            witness.canonical_protocol_json,
            witness.canonical_facts_json,
            witness.canonical_diff_json,
        )
        pretty = ReplayWitness(
            *(
                json.dumps(json.loads(body), ensure_ascii=False, indent=2).encode()
                for body in fields
            )
        )
        steps.append(replace(step, expected_witness=pretty))
    assert replay_runner(source).run(replace(source.trace, steps=tuple(steps))) == ()
