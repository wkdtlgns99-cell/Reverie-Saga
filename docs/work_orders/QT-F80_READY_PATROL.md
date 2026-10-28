# QT-F80 — Prioritize the NPC own support preparation before patrol

Status:IMPLEMENTED_ENV_BLOCKED2026-10-29. Current Codex/local self-review;not independent acceptance.
Authority:original automatic NPC/world development explicitly resumed by human;actual goal ACTIVE.
Primary2internal calculation;related5/6/7. This is a new bounded opt-in NPC goal priority.

| Field | Contract |
|---|---|
| goal/non_goals | Add npc_ready_patrol optional child of npc_call_pause:after own accepted quest,if selected gate currently closed and prior-POST-barrier own stock below existing SUPPORT_STOCK_MIN,prefer original work cell over patrol. Otherwise existing quest patrol target. Existing actual speech/reply holds and occupied-target checks still win. No new task/action duration/supply production/cost/consumption/aid/range/reward/formula/RNG/persistent goal/queue/component/DTO/schema/wire/LLM/dependency/security changes |
| baseline | HEADa973adfbdbc09f95991197fe4346870f0e755ef5,branch codex/cycle-call-recall-20261024;21F77-F79dirty files/8latest F79hashes verified,staging empty/index saved.111sources and native raw baseline copied under tmp/qtf80;all old evidence preserved. F79new2/direct-framed112ops/static256/doc10qualified;F78required import/successful full ENV001unresolved |
| prerequisites/read_files | ENGINEERING_RULES/handoff/backlog/AUTONOMOUS_EXECUTION/MASTER1NPCgoals/2barriers/8memory,guide/template/setup/README;F74/77/78/79contracts+actual sources. Existing domain quest_patrol_target,cycle Supply/state_at/WORK_PERIOD/USE_PERIOD,domain.npc_work.SUPPORT_STOCK_MIN/STOCK_CAP,WatchNpc._patrol/manifest/reply holds,with_patrol/cycle_bundle/bootstrap,GateRead/CycleRead/CYCLE_FAMILY,field consumers/read adapter registration,client/restore/query/slot/native selectors/live verifier |
| MODIFY absolute paths | C:/Reverie Saga/src/domain/npc_patrol.py;C:/Reverie Saga/src/engines/watch.py;C:/Reverie Saga/src/app/npc_patrol.py;C:/Reverie Saga/src/app/npc_cycle.py;C:/Reverie Saga/src/app/client_session.py;C:/Reverie Saga/src/app/client_worker.py;C:/Reverie Saga/src/app/client.py;C:/Reverie Saga/src/app/engine_bridge.py;C:/Reverie Saga/src/app/npc_activity.py;C:/Reverie Saga/src/app/npc_patrol_status.py;C:/Reverie Saga/clients/unity/Assets/Reverie/Scripts/BrainConnection.cs;C:/Reverie Saga/clients/unity/Assets/Reverie/Scripts/PlayRoom.cs;C:/Reverie Saga/clients/unity/Assets/Reverie/Scripts/LiveVerification.cs;C:/Reverie Saga/tools/replay_body_inventory.json;C:/Reverie Saga/README.md;C:/Reverie Saga/clients/unity/README.md;C:/Reverie Saga/BACKLOG.md;C:/Reverie Saga/SESSION_HANDOFF.md;C:/Reverie Saga/GAME_SYSTEM_SUMMARY_KO.md;C:/Reverie Saga/docs/DEFERRED_USER_DECISIONS.md |
| NEW absolute paths | C:/Reverie Saga/tests/unit/test_ready_patrol.py;C:/Reverie Saga/tests/integration/test_ready_patrol.py;C:/Reverie Saga/docs/work_orders/QT-F80_READY_PATROL.md;C:/Reverie Saga/docs/work_orders/QT-F80_REPLAY_SCOPE.json;C:/Reverie Saga/docs/reviews/QT-F80_EXECUTION_2026-10-29.md;owned ignored tmp/qtf80 |
| forbidden_paths | All other production/contracts/CORE/codec/checkpoint/cycle/aid/old tests/goldens/G07tool/governance/config/scene/assets/content/user/reference sources. Preserve all old native methods except selector/error dispatch additions and a new dedicated ReadyPatrolFlow. No agents/publication/commit/push/PR/merge/release/dependency/security/editor/window/native/compile/build/capture actions |
| public_contract | Exact npc_ready_patrol:bool=False following npc_call_pause in all existing Python bootstrap/bundle/session/worker/Tk/bridge/activity restore/query constructors. True requires immediate npc_call_pause and existing parent chain;invalid bool/parent NPC_READY_PATROL_CONTENT before save/thread,old errors keep precedence. WatchNpc ready_patrol:bool=False requires call_pause=True. --npc-ready-patrol both Python CLIs. Native REVERIE_UNITY_NPC_READY_PATROL absent/0/1 only;invalid NPC_READY_PATROL_SELECTION before child/save. New identity quest.harbor-ready-patrol-v1;new isolated default harbor-ready-patrol/<catalog-pin>/game.sqlite,old10identities/pins/outputs unchanged. New mode label NPC 지원 준비 우선·호출 응답 대기·의뢰 순찰·대화 대기·호출 지원·물자·반복 작업·기억 모드 |
| canonical_target | New pure domain ready_patrol_target(layout,current,known_phase,stock:int,is_open:int)->int delegates quest_patrol_target and reuses SUPPORT_STOCK_MIN=2/STOCK_CAP=3. For accepted and is_open0 and stock<2,target=home;otherwise old target. Exact ints/ranges0..3/0..1,bad types/phase/current/unheard-away reject specific NPC_READY_PATROL_TARGET (boot-invalid layout may preserve NPC_PATROL_CONTENT). No duplicated threshold or saved plan |
| engine_ownership | New-only POST_TICK reads CYCLE_FAMILY plus selected gate space_id/cell/is_open;append watch.npc consumers to existing specs. No new event subscriber or writer. Existing own-memory/source/future/actor/wake validation occurs before new reads. Exact Supply type and value state_at(tick-1) required before same-phase cycle update;gate space/cell binding and exact is_open0/1 required. Bad supply/gate INVALID_FACT with explicit ready-patrol context,not a no-op. Actual POST read barrier is shared by quest.cycle/encounter.actions/watch.npc;newly prepared supplies or aid gate delta in that phase are NOT visible until next barrier |
| priority | Existing unread acceptance stays home;reported memory returns home/idle regardless supply. Accepted low stock+closed gate goes home/holds;adequate stock or open gate follows existing two-cell quest patrol. Existing speech/reply actual-turn pause takes precedence before movement;actor at target still blocks until a later actual wake. New condition never advances supply work or creates another wake;tick/stock units seconds/communal units,existing period/cap tie policies unchanged |
| independent_examples | Starting down1/talk2/up3:old call-pause wait4moves6->7;new mode stays6at4(stock after1),6(stock1),8(stock after2). At8POSTprior stock1still holds6despite same-phase preparation;wake10reads prior2,aid opens gate and NPC6->7(stock after1). Wake12open gate follows patrol7->6despite low prior stock. New even bell10holds6/reply1while aid may open;next non-answer wake12moves7,no latent pause. Closed gate with actor blocking home delays return;after own report next free wake returns and stays. Existing cycle state_at(tick)/supply/aid/reward rules unchanged |
| presentation | New-mode talk/activity/slot next-step rows must use same ready_patrol_target on each verified current/saved snapshot,with its own selected CycleRecord(state_at(core.tick))and gate,actor/memory/pose. No extra replay/IO/context/cache. Existing generic own-quest plan stays as long-term goal;new-only policy explains priority: NPC 지원 준비 · 의뢰 진행 중 통행문이 닫혀 있고 공동 물자가 {SUPPORT_STOCK_MIN}개 미만이면 원래 작업 지점 복귀·대기를 우선합니다. Add once to talk/activity/slot,new-only. Old10allrows remain exact |
| algorithm_steps | Freeze21prior/source/index/native. Record actual old wait4moves7and missing new flag2FAIL. StageAimplement pure target/WatchNpc new read+priority/with_patrol metadata/cycle bootstrap and headless true barrier cases;StageBthread all durable/client/query/native selectors/new dedicated source verifier and truthful new current/saved plans;StageCnew/affected/static/old10parity/current runtime/replay-G07/source/scope/document qualification. Do not call this task accepted at a stage boundary |
| wiring | All factories including durable/retained replay/new restore/slot/current projection receive flag;new-only gate/cycle consumers declared through legal contracts,never engine imports engine. Existing phase/read adapters/delta routes/codecs/presenters/queue reused. Unity existing message/position consumers+new selector/path/mode/new verification dispatch source only;no scene/wirechange |
| edge_policy | Defaults/False old10exact. Missing parent/nonbool rejects before resource IO. Absent/bool/negative/overflow/late/wrong-owner/state/cell/space/supply clock/gate state must reject precise codes. Zero available initial is home;unknown/future memory invalid before movement;already home low stock idles even actor shares cell. Existing odd/even call/talk/rejected actions/no latent retry/save/checkpoint/restart/rollback/uncertain commit behavior preserved. Same-phase8preparation does not qualify early;current after8query may say next goal patrol based on current2without claiming movement at8. Current versus selected snapshots never share gate/stock/actor |
| performance | Constant selected2cells/one CycleRead/one GateRead at actual wake only;no new provider/event queue/replay. Actual retained short/long new-mode direct/framed talk/activity/slot once with full state/protocol/source/retry preservation,target2s/10sdeadline;all samples/misses retained,no speedup/global2s/native/MIN-SPECclaim |
| baseline_commands | Actual old call-pause source via F77session down/talk/up/wait4showsNPC7;new bundle/bootstrap required flag currently raises TypeError,not intended content validation. Capture before code. Independent normal/barrier examples above are derived from actual phase contracts/stock constant,not a new implementation oracle |
| verification_commands | README Ruffboth/scoped format/strict all Python with established source fallback;new normal/boundary/source/manifests/actual headless +durable talk/save/previous/load/checkpoint/replay/retry/rollback/uncertain commit/worker/real pipe/withdrawn Tk/CLI error tests;old10whole stable outputs/descriptors/pins/core/protocol/persisted bodies exact against preserved baseline;actual new11runtime source preservation;current replay/G07retain all35/8/8/4source/range/hash/private-index obligations. ENV001required imports/successful full remain unresolved;no repeated unchanged blocked startup/full or checker/security/golden weakening. Final doc10/CI31/scope/hash |
| test_responsibilities | NEW unit canonical target threshold/gate/phase/invalid exact types,registered POSTreads/consumers/source clock/gate binding/odd/even/talk/call/occupied behavior. NEW integration actual at4/6/8hold10resume and bell10pause12resume,closed/open goal changes/report/return,previous/future/rewound snapshots,save isolation/older pins/restart/compact/replay/retry/source preservation/SQL failures/worker/pipe/Tk/new selection rejection. Real domain outcomes,no mocked aid/work/reward |
| acceptance | Useful new priority reachable all registered player/runtime/replay/query/native-source selection paths;normal+boundary/static/affected/old10parity/runtime/performance/currentG07/CI/docs/source/index preservation complete. Overall cannot be LOCAL_ACCEPTED/DONE while required current imports/successful full blocked ENV001. Fresh native/build NOT_RUN AWAY001;CP06/independent/D2regional/MIN-SPEC/standalone/release/global2sOPEN. StageAcore is progress,not feature completion |
| claude_checkpoints | CP01–05not newly triggered:existing selected WatchNpc/cycle/aid/typed records/adapters/phase barriers/state/save/IPC reused;no new engine/pipeline/format. Current source-bound G07self-review is not independent feedback. CP06held;independent patch rereview remains deferred,no agent launch |
| stop_conditions/delivery | Stop on missing real semantics/user overlap/new authority;record required questions and progress independent work. Sync English order/receipt+backlog/handoff/Korean progress with exact stage/limits. Preserve21prior dirty files and all source saves. Original unbounded goal ACTIVE after task,not complete;03:10follow-up already exists,no new timer/publication/dependencies/native work |

