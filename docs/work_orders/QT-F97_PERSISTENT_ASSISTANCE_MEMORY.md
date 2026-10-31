# QT-F97 — Persist an NPC's own passage assistance

READY2026-11-01;current assistant executor,self-review,not independent review.
Primary2internal factual memory +6persistence;related3definitions,5inspection,7village flow.

## Authority and baseline

The director answered the specific F95contract-implementation approval question with
"너 알아서 좋을대로"(delegate the choice to the executor). The executor adopts
[F95](../proposals/QT-F95_PERSISTENT_ASSISTANCE_MEMORY.md) for this bounded optional mode.
This is scoped implementation authority,not blanket approval for other contracts or
implementation/review/release acceptance. Existing holds remain.

Clean main10306960ad36039c0f6e227138b2238c18f4323d equals freshly fetched origin/main.
F96PR29merged;both published-head full3713/boundary31PASS,local main0/0clean. Python3.13.12
AMD64/Tk8.6reused. Native goal remains usageLimited;this direct user task proceeds without
claiming its cross-turn scheduler is active. No agents or desktop interaction.

| Field | Contract |
|---|---|
| goal/non_goals | New opt-in assistance memory survives retained-history compaction/save/load/restart/recovery:exact cumulative count and latest4own causal anchors. Existing assistance behavior/stock/pose/cost/reward unchanged. No regional/general memory framework,LLM,old-save migration,central wire/SQL format,independent/native/release waiver |
| prerequisites/read_files | ENGINEERING_RULES,HANDOFF,BACKLOG,Korean companion,MASTER1/2/3/8,architecture ownership/barriers/checkpoints,AUTONOMOUS_EXECUTION,WORKSTATION_SETUP,READMEverification,Sol template,numbered guide;F95proposal/F82order/F96publication result;actual EncounterActions aid/source/manifest,cycle bundle/bootstrap/policies/codecs/reducers,quest binding,ClientSession/worker/Tk/bridge/activity factories and native selectors/flow |
| public_contract | New npc_assistance_memory:bool=False appended to cycle_bundle/bootstrap_cycle,ClientSession/Worker/PlayWindow,EngineBridge/serve and verified activity/recollection factory paths. Exact bool;True requires immediate npc_reach_aid parent before resource IO;NPC_ASSISTANCE_MEMORY_CONTENT. Both Python CLIs --npc-assistance-memory. Native prepared selector REVERIE_UNITY_NPC_ASSISTANCE_MEMORY absent/0/1,invalid ->NPC_ASSISTANCE_MEMORY_SELECTION,parent error CONTENT;optional constructor argument appended |
| identity/compatibility | New quest.harbor-assistance-memory-v1 child composed after reach/patrol. Distinct schema/rules pins,actual compiled schedule fingerprint. False keeps all13old modes/pins/bytes/outcomes and old optional callback invocation shapes. Never repin/insert/migrate old saves. Old/child mismatch unsupported and source-preserving. Existing ClientView/WireEnvelope/SQLite schema unchanged |
| data | Frozen AssistanceEntry(tick:int,target_id:EntityId,source_kind:Literal[wake,answered_call],cause_event_id:str);AssistanceMemory(total_assists:int,entries:tuple[AssistanceEntry,...]);AssistanceMemoryRecord(entity_id,state),TypeKey(quest.assistance-memory,1). Family quest.assistance-memory/memory,CORE/A,owner encounter.actions,unit own_assistance_records,scale1,cap4. Delta(entity_id,before:AssistanceMemory,after:AssistanceMemory),quest.assistance-memory-delta/1;Patch(state),quest.assistance-memory-patch/1 |
| scalar/shape/error | Exact ints never bool,tick1..MAX_INT,count0..MAX_INT;exact immutable DTO/tuple/string types. Selected NPC owner and selected gate target,namespaced IDs. len(entries)=min(count,4),strictly increasing ticks,unique causes. Fresh0empty. INPUT/OWNER/ENTRIES/ORDER/SOURCE prefixed NPC_ASSISTANCE_MEMORY ValueErrors;codec shape uses existing exact-fields/type errors. Invalid source engine ->CandidateError INVALID_FACT;invalid reducer ->INVALID_DELTA. External malformed save uses existing SAVE_CORRUPT/UNSUPPORTED_RULESET boundary |
| codec | Component fields:{memory:{total_assists,entries:[{tick,target_id,source_kind,cause_event_id}]}}. Delta fields:{entity_id,before:<state>,after:<state>};patch:{state:<state>}. Reject extra/missing/duplicate fields,coercion,wrong type/range/cap/order/owner/reference/source. No separate persistent memory-ID/hash algorithm |
| causal validation | e1- plus64lowercase hex stores actual selected incoming cause,not GateAssisted ID. Wake canonical source:world,tick,PRE_TICK,0,watch.npc,0 and tick divisible by existing WAKE_PERIOD. Answer source:world,tick,CASCADE,existing ECHO_DEPTH,watch.echo,0. Reuse canonical pack/hash recipe;producer_rank is not identity input. At checkpoint verify with actual world,core tick and selected NPC/gate/own quest acceptance;anchors after acceptance and no later than completion report,allow same report tick because prior POSTbarrier applies |
| count feasibility | At most1assist/tick implies retained entry i cannot precede ordinal count-len(entries)+i+1. Checkpoint also bounds count/time after own accepted tick. These are necessary bounds,not invented proof of evicted actions. Persisted component remains authoritative;gate state/retained event count never supplies missing memories |
| writer/ordering | Existing successful EncounterActions._assist_gate appends GateDelta+memory delta+unchanged GateAssisted in one EngineResult at POST_TICK/wave0. Read old memory only after old eligibility checks succeed. Existing _aid_source selects validated answered reply over routine wake when both arrive. Same action and COMMIT own gate/memory/protocol;no new engine/subscriber/phase/wave/event/pending queue/sidecar/world metadata API |
| transition/reducer | Stage and patch require exactly one append:count+1,append new strictly later entry,trim oldest to4. Generic net delta may summarize positive sequential appends;preserve any retained overlap and chronology. Compose validates a contiguous chain and reports first-before/last-after. No empty/identity/duplicate/tied/discontinuous transition. Net validator requires exact staged final state;observed read adapter exposes only state under the registered family |
| checkpoint | New QuestBound policy wraps the actual selected reach/patrol policy. Strip only the exactly selected assistance component for existing policy validation,then validate its immutable shape,owner/target,count/time/acceptance/report and canonical causes. Preserve existing policy/error precedence;old policies never silently accept a new component |
| presentation | New mode only:talk/activity/current-vs-selected slot messages show labelled persisted own count/latest4anchors,chronological oldest-to-newest,source label routine action/answered call. Keep existing retained3assistance history separate and unchanged. UI prefix NPC 지속 도움 기억,detail NPC 도움 기억;saved/current prefixes distinguish snapshot ownership. No event/schema/hash/implementation jargon in player flow |
| query/error/lifecycle | Reuse existing verified replay/current checkpoint;thread new flag through restored factory. Persistent display scans at most4entries,no extra IO/replay/cache. Talk failures retain existing truthful post-COMMIT logging/error semantics;activity/slot failures log and preserve owner/source. Existing worker/Tk pending/input/poll/cancel/close remain operational. Exact retry never adds memory or duplicate talk context |
| native/source | Prepare strict leaf selector/parent/path/forwarding/reconnect and dedicated source flow under isolated harbor-assistance-memory/catalog-pin working path. Actual Python framed responses supply its oracle. C#compile/editor/render/capture/build NOT_RUN under AWAY/ComputerUse STOPPED;source preparation is not native acceptance |
| examples | down1/talk2/up3/wait13->aid16,count1,wake cause. Then down17/close18/wait2->20;three close+wait3cycles->24/28/32:count5,last ticks20/24/28/32. Compact at16or32 retains those component values without GateAssisted bodies. Bell16with routine source records one answered_call cause. Manual open/already open/no own acceptance/low prior stock/far prior pose/same-phase arrival/no aid after committed report/rejected or aborted actions add nothing |
| wiring | New domain/contracts/orchestration/app modules register adapter/spec/codecs/reducer/patch/policy through selected cycle bundle. Existing encounter writer is replaced only for child mode. Bootstrap fresh record,session/worker/Tk/both CLIs/framed/replay restore and current/saved queries connect it. Headless generic machinery unchanged;registered new bundle is exercised |
| algorithm_steps | Freeze current source/index;baseline intended new flag failure;implement typed state/registration/atomic writer;qualify headless/durable/rollback/retry/checkpoint source vectors;wire full Python clients/queries and prepared native source;run old13mode parity,new direct/framed full source/retry/restore/performance,static/replay/G07/full/doc qualification;publish one coherent task and sync main |
| performance | New bookkeeping O(4),no retained/global scan/cache. Measure real short/dense current/saved direct/framed queries with source/state/protocol/retry equality,2sTARGET/10sdeadline. Preserve F96dense2642sOPEN honestly;no global latency/MIN-SPEC/speedup claim without same-input measurements |
| baseline_commands | New integration flag-selection case must fail on unmodified source. Owned tmp/qtf97 entry/probes use actual Python/SQLite;old baseline source copied before edits. GIT_CONFIG exact process-local path trust from workstation setup for nested Git checks;canonical pytest capture=sys and pinned tools |
| verification_commands | README Ruffboth/scopedformat+changed Python,strict mypy,imports3+1,pip;new+affected+exactCI31/docs10;shared engine full pytest with frozen source. Actual source-bound replay/G07 preserves35methods/8sources/8goldens/4nested obligations and updates only factual encounter hash/ranges. No checker/golden weakening. Qualify any newly prepared native assertions only as source/actual-framed evidence |
| test_responsibilities | NEW unit domain/codec/adapter/read lifetime/transition/reducer/checkpoint/cause/count vectors;NEW integration full lifecycle16/32/compact/restart/old-save mismatch/call+routine/report/source errors/rollback/uncertain COMMIT/retry;NEW client integration direct/worker/Tk/framed/bothCLI/save/previous/error/recovery/close;NEW replay child bundle/exact old13mode parity. Preserve old tests/goldens/checkers |
| acceptance | Reachable new Python mode persists count/latest4actual own causes across all stated durability paths with exact type/error/atomicity/caller semantics;all required checks pass;old13outcomes/pins/SQL exact;real measurements/remaining misses truthful;root trio and F95decision/current F96publication reconciled;normal PR/bothCI/merge/localmain equality/clean. Native/independent/device/release remain separately held |
| claude_checkpoints | CP01-05not newly triggered:new owned component through existing extension points and same existing writer,not a new subsystem/engine/central storage format/pipeline. Closed scopes remain closed;self-review/full/G07 do not establish independent review of new feature. CP06/patch review/native/device/release holds retained;no new/reopened/waived checkpoint or agent/provider call |
| stop_conditions/delivery | Preserve user overlap;resolve genuine missing semantics from approved proposal and actual sources. This director-delegated bounded contract permits implementation and standing2026-10-30scoped commit/push/PR/CI/ordinary merge/main sync. It does not resume stopped desktop interaction or authorize unrelated contracts. Do not mark the broad goal complete after F97 |

