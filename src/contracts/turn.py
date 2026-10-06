from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from contracts.messages import (
    CommandPayload, EmittedFact, PresentationEvent, StateDelta, StateDiff, WorldEvent,
)
from contracts.read_views import ComponentKey, ReadPort
from domain.primitives import CommandId, EntityId, FieldFamily, Phase, Tick, TypeKey, WorldRevision


@dataclass(frozen=True, slots=True)
class GameCommand:
    command_id: CommandId
    actor_id: EntityId
    expected_revision: WorldRevision
    payload: CommandPayload


@dataclass(frozen=True, slots=True)
class Failure:
    code: str
    message_key: str


def failure(code: str) -> Failure:
    return Failure(code, "error." + code.lower())


@dataclass(frozen=True, slots=True)
class TurnPlan:
    command: GameCommand
    start_tick: Tick
    target_tick: Tick


@dataclass(frozen=True, slots=True)
class CommitReceipt:
    command_id: CommandId
    previous_revision: WorldRevision
    revision: WorldRevision
    tick: Tick
    core_hash: str


@dataclass(frozen=True, slots=True)
class TurnRejected:
    failure: Failure
    current_revision: WorldRevision | None = None


@dataclass(frozen=True, slots=True)
class TurnAborted:
    failure: Failure


@dataclass(frozen=True, slots=True)
class TurnCommitted:
    receipt: CommitReceipt


type TurnOutcome = TurnRejected | TurnAborted | TurnCommitted


@dataclass(frozen=True, slots=True)
class NodeKey:
    phase: Phase
    engine_id: str


@dataclass(frozen=True, slots=True)
class CompiledSchedule:
    nodes: tuple[NodeKey, ...]
    fingerprint: str


@dataclass(frozen=True, slots=True)
class PhaseAccess:
    phase: Phase
    family: FieldFamily


@dataclass(frozen=True, slots=True)
class Dependency:
    at: Phase
    after: NodeKey


@dataclass(frozen=True, slots=True)
class CapabilityManifest:
    engine_id: str
    phases: tuple[Phase, ...]
    reads: tuple[PhaseAccess, ...]
    writes: tuple[PhaseAccess, ...]
    depends_on: tuple[Dependency, ...]
    emits: tuple[TypeKey, ...]
    consumes: tuple[TypeKey, ...]
    cost_class: Literal["constant", "local", "regional", "global"]


class RandomStream(Protocol):
    def draw_bounded(self, low: int, high_exclusive: int) -> int: ...


class EngineRng(Protocol):
    def stream(self, entity_id: EntityId, purpose: str, causal_key: str) -> RandomStream: ...


class RngService(Protocol):
    def scoped(self, tick: Tick, phase: Phase, wave: int, engine_id: str) -> EngineRng: ...


class DefinitionReadPort(Protocol):
    def definition[ReadT](self, key: ComponentKey[ReadT], entry_id: str) -> ReadT: ...


@dataclass(frozen=True, slots=True)
class AdmittedAction:
    actor_id: EntityId
    payload: CommandPayload
    semantic_key: str


@dataclass(frozen=True, slots=True)
class AdmittedCommand:
    plan: TurnPlan
    action: AdmittedAction


type AdmissionOutcome = AdmittedCommand | TurnRejected


@dataclass(frozen=True, slots=True)
class Degradation:
    producer_id: str
    code: str


@dataclass(frozen=True, slots=True)
class EngineInvocation:
    action: AdmittedAction | None
    logical_tick: Tick
    phase: Phase
    wave: int
    state: ReadPort
    definitions: DefinitionReadPort
    rng: EngineRng
    incoming: tuple[WorldEvent, ...]


@dataclass(frozen=True, slots=True)
class EngineResult:
    deltas: tuple[StateDelta, ...]
    facts: tuple[EmittedFact, ...]
    degraded: tuple[Degradation, ...]


class Engine(Protocol):
    @property
    def manifest(self) -> CapabilityManifest: ...
    def evaluate(self, invocation: EngineInvocation) -> EngineResult: ...


@dataclass(frozen=True, slots=True)
class NodeActivation:
    node: NodeKey
    action_kinds: tuple[TypeKey, ...]
    on_matching_events: bool
    every_tick: bool
    lane: Literal["A", "B"]


@dataclass(frozen=True, slots=True)
class EngineBinding:
    engine: Engine
    module_path: str
    activations: tuple[NodeActivation, ...]


class TurnDriver(Protocol):
    def compile(self, manifests: tuple[CapabilityManifest, ...],
                activations: tuple[NodeActivation, ...]) -> CompiledSchedule: ...
    def submit(self, command: GameCommand) -> TurnOutcome: ...


@dataclass(frozen=True, slots=True)
class StoredReceipt:
    command: GameCommand
    command_fingerprint: str
    receipt: CommitReceipt


@dataclass(frozen=True, slots=True)
class StreamCursor:
    stream_id: str
    actor_id: EntityId
    highest_committed_sequence: int
    status: Literal["active", "retired"]


@dataclass(frozen=True, slots=True)
class ProtocolSnapshot:
    branch_id: str
    revision: WorldRevision
    streams: tuple[StreamCursor, ...]
    receipts: tuple[StoredReceipt, ...]


@dataclass(frozen=True, slots=True)
class TurnPublication:
    outcome: TurnOutcome
    facts: tuple[WorldEvent, ...]
    diff: StateDiff | None
    cues: tuple[PresentationEvent, ...]
    diagnostics: tuple[Failure, ...]
