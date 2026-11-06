# RS-OWN-002 — Claude Feedback Disposition

Primary 7, integration design and evidence. Related 2, 4, 5 and 6. Baseline `dc4e0de`.
Claude reviewed the supplied brief, linked documents and `world_conversation.py`. Its feedback states that it did not run checks and did not inspect the Driver, store, context projection, Unity bridge, tests or Actions. This follow-up checked those paths locally. [Work order](../work_orders/RS-OWN-002_CLAUDE_FEEDBACK.md)

| Finding | Disposition and evidence |
|---|---|
| Retrieval silently drops the last exchange | Confirmed helper defect. The original test fixture retrieved `speech:s8` as the latest item when `speech:s9` was eligible. The live caller already passed the latest exchange separately as the current utterance. Retrieval now accepts an explicit exclusion and the live caller passes that utterance ID. The existing test checks both cases and retains NPC isolation and budget coverage. [Domain](../../src/domain/world_conversation.py), [projection](../../src/orchestration/world_conversation_context.py), [test](../../tests/unit/test_world_conversation.py). |
| Transport timing attribution | Accepted correction. The old cProfile sample establishes where instrumented time was spent. Subtracting independent headless and GUI runs cannot assign the difference to SQLite or Tk. The wall-clock probe below measures stages in one journey. [Historical receipt](RS-PLAY-001I_EXECUTION_2026-11-05.md). |
| Revalidation grows with conversation history | Confirmed code property. `ConversationState.__post_init__` reconstructs every exchange and checks order and uniqueness on each new state. End-to-end latency impact is unmeasured. Measure it against realistic retained histories before changing validation or storage. [Domain](../../src/domain/world_conversation.py). |
| The 4096-exchange cap stops new speech | Confirmed behavior at the intentional prototype cap. The separate replay compaction and 1024 receipt retention provide finite recovery evidence. O2 needs an explicit capacity, retention and durable anchor policy before changing the cap. [Store](../../src/adapters/sqlite_store.py), [Driver](../../src/orchestration/turn.py), [ownership review](RS-OWN-001_DATA_OWNERSHIP_2026-11-05.md). |
| NPC privacy and cognition | Confirmed integration risks and missing capabilities. The context projection filters by the addressed NPC. `FieldSpec.consumers` is descriptive, while the application can read a full snapshot. The active profile contains fixed dispositions and lacks mutable belief/goal/rumor state. O2 owns the knowledge and visibility contracts. [Projection](../../src/orchestration/world_conversation_context.py), [ownership review](RS-OWN-001_DATA_OWNERSHIP_2026-11-05.md). |
| Option C lacks an authored dialogue comparison path | Confirmed campaign gap. The current world already has a direct supply offer and an AI-suggested supply offer. Both confirmations call `confirm_supply` with a typed `SupplyAction`. `NpcReply` only records speech and validates the proposed operation against the NPC context. O1 can reuse this common endpoint. Start with an authored state-aware choice and add a separate command schema only if a durable authored conversation effect requires one. [Client](../../src/app/world_client.py), [reply admission](../../src/orchestration/world_conversation.py). |
| Unity bridge and bundled Python | The active bridge uses the earlier `ClientWorker`. The current world uses `WorldWorker`. A committed-state projection is a suitable first bridge experiment after the data contract. Packaging is a separate release qualification. [Bridge](../../src/app/engine_bridge.py), [world worker](../../src/app/world_worker.py). |
| Evidence and lineage | Confirmed documentation gap. PR40 final CI was already recorded in its PR body, while the checked-in report still said pending. The report and trackers now include both runs. Git ancestor checks succeeded for `0d954c7` → `421de09` → `dc4e0de`. The previous private witnesses remain historical evidence with limited external reproducibility. The new measurement script and command are checked in. [PR39](https://github.com/wkdtlgns99-cell/Reverie-Saga/pull/39), [PR40](https://github.com/wkdtlgns99-cell/Reverie-Saga/pull/40). |
| Billing and provider qualification | Commercial access/payment remains on hold. Claude's pricing suggestion requires a separate decision. The earlier Gemini samples used different scenarios. Compare identical Korean scenarios with stage timings, quality ratings and p50/p95 before selecting a provider or local runtime. [Product direction](../PRODUCT_DIRECTION_2026-11-05.md). |

## Stage timing on the current workstation

Run from the repository root in PowerShell using the qualified environment.

```powershell
$env:PYTHONPATH = "$PWD/src"
$env:PYTHONUTF8 = '1'
$env:PYTHONHASHSEED = '0'
.\.venv\Scripts\python.exe tools/measure_world_transport.py
```

The probe drives the actual Tk worker and SQLite on the fixed carriage and sea route. It withdraws the desktop window, exercises the widget callbacks, starts after initial load and stops at arrival. Each invocation uses a fresh temporary save. It checks 35 simulation calls and the expected final tick of 93851. Timer wrappers call the original methods and restore them afterwards. No profiler or provider call participates. [Probe](../../tools/measure_world_transport.py)

| Run | Total | Simulation | Commit preparation | Durable persistence | SQLite execute subset | Tk render callback |
|---|---:|---:|---:|---:|---:|---:|
| First | 23.5456s | 20.1737s | 0.6528s | 1.9080s | 0.2660s | 0.0538s |
| Second | 23.5873s | 20.1577s | 0.6622s | 1.9475s | 0.2785s | 0.0506s |
| Final tool | 24.1402s | 20.7939s | 0.6604s | 1.9669s | 0.2902s | 0.0502s |

The first two runs used Tkinter's delay-only `after` wrapper. The final tool calls the same
Tcl delay directly to satisfy the type stub. Simulation accounted for about 85–86% of measured
elapsed time in this setup. The historical headless witness restored the checkpoint without a
durable commit port. Its total remains a separate measurement under different conditions.

Commit preparation covers candidate preparation and validation. Durable persistence includes application encoding/checks and SQLite work. The measured `_execute` calls are a subset of that stage and must not be added to the total. Tk rendering here measures callback execution with the window withdrawn. The earlier 39.539s visible-window result remains an observed target miss, and these runs cannot isolate what made that earlier run slower. The 30s qualification remains open.

## Next bounded implementation proposal

**O1 first.** Use one existing supply task and one authored NPC offer in an isolated profile. Have the player confirm it through the existing `SupplyAction` admission and COMMIT path. Give the authored route every clue the task needs. Prove progression with provider access disabled, with controlled AI suggestions, and when generation fails mid-conversation. Start equivalent confirmed actions from identical gameplay inputs at the same tick and compare the command's objective component effects, including supply, inventory and related reputation. Separately verify expected dialogue and time changes and replay each path against its own history. Full CORE hashes can differ because dialogue, time and provenance are authoritative records. Scope the provider-disabled check to access and request behavior. A provider-module-free distribution requires its own boundary because the current worker imports the development adapter at startup.

Verify unauthorized NPC role proposals, rejection with no state/time change, pre/post-COMMIT failure and exact retry, saved authored prerequisites, and old-profile byte preservation. Record tests and results in the repository. A static prerequisite coverage check becomes useful when the authored quest format declares those facts explicitly. Scope the proof to the supply task first. Social actions already have their own typed command and can be added when an authored scenario requires them.

**O2 second.** Specify what an NPC observed or heard, who can retrieve it, which records survive retention, and how branch/save boundaries are enforced. Keep objective facts distinct from player claims. Then run **O3**, the two-NPC slice where a false claim stays a claim and the quest completes with the provider absent or failing. A read-only Unity projection can be designed after the data interface is defined. Further bridge work and platform packaging follow separate qualification. Stage-timed transport optimization and matched Korean latency comparisons are separate measurement tasks. Add Qdrant only after measured retrieval gaps remain after structured lookups.

## Verification

- The expanded retrieval test reproduced the missing latest exchange before the repair. The
  focused world conversation, transport, social, durable turn and read view set passed 143 tests
  in 31.82s after the repair.
- Both lint configurations, scoped formatting, strict types and both import contracts passed.
  The developer probe also passed separate strict typing and ran to completion.
- The engineering document guards passed 11 tests in 1.73s. The patch has no whitespace errors.
- PR40 Actions logs and Git ancestry were rechecked directly. This follow-up's final publication
  evidence will be recorded on its PR after CI and merge.
