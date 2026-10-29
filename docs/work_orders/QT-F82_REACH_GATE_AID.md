# QT-F82 — Gate assistance requires the NPC to reach the passage

Status:PYTHON_VERIFIED_NATIVE_NOT_RUN2026-10-29. Current Codex local self-review,not independent acceptance.
Authority:original human-resumed automatic NPC/world development;actual goal ACTIVE.
Primary2internal calculation;related5/6/7. New bounded opt-in physical interaction rule.

| Field | Contract |
|---|---|
| task_id/title | QT-F82;open the passage only from an adjacent NPC work cell |
| status/executor/review | Current status above;current executor,no agents;self-review explicitly local |
| goal/non_goals | Add npc_reach_aid child of npc_ready_patrol. Existing own acceptance,closed gate,prior-barrier stock minimum and actual wake/call proof still required;NPC must also be physically adjacent at the same POSTread barrier. Reuse domain.encounter.adjacent_cells. No new movement goal/path/range constant/action time/production/use/cost/reward/queue/persistent state/schema/component/wire/LLM/content/security/dependency change |
| baseline | HEAD a973adfbdbc09f95991197fe4346870f0e755ef5,branch codex/cycle-call-recall-20261024. All11F81delivery hashes match;39prior dirty/111production/all260Python/index/native snapshots in tmp/qtf82/entry.json/baseline/src. Actual Git before edits;all jobs terminal |
| prerequisites | F80ready behavior and F81prior-conversation projection bounded-qualified;current362/CI31/static260/old10parity/new11row-only/12actual queries/doc10PASS. ENV001required import/full unresolved,AWAY001native NOT_RUN. Existing local Python3.13.12/ruff0.16.6/source Mypy/Tk reused,no install. Current user03:10check and one actual reset04:49:45recovery are distinct confirmed one-time wakes |
| read_files | ENGINEERING_RULES/HANDOFF/BACKLOG/AUTONOMOUS_EXECUTION/WORKSTATION_SETUP;MASTER1/2/3/8/9;architecture current overrides/CORE ownership/phase barriers;SOLtemplate/GAME_STRUCTURE_GUIDE. EncounterActions __post_init__/manifest/_assist_gate/_aid_source;domain.encounter.adjacent_cells;app.npc_gate_aid.with_gate_aid/npc_cycle/npc_patrol;WatchNpc ready priority;all existing client/query/native flag paths and support projection;current F80G07scope/refresh/tests |
| allowed_edit_paths | MODIFY C:/Reverie Saga/src/engines/encounter.py;src/app/npc_gate_aid.py;src/app/npc_cycle.py;src/app/npc_patrol.py;src/app/client_session.py;src/app/client_worker.py;src/app/client.py;src/app/engine_bridge.py;src/app/npc_activity.py;src/app/npc_support_status.py;clients/unity/Assets/Reverie/Scripts/BrainConnection.cs;PlayRoom.cs;LiveVerification.cs;tools/replay_body_inventory.json;README.md;clients/unity/README.md;BACKLOG.md;SESSION_HANDOFF.md;GAME_SYSTEM_SUMMARY_KO.md;docs/DEFERRED_USER_DECISIONS.md. NEW C:/Reverie Saga/tests/unit/test_reach_gate_aid.py;tests/integration/test_reach_gate_aid.py;docs/work_orders/QT-F82_REACH_GATE_AID.md;docs/work_orders/QT-F82_REPLAY_SCOPE.json;docs/reviews/QT-F82_EXECUTION_2026-10-29.md. Native short names resolve in the same Scripts directory;all suffixes under actual checkout. Owned ignored tmp/qtf82 |
| forbidden_paths | All other production/domain/contracts/CORE/store/codec/checkpoint/old tests/goldens/checker/governance/config/scene/assets/content/reference/user paths. No agents/publication/commit/push/PR/merge/release/dependency/security/native/editor/CUA/compile/render/build/capture action |
| public_contract | Exact npc_reach_aid:bool=False after npc_ready_patrol throughout existing Python bootstrap/bundle/session/worker/Tk/bridge/activity restore/query factories. True requires immediate ready parent/all ancestors;bad bool/parent NPC_REACH_AID_CONTENT before save/thread,old errors retain precedence. EncounterActions npc_reach_aid:bool=False requires npc_call_aid at its narrower engine boundary;with_gate_aid same. with_patrol requires ready parent. Both CLIs --npc-reach-aid. Native REVERIE_UNITY_NPC_REACH_AID absent/0/1;bad string NPC_REACH_AID_SELECTION,missing parent CONTENT before child/save |
| identity | New quest.harbor-reach-aid-v1. Existing11identities/rules/pins/outputs exact when false. Native isolated tmp/unity-play/harbor-reach-aid/<catalog-pin>/game.sqlite;no repin old saves. New mode label NPC 인접 통행 지원·지원 준비 우선·호출 응답 대기·의뢰 순찰·대화 대기·호출 지원·물자·반복 작업·기억 모드 |
| ownership/phase | Existing encounter.actions remains sole gate writer at POST_TICK. Add new-only watch.npc.cell/space_id reads and spec consumers;no new subscriber/writer. Read prior POSTbarrier pose,not watch.npc movement delta in the same phase. Gate assistance may occur before/with movement away only when its prior pose was adjacent. Own movement already uses F80ready target independently;no new goal or execution order |
| algorithm | Validate flag,parent,existing source causality/memory/timing and gate binding in old precedence. Existing unavailable/reported/open-gate early no-op remains. Read existing supply once;new mode requires exact Supply/state_at(tick-1),otherwise INVALID_FACT reach aid cycle source. Stock<existing SUPPORT_STOCK_MIN returns no-op. New-only selected WATCH_NPC cell/space read validates exact int in existing patrol_cells(layout,True)and selected space,otherwise INVALID_FACT reach aid NPC source. Canonical adjacent_cells(npc.cell,gate.cell)false returns no deltas/facts;true uses unchanged GateDelta/GateAssisted/current causal source. Missing typed sources preserve structural UnknownEntity/UnknownComponent;GateAdapter/WatchAdapter earlier validation errors retain actual boundary |
| constants/units | Cells existing3x3IDs,canonical fixed-point Manhattan adjacency1000from domain.encounter. Diagonal6->4false,7->4true. No new range formula/constant,stock integer existing0..STOCK_CAP3/min2,logical ticks seconds. Existing tie consume-then-prepare/cap/wake/range/admission/priority preserved |
| independent_examples | down1/talk2/up3/wait6to9:accepted NPC6/gate0/stock2. Old ready wake10opens gate while NPC6is not adjacent at read barrier,and moves7. New wake10must remain gate0/NPC7;12priorstock1returns6/gate0,14priorstock2moves7/gate0,16priorstock2/NPC7opens gate and moves6. At16same-phase prepare to3is not its source. A bell15after actual arrival14opens gate while adjacent7with prior2,without another wake;NPC holds actual answered turn. Bell13at far6with adequate stock fails to open. Bell11at adjacent7with prior1fails. Same-phase arrival10cannot qualify early |
| presentation | Existing supply_support_plan/support_slot_messages add exact optional npc_reach_aid=False,requires call parent;new-only own WatchNpc pose validation. Existing memory/reported/open/low-stock wording precedence retained. Adequate stock but far shows need to reach adjacent work cell;adequate+adjacent allows requesting nearby passage help. Add one new-mode policy row using canonical adjacency,not a promised time or historical aid. Current/saved snapshots use their own pose,stock,gate,memory;F81history still uses its own unchanged ready movement projection |
| wiring | cycle_bundle passes flag to with_gate_aid then with_patrol and new rules/identity;bootstrap forwards. Every durable/restore/checkpoint/replay/session/worker/Tk/CLI/bridge/activity factory threads flag. Support talk/activity/current-saved queries receive it. Native startup/path/mode/reconnect/errors/dedicated ReachAidFlow dispatch source before parent ready flow. Generic committed message/position consumers unchanged;no scene/wire edit |
| edge_policy | False/default all11exact. Missing parent/nonbool rejects before resource IO. Physical far/diagonal/same-cell/out-of-patrol/wrong-space/typed supplyclock/missing sources use actual documented boundary. Existing no own acceptance/report/gateopen/lowstock/odd-even/call/rejected command/no latent pause/player collision/SQL rollback/uncertain commit/retry/load/reconnect rules unchanged. Validate new source only when eligible path reads it;do not invent errors for sources not read on an existing early no-op |
| algorithm_steps | Freeze39prior/index/native/source. Capture actual old nonadjacent gate opening and baseline new flag2FAIL. StageAimplement engine new read/range/typed-cycle check/bundle consumers/identity/bootstrap,headless independent timeline and malformed source boundaries. StageBfull player/query/native-source wiring and truthful current/saved range plans. StageCnew+affected/static/old11parity/actual new12short-long/replay-G07/CI/docs/source qualification. Do not call StageAfeature complete |
| performance | New eligible evaluation bounded2NPCread fields and existing Supply read/constant canonical geometry;no global scan/cache/event. New projection scans existing selected components only. Actual retained short/long new12mode direct/framed talk/activity/slot once with state/retry/replay/source/raw body guards,TARGET2s/deadline10s. Retain misses,no speedup/global2s/MIN-SPECclaim |
| baseline_commands | Actual old F80ready session down1/talk2/up3/wait6to9(snapshot NPC6stock2gate0),wait10opens despite canonical nonadjacent6->4. New cycle_bundle/bootstrap npc_reach_aid currently TypeError;two independent new integration baseline failures before edits. Preserve raw logs/old source |
| verification_commands | README Ruffboth/scoped format66/strict all262via approved source fallback;new canonical registered headless/durable/replay/talk/current-selected/worker/real pipe/withdrawn Tk/CLI/restore/checkpoint/rollback/uncertain source guards. Old11whole outputs/descriptors/pins/core/protocol/raw bodies exact;new12actual full direct/framed source vector and native-source oracle. Current source-bound replay/G07all35methods8sources8goldens4nested raw hashes/ranges/private index;no checker/golden changes. ExactCI31/docs10/links/source-scope/index. Required current imports/successful full ENV001unresolved,no repeat unchanged blocked startup/full/native |
| test_responsibilities | NEW unit engine flag/manifest/source/adjacency/phase/tie/owner/type/missing actual adapter boundaries;do not duplicate canonical geometry tests as a substitute for registered behavior. NEW integration numeric old/new comparison/same-phase arrival/move-away/prior stock/bell11/13/15/close/open/report/reward/return/save/load/previous/rewind/reconnect/compact/older pins/retry/rollback/uncertain/worker/pipe/Tk/query source preservation. No mocked domain outcomes or test-specific product branches |
| acceptance | New actual physical condition reachable through all runtime/replay/client/query/native-source selectors,truthful selected-pose plans,normal/boundary/static/old11/new12/source/runtime/G07/CI/docs complete. Overall IMPLEMENTED_ENV_BLOCKED until required import/successful full externally resolved;native NOT_RUN AWAY001,not LOCAL_ACCEPTED/DONE. CP06/independent/D2regional/standalone/release/MIN-SPEC/global2s remain OPEN |
| claude_checkpoints | CP01-05not newly triggered:existing engine selected mode/read adapter/field spec/phase/event/delta/replay/query/client contracts reused,no new engine/format/pipeline. Self-review not independent;retain patch-review/CP06holds,no agents |
| stop_conditions | User overlap/missing real semantics/new authority. Defer required questions and memo while independent work remains. On quota use actual reported reset1793216985and confirmed one-time reverie-saga-2,never bypass weekly/spend limits or resume manual pause |
| delivery | Sync English order/receipt/BACKLOG/HANDOFF and Korean progress after real stage evidence;preserve old39dirty and saved sources. No publication/commit/push. Goal remains ACTIVE after bounded progress. Human03:10check and distinct actual quota04:49:45wake confirmed,each once/delete after handling,no periodic polling |


