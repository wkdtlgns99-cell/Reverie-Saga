from __future__ import annotations

from dataclasses import replace
import os
import subprocess
import sys
from typing import cast

import pytest

from app.headless import state_io
from app.trial import TrialBootstrapSpec, bootstrap_trial, main
from app.trial_registry import trial_bundle
from contracts.errors import BootstrapError, ExpiredReadView
from contracts.messages import PresentationEvent, StateDelta, WorldEvent
from contracts.read_views import ComponentPatch, ReadPort
from contracts.trial import CELL_POSITION, TRIAL_MAP, CellDelta, CellPositionRead, MoveBlocked, MoveCommand, Moved, TrialMapRead
from contracts.turn import (
    CapabilityManifest, CommitReceipt, EngineInvocation, EngineResult,
    ProtocolSnapshot, TurnAborted, TurnCommitted, TurnRejected,
)
from domain.canonical import JsonObject, array_value, canonical_json, int_value, object_value
from domain.primitives import MAX_INT, EntityId, FrozenPayload, Tick, TypeKey, WorldRevision
from domain.state_types import ComponentRecord, CoreSnapshot
from domain.trial import ACTOR_ID, SPACE_ID, CellPositionRecord
from engines.trial import Movement
from orchestration.trial import CellPatchRoute, CellReducer, MovePresenter, TrialPayloadCodec
from tests.unit.trial_fixtures import ROOT, command, reference, session


@pytest.mark.parametrize("vector", tuple(object_value(v) for v in array_value(reference("movement_vectors"))))
def test_movement_vectors(vector: JsonObject) -> None:
    live = session(cell=int_value(vector["from_cell"]))
    before = live.snapshot()
    result = live.driver.submit(command(dx=int_value(vector["dx"]), dz=int_value(vector["dz"])))
    assert isinstance(result, TurnCommitted)
    assert (live.snapshot().tick, live.protocol().revision) == (1, 1)
    assert live.snapshot().components[0] == before.components[0]
    assert live.snapshot().components[1] == CellPositionRecord(ACTOR_ID, SPACE_ID, int_value(vector["to_cell"]))
    pub = live.last_publication()
    assert pub.diff is not None
    assert (len(pub.diff.changes), len(pub.facts), len(pub.cues)) == (
        vector["delta_count"], vector["fact_count"], vector["cue_count"])
    fact = pub.facts[0].payload
    assert isinstance(fact, (Moved, MoveBlocked))
    assert ("moved" if isinstance(fact, Moved) else fact.reason) == vector["result"]
    assert pub.diagnostics == ()


def test_full_publications() -> None:
    io = state_io((trial_bundle(),))
    fixture = object_value(reference("expected_fixture"))
    steps = array_value(object_value(fixture["trace"])["steps"])
    expected = array_value(reference("expected_publications"))
    live = session()
    for step, publication in zip(steps, expected, strict=True):
        cmd = io.decode_command(object_value(object_value(step)["command"]))
        live.driver.submit(cmd)
        assert canonical_json(io.encode_publication(live.last_publication())) == canonical_json(publication)


def test_blocked_attempt_time_and_empty_diff() -> None:
    live = session()
    old = live.snapshot()
    io = state_io((trial_bundle(),))
    result = live.driver.submit(command(dx=1, dz=0))
    assert isinstance(result, TurnCommitted)
    pub = live.last_publication()
    assert pub.diff is not None and pub.diff.changes == ()
    assert live.snapshot().components == old.components
    assert io.hash_core(old) != io.hash_core(live.snapshot())
    assert (result.receipt.tick, result.receipt.revision, live.protocol().streams[0].highest_committed_sequence) == (1, 1, 1)
    assert len(live.protocol().receipts) == 1


@pytest.mark.parametrize("dx,dz", [(0, 0), (1, 1), (-1, -1), (2, 0), (0, -2), (True, 0), (0, False), (cast(int, 1.0), 0)])
def test_invalid_command_no_time(dx: int, dz: int) -> None:
    live = session()
    before = live.snapshot(), live.protocol()
    result = live.driver.submit(command(dx=dx, dz=dz))
    assert isinstance(result, TurnRejected) and result.failure.code == "INVALID_COMMAND"
    assert result.current_revision == 0
    assert (live.snapshot(), live.protocol()) == before
    assert live.last_publication().facts == () and live.last_publication().diff is None


