# QT-F40–44 — Bounded NPC supply cycle batch

Status:READY,2026-10-22. Executor:current Codex;review:self-review only.
Authority:director requests two small and three large implementations with verification.
Baseline:bd8e9c710591a0c3eeebeb1d132d840177ccb9ea,clean main;local branch
codex/npc-cycle-batch-20261022. PR13 merged;earlier repair rereview remains DEFERRED.

## Scope and dependency order

| ID | Size | Goal | Primary category | Acceptance |
|---|---|---|---|---|
| F40 | Small | Tk/Unity show the selected NPC mode |5,support | Actual mode displayed without changing scenario/wire identity |
| F41 | Small | Existing stock text uses canonical WORK_PERIOD |5,support | Same text under current period;existing work behavior preserved |
| F42 | Large | Off-screen NPC consumes and replenishes communal supply |2 | Exact time/ordering/cap,partition equivalence,replay,no player reward |
| F43 | Large | Persist recent four own supply actions |2;6,4 retrieval support | Atomic actual causal evidence,eviction,restart/checkpoint rejection,truthful query |
| F44 | Large | Connect cycle to ordinary clients and save recovery |7;5,6 | Tk/worker/pipe/Unity,slots/current/previous restore,retry/read-only/native/build |

Non-goals:regional economy,hunger simulation,relationships,free-form LLM,assets,release,
old-save conversion,publication,agents,external review. D2 remains OPEN;CP06 held.
Prerequisites:F28–39 accepted scoped evidence;installed Python3.13.12/Tk8.6,
Unity6000.3.25f1. Read:ENGINEERING_RULES,MASTER,v2.6 prompt,README verification,
WORKSTATION_SETUP,numbered structure,existing npc_work/npc_memory codecs/engines,
ClientSession/Worker/PlayWindow/engine_bridge,BrainConnection/PlayRoom/LiveVerification.

Allowed NEW paths (under C:/ReverieSaga):src/{domain,contracts,engines,orchestration,app}/npc_cycle.py,
tests/unit/test_npc_cycle.py,tests/integration/test_npc_cycle.py,
docs/reviews/QT-F40_44_EXECUTION_2026-10-22.md,this order.
Allowed MODIFY:src/app/{npc_work,client,client_text,client_session,client_worker,engine_bridge}.py,
clients/unity/Assets/Reverie/Scripts/{BrainConnection.cs,PlayRoom.cs,LiveVerification.cs},clients/unity/README.md,README.md,pyproject.toml,
tests/governance/test_dependency_contracts.py,BACKLOG.md,SESSION_HANDOFF.md,
GAME_SYSTEM_SUMMARY_KO.md. Resolve actual Unity paths from disk before edit.
Forbidden:reference checkout,credentials,private user saves,frozen witnesses,other policies.

## Contracts,edges and examples

New opt-in bool npc_cycle=False in Python client constructors/CLI --npc-cycle;
Unity REVERIE_UNITY_NPC_CYCLE accepts unset/0/1. Requires approved harbor content and
npc_memory=True;mutually exclusive with npc_work. Validate exact bool before allocation.
Separate feature quest.harbor-cycle-v1 and default private Unity save path prevent repinning.
Existing wire/save envelope unchanged;incompatible old feature saves reject unchanged.

One quest.cycle owner holds one structured CORE field:stock0..3,produced/consumed
nonnegative signed64 counters,produced-consumed=stock,and bounded tuple of evidence.
Use existing production period4/cap3;consume one every10 logical seconds when available.
At ties consume first,then prepare. Full production is a no-op;no player inventory/reward.
Scheduled watch.npc-acted/PRE_TICK/0/0 drives POST_TICK/wave0. Validate selected owner,
header/payload/phase/time/bells. All writes through registered delta/reducer/patch at COMMIT.
Memory shares this single atomic owner rather than introducing a second engine/wave:
each actual action stores tick,within-wake sequence,causal NpcActed event ID and before/after
counters. No synthetic history from counts. Exact retries publish no duplicate facts.
Retain last4,with cumulative produced+consumed;empty only at zero. Unique ordered anchors.
Domain constructors reject bool/negative/out-of-range/types/invalid IDs;codecs reject extra
or missing fields;delta chains require same owner/contiguous endpoints;stage max2 actions.
Canonical checkpoint independently checks state and recent anchors,never fills missing data.
Checkpoint recent scan bounded41ticks;stable cycle supplies at least4events in this horizon.

Independent state examples (tick→stock,produced,consumed):0→0,0,0;4→1,1,0;8→2,2,0;
10→1,2,1;12→2,3,1;16→3,4,1;20→3,5,2;30→2,5,3;32→3,6,3;40→3,7,4.
O(1) checkpoint state:before16,stock=t//4-t//10;from16,stock=2 when t%20 in10,11,
otherwise3;consumed=t//10;produced=stock+consumed. Engine uses actual clock/actions,
not this independent closed form. Counter overflow rejects;no wrap/saturation fiction.

Presentation:actual committed action lines;talk/activity show only stored own evidence,
explicit recent4/cumulative count and current stock. Existing quest two conversation memories
remain separate. Saved inspection labels saved evidence;load rewinds own memory;previous
load keeps source untouched/private clone. No new RPC fields or names. F40 uses known mode
selection only,not inferred save data. F41 references WORK_PERIOD rather than literal4.

## Execution and verification

Implement F40/41,then atomic F42/F43 core,then F44 callers. Register engine independence
in pyproject/import probes without weakening controls. Tests in new unit/integration paths
derive expected vectors independently:time boundaries,offscreen,ties,cap,read-only access,
strict malformed data,delta composition,checkpoint corruption,replay,partition equivalence,
quest reward isolation,retry,save/previous/restart/branch and actual Tk/pipe callers.
Performance target:constant per wake,bounded4 memory and41tick checkpoint scan;
measure representative long logical time/checkpoint query and report actual,not guessed.
Commands:README ruff+quality,scoped format,mypy --no-native-parser,both import contracts,
pip check,targeted pytest,full pytest and unchanged exact CI boundary selection.
Native:installed Unity compiled cycle flow,small-view mode/activity/save UI and Windows build;
owned saves validate/replay/source-byte guards. Leave ordinary editor open;no release claim.
Baseline static/CI2174PASS on identical PR13 tree;current-host affected127PASS already.
Acceptance:all five rows independently evidenced,all required checks pass,root progress trio
synchronized,git diff reviewed. NOT_RUN limits remain explicit;do not mark accepted early.
Claude:NOT_APPLICABLE,new bounded implementation under existing deterministic CORE and
save/IPC boundaries;no new scheduler/wire envelope/governance boundary. CP06 release held.
Stop only on conflicting user changes/unresolved semantics/unavailable required validation
after safe repairs. Delivery:Korean task count/category/results;local only,no commit/push/PR.


## Publication authorization update — 2026-10-22

Director explicitly requests Git publication and the next implementation. This supersedes
this order/receipt's earlier local-only restriction for batch commit/push/PR. Actual remote
state belongs to Git/GitHub. Main merge,agents,external review and release remain outside
this new publication instruction.