## StageAcore progress2026-10-29 — not task acceptance

Actual old call-pause down1/talk2/up3/wait4NPC7recorded before source edits. New selection
baseline2FAIL0.59s(missing keyword). New core target/manifest reads/bundle consumers/
metadata/bootstrap implemented;2initial integration PASS0.59s,current46unit/headless cases
PASS0.91s. Independent actual12turn numeric vector shows holds4/6/8then10NPC7/gate1,
12NPC6;actual bell10holdsNPC6and next12moves7. Current cycle state_at remains unchanged.
Ruffboth/strict258PASS. Four production files changed at this stage:domain/npc_patrol,
engines/watch,app/npc_patrol,app/npc_cycle. All other107production/prior nonscope/index
preserved. Current source-bound inventory/reflection/registry refreshed,all35/8/8/4old
obligations retained;no current replay/G07/full/native success claim. Typing57038terminal0.

StageBremaining:thread exact flag/validation through durable session+restore+worker/Tk/
bridge/CLI/activity factories;new-mode current/selected plan uses validated own current
stock/gate and canonical ready target. New policy/mode label and native selector/path/
forwarding/error cases/dedicated verifier source. Do not stop at core or call it complete.
StageCremaining:malformed source guards/recovery/replay/old10parity/runtime/performance/
currentG07/CI/doc/scope qualification. ENV001required full/import and AWAY001native stay
unresolved. Resume the same unfinished order,not another feature. Existing03:10wake still
registered;no duplicate timer/agent/publication/security/dependency/native action.

