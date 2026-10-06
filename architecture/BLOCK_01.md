# BLOCK 1 — Runtime & Production Architecture

Date: 2026-10-02 | Task: RS-ARCH-001 | Owner: GPT-6.1 Sol | Mode: DESIGN
Format: prompt **AI Documentation Format**. English conversion preserves decisions/contracts/status.

Status: document self-reviewed; no production code/tests/CI/final assets. Independent review, compatibility, benchmarks, product approval, and final technology lock-in remain UNVERIFIED.

## 0. Authority & Fixed Requirements

Authority: latest director instruction → [v2.6 engineering prompt](../docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md) → [MASTER product spec](../docs/MASTER_GAME_ARCHITECTURE.md) → [historical v1 governance](../docs/reference/AGENTS_v1.md). Primary documents were read completely in the required order.

- Product: Korean HD-2D/2.5D turn RPG; modular 3D/pixel-toon visuals; required 360° camera; keyboard/gamepad/UI.
- Preserve procedural world, combat/survival/environment, NPC autonomy/memory/social systems, neglected quests, delayed causality. Capabilities need not be separate engines.
- Sol owns all architecture/coding/tests/repair/integration/review. Astra: unresolved-blocker advice only. Documents do not change model selection or launch agents.
- Python Brain owns authoritative WorldState; only COMMIT mutates it. Client/generative AI cannot decide truth.
- No mandatory per-turn LLM. Pre-generate images/3D/audio. Optional runtime LLM: BYOK, explicit windows, validated structured data.
- v1 reuse: curated descriptive content only; no code/formulas/balance/schema/test oracles.
- Evidence: TARGET=acceptance goal; ESTIMATE=reasoned approximation; MEASURED=executed measurement; UNVERIFIED=missing evidence.

### Key Decisions — Five Lines

1. Build a new deterministic modular Python Brain; prefer 3.13, baseline ≥3.12; single COMMIT ownership.
2. Provisionally select Godot4.x/GDScript; lock only after graphics/IPC/MIN-SPEC prototype gates.
3. Derive engine order from manifests; provide recursive read-only state; return typed deltas/events.
4. Accept AI artifacts through manifests/validation/approval/import; ordinary play works offline.
5. Design first; implement exactly four Phase0 items after review/preflight and an implementation request.

## 1. Runtime Topology

```text
UI / keyboard / gamepad
  → typed command → provisional Godot client ↔ local IPC ↔ Python Brain
                                                            → validation/scheduler
                                                            → engines/read-only view
                                                            → deltas/fact events
                                                            → COMMIT → WorldState
  ← committed snapshot/diff/presentation events              → save/replay adapters
  → rendering/camera/animation/audio (derived caches only)

Accepted content package → typed validation → read-only Brain catalog
Factory → approved artifact → import/build → client catalog
Optional BYOK window → acceptance queue → versioned content package
```

### 1.1 Ownership & Dependencies

| Boundary | Owns | Prohibited / failure policy |
|---|---|---|
| domain/contracts | New entities/components/commands/events/deltas/invariants | No SDK/I/O/global RNG |
| engines | Declared reads; typed result production | No engine-to-engine calls or input/authoritative mutation |
| orchestration | Order, staging, event resolution, validation, COMMIT, receipts | No giant cross-system calculation method |
| adapters | Persistence/IPC/content/generation boundary conversion | No raw dict/Any passed into domain |
| client | Input, Korean UI, 3D/camera/animation/audio | Collision/VFX/prediction cannot commit HP/location/quest outcomes |
| production | Jobs/candidates/evidence/approval/import | Generation success cannot auto-accept artifacts/code |

Dependency layers: `domain → contracts → engines → orchestration → adapters → app`; later layers may use earlier layers, never reverse dependencies or same-layer cycles. Client-neutral domain.
Future paths/signatures are PLANNED until later BLOCKs/work orders; this overview does not authorize file creation.

### 1.2 Turn / Error Contract

