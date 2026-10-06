# BLOCK 6 — Observability, Budgets & AI Production Factory

Task: RS-ARCH-002-B06 | Date:2026-10-03 | Mode:DESIGN | Owner:GPT-6.1 Sol
Authority: [v2.6 prompt](../docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md), [MASTER](../docs/MASTER_GAME_ARCHITECTURE.md). Historical v1 governance is reference only.
Contracts extend [BLOCK2](BLOCK_02.md), [BLOCK3](BLOCK_03.md), [BLOCK4](BLOCK_04.md), [BLOCK5](BLOCK_05.md). Python below is interface specification, not production implementation.

## Cross-block Decisions

| Decision | Resolution / evidence |
|---|---|
| Counter units | A13 supersedes BLOCK1's provisional /turn row: simulation counters/cascade are per executed logical tick; normal command/job totals are separate. No limit resets inside a CASCADE wave |
| Allocation gate | Count all specified project-owned creation sites, not just proxy wrappers. Interpreter/SDK allocations remain profiler evidence; never claim exhaustive CPython allocation coverage |
| LOD resource isolation | Independent A/B work reservations; B sampling writes B deltas/cues only, no simulation facts/pending events. B cannot consume A's event allowance. Exact B default; approximation disabled pending A11 qualification |
| Long time advance | Normal command duration<=300 game seconds; longer requests use visible preparation. Exact canonical ticks or proven no-op spans; no elapsed-time approximation to meet a budget |
| Save/export bounds | A13 sets initial logical byte/work limits and separate memory TARGETS. Resource failure preserves old committed state/slot; no pruning CORE to fit |
| Factory | Small local job ledger + typed adapters + immutable manifests; no always-on workflow server/player dependency. Implementation Phase1+ |
| Ownership | Sol owns architecture/all coding/tests/audit/repair/integration; Astra only concrete blocker advice. Specialized generators are tool roles, not permission to launch agents |
| Approval | Technical validation, director approval, import and build verification are distinct. Approval binds reviewed hashes; changed inputs/outputs invalidate downstream acceptance |
| Runtime AI | Optional BYOK windows; zero provider calls during ordinary turns/replay. No mandatory paid relay; prebuilt/cached content supplies complete offline play |

## A13. Observability / Performance Budget

### A13.1 Measurement Boundary / Counters

Orchestration owns an injected observer, not WorldState. Engine.evaluate remains state/definitions/RNG-in -> frozen result-out. A wrapper records engine/node/tick/wave, deterministic costs and diagnostic timings; reducers record leaf writes; bus records produced facts; view factory records wrappers; delivery/save adapters record their own stages. Engines cannot read telemetry, wall clocks, OS load or profiler state. No event IDs, RNG addresses, scheduling or hash input depend on measurements.
Boundary errors: preserve the exception chain and explicit TurnRejected/TurnAborted/RECOVERING contract; log redacted failure code and stage. Contract-approved fallback carries Degradation through result/presentation/report. Observer I/O failure uses bounded local buffering plus explicit diagnostic failure; never hide gameplay failure or retry an already committed action. Run-local counters/observers reset for every fresh service context; none is a mutable module global.

| Counter | Exact counting rule / later gate8 |
|---|---|
| Engine calls | Each actual Engine.evaluate invocation, including no-op result and every CASCADE invocation; skipped inactive nodes do not count |
| State writes | Each proposed leaf-address assignment/deletion accepted by a reducer, including same-value/repeated writes; batch API must report leaves. Abort retains attempted-cost evidence |
| Events | Each produced simulation fact before routing/coalescing; pending insertion counted once, later delivery separate. Presentation cues have a separate count/cap |
| Owned allocations | One per constructed delta, fact/header/queued record, component/staging record, COW page, read wrapper, canonical runtime result/collection record; centrally instrumented construction sites and registered extensible payload constructors. Count replacements and discarded objects too |
| Proxy wrappers | Subset of owned allocations: new wrapper only; cache hit zero; reads/cache hit/miss separate diagnostics |
| Cascade depth | Maximum executed wave depth per logical tick; B03 bound8. Idle-span skip reports skipped ticks; cannot erase executed costs |

Owned-allocation coverage is a reviewed site inventory with independent constructor-path examples; adding a construction category extends the inventory before gate qualification. An execution-local standard Python profile hook counts registered constructor-code entries before initialization; non-constructor factories/COW sites charge their injected owner context explicitly. Orchestration supplies lane/tick/job attribution and restores the previous hook in finally; no mutable global accumulator or observer access from engines. Inheritance/factory paths count each created value once, not once per base initializer. Hook overhead is included in qualified timings; standard tools plus a small observer adapter, not a custom allocation checker/daemon. Ordinary Python temporary integers/strings, interpreter frames, serializer internals and external-library objects are outside this counter; tracemalloc/process meters measure their peaks separately. Gate8 must say **owned allocations**, not total interpreter allocations; constructor/factory-site coverage remains UNVERIFIED until independently exercised.

