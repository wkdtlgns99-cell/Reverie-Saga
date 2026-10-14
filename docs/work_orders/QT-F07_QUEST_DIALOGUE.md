# QT-F07 — Execute One Quest with Prepared Gemini Dialogue

Date:2026-10-13 | Executor/reviewer:Sol;self-review,not independent.
State:LOCAL_IMPLEMENTATION_ACCEPTED / CP05-CONTRACT DONE;CP05-INTEGRATION DONE;verified scoped repair/retests accepted2026-10-14.
[Final execution evidence](../reviews/QT-F07_EXECUTION_2026-10-13.md);actual PASS_WITH_CORRECTIONS received2026-10-14;[repair](RS-REVIEW-CP05_INTEGRATION_REPAIR.md).
Director steering:finish local/Unity verification;live Gemini qualification deferred by request.
Prepare only an empty ignored key file and setup memo;do not make a live API call this turn.
Director requests execution after confirming Brain judges success and AI provides presentation;
director selects Gemini free API. [Exact contracts](QT-F07_QUEST_DIALOGUE_CONTRACTS.md).

| WORK_ORDER field | Concrete value |
|---|---|
| task_id/title | QT-F07;one opt-in harbor quest and four-state Gemini-prepared dialogue |
| goal/non_goals | Brain acceptance/goal/report/one-time favor and approved local dialogue;contract §§1–4 delimit external calls and future capabilities |
| baseline | HEAD1ad22446d48c50b8b72a6d3af8de3c9d775134ea;entry301files/38dirty paths from QT-F02/CP03;retain all existing work and frozen witnesses/ZIPs;packet manifest records exact input hashes/current diff |
| implementation resume baseline |307files at feedback entry;tmp/qt-f07/entry.json anchors bytes before repairs;original CP05 witness/ZIP frozen |
| prerequisites | QT-F02/CP03 first embedded scope DONE;CP05-CONTRACT feedback received,verified corrections accepted;content approval/free-project/key/live qualification separate |
| read_files | ENGINEERING_RULES,SESSION_HANDOFF,BACKLOG,GAME_SYSTEM_SUMMARY_KO,MASTER §§2–3/7–9,prompt A3/A5/A14/C-02/checkpoints,README,WORKSTATION_SETUP,QT-F02 contracts;actual source/caller/test index in review request |
| public_contract | Contracts §§2–5 specify records,commands,stages,fields,errors,generator/CLI/catalog/session/DTO signatures and registered consumers |
| behavior/algorithm_steps | Validate/pin accepted dialogue;bootstrap11records;admit talk;RESOLVE acceptance/report;POST_TICK observe HP;COMMIT once;present selected prose;no per-turn network |
| edge_policy/examples | Exact types/IDs/fields/text/order/caps,pre-defeat,duplicates,zero/negative/oversize,overflow/failure/compatibility in contracts §§2–6;numeric vector derived from existing combat/time constants |
| wiring | quest_bundle/QuestRules/admission/reducer/checkpoint/client session→worker→bridge/Tk/Unity;preparation CLI→Gemini adapter→validated candidate→director receipt→compiled catalog;no runtime stub |
| performance | Core observation O(1),one record/four lines;candidate16KiB/network256KiB;generation latency TARGET180s,turn/render budgets inherited;quest120frames median1.870699ms/p952.767404ms on current host;generation latency UNVERIFIED |
| baseline_commands | git HEAD/status/input hashes;existing CP031360full/47native/build/static PASS are unchanged-source historical evidence,not new QT-F07 tests |
| verification_commands | Document UTF8/local links/exact scope/frozen inputs/packet hashes now;after gate:README shared/selective Ruff/affected format/strict mypy/both Import Linter configs/full pytest;fresh native quest and retained scenarios/build per Unity README |
| test_responsibilities | NEW unit/test_quest.py,unit/test_dialogue.py,adapters/test_gemini_dialogue.py,integration/test_quest.py,replay/test_quest.py;extend actual client/bridge/native tests for contract §6;implemented;final1437full/61native/static/build PASS |
| acceptance | Gate A:complete reviewable contracts/actual input packet/document checks;Gate B:actual feedback/verified dispositions/no blocking semantics;Gate C:real quest/generator/catalog/client wiring and tests;Gate D:separate CP05 integrated review/fixes/retests |
| claude_checkpoints | CP05-CONTRACT actual feedback/verified repairs accepted;CP05-INTEGRATION later blocks larger expansion;never count self-review as independent review |
| stop_conditions | CP05 contract blocker unresolved;integrated feedback absent blocks larger expansion;missing/changed required content approval;missing key/free-project qualification for live only;overlapping user edits;failure outside authorized scope |
| delivery | Korean report/link ready packet;record current status in backlog/handoff/Korean companion together;no automatic upload/commit/push/agent/provider call |

