# BLOCK 3 — Events, State & Deterministic Replay

Date: 2026-10-03 | Task: RS-ARCH-002-B03 | Owner: GPT-6.1 Sol | Mode: DESIGN
Inputs: [BLOCK1](BLOCK_01.md), [BLOCK2](BLOCK_02.md), prompt A4–A6/C-03/C-04. Format: compact English.
Status: proposed contracts/interfaces; no production code/tests/services. Python fences continue BLOCK2's shared declaration listing. Runtime/type/property/performance evidence remains UNVERIFIED.

## Resolved Cross-block Decisions

| Previous OPEN contract | Resolution |
|---|---|
| Long time advance | Repeat the compiled logical-tick program; admit/COMMIT once; action only at its admitted action tick |
| Engine input | Admitted action or None + logical tick; no command receipt/revision/session/outer catch-up interval |
| RNG | One service, engine/tick-scoped stream factory; stable semantic addresses, not invocation order |
| Event identity | Persistent world ID + logical emission position; no session/commit revision |
| State publication | Sparse staged component versions; one owner-head swap after validation/durability |
| Replay hash | All CORE A/B state and semantic pending events; DERIVED/transport metadata excluded |

These resolve composition hazards in BLOCK2's provisional plan/RNG/event declarations; its interfaces are updated in this task. No deployed compatibility change exists yet. A7/A9/A10/A11/A12/A13 still own full commands/save/import/LOD/wire/budget details.

## A4. Event Bus / Delayed Causality

### A4.1 Tick Program / Routing

VALIDATE creates an outer TurnPlan. For each logical tick in `(start_tick, target_tick]`, orchestration runs the compiled PRE_TICK→RESOLVE→REACT→CASCADE→POST_TICK program over the staged state. RESOLVE gets AdmittedAction only at its admitted action tick; other substeps get None. PRE_TICK exposes due changes before that tick's action. POST_TICK advances staged clock once. COMMIT/revision/PRESENT occur once after all substeps.

Passive catch-up uses the same tick program with no action. NPC ecology, off-screen intents/spawns and quest deadlines use this same event bus, not a second simulation loop. Component last-update/due cursors belong to CORE, not hidden process caches. Start/target bounds and transport revision stay in orchestration; engines see logical_tick only. This prevents interval segmentation from changing autonomous results.
Initially execute canonical ticks without approximate shortcuts. A11 may skip intervals only when an exact transition proof preserves all Tier A state/queues/remainders; wall time, camera FPS, or elapsed interval length cannot select different Tier A rules.

| Event stage | Contract |
|---|---|
| Draft | Engine returns typed EmittedFact; scheduler validates schema/producer/causes/due tick |
| Envelope | Scheduler assigns EventHeader/ID; immutable WorldEvent |
| Immediate | Deliver at current tick's declared later phase or next CASCADE wave |
| Delayed | Queue until due_tick/delivery_phase; never execute early |
| Consumed | All matching subscribers run once at a barrier; remove only in staging |
| Commit | Publish queue removals/additions and component outcomes together |
| Abort/crash before commit | Original queue/state survive; no consumed marker or partial consequence escapes |

EventPolicy registry pins kind/version, simulation vs record-only mode, delivery phase, priority, authorized producers/subscribers/cancellers, and late-route policy. Priority is integer0..255; simulation phases are PRE_TICK..POST_TICK; record-only delivery is PRESENT. All gameplay subscriptions are explicit; an emitted simulation kind without a valid consumer fails boot. Record-only facts may have no simulation reader; they still have explicit presentation/audit ownership and must be due now.

For simulation drafts, due_tick<logical_tick is invalid. due_tick=current tick routes to a later declared phase/wave. If that phase has passed, reject unless the kind explicitly permits next_tick; then retime to tick+1 and report the deferral. No silent retiming. Future drafts enter CORE queue. Same-CASCADE emissions enter wave+1; no engine recursively invokes another engine.

Canonical queue order:
`(due_tick, delivery_phase, priority, occurred_at, emission_phase, emission_wave, producer_rank, sequence, event_id)`.
Smaller registered priority runs first within the same delivery phase. producer_rank is the compiled node rank, not registry insertion/hash order. Subscriber batches preserve this order; an engine is called once per phase/wave with its complete matching batch. Same-phase writes retain BLOCK2 barriers.

### A4.2 Identity / Cycles / Cancellation