Provisional phases: `VALIDATE → PRE_TICK → RESOLVE → REACT → CASCADE → POST_TICK → COMMIT → PRESENT`.
Convert input before VALIDATE. Rejection changes no time/state/authoritative events. Later phases stage results without mutating WorldState.

Boot derives topology from phase/dependency manifests. Cycles, unknown dependencies, same-phase write conflicts fail at boot; explicit dependency does not conceal a write conflict.
Later engines read a read-only staged view using defined delta ordering; COMMIT applies validated results once. BLOCK2–3 specify overlay/conflict semantics.

Rule failures may commit cost/delay/partial success/new danger. Invalid input, technical error, or cascade overflow discard the staged turn with explicit error.
Only approved non-authoritative fallback may return `degraded`, propagated to presentation/debug. Never swallow errors into success.

One Engine Protocol; manifest: `engine_id/phases/reads/writes/depends_on/emits/cost_class`.
Explicit registry; adding an engine changes ≤1 existing production file (TARGET: registry).
Co-locate feature payloads/adapters; avoid a growing central optional-field DTO or central union requiring each capability to edit it.

### 1.3 State / Time / Causality

- Component-owned WorldState; no full deep-copy per turn. Recursive proxy wraps children/mappings/sequences, blocks mutating methods, hides raw backing state, records reads. Cache wrappers. Frozen transport DTOs use immutable nested collections.
- Every state field declares CORE/DERIVED and Tier A/B/C. Hash CORE. Rebuilding DERIVED must preserve CORE. Retain entity `traits` semantics; views cannot mutate them.
- Tier A consumes tick-indexed deterministic events. Require full-state composition: `catchup(t0→t2) == catchup(catchup(t0→t1), t1→t2)`. LOD may depend on replayed state, not interval-length-dependent approximations.
- Tier B: feature-specific divergence bounds + CORE invariants. Authoritative economy/quest/death outcomes cross a strict Tier A boundary. Tier C: visuals/caches.
- Persist delayed events ordered by `(due_tick, priority, producer_id, sequence)`. Bound cascades, events, memories/logs/traces with explicit expiry/cap policy; never silently truncate authoritative events.
- Inject game clock/RNG. Derive stable streams from seed/tick/producer/event identity, never Python hash. Persist fixed-point integers with declared scale. Quantize before float-sensitive branches; no unordered accumulation or transcendental authoritative calculations.
- Replay records typed commands, seed/time, schema/ruleset/content versions/hashes, accepted generated packages; no live AI.
- Require same-process repetition, reversed TRACE execution order, fixed/random PYTHONHASHSEED to preserve each trace hash. Do not reverse dependency scheduler order.

World: L0 cosmology → L1 continent → L2 region → L3 nation → L4 settlement → L5 facility; bidirectional influence. Do not preserve v1 counts/parent IDs/classes.
NPC requirements: MASTER's 12-axis traits/10-factor attitude/20-factor persona/BDI/5-level memory/permanent anchors. Design new state/update rules; no v1 psychology formulas.

### 1.4 Storage / Retrieval / IPC / Distribution

Phase0: in-memory headless skeleton. Phase1+: provisional SQLite save + versioned JSON content/exchange.
DB is COMMIT-owned durable representation, not a second state owner. Prevalidate delta → durable transaction → publish same result; publish failure halts and reloads last durable commit. Receipts/version checks prevent duplicate retry commits. A9 defines crash boundaries.

