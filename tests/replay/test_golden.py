from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.headless import replay_runner
from contracts.errors import ReplayFormatError
from contracts.replay import ReplayFixture
from domain.canonical import array_value, canonical_json, decode_json, object_value
from orchestration.replay import Recorder, decode_fixture, encode_fixture
from tests.unit.test_canonical import vectors


from app.feature_registry import feature_bundles
from app.headless import state_io
from domain.primitives import EntityId

IO = state_io(feature_bundles(EntityId("actor:toy")))
core_hash, protocol_document = IO.hash_core, IO.encode_protocol


def fixture() -> ReplayFixture:
    return decode_fixture((Path(__file__).parent / "fixtures/skeleton_v1.json").read_bytes(), io=IO)


def test_core_trace() -> None:
    data = fixture()
    assert len(data.trace.steps) == 5
    assert decode_json(encode_fixture(data, io=IO)) == vectors()["golden_fixture"]
    assert replay_runner(data).run(data.trace) == ()


def test_self_consistent_wrong_leaf_and_digest_only_mismatch() -> None:
    negative = object_value(vectors()["negative_vectors"])
    wrong = decode_fixture(canonical_json(negative["self_consistent_wrong_step1_fixture"]), io=IO)
    mismatches = replay_runner(wrong).run(wrong.trace)
    assert (mismatches[0].step_index, mismatches[0].path, mismatches[0].expected, mismatches[0].actual) == (0, "$core.components[1].fields.x", "2", "1")
    data = fixture()
    step = replace(data.trace.steps[0], expected_witness=None, expected_core_hash="f" * 64)
    mismatches = replay_runner(data).run(replace(data.trace, steps=(step,)))
    assert len(mismatches) == 1 and mismatches[0].path == "$core_hash"


def test_corrupt_fixture_rejected_before_execution() -> None:
    document = object_value(vectors()["golden_fixture"])
    trace = object_value(document["trace"])
    first = object_value(array_value(trace["steps"])[0])
    bad_first = {**first, "core_hash": "f" * 64}
    with pytest.raises(ReplayFormatError, match="witness digest"):
        decode_fixture(canonical_json({**document, "trace": {**trace, "steps": (bad_first,)}}), io=IO)
    header = object_value(trace["header"])
    for key, value in (("initial_core_hash", "f" * 64), ("schema_fingerprint", "f" * 64), ("rng_version", "unsupported")):
        with pytest.raises(ReplayFormatError):
            decode_fixture(canonical_json({**document, "trace": {**trace, "header": {**header, key: value}}}), io=IO)
    for body in (b'{}', b'{"format_version":1,"format_version":1}', b'"\\ud800"'):
        with pytest.raises(ReplayFormatError):
            decode_fixture(body, io=IO)


def test_recorder_captures_real_publications_and_is_bounded() -> None:
    from app.headless import _CheckpointFactory
    data = fixture()
    session = _CheckpointFactory(feature_bundles(EntityId("actor:toy"))).restore(data.initial_core, data.initial_protocol)
    recorder = Recorder(data.trace.header, io=IO)
    for step in data.trace.steps:
        session.driver.submit(step.command)
        assert recorder.record(step.command, session.last_publication(), session.snapshot(), session.protocol()) == step
    assert recorder.finish() == data.trace
    assert replay_runner(data).run(recorder.finish()) == ()
    # Each repeated stale submission is real and preserves the head. No golden is generated here.
    stale = data.trace.steps[-1].command
    for _ in range(4096 - len(data.trace.steps)):
        session.driver.submit(stale)
        recorder.record(stale, session.last_publication(), session.snapshot(), session.protocol())
    with pytest.raises(ReplayFormatError, match="cap"):
        recorder.record(stale, session.last_publication(), session.snapshot(), session.protocol())
    assert len(recorder.finish().steps) == 4096
