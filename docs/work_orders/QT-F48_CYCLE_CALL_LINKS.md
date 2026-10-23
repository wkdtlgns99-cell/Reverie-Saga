# QT-F48 — Causal player-call links in cycle activity

Status:READY,2026-10-23. Executor:current Codex;self-review,not independent.
Authority:director requests one next implementation and verification. Baseline:clean
main e782fa5380edf5119561213e7df7a3b977587351,PR15 merged. D2 remains OPEN.
Primary4retrieval support;related5display/6retained source/7client integration.

| Field | Contract |
|---|---|
| goal/non_goals | Cycle activity shows which actual player calls produced responses;no new behavior,conversation projection,CORE,storage,pins,wire,LLM,dependencies or release |
| prerequisites/reads | F30causal request/echo/reply selector,F47cycle verified activity;ENGINEERING_RULES,MASTER,prompt checkpoint/companion rules,numbered guide,work-order template,WORKSTATION_SETUP,README verification,root progress trio;app.npc_activity,client_session.inspect_activity,new/old cycle and call tests,Unity CycleActivity/CycleFlow |
| MODIFY | C:/ReverieSaga/src/app/npc_activity.py;C:/ReverieSaga/clients/unity/Assets/Reverie/Scripts/LiveVerification.cs;C:/ReverieSaga/tests/integration/test_cycle_self_activity.py;C:/ReverieSaga/README.md;C:/ReverieSaga/BACKLOG.md;C:/ReverieSaga/SESSION_HANDOFF.md;C:/ReverieSaga/GAME_SYSTEM_SUMMARY_KO.md;this order |
| NEW | C:/ReverieSaga/tests/integration/test_cycle_call_links.py;C:/ReverieSaga/docs/reviews/QT-F48_EXECUTION_2026-10-23.md;owned tmp/qtf48/ artifacts |
| forbidden | Other production modules,domain/contracts/engines/orchestration,content,wire,credentials/private saves,frozen evidence,reference checkout |
| public contract/wiring | Existing cycle_activity_messages and ClientSession/worker/Tk/pipe/Unity activity route unchanged signatures;append call section after existing supply and mixed8activity sections. Ordinary talk/F46 remains replay-free |
| algorithm/ownership | Enable existing causal collection in the same single isolated canonical replay;reuse _answered_call request/echo/reply identity+selected actor/NPC/same-tick checks. Verify final core+protocol before rendering. Extract shared private call renderer from return_recollection;its existing conversation-scoped output stays exact. Cycle inspection covers whole retained segment regardless of conversations |
| units/order/caps | Logical integer seconds;existing reply tick/event-ID ascending order;all verified replies counted,latest3details retained via existing _CALL_LIMIT. Mixed8events and persisted4supply anchors remain independent |
| empty/errors | No retained call→existing explicit empty call text even if cumulative reply count>0. Never reconstruct lost request identities from counters. Invalid causal chain/replay/head→SaveError NPC_ACTIVITY_SOURCE,logged/mapped by existing inspection boundary;no mutation,retry/polling/save usable,process control propagates |
| examples | bell1→request1/reply1,count1;five bells1..5→count5,rows3/4/5;wait16aftercall1→mixed bells trim reply1,but separate call1 survives. A subsequent talk does not reset inspection history. Checkpoint5/no trace→no call rows despite replies5;bell6→onlycall6. Rewind/restoration shows only selected branch |
| steps/tests | Reproduce absent causal row with new regression;extract renderer+enable collection;test caps/eviction/conversations/empty/compaction/branch+previous/restart/one replay/causal rejection/error recovery/process control/real pipe+Tk;extend native cycle flow using real bell and unchanged activity button |
| performance | TARGET query<2s on representative retained trace;measure one replay and source preservation,report actual,no regional/device claim |
| baseline/verification | Reuse installed .venv Python3.13.12/Tk8.6 and pinned Unity6000.3.25f1. README Ruff shared/quality,scoped+changed formatting,mypy,imports3+1,pip;new+cycle/self-activity/work/call/client/bridge/recovery tests,exact31CI boundaries. Actual native cycle run/capture and owned save replay/query/byte guards;leave editor open,restore scene. No shared CORE/production Unity change:reuse PR15full2259PASS and historical build only for unchanged inputs,not fresh full/build claims |
| acceptance | Exact settled vectors,one verified replay,independent caps,correct causal identities,truthful empty/error paths,ordinary clients/read-only/retry/recovery,static/affected/boundary/native/save evidence PASS;root progress trio synchronized |
| checkpoints | NOT_APPLICABLE:reuse existing verified retrieval/causal contracts,no new authority,storage or IPC. CP06held,prior patch rereview DEFERRED |
| stop/delivery | Resolve actual failure/unavailable verification before acceptance;no agents,commit/push/PR/merge/provider or automatic next task authorized by this implementation request |

F47test adaptation preserves its exact no-inference assertion at the original section end
(now third-from-last),and additionally asserts the new final empty-call message. No oracle
is removed;the added section intentionally changes the final message position.

Execution:LOCAL_ACCEPTED;[receipt](../reviews/QT-F48_EXECUTION_2026-10-23.md).

Publication follow-up2026-10-23:director now authorizes commit/push/PR,required CI,
ordinary main merge/sync and repeated next bounded tasks. This supersedes this order's
original local-only delivery scope;no release/checkpoint/agent authorization is inferred.
