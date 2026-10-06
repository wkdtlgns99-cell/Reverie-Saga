from __future__ import annotations

from dataclasses import replace
import hashlib
import pytest
from app.headless import restore_checkpoint, state_io
from app.watch_registry import watch_bundle
from contracts.errors import BootstrapError, ExpiredReadView
from contracts.events import QueuedEvent
from contracts.encounter import AttackCommand
from contracts.messages import EmittedFact, EventHeader, EventPolicy, PresentationEvent, WorldEvent
from contracts.read_views import ReadPort
from contracts.skeleton import FeatureBundle
from contracts.turn import CapabilityManifest, CommitReceipt, Engine, EngineBinding, EngineInvocation, EngineResult, AdmittedCommand, AdmissionOutcome, GameCommand, NodeActivation, NodeKey, ProtocolSnapshot, TurnAborted, TurnCommitted
from contracts.watch import WATCH_NPC, BellCommand, BellsDelta, WatchEcho, WatchRequested, WatchNpcRead, WaitCommand, ReplyDelta, BellRung
from domain.canonical import JsonObject, JsonValue, array_value, int_value, decode_json, object_value, pack
from domain.encounter import ATTACK_PROFILE_ID, ENEMY_ID
from domain.primitives import EventId, MAX_INT, Phase, Tick, TypeKey
from domain.state_types import CoreSnapshot
from domain.trial import ACTOR_ID
from domain.watch import NPC_ID, WatchNpcRecord, LanternRecord
from engines.watch import WatchRespond, WatchEchoEngine
from orchestration.watch import WatchCheckpointPolicy, WatchPresenter, WatchAdmission, BellsReducer, BellsPatchRoute
from tests.unit.watch_fixtures import command, reference, session


def with_engine(selected: FeatureBundle, engine: Engine) -> FeatureBundle:
    return replace(selected, bindings=tuple(replace(b, engine=engine) if b.engine.manifest.engine_id == engine.manifest.engine_id else b for b in selected.bindings))


def with_events(selected: FeatureBundle, events: tuple[EventPolicy, ...]) -> FeatureBundle:
    policies: tuple[JsonValue, ...] = tuple({"schema": {"kind": p.schema.kind, "version": p.schema.version}, "mode": p.mode, "delivery_phase": p.delivery_phase.name, "priority": p.priority, "late_route": p.late_route, "producers": tuple(sorted(p.producers)), "subscribers": tuple(sorted(p.subscribers)), "cancellers": tuple(sorted(p.cancellers))} for p in sorted(events, key=lambda p: (p.schema.kind, p.schema.version)))
    return replace(selected, events=events, rules_document={**selected.rules_document, "event_policies": policies})


class _DepthRespond(WatchRespond):
    def __init__(self, depth: int) -> None:
        self.depth = depth
    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        actual = super().evaluate(invocation)
        return replace(actual, facts=tuple(replace(f, payload=WatchEcho(NPC_ID, self.depth)) for f in actual.facts))


@pytest.mark.parametrize("vector", tuple(object_value(v) for v in array_value(reference("cascade_vectors"))))
def test_cascade_vectors(vector: JsonObject) -> None:
    selected = with_engine(watch_bundle(), _DepthRespond(int_value(vector["initial_remaining"])))
    live = session(selected)
    live.driver.submit(command(WaitCommand(2)))
    assert isinstance(live.driver.submit(command(BellCommand(NPC_ID), sequence=2, revision=1)), TurnCommitted)
    facts = tuple(f for f in live.last_publication().facts if f.header.producer_id == "watch.echo")
    io = state_io((selected,))
    actual = io.encode_publication(replace(live.last_publication(), facts=facts, cues=()))
    assert actual["facts"] == vector["expected_emissions"]
    assert len(facts) == vector["waves"]
    assert live.snapshot().components[9].schema.kind == "watch.reply"


class _Feedback(WatchEchoEngine):
    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        result = super().evaluate(invocation)
        return replace(result, facts=tuple(replace(f, payload=WatchEcho(NPC_ID, 1)) for f in result.facts))