- Persistent world_id is frozen at world creation; session tokens/ports/transport command IDs are never event identity inputs.
- `event_id = "e1-" + SHA256(pack("event-id/v1", world_id, logical_tick, phase, wave, producer_id, sequence))`. pack is A6's versioned length-prefixed encoding. Sequence starts0 per producer/phase/wave/tick; enumeration uses canonical tuple order. Delayed delivery preserves the original ID/header.
- Causes reference delivered inputs/current candidate facts. Root autonomous facts have no parent; action provenance is recorded in replay outside passive simulation state. Emitted references to unknown/future IDs fail. Stored pending events retain previously validated cause IDs without requiring an unbounded historical fact ledger.
- Duplicate IDs/duplicate handler delivery in a candidate fail contract validation. Transaction-local delivery cursors are bounded and discarded on abort; no module-global seen set.
- TARGET: CASCADE≤8 waves and produced simulation events≤512 per logical tick, independently of outer turn segmentation. Next wave/limit overflow aborts the whole candidate; no CORE event trimming. Pending queue initial TARGET≤4096 records; overflow is explicit EVENT_QUEUE_LIMIT before commit. These limits are versioned rules, not measured capacity.
- Infinite same-tick feedback reaches the deterministic bound and aborts. Future recurrence requires explicit due tick/expiry policy; limits prevent unbounded fan-out. Legitimate autonomous periodic jobs are not arbitrarily disabled by a cycle heuristic.
- Cancellation is a typed system control fact with event ID, reason, authorized producer. Reserved queue owner stages removal. Already delivered/missing target yields explicit no-op outcome; no retroactive reversal. Renderers cannot cancel events. Full control payload schemas/imports are A10; no generic dict command.

System clock/queue writers are reserved registered owners; their field rights are explicit in schema/boot checks. Game engines may emit events, not directly edit clock/queue internals. System operations and gameplay access have separate attribution. Commit requires no stranded current/past-due simulation event; explicit next_tick routing is the only permitted deferral.

Long preparation may exceed normal-turn budgets only as a visible bounded job with the same semantics and one final commit. Total job ceilings/yield policy are A11/A13 prerequisites; intermediate progress is DERIVED, not authoritative state. No long-job READY order until those contracts exist.

### A4.3 Interface Declarations

AR-003: wave=0 outside CASCADE. Within CASCADE, due/current incoming facts form wave0; up to eight nonempty waves numbered0..7 may execute. Empty inbox ends the cascade and consumes no wave/call. Emission requiring nonempty wave8 raises CASCADE_LIMIT and aborts the entire candidate. Each engine runs at most once in a wave with its full batch; waves never reset tick counters. This numbering refines the earlier informal depth/wave9 examples without changing the eight-wave ceiling.

Boot routing validation resolves every EventPolicy.subscriber to an existing (delivery_phase,engine_id) node with the kind in consumes and on_matching_events=True. Every declared simulated subscription must have a compatible policy; an emit with no runnable subscriber is rejected even if an engine with that ID exists elsewhere. Record-only/PRESENT kinds have registered presenter/audit ownership instead of a simulation node. Policy producers must have matching emitted kinds/phases and lane-A rights; unknown/duplicate delivery owners cannot silently strand a due event. Queue removals are staged only after all subscribers complete their matching batch.

```python
EventMode: TypeAlias = Literal["simulate", "record_only"]
LateRoute: TypeAlias = Literal["reject", "next_tick"]

@dataclass(frozen=True)
class EventPolicy:
    schema: TypeKey
    mode: EventMode
    delivery_phase: Phase
    priority: int
    late_route: LateRoute
    producers: tuple[str, ...]
    subscribers: tuple[str, ...]
    cancellers: tuple[str, ...]

@dataclass(frozen=True)
class QueuedEvent:
    event: WorldEvent
    delivery_phase: Phase
    priority: int

@dataclass(frozen=True)
class QueueChange:
    added: tuple[QueuedEvent, ...]
    removed: tuple[EventId, ...]

@dataclass(frozen=True)
class DeliveryBatch:
    logical_tick: Tick
    phase: Phase
    wave: int
    events: tuple[WorldEvent, ...]

@dataclass(frozen=True)
class RoutedFacts:
    immediate: tuple[DeliveryBatch, ...]
    pending: tuple[QueuedEvent, ...]
    record_only: tuple[WorldEvent, ...]

class EventBus(Protocol):
    def due(
        self, pending: tuple[QueuedEvent, ...], tick: Tick, phase: Phase
    ) -> DeliveryBatch: ...

    def route(
        self,
        invocation: EngineInvocation,
        producer_id: str,
        facts: tuple[EmittedFact, ...],
    ) -> RoutedFacts: ...
```

