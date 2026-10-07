# RS-P1-GOV / GOV-02 — Shared Native Dependency Control

Date:2026-10-07 (Asia/Seoul) | Executor/reviewer:Sol | Authoring:DONE | Execution:SELF-REVIEW_ACCEPTED/DONE | Shared G03:ACTIVE_LOCALLY
Scope:the authoring snapshot in §§1–9 is historical. Director subsequently authorized installation, application and testing; §10 records the current execution and narrowly scoped native findings. Self-review only; no CI changes.

## 1. Goal / Decisions

Introduce G03 using pinned native Import Linter, preserving the accepted gameplay/core/test/fixture bytes. Reviewable [complete candidate pyproject](RS-P1-GOV_02_PYPROJECT.toml), [current input inventory](RS-P1-GOV_02_INPUT_INVENTORY.json), and [complete 20-pin candidate lock](RS-P1-GOV_01_TOOLCHAIN.lock) supply exact inputs. The lock proposal is that existing lock's exact bytes copied to the shared dev lock after acceptance; it is not a new resolution.

Four native contracts:high-to-low layers, four concrete engine modules independent, same-layer sibling cycles, named external SDK/I/O/developer-tool prohibition for domain/contracts/engines. Source/app wiring and gameplay public APIs remain unchanged. G03 is a developer command, not called during a game turn.

Use standard native contracts, not a source-scanning replacement checker. Enabling coverage in the already qualified 20-pin closure does not activate G07. No gate runner, markers, hooks, workflow, report generator, custom checker or additional gameplay feature belongs to this unit.

## 2. Actual Baseline / Relocation

Workspace **C:\ReverieSaga**, main, HEAD `35f3c45dbd73291879c92044cba52f99d13987d3`; entry clean,143 tracked files. The older `C:\Reverie Saga` path in historical documents is provenance, not the current command path. Inventory pins every current tracked input by raw SHA256 before this authoring task.

GOV-01 reports PASS on Windows AMD64/CPython3.13.12/import-linter2.15/grimp3.17/coverage7.16.2,1113 tests and87 strict-mypy files. Historical summaries are retained; its private venv/wheels/native logs are **unavailable here**. There is no project .venv or Python/py/uv on PATH. The bundled authoring interpreter is CPython3.12.14; it has none of the selected pytest/Ruff/mypy/Grimp/Import Linter/coverage modules. It only parses documents/source/config for this task.

Historical protected comparison:99 src/test/config/lock inputs checked,53 byte-identical and46 differ solely by CRLF↔LF;0 unexplained. Git core.autocrlf=true explains this checkout. This is reviewed text-content continuity, **not raw-hash equality or current native qualification**. Keep both old and new fingerprints; do not rewrite old evidence, normalize protected files or treat old coverage ranges/artifact hashes as newly measured.

Execution prerequisite:an existing, qualified Windows AMD64 CPython3.13.12 plus a run-owned20-pin environment. Do not silently select bundled3.12, download a different Python or declare old native evidence current. Environment restoration/installation of Python itself requires its own concrete authorized scope if no eligible interpreter exists. GOV-02 native execution readiness remains UNQUALIFIED until the entry procedure below passes; this does not prevent completing the present authoring task.