## StageAcore evidence,not feature completion

QT-F82 IN_PROGRESS_STAGE_A_CORE2026-10-29:physical gate assistance,primary2internal
calculation;related5/6/7. New exact npc_reach_aid child of ready mode is implemented only
in engine/bundle/bootstrap stage. Prior POSTNPCpose must be adjacent through canonical
adjacent_cells,with exact prior Supply/state_at(tick-1). No new state/goal/schema/wire/
production/aid cost/reward/queue. Existing actual old9NPC6far/stock2then10gateopens recorded;
new flag baseline2FAIL0.48s. Current core13PASS0.89s(including independent16turn numeric
vector and exact flag/manifest/consumer guards):10NPC7gate0,12NPC6gate0,14NPC7gate0,
16NPC6gate1stock3. Same-phase arrival cannot qualify;prior adjacent pose can help while
moving away. Ruffboth/strict262PASS,current source inventory/ranges/hash/registry reviewed,
all35/8/8/4retained;NOT actual current G07/replay/full acceptance. Exactly4production
paths changed. Remaining StageAnegative source/odd-call guards,then complete StageB
client/durable/query/native-source selection and StageCqualification. This is not a fully
exposed player mode or task completion;do not select another feature.
[Receipt](../reviews/QT-F82_EXECUTION_2026-10-29.md).
ENV001required imports/successful full unresolved;AWAY001native NOT_RUN/CU_STOPPED;
CP06/independent/release holds retained,goal ACTIVE,no agents/publication/dependencies/
security. Both one-time wakes confirmed:human03:10reverie-saga and actual five-hour reset
04:49:45KST(Unix1793216985)reverie-saga-2;distinct purposes,no periodic polling.


F82additional StageAodd-call2026-10-29:actual bell11at adjacent7but stock1does not open;
bell13at far6with stock2does not open;bell15at adjacent7with stock2opens. Each actual
call replies exactly once. Three new cases PASS;strict262and focused RuffPASS. No
production change. Source malformed-read guards and fullStageB/StageCstill pending.


Publication2026-10-29:human now authorizes this checkpoint through protected main.
New9registered-source/pose guard cases supplement existing16selected cases;no product
change. Stale fixture12equals14Supplyand is valid;use8for a truly different prior state.
Full player/query/native-source wiring remains unfinished. Actual latest CI/PR/merge
evidence belongs to [checkpoint](../reviews/MAIN_INTEGRATION_2026-10-29.md),not a new
feature acceptance or release/native/independent-review waiver.


Current StageB/C continuation supersedes earlier unfinished-stage statements;see the
[receipt](../reviews/QT-F82_EXECUTION_2026-10-29.md).
Both import contracts now run on this PC;historical ENV001is not inferred for this host.
Native/remote publication/independent/release and measured2sTARGET limits remain explicit.
