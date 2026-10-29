# QT-F77 — Hold NPC patrol during an actual answered call

Status:CHECKPOINT_PARTIALLY_QUALIFIED2026-10-28. Current Codex;local self-review,not independent/native acceptance.
Authority:latest human resumes original automatic goal;ACTIVE verified. Prior checkpoint pushed;no new publication. Primary2
internal calculation;related5/6/7. F76ENV-001acceptance remains deferred,not waived.

| Field | Contract |
|---|---|
| goal/non_goals | Add an explicit optional NPC call-response movement hold:the NPC keeps its current cell during an actually answered call and follows its existing own-knowledge patrol goal at the next actual wake. No persistent pause/goal/memory/new queue,new engine/DTO/payload/save schema/wire,supply/aid/reward/call-range/hearing change,LLM/provider/dependency/security/governance bypass. This extends existing deterministic NPC interactions,not a regional cognition claim |
| baseline | HEAD72c2d588d7f64c3e113cf462af35fb673bf82582,branch codex/cycle-call-recall-20261024;all145F76blocked-snapshot hashes/index verified,staging empty,no live jobs. tmp/qtf77/entry.json and baseline111sources/145prior files. Actual old quest-patrol down1/talk2/up3/bell4:reply1commits while NPC6moves7in the same answered turn;wait6returns6. Separate owned SQLite/log retained. F76full3123cases/3037PASS/86ENV-001FAIL is prior partial evidence,not a successful full |
| prerequisites/read_files | ENGINEERING_RULES/handoff/backlog/Korean guide/MASTER1NPC goals-memory+2Brain/3causality;v2.6immutable/read-view/phase/checkpoint rules;Sol template/AUTONOMOUS_EXECUTION/setup/README/deferred/F74-F76orders+evidence;actual WatchNpc._spoken_patrol/_patrol/manifest,WatchEchoEngine/WatchReplied/ReplyRead/REPLY/ReplyAdapter,EncounterActions._aid_source (reference only,no engine import),with_patrol/cycle_bundle/bootstraps/client/worker/Tk/bridge/activity factories/native selectors/live verifier/G07tool+inventory |
| MODIFY absolute paths | C:/Reverie Saga/src/engines/watch.py;C:/Reverie Saga/src/app/npc_patrol.py;C:/Reverie Saga/src/app/npc_cycle.py;C:/Reverie Saga/src/app/client_session.py;C:/Reverie Saga/src/app/client_worker.py;C:/Reverie Saga/src/app/client.py;C:/Reverie Saga/src/app/engine_bridge.py;C:/Reverie Saga/src/app/npc_activity.py;C:/Reverie Saga/clients/unity/Assets/Reverie/Scripts/BrainConnection.cs;C:/Reverie Saga/clients/unity/Assets/Reverie/Scripts/PlayRoom.cs;C:/Reverie Saga/clients/unity/Assets/Reverie/Scripts/LiveVerification.cs;C:/Reverie Saga/tools/replay_body_inventory.json;C:/Reverie Saga/README.md;C:/Reverie Saga/clients/unity/README.md;C:/Reverie Saga/BACKLOG.md;C:/Reverie Saga/SESSION_HANDOFF.md;C:/Reverie Saga/GAME_SYSTEM_SUMMARY_KO.md;C:/Reverie Saga/docs/DEFERRED_USER_DECISIONS.md;this order |
| NEW absolute paths | C:/Reverie Saga/tests/unit/test_call_pause_patrol.py;C:/Reverie Saga/tests/integration/test_call_pause_patrol.py;C:/Reverie Saga/docs/work_orders/QT-F77_CALL_PAUSE_PATROL.md;C:/Reverie Saga/docs/work_orders/QT-F77_REPLAY_SCOPE.json;C:/Reverie Saga/docs/reviews/QT-F77_EXECUTION_2026-10-27.md;owned ignored tmp/qtf77 |
| forbidden_paths | All other production/domain/contracts/CORE/original checkpoint policies/codecs/reducers/presenters/old tests/goldens/G07tool/governance/scene/content/old orders-receipts/user/reference files. Preserve F76source/tests/evidence unchanged except current progress routing. No agents/publication/commit/push/PR/merge/release/dependencies/security/window/editor/native/build actions |
| selection/public_contract | New exact npc_call_pause:bool=False after npc_quest_patrol through existing with_patrol/cycle_bundle/bootstrap/client/worker/Tk/bridge/activity/return replay factories. True requires immediate npc_quest_patrol and the existing parent chain;invalid new bool/parent raises NPC_CALL_PAUSE_CONTENT before working-save IO/thread,old errors retain precedence. WatchNpc call_pause:bool=False requires quest_patrol=True. --npc-call-pause in both Python CLIs. Native REVERIE_UNITY_NPC_CALL_PAUSE absent/0/1,other values NPC_CALL_PAUSE_SELECTION before child/save. New feature quest.harbor-call-pause-v1,new default folder harbor-call-pause/<catalog-pin>/game.sqlite;old9modes/defaults/descriptors/pins/outputs unchanged. New Korean mode label NPC 호출 응답 대기·의뢰 순찰·대화 대기·호출 지원·물자·반복 작업·기억 모드 |
| ownership/wiring | Existing watch.npc POST_TICK gains watch.reply.count read and WatchReplied consume only in new mode. Existing REPLYadapter wraps the same current barrier snapshot;append watch.npc to reply field consumers and existing watch.replied subscribers without replacing encounter.actions or other subscribers. No reply/memory writes. PREwake/cycle/aid/echo remain unchanged;WatchReplied originates in CASCADE before POST_TICK. No engine imports another engine |
| answered-source validation | New private answered patrol dispatcher first validates POST_TICK context,exact wave0,tick integer1..MAX_INT,actionNone,1..2sources. With no WatchReplied,delegate unchanged spoken patrol. With reply:exact selected NPC/string,producer watch.echo,phase CASCADE,wave ECHO_DEPTH,sequence0,producer_rank exact integer0..MAX_INT (existing serialized header bound),all numeric header fields exact ints,due/occurred same tick,one tuple cause,type_key matches payload;before_count exact int0..MAX_INT-1,after exact before+1<=MAX_INT,current REPLYcount exact int==after. Duplicate replies/unknown/mixed QuestSpoken+WatchReplied reject INVALID_FACT before no-op. Existing one-command flow cannot generate speech and answered bell simultaneously |
| hold/resume algorithm | On an odd answered tick,require exactly the reply and return no deltas/facts;no wake/persistent pause created. On an even answered tick,require exactly one NpcActed sibling,delegate existing spoken patrol after removing reply,with private keyword pause=True. Existing wake source/current pose/own-memory/occupied-destination checks still run. Add optional private pause=False to _spoken_patrol and combine spoken or pause at its _patrol call;old path otherwise byte-equivalent. No actual reply means no new hold. New hold applies while accepted patrolling or reported returning;available/already-home remain idle. Next actual wake reads current own memory and old physical destination rules anew |
| presentation | Keep all old message rows and approved dialogue unchanged. Only new mode appends deterministic policy line to existing talk/activity plan: NPC 응답 대기 · 호출에 답한 턴에는 이동을 멈추고, 다음 행동 시점에 순찰 계획을 다시 따릅니다. This states current policy,not an invented past movement or guaranteed next move. Native/Tk mode label distinguishes new selection;save slots reuse current truthful plans and poses,without another format/query/replay |
| edge_policy | False/default preserves old9paths. Invalid bool/parent rejects before resources. Odd/even/zero/negative/bool/MAX_INT/source timing/producer/subject/schema/wave/sequence/count/current-count/duplicate/missing wake/mixed sources all specified. Future/invalid memory and bad pose on even wake remain INVALID_FACT before pause. Actor blocking target still holds next wake;talk pause still wins;rejected actions create neither pause nor memory. No cached pause after retry/save/load/reconnect/compact checkpoint. Units integer seconds/cells/counters;no new RNG/capacity/deadline/tie policy |
| independent examples | New down1/talk2/up3/bell4:reply1,NPC6held,target7free;wait5stays6,wait6moves7. Old ninth mode bell4still6->7. New down1/talk2/up3/wait4NPC7/bell5oddNPC7/wait6NPC6:odd reply does not suppress later wake. Repeated even actual calls each hold current pose,but subsequent non-call wake resumes. F74report20NPC7,up21frees home,bell22holds7,wait2to24returns6. Calls before acceptance keep home;calls after arrived home keep home. Supply/call aid/reward/reply counts follow their original facts |
| algorithm_steps | Baseline145hash/index/source+actual answer/move recorded before code. Add new session/bundle missing-selection baseline failures;implement dispatcher/read registration/flag/pins first,then thread every restore/replay/query/client/native-source selection and policy text. Fresh semantic/unit/actual client/replay/retry/save/worker/framed/Tk/failure tests. Preserve old9whole updates/descriptors/pins/state/protocol/persisted bytes. Prepare dedicated native call-pause flow source without launching. Refresh only G07source/ranges/hash/scope for actual changed WatchNpc body;retain all35public/8source/8golden/4nested obligations and frozen originals |
| performance | Constant <=2incoming events,one existing reply read on an actual answer only,no new pending/provider/IO/state cache. Reuse verified query context once. Measure actual short/long retained saves direct+framed talk/activity/retry/read-only bytes,target2s/existing10sdeadline;retain every sample,no global2s/native/min-spec inference. Old performance samples reused only for unchanged inputs |
| baseline_commands | Actual F76delivery145hash/index/source111/owned down-talk-up-bell runtime PASS. New required flag currently TypeError:unit/integration baseline tests must demonstrate missing explicit behavior before source edits. First behavioral dispatcher tests derive expectations from actual wake/call contract,not new implementation |
| verification_commands | README Ruffboth/scopedformat57/strict253/source parser fallback,pip reused if unchanged;new+affected patrol/call/quest/memory/activity/slots/client/recovery/replay/current G07/exactCI31/doc10. Real worker/framed/withdrawn Tk,no mocked domain outcomes. Old9complete stable outputs/descriptors/pins/core/protocol/actual persisted bodies exact;only attachment_id/working_path excluded as transport identity. Current source-changing full required before LOCAL_ACCEPTED;ENV-001blocks native import/full qualification so defer those gates without repeating unchanged startup failures,skips or checker changes. Independent source/affected/replay/parity work proceeds;no successful-full claim |
| test_responsibilities | NEW unit exact selection prerequisites/manifest/read consumers/source/header/count/odd/even/wake/no-op errors and reply-origin hold with later physical goal. NEW integration down-talk-up-even-call hold/next wake/odd call/no latent state/available+reported/occupied target/repeated actual calls/save previous/restart/compact/replay/exact retry/rollback+uncertain commit/worker/real framed/Tk/CLI/cross-mode pin rejection. Actual reply counter/aid/cycle/reward preserved;new context helpers do not mock outcomes. Existing tests/goldens untouched |
| acceptance | Useful explicit behavior reachable through all ordinary Python paths/new isolated pins/native source,old9exact;new/affected/static/CI/docs/replay/G07/source/runtime/scope150/index preservation complete. LOCAL_ACCEPTED additionally requires successful current imports/full,which ENV-001currently prevents. Until then status IMPLEMENTED_ENV_BLOCKED,not DONE. Fresh native/build remain NOT_RUN AWAY-001. F76acceptance and global2s not silently closed |
| claude_checkpoints | CP01–05not newly triggered:existing watch engine/typed reply/read adapter/phase barriers and save/IPC envelopes reused,no new engine/pipeline/format. Updated source-bound G07scope records real changed body,not independent feedback. CP06held;D2/independent patch rereview/global2s/MIN-SPEC/standalone/release OPEN. No new checkpoint schedule/agent/provider/publication authority |
| stop_conditions/delivery | Stop on semantic divergence/user overlap/missing actual source semantics;record required decisions while doing independent authorized work. English contracts/evidence and synchronized Korean primary2behavior progress;exact input/session/hash results and failures. No unrequested publication. Original unbounded goal ACTIVE,not complete after this task. ENV-001tool resolution and AWAY-001remain explicitly deferred |

