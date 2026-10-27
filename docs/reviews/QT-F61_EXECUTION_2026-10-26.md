# QT-F61 — Codec round-trip canonical conversion

Status:LOCAL_ACCEPTED2026-10-26. Self-review only,not independent.
Acceptance evidence:owned delivery.json and actual logs,not this status alone.
[Order](../work_orders/QT-F61_CODEC_ROUNDTRIP_CONVERSION.md) owns scope/acceptance.
Primary2internal-calculation performance support;related4/6/7/5.

## Implemented and qualified so far

Actual class is RegisteredStateIO;F60diagnostic used an inaccurate CompiledStateIO label,
but recorded source paths/functions/profile rows are correct and preserved.
Production delta is two round-trip comparison expressions plus one explanation:remove
only seal immediately before canonical_json(object_value(codec.encode(...))). The
shared canonical converter still validates recursively while building its owned JSON
representation. Top-level mapping checks remain. Initial seals,owned immutable decoder
inputs,record immutability/codec identity/closed fields/ranges/roundtrip/read adapters,
checkpoint/hash/replay/witness paths and current consumer wiring remain intact.
No cache/public schema/pin/save envelope/contract change.

New36boundary cases pass on unchanged baseline0.40s,then changed focused120PASS1.72s,
including registered independent reference bytes,replay and save checks. New probes
exercise malformed second encode after valid decode;exact component/payload codes/paths,
source/core preservation,Unicode/depth/cycles/unsupported types/shape/losslessness and
owned immutable returned/decoder DTOs. They do not assert private implementation counts.
Ruffboth/format21/strict221/import3+1/pip/exactCI31PASS10.50s;all check exits0.
Current221Python inputs frozen in check-inputs.json.

## Actual matched performance and runtime integration

Five alternating old/new pairs per exact F59source,each on a fresh private committed copy;
baseline package snapshot imports verified by actual serialization module path/hash.
Only existing path/attachment fields normalized;full updates/core/protocol/trace+1/retry/
read-only activity/source bytes exact. All30unprofiled talks are below10sdeadline.

| Source | Old median/range seconds | New median/range seconds | Median change |
|---|---|---|---|
| short supply |0.325855/0.314566–0.358447|0.305071/0.304630–0.308317|-6.378%|
| long supply |1.644966/1.526435–1.678295|1.634219/1.488616–1.677134|-0.653%|
| long old aid |1.773899/1.753241–1.925361|1.750955/1.662392–1.938530|-1.293%|

Some individual pairs regress,including first long supply/old aid. Long-history median
gains are small and may include host variance;no broad2sTARGET closure is claimed.
One instrumented long-old pair:5.688→5.278s,not player latency. Canonical converter
1005860→905156total calls(-100704),seal105353→96723(-8630),canonical_json23243unchanged.
Converter inclusive1.912→1.668s;inclusive stages overlap,not additive phase totals.
This establishes removed work;it does not equate profiler gains with unprofiled latency.
All32sample copies/raw profiles/results/logs retained in owned performance directories.

Current Python actual framed worker runs three six-operation sequences(talk/activity/
retry/wait16/activity/retry),matching F59entire updates and final state/protocol exactly.
Framed talks short/long supply/old aid0.310240/1.533458/1.668679s,all operations<10s.
All17exact F59native save sources validate/replay/query/independent aid-fact recall/new
talk/retry/source bytes PASS under current Python. Readback durations in integration-result.
These are Python integration checks;new Unity native/window/build NOT_RUN.

## Preserved failures and source review

First readback sample committed a valid talk,then verification metadata compared a Python
tuple with a persisted JSON list. Failed script/log/committed copy/hash retained in
integration-first-failure.json;only metadata normalization changed. Accepted rerun uses
fresh readbacks-v2/framed-v2 copies,never repeats a command on the committed failed copy.
First source guard queried F60entry for a scene_sha256 field it does not contain;corrected
to authoritative F59delivery hash. No source mutation/sampling occurred on that guard.

Source preflight:73dirty paths(expected),66prior non-scope hashes intact;all220entryPython
files preserved except exactly serialization.py,new test makes221. Frozen baseline src
is byte exact to entry. Native159manifest has exactly one changed Python source,
serialization.py;other158and original scene remain exact. Real staged delta empty.
No historical index-byte equality claim,F59metadata difference remains preserved.
Actual diff self-review:both removed seals only fed immediate byte comparisons;owned
objects never escape from the removed temporary. Validation remains at public boundaries,
no outcome/test-name/environment branch or skipped domain check. No unrelated source edit.

## Full regression and final qualification

One current full regression2527PASS1272.62s(21m12s),one invocation;session79450terminal0,
PID33460terminal. JUnit2527cases,zero failures/errors/skips,all36new cases included.
One existing record_property/xunit2metadata warning remains retained,not suppressed.
All251frozen full inputs preserved;real index byte-exact during full interval at
0e05744b90eb694a97901c60b41da40dcc2bd4b8e63c0b36268559fe37b82574.
Private reviewed index/objects only;encounter blob9ad4d019573bc5318939ab0e3f93a81a5b712978
matches unchanged F59reviewed source. No real staging or G07obligation change.

Fresh10document guards and final source/scope/UTF8/local-link/whitespace/index qualification
are recorded in doc-final.log/delivery.json.73dirty paths,66prior non-scope files intact;
221current Python hashes and frozen baseline source exact. Native manifest retains158
unchanged inputs with exactly serialization.py as the one intended Python delta;original
scene bytes exact and F59temporary trigger/meta/stage absent. All original saves,32actual
performance copies and the first metadata-failure committed copy retain their recorded
hashes. Independent source/oracle checks plus actual updates/state/retry equality qualify
this local Python optimization,not whole-product/release performance.

Computer Use STOPPED after physical Escape;no window calls/native relaunch/repeated
permission question. Prior native/build evidence qualifies unchanged inputs only;
post-cleanup desktop remains UNVERIFIED. Goal ACTIVE,indefinite objective not complete.
No agents/commit/push/PR/merge/release/timed wake. CP06held,D2/independent review/2sTARGET/
MIN-SPEC/standalone/release OPEN. Resume owned full handle before any new task.
