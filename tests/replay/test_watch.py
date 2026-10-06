from __future__ import annotations

from dataclasses import replace
import hashlib
import pytest
from app.headless import HeadlessSession, replay_runner, restore_checkpoint, state_io
from app.watch_registry import watch_bundle
from contracts.errors import ReplayFormatError
from contracts.replay import ReplayFixture, ReplaySession
from contracts.skeleton import FeatureBundle
from contracts.turn import ProtocolSnapshot, TurnDriver, TurnPublication
from domain.canonical import array_value, canonical_json, decode_json, object_value
from domain.state_types import CoreSnapshot, PendingDocument
from orchestration.replay import Recorder, Runner, decode_fixture, encode_fixture
from tests.unit.watch_fixtures import fixture_body, reference, session


def fixture(passive: bool = False) -> ReplayFixture:
    return decode_fixture(fixture_body(passive), io=state_io((watch_bundle(),)))


def test_watch_core_trace() -> None:
    data = fixture()
    io = state_io((watch_bundle(),))
    assert hashlib.sha256(fixture_body()).hexdigest() == reference("expected_fixture_canonical_sha256")
    assert encode_fixture(data, io=io) == fixture_body()
    assert replay_runner(data, bundles=(watch_bundle(),)).run(data.trace) == ()


def test_watch_passive_trace() -> None:
    data = fixture(True)
    io = state_io((watch_bundle(),))
    assert hashlib.sha256(fixture_body(True)).hexdigest() == reference("passive_fixture_canonical_sha256")
    assert encode_fixture(data, io=io) == fixture_body(True)
    assert replay_runner(data, bundles=(watch_bundle(),)).run(data.trace) == ()


@pytest.mark.parametrize("passive", (False, True))
def test_recorder(passive: bool) -> None:
    data = fixture(passive)
    io, live = state_io((watch_bundle(),)), session()
    recorder = Recorder(data.trace.header, io=io)
    for step in data.trace.steps:
        live.driver.submit(step.command)
        assert recorder.record(step.command, live.last_publication(), live.snapshot(), live.protocol()) == step
    assert recorder.finish() == data.trace


class _ObservedSession:
    def __init__(self, owner: HeadlessSession, drop: str = "", alter_pending: bool = False) -> None:
        self.owner = owner
        self.drop = drop
        self.alter_pending = alter_pending
    @property
    def driver(self) -> TurnDriver:
        return self.owner.driver
    def snapshot(self) -> CoreSnapshot:
        core = self.owner.snapshot()
        if self.alter_pending and core.tick == 2:
            q = object_value(decode_json(core.pending[0].canonical_event_json))
            e = object_value(q["event"])
            h = object_value(e["header"])
            raw = canonical_json({**q, "event": {**e, "header": {**h, "caused_by": ("e1-"+"f"*64,)}}})
            return replace(core, pending=(PendingDocument(raw),))
        return core
    def protocol(self) -> ProtocolSnapshot:
        return self.owner.protocol()
    def last_publication(self) -> TurnPublication:
        pub = self.owner.last_publication()
        return replace(pub, facts=tuple(e for e in pub.facts if e.payload.schema.kind != self.drop))


class _Factory:
    def __init__(self, selected: FeatureBundle, drop: str = "", alter_pending: bool = False) -> None:
        self.selected, self.drop, self.alter_pending = selected, drop, alter_pending
        self.owners: list[HeadlessSession] = []
    def restore(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> ReplaySession:
        owner = restore_checkpoint(core, protocol, bundles=(self.selected,))
        self.owners.append(owner)
        return _ObservedSession(owner, self.drop, self.alter_pending)


@pytest.mark.parametrize("kind,index", (("watch.npc-acted", 0), ("watch.replied", 6)))
def test_fact_loss(kind: str, index: int) -> None:
    data, selected = fixture(), watch_bundle()
    factory = _Factory(selected, kind)
    mismatches = Runner(data.initial_core, data.initial_protocol, factory=factory, io=state_io((selected,))).run(data.trace)
    # Removing the first fact shifts the future Wake into index0;the existing deep comparator names its differing due_tick.
    path = "$facts[0].due_tick" if kind == "watch.npc-acted" else f"$facts[{index}]"
    assert mismatches[0].step_index == 1 and mismatches[0].path == path
    assert factory.owners[0].snapshot().tick == 27
    live = session()
    for step in data.trace.steps[:2]:
        live.driver.submit(step.command)
    assert len(live.last_publication().cues) == 3


def test_pending_mismatch() -> None:
    data, selected = fixture(), watch_bundle()
    factory = _Factory(selected, alter_pending=True)
    mismatches = Runner(data.initial_core, data.initial_protocol, factory=factory, io=state_io((selected,))).run(data.trace)
    assert mismatches[0].step_index == 1
    assert mismatches[0].path == "$core.pending[0].event.header.caused_by[0]"


def test_wrong_reply() -> None:
    io, selected = state_io((watch_bundle(),)), watch_bundle()
    wrong = decode_fixture(canonical_json(reference("negative_self_consistent_reply_fixture")), io=io)
    mismatches = replay_runner(wrong, bundles=(selected,)).run(wrong.trace)
    assert (mismatches[0].step_index, mismatches[0].path, mismatches[0].expected, mismatches[0].actual) == (1, "$core.components[9].fields.count", "0", "1")


def test_invalid_last_witness_before_execution() -> None:
    data, selected = fixture(), watch_bundle()
    factory, io = _Factory(selected), state_io((selected,))
    last = data.trace.steps[-1]
    assert last.expected_witness is not None
    core = object_value(decode_json(last.expected_witness.canonical_core_json))
    for pending in ((), (*array_value(core["pending"]), *array_value(core["pending"]))):
        witness = replace(last.expected_witness, canonical_core_json=canonical_json({**core, "pending": pending}))
        bad = replace(data.trace, steps=(*data.trace.steps[:-1], replace(last, expected_witness=witness)))
        with pytest.raises(ReplayFormatError):
            Runner(data.initial_core, data.initial_protocol, factory=factory, io=io).run(bad)
        assert factory.owners == []
    for pins in (replace(data.initial_core.pins, schema_fingerprint="f"*64), replace(data.initial_core.pins, rules_fingerprint="f"*64), replace(data.initial_core.pins, schedule_fingerprint="f"*64)):
        wrong = replace(data.initial_core, pins=pins)
        with pytest.raises(ReplayFormatError):
            Runner(wrong, data.initial_protocol, factory=factory, io=io).run(data.trace)
        assert factory.owners == []
    with pytest.raises(ReplayFormatError):
        replay_runner(data).run(data.trace)


def test_fresh_ordered_sessions() -> None:
    data, selected = fixture(), watch_bundle()
    factory = _Factory(selected)
    runner = Runner(data.initial_core, data.initial_protocol, factory=factory, io=state_io((selected,)))
    assert runner.run(data.trace) == () and runner.run(data.trace) == ()
    assert len(factory.owners) == 2 and factory.owners[0] is not factory.owners[1]
    reordered = replace(selected, bindings=tuple(reversed(selected.bindings)), events=tuple(reversed(selected.events)), codecs=tuple(reversed(selected.codecs)), read_adapters=tuple(reversed(selected.read_adapters)), delta_routes=tuple(reversed(selected.delta_routes)), patch_routes=tuple(reversed(selected.patch_routes)), field_specs=tuple(reversed(selected.field_specs)), component_codecs=tuple(reversed(selected.component_codecs)))
    assert state_io((reordered,)).pins == state_io((selected,)).pins
    assert replay_runner(data, bundles=(reordered,)).run(data.trace) == ()
