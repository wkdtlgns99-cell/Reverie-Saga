# QT-F16 — Inspect Conversation Memories in the Tk Client

Date:2026-10-15 | State:LOCAL_ACCEPTED | Executor/review:Sol,self-review.
Director explicitly keeps Claude V3 pending and requests the next implementation.
Primary5;related2/6. This displays the existing scoped records,not broader NPC cognition.

| Field | Contract |
|---|---|
| goal | In the memory-enabled Tk prototype,show the NPC's recorded conversations with this player on demand without taking a turn |
| baseline | e32cf3e08a44d327b7ed091650bec7f74716676f;only BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md dirty from local pause. Preserve those entries;tracked byte witness tmp/qt-f16/entry.json |
| prerequisites/reads | QT-F09/A3 accepted existing memory bundle;rulebook,handoff,backlog,numbered guide,MASTER memory/truth,work-order template,setup;client/session/worker/text,contracts/client,domain/npc_memory,QTF09 order and memory-client/native Tk tests |
| paths | Prefix C:/ReverieSaga/. MODIFY src/app/client.py,client_session.py,client_worker.py,client_text.py;README.md,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md. NEW tests/integration/test_client_memory_inspection.py,this order,docs/reviews/QT-F16_EXECUTION_2026-10-15.md;owned tmp/qt-f16 and .pytest_cache/qt-f16-* |
| excluded | All other production/contracts/CORE/save schemas,wire protocol,C#/Unity,approved prose/catalogs/pins,fixtures/goldens,provider/budget/keys,governance/dependencies,frozen review inputs. No network,agents,publication or release |
| API | ClientSession.inspect_memory()->ClientUpdate;ClientWorker.inspect_memory()->Future[ClientUpdate]. Existing ClientRequest/ClientUpdate and engine-pipe schema unchanged;worker private dispatch alone accepts local memory operation |
| behavior | On the existing owner thread,require memory mode,read its committed snapshot's exact owner NpcQuestMemoryRecord via existing _record,format only its existing two conversation kinds/ticks. Return MEMORY_INSPECTED update/messages with same view/token/path/quest/reward;reset_log=False. No submit/export/load/context-provider call or change to previous exact-retry command |
| UI/wiring | PlayWindow shows a separate NPC conversation-memory button only for npc_memory=True;uses worker Future and existing poll/render/busy/close handling. Add button to enable/disable handling;append result to bounded existing Korean log. No disk access on Tk thread |
| visibility | These two records describe conversations this player participated in;display does not reveal private traits/goals,source hashes,other NPC knowledge,enemy state or inferred eyewitness death. Explicitly distinguish directly heard acceptance from received completion report |
| edges/errors | Empty=>explicit no recorded conversation;accepted=>one ticked line;report=>two chronological lines. Memory-disabled session or unattached worker=>NPC_MEMORY_UNAVAILABLE;pre-attach lookup never creates/opens a game. Worker returns explicit same-view error with Korean notice and remains usable. Invariant missing/duplicate records remain CLIENT_ERROR,not player rejection. Worker closing=>CLIENT_CLOSING;process-control propagates through Future;ordinary failures log and polling/close continue |
| examples | Fresh tick0=>no conversation;accepted@2=>directly heard undertaking;enemy defeated@9=>still only accepted@2;report@11=>reported completion,not witnessed death. Query retains tick/revision/reward/retry identity;loading earlier save removes newer report from subsequent query |
| algorithm/performance | Check mode->snapshot->_record->two typed Korean descriptions->existing update;O(MEMORY_CAPACITY=2),no RNG/time/index. No broad hardware/latency qualification claimed |
| baseline | Existing approved-memory route and client text tests;record actual results separately from historical full1675/current mixed CI |
| verification | New session stages/state/file/protocol/retry/load/resume/error/thread tests;real Tk button/render/busy/failure/close tests;existing client,worker,memory,pipe/text regressions. README Ruff both/scoped format/strict mypy/import commands;no shared CORE changes,so affected tests rather than repeated full CORE suite. UTF8/link/diff/protected-hash checks |
| acceptance | Visible native Tk button/messages and continued input;exact state/retry/save preservation at all four stages;errors explicit/recoverable;unchanged protected runtime/schema/wire/catalogs;all affected/static checks pass;three progress docs synchronized |
| checkpoints | Existing CP01–05 closed;no new checkpoint triggered by read-only display of already exposed player conversation facts. V3 external inspection remains pending at pinned e32cf3e;this implementation is additional local work and not covered by that review/CI. CP06 release remains held |
| stops/delivery | Escalate unresolved privacy/truth semantics,overlapping user edits or required out-of-scope contract changes;repair scoped failures autonomously. Report actual tests/native limits;no commit/push or automatic next task |

Accepted:[execution](../reviews/QT-F16_EXECUTION_2026-10-15.md). Final126affected tests PASS44.24s;
15new cases,3native Tk cases;both Ruff/scoped format13/strict mypy158/imports3+1/pip PASS.
Broader NPC cognition and Unity display are unimplemented by this task;V3/CP06remain pending.
