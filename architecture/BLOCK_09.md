# BLOCK 9 — Roadmap, Work Orders, Risks & Self-check

Date:2026-10-03 | Task:RS-ARCH-002-B09 | Owner:gpt-6.1-sol | Mode:DESIGN
Inputs:[prompt](../docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md) §6/7/8/10, [MASTER](../docs/MASTER_GAME_ARCHITECTURE.md), BLOCK1–8. Format:compact English.
Status:reviewable design packet; no implementation/tool installation/assets/CI activation. Self-check is completeness evidence, not independent validation. Two readiness findings remain explicit; do not declare final architecture acceptance.

Update 2026-10-03:ARCH-003 design repairs accepted; [PREFLIGHT-001](../docs/work_orders/RS-PREFLIGHT-001_COMPATIBILITY.md) Phase0 qualification/four instruction contracts complete. AR-010/011 closed for Phase0; later family/source-order readiness deferred. B09 #6/#34 remain PARTIAL for later tasks, parent ARCH-002 IN_PROGRESS; no all-future-orders READY/runtime/independent proof. Next step3 only after implementation request.

## 1. Readiness / Authority

Nine design documents now exist. This does not mean the architecture is approved or runtime orders are READY. [BACKLOG](../BACKLOG.md) remains task/dependency SSOT.
Completed document task: [RS-ARCH-003 review](ARCHITECTURE_REVIEW.md), design review/repairs accepted for preflight. The original [review order](../docs/work_orders/RS-ARCH-003_ARCHITECTURE_REVIEW.md) is retained; current director scope authorized necessary B02–06 document repairs. No independent reviewer or Astra call occurred.
[Implementation order packet](../docs/work_orders/IMPLEMENTATION_ROADMAP_ORDERS.md) links finalized Phase0 contracts/orders and later DRAFT decomposition. Four Phase0 instructions complete; execution waits request/completed predecessors/actual source-entry checks. Preserve the [coding-order](../docs/prompts/SOL_CODING_WORK_ORDER.md) rule; later DRAFT orders are not READY.

| Stage | Entry / exit |
|---|---|
| Design packet | BLOCK1–9 documents; actual document checks; findings recorded |
| Architecture review | RS-ARCH-003: verify contracts/F/AP/C/§10; repair within approved design scope; independent review status explicit |
| Compatibility planning | RS-PREFLIGHT-001: exact version/platform/license/bundle evidence; unresolved critical inputs keep affected order DRAFT; not Phase0 implementation |
| Implementation | Explicit implementation request + complete READY order + completed prerequisite IDs; execute one bounded responsibility |
| Gameplay completion | Actual files/live wiring/tests/stage-appropriate replay/coverage; no stub/dummy/document substitution |

Latest detailed contracts supersede earlier provisional summaries: B03 event identity/hash; B04 recovery/receipts; B05 activation/wire; B06 counter units/B-facts0/runtime window budgets. In particular B01's provisional two-job generation window is superseded by B06 A14's typed window table. Never combine old/new budgets.

## 2. Dependency Roadmap

Phase numbers follow MASTER §13. Curated first-segment integration/playtest precedes bulk in Phase4; no extra Phase0 item. Gameplay capabilities stay on the product register even when technical modules are merged.

