# QT-F54 — NPC supports an accepted quest by opening the passage gate

Status:LOCAL_ACCEPTED,2026-10-25. Executor:current Codex;self-review,not independent.
Authority:director requests automatic development and selects NPC/world behavior expansion.
Primary2internal calculation;related3bindings,5presentation,6save,7integration.

| Field | Contract |
|---|---|
| goal/non_goals | In a new explicit harbor cycle-aid variant,the NPC uses its committed directly heard quest acceptance to open the existing passage gate at its next scheduled wake while no completion report has been heard. Stop after the report. Preserve old modes/pins/content and supply rules. No new combat,reward,inventory,NPC movement,regional economy,LLM,save envelope/migration,scheduler,dependencies,release or publication |
| baseline | HEAD72c2d588d7f64c3e113cf462af35fb673bf82582,branch codex/cycle-call-recall-20261024,22accepted F49–53dirty paths;hash entry under tmp/qtf54/entry.json. Latest user resume2026-10-25;goal initially paused,user resumed via app,and get_goal confirmed ACTIVE before implementation continuation |
| prerequisites/reads | ENGINEERING_RULES,handoff/backlog/Korean companion,MASTER1.3/2/3/8/9,numbered guide,Sol template,WORKSTATION_SETUP,README verification,prompt checkpoint procedure;EncounterActions/GateDelta ownership and codecs/reducer/presenter,watch NpcActed/registrations,memory read views,cycle bundle/bootstrap,ClientSession/Worker/Tk/bridge/activity and Unity BrainConnection/PlayRoom/LiveVerification;F28/F40–44/F49–53contracts/evidence |
| NEW | Under C:/Reverie Saga:src/contracts/npc_gate_aid.py,src/orchestration/npc_gate_aid.py,src/app/npc_gate_aid.py,tests/unit/test_npc_gate_aid.py,tests/integration/test_npc_gate_aid.py,this order,docs/reviews/QT-F54_EXECUTION_2026-10-25.md;owned ignored tmp/qtf54 and .pytest_cache/qtf54-* |
| MODIFY | Under C:/Reverie Saga:src/engines/encounter.py,src/orchestration/encounter.py;src/app/npc_cycle.py,npc_activity.py,client_session.py,client_worker.py,client.py,client_text.py,engine_bridge.py;clients/unity/Assets/Reverie/Scripts/BrainConnection.cs,PlayRoom.cs,LiveVerification.cs;README.md,clients/unity/README.md,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md. Temporary owned Unity Editor/F54VerificationTrigger.cs and .meta may be created then removed;restore exact entry PlayRoom.unity after public Prepare. No other scene changes |
| forbidden | Reference checkout,user saves/credentials,frozen earlier receipts/orders/tests,old descriptor defaults,goldens,CI/governance/dependency/settings/save envelope or migration changes. Earlier dirty source edits preserved;no agents/provider calls/remote administration |
| public selection | Exact bool npc_aid=False on ClientSession/Worker/PlayWindow/EngineBridge/serve and cycle bundle/bootstrap/retrieval entrypoints. True requires npc_memory and npc_cycle and not npc_work,valid harbor content;otherwise NPC_AID_CONTENT before save/thread/process allocation. CLI --npc-aid. Unity REVERIE_UNITY_NPC_AID accepts unset/0/1,default0 and same prerequisites;separate default harbor-cycle-aid/catalog-pin/game.sqlite. Existing wire/view/update/request fields unchanged |
| feature identity | New quest.harbor-cycle-aid-v1 with added rule/payload/presenter descriptors. False returns byte-identical prior descriptors/pins. New variant adds no component,state field,persistence envelope or pending event;incompatible old saves reject unchanged,never repin. Current/previous slots,restart/replay/retrieval select the exact same variant |
| single writer | Existing encounter.actions retains sole ownership of encounter.gate.is_open. Its optional aid mode adds a POST_TICK activation consuming existing PRE_TICK watch.npc-acted. No engine-to-engine import. Existing RESOLVE player operations unchanged. Reads existing gate and own quest.npc-memory entries through registered views;memory consumer metadata adds encounter.actions only in the new variant |
| behavior/order | On each actual2second wake,validate exact source class/schema/owner/producer/phase/wave/sequence/due/occurred_at/bell endpoints. Read the POST_TICK barrier's prior memory:accepted_at>0,nonempty acceptance_source,reported_at==0 and empty report_source. If active and gate closed,stage existing GateDelta(gate,0,1) and emit GateAssisted(npc_id,target_id) with actual wake causal ID. If open/inactive,explicit no-op and no fact. Never use enemy defeat or aggregate reply counts as a heard report. Memory written in the same POST_TICK barrier becomes visible at the next wake;no same-barrier read-after-write assumption |
| payloads/errors | New quest.gate-assisted/v1 FactPayload(npc_id:EntityId,target_id:EntityId) and quest.gate-aid-cue/v1 PresentationPayload(npc_id,target_id,logical_tick:int). Strict exact fields/types/selected IDs,positive even cue tick;codec mismatch NPC_AID_PAYLOAD. Registered presenter validates source/phase/wave/sequence/time/one wake cause and committed open gate before producing cue. Invalid source -> CandidateError INVALID_FACT before mutation. No numeric player aid input;no RNG/wall clock |
| edges | Empty memory/complete report/open gate are no-ops. Repeated wakes do not duplicate opening. Closing while aid active is allowed;the next eligible wake reopens,including the same logical tick after RESOLVE when even. Multiple gate changes compose through existing registered reducer and final state. NPC only opens,never closes/crushes occupants. Rejected actions do not advance/wake. Retry adds no opening/fact. Precommit faults preserve gate/memory/bytes;postcommit truth and uncertain recovery retain normal durable semantics. Stop/later load/restart restores exact branch truth |
| independent examples | down1,talk2accept:gate remains closed at2;wait1to3still closed;wait1to4opens once alongside normal prepare4. Equivalent wait16from2 reaches18with one aid opening at4 and unchanged supply state3/4/1. Manual open before acceptance means no aid fact. While active close on odd tick leaves closed until next even wake;close on an even wake is followed by real NPC reopen. Existing combat/report flow ends with one favor;after report,close then wait16leaves closed. A compacted accepted-memory checkpoint still drives future aid without inventing old gate history |
| wiring/algorithm | Compose variant from unchanged cycle bundle,replace only encounter.actions binding with optional implementation and append POST_TICK activation/source subscriber,read consumer,strict new payload codecs/presenter/rule descriptors. Thread explicit selection through ordinary session/worker/pipe/Tk/Unity and all isolated activity replays. Existing gate state drives board;new cue adds Korean NPC opening message and selected-mode label. No isolated helper-only completion |
| performance | O(1)decision per existing wake,zero new events when no state change,no dynamic cache. Measure ordinary aid talk/wait/read-only activity vs2second representative target;retain F53long-history overrun as OPEN unless repaired and measured separately. No MIN-SPEC/device claim |
| baseline/verification commands | Reuse installed Python3.13.12/Tk8.6 and pinned Unity6000.3.25f1 after actual readiness checks. README both Ruff configs,changed-file format,strict mypy,both import checks,pip;new unit/integration,affected cycle/memory/encounter/slot/client/bridge tests,exact CI boundary selection,and full pytest because shared authoritative EncounterActions changes. Keep original sandbox hardlink errors and qualify same failing cases with permitted access |
| test responsibilities | Unit source/memory/open/closed/tie/noop/malformed codec/constructor and registered invocation guards. Integration real SQLite down/talk/wait/close/report,partition equivalence,canonical replay,compact checkpoint,exact retry,precommit preservation,slots/previous/restart/old-pin rejection,read-only query and real worker/pipe/Tk. Native opt-in mode/action/save/load/reconnect/returned message,actual board gate state,source-preserving readbacks and fresh Windows build/release-hook exclusion. Reuse earlier evidence only for unchanged inputs |
| acceptance/delivery | Actual new NPC gate action on ordinary registered clients,truthful message,one writer,unchanged old identities,determinism/retry/recovery/read-only preservation,required checks/full/native/build pass. Synchronize root progress trio/receipt,review diff/scope. Partial stages remain IN_PROGRESS/UNVERIFIED,never new feature DONE. Local only,no commit/push/PR/merge/agents/release |
| checkpoints/stops | CP05first bounded quest/NPC integration closed;this optional action reuses existing phases/gate writer/deltas/save/IPC boundary,so no new scheduled checkpoint trigger. CP06release held;earlier independent patch rereview deferred. Stop/escalate on unresolved ownership/phase/source semantics,new save-format/scheduler authority,overlapping user edits or unavailable required checks after safe alternatives |

