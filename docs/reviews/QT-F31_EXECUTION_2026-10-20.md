# QT-F31 — Persistent player statements in return dialogue

Date:2026-10-20 | LOCAL_ACCEPTED,self-review/current Windows host only.
Primary4retrieval/context;related2/3/5/6/7. [Contract](../work_orders/QT-F31_NPC_PLAYER_MEMORY.md).
D2 remains OPEN. This uses the existing two quest-statement anchors;it adds no new
authoritative memory,relationship/personality/reward rule,LLM,save format,pin or wire change.

## Result and evidence boundary

Work-mode return context selects the latest existing persistent player statement and shows
its original time. A directly heard acceptance remains a promise until the player reports
completion. Enemy defeat alone never becomes received-report or eyewitness knowledge.
The completion conversation commits its report memory before presentation;later talks reuse
that report's original time. Load/reconnect follows the selected branch's older/newer report.

The existing recent_evidence selector supplies latest1of MEMORY_CAPACITY2. Source records
come from the same verified isolated replay as work/call recollection;exact current core,
protocol and actual talk identity must agree. The memory checkpoint policy already validates
owner/count/stage/tick and source_identity. Old trace truncation cannot erase those existing
CORE anchors;work/call facts keep their retained-trace limitation. No extra replay,IO or turn.
Empty/invalid sources are explicit;postcommit projection failure logs NPC_RECOLLECTION_SOURCE,
reconciles actual committed state and retains retry/save/next talk/close. No false rollback.

## Verification

- Reused Python3.13.12/Tk8.6/editor6000.3.25f1;pip check PASS,no install/settings change.
- All16new cases PASS18.58s on first run. Cases cover0/1/2anchors,invalid input,unreported
  actual defeat,same-commit report,stable original time,retry/branch rewind/restart,valid
  truncated checkpoints,4malformed anchors,read-only latency,postcommit failure,real pipe/Tk.
- Final affected client/worker/real Tk/binary pipe/memory/query/work/call/activity/reconciliation/
  text/document regression:206PASS133.77s,exit0;tmp/qt-f31/affected.log.
- Both Ruff configs,format3changed Python files,strict mypy189files,imports3+1,pip/diff and
  final10document checks PASS. No runtime/test-expectation repair was needed.
- Authoritative sources/pins/schema/registry/governance inputs and F29/F30tests remain
  hash-identical to entry. Reuse F28full2029-case evidence with its documented restricted
  failures/permitted reruns. New full-suite/remote CI/release build NOT_RUN.

## Native screen and durable evidence

Computer Use reused the returned editor8336window and ordinary Reverie verification menu;
zero launches/restarts. An existing external-scene notification was dismissed with Ignore.
Initial native98PASS/0FAIL,result/retained/idle0. Actual547x376captures exposed a partly
clipped first line at the bottom scroll position. This is not small-viewport UX acceptance.

To resolve visual verification only,the Game pane was expanded through its UI and the same
unchanged native sequence rerun:98PASS/0FAIL,result/retained/idle0. These are98cases repeated,
not196distinct checks. Actual955x672player-reported/player-restored captures were inspected:
full37-second versus38-second report lines and explicit non-eyewitness wording are readable.
The original editor layout was restored afterward;Unity stays open in Edit mode. No terminal
UI,security/authentication action or product-layout change.

Final source root:tmp/unity-verification/2dea8073a83b4f92b145409914dab341.
Five exact owned saves independently validate/replay with identical before/after bytes:

| Save | Tick / quest stage | Latest NPC statement |
|---|---|---|
| Original |16/1|accepted2|
| First loaded branch |35/1|accepted2|
| Second loaded branch |38/3|reported37|
| Third loaded branch |38/3|reported38|
| slot01 |35/2,enemy defeated/unreported|accepted2|

All stock3;reported branches grant the existing favor once. Combined context210–598ms,
target<2s on this host. Initial5save readbacks also passed;final5are the delivery witnesses.
Logs/readbacks:tmp/qt-f31/native-small.log,native-wide.log,readback.json,readback-wide.json.
Scene content-normalized equality proved and exact entry bytes restored after each run.

## Preservation and limits

All31entry dirty/untracked files copied/hashed under tmp/qt-f31/baseline. Earlier work,stash
and witnesses preserved. Production edits are only npc_activity/npc_memory_query;other edits
are native verification,one new test file and linked docs. No commit/push/PR/merge/agents/
provider call. CP06held,V3stoppedPARTIAL. Other-device,MIN-SPEC,long-save,standalone,human UX,
independent review and whole-D2 acceptance remain unqualified.
