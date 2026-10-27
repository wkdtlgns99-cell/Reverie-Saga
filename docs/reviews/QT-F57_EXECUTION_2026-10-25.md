# QT-F57 — Canonical conversion execution

Status:LOCAL_ACCEPTED2026-10-25. Self-review only;not independent acceptance.
[Order](../work_orders/QT-F57_CANONICAL_CONVERSION.md) owns scope/acceptance.
Primary2internal-calculation performance support;related4/6/7/5. No gameplay capability.

## Change and preliminary qualification

Fresh current aid265read-only profile:10,438,742calls/5.810s with profiling overhead.
Canonical JSON20,201calls/1.350s cumulative and separate plain-tree conversion0.363s;
global seal1.765s also includes other callers. This is diagnostic,not unprofiled latency.
Exact source bytes retained in tmp/qtf57/profile-result.json.

One private recursive converter retains all scalar/key/type/NFC/UTF8/depth validation.
Immutable mode still creates owned MappingProxyType/tuple DTOs. Serialization mode
creates owned dict/list directly for unchanged sorted compact UTF8 json.dumps options.
No domain cache,trusted-input shortcut,new format,pin,hash rule or public signature.
Removed private _plain has no source/test callers outside the old canonical pipeline.
Scoped formatting of the small changed module also normalizes old line wrapping.

New42semantic cases plus4existing literal vector/hash tests:baseline46PASS0.31s;
current46PASS0.28s. Optimization has no intended functional red case. Independently
specified literal bytes,subclass/non-NFC/surrogate/key/unsupported/cycle/depth/error
precedence,immutable snapshot/alias ownership and caller preservation qualify semantics.
Ruff both/format14/strict217/import3+1/pip PASS;exact current CI31PASS13.64s.

Five alternating pairs per mode,20fresh subprocesses with only frozen canonical module
import differing:cycle talk median1.704118→1.598855s,CPU1.703125→1.5625s;aid talk median
1.955706→1.827731s,CPU1.921875→1.765625s. Identical nested document1500serializations
median0.450247→0.307717s(cycle group),0.474761→0.314863s(aid group). All10pairs preserve
messages/core/protocol/micro bytes/source hashes/supply/retry. One cycle pair regressed
1.696398→1.774788s;optimized aid range1.775183–2.505368s includes one2starget overrun.
Raw samples retained;median improvement does not close broad long-talk/MIN-SPEC targets.

All evidence is under owned tmp/qtf57. Original54dirty paths are preserved except the
authorized3root progress files and2C#verification-isolation changes. No extra production
scope,real Git staging/ref change or publication. Current build evidence is below.

Initial full-launcher preflight(not pytest)required raw Git blob/working bytes equal.
The preserved reviewed-source blob is LF14,654bytes;unchanged Windows checkout has
355CRLFpairs/15,009bytes. Normalized bytes and all text lines are identical. Fixed only
the owned launcher's Git-normalization check;no source/index content altered. Original
launcher/failure hashes retained in full.first.py/full-preflight-first.json. First pytest
invocation started only after this corrected preflight;no completed test was restarted.

Full regression session62881terminal0:2418PASS1343.55s in one invocation. Default
capture=sys,permitted host and separate copied reviewed-source index/objects;all244
frozen inputs and real index preserved. No published CI/staging/ref claim.

Actual unchanged binary framed worker protocol:cycle talk262=1.702142s,aid265=1.818140s;
messages/core/protocol exactly match current direct samples,activity/retry/source-byte
guards PASS. Existing10sdeadline qualified by these samples;not a broad target closure.
Session72164terminal0;no source saves mutated,only fresh owned copies accept new talk.

