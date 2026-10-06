from __future__ import annotations

from dataclasses import replace
import hashlib

import pytest

from app.headless import HeadlessSession, replay_runner, restore_checkpoint, state_io
from app.encounter_registry import encounter_bundle
from contracts.errors import ReplayFormatError
from contracts.replay import ReplayFixture, ReplaySession
from contracts.skeleton import FeatureBundle
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, ProtocolSnapshot, TurnDriver, TurnPublication
from contracts.encounter import HitPointsDelta
from domain.canonical import JsonObject, array_value, canonical_json, decode_json, object_value
from domain.state_types import CoreSnapshot
from domain.trial import ACTOR_ID
from engines.encounter import EncounterActions
from orchestration.replay import Recorder, Runner, decode_fixture, encode_fixture
from tests.unit.encounter_fixtures import fixture_body, reference, session


def fixture(death: bool = False) -> ReplayFixture:
    return decode_fixture(fixture_body(death), io=state_io((encounter_bundle(),)))


def test_encounter_core_trace() -> None:
    data, selected = fixture(), encounter_bundle()
    io = state_io((selected,))
    assert hashlib.sha256(fixture_body()).hexdigest() == reference("expected_fixture_canonical_sha256")
    assert encode_fixture(data, io=io) == fixture_body()
    assert replay_runner(data, bundles=(selected,)).run(data.trace) == ()


@pytest.mark.parametrize("death", (False, True))
def test_recorder_matches_independent_traces(death: bool) -> None:
    data = fixture(death)
    io, live = state_io((encounter_bundle(),)), session(cell=7, actor_hp=1) if death else session()
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


def test_encounter_blocked_fact_loss() -> None:
    data, selected = fixture(), encounter_bundle()
    factory = _Factory(selected, True)
    mismatches = Runner(data.initial_core, data.initial_protocol, factory=factory,
                        io=state_io((selected,))).run(data.trace)
    assert [(m.step_index, m.path, m.actual) for m in mismatches] == [(0, "$facts[0]", "<missing>")]
    # The actual cue remains published; presentation is excluded from simulation witnesses.
    owner = factory.owners[0]
    assert owner.snapshot().tick == 16
    live = session()
    live.driver.submit(data.trace.steps[0].command)
    assert len(live.last_publication().cues) == 1


def test_encounter_wrong_leaf() -> None:
    selected = encounter_bundle()
    wrong = decode_fixture(canonical_json(reference("negative_self_consistent_movement_fixture")),
                           io=state_io((selected,)))
    mismatches = replay_runner(wrong, bundles=(selected,)).run(wrong.trace)
    assert (mismatches[0].step_index, mismatches[0].path, mismatches[0].expected, mismatches[0].actual) == (
        6, "$core.components[6].fields.cell", "6", "4")


def test_encounter_invalid_checkpoint_before_execution() -> None:
    data, selected = fixture(), encounter_bundle()
    io, factory = state_io((selected,)), _Factory(selected)
    altered_rules = state_io((replace(selected, rules_document={**selected.rules_document, "drift": 1}),))
    with pytest.raises(ReplayFormatError):
        Runner(data.initial_core, data.initial_protocol, factory=factory, io=altered_rules).run(data.trace)
    assert factory.owners == []
    for pins in (replace(data.initial_core.pins, schema_fingerprint="f" * 64),
                 replace(data.initial_core.pins, rules_fingerprint="f" * 64),
                 replace(data.initial_core.pins, schedule_fingerprint="f" * 64)):
        with pytest.raises(ReplayFormatError):
            Runner(replace(data.initial_core, pins=pins), data.initial_protocol,
                   factory=factory, io=io).run(data.trace)
        assert factory.owners == []
    last = data.trace.steps[-1]
    assert last.expected_witness is not None
    core = object_value(decode_json(last.expected_witness.canonical_core_json))
    original = tuple(object_value(c) for c in array_value(core["components"]))
    invalid_sets: list[tuple[JsonObject, ...]] = [original[:4] + original[5:]]
    invalid_fields: tuple[tuple[int, JsonObject], ...] = ((0, {"space_id": "space:trial", "cell": 4, "is_open": 0}),
                          (2, {"hp": 4}), (3, {"value": True}),
                          (5, {"space_id": "space:trial", "cell": 7}),
                          (6, {"space_id": "space:missing", "cell": 8}),
                          (6, {"space_id": "space:trial", "cell": 1}))
    for index, fields in invalid_fields:
        changed = list(original)
        changed[index] = {**original[index], "fields": fields}
        if index == 0:
            changed[6] = {**original[6], "fields": {"space_id": "space:trial", "cell": 4}}
        invalid_sets.append(tuple(changed))
    changed = list(original)
    changed[1] = {**original[1], "fields": {"hp": 1}}
    invalid_sets.append(tuple(changed))
    for components in invalid_sets:
        witness = replace(last.expected_witness, canonical_core_json=canonical_json({**core, "components": components}))
        bad = replace(data.trace, steps=(*data.trace.steps[:-1], replace(last, expected_witness=witness)))
        with pytest.raises(ReplayFormatError):
            Runner(data.initial_core, data.initial_protocol, factory=factory, io=io).run(bad)
        assert factory.owners == []
    for changed_core in (replace(data.initial_core, components=data.initial_core.components[:6]),
                    replace(data.initial_core, pins=replace(data.initial_core.pins, schema_fingerprint="f" * 64))):
        with pytest.raises(ReplayFormatError):
            restore_checkpoint(changed_core, data.initial_protocol, bundles=(selected,))
    with pytest.raises(ReplayFormatError):
        replay_runner(data).run(data.trace)


