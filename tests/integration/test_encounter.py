from __future__ import annotations

from dataclasses import replace
import os
import subprocess
import sys
from typing import Literal, cast

import pytest

from app.encounter import EncounterBootstrapSpec, bootstrap_encounter, main
from app.encounter_registry import encounter_bundle
from app.headless import state_io
from contracts.encounter import (
    STAMINA, AttackCommand, Defeated, EncounterMoveBlocked,
    EncounterMoved, RestCommand,
)
from contracts.encounter import GateChanged, HitPointsDelta, InteractCommand, StaminaRead
from contracts.errors import BootstrapError, ExpiredReadView
from contracts.messages import PresentationEvent, StateDelta, WorldEvent
from contracts.read_views import ComponentPatch, ReadPort, StagingEditor
from contracts.trial import TRIAL_MAP, CellDelta, MoveCommand, TrialMapRead
from contracts.turn import (
    AdmittedCommand, AdmissionOutcome, CapabilityManifest, CommitReceipt,
    EngineInvocation, EngineResult, GameCommand, ProtocolSnapshot,
    TurnAborted, TurnCommitted, TurnRejected,
)
from domain.canonical import JsonObject, array_value, canonical_json, int_value, object_value, text_value
from domain.encounter import (
    ATTACK_PROFILE_ID, ENEMY_ID, GATE_ID, GateRecord, HitPointsRecord, StaminaRecord,
    life_status, stamina_status,
)
from domain.primitives import MAX_INT, EntityId, FrozenPayload, Tick, TypeKey, WorldRevision
from domain.state_types import ComponentRecord, CoreSnapshot
from domain.trial import ACTOR_ID, SPACE_ID, CellPositionRecord
from engines.encounter import EncounterActions, EncounterMovement
from orchestration.encounter import (
    EncounterAdmission, EncounterCheckpointPolicy, EncounterPayloadCodec, EncounterPresenter,
    GatePatchRoute, HitPointsReducer, StaminaReducer,
)
from tests.unit.encounter_fixtures import ROOT, command, reference, session, vector_session


@pytest.mark.parametrize("vector", tuple(object_value(v) for v in array_value(reference("movement_vectors"))))
def test_movement_vectors(vector: JsonObject) -> None:
    live = vector_session(object_value(vector["state"]))
    before = live.snapshot()
    result = live.driver.submit(command(MoveCommand(int_value(vector["dx"]), int_value(vector["dz"]))))
    assert isinstance(result, TurnCommitted)
    assert (live.snapshot().tick, live.protocol().revision) == (1, 1)
    assert live.snapshot().components[:6] == before.components[:6]
    assert live.snapshot().components[6] == CellPositionRecord(ACTOR_ID, SPACE_ID, int_value(vector["to_cell"]))
    pub = live.last_publication()
    assert pub.diff is not None
    assert (len(pub.diff.changes), len(pub.facts), len(pub.cues)) == (vector["delta_count"], vector["fact_count"], vector["cue_count"])
    fact = pub.facts[0].payload
    assert isinstance(fact, (EncounterMoved, EncounterMoveBlocked))
    assert ("moved" if isinstance(fact, EncounterMoved) else fact.reason) == vector["result"]
    assert pub.facts[0].header.producer_rank == 1 and not pub.diagnostics


@pytest.mark.parametrize("vector", tuple(object_value(v) for v in array_value(reference("interaction_vectors"))))
def test_interaction_vectors(vector: JsonObject) -> None:
    live = vector_session(object_value(vector["state"]))
    before = live.snapshot(), live.protocol()
    result = live.driver.submit(command(InteractCommand(GATE_ID, cast("LiteralOpenClose", text_value(vector["option"])))))
    if vector["rejection"] is not None:
        assert isinstance(result, TurnRejected) and result.failure.code == vector["rejection"]
        assert (live.snapshot(), live.protocol()) == before
        assert live.last_publication().diff is None
    else:
        assert isinstance(result, TurnCommitted)
        assert live.snapshot().components[0] == GateRecord(GATE_ID, SPACE_ID, 4, int_value(vector["gate_after"]))
        assert live.snapshot().components[1:] == before[0].components[1:]
        pub = live.last_publication()
        assert pub.diff is not None and len(pub.diff.changes) == vector["delta_count"]
        assert len(pub.facts) == len(pub.cues) == 1 and not pub.diagnostics
        assert isinstance(pub.facts[0].payload, GateChanged)