def test_cascade_limit() -> None:
    live = session(with_engine(watch_bundle(), _Feedback()))
    old = live.snapshot(), live.protocol()
    result = live.driver.submit(command(BellCommand(NPC_ID)))
    assert isinstance(result, TurnAborted) and result.failure.code == "CASCADE_LIMIT"
    assert (live.snapshot(), live.protocol()) == old
    assert live.last_publication().facts == () and live.last_publication().diff is None


class _FaultEngine:
    def __init__(self, real: Engine, mode: str) -> None:
        self.real, self.mode = real, mode
        self.alias: WatchNpcRead | None = None
    @property
    def manifest(self) -> CapabilityManifest:
        return self.real.manifest
    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        result = self.real.evaluate(invocation)
        if self.manifest.engine_id == "watch.npc":
            self.alias = invocation.state.component(WATCH_NPC, NPC_ID)
        if self.mode == "cause":
            return replace(result, facts=tuple(replace(f, caused_by=(EventId("e1-"+"f"*64),)) for f in result.facts))
        if self.mode == "delta":
            return replace(result, deltas=(BellsDelta(NPC_ID, 1, 2),))
        if self.mode == "duplicate":
            return replace(result, deltas=(*result.deltas, *result.deltas))
        if self.mode == "read":
            from contracts.trial import TRIAL_MAP
            from domain.trial import SPACE_ID
            invocation.state.component(TRIAL_MAP, SPACE_ID).width
            return result
        raise RuntimeError("fault after real calculation")


@pytest.mark.parametrize("mode,code", (("cause", "INVALID_CAUSE"), ("delta", "INVALID_DELTA"), ("duplicate", "DUPLICATE_TARGET"), ("exception", "ENGINE_EXCEPTION"), ("read", "UNDECLARED_READ")))
def test_abort_restores_queue(mode: str, code: str) -> None:
    selected = watch_bundle()
    real = next(b.engine for b in selected.bindings if b.engine.manifest.engine_id == "watch.npc")
    fault = _FaultEngine(real, mode)
    live = session(with_engine(selected, fault))
    live.driver.submit(command())
    old = live.snapshot(), live.protocol()
    result = live.driver.submit(command(WaitCommand(2), sequence=2, revision=1))
    assert isinstance(result, TurnAborted) and result.failure.code == code
    assert (live.snapshot(), live.protocol()) == old
    assert fault.alias is not None
    with pytest.raises(ExpiredReadView):
        _ = fault.alias.bells
    assert live.last_publication().facts == ()


def test_fault_after_real_hp_staging() -> None:
    selected = watch_bundle()
    real = next(b.engine for b in selected.bindings if b.engine.manifest.engine_id == "encounter.actions")
    live = session(with_engine(selected, _FaultEngine(real, "cause")), cell=7)
    live.driver.submit(command())
    old = live.snapshot(), live.protocol()
    result = live.driver.submit(command(AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID), sequence=2, revision=1))
    assert isinstance(result, TurnAborted) and result.failure.code == "INVALID_CAUSE"
    assert (live.snapshot(), live.protocol()) == old


class _PolicyFault(WatchCheckpointPolicy):
    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        super().validate(core, protocol)
        if core.tick >= 2:
            raise ValueError("fault after complete candidate validation")


class _NetFault(BellsReducer):
    def validate_net(self, delta: object, after: ReadPort) -> None:
        from contracts.messages import StateDelta
        assert isinstance(delta, StateDelta)
        super().validate_net(delta, after)
        after.component(WATCH_NPC, NPC_ID).cell


class _PatchFault(BellsPatchRoute):
    def apply(self, before: object, patch: object) -> WatchNpcRecord:
        from contracts.read_views import ComponentPatch
        from domain.state_types import ComponentRecord
        assert isinstance(before, ComponentRecord) and isinstance(patch, ComponentPatch)
        result = super().apply(before, patch)
        assert isinstance(result, WatchNpcRecord)
        return replace(result, cell=7)


