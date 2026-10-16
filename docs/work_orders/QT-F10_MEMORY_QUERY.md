# QT-F10 — Small Structured Evidence Query

Date:2026-10-14 | State:ACCEPTED | Executor/reviewer:self.
Director requests one small next task with10%usage remaining. Primary4;related3/6.
Authority:BLOCK4 A8 T0;existing QT-F09 two-record memory/context contracts.

| Field | Contract |
|---|---|
| goal/non_goals | Add pure subject/kind/inclusive-time/limit filtering and newest-first ranking;use default selector in actual memory_brief. No new memories/CORE/save/UI/provider/API call/dependency/agent |
| baseline/reads | Current dirty state preserved;tmp/qt-f10/entry.json;rulebook/handoff/backlog/guide,QTF09 order,actual context/domain/brief/tests,README/setup/template already qualified |
| allowed paths | NEW src/app/npc_memory_query.py,tests/integration/test_npc_memory_query.py,this order,docs/reviews/QT-F10_EXECUTION_2026-10-14.md. MODIFY src/app/npc_memory_prepare.py,README,BACKLOG,SESSION_HANDOFF,GAME_SYSTEM_SUMMARY_KO;owned tmp/qt-f10 |
| API | Frozen EvidenceQuery(subject_id:str\|None=None,kind:EvidenceKind\|None=None,since:int=0,limit:int=MEMORY_CAPACITY). select_evidence(context:NpcMemoryContext,query:EvidenceQuery)->tuple[QuestEvidence,...] |
| validation/edges | Exact types;subject actor:/quest: namespace;kind accepted/completion_reported;since0..MAX_INT inclusive;limit0..2 exact int. Empty/foreign valid subject/no match/limit0→(). Bad query→ValueError NPC_MEMORY_QUERY;wrong selector input→GenerationError NPC_CONTEXT_INPUT |
| algorithm/wiring | Filter against context's explicit actor/quest subjects,kind and observed_at>=since;sort by(-observed_at,memory_id),slice limit. Default brief selects both records;mandatory evidence/constraints unchanged,queries never write/advance/query provider |
| examples | Actual accepted@2/report@11→default report then accepted;since11→report;since12→empty;kindaccepted→accept;limit1→report;foreign valid actor→empty |
| ownership/performance | Pure application T0 projection over≤2validated immutable entries;O(2),no DB/index/vector/tokenizer or ranking-score invention |
| acceptance/commands | Real saved-game query/order/filter/invalid-input/source-preservation and brief integration tests;affected previous adapter/context tests;Ruff/format/mypy/imports;documentation links. Reuse prior CORE/full/native/live evidence for unchanged inputs;no new live qualification claim |
| checkpoints/delivery | NOT_TRIGGERED:derived read-only helper under closed CP05;no new schedule/review/hold. Update3progress files;small completed task only,no automatic next work/publication |

Acceptance:[receipt](../reviews/QT-F10_EXECUTION_2026-10-14.md);29affected tests PASS;
Ruff/format/mypy143/imports3+1 PASS. No new provider call or CORE/save change.