Structural read-error clarification before negative source qualification:missing typed
CORE components/entities retain existing UnknownComponent/UnknownEntity errors,not an
ordinary player rejection or fabricated no-op. Malformed present cycle/gate data uses
CandidateError INVALID_FACT with new-source context;display boundaries use their exact
SaveError caller code. This follows the existing read-view/CORE error authority.

Existing GateAdapter validates exact cell/open integer ranges during registration,so
those malformed fields reject ValueError at that earlier boundary before any read epoch
or engine invocation. Do not bypass that adapter to force a later CandidateError. Present
wrong-space gate and stale/future valid CycleRecord still reach engine INVALID_FACT;
missing entity retains UnknownEntity. Negative qualification follows these actual
registered boundaries;no adapter/engine/checker behavior is weakened.

## StageBcomplete and StageCfreeze entry2026-10-29

All Python player/resource/restore/replay/query paths now thread exact ready flag and
validate parent before resources. Current/saved projection validates its own current
CycleRecord(state_at(core.tick))/gate and uses canonical ready target;policy appears once
in talk/activity/slot. Native strict selector/path/flag/mode/error forwarding and dedicated
ReadyPatrolFlow are prepared,not executed. Actual2direct/framed whole scenarios PASS16.47s,
whole updates/core/protocol exact. New full route initial readiness4/6/8,answer10hold,
12resume,save4/10/previous contrast,load/reconnect10,report26/reward1/return30/gratitude31.
StageB68PASS24.29s included real worker/withdrawn Tk/CLI/previous/checkpoint/pin rejection;
additional new source119PASS3.27s and rollback/uncertain3PASS2.45s. Counts overlap,not summed.