@pytest.mark.parametrize("fault", ("policy", "net", "patch"))
def test_final_barrier_fault(fault: str) -> None:
    selected = watch_bundle()
    if fault == "policy":
        selected = replace(selected, checkpoint_policy=_PolicyFault())
    elif fault == "net":
        selected = replace(selected, delta_routes=tuple(_NetFault() if r.schema.kind == "watch.bells-delta" else r for r in selected.delta_routes))
    else:
        selected = replace(selected, patch_routes=tuple(_PatchFault() if r.schema.kind == "watch.bells-patch" else r for r in selected.patch_routes))
    live = session(selected)
    old = live.snapshot(), live.protocol()
    assert isinstance(live.driver.submit(command(WaitCommand(2))), TurnAborted)
    assert (live.snapshot(), live.protocol()) == old


class _PresenterFault(WatchPresenter):
    def map(self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt, committed: ReadPort) -> tuple[PresentationEvent, ...]:
        super().map(facts, receipt, committed)
        raise RuntimeError("fault after real presentation")


def test_postcommit_failure() -> None:
    selected = watch_bundle()
    selected = replace(selected, presenters=tuple(replace(p, presenter=_PresenterFault()) if p.presenter_id == "watch.presenter" else p for p in selected.presenters))
    live = session(selected)
    result = live.driver.submit(command(WaitCommand(2)))
    assert isinstance(result, TurnCommitted) and live.snapshot().tick == 2
    pub = live.last_publication()
    assert tuple(d.code for d in pub.diagnostics) == ("PRESENTATION_FAILED",)
    assert not pub.cues and len(pub.facts) == 2 and pub.diff is not None
    io = state_io((selected,))
    assert io.decode_pending(live.snapshot().pending[0]).event.due_tick == 4
    assert result.receipt.core_hash == io.hash_core(live.snapshot())


def test_event_tick_budget() -> None:
    selected = watch_bundle()
    execution = object_value(selected.rules_document["execution"])
    selected = replace(selected, rules_document={**selected.rules_document, "execution": {**execution, "max_events_per_tick": 6}})
    live = session(selected)
    live.driver.submit(command())
    old = live.snapshot(), live.protocol()
    result = live.driver.submit(command(BellCommand(NPC_ID), sequence=2, revision=1))
    assert isinstance(result, TurnAborted) and result.failure.code == "EVENT_LIMIT"
    assert (live.snapshot(), live.protocol()) == old
    selected = watch_bundle()
    selected = replace(selected, rules_document={**selected.rules_document, "execution": {**execution, "max_pending": 1}})
    live = session(selected)
    assert isinstance(live.driver.submit(command(WaitCommand(2))), TurnCommitted)
    assert len(live.snapshot().pending) == 1


@pytest.mark.parametrize("kind", ("cascade_every_tick", "policy_drift", "cancellers", "bad_limit", "missing_consume", "lane"))
def test_registry_rights(kind: str) -> None:
    selected = watch_bundle()
    if kind == "policy_drift":
        selected = replace(selected, events=tuple(replace(p, priority=p.priority+1) if p.schema.kind == "watch.echo" else p for p in selected.events))
    elif kind == "cancellers":
        selected = with_events(selected, tuple(replace(p, cancellers=("watch.bell",)) if p.schema.kind == "watch.echo" else p for p in selected.events))
    elif kind == "bad_limit":
        execution = object_value(selected.rules_document["execution"])
        selected = replace(selected, rules_document={**selected.rules_document, "execution": {**execution, "max_duration_seconds": True}})
    elif kind == "missing_consume":
        class MissingConsume(WatchRespond):
            @property
            def manifest(self) -> CapabilityManifest:
                return replace(super().manifest, consumes=())
        selected = with_engine(selected, MissingConsume())
    else:
        selected = replace(selected, bindings=tuple(replace(b, activations=tuple(replace(a, every_tick=True) if kind == "cascade_every_tick" else replace(a, lane="B") for a in b.activations)) if b.engine.manifest.engine_id == "watch.echo" else b for b in selected.bindings))
    with pytest.raises(BootstrapError):
        state_io((selected,))


class _AllowRequests(WatchCheckpointPolicy):
    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        wake = tuple(d for d in core.pending if object_value(object_value(object_value(decode_json(d.canonical_event_json))["event"])["header"])["type_key"] == {"kind": "watch.wake", "version": 1})
        super().validate(replace(core, pending=wake), protocol)


