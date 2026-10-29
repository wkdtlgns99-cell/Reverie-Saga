# QT-F67 — Compile immutable serialization metadata once

Status:LOCAL_ACCEPTED2026-10-26. Local/self-review,not independent.
Order:[QT-F67](../work_orders/QT-F67_SERIALIZATION_METADATA.md). Primary2internal
calculation performance support;related4/6/7/5. Automatic objective ACTIVE/unfinished.
No new gameplay ability,contract/schema/pin/save/wire/engine/dependency/governance change.

## Construction and consumers

RegisteredStateIO retains the exact ordered frozen FieldSpec tuples already produced
and validated by its descriptor loop,then publishes an owned MappingProxyType by kind.
_component_fields uses get(kind,()) instead of scanning the whole field registry per
record. All record/codec/type/entity/field/range/cap/NFC/immutable/roundtrip/fresh adapter
validation remains on every call. The fallback matches the prior empty filter.

After existing activation/policy validation,one owned immutable NodeKey→A-lane integer
rank map enumerates the same compiled schedule order. _event and non-simulation
validate_effects use its membership/rank. Rank0is valid;Bnodes do not shift ranks;
different phases remain separate keys. Payload,producer,emission,phase,activation,
wave,sequence,time,causality,identity,ordering and effect checks remain. No mutable
state/decoded data/validation result is cached;maps live only with their own IO instance.

## Entry and baseline

Owned evidence:tmp/qtf67. All96F66delivery path hashes verified,frozen baseline src.
HEAD72c2d588d7f64c3e113cf462af35fb673bf82582,branch codex/cycle-call-recall-20261024.
Real index0e05744b90eb694a97901c60b41da40dcc2bd4b8e63c0b36268559fe37b82574;staged empty.
No agents/publication/remote administration. Previous turn PROGRESS:F66accepted.

profile-before-result.json uses four actual unchanged sources:short supply tick9→10,
long supply264→265,old aid264→265 and new call267→268. Unprofiled/profiled copies preserve
whole updates/core/protocol/trace/retry/activity/source bytes. Baseline unprofiled times
0.2948754/1.4655825/1.7062528/1.5860697s respectively;profiling is about3times slower and
is not player latency. Current long profiles invoke _component_fields3195/3727/3534times
and _event542/592/588times;old implementation reconstructs the corresponding fixed
metadata each time. Inclusive profiling costs overlap and are not summed as disjoint.

baseline.log:14PASS0.51s before production edits. Independent cases retain exact component
values and fresh codec calls,invalid values,rank0/invalid numeric ranks,B-lane filtering,
same producer in two phases,per-IO differing bounds and invalid registry rejection.
focused.log:77PASS6.22s after edits,including registered IO/events/codec/replay boundaries.
Two test-only strict-type errors in a raw event dictionary remain in mypy.first.log;
annotated it JsonObject,without production changes/type-policy weakening. Current
checks-console.log:both Ruff/format33/strict232/import3+1/pip/exactCI31PASS10.69s.
Final annotation correction is additionally covered by the required current full run.

## Current measurements

profile-after-result.json and profile-comparison.json preserve every baseline/profile
whole update/core/protocol/retry/activity/source. _component_fields/_event/validate_effects
entry counts are exact before/after,so no validation operation was skipped. Separate
unprofiled after cohorts are slower (0.350/1.769/2.000/1.916s);those non-alternating values
are retained as cohort drift,not a measured optimization gain. paired comparison is
required before any speed claim.

The alternating20-pair run (exec69376) completed successfully. All four sources/five
pairs each retained,whole outcomes/core/protocol/retry/query/source and current inputs
exact. Talk medians:short0.320366→0.306564s(-4.31%);long supply1.552438→1.560124s(+0.50%);
old aid1.678067→1.668798s(-0.55%);call1.630099→1.631066s(+0.06%). Some individual regressions
remain. Long end-to-end improvement is small/within noise;global2sTARGET remains OPEN.

The old-aid first-IO median increased0.016152→0.017428s(+7.9%),so the order's investigation
threshold was triggered. cold.py(exec48164) alternated five process pairs,5explicit warmups
then40fresh IO instances per child:200measured per variant. Combined repeated construction
median0.0158827→0.0162654s(+2.41%,+0.383ms);individual batch changes-0.53%..+4.31%. Exact pins
throughout. This qualifies repeated construction overhead only;first-import/attach effects
and all original larger samples remain retained. No claim that initialization is faster.
The small startup cost is accepted for removal of observed repeated per-record/event
metadata scans;whole long talk speed is not claimed materially improved.

source-audit.json/serialization.diff normalize only the two metadata constructions and
three consumers/two rank lookups:all other module ASTexact. Actual six-mode ownership
checks confirm exact tuple identity/order/frozen FieldSpec references,owned MappingProxyType
maps,exact schedule A-ranks.91prior non-scope paths/index preserved. audit_source.first.py
retains a diagnostic SyntaxError from using the reserved word import as a Counter keyword;
corrected it to a dictionary key;no production/check success came from that attempt.

runtime/old-result.json(exec31359) verifies six modes x16whole before/current updates,
core/protocol/pins/schema/rules bytes exact with no message stripping. Actual direct/framed
ready sources8/267initial activity/talk/activity/slot/retry are exact and source files preserved.
Long talk1.769237s/direct,1.736597s/framed;long activity1.798781s/direct,1.803535s/framed.
All below10sdeadline in these samples;not global2s/MIN-SPEC/native/build qualification.

## Current full regression

One current full run completed:exec46743,pytest PID28040,**2726PASS** including all14new
cases;no failures/errors/skips. One existing JUnit metadata warning retained. Wrapper
elapsed**1420.46s**. All271frozen inputs/real index preserved;private reviewed index/
objects remain separate,reviewed engine blob3ca0453b58cbe6819c28abc234aafc67b0c034b7,F65scope
unchanged. Current complete persisted benchmark segments:20pairs/40files have exact
checkpoint/protocol/retained traces,all source bytes preserved (saved-pairs.json).
All baseline/profile/pairs/cold/runtime/static/full sessions terminal,no live jobs.
Usage before full was ordinaryAllowed,primary73%/secondary27%,reset1793032056;not a quota
interruption and no timed wake registered. Runtime/pairs/source/metadata evidence above
is current;historical full evidence was not substituted for this run.

## Remaining acceptance and limits

Current full and preceding measurement/source/runtime/static/saved-trace checks qualify
the local scope. Root trio/deferred are synchronized;final document/scope/index/UTF8/link
closure is recorded in delivery.json. Do not relaunch on observation timeout. No fresh native/build/window calls;
AWAY-001Computer Use STOPPED and dedicated call-mode native qualification deferred.
CP06held,D2/independent patch rereview/global2s/MIN-SPEC/standalone/release OPEN. No agents/
commit/push/PR/merge/release/timed wake. Root trio/deferred/final document/scope/index
closure PENDING;retain objective ACTIVE after bounded acceptance,not complete.