Native aid54PASS0FAIL/result-retained-idle0;4actual save readbacks replay/query/independent
assistance/new-talk/retry/source-byte PASS. Actual642x500open/completed captures inspected.
Initial Ctrl+R computer-use observation timed out;fresh retained-editor log proved the
stage had already run,so no repeated input/restart. Actual desktop was occluded by the
user's active game;no manual button/unobstructed desktop qualification or game control.
Cycle1failed strict genesis. Direct read-only validation proves tick1/one actual
`trial.move(0,1)`before any scripted movement;PlayRoom's normal physical keyboard/UI
path was still active while the user played another game. Original tick0oracle remains.
Preserve all5initial sources(raw aid1and failed cycle1),hashes/log and original C#inputs.

Order scope explicitly amended for editor/development per-room physical-input isolation
in PlayRoom/LiveVerification:runner sets flag before readiness,clears on destruction;
Poll/render/direct script commands continue,physical Escape/movement and IMGUI key/mouse/
scroll inputs alone are suppressed during automation. Defaultfalse;nondevelopment field
and guards excluded. No OS/game input control,domain change or assertion weakening.
Current editor DLL metadata confirms the flag compiled. Only2C#hashes rebound in the
159input manifest;original scene hash stays frozen for final restoration. First attempt
to rebind detected expected generated scene bytes and stopped before writing;explicit
scene exclusion preserves the original scene hash. No runtime source/golden changed.

Current aid2=54PASS/cycle2=153PASS,all original assertions unchanged and both result/
retained/idle code0. Python
source/tests/tool244inputs stay unchanged,so completed shared-CORE full remains valid.
Source search finds no Python consumer of these2modified C#files(only unchanged
Wire.Generated.cs);native/current build qualifies the C#repair. F56build reuse superseded.

All13current native managed saves(4aid2,9cycle2)validate/replay/query independently
confirmed assistance,then new-talk supply deltas/retry on isolated copies/source bytes
PASS. Continued-talk mean0.913122s,max1.516817s,short-source scope. Sessions72122/34232
terminal0. Actual642x456current aid-completed/cycle-causal-call captures inspected;
these are distinct from the initial642x500captures. No manual/unobstructed gameplay claim.

Fresh Windows nondevelopment build89,491,232bytes:
`tmp/unity-builds/04aa887aea7948898ab8c709132a2643/ReverieSaga.exe`.
Actual Assembly-CSharp.dll PE type/method/field metadata:PlayRoom present,LiveVerification,
get_GateOpenForVerification and IsolatePhysicalInputForVerification absent. DLL SHA256
`754557b1075528887b669b0f83a7eb0293a838fef23c1b9c0d5a85e0da2cd8d3`.
Build PASS/F57_BUILD_COMPLETE;no standalone execution/qualification inferred.

## Cleanup,review and limits

Owned trigger/meta/stage removed;original PlayRoom.unity bytes restored,all159current
native input hashes preserved. User then stopped Computer Use with physical Escape
during the post-cleanup window observation. No further Computer Use calls. Subsequent
file/hash/log checks and process metadata only:editor36260retained(same creation time),
0owned F57Brain processes. Last confirmed editor-idle codes are before the build;
post-cleanup editor scene reload/screen remains UNVERIFIED. Disk restoration is proven
independently;do not silently treat the missing UI observation as performed.

Self-review:all11canonical public signatures preserved;actual baseline/current converter
and C#diffs inspected. Validation/depth/key/error branches share one implementation;
serialization avoids a second tree traversal,seal retains owned immutable containers.
Automation flag is per-room/defaultfalse/runner-lifetime/nondevelopment-excluded;Poll,
direct scripted commands,rendering and every original native oracle remain. No Python
source changed after the full run. Current244full/159native inputs,index and initial5/
current13save hashes preserved;final58paths/49prior non-scope files/UTF8/local links/
whitespace and10document guards are bound by delivery.json. Local qualification only.

Goal ACTIVE,no agents/publication/release. CP06held,D2/independent patch rereview and
long-talk2s target OPEN until appropriately qualified. Retain editor36260;no game control.