type LiteralOpenClose = Literal["open", "close"]


@pytest.mark.parametrize("vector", tuple(object_value(v) for v in array_value(reference("attack_vectors"))))
def test_attack_counter_atomicity(vector: JsonObject) -> None:
    live = session(cell=7, actor_hp=int_value(vector["actor_hp_before"]),
                   enemy_hp=int_value(vector["target_hp_before"]), stamina=int_value(vector["stamina_before"]))
    old = live.snapshot()
    assert isinstance(live.driver.submit(command(AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID))), TurnCommitted)
    head = live.snapshot()
    assert head.components[1:4] == (HitPointsRecord(ENEMY_ID, int_value(vector["target_hp_after"])),
                                   HitPointsRecord(ACTOR_ID, int_value(vector["actor_hp_after"])),
                                   StaminaRecord(ACTOR_ID, int_value(vector["stamina_after"])))
    assert head.components[:1] + head.components[4:] == old.components[:1] + old.components[4:]
    pub = live.last_publication()
    assert pub.diff is not None
    assert (len(pub.diff.changes), len(pub.facts), len(pub.cues)) == (vector["delta_count"], vector["fact_count"], vector["fact_count"])
    assert not pub.diagnostics
    assert pub.cues[0].payload.schema.kind == "encounter.attack-cue"
    assert io_payload(pub.cues[0].payload)["result"] == vector["result"]
    if vector["fact_count"] == 2:
        victim, killer = (ENEMY_ID, ACTOR_ID) if vector["target_hp_after"] == 0 else (ACTOR_ID, ENEMY_ID)
        assert pub.facts[1].payload == Defeated(victim, killer)
    assert [d.target.entity_id for d in pub.diff.changes if isinstance(d, HitPointsDelta)] == ([ENEMY_ID] if vector["actor_hp_before"] == vector["actor_hp_after"] else [ENEMY_ID, ACTOR_ID])
    assert (head.tick, live.protocol().revision, len(live.protocol().receipts)) == (1, 1, 1)


def io_payload(payload: FrozenPayload) -> JsonObject:
    return EncounterPayloadCodec(payload.schema).encode(payload)


@pytest.mark.parametrize("death", (False, True))
def test_full_publications(death: bool) -> None:
    io = state_io((encounter_bundle(),))
    fixture = object_value(reference("death_fixture" if death else "expected_fixture"))
    steps = array_value(object_value(fixture["trace"])["steps"])
    live = session(cell=7, actor_hp=1) if death else session()
    for step, publication in zip(steps, array_value(reference("death_publications" if death else "expected_publications")), strict=True):
        cmd = io.decode_command(object_value(object_value(step)["command"]))
        live.driver.submit(cmd)
        assert canonical_json(io.encode_publication(live.last_publication())) == canonical_json(publication)


@pytest.mark.parametrize("payload,cell,enemy_hp,stamina,code", (
    (AttackCommand(GATE_ID, ATTACK_PROFILE_ID), 0, 0, 0, "INVALID_TARGET"),
    (AttackCommand(ENEMY_ID, "attack:unknown"), 0, 0, 0, "INVALID_ATTACK_PROFILE"),
    (AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID), 0, 0, 0, "TARGET_DEFEATED"),
    (AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID), 4, 5, 0, "OUT_OF_RANGE"),
    (AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID), 7, 5, 0, "INSUFFICIENT_STAMINA"),
    (InteractCommand(ENEMY_ID, "close"), 4, 5, 0, "INVALID_TARGET"),
    (InteractCommand(GATE_ID, "close"), 4, 5, 0, "TARGET_OCCUPIED"),
    (InteractCommand(GATE_ID, "open"), 0, 5, 0, "OUT_OF_RANGE"),
))
def test_rejection_no_time(payload: AttackCommand | InteractCommand, cell: int,
                           enemy_hp: int, stamina: int, code: str) -> None:
    live = session(cell=cell, gate=1, enemy_hp=enemy_hp, stamina=stamina)
    before = live.snapshot(), live.protocol()
    outcome = live.driver.submit(command(payload))
    assert isinstance(outcome, TurnRejected) and outcome.failure.code == code and outcome.current_revision == 0
    assert (live.snapshot(), live.protocol()) == before
    pub = live.last_publication()
    assert not pub.facts and not pub.cues and pub.diff is None
    assert isinstance(live.driver.submit(command(RestCommand())), TurnCommitted)