Initial reference-fixture ceilings, versioned TARGETS: per executed tick **each lane** A/B calls128, writes2048, owned allocations32768, proxy wrappers8192. Total simulation events<=512/tick and pending queue<=4096 retain B03 bounds, fully reserved for A; B event/pending allowance0. B writes B fields and optional cues only, driven by B05's CORE sample cursors/derived due index; it cannot emit simulation facts. No B producer can borrow A work/event capacity; aggregate call/write/allocation/wrapper costs are reported in addition to lanes. CASCADE<=8 per logical tick remains unchanged. Reference B fixtures require exact implementations; unavailable B -> profile UNVERIFIED, no silent approximation. These are prototype envelopes, not measured full-world capacity. Changes require versioned fixture/rules/profile and stated behavior/performance justification; never auto-raise a failed baseline.

Normal command and long-job deterministic cost ceiling: executed ticks86400, calls1000000, writes1000000, A produced facts262144/B0, owned allocations8388608, wrappers2097152 **per lane per job**. Same limits for normal and visible jobs; duration cap alone distinguishes normal requests. Tick ceilings count executed canonical ticks, not proven no-op elapsed spans. Reservation/accounting checks happen before publishing candidate effects. Exhaustion -> explicit RESOURCE_LIMIT, discard complete candidate; no partial COMMIT, skipped A ticks, removed A events or truncated writes. Resource-rejected requests have no simulated result; full A composition is required for successfully completed requests with equivalent accepted inputs, regardless of grouping. Service/control progress TARGET<=100ms between pumps; no background authoritative ticking.

Hard deterministic gates compare counts against fixture-profile ceilings **and recorded reference counts**; an increase beyond a profile's reviewed tolerance fails, even below the broad ceiling. Initial tolerance0% until a reasoned replacement baseline is accepted. CI must assert real output/state invariants as well as costs; an engine returning nothing cannot pass by using fewer operations. Logical caps are admission/execution safety conditions; wall-time and MB are never hard commit-CI gates.

### A13.2 Environments / TARGET–ESTIMATE–MEASURED–UNVERIFIED

| Metric / environment | TARGET | ESTIMATE | MEASURED / status |
|---|---|---|---|
| DEV-A | Lenovo LOQ-E15.6 ARP10e; Ryzen7 7735HS; RTX4050 Laptop6GB; RAM16GB DDR5; NVMe512GB; temporary Windows11 | Hardware supplied by director; no speed estimate | No workload execution; UNVERIFIED |
| DEV-B logic | Actual 4-core CPU/8GB/iGPU; full suite, same versions/fixtures | Device CPU/GPU/storage/OS not supplied | Device qualification UNVERIFIED |
| MIN-SPEC release | Actual 4-core CPU/8GB/iGPU; bundled Brain + lowest-profile graphical client | Exact CPU/iGPU/storage/model selection pending | Device/game qualification UNVERIFIED |
| Authoritative latency | MIN-SPEC p95<=100ms, p99<=250ms; validate -> projection reservation -> durable COMMIT, includes save; excludes provider/render/ACK | No runnable v2; unavailable | UNVERIFIED |
| Runtime memory | Brain<=512MiB; client<=1536MiB; combined<=2048MiB=2147.484MB private commit; launcher counted in combined limit | No object/layout/import profile; unavailable | UNVERIFIED |
| Rendering | Lowest profile1280x720, p95 frame<=33.3ms; representative modular combat/camera scene | Exact iGPU/scene not supplied | UNVERIFIED |
| Proxy | Turn CPU overhead<=10%; observed recursive proxy enabled vs equivalent immutable reference reader | No runnable proxy; unavailable | UNVERIFIED |
| DEV-A tools/job | Combined process-tree private commit<=12GB; local generation VRAM<=4.5GB; regenerable cache<=30GB | No tested provider/model fit; unavailable | UNVERIFIED |
| SD image profile | SD1.5 + LoRA + ADetailer; initial batch1,512x512; record all hashes/settings; approve larger profile only after measurement | Even batch1 fit unknown | UNVERIFIED |
| Long-job memory | Staging Python allocation peak<=128MiB, within Brain512MiB; no growing per-tick history | No staging implementation; unavailable | UNVERIFIED |
| CI trend | Later11 commit gates<=60s total; local Ruff+core replay<=20s; mutation/report drift async | Toolset/pipeline not configured | UNVERIFIED |
| Lifecycle | Heartbeat1s; timeout3s; process cleanup<=5s | Native deployment adapter deferred | UNVERIFIED |
| Runtime generation | Per-request timeout30s, bounded window wall-time300s; UI progress/defer; no turn-budget inclusion | Provider/model/quota/average calls unknown | UNVERIFIED |

GB/MB are decimal; GiB/MiB binary. CPU core count alone does not define a reproducible MIN-SPEC machine. Record exact model, cores/logical threads, RAM, iGPU/driver, storage/free space, OS/build, power mode/plugged state, runtime/client versions, content/build/fixture hashes, graphics settings and background processes. Actual laptop results qualify development only; emulated/throttled DEV-A is diagnostic, not MIN-SPEC certification. Windows release/device checks remain required at deployment; no OS-specific implementation now.

### A13.3 Exact Benchmark Plan / Pass–Fail

Phase1 PLANNED harness through ordinary pytest/replay + standard profilers; no fifth Phase0 implementation. Stable trace IDs/immutable fixture and build hashes recorded. Synthetic v2 inputs and independently calculated expected boundaries; no v1 formulas/test oracles. If a required system/fixture/device is missing, result UNVERIFIED, not a dummy-skeleton substitute.

