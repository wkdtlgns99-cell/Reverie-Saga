# QT-F50 — Execution receipt

Order:[cycle return change](../work_orders/QT-F50_CYCLE_RETURN_CHANGE.md).
Status:LOCAL_ACCEPTED;bounded implementation/native/save/delivery acceptance complete. Self-review,not independent.
Baseline72c2d58plus11accepted F49dirty paths;existing branch reused. F49receipt/order/test
hashes preserved at entry;no commit/push/PR/merge,agents,release or checkpoint waiver.

## Implementation

Cycle talk now reports confirmed prepared/used count changes since the previous retained
conversation,or explicitly since the source checkpoint when no earlier talk is retained.
The existing single isolated replay captures exact selected Supply states at checkpoint
and latest2talks. Counts compare these verified committed states;no periodic reconstruction
or invented missing activity. Whole-range counts stay distinct from retained4detail anchors.
Same-turn supply actions are included once;retry and next talk never repeat the delta.
F49call-only API remains exact;new cycle_return_recollection shares the same factory/call
renderer and is wired to ClientSession→worker→Tk/binary bridge→Unity ordinary talk.
No CORE/schema/pins/save/wire/content/production Unity behavior change.

## Verification so far

- First red test used unsupported wait17and failed at tick3;corrected to wait16+wait1.
  Corrected regression then failed at the intended missing since-talk summary(tick20).
- Initial F50regression+F49selection14PASS33.70s.
- New9cases initially8PASS/1fixture failure:PipeClient.send has no seconds keyword.
  Reused existing send_seconds helper;final9PASS17.82s. Cases cover since-talk/reset,
  long83second trace with11preparations/8uses despite4anchors,same-turn work exactly once,
  checkpoint16without new inferred changes,previous/current rewind+restart+source bytes,
  one observed real replay with calls/retry,real source-missing/process-control worker
  recovery,actual binary-pipe/load/new-process and actual Tk display.
- Expanded15module selection:241PASS/2sandbox environment failures231.92s. Both failures
  are Windows hardlink permission denial in existing previous-slot recovery tests;the same
  two cases PASS1.36s on permitted execution. Thus243distinct affected cases qualified,
  not one all-green combined run. Original failed output preserved(affected.log).
- Exact checks.yml boundary selection31PASS11.16s(boundaries.log).
- Both Ruff configurations PASS,14CI+changed formatter inputs PASS,strict mypy208files
  PASS via existing pinned source fallback,import contracts3+1KEPT,pip health PASS.
- performance.py uses real committed talk20and verified factory:1000samples of two exact
  state selections plus supply summary rendering,mean0.002276ms/max0.012800ms(<2ms target).
  Representative durable talk+single replay387.947ms(<2s target). Host scope only.

## Native and saved-source qualification

Reused installed pinned Unity6000.3.25f1/editor31168/window3539826,zero launches/restarts.
Temporary F50VerificationTrigger uses approved explicit harbor/catalog SHA,memory1/work0/
cycle1,retained0 and fresh tmp/qtf50/native/game.sqlite then public PlaytestBuild.Verify.
Observed existing window activation refreshed/compiled the trigger and started verification.
Original editor log is tmp/qtf49/unity.log;F50_SELECTION_START marks this run. Starting byte
offset retained under tmp/qtf50/native-log-offset.txt;copy completed F50segment after idle.
New native assertions:talk31since22prepared0/used1;talk37since31prepared1/used0;existing
F49calls and all cycle/save-manager assertions preserved. New cycle-return-change capture.

Input manifest156files and original scene snapshot recorded before native;F49frozen files
unchanged. Actual native run134PASS0FAIL;PASSED/RESULT/RETAINED/IDLE all code0. Completed segment
copied to tmp/qtf50/unity.log after F50_SELECTION_START,without overwriting earlier F49
log bytes. Actual642x500cycle-return-change.png inspected:previous22and prepared0/used1
are readable with original own-memory/player/call sections. Talk37similarly confirms
prepared1/used0since31while F49call34/35/36assertions pass.

readback.py/readback.json:exact9owned managed saves validate/replay/query/source bytes
PASS. Current-talk saves retain original prepared1/used0summary;fresh private copies
continue to known new talk ticks2/22/32/38/39/40with independently enumerated empty/5,2/
6,3/empty/empty/1,1changes. Calls remain empty after the last talk,and retry adds no
duplicate summary. All original hashes unchanged. Nine continued-talk samples mean
983.720ms/max1498.042ms(<2s target),host scope only.

After verified idle,removed temporary trigger and generated .meta,kept its source under
ignored evidence,restored scene byte-exact and refreshed/reloaded via observed UI. All156
native input hashes unchanged. Same editor31168retained,zero restart/launch. Final
document guards10PASS1.61s;delivery.py checks14combined dirty paths,UTF-8/local links/
whitespace,all156native input hashes,scene/trigger cleanup and F49frozen witness files.
Progress trio synchronized;final manifest under tmp/qtf50/delivery.json.
Existing CP06release hold and deferred independent review unchanged;D2 remains OPEN.


## Self-review

The new summary compares existing COMMIT-owned states on the registered conversation
route;it does not replace the four detailed anchors or infer lost event identities. The
factory retains only one baseline and two conversation states;default non-cycle paths
remain unchanged. F49public call-only output and frozen receipt/order/test are preserved.
No test assertions,goldens,guards or dependencies weakened. No new full regression,release
build,independent review or whole-D2completion claim. Final static checks apply to current
unchanged Python inputs;final delivery checks are recorded under tmp/qtf50/.


Acceptance:PASS for independent change vectors,source boundary,no duplicate replay,
ordinary callers,postcommit failure recovery,old modes and F49call output,static/affected/
boundary/native/save and document delivery. Local self-review only;D2 remains OPEN.
Goal ACTIVE for subsequent bounded work. No new publication or release authorized by
this receipt. Prior full/build evidence remains historical and input-scoped.