READ:BACKLOG/SESSION_HANDOFF, [coding-order template](../prompts/SOL_CODING_WORK_ORDER.md), [staged GOV order §10](RS-P1-GOV_STAGED_CONTROLS.md#10-gov-01-execution--acceptance--2026-10-06), [GOV-01 execution JSON](RS-P1-GOV_01_QUALIFICATION.json), current locks/config and inventory. Authority/layers/evidence:[BLOCK01](../../architecture/BLOCK_01.md), [BLOCK07](../../architecture/BLOCK_07.md), [BLOCK08](../../architecture/BLOCK_08.md).
Source-specific reads:all50 source modules, especially four src/engines modules, four app/*_registry.py modules, app/headless.py, app/durable.py, orchestration/turn.py, orchestration/replay.py, orchestration/read_views.py, orchestration/persistence.py and both namespace adapters. Current static inventory is authoring evidence; native graph enumeration is mandatory at execution.

## 3. Exact Edit Scope / Authority

Present authoring:NEW this order,candidate TOML,input JSON;MODIFY staged GOV order,roadmap,BACKLOG,SESSION_HANDOFF factual records only. The existing shared pyproject/dev lock,source/tests/fixtures/previous evidence remain READ.

Future GOV-02 execution, after specific director execution authorization:

| Path under C:\ReverieSaga | Action / owner |
|---|---|
| pyproject.toml | MODIFY to exact reviewed candidate after isolated qualification; preserve original Ruff/mypy/pytest tables |
| requirements-dev.lock | MODIFY to exact GOV-01 20-pin lock bytes; original13 version/hash lines preserved |
| .venv/ | CREATE if absent using selected existing3.13.12; if present inventory first, install only accepted hash closure without recreating/deleting unrelated packages |
| tests/governance/__init__.py | NEW namespace ownership for native developer tests; empty intentional package is permitted |
| tests/governance/test_dependency_contracts.py | NEW real native-tool subprocess probes from independently specified inventory cases |
| docs/work_orders/RS-P1-GOV_02_ACTIVATION.json | NEW bounded execution evidence, schema §8 |
| .pytest_cache/gov02-<run_id>/ | NEW private candidate venv,wheels,fixture trees,logs,JUnit,temporary outputs; unique owned path |
| this order,staged order,roadmap,BACKLOG,SESSION_HANDOFF | MODIFY dated actual acceptance/next state |

No other source/tests/oracles/spec/AGENTS/CI/hooks files; no test deletion,skip,xfail,Any whitelist,source workaround,version loosening,additional dependency or policy. Normal ignored tool/bytecode caches are permitted. No commit/push/agent/external messages. Existing human rule authority:[prompt B1/B5](../ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md); the current request executes next-item authoring, not shared-policy activation. A later explicit instruction to execute this reviewed GOV-02 proposal is sufficient task authorization; do not ask again once given.

If an existing .venv has incompatible/extra packages, preserve it and qualify an owned isolated candidate; report the concrete environment conflict before altering shared packages. Do not remove packages or rename/replace the environment without authorization.

## 4. Exact Configuration / Lock

The candidate contains complete shared configuration. Parsed Ruff/mypy/pytest tables must equal current shared tables exactly. Add only tool.importlinter;no exclusions/ignores or optional roots. Contract IDs must remain unique.

| Contract | Exact semantics |
|---|---|
| rs-layers | app > adapters > orchestration > engines > contracts > domain; imports from later to earlier allowed; reverse/direct/transitive imports fail |
| rs-engines-independent | engines.skeleton/trial/encounter/watch cannot import one another directly or through internal intermediaries |
| rs-siblings-acyclic | six actual roots,depth10,all immediate sibling dependencies checked at each configured generation; acyclic same-layer cooperation allowed; cycle forbidden |
| rs-core-no-external-effects | source packages domain/contracts/engines including descendants; exact finite forbidden roots in candidate/inventory; direct and indirect named imports fail |

include_external_packages=true;exclude_type_checking_imports=false. TYPE_CHECKING violations are included. Only top-level external roots are valid;Google subpackages map to google,Path.open to pathlib,HTTP subpackages to their root. No wildcard claiming unknown SDK coverage. Missing *forbidden* roots that have no imports may pass;missing source/layer/independence roots or modules is an input error. adapters intentionally remains a namespace package with both existing children;do not add its __init__.py.

Current native module expectation:51 internal graph nodes (50 physical .py modules plus adapters namespace),four concrete engine modules,10 production classes/20 public methods. With externals included,**total graph nodes/dependencies change**;do not reuse the historical286-dependency count as a total. Require internal module set equality with GOV-01's graph after the inspected newline relocation, and exact internal root-edge sets from the authoring inventory. No extra/missing internal root or unaccounted .py file may be ignored.

Finite bans cover current dev distribution import names,selected generation/client SDK families,filesystem/network/persistence/process/thread/clock/global-RNG roots. adapters/app may use os/pathlib/sqlite3;orchestration's logging remains allowed. Pure dataclasses/hashlib/json/typing/collections use is allowed. This proposal is deliberately **named-import enforcement**:unlisted third-party roots,built-in open without an import,dynamic/reflection/native access and dependencies inside squashed external packages are not exhaustively proved by G03. Existing Ruff TID251,typed ownership and replay remain necessary. New dependency/import roots require source-order/config review;no claim of universal SDK rejection. No custom third-party banning plugin is added.

20 package pins/wheel hashes come from GOV-01 lock and metadata JSON;13 original pins exact,7 added closure pins exact. Include coverage7.16.2 as that qualified closure,not a separately activated G07 gate. Bootstrap pip25.3 is separate from20 packages. Fetch wheels binary-only with the exact hashes and metadata-selected wheel filenames;no source builds. A new download is independently hash-checked,not a reconstruction of lost old logs. Allowlisted URLs/metadata use the existing package records;credentials never logged.

## 5. Native Probe / Test Contract

NEW test module selects the actual native executable with `Path(sys.executable).parent / "lint-imports.exe"` and invokes subprocess.run(list[str],cwd=probe_tree,text=True,encoding="utf-8",capture_output=True,timeout=60). Require executable/tool versions before collection;missing tool fails setup,never skip. timeout is TOOL_ERROR/INCOMPLETE,not successful detection. Use pytest.MonkeyPatch.context() for only PYTHONPATH/encoding/hashseed/plugin settings;inherit existing Windows PATH/SystemRoot/TEMP normally,restore patched values at context exit even on failure. Do not directly reference os.environ/os.getenv or add Ruff exceptions for this new test module.

Every case gets a fresh pytest tmp_path tree and complete candidate config. Six root dirs;regular __init__.py except adapters. Baseline source files:
app/entry.py imports adapters.port and engines.skeleton/trial/encounter/watch;
adapters/port.py imports orchestration.driver;
orchestration/driver.py imports contracts.port;
each concrete engine imports contracts.port and domain.value;
contracts/port.py imports domain.value;
domain/value.py contains `VALUE = 1`.
All these are literal static-import fixtures;no application/provider/SDK execution or domain mocks.

Inventory `probe_expectations` and `parameterized_probe_expectations` are independently prescribed mutations. Replace the named fixture file's complete contents,not production code; fresh baseline for each case. No unknown braces/placeholders remain after formatting the single named root. The cases do not use captured production outcomes as oracles.

PLANNED tests:

- test_dependency_allowed_graph:baseline,adapter-I/O,pure-core stdlib,absent forbidden roots;exit0/all4 named contracts KEPT.
- test_dependency_internal_violation:direct/indirect reverse,direct/indirect engine dependency,TYPE_CHECKING reverse;exit1 and intended contract BROKEN with exact offending modules.
- test_dependency_external_root:one case per56 exact forbidden roots,engines.skeleton imports root;exit1,rs-core-no-external-effects BROKEN,native chain includes root. Packages need not be installed/executed. An import-resolution/config exception is not detection.
- test_dependency_indirect_external:engines.skeleton→contracts.port→pathlib;rs-core-no-external-effects BROKEN. Native reporting may suppress redundant chains;use native Grimp.find_shortest_chain for the independently named complete chain if CLI prints only its minimal violation.
- test_dependency_type_only_external:domain.value TYPE_CHECKING→openai;external contract BROKEN despite no runtime import.
- test_dependency_sibling_cycle:each of six roots gets cycle_a→cycle_b→cycle_a;rs-siblings-acyclic BROKEN. A single acyclic sibling edge remains allowed.
- test_dependency_missing_input:missing adapters root or engines.watch;nonzero and named missing-input diagnostic;classified TOOL_INPUT_ERROR,not contract detection.

Missing root/control configurations must never count as compliant. Separate each intended violation from additional broken contracts. Check actual native diagnostics/contract identity,not just nonzero or searching a filename. Test names are PLANNED until implementation. No artificial tests for this authoring document.

Source-specific positive check:run all4 contracts against actual unchanged src. Static review finds no currently banned core root;that is not substituted for the required native positive run. Independent toy probes must pass before any shared edit.

## 6. Ordered Execution / Baseline / Wiring

1. Refresh HEAD/status/all current inventory hashes. The four factual delivery docs legitimately change during authoring;record their new entry hashes. Any other drift requires source re-review. Verify current policy authorization and existing3.13.12 interpreter;record exact path/version/architecture/SQLite. If absent,retain proposal and report ENVIRONMENT_UNQUALIFIED.
2. Make unique owned run directory,temporary TEMP/TMP and private candidate venv from that interpreter. Resolve paths under workspace before creating/cleaning. Download/install exact20 binary wheels with --require-hashes;pip check,version/native import checks. Escalate sandbox network/filesystem failures through normal approval tool;never auto-loosen hash/version/platform requirements.
3. Copy candidate config into run-owned fixture trees;run independent probes and actual native graph. Native active configuration has4 contracts. Compare internal graph/namespace/type-only evidence. Record native stdout/stderr/exit and all versions/sources.
4. In candidate environment run pre-edit Ruff,strict mypy,full existing tests and six explicit goldens plus3 supplemental nodes. Capture exact node collection/JUnit/old failures. 1113 is a historical expected count,not a substitute for results. Do not apply shared changes after a baseline failure.
5. Add the one bounded native-test module/package;preserve every old test/assertion/fixture byte. Apply exact reviewed shared TOML/lock. Create/install .venv only under §3 ownership. Shared tools must pass pip check and match20 pins;bootstrap separately reported.
6. Run native dependency tests using the **shared** candidate config and executable;actual source lint-imports positive;Ruff/strict mypy src tests;complete pytest suite including every old and new case;six goldens plus3 supplemental nodes. All actual source/input hashes and original assertions retained;no narrowed collection.
7. Inspect complete diff/evidence/namespace/native positive+negative chains;old and new regression results;configuration equivalence;unchanged production bytes. Append actual acceptance/status. If native/shared activation fails,do not mark G03 active or restore broad directories;record exact edits and scoped repair.
8. Parent GOV remains IN_PROGRESS after G03. NEXT author GOV-03 typed native replay-body coverage harness. Do not automatically execute it,all11 gates or graphical/world capabilities.

Wiring:`lint-imports --config pyproject.toml --no-cache` reads shared config and discovers src via PYTHONPATH;the NEW pytest module calls the same native executable against fresh independent fixture trees. No registered engine/Driver public API changes. Existing app registries instantiate Stepper/Counter/Movement/EncounterActions/EncounterMovement/WatchNpc/WatchBell/WatchRespond/WatchEchoEngine/WatchPassive as before.

No gameplay numerical/error/default/ordering/save migration changes;zero/negative/duration/tie policies NOT_APPLICABLE. Developer errors:empty selection,missing source root,unknown/duplicate contract,invalid TOML,mismatched lock/version/hash,stale fingerprint or missing native executable fail qualification. External root names case-sensitive Python module names;paths normalize to actual Windows workspace without conflating historical and current paths. Native contract failures retain actual nonzero exits and named chains;no artificial DomainError conversion.

## 7. Exact Command Families

Run from C:\ReverieSaga. Commands below are **NOT_RUN** in this authoring task. GOV-02 executor supplies real selected interpreter and uniquely owned run paths as recorded values;there is no invented local Python3.13 path.

Candidate interpreter creation/download/install follows GOV-01 §4 but uses this baseline/candidate20-pin lock. Download command:`<candidate-python> -m pip download --only-binary=:all: --require-hashes -r docs/work_orders/RS-P1-GOV_01_TOOLCHAIN.lock -d <owned-wheel-dir>`.
Install:`<candidate-python> -m pip install --require-hashes --no-index --find-links <owned-wheel-dir> -r docs/work_orders/RS-P1-GOV_01_TOOLCHAIN.lock`.
Bootstrap:`<existing-qualified-python313> -m venv --copies <owned-candidate-venv>`;set owned TEMP/TMP before ensurepip. No PowerShell separators may hide nonzero exits;check each result immediately.

Shared verification example after successful preflight/apply:

```powershell
$govRoot = 'C:\ReverieSaga'
$govPython = Join-Path $govRoot '.venv\Scripts\python.exe'
$govLinter = Join-Path $govRoot '.venv\Scripts\lint-imports.exe'
$govGolden = @(
 'tests/replay/test_golden.py::test_core_trace',
 'tests/replay/test_trial.py::test_trial_core_trace',
 'tests/replay/test_encounter.py::test_encounter_core_trace',
 'tests/replay/test_encounter.py::test_encounter_death_trace',
 'tests/replay/test_watch.py::test_watch_core_trace',
 'tests/replay/test_watch.py::test_watch_passive_trace'
)
$govSavedEnvironment = @{}
foreach ($govKey in @('PYTHONPATH','PYTHONHASHSEED','PYTHONIOENCODING','PYTEST_DISABLE_PLUGIN_AUTOLOAD')) {
 $govSavedEnvironment[$govKey] = [Environment]::GetEnvironmentVariable($govKey, 'Process')
}
try {
 $env:PYTHONPATH = Join-Path $govRoot 'src'
 $env:PYTHONHASHSEED = '0'
 $env:PYTHONIOENCODING = 'utf-8'
 $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
 & $govPython -m pip check
 if ($LASTEXITCODE -ne 0) { throw 'pip check failed' }
 & $govPython -c 'from importlinter.cli import lint_imports_command; lint_imports_command()' --config (Join-Path $govRoot 'pyproject.toml') --no-cache
 if ($LASTEXITCODE -ne 0) { throw 'G03 type-inclusive contracts failed' }
 & $govPython -c 'from importlinter.cli import lint_imports_command; lint_imports_command()' --config (Join-Path $govRoot '.importlinter-runtime.toml') --no-cache
 if ($LASTEXITCODE -ne 0) { throw 'G03 runtime cycles failed' }
 & $govPython -m pytest -q tests/governance/test_dependency_contracts.py
 if ($LASTEXITCODE -ne 0) { throw 'native probes failed' }
 & $govPython -m ruff check src tests
 if ($LASTEXITCODE -ne 0) { throw 'Ruff failed' }
 & $govPython -m mypy --strict --no-incremental --no-native-parser src tests
 if ($LASTEXITCODE -ne 0) { throw 'strict mypy failed' }
 & $govPython -m pytest --collect-only -q @govGolden
 if ($LASTEXITCODE -ne 0) { throw 'golden collection failed' }
 & $govPython -m pytest -q @govGolden
 if ($LASTEXITCODE -ne 0) { throw 'goldens failed' }
 & $govPython -m pytest -q tests
 if ($LASTEXITCODE -ne 0) { throw 'regression failed' }
} finally {
 foreach ($govKey in $govSavedEnvironment.Keys) {
  [Environment]::SetEnvironmentVariable($govKey, $govSavedEnvironment[$govKey], 'Process')
 }
}
```

Actual evidence-producing executor adds unique owned --basetemp/--junitxml paths to each pytest run;never reuse baseline/final paths. Supplemental node names come from inventory;run separately and retain results. Record all commands including --collect-only;collection is not test execution.

If compiled mypy loader is denied,use only the unchanged installed-source fallback in [CORE review §5](RS-P1-CORE_INTEGRATION_REVIEW.md#5-reproduce-installed-source-mode-type-check),redirect its site-packages root to the relevant candidate/shared environment,preserve strict flags and report source-mode explicitly. No grimp/Rust DLL substitute or OS-policy adjustment. Failed required native import makes G03 UNVERIFIED.

## 8. Evidence / Acceptance / Stop Conditions

NEW activation JSON:UTF-8/LF,`schema_version:1,task_id:"RS-P1-GOV/GOV-02",status:PASS|FAIL|UNVERIFIED,baseline_head,run_id,workspace,authorization_reference,platform,entry_input_sha256,final_input_sha256,config_sha256,lock_sha256,tool_versions,runs,graph,probes,scope,limitations,next`.

Each run stores id,argv list,cwd,allowlisted env,exit_code(or null only not started/interrupted),elapsed_seconds,status and artifact path/SHA256/byte size. Probes link exact fixture/config/native logs plus independently named expected contract/chain and actual result. Graph lists internal/external nodes separately,internal root edges,namespace verification. Tests include collected node IDs,JUnit case outcomes and actual result;no stdout invention or skipped-case PASS. Required fields absent/malformed/stale -> UNVERIFIED. Historical raw evidence unavailable flag remains;do not reconstruct old raw artifacts under their old hashes.

Acceptance for future activation:qualified same-version20-pin environment;original13 hashes preserved;4 exact native contracts;all prescribed positives/negatives exercise intended condition;complete internal graph and namespace;pre/post baseline and full added-test regression;Ruff/strict mypy/six goldens/3supplements;no production/prior-test/fixture change;scope/hash/diff review. Only then G03 ACCEPTED/active locally. No automatic CI activation or G07/full11 qualification.

Time:G03≤3s and full11≤60s remain TARGET/UNQUALIFIED;record timings diagnostically,no wall-clock hard gate. Native CLI watchdog60s/test reports incomplete tool execution. Historical full suite253.15s is not a60s qualification. No new hardware/model-fit claim.

Stop dependent activation for missing3.13.12/native tool,signed loader denial,no exact binary wheel,hash/version mismatch,unexpected source drift,unknown root,new depth beyond inspected policy,broken real graph or preexisting test failure. Complete independent documentation/evidence work. Diagnose actual in-scope failures;no optional-layer syntax,ignore imports,assertion weakening,source edits or version upgrades to force a pass. Routine private test/helper naming within the one allowed module needs no added approval.

## 9. Authoring Verification / Current Outcome

Actual current interpreter3.12.14 performs strict TOML/JSON parsing,source AST inventory,raw input/proposal preservation,lock13-in20 inclusion and hashes,local-link/fence/PowerShell syntax/diff/scope checks. The authoring inventory marks native proposal NOT_RUN. Present source/test/config/lock unchanged;historical qualification and new relocation checks remain distinguishable.

Native test collection/execution,install,pip check,Import Linter/Grimp,Ruff/mypy/full pytest in selected3.13.12 are NOT_RUN here because the qualified environment is absent. Authoring completion does not declare GOV-02 activated or remove its entry preflight.

Actual authoring validation:7 UTF-8 delivery files,88 existing local Markdown links,strict candidate TOML/JSON parsing,4 distinct native contract IDs,56 unique named forbidden roots,original13-in20 exact pin/hash preservation,unchanged parsed Ruff/mypy/pytest configuration,literal independent-probe Python syntax and PowerShell example syntax PASS. All50 source-module ASTs parse;this is syntax review,not native graph/runtime proof. Exact143-entry scope:139 unchanged/four authorized factual-document edits/three NEW proposal artifacts. git diff --check PASS;HEAD unchanged. Historical99 protected files remain53 byte-identical/46 LF-equivalent/zero unexplained. Self-review authoring ACCEPTED;native entry/activation remains UNQUALIFIED/NOT_STARTED.

Official interface review2026-10-07:[pinned forbidden-contract source](https://raw.githubusercontent.com/seddonym/import-linter/v2.15/src/importlinter/contracts/forbidden.py),[forbidden contract docs](https://import-linter.readthedocs.io/en/stable/contract_types/forbidden/),[acyclic siblings docs](https://import-linter.readthedocs.io/en/stable/contract_types/acyclic_siblings/),[Grimp external graph semantics](https://grimp.readthedocs.io/en/stable/usage.html). Source confirms named absent forbidden roots are filtered rather than required as installed packages;native new-contract behavior still requires the prescribed experiment. Moving docs describe candidate semantics,not selected-tool execution proof.

## 10. GOV-02 Execution / Native Corrections — 2026-10-07

Authority:director explicitly requested "너가 Python 3.13.12 깔아서 알아서 적용이랑 테스트 해". This authorizes project-local exact-version Python installation, shared GOV-02 policy/dependency application and verification. §§1–9's authoring-only NOT_RUN/absent-environment statements are dated history, not current status. The input inventory remains an immutable authoring snapshot; activation evidence records new entry/final fingerprints separately.

Bounded scope refinements following actual native tests:

- NEW .importlinter-runtime.toml and corresponding reviewed [runtime config](RS-P1-GOV_02_RUNTIME_IMPORTS.toml). AP-09 explicitly permits annotation-only forward-reference cycles. The original all-type-inclusive sibling check rejected existing contracts.messages/read_views/turn TYPE_CHECKING edges. Three type-inclusive contracts stay in pyproject.toml (layers/engine independence/56 named bans); only runtime sibling-cycle checking uses exclude_type_checking_imports=true in the second native configuration. No ignored edge, optional root or source workaround. An added independent type-only sibling-cycle positive plus type-only reverse/SDK negatives prove the distinction. Candidate configuration is corrected to the same final policy; historical four-in-one proposal validation is not re-labelled as its final native result.
- Python base installed at C:\ReverieSaga\venv\python-3.13.12; project .venv created using that full standard runtime. Both ignored local directories must be retained together. Official MSI exited3 with package-cache path error0x80070003; official full-runtime ZIP hash/manifest verification enabled installation without OS-policy or system PATH changes. Original private candidate runtime/cache remains diagnostic provenance, not .venv's final base.
- Windows Application Control denied ast_serialize's DLL under normal mypy2.4.0 parsing. The package's official --no-native-parser option uses its existing Python parser with unchanged strict rules and complete src/tests scope; baseline87/final89 files PASS. Initial installed-source finder alone also failed at the same denied Rust parser and is recorded, not claimed successful. No package modification/version loosening/OS-policy change.
- Windows denied pip-generated shared lint-imports.exe (WinError4551). The exact installed console entry point declared in import_linter-2.15.dist-info/entry_points.txt is called by Python:from importlinter.cli import lint_imports_command; lint_imports_command(). This executes unchanged native CLI/config/Grimp contracts and real subprocess diagnostics. The new test module uses this invocation consistently, not a replacement checker. Initial launcher-only full run is retained separately as a failed attempt; final complete rerun uses final test bytes.

Native isolated79 probes PASS; shared final invocation79 probes PASS. Real graph internal51 modules/namespace adapters/four engines/root edges match both authoring inventory and GOV-01. Type-inclusive graph71nodes/448dependencies; runtime graph51nodes/284dependencies. No gameplay source, previous test/assertion/golden fixture or architecture/specification edits. Existing Ruff/mypy/pytest parsed configuration preserved, original13 lock pin/hash lines included in the exact20-pin shared lock; pip25.3 bootstrap separate. G03 requires both §7 CLI calls, also exercised by normal pytest. No custom checker/hook/workflow/CI/G07 coverage adapter or all11-gate activation.

Execution acceptance:SELF-REVIEW ACCEPTED/DONE. Final complete regression1192passed in262.07s (native process262.369s),zero failures/errors/skips;1113 original cases retained plus79 new meaningful native cases. [Fresh execution evidence](RS-P1-GOV_02_ACTIVATION.json); actual run directory C:\ReverieSaga\.pytest_cache\gov02-e883728d82d1437397dbdd85867cb610. Current baseline1113 tests PASS (238.45s); isolated79 PASS (33.72s); shared79 PASS (32.80s), Ruff PASS, strict Python-parser mypy89files PASS, native3+1 contracts PASS, shared six goldens2.88s/three supplements6.42s PASS. Final evidence retains failed attempts, exact argv/env/exit/timing/log hashes, all1192 collected node IDs/JUnit outcomes, independent probe fixture/config hashes and graph/source fingerprints. Initial shared full run78failed/1114passed (244.64s) was solely the generated-linter launcher denial;all1113 previous cases passed. Final complete rerun above uses unchanged final test bytes and the qualified console entry point. Exact146 execution-entry files:138 unchanged/eight authorized changes;four execution additions plus this evidence JSON. All source/prior-test hashes match entry. G03 direct CLI process timings0.225/0.214s are diagnostic,not full11/G07/hardware qualification. NEXT after acceptance:author GOV-03 typed native replay-body coverage order; do not execute it automatically.

Final proposal fingerprint note:shared primary pyproject uses checkout CRLF and one terminal newline;candidate proposal uses LF and an additional terminal blank line. Parsed TOML and normalized text are equal,not raw bytes. Both raw fingerprints are retained separately;no production/old-test normalization performed. Runtime TOML proposal/shared and20-pin lock source/shared are byte-identical. Initial evidence-assembly raw-primary equality assertion failed on that encoding distinction and was corrected to explicitly validate parsed/text equivalence;the failed assembly remains diagnostic evidence.