Initial static1unused import/1label-line length/1redundant test cast repaired,then Ruffboth/
strict258PASS. Source fixture first19failed before engine due missing canonical root sort;
repaired setup. Next10range cases hit existing GateAdapter earlier ValueError boundary;
separated exact adapter error tests from later engine source errors without production
mutation/skips. Original failed logs retained. Current all119source cases pass. No domain
oracle/golden/checker weakening. StageCfull affected/CI/old10parity/current11runtime/
long source performance/currentG07/doc/scope qualification pending. New long-mode retained
history263has NPC7and player3out of talk range,so prepare one real down264to adjacent6
before saving;measure talk265/current selected264. No repinning/regenerating old sources.


## Terminal bounded qualification2026-10-29

QT-F80 IMPLEMENTED_ENV_BLOCKED2026-10-29:own supply-readiness patrol priority,
primary2internal calculation;related5/6/7. New opt-in mode prioritizes home while own
accepted quest/gate closed/prior_POSTstock<2;existing speech/reply/occupancy/phase rules
retain priority. All Python client/worker/Tk/CLI/durable/restore/replay/query paths wired;
current/saved displays use each snapshot's own current stock/gate/actor. New147cases
included in792affectedPASS255.58s;exactCI31PASS8.09s;Ruffboth/
format62/strict258PASS. Initial untouched legacy callback test1FAIL/791PASS exposed a
new-keyword/default-mode regression;fixed old invocation shape,focused2PASS2.17s,then
fresh whole792PASS. Old tests/goldens/checker unchanged. Old9whole153updates and tenth
actual direct/framed56each preserve outputs/descriptors/pins/core/protocol/persisted
bodies. New11mode actual7/264sources/direct-framed12query samples,retry,replay/source
preservation PASS;All12samples below2s/10s. No global2s/speedup/MIN-SPECclaim.
Current replay/G07168PASS184.09s,317frozen inputs/index preserved,all
35/8/8/4obligations retained. Exactly10production files changed,101other production/
245legacy nonscopePython/10prior nonscope/index preserved. Native source strict selector/
path/forwarding/new45operation flow prepared and matched actual46updates including attach;
fresh compile/native/render/build NOT_RUN AWAY001. ENV001required current imports/
successful full unresolved;NOT LOCAL_ACCEPTED/DONE. CP06/independent/D2regional/standalone/
release/global2sOPEN. All product checks terminal0;runner55884terminal1at post-check Path audit typo,then
separate preserved-input audit terminal0. Goal ACTIVE,no new publication/agents.
[Receipt](../reviews/QT-F80_EXECUTION_2026-10-29.md).

Earlier StageA/StageBremaining paragraphs are historical snapshots,resolved by terminal
evidence except explicit environment/native/independent/release holds. Final documents
follow terminal0and are checked separately;no subsequent gameplay source change.
Original unbounded goal remains ACTIVE,not complete.
