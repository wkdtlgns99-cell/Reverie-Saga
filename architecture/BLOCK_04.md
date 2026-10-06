# BLOCK 4 — Commands, Memory & Persistence

Date: 2026-10-03 | Task: RS-ARCH-002-B04 | Owner: GPT-6.1 Sol | Mode: DESIGN
Inputs: [BLOCK1](BLOCK_01.md), [BLOCK2](BLOCK_02.md), [BLOCK3](BLOCK_03.md), prompt A7–A9/C-01 and MASTER §§2/7–9.
Status: self-reviewable proposed contracts; no production code/services/tests. Compact English. Python fences extend BLOCK2→3's shared declaration listing; payload ABCs describe feature-owned shapes, not implemented codecs.

## Cross-block Decisions

| Open contract | Decision |
|---|---|
| Action timing | Consuming command has positive duration; one admitted action at target_tick; earlier substeps are passive |
| Inspect/UI | Pure queries use a separate port; discoveries/interactions that change CORE require commands |
| Retry | Exact committed duplicate returns original receipt; durable stream high-water prevents execution after receipt eviction |
| Memory | Five structured semantic levels; permanent anchors CORE, search indexes/summaries DERIVED |
| Retrieval | T0 structured local queries; semantic T1 deferred and never authoritative |
| Save | Phase1 SQLite changed-row transaction, then owner-head publication; slot export temp→validate→replace |
| Compatibility | No v1 save support; explicit forward chains for intentionally supported v2 versions only |

BLOCK3 replay declarations add initial/per-step protocol hashes for separate receipt/stream verification. No protocol metadata enters CORE/RNG/event identity. A10 owns final schemas/codecs/import validation; A11 time units/duration rules; A12 wire/bindings/lifecycle; A13 measured budgets; A14 provider jobs/approval.

## A7. Typed Player Commands / Admission

### A7.1 Input Boundary

Keyboard/gamepad/UI → client input mapping → schema/versioned intent → Brain adapter → GameCommand → authoritative admission → BLOCK2 tick program. Camera rotation, menu focus and animation timing remain client-local. Client SDK/vector objects never cross domain contracts.

| Intent | Payload requirements / ownership |
|---|---|
| Attack | Target entity, registered attack profile, whitelisted modifiers; Brain calculates hit/damage/cost |
| Skill | Skill reference, schema-specific target and modifiers; no client-calculated effect |
| Guard | Registered guard mode; Brain determines cost/duration/status |
| Item | Owned inventory entry, quantity, schema-specific target; Brain consumes/applies |
| Move | Location + fixed-point coordinates; Brain validates route/collision/reachability |
| Interact | Target + registered interaction option; Brain checks availability/consequences |
| Talk | Conversation/content reference + legal option ID; selected text cannot award rewards |
| Travel / Wait | Destination or requested interval; Brain computes/adopts bounded legal duration |
| Inspect | Read-only query when no CORE change; revelation/discovery is an explicit command |

Target forms and units are feature-owned schemas, not a growing central optional-field DTO/union. No open parameters dict. Names/IDs must resolve in accepted catalogs; coordinates use schema scale and space ID, never screen pixels/floats. Optional language/debug/accessibility adapters later produce these same intents; normal play has no language parser/LLM dependency.

Decode checks exact schema/version, required fields, unknown-field rejection, integer-vs-bool distinction, ID syntax, tuple/field bounds and UTF-8/NFC. Initial command-body TARGET≤16KiB and modifiers≤4; A12 wire cap is separate. Reject client-supplied HP/damage/cost/outcome/seed/time overrides. Bytes become typed payloads at the I/O boundary; no Any/object enters domain.

### A7.2 Admission / Execution / Results

