# Gemini Daily Limit Removal / Real NPC Context Retest

Date:2026-10-14 | Acceptance:PASS for requested policy change and actual NPC-context generation.
Execution/self-review;independent review NOT_RUN.
[Order](../work_orders/GEMINI_DAILY_LIMIT_REMOVAL.md). Primary4 AI support;related6 usage accounting.

## Changed Behavior

Director explicitly removed the local daily limitation. Both local daily call and token ceilings
are removed;at most2HTTP requests per explicit job and minimum60s cross-process spacing remain.
The same durable profile continues without reset. Unknown usage retains conservative accounting;
usage reconciliation remains idempotent. Reservation numbers now admit any positive exact integer.
The bounded ledger read grows4KiB→16KiB to fit a full day of1/minute settled accounting.
If a retry reservation fails,the initial timeout/transient error remains primary with the
local reservation error as its cause. No unauthorized request can escape failed reservation.

## Verification

- Before change:7expected failures/18passes in affected adapter tests;third reservations blocked
  and first provider error replaced by reservation failure. Oracles intentionally changed for the
  director-authorized policy;old frozen review witnesses were not rewritten.
- Final:78affected adapter/dialogue/NPC unit/integration cases PASS7.75s;
  tmp/gemini-retest/final.xml. Real spawned processes prove third/fourth requests retain accounting,
  lock contention and spacing. Tests also cover a legacy exhausted profile without reset,
  unknown usage>40000tokens,once-only settlement,1440settlements/day and cross-day spacing,
  original-error preservation and a maximum of2HTTP requests per explicit job.
- Ruff shared+quality and four-file format PASS;strict mypy132files PASS;
  import contracts3shared+1runtime KEPT. Initial new-test missing annotation was fixed;
  first import command lacked PYTHONPATH and was rerun with src,not a dependency failure.
- No CORE/client/Unity changes;full regression/native/build NOT_RUN for this adapter-only scope.
  Existing gameplay evidence is retained,not relabeled as new qualification.

## Actual Gemini Request

Used the primary key from ignored.env only;no credential output,spare rotation,ledger reset,
paid fallback,model switch or account administration. The live job ran outside the network
sandbox after an unauthenticated probe distinguished sandbox DNS failure from actual reachability.

Fresh automated-test-only quest source at tick9/stage2 exports only NPC-known acceptance/favor0,
not unreported enemy defeat. Actual app.npc_prepare CLI rechecks source and publishes a fresh
NEEDS_REVIEW envelope. Sanitized result:tmp/gemini-retest/live-result.json.

| Observation | Actual result |
|---|---|
| status/exit | GENERATED_NEEDS_REVIEW/0 |
| model | gemini-3.5-flash-lite |
| latency/attempts |19.716seconds/1HTTP attempt |
| prompt/output/total tokens |309/252/561;thought usage absent/null |
| context/brief |565/1346UTF8bytes |
| source |Original diagnostic save bytes unchanged |
| candidate |Four-intent local validation/hash passed;fresh source binding verified |
| raw candidate SHA256 |fff005fcefd972c6ad360adc05c9013351f105b47ad33db39d02ea463637ec18 |
| output |tmp/gemini-retest/live-c75882ce0e6049b798fdad84c0353b54/npc-preparation.json |
| accounting after call |attempts3,settled[1,3],tokens21013;old uncertain20000 retained |

The original QT-F08 failure receipt remains unchanged. This new success qualifies real
NPC-context generation;it does not recover the historical first timeout/transient details.
Candidate text remains subject to editorial/director review,not installed production dialogue.
No full NPC memory,vector retrieval,gameplay-time LLM calls or live-AI Unity demonstration is claimed.
Account billing tier/remaining provider quota remain UNVERIFIED;the program did not change them.