EventBus is an orchestration service, not a second state owner. due/route operate on candidate data and cannot mutate committed queue. due supplies scheduled wave0; route groups current-tick inboxes by delivery phase/wave and future events into pending. Inbox barriers merge batches in canonical event order before one subscriber invocation. RoutedFacts separates these from record-only presentation facts; record-only items are never persisted as pending simulation. QueueChange is validated by the reserved owner alongside engine deltas. Event policies cannot silently change under an existing version/fingerprint.
Chosen: typed queues + phase/wave barriers. Rejected: direct engine calls, recursive callback buses, dropped overflow, reconstructing future events from prose. Escape: change internal queue index while preserving canonical ordering/IDs/schema.
Mapped: F-01/F-03/F-05/F-10; AP-02/AP-05/AP-06/AP-08; C-03/C-04/C-05.

## A5. Component State / Recursive Read-only Views

### A5.1 Ownership / Schema

Choose component-oriented state with a six-level location graph; no general-purpose ECS runtime and no giant NPC/world dataclass. StateDelta commit is authoritative; fact/replay logs provide evidence, not an event-sourcing requirement to rebuild every state from full history.

| Component family | Responsibility / CORE A examples |
|---|---|
| identity/profile | Entity ID, traits, visual/content references that gameplay uses |
| physiology/equipment | HP/stamina/injury, food/sleep/temperature, inventory/weight |
| cognition/memory | Traits/attitude/persona, goals/intents, memories/permanent anchors |
| social/economy | Relationships/factions/resources/trade; no duplicated owner fields |
| quest/consequence | Quest state/deadlines and causal references |
| location/world | L0 cosmology→L1 continent→L2 region→L3 nation→L4 settlement→L5 facility; parent/child/network facts |
| system clock/events | Logical tick/update cursors and semantic pending queue |

These are responsibility groups, not approved concrete gameplay schemas or engine-file counts. A5 establishes schema mechanics; detailed numerical rules remain future bounded design tasks. Traits/12-axis/10-factor/20-factor/BDI/5-level memories/anchors remain MASTER capability requirements.

Every registered leaf field declares storage_class, tier, owner_id, field type, unit, scale, bounds/cap, consumers. Validate matrices: CORE→A or B; DERIVED→C. No unclassified/ambiguous field. CORE A includes update cursors, integer fractional remainders, pending causal state and deterministic spawn counters—not just visible values.
CORE B permits declared divergence between different LOD configurations but same replay/config still reproduces it exactly. Approximate B values cannot decide strict A outcomes; deterministic A rules decide authoritative promotion. A11 specifies feature-specific B bounds before implementation.
DERIVED includes rendering/index/cache/debug/progress and is stored separately from the sealed CORE root. Deleting/rebuilding it must preserve complete CORE hash. CORE engines cannot declare DERIVED reads; derived adapters may read CORE. Raw transport revision/receipt ledger belongs to owner protocol metadata, is verified separately, and never enters engine inputs or CORE hash. Recover revision from A9 commit records; it is not autonomous simulation time.

Location graph stores typed IDs, level, parent and canonical child/route sets. Enforce legal adjacent levels/acyclic parents and referential integrity. Do not duplicate full ancestors into every component; indexes are DERIVED. gameplay effects use events/deltas, not recursive mutable hierarchy objects.

### A5.2 Staging / Single Publication

WorldState is a mutable owner facade, not a frozen transport DTO. Its private head contains a sealed CORE root plus protocol revision. Engines only receive ReadPort; no head/root/raw component handle. Owner components may use `traits: list[str]`; read views expose read-only sequences and transport snapshots use tuples.

For Phase1 scale, choose a fixed256-bucket copy-on-write component index using a stable SHA256 address prefix. Each bucket mapping is protected by MappingProxyType; raw backing dictionaries never escape. Stage copies only touched buckets/components/changed mutable paths. Root tuple/page structure is immutable; published component versions are sealed by owner capability and never edited in place. This is shallow structural sharing, not full WorldState deep-copy. Phase0 uses only the tiny skeleton's typed in-memory root; no separate index/schema tooling implementation is added to its four items.
Schema-owned typed delta reducers check expected-old values against phase-start view, validate field rights/units/ranges and construct new component versions. No generic `object`/Any value setter. Multiple phase writes compose into one base→final StateDiff per concrete target; facts retain intermediate causes. Reducers operate on staging capability, never WorldState.

