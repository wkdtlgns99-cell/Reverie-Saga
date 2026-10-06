# BLOCK 5 — Content Schemas, Time/LOD & Client Boundary

Date: 2026-10-03 | Task: RS-ARCH-002-B05 | Owner: GPT-6.1 Sol | Mode: DESIGN
Inputs: [BLOCK1](BLOCK_01.md), [BLOCK2](BLOCK_02.md), [BLOCK3](BLOCK_03.md), [BLOCK4](BLOCK_04.md); prompt A10–A12/C-03/C-05; MASTER §§1–3/8–11.
Status: proposed contracts/interfaces, self-review only; no production schemas/code/services/tests. Compact English. Three Python fences extend BLOCK2→3→4's shared declaration listing. Compatibility/performance/property/lifecycle evidence UNVERIFIED.

## Cross-block Decisions

| Contract | Resolution |
|---|---|
| Schema SSOT | Feature-owned frozen Python DTO + field annotations/registry metadata; export JSON Schema/field tables, never hand-edit generated projections |
| Data growth | Validated package catalog/chunks; counts are data, not engine branches |
| Logical time | Tick=1game second=1/60game minute; variable positive command duration; no wall-time advancement |
| Sparse simulation | Explicit node activation/wake boundaries; idle skip only when the entire tick program is a proven no-op except clock |
| LOD | CORE state determines interest; strict A unchanged by approximation; B profiles gated by bounds, C recomputable |
| Wire | Loopback TCP, u32 length + strict UTF-8 JSON; integer values use decimal strings |
| Public client state | Typed projection patches/snapshots, separate projection hash; private CORE remains Brain-owned |
| Lifecycle | Supervisor contains client+Brain, liveness outside simulation, one game instance; platform implementation deferred |

A13 next owns measured budgets/job ceilings; A14 generation/artifact approval/import orchestration. Exact gameplay formulas/balance/schema inventory remain separate bounded design tasks. No bulk assets/v1 mechanics imported. Custom planned2/max3/current0; Phase0 exactly4; commit gates11 Phase1+.

## A10. Typed Schemas / Content Pipeline

### A10.1 One Source / Boundary Validation