def test_death_retry() -> None:
    live = session(cell=7, actor_hp=1)
    attack = command(AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID))
    first = live.driver.submit(attack)
    assert isinstance(first, TurnCommitted)
    assert live.snapshot().components[2] == HitPointsRecord(ACTOR_ID, 0)
    before = live.snapshot(), live.protocol()
    assert live.driver.submit(attack) == first
    assert live.last_publication().diff is None and not live.last_publication().facts
    for cmd, code in ((command(sequence=2, revision=1), "ACTOR_DEFEATED"),
                      (command(), "COMMAND_ID_CONFLICT"),
                      (command(MoveCommand(1, 0), sequence=2, revision=1), "ACTOR_DEFEATED")):
        result = live.driver.submit(cmd)
        assert isinstance(result, TurnRejected) and result.failure.code == code
        assert (live.snapshot(), live.protocol()) == before


@pytest.mark.parametrize("vector", tuple(object_value(v) for v in array_value(reference("rest_vectors"))))
def test_noop_time(vector: JsonObject) -> None:
    live = session(actor_hp=1, stamina=int_value(vector["before"]))
    old = live.snapshot()
    result = live.driver.submit(command())
    assert isinstance(result, TurnCommitted)
    pub = live.last_publication()
    assert pub.diff is not None and len(pub.diff.changes) == vector["delta_count"]
    assert live.snapshot().components[3] == StaminaRecord(ACTOR_ID, int_value(vector["after"]))
    assert live.snapshot().components[:3] + live.snapshot().components[4:] == old.components[:3] + old.components[4:]
    assert (result.receipt.tick, result.receipt.revision, live.protocol().streams[0].highest_committed_sequence) == (1, 1, 1)
    assert len(pub.facts) == len(pub.cues) == len(live.protocol().receipts) == 1


class _FaultActions:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.retained: StaminaRead | None = None
        self.calculated: EngineResult | None = None

    @property
    def manifest(self) -> CapabilityManifest:
        return EncounterActions().manifest

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        self.retained = invocation.state.component(STAMINA, ACTOR_ID)
        result = EncounterActions().evaluate(invocation)
        self.calculated = result
        if self.mode == "engine":
            raise RuntimeError("fault after real three-address calculation")
        if self.mode == "admitted":
            assert invocation.action is not None
            changed = replace(invocation, action=replace(invocation.action,
                              payload=AttackCommand(GATE_ID, ATTACK_PROFILE_ID)))
            return EncounterActions().evaluate(changed)
        if self.mode == "read":
            _ = invocation.state.component(TRIAL_MAP, SPACE_ID).width
        if self.mode == "foreign":
            result = replace(result, deltas=(*result.deltas, HitPointsDelta(GATE_ID, 3, 2)))
        if self.mode == "position":
            result = replace(result, deltas=(*result.deltas, CellDelta(ACTOR_ID, 7, 6)))
        if self.mode == "duplicate":
            result = replace(result, deltas=(*result.deltas, result.deltas[0]))
        return result


class _FaultStamina(StaminaReducer):
    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        super().stage(delta, before, editor)
        raise ValueError("fault after real HP and stamina staging")


class _CrossReadHP(HitPointsReducer):
    def __init__(self, net: bool) -> None:
        self.net = net
        self.retained: StaminaRead | None = None

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        super().stage(delta, before, editor)
        if not self.net:
            self.retained = before.component(STAMINA, ACTOR_ID)
            _ = self.retained.value

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        super().validate_net(delta, after)
        if self.net:
            self.retained = after.component(STAMINA, ACTOR_ID)
            _ = self.retained.value


class _FaultPolicy(EncounterCheckpointPolicy):
    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        super().validate(core, protocol)
        if core.tick:
            raise ValueError("fault after valid candidate checkpoint")


