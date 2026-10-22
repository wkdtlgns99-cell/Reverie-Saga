# QT-F46 — Recall player statements in cycle-mode conversations

Status:READY,2026-10-23. Executor:current Codex;self-review,not independent review.
Authority:director requests the next task. Baseline:main6dc918e,clean;PR14 merged.
Primary4retrieval support;related5screen/6persistent memory/7integration. D2 stays OPEN.

| Field | Contract |
|---|---|
| goal | Cycle-mode committed talk includes the latest actual persistent player quest statement,as existing work-mode talk already does |
| non_goals | New mechanics,memories,LLM,CORE/schema/pins/save/IPC changes,content approval,release,publication or agents |
| prerequisites | F31 pure player_memory_recollection,F40–44 cycle integration,F45 comparison;installed .venv Python3.13.12/Tk8.6 and pinned Unity6000.3.25f1 |
| reads | ENGINEERING_RULES,MASTER,prompt checkpoint/companion rules,numbered guide,README verification,WORKSTATION_SETUP,SESSION_HANDOFF,BACKLOG,GAME_SYSTEM_SUMMARY_KO;client_session._publication,npc_memory_query.player_memory_recollection,npc_activity.return_recollection,client_worker._run/_error_update;cycle/player-memory integration tests,Unity CycleFlow/PlaytestBuild.Verify |
| MODIFY | C:/Reverie Saga/src/app/client_session.py;C:/Reverie Saga/clients/unity/Assets/Reverie/Scripts/LiveVerification.cs;C:/Reverie Saga/README.md;C:/Reverie Saga/BACKLOG.md;C:/Reverie Saga/SESSION_HANDOFF.md;C:/Reverie Saga/GAME_SYSTEM_SUMMARY_KO.md;this order |
| NEW | C:/Reverie Saga/tests/integration/test_cycle_player_memory.py;C:/Reverie Saga/docs/reviews/QT-F46_EXECUTION_2026-10-23.md;owned artifacts under C:/Reverie Saga/tmp/qtf46/ |
| forbidden | Other production modules,domain/contracts/engines/orchestration,wire/content/private user saves/credentials/security settings/frozen evidence/reference checkout |
| public contract | Existing ClientSession.act/retry and ClientUpdate unchanged;no new public signature. Reuse player_memory_recollection(record:NpcQuestMemoryRecord)->tuple[str,...] without changing it |
| behavior | After a new committed QuestSpoken in cycle mode,append one latest-statement line after existing cycle messages,from selected NPC record in the same committed snapshot. No retained-segment read/replay or extra command |
| edge policy | No record synthesis;existing exact owner lookup applies. Empty record uses existing explicit empty text. Acceptance reports original accepted tick;completion reports original reported tick and expressly denies eyewitness knowledge. No recall on rejected/non-talk/retry. Other modes unchanged |
| failure | GenerationError during statement selection is logged and mapped to existing SaveError NPC_RECOLLECTION_SOURCE;commit remains durable. Existing worker exposes postcommit error with live view,quiet retry/save/next request remain usable. Unexpected exceptions retain existing boundary logging;BaseException propagates |
| examples | down/talk→promise2;GOAL at9→dead enemy,reward0,only accepted2 anchor;left/talk→report11,reward1;talk again12→report11;load pre-report9,wait,left,talk→report12. Checkpoint-only restoration retains original2/11 rather than synthesizing current tick |
| algorithm | Reuse helper/import;add cycle branch projection/error mapping;add independent lifecycle/error/registered-caller tests;extend native CycleFlow checks for promise22 and report31 without changing its command vector |
| wiring | ClientSession._publication→ClientWorker→Tk and engine_bridge binary pipe→Unity BrainConnection/PlayRoom. Existing work recall and non-cycle outputs preserved |
| performance | TARGET added selection<2ms on actual persisted record,sample1000 calls;bounded2 anchors,no extra IO/replay |
| baseline commands | .venv Python version/import probe PASS;new regression must fail for missing cycle recall before implementation;existing cycle+player-memory selection expected PASS |
| verification | README shared/quality Ruff,scoped/new-file format,strict mypy,imports3+1,pip;new tests plus cycle/player-memory/work/slot/recovery/client/bridge/quest-memory tests;exact CI boundaries;real Unity cycle run/capture/source-preserving save replay. No shared CORE changes:reuse historical full2216/build only for unchanged authoritative/Unity production sources,not fresh full/build evidence |
| test responsibilities | NEW test_cycle_player_memory.py:normal/rejected/retry,unreported death/record origin,checkpoint-only restore(two states),current/previous rewind/restart/source bytes,real pipe/Tk/worker,failing postcommit projection and process control. Existing helper unit vectors reused |
| acceptance | Settled vectors and source/branch/retry isolation pass;ordinary callers display line;static/dependency/affected/boundary checks pass;native evidence explicit;root progress trio synchronized |
| checkpoints | NOT_APPLICABLE:reuse existing read-only context with no new authority/storage/IPC boundary. CP06 release held;prior patch rereview DEFERRED |
| stop | Overlapping user edits,unresolved actual-source contract,unavailable validation after safe diagnosis;report evidence rather than claim acceptance |
| delivery | Local implementation/evidence only;no commit/push/PR/merge requested. Report category,actual results and limits;no automatic next task |

Execution:LOCAL_ACCEPTED;[receipt](../reviews/QT-F46_EXECUTION_2026-10-23.md).
