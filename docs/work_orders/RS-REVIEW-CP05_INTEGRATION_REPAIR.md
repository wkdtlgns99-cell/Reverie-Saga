# CP05 Integration — Verified Scoped Repair

Date:2026-10-14 | State:DONE;Sol execution/self-review,not independent patch review.
[Actual feedback](../reviews/RS-REVIEW-CP05_INTEGRATION_FEEDBACK.txt)/
[existing contracts](QT-F07_QUEST_DIALOGUE_CONTRACTS.md)/[order](QT-F07_QUEST_DIALOGUE.md).
Director supplied the requested actual review;existing repair authorization covers verified findings.

| Field | Concrete scope/contract |
|---|---|
| task_id/title | RS-REVIEW-CP05-INTEGRATION-REPAIR;fail-closed quest detection and crash-recoverable local budget publication |
| goal/non_goals | Reproduce/fix P2-1/P2-2,disposition P3/coverage comments;no new quest/provider call/content approval/remote work |
| baseline | HEAD1ad22446d48c50b8b72a6d3af8de3c9d775134ea;334-file snapshot tmp/cp05-integration-repair/entry.json after feedback copy;retain preexisting dirty work;original CP03/CP05 manifests/ZIPs frozen |
| prerequisites | Actual PASS_WITH_CORRECTIONS received;prior1437full/61native/build accepted;current Windows CPython3.13.12/Unity6000.3.25f1 reused per WORKSTATION_SETUP |
| read_files | Rulebook/handoff/backlog/Korean companion/template/canonical CP05 procedure;QT-F07 order/contracts;actual serialization,quest,turn,budget,dialogue/provider and callers/tests;README/Unity README/workstation setup |
| allowed_edit_paths | MODIFY C:/ReverieSaga/src/orchestration/serialization.py,src/adapters/generation_budget.py,src/orchestration/quest.py;tests/unit/test_quest.py,test_dialogue.py,tests/adapters/test_generation_budget.py,test_gemini_dialogue.py;BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md;QT-F07 order/contracts;NEW this order and docs/reviews/RS-REVIEW-CP05_INTEGRATION_FEEDBACK.txt,RS-REVIEW-CP05_INTEGRATION_DISPOSITIONS_2026-10-14.md,RS-REVIEW-CP05_INTEGRATION_REPAIR_INPUTS.json;owned tmp/cp05-integration-repair and new repaired ZIP |
| forbidden_paths | CORE driver/store/save/slots,watch/encounter behavior,existing goldens,policy/CI/dependencies,Unity source/generated DTOs,approved content,credentials,reference repo and original review witnesses/archives |
| public_contract | Existing signatures/pins/DTOs unchanged;missing rules.quest with registered quest presence raises BootstrapError INVALID_QUEST_BINDING before scenario access;rules.quest without quest registrations rejects likewise |
| behavior | Gather registered quest roles before optional-key early return;require declaration/presence agreement;retain exact role/content checks. Under exclusive OS budget lock,remove only owned budget.pending before writing/fsync/atomic replacement;budget.json remains authoritative |
| edge_policy | Normal nonquest bundles unchanged;missing declaration with honest/wrong-content/skipped-constructor consumers all reject typed;ghost declaration rejects. Pending file can be empty/partial/stale and never replaces committed counters;bad ledger remains unavailable;unlink/open/replace failure fails closed with zero new HTTP call |
| examples | Honest quest minus declaration→INVALID_QUEST_BINDING;existing1attempt/20000tokens+stale pending,second reservation at+60000ms→2attempts/40000tokens;third→BUDGET_EXHAUSTED;crashed process before publication cannot spend HTTP because reserve has not returned |
| algorithm_steps | Add independently expected tests;observe failures;repair guard/publication;remove redundant quest total-count literal and delegate base count to WatchCheckpointPolicy;retain strict raw response order/provenance contracts with explicit tests/docs;qualify current paths and freeze original input |
| wiring | RegisteredStateIO state_io/bootstrap/resume use guard;GeminiDialogue.generate reserve/reconcile use locked ledger;checkpoint delegates remaining records;provider-order/approval tests cover actual preparation boundaries |
| performance | Guard O(number of registrations),existing boot cost;budget one extra unlink per valid publication,no lock waiting/retries;native measurements reused only for unchanged C#/render inputs |
| baseline_commands | Git HEAD/status/exact SHA256 snapshot;prior native61/Python1437 evidence historical;new failing probes recorded separately |
| verification_commands | Focused actual unit/adapter/integration/replay/client tests;README shared/selective Ruff,affected formatter,strict mypy,both imports/full regression;fresh native quest uses changed Python guard/checkpoint. Reuse unchanged C# build/hook evidence;docs UTF8/links/anchors/scope/frozen hashes/new repaired packet |
| test_responsibilities | test_quest missing-key/mismatch/skipped-constructor and ghost declaration;test_generation_budget stale/crashed pending/committed cap/settlement/failure preservation;test_gemini_dialogue unordered output consumes exactly one attempt and actual usage;test_dialogue raw-byte anchor vs trusted catalog pin deliberate behavior |
| acceptance | P2 tests fail before/pass after;existing contracts/pins retained;full/static/current native quest pass;all actual findings dispositioned with limits;CP05 DONE only after actual feedback+verified repairs/retests,not claimed full independent review |
| claude_checkpoints | CP05-INTEGRATION actual feedback received;hold downstream expansion while required repairs/retests unfinished;patch external rereview NOT_RECEIVED;no automatic follow-on task |
| stop_conditions | Overlapping user changes,unresolved actual blocker/out-of-scope behavior;live key/project/model verification stays deferred by director and is not a repair prerequisite |
| delivery | Korean result plus repaired packet/dispositions;update all3progress files;no publication/agents/provider call/dependency change |

Acceptance2026-10-14:[dispositions/actual results](../reviews/RS-REVIEW-CP05_INTEGRATION_DISPOSITIONS_2026-10-14.md).
Before8FAIL/1PASS;focused88PASS;full1451PASS341.35s;Ruff/format/mypy127/imports3+1 PASS;
fresh native quest14PASS. Original C#/61native/build/hook evidence unchanged;no live API/remote CI.
CP05 integrated checkpoint DONE for bounded first quest;patch external rereview NOT_RECEIVED.

P3 interpretation:strict intent ordering and raw candidate output hashes are retained rather than
normalizing unapproved model bytes. Approval is a local authorization/provenance record plus an
externally chosen trusted full catalog pin,not authenticated approval at load. The brief anchor
cannot be recomputed by the loader without the originating brief. Nonblocking lock failure and
coarse sanitized HTTP mapping remain deliberate documented contracts;real API behavior deferred.
Unity environment selectors remain part of the documented local development harness. Remove
the redundant11-record check;the base watch policy already owns its exact record count.
