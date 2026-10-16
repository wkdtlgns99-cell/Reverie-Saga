# QT-F02 — Execution and Native Acceptance

Date:2026-10-13 (Asia/Seoul) | Executor/reviewer:Sol;self-review only
State:implementation/native acceptance PASS;parent READY_FOR_REVIEW,CP03 feedback NOT_RECEIVED.
Authority:director's request to execute remaining work;[contract](../work_orders/QT-F02_SCENARIO_CONTRACTS.md),
[order](../work_orders/QT-F02_SCENARIO_GENERALIZATION.md). No publication/bulk/world expansion.

## Result / Compatibility

Harbor and grove execute through one parameterized watch/encounter path with independent role
IDs,wall/enemy/NPC placement. Definitions are embedded frozen data,pinned by existing rule/schema
fingerprints. Registered engines,admission,codecs,reducers,presenters,checkpoint checks,worker,
narration and client use the same binding. Canonical component lookup supports arbitrary lexical
player/enemy ordering;legacy constructors/default fingerprints and golden fixtures remain compatible.
Client/bridge expose explicit startup selection and generated scenario labels. New saves use the
unchanged SQLite format;resume/load require matching selected pins and cannot convert another world.
External mutable gameplay catalogs,quest consequences,bulk narratives and final art remain later scopes.
CP05 NOT_TRIGGERED for this embedded stage;no major save/quest/memory format/behavior change.

Baseline HEAD1ad22446d48c50b8b72a6d3af8de3c9d775134ea unchanged. Earlier four authoring-document
edits retained;all further delivery files are task-owned. Generic turn/SQLite/save-slot code,pins,
dependencies,CI,reference/candidate/provenance originals and golden bytes were not edited.
Unity Prepare regenerated only scene serialization IDs;that incidental scene output was restored to
its clean entry version. Test evidence uses fresh directories and preserves earlier CP04 captures.

## Actual Verification

| Command / path | Exit / result |
|---|---|
| `.venv/Scripts/python.exe -m pytest -q tests/replay/test_encounter.py tests/replay/test_watch.py tests/integration/test_client.py --basetemp .pytest_cache/qt-f02-legacy` | 0;71PASS33.91s,initial unchanged legacy behavior |
| Focused scenario/encounter/event/trial modules,`--basetemp .pytest_cache/qt-f02-focused-final` | 0;332PASS15.56s,including12new independent cases |
| README full pytest,`--basetemp .pytest_cache/qt-f02-full-final --junitxml tmp/qt-f02-full-final.xml` | 0;1304PASS314.13s |
| README shared/selective Ruff | 0;both PASS |
| README12formatter targets +scenario domain/app/test files | 0;15files PASS |
| README strict mypy `--no-native-parser` | 0;106files PASS |
| README type-inclusive/runtime Import Linter configs | 0;3+1contracts KEPT,no broken contracts |
| `python -m app.engine_project --root C:/ReverieSaga` | 0;generated C# fields/hash match Python;accepted narratives unchanged |
| `git diff --check`,document/manifest/scope checks | PASS;portable input manifest accompanies review packet |

Actual new tests independently assert cell/HP/stamina/tick/wake values,save midcombat,resume loaded
branch,exact retry,wrong scenario resume/load state preservation,old target rejection,selected walls,
noncentral door geometry,lexical role swap,replay and real child pipe. No domain-outcome mocks.
Initial pipe test setup used wrong child cwd:2FAIL7PASS6.04s;aligned with existing src cwd,then PASS.
Initial full diagnostic began before constructor compatibility repair:10FAIL1291PASS318.93s.
Legacy extension constructors did not call the newly added base initializer;fixed explicit immutable
legacy default binding without editing those tests or their expected diagnostic codes. Final full
run uses settled Python inputs. The preexisting Python launcher-location stderr remains;actual
commands complete. No skip/golden rewrite/blanket suppression or dependency reinstall.

## Unity / Device Evidence

Observed Windows host:Python3.13.12 AMD64/Tk8.6;editor6000.3.25f1/e1dba0a9aba4;
Intel UHD Graphics750. Fresh permitted license status:success/active/signedIn=true.
Named laptop/other-PC mapping and readiness remain UNVERIFIED;no cross-device inference.

Each editor run uses Start-Process Hidden and explicit WaitForExit,one heavy job at a time.
Set REVERIE_UNITY_SCENARIO and a fresh REVERIE_UNITY_WORKING directory under tmp/qt-f02-native;
executeMethod `ReverieSaga.PlaytestBuild.Verify` for samples,`BuildAndVerify` for legacy,
`VerifyCorrupt` with case=corrupt for the corrupt-save probe. Current-source final receipts:

| Run / local log | Actual result |
|---|---|
| harbor-final.log | exit0;11VERIFY_PASS,ENGINE_VERIFY_PASSED;screenshot/final view/120frames |
| grove-final.log | exit0;11VERIFY_PASS,ENGINE_VERIFY_PASSED;screenshot/final view/120frames |
| legacy-build-permitted.log | exit0;24VERIFY_PASS,ENGINE_VERIFY_PASSED;Windows build89477040bytes PASS;release verification hook ABSENT |
| corrupt-final.log | exit0;1VERIFY_PASS,SAVE_CORRUPT visibly reported,ENGINE_VERIFY_PASSED |

Total47native checks. The two samples verify actual selected cells,combat arithmetic,failed load
preservation,exact successful load,retry once,NPC causal response and loaded-branch reconnect.
Actual screenshots were inspected;they are placeholder rooms with Korean labels,not towns/final art.
Raw logs/private saves/session tokens stay local ignored. [Inputs/evidence](QT-F02_INPUTS.json)
retain sanitized native view/check/performance facts and screenshot hashes for the review packet.

Initial sandboxed editor attempt failed initialization (`ERROR_SUCCESS == status`),spawned its
owned crash reporter and reached no gameplay checks. Current-account license read and native
execution succeeded under permitted execution. Closed only that owned reporter/interrupted waiter;
retained the functioning license service. Earlier successful sample runs are historical;final sample
runs follow the final verifier output-path repair. No OS/security/license-policy relaxation.

Harbor final120frames:median2.052296ms/p953.003005ms;grove:median1.7893ms/p952.871103ms.
Two traced bootstrap samples per configuration:58.186–89.735ms,peak Python allocation≤254712bytes.
Tracemalloc overhead/import warming are included;this is not total process RAM,MIN-SPEC/release
qualification or a performance improvement claim. New standalone executable launch NOT_RUN;
historical unsigned-player block remains separate. Human UX/HD-2D/release QA remain UNVERIFIED.

## Delivery / Held Step

Code/native acceptance is complete for this bounded scope. CP03 packet is prepared with actual
sources/contracts/tests,independent examples,diff/hash inventory and receipts. Feedback is not
invented or replaced by self-review. Hold further scenario/world/bulk expansion until actual Claude
feedback has verified dispositions and required repairs/retests. No commit/push/PR/external upload.