@pytest.mark.parametrize("mode,code", (
    ("engine", "ENGINE_EXCEPTION"), ("read", "UNDECLARED_READ"),
    ("admitted", "INVALID_ACTION"),
    ("foreign", "INVALID_DELTA"), ("position", "UNDECLARED_WRITE"),
    ("duplicate", "DUPLICATE_TARGET"), ("stage", "ENGINE_EXCEPTION"),
    ("stage_read", "UNDECLARED_READ"), ("net_read", "ENGINE_EXCEPTION"),
    ("policy", "ENGINE_EXCEPTION"),
))
def test_candidate_failures(mode: str, code: str) -> None:
    selected = encounter_bundle()
    engine = _FaultActions(mode)
    reducer = _CrossReadHP(mode == "net_read")
    selected = replace(selected, bindings=(replace(selected.bindings[0], engine=engine), selected.bindings[1]))
    if mode == "stage":
        selected = replace(selected, delta_routes=tuple(_FaultStamina() if r.schema.kind == "encounter.stamina-delta" else r for r in selected.delta_routes))
    if mode in ("stage_read", "net_read"):
        selected = replace(selected, delta_routes=tuple(reducer if r.schema.kind == "encounter.hp-delta" else r for r in selected.delta_routes))
    if mode == "policy":
        selected = replace(selected, checkpoint_policy=_FaultPolicy())
    live = session(selected, cell=7)
    before = live.snapshot(), live.protocol()
    result = live.driver.submit(command(AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID)))
    assert isinstance(result, TurnAborted) and result.failure.code == code
    assert (live.snapshot(), live.protocol()) == before
    pub = live.last_publication()
    assert pub.diff is None and not pub.facts and not pub.cues
    assert engine.calculated is not None and len(engine.calculated.deltas) == 3
    assert engine.retained is not None
    with pytest.raises(ExpiredReadView):
        _ = engine.retained.value
    if reducer.retained is not None:
        with pytest.raises(ExpiredReadView):
            _ = reducer.retained.value


class _ProtectedGatePatch(GatePatchRoute):
    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        result = super().apply(before, patch)
        assert isinstance(result, GateRecord)
        return replace(result, space_id=EntityId("space:other"))


def test_protected_reference_patch() -> None:
    selected = encounter_bundle()
    selected = replace(selected, patch_routes=tuple(_ProtectedGatePatch() if p.schema.kind == "encounter.gate-patch" else p for p in selected.patch_routes))
    live = session(selected, cell=3)
    before = live.snapshot(), live.protocol()
    result = live.driver.submit(command(InteractCommand(GATE_ID, "open")))
    assert isinstance(result, TurnAborted) and result.failure.code == "UNDECLARED_WRITE"
    assert (live.snapshot(), live.protocol()) == before


class _BadPresenter(EncounterPresenter):
    def __init__(self) -> None:
        self.retained: StaminaRead | None = None

    def map(self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt,
            committed: ReadPort) -> tuple[PresentationEvent, ...]:
        super().map(facts, receipt, committed)
        self.retained = committed.component(STAMINA, ACTOR_ID)
        _ = self.retained.value
        raise ValueError("fault after real postcommit cues")


class _BadCueCodec(EncounterPayloadCodec):
    def encode(self, payload: FrozenPayload) -> JsonObject:
        raise ValueError("postcommit cue encoding fault")


@pytest.mark.parametrize("mode", ("presenter", "codec"))
def test_postcommit_failure(mode: str) -> None:
    selected, presenter = encounter_bundle(), _BadPresenter()
    if mode == "presenter":
        selected = replace(selected, presenters=(replace(selected.presenters[0], presenter=presenter),))
    else:
        selected = replace(selected, codecs=tuple(_BadCueCodec(c.schema) if c.schema.kind == "encounter.attack-cue" else c for c in selected.codecs))
    live = session(selected, cell=7, enemy_hp=1)
    assert isinstance(live.driver.submit(command(AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID))), TurnCommitted)
    assert live.snapshot().components[1:4] == (HitPointsRecord(ENEMY_ID, 0), HitPointsRecord(ACTOR_ID, 3), StaminaRecord(ACTOR_ID, 1))
    pub = live.last_publication()
    assert len(pub.facts) == 2 and pub.diff is not None and len(pub.diff.changes) == 2 and not pub.cues
    assert pub.diagnostics[0].code == "PRESENTATION_FAILED"
    assert len(live.protocol().receipts) == 1
    if presenter.retained is not None:
        with pytest.raises(ExpiredReadView):
            _ = presenter.retained.value


