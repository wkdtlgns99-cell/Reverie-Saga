# QT-F64 — Current/selected-save NPC support comparison

Status:LOCAL_ACCEPTED2026-10-26. Self-review only,not independent.
[Order](../work_orders/QT-F64_SUPPORT_SLOT_COMPARISON.md) owns scope/acceptance.
Primary4derived factual NPC context/presentation support;related2/5/6/7.

## Delivered behavior and scope

Existing supply-aid slot preview now appends exactly three lines:current/selected tick
header,currently labeled canonical plan,selected-save labeled canonical plan. Both sides
use their own heard memory/stock/gate. Equal snapshots keep both labels;previous/future/
rewound/report-complete saves remain branch-specific. No inferred past aid/future timing.
One small pure formatter reuses supply_support_plan twice after the caller's existing
identity/anchor validation. No plan-prose copy,parser,new authority or schema framework.

Only ClientSession.inspect_slot changed plus an import. Reuse its already constructed
current checkpoint;existing slot/cycle validation precedes new formatting. A projection
SaveError logs NPC support slot plan comparison failed and propagates unchanged;ordinary
worker error handling preserves current view/input. Other programmer exceptions propagate.
No extra slot read/replay,CORE/state/action/pin/save/wire/dependency/Unity change.
ASTsource audit:only inspect_slot changed among client methods;slot read1→1,snapshot2→2,
protocol2→2. Existing supply_support_plan ASTexact,new formatter calls only that helper
twice. Precise entry-source diffs/source-audit.json retained under owned tmp/qtf64.

## Actual qualification

Baseline actual missing comparison3FAIL2.38s,retained;changed same3PASS2.32s.
New focused21PASS11.81s(12unit+9integration):literal labels/order/priority/source failures,
real equal/current/previous/future/rewind/restart/heard-completion,read-only query/quiet retry,
logged projection failure/worker recovery,actual framed worker and hidden Tk preview/log.
No authoritative outcome mock,oracle weakening or skipped failure.
Current affected28files491PASS291.65s one invocation,session32277terminal0. JUnit491cases,
zero failures/errors/skips,all21new included;all260frozen inputs preserved.
Ruffboth/format27/strict227/import3+1/pip/exactCI31PASS7.73s,all8checks exit0;227Python hashes
preserved. Shared CORE unchanged:previous F63full2591retains255of257inputs unchanged,
only client_session.py/npc_support_status.py differ;not a fresh current full-suite claim.

Current/baseline read-only runtime comparisons use exact same owned saved sources and
isolated pre-F64package imports. Six modes(memory/work/cycle/aid/supply/long supply),each
six queries per variant(current/previous repeated3),72actual queries total. First four
modes entire updates exact;selected supply modes differ by exactly three independently
specified appended comparison lines. All other fields/current activity/core/protocol/pins
match. All managed save SQLite bytes unchanged,source ownership leases excluded explicitly;
original F59long source also preserved. No gameplay command re-executed after a failed writer.

| Current mode | Query min/max seconds |
|---|---|
| memory |0.050355/0.051759|
| work |0.054660/0.058994|
| cycle |0.057115/0.063267|
| aid |0.057854/0.063454|
| supply |0.056413/0.061783|
| long supply |0.089926/0.093295|

All observed direct queries<2sTARGET/<10sdeadline. Not an end-to-end graphical latency,
whole-product2s/MIN-SPEC or speedup claim;earlier long talk overruns remain OPEN.
New Tk tests are automated hidden widgets,not resumed Computer Use. Fresh Unity/native/
build NOT_RUN under existing stop and AWAY-001;current Python evidence is separate.

Fresh10document and final87paths/77prior non-scope/227Python/source/UTF8/local-link/
whitespace/real logical index closure are in doc-final.log/delivery.json. Scene exact,
F59trigger/meta/stage absent. Historical native159has155unchanged inputs and only earlier
F61serialization/F62activity/F63read_views plus current client_session Python deltas;new
support helper in current227manifest. C#unchanged. Historical index metadata difference
not reset or falsely claimed byte-equal. No commit/push/PR/merge/agents/release.

## Explicit manual stop after this task

Latest user2026-10-26:finish only the current F64task,then temporarily pause automatic
execution and provide a very brief1–7summary plus honest remaining scope. This overrides
earlier away/run-until-quota continuation. F64acceptance leaves NO authorization forF65,
quota-resume/wake or other development until fresh user resumption. No live jobs remain.
Repository MANUAL_HOLD is effective after this accepted delivery. The actual app goal
pause is the final required control call after delivery validation;report its returned
paused state in chat,then stop. Do not mark the full indefinite objective complete.
CP06held,D2/independent review/2sTARGET/MIN-SPEC/standalone/release OPEN. AWAY-001retained.

Requested overall summary is grounded in GAME_STRUCTURE_GUIDE_EN,MASTER,BACKLOG/current
sources:1bulk media production deferred;2movement/combat/time/NPC behavior foundations;
3small structured quest/NPC data and validation;4bounded NPC memory/recollection/support
context;5Unity/UIprototype;6durable saves/branches/retry/recovery;7bounded playable quest/
combat/NPC/save flow and verification. Broad world/cognition/relationships/economy/content/
media/final rendering/standalone/release qualification remain. No weighted whole-game
work estimate exists;do not fabricate percent or delivery date from test/task counts.
