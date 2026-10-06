from __future__ import annotations

from dataclasses import replace
import hashlib

import pytest

from app.headless import HeadlessSession, replay_runner, restore_checkpoint, state_io
from app.trial_registry import trial_bundle
from contracts.errors import ReplayFormatError
from contracts.replay import ReplayFixture, ReplaySession
from contracts.skeleton import FeatureBundle
from contracts.turn import ProtocolSnapshot, TurnDriver, TurnPublication
from domain.canonical import JsonObject, array_value, canonical_json, decode_json, object_value
from domain.state_types import CoreSnapshot
from orchestration.replay import Recorder, Runner, decode_fixture, encode_fixture
from tests.unit.trial_fixtures import fixture_body, reference, session


def fixture() -> ReplayFixture:
    return decode_fixture(fixture_body(), io=state_io((trial_bundle(),)))


def test_trial_core_trace() -> None:
    data, selected = fixture(), trial_bundle()
    io = state_io((selected,))
    assert hashlib.sha256(fixture_body()).hexdigest() == reference("expected_fixture_canonical_sha256")
    assert encode_fixture(data, io=io) == fixture_body()
    assert replay_runner(data, bundles=(selected,)).run(data.trace) == ()


def test_trial_recorder_matches_independent_trace() -> None:
    data = fixture()
    io, live = state_io((trial_bundle(),)), session()
    recorder = Recorder(data.trace.header, io=io)
    for step in data.trace.steps:
        live.driver.submit(step.command)
        assert recorder.record(step.command, live.last_publication(), live.snapshot(), live.protocol()) == step
    assert recorder.finish() == data.trace


class _ObservedSession:
    def __init__(self, owner: HeadlessSession, drop_first: bool) -> None:
        self.owner = owner
        self.drop_first = drop_first

    @property
    def driver(self) -> TurnDriver:
        return self.owner.driver

    def snapshot(self) -> CoreSnapshot:
        return self.owner.snapshot()

    def protocol(self) -> ProtocolSnapshot:
        return self.owner.protocol()

    def last_publication(self) -> TurnPublication:
        pub = self.owner.last_publication()
        return replace(pub, facts=()) if self.drop_first and self.owner.snapshot().tick == 1 else pub


class _Factory:
    def __init__(self, selected: FeatureBundle, drop_first: bool = False) -> None:
        self.selected = selected
        self.drop_first = drop_first
        self.owners: list[HeadlessSession] = []

    def restore(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> ReplaySession:
        owner = restore_checkpoint(core, protocol, bundles=(self.selected,))
        self.owners.append(owner)
        return _ObservedSession(owner, self.drop_first)


def test_trial_blocked_fact_loss() -> None:
    data, selected = fixture(), trial_bundle()
    factory = _Factory(selected, True)
    mismatches = Runner(data.initial_core, data.initial_protocol, factory=factory,
                        io=state_io((selected,))).run(data.trace)
    assert [(m.step_index, m.path, m.actual) for m in mismatches] == [(0, "$facts[0]", "<missing>")]
    # The actual cue remains published; presentation is excluded from simulation witnesses.
    owner = factory.owners[0]
    assert owner.snapshot().tick == 7 and owner.last_publication().cues


def test_trial_wrong_leaf() -> None:
    selected = trial_bundle()
    wrong = decode_fixture(canonical_json(reference("negative_self_consistent_step3_fixture")),
                           io=state_io((selected,)))
    mismatches = replay_runner(wrong, bundles=(selected,)).run(wrong.trace)
    assert (mismatches[0].step_index, mismatches[0].path, mismatches[0].expected, mismatches[0].actual) == (
        2, "$core.components[1].fields.cell", "6", "4")


def test_trial_invalid_checkpoint_before_execution() -> None:
    data, selected = fixture(), trial_bundle()
    io, factory = state_io((selected,)), _Factory(selected)
    altered_rules = state_io((replace(selected, rules_document={**selected.rules_document, "drift": 1}),))
    with pytest.raises(ReplayFormatError):
        Runner(data.initial_core, data.initial_protocol, factory=factory, io=altered_rules).run(data.trace)
    assert factory.owners == []
    last = data.trace.steps[-1]
    assert last.expected_witness is not None
    core = object_value(decode_json(last.expected_witness.canonical_core_json))
    grid, position = (object_value(c) for c in array_value(core["components"]))
    invalid_sets: tuple[tuple[JsonObject, ...], ...] = ((position,), (grid, {**position, "fields": {"space_id": "space:trial", "cell": 1}}),
                       (grid, {**position, "fields": {"space_id": "space:missing", "cell": 6}}),
                       ({**grid, "schema": {"kind": "trial.map", "version": 2}}, position))
    for components in invalid_sets:
        witness = replace(last.expected_witness, canonical_core_json=canonical_json({**core, "components": components}))
        bad = replace(data.trace, steps=(*data.trace.steps[:-1], replace(last, expected_witness=witness)))
        with pytest.raises(ReplayFormatError):
            Runner(data.initial_core, data.initial_protocol, factory=factory, io=io).run(bad)
        assert factory.owners == []
    for changed in (replace(data.initial_core, components=data.initial_core.components[:1]),
                    replace(data.initial_core, pins=replace(data.initial_core.pins, schema_fingerprint="f" * 64))):
        with pytest.raises(ReplayFormatError):
            restore_checkpoint(changed, data.initial_protocol, bundles=(selected,))
    with pytest.raises(ReplayFormatError):
        replay_runner(data).run(data.trace)


def test_trial_fresh_sessions_and_registry_order() -> None:
    data, selected = fixture(), trial_bundle()
    factory = _Factory(selected)
    runner = Runner(data.initial_core, data.initial_protocol, factory=factory, io=state_io((selected,)))
    assert runner.run(data.trace) == () and runner.run(data.trace) == ()
    assert len(factory.owners) == 2 and factory.owners[0] is not factory.owners[1]
    assert factory.owners[0].snapshot() == factory.owners[1].snapshot()
    reordered = replace(selected, read_adapters=tuple(reversed(selected.read_adapters)),
                        field_specs=tuple(reversed(selected.field_specs)), events=tuple(reversed(selected.events)),
                        codecs=tuple(reversed(selected.codecs)), component_codecs=tuple(reversed(selected.component_codecs)))
    assert state_io((reordered,)).pins == state_io((selected,)).pins
    assert replay_runner(data, bundles=(reordered,)).run(data.trace) == ()