class _Observer:
    def __init__(self) -> None:
        self.inboxes: list[tuple[WorldEvent, ...]] = []
    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest("watch.observer", (Phase.REACT,), (), (), (), (), (TypeKey("watch.requested", 1),), "local")
    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        assert invocation.action is None
        self.inboxes.append(invocation.incoming)
        return EngineResult((), (), ())


def test_multisubscriber_barrier() -> None:
    selected, observer = watch_bundle(), _Observer()
    selected = replace(selected, bindings=(*selected.bindings, EngineBinding(observer, "engines.watch", (NodeActivation(NodeKey(Phase.REACT, "watch.observer"), (), True, True, "A"),))), checkpoint_policy=_AllowRequests())
    selected = with_events(selected, tuple(replace(p, subscribers=(*p.subscribers, "watch.observer")) if p.schema.kind == "watch.requested" else p for p in selected.events))
    live = session(selected)
    live.driver.submit(command(WaitCommand(7)))
    core = live.snapshot()
    io = state_io((selected,))
    requests: list[QueuedEvent] = []
    for seq in range(6):
        identifier = EventId("e1-"+hashlib.sha256(pack(("event-id/v1", core.world_id, "1", "RESOLVE", "0", "watch.bell", str(seq)))).hexdigest())
        event = WorldEvent(EventHeader(identifier, TypeKey("watch.requested", 1), "watch.bell", Tick(1), Phase.RESOLVE, 0, 3, seq, (), ()), Tick(8), WatchRequested(ACTOR_ID, NPC_ID))
        requests.append(QueuedEvent(event, Phase.REACT, 20))
    observer.inboxes.clear()
    combined = (*tuple(io.decode_pending(d) for d in core.pending), *requests)
    from orchestration.events import queued_sort_key
    queued = tuple(io.encode_pending(q) for q in sorted(combined, key=queued_sort_key))
    live = restore_checkpoint(replace(core, pending=queued), replace(live.protocol(), receipts=()), bundles=(selected,))
    assert isinstance(live.driver.submit(command(WaitCommand(1), sequence=2, revision=1)), TurnCommitted)
    assert observer.inboxes == [tuple(q.event for q in requests)]
    pub = live.last_publication()
    replies = tuple(f for f in pub.facts if f.payload.schema.kind == "watch.replied")
    assert len(replies) == 6 and pub.diff is not None
    assert tuple(d for d in pub.diff.changes if d.schema.kind == "watch.reply-delta")[0] == ReplyDelta(NPC_ID, 0, 6)
    assert not any(f.payload.schema.kind == "watch.requested" for f in pub.facts)
    assert len(live.snapshot().pending) == 1


class _PostRequest:
    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest("watch.post", (Phase.POST_TICK,), (), (), (), (TypeKey("watch.requested", 1),), (), "local")
    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        return EngineResult((), (EmittedFact(WatchRequested(ACTOR_ID, NPC_ID), invocation.logical_tick, ()),), ())


@pytest.mark.parametrize("defer", (False, True))
def test_late_route_live(defer: bool) -> None:
    selected = watch_bundle()
    post = _PostRequest()
    selected = replace(selected, checkpoint_policy=_AllowRequests(), bindings=(*selected.bindings, EngineBinding(post, "engines.watch", (NodeActivation(NodeKey(Phase.POST_TICK, "watch.post"), (), False, True, "A"),))))
    selected = with_events(selected, tuple(replace(p, producers=(*p.producers, "watch.post"), late_route="next_tick" if defer else "reject") if p.schema.kind == "watch.requested" else p for p in selected.events))
    live = session(selected)
    old = live.snapshot(), live.protocol()
    result = live.driver.submit(command())
    if not defer:
        assert isinstance(result, TurnAborted) and result.failure.code == "EVENT_LATE"
        assert (live.snapshot(), live.protocol()) == old
    else:
        assert isinstance(result, TurnCommitted)
        assert tuple(d.code for d in live.last_publication().diagnostics) == ("EVENT_DEFERRED",)
        io = state_io((selected,))
        q = tuple(io.decode_pending(d) for d in live.snapshot().pending)
        request = next(p.event for p in q if p.event.payload.schema.kind == "watch.requested")
        assert request.header.occurred_at == 1 and request.due_tick == 2
        assert isinstance(live.driver.submit(command(sequence=2, revision=1)), TurnCommitted)
        assert any(f.payload.schema.kind == "watch.replied" for f in live.last_publication().facts)