COMMIT sequence: validate candidate entirely → create new sealed owner head/diff → durable A9 transaction when enabled → one head-reference publication. No per-field mutation of the published root during publication. Fail before durability leaves old head untouched; fail after durability halts/reloads recorded commit instead of rerunning action. Phase0 uses the same ownership rule without save implementation.
256 buckets are a representation choice, not world-size limit. Field ownership and semantic hash are independent of bucket layout. Measure transient copies/index/hashing on the real laptop; representation fit UNVERIFIED.

### A5.3 Proxy / Observation / Cache

| Value | Engine view / required behavior |
|---|---|
| Scalar | Typed immutable value; observe declared leaf read |
| Component/child record | Registered read Protocol backed by recursive wrapper; property reads observed |
| Mapping | Observed read-only wrapper over MappingProxyType; keys stable; values recursively wrapped |
| Sequence | Read-only indexing/iteration/slicing; children recursively wrapped; semantic order retained |
| Set | Canonical sorted immutable view; never expose hash iteration |
| Unknown class/callable/descriptor/raw handle | Reject unsupported read type; no accidental lazy I/O |

Mutation through aliases, setattr/setitem/del/append/update/clear and nested children fails immediately with ReadOnlyViolation. No unwrap/raw/asdict escape returning mutable state. Support only registered pure field adapters; do not execute arbitrary object descriptors.
Cache by view epoch + component address + nested path; epoch includes engine/phase/wave/tick and pinned staged root. Scope cache to invocation; invalidate at barrier; retained old views raise ExpiredReadView. Reusing wrappers cannot lose access attribution or grow across the whole campaign.
Observe concrete read paths and collection membership/order/length. Compare declared/observed reads with proposed writes and reserved owner operations. Report undeclared read, unused declaration, unconsumed field, zero-hit public engine method separately. Coverage complements proxy evidence; AST cannot prove all readers.

Proxy TARGET: total turn CPU overhead≤10% with recorder enabled; new-wrapper target from BLOCK1. Benchmark identical device/build/rules/seed/trace against a validation baseline, warmup/repeats/peaks included. DEV laptop and concrete MIN-SPEC are separate runs. Fail→optimize adapter/cache, remeasure; release keeps proxy on by default. No unsupported disablement. Current measurement UNVERIFIED.

### A5.4 Interface Declarations

```python
from collections.abc import Mapping, Sequence

StorageClass: TypeAlias = Literal["CORE", "DERIVED"]
DeterminismTier: TypeAlias = Literal["A", "B", "C"]

@dataclass(frozen=True)
class ComponentAddress:
    schema: TypeKey
    entity_id: EntityId

@dataclass(frozen=True)
class FieldSpec:
    family: FieldFamily
    storage_class: StorageClass
    tier: DeterminismTier
    owner_id: str
    consumers: tuple[str, ...]
    value_kind: str
    unit: str
    scale: int
    minimum: int | None
    maximum: int | None
    collection_cap: int | None

class EntityProfileRead(Protocol):
    @property
    def entity_id(self) -> EntityId: ...

    @property
    def traits(self) -> Sequence[str]: ...

class PhysiologyRead(Protocol):
    @property
    def hp(self) -> int: ...

    @property
    def reserves(self) -> Mapping[str, int]: ...

@dataclass(frozen=True)
class ViewEpoch:
    logical_tick: Tick
    phase: Phase
    wave: int
    engine_id: str
    root_token: int

@dataclass(frozen=True)
class AttributePath:
    name: str

@dataclass(frozen=True)
class MappingPath:
    key: str

@dataclass(frozen=True)
class SequencePath:
    index: int

AccessPathSegment: TypeAlias = AttributePath | MappingPath | SequencePath

@dataclass(frozen=True)
class AccessObservation:
    epoch: ViewEpoch
    target: FieldAddress
    path: tuple[AccessPathSegment, ...]
    operation: Literal["read", "membership", "length", "iteration", "write"]

class ComponentPatch(FrozenPayload, ABC):
    """Schema-owned immutable proposed field values; no raw dict setter."""

class StagingEditor(Protocol):
    def apply_patch(
        self, address: ComponentAddress, patch: ComponentPatch
    ) -> None: ...

DeltaT = TypeVar("DeltaT", bound=StateDelta)

class DeltaReducer(Protocol[DeltaT]):
    def stage(
        self, delta: DeltaT, before: ReadPort, editor: StagingEditor
    ) -> None: ...

    def compose(self, changes: tuple[DeltaT, ...]) -> DeltaT: ...

class ReadViewFactory(Protocol):
    def open(self, epoch: ViewEpoch) -> ReadPort: ...

    def close(self, epoch: ViewEpoch) -> tuple[AccessObservation, ...]: ...
```

