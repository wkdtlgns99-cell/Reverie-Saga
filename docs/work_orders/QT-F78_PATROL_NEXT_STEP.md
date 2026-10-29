# QT-F78 — Share the actual patrol target and expose the next movement condition

Status:IMPLEMENTED_ENV_BLOCKED2026-10-29. Current Codex implementation/self-review;not independent acceptance.
Authority:latest human explicitly resumes original automatic development;goal ACTIVE.
Primary5presentation support for existing2NPC calculation;related6/7. No new NPC capability.

| Field | Contract |
|---|---|
| goal/non_goals | Show why the current or selected saved NPC would hold or which existing work cell it would next attempt in the existing explicit call-pause mode. Extract the existing quest target formula into one pure domain function shared by engine and projection. No new behavior/flag/goal/component/DTO/schema/pins/wire/queue/cached state/supply/reward/range/provider/IO |
| baseline | HEADa973adfbdbc09f95991197fe4346870f0e755ef5,branch codex/cycle-call-recall-20261024;only5verified F77resume metadata docs dirty,staging empty. All prior checkpoint/F77resume hashes inspected;entry records production/prior/index/source saves,baseline/src copied. F77performance qualified;ENV-001required import/full gates remain blocked. Prior goal turn PROGRESS |
| prerequisites/read_files | ENGINEERING_RULES/handoff/backlog/AUTONOMOUS_EXECUTION/setup/README/MASTER8memory+1NPCgoals/numbered guide/Soltemplate/v2.6layers;F74/75/77orders+receipts;actual WatchNpc._patrol,domain patrol_cells,NpcQuestMemoryRecord.known_phase,quest_patrol_plan/slot_messages,cycle_return_recollection/activity_messages,ClientSession.inspect_slot/current snapshots,registered worker/bridge/withdrawn Tk,G07inventory/assessor and existing frozen golden policies |
| MODIFY absolute paths | C:/Reverie Saga/src/domain/npc_patrol.py;C:/Reverie Saga/src/engines/watch.py;C:/Reverie Saga/src/app/npc_patrol_status.py;C:/Reverie Saga/src/app/npc_activity.py;C:/Reverie Saga/src/app/client_session.py;C:/Reverie Saga/tools/replay_body_inventory.json;C:/Reverie Saga/BACKLOG.md;C:/Reverie Saga/SESSION_HANDOFF.md;C:/Reverie Saga/GAME_SYSTEM_SUMMARY_KO.md |
| NEW absolute paths | C:/Reverie Saga/tests/unit/test_patrol_next_step.py;C:/Reverie Saga/tests/integration/test_patrol_next_step.py;C:/Reverie Saga/docs/work_orders/QT-F78_PATROL_NEXT_STEP.md;C:/Reverie Saga/docs/work_orders/QT-F78_REPLAY_SCOPE.json;C:/Reverie Saga/docs/reviews/QT-F78_EXECUTION_2026-10-28.md;owned ignored tmp/qtf78 |
| forbidden_paths | Other production/contracts/CORE/codecs/checkpoint policies/old tests/goldens/G07checker/governance/config/native/scene/assets/catalogs/old orders-receipts/user/reference sources. No security/dependencies/agents/publication/commit/push/PR/merge/release/native UI/editor/build |
| public_contract | New pure domain quest_patrol_target(layout:Scenario,current:int,known_phase:Literal[available,accepted,reported])->int;use existing patrol_cells(layout,True). Invalid exact type/phase/current/unheard-away rejects ValueError NPC_QUEST_PATROL_TARGET. Existing engine prechecks retain INVALID_FACT precedence/details for unheard-away/future/bad references;only substitute equivalent target selection after them. New app quest_patrol_next_step(core,layout,*,error_code)->tuple[str,...] and quest_patrol_step_slot_messages(saved,current,layout)->tuple[str,...];derive from verified snapshot,not new persisted data |
| behavior | Target home before own heard acceptance;accepted alternates home/neighbor;reported targets home. Existing engine pause/occupied target logic unchanged. Projection validates selected memory/NPC via existing plan,one selected actor position same space/exact int0..8,canonical target. If target==current,show waiting at work point. Otherwise label original/neighbor target;actor==target states currently occupied,else next actual wake attempts target. Label current conditions,never guarantee next move or claim past waiting. Existing response policy remains separate. No new replay/read/IO beyond existing context |
| edge_policy | Empty selected memory means available/home only;zero tick valid if source valid;future memory/missing/duplicate/wrong-owner NPC or actor/wrong space/bool/negative/out-of-grid/current outside patrol/unknown phase reject exact caller SaveError code before output. Saved/current independently selected,including equal/future/rewound ticks;one side never borrows other actor occupancy. Subject already at target remains idle even if actor shares cell. Actual talk/call hold creates no future pause;later non-talk/call wake recomputes. No RNG/capacity/deadline/tie changes |
| examples | Home6/neighbor7,own available6->6;accepted6->7,accepted7->6;reported7->6,reported6->6. Available7 invalid. Actual down1/talk2/up3/wait4 moves7,down5/down6 actor6 blocks home:activity shows occupied original point. Save at6,up7frees home:current attempts original,selected save remains blocked. Wait8returns6,its next target7free. Actual bell response at even tick holds current6but next target remains7,not a saved pause. Complete report/blocked home and arrived-home waits use own report only |
| algorithm_steps | Freeze current source/index/evidence before edits;new actual baseline tests fail missing reason/paired rows. Implement canonical pure target,keep engine validation and old nonquest path,make projection share target. Add next-step row only when npc_call_pause in existing talk/activity and3labeled current/saved rows only under self._npc_call_pause before physical-position tail. Existing9modes display exact;new tenth only declared messages differ. Add unit/source/error and real gameplay/save/restart/retry/worker/framed/Tk tests;refresh G07current source/ranges while retaining35/8/8/4obligations;measure actual retained-source queries once before/current direct/framed |
| wiring | Actual WatchNpc._patrol uses canonical target;app plan uses same target;ClientSession talk postcommit and read-only activity via cycle_return_recollection/cycle_activity_messages;save manager via existing inspect_slot;worker/bridge/Tk/Unity existing messages consumers require no new DTO/native source. New text restricted to already selected call-pause mode,old9full stable outputs/pins/core/protocol/persisted bodies exact |
| performance | Constant two work cells/selected snapshot records;no extra verified replay/plan context/source read. Target talk/activity2s/existing10sdeadline measured actual F77new-mode7/263source copies direct/framed before/current,source hashes preserved;one sample/operation/all results retained. New layer call cost assessed by real timings;no global2s/MIN-SPEC/native/speedup claim |
| baseline_commands | New actual occupied-home activity and paired current/saved preview expectations fail under existing implementation before source edits;all original saved source trees untouched. Previous F77old9parity/current535/31/168/static unchanged-input evidence retained until actual source delta requires affected rerun |
| verification_commands | README Ruffboth/scopedformat/strict types using established source fallback;new and affected patrol/memory/quest/call/activity/slots/client/recovery tests,exactCI31,doc10,old9whole outputs/pins/core/protocol/persisted bodies exact,new-mode existing runtime stable outputs exact after removing only precisely declared new messages,actual real pipe/worker/withdrawn Tk. Current replay/G07required;source raw EOL/actual inventory private index frozen. No repeated unchanged grimp startup/full;required successful full/import stays ENV-001unresolved |
| test_responsibilities | NEW unit independent5valid target examples,exact-type/invalid targets,projection blocked/free/idle,missing/duplicate/wrong-owner/space/bool/future on either saved/current side. NEW integration actual acceptance/blocked home/free next wake/call-hold no latent pause/report/return,read-only activity+slot/previous/rewind/restart/exact retry/core/protocol/save bytes,real worker/framed/withdrawn Tk with new text;old tests unchanged |
| acceptance | Useful truthful current/saved next action on all existing Python paths;canonical engine target mathematically equivalent for all valid old states,old9exact,new tenth only declared rows;new+affected/static/CI/docs/replay/G07/performance/source/index/scope qualification recorded. Required successful import/full remains ENV-001blocked so overall IMPLEMENTED_ENV_BLOCKED,not LOCAL_ACCEPTED/DONE;native fresh/build NOT_RUN AWAY-001 |
| claude_checkpoints | CP01–05not newly triggered:existing engine/domain/typed events/read adapters/phase barriers/checkpoint/save/IPC boundaries preserved. Pure target extraction+derived message projection,no new simulation subsystem. Source-bound G07refresh is self-review,not independent feedback. CP06/D2regional cognition/independent rereview/global2s/MIN-SPEC/standalone/release OPEN |
| stop_conditions/delivery | Stop on semantic divergence/new authority/user overlap;record concrete deferred questions while independent work continues. Sync English order/receipt+backlog/handoff/Korean progress after actual results. Preserve F77resume changes and old evidence. Goal ACTIVE beyond this bounded task;no new publication/agents/native/security/dependencies. Same-chat03:10follow-up already registered,do not duplicate |