## Exact edit scope

NEW:C:/Reverie Saga/src/domain/npc_assistance_memory.py;
C:/Reverie Saga/src/contracts/npc_assistance_memory.py;
C:/Reverie Saga/src/orchestration/npc_assistance_memory.py;
C:/Reverie Saga/src/app/npc_assistance_memory.py;
C:/Reverie Saga/tests/unit/test_npc_assistance_memory.py;
C:/Reverie Saga/tests/integration/test_npc_assistance_memory.py;
C:/Reverie Saga/tests/integration/test_assistance_memory_clients.py;
C:/Reverie Saga/tests/replay/test_assistance_memory.py;
C:/Reverie Saga/docs/work_orders/QT-F97_PERSISTENT_ASSISTANCE_MEMORY.md;
C:/Reverie Saga/docs/work_orders/QT-F97_REPLAY_SCOPE.json;
C:/Reverie Saga/docs/reviews/QT-F97_EXECUTION_2026-11-01.md.

MODIFY:C:/Reverie Saga/src/engines/encounter.py;C:/Reverie Saga/src/app/npc_cycle.py;
C:/Reverie Saga/src/app/client_session.py;C:/Reverie Saga/src/app/client_worker.py;
C:/Reverie Saga/src/app/client.py;C:/Reverie Saga/src/app/engine_bridge.py;
C:/Reverie Saga/src/app/npc_activity.py;
C:/Reverie Saga/clients/unity/Assets/Reverie/Scripts/BrainConnection.cs;
C:/Reverie Saga/clients/unity/Assets/Reverie/Scripts/PlayRoom.cs;
C:/Reverie Saga/clients/unity/Assets/Reverie/Scripts/LiveVerification.cs;
C:/Reverie Saga/tools/replay_body_inventory.json;C:/Reverie Saga/README.md;
C:/Reverie Saga/clients/unity/README.md;C:/Reverie Saga/BACKLOG.md;
C:/Reverie Saga/SESSION_HANDOFF.md;C:/Reverie Saga/GAME_SYSTEM_SUMMARY_KO.md;
C:/Reverie Saga/docs/proposals/QT-F95_PERSISTENT_ASSISTANCE_MEMORY.md.

Owned tmp/qtf97 and .pytest_cache/f97-* only. Other production/tests/goldens/checkers,
central contracts/IO/SQL/config/dependencies/assets/scenes/reference/private files forbidden.
Before full,stage only the owned encounter/inventory changes if needed for unchanged
checkout-index byte guards;record exact staged paths,never stage unrelated work or skip
the guard. No commit/push until full local acceptance;one final task PR includes all stages.

## Local acceptance

LOCAL_ACCEPTED2026-11-01:self-review. Full3761PASS901.83s,all434inputs unchanged;
new48PASS,old13modes/14pairs291updates+core/protocol/pins/full SQL EXACT. G07CURRENT/PASS
35bodies/8replays,all35/8/8/4obligations preserved. Ruffboth/format23/strict286/import3+1/
pip PASS. All12measured direct/framed queries<10s;dense264activity/talk2sTARGET remains
OPEN. Original sandbox local-socket restriction diagnosed without code/test/config change.
[Receipt](../reviews/QT-F97_EXECUTION_2026-11-01.md) owns exact results and limitations;
ordinary authorized publication follows. No native/independent/device/release acceptance.
