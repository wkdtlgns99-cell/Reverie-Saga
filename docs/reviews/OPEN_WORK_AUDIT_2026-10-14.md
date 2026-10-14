# Open Work Audit — 2026-10-14

Requested:why actual dialogue approval was left pending,and what else was left after completion.
Scope:current backlog/handoff,QTF02/06–15/provider receipts,CP01/03/04/05 dispositions,actual
client/worker/bridge sources,and four known live candidate artifacts. Read-only audit of code/data;
only this register and three progress routers updated. Primary7support,covering categories1–6.
Self-audit;no new implementation/provider/reviewer/approval/publication action.

## Findings and counting rule

15deduplicated follow-up groups:3unfinished delivery links(A),5qualification limits(V),7planned/
explicitly deferred groups(D). This is a bounded register,not fifteen failed tasks or an estimate
of all future game development. Repeated NEEDS_REVIEW/NOT_RUN text is counted once per responsibility.
Historical failures/holds superseded by actual repairs/success are excluded. Future capabilities
excluded from a narrow work order are not silently reclassified as its failed acceptance.

Approval authority:[MASTER](../MASTER_GAME_ARCHITECTURE.md) states
“Human = director/planner/approver”;the workflow is candidate→validation→approval→import.
Existing receipt requires explicit APPROVED/approver/UTC. The human approval was not supplied;
executor cannot invent it. However,content inspection/correction/proposal is executor work and
could have been completed before presenting a concrete approval decision. QTF13–15 continued
building review/compile tooling while the actual prose issue remained unresolved. This is a
sequencing/reporting weakness:tool acceptance was clear in detailed receipts,but short “complete”
messages did not sufficiently emphasize the unclosed overall game path.

## A — Unfinished recent delivery links:3

| ID | Structure | Remaining step / evidence | Current status / closure |
|---|---|---|---|
| A1 |4;3 | Actual candidate editorial review/correction and director decision. Latest completion says “확인했다” although evidence only proves receipt of a report. [QTF13](QT-F13_EXECUTION_2026-10-14.md),[QTF14](QT-F14_EXECUTION_2026-10-14.md),[pending receipt](../../tmp/qt-f15/GEMINI_APPROVAL_PENDING.json) | Tool validation completed;candidate not production-approved. Prepare final concrete prose proposal,then record real director decision. Four unapproved diagnostic bundles are inventoried below;only selected candidate needs approval,old alternatives need not all be promoted |
| A2 |3/6/7;4/5 | Selected real generated candidate→approved catalog→ordinary graphical gameplay verification. QTF15 positive catalog/game tests used AUTOMATED_TEST_ONLY approvals;actual candidate received PENDING only. [QTF15](QT-F15_EXECUTION_2026-10-14.md) | Existing compiler/client can consume a catalog. Actual approved delivery/use not executed;depends on A1. QTF07 did use actual Gemini prose in a Python diagnostic game,so this is not “no real AI game test ever” |
| A3 |7;2/4/5/6 | Persisted NPC-memory option through ordinary client/Unity route. ClientSession has npc_memory=False by default;ClientWorker does not forward that option;EngineBridge/Unity startup has catalog args but no memory mode. [session](../../src/app/client_session.py),[worker](../../src/app/client_worker.py),[bridge](../../src/app/engine_bridge.py),[Unity](../../clients/unity/Assets/Reverie/Scripts/BrainConnection.cs) | Python opt-in feature and standalone preparation verified;normal Unity path does not enable this memory bundle. Essential client integration remains;this is independent of deferred art/camera and does not imply a per-turn LLM requirement |

## V — Unverified/limited qualification:5

| ID | Structure | Limit | Interpretation |
|---|---|---|---|
| V1 |7;2/6 | No single fresh all-green full suite after QTF09 additions. Its full run had1525passes+2new governance expectation failures;the2were repaired/retested successfully. Later affected runs passed. [receipt](QT-F09_EXECUTION_2026-10-14.md) | Aggregate passing evidence exists;zero unresolved observed failures. One-run current full-suite evidence absent;do not portray legal evidence reuse as unfinished bug repair |
| V2 |7support | Latest accumulated local changes have no new publication/remote CI receipt | Local checks completed;old successful CI is historical. No commit/push authorized by this audit;publication is a separate action,not silently pending test failure |
| V3 |7support | Later memory/tools self-reviewed;external patch rereviews not received | Required CP01–05 feedback/repairs are closed. No newly invented mandatory checkpoint;independent rereview is an evidence limit,not five reopened CP failures |
| V4 |7;5/6 | Other named computer readiness/native qualification unknown. [setup](../WORKSTATION_SETUP.md) | Current host evidence cannot qualify another machine;verification needs that machine |
| V5 |4support | Actual Gemini project billing tier/remaining provider quotas not verified. [real request](QT-F07_LIVE_GEMINI_2026-10-14.md),[later request](QT-F13_EXECUTION_2026-10-14.md) | Real calls succeeded. No need to burn quota or change account settings to claim failure tests/free-only intent;no new live failure/quota administration requested |

