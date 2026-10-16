# Reverie Saga — Backlog

Updated:2026-10-16 | Current task/status/dependency SSOT.
Entry:[handoff](SESSION_HANDOFF.md). Execution:[rules](ENGINEERING_RULES.md). Product:[MASTER](docs/MASTER_GAME_ARCHITECTURE.md).
Scope acceptance is local/self-reviewed unless explicitly identified as independent.
Replace current rows when status changes;put execution detail in linked receipts,not another root chronology.

## Current Delivery

PR8 repair2026-10-16:director authorizes CI repair,ordinary merge and local synchronization.
Compatible integration retains courtyard plus current harbor/grove/quest/memory paths and both save identities.
Checkout7/courtyard40/affected82/pin3tests and Unity225checks/build PASS;final merged checks are revision-specific.
[Receipt](docs/reviews/PR08_CI_REPAIR_2026-10-16.md);use the live PR8checks and final delivery for publication acceptance.
Ordinary Unity verification now retains the editor;[workflow](clients/unity/README.md#reuse-the-editor--director-preference-2026-10-16).

| ID | State | Result / evidence |
|---|---|---|
| RS-P1-GOV-03 | LOCAL_ACCEPTED,published86ba74c | Manual producer/read-only assessor:8replays/35body hits/200inputs;110new tests/full1897PASS. Identical assessment,no writes;[evidence](docs/work_orders/RS-P1-GOV_03_ACTIVATION.json). Full uses identical Tcl copy;original Tk error/symlink/timing limits retained;CI NOT_ACTIVE |
| RS-P1-GOV-03R | LOCAL_ACCEPTED,published4257d4f | GOV-03 scope refreshed:35methods/12classes/8sources,8replays PASS/all35body hits. Planning/probe only. [Receipt](docs/reviews/RS-P1-GOV_03_SCOPE_REFRESH_2026-10-16.md) |
| QT-F24 | LOCAL_ACCEPTED,published4257d4f | Unity wait1/4/8/16presets;515Python/native7modes519/build/static and24readbacks PASS. [Receipt](docs/reviews/QT-F24_EXECUTION_2026-10-16.md) |
| QT-F23 | LOCAL_ACCEPTED,published4257d4f | Unity slot01–08selector/shared save-load-preview;452native/Windows build,46Python/static and24save readbacks PASS. [Receipt](docs/reviews/QT-F23_EXECUTION_2026-10-16.md) |
| RS-V3-R1 | LOCAL_ACCEPTED,published4257d4f | Real malformed HTTP reproduced;transient classification/child-parent retry fixed. [Receipt](docs/reviews/RS-V3-R1_EXECUTION_2026-10-16.md);combined225affected/static PASS |
| QT-F22 | LOCAL_ACCEPTED,published4257d4f | Explicit read-only retained-save inventory;17new cases,combined225affected/static PASS. No deletion/cap change. [Receipt](docs/reviews/QT-F22_EXECUTION_2026-10-16.md) |
| RS-DOC-005 | LOCAL_ACCEPTED | Compact entry/navigation;[receipt](docs/reviews/RS-DOC-005_EXECUTION_2026-10-16.md). Documentation support;runtime unchanged |
| QT-F21 | LOCAL_ACCEPTED,published4257d4f | Compact Unity controls/history;307 native checks,51 Python tests/build/static PASS. [Receipt](docs/reviews/QT-F21_EXECUTION_2026-10-16.md) |
| QT-F18–20 | LOCAL_ACCEPTED,published at 0e06577 | Saved-memory comparison,recent inspection,slot preview;[F18](docs/reviews/QT-F18_EXECUTION_2026-10-15.md),[F19](docs/reviews/QT-F19_EXECUTION_2026-10-15.md),[F20](docs/reviews/QT-F20_EXECUTION_2026-10-15.md). F20 full:1741 PASS,historical evidence |
| Publication / CI | Current branch publication requested | Current director authorizes ordinary PR8merge and local update after passing checks;CP06release remains held. CI remains revision-specific |
| V3 additional independent review | STOPPED / PARTIAL by director2026-10-16 | Latest supplied [feedback/dispositions](docs/reviews/OPEN_WORK_V3_FINAL_DISPOSITIONS_2026-10-16.md);clone-cap defect withdrawn,R1locally repaired. No further Claude request;whole-review coverage remains incomplete |
| A1–A3 / D5 bounded repair | LOCAL_ACCEPTED | Approved harbor prose,ordinary memory client,reconciliation;[closure ledger](docs/reviews/OPEN_WORK_CLOSURE_2026-10-14.md),[D5receipt](docs/reviews/RS-STRUCT-001_EXECUTION_2026-10-14.md). Broader closure remains open |

## Adopted Architecture Direction — 2026-10-16

Direction only;not an implementation order or completion claim.

- Keep deterministic code authoritative for state,events,replay and persistence. Use RAG for retrieval and a shared optional LLM for bounded dialogue or proposals,never factual calculation.
- Simulate gameplay-relevant off-screen changes through exact ordered events/catch-up;freeze only proven no-op or cosmetic state.
- Continue with Unity 3D/HD-2D plus selective sprites. Treat low-spec performance as UNVERIFIED until measured on target hardware;do not infer speed from abstraction or art style.
- Prefer one bounded end-to-end village slice across categories2–7 before broad legacy migration,bulk assets or more general governance tooling:accept quest → travel/combat → off-screen change → changed NPC return → report/reward → save/restart.

## Priority Tasks

No automatic next task. On explicit execution request,select one bounded order with current contracts;
old READY labels or historical permissions alone do not authorize implementation/publication.

| ID / audit group | State | Required entry / remaining scope |
|---|---|---|
| D2 | OPEN,staged scope authorized | World/NPC/memory/retrieval beyond two conversation records;[audit](docs/reviews/OPEN_WORK_AUDIT_2026-10-14.md),[closure order](docs/work_orders/OPEN_WORK_CLOSURE_2026-10-14.md). F08–20cover bounded subsets only |
| RS-V1-MIGRATION / D3 | IN_PROGRESS | 326 screened,6 descriptions imported,319 queued+1 rewrite. Artifact-specific rights,adaptation,new contracts/import validation required;[F06](docs/work_orders/QT-F06_NARRATIVE_IMPORT.md). No legacy mechanics/code/formulas/oracles/schema port |
| RS-P1-GOV / D4 | IN_PROGRESS | GOV-01/02 DONE;[GOV-03manual command](docs/work_orders/RS-P1-GOV_03_CURRENT_IMPLEMENTATION.md) LOCAL_ACCEPTED:35methods/8sources/8traces/200inputs,full1897PASS. Further controls need current bounded orders;3s/all11/device/CI targets unqualified |
| RS-ARCH-002 / D6 | IN_PROGRESS | B02–08 design DONE;B09 READY_FOR_REVIEW,#6/#34 later-order readiness PARTIAL;[BLOCK09](architecture/BLOCK_09.md). Design completion does not qualify runtime |
| RS-RELEASE / D7 | OPEN,CP06 held | Standalone packaging/lifecycle/crash timing/offline/device/MIN-SPEC/human UX/final engine qualification;no security bypass. F21 layout repair does not establish human UX acceptance |
| RS-STRUCT-001 residuals | CONDITIONAL / DEFERRED | D5postcommit/load-close repairs accepted;remaining codec-extension/format/performance follow-ups need demonstrated scope,not a broad rewrite. [Original risks](docs/reviews/RS-REVIEW-CP01_DISPOSITIONS.md#findings) |
| RS-FACTORY / RS-BULK | DEFERRED | Stable modality/content contracts,provenance/license,validation,actual approval/import/build and applicable review gates. Images/modeling/camera(D1) excluded from current closure by director |
| QT-F05 | OPTIONAL / DEFERRED | Non-authoritative NPC-line LLM experiment requires separate order,offline fallback and deterministic replay |
| V4 / V5 | PARTIAL | Director limited run to current PC;other device unqualified. Director confirms Gemini free tier;remaining quota/project identity unmeasured. [Setup](docs/WORKSTATION_SETUP.md) |

## Claude Checkpoints and Defect Repair — 2026-10-07

Canonical [procedure](docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md#claude-checkpoints-and-defect-repair--director-rule-2026-10-07).
Existing checkpoint closures retain their reviewed scope;V3 additional review does not reopen them.
Patch self-review/native tests are not independent patch rereview.

| ID | State | Accepted scope / held downstream step |
|---|---|---|
| RS-REVIEW-CP01 | DONE | Core/client failure repair;[dispositions](docs/reviews/RS-REVIEW-CP01_DISPOSITIONS.md). F4residuals routed to STRUCT-001 |
| RS-REVIEW-CP02 | DONE | Full-input document consistency;[repair](docs/work_orders/RS-REVIEW-CP02_FULL_REPAIR.md). No blanket rights/import approval;frozen witness/ZIP retained |
| RS-REVIEW-CP03 | DONE | First embedded two-scenario slice/static feedback/scoped repairs;[dispositions](docs/reviews/RS-REVIEW-CP03_DISPOSITIONS_2026-10-13.md). Broader expansion requires its own contracts |
| RS-REVIEW-CP04 | DONE | First Unity prototype/scoped repairs;[dispositions](docs/reviews/RS-REVIEW-CP04_DISPOSITIONS_2026-10-12.md). Final engine/bulk assets remain separately gated |
| RS-REVIEW-CP05 | CONTRACT + INTEGRATION DONE | First quest/reward;[contract](docs/reviews/RS-REVIEW-CP05_CONTRACT_DISPOSITIONS.md),[integration repair](docs/reviews/RS-REVIEW-CP05_INTEGRATION_DISPOSITIONS_2026-10-14.md) |
| RS-REVIEW-CP06 | DEFERRED / HOLD RELEASE | After integrated feature/content freeze,before release acceptance/public distribution;actual regression/replay/crash/offline/device/build/license evidence and findings closure |

## Accepted Baseline

| Group | Current accepted boundary |
|---|---|
| RS-P0-002→004→001→003 | Four Phase0items DONE;[orders](docs/work_orders/PHASE0_WORK_ORDERS.md) |
| RS-P1-CORE-01..05 / parent | Representative deterministic movement/combat/NPC/events/save/replay DONE;[integration](docs/work_orders/RS-P1-CORE_INTEGRATION_REVIEW.md). Full world/cognition remains future |
| RS-P1-QUALITY-01..06,RS-CLIENT-001..003 | Bounded tooling/client/prototype work DONE;[quality](docs/work_orders/RS-P1-QUALITY.md),[rulebook corrections](docs/work_orders/RS-P1-QUALITY-06_CORRECTIONS.md) |
| QT-F01..04,F06..17 | Accepted bounded work;F01human feedback recorded,original UX_NOT_ACCEPTED retained. [Per-task states/receipts](docs/history/BACKLOG_2026-10-16.md) |
| RS-CI-001/002,RS-ENV-001 | CI/protection and setup routing DONE;[CI](docs/work_orders/RS-CI-002_MAIN_PROTECTION.md),[setup](docs/WORKSTATION_SETUP.md). Protected-main PR/check workflow;per-device qualification separate |
| RS-DOC-001..004,RS-REUSE-001,RS-CONTENT-001,RS-ARCH-001/003,RS-PREFLIGHT-001 | Accepted documents/curation/design/preflight;[full register](docs/history/BACKLOG_2026-10-16.md#priority-tasks). No whole-game/independent/runtime acceptance inferred |

## QT-F07 Deferred Qualification

Actual Gemini calls succeeded under the primary key;generated diagnostics remain NEEDS_REVIEW.
Only the separately approved harbor-memory catalog has production approval. Coarse sanitized HTTP
errors remain intentional;remaining quota,induced HTTP diagnostics and signed provider/human identity
are unqualified. No automatic key rotation/paid fallback. [Workflow](docs/CLI_WORKFLOWS.md).

## External Feedback — Recorded Reviews (2026-10-07)

RS-REVIEW-QT-001 and RS-REVIEW-GPT-001 recording/triage DONE;[records](docs/history/BACKLOG_2026-10-16.md#external-feedback--recorded-reviews-2026-10-07).
Later accepted repairs supersede old pending states,not original evidence.

## Paused for Next Session — Director Request 2026-10-15

Historical pause superseded only by subsequent explicit tasks;V3review now stopped PARTIAL by director.
[Original pause/publication conditions](docs/history/BACKLOG_2026-10-16.md#paused-for-next-session--director-request-2026-10-15).

## Status / History

READY=complete order,not authority;DONE=scope accepted;LOCAL_ACCEPTED=local evidence only;
DEFERRED=not active;UNVERIFIED=missing evidence. Evidence is revision/host/scope specific.
All old IDs,states,failures,permissions and receipts remain in [2026-10-16snapshot](docs/history/BACKLOG_2026-10-16.md)
and [earlier history](docs/history/BACKLOG_2026-10-07.md). Historical NEXT is non-operative.

## PR09 Integration

Preserve the courtyard room and its V1 rules/save identity through the shared current layout path.
Original [room evidence](docs/reviews/QT-F02_ROOM_BINDINGS_2026-10-15.md) and
[Unity evidence](docs/reviews/QT-F02_UNITY_SELECTION_2026-10-15.md) remain historical;
[PR08 repair](docs/reviews/PR08_CI_REPAIR_2026-10-16.md) records current integration acceptance.