## Historical human checkpoint instruction2026-10-27

Director2026-10-27:finish current work,record handoff and upload to Git. Actual automatic
goal PAUSED. This authorizes current branch checkpoint commit/push only and supersedes
this order's earlier no-publication wording for that action. Finish bounded verification,
retain ENV-001/AWAY-001/unrun gates explicitly,then stop. No new feature or protected-main
merge/release/checkpoint waiver is included. Checkpoint memo is one additional authorized
new file:docs/reviews/DEVELOPMENT_CHECKPOINT_2026-10-27.md,total151paths at publication.

## Historical terminal bounded checkpoint evidence2026-10-27

Current82new in535relatedPASS357.30s,exactCI31PASS12.83s;Ruffboth/format57/strict253PASS.
Old9whole stable outputs/descriptors/pins/core/protocol/persisted bodies EXACT,excluding
only existing per-session attachment_id/working_path identity. Current replay/G07168
PASS335.51s(wrapper336.539227s),exec18835/PID30468terminal0;all365frozen inputs/index
preserved. One existing record_property/xunit2warning retained. G07all35/8/8/4retained,
new actual WatchNpc reviewed blob57adbd0191d850835ae507bd84a2e264e31a78e2;encounter blob
3ca0453b58cbe6819c28abc234aafc67b0c034b7unchanged. Existing checkout byte/EOLpreflight
passes without source rewrite. Source audit103other production/127prior nonscope and
old8module AST/3native normalized text preservation PASS. Final9metadata documents
follow terminal;no product code/test/golden change afterward. All jobs terminal.

