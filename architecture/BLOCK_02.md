# BLOCK 2 — Turn, Engine & Presentation Contracts

Date: 2026-10-03 | Task: RS-ARCH-002-B02 | Owner: GPT-6.1 Sol | Mode: DESIGN
Inputs: [BLOCK1](BLOCK_01.md), prompt A1–A3, MASTER §§2–3. Format: prompt **AI Documentation Format**.
Status: design/interface specification only. Code fences are proposed declarations, not implemented modules. Ellipsis occurs only in Protocol/ABC declarations. No runtime/tests/CI/graphics created.

## Contract Scope

This block resolves phase visibility, scheduling, plugin registration, typed extension, commit/presentation separation. [BLOCK3](BLOCK_03.md) resolves event identity, tick substeps, state/proxy schemas, and RNG/hash/replay, including the refinements below. [BLOCK4](BLOCK_04.md) defines admission/query/retry/save contracts; A10/A11/A12 later complete schemas/time/wire behavior. Remaining prerequisites are OPEN; no production order is READY.
Paths below are PLANNED: `src/contracts/turn.py`, `engine.py`, `events.py`; `src/orchestration/scheduler.py`; `src/app/feature_registry.py`; feature contracts/engines/presenters. Revisit layout in BLOCK9 before implementation. No v1 classes/formulas/test oracles are adopted.

Review correction AR-008: the concatenated listing is not a module dependency graph. NEW `src/domain/primitives.py` owns EntityId/CommandId/EventId/Tick/WorldRevision/Phase/TypeKey/FieldFamily/FieldAddress/FrozenPayload; later contracts import these names. Domain state records import domain primitives only. Concrete command/fact/delta/read/presenter contracts live in contracts; engines/orchestration/adapters/app obey the existing low-to-high layer order. No duplicated primitive declarations or domain import of contracts. P0-004 creates primitives before dependent state/views; P0-001 uses the same definitions. Exact package initializers/import configuration remain next-step order inputs.

## A1. Turn Pipeline / Scheduler

### A1.1 Phases & Visibility

Phase sequence: `VALIDATE → [PRE_TICK → RESOLVE → REACT → CASCADE → POST_TICK] → COMMIT → PRESENT`. BLOCK3 repeats the bracketed compiled tick program for long advances; admission/COMMIT/PRESENT occur once per player command, and RESOLVE receives the action only at its admitted action tick.
One authoritative turn runs at a time per world. Concurrent input is bounded/queued; no engine concurrency in the initial implementation. Engine work receives game ticks, never a wall clock.

| Phase | Input / allowed output | Invariant |
|---|---|---|
| VALIDATE | Typed command + committed read view → admission/turn plan | Pure; no time/RNG/state/event mutation. Reject before ticking. Query-only commands return committed read data outside this turn pipeline |
| PRE_TICK | Admitted plan; due pre-action rules → staged deltas/facts | No WorldState mutation; conditions may change before action |
| RESOLVE | Plan + PRE_TICK overlay → action deltas/facts | Recheck execution conditions; rule fizzle/partial failure is an explicit domain outcome, not invalid input |
| REACT | Previous phase facts/view → immediate consequences | Cross-engine interaction uses events, never direct calls |
| CASCADE | Unhandled immediate events → bounded event waves | Stable waves; no recursive engine calls; overflow aborts before COMMIT |
| POST_TICK | Resolved overlay → final upkeep/time delta | Tick advances once per tick substep; revision once per command; validate final invariants |
| COMMIT | Fully validated candidate → one receipt/version | Sole authoritative writer; all-or-nothing. Phase0 in memory; durable A9 transaction later |
| PRESENT | Committed facts/diff/read view → presentation outbox | Cannot change CORE; renderer failure cannot undo/repeat commit |

**Phase barrier rule:** all engines in one phase read the same phase-start overlay. Collect results, validate them, then apply them to the next overlay at the barrier. No full WorldState copy; overlay is touched-field staging over a stable committed base. Later same-phase engines MUST NOT see earlier same-phase writes. Dependencies cannot change this visibility rule.

