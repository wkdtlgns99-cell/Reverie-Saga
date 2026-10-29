# QT-F62 — Current NPC support plan

Status:LOCAL_ACCEPTED2026-10-26. Self-review only,not independent.
[Order](../work_orders/QT-F62_NPC_SUPPORT_PLAN.md) owns scope/acceptance.
Primary4derived factual NPC context/presentation support;related2/5/6/7.

## Player behavior and wiring

Opt-in supply-aid talk and activity now append one current-plan line after their existing
verified replay. Shared pure app/npc_support_status.py selects exactly the current NPC's
own heard quest memory/cycle plus scenario-bound gate. Priority:unheard→heard completion
→currently open gate→missing stock→ready stock. Existing SUPPORT_STOCK_MIN/STOCK_CAP are
canonical;no duplicated balance constant. Missing/duplicate source or wrong gate binding
rejects with caller's existing NPC_ACTIVITY_SOURCE/NPC_RECOLLECTION_SOURCE SaveError.

Independent actual timeline:heard acceptance2stock0shows missing2;talk4stock1missing1;
talk8stock2closed shows readiness,not invented help;actual opening10stock1shows open gate
plan. Close11stock1shows missing1,preparation12stock2shows ready,actual aid14opens.
Manual opening gets current-open plan without fabricated GateAssisted. Heard completion
finishes plan regardless of gate/stock;global quest stage never substitutes for NPC hearing.
No future wake guarantee,historical-help inference or accepted NPC statement is created.

The two existing app activity/recollection consumers append conditionally only when
npc_supply_aid is true. Reuse current verified checkpoint and one replay;no added file IO,
state writes,events,phases,components,payloads/actions,CORE/pins/save/wire/cache or LLM.
Ordinary ClientSession→worker→Tk/pipe message tuples carry the line without client forks.
Precise entry-source wiring diff retained in activity-diff.txt:one import and two guarded
append blocks. Previous accepted code in that already-dirty file is preserved.

## Tests and preserved failures

Baseline missing-line3FAIL1.91s(actual ticks2/4/8),retained. Initial real8PASS6.44s,then
initial unit+integration44PASS7.51s. Expanded first suite55PASS+one new Tk-test KeyError
in17.10s:the test incorrectly searched ordinary action buttons for the separate existing
activity button. Failed script/log retained;actual activity_button.invoke plus normal
Tk pump repair1PASS2.23s. No production bypass/oracle weakening. First strict run found
two test annotations(ComponentRecord dataclass narrowing/EntityIdassignment);retained in
checks-first,then explicit narrowing/EntityId fixed. No domain outcome mock or skip.

Current source-frozen affected26files470PASS280.94s one invocation,session86144terminal0.
JUnit470cases,zero failures/errors/skips,all56new(36unit+20integration) included. All255
frozen inputs preserved. Coverage includes literal precedence/boundaries/source errors,
real previous-barrier state/preparation/help/completion/manual gate,compaction/save previous/
load/restart,quiet retry/read-only query,one real verified replay,invalid owner/core/
protocol/trace/mode,actual framed worker and hidden Tk buttons/log display/input cleanup.
Final Ruffboth/format24/strict224/import3+1/pip/exactCI31PASS7.46s,all8checks exit0.
224current Python input hashes preserved. No shared CORE change:previous full2527has250
of251frozen inputs unchanged,only npc_activity.py differs;this is not a fresh current full.

## Current actual runtime and unchanged old modes

Three exact F59sources,three fresh direct six-operation samples each and one fresh framed
sequence per source:talk/activity/retry/wait16/activity/retry.
Supply talk/activity add exactly the independently specified appended open-plan line;
removing exactly that one documented line leaves the entire F59update identical. Old-aid
whole updates match exactly. Direct/framed complete current updates and final core/protocol
match;query/retry save bytes unchanged,all original sources byte exact,all operations<10s.
All committed sample copies/results/logs are retained under owned performance directories.

| Source | Direct talk median/range seconds | Framed talk seconds |
|---|---|---|
| short supply |0.221837/0.221260–0.221906|0.229775|
| long supply |1.137801/1.117707–1.199322|1.126131|
| long old aid |1.277931/1.261815–1.285677|1.227347|

These are current-host observations,not a pre/post speedup or global2sTARGET/MIN-SPEC
closure. Earlier measured2s overruns remain OPEN;do not attribute host variance to this
small projection. One replay stays verified by a real counted restore test,not a fake result.

Four other modes(memory/work/cycle/aid):isolated package copies differ only by exact
pre-F62activity module,verified to entry hash;new helper is unused there. Fresh real
owned source copies run talk/activity/retry under both imports. Whole updates/core/protocol/
pins match,source bytes preserved,all new plan lines absent. sources/results/process logs
retained under old-modes. This is factual parity evidence,not historical release acceptance.

## Delivery, away decisions and limitations

Fresh10document guards and final79paths/69prior non-scope/UTF8/local-link/whitespace/Git/
source qualification are in doc-final.log and delivery.json. Real staged delta empty and
logical entries preserved. Historical F59index metadata difference remains truthful;
no index reset or claim of historical byte equality. Current scene exact,temporary F59
trigger/meta/stage absent. Historical native159manifest has157unchanged inputs and only
accepted F61serialization plus current F62activity Python deltas;new helper covered by224
current Python hashes. C#unchanged. Fresh Unity/native/build NOT_RUN,not inferred from
Python tests or earlier build. Post-cleanup desktop remains UNVERIFIED.

User away:continue useful authorized work until actual allowance exhausted;no questions.
AWAY-001records fresh native/build and actual required UI resumption in
[deferred memo](../DEFERRED_USER_DECISIONS.md);continue other authorized work meanwhile.
No other concrete user decision is required. Computer Use remains STOPPED,no window
calls/native relaunch. Hidden Tk automated Python checks are not desktop input control.
Goal ACTIVE,indefinite objective not complete,no live jobs. No agents/commit/push/PR/merge/
release/timed wake. CP06held,D2/independent review/2sTARGET/MIN-SPEC/standalone/release OPEN.