FieldSpec value_kind resolves to registered typed schema; string is a schema key, not untyped runtime value. scale is positive; irrelevant bounds/caps are explicit None. root_token identifies an ephemeral wrapper cache only; never RNG/hash/event identity. Stage capabilities are issued only to trusted reducers with declared rights; engines cannot request them. Concrete owner/index/core-root shapes depend on approved gameplay schemas; no giant union introduced here.

AR-002: AccessObservation.path is relative to target.family.field; empty tuple identifies the field/container itself. MappingPath('food') and SequencePath(0) are distinct; indices are normalized nonnegative integers, never bool. AttributePath names come only from registered child adapters. Views over mappings with non-string keys need a separately approved typed key codec, not str/repr coercion. These structural path types live with read-view contracts; a feature never expands their union.
Observation order is actual operation order, including repetitions/cache hits, with no deduplication. A scalar property emits one read; acquiring a container emits one read at its container path; getitem emits one read at the normalized child path, including failed missing-key/index reads. len and membership each emit one operation at the container/queried-child path respectively. Creating an iterator emits one iteration at its container path; each yielded value emits one child read; keys are canonical and sequences retain semantic order. Explicit length hints are additional length operations, never hidden or suppressed. Slice validates bounds and emits one iteration plus reads of included child paths; returned view retains the epoch. Manifest checks authorize the schema leaf family; nested paths preserve evidence and never grant extra rights.
Denied setattr/setitem/delete/mutator lookup emits one write at the attempted target/path and raises ReadOnlyViolation before backing mutation. Stale access raises ExpiredReadView without recording a successful access. Missing component/entity raises UnknownComponent/UnknownEntity. Invalid epoch is InvalidViewEpoch; duplicate open is ViewAlreadyOpen; closing a never-opened epoch is InvalidViewEpoch; closing twice is ViewAlreadyClosed. A closed epoch cannot reopen. Factory ownership/root pin mismatch fails before access. close expires all aliases and returns the immutable ordered observations; the driver closes every opened epoch in finally. Negative/out-of-range indices and unknown fields remain explicit errors; no silent clamp/descriptor call. Concrete typed backing adapter registrations remain source-specific order inputs.
Chosen: component delta-commit + sparse COW + hierarchical IDs. Rejected: full ECS framework before play evidence, mutable nested world graph, full deep-copy, full-history event sourcing. Escape: replace index/storage behind schema/read/delta contracts without changing simulation semantics/hash version.
Mapped: F-02/F-03/F-04/F-07/F-10; AP-01/AP-04/AP-05/AP-08/AP-09; C-01/C-03/C-04/C-05.

## A6. RNG / Canonical Hash / Replay

### A6.1 One RNG Service

World seed: fixed32bytes, stored as64lowercase hex. Seed creation is outside replay; accepted seed is frozen before world generation. world_id is `"w1-" + SHA256(pack("world-id/v1", seed_hex, initial_rules_fingerprint, initial_gameplay_catalog_hash))`; catalog hash uses sorted package pins. Persist it once; later packages/session restart never redefine it.
Version `sha256-counter-v1`. EngineRng is a scoped adapter over one injected RngService, fixed to engine_id/logical_tick/phase/wave. A stream address also contains entity_id, registered purpose, and stable causal key. No caller interval/commit revision/thread/order/wall time/hash() input.
Autonomous purpose uses logical tick/entity/cause; action purpose uses admitted semantic_key or source event ID. semantic_key is `"a1-" + SHA256(pack("action-key/v1", world_id, execution_tick, actor_id, canonical_payload_hash))`; no command ID/expected revision/session token. Reopening the same address in one invocation returns the same cursor; independent entity/purpose addresses cannot consume each other's draws. Cursors are invocation-local DERIVED, discarded on abort; retry rebuilds identical streams.

