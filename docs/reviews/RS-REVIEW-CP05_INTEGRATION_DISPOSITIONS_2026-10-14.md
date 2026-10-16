# CP05 Integration — Actual Feedback / Verified Dispositions

Date:2026-10-14 | Actual review:PASS_WITH_CORRECTIONS;required repairs/retests accepted;CP05-INTEGRATION DONE for the first quest scope.
Sol verification of findings/patches;not independent patch rereview.
[Original reply](RS-REVIEW-CP05_INTEGRATION_FEEDBACK.txt)/
[bounded repair order](../work_orders/RS-REVIEW-CP05_INTEGRATION_REPAIR.md)/
[contracts](../work_orders/QT-F07_QUEST_DIALOGUE_CONTRACTS.md).
Reply SHA256:21604e89fed53077e7fc382549dee7774a4b8e9ca6586c0835f8f11ba956c569.

## Actual Review Scope

Reviewer inspected quest domain/contracts/engine/orchestration/registry,boot validation,
dialogue/provider/transport/budget/preparation and session/worker/text plus selected Unity gating.
Reviewer reports Linux Python3.12.3:89focused PASS;first broad run85governance/rule failures due
to missing importlinter,then pinned tools installed and91governance/rule+13client-text PASS.
About1400total is the reviewer's reconstruction,not a new independently witnessed exact full-run
receipt. Shared Ruff/3import contracts PASS reported;no mypy/live API/Tk/Windows/native run.
Reviewer did not inspect durable/store/slots/driver/scheduler,bridge/Tk,most C#/scene/diff or
screenshots/build;37Tk cases were inferred rather than executed. These omissions remain explicit;
the actual review closes only the bounded first quest integration checkpoint after verified repair.

## Required Corrections

| ID | Evidence / classification | Disposition |
|---|---|---|
| P2-1 | Confirmed fail-open:rules.quest deletion accepts honest or mismatched quest consumers;skipped constructor leaks AttributeError. Ghost declaration also lacked typed rejection | Gather registered quest roles before early return;require declaration/presence agreement,then retain exact role/content validation. Four real state_io tests fail before/pass after |
| P2-2 | Confirmed availability bug:stale budget.pending makes exclusive open fail forever | Under the existing exclusive OS profile lock,remove only reserved pending sibling;preserve budget.json truth. Three pending-byte variants,real abruptly exited child writer/reconcile idempotence,and cleanup/corrupt-ledger preservation tests |

Before repair:new failing selection8FAILED/1PASS/17deselected in1.47s;captured under owned
tmp/cp05-integration-repair/before.log. Initial probes assert specific typed errors/counters rather
than ordinary successful imports. After repair:88focused PASS12.15s,including14new cases across
boot/budget/provider-order/provenance tests. Full/static/native completion is recorded below.

## Lower-Priority Findings

