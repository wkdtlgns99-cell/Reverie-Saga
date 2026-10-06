from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from contracts.turn import GameCommand, ProtocolSnapshot, RngService as RngService, TurnDriver, TurnOutcome, TurnPublication
from domain.primitives import EntityId, Phase, Tick
from domain.state_types import CoreSnapshot


@dataclass(frozen=True, slots=True)
class RngAddress:
    logical_tick: Tick
    phase: Phase
    wave: int
    engine_id: str
    entity_id: EntityId
    purpose: str
    causal_key: str


@dataclass(frozen=True, slots=True)
class PackagePin:
    package_id: str
    version: int
    sha256: str


@dataclass(frozen=True, slots=True)
class ReplayHeader:
    world_id: str
    world_seed_hex: str
    initial_core_hash: str
    initial_protocol_hash: str
    schema_fingerprint: str
    rules_fingerprint: str
    schedule_fingerprint: str
    rng_version: str
    hash_version: str
    gameplay_packages: tuple[PackagePin, ...]
    build_artifacts: tuple[PackagePin, ...]


@dataclass(frozen=True, slots=True)
class ReplayWitness:
    canonical_core_json: bytes
    canonical_protocol_json: bytes
    canonical_facts_json: bytes
    canonical_diff_json: bytes


@dataclass(frozen=True, slots=True)
class ReplayStep:
    command: GameCommand
    expected_outcome: TurnOutcome
    expected_core_hash: str
    expected_protocol_hash: str
    expected_facts_hash: str
    expected_diff_hash: str
    expected_witness: ReplayWitness | None


@dataclass(frozen=True, slots=True)
class ReplayTrace:
    header: ReplayHeader
    steps: tuple[ReplayStep, ...]


@dataclass(frozen=True, slots=True)
class ReplayMismatch:
    step_index: int
    path: str
    expected: str
    actual: str


class ReplayRunner(Protocol):
    def run(self, trace: ReplayTrace) -> tuple[ReplayMismatch, ...]: ...


@dataclass(frozen=True, slots=True)
class ReplayFixture:
    initial_core: CoreSnapshot
    initial_protocol: ProtocolSnapshot
    trace: ReplayTrace


class ReplayRecorder(Protocol):
    def record(self, command: GameCommand, publication: TurnPublication,
               core: CoreSnapshot, protocol: ProtocolSnapshot) -> ReplayStep: ...
    def finish(self) -> ReplayTrace: ...


class ReplaySession(Protocol):
    @property
    def driver(self) -> TurnDriver: ...
    def snapshot(self) -> CoreSnapshot: ...
    def protocol(self) -> ProtocolSnapshot: ...
    def last_publication(self) -> TurnPublication: ...


class ReplaySessionFactory(Protocol):
    def restore(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> ReplaySession: ...