1. Adapter validates authenticated world/branch/session route and controlled actor; actor_id alone is not authority.
2. Check committed duplicate ID/fingerprint before expected_revision. Same ID/different canonical command is COMMAND_ID_CONFLICT; exact duplicate returns original receipt plus resync when current revision is newer.
3. Check registered stream/sequence window; then expected_revision against committed owner head. Stale command is STALE_REVISION + current revision/resync status, no simulation.
4. Schema-owned pure admission uses an observed committed view: actor exists/alive/controllable, target/legal choice available, resources and rules permit starting. No RNG/time/state/queue mutation.
5. Brain computes positive integer duration and TurnPlan; target_tick>start_tick for every consuming command. A11 assigns real-minute scale/duration policies. Initial AdmittedAction executes at target_tick exactly once; all prior substeps carry None. No client-specified arbitrary target_tick.
6. PRE_TICK and intervening events may invalidate execution. Execution engine rechecks the staged view and emits a typed fizzle/partial outcome with rule-defined time/cost; this is a committed domain result.
7. Technical contract failure/exception aborts the candidate. Successful candidate durably commits once before presenting. Render failure retains receipt; never rerun the action.

Pure Inspect/journal/status queries pin one committed revision and public read permissions. GameQuery expected_revision=None explicitly means latest; a concrete revision mismatch returns stale status. Queries do not advance tick/revision, draw RNG, create memories or consume events. Private NPC memories are not automatically public UI data. A query requiring authoritative change must route through a command instead.

Error families: malformed/unsupported schema; unknown/unauthorized actor; illegal target/choice/resource; stale revision; ID conflict/expired retry; runtime contract abort; persistence unavailable/uncertain. Failure code + localized message key + current revision where meaningful; no misleading successful empty result. A7 uses BLOCK2 TurnRejected/TurnAborted/TurnCommitted; feature facts explain rule outcomes.

### A7.3 Bounded Idempotency

Protocol command IDs: `c1:<branch_hex>:<stream_hex>:<sequence_decimal>`. Branch/stream are owner-issued 32lowercase-hex protocol IDs; sequence is1..2^63−1, canonical decimal. These identifiers are outside simulation; semantic action keys remain BLOCK3's payload/actor/execution_tick hash.
One actor-bound stream has strictly increasing successful sequence numbers; gaps are legal. Store its highest committed sequence and up to1024 recent receipts globally per save. Canonical command fingerprint includes actor, expected_revision, kind/version and full payload; request envelope/session token is excluded. Duplicate retries must resend that exact command, not rewrite its expected revision.

Receipt lookup precedes stale checking. If a known stream's old sequence has no retained receipt, return RETRY_WINDOW_EXPIRED; never execute it again, even if supplied with the current revision. New successful commit stores receipt/fingerprint/high-water in the same transaction as CORE. Admission rejection/abort does not advance high-water; corrected requests use a new ID. In-flight duplicate submissions share one candidate/result; no second evaluation.
TARGET≤16 registered streams per save; retire explicitly, do not silently reuse IDs. Unknown/retired streams cannot submit new commands; reconnect registration and save locking are A12. Retention removes oldest receipts by commit revision deterministically while keeping active stream high-water. No unbounded command ledger/global seen set.
Replay fixtures include branch/stream registration and protocol state; no real handshake/clock/network required. Protocol registration/retirement/fork occurs at owner-controlled boundaries and begins a new validated replay checkpoint; a command trace never infers those changes from its environment. A6's separate protocol hash is `SHA256(pack("protocol/v1", canonical_JSON(ProtocolSnapshot)))`, with streams sorted by stream_id and receipts by commit revision/command_id; it covers branch/revision/high-water/fingerprints/full retained commands/receipts. Restore/fork is an explicit owner operation: a fork issues a new branch, invalidates prior routing, preserves CORE and records provenance. Loading cannot let queued commands from a previously attached world act on the new one.

### A7.4 Interface Declarations

AR-007: the16-stream bound includes active cursors and retired tombstones in a branch. Retiring marks StreamCursor.status='retired', preserves actor/high-water, and prevents new execution; IDs are never removed/reused within that branch. Authorized exact retained retries may recover their existing receipt; old sequences without a receipt return RETRY_WINDOW_EXPIRED, new retired-stream sequences return STREAM_RETIRED. Registering the17th stream returns STREAM_LIMIT without mutation. Reclaim capacity only through explicit new-branch fork/checkpoint, invalidating old routing and recording replay provenance; never infer a new branch during an ordinary command. Retire/register/fork protocol transitions occur at quiescent owner boundaries, outside engine input/CORE time. This prevents retired-ID reuse without an unbounded seen-ID ledger.