| Phase / backlog IDs | Deliverables / measurable exit | Dependencies / reason | Tool activation | v1 disposition / order |
|---|---|---|---|---|
| Planning:ARCH-003,PREFLIGHT-001 | Design review/repairs +Phase0 selected-version evidence/exact four instructions DONE | B01–09; prevent implementation under conflicting contracts/unknown native dependencies | Read/check only; no new checker/config | Inventory/candidates read-only; review ACCEPTED_FOR_PREFLIGHT; preflight Phase0 DONE, later qualification deferred |
| Phase0:P0-002 → P0-004 → P0-001 → P0-003 | Strict lint/types; recursive views; one full command→COMMIT→presentation path with1–2dummy engines; fixed replay/contamination matrix passes | Review/preflight/request; proxy before engines, live turn before record/replay | Ruff+mypy configuration; pytest unit/integration/replay only | No v1 runtime/data/fixtures/oracles; P0 instruction packet FINALIZED, request/predecessor/source-entry gates |
| Phase1:P1-CORE + staged P1-GOV | Small headless movement/interaction/combat/save/load/NPC/world path; invalid input preserves CORE; save crash/recovery tests; full TierA composition | P0 outputs become real callers/state; add schemas only for settled gameplay | import-linter then native coverage, cost observations, CUST01/02, migration; report after evidence exists; async engine mutation | Descriptive candidates stay quarantined; no port of engines/formulas; work orders split below |
| Phase2:CLIENT | Brain/client boundary wired; camera/modular placeholder scene; keyboard/gamepad; public-view resync; stated MIN-SPEC frame/memory targets + director visual acceptance | P1 public projection/receipts and frozen schema; graphics cannot dictate truth | Existing gates + lifecycle/prototype harness; no extra commit gate | No legacy text-client/CSS/icon adoption; NEW client/adapter orders after P1 paths exist |
| Phase3:FACTORY | Provider-neutral manifests, validation/approval/import; one approved representative sample per content/image/3D/animation/BGM/SFX/short-voice path builds | Stable relevant schemas/import/rig/style contracts; foundations may start after P1 data contract, modality integration waits for client | CUST02 consumes standard validators/import results; native report aggregation; no workflow server | Narrative source provenance may be input; no automatic import; vendor/license/style gaps fail approval |
| Phase4:V1-MIGRATION → BULK | Six candidates considered individually/new IDs; first-segment playtest fixes required gaps; bulk only after repeatable validated import/build and profile acceptance | P1 systems + P2 graphical controls + P3 manifest/approval/import; no mass production before compatibility | Eleven applicable gates; engine mutation at phase exit; content/style/rights review | Import only approved descriptive fields; reject unsuitable entries; discard mechanics/balance/schema/tests |
| Phase5:RELEASE | Qualified integrated build; supported saves; launcher cleanup matrix; offline/BYOK fallback; performance/device evidence; director release decision | Playable first segment and approved asset library; polish actual observed behavior | Full11 gates + async mutation + device benchmarks/build/QA outside commit timing | No v1 save promise/code dependency; old repo remains read-only |

### 2.1 Phase0 — Exactly Four

| Sequence | ID | One implementation item | Completion evidence |
|---|---|---|---|
| 1 | RS-P0-002 | Ruff+mypy strict config | Selected versions/config pass on actual source; no extra CI/checker/report |
| 2 | RS-P0-004 | Recursive read-only proxy | Nested fields/mappings/sequences blocked; attributed observations; epoch expiry/cache; independent tests |
| 3 | RS-P0-001 | Walking skeleton | Typed command→compiled phase barriers→two dummy engine results→single COMMIT→diff/cue; rejection/abort preserve state |
| 4 | RS-P0-003 | Golden replay | Record/replay full CORE+protocol; rejected/aborted steps; repeat/reversed trace execution/hashseed; frozen inputs |

Each item includes its necessary tests/types and live integration; that does not introduce a fifth tooling item. Boot manifest safety in the skeleton is structural scheduling, distinct from the deferred CUST01 evidence wrapper. Phase0 has no coverage/report generator, cost gate, mutation job, migration, schema-validation wrapper, or graphics/asset implementation.

### 2.2 Phase1 Work Decomposition / Contract Promotion

Parent IDs describe capabilities, never a single huge coding order. Detailed orders must be prepared against actual predecessor source; planned filenames are not evidence that callers exist.

1. P1-CORE: settle new position/geometry/physiology/action schemas and independent units/formulas → movement/interaction → representative combat/status/failure-forward → persistence/recovery → memory/representative BDI NPC → off-screen causality/composition.
2. P1-GOV: one-way import contracts once actual modules exist → coverage/access observations → owned-site cost instrumentation → two thin wrappers → native evidence report → bounded asynchronous mutation. Activate each corresponding B08 gate when its implementation/fixtures exist, never report dormant gates PASS.
3. Brain/client public projection + delivery-capacity preparation precede CLIENT; only then implement rendering/IPC. Factory schema/manifest foundations can proceed after settled content contracts; no modality importer before its target format is known.
4. Extend capability paths using MASTER requirement + observed trigger/search evidence. Before first playtest, a mandatory MASTER requirement is valid bootstrap justification; keep path small and schedule actual playtest. No speculative unused engines.

### 2.3 Product Capability Coverage — Preserve, Do Not Port