def test_invalid_json_schema_actor_and_shape() -> None:
    io, live = state_io((trial_bundle(),)), session()
    before = live.snapshot(), live.protocol()
    base = io.encode_command(command())
    bodies: tuple[JsonObject, ...] = ({**base, "payload": {"dx": True, "dz": 0}},
                 {**base, "payload": {"dx": 0}},
                 {**base, "payload": {"dx": 0, "dz": 1, "extra": 0}},
                 {**base, "schema": {"kind": "trial.move", "version": 2}},
                 {**base, "actor_id": "actor:e\u0301"})
    for body in bodies:
        # Non-NFC must reach the byte boundary without canonicalizing it first.
        raw = b'{"actor_id":"actor:e\xcc\x81"}' if body.get("actor_id") == "actor:e\u0301" else canonical_json(body)
        pub = live.submit_json(raw)
        assert isinstance(pub.outcome, TurnRejected)
        assert pub.outcome.failure.code == "INVALID_COMMAND" and pub.outcome.current_revision is None
        assert (live.snapshot(), live.protocol()) == before
    unauthorized = live.driver.submit(replace(command(), actor_id=EntityId("actor:other")))
    assert isinstance(unauthorized, TurnRejected) and unauthorized.failure.code == "UNAUTHORIZED_ACTOR"
    unsupported = live.driver.submit(replace(command(), payload=_FutureMove(0, 1)))
    assert isinstance(unsupported, TurnRejected) and unsupported.failure.code == "UNSUPPORTED_SCHEMA"
    assert (live.snapshot(), live.protocol()) == before


class _FutureMove(MoveCommand):
    @property
    def schema(self) -> TypeKey:
        return TypeKey("trial.move", 2)


@pytest.mark.parametrize("cell", [2, 5])
def test_row_boundary_no_wrap(cell: int) -> None:
    # Retain the real engine's map alias to verify no invalid membership read at boundary.
    engine = _ObservedMovement()
    selected = trial_bundle()
    selected = replace(selected, bindings=(replace(selected.bindings[0], engine=engine),))
    live = session(selected, cell=cell)
    assert isinstance(live.driver.submit(command(dx=1, dz=0)), TurnCommitted)
    assert live.snapshot().components[1] == CellPositionRecord(ACTOR_ID, SPACE_ID, cell)
    assert live.last_publication().facts[0].payload == MoveBlocked(ACTOR_ID, SPACE_ID, cell, 1, 0, "boundary")
    assert engine.retained is not None
    with pytest.raises(ExpiredReadView):
        engine.retained.is_blocked(9)


def test_retry_stale_conflict_and_rejected_id_reuse() -> None:
    live = session()
    first = live.driver.submit(command(dx=1, dz=0))
    assert isinstance(first, TurnCommitted)
    assert isinstance(live.driver.submit(command(2, 0, 1, 1)), TurnCommitted)
    before = live.snapshot(), live.protocol()
    assert live.driver.submit(command(dx=1, dz=0)) == first
    pub = live.last_publication()
    assert pub.diff is None and not pub.facts and not pub.cues
    assert pub.diagnostics[0].code == "RESYNC_REQUIRED"
    for cmd, code in ((command(3, 1, 0, 0), "STALE_REVISION"),
                      (command(1, 0, 1, 0), "COMMAND_ID_CONFLICT")):
        result = live.driver.submit(cmd)
        assert isinstance(result, TurnRejected) and result.failure.code == code
        assert (live.snapshot(), live.protocol()) == before
    assert isinstance(live.driver.submit(command(3, 1, 0, 2)), TurnCommitted)


class _ObservedMovement:
    def __init__(self, mode: str = "valid") -> None:
        self.mode = mode
        self.retained: TrialMapRead | None = None

    @property
    def manifest(self) -> CapabilityManifest:
        return Movement().manifest

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        self.retained = invocation.state.component(TRIAL_MAP, SPACE_ID)
        result = Movement().evaluate(invocation)
        if self.mode == "read":
            _ = self.retained.cell_mm  # Undeclared in the actual Movement manifest.
        elif self.mode == "raise":
            raise RuntimeError("fault after actual movement evaluation")
        return result


class _BadPatch(CellPatchRoute):
    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        result = super().apply(before, patch)
        assert isinstance(result, CellPositionRecord)
        return replace(result, space_id=EntityId("space:other"))


class _ObservedReducer(CellReducer):
    def __init__(self, mode: str = "valid") -> None:
        self.mode = mode
        self.retained: CellPositionRead | None = None

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        super().validate_net(delta, after)
        assert isinstance(delta, CellDelta)
        self.retained = after.component(CELL_POSITION, delta.entity_id)
        if self.mode == "read":
            _ = self.retained.space_id


class _CandidatePolicy:
    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        if core.tick:
            raise ValueError("candidate policy fault")