Within CASCADE, each wave is a barrier: every subscribed engine receives its stable batch once; resulting writes/events become visible in the next wave. Never mix producer output into the current wave. An engine locally reduces multiple changes to one typed delta per concrete field target. Two deltas for the same field in one barrier fail; no implicit last-writer-wins/additive merging.

Cross-engine event subscription within a phase also consumes only phase-start input. A dependency orders invocation/diagnostics, not visibility. A consumer needing a newly produced value/event must move to a later phase/wave. This deliberately trades same-phase chaining for explicit, testable barriers.

### A1.2 Boot DAG / Deterministic Order

1. Load explicit feature registry; validate schema/kind/engine uniqueness and immutable registrations.
2. Create node `(phase, engine_id)` for each declared engine phase. VALIDATE/COMMIT/PRESENT are orchestrator-owned, not engine phases.
3. Add phase barriers and declared dependency edges. Referenced node must exist and be the same/earlier phase; later-phase dependencies fail.
4. Expand declared field-family selectors against the pinned state schema. Reject same-phase overlapping writes, even with dependency edges or expected different actors. Validate handlers/reads/writes/emits/consumes references.
5. Detect cycles/self-dependencies at boot. Stable topological ordering chooses the smallest `(phase ordinal, engine_id)` among available nodes; registry insertion/set order cannot affect output.
6. Freeze schedule for the session; replay stores its registration/schema/ruleset fingerprint. No runtime plugin discovery/hot reload.

Read/write overlap in a phase is legal only with documented phase-start semantics; dependency MUST NOT be interpreted as read-after-write. Bootstrap validation rejects impossible dependencies/unknown fields; feature integration examples must prove intended visibility. A later write may intentionally overwrite an earlier-phase field using the staged expected value.

### A1.3 Transaction / Retry / Failure

- Admission verifies session/world routing, command schema/version, actor/target availability and expected world version. Detailed command policies belong to A7. No input is silently coerced into an admitted action.
- Successfully committed duplicate command ID returns its recorded receipt before stale-version rejection; same ID with different content is rejected. No new tick, RNG consumption, facts, or application. Receipt retention/durable retry policy is finalized A9.
- A valid action can become impossible after PRE_TICK; commit its defined fizzle/cost/time consequences. Do not retroactively label it an invalid zero-mutation command.
- Runtime contract violation/exception/cascade overflow rejects the entire candidate; original WorldState/hash/tick and queued authoritative events remain unchanged. Retry uses the same declared deterministic input, not partially consumed RNG state.
- Every engine result is validated before staging. Final validation precedes COMMIT. Only commit owner holds mutation capability; engines/presenters receive read views.
- BLOCK5 prepares required public-state projection/delivery capacity before durability; no tentative data is transmitted. Optional cue mapping remains PRESENT after confirmed commit.
- Durability-before-publication is retained from BLOCK1. Failure after durable commit recovers its receipt/state rather than executing the command again. BLOCK4 A9 defines crash transitions: uncertain database commit enters RECOVERING until confirmed, never a blind retry/definitive abort.
- After commit, presentation problems produce delivery/degraded status and snapshot resynchronization. They never return TurnAborted for an already committed turn. Client slowness uses backpressure outside simulation.

### A1.4 Interface Declarations

The three Python fences in this document form one interface listing when concatenated in order. Forward annotations refer to declarations in A2/A3; no omitted implementations are implied.

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import Generic, Literal, NewType, Protocol, TypeAlias, TypeVar

EntityId = NewType("EntityId", str)
CommandId = NewType("CommandId", str)
EventId = NewType("EventId", str)
Tick = NewType("Tick", int)
WorldRevision = NewType("WorldRevision", int)

class Phase(IntEnum):
    VALIDATE = 0
    PRE_TICK = 1
    RESOLVE = 2
    REACT = 3
    CASCADE = 4
    POST_TICK = 5
    COMMIT = 6
    PRESENT = 7

@dataclass(frozen=True)
class TypeKey:
    kind: str
    version: int

class FrozenPayload(ABC):
    @property
    @abstractmethod
    def schema(self) -> TypeKey: ...