| MASTER outcome | First representative path | Expansion / acceptance |
|---|---|---|
| L0–L5 procedural hierarchy + bidirectional influence | P1 small typed graph + drought/supply/event chain | Phase4 generated catalog120→200 regression without code edit; new IDs/topology; counts not mandatory populations |
| Physics/environment | P1 range/material interaction + light/noise/temperature hazard slice | Extend destruction/collapse/weather/oxygen/enclosed-space paths with independent fixed-point rules before product completion |
| Combat/survival | P1 action/status/stamina + food/fatigue slice | Injury/poise/toxicology/disease/spoilage/encumbrance/harvesting consequences where enabled; no v1 dice/balance port |
| NPC/social | P1 one autonomous NPC, traits/attitude/persona/BDI + five memory levels/anchors | Factions/relations/rumors/trade/economy; validated off-screen wakes;12/10/20 axis contract retained with newly designed updates |
| Space/infrastructure | P1 movement/routes/facility + neglected-quest delayed effect | Dungeons/roads/calendar/settlements/nations + persistent consequences; no requirement-per-engine mapping |
| Graphical product | P2 scene/360°camera/modular body/equipment/input + state-owned outcomes | P3/P4 portraits/lighting/depth/pixel stability/approved animation/audio; final capability acceptance on client |
| Human-director Factory | P3 each representative modality from brief to approved build | P4 repeatable bulk; paid production separate from optional runtime BYOK; director approval required |
| Standalone/offline/BYOK | P1 offline authoritative loop; P2 IPC; P5 bundle/lifecycle | No player Python/Docker/DB service; runtime generation disabled by default and outside turns; quota/uncertain billing safe fallback |

Small first slices do not fulfill every MASTER row. Release coverage register must list each sub-capability with actual source/test/playtest evidence, or mark it pending; no silent deletion under “merge engines”.

## 3. Compatibility Preflight — Planning, Not Implementation

Preferred Brain minor:Python3.13; local interpreter3.13.12 used for document syntax checks only. Select exact release patch after dependency evidence; supported baseline≥3.12. Phase0 selected/native-probed tool versions below; later third-party versions NOT_SELECTED until applicable entry.

| Critical family / boundary | Candidate decision / required evidence | Current status |
|---|---|---|
| CPython + stdlib | Windows runtime, sqlite3 SQLite library version, TCP/JSON/hash/decimal/profile/tracemalloc behavior; bundle proof | Python3.13.12/SQLite3.50.4 JSON/hash/transaction/loopback probes PASS; deployment UNVERIFIED |
| pytest | 9.1.1/nativeWindows3.13.12; independent UTF8/hashseed subprocess probe | PASS inspection; project tests NOT_STARTED |
| Ruff | 0.16.6/nativeWindows; all9required rules/TOML/bannedAPI positive+negative probes | PASS inspection; source lint deferred |
| mypy | 2.4.0/cp313winAMD64 +nativeclosure; strict/explicitAny/typedbridge/package probes | PASS inspection; source checks deferred |
| import-linter / grimp dependencies | Exact pins/native execution on planned package graph; lock transitive binaries | NOT_SELECTED/UNVERIFIED |
| coverage.py | Exact pin/native tracing/context/JSON/JUnit collection compatibility | NOT_SELECTED/UNVERIFIED |
| Mutation | mutmut PROVISIONAL, async WSL/Linux fork environment; cosmic-ray same-layer alternative requires justification/evidence | Exact version/environment UNVERIFIED; no native-Windows mutmut assumption |
| Pydantic2 / pydantic-core | Exact compatible wheel/architecture/3.13; strict frozen-payload adapter and restricted schema export | NOT_SELECTED/UNVERIFIED |
| Persistence/retrieval | Embedded SQLite + typed JSON; local structured T0, FTS only if needed; no vector server | Project durability/FTS/export/bundle UNVERIFIED |
| Godot4.x/GDScript | Exact editor/export template/renderer/native export/license; public JSON integer-string/frame prototype | PROVISIONAL/UNVERIFIED |
| Launcher/IPC/process | Loopback TCP + secure inherited token + Windows Job Object/file-identity writer lock | Native bindings/helper runtime strategy to select at deployment; matrix defined B05, execution UNVERIFIED |
| PyInstaller onedir | Exact pin/3.13/native hooks/hidden imports/Godot+helper standalone/redistribution | PROVISIONAL/UNVERIFIED; Nuitka/other verified bundle escape |
| Factory2D | SD1.5+LoRA+ADetailer FIXED; runner/PyTorch/CUDA/driver/model/license pins; RAM/VRAM/SSD sample on actual laptop | Toolchain NOT_SELECTED; fit/rights UNVERIFIED |
| 3D/animation | Provider-neutral glTF2/GLB candidate; rig/units/slots/material/clip format + export/import/tool versions | Formats provisional until sample validates; service/model rights UNVERIFIED |
| Images/audio/content | PNG candidate; WAV approved master/OGG shipping candidate; typed UTF-8 JSON + manifest/hash; importer/codec versions/rights | Exact profiles/platform decoder/import behavior UNVERIFIED |