```python
@dataclass(frozen=True)
class WorldPosition:
    location_id: EntityId
    x: int
    y: int
    z: int

@dataclass(frozen=True)
class AttackPayload(CommandPayload, ABC):
    target_id: EntityId
    attack_profile_id: str
    modifiers: tuple[str, ...]

@dataclass(frozen=True)
class MovePayload(CommandPayload, ABC):
    destination: WorldPosition

class QueryPayload(FrozenPayload, ABC):
    """Feature-owned immutable query fields; no simulation edits."""

@dataclass(frozen=True)
class InspectPayload(QueryPayload, ABC):
    target_id: EntityId
    section: Literal["public_profile", "visible_status", "available_actions"]

@dataclass(frozen=True)
class GameQuery:
    actor_id: EntityId
    expected_revision: WorldRevision | None
    payload: QueryPayload

@dataclass(frozen=True)
class AdmittedCommand:
    plan: TurnPlan
    action: AdmittedAction

AdmissionOutcome: TypeAlias = AdmittedCommand | TurnRejected
PayloadT = TypeVar("PayloadT", bound=CommandPayload, contravariant=True)

class CommandAdmission(Protocol[PayloadT]):
    def admit(
        self, command: GameCommand, payload: PayloadT, state: ReadPort
    ) -> AdmissionOutcome: ...

class QueryResult(FrozenPayload, ABC):
    """Registered typed response, with explicit revision binding."""

@dataclass(frozen=True)
class QueryReply:
    revision: WorldRevision
    result: QueryResult

QueryOutcome: TypeAlias = QueryReply | TurnRejected

class QueryService(Protocol):
    def execute(self, query: GameQuery) -> QueryOutcome: ...
```

Concrete feature subclasses provide the inherited schema property; abstract shapes above are not instantiable completed commands. Registry binds kind/version → typed codec/admission/engine/presenter, not a central dispatch switch. Admission rules and observed read rights are registered, distinct from engine manifests. No production tasks READY until duration/schema/route constraints are complete.
Chosen: typed intent + pure admission + delayed execution recheck. Rejected: client outcomes, natural-language core, generic kwargs, optimistic client-authority and unlimited dedup history. Escape: replace input/transport adapter without changing payload/domain semantics.
Mapped: F-01/F-02/F-06/F-09; AP-01/AP-02/AP-05/AP-06/AP-08/AP-09; C-03/C-05.

## A8. Structured Memory / Retrieval / Generation Context

### A8.1 Five Levels / Truth Boundary

| Level | Structured semantic role | Authority |
|---|---|---|
| 1 Evidence | Observed/reported event proposition with source/certainty | CORE knowledge/belief, not automatically objective world truth |
| 2 Episode | Ordered related evidence and participant/place links | CORE links; generated narration is DERIVED |
| 3 Pattern | Rule-derived semantic association/repeated experience | CORE only when explicitly calculated/committed; LLM summary cannot invent it |
| 4 Biography | Enduring self/relationship/goal-relevant propositions | CORE; ordinary expiry/retirement only by explicit rules |
| 5 Anchor | Permanent high-priority identity/trauma/commitment propositions | CORE A, protected; never silently evicted/truncated |

These are new semantic levels, not v1 memory classes/formulas. Memories integrate MASTER traits/12-axis/10-factor/20-factor/BDI capabilities through typed propositions/references; detailed cognition calculations remain later design. Observer belief can be mistaken; it cannot change objective HP/economy/quest state without a domain action.
Owner memory component stores immutable records, stable IDs, logical ticks, subject links, priority, certainty, source event/package references and protected status. Retirement/merge is a typed delta/fact from its declared owner; no summarizer writes directly to CORE. Future events/goals retain required references or a validated structured replacement; forgetting cannot erase pending causality.

