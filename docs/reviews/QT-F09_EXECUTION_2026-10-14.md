# QT-F09 — Persisted NPC Evidence Acceptance

Date:2026-10-14 | Acceptance:LOCAL_IMPLEMENTATION_ACCEPTED;LIVE_MEMORY_CONTEXT_GENERATION PASS.
Execution/self-review;independent memory review NOT_RUN.
[Order](../work_orders/QT-F09_NPC_EVIDENCE_MEMORY.md). Primary2;related3/6/4/7.

## Behavior and Wiring

Fresh opt-in ClientSession(npc_memory=True) uses quest.harbor-memory-v1;ordinary quest/legacy
sessions retain their original bundle/pins. One additional12th CORE component stores two typed,
monotonic evidence slots. Registered quest.memory engine consumes only QuestAccepted/QuestCompleted
at POST_TICK. Existing staging/COMMIT/SQLite ownership persists quest and memory atomically.
Source event IDs/ticks survive save/load/resume;repeat talk/exact retry creates no new memory.

Independent scenario expectations:acceptance conversation at tick2→observed acceptance;
enemy defeat tick9→no extra NPC memory;completion report tick11→reported completion.
The NPC did not witness that defeat. No relationship/personality/5level/anchor/forgetting/vector
system is claimed. This is bounded level1conversation evidence with fixed priority128/capacity2.
No existing save migration,game objective/reward change,UI/C#/wire/art/camera/asset change.

Read-only read_memory and actual npc_memory_prepare CLI pin source identity and hash,include
ordered evidence and recheck freshness after generation. A changed world rejects publication;
prior committed truth is not rolled back. Output is fresh CONTEXT_ONLY/NEEDS_REVIEW only.
Provider errors/raw validation reuse accepted boundaries. Ordinary turns perform no LLM calls.
Metadata identifies reconstructible source propositions;hashes are not signed proof against a
user rewriting a complete local save. No historical-source authentication claim is made.

## Actual Verification and Repairs

- New focused tests:39PASS10.90s (tmp/qt-f09/focus2.xml),including exact types/order/frozen
  records,expired/observed read views,append-only composition,missing/mismatched consumer roles,
  real durable stages,retry/repeat/save/load/resume,replay,checkpoint contradictions/forged
  source IDs,failed commit preserving quest+memory together,legacy rejection and network-forbidden
  standalone offline CLI. Provider IO fakes only test source changes/output/failure boundaries.
- First focus:38PASS/1test harness failure;HeadlessSession has driver.submit,not submit.
  Corrected the test to the actual API;production behavior was not changed for this failure.
- Full suite:1525PASS/2FAIL361.15s (tmp/qt-f09/full.xml/full.log). The two newly added governance
  probes correctly found forbidden memory↔quest engine imports,but their final test assertion
  mistakenly expected the older skeleton/trial engine pair. Corrected exact pair expectations;
  two affected probes then PASS1.35s (tmp/qt-f09/guard-repair.xml). Retain the original failed
  run;there was no second all-green full invocation. Qualification reuses the1525unchanged
  passing cases plus2corrected passing cases;no remaining observed failure or suppression.
- Final Ruff(shared/selective quality),10affected formatted files,strict mypy141files PASS;
  import contracts3shared+1runtime KEPT. New engine is added to the existing independence gate,
  with real forward/reverse forbidden-import probes. No gate weakened/new dependency installed.
- Native Unity/build NOT_RUN:default client/game contracts unchanged;new memory is enabled
  through the Python boundary API. This is not a live-memory Unity demonstration.

## Real Gemini Test

New public automated-test-only source at tick11 contains acceptance@2/report@11. Primary.env
key only;no credential output/key rotation/model switch/ledger reset/billing administration.
Actual app.npc_memory_prepare subprocess outside restricted network sandbox:

| Observation | Actual |
|---|---|
| status/exit |GENERATED_NEEDS_REVIEW/0 |
| model |gemini-3.5-flash-lite |
| attempts/elapsed |1/2.059seconds |
| prompt/output/total tokens |686/253/939;thought usage absent/null |
| context/brief UTF8 |1415/2104bytes |
| source integrity |original diagnostic save bytes unchanged |
| context SHA256 |3b0c13dc5c878d69f6f06fdbae7396b350ac7319b82aefff1bcc71543e27e1c5 |
| raw candidate SHA256 |b8642fdbd8f49f0167d84ed34a5dcbc2e7b70effd00e19882ba81b9d4070fb88 |
| receipt |tmp/qt-f09/live-result.json |
| fresh output |tmp/qt-f09/live-11d4b31e305a4cffac5ee87bed74c2e0/npc-memory-preparation.json |

Four-intent raw candidate/schema/hash/source binding validation PASS. Editorial wording remains
NEEDS_REVIEW;not approved or installed into a production game. Provider generation acceptance is
not semantic-proof of every sentence. Free project/account quotas remain unverified as before.
Shared accounting after call:attempts4,settled[1,3,4],tokens21952;old uncertain20000 retained.

CP05 first quest contract/integration gate remains DONE;this extension does not claim a fresh
Claude memory review or silently add a scheduled checkpoint. CP06 release gate remains held.
Baseline/allowed-path/frozen-archive/document checks are recorded in tmp/qt-f09/checks.json.
No agents/publication/remote administration/dependency/asset production was performed.
