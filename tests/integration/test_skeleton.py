from __future__ import annotations

from dataclasses import dataclass, replace
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.feature_registry import feature_bundles
from app.headless import BootstrapSpec, bootstrap, _restore, state_io
from contracts.errors import ExpiredReadView, ReadOnlyViolation
from contracts.messages import PresentationEvent, WorldEvent
from contracts.read_views import ReadPort
from contracts.skeleton import COUNTER, POSITION, StepCommand
from contracts.turn import (
    CapabilityManifest, CommitReceipt, Engine, EngineBinding, EngineInvocation, EngineResult,
    GameCommand, NodeActivation, NodeKey, PhaseAccess, TurnAborted, TurnCommitted, TurnRejected,
    AdmittedCommand, AdmissionOutcome,
)
from domain.canonical import array_value, canonical_json, decode_json, hash_document, object_value
from domain.primitives import CommandId, EntityId, FieldFamily, MAX_INT, Phase, Tick, TypeKey, WorldRevision
from domain.state_types import CounterRecord, PositionRecord
from engines.skeleton import Counter, Stepper
from orchestration.skeleton import StepAdmission
from orchestration.turn import NoDrawRng
from tests.unit.test_canonical import vectors

SPEC = BootstrapSpec("0" * 64, "0" * 32, "1" * 32)
ACTOR = EntityId("actor:toy")
IO = state_io(feature_bundles(ACTOR))
command_document, core_hash = IO.encode_command, IO.hash_core
protocol_document, publication_document = IO.encode_protocol, IO.encode_publication


def command(sequence: int, dx: int = 1, revision: int = 0) -> GameCommand:
    return GameCommand(CommandId(f"c1:{SPEC.branch_id}:{SPEC.stream_id}:{sequence}"), ACTOR,
                       WorldRevision(revision), StepCommand(dx))


def test_two_turns_and_zero() -> None:
    session = bootstrap(SPEC)
    data = vectors()
    expected = array_value(data["publications"])
    for index, dx in enumerate((1, -1, 0)):
        assert isinstance(session.driver.submit(command(index + 1, dx, index)), TurnCommitted)
        actual = publication_document(session.last_publication())
        oracle = {k: v for k, v in object_value(expected[index]).items() if k != "root_document"}
        assert canonical_json(actual) == canonical_json(oracle)
    assert [(c.x if isinstance(c, PositionRecord) else c.visits) for c in session.snapshot().components
            if isinstance(c, (PositionRecord, CounterRecord))] == [3, 0]


def test_admission_errors() -> None:
    session = bootstrap(SPEC)
    before = (session.snapshot(), session.protocol())
    for bad, code in ((command(1, 2), "INVALID_COMMAND"), (command(1, 1, 4), "STALE_REVISION"),
                      (replace(command(1), actor_id=EntityId("actor:missing")), "UNAUTHORIZED_ACTOR")):
        outcome = session.driver.submit(bad)
        assert isinstance(outcome, TurnRejected) and outcome.failure.code == code
        assert (session.snapshot(), session.protocol()) == before
    for raw in (b"{}", b'{"x":NaN}', b'{"x":1,"x":2}'):
        outcome = session.submit_json(raw).outcome
        assert isinstance(outcome, TurnRejected) and outcome.current_revision is None
    missing = _restore(session.snapshot(), session.protocol(), feature_bundles(ACTOR), NoDrawRng())
    # Fault injection after qualified restore preserves the UNKNOWN_ACTOR admission case.
    missing._driver._head = replace(missing._driver._head, core=replace(missing.snapshot(), components=()))
    outcome = missing.driver.submit(command(1))
    assert isinstance(outcome, TurnRejected) and outcome.failure.code == "UNKNOWN_ACTOR"
    assert not missing.snapshot().components and missing.protocol().revision == 0