Canonical source: concrete deeply frozen dataclasses, typed scalar aliases/Annotated constraints and co-located FieldSpec metadata in feature contracts; TypeKey→type registration is explicit. Export both machine JSON Schema Draft2020-12 and a restricted client field-table catalog from that source. Schema/metadata hashes join boot/save/replay fingerprints. No separate hand-authored JSON/GDScript model may define different fields/ranges/units.
Choose Pydantic2 TypeAdapter for boundary validation/JSON Schema export; cache adapters at boot. Engines retain ordinary typed DTOs and do not validate JSON or import provider/client SDKs. Strict validation and extra=forbid are explicit; special decimal-string aliases validate lexemes/ranges, not permissive coercion. Concrete configuration/version support must pass preflight.
[Dataclass support](https://docs.pydantic.dev/latest/concepts/dataclasses/), [TypeAdapter](https://docs.pydantic.dev/latest/concepts/type_adapter/) and [JSON Schema export](https://docs.pydantic.dev/latest/concepts/json_schema/) support this candidate. They do not prove frozen children, custom metadata, polymorphic payload dispatch or cross-language behavior; independent conformance vectors are required.

| Domain | Source / required schema rules |
|---|---|
| Command/fact/delta/cue/query | Concrete feature payload; kind/version registry; closed fields, bounded immutable children |
| Component state | Every leaf CORE/DERIVED, A/B/C, owner/consumers, unit/scale/range/cap; no ambiguous classification |
| Content definition | Stable new IDs, typed references/effects/tags; no Python expressions/executable scripts |
| Package/import manifest | Version/hash/dependencies/provenance/license/acceptance/import target; A14 finalizes artifact fields |
| Wire/public projection | Generated schema projection + shared scalar rules; private fields excluded explicitly |
| Save/replay | Internal canonical CORE integers, explicit versions/migrations; never confuse wire bytes with CORE hash input |

External content/wire JSON encodes integer-typed fields as canonical decimal strings; internal DTO/CORE values remain integers. Canonical source aliases export the string pattern plus x-min/x-max/unit/scale for client tables and use explicit checked conversion. No bool/float/exponent/whitespace/leading-plus/leading-zero/-0 coercion. Tick/revision/sequence0..2^63−1 where applicable; positive sequence/version constraints narrow this range. Hashes/seeds remain fixed lowercase hex, entity IDs namespaced strings. JSON null is permitted only where None has a defined meaning. Presentation floats may be approved; they cannot feed CORE.

Type dispatch resolves registered kind/version before decoding its concrete payload; no universal Any dict or growing payload union. Raw JSON exists only inside reviewed I/O boundaries. Detect duplicate keys/NaN/Inf, depth/size violations and unknown fields before conversion. Cross-record rules validate references/ownership/location levels/acyclic parents, units, allowed effects, deterministic ordering and immutable children. JSON Schema shape checks alone cannot prove these invariants.
Local schema refs only; no network schema fetching or arbitrary classes/descriptors. Unsupported schema constructs fail export, not silently omitted. Initial client subset: closed objects, required/explicit nullable fields, enums/literals, strings/patterns, bounded tuples/arrays, booleans, decimal integers, local refs. Numeric range/unit metadata stays mandatory in generated tables. Field-table exporter/client decoder are ordinary binding code, not additional governance checkers; Phase1 tests and the existing data wrapper validate their outputs.

### A10.2 Build / Import / Runtime Loading

Pipeline: source candidate → strict typed decode → reference/domain validation → required acceptance/provenance → canonical compiled chunks/catalog → atomic validated publication → runtime scoped load. Generation alone cannot publish; runtime rejected packages do not enter CORE. A14 owns approval UX/job states. Imported accepted runtime gameplay payloads persist before use under A9.

| Stage | Contract |
|---|---|
| Build | Sort inputs by stable ID/path, reject duplicate IDs/schema collisions, compute canonical hashes; deterministic compiler |
| Catalog | Package ID/version/hash, entries/type keys, dependency pins, chunk paths/hashes/byte bounds; paths confined to package root |
| Chunks | Canonical typed records, TARGET≤1MiB raw/chunk; larger collections split deterministically by sorted record IDs |
| Runtime | Read small catalog first; load requested definitions by ID/location/dependency; validate bytes/hash/schema before caching |
| Cache | Bounded derived decoded-definition cache TARGET≤32MiB; eviction by deterministic accounting/LRU cannot change CORE |
| World reference | Accepted catalog/package pins in CORE/replay; seeds/IDs fixed; package change requires explicit ingestion, not hot reload |

Cache stores immutable definitions, never mutable entity state. Orchestration prefetches declared definition dependencies before engine invocation; engine DefinitionReadPort exposes recursively observed read Protocols over those pinned immutable records, with no filesystem/provider/DB call. Declare catalog reads/consumer rights like state reads; a missing prefetched dependency is an explicit contract error. Adapter cache miss reloads identical pinned bytes; missing/hash-mismatched content fails explicitly, never triggers a provider. Build artifacts can be regenerated; approved originals/provenance and accepted runtime packages cannot be treated as disposable cache. No pickle/code execution/archive path escape. Phase0 dummy skeleton uses an explicit empty definition view/embedded immutable constants; package compiler/loaders remain Phase1+.
Historical≈5.53MB corpus is a scale reference (inspection5,661,063bytes), not authorization to import its stats/schema. Planned new-schema synthetic catalogs≥6MiB and120→200 continents must build/load through the same code/registry. More records add data/chunks, not hardcoded counts/dispatch branches. Verify increasing corpus cardinality, cross-links, cold/warm cache equality, peak RAM and load time on concrete MIN-SPEC; targets are not measured viability.

Location definitions preserve L0..L5 and traits semantics; combat/item/quest/cognition templates register their own typed fields. Six curated v1 descriptions remain reference-only until approved conversion into new IDs/schema. No v1 code/calculation/test oracle/schema binding reuse.
Schema evolution uses new versions and explicit reader/migration policy from A9; no implicit defaults or silently ignored fields. Required writer/consumer coverage comes from FieldSpec/manifests/proxy/replay, not an AST claim. One planned thin data/manifest wrapper aggregates standard validation; no new checker/tooling in Phase0.

### A10.3 Interface Declarations

```python
SchemaT = TypeVar("SchemaT", bound=FrozenPayload)

@dataclass(frozen=True)
class SchemaBinding(Generic[SchemaT]):
    key: TypeKey
    payload_type: type[SchemaT]
    schema_sha256: str

class PayloadCodec(Protocol[SchemaT]):
    def decode(self, encoded: bytes) -> SchemaT: ...

    def encode(self, payload: SchemaT) -> bytes: ...

class ContentRecord(FrozenPayload, ABC):
    """Feature-owned accepted immutable definition."""

@dataclass(frozen=True)
class LocationDefinition(ContentRecord, ABC):
    entity_id: EntityId
    level: Literal[0, 1, 2, 3, 4, 5]
    parent_id: EntityId | None
    display_name: str
    traits: tuple[str, ...]

@dataclass(frozen=True)
class CatalogEntry:
    entry_id: str
    schema: TypeKey
    chunk_path: str
    chunk_sha256: str
    chunk_bytes: int

@dataclass(frozen=True)
class ContentCatalog:
    package: PackagePin
    dependencies: tuple[PackagePin, ...]
    entries: tuple[CatalogEntry, ...]
    compiler_version: str

ContentT = TypeVar("ContentT", bound=ContentRecord)

class ContentReader(Protocol):
    def load(
        self, binding: SchemaBinding[ContentT], entry_id: str
    ) -> ContentT: ...

class DefinitionReadPort(Protocol):
    def definition(
        self, key: ComponentKey[ReadT], entry_id: str
    ) -> ReadT: ...
```

LocationDefinition is an abstract shape; concrete feature subclass supplies inherited schema property. Nonzero level requires an existing adjacent-level parent; level0 has None. ContentReader is an adapter for immutable definitions, not engine mutable-state access. Codec generic typing is backed by concrete registrations/validation; type hints alone are not schema proof.
Chosen: typed source→Pydantic/schema export→compiled catalog/scoped loading. Rejected: parallel handwritten schemas, whole corpus deserialization every turn, reflection/plugin auto-discovery, untyped executable templates and blind v1 corpus port. Escape: change validator/chunk storage behind identical source/codec/hash contracts after conformance/migration validation.
Mapped: F-02/F-03/F-07/F-10; AP-01/AP-02/AP-05/AP-06/AP-08/AP-09; C-03/C-04/C-06.

## A11. Game Time / Sparse Simulation / LOD

### A11.1 Variable Duration / Clock

Tick is nonnegative signed64-bit **game seconds**; one minute=60ticks, hour=3600, day=86400. Calendar begins at an accepted world epoch; calendar configuration is pinned data. No wall clock/FPS/provider latency changes time. Quantities expressed in minutes use exact numerator/denominator or schema-scaled integers; never floating minute accumulators.
Admitted consuming duration is a positive integer number of seconds, computed from pinned action rules and committed actor/route state. A fractional approved duration rounds upward to a whole tick before scheduling; rules validate units/maximum/overflow. Final action executes at target_tick once, per A7. Queries/menu/camera/loading do not consume time. Exact action costs/durations are new gameplay-rule tasks, not copied v1 values.
Active command target_tick is fixed at admission. Intervening changes cause explicit staged consequences/fizzle, not a hidden target-time extension. Multi-leg travel/interruptible actions require separately defined bounded commands; do not implement an entire journey as a teleport hidden behind this generic contract.

Initial routing TARGET:≤300seconds uses normal command path; longer admitted durations use a visible preparation job with one final COMMIT, identical tick semantics and old committed state visible until completion. Cancel before durable commit discards candidate; after possible durability recover first. Control/liveness pump yields at least every100ms TARGET, without altering tick/order/RNG. Wall-time measurement never selects different domain rules. A13 sets total tick/write/event/memory job ceilings before any long-job order READY.

### A11.2 Activation / Exact Idle Skip

BLOCK2 schedule retains stable compiled node ranks even when a node is inactive. Feature bindings now register NodeActivation for each manifest node: action kinds (RESOLVE only), matching event subscription, or explicit every_tick. Never infer autonomous behavior from source scanning. Any autonomous owner must schedule its next required wake in CORE or declare every_tick; undeclared hidden time dependence is invalid.
Phase-start barriers still apply; empty inactive phases are no-ops. An event subscriber receives its full sorted batch once/phase/wave. Wake events contain typed scope IDs; handler examines only that stable scope, not every continent/entity. Scope membership/references are CORE; optimized indexes are DERIVED. Coalescing exact wake bookkeeping must not coalesce/discard semantic consequences.

Reference semantics run the canonical one-second program from A4. Optimized planner selects the next action/event/required autonomous boundary and may skip only intervals where **all CORE changes, queued effects, RNG draws and event emissions are absent except clock**. For an idle span, reserve queue/cursors/remainders unchanged, advance clock to its end; do not skip action target or any A/B update. No full-world copy. Recompute next span after each staged boundary using a fresh observed view; do not retain a stale proxy/forecast across changes.
Initially permit only this proven no-op skip. Continuous rules requiring a per-second transition use every_tick or explicitly equivalent canonical wake rules; a generic `rate*elapsed_hours` approximation is prohibited. Any later exact closed-form optimization must independently prove **all fields/remainders/threshold crossings/event IDs/order** equal to the reference and satisfy every valid split; not approved merely because final HP matches.
This resolves A4's optional skip contract while retaining its reference tick sequence. Sparse entities with no scheduled transition remain unchanged; hierarchy/catalog definitions do not all run engines each turn. If an owner genuinely needs frequent work, use its exact declared schedule; insufficient performance requires redesign/measurement, never dropping its Tier A effects.

### A11.3 Interest / Tier A–B–C

LOD interest is a pure function of replayed player location, graph distance, quest/causal dependencies and pinned importance rules. Camera, wall time, cache residency and host load are excluded. Initial interest bands: near=same facility/adjacent route hop or immediate actor/target; regional=same region/relevant active quest; remote=other scopes. Rules resolve overlaps to highest interest in stable ID order. Threshold/profile changes are versioned.

| Tier | Initial rule / resolution |
|---|---|
| A strict | Same canonical causal transitions at every distance; due events/intent/food/temperature/resources/quest/death state remain exact; scopes skip only true no-op intervals |
| B bounded | Optional ambient crowd/rumor/encounter-suggestion statistics; profile samples at anchored game ticks (near60s/regional300s/remote1800s TARGET); no authoritative consequences |
| C derived | Rendering animation/crowd instances/indexes/caches; rebuild freely from accepted state |

Actual rumors that alter beliefs/relations/quests, actual spawned NPCs and encounter outcomes are Tier A. Tier B estimates never decide promotions/rewards/death/economy/quest states. An encounter suggestion becomes an authoritative encounter only through an independent deterministic A rule, not copied estimated B values. Enforce A-reader manifests cannot read B/C; A fact handlers cannot consume B estimates. Split mixed engines/fields by explicit ownership where needed.
B emits no delayed simulation facts into the A pending queue. Its next-sample cursors are typed CORE B fields; scheduler's derived due index includes them without becoming an authority. Separate producers/RNG addresses/budget reservations prevent B approximation from altering A emission sequence or exhausting A event capacity. Approved profiles must demonstrate these bounds before activation. All B is still included in full CORE hash and reproduces exactly under the same profile/trace.

| B candidate metric | Initial acceptance TARGET against fine reference |
|---|---|
| Ambient crowd density index0..10000 | Absolute difference≤1000; counts/IDs of real A entities unchanged |
| Cosmetic rumor exposure index0..10000 | Absolute difference≤500; factual knowledge/content/causal links unchanged |
| Optional encounter suggestion sets | Jaccard≥0.80 when either set nonempty; both empty=1; all actual outcomes A |
| Invariants | No negative/beyond-schema values; zero A-field/A-queue differences; no hidden B→A read |

Measure at every reference sample over versioned traces containing profile changes, return visits, deadlines and dense populations. Default implementation uses exact/reference B; approximating profiles remain disabled until independent tests meet bounds. No blanket “10% divergence” across unrelated systems. Quality/cost NOT_MEASURED; failure→retain exact B/repair profile, not relax A. Profile configuration is pinned for replay and changes only at explicit recorded/checkpointed boundaries.

Player return: before action/region reveal, consume all due causal transitions through admitted target in staging; load required pinned definitions. Any exact deferred local materialization must reproduce the canonical complete state and pending IDs; read-only queries never write catch-up state. Cosmetic caches may rebuild afterward. Long work becomes a visible bounded job, not a lost-event shortcut or secretly partially committed time advance.

### A11.4 Interface Declarations

AR-004: NodeActivation.lane is mandatory frozen metadata, defaults forbidden, and included in the schedule fingerprint. Every node of an engine has the same lane. Boot expands leaf fields and rejects lane-A reads/writes of B/C, lane-B writes of A, any B simulation emission/pending-queue right, and any A dependency on a B node. A consumers cannot subscribe to B estimates. B may read A/B and observe A events under declared rights; isolated cursors/budgets cannot choose A activation/order. Lane-A fact producer ranks use only the canonical A schedule subsequence (B02 A3); full A+B schedule still drives deterministic invocation. Lane declarations are registry data, never profiler inference.
Different B profiles may have different full CORE/schedule fingerprints; composition/LOD comparison uses complete A fields, A queue and A policy pins, excluding B-only configuration. Same-profile replay compares full CORE A+B/fingerprints exactly. Adding B nodes with unchanged A registrations must preserve all A producer ranks/IDs/queue headers; no global-node-index rank is allowed in A semantic state.

```python
@dataclass(frozen=True)
class NodeActivation:
    node: NodeKey
    action_kinds: tuple[TypeKey, ...]
    on_matching_events: bool
    every_tick: bool
    lane: Literal["A", "B"]

@dataclass(frozen=True)
class TickSpan:
    start_exclusive: Tick
    end_inclusive: Tick
    mode: Literal["execute", "idle"]

class TimePlanner(Protocol):
    def next_span(
        self, state: ReadPort, current: Tick, target: Tick
    ) -> TickSpan: ...

InterestBand: TypeAlias = Literal["near", "regional", "remote"]

@dataclass(frozen=True)
class LodScope:
    scope_id: EntityId
    band: InterestBand
    profile_version: str

class InterestResolver(Protocol):
    def scopes(self, state: ReadPort) -> tuple[LodScope, ...]: ...
```

execute span=end=start+1; idle span=end>start with verified no-op contract and no missed boundary. A duration may generate many spans, but planner emits one at a time; no array proportional to world time. Node activations are frozen feature metadata included in schedule fingerprint; every manifest phase has exactly one activation entry, no unknown node/action kinds. TimePlanner/InterestResolver are pure orchestration contracts, not engine-to-engine calls; access observation includes their reserved owner/system attribution.
PLANNED proof: dense reference vs sparse execution **full CORE** equality for exact profiles; Tier A full composition for arbitrary interval splits; all A cursors/remainders/IDs/pending effects compared, not visible projections. For different approved B profiles, A fields/A queue remain identical and each B metric meets its bound. Delete DERIVED, randomize registry/hashseed/trace order, retry/save/load at boundaries, and verify the same outcomes.
Chosen: second-indexed variable turns + explicit wakes/exact idle skip + measured B-only LOD. Rejected: full world scan every turn, wall-clock simulation, approximate global catch-up, camera-driven A resolution and visible-field-only equality. Escape: approved exact transition optimizations behind the same tick/event/schema contracts, with new independent property/reference evidence.
Mapped: F-01/F-03/F-05/F-09/F-10; AP-02/AP-05/AP-06/AP-08/AP-10/AP-11; C-01/C-03/C-04.

## A12. Brain↔Client Protocol / Lifecycle

### A12.1 Topology / Discovery / Security

Retain separate local Python Brain + provisional Godot4.x/GDScript client, supervised by a small launcher. Brain owns state/durable commits; Body owns rendering/input/public-view cache. Headless/debug app uses the same contracts/driver/engines in process; it does not fork alternate rules. Replacing Body/transport cannot change CORE hash for a pinned trace.
Choose loopback TCP (`127.0.0.1:0` kernel-assigned port); no fixed/manual port or service installation. Launcher provides endpoint and256-bit random session token through inherited private bootstrap handles, not logs/command line/world seed. Handshake timeout2s TARGET; bind only loopback, constant-time token comparison, bounded unauthenticated clients. Session entropy/liveness belongs adapters, never engines/replay.
Initial policy: **one active game instance per OS user/installation**. Second launch activates existing client or reports explicit startup/availability status; no second authoritative world. OS-owned instance lock releases on process death; PID alone is not ownership. A save has a separate exclusive writer lock keyed to its resolved file identity; SAVE_IN_USE never force-kills another writer. Every attachment has fresh routing epoch; old queued packets cannot execute after load/fork.
[StreamPeerTCP](https://docs.godotengine.org/en/stable/classes/class_streampeertcp.html) is the candidate Godot stream adapter. Python sockets provide the matching local adapter; client-neutral typed messages sit above them. Loopback token prevents accidental/unauthorized local connection; it is not a hostile-same-account/multiplayer security boundary. No internet gameplay listener is introduced.

### A12.2 Framing / SSOT / Compatibility

Each frame: `u32_big_endian body_byte_length || UTF8_JSON_body`; body1..1MiB inclusive. Incremental parser handles partial headers/bodies and multiple frames/read; validate length before allocation, depth≤32 TARGET, bounded arrays/strings per schema. Invalid frame closes the connection with explicit diagnostic; no resynchronization by scanning arbitrary bytes. Initial partial-header deadline2s/body5s/transfer10s TARGET; frame/read/control deadlines are transport timeouts, never simulation clocks.
Wire envelope pins protocol major/minor, routing epoch, message kind/version and request ID; typed payload registration determines its schema. Session token appears only in bootstrap/hello, not ordinary logged payloads. Commands retain A7≤16KiB body bound. All integer-typed JSON fields use A10 decimal strings; checked signed64 conversion precedes client arithmetic. No locale parsing, exponent, fractional numeric coercion or precision loss. CORE hashing still uses canonical internal integers; wire hashes only identify transfer bytes.
[Godot JSON](https://docs.godotengine.org/en/stable/classes/class_json.html) documents float conversion of JSON numeric values, motivating this representation. [Python JSON compliance](https://docs.python.org/3.13/library/json.html#standard-compliance-and-interoperability) explains permissive defaults; Brain parsing must reject duplicate keys/nonfinite values explicitly. Generic permissive JSON parsing is not authoritative validation.

The A10 canonical typed source exports protocol JSON Schema and client field tables under one fingerprint. Generic Godot binding decodes the supported subset/registered kinds using those tables; no manually maintained second schema. Build records exporter/table/decoder versions. Phase1 tests compare valid/boundary/invalid round trips in Python and Godot headless, including2^53+1/2^63−1, units/nulls/unknown fields/arrays/UTF-8. This uses ordinary binding code and the planned data wrapper/tests, not another custom checker.
Initial protocol1.0 accepts exact required schema fingerprint/build package compatibility. Major/minor changes need explicit supported codec-pair matrix; never assume all minor changes are safe. Unknown required state kind/version stops application with compatibility status; declared optional cosmetic cues may degrade. No schema/default guessing. Gameplay payload additions change feature contracts + registry, not the stable transport-message union.

### A12.3 Public Projection / Delivery / Backpressure

Brain adapter maps internal StateDiff and pinned owner view into a **public ClientViewDiff**, containing feature-owned immutable ViewPatch records and receipt. Visibility/knowledge filters are explicit; raw world/private NPC memory never becomes a client snapshot. Hidden changes may produce an empty public patch with a new receipt/revision. This is an intentional projection, not dropped authoritative state.
Client projection has its own canonical hash/version over disclosed values + scope membership; client never claims to reconstruct hidden CORE from receipt.core_hash. Apply diff only when base revision/projection hash matches; apply all typed before→after patches atomically, then verify result projection hash. Missing base/required type/value mismatch→request a pinned full **public** snapshot; no incremental guess. Internal StateDiff remains complete for persistence/replay; every required visible change is delivered.

Large diff/snapshot transfer: begin manifest → ordered chunks → end; transfer_id, routing epoch, kind, revision/base, total raw bytes, chunk count and raw-byte SHA256. JSON chunks use base64 bytes; raw chunk≤640KiB TARGET keeps envelope under1MiB. Initial maximum raw transfer32MiB/chunks64, one in-flight transfer; receive window≤2frames. No client partial application. Validate all chunks/whole hash/schema/projection before replacing view; disconnect/timeout discards candidate view, retaining prior committed display cache.
Prepare/validate bounded public projection/delivery plan **before durable COMMIT**; oversized diff switches to validated snapshot within32MiB. This prepares required state bytes only; nothing is sent and optional visual cues still map during postcommit PRESENT. If neither fits, explicit precommit capacity failure; never commit then silently trim required fields. Snapshot source stays pinned, not repeatedly copied from a moving WorldState. Bounds/serialization peaks must meet A13/MIN-SPEC before release.

TARGET: one unacknowledged committed update; admission queue≤8commands, reliable prepared transfer≤32MiB raw, transient wire window≤2MiB. No next command admission until client acknowledges atomic revision/projection application or completes resync. Additional requests get BUSY/status; no unbounded work queue. Lost receipt is recovered by A7 duplicate identity/stream high-water. Queries/status/control may continue against committed state.
ACK never controls CORE truth or re-executes a command. Slow UI blocks further admission outside simulation; animations may skip, ambient cues follow A3 coalescing. Essential/required state is never discarded. Invalid ACK/stale epoch cannot advance delivery cursor. Disconnect quiesces new admission and invokes shutdown; no autonomous game ticks while unattended.

### A12.4 Supervision / Shutdown

AR-005: required delivery has an explicit reservation lifecycle. prepare accepts both the public diff and a pinned PublicSnapshotSource over the candidate public projection; it materializes a snapshot only if the diff cannot fit, before durability. No full snapshot is rebuilt for every ordinary diff. Snapshot revision/hash must equal the candidate receipt; private CORE fields cannot enter it. The source is read-only and expires after preparation; prepared bytes are bounded and owned by the adapter. prepare failure releases any partial allocation internally; confirmed precommit abort invokes release. Possible durable commit retains the reservation until recovery confirms old/new state: absent commit -> release, present commit -> publish/resync from confirmed state. release and publish do not reevaluate engines or presentation.
Reservation states: PREPARED -> PUBLISHED -> ACKED, or PREPARED -> RELEASED. release is idempotent for an owned released reservation, rejects unknown/cross-session reservations, and cannot discard published required data. publish is idempotent for the same reservation/receipt; no second wire-update identity or action commit. ACKED frees prepared bytes. Disconnect releases uncommitted reservations; committed delivery is recovered from the durable head/public snapshot on reconnect. Errors: DELIVERY_CAPACITY, DELIVERY_RESERVATION_UNKNOWN, DELIVERY_RESERVATION_STATE, DELIVERY_PROJECTION_MISMATCH, DELIVERY_UNAVAILABLE; postcommit errors retain TurnCommitted. Adapter classes/codecs are finalized in the client order.

Launcher owns client+Brain handles and process containment; no detached authoritative helper. Deployment candidate: Windows Job Object with KILL_ON_JOB_CLOSE, non-inherited job handle, no breakaway. Create children suspended→assign to job→resume to close startup escape; launcher supervises exit of either child and shuts down sibling. Fail containment/bootstrap means explicit startup failure, no playable uncontained backend.
[Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) documents group management/kill-on-close; [assignment](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject) documents suspended-process/nested-job constraints. Packaging/Steam host containment must be tested; native launcher/OS code is deferred to deployment, not prioritized because the temporary dev OS is Windows11.

Liveness TARGET: client/Brain/launcher heartbeat every1s, loss timeout3s, helper cleanup≤5s. Control pump is separate from engine tick work and remains responsive during catch-up/provider windows; IO threads cannot write CORE. Watchdog checks real process handles + heartbeat so reused PID is not authority. Parent loss or client death stops Brain admission; backend cannot continue ticking in a disconnected orphan.
Graceful exit/Alt+F4: quiesce→reject new admission→cancel/discard precommit candidate or finish current durable boundary→flush/close working store→close channels/helpers. If deadline expires, supervisor terminates contained group; next launch uses A9 old-or-new durable recovery. An uncertain commit enters RECOVERING; never report it definitively aborted or rerun it. No need to finish a long job merely to exit.

| Deployment scenario | Required outcome / evidence |
|---|---|
| Normal menu exit / Alt+F4 | No helper remains≤5s; saved head complete; no partial view/turn |
| Client crash / Task Manager client kill | Supervisor stops Brain, old/new durable candidate recoverable |
| Brain crash / Task Manager Brain kill | Client stops accepting intent, explicit unavailable status; launcher closes group |
| Launcher crash / Task Manager launcher kill | Job handle closure + Brain parent liveness removes children; verify actual tree |
| Steam forced termination | Killing parent/client/group leaves zero authoritative orphans; actual packaged launch test |
| IPC disconnect/stall, parent hang | Quiesce/timeout/cleanup, never new game ticks or duplicate retry |
| Port race / second launch / save lock collision | Automatic discovery/activation or explicit conflict; no second writer |
| Exit during catch-up / commit / generation | Discard precommit work or recover durable commit; bounded cancellation/zero dangling refs |
| Power loss | Excluded from ordinary lifecycle CI; A9 durable storage/validated exports protect committed state under filesystem assumptions |

Verify process handles/tree after deadline, working save integrity/hashes/receipts, forced startup termination windows and reopen/retry; a disappearing game window is insufficient proof. Linux demo lifecycle optional only if later retained. Runtime shipped path needs no visible Python console/pip/Docker/DB service; provisional bundle choices stay subject to preflight.

### A12.5 Interface Declarations

```python
class ViewPatch(FrozenPayload, ABC):
    """Feature-owned before/after public projection edit."""

class ViewRecord(FrozenPayload, ABC):
    """Feature-owned complete disclosed record for a public snapshot."""

@dataclass(frozen=True)
class ClientViewSnapshot:
    revision: WorldRevision
    projection_hash: str
    records: tuple[ViewRecord, ...]

class PublicSnapshotSource(Protocol):
    def snapshot(self) -> ClientViewSnapshot: ...

@dataclass(frozen=True)
class ClientViewDiff:
    base_revision: WorldRevision
    receipt: CommitReceipt
    before_projection_hash: str
    after_projection_hash: str
    patches: tuple[ViewPatch, ...]

class WirePayload(FrozenPayload, ABC):
    """Registered adapter message, not renderer/domain state."""

@dataclass(frozen=True)
class WireEnvelope:
    protocol_major: int
    protocol_minor: int
    routing_epoch: str
    request_id: str
    message_schema: TypeKey
    payload: WirePayload

@dataclass(frozen=True)
class TransferManifest:
    transfer_id: str
    routing_epoch: str
    kind: Literal["view_diff", "view_snapshot"]
    revision: WorldRevision
    base_revision: WorldRevision | None
    raw_bytes: int
    chunk_count: int
    raw_sha256: str
    projection_hash: str

@dataclass(frozen=True)
class TransferChunk:
    transfer_id: str
    index: int
    raw_data: bytes

@dataclass(frozen=True)
class ViewAck:
    routing_epoch: str
    revision: WorldRevision
    projection_hash: str

@dataclass(frozen=True)
class PreparedDelivery:
    reservation_id: str
    manifest: TransferManifest

class WireCodec(Protocol):
    def decode(self, encoded: bytes) -> WireEnvelope: ...

    def encode(self, envelope: WireEnvelope) -> bytes: ...

class DeliveryPort(Protocol):
    def prepare(
        self, update: ClientViewDiff, snapshot: PublicSnapshotSource
    ) -> PreparedDelivery: ...

    def publish(self, prepared: PreparedDelivery) -> None: ...

    def release(self, prepared: PreparedDelivery) -> None: ...

    def acknowledge(self, ack: ViewAck) -> None: ...

ShutdownReason: TypeAlias = Literal[
    "normal", "client_lost", "brain_lost", "parent_lost", "timeout"
]

class ProcessSupervisor(Protocol):
    def start(self) -> None: ...

    def shutdown(self, reason: ShutdownReason) -> None: ...
```

WireCodec handles body bytes; separate framer applies u32 length. message_schema determines concrete payload dispatch and must equal payload.schema. TransferChunk bytes are base64 only in wire projection, indices0..chunk_count−1. Diff base_revision is required; snapshot base_revision=None means full replacement. DeliveryPort.prepare reserves/encodes before COMMIT; publish after commit uses the bounded private prepared bytes, never reruns state. Abort releases the reservation without delivery; reservation_id is adapter metadata outside CORE/RNG. Supervisor methods are effectful adapter boundaries, not engines. Their None return means a documented completed side effect or explicit exception, not an unimplemented successful stub.
Chosen: supervised separate Brain/client + local framed JSON + schema-derived public projections. Rejected: renderer-owned rules, remote/local server setup by player, raw full WorldState per turn, unbounded queues, numeric JSON precision assumptions and detached backend. Escape: substitute client/IPC/bundle/containment adapter after the same codec/replay/lifecycle conformance matrix.
Mapped: F-02/F-05/F-06/F-09/F-10; AP-01/AP-02/AP-05/AP-06/AP-08/AP-09; C-03/C-05/C-06.

## PLANNED Acceptance Examples

Synthetic v2 fixtures, no imported v1 mechanics or expected values.

| Case | Expected contract |
|---|---|
| Catalog120→200 continents,≥6MiB | Same code/registry; extra data/chunks; cold/warm loads yield same typed records/hash |
| Unknown field/duplicate ID/cyclic parent/float CORE | Explicit build/import rejection; no accepted package/state mutation |
| Cache eviction/missing package | Identical pinned reload / explicit missing-data failure, no provider call |
| Duration120seconds from tick10 | target130; exact2minutes; action once at130; no wall-time influence |
| Idle ticks10→40, first due event40 | Skip at most to39; execute40 in canonical phase/order; retain same event ID |
| Hidden autonomous owner without wake declaration | Boot/contract failure, not a silently frozen world |
| Passive10→12 vs10→11→12 | Entire Tier A fields/queues/cursors/remainders/IDs equal; protocol commits separate |
| Camera/FPS/cache changes | No A/CORE time change; C may differ |
| Crowd indices4000 vs4900 / vs5100 | B error900 passes1000 TARGET /1100 fails; A remains identical |
| Numeric value2^53+1 | Decimal string9007199254740993 round-trips exactly; numeric/exponent coercion rejected |
| Partial/oversized frame / unknown required version | Buffer within cap / reject before allocation / stop applying updates |
| Private memory changed, no visible field changed | Empty public patch + new receipt; no hidden memory disclosure |
| Missing chunk/wrong projection base | No partial application; pinned public snapshot resync |
| Slow client/duplicate/stale attachment | Bounded BUSY/one unacked update; same receipt; old epoch rejected |
| Client/Brain/launcher/Steam kill | No authoritative orphan≤5s; recover complete saved commit; never rerun uncertain action |
| Different Body/headless path | Same command trace CORE/protocol outcomes; no renderer types in Brain |

Verification plan: typed-source/schema/table conformance, numeric/UTF-8/error boundaries, catalog growth/cache/hash/reference validation, exact dense-vs-sparse full state and composition properties, B metrics/A-isolation, framed segmented projection round trips and pressure, packaged process-death/save-lock matrix. Actual runtime/type/property/pytest/replay/client/packaging/performance NOT_RUN.

## Completion / Next

A10–A12 designs/interfaces/alternatives/mappings specified. All numeric limits TARGET; resource/compatibility/lifecycle evidence UNVERIFIED. No production order READY; gameplay field/rule inventory and A13/A14 job/resource contracts remain prerequisites.
Record actual document checks in [BACKLOG](../BACKLOG.md)/[handoff](../SESSION_HANDOFF.md). Next: **RS-ARCH-002-B06 / BLOCK6 A13 observability/budgets, A14 AI Factory/artifact validation**. Stop after BLOCK5.

--- BLOCK 5/9 END. Enter "continue" for the next block. ---