## Terminal current qualification2026-10-29

Baseline2FAIL2.05s;current110new in645PASS232.32s(25files),CI31PASS7.79s,
Ruffboth/format59/strict255PASS. Existing old9whole153updates/schema+rules bytes/pins/
core/protocol/persisted bodies EXACT. New tenth-mode actual7/263source direct/framed
queries preserve all old fields and state/persisted bodies except explicitly reviewed
1talk/1activity/3slot message rows. No new excluded fields. All20current measured samples
<2s/<10s;long talk1.313450/1.313432s,activity1.223115/1.209963s. Reused unchanged F77
before samples,no duplicate gameplay or source generation. No overall speedup/global2sclaim.

Current replay/G07168PASS;all370frozen inputs/real index preserved through terminal.
Runner81444/G07PID35364terminal0,private reviewed Watch04f910a5ca49ecc3ccd30d9d31ab2ae0cb0d8a0d;
all35public/8source/8goldens/4nested obligations retained. New pure domain function is
covered by independent target tests and actual engine replay;it adds no public engine
method to the existing G07registry. Old domain/watch/client/activity ASTs exact after
only declared helper/extraction/calls removed;106other production and prior nonscope/
old+F77source saves unchanged. Initial17new test E402and2tuple-variable type findings
repaired without suppression;all old tests untouched. Current source review is local,
not independent feedback. Only final5metadata documents change after terminal;no code,
source-bound inventory/scope/golden change. Doc10/final hash-scope results retained in
tmp/qtf78/delivery.json. Required current imports/successful full ENV-001remain unresolved;
native/build NOT_RUN AWAY-001. This scope is implemented/partially qualified,not accepted.
Original goal ACTIVE with same-chat03:10follow-up;no new publication or agents.

## Final continuation mechanism observation2026-10-29

F78implementation/bounded qualification is preserved as above. At final delivery,
get_goal twice reports BLOCKED;at entry it reported ACTIVE. Reason is not exposed.
No update_goal call was made by this executor during this batch. Ordinary usage allowed
(primary11percent/secondary4percent). Available tools provide no resume/active status
mutation;human app Resume action is required for automatic next turns. This does not
revoke the latest human coding authorization or close the full objective. Do not claim
ACTIVE or create a substitute goal/daemon. Existing human-requested03:10one-time follow-up
remains registered;its actual goal/usage/latest-instruction preflight still applies.
No live jobs remain. Record this required app action while preserving all code/evidence.
