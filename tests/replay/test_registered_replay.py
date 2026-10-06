from __future__ import annotations

from dataclasses import replace

import pytest

from app.headless import HeadlessSession, replay_runner, restore_checkpoint, state_io
from contracts.errors import ReplayFormatError
from contracts.replay import ReplayFixture, ReplaySession
from contracts.skeleton import FeatureBundle
from contracts.turn import ProtocolSnapshot, TurnDriver, TurnPublication
from domain.canonical import JsonObject, array_value, canonical_json, decode_json, hash_document, object_value
from domain.state_types import CoreSnapshot
from orchestration.replay import Recorder, Runner, decode_fixture, encode_fixture
from tests.unit.registered_io_fixtures import bundle, reference_body, session


def fixture(selected: FeatureBundle) -> ReplayFixture:
    return decode_fixture(reference_body(), io=state_io((selected,)))


def test_registered_roundtrip_trace() -> None:
    selected = bundle()
    io = state_io((selected,))
    data = fixture(selected)
    assert encode_fixture(data, io=io) == reference_body()
    assert replay_runner(data, bundles=(selected,)).run(data.trace) == ()
    live = session(selected)
    recorder = Recorder(data.trace.header, io=io)
    for step in data.trace.steps:
        live.driver.submit(step.command)
        recorded = recorder.record(step.command, live.last_publication(), live.snapshot(), live.protocol())
        assert recorded == step  # Independent stdlib reference, not Recorder-generated expectations.
    assert recorder.finish() == data.trace


class _ObservedSession:
    def __init__(self, owner: HeadlessSession, drop_facts: bool) -> None:
        self._owner = owner
        self._drop = drop_facts

    @property
    def driver(self) -> TurnDriver:
        return self._owner.driver

    def snapshot(self) -> CoreSnapshot:
        return self._owner.snapshot()

    def protocol(self) -> ProtocolSnapshot:
        return self._owner.protocol()

    def last_publication(self) -> TurnPublication:
        pub = self._owner.last_publication()
        return replace(pub, facts=()) if self._drop else pub


class _Factory:
    def __init__(self, selected: FeatureBundle, drop_facts: bool = False) -> None:
        self.selected = selected
        self.drop_facts = drop_facts
        self.owners: list[HeadlessSession] = []

    def restore(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> ReplaySession:
        owner = restore_checkpoint(core, protocol, bundles=(self.selected,))
        self.owners.append(owner)
        return _ObservedSession(owner, self.drop_facts)


def test_registered_fact_loss() -> None:
    selected = bundle()
    data = fixture(selected)
    factory = _Factory(selected, True)
    mismatches = Runner(data.initial_core, data.initial_protocol, factory=factory, io=state_io((selected,))).run(data.trace)
    assert [(m.step_index, m.path, m.actual) for m in mismatches] == [(0, "$facts[0]", "<missing>"), (1, "$facts[0]", "<missing>")]
    assert factory.owners[0].snapshot().components == data.initial_core.components
    assert factory.owners[0].protocol().revision == 2


def test_registered_wrong_leaf() -> None:
    selected = bundle()
    io = state_io((selected,))
    wrong = decode_fixture(reference_body(first_value=6), io=io)
    mismatches = replay_runner(wrong, bundles=(selected,)).run(wrong.trace)
    assert (mismatches[0].step_index, mismatches[0].path, mismatches[0].expected, mismatches[0].actual) == (0, "$core.components[0].fields.value", "6", "5")
    doc = object_value(decode_json(reference_body()))
    trace = object_value(doc["trace"])
    steps = array_value(trace["steps"])
    first = object_value(steps[0])
    with pytest.raises(ReplayFormatError, match="corrupt witness digest"):
        decode_fixture(canonical_json({**doc, "trace": {**trace, "steps": ({**first, "core_hash": "f" * 64}, *steps[1:])}}), io=io)


def test_registered_pins_before_execution() -> None:
    selected = bundle()
    io = state_io((selected,))
    data = fixture(selected)
    factory = _Factory(selected)
    wrong_io = state_io((replace(selected, rules_document={**selected.rules_document, "new_rule": 1}),))
    with pytest.raises(ReplayFormatError):
        Runner(data.initial_core, data.initial_protocol, factory=factory, io=wrong_io).run(data.trace)
    assert factory.owners == []
    step = data.trace.steps[-1]
    assert step.expected_witness is not None
    core = object_value(decode_json(step.expected_witness.canonical_core_json))
    component = object_value(array_value(core["components"])[0])
    # A self-consistent unsupported schema in the LAST step must fail before FIRST execution.
    invalid: JsonObject = {**core, "components": ({**component, "schema": {"kind": "fixture.gauge", "version": 2}},)}
    witness = replace(step.expected_witness, canonical_core_json=canonical_json(invalid))
    bad_trace = replace(data.trace, steps=(*data.trace.steps[:-1], replace(step, expected_witness=witness)))
    with pytest.raises(ReplayFormatError, match="UNSUPPORTED_SCHEMA"):
        Runner(data.initial_core, data.initial_protocol, factory=factory, io=io).run(bad_trace)
    assert factory.owners == []
    with pytest.raises(ReplayFormatError):
        replay_runner(data).run(data.trace)  # Foreign schemas always need an explicit selected registry.


def test_fresh_registry_sessions() -> None:
    selected = bundle()
    data = fixture(selected)
    factory = _Factory(selected)
    runner = Runner(data.initial_core, data.initial_protocol, factory=factory, io=state_io((selected,)))
    assert runner.run(data.trace) == () and runner.run(data.trace) == ()
    assert len(factory.owners) == 2 and factory.owners[0] is not factory.owners[1]
    first = factory.owners[0].snapshot()
    assert first == factory.owners[1].snapshot()
    different = bundle()
    assert state_io((different,)).pins == state_io((selected,)).pins
    assert replay_runner(fixture(different), bundles=(different,)).run(data.trace) == ()
    assert hash_document("protocol/v1", state_io((selected,)).encode_protocol(factory.owners[0].protocol())) == data.trace.steps[-1].expected_protocol_hash
