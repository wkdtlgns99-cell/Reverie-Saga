# QT-F81 — Recall the patrol plan at the previous committed conversation

Status:IMPLEMENTED_ENV_BLOCKED2026-10-29. Local Codex self-review,not independent acceptance.
Authority:original human-resumed automatic development,actual goal ACTIVE. Primary5
presentation support for existing2/6/7;no new NPC cognition or movement behavior.

| Field | Contract |
|---|---|
| task_id/title | QT-F81;show a retained prior conversation's own next-action context |
| status/executor/review | Current status above;current executor,no agent;self-review explicitly local |
| goal/non_goals | In existing F80ready mode only,recall the actual previous committed conversation-end plan beside the unchanged current next-step row. Activity lists most recent2conversation-end plans. No new flag,goal,engine,supply/aid/reward/state/schema/save/wire/pin/queue/content/cache/provider behavior |
| baseline | HEAD a973adfbdbc09f95991197fe4346870f0e755ef5,branch codex/cycle-call-recall-20261024;35prior dirty paths/index/111production/all258Python hashes in tmp/qtf81/entry.json. All25F80delivery hashes match;all jobs terminal. Preserve baseline/src;refresh actual Git before edits |
| prerequisites | F80bounded792/31/168/static258/old10parity/12actual queries/doc10PASS;ENV001required imports/successful full unresolved,AWAY001native NOT_RUN. Existing local Python3.13.12/ruff0.16.6/source Mypy/Tk,READMEcommands;no install |
| read_files | ENGINEERING_RULES,SESSION_HANDOFF,BACKLOG,MASTERsections1/2/3/8/9,architecture prompt current overrides,WORKSTATION_SETUP,AUTONOMOUS_EXECUTION,SOLtemplate;src/app/npc_activity.py _ActivitySession.last_publication/_ActivityFactory/_verified_activity/cycle_activity_messages/cycle_return_recollection;src/app/npc_patrol_status.py quest_patrol_next_step;contracts/replay/turn;orchestration/replay Runner;F80tests/current evidence |
| allowed_edit_paths | MODIFY C:/Reverie Saga/src/app/npc_activity.py;README.md;clients/unity/README.md;BACKLOG.md;SESSION_HANDOFF.md;GAME_SYSTEM_SUMMARY_KO.md;docs/DEFERRED_USER_DECISIONS.md. NEW C:/Reverie Saga/tests/unit/test_conversation_patrol_plan.py;tests/integration/test_conversation_patrol_plan.py;docs/work_orders/QT-F81_CONVERSATION_PATROL_PLAN.md;docs/reviews/QT-F81_EXECUTION_2026-10-29.md. All relative suffixes resolve under C:/Reverie Saga. Owned ignored tmp/qtf81 |
| forbidden_paths | Every other production/domain/contracts/CORE/engine/codec/store/checkpoint/content/native/scene/old test/golden/G07tool/inventory/governance/config/reference/user file. No agents/publication/commit/push/PR/merge/release/native/editor/CUA/build/dependency/security action |
| public_contract | Existing signatures and all11mode feature identities/pins unchanged. New text only in ready-mode talk(activity's previous conversation,excluding the current one) and activity(last2retained conversations). Every new row begins NPC 지난 대화 계획 or NPC 대화 계획 기록. Existing next-action rows unchanged;slot output unchanged |
| behavior | During the one existing isolated replay,on each actual selected-NPC QuestSpoken publication,read that session's committed snapshot once,sharing it with existing cycle supply capture. Compute quest_patrol_next_step(core,selected layout,error_code=NPC_RECOLLECTION_SOURCE,npc_ready_patrol=True),store immutable tick/text pair in a per-factory list bounded2. Capture only ready mode. Never recompute historical text from current state or call another replay. Publish only after existing Runner verifies whole trace and final core/protocol;conversation id guard remains unchanged |
| semantics | A recalled plan is a conversation-END committed-state projection,not the earlier POSTbarrier source or proof of an executed movement/wait. It includes its own supply/gate/memory/NPC/actor context. Do not claim an unrecorded past action,reason for no event,or history before retained checkpoint. New history is derived/rebuildable,not authoritative persisted memory |
| edge_policy | No retained conversations:activity explicit empty/no inference. First retained current talk:no previous snapshot;explicit absence,even if persistent memory contains old talk. Keep only latest2,chronological/event order from verified replay;talk selects earlier of2only,current existing row remains current. Invalid derived count/order/window rejects caller-specific SaveError NPC_ACTIVITY_SOURCE/NPC_RECOLLECTION_SOURCE;no silent ignore. Wrong owner/mismatch/corrupt replay/current conversation guard retain existing errors. Other10modes return exact existing outputs/call paths. No change to tick/stock units or deterministic simulation |
| examples | Actual talk9recalls2idle while current9nextNeighbor;activity14retains9nextNeighbor and12homeblocked while current14nextNeighbor. First talk and compacted history explicitly lack older conversation-end snapshots. These are committed snapshot goals,not proof of an executed past action |
| exact_timeline | down1/talk2/wait(seconds=6)->8/talk9/wait10/down11/talk12/up13/wait14. At2NPC6stock0gate0idle;9NPC6stock2gate0nextNeighbor;10NPC7gate1stock1;12NPC7actor6homeblocked;14NPC6actor3nextNeighbor. Prior conversation9snapshot must stay nextNeighbor,12snapshot stays blocked despite later14position. Talk rejected/out-of-range must add no history |
| algorithm_steps | Freeze actual entry/old sources/index;author READY order;new baseline2missing-row failures. Add only new-mode bounded conversation snapshot capture/private renderer/two existing message sites. Derive source guards and real normal/empty/checkpoint/reload/previous/worker/pipe/Tk/retry/failure tests. Current static/affected/CI31,old10whole parity,new11only declared row deltas and same state/pins/bodies,actual retained7/264before/current query measurements. Final documents/scope/hashes after terminal |
| wiring | Existing ClientSession durable talk and inspect_activity already call cycle_return_recollection/cycle_activity_messages;worker/Tk/engine bridge/native generic message consumers inherit strings. No startup/native source edit. Save/load/reconnect uses existing replay/branch isolation;slot output remains exact |
| performance | Bounded2derived tick/text pairs per existing replay factory;one canonical small-snapshot projection per actual retained conversation,no extra replay/IO/cache. Reuse byte-identical F80actual7/264sources and existing before measurements;fresh current direct/framed talk/activity/slot once,state/protocol/retry/source/raw body equality. TARGET2s/query,deadline10s;retain all misses,no speedup/global2s/MIN-SPECclaim |
| baseline_commands | Two actual durable integration assertions for new prior-talk row and activity chronology must fail before source edits. Existing F80source/runtime/query evidence remains baseline;no rerun of unchanged ENV001startup/full/native |
| verification_commands | README Ruffdefault/quality,scoped format add2new tests,strict all260Python via approved source Mypy;new unit/integration plus relevant F80/F78/F79/cycle/recollection/client routes;exactCI31. Old10whole stable outputs/descriptors/pins/core/protocol/persisted bodies vs F80baseline. New11actual whole scenario strip only declared prefixes vs F80and preserve every other byte/state/body;source-preserving query measurements. Doc10/link/scope/index. Reuse F80current replay-G07168because every engine/domain/contracts/G07source/inventory/golden/checker unchanged;actual new query replays still run. Required current import/full remains ENV001blocked |
| test_responsibilities | NEW unit verifies renderer empty/latest2/previous/caller-specific malformed-window errors/defaultFalse exact. NEW integration actual independent timeline,first/no retained history,after compact checkpoint with persistent old conversation,no inferred history,rejected action,load/previous/rewind/restart,read-only/retry/state/source,real worker/pipe/withdrawn Tk and malformed replay/logged failure recovery. No mocked domain outcomes,old tests unchanged |
| acceptance | Useful previous actual conversation context visible through player talk/activity and all existing message consumers;new cases/static/affected/CI/old10parity/new11declared row-only parity/measurements/source-scope/doc checks pass. Engine and actual current F80save/pins/queries preserve except explicit new rows. Overall IMPLEMENTED_ENV_BLOCKED,not LOCAL_ACCEPTED/DONE while required import/full unresolved. Native/build NOT_RUN AWAY001;independent/CP06/D2regional/standalone/release/global2s/MIN-SPEC OPEN |
| claude_checkpoints | CP01-05not newly triggered:existing projection/isolated replay/player message route,no new engine/pipeline/format. Self-review not independent patch rereview;retain deferred review and CP06release hold,no agent |
| stop_conditions | User overlap,new unsolved semantic/format/policy authority,unverifiable ownership. Defer required questions with memo and continue independent work. Preserve all prior35dirty paths and old source histories |
| delivery | Sync English order/receipt/BACKLOG/HANDOFF and Korean progress;current hashes/exact commands/results/errors/limits. No commit/push/publication. Original unbounded goal remains ACTIVE,existing03:10wake retained,no duplicate timer |


## Actual implementation and qualification entry

QT-F81 IN_PROGRESS_QUALIFICATION2026-10-29:retained previous conversation-end patrol
plan context,primary5presentation support for existing2/6/7. New rows only in F80ready
mode talk(previous retained conversation)and activity(latest2retained conversations).
One existing isolated verified replay captures canonical snapshot-local next-step text;
no extra replay/IO/cache/flag/state/schema/pin/wire/engine/native change. Missing rows
baseline2FAIL2.62s,initial2PASS2.51s. Expanded35cases first34PASS/1new test-oracleFAIL:
retry correctly returns original COMMITTED,not a new DUPLICATE label. Corrected exact
retry/state/no-extra-context expectation,focused1PASS1.72s. New test typing12diagnostics
fixed with explicit action/event/JSON/caller types;strict260PASS,RuffbothPASS. No product
change for oracle/typing fixes,no old test edited. Source only src/app/npc_activity.py.
Current affected/CI/old10whole parity/new11declared-row-only parity/retained7/264query/
source-scope/document qualification STARTING. Reuse unchanged F80engine/G07168evidence;
all source/test inputs will stay frozen until terminal. No task acceptance yet.
[Receipt](../reviews/QT-F81_EXECUTION_2026-10-29.md).
ENV001imports/successful full and AWAY001native remain unresolved;goal ACTIVE,existing
03:10one-time wake retained,no agents/publication/dependencies/security/native actions.


## Terminal bounded qualification

QT-F81 IMPLEMENTED_ENV_BLOCKED2026-10-29:prior committed conversation-end patrol
plan display,primary5presentation support for existing2/6/7. Only ready mode talk adds
previous retained conversation projection;activity lists latest2conversation-end plans.
One existing verified isolated replay shares the selected snapshot with supply capture,
uses canonical next-step text and stores at most2tick/text pairs. No new goal/flag/state/
schema/pin/wire/cache/IO/replay/engine/native change. Missing-row baseline2FAIL2.62s;
new35included in362affectedPASS319.07s;CI31PASS8.00s;Ruffboth/
format64/strict260PASS. First34PASS/1FAILwas an incorrect new retry-label oracle;exact
COMMITTED/state/no-extra-context fixed,focused1PASS1.72s. New test typing12findings fixed,
no product/old-test/golden/checker workaround. Old10whole outputs/state/raw stored bodies
EXACT;new11whole46updates/core/protocol/source EXACT after removing only declared two
new prefixes. Original F80actual7/264sources reused unchanged,12direct/framed queries/
retry/replay/state/body/source PASS;All12samples below2s/10s. No overall speedup/global2sclaim.
Unchanged F80engine/CORE/contracts/G07sources/goldens/checker retain168PASS/35/8/8/4,
not a new G07run;current app query replays exercised. Only npc_activity.py production
changed;110other production/257oldPython/28prior nonscope/index preserved. ENV001required
current imports/successful full unresolved;AWAY001native/compile/render/build NOT_RUN.
NOT LOCAL_ACCEPTED/DONE;CP06/independent/D2regional/standalone/release/MIN-SPEC/global2s
OPEN. Runner6692terminal1at comparison-tool issue;recovery terminal0with all results/input
hashes verified. Goal ACTIVE,no agents/publication/dependencies/security changes.
[Receipt](../reviews/QT-F81_EXECUTION_2026-10-29.md).

Earlier in-progress section is historical. Final documents follow terminal0with separate
document/scope checks;all implementation inputs stayed frozen. Original goal ACTIVE.