@pytest.mark.parametrize("mode", ["engine", "read", "patch", "net", "policy"])
def test_candidate_abort_atomicity(mode: str) -> None:
    selected = trial_bundle()
    engine = _ObservedMovement("raise" if mode == "engine" else "read" if mode == "read" else "valid")
    reducer = _ObservedReducer("read" if mode == "net" else "valid")
    selected = replace(selected, bindings=(replace(selected.bindings[0], engine=engine),), delta_routes=(reducer,))
    if mode == "patch":
        selected = replace(selected, patch_routes=(_BadPatch(),))
    elif mode == "policy":
        selected = replace(selected, checkpoint_policy=_CandidatePolicy())
    live = session(selected)
    before = live.snapshot(), live.protocol()
    result = live.driver.submit(command())
    assert isinstance(result, TurnAborted)
    expected_codes = {"engine": "ENGINE_EXCEPTION", "read": "UNDECLARED_READ",
                      "patch": "UNDECLARED_WRITE", "net": "ENGINE_EXCEPTION",
                      "policy": "ENGINE_EXCEPTION"}
    assert result.failure.code == expected_codes[mode]
    assert (live.snapshot(), live.protocol()) == before
    pub = live.last_publication()
    assert not pub.facts and pub.diff is None and not pub.cues
    assert engine.retained is not None
    with pytest.raises(ExpiredReadView):
        _ = engine.retained.width
    if reducer.retained is not None:
        with pytest.raises(ExpiredReadView):
            _ = reducer.retained.cell


class _BadPresenter(MovePresenter):
    def __init__(self) -> None:
        self.retained: CellPositionRead | None = None

    def map(self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt,
            committed: ReadPort) -> tuple[PresentationEvent, ...]:
        self.retained = committed.component(CELL_POSITION, ACTOR_ID)
        _ = self.retained.cell
        raise ValueError("postcommit presentation fault")


class _BadCueCodec(TrialPayloadCodec):
    def encode(self, payload: FrozenPayload) -> JsonObject:
        raise ValueError("postcommit cue encoding fault")


@pytest.mark.parametrize("mode", ["presenter", "codec"])
def test_postcommit_presentation_failure(mode: str) -> None:
    selected = trial_bundle()
    presenter = _BadPresenter()
    if mode == "presenter":
        selected = replace(selected, presenters=(replace(selected.presenters[0], presenter=presenter),))
    else:
        selected = replace(selected, codecs=tuple(_BadCueCodec(c.schema) if c.schema.kind == "trial.move-cue" else c for c in selected.codecs))
    live = session(selected)
    assert isinstance(live.driver.submit(command()), TurnCommitted)
    assert live.snapshot().components[1] == CellPositionRecord(ACTOR_ID, SPACE_ID, 3)
    pub = live.last_publication()
    assert pub.facts and pub.diff is not None and not pub.cues
    assert pub.diagnostics[0].code == "PRESENTATION_FAILED"
    if mode == "presenter":
        assert presenter.retained is not None
        with pytest.raises(ExpiredReadView):
            _ = presenter.retained.cell


def test_trial_cli_and_snapshot_no_time() -> None:
    io, live = state_io((trial_bundle(),)), session()
    before = live.snapshot(), live.protocol()
    for _ in range(3):
        io.encode_core(live.snapshot())
        io.encode_protocol(live.protocol())
    assert (live.snapshot(), live.protocol()) == before
    body = canonical_json(io.encode_command(command(dx=1, dz=0)))
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    result = subprocess.run([sys.executable, "-m", "app.trial"], input=b"\n" + body + b"\n",
                            cwd=ROOT, env=env, capture_output=True, check=False, timeout=30)
    assert result.returncode == 0, result.stderr
    expected = array_value(reference("expected_publications"))[0]
    assert result.stdout == canonical_json(expected) + b"\n"
    with pytest.raises(ValueError):
        main(("--unexpected",))


@pytest.mark.parametrize("cell", [-1, 1, 9, True, cast(int, 0.0)])
def test_invalid_bootstrap(cell: int) -> None:
    with pytest.raises(BootstrapError, match="INVALID_INITIAL_STATE"):
        bootstrap_trial(TrialBootstrapSpec("0" * 64, "0" * 32, "1" * 32, cell))


def test_invalid_bootstrap_identifiers_and_bounds() -> None:
    spec = TrialBootstrapSpec("0" * 64, "0" * 32, "1" * 32)
    for bad in (replace(spec, seed_hex="F" * 64), replace(spec, branch_id="0" * 31),
                replace(spec, stream_id=cast(str, None)),
                replace(spec, initial_tick=Tick(-1)), replace(spec, initial_revision=WorldRevision(True))):
        with pytest.raises(BootstrapError, match="INVALID_INITIAL_STATE"):
            bootstrap_trial(bad)


@pytest.mark.parametrize("tick,revision", [(MAX_INT, 0), (0, MAX_INT)])
def test_final_tick_revision_guard(tick: int, revision: int) -> None:
    live = session(tick=tick, revision=revision)
    before = live.snapshot(), live.protocol()
    result = live.driver.submit(command(revision=revision))
    assert isinstance(result, TurnAborted) and result.failure.code == "INTEGER_OVERFLOW"
    assert (live.snapshot(), live.protocol()) == before