Export/migration: consistent snapshot → temporary same-filesystem file → validate/close/flush → replace. Never copy a live DB casually.
[Python sqlite3](https://docs.python.org/3.13/library/sqlite3.html) documents transaction/backup APIs; project durability/version fit remain UNVERIFIED.
Provisional save policy: no v1 compatibility; forward-migrate intentionally supported v2 fixtures only.

Memory default: structured ID/relation/time/priority queries. Evaluate embedded T0 index/FTS only when needed.
No mandatory vector/Qdrant/Docker service. T1 deferred; adoption requires T0 fallback, quality dataset/targets. Do not embed data without demonstrated retrieval need.

Separate client/Brain processes. Provisional transport: loopback TCP using client adapter such as [StreamPeerTCP](https://docs.godotengine.org/en/stable/classes/class_streampeertcp.html).
Wire: schema/versioned length-framed JSON; message ≤1MiB TARGET; bounded queues, timeout, backpressure. Large seeds/IDs use decimal strings to avoid cross-runtime integer loss. A12 defines envelopes/binding consistency.

Brain binds `127.0.0.1:0`; launcher securely supplies assigned endpoint + session handshake token. Token is not a simulation seed/replay field.
Isolate port/token/save lock per session; reject simultaneous writers to the same save. No manual player port/service setup.

Deployment: thin launcher/supervisor owns client+Brain. Windows containment (e.g. Job Object) plus parent liveness; terminate authoritative backend if launcher/client/backend fails.
TARGET: heartbeat1s, timeout3s, helper cleanup≤5s. Test normal exit, Alt+F4, client/backend/launcher crash, Task Manager kill, Steam forced termination. No visible partial turn on reload.
Defer OS-specific implementation to deployment; API/kill behavior UNVERIFIED.

Provisional bundle: Godot export + PyInstaller onedir helper; preflight Python3.13/dependency/standalone support.
[PyInstaller operating modes](https://pyinstaller.org/en/stable/operating-mode.html) explain onedir; not project compatibility proof.
Players need no Python/pip/database/Docker installation.

## 2. Client Choice / Prototype Gate

Viable candidates: Godot4.x/GDScript, Unity/URP. Provisional Godot rationale: maintainable by one director+AI, client-neutral Python boundary, no initial .NET development requirement.
No measured claim that Godot is faster/smaller than Unity. Unity remains an escape route for unmet visuals/tooling/assets.

Start low-end prototype with Compatibility renderer. [Godot renderer documentation](https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html) describes low-end/core3D support and feature differences.
Validate pixel/toon/lighting/depth; renderer switching may alter visuals. Mobile is another profile candidate. Do not require Forward+-only effects without MIN-SPEC review.

Prototype occurs post-Phase0 after Brain/client contract; does not authorize early final graphics/audio production.

| Axis | PASS target | Failure response |
|---|---|---|
| Visuals | Representative modular character/environment; pixel/toon/lighting/depth alternatives; 360° camera; director acceptance | Adjust profile/style or prototype Unity; preserve product capabilities |
| Controls/truth | Keyboard/gamepad → commit → UI/animation; cache rebuild preserves CORE hash | Repair adapter; never give client state ownership |
| MIN-SPEC | Stated 4-core/8GB/iGPU device; 1280×720; p95 frame≤33.3ms; total game private commit≤2GiB | Optimize/retest; unspecified test device means UNVERIFIED |
| Replaceability | Same headless trace hash/typed contract with another client | Remove SDK types from Brain |
| Reliability | Disconnect/duplicate/reconnect/exit: no duplicate/partial commit or orphan backend | Repair receipt/lifecycle contract |

## 3. AI Production Factory

Flow: director brief/criteria → versioned job → replaceable tool/provider → candidate+manifest → deterministic/domain/import checks → required human review → accepted immutable artifact → reproducible import/build.
Failure/rejection → bounded retry or review queue.

Phase1+: small local CLI/job queue; no initial Airflow/workflow server. Expose candidates/evidence/cost/retry state; do not require human manual craft.

| Role | Producer/output | Acceptance |
|---|---|---|
| Architecture/code/tests/repair/integration | 6.1 Sol; scoped diff + execution evidence | Sol technical review; applicable product/rule approvals |
| Blocker advice | Astra only if needed | Sol validates advice against contracts/results |
| Content | Structured generation tools; new-schema NPC/quest/dialogue/location data | Schema/refs/effects + director acceptance |
| Portrait/2D | Fixed SD1.5+LoRA+ADetailer | Manifest/file checks + visual approval |
| 3D/animation | Replaceable pre-generation services; model/rig/clip | Scale/pivot/slot/rig/clip/import + visual approval |
| BGM/SFX/voice | Replaceable pre-generation services | Format/loudness/loop/import + listening approval |
| QA/import/build | Sol validators + standard tools | Deterministic evidence + required acceptance |

Manifest: ID/type/schema, tool/provider/model version, input/prompt hash, available seed, files/dependency hashes, license/provenance, validation evidence, acceptance, import target. No API secrets.
State: `PROPOSED → GENERATED → VALIDATED → APPROVED → IMPORTED`; failed/rejected states separate. Partial technical validation is not approval. Keep provider-neutral job/manifest contracts. A14 finalizes schema/imports.

Runtime generation is separate: new-game/transition/loading only; pre-generated fallback.
TARGET/window: 2 jobs × 2 attempts/job (1 retry) = ≤4 API attempts total.
Provider adapter enforces token bounds, RPM/RPD/TPM accounting, exponential backoff, 429 defer; A14 finalizes details. Current quota/capacity UNVERIFIED and rechecked at implementation/release.
Accept/cache/version data before gameplay. Eval defaults offline; paid/player-quota calls require explicit opt-in.

## 4. Technology Decision Register

Official feature docs are not project compatibility/benchmark evidence. Rejected means current choice, not permanent prohibition.

| decision | candidates | chosen/provisional | rejected | escape route | evidence status |
|---|---|---|---|---|---|
| Brain/minor | Python3.13 / supported≥3.12 | Python FIXED; prefer3.13 | Non-Python; unsupported minor change | Another supported minor only with compatibility evidence | UNVERIFIED |
| Runtime topology | Modular monolith / microservices / embedded interpreter | One Brain process | Service overhead / client coupling | Preserve typed contract, replace helper topology | UNVERIFIED |
| Client | Godot4 GDScript / Unity URP | Godot PROVISIONAL | Unity lower priority; web-only fit unproven | Same boundary with Unity prototype | UNVERIFIED |
| Renderer | Compatibility / Mobile / Forward+ | Low-end Compatibility prototype | Mandatory Forward+ assumption | Compare scenes/profiles or replace client | UNVERIFIED |
| IPC | TCP / Named Pipe / WebSocket / embedding | Loopback TCP, framed typed JSON | Initial native-pipe/WS stack cost; embedded fault coupling | Transport adapter, same schema | UNVERIFIED |
| Wire schema | JSON Schema / Protobuf / manual dict | Validated JSON + typed boundary | Generic dict; initial binary codegen | Protobuf adapter if needed | UNVERIFIED |
| Persistence | JSON snapshot / SQLite / external DB | SQLite save + JSON content | Player DB service; large per-turn snapshots | Versioned export/import + adapter | UNVERIFIED |
| Retrieval | Structured / FTS / vectors / Qdrant | Structured; T0 FTS if needed | Mandatory vector service; T1 deferred | T0 baseline, evidence before T1 | UNVERIFIED |
| Registration | Explicit / decorator discovery | Explicit; ≤1 existing-file edit | Hidden import side effects/discovery | Same manifest API, replace loader | TARGET |
| Packaging | Export+PyInstaller / Nuitka / player Python | Bundled onedir PROVISIONAL | Player installs; initial compiler complexity | Other verified bundle | UNVERIFIED |
| Factory | Local CLI queue / server / cloud jobs | Small queue + provider adapters | Initial always-on service dependency | Same manifest, replace backend | UNVERIFIED |
| Assets | Fixed2D / replaceable3D+audio | SD1.5+LoRA+ADetailer FIXED; pre-generation | Gameplay-critical live generation | Approved neutral export/manifest | UNVERIFIED |
| Runtime LLM | None / optional BYOK / per-turn relay | Offline default + optional windows | Mandatory narration/developer relay | Accepted cache/provider adapter | UNVERIFIED |
| Governance | Required tool families / approved same-layer alternatives | Ruff/mypy/import-linter/pytest/coverage; async mutation | Custom AST/assert-count substitute | Justified equal-layer replacement | UNVERIFIED |

Exact version pins: preflight output; not assumed installed/compatible.

## 5. Input Conflicts / v1 Evidence

| Conflict | Resolution |
|---|---|
| Earlier Astra/Sol/Luna split | All development Sol; Astra blocker advice |
| Wrong DEV-A8845HS/32GB/4060 | Actual7735HS/16GB/4050 6GB/512GB |
| Temporary dev OS vs Windows product | Portable core now; Windows deployment gate later |
| MASTER technology examples | Only fixed language/tool/product constraints mandatory; infrastructure compared |
| v1 Two-Pass/GameMaster wiring | Keep truth/AI separation; discard old classes/paths/per-turn narration |
| Preserve capabilities vs poor formulas/structure | MASTER capability contract; v1 failure evidence + descriptive content only |
| Prompt80modules/692methods vs saved audit71/606 | Historical snapshots; not rerun audit |
| README689passed | Historical claim; not this session's pytest |
| Templates assumed mechanic-free | Strip stats/DC/reward/time/behavior/IDs |
| Historical governance | Map preserved purposes; do not auto-port v1 procedures or deploy new CI rules |
| Premature implementation | BLOCK1 only, then2–9/review/preflight/request/four Phase0 items |

Details: [V1_REUSE_INVENTORY](V1_REUSE_INVENTORY.md). Source HEAD `9f2ec20a7a06fedf01dd141b740bf4da8c3fc3ec`.

| Inspected | Observation | Use |
|---|---|---|
| README/audit/handoff/representative tests | Past capabilities/wiring/invalid-command failure evidence | No copied tests/fixtures/oracles |
| 23 template JSON files | 5,661,063bytes; syntax parses | Not semantic/schema/reference/quality approval |
| dice/ration/rumor | Global random, set order, input mutation, broad exceptions, uuid4 | Justifies deterministic/proxy/error contracts; no formulas reused |
| NPC/world/templates | Hierarchy/cognition; terminology/count differences | New MASTER-driven schema |
| Audio config | BGM7+SFX13 refs; 0 actual files | Not reusable audio assets |
| Maps/icons/CSS/legacy | Some files present; legacy only.gitkeep | Not adopted; no assumed save fixtures |
| Curated JSON | 3 locations+1 facility+1 premise+1 visual | [Six candidates](../docs/reference/QUILLTALE_CONTENT_CANDIDATES.json); CURATED_REFERENCE; runtime_imported=false |

Counts are executed file inspection, not runtime benchmarks. Four source hashes/entry/field records preserve provenance. Editorial selection is not measured product quality; approval/rights checked at import. No v1 writes/tests/deletions.

## 6. Failure Mapping F-01–F-10

| ID | Prevention/evidence | Layer / contract |
|---|---|---|
| F-01 | Boot manifest topology; fail cycles/write conflicts | L1/L2; A1/A2 |
| F-02 | Feature typed payload/delta; separate presentation adapters | L1/L3; A3 |
| F-03 | Explicit reads/writes/dependencies + observed accesses | L1/L2/L4①; A2/A5 |
| F-04 | Live replay coverage/zero-hit public methods/caller evidence | L2; B2/B3 |
| F-05 | Inject RNG/clock; fixed-point/hash/replay | L1/L2/L3; A6 |
| F-06 | Typed commands; optional language adapter outside domain | L1/L3; A7 |
| F-07 | New versioned schemas/IDs/refs/artifact validation | L1/L4②; A10/A14 |
| F-08 | Short bootstrap handoff/backlog; Phase1+ tool aggregation | L2/GATED; B2 |
| F-09 | One-responsibility orders; live play path/playtest scope gate | GATED/JUDGMENT; B4 |
| F-10 | Component ownership/COMMIT/layers/integration traces | L1/L2/L3; A2/A5/B3 |

These are design controls, not proof that unimplemented code is safe.

## 7. Anti-pattern Mapping AP-01–AP-11

| ID | Rule | Exception | Enforcement |
|---|---|---|---|
| AP-01 | No Any in domain/engines/events/state; immediately type I/O | Reviewed boundary whitelist | L1; mypy strict/disallow_any_explicit, Ruff ANN401 L3; whitelist GATED |
| AP-02 | Reraise/domain error OR log+explicit fallback+degraded | Contract-approved fallback only | L1 errors; L2 boundary/degraded/replay; Ruff E722/S110/S112/BLE001 |
| AP-03 | Pure state-in/result-out domain tests; no mock | Adapter external API/FS tests | Ruff TID251 L3 |
| AP-04 | No completed pass/ellipsis/meaningless None stubs | Protocol/ABC; explicit NotImplementedError(reason+TODO-ID) | L1 registry; L2 live replay; Ruff-supported checks/TODO search, not semantic proof |
| AP-05 | No global mutable state; Final is not deep immutability | Deeply immutable constants; owner/injected context | L1 ownership; L2 contamination; Ruff PLW0603/RUF012/B006 |
| AP-06 | Stable order/RNG/time/numeric state | Boundary/visual floats; quantize before domain branching | L1 services/hash schema; L2 replay/hashseed; Ruff TID251; no custom checker |
| AP-07 | Refactor preserves hash; behavior change separate reason/commit | Approved test deletion; intentional change explicit | L2 replay/GATED; no v1 hash oracle |
| AP-08 | Frozen DTO/recursive proxy/deltas; only COMMIT writes | COMMIT owner raw state | L1 ownership/L2 proxy/benchmark; no assignment AST checker |
| AP-09 | One-way imports; no same-layer cycles | TYPE_CHECKING without runtime cycles | L1 layers/L3 import-linter |
| AP-10 | No assert-count acceptance; state engine invariants | Adapter mock under AP-03 only | L2 mutation/pytest/property tests |
| AP-11 | Independent expected values, invariants/boundaries | Explain equivalent mutants/timeouts separately | L2 mutation; no Hypothesis-existence checker |

Mutation: engines only; weekly/phase end, not commit gate. Initial proposal: ≥80% meaningful non-equivalent kill score per engine (TARGET); finalize B3. Never count equivalence/timeout/unmeasured as pass.
Selected mutmut/cosmic-ray version/platform UNVERIFIED pending preflight; no configuration/run yet.

## 8. Hard Constraints C-01–C-06

| ID | Decision/acceptance | Detail |
|---|---|---|
| C-01 | Local structured query; T0 if retrieval; complete play without T1/server | A8/A12/A13; quality target before T1 |
| C-02 | Paid production separate from BYOK; bounded window calls/tokens/rate/retry/defer/cache | A14; current quota/average calls UNVERIFIED |
| C-03 | A/B/C schema, TierA full composition, CORE hash/DERIVED isolation | A5/A6/A11; property tests NOT_RUN |
| C-04 | Manifest differences + proxy + coverage; distinguish undeclared/unused/unconsumed/unreachable | A2/A5/B3; custom① compares declarations |
| C-05 | Topology/isolation/heartbeat/cleanup/atomic commit/exit matrix | A9/A12; OS implementation later, UNVERIFIED |
| C-06 | Separate sequential9 BLOCKs; one per turn; brief chat | End after BLOCK1; BLOCK2 next |

## 9. Four Enforcement Layers / Historical Rules

Highest applicable layer first. ENFORCED=implementation automation target; GATED=approval/review; JUDGMENT=concise human/agent judgment.
This is a design mapping, not deployment of AGENTS/CI policy.

| Layer | Mechanism | Limit |
|---|---|---|
| L1 structural | COMMIT, typed boundaries, ownership, registry, dependency DAG | Public-path capability restrictions; not a Python malicious-reflection sandbox |
| L2 runtime | Proxy, staging, replay, coverage, mutation, lifecycle/performance | Requires real execution/fixtures |
| L3 standard | Ruff/mypy/import-linter/pytest/coverage | Cannot statically prove all field consumption/domain semantics |
| L4 custom | ① access manifest; ② data/artifact manifest | Thin wrappers; no custom AST framework |

**Custom checkers: planned2 / maximum3 / implemented0; Phase1+.**
① Standard tools cannot compare executed state paths to capability declarations; use proxy observations.
② Reuse JSON Schema/Pydantic; wrap project ID/ref/hash/import/provenance relationships.
Async mutation/report drift are not additional commit gates.

### v1 Rule Residency

Numbers refer to historical AGENTS_v1. Preserve B1 purposes; do not import v1-specific paths/approval procedures automatically.
Governance/rule-file/CI/backlog/test-deletion/custom-checker changes need explicit authorization. Historical file unchanged.

| Historical rule | v2 treatment | Class/layer |
|---|---|---|
| DoD1/3/4/5 | Actual pytest, meaningful feature tests, no gaming, baseline regression/evidence | L2/L3/GATED; document-only work does not invent pytest |
| DoD2 | State regression via v2 replay/invariants | L2; no v1 eval_runner/metric wiring |
| Hygiene1/2/3 | Direct edits/full diff/scratch isolation/tmp_path | GATED/L3; inspection scripts are not production code |
| Hygiene4/5 | Exclude cache/pyc; lint/status; placeholders not implementation | L3/GATED; no absolute zero-byte ban |
| Hygiene6 | Client I/O/render, Korean UI, nonblocking I/O; Brain rules | L1/L2; no fixed app.py |
| Dup1/2/6 | Search responsibility/callers; check IDs | GATED/L4②; no fixed legacy paths |
| Dup3 | Explicit supported migration chain | L1/L2; no unlimited optional/default debt |
| Dup4/5 | UTF-8; avoid confusing names | L3/GATED; no global filename uniqueness |
| TwoPass1/2 | Truth/generation separation; remove mandatory Pass2 | L1; no old runtime loop |
| TwoPass3/4 | Memory bounds/anchors; explicit network fallback/degraded | L1/L2; summaries cannot overwrite CORE facts |
| Scope1/2/3 | Authorized rule/test/backlog changes; atomic responsibility commits | GATED; no absolute one-session=one-task |
| Handoff1/2/3 | Files/results/start markers; missing evidence UNVERIFIED | L2/GATED; document evidence distinct from runtime |
| Wiring1/2/5/7/8 | Live integration/zero-hit/evidence/incremental wiring | L1/L2; no old classes, grep-only audit, blanket engine freeze |
| Wiring3/4/6 | Field readers/writers/search/bounded lists | L1/L2/L4①/GATED |
| Ops1/2/3/6 | Brief Korean chat; fixed facts; actual laptop; reasoned questions | JUDGMENT; no caveman/lab role constraint |
| Ops4 | Search; in-scope design choices by Sol | GATED/JUDGMENT; no permission per new class |
| Ops5 | Entity/world traits convention | L1 new schema; no v1 class copy |
| Ops7 | Sol all development; artifact tools + validation/approval | GATED/L1; no low-model coding delegation |
| Ops8 | Unit → live integration → full regression | L2; no TwoPass wiring |
| Report | Detailed evidence links + brief Korean result | JUDGMENT/GATED; no historical fixed4 headings |

Phase1+ commit gates exactly11: Ruff; mypy; import-linter; pytest; replay hash; contamination; coverage/zero-hit; deterministic counters; supported save migration; engine manifest; data/artifact manifest.
B3 defines failures/platform/time. Do not front-load all gates into Phase0.

## 10. Hardware / Measurement Plan

Actual developer laptop: Lenovo LOQ-E15.6 ARP10e / Ryzen7 7735HS / RTX4050 Laptop6GB / RAM16GB DDR5 / NVMe512GB; temporary Windows11.
User-supplied specs, not measured performance. Release MIN-SPEC4-core/8GB/iGPU is separate.

| Metric | TARGET | Method/failure rule |
|---|---|---|
| Dev RAM | Tools/job private commit≤12GB | Laptop process-tree peak; serialize/unload/split if over |
| Generation VRAM | Peak≤4.5GB | SD1.5+LoRA+ADetailer, start batch1; record versions/model hashes/peak/runtime; even batch1 fit UNVERIFIED |
| Regenerable cache | ≤30GB | Directory sizes/eviction; preserve approved originals separately |
| Game RAM | Brain≤512MiB; client≤1536MiB; total≤2GiB | Concrete MIN-SPEC device/scene/save/private-commit peak |
| Authoritative turn | p95≤100ms; p99≤250ms | MIN-SPEC validate→durable COMMIT; exclude LLM/render; Phase0 in-memory is not shipping proof |
| Rendering | 1280×720; p95 frame≤33.3ms | Lowest profile, camera/combat/modular scene; unspecified iGPU=UNVERIFIED |
| Proxy overhead | Total turn CPU increase≤10% | Same build/device/seed/trace with enabled proxy vs validation baseline; reads recorder included; wrapper peak |
| Release proxy | Keep enabled by default | Optimize cache/views/retest; no unsupported disablement |
| Deterministic counters | Per executed tick/lane calls≤128, writes≤2048, owned allocations≤32768, wrappers≤8192; total A facts≤512, cascade≤8; B facts0 | BLOCK6 A13 finalizes units/owned-site coverage/job totals; wrapper count≠all Python allocations |
| CI | Commit gates≤60s; local Ruff+core replay≤20s | Actual pipeline elapsed; NOT_RUN; exclude async mutation |
| Cleanup | Heartbeat1s; timeout3s; cleanup≤5s | Deployment matrix/process-tree + last committed save |

Initial workload TARGET: near NPC64, off-screen actors1000, delayed events512, commands1000; warm-up100 commands; repeated quantiles/peaks/hash.
Author new fixture inputs/expected values from v2 contracts. Large catch-up/new-game generation is a separate visible preparation job, not hidden normal-turn cost.
This workload is not proof of final full-world scale; later scene/long-run stress required.
All performance values TARGET; execution UNVERIFIED. Heavy LLM/image/editor jobs sequential; over budget → smaller batches/unload/external pre-generation. No assumed model fit/vendor capacity.

## 11. Cost / Risks / Next

Typed boundaries/standard tools/ownership reduce late rewiring and mutable-state defects. Proxy costs wrappers/access recording but blocks alias mutation and supplies manifest evidence; benchmark≤10% and optimize.
Reuse standard tooling plus two thin wrappers. One Brain/local Factory minimizes service operations; typed client boundary limits replacement cost.

Unverified: Python3.13/toolchain/bundle (preflight), visuals/MIN-SPEC (prototype), proxy/catch-up (A5/A11/A13), SQLite crash/migration (A9), IPC/cleanup (A12), asset quality/import (A14). Do not treat these as passed implementation prerequisites.

[BACKLOG](../BACKLOG.md) is task authority. Next: **RS-ARCH-002-B02**, A1 scheduler/A2 engine/A3 presentation.
Order: BLOCK2–9 → review/preflight → implementation request → Ruff+mypy → recursive proxy → walking skeleton(1–2 dummy engines) → golden replay.
Exactly four Phase0 implementations. Manifest/data/report generators, save/migration, performance counters, graphics prototype begin Phase1+.
No new v1 copying, production code, BLOCK2, or bulk assets in this task. Document completion does not mean gameplay or lock-in completion.

--- BLOCK 1/9 END. Enter "continue" for the next block. ---
