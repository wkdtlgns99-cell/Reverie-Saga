# QT-F55 — Static schema reuse and binary save-header repair

Status:LOCAL_ACCEPTED2026-10-25. Primary2internal-calculation performance support;
related4retrieval,6save,7integration,5client wait. Self-review only.
Order:[static schemas](../work_orders/QT-F55_STATIC_COMPONENT_SCHEMAS.md).
Baseline72c2d58plus40accepted F49–54dirty paths;entry/source hashes under tmp/qtf55/.

F53profile independently shows343,705calls across8static component schema properties,
about1.37s cumulative with profiler overhead. Neighboring quest/memory/cycle records
already return validated immutable module constants. Applied that pattern to encounter
gate/hp/stamina,trial map/position and watch NPC/lantern/reply. Existing registered
ComponentKeys reuse the same canonical domain constants. No dynamic world-state/result
cache,read-view lifetime change,codec validation skip or change to serialized values.

Eight new parameterized checks pin independent literal kind/version values,distinct
record states,shared metadata across records/registered keys,and ordinary immutability.
Red8FAIL0.38s on original source;after scoped6file change,green8PASS0.18s. Existing tests
unchanged. All7changed/new Python files already meet Ruff formatting;scoped Ruff PASS.

Prepared a private aid source at264from the preserved F54accepted source8with16supported
16second waits. Existing long cycle source261is read-only. Baseline5full ordinary talks
per mode on byte-identical source copies:cycle median2.172809s(range1.820672–2.597735),aid
median2.737609s(range2.662408–3.443048). Every talk checks exact promise2,zero calls/reward,
supply differences,source preservation and exact quiet retry. Separate profiled sample
does not enter unprofiled statistics. Both baseline medians exceed2second TARGET.

The first benchmark invocation preserved its source preparation,then stopped before any
sample because its output name conflicted with the owned baseline-source snapshot folder.
Changed only the helper output destination to measurements/{phase};reused the already
prepared aid source without replaying waits. Original failure remains in baseline.log.

Optimized measurements,full/affected/static checks,real bridge/native integration and
final scope/preservation review remain pending. Current feature is not accepted on the
strength of the8new unit cases. CP06held,D2OPEN,no agents/publication/release.

## Paired measurement and static qualification

First sequential optimized phase was inconclusive:cycle median2.449172s versus2.172809s
baseline,aid2.661060s versus2.737609s. Do not claim a speedup from that sequence. Its
profile reduces function calls12,754,004→10,650,442and8schema-property cumulative time
1.531836→0.045671s at exactly350,651property calls;profiled wall8.830286→7.954520s.
These profiler observations do not establish the unprofiled TARGET.

Added5alternating baseline/optimized subprocess pairs per mode. A narrowly scoped import
finder loads only the6exact hash-verified frozen baseline modules for baseline processes;
optimized processes load normal current modules. Each process verifies actual loaded paths.
Production files are never swapped. All10pairs preserve exact input bytes,messages,tick,
supply and core hashes,plus retry/source guards. CPU time separates process work from waits.

| Mode | Baseline wall median/range(s) | Optimized wall median/range(s) | CPU median before→after(s) |
|---|---|---|---|
| cycle |2.381717 /2.357477–2.876988|1.802543 /1.725361–2.010588|2.343750→1.781250|
| aid |2.570909 /2.556968–3.582984|2.417111 /1.894228–3.104920|2.578125→2.359375|

Actual median improvements are about24.3%and6.0%;host variation remains visible. Cycle's
slowest sample and aid's median still exceed2s. The overall2second latency issue remains
OPEN,with the bounded allocation cost reduced. No MIN-SPEC/transport speed claim.
Original phases/profiles and alternating pairs remain under tmp/qtf55/measurements/ and
paired/,with paired-result.json and paired.log. No timing sample is discarded.

Both Ruff configurations PASS;README plus new scoped format18PASS;strict214files PASS
using the same pinned mypy source fallback;type-inclusive imports3/runtime imports1and
pip PASS. Exact current CI12node selection expands to31PASS15.48s(static-result.json/logs).
All production/test inputs are now frozen in full-inputs.json(240files). Full regression
is running in live exec session47096,log full.log,with .pytest_cache/qtf55-full. Its owned
private evidence index contains HEAD plus exact current F54encounter source for the same
three original checkout tests;all other8reviewed source bytes remain HEAD-identical.
No real Git staging/index/reference changes. Do not restart a live job on observation timeout.
Native/backend checks and final delivery remain pending;F55is IN_PROGRESS.

All4existing memory/work/cycle/aid pin sets independently match their pre-edit values
(compatibility.json). Prior37accepted non-progress paths and frozen240full-run inputs
remain unchanged. Prepared bridge.py,long-source comparisons,F55stage watcher and adapted
readback tools under tmp only. Native159input manifest differs from F54only in the6allowed
static-schema sources;original scene snapshot retained. No Assets trigger or stage is armed.
Last observed live full-run progress9%,session47096still running;no terminal/full-pass claim.
Run bridge/native jobs only after this heavy full regression finishes. Resume state and
actual quota snapshot are in tmp/qtf55/resume.json;no scheduled wake-up was registered.

## First full pass and real Windows binary-header failure

First full invocation2355PASS1449.97s,session47096terminal0. All240frozen inputs and the
real Git index were unchanged at that completion(full-result.json). This qualifies the
static-schema change before the following adapter repair;it is not the final combined run.

