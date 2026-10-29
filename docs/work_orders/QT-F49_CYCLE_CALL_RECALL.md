# QT-F49 — Recall answered calls during cycle-mode talk

Status:READY,2026-10-24. Executor:current Codex;self-review,not independent.
Authority:director requests next task and automatic execution. Baseline:clean main
72c2d588d7f64c3e113cf462af35fb673bf82582;branch codex/cycle-call-recall-20261024.
Primary4retrieval support;related5/6/7. D2 OPEN;CP06 release held.

| Field | Contract |
|---|---|
| goal/non_goals | Cycle talk recalls verified answered player calls since the previous retained conversation,as work talk already does. No new facts,CORE/schema/save/pins/wire/content/LLM/dependencies or release |
| prerequisites/reads | F30causal selector/conversation scope,F46player statement projection,F48cycle inspection;ENGINEERING_RULES,MASTER,prompt checkpoint/companion rules,numbered guide,work-order template,WORKSTATION_SETUP,README verification,root progress trio,app.npc_activity/client_session,cycle/player-memory/call tests,Unity LiveVerification |
| MODIFY | C:/Reverie Saga/src/app/npc_activity.py;C:/Reverie Saga/src/app/client_session.py;C:/Reverie Saga/tests/integration/test_cycle_player_memory.py;C:/Reverie Saga/clients/unity/Assets/Reverie/Scripts/LiveVerification.cs;C:/Reverie Saga/README.md;C:/Reverie Saga/BACKLOG.md;C:/Reverie Saga/SESSION_HANDOFF.md;C:/Reverie Saga/GAME_SYSTEM_SUMMARY_KO.md;this order |
| NEW | C:/Reverie Saga/tests/integration/test_cycle_call_recollection.py;C:/Reverie Saga/docs/reviews/QT-F49_EXECUTION_2026-10-24.md;owned tmp/qtf49 artifacts |
| temporary native repair harness | C:/Reverie Saga/clients/unity/Assets/Reverie/Editor/F49VerificationTrigger.cs and generated .meta,verification only. Reuse editor31168;set explicit harbor/approved catalog SHA,memory1/work0/cycle1,retained mode0 and fresh tmp/qtf49/native-corrected/game.sqlite via Environment/EditorApplication APIs,then existing PlaytestBuild.Verify. Refresh through observed Unity UI;remove both owned files after verified idle. Preserve first failed log,source bytes and scene |
| forbidden | Other production modules,domain/contracts/engines/orchestration,content,wire,private saves/credentials,frozen evidence,reference checkout |
| public contract | New app-only cycle_call_recollection(segment:SaveSegment,npc_id:str,*,content:QuestContent,current:DurableCheckpoint,conversation_id:str)->tuple[str,...]. Existing ClientSession/worker/Tk/pipe/Unity signatures unchanged |
| algorithm/ownership | Reuse _conversation_activity with private npc_cycle=False default and existing _call_messages;one isolated cycle replay verifies final core/protocol and current QuestSpoken identity. Keep F46persistent player selector and cycle_messages unchanged;append call lines. No work-mode renderer changes or duplicate replay |
| units/order/caps | Integer game seconds;all verified replies since prior retained talk counted,latest3 tick/event-ID ascending. Missing previous talk uses checkpoint boundary. Mixed bells and persisted supply anchors never substitute for causal evidence |
| edge/error | No calls→explicit empty even with persisted cumulative replies. Rejected/non-talk/retry adds no recall/replay. Missing/wrong owner/current talk,malformed causal chain,replay/core/protocol mismatch→NPC_RECOLLECTION_SOURCE. OSError logged/remapped at postcommit session boundary;durable turn remains committed,retry/save/polling usable;BaseException propagates |
| independent examples | down1,talk2,bell3,wait16→19,talk20 recalls onlycall3 since2;nexttalk21 empty. Fivebells3..7,talk8→count5/details5,6,7;bell9,talk10→only9. Checkpoint with replies5/no trace→new talk empty,not five inferred calls. Rewind restores selected branch |
| steps/tests | Add failing real session regression;reuse renderer/factory and wire committed cycle talk;test first/subsequent/empty/caps/eviction/retry/compaction/rewind/restart/error/process control/one replay and real pipe/Tk;extend native cycle checks |
| test adaptation | F46's no-replay assertion applies only to player statement selection;this new authorized call projection intentionally needs one verified replay. Replace that assertion with exactly-one canonical restore while preserving original persistent statement/time/quest assertions;no expectation weakening |
| performance | TARGET added call projection<2s on representative retained trace;measure actual single replay including durable talk,report samples and host scope |
| baseline/verification | Reuse local .venv Python3.13.12/Tk8.6,pinned Unity6000.3.25f1. New regression fails absent call. README shared/quality Ruff,changed+CI format,mypy,imports3+1,pip;cycle/call/work/player-memory/client/bridge/recovery affected tests,exact31CI boundaries;actual native cycle/capture and owned-save replay/query/byte guards. Preserve editor/scene. No CORE/production Unity change:prior full/build evidence only for unchanged inputs |
| acceptance | Independently derived vectors and real registered consumers pass;single verified replay,truthful postcommit recovery,old work behavior preserved,static/affected/boundary/native/save evidence pass,progress trio synchronized |
| checkpoints | NOT_APPLICABLE:existing read-only verified causal/conversation boundary,no new authority/storage/IPC. Prior independent patch review DEFERRED;CP06 release held |
| stop/delivery | Diagnose/repair authorized failures;escalate unresolved semantics/overlapping edits/unavailable validation after safe alternatives. Continue authorized bounded work;no agents,release,protection change or unrequested publication |

Execution:LOCAL_ACCEPTED2026-10-24;[receipt](../reviews/QT-F49_EXECUTION_2026-10-24.md).
