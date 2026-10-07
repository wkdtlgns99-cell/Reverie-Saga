# Reverie Saga — Backlog

Updated:2026-10-07 (Asia/Seoul). Task/status/dependency SSOT;engineering authority:[prompt](docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md),product:[MASTER](docs/MASTER_GAME_ARCHITECTURE.md).
Orders/evidence:docs/work_orders;designs:architecture. Read [current handoff](SESSION_HANDOFF.md) before execution.
Every backlog delivery also updates [Korean progress](GAME_SYSTEM_SUMMARY_KO.md);do not copy full specifications here.
Complete pre-QT-F03 logs/IDs/prerequisites/commands/failures:[historical backlog](docs/history/BACKLOG_2026-10-07.md). Historical NEXT statements are non-operative;source orders remain authoritative for acceptance details.

## Current Snapshot — 2026-10-07

- Phase0 and RS-P1-CORE representative slice DONE:movement/door/combat/rest,timed rule-based NPC/events,SQLite save/load/recovery/replay;not the full world/cognition or finished graphical game.
- RS-P1-QUALITY sequence and RS-CLIENT-001/002 DONE. Latest runtime evidence:[action history acceptance](docs/work_orders/RS-CLIENT-002_ACTION_LOG.md),1242PASS283.95s,focused36PASS twice,replays45PASS,strict mypy96files/shared+selective lint/scoped format/dependencies3+1contracts PASS. These are prior runs,not fresh QT-F03 checks.
- Native desktop combat/save/load narration observed;original QT-F01 UX_NOT_ACCEPTED retained. Updated human UX/final graphics/device/release/remote CI/independent review remain UNVERIFIED.
- GOV-01/02 DONE;GOV-03 order READY,implementation DEFERRED/G07 NOT_ACTIVE. RS-P1-GOV and RS-ARCH-002 remain IN_PROGRESS;B09 READY_FOR_REVIEW/#6/#34 later-order readiness PARTIAL.
- QT-F03 DONE. [QT-F04 investigation](docs/work_orders/QT-F04_PROVENANCE.md) recorded;rights remain UNVERIFIED,not DONE. Director deferred CP02 once because Claude usage is exhausted;resume when usage is available,before reuse. CP01 still holds core/client expansion;QT-F02/graphics/engine/modeling-AI/QT-F05 stay deferred. Current request authorizes publication of accumulated work only;no new reuse imports,purchase,bulk assets or expansion.

## Highest Priority — Director Execution 2026-10-07

Director-approved [quality/client order](docs/work_orders/RS-P1-QUALITY.md);all eight entries below accepted. Detailed outcomes belong to linked orders/history;rules do not guarantee error-free code.

| Order | ID | State | Scope / acceptance |
|---|---|---|---|
| 1 | RS-P1-QUALITY-01 | DONE | Canonical quality/repair policy;UTF8/links/diff checks PASS |
| 2 | RS-P1-QUALITY-02 | DONE | Root AGENTS router ≤40lines;links/authority checks PASS;future-session discovery not simulated |
| 3 | RS-DOC-002 | DONE | Actual runtime/commands/document index README;UTF8/links PASS,strict mypy89files PASS |
| 4 | RS-P1-QUALITY-03 | DONE | Selective E501/PT011 and Windows CI configuration;native local gates and both PT011 probes PASS;remote Actions run UNVERIFIED |
| 5 | RS-P1-QUALITY-04 | DONE | Canonical repair/retest/evidence loop linked in work-order acceptance;document checks PASS |
| 6 | RS-P1-QUALITY-05 | DONE | Driver responsibility split/static indexes,encounter SCHEMA/domain constants,precise corruption assertions;full1206tests274.33s PASS;stored fixtures unchanged |
| 7 | RS-CLIENT-001 | DONE | Typed input/derived projection,Tk screen,single-worker durable lifetime;15focused tests and final1221tests280.39s PASS;not final HD-2D qualification |
| 8 | RS-CLIENT-002 | DONE | [Korean action/dialogue history](docs/work_orders/RS-CLIENT-002_ACTION_LOG.md):bounded bottom panel,postcommit explanations,rejection/retry/load;focused36/full1242tests283.95s PASS,actual desktop combat/save/load observed;graphics deferred |