Initial configurable rules TARGET:≤256 records/NPC, including≤16 anchors; priority0..255. At normal-record pressure, deterministic explicit retirement of eligible unprotected records by `(priority, observed_at, memory_id)`; protected/required references are ineligible. If no eligible slot, emit typed capacity outcome and do not create a record. Mandatory protected additions must reserve capacity; impossible mandatory preservation fails the candidate before commit. No silent dropping or unbounded anchor growth. This is a new provisional capacity policy, not validated psychology/balance.
Anchor rewrites/removal require a separately approved behavior/content policy; ordinary engine expiry cannot do it. World memory partitioning/population sizing/retirement invariants and representative playtests are prerequisites before memory production orders. Capacity behavior must not be implemented as partial mutation.

### A8.2 T0 / T1

Authoritative decisions use a pure selector over the recursively observed typed memory view, with explicit filters and stable ranking `(-priority, -observed_at, memory_id)`. Enumeration observes membership/order; anchors/required links have explicit access. No engine calls a DB/vector/provider service. Index warmness cannot change chosen authoritative records.

T0 for optional generation/UI retrieval: local structured entity/subject/level/time/priority queries from a CORE-derived projection, pinned to revision/core_hash. Choose ordinary SQLite indexes in Phase1 if needed; no FTS/vector dependency in Phase0. Validate projection freshness; unavailable index uses the same capped typed-state scan. Natural-language full-text evaluation, including Korean tokenization, precedes any FTS adoption; do not assume English BM25 solves Korean retrieval.
T1 semantic retrieval is DEFERRED. It may rerank optional generation context only; domain types/engines are unchanged by config. T1-off/failure→T0 + explicit degraded; no Docker/player DB/server installation. Build embeddings/indexes outside turns. No large local embedding/LLM process alongside editor/asset generation on the16GB/6GB laptop.

Before T1 adoption: labeled versioned dataset TARGET≥100 representative Korean/English/entity/temporal/anchor queries, disjoint evaluation examples. Mandatory anchors/constraints inclusion=100%; T0 relevant recall@8≥0.85 and T1-off decrease≤0.10 absolute against accepted T1 results. Score recall@8 over optional retrieval; mandatory facts are added separately, not competing for those eight positions. Ground truth is independently labeled, not provider output. Quality/memory/latency NOT_MEASURED; if bounds fail, improve T0 or defer T1. Ordinary game cognition must remain complete without any semantic service.

### A8.3 Optional Generation Context

Only explicit MASTER generation windows: new game/chapter/loading/large-content preparation. Pause authoritative turn admission or freeze a revision; outputs bind to world/core_hash/source refs. If relevant source state changes, reject/rebuild context before acceptance; never apply stale outputs to a different world.

| Input allocation TARGET | Tokens | Overflow rule |
|---|---:|---|
| System/job/schema instructions | 1024 | Required; fail if contract cannot fit |
| Protected anchors/mandatory constraints | 2048 | No truncation; narrower job or CONTEXT_REQUIRED_OVERFLOW |
| Scoped structured world/entity facts | 3072 | Explicit scope; required facts cannot be dropped |
| Optional ranked memories | 1536 | Whole lowest-priority records omitted first |
| Source/provenance references | 512 | Required references retained |
| Total input / reserved output | 8192 / 2048 | Total context ceiling10240 for this profile |

Use the actual selected tokenizer and record its version/counts; absent compatible tokenizer means budget UNVERIFIED, no falsely certified request. Provider/model capability check remains A14; these are project ceilings, not quota guarantees. Do not truncate arbitrary bytes/UTF-8, structural IDs, half records or anchors. Exact deterministic compression uses schema-owned projections; optional generated prose summaries are DERIVED, labeled and linked to full source records, never a replacement for authoritative constraints.
Context contains no API keys/save paths/session secrets. Sources include memory/event/entity/content IDs, revision/core hash and value hashes. Accepted structured output gets validation/required approval plus package hash/provenance, persisted before gameplay consumption. Cache by canonical context + job/schema/prompt/provider/model/budget versions; reuse only validated compatible accepted packages, not raw failed candidates. Art/audio binaries stay outside simulation memory. Replay uses frozen packages with zero provider calls.

### A8.4 Interface Declarations