| Profile | Fixed workload / repetitions / scope |
|---|---|
| PERF-TURN-01 | seed0x525356320001; clock0; six linked locationsL0–L5;64 near NPCs +1000 remote actors;512 initially pending A facts due ticks1..512 in stable ID order.100 warm-up +1000 measured one-second Wait commands, fresh copy per run,5 runs. Near wakes every1s; remote wakes every300s with offset=index mod300. Include real memory/reducers/queue/SQLite/public preparation; exact B profile pinned |
| PERF-CATCHUP-01 | Same start + passive86400-second advance, followed by re-entry; compare dense ticks vs proven-sparse path and splits at seconds60/300/43200. Fresh services5runs; compare entire A state/queues/cursors/remainders/event IDs. Full CORE equality for identical B profile. Record cumulative counters/peak staged memory/yield gaps; no normal-turn100ms claim |
| PERF-CATALOG-01 | A10 synthetic catalog>=6MiB;120 then200 continents; same executable.5 cold +5 warm loads; access sorted IDs through32MiB decoded cache, force eviction/reload; identical typed records/pins |
| PERF-PROXY-01 | PERF-TURN trace/expected outputs with recursive observed proxy vs an equivalent immutable snapshot/reference reader; interleave A/B runs5pairs. Same core hashes/counters, proxy wraps/reads reported; compare process CPU total, not SQLite wall-time noise. Baseline never ships as an unsafe mutable view |
| PERF-CLIENT-01 | After client scene exists:1280x720 lowest profile;64 visible modular actors, camera one360-degree rotation per60s, scripted combat/UI/audio.30s warm-up +120s capture,5runs; bind exact scene/assets/graphics/driver hashes |
| PERF-FACTORY-01 | Actual DEV-A, one job at a time: SD profile, one representative3D conversion, animation import, audio import, content compile.5 measured jobs per qualified profile; other heavy tools unloaded; record RAM/VRAM/cache/time/license/import result |

1000 commands run after100 warm-up, so measured ticks101..1100; snapshot template contains pending facts1..512. Nearest-rank percentile: sorted samples[index ceil(p*n)-1]; never percentile-of-percentiles. Report per-run p50/p95/p99/max and combined distribution, peaks and attempted/committed/aborted counts. Capture full fixture state/trace before timing. Real benchmark command is written in the implementation work order after the harness exists; now **command NOT_AVAILABLE / result UNVERIFIED**. Do not invent a runnable command.

Hard CI: any counter-limit/reference-count violation, hash/invariant mismatch or incomplete allocation coverage fails gate8/appropriate existing test gate. Soft CI: ms/MB regressions create a bottleneck report, never flaky timing failure. Device/release qualification: each run's p95/p99 and memory/frame/proxy TARGET must pass; failure blocks qualification and triggers optimization/profile re-evaluation, not CORE simplification. PERF-CATCHUP memory/yield TARGETs qualify separately; total latency recorded without invented speed estimate.