This is a partial review/backup checkpoint,NOT LOCAL_ACCEPTED:required import/successful
full qualification remains ENV-001unresolved,new-mode long-source latency NOT_RUN,
fresh native/build NOT_RUN AWAY-001. Latest human PAUSED the original goal and requested
current Git upload. Complete final docs/hash/scope151/staging/normal commit+push only;
no further feature/agent/publication/release or automatic continuation.

## Human-authorized resume2026-10-28

Latest director instruction explicitly resumes original automatic development and requests
one same-chat quota/usage follow-up at2026-10-29T03:10Asia/Seoul. Actual goal ACTIVE and
ordinaryUsageAllowed true verified;this supersedes the historical paused execution boundary
above. Previous a973adf checkpoint is pushed;no additional publication is authorized.
This bounded continuation completes only outstanding F77performance evidence before
choosing another order. Primary2internal-calculation verification support;related5/6/7.

- Baseline:clean a973adfbdbc09f95991197fe4346870f0e755ef5,all151delivery hashes EXACT.
  Reuse535affected/31boundary/168G07/static/old9parity;no unchanged reruns.
- MODIFY only this order,its receipt,BACKLOG,SESSION_HANDOFF,GAME_SYSTEM_SUMMARY_KO.
  NEW owned ignored tmp/qtf77/resume-20261028 scripts/logs/results/saves;no production,
  test,config,dependency,security,scene,old evidence or frozen source changes.