Binary pack v1: tuple of UTF-8 string tokens; each token is `u32_big_endian byte_length || bytes`; reject token lengths above2^32−1. Integer tokens use canonical base10, no plus/leading zeros; Phase tokens use their exact uppercase enum name. IDs/kinds/purposes are validated English namespaces; gameplay text is accepted NFC UTF-8. No delimiter ambiguity or Python hash.
`K = SHA256(pack("rng-key/v1", seed_hex, world_id, tick, phase, wave, engine_id, entity_id, purpose, causal_key))`.
Counter c starts0. `u = big_endian_uint64(SHA256(K || uint64_big_endian(c))[0:8])`; increment c for every attempted draw.
draw_bounded(low,high): require integer bounds, `0 < n=high-low <= 2^64`; `limit=2^64-(2^64 % n)`; discard u≥limit; return `low+(u % n)`. Count rejections; deterministic exhaustion at counter2^64 fails candidate. No platform-dependent random/randrange behavior.
Purpose names/draw semantics are versioned rules; changing them is behavior change. Independent A6 reference vectors from this specification must be established during implementation, not copied from implementation output.

### A6.2 All Nondeterminism Controls

| Source | Rule |
|---|---|
| Sets/maps/files | Sort stable IDs/keys before semantic iteration; preserve explicit tuple sequence; file discovery/build inputs sorted |
| Float | CORE stores fixed-point integers with schema unit/scale; quantize before thresholds/branches/sort keys; comparison never uses raw float |
| Quantization | At approved I/O boundary use decimal text/rational input; nearest integer with ties-to-even; reject NaN/Inf/overflow/bool-as-int |
| Math | No sin/exp/log/pow on authority paths; use pinned integer tables/approximations with hashes and independent error bounds |
| Time/identity | No time.time/datetime.now/time.monotonic/uuid4/environment reads in engines; game Tick only |
| Threads/processes | Serial canonical program; any future parallel work publishes in canonical order |
| Optional AI | Only persisted accepted packages; offline replay never calls providers |
| Diagnostics | Wall-time profiling/session IDs/root tokens are outside CORE and cannot select domain outcomes |

Floats remain allowed for schema-approved presentation-only effects. Ruff/mypy/import-linter/proxy/replay supply controls; no new custom nondeterminism checker. All CORE A and B values are hashed; B is not a loophole for hidden live randomness.

### A6.3 Semantic Hash / Versioning

Hash schema `sha256-core-tree-v1`. Canonical JSON: UTF-8, sorted keys, compact separators, ensure_ascii=False, no duplicate keys/floats/NaN/Inf; typed schema prevents bool/int coercion. CORE collections have explicit order; no repr/pickle/object ID/Python hash.

Each node hash is `SHA256(pack(domain_tag, canonical_JSON_text))`; domain tags are component/v1, pending-event/v1, core-root/v1 respectively.
1. Component leaf: canonical address/schema/CORE field values sorted by field name. Include units/scales via pinned schema fingerprint; omit DERIVED fields.
2. Pending-event leaf: complete semantic event/payload/policy routing. Include due tick, causes and ID; omit transport/debug data.
3. Root: canonical identity/clock, sorted address+component-hash pairs, canonical queue-order+event-hash pairs, schema/rules/schedule/RNG versions and accepted gameplay-package hashes.

Hash caches are DERIVED and tied to sealed component versions; recomputation from scratch must produce the same hash. Index page layout is excluded. CORE root includes every Tier A/B field/cursor/remainder/queued effect; never hash only visible player/NPC fields.
Transport revision/receipt retention/presentation caches are checked separately, not authority time or event identity. Same command replay must still reproduce receipts/acceptance sequence. Changing only transport metadata cannot alter simulation hash.
Gameplay schema/rules/RNG/hash/schedule fingerprints are pinned per save/trace. Incompatible versions reject before replay; do not silently reinterpret. Explicit forward save migration belongs A9, supported-fixture tests later. Content/asset packages carry IDs/schema/hash; runtime accepted outputs persist before simulation. Missing/mismatched packages stop replay instead of regenerating them.
Pure art/audio/model artifacts are outside authoritative calculation; their import versions/hashes remain in build/replay provenance. Authoritative geometry/material/gameplay values belong validated gameplay packages and CORE rules, not renderer data.