```python
MemoryLevel: TypeAlias = Literal[1, 2, 3, 4, 5]

class MemoryProposition(FrozenPayload, ABC):
    """Typed observer proposition; not opaque LLM context."""

@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    owner_id: EntityId
    subjects: tuple[EntityId, ...]
    level: MemoryLevel
    priority: int
    observed_at: Tick
    certainty: Literal["observed", "reported", "inferred"]
    protected: bool
    proposition: MemoryProposition
    source_events: tuple[EventId, ...]
    source_packages: tuple[PackagePin, ...]

class MemoryRead(Protocol):
    @property
    def records(self) -> Sequence[MemoryRecord]: ...

@dataclass(frozen=True)
class MemoryQuery:
    subjects: tuple[EntityId, ...]
    levels: tuple[MemoryLevel, ...]
    since: Tick
    limit: int

class MemorySelector(Protocol):
    def select(
        self, memory: MemoryRead, query: MemoryQuery
    ) -> tuple[MemoryRecord, ...]: ...

@dataclass(frozen=True)
class ContextSource:
    source_id: str
    value_hash: str

@dataclass(frozen=True)
class ContextBundle:
    world_id: str
    revision: WorldRevision
    core_hash: str
    canonical_context: str
    sources: tuple[ContextSource, ...]
    input_tokens: int
    output_reserve: int
    tokenizer_version: str
    context_hash: str
    degraded: tuple[Degradation, ...]

class GenerationContextBuilder(Protocol):
    def build(
        self, revision: WorldRevision, job_spec_hash: str
    ) -> ContextBundle: ...
```

ContextSource IDs resolve through a versioned provenance catalog to typed field/event/memory/package references; no unchecked prose citation. Context strings are a generation-adapter boundary, never engine state. GenerationContextBuilder failures use explicit context/index/tokenizer error codes, not empty successful bundles. MemoryQuery limit1..32; empty subject/level tuples mean all eligible records within the authorized owner component; since is inclusive.
Chosen: structured five-level memory + pure selection/T0 local indexes; optional budgeted provenance context. Rejected: opaque chat history as state, mandatory Qdrant/Docker/embeddings, live generation deciding cognition, destructive LLM summarization. Escape: replace derived retrieval adapter/index under identical schema/fallback; T1 needs evaluation before adoption.
Mapped: F-03/F-04/F-05/F-07/F-10; AP-01/AP-02/AP-05/AP-06/AP-08/AP-10/AP-11; C-01/C-02/C-03/C-04.

## A9. Persistence / Recovery / Migration

### A9.1 Durable Representation

Phase0 stays in-memory; persistence is Phase1+. Choose embedded SQLite durable save + versioned JSON content/replay exchange, retaining BLOCK1's provisional adapter boundary. One owner/connection writes a working save; database rows represent committed state, not a second live authority. Engines never query/update SQL. Ship the selected runtime; player installs no service.

| Stored group | Contents / invariant |
|---|---|
| Header | Save-format version; world/seed/tick/revision; CORE/protocol hashes; schema/rules/schedule/RNG/hash fingerprints |
| Components | Typed address/schema + canonical CORE fields, changed-row writes; all A/B fields/cursors/remainders |
| Pending events | Full envelope/payload/due/policy routing; IDs/causes/order preserved |
| Accepted gameplay packages | ID/version/hash + runtime accepted payload; shipped package references resolve against matching build |
| Protocol | Branch/registered actor-bound streams/high-water/recent command fingerprints/receipts |
| Replay/provenance | Initial checkpoint + bounded recorded command segment; generated-source refs/import/build pins |

No DERIVED caches/indexes or API keys in authoritative saves. Large pre-generated art/audio/models remain build assets, not duplicated per save. Runtime accepted gameplay data is retained with every export that references it; missing required data is CONTENT_MISSING, never provider regeneration.