## D — Planned/deferred groups:7

| ID | Structure | Scope | Existing reason/status |
|---|---|---|---|
| D1 |1/5 | Images/models/assets/camera/final visual production | Explicit director deferral. Essential UI/integration may proceed;not counted as executor omission |
| D2 |2/3/4/6 | Broad world/NPC cognition/personality/relations/5-level memory/anchors/forgetting/vector retrieval/AI quest packages | Future MASTER capabilities;QTF09 implements only2quest conversation memories and preparation. Not claimed complete |
| D3 |3;1/7 | Broad narrative adaptation/import | QT-F06 imported6descriptions;319queued+1rewrite-required records remain.320records are one bulk-work group,not320unclosed recent coding tasks;artifact-specific qualification/contracts still needed |
| D4 |7support | GOV-03 and remaining governance automation | Explicit DEFERRED/engine-method replay body coverage not active;GOV-01/02 completed |
| D5 |7;5/6 | RS-STRUCT-001 conditional reconciliation/extension risks | CP01-F4 projection after COMMIT/load-close after swap/codec assessment explicitly nonblocking,deferred with rationale. No demonstrated normal-input defect left unfixed by this audit |
| D6 |7support | ARCH-002/B09 final roadmap/readiness closure | Parent IN_PROGRESS,B09 READY_FOR_REVIEW,checks6/34 later-order readiness PARTIAL. Document-design completion is not whole implementation |
| D7 |7;5/6 | Release qualification/standalone Windows launch/human UX/full crash and MIN-SPEC evidence/CP06 | Release deferred,standalone launch previously blocked by application control;no policy bypass. Current editor/build success does not close release or human acceptance |

Sources for D groups/current checkpoint states:[BACKLOG](../../BACKLOG.md),
[CP01 residual disposition](RS-REVIEW-CP01_DISPOSITIONS.md),[B09](../../architecture/BLOCK_09.md).

## Actual candidate inventory:4bundles/16lines,0director approvals established

| Origin | Format/status | Raw output SHA256 | Local artifact |
|---|---|---|---|
| QT-F07 actual service qualification | Candidate +metadata NEEDS_REVIEW;452tokens |10e418e5039271dede2a29b1e205b026252ab89d73c2e44aa1b34a65741caf35 |[candidate](../../tmp/qt-f07-live/run-41752f8e83db4a6daa29420d01f6cd25/candidate.json) |
| Daily-cap removal/context retest | Preparation/v1 NEEDS_REVIEW;561tokens |fff005fcefd972c6ad360adc05c9013351f105b47ad33db39d02ea463637ec18 |[preparation](../../tmp/gemini-retest/live-c75882ce0e6049b798fdad84c0353b54/npc-preparation.json) |
| QT-F09 persisted memory | Memory preparation/v1 NEEDS_REVIEW;939tokens |b8642fdbd8f49f0167d84ed34a5dcbc2e7b70effd00e19882ba81b9d4070fb88 |[preparation](../../tmp/qt-f09/live-11d4b31e305a4cffac5ee87bed74c2e0/npc-memory-preparation.json) |
| QT-F13 preview-bound memory | Memory preparation/v2 NEEDS_REVIEW;865tokens |bd944eda92c53604e2fed3f593db5daa102ca6b1f2a761273d11b467577f4657 |[preparation](../../tmp/qt-f13/live-e8599c2107104ccda0e6ae2301b5d2ba/candidate-preparation.json) |

These are alternatives/evolutionary diagnostic outputs,not four mandatory production approvals.
Latest QTF13 is the candidate bound to the current preview/review/compile path. The failed original
QTF08 request created no candidate;later successful retest supersedes that live qualification gap.
The original20000uncertain token reservation remains historical accounting,not an unfinished game job.

## Audit checks and limits

Observed actual sources/callers and retained local output hashes/statuses;no code/provider/approval
mutation. Preserved entry source/test hashes and frozen archives;UTF8/local links/diff checks.
Audit witness:tmp/open-work-audit/checks.json. Runtime tests NOT_RUN for document-only audit.
No scheduling/execution of A/V/D actions,policy edits,new holds or reopening accepted checkpoints.
Recommended sequencing:A1concrete editorial proposal→actual decision→A2delivery;A3essential memory
client wiring also needed. This recommendation does not itself authorize additional implementation.