class CommandPayload(FrozenPayload, ABC):
    """Feature-owned, deeply immutable admitted command fields."""

@dataclass(frozen=True)
class GameCommand:
    command_id: CommandId
    actor_id: EntityId
    expected_revision: WorldRevision
    payload: CommandPayload

@dataclass(frozen=True)
class Failure:
    code: str
    message_key: str

@dataclass(frozen=True)
class TurnPlan:
    command: GameCommand
    start_tick: Tick
    target_tick: Tick

@dataclass(frozen=True)
class CommitReceipt:
    command_id: CommandId
    previous_revision: WorldRevision
    revision: WorldRevision
    tick: Tick
    core_hash: str

@dataclass(frozen=True)
class TurnRejected:
    failure: Failure
    current_revision: WorldRevision | None = None

@dataclass(frozen=True)
class TurnAborted:
    failure: Failure

@dataclass(frozen=True)
class TurnCommitted:
    receipt: CommitReceipt

TurnOutcome: TypeAlias = TurnRejected | TurnAborted | TurnCommitted

@dataclass(frozen=True)
class NodeKey:
    phase: Phase
    engine_id: str

@dataclass(frozen=True)
class CompiledSchedule:
    nodes: tuple[NodeKey, ...]
    fingerprint: str

class TurnDriver(Protocol):
    def compile(
        self,
        manifests: tuple[CapabilityManifest, ...],
        activations: tuple[NodeActivation, ...],
    ) -> CompiledSchedule: ...

    def submit(self, command: GameCommand) -> TurnOutcome: ...
```

Contracts: nonnegative tick/revision; successful turn advances revision exactly1; target_tick≥start_tick, admitted consuming actions advance game time per A7 policy. Rejections/aborts do not advance revision. TypeKey kind is namespaced English; schema version is positive. Structural NewType annotations alone do not validate ranges.

### A1.5 Choice / Acceptance

AR-009: TurnRejected.current_revision is the pinned committed revision for authenticated admission/stale failures; None means no authorized world revision is available, including malformed/unauthenticated input. Failure.message_key remains localized through the Korean catalog. Return current revision in typed results rather than embedding it in strings. Rejection carries no mutable owner/view handle; full error-code/class inventory is finalized in the next implementation order.

Chosen: serial phase barriers + boot-compiled stable DAG. Rejected: hand-maintained central call order (hidden dependencies), immediate same-phase mutation (order-sensitive reads), early parallel engines (scheduling/merge complexity on the actual laptop). Escape: parallelize only proven independent phase work while preserving barrier inputs and canonical output order.
Mapped: F-01/F-03/F-05/F-10; AP-02/AP-05/AP-06/AP-08/AP-09; C-03/C-04/C-05.

PLANNED verification: registry permutations yield identical schedule/hash; cycle/unknown/late dependencies fail boot; invalid command yields zero mutation; injected mid-turn failure leaves original state; post-commit delivery failure retains receipt; duplicate commit does not rerun.

## A2. Engine Plugin Contract

### A2.1 Manifest / Invocation / Access

One Engine Protocol; no separate interfaces for each gameplay engine. Required manifest fields remain `engine_id/phases/reads/writes/depends_on/emits/cost_class`; `consumes` explicitly declares event subscriptions.

| Field | Contract |
|---|---|
| engine_id | Unique stable namespaced English ID; no runtime generated identity |
| phases | Nonempty canonical subset PRE_TICK/RESOLVE/REACT/CASCADE/POST_TICK |
| reads/writes | Phase-scoped component/field families; schema-expanded at boot; no implicit access |
| depends_on | `(at phase, after node)`; node exists; same/earlier phase; no cycle |
| emits/consumes | Registered versioned fact kinds; no unknown/generic dict payload |
| cost_class | constant/local/regional/global; scheduling scope, not measured cost proof |

Field-family conflict is conservative: different runtime actor IDs do not make overlapping write declarations safe. Split ownership/phases or design one reducer engine. Entity-partition scheduling is not introduced now.

At invocation, ReadPort dispatches an approved typed ComponentKey to its feature-specific read-only Protocol backed by the recursive proxy. Component keys/read Protocols are declared with the state schema in A5. Arbitrary mutable models cannot be registered. No raw WorldState/object/Any escape hatch.
Proxy records concrete `(component, entity, field)` reads; collection enumeration observes membership/order fields as well. Proposed delta targets record writes. Observation is attributed to engine/phase/wave, including aborted candidates for diagnostics. Staging-owned work is distinct from engine access.
Undeclared read/write, unregistered type, malformed payload/delta, wrong producer/phase, duplicate target, or invalid invariant is a pre-COMMIT contract failure. Unused declarations/unconsumed fields/zero-hit methods are report categories, not interchangeable with undeclared access.
Runtime guard enforces safety; the planned Phase1 manifest thin checker aggregates declared/observed evidence. No additional custom checker.

### A2.2 Interface Declarations

```python
ReadT = TypeVar("ReadT")
CostClass: TypeAlias = Literal["constant", "local", "regional", "global"]