Initial SQLite profile: rollback journal DELETE, synchronous FULL, foreign_keys ON; local filesystem and sole writer. Set/verify PRAGMAs outside transactions, then explicit Python3.13 autocommit=False with commit/rollback; no reliance on defaults or executescript during a turn transaction. Pin/measure the bundled SQLite version in preflight. Alternative WAL requires a separate read-concurrency/backup/cleanup justification; not enabled by default.
[Python sqlite3](https://docs.python.org/3.13/library/sqlite3.html) supplies transaction and backup APIs. [SQLite atomic commit](https://www.sqlite.org/atomiccommit.html) documents rollback-journal recovery and filesystem/flush assumptions; [synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous) documents the selected durability setting. These support the candidate, not proof of this game's crash/power-loss safety or p95 budget; fit remains UNVERIFIED.

### A9.2 Turn Transaction / Crash Boundary

Prepare candidate components/events/hash/new protocol receipt before acquiring durable write transaction. Compare expected base revision/hash; write changed/deleted component rows, queue changes, accepted dependencies, receipt/high-water, replay step and new header in **one transaction**. No full snapshot/JSON dump per ordinary turn. Validate constraints; commit durable transaction; publish one prepared owner head; then deliver receipt/diff. Rejected/aborted gameplay commands do not update saved CORE/revision/high-water. Diagnostic rejected-step trace recording is separate, optional and non-authoritative.

| Failure position | Required result |
|---|---|
| Before SQL / during staging | Discard candidate; old state/queue/receipts remain |
| SQL constraint/busy/disk-full with confirmed rollback | Explicit SAVE_UNAVAILABLE/TurnAborted; no head publication |
| Commit raises with uncertain durable result | Enter RECOVERING; stop submissions; reopen and inspect command receipt/header, never blindly retry |
| After durable commit, before head publication | Reload exact durable candidate; no action re-evaluation |
| After publication, before client receipt | Exact duplicate returns retained receipt; client resyncs |
| Forced termination/power interruption | Recover complete old or new commit, validate hashes/queue; corrupt store is explicit failure, never partial playable state |

RECOVERING is lifecycle status, not a fabricated successful TurnOutcome. A9 errors after possible durability must not report definitive TurnAborted until recovery proves absence. submit resolves only after confirmed outcome; unrecoverable uncertainty raises an explicit world-unavailable boundary error instead of returning a finalized TurnOutcome. Record no finalized replay step until resolution. This resolves BLOCK2's generic runtime-abort rule at the persistence boundary. Never delete/rename a working database's hot journal during recovery. Runtime save lock blocks a second writer; OS mechanism/scenario matrix belongs A12.

Bounded replay storage TARGET≤4096 command records/segment. At a boundary, create/validate a new full checkpoint with pinned protocol/content state, then rotate only replay history in the same owner transaction. Replay is not required to reconstruct current state from all history. Do not truncate pending events, protected memory or accepted referenced packages as log retention. Debug/golden fixture exports are separate retained artifacts. Actual checkpoint peak memory/disk/performance budgets remain A13 prerequisites.

### A9.3 Atomic Slot Save / Load

Working-save commits use database transactions. Manual save/autosave export to a named slot uses this separate protocol:
1. At a turn boundary, pause new admission; finish/discard active candidate; pin committed revision. No serialization of staged data.
2. Create uniquely named temporary SQLite destination in the **same directory/filesystem** as target slot; consistent backup from working DB using SQLite backup API. No raw copy of an open database. Stream pages; no required full-memory save copy. [Backup API](https://www.sqlite.org/backup.html) provides consistent database snapshots.
3. Validate destination integrity/foreign keys/schema/package hashes/full CORE/protocol hashes; close destination handles; flush file. Preserve previous slot until all checks pass.
4. Atomically replace target with validated temporary file; sync containing directory when supported by selected deployment filesystem. Report success only after required durability steps; unavailable guarantees are explicit preflight/release limits.
5. Replace failure retains old slot and reports SAVE_EXPORT_FAILED. Leftover temp files are never auto-promoted; bounded cleanup after inspection. Keep≤2 validated recovery generations per slot TARGET; A13 sets byte/job caps.

Do not replace an open working DB or use a cross-filesystem rename. Imported slots load into a new private working save: validate/migrate completely while old world stays untouched → acquire attachment/save lock → publish reconstructed owner head once → reset view/retrieval/presentation caches and session routing. Schema/queue/hash mismatch aborts load, leaving current world. Reload preserves world seed/ID/pending IDs/tick/revision/protocol; explicit fork changes routing provenance only. No live AI required.

### A9.4 Schema / Forward Migration

Save-format version is a positive integer, separate from component/event/content versions and gameplay-rule fingerprints. Register explicit forward edges vN→vN+1 with input/output schemas, deterministic transforms, expected hashes/invariants and supported fixture IDs. No downgrade; no silent application of different rules/RNG/schedule. Rule changes require explicit compatibility policy/task, not an incidental defaults tweak.

| Compatibility class | Action |
|---|---|
| Current compatible v2 | Validate all typed data/fingerprints; load |
| Intentionally supported older v2 | Copy to temp; apply complete forward chain; validate each step/final invariants; publish atomically |
| Missing chain / unsupported gameplay rules | UNSUPPORTED_SAVE_VERSION/RULESET; no write to original |
| Future version | NEWER_SAVE_VERSION; preserve file |
| Quilltale/v1 saves | UNSUPPORTED_LEGACY_SAVE; no promised compatibility/migration |
| Malformed/corrupt/missing package | Explicit detailed failure; no guessing/default success |

Migration operates on a backup/staging store, never the only source. Preserve old original and migration manifest; rebuild DERIVED only afterward. Preserve world/event identities and queue order unless an explicitly approved migration specifies a justified transform. Protocol receipt history binds its original command/schema/outcome: retain compatible codecs or explicitly retire old retry streams during migration, with reconnect status; never reinterpret old IDs as fresh commands.
“Optional fields with defaults” as implicit migration hide missing meaning/units, rewrite old gameplay silently, leave dead branches and undermine hashes. Defaults belong **explicit versioned migrations** with independent expected examples; actual nullable fields remain valid only when None has a defined domain meaning. Maintain every intentionally supported historical fixture in CI (future implementation); removing support needs documented policy/task, not deletion under refactor.

### A9.5 Interface Declarations

```python
@dataclass(frozen=True)
class StoredComponent:
    address: ComponentAddress
    canonical_core_json: bytes
    core_sha256: str

@dataclass(frozen=True)
class StoredReceipt:
    command: GameCommand
    command_fingerprint: str
    receipt: CommitReceipt

@dataclass(frozen=True)
class StreamCursor:
    stream_id: str
    actor_id: EntityId
    highest_committed_sequence: int
    status: Literal["active", "retired"]

@dataclass(frozen=True)
class ProtocolSnapshot:
    branch_id: str
    revision: WorldRevision
    streams: tuple[StreamCursor, ...]
    receipts: tuple[StoredReceipt, ...]

@dataclass(frozen=True)
class SaveHeader:
    format_version: int
    replay: ReplayHeader
    tick: Tick
    revision: WorldRevision
    core_hash: str
    protocol_hash: str

@dataclass(frozen=True)
class DurableTurn:
    expected_revision: WorldRevision
    expected_core_hash: str
    components: tuple[StoredComponent, ...]
    removed_components: tuple[ComponentAddress, ...]
    queue_change: QueueChange
    next_header: SaveHeader
    next_protocol: ProtocolSnapshot
    trace_step: ReplayStep
    accepted_packages: tuple[PackagePin, ...]

class DurableCommitStore(Protocol):
    def persist(self, candidate: DurableTurn) -> CommitReceipt: ...

    def recover_receipt(self, command_id: CommandId) -> StoredReceipt | None: ...

@dataclass(frozen=True)
class SaveExportReceipt:
    slot_id: str
    revision: WorldRevision
    core_hash: str
    file_sha256: str

class SaveSlots(Protocol):
    def export(self, slot_id: str) -> SaveExportReceipt: ...

@dataclass(frozen=True)
class MigrationEdge:
    source_version: int
    target_version: int
    transform_id: str
    fixture_ids: tuple[str, ...]
```

StoredComponent bytes are a persistence-codec boundary, validated into registered typed state before owner publication; never an engine byte/dict escape. accepted_packages references only already validated durable immutable package blobs; persist missing blobs before referencing and never permit dangling hashes. SaveHeader.replay pins the retained checkpoint, while current hashes/tick/revision identify the latest head. next_protocol uses bounded structural sharing; receipts do not embed previous protocol snapshots. recover_receipt=None proves no retained receipt only after successful validated recovery; expired-window rules still apply. Slot IDs map to owner-approved paths, not arbitrary client filesystem requests.
MigrationEdge is registry metadata; actual typed transforms/codecs are separate A10/Phase1 tasks, not fabricated implementations. No extra custom migration checker; pytest fixtures/replay/DB constraints supply evidence.
Chosen: delta-row SQLite transactions + atomic validated slot backup + explicit migration chain. Rejected: full-world JSON every turn, external DB, raw live DB copying, indefinite event-sourcing history, implicit default migrations and pretend v1 compatibility. Escape: versioned export/new adapter behind identical commit/codec/recovery contracts; retain old readers for supported fixtures.
Mapped: F-02/F-05/F-07/F-10; AP-01/AP-02/AP-05/AP-06/AP-07/AP-08/AP-10/AP-11; C-02/C-03/C-05.

## PLANNED Acceptance Examples

Synthetic contract fixtures only; no v1 calculations/oracles.

| Case | Expected contract |
|---|---|
| Client submits attack damage or float position | Decode rejection; zero CORE/tick/revision/queue mutation |
| Actor unauthorized / target unknown | Admission rejection; no RNG/effects |
| Exact committed retry with now-stale revision | Same original receipt; no new tick; resync when needed |
| Same command ID with changed target | COMMAND_ID_CONFLICT before simulation |
| Evicted receipt sequence below high-water | RETRY_WINDOW_EXPIRED; cannot execute again |
| Valid action, target removed during PRE_TICK | Defined fizzle/cost/time commit, not invalid-command rollback |
| Inspect twice / camera rotation | Identical CORE; no memory/event creation |
| Abstract payload or unknown codec version | Not admitted as a completed concrete action |
| Priorities7/9/9; tie ticks5/4/6 | Selection priority9,tick6 → priority9,tick4 → priority7,tick5; ID breaks exact ties |
| Memory full, only protected/required records | Explicit capacity outcome; no silent anchor deletion |
| T1 disabled/fails, T0 cold index | Complete gameplay; typed scan + degraded optional context, same CORE |
| Mandatory context2050 exceeds2048 allocation | Explicit required overflow/narrower job; never truncate anchor |
| Source world changes during generation | Reject/revalidate before acceptance; no stale package application |
| Failure between SQL writes and durable commit | Entire old components/queue/receipt state restored |
| Durable commit succeeds, reply/publication fails | Recover exact recorded commit; retry does not rerun |
| Save temp validation/replace fails | Previous slot usable; explicit export failure |
| Save/load with pending tick40 event | Same seed/IDs/order/CORE/protocol; event fires once at40 |
| v2 old supported / future / v1 fixture | Forward-chain load / explicit newer rejection / explicit legacy rejection |
| Delete all derived retrieval/visual caches | Full CORE unchanged; rebuild without provider calls |

Verification plan: pure admission/query boundaries, retries before/after eviction/reconnect/load, execution fizzles, memory ranking/protection/reference retirement, tokenizer/overflow/provenance, T0 fallback/quality, DB fault injection and process-crash matrix, snapshot/hash equality, all supported migrations/unknown fields, offline packages/replay. Assertions derive independently from contracts; runtime/property/mypy/pytest/replay/performance NOT_RUN.

## Completion / Next

A7–A9 design/interfaces/choices/mappings specified; hardware/token/retention limits TARGET, not measured. No production order READY. Phase0 exactly4; custom planned2/max3/current0; commit gates11 remain Phase1+. Self-review is not independent review.
Record actual checks in [BACKLOG](../BACKLOG.md)/[handoff](../SESSION_HANDOFF.md). Next: **RS-ARCH-002-B05 / BLOCK5 A10 schemas/content, A11 time/LOD, A12 IPC/lifecycle**. Stop after BLOCK4.

--- BLOCK 4/9 END. Enter "continue" for the next block. ---
