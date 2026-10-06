from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import hashlib
import re
import sys
from typing import Protocol, cast

from app.feature_registry import feature_bundles, rng_purposes
from contracts.errors import BootstrapError
from contracts.persistence import DurableCommitPort
from contracts.replay import ReplayFixture, ReplayRunner, ReplaySession
from contracts.skeleton import FeatureBundle
from contracts.state_io import StateIO
from contracts.turn import (
    CompiledSchedule, ProtocolSnapshot, RngService, StreamCursor, TurnDriver, TurnPublication,
)
from domain.canonical import (
    canonical_json, decode_json, object_value, pack,
)
from domain.primitives import EntityId, Tick, WorldRevision, require_integer
from domain.state_types import CoreSnapshot, CounterRecord, PositionRecord
from orchestration.scheduler import compile_schedule
from orchestration.rng import CounterRngService
from orchestration.replay import Runner, validate_checkpoint
from orchestration.serialization import RegisteredStateIO
from orchestration.turn import Driver


@dataclass(frozen=True, slots=True)
class BootstrapSpec:
    seed_hex: str
    branch_id: str
    stream_id: str
    actor_id: EntityId = EntityId("actor:toy")
    initial_x: int = 0
    initial_visits: int = 0
    initial_tick: Tick = Tick(0)
    initial_revision: WorldRevision = WorldRevision(0)


class HeadlessSession(Protocol):
    @property
    def driver(self) -> TurnDriver: ...
    def snapshot(self) -> CoreSnapshot: ...
    def protocol(self) -> ProtocolSnapshot: ...
    def last_publication(self) -> TurnPublication: ...
    def submit_json(self, body: bytes) -> TurnPublication: ...


class _Session:
    def __init__(self, driver: Driver, io: StateIO) -> None:
        self._driver = driver
        self._io = io

    @property
    def driver(self) -> TurnDriver:
        return self._driver
    def snapshot(self) -> CoreSnapshot:
        return self._driver.snapshot()
    def protocol(self) -> ProtocolSnapshot:
        return self._driver.protocol()
    def last_publication(self) -> TurnPublication:
        return self._driver.last_publication()

    def submit_json(self, body: bytes) -> TurnPublication:
        try:
            if not 1 <= len(body) <= 16384:
                raise ValueError("command body cap")
            command = self._io.decode_command(object_value(decode_json(body)))
        except (ValueError, TypeError, UnicodeError, RecursionError):
            return self._driver.reject_malformed()
        self._driver.submit(command)
        return self._driver.last_publication()


def bootstrap(spec: BootstrapSpec, *, bundles: tuple[FeatureBundle, ...] | None = None,
              rng: RngService | None = None) -> HeadlessSession:
    selected = feature_bundles(spec.actor_id) if bundles is None else bundles
    if re.fullmatch("[0-9a-f]{64}", spec.seed_hex) is None or any(
        re.fullmatch("[0-9a-f]{32}", s) is None for s in (spec.branch_id, spec.stream_id)
    ):
        raise BootstrapError("DUPLICATE_SCHEMA", "invalid bootstrap identifiers")
    require_integer(spec.initial_tick)
    require_integer(spec.initial_revision)
    io = state_io(selected)
    pins = io.pins
    rules_hash, catalog_hash = pins.rules_fingerprint, pins.gameplay_catalog_hash
    world_id = "w1-" + hashlib.sha256(pack(("world-id/v1", spec.seed_hex, rules_hash, catalog_hash))).hexdigest()
    core = CoreSnapshot(world_id, spec.seed_hex, spec.initial_tick,
                        (CounterRecord(spec.actor_id, spec.initial_visits), PositionRecord(spec.actor_id, spec.initial_x)), (), pins)
    protocol = ProtocolSnapshot(spec.branch_id, spec.initial_revision,
                                (StreamCursor(spec.stream_id, spec.actor_id, 0, "active"),), ())
    return _restore(core, protocol, selected, rng if rng is not None else CounterRngService(spec.seed_hex, world_id, rng_purposes()), io=io)


def state_io(bundles: tuple[FeatureBundle, ...]) -> StateIO:
    bindings = tuple(b for f in bundles for b in f.bindings)
    schedule = compile_schedule(tuple(b.engine.manifest for b in bindings),
                                tuple(a for b in bindings for a in b.activations))
    return RegisteredStateIO(bundles, schedule)


def _restore(core: CoreSnapshot, protocol: ProtocolSnapshot, bundles: tuple[FeatureBundle, ...],
             rng: RngService, schedule: CompiledSchedule | None = None, *, io: StateIO | None = None,
             commit_port: DurableCommitPort | None = None) -> _Session:
    selected_io = state_io(bundles) if io is None else io
    if schedule is not None and schedule != selected_io.schedule:
        raise BootstrapError("INVALID_ACTIVATION", "checkpoint schedule fingerprint")
    return _Session(Driver(core, protocol, bundles, selected_io.schedule, rng, io=selected_io,
                           commit_port=commit_port), selected_io)


def restore_checkpoint(core: CoreSnapshot, protocol: ProtocolSnapshot, *,
                       bundles: tuple[FeatureBundle, ...], rng: RngService | None = None) -> HeadlessSession:
    io = state_io(bundles)
    validate_checkpoint(core, protocol, io=io)
    return _restore(core, protocol, bundles,
                    rng if rng is not None else CounterRngService(core.world_seed_hex, core.world_id, rng_purposes()), io=io)


class _CheckpointFactory:
    def __init__(self, bundles: tuple[FeatureBundle, ...]) -> None:
        self._bundles = tuple(bundles)

    def restore(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> ReplaySession:
        return restore_checkpoint(core, protocol, bundles=self._bundles)


def replay_runner(fixture: ReplayFixture, *, bundles: tuple[FeatureBundle, ...] | None = None) -> ReplayRunner:
    selected = feature_bundles(EntityId("actor:toy")) if bundles is None else tuple(bundles)
    io = state_io(selected)
    return Runner(fixture.initial_core, fixture.initial_protocol, factory=_CheckpointFactory(selected), io=io)


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv:
        raise ValueError("headless CLI accepts stdin commands only")
    session = cast(_Session, bootstrap(BootstrapSpec("0" * 64, "0" * 32, "1" * 32)))
    for line in sys.stdin.buffer:
        if not line.strip():
            continue
        publication = session.submit_json(line.rstrip(b"\r\n"))
        sys.stdout.buffer.write(canonical_json(session._io.encode_publication(publication)) + b"\n")
        sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
