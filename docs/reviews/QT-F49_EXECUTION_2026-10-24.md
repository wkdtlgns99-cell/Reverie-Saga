# QT-F49 — Execution receipt

Order:[cycle call recollection](../work_orders/QT-F49_CYCLE_CALL_RECALL.md).
Baseline72c2d58,branch codex/cycle-call-recall-20261024. Self-review,not independent.
Status:LOCAL_ACCEPTED;bounded implementation acceptance complete. No publication or release performed.

Director requested next implementation and automatic execution on2026-10-24. Supported
same-chat goal created and confirmed ACTIVE;no timed automation or agent created. Earlier
paused state is historical. Read current source/Git/goal before automatic continuation.

## Implemented and verified

Cycle committed talk reuses the causal call collector/conversation boundary/renderer in
one isolated verified cycle replay. Existing persistent player statement and supply memory
projections remain separate. Retry/rejected/non-talk output adds no recollection. No CORE,
save/pins/wire/content/dependency or production Unity behavior change.

- Baseline new real session regression failed:expected call3 at talk20,actual no call.
- Initial new regression plus F46tests:9PASS23.20s.
- Affected cycle/call/work/player-memory/client/bridge selection:164PASS163.72s;includes
  the initial8new F49cases covering caps,conversation scope,compaction,rewind/restart,
  causal failure/process control,one replay/retry,real binary pipe and actual Tk.
- Added source guards:5PASS3.68s(final):wrong NPC/current talk/core/protocol and retained
  IO failure. Failure assertions preserve committed/live/source state and recovery.
- Exact CI boundary selection from checks.yml:31PASS11.99s.
- Both Ruff configurations PASS;15CI+changed formatting inputs PASS before final source
  additions;final new test formatted. Strict mypy207files PASS via existing pinned source
  fallback tmp/qtf02/typecheck;import contracts3+1PASS,pip check PASS.
- Initial supplemental tests had2type errors;WorldRevision and SaveSegment annotations
  corrected,final mypy and both Ruff runs PASS. No checks suppressed or weakened.
- New cycle talk representative19second trace sample355.799ms including durable talk;
  see f49-affected/test_cycle_talk_one_replay*/latency.txt. Other five samples belong to
  existing work-call tests and are not additional cycle measurements.

F46checkpoint test's former total no-replay assertion intentionally changed for F49's
new call retrieval. It now requires exactly one canonical restore while preserving original
persistent promise/report time,quest reward and supply checks. Player selector itself
remains a pure projection. Existing work-mode logic unchanged.

## Native attempt and next action

Elevated discovery found no Unity editor. Launched installed
C:/Program Files/Unity/Hub/Editor/6000.3.25f1/Editor/Unity.exe once,pid31168,
revisione1dba0a9aba4,file6000.3.25.14801824. Retained-editor mode0,working path
tmp/qtf49/native/game.sqlite,log tmp/qtf49/unity.log. Harness adds explicit talk37
count5/latest34,35,36since talk31 and cycle-talk-calls capture.

First run failed before gameplay with NPC_MEMORY_CONTENT and RESULT/RETAINED/IDLE code1.
Cause:launcher supplied NPC_MEMORY=1 with empty scenario/catalog/hash,which disables the
approved-preset branch in PlayRoom.Start and falls to legacy with no memory content.
This is verification configuration failure;do not alter production validation. Preserve
log and editor. Next:reuse same editor with correct explicit harbor/catalog/hash or unset
memory selector and use approved preset;use registered VerifyInteractive menu. If a
temporary editor-only harness is needed,record exact allowed paths in the order first,
remove it afterward,and preserve the editor. Computer Use skill has been read;guidance,
confirmations and API docs still required before controlling the UI.

Original scene restored byte-exact after failed/idle run;all156input manifest files matched
entry hashes(interim.json). The following corrected run supersedes the native failure for
acceptance while retaining the original configuration error and log.

Existing CP06 release hold and deferred independent review unchanged;D2 remains OPEN.


## Corrected native run and self-review

Reused the same editor31168 with zero restarts. Computer Use selected its returned Unity
window3539826,refreshed Assets,and reloaded the restored scene. Owned temporary
F49VerificationTrigger used public Environment/EditorApplication APIs to set explicit
harbor/approved catalog+hash,memory1/work0/cycle1,retained0 and fresh native-corrected path,
then invoked existing PlaytestBuild.Verify. No production selection/security change.
The earlier failure remains before F49_CORRECTED_SELECTION_START in unity.log.

Corrected run:130VERIFY_PASS,0VERIFY_FAIL,ENGINE_VERIFY_PASSED and RESULT/RETAINED/IDLE
all code0. Existing cycle/current+previous slot recovery/reconnect/quest/player-statement
checks preserved. New talk37requires exact previous31,count5,latest34/35/36. Actual
642x500cycle-talk-calls.png inspected:heading,count and complete three reply rows readable
through ordinary dialogue focus. Matching response/history files preserve exact messages.

readback.py/readback.json:all9exact owned managed saves validated and replayed to their
saved state;activity causal rows match the independently known calls34/35/36after37or
empty before calls. Current-talk saves additionally project the original talk directly.
Every source was then copied to a fresh owned working path,continued through a new talk,
and required explicit empty new-call output with retry/source-byte preservation;no calls
have occurred since the last saved conversation. Source hashes unchanged throughout.
Nine continued-talk samples mean807.764ms,max1096.317ms(<2s target)on this host only.

After corrected idle,removed owned trigger and generated .meta,copied its source to ignored
native evidence,and restored original scene bytes. All156native input hashes unchanged.
Refreshed/reloaded scene through observed UI;existing editor remains open. No source test,
golden,assertion or check suppressed. Product behavior follows retained facts and current
conversation identity;shared helper defaults preserve old work/memory paths. No additional
CORE or release-build qualification is claimed. Supplemental affected checks:63PASS/2environment failures48.35s;both failures are
pre-existing Windows sandbox hardlink permission denial in previous-slot recovery,then
the same2PASS1.36s on permitted execution(hardlink.log). Combined234distinct affected
cases qualified(164+5+65);not a single all-green combined run. Final15format inputs PASS.
Final document guards10PASS1.50s;delivery.py PASS:11exact scoped paths,269local links,
UTF-8/whitespace,156input hashes,scene and temporary harness cleanup. Evidence manifest
under tmp/qtf49/delivery.json;final progress/status edits rechecked successfully.


Acceptance:PASS for settled vectors,real callers,read-only source/replay,postcommit recovery,
old work behavior,static/affected/boundary/native/save evidence and synchronized progress.
No fresh complete regression or release build;unchanged CORE/build inputs retain historical
revision-scoped evidence only. Current goal remains ACTIVE for subsequent authorized bounded
work;this task is locally accepted and not independently reviewed or newly published.