def test_cli_and_query() -> None:
    io, live = state_io((encounter_bundle(),)), session()
    before = live.snapshot(), live.protocol()
    for _ in range(3):
        core = live.snapshot()
        assert isinstance(core.components[2], HitPointsRecord) and isinstance(core.components[3], StaminaRecord)
        assert (life_status(core.components[2].hp), stamina_status(core.components[3].value)) == ("alive", "ready")
        io.encode_core(core)
        io.encode_protocol(live.protocol())
    assert (live.snapshot(), live.protocol()) == before
    fixture = object_value(reference("expected_fixture"))
    steps = array_value(object_value(fixture["trace"])["steps"])
    bodies = [canonical_json(object_value(step)["command"]) for step in steps]
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    result = subprocess.run([sys.executable, "-m", "app.encounter"], input=b"\n" + b"\n".join(bodies) + b"\n", cwd=ROOT, env=env, capture_output=True, check=False, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [canonical_json(pub) for pub in array_value(reference("expected_publications"))]
    with pytest.raises(ValueError):
        main(("--unexpected",))


@pytest.mark.parametrize("field,value", (
    ("initial_cell", -1), ("initial_cell", 1), ("initial_cell", 4), ("initial_cell", 8),
    ("initial_cell", 9), ("gate_open", True), ("gate_open", 2), ("actor_hp", 4),
    ("enemy_hp", -1), ("enemy_hp", 6), ("stamina", cast(int, 1.0)), ("stamina", 3),
    ("initial_tick", -1), ("initial_revision", True),
))
def test_invalid_bootstrap(field: str, value: int) -> None:
    spec = EncounterBootstrapSpec("0" * 64, "0" * 32, "1" * 32)
    if field == "initial_cell":
        bad = replace(spec, initial_cell=value)
    elif field == "gate_open":
        bad = replace(spec, gate_open=value)
    elif field == "actor_hp":
        bad = replace(spec, actor_hp=value)
    elif field == "enemy_hp":
        bad = replace(spec, enemy_hp=value)
    elif field == "stamina":
        bad = replace(spec, stamina=value)
    elif field == "initial_tick":
        bad = replace(spec, initial_tick=Tick(value))
    else:
        bad = replace(spec, initial_revision=WorldRevision(value))
    with pytest.raises(BootstrapError, match="INVALID_INITIAL_STATE"):
        bootstrap_encounter(bad)


@pytest.mark.parametrize("tick,revision", ((MAX_INT, 0), (0, MAX_INT)))
def test_final_tick_revision_guard(tick: int, revision: int) -> None:
    live = session(tick=tick, revision=revision)
    before = live.snapshot(), live.protocol()
    result = live.driver.submit(command(revision=revision))
    assert isinstance(result, TurnAborted) and result.failure.code == "INTEGER_OVERFLOW"
    assert (live.snapshot(), live.protocol()) == before


class _ObservedMovement:
    def __init__(self) -> None:
        self.retained: TrialMapRead | None = None

    @property
    def manifest(self) -> CapabilityManifest:
        return EncounterMovement().manifest

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        self.retained = invocation.state.component(TRIAL_MAP, SPACE_ID)
        return EncounterMovement().evaluate(invocation)


def test_boundary_guard_and_exhausted_movement() -> None:
    selected, engine = encounter_bundle(), _ObservedMovement()
    selected = replace(selected, bindings=(selected.bindings[0], replace(selected.bindings[1], engine=engine)))
    live = session(selected, cell=5, stamina=0)
    assert isinstance(live.driver.submit(command(MoveCommand(1, 0))), TurnCommitted)
    assert live.last_publication().facts[0].payload == EncounterMoveBlocked(ACTOR_ID, SPACE_ID, 5, 1, 0, "boundary")
    assert engine.retained is not None
    with pytest.raises(ExpiredReadView):
        engine.retained.is_blocked(9)
    assert isinstance(live.driver.submit(command(MoveCommand(0, -1), sequence=2, revision=1)), TurnCommitted)
    assert live.snapshot().components[6] == CellPositionRecord(ACTOR_ID, SPACE_ID, 2)
    assert live.snapshot().components[3] == StaminaRecord(ACTOR_ID, 0)


class _FutureAttack(AttackCommand):
    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.attack", 2)


def test_typed_and_json_commands_reject_without_time() -> None:
    live, io = session(cell=7), state_io((encounter_bundle(),))
    before = live.snapshot(), live.protocol()
    for payload in (InteractCommand(GATE_ID, cast(LiteralOpenClose, "toggle")),
                    AttackCommand(ENEMY_ID, "bad profile"), MoveCommand(True, 0)):
        result = live.driver.submit(command(payload))
        assert isinstance(result, TurnRejected) and result.failure.code == "INVALID_COMMAND"
        assert result.current_revision == 0 and (live.snapshot(), live.protocol()) == before
    result = live.driver.submit(command(_FutureAttack(ENEMY_ID, ATTACK_PROFILE_ID)))
    assert isinstance(result, TurnRejected) and result.failure.code == "UNSUPPORTED_SCHEMA"
    result = live.driver.submit(replace(command(), actor_id=ENEMY_ID))
    assert isinstance(result, TurnRejected) and result.failure.code == "UNAUTHORIZED_ACTOR"
    base = io.encode_command(command(AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID)))
    bad_bodies: tuple[JsonObject, ...] = (
        {**base, "schema": {"kind": "encounter.attack", "version": 2}},
        {**base, "payload": {"target_id": ENEMY_ID}},
        {**base, "payload": {"target_id": ENEMY_ID, "profile_id": ATTACK_PROFILE_ID, "damage": 100}},
        {**base, "payload": {"target_id": True, "profile_id": ATTACK_PROFILE_ID}},
        {**base, "schema": {"kind": "encounter.rest", "version": 1}, "payload": {"value": 2}},
        {**base, "schema": {"kind": "encounter.interact", "version": 1}, "payload": {"target_id": GATE_ID, "option": "toggle"}},
    )
    raws = [canonical_json(body) for body in bad_bodies] + [
        b'{"actor_id":"actor:e\xcc\x81"}',
        canonical_json(base).replace(b'"expected_revision":0', b'"expected_revision":0.0'),
    ]
    for raw in raws:
        pub = live.submit_json(raw)
        assert isinstance(pub.outcome, TurnRejected) and pub.outcome.failure.code == "INVALID_COMMAND"
        assert pub.outcome.current_revision is None and (live.snapshot(), live.protocol()) == before
        assert not pub.facts and pub.diff is None and not pub.cues
    assert isinstance(live.driver.submit(command(AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID))), TurnCommitted)


