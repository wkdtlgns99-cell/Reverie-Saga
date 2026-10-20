# QT-F30 — Remember answered player calls on return

Date:2026-10-20 | LOCAL_ACCEPTED,self-review/current Windows host only.
Primary4retrieval/context;related2/3/5/6/7. [Contract](../work_orders/QT-F30_NPC_CALL_RECOLLECTION.md).
D2 remains OPEN. This derives existing response facts;it adds no authoritative NPC action,
personality/relationship rule,LLM,save format,pin or wire change.

## Result and truth boundary

Work-mode return dialogue now recalls actual responses to this player's calls after the
previous retained conversation. Each reply follows its caused_by chain through own echoes
to the selected player's own request,using event identities rather than matching clocks.
Canonical isolated replay verifies retained outcomes/hashes and exact current core/protocol
and talk identity. Missing/ambiguous/wrong-caller/other-NPC/wrong-time/cyclic chains reject
NPC_RECOLLECTION_SOURCE. Current watch rules answer within the same command;no deferred
reply is inferred. No direct enemy observation or quest reward is created.

Latest3calls are retained separately from the mixed8activity list;conversation counters
retain the exact range total even when more than3calls occurred. Both work and call context
use one replay. F29work_recollection API/output remains unchanged;ClientSession uses the
combined return_recollection API. Stock remains the final message. First/truncated history
uses the current-segment label;old cumulative reply counters never reconstruct lost calls.
Retry/non-talk/rejected talk emits no recollection. Load/reconnect uses the selected branch.
Projection failure after commit is logged with truthful committed-state wording;worker
reconciliation,retry,save,next conversation and close remain usable.

## Verification

- Existing Python3.13.12/Tk8.6/editor6000.3.25f1 reused;pip check PASS,no install/settings change.
- Initial13new and14existing F29cases PASS15.56s/14.91s. Added6actual-source causal mutation
  cases and1postcommit projection-failure recovery case:20new cases total.
- Final affected client/worker/real Tk/binary pipe/memory/activity/work/reconciliation/text/
  document regression:168PASS103.46s,exit0;tmp/qt-f30/affected.log. Includes all20new cases.
- Both Ruff configs,format3changed Python files,strict mypy188files,imports3+1,pip/diff and
  final10document checks PASS. Initial mypy found2test NewType assignments;changed their
  explicit EventId/Tick constructors without changing test expectations;final strict PASS.
- Shared authoritative inputs are unchanged from F28/F29. Reuse F28full2029-case evidence
  with its documented restricted-environment failures/permitted reruns;no fresh full/CI claim.

## Native and durable evidence

Computer Use reused returned Unity window/editor8336,zero launches/restarts,and invoked
Reverie/Verify Current Selection (Keep Editor Open). Existing external-scene notification
was dismissed with Ignore before the menu run. No terminal UI/security/authentication action.
Native scripts compiled;66PASS/0FAIL,result/retained/idle0. Editor remains open in Edit mode.

Actual547x376call-capped/call-restored captures inspected:latest33-second call and restored
11-second call readable with Korean wrapping;earlier lines/summary are above the small
viewport's scroll position,not claimed simultaneously visible. Full chronological message
arrays and exact5-total/latest3 assertions pass. No new human UX/MIN-SPEC/layout acceptance.
Source root:tmp/unity-verification/adb3676c6250446c916de57e9413f786.

Four exact owned saves independently validate/replay with byte-identical before/after:
original16/stock3/replies0;first loaded35/stock3/replies6,latest-talk range empty;
second loaded28/stock3/replies1,recalls11only;slot01at27/stock3/replies1.
Combined context measured224–571ms,target<2s on this host;long-save/other-device unqualified.
Logs/readbacks:tmp/qt-f30/native.log,readback.json. Scene normalized equality proved before
restoring entry bytes;no retained scene change.

## Preservation and delivery

All28entry dirty/untracked files copied/hashed under tmp/qt-f30/baseline. Previous work,
stash and evidence preserved. This increment changes app projection,native verification,
one test file and linked docs only. No commit/push/PR/merge/provider/agent action.
CP06release held,V3independent review stoppedPARTIAL;no whole-D2 or release claim.