## Claude Checkpoints and Defect Repair — 2026-10-07

Director-approved scheduling only;no Claude review/repair executed by recording it. Follow the [canonical review/repair procedure](docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md#claude-checkpoints-and-defect-repair--director-rule-2026-10-07);timing/status SSOT is this table. At trigger:notify director → prepare actual files/tests/evidence packet → obtain Claude feedback → verify findings → scoped fixes/retests → close. Hold only the named dependent step;QT-F04 read-only investigation may proceed while CP01 awaits feedback.

| ID | State | Insert after / before | Review focus / held downstream step |
|---|---|---|---|
| RS-REVIEW-CP01 | TODO | NOW:after QUALITY-05 + CLIENT-002;before next gameplay/core/client expansion | Driver atomic/retry/read lifetimes,encounter contracts,worker ownership,fact-based narration/tests;packet includes actual turn/encounter/client session-worker-text and unit/replay/integration callers. Existing1242PASS is prior evidence,not external review |
| RS-REVIEW-CP02 | DEFERRED | Director-approved one-time delay:Claude usage exhausted;resume when available,before RS-V1-MIGRATION/any new reuse import | [Prepared packet](docs/reviews/RS-REVIEW-CP02_REQUEST.md) retained;refresh actual input hashes before forwarding. Feedback NOT_RECEIVED,not DONE/waived. Hold imports until evidenced rights and verified review/fixes;CP01 unchanged |
| RS-REVIEW-CP03 | DEFERRED | After QT-F02 content generalization + first small playable content segment,when authorized;before more engines/bulk content | Multiple independent scenarios,no fixed-target leakage,live consumers/quest consequences/bounds,integrated save-load/replay;hold scenario/world expansion until valid findings repaired |
| RS-REVIEW-CP04 | DEFERRED | When graphics resumes:after first Brain↔graphical-client room/import sample;before final engine commitment/bulk assets | CORE ownership,coordinate/identity mapping,input/retry/resync,load/UI history,asset provenance/scale/pivot and measured render performance;not final art approval |
| RS-REVIEW-CP05 | DEFERRED | At first major NPC memory/quest/save-contract change:before implementation for contracts,then after first integrated implementation | Determinism,causal events,memory bounds,persistence/migration/compatibility/failure cases;hold implementation until contract pass and larger integration until repair/retest pass. Track both review passes separately |
| RS-REVIEW-CP06 | DEFERRED | After integrated feature/content freeze;before RS-RELEASE acceptance/public distribution | Native full regression/replays/crash/offline/device/build/license evidence and unresolved findings;hold release. Review is not release QA or permission to publish |

## External Feedback — Quilltale Comparison (2026-10-07)

RS-REVIEW-QT-001 DONE for [feedback storage/triage](docs/reviews/CLAUDE_QUILLTALE_FEEDBACK_2026-10-07.md) only. Existing rules retained;no copied rulebook or v1 engine/schema port.

| ID | State | Follow-up / entry and acceptance |
|---|---|---|
| QT-F01 | DONE / feedback and next order | [Playtest record](docs/reviews/QT-F01_PLAYTEST_2026-10-07.md):human feedback recorded;bounded RS-CLIENT-002 order authored and accepted. Original UX_NOT_ACCEPTED retained;graphics deferred by director,not final HD-2D or human acceptance of the updated panel |
| QT-F02 | DEFERRED | Generalize fixed scenario targets/content only when needed;content contract plus multiple independent scenarios before reusable-content claims;no v1 engine/formula/schema port;then CP03 review/repair before further expansion |
| QT-F03 | DONE | [Document compaction acceptance](docs/work_orders/QT-F03_DOCUMENT_COMPACTION.md);complete linked snapshots recover exactly after presentation normalization,42task rows retained,UTF8/links/fragments/hash/scope checks PASS;no gameplay change |
| QT-F04 | UNVERIFIED | [Investigation recorded](docs/work_orders/QT-F04_PROVENANCE.md):actual origin/Aeesh shared blobs,6source IDs and4newline witnesses verified;no license grant established. Need artifact-specific authorship/permission evidence and CP02 dispositions before reuse;not rights-qualified/DONE |
| QT-F05 | OPTIONAL / DEFERRED | Proposed non-authoritative NPC-line LLM adapter experiment;separate approved contract/order,offline fallback and unchanged deterministic replay,no new mandatory provider/UI stack |

## Priority Tasks

Owner:Sol;Astra blocker advice only. READY does not authorize agent/model changes.

| ID | Priority | State | Task | Dependency / artifact / acceptance |
|---|---|---|---|---|
| RS-DOC-001 | P0 | DONE | Handoff/backlog/order foundation | Earlier role split superseded by DOC-003; retain foundation/evidence |
| RS-DOC-003 | P0 | DONE | All development assigned to Sol | Prompt/MASTER/context/orders agree; Astra blocker-only; `docs/prompts/SOL_CODING_WORK_ORDER.md` |
| RS-DOC-004 | P0 | DONE | English compact AI documentation | Director-authorized rule;8 active docs in compact English; contracts/status/IDs/links verified; no next BLOCK |
| RS-REUSE-001 | P0 | DONE | v1 evidence/inventory | `architecture/V1_REUSE_INVENTORY.md`; broad code/formula/test migration rejected |
| RS-CONTENT-001 | P0 | DONE | Six curated narratives | `docs/reference/QUILLTALE_CONTENT_CANDIDATES.json`; hash/entry/field trace; no mechanics/runtime import |
| RS-ARCH-001 | P0 | DONE | BLOCK1 architecture | `architecture/BLOCK_01.md`; decision register/F/AP/C/layers/conflicts/targets/risks; self-review only |
| RS-DOC-002 | P0 | DONE | Root README runtime/index | Approved QUALITY refresh;actual state/commands/links verified |
| RS-ARCH-002 | P0 | IN_PROGRESS | BLOCK2–9 contracts/governance/roadmap | B02–08 DONE; B09 READY_FOR_REVIEW, #6/#34 order-readiness gaps; no final accepted-architecture claim |
| RS-ARCH-003 | P0 | DONE | Review candidate design gaps/conflicts | [ARCHITECTURE_REVIEW](architecture/ARCHITECTURE_REVIEW.md);Step1 historical11findings/9CLOSED/2OPEN; Phase0 readiness resolved by PREFLIGHT-001 addendum;27F/AP/C+34checks; self-review only; independent/runtime UNVERIFIED |
| RS-PREFLIGHT-001 | P0 | DONE | Selected runtime/tool compatibility +Phase0 instructions | [preflight](docs/work_orders/RS-PREFLIGHT-001_COMPATIBILITY.md),PHASE0_WORK_ORDERS/CONTRACTS/TOOLCHAIN/REFERENCE_VECTORS;13pins/native probes/literal vectors/document checks PASS; later family qualification deferred; not fifthPhase0 |

## BLOCK2–9 Breakdown

Parent remains IN_PROGRESS until children/readiness close. DONE here is design acceptance,not all future runtime capabilities. Candidate review may precede final acceptance.

| ID | State | Scope | Prerequisite / PLANNED artifact |
|---|---|---|---|
| RS-ARCH-002-B02 | DONE | A1 scheduler; A2 Protocol/manifest; A3 presentation | `architecture/BLOCK_02.md`; design self-review + Python3.13.12 syntax checks; runtime/type/behavior evidence UNVERIFIED |
| RS-ARCH-002-B03 | DONE | A4 delayed events; A5 state/proxy; A6 RNG/replay | `architecture/BLOCK_03.md`; self-reviewed design, BLOCK2 aligned; document/Python3.13.12 syntax PASS; behavior/property/performance UNVERIFIED |
| RS-ARCH-002-B04 | DONE | A7 commands; A8 memory/retrieval; A9 save/migration | `architecture/BLOCK_04.md`; self-reviewed design + BLOCK2/3 alignment; document/Python3.13.12 syntax PASS; runtime/type/crash/migration/quality/performance UNVERIFIED |
| RS-ARCH-002-B05 | DONE | A10 schema/content; A11 time/LOD; A12 IPC/lifecycle | `architecture/BLOCK_05.md`; self-reviewed design + BLOCK2 alignment; document/Python3.13.12 syntax PASS; runtime/schema-export/LOD/client/lifecycle/performance UNVERIFIED |
| RS-ARCH-002-B06 | DONE | A13 budgets/observability; A14 Factory/generation | `architecture/BLOCK_06.md`; document/Python3.13.12 syntax/arithmetic PASS; BLOCK1 counter units aligned; runtime/allocation coverage/measurement/provider/import/build UNVERIFIED |
| RS-ARCH-002-B07 | DONE | B0 layers; B1 rule residency; B2 evidence reports | `architecture/BLOCK_07.md`; AP11/v1-48 matrix + document/Python3.13.12 syntax/reading-budget checks PASS; active policy/tool/report/coverage execution NOT_RUN |
| RS-ARCH-002-B08 | DONE | B3 eleven gates; B4 scope; B5 sessions | `architecture/BLOCK_08.md`; exact11=4standard/5harness/2custom,58+2=60s TARGET; document/Python3.13.12 syntax/arithmetic PASS; policy/tool/CI/runtime NOT_RUN |
| RS-ARCH-002-B09 | READY_FOR_REVIEW | Work-order roadmap; risks; §10 self-check | `architecture/BLOCK_09.md`;32/34full-packet checks, #6/#34 later readiness PARTIAL; Phase0 four instructions FINALIZED/preflightDONE; no all-future-ordersREADY claim |

## Phase0 — Exactly Four Implementation Items

Executed in dependency order RS-P0-002 → RS-P0-004 → RS-P0-001 → RS-P0-003 after approved preflight/contracts/request. [Orders/contracts/vectors/acceptance](docs/work_orders/PHASE0_WORK_ORDERS.md).

| ID | State | Prerequisite | Item | Actual acceptance |
|---|---|---|---|---|
| RS-P0-002 | DONE | ARCH-003/PREFLIGHT-001/request | Ruff+mypy strict | Exact TOML/hash and13locked wheels; native install/pip check, nine-rule/strict/generic/package/subprocess probes PASS |
| RS-P0-004 | DONE | P0-002 + state/proxy contract | Recursive read-only proxy | Nine tests; nested mutation/order/cache/slices/iterator expiry/epoch/registration/bounds PASS; real driver integration |
| RS-P0-001 | DONE | P0-004 + command/state/event/scheduler contracts | One-turn walking skeleton | Real Stepper/Counter ±1/0; complete literal publications match; admission/retry/atomic abort/manifest/phase visibility/finally/presentation/CLI PASS |
| RS-P0-003 | DONE | P0-001 + RNG/hash/replay contract | Golden replay | Five independent golden steps, RNG/rejection/exhaustion, witness corruption/leaf diagnostics/fact loss, repeat/world-order/cache and fresh hashseed0/1/2249326019 PASS; total37tests |

## First Gameplay Slice — DONE / Later — DEFERRED

CORE-01 → CORE-02 → CORE-03 → CORE-04 → CORE-05 → [parent integration review](docs/work_orders/RS-P1-CORE_INTEGRATION_REVIEW.md) DONE. Orders retain exact source/contract/error/oracle/acceptance prerequisites;no invented CORE-06.

| ID | Task | Entry condition |
|---|---|---|
| RS-P1-CORE | Combat/movement/interaction/events/save/representative NPC/world | First representative headless slice DONE;CORE-01/02/03/04/05 DONE;[integration acceptance](docs/work_orders/RS-P1-CORE_INTEGRATION_REVIEW.md). Combined movement/interaction/combat/NPC/save-load/replay path;1113tests. Full world/cognition/client remain future capabilities |
| RS-P1-GOV | import-linter/coverage/manifests/reports/counters/migration | IN_PROGRESS:GOV-01/02 DONE;GOV-03 order READY/implementation DEFERRED behind quality/client;later controls DEFERRED;custom planned2/current0/max3,commit gates11 |
| RS-CLIENT | Camera/modular-assets/client performance prototype | Brain/client boundary; final choice after measurements;CP04 after first graphical sample,before final engine/bulk assets |
| RS-FACTORY | Content/image/3D/animation/audio validation/approval/import | Stable contracts; fixed SD1.5+LoRA+ADetailer; pre-generation;applicable CP02/04 before dependent reuse/bulk imports |
| RS-V1-MIGRATION | Selected descriptive content in new schema | CONTENT-001 + importer + QT-F04 source/license qualification;new IDs/effects/stats/links,no old code/formulas/oracles/schema;CP02 review/repair before import |
| RS-BULK | Bulk approved content/assets | Import/license/provenance/validation/approval gates pass;applicable CP02/03/04 review dispositions/fixes accepted first |
| RS-RELEASE | Optimization/bundle/lifecycle/MIN-SPEC/release QA | Playable integrated build;CP06 review/repair plus actual release qualification before distribution |

## Evidence / Resume

- [GOV-01 qualification](docs/work_orders/RS-P1-GOV_01_QUALIFICATION.json),[GOV-02 activation](docs/work_orders/RS-P1-GOV_02_ACTIVATION.json),[GOV-03 READY order](docs/work_orders/RS-P1-GOV_03_REPLAY_BODY_COVERAGE.md). Refresh GOV-03 source/input fingerprints before any future execution;G07/3s/all11-gate/device targets UNQUALIFIED.
- [Quality/client acceptance](docs/work_orders/RS-P1-QUALITY.md),[action-panel acceptance](docs/work_orders/RS-CLIENT-002_ACTION_LOG.md),[negative playtest/next order](docs/reviews/QT-F01_PLAYTEST_2026-10-07.md). Initial1241PASS/1Tk setup failure remains in evidence;final1242PASS is a distinct corrected run,not hidden failure or approval of visual quality.
- [QT-F03 acceptance](docs/work_orders/QT-F03_DOCUMENT_COMPACTION.md):documentation checks PASS,self-review only. Runtime tests NOT_RUN for this task. Preserve historical publication records in the linked snapshot;past upload permission is not new commit/push authority.
- Director-approved Claude checkpoint scheduling2026-10-07:6UTF8 docs/80local links/8fragments/fences/diff checks PASS;42existing task rows retain IDs/states/prerequisites,6pending/deferred review rows added. Exact6existing docs changed/166of172entry files byte-identical/HEAD unchanged;no runtime tests or Claude review executed by scheduling.
- QT-F04:read-only provenance investigation recorded;rights UNVERIFIED/no imports. CP02 packet PREPARED/review DEFERRED once by director due to usage exhaustion;feedback NOT_RECEIVED. Refresh packet inputs on resume;manual director-forwarded review remains required before reuse. Native game tests NOT_RUN;prior1242PASS historical;CP01 unchanged.
- Historical Git/source/task transitions and detailed acceptance logs:[backlog archive](docs/history/BACKLOG_2026-10-07.md),[handoff archive](docs/history/SESSION_HANDOFF_2026-10-07.md). Do not import historical v1 task lists or delete task IDs.

## Status / Acceptance

TODO=unmet prerequisites;READY=complete order,not executed;IN_PROGRESS=active;READY_FOR_REVIEW=evidence awaiting acceptance;DONE=scope accepted by self-review unless stated otherwise;BLOCKED=concrete impediment;DEFERRED=later phase;UNVERIFIED=missing evidence.
Document DONE is not implemented gameplay/product approval. Code DONE requires actual files/live path/results/stage-appropriate tests/replay. Self-review is not independent review;historical counts are not fresh verification.

## Publication — Director Request 2026-10-07

- Scope:31 accumulated changed/new files,quality rules/router/README/CI,core cleanup/client/action history/tests,feedback/checkpoints/provenance and lossless document archives. Director authorized commit/push to existing origin/main;no force-push or private/generated files.
- State:LOCAL_VERIFIED/PUSH_PENDING. Fresh full1242PASS278.98s,shared/selective Ruff,11-file format,mypy96files,import contracts3+1 PASS;18UTF8 docs/210local prose links/fences/staged diff checks PASS. Secret-pattern/path scan PASS (not exhaustive). Remote main matched b0f98e2;CP01 TODO/CP02 DEFERRED/rights UNVERIFIED unchanged;remote Actions UNVERIFIED.