def test_dead_actor_admission_precedes_target_errors() -> None:
    live = session(cell=7, actor_hp=0, stamina=0)
    before = live.snapshot(), live.protocol()
    for payload in (AttackCommand(GATE_ID, "attack:other"), InteractCommand(ENEMY_ID, "close"), RestCommand()):
        result = live.driver.submit(command(payload))
        assert isinstance(result, TurnRejected) and result.failure.code == "ACTOR_DEFEATED"
        assert (live.snapshot(), live.protocol()) == before


class _ChangedAdmission(EncounterAdmission):
    def admit(self, command: GameCommand, state: ReadPort, *, start_tick: Tick,
              world_id: str) -> AdmissionOutcome:
        result = super().admit(command, state, start_tick=start_tick, world_id=world_id)
        assert isinstance(result, AdmittedCommand)
        # Fault after genuine admission, exercising execution's independent recheck.
        return replace(result, action=replace(result.action, payload=AttackCommand(GATE_ID, ATTACK_PROFILE_ID)))


def test_driver_rejects_changed_admission_plan() -> None:
    selected = encounter_bundle()
    selected = replace(selected, command_routes=tuple(
        _ChangedAdmission(r.schema) if r.schema.kind == "encounter.attack" else r
        for r in selected.command_routes))
    live = session(selected, cell=7)
    before = live.snapshot(), live.protocol()
    result = live.driver.submit(command(AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID)))
    assert isinstance(result, TurnAborted) and result.failure.code == "INVALID_COMMAND"
    assert (live.snapshot(), live.protocol()) == before


def test_bootstrap_identifier_validation() -> None:
    spec = EncounterBootstrapSpec("0" * 64, "0" * 32, "1" * 32)
    for bad in (replace(spec, seed_hex="F" * 64), replace(spec, branch_id="0" * 31),
                replace(spec, stream_id=cast(str, None)),
                cast(EncounterBootstrapSpec, object())):
        with pytest.raises(BootstrapError, match="INVALID_INITIAL_STATE"):
            bootstrap_encounter(bad)


def test_attack_from_other_adjacent_cell() -> None:
    live = session(cell=5, actor_hp=1, enemy_hp=1, stamina=1)
    assert isinstance(live.driver.submit(command(AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID))), TurnCommitted)
    assert live.snapshot().components[1:4] == (HitPointsRecord(ENEMY_ID, 0), HitPointsRecord(ACTOR_ID, 1), StaminaRecord(ACTOR_ID, 0))
    assert len(live.last_publication().facts) == len(live.last_publication().cues) == 2