### A6.4 Tier A Composition / Golden Regression

`catchup_A(catchup_A(S,t0→t1),t1→t2) == catchup_A(S,t0→t2)` for all valid splits using identical rules/frozen inputs and no inserted actions.
Compare **all Tier A fields and pending semantic state**, including clock/update cursors/remainders/entity IDs/spawn counters/event IDs/causal links. Compare canonical values as well as projection hash; not a selected-field shortcut. Transport commits may differ between callers and are excluded from this autonomous-state law.
Ordinary same-command replay compares full CORE A+B hashes and receipts; B divergence is allowed only between declared different LOD modes under A11 bounds. No B approximation may silently change A outcomes. Deleting DERIVED preserves full CORE.

Golden workflow: record new typed trace → replay from identical initial snapshot/packages → compare outcome and post-step CORE hashes; compare first differing component/event path. Record rejected/aborted commands with unchanged expected state, not only successful turns.
Mandatory matrix: same trace twice in one process; traces X then Y versus Y then X, comparing each trace to itself; fresh world/services/view/RNG caches for each run; fixed0/fixed1 and randomized PYTHONHASHSEED subprocesses; DERIVED warm/cold; accepted content frozen. Never reverse dependency schedule or reverse commands within a trace.

| Anti-pattern | Golden evidence / limit |
|---|---|
| AP-05 global mutable state | Repeated/reversed trace execution detects cross-run contamination |
| AP-07 destructive refactor | Same pinned hashes/outcomes; changed behavior requires separate reason/versioned change |
| AP-10 fake tests | Meaningful traces detect changed outcomes; mutation later verifies tests kill engine defects |
| AP-11 overfitted tests | Boundary/invariant/composition traces + independent expected vectors + engine mutation |

Golden replay is the primary regression barrier, not proof against all unvisited code. Coverage/zero-hit/mutation supplement it; do not claim a toy happy trace verifies the whole game. Mutation remains async, engines-only; no new CI/custom tool built in Phase0.

### A6.5 Interface Declarations

```python
@dataclass(frozen=True)
class RngAddress:
    logical_tick: Tick
    phase: Phase
    wave: int
    engine_id: str
    entity_id: EntityId
    purpose: str
    causal_key: str

class RngService(Protocol):
    def scoped(
        self, tick: Tick, phase: Phase, wave: int, engine_id: str
    ) -> EngineRng: ...

@dataclass(frozen=True)
class PackagePin:
    package_id: str
    version: int
    sha256: str

@dataclass(frozen=True)
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

@dataclass(frozen=True)
class ReplayWitness:
    canonical_core_json: bytes
    canonical_protocol_json: bytes
    canonical_facts_json: bytes
    canonical_diff_json: bytes

@dataclass(frozen=True)
class ReplayStep:
    command: GameCommand
    expected_outcome: TurnOutcome
    expected_core_hash: str
    expected_protocol_hash: str
    expected_facts_hash: str
    expected_diff_hash: str
    expected_witness: ReplayWitness | None

@dataclass(frozen=True)
class ReplayTrace:
    header: ReplayHeader
    steps: tuple[ReplayStep, ...]

@dataclass(frozen=True)
class ReplayMismatch:
    step_index: int
    path: str
    expected: str
    actual: str

class ReplayRunner(Protocol):
    def run(self, trace: ReplayTrace) -> tuple[ReplayMismatch, ...]: ...
```

ReplayHeader pins initial CORE/protocol hashes; fixture loader supplies validated full state and protocol metadata separately. BLOCK4 defines stream/receipt metadata; each step verifies its separate protocol hash as well as CORE/outcome. Protocol metadata remains outside catch-up composition/RNG/event identity. Trace serialization uses registered command/payload codecs, never live object repr. ReplayRunner mismatch tuples report facts; an empty tuple alone is not execution proof without recorded commands/results. RngAddress is semantic schema; scoped facade constructs it and rejects impersonated/out-of-tick streams.

