# Claude Request — Finish All Remaining V3 Inspection

Please continue your two partial reviews and finish ALL remaining blocks below in this review.
Do not stop after one block or ask me to choose the next block. If access, time or context prevents
completion, preserve a file/range coverage ledger and identify the exact remainder;do not declare
the whole review passed. This is independent review,not implementation or a new checkpoint.

## Obtain and pin the current source

- Repository:https://github.com/wkdtlgns99-cell/Reverie-Saga
- Branch:codex/open-work-closure-20261014
- Source:https://github.com/wkdtlgns99-cell/Reverie-Saga/tree/codex/open-work-closure-20261014
- Draft PR:https://github.com/wkdtlgns99-cell/Reverie-Saga/pull/8
- Full comparison base:1ad22446d48c50b8b72a6d3af8de3c9d775134ea.
- Previous reviewed snapshot:3159c92251afc61cd3d30e5156020adac4937c5d.

Fetch the branch/PR head and record its full SHA before reading. Pin that revision for all files,
diffs and tests. Review both base-to-head history and the incremental patch since3159c92.
The delivery message supplies the newly published SHA;verify equality. If GitHub access fails,
report the exact inaccessible paths and request the current source archive. Do not substitute
the old OPEN_WORK_V3_3159c92_2026-10-15.zip:it excludes the F1repair and both review dispositions.
No new ZIP is supplied by this request. A GitHub source archive of the pinned head is sufficient
for current tracked inputs;ignored local evidence is a separate availability limit.

Read first:

- `AGENTS.md`, `ENGINEERING_RULES.md`, `BACKLOG.md`, `SESSION_HANDOFF.md`.
- `docs/MASTER_GAME_ARCHITECTURE.md`.
- `docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md`.
- `docs/reviews/OPEN_WORK_REVIEW_START_HERE_2026-10-15.md`.
- `docs/reviews/OPEN_WORK_INDEPENDENT_REVIEW_REQUEST_2026-10-14.md` (old snapshot section is historical).
- `docs/reviews/OPEN_WORK_V3_FEEDBACK_2026-10-15.txt` and `OPEN_WORK_V3_DISPOSITIONS_2026-10-15.md`.
- `docs/reviews/OPEN_WORK_V3_CONTINUATION_FEEDBACK_2026-10-15.txt` and
  `OPEN_WORK_V3_CONTINUATION_DISPOSITIONS_2026-10-15.md`.
- `docs/work_orders/OPEN_WORK_V3_FOLLOWUP_2026-10-15.md`.

## Current corrections and qualifications

F1is repaired ONLY in `tests/integration/test_save_slots.py::test_link_count_metadata_rejects_alias`:
provide st_file_attributes to os.stat_result only when the real stat exposes it. Preserve Windows
metadata,force only link count2,and require the exact hardlink INVALID_PATH diagnostic plus real
save reopen at tick0. Simply omitting extras fails Windows3.13with attrs=None before the guard.
Verify the actual conditional repair on Linux3.13;do not reapply your unconditional suggestion.
Native Windows affected module29PASS/final target1PASS,both Ruff and strict mypy157PASS recorded.
No production source changed in this follow-up. Prior full1675PASS applies to3159c92,not automatically
to this later test patch. Your prior Linux run1674PASS/1FAIL also applies to the old snapshot.

F3was reproduced offline using the actual budget lock and an isolated ledger:successful stub
response followed by reconcile-lock failure returns GENERATION_BUDGET_UNAVAILABLE and retains
the conservative20000token reservation. APIcalls0. This is a confirmed availability limitation,
not under-accounting;assess severity/contract without silently changing retry/publication policy.
F2typed errors remain a maintenance note. For F4account for the current64KiB admitted catalog cap
before claiming a reachable1MiBframe overflow. F5startup latency remains unmeasured. F6preset
pins are development consistency checks. CP03missing-role and directory-fsync concerns remain
hypotheses until a contract and reproduction establish a defect.

## A. Finish authoritative execution and engine inspection

Read complete bodies,not just earlier line prefixes:

- ALL tracked Python files in `src/engines/`, `src/orchestration/`, `src/domain/` and `src/contracts/`.
  In particular `engines/skeleton.py`, `trial.py`, `encounter.py`, the remainder of `watch.py`;
  `orchestration/turn.py`, `scheduler.py`, `read_views.py`, `persistence.py`, `replay.py`, `events.py`,
  `rng.py`, `serialization.py` and every engine reducer/codec/checkpoint policy.