## Exact Edit Scope

Current review preparation only,all under C:/ReverieSaga:
NEW docs/work_orders/QT-F07_QUEST_DIALOGUE.md,QT-F07_QUEST_DIALOGUE_CONTRACTS.md;
docs/reviews/RS-REVIEW-CP05_CONTRACT_REQUEST.md,RS-REVIEW-CP05_CONTRACT_INPUTS.json,
QT-F07_DIALOGUE_EXAMPLE.json,QT-F07_CONTRACT_PREPARATION_2026-10-13.md;
MODIFY BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md.
Ignored owned tmp/cp05-contracts and tmp/reviews packet artifacts permitted.

After actual contract pass,refresh baseline/order and only then execute bounded NEW
src/domain/quest.py,src/contracts/quest.py,src/contracts/dialogue.py,src/engines/quest.py,
src/orchestration/quest.py,src/app/quest.py,src/app/quest_definition.py,src/app/quest_registry.py,src/app/dialogue_prepare.py,
src/adapters/quest_dialogue.py,src/adapters/gemini_dialogue.py,gemini_transport.py,generation_budget.py
and planned tests above,plus tests/adapters/test_generation_budget.py for real process contention,
tests/unit/quest_fixtures.py and tests/replay/fixtures/quest_harbor_vector_v1.json independent oracle.
MODIFY tests/governance/test_dependency_contracts.py:task-scoped fixture must create the newly
registered quest engine;add forward/reverse engine independence probes. Existing probes and
expected guard behavior retained. This corrects the initial full-run missing-module failure,
not a skip/threshold/golden change.
MODIFY only existing app/client_session.py,client_worker.py,client_text.py,client.py,engine_bridge.py,
engine_project.py,watch.py,contracts/client.py,orchestration/serialization.py,
tests/integration/test_client.py,test_engine_bridge.py,
tests/unit/test_client_text.py;Unity Scripts BrainConnection/PlayRoom/LiveVerification/Wire.Generated.cs
and Editor/PlaytestBuild.cs;root README,three progress files,clients/unity/README,WORKSTATION_SETUP
and task order/contracts/execution/CP05 integrated packet. NEW approved content path
content/quest-dialogue/harbor-v1.json only after exact director approval;receipt/provenance adjacent.
Every path in this paragraph is rooted at C:/ReverieSaga. Generated wire only via existing exporter.
MODIFY pyproject.toml to add engines.quest to rs-engines-independent and exact three provider-
adapter TID251 exceptions for real IO deadlines/quota clocks. This preserves the domain/contracts/
engines time ban and existing dependency/CI gates;the exception is limited to external IO modules
as required by H1/M7. No blanket suppression or CORE clock exception. NEW feedback/dispositions/execution/CP05 integrated input
files under docs/reviews;owned tmp/qt-f07 test/native/review artifacts. This exact strengthening
exception addresses H1;the preceding older blanket policy-file exclusion does not forbid it.

Forbidden:reference repository,old candidate/provenance content,goldens,old review witnesses/ZIPs,
CORE driver/store/slots/save format,governance/CI/dependency files,existing watch/encounter rules,
provider/account/billing settings and unrelated user files. Registration uses current FeatureBundle
extension paths. If native interfaces need edits outside this list,revalidate the exact contract
and obtain appropriate scope before editing;do not silently patch CORE to make a test pass.

## Execution Progress

Actual CP05 contract feedback received and verified;[dispositions](../reviews/RS-REVIEW-CP05_CONTRACT_DISPOSITIONS.md).
Preimplementation contracts corrected;implementation/local qualification complete.
Final1437full/61native/build/static PASS;[execution](../reviews/QT-F07_EXECUTION_2026-10-13.md). The original packet is
historical frozen reviewed input. No content approval or Gemini result fabricated;live job needs
local key/free-tier/data-use confirmation. CP05 integrated reply received;required repair/retest acceptance DONE in the linked repair order.
Repair full1451/native quest14/static PASS;patch external rereview NOT_RECEIVED. No automatic next task.
See [preparation evidence](../reviews/QT-F07_CONTRACT_PREPARATION_2026-10-13.md).