Collect per dependency:exact version + source URL/date + Python/OS/architecture + native/transitive components + wheel/build/export/bundle/license evidence + actual command/exit + PASS/FAIL/UNVERIFIED. Official feature documentation alone is not project compatibility proof. Declared licenses/model licenses/providers/build redistribution are separate checks.
Preflight does not install all future asset tools or choose providers before their phases. Phase0 can qualify only its required tool subset; later fields remain UNVERIFIED and gate only affected orders. If3.13 materially fails while another supported minor passes, propose the evidence-backed change; do not silently switch.

## 4. Risks / Trade-offs

### 4.1 Three Expensive Areas / One-person Ceiling

| Area | Concrete cost / containment | Rejected alternative |
|---|---|---|
| Performance | Recursive observations, canonical full CORE/event hashing and per-second exact autonomous steps; bounded COW/cached hashes/prefetch/exact idle proof; A13 budgets/benchmarks | Turning off semantic checks without evidence; full graph deepcopy; approximate TierA |
| Complexity | Schema→typed payload→manifest→read/delta→public projection→save/replay integration; co-located feature bundle, single registry edit TARGET, explicit owned contracts | Generic dictionaries/central union/hot plugin discovery/microservices |
| Development speed | Independent expectations/replay/crash tests + Factory validation/human approval delay “looks done”; staged controls/native outputs; small live paths | Accepting disconnected classes/unapproved generated assets to inflate progress |

Ceiling:one Brain process, serial authoritative turn, one bounded Factory job runner; custom planned2/max3/actual0; exactly11 later commit gates; one bounded order/session scope TARGET≤5production modules and one capability (B08). If an order exceeds this, split coherent responsibilities rather than dropping necessary verification. User-authorized scope/necessary repairs take precedence over this planning target.
One-developer overengineering trigger: a new abstraction/service/checker has no current MASTER-triggered live caller, duplicates a standard-tool layer, or requires a fifth Phase0 item. Reject/postpone it; record a concrete later need. Fixed product outcomes are not cut to fit the ceiling.

### 4.2 Proxy Release Decision / Measurement

CPU overhead TARGET≤10%:five matched proxy/raw-capability benchmark pairs, identical fixed trace/content/seed/engine results, warm-up and CPU sampling; `(proxy_CPU/raw_CPU - 1)*100`, B06 BENCH-PROXY. Raw path is isolated benchmark code, never an engine production mutation capability. Measure on actual laptop and qualified DEV-B/MIN-SPEC device; actual device models missing => that tier UNVERIFIED. Working-set/turn budgets also must pass.
Defensible numeric overhead ESTIMATE unavailable before implementation; MEASURED=UNVERIFIED. Keep proxy enabled by default in release. If>10%:optimize wrapper caching/specialized typed views/profile and remeasure. Disable only with explicitly approved proposal proving equivalent immutable access/observations, contamination/regression safety, and actual budget gains; never an automatic build flag to bypass gates. If evidence still missing, keep it and withhold performance qualification.

| Qualification | Numeric TARGET / environment / decision |
|---|---|
| Brain turn | MIN-SPEC p95≤100ms,p99≤250ms validate→durableCOMMIT; PERF-TURN fixed population/workload/warmup/5runs B06; over target fails qualification |
| Runtime memory | Brain≤512MiB/client≤1536MiB/combined including launcher≤2048MiB; measured private commit/peak during representative runtime; any excess fails |
| Client | MIN-SPEC1280×720 p95 frame≤33.3ms,64visible representative scene/120s/5runs B06; visuals also director-approved; any missing test UNVERIFIED |
| Development | Actual7735HS/RTX4050 Laptop6GB/RAM16GB/SSD512GB; active tools/job≤12GB private commit, generationVRAM≤4.5GB, evictablecache≤30GB; heavy jobs sequential; excess triggers batch/unload/external-production repair |
| Commit/local | Eleven-gate58+2=60s TARGET; local Ruff+one golden≤20s TARGET; Windows-native commit-family compatibility preflight; runtime cost gates use deterministic counters, not ms |