- `src/app/feature_registry.py`, `headless.py`, `npc_memory.py`, `scenarios.py`, `quest.py`,
  `quest_definition.py`, `quest_registry.py`, `watch.py`, `watch_registry.py`, `trial.py`,
  `trial_registry.py`, `encounter.py`, `encounter_registry.py`.
- `tests/integration/test_core_slice.py`, `test_event_turn.py`, `test_registered_state.py`,
  `test_skeleton.py`, `test_watch.py`, `test_trial.py`, `test_encounter.py`, `test_quest.py`,
  `test_npc_memory.py`, `test_scenarios.py`, `test_cp03_repairs.py`.
- ALL `tests/replay/*.py`, `tests/replay/fixtures/*.json`;relevant `tests/unit/*_fixtures.py` and
  `test_schedule.py`, `test_read_views.py`, `test_events.py`, `test_rng_vectors.py`,
  `test_registered_io.py`, `test_save_codec.py` and per-engine unit tests.

Trace registration through actual callers. Verify deterministic ordering/RNG/hash/replay,
phase barriers and COMMIT-only mutation,read-view lifetime,isolation,scenario binding,quest
reward exactly once,NPC observed-versus-reported evidence,and rejection/retry/recovery behavior.
Distinguish generic consumers from consumers contractually required to expose scenario roles.

## B. Finish dialogue preparation,approval and retained-content inspection

- `src/app/npc_prepare.py`, `dialogue_prepare.py`, ALL `npc_memory_*.py` and `npc_dialogue_*.py`.
- `src/adapters/quest_dialogue.py`, `narrative_catalog.py`, `gemini_dialogue.py`,
  `gemini_transport.py`, `generation_budget.py`;`src/contracts/dialogue.py`, `npc_context.py`,
  `npc_memory.py`, `narratives.py` and the actual source/save bindings they consume.
- ALL tracked `content/dialogue/harbor-memory-v1.*`, plus `content/narratives.json` and
  `content/narratives.manifest.json` where consumed.
- ALL `tests/adapters/*.py`;`tests/integration/test_npc_context.py`, `test_npc_memory*.py`,
  `test_npc_dialogue_*.py`;`tests/unit/test_dialogue.py`, `test_npc_context.py`,
  `test_npc_memory.py`, `test_narrative_catalog.py`.

Trace saved facts → filtered evidence → brief/plan → provider request → strict candidate → review
→ explicit human approval → atomic compiled catalog → live client delivery and restored save.
Check stale-source/replacement races,exact schema/type rejection,lineage/hash binding,approval
semantics,no automatic import/rotation,secret boundaries,cancellation and conservative accounting.
Four actual human-approved lines are recorded;review cannot invent or replace that approval.
Normal gameplay/replay must not call the LLM. Use offline provider doubles;no live key is supplied.

## C. Finish durable storage,client and Unity inspection

- `src/app/durable.py`, `client_session.py`, `client_worker.py`, `engine_bridge.py`, `client.py`,
  `client_text.py`, `engine_project.py`;`src/adapters/sqlite_store.py`, `save_slots.py` in full;
  `src/contracts/client.py`, `persistence.py`, `state_io.py` and corresponding codecs.
- ALL C#source in `clients/unity/Assets/Reverie/Scripts/`,including `LiveVerification.cs`,
  `Wire.Generated.cs`, `CatalogPin.Generated.cs`, `BrainConnection.cs`, FULL `PlayRoom.cs`;
  `clients/unity/Assets/Reverie/Editor/PlaytestBuild.cs`.
- `clients/unity/README.md`, `ProjectSettings/ProjectVersion.txt`, `Packages/manifest.json`,
  `Packages/packages-lock.json`;follow relevant scene/source/config references.
- `tests/integration/test_client_reconciliation.py`, `test_client.py`, `test_memory_client_route.py`,
  `test_engine_bridge.py`, `test_durable_turn.py`, `test_sqlite_recovery.py`, `test_save_slots.py`;
  `tests/unit/test_client_text.py` and durable/replay/codec fixtures.
- `docs/work_orders/RS-STRUCT-001_RECONCILIATION_2026-10-14.md` and
  `docs/reviews/RS-STRUCT-001_EXECUTION_2026-10-14.md`.