Real old-cycle bridge talk262passed in1.342994s. The aid talk265and its read-only activity/
quiet retry assertions completed,but the subsequent persisted-file validation raised
SAVE_CORRUPT at classify_file's header-length check. The106,496byte file physically contains
the correct SQLite signature. Its page-count26puts0x1Aat header offset31. An unchanged-byte
probe confirmed os.open(O_RDONLY)+os.read100returns31bytes on this Windows process;
O_RDONLY|O_BINARY returns the exact100bytes. Ordinary Windows CRT text translation caused
a false corruption report. No save corruption or data loss occurred;original failure retained.

Extended the order for this necessary IO-boundary repair. Only classify_file's local open
flags change:O_BINARYon Windows,unchanged flags on POSIX. All signature/length/application/
version/page/limit checks,os.read/finally-close and failure codes remain. No format migration,
header fallback,validation suppression or global process-mode change. The precise adapter
diff is independently checked against HEAD. Whole-file formatting already fails at HEAD;
legacy style retained(binary-format-baseline.log),with no configured format target removed.

New real SQLite cookie tests26/0x0D0A/0x1A000001reproduce3false failures;two malformed-header
cases already reject correctly. After repair,affected storage/recovery/slot/inventory/
durable/replay selection103PASS/1sandbox hardlink PermissionError147.96s. The exact original
hardlink case passes with permitted access1PASS0.39s;all104distinct cases qualified. No
test or original failure is hidden. New tests do not patch app save bytes:SQLite writes
legal internal schema cookies while application version1and authoritative rows stay fixed.

Recovered both already-committed bridge files at262/265by validate/replay/core-hash checks,
issuing zero commands and preserving bytes(bridge-recovered.json). Fresh copies then pass
actual framed talk/query/retry/source guards:cycle1.348574s,aid1.501464s,within the existing
10second deadline and with exact messages/core matching direct sessions. These are single
samples,not general2second acceptance. Both timed conversation profiles call classify_file
zero times,so the independent schema-allocation measurements remain labeled to their
original pre-repair inputs;no new speed ratio is inferred from the IO repair.

Post-repair both Ruff/format19/strict215/import3+1/pip PASS;exact CI31PASS10.14s in separate
*-repair.log/static-repair-result.json files. Original static logs retained. Current241inputs
are frozen in full-repair-inputs.json;only the adapter differs among the previous240inputs.
Native159manifest refreshed only for this authorized adapter change;no stage/Editor file
installed. Fresh combined full regression RUNNING session97966,full-repair.log,private
qualified index reused. All other jobs are terminal;never poll/restart47096as a live job.
Native aid/cycle/readbacks and final delivery remain pending. F55is IN_PROGRESS.

## Current combined acceptance

Fresh combined full2360PASS923.83s,session97966terminal0. All241post-repair inputs and the
real Git index remain unchanged(full-repair-result.json). This includes both source changes
and all13new cases;first full2355before IO repair remains separately recorded. No earlier
test/golden/CI rule was changed or skipped. Private index qualifies current8reviewed source
bytes only;no remote CI or published-head claim follows.

Reused the same installed editor36260/window328814with an owned F55stage watcher. No second
editor launch. Its existing log stays at tmp/qtf54/unity.log;bound the complete existing
prefix length/SHA before starting and copy only the append-only task suffix into F55unity.log.
capture_log.py checks both original prefix preservation and its own accumulated prefix.
Earlier F54log content is retained,not truncated or relabeled.

| Fresh native stage | PASS | FAIL |
|---|---:|---:|
| aid1 |36|0|
| cycle1 |153|0|

Both independently contain PASSED/RESULT0/RETAINED0/IDLE0. Native total189PASS0FAIL. Actual
642x500aid open/completed captures inspected:the factual NPC opening follows the blocked
door message. Registered checks observe the actual gate GameObject through previous-load,
reconnect and reported/closed states. Old-cycle stock/calls/history/slots remain qualified.
An initial Computer Use Ctrl+R request timed out while observing input completion;fresh
window/log inspection proved the requested aid stage had already finished successfully.
Did not repeat that stage,restart the editor or infer failure from the observation timeout.

All13exact managed native saves(4aid+9cycle,lock databases excluded)validate/replay/query,
retain original bytes,and continue in fresh copies with correct ordinary talk supply deltas
and quiet retry. Mean talk0.706341s,max1.071299s;these short saved-source probes do not close
the long-history2second issue. Logs/results under readback-{aid1,cycle1}.json and
native-readback/. Native saved-source tick multiset0/8/8/20/30/30/30/37/38/38/38/38/39.

Removed only the owned stage,Editor trigger and meta,retaining copies under tmp;restored
original PlayRoom.unity byte-exact and accepted its Reload in the editor. All159current
native inputs match the frozen manifest. Actual idle screenshot and process observation
confirm editor36260retained,out of Play mode,zero owned Brain processes. Existing editor
font-reference warning remains;captured Korean text is readable,no font repair is claimed.
No Assets trigger or automatic stage is armed. Unchanged C#sources/player packaging reuse
F54build/hook-exclusion evidence;no new build or standalone/release acceptance is claimed.

Self-review verifies all8canonical TypeKey values and legal dependency direction,unchanged
ComponentKey identity guards,pins,codec validation,read-view epochs and COMMIT ownership.
The save fix changes only Windows descriptor flags and preserves all validation/cleanup.
All4memory/work/cycle/aid pin sets remain equal. Earlier37non-progress delivery paths stay
byte-identical. Final scope51paths,document/UTF-8/link/whitespace/source receipts are bound
by delivery.py after synchronized root/order updates. No whole-file reformat,domain cache,
public storage contract or governance change. Some2s overruns,D2,independent patch review
and CP06release hold remain open. Local only;no commit/push/PR/merge/agents/publication.
Automatic goal remains ACTIVE for the next authorized bounded task.