Use Python cProfile for call attribution, tracemalloc for traced Python allocation peaks, and platform process/GPU meters for full private commit/VRAM. Detailed-profiler diagnostic run is separate from latency run with mandatory cost counters retained; cProfile and constructor hooks need a qualified combined dispatcher or separate runs, never one silently replacing the other. Memory sampling interval100ms plus process/GPU high-water values where supported. Unavailable high-water evidence is incomplete/UNVERIFIED, not proof of peak fit. [Python profiling](https://docs.python.org/3.13/library/profile.html), [tracemalloc](https://docs.python.org/3.13/library/tracemalloc.html), [profile hook](https://docs.python.org/3.13/library/sys.html#sys.setprofile) describe standard tools; they do not prove project-site coverage/full process/GPU memory.
Bottleneck report: environment/commands/hashes; each engine/node calls/writes/events/allocations, CPU/wall inclusive/exclusive attribution; per-stage admission/ticks/hash/projection/save/PRESENT; p95/p99/peaks; queue/cache/LOD sizes; top5 cost contributors; failures and next bounded optimization. CPU sums do not explain all I/O wall time. Store redacted derived output under PLANNED `reports/performance/`; B2 integrates existing evidence, no new checker/report subsystem here.

### A13.4 Memory / Storage Backpressure

| Resource | Initial bounded policy / TARGET |
|---|---|
| Runtime caches/output | A10 decoded definitions32MiB; A12 required prepared delivery32MiB raw + transient wire2MiB; all within Brain512MiB, not additional allowances. One unacked commit, eight queued commands; reliable diff never truncated |
| Staging | Deterministic canonical retained staging payload<=64MiB total, reserved A48MiB/B16MiB; B cannot borrow A. Count replacing/removing bytes accurately, separate from128MiB traced allocation peak TARGET. Retain latest changed leaves + required causal queue, not every obsolete per-tick delta |
| Save/export | Live SQLite payload<=512MiB initial profile; checkpoint validation reads bounded batches<=1MiB; one export/migration job/world; temp + active slot + two retained recovery generations <=4x512MiB=2GiB/slot. Reserve additional journal/work space separately; check actual free space before writes |
| Save operation | At most1 active job/world; cancel before publication preserves old slot; insufficient disk/unsupported size explicit error. Resource counters do not imply a5s backup guarantee. B04 migration fixtures/atomic recovery remain required |
| Accepted runtime data | Optional accepted package<=32MiB raw; one provider response<=1MiB; one active candidate import. Artwork/audio binaries remain shipped asset pool, not save copies |
| Factory scratch | Regenerable cache<=30GB decimal; LRU eviction only unpinned scratch; approved originals/manifests/dependencies never evicted. Initial free-space reserve32GiB after admitting job plus declared worst-case temporary/output bytes; inadequate disk -> defer |
| Heavy production | Concurrency1 local image/LLM/3D-processing/editor-heavy task; reservations include launcher's/tool's child processes. Split/unload/smaller validated profile or external paid production if over12GB RAM/4.5GB VRAM |

Retained-byte limits use canonical payload size, not guessed Python sizeof; allocation profilers qualify actual overhead. Serialization work must be incremental/accounted, not repeated full-world deep copy. Failure before COMMIT aborts candidate; commit uncertainty follows A9 recovery. No approved artifact deletion, save truncation or gameplay-quality reduction to satisfy hardware limits. Save size is an initial supported-envelope target, not proof that all MASTER scales fit; grow only after real memory/storage/lifecycle evidence.

### A13.5 Interface

Uses shared BLOCK2–5 types. Diagnostics remain frozen observer outputs outside CORE.

```python
CostLane: TypeAlias = Literal["A", "B"]

@dataclass(frozen=True)
class WorkCounts:
    engine_calls: int
    leaf_writes: int
    simulation_events: int
    owned_allocations: int
    proxy_wrappers: int
    executed_ticks: int
    skipped_ticks: int
    cascade_depth: int

@dataclass(frozen=True)
class WorkLimit:
    lane: CostLane
    scope: Literal["tick", "job"]
    ceiling: WorkCounts
    retained_bytes: int
    profile_hash: str

@dataclass(frozen=True)
class NodeObservation:
    node: NodeKey
    logical_tick: Tick
    wave: int
    lane: CostLane
    counts: WorkCounts
    cpu_ns: int
    wall_ns: int
    failure: Failure | None
    degraded: tuple[Degradation, ...]

class RuntimeObserver(Protocol):
    def record(self, observation: NodeObservation) -> None: ...

class WorkBudget(Protocol):
    def charge(self, lane: CostLane, tick: Tick, counts: WorkCounts) -> None: ...

    def reserve_retained_bytes(self, lane: CostLane, amount: int) -> None: ...

    def release_retained_bytes(self, lane: CostLane, amount: int) -> None: ...
```

WorkBudget is orchestration-owned, absent from EngineInvocation; nonnegative additive counts except depth=max, retained bytes current/peak. skipped_ticks is diagnostic, not a resource ceiling; limit field0 means unconstrained only for that diagnostic field. Job starts/reset once per submission; tick resets only at canonical boundary. charge checks both tick/job counters atomically before applying the associated candidate effect, raises typed RESOURCE_LIMIT on exhaustion. Observer decorator calls Engine.evaluate once, records result/error, returns same EngineResult or propagates failure; approved fallback is explicit, never manufactured empty success. Constructor-hook errors/missing instrumentation abort the candidate as OBSERVABILITY_CONTRACT; restore hook in finally and verify hook continuity at barriers because Python unsets a failing profile hook. Core execution stays on one thread; any future worker path requires separate accounting qualification. Optional diagnostic-log I/O failure differs from lost required cost evidence.

AR-004 attribution uses B05 NodeActivation.lane validated at boot. Tick/job engine costs and state writes use that lane; clock/queue/admission/commit and other required shared work charge A, B-only staging work charges B. B cannot relabel a shared A allocation or reset A counters. Cascade wave index0..7 corresponds to executed-depth1..8; outside CASCADE depth0. AR-006 fact/diff digest accumulators are bounded candidate metadata: incremental hashing avoids a full per-tick fact-history list; any retained fact/witness/output bytes count toward the existing lane/job/staging limits. Overflow aborts before COMMIT, never drops semantic facts to fit. Small replay fixture witnesses are developer-test data, not a required full-world copy in every production turn.
Chosen: deterministic harness counters + standard profiling + device qualification. Rejected: ms CI gate, wrappers called total allocations, telemetry in CORE, FPS-driven LOD, exhaustive custom profiler/checker. Escape: replace profiler/meters without changing cost schema, CORE or replay.
Mapped: F-03/F-04/F-05/F-08/F-09/F-10; AP-01/AP-02/AP-04/AP-05/AP-06/AP-07/AP-08/AP-10/AP-11; C-01/C-03/C-04/C-05.

## A14. AI Production Factory / Optional Runtime Generation

### A14.1 Roles / Flow / Scope

`DirectorBrief -> ProductionPlan -> SpecializedJobs -> ArtifactValidation -> HumanApproval -> Import/Compile -> Tests -> Build`
Director supplies gameplay/style constraints, criteria, direction/priorities and acceptance/rejection. Sol turns them into bounded orders and adapters; tools generate candidates, validators check, director reviews concrete results. Manual painting/modeling/keyframing/composition/bulk writing is not the baseline.

| Role | Typed output / responsibility |
|---|---|
| Sol | All architecture/code/tests/repair/integration/technical review; [coding order](../docs/prompts/SOL_CODING_WORK_ORDER.md), actual diff/live-path/evidence before DONE; self-review is not independent review |
| Astra | Advice for named unresolved blocker + evidence/constraints; Sol validates advice; no mandatory handoff/implementation ownership |
| Structured content | New-schema NPC/traits/dialogue/quest/item/faction/location/lore/encounter/world packages; no executable expressions/old balance/state bindings |
|2D FIXED | SD1.5 + project LoRA + ADetailer; identity/style brief -> pre-generated portraits/illustrations -> technical/style approval; tool/model versions and weights hashes pinned |
|3D | Replaceable paid adapter; bases/modular equipment/environment/props; AI/service optimization/rigging where required; neutral export retained |
| Animation | Skeleton-first generated/assisted clips; mapping/root motion/loops/events/weapon alignment; pre-generated |
| Audio | Replaceable paid adapter/library for BGM/SFX/gibberish/short voice; tags/library + runtime selection/crossfade/limited variations; no mandatory full-sentence live TTS |
| QA | Sol + deterministic schema/domain/media/import/build validators; explicit labeled style/playtest evaluation; optional independent reviewer only when requested |
| Director | Approves hash-bound candidates/profile/style/license scope; reviews visuals/audio/gameplay, sets priorities; no default manual production obligation |

Use a local serialized CLI/job ledger with explicit dependencies; immutable revisions stored in project-owned Factory workspace, adapters own side effects. PLANNED roots: `production/briefs/`, `production/manifests/`, `production/candidates/`, `assets/approved/`, `data/approved/`, `reports/factory/`. No folders/tools/jobs created in DESIGN. Long-term report aggregates ledger/validator/import/build output in B2. Implementation follows manifest/content foundations -> representative import per modality -> approved client profile -> bulk jobs. Bulk production before stable importer/client/skeleton/style contracts is prohibited by the product progression, not solved by detailed prompting.

### A14.2 Artifact Contract / State Machine

ArtifactManifest schema is generated under A10, recursively frozen, strict/closed and versioned. Required fields in interface below; important modality-specific settings are a registered frozen ProductionSpec payload, never an untyped generic dict. Exact brief/spec bytes retained by hash; inputs pin IDs+hashes; source/output/imported bytes are immutable by revision. Code artifacts pin scoped repository diff/build/order/test evidence without pretending a source file's existence proves correctness.

| Transition | Mandatory condition / failure |
|---|---|
| PLANNED -> GENERATED | Frozen brief/spec/criteria/profile/input pins + bounded job/resource/spend plan; complete output hashes; partial download stays RETRY/NEEDS_REVIEW |
| GENERATED -> VALIDATED | All required technical/domain/license-completeness checks PASS with validator versions/results/output hashes; failure REJECTED or corrected new revision |
| VALIDATED -> APPROVED | Explicit director decision on reviewed candidate/spec/dependency/license hashes and permitted import/build scope; no automatic approval from generation or validator success |
| APPROVED -> IMPORTED | Approval current; confined collision-free destination; pinned deterministic importer/profile; validate converted outputs, publish atomically; failed import preserves prior accepted artifact |
| IMPORTED -> BUILD_VERIFIED | Named build ID/hash, integration/tests/client import pass; runtime referents reachable; complete evidence. Code tests/coverage/replay according to phase, not arbitrary full-stack claim |
| Any -> REJECTED | Explicit reason/reviewer; retain evidence; never imported or referenced in release |
| Failed attempt -> RETRY | Retry permitted by remaining job/call/spend bounds; corrected candidate becomes new manifest revision, never overwrites approved bytes |
| Any unresolved -> NEEDS_REVIEW | Missing terms/provider version, uncertain billing, ambiguous style/skeleton or build result; explicit blocker, no false completion |

Invalidation is graph-based: changed source spec, settings, dependencies, output/license/importer/profile hashes revoke affected approval/import/build associations. Unchanged original remains retained; new bytes get new revision. Validators are pure on frozen inputs where feasible; external generator may be nondeterministic, but its accepted outputs are pinned. Build determinism means reusing accepted inputs/importer gives expected outputs; never promise identical AI generation from the same prompt.
Director can explicitly approve a finite batch/profile scope with named IDs/hash set and criteria; technical automation may not invent blanket approval. Approval does not waive required validation, compatibility or license terms. Runtime player acceptance uses separate policy below, not developer artifact approval.

### A14.3 Validation / Import Profiles / Vendor Escape

ValidationResult contains check ID, PASS/FAIL/UNVERIFIED, validator/version, subject hash and evidence reference. **Required UNVERIFIED blocks VALIDATED.** Numerical thresholds live in a versioned approved modality profile before a job becomes READY; missing polygon/material/loudness/rig budget means no job launch. A13 resource limits do not substitute for asset quality checks.

| Class | Machine checks / human criterion | Retained handoff / replacement |
|---|---|---|
| Code | Scoped diff/path/wiring; lint/types/phase-appropriate actual tests + replay evidence; product behavior review | Plain source/diff/order + lock/build/test pins; no provider SDK in engine |
| Content | A10 closed schema/refs/unique IDs/traits/ranges/new mechanics; forbidden executables, unresolved references, old stats rejected; world/style review | Canonical typed JSON + schema/catalog/input pins; regenerate with another structured provider |
| Image | Decodable approved format/profile dimensions, alpha/color-space/size, output hash, character/spec/SD/LoRA/ADetailer pins; identity/style review | Lossless PNG originals + settings/spec/pins; replace adapter preserving approved files; fixed production stack requires director change |
|3D | Profile polygon/submesh/material/texture maxima; declared units/scale/pivots/normals, skeleton+collision, no missing resources; import preview | Self-contained neutral mesh/material/texture/rig export (provisional glTF/GLB import profile); keep accepted original; adapter/converter switch after conformance |
| Animation | Exact skeleton mapping, clip bounds/root-motion policy, loops, event timing, hand/weapon alignment, import; motion review | Clip + skeleton/event metadata, neutral export or documented conversion; baked motion avoids provider-only playback |
| Audio | Decode/channel/sample rate/format/duration/loudness/true-peak limits and loop markers in profile; tags/import/crossfade/variation; listening review | Lossless WAV source + loop/tag/level metadata; derived client codec through pinned importer; library usable without generator |
| All | Naming/normalized confined paths, case-insensitive collisions, hashes/dependency completeness, license/provenance, import/build result | Immutable original + manifest + validation + approval; no hosted URL as only copy |

Technical validators use standard codec/client import tools and typed schemas; no bespoke global asset god system. Automatic fixes (conversion/retopo/level adjustment) create derived candidates with dependency hashes and must be revalidated/reviewed. Style cannot be certified solely by dimensions/tags; human visual/audio acceptance remains explicit. License completeness includes source URL/reference, provider terms version/capture, rights holder/license identifier, permitted redistribution/modification/attribution and required credits; unknown or incompatible rights -> NEEDS_REVIEW/REJECTED. Provider terms/quotas are externally checked at implementation/release, currently UNVERIFIED. No recommendation/selection of an unverified paid provider here.
Sandbox adapters/paths: allowlisted roots/relative targets, reject traversal/absolute external targets/case collisions/symlink escapes; download limits/hash before decode; no generated scripts executed by content importer. API keys in credential store/environment accessed only by reviewed adapters, never manifests/logs/saves/replay. Redact prompts/IDs where sensitive; retain spec reference for reproducibility without leaking credentials. Project paths/neutral-format versions/validator packages are preflight choices, not implemented guarantees.

### A14.4 Optional Runtime Windows / Quota / Acceptance

Runtime provider interface separate from production billing/assets; candidates: Gemini/Claude/Ollama/other suitable adapter, not mandatory provider list. Ordinary turn/replay provider calls **0**. Live generation disabled by default until explicitly enabled; missing/offline/failed provider uses approved bundled/cached complete content. Heavy local inference optional, serialized and hardware-qualified; MIN-SPEC never depends on it.

| Window | Maximum jobs | Maximum request attempts including retries | Maximum reserved tokens |
|---|---:|---:|---:|
| New game/world package |8|24|245760|
| Chapter transition |4|12|122880|
| Loading/preparation |1|3|30720|
| Explicit large-content request |8|24|245760|

Initial profile limits, not provider capacity promises. One active window; one in-flight request; per job<=3 attempts (initial +2 retries),<=8192 input/2048 output tokens/attempt from A8, total10240. Shared window ledger cannot reset by retry/reopen; new window requires an explicit generation trigger/ID. Every network attempt reserves call+worst-case tokens before dispatch; unconfirmed cost remains reserved, including retries/429/timeouts unless reliable provider evidence reconciles it. Input token count requires selected actual tokenizer; otherwise preflight budget UNVERIFIED and no unbounded dispatch.
One job emits one<=1MiB closed structured response into typed candidate records; aggregate package<=32MiB. Context frozen by source revision/CORE hash/schema/prompt/policy/provider/model pins; authority-changing package application requires unchanged admitted context or explicit replan. Accepted cache key includes those pins/spec/dependencies; cache hit never regenerates by accident.

| Service condition | Deterministic data / explicit service result |
|---|---|
| Valid candidate | Shape + domain references/constraints + safety/content criteria; player preview/accept or explicitly enabled finite auto-accept policy. Freeze/hash + persist package before a typed ingestion command binds it at COMMIT |
| Player declines / stale context | REJECTED or DEFERRED, no CORE mutation; retain redacted diagnostic candidate record; replan with new pins, not splice live text into state |
|429/transient retryable error | Respect provider Retry-After; otherwise exponential1s,2s retry delays; at most2 retries, maximum queued wait60s and request30s; beyond remaining window300s -> DEFERRED/degraded |
| Quota exhausted / unsupported required accounting | DEFERRED/degraded or FALLBACK to existing accepted package; expose reason/retry eligibility; never fabricate generated data |
| Timeout/uncertain billed result | Reconcile known operation ID using provider support; unsupported reconciliation -> NEEDS_REVIEW/defer, no blind resubmission or assumed idempotency |
| Invalid output | REJECTED/degraded; optional repair uses remaining attempts and full revalidation, not unlimited second job/window |
| Offline/no key/local model over budget | Complete prebuilt/cached gameplay, FALLBACK/degraded; no live image/3D/audio calls |

Limiter per provider/model/account scope: token bucket RPM (capacity/current refill), rolling/reserved TPM and token budget, RPD/reset clock and any provider concurrency cap where applicable; persist accounting across service restart. Use provider-specific documented enforcement windows/reset semantics, not assume midnight or unlimited free tier. Transport time/limits are adapter state outside deterministic simulation. Unknown quota cannot be used in a numeric capacity promise; require configured/verified quota or explicit conservative user limit labeled UNVERIFIED. Current provider/model/tier quotas and average usage all **UNVERIFIED**.
Capacity table distinguishes **configured maximum3 calls/job (TARGET)** from average calls/job, average input/output tokens/job and calls/window (**not estimated/measured yet**). Later record successful/rejected/retried/cached jobs separately: mean actual attempts/jobs and actual tokens/jobs, plus distribution and worst-case reservation. Available capacity=min(remaining verified request quota / observed average attempts, remaining verified token quota / observed average tokens, explicit job/window bounds), rounded down with safety reserve; obey RPM/TPM scheduling too. Average-based projection is labeled ESTIMATE, never guaranteed. Dispatch admission always uses worst-case reservation, so a favorable average cannot overrun quota.
Offline eval mode uses frozen provider-response bytes and deterministic schema/rule expectations; provider mocked only in adapter tests. Live eval explicit opt-in + declared spend/quota cap, separate production/developer vs player ledger; never silently use player's key/quota. Track acceptance/repair/rejection/token usage/relevance/style/invariant violations; no claimed measured quality until labeled set/results exist. Replay reads accepted package pins only; no API key/credentials/provider session persisted in WorldState.

### A14.5 Interface

Production and runtime contracts deliberately distinct; all fields deeply immutable/validated through A10. Existing FrozenPayload registry enables modality specs without a growing central union.

```python
ArtifactState: TypeAlias = Literal[
    "PLANNED", "GENERATED", "VALIDATED", "APPROVED", "IMPORTED",
    "BUILD_VERIFIED", "REJECTED", "RETRY", "NEEDS_REVIEW"
]

class ProductionSpec(FrozenPayload, ABC):
    """Concrete modality schema; prompt/settings/criteria/profile pins."""

@dataclass(frozen=True)
class ArtifactInput:
    artifact_id: str
    revision: int
    manifest_hash: str

@dataclass(frozen=True)
class ArtifactFile:
    relative_path: str
    sha256: str
    byte_size: int

@dataclass(frozen=True)
class ToolProvenance:
    provider: str
    tool: str
    model: str
    version: str
    weights_hashes: tuple[str, ...]
    request_reference: str | None

@dataclass(frozen=True)
class LicenseProvenance:
    identifier: str
    source_reference: str
    terms_capture_hash: str
    rights_holder: str
    redistribution: bool
    modification: bool
    required_attribution: tuple[str, ...]

@dataclass(frozen=True)
class ValidationResult:
    check_id: str
    status: Literal["PASS", "FAIL", "UNVERIFIED"]
    validator_version: str
    subject_hash: str
    evidence_reference: str

@dataclass(frozen=True)
class ArtifactApproval:
    status: Literal["PENDING", "APPROVED", "REJECTED", "INVALIDATED"]
    reviewed_hash: str
    director_decision_reference: str | None
    scope_reference: str

@dataclass(frozen=True)
class ArtifactManifest:
    artifact_id: str
    revision: int
    category: str
    schema: TypeKey
    state: ArtifactState
    brief_id: str
    source_spec_hash: str
    spec: ProductionSpec
    provenance: ToolProvenance
    inputs: tuple[ArtifactInput, ...]
    outputs: tuple[ArtifactFile, ...]
    licenses: tuple[LicenseProvenance, ...]
    validation: tuple[ValidationResult, ...]
    approval: ArtifactApproval
    import_target: str
    import_type: TypeKey
    importer_version: str
    imported_outputs: tuple[ArtifactFile, ...]
    build_id: str | None
    build_hash: str | None
    failure: Failure | None

@dataclass(frozen=True)
class ProductionJob:
    job_id: str
    order_reference: str
    manifest: ArtifactManifest
    maximum_attempts: int
    maximum_spend_minor_units: int
    currency: str
    resource_profile_hash: str

class ArtifactValidator(Protocol):
    def validate(self, candidate: ArtifactManifest) -> tuple[ValidationResult, ...]: ...

class ProductionAdapter(Protocol):
    def generate(self, job: ProductionJob) -> ArtifactManifest: ...

class ArtifactImporter(Protocol):
    def import_approved(self, artifact: ArtifactManifest) -> ArtifactManifest: ...

@dataclass(frozen=True)
class GenerationBudget:
    maximum_jobs: int
    maximum_attempts: int
    maximum_input_tokens_per_attempt: int
    maximum_output_tokens_per_attempt: int
    maximum_reserved_tokens: int

@dataclass(frozen=True)
class RuntimeGenerationJob:
    window_id: str
    job_id: str
    trigger: Literal["new_game", "chapter", "preparation", "large_content"]
    context: ContextBundle
    response_schema: TypeKey
    spec_hash: str
    budget: GenerationBudget

@dataclass(frozen=True)
class CandidateRecords:
    records: tuple[ContentRecord, ...]
    response_hash: str
    input_tokens: int | None
    output_tokens: int | None

@dataclass(frozen=True)
class GenerationResult:
    job_id: str
    status: Literal[
        "CANDIDATE", "ACCEPTED", "REJECTED", "DEFERRED",
        "FALLBACK", "NEEDS_REVIEW"
    ]
    candidate: CandidateRecords | None
    accepted_package: PackagePin | None
    failure: Failure | None
    degraded: tuple[Degradation, ...]
    charged_attempts: int
    reserved_tokens: int

class RuntimeProvider(Protocol):
    def generate_candidate(self, job: RuntimeGenerationJob) -> GenerationResult: ...
```

ProductionAdapter returns GENERATED or explicit failure-state manifest; it cannot approve/import/build its own output. No-content/model field uses explicit not-applicable value with justification; unknown provider version/terms cannot pretend to be pinned. ArtifactValidator returns required check evidence; ledger derives VALIDATED only when all required checks PASS. Importer verifies approval/bound hashes and returns IMPORTED only after atomic verified import; build verifier is separate ordinary build/test runner.
RuntimeProvider may return CANDIDATE/failure only; ACCEPTED/FALLBACK produced by separate acceptance/cache service after persistence and policy. CandidateRecords are immutable typed but not yet authority-approved. ACCEPTED requires accepted_package and persisted bytes; FALLBACK requires a previously accepted pin plus degraded reason; rejection/defer has no usable candidate/package; NEEDS_REVIEW may retain candidate for review but cannot ingest. Accepted pins use B03 PackagePin, bind into A9 durable package state through normal Brain ingestion; no provider object or wall-time field in engines. Secrets/SDK objects/raw JSON stay adapter-only.
Chosen: local typed Factory ledger, hash-bound validation/approval/import/build and optional bounded BYOK service. Rejected: single omnipotent agent workflow, generation-as-DONE, provider SDKs in engines, live text mutations, per-turn inference, mandatory paid relay, fixed free-play quotas, mandatory manual art production. Escape: replace provider/queue/media converter through pinned handoff/profile and existing conformance checks; retain accepted neutral artifacts/offline packages.
Mapped: F-02/F-04/F-05/F-06/F-07/F-08/F-09/F-10; AP-01/AP-02/AP-03/AP-04/AP-05/AP-06/AP-07/AP-08/AP-09/AP-10/AP-11; C-01/C-02/C-03/C-04/C-05.

## PLANNED Acceptance Examples

| Case | Expected evidence / result |
|---|---|
| Owned allocation32768 vs32769/tick/lane | Boundary passes/fails cost gate; proxy wrappers subset separately; independently verified constructor coverage |
| CASCADE/new tick | Wave cannot reset tick costs; next tick resets tick scope only, job scope accumulates |
| Profiler off/on / B stress / cache eviction | Same A state/queue/RNG/event IDs; no measurements in CORE; B separate reservation |
| Tick/job/staging cap exceeded | RESOURCE_LIMIT with attempted costs; old revision/save intact; no dropped A consequence |
| Latency300ms with valid counters | Soft CI regression report; fails250ms p99 device qualification, not hard timing CI |
| No MIN-SPEC/proxy/job executable | Actual remains UNVERIFIED; no fake percentile/MB/model-fit result |
| Output exists but checks/approval missing | GENERATED only; import rejected; cannot claim BUILD_VERIFIED |
| Dependency/output/terms hash changes | Affected approval/import/build invalidated; old accepted bytes retained |
| Case/path collision or incomplete rights | Explicit rejection/review; no overwrite/import/license assumption |
| SD/editor heavy jobs collide | Local reservation queues one; measured RAM/VRAM profile required before bulk |
| Job uses3 attempts in world window | Charged3 and <=30720 reserved tokens; eight jobs cap24/245760; no retry reset |
|429/timeout/quota/invalid data | Bounded retry/defer/review or accepted fallback + degraded; no fabricated data/spend/result |
| Runtime ACCEPTED before durable package | Rejected service transition; cannot bind unavailable package into CORE |
| Live eval disabled / offline replay |0 provider calls, same pinned CORE hashes; no player quota usage |
| Adapter replacement | Frozen accepted artifacts/packages stay usable; new output requires validation/approval/import conformance |

## Completion / Next

A13–A14 designs/interfaces/alternatives/mappings specified; counter units/reservations and initial save/job bounds explicit. All speed/memory/model-fit/provider-quota/quality results UNVERIFIED; no defensible empirical ESTIMATE or MEASURED result. Modality profiles/provider compatibility/site coverage/reference baselines need concrete Phase1 orders and evidence before implementation READY.
Document checks recorded in [BACKLOG](../BACKLOG.md)/[handoff](../SESSION_HANDOFF.md); no production code/tests/jobs/assets generated. Custom checkers planned2/max3/current0; Phase0 exactly4; later commit gates11; no new governance policy/report tool. Next **RS-ARCH-002-B07 / BLOCK7 B0 layers, B1 rule residency, B2 evidence reports**. Stop after BLOCK6.

--- BLOCK 6/9 END. Enter "continue" for the next block. ---