def test_overflow() -> None:
    selected, io = watch_bundle(), state_io((watch_bundle(),))
    live = session()
    core = live.snapshot()
    tick = MAX_INT - 2
    components = tuple(replace(c, bells=tick//2) if isinstance(c, WatchNpcRecord) else replace(c, charge=3) if isinstance(c, LanternRecord) else c for c in core.components)
    q = io.decode_pending(core.pending[0])
    previous = tick//2*2
    identifier = EventId("e1-"+hashlib.sha256(pack(("event-id/v1", core.world_id, str(previous), "PRE_TICK", "0", "watch.npc", "1"))).hexdigest())
    event = replace(q.event, header=replace(q.event.header, occurred_at=Tick(previous), sequence=1, event_id=identifier, caused_by=(EventId("e1-"+"f"*64),)), due_tick=Tick(MAX_INT-1))
    core = replace(core, tick=Tick(tick), components=components, pending=(io.encode_pending(replace(q, event=event)),))
    for seconds in (1, 3):
        owner = restore_checkpoint(core, live.protocol(), bundles=(selected,))
        result = owner.driver.submit(command(WaitCommand(seconds)))
        assert isinstance(result, TurnAborted) and result.failure.code == "INTEGER_OVERFLOW"
        assert owner.snapshot() == core and owner.protocol() == live.protocol()


class _PlanFault(WatchAdmission):
    def __init__(self, target: int) -> None:
        super().__init__(TypeKey("watch.wait", 1))
        self.target = target
    def admit(self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str) -> AdmissionOutcome:
        result = super().admit(command, state, start_tick=start_tick, world_id=world_id)
        assert isinstance(result, AdmittedCommand)
        return replace(result, plan=replace(result.plan, target_tick=Tick(self.target)))


@pytest.mark.parametrize("target,code", ((-1, "INVALID_COMMAND"), (0, "INVALID_COMMAND"), (True, "INVALID_COMMAND"), (17, "TURN_LIMIT"), (MAX_INT+1, "INTEGER_OVERFLOW")))
def test_admission_bounds(target: int, code: str) -> None:
    selected = watch_bundle()
    selected = replace(selected, command_routes=tuple(_PlanFault(target) if r.schema.kind == "watch.wait" else r for r in selected.command_routes))
    live = session(selected)
    before = live.snapshot(), live.protocol()
    result = live.driver.submit(command())
    assert isinstance(result, TurnAborted) and result.failure.code == code
    assert (live.snapshot(), live.protocol()) == before


class _BudgetProducer:
    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest("watch.budget", (Phase.POST_TICK,), (), (), (), (TypeKey("watch.bell-rung", 1),), (), "local")
    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        # Conformance port:existing NPC emits two events on even seconds;total exactly512 each second.
        count = 510 if invocation.logical_tick % 2 == 0 else 512
        return EngineResult((), tuple(EmittedFact(BellRung(ACTOR_ID, NPC_ID), invocation.logical_tick, ()) for _ in range(count)), ())


def test_dense_tick_budget_resets_and_outer_cap() -> None:
    selected = watch_bundle()
    engine = _BudgetProducer()
    selected = replace(selected, bindings=(*selected.bindings, EngineBinding(engine, "engines.watch", (NodeActivation(NodeKey(Phase.POST_TICK, "watch.budget"), (), False, True, "A"),))))
    selected = with_events(selected, tuple(replace(p, producers=(*p.producers, "watch.budget")) if p.schema.kind == "watch.bell-rung" else p for p in selected.events))
    live = session(selected)
    assert isinstance(live.driver.submit(command(WaitCommand(16))), TurnCommitted)
    pub = live.last_publication()
    assert len(pub.facts) == 8192 and len(pub.cues) == 8184
    assert tuple(sum(f.header.occurred_at == tick for f in pub.facts) for tick in range(1, 17)) == (512,)*16
    assert live.snapshot().tick == 16 and live.protocol().revision == 1 and len(live.protocol().receipts) == 1
