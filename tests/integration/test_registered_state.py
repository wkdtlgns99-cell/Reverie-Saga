from __future__ import annotations

from dataclasses import replace

import pytest

from app.headless import state_io
from contracts.errors import ExpiredReadView, ReadOnlyViolation
from contracts.read_views import ReadPort, StagingEditor
from contracts.messages import StateDelta
from contracts.turn import CapabilityManifest, EngineBinding, EngineInvocation, EngineResult, NodeActivation, NodeKey, PhaseAccess, ProtocolSnapshot, TurnAborted, TurnCommitted, TurnRejected
from domain.canonical import JsonObject, canonical_json, object_value
from domain.primitives import ComponentAddress, FrozenPayload, TypeKey
from domain.state_types import CoreSnapshot
from domain.primitives import Phase
from tests.unit.registered_io_fixtures import ACTOR, GAUGE, VALUE, GaugeChanged, GaugeCue, GaugeDelta, GaugeEngine, GaugePatch, GaugePayloadCodec, GaugePresenter, GaugeRead, GaugeRecord, GaugeReducer, bundle, command, key, session
from tests.unit.test_registered_io import BadPatchRoute


def test_foreign_schema_real_turn() -> None:
    selected = bundle()
    live = session(selected)
    old = live.snapshot().components[0]
    result = live.driver.submit(command())
    assert isinstance(result, TurnCommitted)
    assert live.snapshot().components == (GaugeRecord(ACTOR, 5, "계기"),)
    assert old == GaugeRecord(ACTOR, 2, "계기")
    assert (live.snapshot().tick, live.protocol().revision) == (1, 1)
    pub = live.last_publication()
    assert pub.diff is not None and pub.diff.changes == (GaugeDelta(ACTOR, 2, 5),)
    assert tuple(f.payload for f in pub.facts) == (GaugeChanged(ACTOR, 2, 5),)
    assert tuple(c.payload for c in pub.cues) == (GaugeCue(ACTOR, 2, 5),)
    assert pub.diagnostics == ()


def test_foreign_json_submit() -> None:
    selected = bundle()
    io = state_io((selected,))
    live = session(selected)
    publication = live.submit_json(canonical_json(io.encode_command(command())))
    assert isinstance(publication.outcome, TurnCommitted)
    encoded = io.encode_publication(publication)
    assert object_value(encoded["outcome"])["kind"] == "committed"
    assert live.snapshot().components == (GaugeRecord(ACTOR, 5, "계기"),)
    before = (live.snapshot(), live.protocol())
    bad = {**io.encode_command(command(2, 1, 1)), "payload": {"amount": True}}
    malformed = live.submit_json(canonical_json(bad)).outcome
    assert isinstance(malformed, TurnRejected) and malformed.current_revision is None
    assert (live.snapshot(), live.protocol()) == before


def test_foreign_retry_and_abort_atomicity() -> None:
    live = session()
    receipt = live.driver.submit(command())
    assert isinstance(receipt, TurnCommitted)
    assert isinstance(live.driver.submit(command(2, -3, 1)), TurnCommitted)
    before = (live.snapshot(), live.protocol())
    assert live.driver.submit(command()) == receipt
    assert live.last_publication().facts == () and live.last_publication().diff is None
    for cmd, code in ((command(3, 1, 0), "STALE_REVISION"), (command(1, -3, 0), "COMMAND_ID_CONFLICT")):
        result = live.driver.submit(cmd)
        assert isinstance(result, TurnRejected) and result.failure.code == code
        assert (live.snapshot(), live.protocol()) == before
    bounded = session(value=9)
    before = (bounded.snapshot(), bounded.protocol())
    result = bounded.driver.submit(command(1, 1))
    assert isinstance(result, TurnRejected) and result.failure.code == "INVALID_COMMAND"
    assert (bounded.snapshot(), bounded.protocol()) == before
    for mode in ("label", "entity", "schema", "range"):
        original = bundle()
        bad = session(replace(original, patch_routes=(BadPatchRoute(mode),)))
        before = (bad.snapshot(), bad.protocol())
        result = bad.driver.submit(command())
        assert isinstance(result, TurnAborted)
        assert (bad.snapshot(), bad.protocol()) == before
        assert bad.last_publication().facts == () and bad.last_publication().diff is None


def test_registered_post_tick_fact() -> None:
    observer = _Observer()
    original = bundle(Phase.POST_TICK)
    selected = replace(original, bindings=(*original.bindings, EngineBinding(observer, "tests.integration.test_registered_state", (
        NodeActivation(NodeKey(Phase.RESOLVE, "fixture.observer"), (), False, True, "A"),))))
    live = session(selected)
    result = live.driver.submit(command())
    assert isinstance(result, TurnCommitted)
    fact = live.last_publication().facts[0]
    assert fact.header.phase == Phase.POST_TICK and fact.header.producer_id == "fixture.adjuster"
    assert (fact.header.producer_rank, fact.header.sequence) == (1, 0)
    assert observer.seen == [2]
    io = state_io((selected,))
    document = io.encode_publication(live.last_publication())
    io.validate_effects(command(), result, live.snapshot(), live.protocol(), document["facts"], document["diff"])


