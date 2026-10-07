# RS-REVIEW-GPT-001 — Structural Plan Fact Check

Date:2026-10-07 (Asia/Seoul) | Triage:RECORDED | Implementation:NOT_AUTHORIZED | Review:Sol self-review,not Claude
Input:director-pasted general-GPT structural improvement plan;source SHA256 `605f7a674aa4cbef1b119bd8549efccb7cdf9b8e9728aefa098074d06d189377`.
Original local attachment:`C:/Users/User/.codex/attachments/64d92c5b-de4a-4773-8056-eccd7353bc93/붙여넣은 텍스트.txt`. This file preserves its claim inventory/dispositions,not a second rulebook or executable work order.
Baseline:clean main at `99786af93eb4efbc9940110ef568b7156e8b16bb`;174 nonignored files fingerprinted before edits. Scope:inspect actual sources/tests/specs,read remote state,record justified future work. No implementation,remote setting changes,workflow reruns,dependency changes,commit or push.

## Overall verdict

Sound direction,not ten demonstrated bugs. Distinguish verified omissions,maintenance risks,existing safeguards and future-product requirements. Do not adopt the proposed priority order wholesale or replace the deterministic Brain.
The most immediate confirmed problem is now a failing remote CI run,followed by absent main protection. This is new read-only evidence;previous local1242PASS and publication success remain valid historical facts,not remote success.

## Claim-by-claim disposition

| Input section | Verdict | Actual evidence / bounded disposition |
|---|---|---|
| P1 CI/main protection | CONFIRMED gap | Workflow exists,but remote main reports protected=false/enforcement off/empty required contexts;rulesets returned []. Latest inspected push run failed. Fix actual CI before configuring required checks;repository administration needs explicit authorization |
| P2 orchestration splits | CONFIRMED size/responsibilities;PROPOSAL,not defect proof | encounter898/turn876/serialization763/watch723 lines. Encounter/watch contain views/adapters/codecs/reducers/patch routing/admission/checkpoint/presentation;RegisteredStateIO combines registry/encoding/effect checks. Driver `_submit` already delegates to `_check_command/_admit/_simulate/_prepare_commit/_commit/_present` after QUALITY-05. No repeat of the old monolithic-function claim;no measured AI-error/context improvement |
| P3 reduce boilerplate | PARTIAL;reasonable conditional proposal | encounter/watch `_View` lifetime/write-observation scaffolding repeats;validation helpers already exist. Record types,range/identity checks and reducer behavior differ. Prove semantic equivalence before extracting small typed composition helpers;no universal BaseEngine/reflection framework |
| P4 GOV-03 coverage | CORRECT deferred status;scope correction required | Existing G07 order is for six golden nodes and20 registered public engine methods,not comprehensive reducer/codec/persistence body coverage. Those other paths have tests but are not G07's required inventory. Keep GOV-03 deferred;extending its gate requires a separately approved contract/inventory,not silent scope growth |
| P5 invariant/property tests | VALID principle;largely ALREADY_PRESENT | Concrete tests below cover rejection,atomic abort,retry,durability/recovery,save/load,replay/views/events. Fresh selected19 cases PASS. This is not missing-all-invariants evidence or exhaustive property coverage. Gap-map before adding tests;no Hypothesis dependency implied |
| P6 edit scope | ALREADY_PRESENT | AGENTS,canonical quality loop and SOL_CODING_WORK_ORDER require reads/exact allowed/new/forbidden paths,independent examples and protected formats. A new duplicate rules file is unnecessary. Status may record IN_PROGRESS/errors before acceptance;only DONE must wait for evidence |
| P7 broader format/lint | CONFIRMED format gap;lint qualification | Shared `ruff check src tests` is already repository-wide. Extra E501/PT011 are selective;CI formatter names9 files versus11 in README/local acceptance,omitting client_text and its unit tests. Read-only whole-tree format check:67 would change/29 already formatted. Formatting diagnostics are not67 bugs;normalize separately before expanding enforcement |
| P8 performance baselines | VALID future requirement,not measured bottleneck | BLOCK_06 A13/BLOCK_08 already define benchmarks/bounds and soft wall-time trends. No executable benchmark/performance-named path found in the inspected tree. Future measured Brain scenarios are useful at scale;do not invent current capacity/latency or hard noisy timing gates |
| P9 schema-driven content | ALREADY_DESIGNED/future implementation | MASTER4.3 and BLOCK_05 A10 require typed/versioned/validated approved content. QT-F02/general importer remain deferred;the representative slice intentionally pins targets. Avoid per-item Python rules and unvalidated JSON;use existing contract decisions rather than a second content pipeline |
| P10 generic Driver | ALREADY_FOLLOWED/intended invariant | Driver invokes registered contracts/routing rather than poison/quest/economy-specific rules. QUALITY-05 already split orchestration and cached static metadata. Scalability is not established:Driver.__init__ still requires one selected FeatureBundle;future composition needs a settled aggregate pin/schema contract,not only file splitting |

## Remote CI evidence — concrete follow-up,not speculation

