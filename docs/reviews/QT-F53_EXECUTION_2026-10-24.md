# QT-F53 — Longer retained-history dialogue qualification

Order:[latency diagnostic](../work_orders/QT-F53_LONG_HISTORY_LATENCY.md).
Status:LOCAL_ACCEPTED for diagnostic correctness/evidence;2second target NOT_MET at256.
Baseline72c2d58plus20accepted F49–52dirty paths;existing branch reused,self-review only.
Primary7integration/performance support,related4retrieval/6save/5response wait.
No new gameplay or production/test/Unity/settings/dependency/content changes.

## Unprofiled real-session measurements

Installed Python3.13.12,Windows11build26200,current host;stdlib perf_counter/cProfile.
Use approved harbor cycle content and three private durable saves. Each starts with down1,
talk2,and16second ordinary waits totaling the stated gap. Measure the complete real
ClientSession.act(talk),including COMMIT,durable publication and verified return context.

| Saved gap | Talk tick | Retained commands before talk | Seconds | Prepared/used since2 |
|---|---|---|---|---|
|16|19|3|0.406317|4/1|
|64|67|6|0.829128|9/6|
|256|259|18|2.296391|28/25|

All three independently specified counter summaries,promise at2,no received report/calls/
reward,bounded last4anchors,and retry snapshot/protocol/source-byte guards PASS. These
are one sample per history,not a statistical distribution or device/MIN-SPEC result.
The longest exceeds the2second representative target by0.296391seconds. It is below the
actual Unity BrainConnection.Poll10second deadline,but direct-session timing does not
qualify transport latency,timeout absence,human UX or whole-product performance.

## Original oracle failure and retained source

benchmark.py completed all three samples and persisted timings.json before an extra
profiled talk at260. Its expectation of no new supply action was incorrect:260is divisible
by10and4,so consume-before-prepare correctly adds one use and one preparation. That talk
was already committed. Original exit1/assertion/log and saved source retained;no production
bug or rollback claimed and no unchanged benchmark sample repeated to obtain green output.

resume_profile.py first verifies all103production Python hashes,opens that same saved
source at260,and checks29prepared/26used. It profiles the next real talk261,which has no
supply action,verifies the empty change message/original promise/no calls or reward,
and verifies retry snapshot/protocol/file bytes. Final103hashes unchanged. PASS.

## Actual profile and next repair boundary

Profiled act261:7.949334seconds,20retained commands before talk. This is a later trace
with two more commands than the original259sample and cProfile overhead;do not compare
these elapsed values as a speed ratio. talk-256.pstats/profile.txt preserve actual data.
The profiler reports12,437,496calls(11,296,639primitive);nested cumulative times include:

- _conversation_activity/_verified_activity:7.383seconds;Runner.run:7.302seconds.
- Turn submit:6.572seconds;prepare-commit:2.875seconds;simulate:2.869seconds.
- Component encoding:2.149seconds;canonical seal:1.940seconds;encode_core:1.784seconds;
  validate_checkpoint:1.689seconds;read-view install/register:1.414/1.391seconds.

These nested values overlap. The evidence identifies verified history replay and its
serialization/validation work as the primary cost;it does not authorize skipping replay,
weakening validation,shared dynamic-state caches or an unmeasured replacement. Any repair
needs its own bounded order and semantic/replay preservation evidence. The measured
overrun remains open;the director selected NPC/world behavior expansion as the next
development direction,so this supporting diagnostic does not claim a new NPC capability.

## Source preservation and delivery

readback.py reopens all three actual sources,checks final ticks19/67/261and exact stock/
produced/consumed(3/4/1,3/9/6,3/29/26),runs each complete retained trace through the
canonical runner,and verifies source bytes after close. All3PASS(readback.json).
No new native/build/full regression is needed for unchanged production inputs;reuse
F49–52evidence only within their unchanged scopes. No new independent review claimed.

Final document guards10PASS3.06s;scope/hash/link/UTF-8/whitespace evidence is under tmp/qtf53/;root progress
trio synchronized. Previous20path inputs frozen except the allowed progress trio.
CP06held,D2/broader performance/human UX/device acceptance remain OPEN. Goal ACTIVE;
no publication,agents or release. Next bounded implementation follows the director's
NPC/world behavior preference and must settle its actual contracts before source edits.
