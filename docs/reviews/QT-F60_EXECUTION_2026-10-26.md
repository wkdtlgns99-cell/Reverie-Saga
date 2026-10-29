# QT-F60 — Current NPC dialogue cost attribution

Status:LOCAL_ACCEPTED2026-10-26. Diagnostic only;self-review,not independent.
[Order](../work_orders/QT-F60_DIALOGUE_COST_ATTRIBUTION.md) owns scope/acceptance.
Primary7integration/performance diagnostic support;related2/4/6/5.

## Method and actual outputs

Installed Python3.13.12/stdlib cProfile;no dependency or production/test change.
Reused frozen F59owner/io/normalization helpers and three exact F59sources. One new
unprofiled plus one profiled actual ClientSession.act('talk') per source,each on a fresh
owned copy;no domain monkeypatch. Profile starts after constructor and ends before
readback/retry/activity. Six committed samples retained;session99851terminal0.
Normalized complete output equals the accepted F59first direct talk;paired core/protocol
hashes exact. Trace grows by exactly one;retry is quiet with snapshot/protocol/file bytes
unchanged. Activity inspection is read-only;all original sources remain byte exact.

| Source | Tick | Prior trace/witnesses | Baseline wall/CPU seconds | Profile wall/CPU seconds |
|---|---|---|---|---|
| short supply |9→10|3/0|0.309460/0.312500|0.955801/0.953125|
| long supply |264→265|19/0|1.790181/1.750000|5.574982/5.453125|
| long old aid |264→265|24/0|2.049953/1.937500|6.200221/5.921875|

These are three single matched pairs,not a distribution or pre/post repair comparison.
Profiling costs about3.0–3.1x:6.200s is instrumented time,not player latency. Actual old
long talk still exceeds2sTARGET;all unprofiled samples remain below10sdeadline.

## Attribution and next repair

Long supply/old aid profile:publication5.294/5.907s;verified recollection5.096/5.688s;
Runner.run5.011/5.605s. SQLite retained read0.197/0.217s. Replay validation and simulation
rather than storage dominate these samples. Inclusive figures overlap;never sum them.
CompiledStateIO encode_core174/209calls(1.214/1.448s),hash_core94/114(0.826/0.995s),
validate_checkpoint28/33(1.224/1.542s),component-fields3195/3727(1.441/1.648s).
Canonical converter899487/1005860total calls(1.793/2.044s inclusive). Read registration
49016/55275calls(0.677/0.720s);serialization factory3237/3774calls(0.304/0.352s).
Fresh adapter validation/lifetimes cannot be replaced by a cached live factory.

Concrete next responsible-layer repair candidate:serialization.py component and payload
codec round-trip comparisons seal temporary encode output,then canonical_json immediately
validates/converts it again. Both use the same strict canonical converter. Investigate
removing only the intermediate immutable representation consumed solely by that byte
comparison. Keep object shape checks,canonical/depth/Unicode/type rejection,owned immutable
decoder input,codec identity/losslessness,exact error codes/paths and ordinary runtime calls.
No source change or measured improvement is claimed here. A separate bounded order must
prove invalid codecs/round-trips and state preservation,full regression,and matched real
performance/output before acceptance. It may yield only a modest gain;2s remains OPEN.

Rejected shortcut:object_value/exact_fields do NOT recursively seal,so boundary seals stay.
Do not skip checkpoint/replay/hash/witness validation or bypass custom StateIO hashing.
Do not cache mutable/state-derived objects,ports or replay outcomes. Registration metadata
is another measured candidate,not part of this proposed smallest first repair.

## Evidence, qualification and limits

Owned tmp/qtf60/profile_dialogue.py,profile.log,profile-result.json,profile-inputs.json;
three baseline/profiled folders retain committed SQLite/results/raw talk.pstats/cumulative
text/profile JSON. attribution-summary.json reads existing raw profiles without rerunning
talk. Initial profile selector mistakenly named state_io.py;raw profiles were correct;
corrected summary selects actual serialization.py. Original selector evidence is retained.
All229frozen inputs(220Python+helper/source metadata/script+3sources+3expected outputs)
are verified unchanged. F59full2491/static/native287/17save/build evidence is reused only
for unchanged inputs,not claimed as a fresh F60run. Native159,scene bytes and removed
trigger/stage remain preserved. No new Unity/transport test required for this diagnostic.

Final document guards10PASS and delivery/scope/UTF8/local-link/whitespace checks are in
owned doc-final.log and delivery.json.69dirty paths,64prior non-scope paths preserved;
real staged delta remains empty,logical entries match F59. No historical index-byte equality
claim:the F59later cache/stat difference remains recorded with writer unverified.
Actual final evidence is written only after checks pass;this receipt is not standalone proof.

Computer Use remains STOPPED after physical Escape;no window calls/native relaunch or
repeat permission question. Post-cleanup desktop remains UNVERIFIED. Goal ACTIVE,
indefinite objective not complete. No agents/commit/push/PR/merge/release. CP06held,
D2/independent review/2sTARGET/MIN-SPEC/standalone/release OPEN. No timed wake.