Every value above is TARGET, actual timings/fit NOT_MEASURED. Temporary Windows11 does not constrain portable core; final Windows standalone remains product-required.

### 4.3 Governance Construction Effort / ROI

ESTIMATE, not measurement:one person-day=6focused engineering hours; Sol-assisted implementation/debug/review time. Scope is initial governance construction/integration once representative code exists, not calendar delivery, gameplay, proxy/RNG/scheduler/replay product architecture, ongoing test writing, tool subscriptions, or asset production. Rework/pins/device availability can change ranges; review after first measured phase. No monetary ROI claim without data.

| Governance construction slice | ESTIMATE person-days | Loss prevented / activation |
|---|---|---|
| Ruff+mypy configuration/typed boundaries | 0.5–1.0 | Type cheating/silent exception/nondeterministic API; Phase0 |
| import-linter contracts/native CI integration | 0.5–1.0 | Cycles/reverse imports; actual modules Phase1 |
| Native coverage/access evidence + CUST01 | 1.5–3.0 | Unwired/unused/unconsumed state and undeclared reads; Phase1 |
| Owned-site cost instrumentation/gate integration | 1.5–3.0 | Unbounded events/allocation/CPU work independent of CI speed; Phase1 |
| Schema/reference/artifact CUST02 wrapper | 1.0–2.0 | Invalid generated data/refs/approval/import drift; Phase1–3 |
| Save-fixture/contamination gate integration | 0.5–1.0 | Forgotten fixture/regression lane; harness implementations budgeted with runtime separately |
| Native evidence report/CLI/drift aggregation | 1.0–2.0 | Stale/fabricated completion/session rereads; after source evidence exists |
| Async mutation/weekly qualification integration | 0.5–1.0 | Fake/overfitted tests; real engines only |
| Remaining eleven-gate selection/freshness/bundle CI wiring | 1.0–2.0 | Empty test lanes/cross-snapshot green reports; staged activation |
| **Total construction** | **8.0–16.0 person-days (48–96focused hours)** | Planned2 wrappers, existing tool outputs; not measured savings |

§0.3(2) Control ROI:pay early for ownership/types/proxy/replay because corruption/nondeterminism makes later gameplay debugging and saved-state repair expensive. Postpone costs that need real source evidence; avoid custom static-analysis/report/test frameworks. Estimate range is a resource allocation proposal, not proof that it is cheaper than v1 loss. Track actual construction hours + incidents caught/rework prevented; if a control's maintenance exceeds observed benefit, propose a same-layer simplification with preserved guarantees and explicit approval. Do not remove fixed invariants to manufacture savings.

### 4.4 What Costs More Than v1 / Highest Risk

New path adds recursive observation, declared boot validation, typed/hash validation and explicit durable transaction/projection-capacity work relative to v1's informal/direct mutation path. Those added operations consume work; net turn latency against v1 is UNVERIFIED because neither comparable runtime was benchmarked. New architecture removes mandatory per-turn LLM; no inferred net speed ratio. Slower preparation/acceptance is justified by replayable truth, zero partial commits, bounded resources, and honest artifact quality gates.

Highest risk:per-second TierA autonomous simulation + full composition while covering large procedural worlds on MIN-SPEC. Sparse stepping is legal only for proved no-op spans; a convenient approximate rate formula cannot replace it. Escape:profile dense/sparse workloads, reduce declared active workload/content population or design exact event-driven update rules with independent full-A split proofs; keep omitted MASTER capabilities pending, not silently dropped. If target still fails, propose a measured budget/product-profile decision; never weaken TierA law or let B events affect A.
Secondary risk:16GB/6GB local production fit; run one representative SD job before batch plans. Reduce batch/resolution only within approved output profile, unload models, or use paid external production retaining SD pipeline/provenance; no guarantee that a particular runner fits.

### 4.5 Do Not Build Yet