AR-006: replay verifies committed fact/diff output as well as state/outcome. facts hash=SHA256(pack('turn-facts/v1', canonical_JSON(ordered_emitted_WorldEvents))); diff hash=SHA256(pack('turn-diff/v1', canonical_JSON(StateDiff_or_null))). Facts are all candidate-produced simulation and record-only events in canonical emission order, published only on confirmed commit; delayed deliveries are not new emissions. Rejection/abort/exact duplicate replay emits [] and null diff; an exact duplicate still returns its original receipt. Presentation cues remain DERIVED and have separate integration tests. Removing a record-only Stepped fact must fail replay even if x/visits/CORE are unchanged.
ReplayWitness holds canonical expected post-step CORE/protocol/fact/diff documents at the fixture boundary, validated by registered schemas before comparison; engines never receive these bytes. The CORE document contains full canonical semantic state, not only the tree of component hashes. Fixture codec converts bytes to/from strict UTF-8 JSON and checks all witness hashes. With witness, compare normalized values and report first sorted component/field path or ordered event index with expected/actual values. Without witness, report only $core_hash/$protocol_hash/$facts_hash/$diff_hash or outcome; never invent a differing leaf from two digests. Phase0 small goldens require non-None independently authored witnesses; full expected state need not be retained for every ordinary production checkpoint.
AR-001: core/protocol canonical encoding and receipt hashes already belong to the P0-001 COMMIT path. P0-001 creates NEW src/domain/canonical.py with its exact skeleton encoding/vectors; P0-003 reuses it (MODIFY only where the promoted source-based order requires), adding RNG/record/replay and fact/diff comparison. A full replay runner is not a skeleton prerequisite; canonical hashes are. Both remain parts of the original four Phase0 items.
Chosen: addressable SHA256 counter service + CORE tree hashing + command replay. Rejected: global random/Python hash/UUID seeds, full-history event sourcing, replaying live AI, float CORE. Escape: versioned replacement RNG/hash with explicit migration/new fixtures; old traces remain pinned, never compared under silently changed algorithms.
Mapped: F-04/F-05/F-07/F-08; AP-05/AP-06/AP-07/AP-10/AP-11; C-02/C-03/C-04.

## PLANNED Acceptance Examples

Fixtures below are synthetic contract values, not v1 calculations or game balance.

| Case | Expected contract |
|---|---|
| Delayed effect emitted tick10, due40 | No application before40; consume at declared phase at40; save/reload preserves ID/payload/order |
| Handler fails after staging due event | Abort leaves original pending record/state intact; retry produces same effects/IDs |
| Same-tick feedback needs wave8 after0..7 | CASCADE_LIMIT before commit; no queue/event dropping |
| Tick10→12 vs10→11→12, passive | Same entire Tier A state/queue/IDs/clock/remainders; transport revisions checked separately |
| Nested alias `reserves` mutation | Immediate ReadOnlyViolation; parent and child state unchanged |
| Retained proxy after barrier | ExpiredReadView before reading stale values |
| Clear indexes/visual caches | Full CORE hash unchanged; rebuilt DERIVED is not authority |
| Fixed-point scale1000, decimal0.5005/0.5015 | Ties-to-even500/502; branch on integers only |
| RNG interval n=10, candidate u=2^64−1 | Rejected (limit=2^64−6); next acceptable candidate determines result |
| Two entity stream addresses | Drawing from one cannot advance the other; reopened same address preserves its cursor within invocation |
| Same trace twice / X,Y thenY,X | Each trace retains hashes/outcomes; not reversed simulation order |
| Missing accepted package/hash mismatch | Explicit offline replay failure; zero provider calls |
| Change only presentation artifacts | CORE unchanged; build provenance differs |
| CORE field without registered writer/consumer | Boot/schema evidence fails or explicit future scope; never silent write-only completion |

Verification: event save/order/cancellation/abort; full Tier A property tests; nested mutation/access attribution; typed reducers/base→final diffs; RNG independent reference vectors; full/cached hash equality; contamination/hashseed/package pinning; rejected/aborted trace steps. No executable tests are created in this DESIGN task.

## Completion / Next

A4–A6 designs/interfaces/alternatives/mappings specified. Exact gameplay field schemas, time units/LOD bounds/job budgets, serialization/import/save migrations remain later prerequisites; no production task READY. Custom planned2/max3/current0; Phase0 exactly4. Actual tests/benchmarks/type checking NOT_RUN.
Record actual document/interface checks in [BACKLOG](../BACKLOG.md) and [handoff](../SESSION_HANDOFF.md). Next: **RS-ARCH-002-B04 / BLOCK4 A7 typed commands, A8 memory/retrieval, A9 persistence/migration**.

--- BLOCK 3/9 END. Enter "continue" for the next block. ---