def test_encounter_fresh_sessions_and_registry_order() -> None:
    data, selected = fixture(), encounter_bundle()
    factory = _Factory(selected)
    runner = Runner(data.initial_core, data.initial_protocol, factory=factory, io=state_io((selected,)))
    assert runner.run(data.trace) == () and runner.run(data.trace) == ()
    assert len(factory.owners) == 2 and factory.owners[0] is not factory.owners[1]
    assert factory.owners[0].snapshot() == factory.owners[1].snapshot()
    reordered = replace(selected, read_adapters=tuple(reversed(selected.read_adapters)),
                        field_specs=tuple(reversed(selected.field_specs)), events=tuple(reversed(selected.events)),
                        codecs=tuple(reversed(selected.codecs)), component_codecs=tuple(reversed(selected.component_codecs)),
                        bindings=tuple(reversed(selected.bindings)), command_routes=tuple(reversed(selected.command_routes)),
                        delta_routes=tuple(reversed(selected.delta_routes)), patch_routes=tuple(reversed(selected.patch_routes)))
    assert state_io((reordered,)).pins == state_io((selected,)).pins
    assert replay_runner(data, bundles=(reordered,)).run(data.trace) == ()


def test_encounter_death_trace() -> None:
    data, io = fixture(True), state_io((encounter_bundle(),))
    assert hashlib.sha256(fixture_body(True)).hexdigest() == reference("death_fixture_canonical_sha256")
    assert encode_fixture(data, io=io) == fixture_body(True)
    assert replay_runner(data, bundles=(encounter_bundle(),)).run(data.trace) == ()


class _DefeatLossSession(_ObservedSession):
    def last_publication(self) -> TurnPublication:
        publication = self.owner.last_publication()
        return replace(publication, facts=tuple(f for f in publication.facts if f.payload.schema.kind != "encounter.defeated"))


class _DefeatLossFactory(_Factory):
    def restore(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> ReplaySession:
        owner = restore_checkpoint(core, protocol, bundles=(self.selected,))
        self.owners.append(owner)
        return _DefeatLossSession(owner, False)


def test_defeat_fact_loss() -> None:
    data, selected = fixture(), encounter_bundle()
    factory = _DefeatLossFactory(selected)
    mismatches = Runner(data.initial_core, data.initial_protocol, factory=factory,
                        io=state_io((selected,))).run(data.trace)
    assert [(m.step_index, m.path, m.actual) for m in mismatches] == [(14, "$facts[1]", "<missing>")]
    assert factory.owners[0].snapshot().tick == 16
    # Verify the removed defeat fact still produced its actual postcommit cue.
    live = session()
    for step in data.trace.steps[:15]:
        live.driver.submit(step.command)
    assert len(live.last_publication().cues) == 2


class _CounterLoss:
    @property
    def manifest(self) -> CapabilityManifest:
        return EncounterActions().manifest

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        result = EncounterActions().evaluate(invocation)
        return replace(result, deltas=tuple(d for d in result.deltas
                                            if not isinstance(d, HitPointsDelta) or d.entity_id != ACTOR_ID))


def test_missing_counter_damage_is_visible_in_replay() -> None:
    data, selected = fixture(), encounter_bundle()
    selected = replace(selected, bindings=(replace(selected.bindings[0], engine=_CounterLoss()), selected.bindings[1]))
    prefix = replace(data.trace, steps=data.trace.steps[:11])
    mismatches = replay_runner(data, bundles=(selected,)).run(prefix)
    assert (mismatches[0].step_index, mismatches[0].path, mismatches[0].expected, mismatches[0].actual) == (
        10, "$core.components[2].fields.hp", "2", "3")


class _AttackLossSession(_ObservedSession):
    def last_publication(self) -> TurnPublication:
        publication = self.owner.last_publication()
        return replace(publication, facts=tuple(f for f in publication.facts if f.payload.schema.kind != "encounter.attack-resolved"))


class _AttackLossFactory(_Factory):
    def restore(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> ReplaySession:
        owner = restore_checkpoint(core, protocol, bundles=(self.selected,))
        self.owners.append(owner)
        return _AttackLossSession(owner, False)


def test_attack_fact_loss() -> None:
    data, selected = fixture(), encounter_bundle()
    factory = _AttackLossFactory(selected)
    prefix = replace(data.trace, steps=data.trace.steps[:11])
    mismatches = Runner(data.initial_core, data.initial_protocol, factory=factory,
                        io=state_io((selected,))).run(prefix)
    assert [(m.step_index, m.path, m.actual) for m in mismatches] == [(10, "$facts[0]", "<missing>")]