- Additional custom AST/nondeterminism/assert-count/Hypothesis-existence checkers; max3 is a ceiling, not a quota.
- Phase0 reports/coverage infrastructure/cost gates/mutation/migration/data-wrapper/graphics/final assets.
- Microservices, mandatory Docker/Qdrant/vector server, workflow server, large local LLM/per-turn narration.
- Hot reload/runtime plugin discovery, parallel authoritative engine execution, full ECS/event-sourcing framework.
- Bulk art/audio/3D before representative importer/rig/style/license/approval gates; live full-sentence TTS.
- v1 code/calculations/balance/test/schema/save port; automatic import of quarantined candidates.
- Provider hard-coded free-turn promises; mass BYOK evaluation; unrequested production/push/publish.

### 4.6 Factory Risk Containment

| Risk | Containment / fail rule |
|---|---|
| Vendor lock-in | Typed ProductionSpec/provider adapter/neutral approved exports + pinned importer; replacement must pass same sample/import tests |
| Rights/provenance gaps | Manifest input/output/model/tool/version/license evidence; unclear rights => NEEDS_REVIEW, excluded from approved build |
| Inconsistent identity/art/audio | Versioned style/character/rig/audio profiles + machine thresholds finalized before job READY + director visual/listening approval |
| Invalid imports | Scale/pivot/normals/material/texture/rig/clip/collision/audio/schema tests + selected-engine import/build; generation success != usable artifact |
| Silent automation mistake | Content hashes bind validation/approval/dependencies/importer/build; changed input invalidates affected graph; missing evidence never PASS |
| Partial job/failed retry/cost growth | PLANNED→GENERATED→VALIDATED→APPROVED→IMPORTED→BUILD_VERIFIED; typed failure/RETRY/NEEDS_REVIEW/REJECTED, bounded attempts/ledger; approved originals preserved |
| Runtime quota/uncertain billing | Optional disabled default, frozen accepted packages/offline fallback; reserve B06 typed job/window caps, current RPM/RPD/TPM only verified; uncertain call reconcile/defer, no blind retry |
| Accidental gameplay authority | Runtime candidate validated/persisted before explicit ingestion COMMIT; no provider call during engine evaluation/replay; art geometry cannot silently define rules |

## 5. Requirement Closure / Patterns

Design controls address all F/AP/C; implementation evidence for every row remains NOT_RUN. Requirement closure is not order readiness or proof of enforcement. Full AP/historical59-row residency matrix:[B07 B1](BLOCK_07.md); authoritative gate mapping:[B08 B3](BLOCK_08.md).

| ID | Final design owner / prevention / planned evidence |
|---|---|
| F-01 | B02 A1 DAG/phase barriers; boot cycles/unknown dependency/write-conflict tests |
| F-02 | B02 A2/A3 feature-local immutable payloads/deltas/presenters; registry-only extension review |
| F-03 | B02 A2+B03 A5 declared/observed access; B07 CUST01 actual-path differences |
| F-04 | B03 A6 replay +B07 B2 live coverage/unwired distinction; no file-exists DONE |
| F-05 | B03 A6 scoped SHA256 RNG/order/fixed-point/semantic time; hashseed/independent vectors |
| F-06 | B04 A7 typed commands/query; client/LLM cannot set outcomes; invalid0mutation |
| F-07 | B05 A10 schemas/refs+B06 A14 approval/import; new-schema descriptive migration only |
| F-08 | B07 B2 native-source reports/bounded human intent; stale/not-run evidence explicit |
| F-09 | B08 B4/B5 one responsibility/live trigger/search/MASTER bootstrap; no unsupported standalone completion |
| F-10 | B02–B04 COMMIT/component ownership +B07 dependency layers; split driver/services, no engine cross-calls |
| AP-01 | B02 types+B08 strict mypy/ANN401; reviewed narrow I/O whitelist, no domain Any |
| AP-02 | B02 boundary errors/degraded+B08 Ruff; exception≠successful empty result |
| AP-03 | B08 TID251/domain pure tests; mocks external adapters only |
| AP-04 | B07 file/test/live-body evidence+B08 gates; Protocol ellipses not production stubs |
| AP-05 | B03 fresh scoped services/repeated &X,Y vsY,X replay; Final not deep immutable |
| AP-06 | B03 semantic RNG/order/ticks/quantize-before-branch+B08 TID251; no custom linter |
| AP-07 | B03 pinned golden+B08 authorized separate behavior change/test protection; no destructive refactor |
| AP-08 | B03 recursive views/COW/deep immutable DTO/soleCOMMIT; nested mutation cases |
| AP-09 | B07 one-way layers+B08 import-linter; boot/runtime/type cycles tested |
| AP-10 | B03 independent invariants+B08 engine mutation≥80% TARGET; no assert-count acceptance |
| AP-11 | B03 composition/boundary vectors+B08 meaningful non-equivalent mutation; no implementation-derived oracle |
| C-01 | B04 T0 structured memory+B06512MiB Brain+B05 local IPC; complete without T1/server |
| C-02 | B06 typed BYOK quota/job/window/uncertain-call ledger; paid production separate, offline replay |
| C-03 | B03 full-A composition+B05 tick/wake/exact-skip/Bbounds; allCORE A+B hashing, no A from B |
| C-04 | B03 observations+B07 CUST01/native coverage; unused declaration/unconsumed field/unreachable code distinct |
| C-05 | B04 durable recovery+B05 collision/JobObject/heartbeat/kill matrix; bundle qualification pending |
| C-06 | Nine separate design blocks; stop after B09; brief chat/linked contracts/bounded resume; no implementation |