@dataclass(frozen=True)
class FieldFamily:
    component: str
    field: str

@dataclass(frozen=True)
class PhaseAccess:
    phase: Phase
    family: FieldFamily

@dataclass(frozen=True)
class Dependency:
    at: Phase
    after: NodeKey

@dataclass(frozen=True)
class CapabilityManifest:
    engine_id: str
    phases: tuple[Phase, ...]
    reads: tuple[PhaseAccess, ...]
    writes: tuple[PhaseAccess, ...]
    depends_on: tuple[Dependency, ...]
    emits: tuple[TypeKey, ...]
    consumes: tuple[TypeKey, ...]
    cost_class: CostClass

@dataclass(frozen=True)
class ComponentKey(Generic[ReadT]):
    schema: TypeKey

class ReadPort(Protocol):
    def component(
        self, key: ComponentKey[ReadT], entity_id: EntityId
    ) -> ReadT: ...

class RandomStream(Protocol):
    def draw_bounded(self, low: int, high_exclusive: int) -> int: ...

class EngineRng(Protocol):
    def stream(
        self, entity_id: EntityId, purpose: str, causal_key: str
    ) -> RandomStream: ...

@dataclass(frozen=True)
class AdmittedAction:
    actor_id: EntityId
    payload: CommandPayload
    semantic_key: str

@dataclass(frozen=True)
class Degradation:
    producer_id: str
    code: str

@dataclass(frozen=True)
class FieldAddress:
    family: FieldFamily
    entity_id: EntityId

class StateDelta(FrozenPayload, ABC):
    @property
    @abstractmethod
    def target(self) -> FieldAddress: ...

@dataclass(frozen=True)
class EngineInvocation:
    action: AdmittedAction | None
    logical_tick: Tick
    phase: Phase
    wave: int
    state: ReadPort
    definitions: DefinitionReadPort
    rng: EngineRng
    incoming: tuple[WorldEvent, ...]

@dataclass(frozen=True)
class EngineResult:
    deltas: tuple[StateDelta, ...]
    facts: tuple[EmittedFact, ...]
    degraded: tuple[Degradation, ...]

class Engine(Protocol):
    @property
    def manifest(self) -> CapabilityManifest: ...

    def evaluate(self, invocation: EngineInvocation) -> EngineResult: ...

@dataclass(frozen=True)
class EngineBinding:
    engine: Engine
    module_path: str
    activations: tuple[NodeActivation, ...]