def test_retry_conflict_expired() -> None:
    session = bootstrap(SPEC)
    original = session.driver.submit(command(1))
    session.driver.submit(command(2, 0, 1))
    assert session.driver.submit(command(1)) == original
    assert session.last_publication().facts == () and session.last_publication().diff is None
    assert session.last_publication().diagnostics[0].code == "RESYNC_REQUIRED"
    conflict = session.driver.submit(command(1, -1))
    assert isinstance(conflict, TurnRejected) and conflict.failure.code == "COMMAND_ID_CONFLICT"
    bundles = feature_bundles(ACTOR)
    protocol = replace(session.protocol(), receipts=())
    restored = _restore(session.snapshot(), protocol, bundles, NoDrawRng())
    expired = restored.driver.submit(command(1))
    assert isinstance(expired, TurnRejected) and expired.failure.code == "RETRY_WINDOW_EXPIRED"
    retired_protocol = replace(protocol, streams=(replace(protocol.streams[0], status="retired"),))
    restored = _restore(session.snapshot(), retired_protocol, bundles, NoDrawRng())
    retired = restored.driver.submit(command(3, 1, 2))
    assert isinstance(retired, TurnRejected) and retired.failure.code == "STREAM_RETIRED"


@dataclass(frozen=True)
class _BrokenCounter:
    @property
    def manifest(self) -> CapabilityManifest:
        return Counter(ACTOR).manifest
    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        raise RuntimeError("purpose-built technical failure after Stepper")


@dataclass(frozen=True)
class _DuplicateStepper:
    @property
    def manifest(self) -> CapabilityManifest:
        return Stepper().manifest
    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        result = Stepper().evaluate(invocation)
        return replace(result, deltas=result.deltas * 2)


def _replace_engine(engine: Engine) -> tuple[EngineBinding, ...]:
    return tuple(replace(b, engine=engine) if b.engine.manifest.engine_id == engine.manifest.engine_id else b
                 for b in feature_bundles(ACTOR)[0].bindings)


def test_abort_atomicity() -> None:
    for engine, code in ((_BrokenCounter(), "ENGINE_EXCEPTION"), (_DuplicateStepper(), "DUPLICATE_TARGET")):
        bundle = replace(feature_bundles(ACTOR)[0], bindings=_replace_engine(engine))
        session = bootstrap(SPEC, bundles=(bundle,))
        before = (core_hash(session.snapshot()), hash_document("protocol/v1", protocol_document(session.protocol())))
        result = session.driver.submit(command(1))
        assert isinstance(result, TurnAborted) and result.failure.code == code
        assert before == (core_hash(session.snapshot()), hash_document("protocol/v1", protocol_document(session.protocol())))
        assert session.last_publication().facts == () and session.last_publication().diff is None
    session = bootstrap(replace(SPEC, initial_x=MAX_INT))
    before_core = session.snapshot()
    result = session.driver.submit(command(1))
    assert isinstance(result, TurnAborted) and result.failure.code == "INTEGER_OVERFLOW"
    assert session.snapshot() == before_core


class _RetainStepper:
    def __init__(self) -> None:
        self.retained: ReadPort | None = None
    @property
    def manifest(self) -> CapabilityManifest:
        return Stepper().manifest
    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        self.retained = invocation.state
        return Stepper().evaluate(invocation)


def test_view_finally_expiry() -> None:
    engine = _RetainStepper()
    bundle = replace(feature_bundles(ACTOR)[0], bindings=_replace_engine(engine))
    session = bootstrap(SPEC, bundles=(bundle,))
    session.driver.submit(command(1))
    assert engine.retained is not None
    with pytest.raises(ExpiredReadView):
        engine.retained.component(POSITION, ACTOR)


class _BrokenPresenter:
    def map(self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt,
            committed: ReadPort) -> tuple[PresentationEvent, ...]:
        raise RuntimeError("purpose-built presentation delivery failure")


def test_presenter_failure() -> None:
    bundle = feature_bundles(ACTOR)[0]
    bundle = replace(bundle, presenters=(replace(bundle.presenters[0], presenter=_BrokenPresenter()),))
    session = bootstrap(SPEC, bundles=(bundle,))
    result = session.driver.submit(command(1))
    assert isinstance(result, TurnCommitted) and session.protocol().revision == 1
    assert session.last_publication().diagnostics[0].code == "PRESENTATION_FAILED"
    assert session.last_publication().facts and session.last_publication().diff is not None
    assert session.driver.submit(command(1)) == result