Industry patterns:ports/adapters, modular monolith, immutable messages/CQRS read views, unit-of-work transaction, event queues, deterministic replay, content-addressed build artifacts, staged CI. Project deviations:Python cooperative runtime guard is not a hostile-code sandbox; per-phase barriers instead of same-phase dependency visibility; semantic tick event IDs exclude transport revision; full-A composition excludes protocol receipts; exactly four bootstrap items/two thin wrappers/no early report. Each deviation supports explicit ownership or a lean bootstrap, rather than copying v1 modules.

## 6. §10 Self-check — 34 Items

✅=design requirement internally specified with linked evidence; not runtime PASS. ❌=literal full-roadmap requirement still partly unmet. Phase0 compatibility/contracts/orders now finalized; items6/34 remain PARTIAL because later source-specific orders are DRAFT. No final accepted architecture/all-future-order READY claim; implementation entry still inspects actual predecessors.

| # | Check | Status / one-line evidence |
|---|---|---|
| 1 | Custom checker count | ✅ Planned2/max3/actual0; B07 B0 CUST01/02 |
| 2 | Why custom layer necessary | ✅ B07 B0:standard tools do not join observed access to manifest or project refs/approval/hash relationships |
| 3 | Phase0 exactly four | ✅ §2.1 P0-002/004/001/003; no fifth implementation item |
| 4 | Honest standard-tool labels | ✅ B07/B08 distinguish standard/runtime/wrapper; no replacement/tool installation claimed |
| 5 | Governance effort/ROI | ✅ §4.3 ESTIMATE8–16person-days,48–96hours; scoped loss-prevention and review rule |
| 6 | Engine extension / Sol-ready roadmap | ❌ PARTIAL:B02 registry≤1existing production file TARGET; Phase0 pins/contracts/four orders complete; later source-specific orders DRAFT |
| 7 | Prevent god turn function | ✅ B02 driver only orchestrates phase barriers; feature computations/read/delta/event ownership; no engine cross-call |
| 8 | No central presentation expansion | ✅ B02 A3 feature-local presenters/payload registrations; public projections B05 |
| 9 | Remove human execution order | ✅ B02 stable compiled manifest DAG, not manually ordered runtime calls |
| 10 | Boot conflicts/cycles | ✅ B02 A1 rejects expanded overlapping writes and invalid/cyclic dependency nodes |
| 11 | Primary replay barrier/AP05/07/10/11 | ✅ B03 A6 required matrix/independent outcomes; P0-003 first regression harness |
| 12 | AI replay freeze policy | ✅ B03/B06 versioned hashed accepted packages persisted before use; no live replay AI |
| 13 | Field usage/reachability evidence | ✅ B03 recursive observations+B07 declaration/body coverage distinctions; no static-magic claim |
| 14 | Delayed causality persisted | ✅ B03 typed due queues+semantic causes/order+B04 durable pending state |
| 15 | Full TierA composition test contract | ✅ B03 A6/B05 A11 allA fields/pending/cursors/splits; actual property tests NOT_RUN |
| 16 | Schema hash/tier classification | ✅ B03 FieldSpec+B05 leaf schemas; CORE A+B hashed, DERIVED excluded |
| 17 | Numeric runtime targets/method | ✅ §4.2+B06 turn100/250ms,Brain512MiB,total2048MiB with device/method/failure; actual UNVERIFIED |
| 18 | Versioned atomic migration | ✅ B04 A9 explicit supported-v2 chain/consistent temp flush replace; v1 unsupported |
| 19 | Local T0 complete | ✅ B04 A8 structured memory/context; no T1/vector/DB server prerequisite |
| 20 | Player no service installs | ✅ B01/B05 bundled helper+SQLite/IPC/supervision; packaging proof deferred |
| 21 | Graphical no per-turn LLM | ✅ B01/B04/B05 typed graphical commands; optional generation B06 outside turns |
| 22 | Production/BYOK quota split | ✅ B06 A14 windows/calls/tokens/current RPM/RPD/TPM/fallback; no free-turn guarantee |
| 23 | Opt-in evaluation/artifact gate | ✅ B06 A14 explicit evaluation opt-in/hash-bound validation/approval/import/build |
| 24 | Provisional client/lifecycle | ✅ B01 client gate+B05 A12 isolation/collision/cleanup/kill matrix; OS deployment proof UNVERIFIED |
| 25 | Final/contamination | ✅ B03/B08 deep immutable children/fresh services/repeated/reversed traces; Final alone insufficient |
| 26 | Quantization/transcendentals | ✅ B03 ties-to-even integer before branch; authoritative transcendental ban |
| 27 | Exception defenses | ✅ B02 boundary guard/degraded+B08 Ruff E722/S110/S112/BLE001; no swallowed success |
| 28 | Recursive proxy/no assignment AST | ✅ B03 A5 typed recursive children/maps/sequences/epoch views; no custom state-assignment checker |
| 29 | Proxy target/measurement | ✅ §4.2+B06 paired CPU≤10% TARGET; laptop/DEV-B/MIN-SPEC method; MEASURED UNVERIFIED |
| 30 | Bounded mutation | ✅ B08 engines-only weekly/phase≥80% meaningful kill TARGET; timeouts/equivalence/unrun explicit |
| 31 | Standard banned APIs | ✅ B08 Ruff TID251; no custom nondeterminism linter |
| 32 | Historical/AP four-layer residency | ✅ B07 exact59rows AP11+historical48;2custom; active policy remains proposal pending approval |
| 33 | Deterministic CI counters/time honesty | ✅ B06 WorkBudget+B08 G08; gate58+2=60s TARGET, not measured/absolute machine timing |
| 34 | Report/Factory/register/ready orders | ❌ PARTIAL:B07 bounded native report+B01 decision register+B06 A14 complete; Phase0 instructions finalized; later implementation-order authoring deferred |

