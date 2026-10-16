# Gemini Daily Limit Removal / Live Context Retest

Date:2026-10-14 | State:ACCEPTED | Executor:self;independent review NOT_RUN.
Director explicitly requests removal of the local daily limit and another real test.
This order supersedes only the daily caps in QT-F07 contracts;historical receipts remain frozen.
Classification:primary4 AI support;related6 local accounting.

| Field | Contract |
|---|---|
| goal/non_goals | Remove local daily call/token ceilings;retain usage accounting,minimum60s cross-process spacing,at most2HTTP attempts per explicit job,no automatic gameplay calls. No key rotation,billing/model change,game/save/schema/client changes |
| baseline/prerequisites | HEAD1ad22446d48c50b8b72a6d3af8de3c9d775134ea;dirty source hashes tmp/gemini-retest/entry.json;existing Python3.13.12/std-library Gemini adapter;QT-F08 source/CLI accepted |
| reads | ENGINEERING_RULES,guide,handoff,backlog,Korean progress,README/setup/template,QT-F07 provider contracts;generation_budget,GeminiDialogue,real NPC CLI and their tests |
| allowed edits | MODIFY src/adapters/generation_budget.py,gemini_dialogue.py;tests/adapters/test_generation_budget.py,test_gemini_dialogue.py;QT-F07_QUEST_DIALOGUE_CONTRACTS.md,README,BACKLOG,SESSION_HANDOFF,GAME_SYSTEM_SUMMARY_KO. NEW this order,docs/reviews/GEMINI_RETEST_2026-10-14.md;owned tmp/gemini-retest;existing shared profile through normal reserve/reconcile only |
| forbidden | Unrelated source/CORE/C#/pins/goldens/old witnesses/archives/credentials/dependencies;no ledger reset or old-receipt rewrite |
| public contract | Existing GenerationBudget.reserve/reconcile and Reservation signatures retained. Reservation.number positive exact int without2maximum. Ledger attempts/tokens/next_ms exact nonnegative ints;settled sorted unique1..attempts. Read limit16384bytes supports1440spaced attempts/day;old valid ledger accepted unchanged |
| behavior/algorithm | Exclusive lock/read authoritative ledger;enforce clock/spacing;reserve20000 accounting tokens and increment attempt without daily exhaustion;atomic publication;returned provider total reconciled exactly once. Unknown usage keeps reservation. UTC rollover retains next_ms. If second reservation fails after transient/timeout,preserve initial GenerationError as primary with sanitized reservation error as cause;never send without reservation |
| edges/examples | Existing2attempts/20452tokens at expired next_ms→reservation3/40452tokens;third unknown request after2unknown→3/60000,not exhaustion. Same instant or+59999→DEFERRED;corrupt/unavailable ledger fails before HTTP. InitialTIMEOUT+retry reservation unavailable→TIMEOUT with causeBUDGET_UNAVAILABLE;no secondHTTP |
| wiring/ownership | dialogue_prepare and npc_prepare both reuse the same budget adapter/defaultprofile;no new configuration/loading. Ledger owned local tooling,not game state |
| performance | Existing60s transport deadline and≤60s retry delay,≤180s job target plus process overhead;no busy wait. Small bounded ledger IO under existing nonblocking OS lock |
| baseline/verification | Existing error masking reproduced offline. Update old cap oracles explicitly for director-authorized semantics;add persistence/restart/spacing/unknown/reconcile/legacy cases and original-error regression;run adapters+NPC/unit dialogue+integration context,Ruff/format/mypy/import contracts. Actual fresh npc_prepare job outside sandbox,primary.env key only,public automated-test data,save bytes unchanged;candidate decode/hash/source check |
| acceptance/checkpoint | No daily ceilings,all affected checks pass;real result reported honestly,candidate NEEDS_REVIEW only. CP05 NOT_TRIGGERED:provider tooling policy explicitly changed by director,no authoritative gameplay/public save contract change |
| stop/delivery | Live provider failure preserves source/old content and is reported;no account administration/paid fallback/agents/commit/push. Synchronize3progress files and retain old failure evidence |

Acceptance:[actual receipt](../reviews/GEMINI_RETEST_2026-10-14.md);78affected tests/static checks PASS;
real source-bound NPC generation1attempt/19.716s/561tokens PASS,save unchanged,candidate NEEDS_REVIEW.
