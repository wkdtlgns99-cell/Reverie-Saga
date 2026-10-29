# QT-F85 — Show current next patrol step after an NPC reply

Status:LOCAL_ACCEPTED2026-10-29. Human requests one next task after F84optimization/verification.
Executor:local Codex,self-review. Primary5presentation support;related2existing NPC rules,
6postcommit truth,7actual direct/framed delivery. No new movement capability.

| Field | Contract |
|---|---|
| goal/non_goals | Add current next-patrol-step text to reach-mode actual reply feedback,alongside F83support plan. No new goal,movement,timing,queue,cache,replay,IO,state/save/schema/pin/flag/native change |
| baseline | main5fa348b plus qualified F82/F83/F84dirty work. F84full3562PASS,13mode/source parity and paired12queries qualified;2sTARGET remains OPEN. Preserve all existing paths;owned prior client source in tmp/qtf85 |
| prerequisites/reads | ENGINEERING_RULES,HANDOFF,BACKLOG,Korean progress,MASTER,structure guide,F83/F84orders/receipts;ClientSession._publication,WatchReplied/TurnCommitted;quest_patrol_next_step and ready_patrol_target;actual F82driver/reply helpers |
| allowed_edit_paths | MODIFY C:/ReverieSaga/src/app/client_session.py;BACKLOG.md;SESSION_HANDOFF.md;GAME_SYSTEM_SUMMARY_KO.md;README.md. NEW tests/integration/test_call_patrol_feedback.py;docs/work_orders/QT-F85_CALL_PATROL_FEEDBACK.md;docs/reviews/QT-F85_EXECUTION_2026-10-29.md. Owned tmp/qtf85/.pytest_cache/f85-* |
| forbidden_paths | Other sources/prior tests/goldens/checkers/engine/domain/store/protocol/Unity/reference/user paths;no agents/dependencies/settings/security/native/publication/goal action |
| public_contract/behavior | No signature/schema change. Existing reach-mode selected NPC actual WatchReplied condition appends existing quest_patrol_next_step(current_core,layout,error_code='NPC_RECOLLECTION_SOURCE',npc_ready_patrol=True),each line prefixed '응답 후 현재 '. Capture the same current snapshot once for support+movement plans. Text is a current condition,not a promised future event |
| ownership/wiring | Committed facts remain sole authority. Reuse pure existing plan helper inside ClientSession._publication,then unchanged ClientWorker/framed/Tk/native message consumers. No separate inspection/replay/IO or stored state |
| edge_policy | Default/ready parent only/other NPC/no actual reply/rejected command/exact retry add no new row. Actual reply adds once. Existing helper preserves no-memory/report/open/stock/occupancy precedence. If either projection raises SaveError,the reply remains committed;existing logging/NPC_RECOLLECTION_SOURCE propagates and retry/next action remains possible. No partial successful plan publication |
| examples | Actual bell11NPC7stock1 ->FREE_HOME;bell13NPC6stock2closed ->FREE_NEIGHBOR;bell15NPC7gate opens ->FREE_HOME. After waiting14,down15/down16occupies home6while NPC7cannot return;bell17 ->BLOCKED_HOME. Use independently specified existing Korean strings,not helper-derived oracle |
| algorithm_steps | Add actual direct/framed failing11/13/15/17examples;reuse helper and same snapshot;qualify exact retry/source bytes,no row in old ready mode,and postcommit helper failure/recovery |
| performance | One bounded current-snapshot helper per actual reply,no replay/IO. Reuse F84query measurements for unchanged expensive query paths;no new global latency claim |
| baseline_commands | pytest new test file -k actual:8missing-row failures expected before edit |
| verification_commands | New+F83+F82+existing next-step/client affected tests,Ruffboth/strict/scoped format/import3+1/currentCI31/docs10/UTF8/links/scope. Reuse unchanged F84shared full/replay/G07 evidence;no shared CORE change here |
| test_responsibilities | NEW file owns actual current-state11/13/15/17direct/framed paths,exact row/no retry replay,source byte invariants,legacy absence,postcommit failure no rollback and recovery. No mocked domain outcomes |
| acceptance | Correct next-action row reaches actual callers once;current support and world state remain correct;all affected/static/boundary checks pass;root trio synchronized. F84four2sTARGET misses/native/independent/device/CP06/release holds remain explicit |
| claude_checkpoints | No new CP01–05trigger:reuse established pure presentation helper/message pipeline. Prior CP06/independent patch-review holds retained;self-review is not independent acceptance |
| stop_conditions/delivery | Preserve user/prior edits;stop on missing semantics/new authority/evidenced unavailable verification after safe alternatives. English receipt/Korean result. Exactly one further task then stop;no commit/push/native/agent/automatic loop |


[Execution evidence](../reviews/QT-F85_EXECUTION_2026-10-29.md). Self-review only;F84
2sTARGET and prior native/independent/device/release holds remain. No next automatic task.