Result:32/34 full-packet design checks complete;6/34 PARTIAL for later source-specific readiness. Phase0 portions of AR-010/011 closed with actual tool evidence and complete prospective contracts; later qualification is deferred, not fabricated. B09 READY_FOR_REVIEW; parent ARCH-002 IN_PROGRESS. Gameplay/runtime/deployment/independent-person proof UNVERIFIED.

## Completion / Next

Saved:dependency roadmap, four-item bootstrap, concrete order packet, READY document-review order, version/platform checklist, capability preservation, numeric resource targets, ESTIMATE governance effort, explicit risks and34-item self-check.
Document checks/evidence:[BACKLOG](../BACKLOG.md), [handoff](../SESSION_HANDOFF.md). Isolated selected-tool mypy/pytest/Ruff compatibility probes PASS; project runtime/type/replay/coverage/mutation/CI/performance/provider/import/build NOT_RUN. Later compatibility/independent review UNVERIFIED. No active policy/code/v1 edits.
Next **step3 Phase0 implementation** only after the director requests it, using [four finalized orders](../docs/work_orders/PHASE0_WORK_ORDERS.md). PREFLIGHT-001 Phase0 DONE; exact pins/native probes/independent vectors linked in its evidence. No rootconfig/src/tests/CI implementation yet. Later qualification/ready-order authoring deferred to corresponding entry.

--- BLOCK 9/9 END. Later readiness deferred; Phase0 instructions finalized; implementation NOT_STARTED. ---