- Use actual session/bundle/call_pipe and state_io/replay registered paths. New feature
  pins intentionally reject F74saves;preserve them. Prepare new-mode7/263second saves
  once through actual down/talk then wait5 or16wait16+wait5,save slot01,close. Never
  migrate/relabel old save pins. Copy each owned source for direct/framed measurements.
- Measure talk,activity and slot separately with perf_counter on current host;retain
  every sample and any2starget/10sdeadline misses. Only attachment_id/working_path are
  excluded by established transport identity normalization. Compare whole stable
  updates,actual persisted checkpoint/replay body bytes,core/protocol and pins.
- Read-only activity/slot and exact retry preserve core/protocol/working bytes. On the
  resulting even talk tick,wait1then bell on the following even tick:actual reply must
  hold current pose;retry is exact/unchanged;wait2must reach the next free patrol cell.
  Independently require reply+1,actual source tick7/263,talk tick8/264. Verify retained
  replay and all source tree bytes before/after including both older F74source trees.
- No duplicate source generation or measurement to cherry-pick timings. Owned child
  errors propagate;close only owned resources. Missing semantics/output divergence
  stops this batch with evidence. No source-level timing branch or cache added.
- Acceptance:all4short/long direct/framed samples have exact stable outputs/state and
  source preservation;record numerical results truthfully. Run document10checks and
  final Git/scope/input/index checks after synchronized metadata. F77remains partially
  qualified until required imports/successful full;ENV-001/AWAY-001and all existing
  independent/release/global2s/MIN-SPECholds remain unresolved. No new checkpoint or
  external-public-contract change;CP06still held. No agent/publication/native action.

## Performance continuation terminal2026-10-28

Actual new-mode source7/263prepared once;original F74source trees retained. Successful
short direct/framed talk0.238026/0.217931s,activity0.180624/0.170910s,slot0.064448/
0.059019s. Long talk1.288938/1.298705s,activity1.220742/1.244969s,slot0.092372/
0.090585s. Actual even answered bell10/266holds6;next wake12/268resumes7;retry leaves
reply count1and working bytes unchanged. All9stable updates/pins/core/protocol/actual
persisted checkpoint/replay body bytes exact direct/framed. Only existing per-session
attachment_id/working_path excluded.20successful timings all<2s/<10s;single samples,
no speedup/global2s/MIN-SPEC/native inference. Earlier slow evidence remains historical.

Initial short framed helper called send_seconds without intent;talk/activity/slot/bell
samples and failure retained. Corrected actual signature send_seconds(pipe,'wait','2');
only failed path rerun in separate pipe-repaired folder. Initial direct attach used
update()while registered worker explicitly uses update(reset_log=True). Actual matching
read-only attach captured on a separate source copy,all other fields exact;raw original
outputs/timings retained,no completed measurement rerun. Comparator excludes no new field.
Corrected future long direct call uses the exact worker argument. This is harness repair,
not gameplay change. All production/tests/content/native/index/source bytes preserved.
Runner42246terminal0;tmp/qtf77/resume-20261028/performance-result.json retains evidence.
Imports/successful full ENV-001and native AWAY-001remain unresolved,F77not LOCAL_ACCEPTED.
