from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
import secrets
import subprocess
import sys

from app.feature_registry import feature_bundles
from app.headless import state_io
from app.headless import BootstrapSpec, _CheckpointFactory, bootstrap, replay_runner
from contracts.read_views import ViewEpoch
from contracts.replay import ReplayFixture, ReplaySession
from contracts.skeleton import POSITION
from contracts.turn import ProtocolSnapshot, TurnDriver, TurnPublication
from domain.canonical import hash_document
from domain.primitives import EntityId, Phase
from domain.state_types import CoreSnapshot, StoredRoot
from orchestration.read_views import ObservedReadViewFactory
from orchestration.replay import Recorder, Runner
from orchestration.skeleton import CounterAdapter, PositionAdapter
from tests.replay.test_golden import fixture


class _ObservedSession:
    def __init__(self, session: ReplaySession, owner: _Factory) -> None:
        self._session, self._owner = session, owner

    @property
    def driver(self) -> TurnDriver:
        return self._session.driver

    def snapshot(self) -> CoreSnapshot:
        return self._session.snapshot()

    def protocol(self) -> ProtocolSnapshot:
        return self._session.protocol()

    def last_publication(self) -> TurnPublication:
        publication = self._session.last_publication()
        self._owner.publications.append(publication)
        return replace(publication, facts=()) if self._owner.drop_facts else publication


class _Factory:
    def __init__(self, *, drop_facts: bool = False, warm: bool = False) -> None:
        self.drop_facts, self.warm = drop_facts, warm
        self.restores = 0
        self.publications: list[TurnPublication] = []

    def restore(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> ReplaySession:
        self.restores += 1
        if self.warm:
            # Query an actual guarded cache, expire it, then restore the same authoritative head.
            view_factory = ObservedReadViewFactory(StoredRoot(core.components, 0))
            view_factory.register(PositionAdapter())
            view_factory.register(CounterAdapter())
            epoch = ViewEpoch(core.tick, Phase.PRESENT, 0, "test.cache", 0)
            port = view_factory.open(epoch)
            port.component(POSITION, EntityId("actor:toy")).x
            port.component(POSITION, EntityId("actor:toy")).x
            view_factory.close(epoch)
        return _ObservedSession(_CheckpointFactory(feature_bundles(EntityId("actor:toy"))).restore(core, protocol), self)



IO = state_io(feature_bundles(EntityId("actor:toy")))
core_hash, protocol_document = IO.hash_core, IO.encode_protocol


def test_removed_record_only_fact_detected_with_same_state() -> None:
    data = fixture()
    factory = _Factory(drop_facts=True)
    mismatches = Runner(data.initial_core, data.initial_protocol, factory=factory, io=IO).run(data.trace)
    assert factory.restores == 1 and len(factory.publications) == 5
    assert tuple((m.step_index, m.path, m.actual) for m in mismatches) == (
        (0, "$facts[0]", "<missing>"), (1, "$facts[0]", "<missing>"), (2, "$facts[0]", "<missing>"),
    )


def test_repeated_runner_and_warm_cold_cache_are_isolated() -> None:
    data = fixture()
    for warm in (False, True):
        factory = _Factory(warm=warm)
        runner = Runner(data.initial_core, data.initial_protocol, factory=factory, io=IO)
        assert runner.run(data.trace) == runner.run(data.trace) == ()
        assert factory.restores == 2 and len(factory.publications) == 10
        assert factory.publications[:5] == factory.publications[5:]


def _other_world(data: ReplayFixture) -> ReplayFixture:
    session = bootstrap(BootstrapSpec("2" * 64, "0" * 32, "1" * 32))
    initial_core, initial_protocol = session.snapshot(), session.protocol()
    header = replace(data.trace.header, world_id=initial_core.world_id, world_seed_hex=initial_core.world_seed_hex,
                     initial_core_hash=core_hash(initial_core), initial_protocol_hash=hash_document("protocol/v1", protocol_document(initial_protocol)))
    recorder = Recorder(header, io=IO)
    for step in data.trace.steps:
        session.driver.submit(step.command)
        recorder.record(step.command, session.last_publication(), session.snapshot(), session.protocol())
    # This is reproducibility evidence, not an independently authored golden expectation.
    return ReplayFixture(initial_core, initial_protocol, recorder.finish())


def test_world_order_isolation() -> None:
    first = fixture()
    second = _other_world(first)
    x, y = replay_runner(first), replay_runner(second)
    assert x.run(first.trace) == y.run(second.trace) == ()
    assert y.run(second.trace) == x.run(first.trace) == ()
    assert first.initial_core.world_id != second.initial_core.world_id
    assert first.trace.steps[0].expected_core_hash != second.trace.steps[0].expected_core_hash


def test_hashseed_processes() -> None:
    root = Path(__file__).resolve().parents[2]
    assert os.environ.get("RS_P0_HASHSEED_CHILD") != "1"
    chosen = str(2 + secrets.randbelow(2**32 - 2))
    argv = [sys.executable, "-m", "pytest", "-q", "tests/replay/test_golden.py::test_core_trace"]
    for seed in ("0", "1", chosen):
        environment = dict(os.environ, PYTHONHASHSEED=seed, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", RS_P0_HASHSEED_CHILD="1")
        result = subprocess.run(argv, cwd=root, env=environment, capture_output=True, text=True, timeout=45, check=False)
        print(f"PYTHONHASHSEED={seed} argv={argv!r} exit={result.returncode}")
        assert result.returncode == 0, result.stdout + result.stderr
        assert "1 passed" in result.stdout