Projection clarification from real initial integration failure:RESOLVE player close followed
by POST_TICK aid open is a valid ordered0/1gate chain;an earlier blocked-door move can also
precede the NPC opening. The optional EncounterPresenter must validate those actual gate
facts in order and their final committed endpoint,then render the intermediate player fact.
Old-mode projection remains unchanged. Reuse the existing encounter.presenter identity and
register GateAssisted there,with new payload codecs;no second gate presenter or fake view.
This requires the explicit existing orchestration/encounter.py edit above. GateAidPresenter
in the initial draft is replaced by that responsible-layer integration before acceptance.

Required qualification metadata discovered by the full run:the existing manual G07
inventory correctly rejects the modified encounter engine as STALE_INPUT. Add allowed
MODIFY C:/Reverie Saga/tools/replay_body_inventory.json and
C:/Reverie Saga/tests/governance/test_replay_body_coverage.py;NEW
C:/Reverie Saga/docs/work_orders/QT-F54_REPLAY_SCOPE.json. Changes are solely the reviewed
source hash,six existing encounter public-member ranges,the manifest's exact additional
static read-tuple generator identity,and the independent expected nested-count3→4.
Preserve all35public obligations,8sources/8nodes,other29members,the native-body positive
requirement,all rejection tests,tool code/policy/CI and frozen prior authoring scope.
This is necessary current-input qualification,not new governance policy or a bypass.
Review source/factory/nested code before metadata edits;never derive obligations from hits.
Private aid behavior remains covered by the57new real tests;the old8manual contexts do
not claim aid-branch coverage. Retain the first full run's stale errors and requalify the
full suite after the changed test/input metadata. No failure is skipped or relabeled PASS.

The first full run also exposes three unchanged checkout-index tests:the real Git index
still contains the old encounter source,while the reviewed working source is intentionally
uncommitted. Qualify the exact current prospective source with a private GIT_INDEX_FILE and
private GIT_OBJECT_DIRECTORY under tmp/qtf54,using the real read-only object store as an
alternate. Run the original three autocrlf cases unchanged;hash the real index before/after.
No real-index staging,commit,reference update or publication. Preserve the original failures
and distinguish current-source checkout qualification from published-head CI acceptance.

While native timing is pending,an allowed supporting qualification uses the installed
Unity6000.3.25f1NetCoreRuntime/DotNetSdkRoslyn compiler with the project's actual cached
editor/player response files. Preserve references,defines,analyzers and warning policy;
redirect only assembly/reference outputs into owned tmp/qtf54/csharp. Editor-tool compile
may reference that fresh editor client and include an owned tmp copy of the prepared
verification trigger. Do not install it into Assets,start Unity,execute client assemblies
or alter Library responses. Bind compiler/response/source hashes and check preservation.
This establishes C#compilation only,never substitutes for native flow/screen/player build.