```

Frozen dataclasses are not deep-immutability proof. Registered concrete command/fact/delta/presentation payloads MUST be frozen dataclasses with schema-approved immutable children. Scalar integers/bools/strings and immutable typed records/tuples are accepted; no nested dict/list/set, floats in CORE, raw services/state handles, or lazy I/O. Presentation-only floats may be schema-approved but cannot feed domain branching. Runtime/schema validation and proxy contracts finalize in A5/A10. ReadPort returns only registered read Protocols; TypeVar alone cannot enforce that restriction.

Concrete delta classes carry feature-specific expected-old/new values and units; their typed validators/reducers own that behavior. Do not add generic `value: object` or central union members. Reducers receive only staging edit capability; authoritative application belongs to COMMIT. BLOCK3 A5 specifies reducer interfaces; concrete payload schemas/codecs remain A10 prerequisites, not completed implementation.

### A2.3 Registration / Errors / Extension Cost

App-layer `feature_registry.py` explicitly lists immutable feature bundles. A bundle composes EngineBinding, feature-owned typed schemas/codecs/delta reducers, command admission routes, and presentation adapters. Bootstrap distributes these to orchestration/adapters; engine modules never import the app/adapters or other engines.
Registry builder rejects duplicate IDs/type-key collisions and unsupported versions. Shared event schemas may have multiple declared producers/consumers, but conflicting definitions under the same kind/version fail. Registry is frozen before play.
Engine instances retain no turn-dependent authority, read view, RNG cursor, or partial result between invocations. Immutable lookup tables are allowed. BLOCK5 defines activation metadata and the observed, prefetched definition view; adapters perform catalog I/O outside engine calls. Injected derived caches are bounded/session-isolated and cannot affect CORE results; replay contamination verifies this later.

**Adding one capability:** NEW feature contracts/engine/adapter/tests; MODIFY exactly1 existing production file (registry TARGET). A unit-only engine is not live completion. No central DTO/type union/presenter switch/import list elsewhere should expand. New CORE component schema or public compatibility changes are separate explicit tasks, not hidden in this marginal-cost claim.

Engine boundary distinguishes:
- Rule outcome: typed facts/deltas, including meaningful failure/cost; normal commit.
- Allowed optional fallback: explicit result + degradation, no invented authoritative fact.
- Contract violation/unexpected exception: bounded diagnostic + TurnAborted before COMMIT; preserve error chain. Missing feature implementation raises reasoned NotImplementedError with task ID, never empty success.

Chosen: explicit registration + feature-local typed payload subclasses. Rejected: decorator/import discovery (hidden startup), generic dict/object payloads (type escape), central growing union (cross-feature edits). Escape: replace registry loader without changing Engine/manifest/read/result contracts. Domain tests are state-in/result-out; adapter mocks only.
Mapped: F-02/F-03/F-04/F-07/F-09/F-10; AP-01/AP-02/AP-03/AP-04/AP-05/AP-08/AP-09/AP-10/AP-11; C-04.
PLANNED verification: nested mutations fail, all concrete reads/writes match phase declarations, duplicate schema/engine boot failure, live registration/consumer evidence, new-engine edit-count review. Mutation/coverage are later-stage evidence, not current results.

## A3. Simulation → Presentation

### A3.1 Fact / Diff / Cue Separation

Facts describe simulated outcomes; deltas describe proposed changes; StateDiff describes committed field changes; presentation cues describe display only. No per-turn LLM assembly.

| Unit | Owner / contract |
|---|---|
| EmittedFact | Engine-produced typed immutable fact draft; explicit due tick/causal references |
| WorldEvent | Orchestrator-assigned stable ID/kind/version/producer/tick/causation/degraded + FactPayload; delayed events persist through A4/A9 |
| StateDelta | Feature-owned typed proposal/expected values; no mutation capability |
| EngineResult | Fixed envelope of deltas/facts/degradation; no capability-specific optional fields |
| StateDiff | COMMIT-produced canonical typed changes with matching receipt/base/new revision |
| PresentationEvent | Adapter-produced typed visual/audio/UI cue; source fact links; non-authoritative |
| GeneratedContentRef | Already validated/accepted package ID/version/hash/entry; no live generation request |

Fact schema kinds are namespaced/versioned. Metadata must match concrete payload schema. Scheduler assigns producer/IDs; engines cannot forge another producer. Emission sequence is tuple order under stable node order, not set/hash order. Canonical producer_rank is the node's index in the compiled lane-A subsequence, not lexical producer order or its index among A+B nodes (AR-004). B emits no simulation facts; adding B nodes cannot renumber A producers. A nodes cannot depend on B nodes. Causal references identify validated prior/delivered IDs; unknown/future references fail. Root facts use an empty tuple; command provenance is recorded separately from autonomous simulation state.
BLOCK3 event IDs use persistent world identity + logical emission tick + phase/wave + producer + sequence. Session/commit revision is excluded to preserve catch-up composition. IDs use versioned canonical encoding, no UUID4/wall time.
Immediate facts target the current logical tick and a permitted later phase/wave. Future ticks enter the delayed queue, never consumed early; BLOCK3 defines routing/retiming. Before commit these are candidates only. Rejections/aborts publish no authoritative facts.
Committed diff includes one canonical change per target with before/after semantics supplied by its typed delta. If a field changes across multiple phases, reduce to base→final; retain ordered causality facts separately. Do not make client replay tentative staging operations.

### A3.2 Interface Declarations

```python
class FactPayload(FrozenPayload, ABC):
    """Feature-owned simulation facts, not display instructions."""

