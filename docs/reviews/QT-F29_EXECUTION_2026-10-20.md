# QT-F29 — NPC work recollection acceptance

Date:2026-10-20 | LOCAL_ACCEPTED,self-review/current Windows host only.
Primary4retrieval/context;related2/3/5/6/7. [Contract](../work_orders/QT-F29_NPC_WORK_RECOLLECTION.md).
D2remains OPEN. No model inference,new cognition,production rule,save schema or wire change.

## Result and source truth

Work-mode conversations now recall only the NPC's actual ProvisionPrepared facts after
the previous retained QuestSpoken. Existing canonical isolated replay verifies all retained
outcomes/hashes plus exact current core/protocol and current conversation event identity.
The collector retains3production records separately from mixed recent8activity and last2
conversation identities. Frequent bells cannot hide work. Same-turn production belongs to
that committed talk;the next talk excludes it. No lost history is inferred from stock/time.

No prior conversation in retained history is labeled as the current saved segment. Empty
intervals are explicit. Load/reconnect use their current branch. Exact retry adds no recall.
An ordinary source-read failure after commit is logged and reports NPC_RECOLLECTION_SOURCE
with truthful committed-state wording;the worker reconciles actual state and still accepts
retry/save/next talk/close. Fatal exceptions are not swallowed. No authoritative mutation
is performed by recollection.

## Verification

- Reused Python3.13.12/Tk8.6,pip check PASS;no dependency/login/security changes.
- Initial14new tests:13PASS/1test assertion failure14.77s. Substring `4초:` also matched14초;
  corrected the assertion to the exact existing activity-line prefix,no production change.
- New+F28/activity tests34PASS39.22s. Final related client/worker/Tk/pipe/memory/activity/text/
  reconciliation/document regression148PASS84.52s,including all14new cases.
  Log:tmp/qt-f29/affected.log. Cases include replay mismatch/stale core/wrong NPC/wrong talk/
  invalid trace header,checkpoint without old events,source byte preservation and postcommit IO.
- Both Ruff configurations,format4changed Python files,strict mypy187files,import contracts3+1
  PASS. New static issues were one long narration line and an EntityId test assignment;fixed.
- Authoritative code/schema/engine/registry/pins remain byte-identical to F28accepted inputs.
  Reuse F28full2029-case evidence with its recorded restricted-environment failures/permitted
  reruns. A new complete full-suite run/remote CI was NOT_RUN;148affected tests are fresh.

## Native and durable evidence

Reused editor8336,zero new launches/restarts. Computer Use selected the returned Unity window
and invoked Reverie/Verify Current Selection (Keep Editor Open). Initial accessibility-index
inputs reported unavailable cached elements;fresh coordinate observations succeeded. No terminal
UI/security/authentication action. Native scripts compiled;40checks PASS/0FAIL,including
13new recollection assertions. Result/retained/idle0;the editor remains responsive in Edit mode.

Actual1101x506work-full and work-reconnected captures inspected:8/12-second recollections
and the explicit empty interval after the9-second conversation are readable. Source history,
response JSON and old stock checks also pass. Work-activity capture remains an unchanged
mixed recent8display;it is not used to claim full work-history visibility.

Exact3owned saves validated/replayed with identical before/after bytes:original tick16/stock3
recalls8/12 after talk7;loaded tick10/stock2 has no work after talk9;slot01tick6/stock1.
Independent recollection readback latency205–211ms,target<2s on this host. Long-save/MIN-SPEC
performance remains UNVERIFIED. Native working root:
tmp/unity-verification/0c9234fbbd394e7683815480864de3b3;local log/readbacks under tmp/qt-f29.
Scene normalized equality proved before restoring its exact entry bytes;no scene changes retained.

## Preservation and limits

All25prior dirty/untracked paths were copied/hashed at tmp/qt-f29/baseline before edits.
Previous stash and accepted evidence preserved. Current task modifies only app projection,
native verification,tests and linked documentation;no commit/push/PR/merge/provider/agent action.
No independent review,release build,other-device acceptance or D2whole-scope closure.
