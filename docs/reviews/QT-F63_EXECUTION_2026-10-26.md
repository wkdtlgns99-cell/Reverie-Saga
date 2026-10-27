# QT-F63 — Invocation-local registration metadata

Status:LOCAL_ACCEPTED2026-10-26. Self-review only,not independent.
[Order](../work_orders/QT-F63_REGISTRATION_METADATA.md) owns scope/acceptance.
Primary2internal-calculation performance support;related4/6/7/5.

## Current implementation and functional checks

Only ObservedReadViewFactory.register changed:reject frozen registration before looking
up adapter.key,snapshot immutable key/schema once within the call,perform duplicate schema
check,store the same key/adapter,and validate every matching root record in original order.
No cross-call cache,CORE/root index,record/port/factory/outcome reuse,custom registration
bypass or public contract/pin/save/wire change. _component/open/close and actual callers
unchanged. Validator exceptions and original registration insertion semantics remain;
no invented rollback or suppressed failure. Exact alias identity remains distinct.

New8functional boundaries pass baseline0.06s,changed focused58PASS2.28s across read views,
registered IO,save and durable replay. They cover matching-record order/fresh reads,
duplicate rejection without replacing original adapter/key,frozen/closed guards without
late key access,empty root/missing entity,unregistered backing,unchanged validator exception,
per-factory changed metadata identity,fresh records/ports and expired aliases. Existing
nested observations/mutation/reference fixtures/replays unchanged. Tests do not assert
private key-getter counts or mock domain outcomes.
Ruffboth/format25/strict225/import3+1/pip/exactCI31PASS7.53s,all8checks exit0. Existing
selective format rollout remains;read_views outside that whole-file rollout,changed range
style reviewed rather than reformatting unrelated source. Current225Python hashes frozen.

## Actual paired measurement and consumer evidence

Five alternating actual committed talk pairs per exact F59short supply/long supply/old
aid source;each sample a fresh named copy. Actual baseline/current read_views module
path/hash verified. Entire current F62update/core/protocol/trace+1/retry/read-only query/
source bytes match;only standard path/attachment metadata normalized. All30unprofiled
talks below10sdeadline;all32sample copies/results/raw profiles retained.

| Source | Old median/range seconds | New median/range seconds | Median change |
|---|---|---|---|
| short supply |0.222705/0.220314–0.230087|0.221003/0.219222–0.226211|-0.764%|
| long supply |1.118106/1.113792–1.127773|1.100871/1.097091–1.117073|-1.541%|
| long old aid |1.236144/1.228337–1.243627|1.221289/1.215626–1.298671|-1.202%|

Some individual pairs regress,including first two long-old samples. Gains are modest and
may include host variance;no global2sTARGET/MIN-SPEC closure. One instrumented long-old
pair3.931246→3.891081s includes profiling overhead and is not player latency.
Raw profile attribution:key getter calls from register392436→55275(-337161),all
orchestration key calls420087→82926;other key reads27651unchanged. Register55275calls
and orchestration validate38385calls unchanged. Register inclusive0.481739→0.401891s;
inclusive stages overlap,never sum as disjoint savings. Removed static work is actual,
but its profile reduction must not be equated with whole-player latency improvement.

Current17exact F59native save sources validate/replay/query/independent assistance facts/
new talk/retry/source bytes PASS under current Python. F62plan contributes exactly one
extra supply activity row compared with historical F59summary;other recorded fields
match,normalizing tuple/list verification metadata only. No failed sample or repeated
committed-copy command in F63. Actual framed three six-operation sequences match whole
F62current updates and final core/protocol;talk0.223039/1.138275/1.265155s,all operations
below10s. These are current Python consumer checks,not fresh Unity/native/build evidence.

## Current full and delivery closure

One current full2591PASS896.80s(14m56s),one invocation,session27240terminal0/PID19532terminal.
JUnit2591cases,zero failures/errors/skips,all8new included. Existing record_property/xunit2
metadata warning1retained,not suppressed. All257frozen inputs preserved and real index
byte-exact during full interval at0e05744b90eb694a97901c60b41da40dcc2bd4b8e63c0b36268559fe37b82574.
Private reviewed index/objects only,unchanged F59encounter blob
9ad4d019573bc5318939ab0e3f93a81a5b712978. No real staging,new G07obligation/inventory change.

Additional source audit inspects actual five selected production modes and twelve adapter
types:each key getter returns its exact fixed module-level frozen ComponentKey. Evidence
in key-source-audit.json;no gameplay run or domain result patch. Generic per-factory key
changes/exact alias/lifetime boundaries remain independently qualified by functional tests.
This supports local metadata reuse;no new promise for invalid changing getter metadata.

Fresh10document guards and final83paths/75prior non-scope/225Python/source/baseline/scene/
UTF8/local-link/whitespace/logical index checks are in doc-final.log/delivery.json. Original
source/sample hashes preserved. Historical native159manifest has156unchanged inputs and
only accepted F61serialization/F62activity plus intended F63read_views Python deltas;new
F62helper tracked in current225Python. C#and original scene unchanged;temporary F59trigger/
meta/stage absent. Fresh Unity/native/build NOT_RUN and not inferred from Python evidence.
Post-cleanup desktop remains UNVERIFIED. Previous historical index metadata difference is
not reset or claimed byte-equal. No full-run timing comparison is a speedup claim:input
counts/host conditions differ from earlier full runs. No live jobs remain.

Before long checks,ordinary usage allowed;last pre-full snapshot primary72%,reset1793013115,
secondary11%,reset1793599915. No actual quota interruption or timed wake at that point;
check live quota at the next task boundary and retain existing reset-only recovery policy.

User away:no questions;record any genuinely required decision in
[deferred memo](../DEFERRED_USER_DECISIONS.md) and choose other authorized work. AWAY-001
now includes F63fresh native/build after earlier F61/F62changes. Computer Use STOPPED,
no window calls/native relaunch;post-cleanup desktop UNVERIFIED. Goal ACTIVE,indefinite
objective not complete. No agents/commit/push/PR/merge/release. CP06held,D2/independent
review/2sTARGET/MIN-SPEC/standalone/release OPEN. Local acceptance complete;next bounded authorized task may proceed.