class PresentationPayload(FrozenPayload, ABC):
    """Feature-owned display data, never authoritative edits."""

@dataclass(frozen=True)
class EmittedFact:
    payload: FactPayload
    due_tick: Tick
    caused_by: tuple[EventId, ...]

@dataclass(frozen=True)
class EventHeader:
    event_id: EventId
    type_key: TypeKey
    producer_id: str
    occurred_at: Tick
    phase: Phase
    wave: int
    producer_rank: int
    sequence: int
    caused_by: tuple[EventId, ...]
    degraded: tuple[Degradation, ...]

@dataclass(frozen=True)
class WorldEvent:
    header: EventHeader
    due_tick: Tick
    payload: FactPayload

@dataclass(frozen=True)
class StateDiff:
    receipt: CommitReceipt
    changes: tuple[StateDelta, ...]

CuePriority: TypeAlias = Literal["essential", "important", "ambient"]
CoalescePolicy: TypeAlias = Literal["keep_all", "replace_latest"]

@dataclass(frozen=True)
class PresentationEvent:
    header: EventHeader
    payload: PresentationPayload
    priority: CuePriority
    coalesce_policy: CoalescePolicy
    coalesce_key: str

@dataclass(frozen=True)
class GeneratedContentRef:
    package_id: str
    version: int
    package_hash: str
    entry_id: str

@dataclass(frozen=True)
class PresentationBatch:
    diff: StateDiff
    events: tuple[PresentationEvent, ...]
    degraded: tuple[Degradation, ...]

class Presenter(Protocol):
    def map(
        self,
        facts: tuple[WorldEvent, ...],
        receipt: CommitReceipt,
        committed: ReadPort,
    ) -> tuple[PresentationEvent, ...]: ...