Check actual ordinary startup/memory registration,wire bounds/typing,readback truth after COMMIT,
projection failure,changed-attachment history,reconnect/load pins,cleanup resource identity,
close failure and retry,uncertain persistence,and development-hook exclusion in release builds.
Read regression assertions,not just names or green summaries. Trace CP03selected wait narration
through its actual use. Static C#reading/Python execution do not constitute native Unity proof.

## D. Independently verify historical repairs from original inputs

Read these exact inputs,then map EVERY finding to current symbols and regression assertions:

- `docs/reviews/RS-REVIEW-CP03_FEEDBACK.txt`, `RS-REVIEW-CP03_REPAIR_INPUTS.json`,
  `RS-REVIEW-CP03_DISPOSITIONS_2026-10-13.md`, `RS-REVIEW-CP03_REQUEST.md`.
- `docs/work_orders/RS-REVIEW-CP03_REPAIR.md`.
- `docs/reviews/RS-REVIEW-CP05_CONTRACT_FEEDBACK.txt`, `RS-REVIEW-CP05_CONTRACT_INPUTS.json`,
  `RS-REVIEW-CP05_CONTRACT_DISPOSITIONS.md`, `RS-REVIEW-CP05_CONTRACT_REQUEST.md`.
- `docs/reviews/RS-REVIEW-CP05_INTEGRATION_FEEDBACK.txt`, `RS-REVIEW-CP05_INTEGRATION_INPUTS.json`,
  `RS-REVIEW-CP05_INTEGRATION_REPAIR_INPUTS.json`,
  `RS-REVIEW-CP05_INTEGRATION_DISPOSITIONS_2026-10-14.md`, `RS-REVIEW-CP05_INTEGRATION_REQUEST.md`.
- `docs/work_orders/RS-REVIEW-CP05_INTEGRATION_REPAIR.md`, `QT-F07_QUEST_DIALOGUE.md`,
  `QT-F07_QUEST_DIALOGUE_CONTRACTS.md`;follow named implementation/acceptance evidence.

Include CP03F1–F5,CP05H1/H2/M1–M7/low comments and integrationP2-1/P2-2/P3dispositions.
Inspect full tests and independently assess their expectations. Explain accepted intentional net
quest transitions and scenario roles. Do not replace original feedback with disposition summaries.

## E. Cleanup and evidence-retirement limits

Read `docs/work_orders/LOCAL_FILE_CLEANUP_2026-10-15.md`,
`docs/reviews/LOCAL_FILE_CLEANUP_2026-10-15.md` and its `.json`,plus closure order/ledger.
Assess retained unique checkpoint ZIPs,CP02rights originals,GOV02/GOV03native evidence,legacy
Python copy and17restricted caches. Approve retirement only with exact recoverability proof
for necessary inputs/findings/provenance/acceptance. Git cannot reproduce ignored local archives,
ACLs,provider originals or private saves by itself. Mark unavailable evidence explicitly;no
blanket deletion/ownership takeover recommendation and no claim of inspecting my local disk.

## Execution and final report

Use the repository README verification commands and current pinned versions. Record actual
OS/Python/Tk/tool versions,hash-lock enforcement,commands,collected/passed/failed/errors/skips/
exclusions and JUnit evidence. Run the corrected save-slot test on Linux3.13and relevant regressions;
run full tests/static gates if available. Do not suppress failures,edit original sources or weaken
the lock to present a qualified pass. If an alternative environment is necessary,identify it as
an exploratory run and retain the qualified-platform gap. Reusing prior unchanged evidence is
allowed only with its exact revision/platform and a clear distinction from execution this review.
Inspect current-head CI directly if available;otherwise label it unverified by you.

Return:

1. Exact reviewed SHA/base and verdict,separating defect severity from coverage/environment gaps.
2. A coverage ledger for A–E:files/ranges read,tests whose assertions were read,tests actually run,
   unavailable inputs and exact remainder. Reconcile BOTH prior review coverage reports.
3. Each finding:ID/priority,path:line,contract,trigger,expected/actual,reproducer and bounded repair.
   Separate confirmed defects,intentional behavior,maintenance and unverified hypotheses.
4. A finding-by-finding CP03/CP05repair matrix and current V3F1–F6dispositions.
5. Actual test/static results and honest native/live/platform/hash-closure limits.
6. Remaining blockers or an explicit statement that all requested source inspection is complete.

Do not call a partial block review a full PASS. Explain whether any remaining limit blocks
source review acceptance or only later platform/release qualification. CP01–05remain closed;
CP06release remains held. This request grants no content/rights/billing/merge/release approval.
Proceed through all five blocks without asking which one to inspect next.
