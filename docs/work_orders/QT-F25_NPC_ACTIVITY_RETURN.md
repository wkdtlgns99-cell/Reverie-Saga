# QT-F25 — Present committed NPC activity on return

Date:2026-10-16 | State:LOCAL_ACCEPTED | Executor/review:Sol,self-review.
Director requests the next task after Tk repair;BACKLOG's bounded village direction selects
this small presentation/connection step. Primary5;related2/3/6/7. D2 remains OPEN.

| Field | Contract |
|---|---|
| goal/non_goals | On successful NPC talk show current committed watcher activity alongside approved dialogue. Qualify quest→travel/combat with autonomous activity while distant→return/report→one reward→save/load/restart. This remains the existing3x3harbor prototype,not regional streaming,roaming,RAG or a whole village implementation |
| baseline | b2876a7 plus RS-TK-001 local capture repair;121affected/static PASS. Read Git status before edits and preserve all Tk changes,prior engines/save pins and approved prose |
| prerequisites/read_files | Rulebook,MASTER3.1–3.4,BACKLOG/handoff/Korean companion,template/setup;src/app/client_session.py/client_text.py/client_worker.py/engine_bridge.py;contracts/client.py/quest.py/watch.py;domain/watch.py;engines/watch.py;approved content/harbor-memory-v1 pin;Tk/Unity generic messages consumers;test_quest/test_npc_memory/test_memory_client_route/test_engine_bridge |
| allowed_edit_paths | MODIFY C:/Reverie Saga/src/app/client_session.py,src/app/client_text.py,tests/unit/test_client_text.py,tests/integration/test_client.py(existing click helper's truthful ClientRequest annotation),README.md,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md;NEW tests/integration/test_npc_activity_return.py,this order,docs/reviews/QT-F25_EXECUTION_2026-10-16.md;owned tmp/qt-f25 evidence |
| forbidden_paths | CORE,engines,contracts/wire,scenario constants/save identities,accepted catalogs/approvals,generated Unity wire/source/scene/assets,frozen evidence,old test expectations,credentials,other repository |
| public_contract | ClientSession/ClientUpdate/wire unchanged. Add one system-information string to messages only for a committed publication containing actual QuestSpoken. Internal npc_activity_text(ClientView)->str uses only tick/npc_bells/npc_replies;Tk log and Unity PlayRoom.messages consume unchanged messages[] |
| behavior/ownership | Format `NPC 활동 현황 · {tick}초 · 종 {npc_bells}회 · 호출 응답 {npc_replies}회.` using the same postcommit derived view returned to the client. This is system factual status,not a new approved dialogue line or NPC memory. No extra command,write,clock step,provider call or enemy fact |
| edge_policy | All four successful intents include one status line. Out-of-range/rejected/aborted talk,unrelated actions and exact retry emit no extra status. Zero counters display0;counts reflect actual restored branch. Wrong IDs/missing fields/negative bounds retain existing runtime validation;no new external input or tie policy |
| independent examples | Down1/talk2→tick2,bells1,replies0. Open3/right4/down5,wait16→tick21,bells10;attack22/attack23/rest24/attack25→enemy0/actor1/stamina0,bells12. Left26/report27→stage3/reward1,bells13. Gratitude28→bells14,reward1. At25NPC remembers only accepted2;report27records completion_reported27,never witnessed defeat |
| algorithm_steps | Build committed ClientUpdate with existing formatter;detect actual QuestSpoken fact;append status from its view. Keep canonical dialogue bytes and command/publication ownership. Verify actual Tk buttons,worker,binary pipe and reopened owner |
| wiring | Durable publication→ClientSession._publication→ClientUpdate.messages→worker/Tk._render;EngineBridge's unchanged serializer→binary pipe→unchanged Unity PlayRoom.AddRange. No new registration/format |
| performance | Constant-size projection from existing update;no new IO/scan of world. One bounded fact scan of current publication;no timing target claimed |
| baseline_commands | RS-TK-001121PASS78.84s;PR8same tree full1946PASS remotely twice,historical. Add failing new expected-status tests before production edit |
| verification_commands | New normal/error/retry/restored-branch and actual Tk/pipe journey tests;affected quest/memory/text tests;README Ruff both/format/strict mypy/import3+1/pip;combined full regression after edits. Native Unity unchanged;new rendered line qualification there NOT_RUN unless actual reused-editor run occurs |
| test_responsibilities | NEW test_npc_activity_return:real deterministic route with16-second wait,ordered2-second NPC cues,privacy/source memory,one reward,retry,slot rewind,new Tk window and actual second process attach;test_client_text independently supplied nonzero/zero view values;no domain mocks |
| acceptance | Exact examples and failure preservation pass;new line reaches actual Tk log/binary messages;catalog/save/schema fingerprints unchanged;restart/restored branch matches actual saved facts;affected/static/full checks pass;3progress docs and receipt consistent |
| claude_checkpoints | NOT_APPLICABLE:small derived presentation using existing CP03–05 qualified rules,content and wire;no new risky CORE/format/first integration boundary. V3 stopped;CP06 release held |
| stop_conditions | Unexpected state/fact mismatch or unresolved new gameplay contract requires diagnosis;do not invent a world/NPC rule. No acceptance by updating existing goldens |
| delivery | Local reviewable edits and exact results/limits in Korean;no agents,commit/push/merge,provider calls or release. Record D2remaining world/retrieval scope |

Acceptance:[execution receipt](../reviews/QT-F25_EXECUTION_2026-10-16.md).
Actual Tk/pipe/restart/replay/text18PASS;combined1971PASS1092.70s/exit0/static PASS.
Native Unity new-line display NOT_RUN;existing editor retained. D2broader scope OPEN.