- [Main branch API](https://api.github.com/repos/wkdtlgns99-cell/Reverie-Saga/branches/main):SHA99786af...,protected=false,protection.enabled=false,required_status_checks.enforcement_level=off,contexts=[]/checks=[]. [Rulesets](https://api.github.com/repos/wkdtlgns99-cell/Reverie-Saga/rulesets):[]. Direct protection endpoint returned403 (integration lacks administration);that response alone would not prove absence,but the branch metadata independently exposes the disabled state. Effective-branch-rules URL was rejected by the connector;no result inferred.
- [Native checks run37578176533](https://github.com/wkdtlgns99-cell/Reverie-Saga/actions/runs/37578176533),attempt1,push main/SHA99786af...,completed failure. [Job112651651747](https://github.com/wkdtlgns99-cell/Reverie-Saga/actions/runs/37578176533/job/112651651747):installation,lint,scoped format,types and both import checks success;full regression failed.
- Job log:1065passed/177errors169.59s,exit1. Setup trace attempts `mkdir(parents=False)` at `.pytest_cache/ci-run` and raises FileNotFoundError/WinError3. This is not177 independently demonstrated gameplay bugs or a Tk failure diagnosis.
- Workflow uses `pytest -q --basetemp .pytest_cache/ci-run` without first establishing that ignored parent directory. Pinned pytest9.1.1 `_pytest/tmpdir.py:getbasetemp` calls `basetemp.mkdir(mode=0o700)` without parents. Local cached runs had the parent;fresh checkout need not.
- Diagnostic reproducer,with a verified-absent unique parent: `.venv/Scripts/python.exe -m pytest -q tests/governance/test_dependency_contracts.py -k allowed-dag --basetemp .pytest_cache/gpt-structural-probe-7e01a435/base` → exit1,78deselected/1setup error0.06s,same WinError3/parents=False. No preexisting temporary directory removed.
- Later repair candidates:explicitly create the owned parent before invoking pytest,or choose a unique owned basetemp beneath an existing runner temp directory. Verify on a clean environment and a real complete Actions run;do not skip tmp_path/GUI/dependency tests or weaken assertions. Fix is NOT_APPLIED and complete remote acceptance remains FAIL.

## Existing invariant evidence / precise limits

These are inspected concrete test bodies,not a claim of exhaustive coverage. Source/test names are stable lookup keys;read surrounding fixtures/contracts before a repair.

| Proposed invariant | Existing witness / remaining qualification |
|---|---|
| 1 rejected command unchanged | integration/test_trial.py:test_invalid_command_no_time and test_invalid_json_schema_actor_and_shape compare core/protocol before/after |
| 2 failed command atomic | integration/test_event_turn.py:test_fault_after_real_hp_staging,test_abort_restores_queue check unchanged core/protocol/facts and expired aliases |
| 3 same seed/pins/trace | replay/test_encounter.py:test_encounter_fresh_sessions_and_registry_order;test_contamination.py repeated sessions/cache/world/hashseed checks. Not qualification of the future generated-content importer |
| 4 retry exactly once | integration/test_durable_turn.py:test_disk_precedes_head_and_no_retry_write checks no duplicate facts/diff/persist/replay step |
| 5 save/load state | integration/test_save_slots.py:test_export_previous_generation_and_atomic_load;integration/test_core_slice.py combined path |
| 6 replay facts/events/RNG/hash | replay/test_registered_replay.py:test_registered_roundtrip_trace compares independent fixture steps;test_encounter/test_watch corruption cases;unit/test_rng_vectors.py independent vectors |
| 7 malformed input no RNG/events | Trial rejection tests compare complete snapshots/protocol and empty publications;unit RNG isolation/exhaustion tests. Arbitrary future RNG-consuming feature rejection needs specific instrumentation/tests;do not claim universal proof |
| 8 commit failure atomic | durable_turn.py:test_confirmed_rollback_atomic_after_real_wake and test_uncertain_commit_proves_old_or_new_without_reevaluation. Uncertain commit can prove old OR new;forcing old state on every reported failure would violate durability semantics |
| 9 presenter cannot mutate CORE | durable_turn.py:test_postcommit_real_presentation_failure verifies committed durable state survives failure/retry/resume. The command already committed;do not incorrectly require the entire command to be rolled back |
| 10 canonical round-trip | unit/test_events.py:test_pending_roundtrip_and_leaf_hash and replay/test_registered_replay.py:test_registered_roundtrip_trace |
| 11 registration independence | Existing encounter test reverses adapters/fields/events/codecs/bindings/routes and preserves pins/replay. Adding an unrelated feature is different:extra CORE fields/package pins may change the global hash by design,and multi-bundle runtime is currently restricted. Compare existing-feature projections/RNG addresses under settled contracts,not unconditional global-hash equality |
| 12 read-only views | unit/test_read_views.py:test_nested_mutation_preserves_backing,test_expired_aliases validate denied writes,unchanged backing and lifetime |
| 13 load branch | integration/test_save_slots.py:test_export_previous_generation_and_atomic_load uses a new working path/original retained;client tests cover attachment/retry/display reset. Complete original-file byte preservation is a possible targeted strengthening,not inferred from existence alone |
| 14 delayed-event order | unit/test_events.py:test_queue_order compares independent ordering vectors and actual bus delivery;integration/test_event_turn.py barrier/cascade tests |

Fresh bounded check:19PASS4.37s,exit0,with PYTHONPATH=src and previously absent basetemp below existing .pytest_cache. Exact command:

```text
.venv/Scripts/python.exe -m pytest -q tests/integration/test_trial.py::test_invalid_command_no_time tests/integration/test_event_turn.py::test_fault_after_real_hp_staging tests/integration/test_durable_turn.py::test_disk_precedes_head_and_no_retry_write tests/integration/test_durable_turn.py::test_confirmed_rollback_atomic_after_real_wake tests/integration/test_durable_turn.py::test_uncertain_commit_proves_old_or_new_without_reevaluation tests/integration/test_durable_turn.py::test_postcommit_real_presentation_failure tests/integration/test_save_slots.py::test_export_previous_generation_and_atomic_load tests/unit/test_events.py::test_pending_roundtrip_and_leaf_hash tests/unit/test_events.py::test_queue_order tests/unit/test_read_views.py::test_nested_mutation_preserves_backing tests/replay/test_encounter.py::test_encounter_fresh_sessions_and_registry_order --basetemp .pytest_cache/gpt-invariants-7e01a435
```

This is not a fresh full1242 run. Read-only `.venv/Scripts/python.exe -m ruff format --check src tests` exited1 with67 would-reformat/29 already-formatted;it did not modify code. No fresh whole-tree lint/types/dependency/full-regression run for this documentation task.

## Additional recommendations — avoid duplicate policy

- Contract stability:already required by AGENTS/quality loop/MASTER and work-order template;persistent changes require defined compatibility/migration/independent vectors. Internal behavior-preserving refactors do not inherently need a schema migration.
- Feature registration:validate_registry,scheduler and RegisteredStateIO already reject collisions/ownership/activation/codec/event issues. These functions do not establish arbitrary future hundreds-feature composition;retain the single-bundle limitation as a future contract topic.
- Error model:typed BootstrapError/SchemaError/CandidateError/ReplayFormatError,TurnRejected/TurnAborted and persistence uncertainty categories already exist. Do not replace intentional exception boundaries without a demonstrated missing/error-misclassification case.
- Observability:Driver already logs candidate/presentation failures;receipts/events expose revision/tick/IDs. Comprehensive correlated diagnostics remain a future A13/B2 job,not evidence that logging is wholly absent. Keep logs outside CORE and exclude secrets/session credentials.
- Dependency control/development loop:already established through core bans/layer contracts/strict typing and the canonical repair policy. No additional rulebook or unapproved checker/library needed.

## Later application / dependency routing

Timing/status SSOT:[BACKLOG](../../BACKLOG.md). The following is a proposed decomposition,not permission to implement or a replacement backlog schedule.

1. RS-CI-001:bounded clean-run CI repair,including the missing formatter targets;independent fresh-parent reproduction → native checks → real green remote run. Scope/order/commit/push must be authorized when executing.
2. RS-CI-002:after real green job names are known,request administration approval for main protection/required checks/PR workflow and verify enforcement,including any bypass. Do not fabricate settings access or demand another human reviewer merely because the project is solo.
3. RS-STRUCT-001:CP01 context should include this report. Review responsibility seams and actually uncovered invariants;split one module at a time only with preserved public imports/pins/save/replay/goldens and focused/full regression. Prove helper equivalence before commonization;no blanket architecture rewrite.
4. Preserve existing GOV-03 deferral and refresh its old source inventory before any later authorization. Engine body hits are useful but do not prove every branch,runtime path or persistence method;do not silently enlarge G07.
5. Separate formatting normalization and future enforcement from feature changes;record format-only diff and unchanged behavior. Performance harnesses follow BLOCK_06/08 and real scale needs;no speculative hard timing gate.
6. Route new-schema content to QT-F02/RS-FACTORY/RS-V1-MIGRATION prerequisites and rights/CP02/CP03 holds. New multi-feature composition contracts may affect pins/formats and need authorization;generic Driver remains an existing invariant.

Acceptance of this task is evidence-backed storage/triage only. CP01 TODO/CP02 DEFERRED remain unchanged;this general-GPT plan is not either Claude checkpoint's feedback. Code/workflow/rules/settings are untouched;no tests/goldens waived or rewritten. Document/scope validation results are recorded in the delivery;all later improvements remain unimplemented.
Delivery checks:5strictUTF8 documents/81local prose links/fences/diff PASS;174baseline files checked,170byte-identical/only4existing docs modified plus this NEW review,HEAD unchanged. Backlog retains all prior task rows and checkpoint states;publication receipt consolidated without losing its result. Attachment hash preserved;no source/reference/candidate/format/fixture/settings writes or commit/push.