class _Observer:
    def __init__(self) -> None:
        self.seen: list[int] = []
    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest("skeleton.observer", (Phase.RESOLVE,),
                                  (PhaseAccess(Phase.RESOLVE, FieldFamily("skeleton.position", "x")),),
                                  (), (), (), (), "constant")
    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        self.seen.append(invocation.state.component(POSITION, ACTOR).x)
        return EngineResult((), (), ())


def test_same_phase_visibility() -> None:
    observer = _Observer()
    binding = EngineBinding(observer, __name__, (NodeActivation(NodeKey(Phase.RESOLVE, "skeleton.observer"), (), False, True, "A"),))
    bundle = feature_bundles(ACTOR)[0]
    session = bootstrap(SPEC, bundles=(replace(bundle, bindings=(*bundle.bindings, binding)),))
    session.driver.submit(command(1))
    assert observer.seen == [0]


def test_headless_cli() -> None:
    root = Path(__file__).resolve().parents[2]
    env = dict(os.environ, PYTHONPATH=str(root / "src"), PYTHONIOENCODING="utf-8")
    result = subprocess.run([sys.executable, "-m", "app.headless"], cwd=root, env=env,
                            input=b"{}\n\n" + canonical_json(command_document(command(1))) + b"\n", capture_output=True, check=True)
    lines = result.stdout.splitlines()
    assert len(lines) == 2
    assert object_value(object_value(decode_json(lines[0]))["outcome"])["kind"] == "rejected"
    doc = object_value(decode_json(lines[1]))
    assert object_value(doc["outcome"])["kind"] == "committed"
    assert object_value(object_value(doc["outcome"])["receipt"])["tick"] == 1
    bad_flags = subprocess.run([sys.executable, "-m", "app.headless", "--unsupported"], cwd=root, env=env, capture_output=True, check=False)
    assert bad_flags.returncode != 0 and not bad_flags.stdout


class _InvalidPlan:
    @property
    def schema(self) -> TypeKey:
        return StepCommand(1).schema
    @property
    def reads(self) -> tuple[FieldFamily, ...]:
        return StepAdmission(ACTOR).reads
    def admit(self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str) -> AdmissionOutcome:
        admitted = StepAdmission(ACTOR).admit(command, state, start_tick=start_tick, world_id=world_id)
        assert isinstance(admitted, AdmittedCommand)
        return replace(admitted, plan=replace(admitted.plan, target_tick=Tick(start_tick + 2)))


class _BadAccessStepper:
    def __init__(self, *, write: bool) -> None:
        self.write = write
        self.retained: ReadPort | None = None
    @property
    def manifest(self) -> CapabilityManifest:
        return Stepper().manifest
    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        self.retained = invocation.state
        if self.write:
            try:
                setattr(invocation.state.component(POSITION, ACTOR), "x", 100)
            except ReadOnlyViolation:
                # Swallowing the guard cannot hide a write attempt from manifest enforcement.
                return Stepper().evaluate(invocation)
        invocation.state.component(COUNTER, ACTOR).visits
        return Stepper().evaluate(invocation)


def test_invalid_plan_and_manifest_access_abort_before_commit() -> None:
    bundle = feature_bundles(ACTOR)[0]
    session = bootstrap(SPEC, bundles=(replace(bundle, command_routes=(_InvalidPlan(),)),))
    before = (session.snapshot(), session.protocol())
    result = session.driver.submit(command(1))
    assert isinstance(result, TurnAborted) and result.failure.code == "INVALID_COMMAND"
    assert (session.snapshot(), session.protocol()) == before
    for write, code in ((False, "UNDECLARED_READ"), (True, "UNDECLARED_WRITE")):
        engine = _BadAccessStepper(write=write)
        session = bootstrap(SPEC, bundles=(replace(bundle, bindings=_replace_engine(engine)),))
        before = (session.snapshot(), session.protocol())
        result = session.driver.submit(command(1))
        assert isinstance(result, TurnAborted) and result.failure.code == code
        assert (session.snapshot(), session.protocol()) == before
        assert session.last_publication().facts == () and session.last_publication().diff is None
        assert engine.retained is not None
        with pytest.raises(ExpiredReadView):
            engine.retained.component(POSITION, ACTOR)