| Review item | Classification / evidence / disposition |
|---|---|
| P3 intent order/schema | Intentional strict local contract:generic schema cannot enforce the lexical tuple;local decoder does. Do not reorder model bytes before approval/hashing. New reversed/duplicate response tests assert GENERATION_OUTPUT,one send/attempt and returned260tokens settled once;no retry. Contract now states this explicitly |
| P3 approval anchors | Trust-boundary clarification accepted. Compilation binds output hash to exact raw bytes;brief anchor is external provenance. Load validates a caller-chosen trusted full catalog pin and schema,not authenticated reviewer/brief identity. New whitespace raw-byte test and two well-formed changed-anchor tests assert old pin rejection/new deliberately trusted pin acceptance. No signatures/authority invented |
| P3 lock contention | Intentional nonblocking contract retained:failure before reserve publication yields BUDGET_UNAVAILABLE/zero HTTP/no counter change. Existing real-process lock contention test remains. Automatic bounded waiting/retry is a product policy change,unnecessary for this low-volume explicit preparation job |
| P3 coarse HTTP codes | Intentional sanitized mapping retained:401/403 AUTH;other4xx REJECTED;URLError/TLS/DNS TIMEOUT. REJECTED never retries;network failure retries at most once with reservation. Do not infer invalid-key origin from400 or expose raw provider error bodies. Actual service diagnostics remain deferred in linked qualification item |
| P3 component count | Maintainability issue repaired:remove redundant quest total11literal. Exactly one quest record remains required;delegate remaining record count/schema/identity invariants to existing WatchCheckpointPolicy (which owns10),without changing that policy |
| P3 Unity environment selectors | Intentional documented local development harness retained. Selectors already configure both catalog and expected hash,with equal caller authority;not production hostile-input authentication. Verification hooks remain stripped in accepted release build evidence;portable release configuration is separately unqualified |
| API casing/schema uncertainty | Not a reason to silently change a reviewed request. Existing MINIMAL thinking request/schema retained;no current live result claimed. Director deferred free-project/quota/model/endpoint/schema/actual error qualification;[backlog routing](../../BACKLOG.md#qt-f07-deferred-qualification) records limits |
| Stale artifact pending sibling | Separate from budget lock:publish_fresh has no cross-job profile lock,so blindly deleting an existing pending artifact could destroy an active producer's work. Keep exclusive fail-closed publication and owned cleanup;use a fresh output path after interrupted prep. Never overwrite approved artifact. No automatic deletion added |

## Composition and Coverage Verification

Reviewer did not trace turn.py. Sol checked actual path:TurnDriver._phase calls _stage for each
emitted delta against pre-barrier root before appending candidate.changes and publishing the
barrier;_stage invokes registered QuestReducer.stage,which requires single-step and matching
before.stage. _compose later validates contiguous changes/allowed net. Real pre-defeat0→2,
forged0→3/1→3,precommit preservation,durable retry/recovery and offline replay tests retain coverage.
No driver/store/slots changes,save-format changes or golden replacements are part of this repair.
Existing stage/pins/vector/texts remain unchanged;the missing-declaration guard tightens boot only.

## Qualification and Remaining Limits

Final full1451PASS341.35s (JUnit341.191s),zero failures/errors/skips;14new cases beyond1437.
Actual command:`.venv/Scripts/python.exe -m pytest -q --basetemp .pytest_cache/cp05-repair-full --junitxml tmp/cp05-integration-repair/full.xml`.
Focused88PASS12.15s;shared/selective Ruff PASS;strict mypy127files PASS;shared3/runtime1import
contracts kept with --no-cache;README12-file and affected5-file formatter checks PASS.
Initial import checks omitted PYTHONPATH and could not find app;rerun with PYTHONPATH=src passed
both configs. This was command environment setup,not a dependency/layering failure or policy change.

Fresh current-account graphical Unity quest14checks PASS,exit0 on repaired Python source:
tmp/qt-f07/native/quest-b08628b4a9ad44789fa694616098f464;Verify method,offline test-only catalog,
fresh owned save. Final screenshot visually inspected:tick11/quest complete/favor1 and completion
NPC line visible.120frames median1.782001ms/p952.335899ms,current placeholder host only.
Generated scene restored to exact entry bytes. No C#/build/render input changed;prior61native/
Windows build/release-hook absence evidence retained rather than relabeled as new execution.
CP05-INTEGRATION DONE per actual feedback+verified dispositions+required repairs/retests for this
bounded first quest. No independent patch rereview/full omitted-source audit is claimed.
[Separate repaired inputs](RS-REVIEW-CP05_INTEGRATION_REPAIR_INPUTS.json) anchor this delivery.
The original integrated request/input manifest/ZIP remain historical frozen reviewed bytes;
new repaired manifest/ZIP separately anchor current files/task delta and summarized evidence.
No live API,key read,dependency install,publication,external upload,agent launch or new feature.
Prior C# build/render/61native acceptance remains unchanged-source evidence;new Python runtime
quest14checks on repaired Python observed above. Other-device/standalone/production content/
final HD-2D/human UX remain UNVERIFIED,as in the original execution receipt.