```

WorldEvent producer is the engine/scheduler source. PresentationEvent producer is the presenter; caused_by retains source fact IDs. Batch receipt identifies the world revision for all its cues. Presenters receive a stable committed version/read view, never a mutable live state or arbitrary future revision.
GeneratedContentRef resolves only against the accepted package catalog; missing/hash-mismatched references fail content validation. Do not turn missing content into a live gameplay LLM call. Production/runtime acceptance belongs to A14.

### A3.3 Ordering / Coalescing / Backpressure

1. Preserve authoritative fact order `(occurred_at, phase, wave, producer_rank, sequence)` from A1, including topological order rather than re-sorting producers by name; scheduled due-order is finalized A4.
2. Run matching registered presenters in stable presenter-ID order. Cue ID derives from source IDs/presenter ID/local index. Preserve causal order; essential/UI and importance scheduling cannot invent gameplay ordering.
3. Coalesce only explicitly replaceable same-kind/version/target/key cues within one batch; retain the last display update. Empty key means no coalescing. Combat/action/causal narration cues default keep_all. No rewriting CORE facts/diffs or cross-turn fact deletion.
4. Initial visual queue TARGET≤256 cues per batch after coalescing. If exceeded, discard oldest ambient cues first, then explicitly discardable important cues; record degradation/drop counts. Essential overflow requires resync/backpressure, never silent loss. Cue payload schema declares discardability; importance alone does not permit dropping it.
5. StateDiff/receipt delivery is reliable and never truncated for display budgets. Large updates use bounded framing/segmentation under A12; partial segments are not applied. On revision gap/missing essential data, request a committed snapshot.
6. Unknown cosmetic cue/version: explicit fallback + degradation. Unknown required state contract: stop applying updates and resync/compatibility error; never interpret generic payload heuristically.
7. Animation/VFX/audio may be skipped while authoritative UI applies the committed diff. Client cannot derive HP/resource/quest truth from missing cue counts or animation timing.

Player error/UI text uses Korean message catalogs; internal message keys/schema IDs remain English. Generated prose is optional accepted content, not a source of authoritative math. No token/LLM-based truncation or narration is needed.

Chosen: typed fact/diff envelopes + registered feature-local presenters. Rejected: central optional result DTO, universal string/dict payload, direct engine UI calls, mandatory LLM narration. Escape: replace client/presentation adapter behind stable receipts/diffs/facts.
Mapped: F-02/F-05/F-06/F-07/F-10; AP-01/AP-02/AP-06/AP-08/AP-09; C-02/C-04/C-05.

## Contract Examples / PLANNED Acceptance

Examples are new synthetic contract fixtures, not combat formulas/balance and not copied v1 expectations.

| Case | Input / setup | Expected outcome |
|---|---|---|
| Admission rejection | Actor missing, base HP42/tick10/revision3 | TurnRejected; HP42/tick10/revision3; no facts/RNG draws |
| Barrier staging | Base revision3/tick10; admitted target tick11; PRE_TICK dummy proposes HP42→40; RESOLVE reads40, proposes40→35 | Before COMMIT original42; after HP35/tick11/revision4; one base42→35 diff; ordered two facts |
| Same-phase view | Two RESOLVE engines read HP42; only one declares HP write | Both read42 regardless registry order; permitted writer applied at barrier |
| Boot writer conflict | Two RESOLVE manifests write actors.hp, even for different expected actor IDs | Boot failure with phase/engine IDs/field family; neither runs |
| Boot dependency cycle | Same-phase A after B, B after A | Boot failure; no runtime fallback ordering |
| Missing declaration | Proxy observes hp but manifest declares stamina only | Contract failure before COMMIT; no mutation |
| Duplicate field proposal | One barrier returns two deltas for same concrete hp address | TurnAborted; no last-writer-wins |
| Aborted cascade | Nonempty wave8 would follow waves0..7 | CASCADE_LIMIT; entire candidate discarded; no dropped CORE event |
| Committed retry | Same command ID/content, recorded receipt revision4 | Return same receipt; no second tick/damage/facts |
| Presentation failure | Commit succeeds, presenter/client fails | Keep revision4/hash/receipt; explicit degraded/resync; no replayed commit |
| Queue reduction | 300 cues,256 essential,44 discardable ambient | Keep256 essential; drop44 ambient with count; unchanged diff/hash |
| Essential overflow | 257 essential cues | Explicit resync/backpressure; no silent authoritative truncation |
| Schema extension | New typed engine/fact/presenter feature | Add new files +1 existing registry TARGET; central contracts unchanged |

Verification responsibilities (PLANNED): schedule permutation/cycle/write conflict; nested proxy reads; phase/wave visibility; invalid/abort atomicity; idempotency; stable event/cue ordering; degradation propagation; queue/resync; end-to-end headless command→commit→presentation trace. Runtime/mypy/pytest/replay/performance execution: NOT_RUN. Document interface syntax checks do not prove these properties.

## Completion / Next

A1–A3 now specify interfaces, invariants, rejected alternatives, mappings, and future verification. Python/schema/version/tool compatibility and cross-block open contracts remain UNVERIFIED. Standard tools/custom-checker count unchanged: planned2/max3/current0; Phase0 remains exactly4. No new governance tool or v1 migration.
Update [BACKLOG](../BACKLOG.md)/[SESSION_HANDOFF](../SESSION_HANDOFF.md) with actual document verification only. Next: **RS-ARCH-002-B03 / BLOCK3 A4 events, A5 state/proxy, A6 determinism/replay**. Stop after this block.

--- BLOCK 2/9 END. Enter "continue" for the next block. ---