def test_finally_expiry_and_presenter() -> None:
    selected = bundle()
    live = session(selected)
    assert isinstance(live.driver.submit(command()), TurnCommitted)
    engine, presenter = selected.bindings[0].engine, selected.presenters[0].presenter
    assert isinstance(engine, GaugeEngine) and isinstance(presenter, GaugePresenter)
    assert engine.retained is not None and presenter.retained is not None
    for alias in (engine.retained, presenter.retained):
        with pytest.raises(ExpiredReadView):
            _ = alias.value
        with pytest.raises(ExpiredReadView):
            _ = alias.label
    zero = live.driver.submit(command(2, 0, 1))
    assert isinstance(zero, TurnCommitted)
    diff = live.last_publication().diff
    assert diff is not None and diff.changes == ()
    assert live.last_publication().facts[0].payload == GaugeChanged(ACTOR, 5, 5)


class _BadCueCodec(GaugePayloadCodec):
    def encode(self, payload: FrozenPayload) -> JsonObject:
        raise ValueError("broken registered presentation codec")


def test_cue_codec_failure_retains_commit() -> None:
    original = bundle()
    selected = replace(original, codecs=tuple(_BadCueCodec(c.schema) if c.schema == key("gauge-cue") else c for c in original.codecs))
    live = session(selected)
    assert isinstance(live.driver.submit(command()), TurnCommitted)
    assert live.snapshot().components == (GaugeRecord(ACTOR, 5, "계기"),)
    pub = live.last_publication()
    assert pub.facts and pub.diff is not None and not pub.cues
    assert pub.diagnostics[0].code == "PRESENTATION_FAILED"


class _Observer:
    def __init__(self) -> None:
        self.seen: list[int] = []

    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest("fixture.observer", (Phase.RESOLVE,), (PhaseAccess(Phase.RESOLVE, VALUE),), (), (), (), (), "constant")

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        self.seen.append(invocation.state.component(GAUGE, ACTOR).value)
        return EngineResult((), (), ())


class _ObservedNet(GaugeReducer):
    def __init__(self, mode: str = "valid") -> None:
        self.mode = mode
        self.retained: GaugeRead | None = None

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        super().validate_net(delta, after)
        assert isinstance(delta, GaugeDelta)
        self.retained = after.component(GAUGE, delta.subject)
        if self.mode == "read":
            _ = self.retained.label
        elif self.mode == "write":
            try:
                setattr(self.retained, "value", 3)
            except ReadOnlyViolation:
                pass


def test_net_validator_access_and_expiry() -> None:
    for mode in ("valid", "read", "write"):
        original = bundle()
        reducer = _ObservedNet(mode)
        live = session(replace(original, delta_routes=(reducer,)))
        before = (live.snapshot(), live.protocol())
        result = live.driver.submit(command())
        if mode == "valid":
            assert isinstance(result, TurnCommitted)
        else:
            assert isinstance(result, TurnAborted)
            assert (live.snapshot(), live.protocol()) == before
        assert reducer.retained is not None
        with pytest.raises(ExpiredReadView):
            _ = reducer.retained.value


class _CandidatePolicy:
    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        if core.tick != 0:
            raise ValueError("candidate checkpoint policy rejection")


def test_candidate_policy_failure_is_atomic() -> None:
    original = bundle()
    live = session(replace(original, checkpoint_policy=_CandidatePolicy()))
    before = (live.snapshot(), live.protocol())
    assert isinstance(live.driver.submit(command()), TurnAborted)
    assert (live.snapshot(), live.protocol()) == before
    assert live.last_publication().facts == () and live.last_publication().diff is None


class _UnknownPatch(GaugePatch):
    @property
    def schema(self) -> TypeKey:
        return key("missing-patch")


class _UnknownPatchReducer(GaugeReducer):
    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        assert isinstance(delta, GaugeDelta)
        editor.apply_patch(ComponentAddress(GAUGE.schema, delta.subject), _UnknownPatch(delta.after_value))


def test_unregistered_patch_is_atomic() -> None:
    original = bundle()
    live = session(replace(original, delta_routes=(_UnknownPatchReducer(),)))
    before = (live.snapshot(), live.protocol())
    result = live.driver.submit(command())
    assert isinstance(result, TurnAborted) and result.failure.code == "INVALID_DELTA"
    assert (live.snapshot(), live.protocol()) == before
