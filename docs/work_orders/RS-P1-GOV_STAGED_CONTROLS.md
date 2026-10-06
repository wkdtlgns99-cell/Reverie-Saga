# RS-P1-GOV — Staged Dependency / Replay Coverage Controls

Date:2026-10-06 | Owner/executor/reviewer:Sol | Authoring:DONE, self-reviewed | Parent:IN_PROGRESS | GOV-01 native qualification:ACCEPTED/DONE | Shared gate activation:NOT_STARTED

Director request "담꺼 ㄱㄱ" executes the next authoring item after [CORE integration acceptance](RS-P1-CORE_INTEGRATION_REVIEW.md). This document supplies a READY isolated qualification order; actual shared dependency/policy activation is a later stage with its own qualified inputs. No agent/model change, commit/push or eleven-gate activation.

## 1. Decisions / Stage Register

| Unit within RS-P1-GOV | State | Concrete outcome / promotion prerequisite |
|---|---|---|
| GOV-01 tool qualification | ACCEPTED/DONE | Isolated Windows CPython3.13.12;20 hashed packages preserve original13 pins;native probes/51-module graph/20 golden body hits;1113tests253.15s,Ruff/native strict mypy87files PASS;§10 evidence |
| GOV-02 G03 dependency control | DRAFT, NOT_STARTED | After GOV-01 passes, materialize exact shared lock/config diff and source-specific execution order; activate native layer +engine independence contracts; preserve runtime/test bytes |
| GOV-03 G07 replay body coverage | DRAFT, NOT_STARTED | After native JSON/body/context qualification, finalize typed native-evidence adapter contract/path/errors and independent rejection fixtures; require all registered public engine bodies in qualified goldens |
| GOV later G08/G09/G10/G11/report/mutation | DEFERRED implementation | Actual applicable counters, supported migration corpus, observed access/consumer semantics, approved artifacts, selected native interfaces; bounded orders required |

First execution is **GOV-01 only**. Qualification is a real standalone tooling experiment, with no shared gate installation. Its readiness means complete experiment instructions, not already-compatible tools. Failed or unavailable native support stays FAIL/UNVERIFIED, with its actual reason. No automatic version upgrade, substitute AST checker or empty lane.

Goals:G03 detect prohibited static import chains; G07 prove public engine method bodies execute in real successful golden traces. These controls preserve the accepted representative gameplay slice. They do not implement NPC emotion/persona/BDI/memory or certify balance, declared field usage, crash/platform performance or the full game.

## 2. Actual Entry / Required Reads

Workspace `C:\Reverie Saga`; HEAD `efd2478ff8a6ed93ee833c3f8464a0efdd8a181a`. Tracked prompt/MASTER modifications and many untracked accepted files predate this task. Preserve them. [Input inventory](RS-P1-GOV_INPUT_INVENTORY.json) records139 entry files/SHA256, six roots,20 public method body ranges,9 selected test nodes and independently specified toy expectations. It is an authoring inventory, **not native execution evidence**. Source ranges were enumerated once from actual code; no persistent AST validator was added.

Installed:.venv CPython3.13.12,SQLite3.50.4,Ruff0.16.6,mypy2.4.0,pytest9.1.1. Existing [hashed dev lock](../../requirements-dev.lock) has13 pins. New tools absent. Native Windows mypy DLL import was blocked by Application Control; installed Python-source mode passed unchanged strict checks. PyPI metadata lookup through local urllib failed DNS `[Errno 11001] getaddrinfo failed`; public documentation was accessible through web lookup. Neither condition qualifies/condemns the unexecuted new tools. No OS-policy modification or install in this authoring task.

READ, in addition to BACKLOG/SESSION_HANDOFF/template:

- [BLOCK01](../../architecture/BLOCK_01.md) layers/AP; [BLOCK06](../../architecture/BLOCK_06.md) real counters/profiles; [BLOCK07](../../architecture/BLOCK_07.md) B0 standard-first/B2 evidence truth; [BLOCK08](../../architecture/BLOCK_08.md) B3 G03/G07/selection and B5 authority.
- [pyproject](../../pyproject.toml), dev lock, [Phase0 toolchain](PHASE0_TOOLCHAIN.json), [CORE acceptance](RS-P1-CORE_INTEGRATION_REVIEW.md) including installed Python-source mypy invocation.
- `src/engines/{skeleton,trial,encounter,watch}.py`; `src/app/{headless,feature_registry,trial_registry,encounter_registry,watch_registry,durable}.py`; `src/orchestration/{turn,replay,read_views,persistence}.py`; `src/adapters/{sqlite_store,save_slots}.py`; actual contracts/domain roots.
- Six golden test files/nodes and `tests/integration/test_core_slice.py`, `tests/replay/test_registered_replay.py` named in inventory. Inspect live registry bindings/callers, fixtures and literal expected assertions; never derive new oracles from production outputs.

Prior accepted baseline:1113tests263.97s,Ruff PASS,strict mypy87files PASS in installed Python-source mode; six goldens3.15s. These are historical integration-review results, not GOV measurements. At execution refresh HEAD/status/all input hashes and candidate metadata; ordinary allowed delivery-doc changes are explained separately, source/config/lock/fixture drift requires source-order re-review before qualification.

## 3. GOV-01 Allowed Scope / Delivery

Exact future paths (NEW unless stated), absolute prefix `C:\Reverie Saga\`:

| Path | Ownership / limit |
|---|---|
| `.pytest_cache\gov01-<run_id>\` | Private ephemeral venv/wheels/copied config/probe packages/native logs/coverage/JUnit; run_id opaque unique hex; resolve within this workspace before use; no recursive cleanup of other runs |
| `docs\work_orders\RS-P1-GOV_01_QUALIFICATION.json` | NEW strict JSON execution evidence, schema below; retain actual commands/results/artifact hashes and limitations |
| `docs\work_orders\RS-P1-GOV_01_TOOLCHAIN.lock` | NEW complete hashed candidate closure; evidence/proposal only, never shared install implicitly |
| `docs\work_orders\RS-P1-GOV_STAGED_CONTROLS.md` | MODIFY dated GOV-01 execution/acceptance appendix and later readiness only with qualified support |
| `BACKLOG.md`, `SESSION_HANDOFF.md`, `docs\work_orders\IMPLEMENTATION_ROADMAP_ORDERS.md` | MODIFY factual scope/status/next-action links |

Everything else READ ONLY during GOV-01:shared `.venv`, `requirements-dev.lock`, `pyproject.toml`, all src/tests/fixtures/reference/spec/AGENTS/CI/hooks. Python bytecode/pytest cache writes only normal ignored caches. No permanent probe helper/wrapper/custom checker; disposable probes are standard-tool experiments. No gameplay/schema/method/test changes, test deletion/skip/xfail, added pytest markers or changed collection ownership. Later policy activation requires a concrete finalized diff/order and director execution authorization; the present authoring request does not activate it.

Execution evidence schema:top-level `schema_version:1`, `task_id:"RS-P1-GOV/GOV-01"`, `status:PASS|FAIL|UNVERIFIED`, `baseline_head:str`, `run_id:str`, `platform:{os,architecture,python,sqlite}`, `input_sha256:{relative_path:64hex}`, `toolchain:{lock_sha256,packages:[{name,version,wheel,sha256,requires_python,license}]}`, `runs:[{id,argv:list[str],cwd:str,environment:{allowlisted_key:str},exit_code:int|null,status:PASS|FAIL|NOT_RUN|UNVERIFIED,elapsed_seconds:nonnegative_number,selected_nodes:list[str],artifacts:[{path,sha256,bytes}]}]`, `graph:{roots,modules,root_edges,namespace_verified}`, `methods:[{path,class_name,method,source_sha256,body_start,body_end,executed_body_lines:list[int],golden_nodes:list[str],status}]`, `limitations:list[str]`, `scope:{unchanged_inputs,authorized_doc_differences,head_unchanged}`. UTF-8/LF, deterministic sorted collections except execution-order runs; native logs unchanged. Null exit only when process never started or was interrupted, never exit0. No credentials/environment dump. Missing/invalid/stale evidence stays UNVERIFIED; JSON creation alone does not certify PASS.

Each run owns its output files. Persist hashes/versions/exact tested snippets/native stdout/stderr and raw JSON plus collected nodes/JUnit. Native artifacts needed for reproducibility remain in the private run directory; evidence lists exact absolute paths and hashes. If unavailable later, evidence is unavailable rather than reconstructible from claimed success. Lock includes every installed candidate dependency with exact version and wheel hash. No dependency-count assumption for the newly resolved closure.

## 4. GOV-01 Algorithm / Native Contracts

1. Refresh source/HEAD/input inventory, inspect all reads/callers, record original13 pinned packages unchanged. Record compiler-loader/DNS/base-interpreter diagnostics separately from gameplay failures.
2. Create isolated workspace venv from actual CPython3.13.12, initially using `.venv\Scripts\python.exe -m venv --copies <run_dir>\venv`. If original base path is missing, locate/read interpreter metadata and qualify an existing same-version interpreter; if none works, report UNVERIFIED. Do not download another Python or alter OS policy.
3. In that venv resolve binary wheels for original13 pins +`import-linter==2.15`, `grimp==3.17`, `coverage==7.16.2`, no UI extras/pytest-cov/plugin. Derive an owned plain `baseline-constraints.txt` with the13 exact `name==version` entries (no hash options); owned `requested.txt` lists those13 plus the3 candidates. Never feed the partially hashed original lock as resolver constraints:that would prematurely require unknown candidate hashes. Use `pip download --only-binary=:all: -r <requested.txt> -c <baseline-constraints.txt> -d <owned_wheels>`; record complete Requires-Dist closure, PyPI release wheel digest/license/Requires-Python. Original13 selected wheel hashes must still equal the original lock. Reject mismatched hashes, incompatible tags, changed original pins, missing binaries or undeclared extra packages. Build exact new hash lock then install with `--require-hashes --no-index --find-links <owned_wheels>`. Native `pip check`, versions and imports must pass. Resolver/install failure is visible; don't source-build Rust or silently change pins.
4. Execute **independent toy import cases** from inventory with the exact candidate TOML below, isolated source roots and no cache. Each case gets a fresh copy; remove previous added edges rather than accumulating faults. Graph must enumerate all required roots/children including namespace adapters. Positive0; negative actual named BROKEN chain +nonzero. A DLL failure/config parse error is not successful detection of a prohibited import.
5. Execute actual source graph/native contracts with `PYTHONPATH=<workspace>\src`. Confirm all source modules present, both adapters children and all four engine modules; compare actual native edges with current source inventory. Current actual graph is expected KEPT; discrepancy must be diagnosed, not ignored. Native static analysis does not guarantee dynamic/reflection import safety.
6. Run coverage toy called(False/True) and import-only cases in separate erased data files under owned directories. Exact five-line source is in inventory; returns1/2, body lines2..5 exercised by called tests; import-only body intersection empty, even if definition line1 executed. Require actual branch data and test_function contexts. Import-only pytest passes but preflight must explicitly record ZERO_HIT; no global percentage proves body execution.
7. Run **six original golden nodes only**, fixed hashseed0, branch coverage, source `src/engines`, explicit pytrace and contexts. Require all20 current method bodies hit in successful golden test contexts; `manifest` property boot-body hits reported separately from `evaluate` turn-body hits. Definition/decorator/import lines excluded by the pinned body ranges. Native analysis executable lines intersect ranges, then executed/context lines; import-time ranges are insufficient. Missing method/file, zero executable denominator, stale range/hash, skip/xfail/empty selection or failed pytest cannot qualify a body. Review each range: no nested function/class body may count for its outer method; current20 methods have none.
8. Separately measure both joined gameplay cases and foreign registered Gauge trace; record supplemental context/results. They prove combat/save integration and registry generality; they **do not fill a six-golden zero-hit**. Gauge fixture engines are identified as test-only, outside the production10-class list. If current public engine inventory changes, stop and reconcile it rather than silently omitting new bindings/methods.
9. Run baseline Ruff and strict mypy (same installed-source fallback if compiled mode denied) plus full1113-test regression in the qualified isolated environment. No pytest marker exclusions. Capture actual collected count/exits/timings, do not assert counts alone. Native coverage jobs do not measure subprocess code unless explicitly traced; full-suite crash/replay child-process tests remain ordinary regression, not falsely included in coverage.
10. Inspect lock/evidence/scope and native negative diagnostics, compare all original input hashes, record self-review. GOV-01 DONE only if all qualification requirements PASS; blocked cases retain actual limitation and unaffected outputs. GOV-02/03 remain DRAFT until their own exact diff/interfaces/readiness are finalized; propose next bounded execution in handoff.

Process boundaries:normal positive native commands exit0; genuine broken import contract nonzero plus expected native contract/edge diagnostic; CLI/config/runtime/DLL failures are tool errors, not contract-detection PASS. Pytest nonzero never qualifying coverage. Empty selection returns no passing gate. No public runtime API/error changes:tool errors stay native; evidence classification is developer documentation, not an engine exception. Numeric/gameplay edge policy NOT_APPLICABLE because runtime behavior is preserved; toy/selection/hash/namespace/missing/duplicate/version/tool-error boundaries are explicit above.

## 5. Candidate G03 Configuration / Independent Cases

GOV-01 writes this only to `<run_dir>\imports.toml`. GOV-02 may later propose the same `tool.importlinter` sections in shared pyproject after actual qualification.

```toml
[tool.importlinter]
root_packages = ["app", "adapters", "orchestration", "engines", "contracts", "domain"]
include_external_packages = false
exclude_type_checking_imports = false

[[tool.importlinter.contracts]]
id = "rs-layers"
name = "Reverie Saga six internal layers"
type = "layers"
layers = ["app", "adapters", "orchestration", "engines", "contracts", "domain"]

[[tool.importlinter.contracts]]
id = "rs-engines-independent"
name = "Reverie Saga concrete engine modules are independent"
type = "independence"
modules = ["engines.skeleton", "engines.trial", "engines.encounter", "engines.watch"]
```

Six-root order is high→low; current actual imports:domain none,contracts→domain,engines→contracts/domain,orchestration→contracts/domain,adapters→orchestration/contracts/domain,app→all lower. Engines never import each other. All four modules are required;10 registered classes currently expose20 public methods. `adapters` intentionally lacks `__init__.py`; its two child modules must appear. No init insertion, optional parentheses, ignore-imports or missing-root workaround. Multiple-root configuration is not claimed automatically exhaustive for future added roots/modules; refresh inventory at each order entry. External SDK/I/O bans remain existing Ruff/typed ownership requirements; this internal graph contract does not claim full G03 external-import qualification. An exact reviewed external prohibited-root contract is a later readiness item.

Toy fixture construction:under owned `probe_src`, make six named root directories; regular `__init__.py` everywhere except adapters; files `app/entry.py`, `adapters/port.py`, `orchestration/driver.py`, `contracts/port.py`, `domain/value.py`, four engine modules with literal ordinary import statements for the inventory edges, otherwise an innocuous constant. These are import-analysis fixtures, not mock engine outcomes. Prefix PYTHONPATH only that probe tree during each toy invocation; native cache disabled. Expected positive both KEPT; negative reverse domain→app, transitive reverse, direct/transitive engine dependency and TYPE_CHECKING reverse must produce their real offending chain. Removing adapters means missing-required-root failure, never compliant missing coverage. Preserve each exact source/command/output and classify separately.

## 6. Candidate G07 Collection / Commands

GOV-01 writes `<run_dir>\coverage.toml`, substitutes only the owned absolute data-file path (TOML literal string or correctly escaped path):

```toml
[tool.coverage.run]
branch = true
core = "pytrace"
source = ["src/engines"]
dynamic_context = "test_function"
data_file = ".pytest_cache/gov01-<run_id>/golden.coverage"

[tool.coverage.report]
ignore_errors = false
```

No omission/exclusion patterns suppress real engine methods. Toy coverage uses its own literal source/data_file override; supplemental run owns another data_file. Explicit pytrace avoids silently assuming an allowed C DLL; it is coverage.py's native supported Python tracer. Python3.13 sysmon does not support branch measurement, so is not this order's core. Record actual tracer/version/native executed lines and contexts; report branch percentages as diagnostic only, no invented95% gate. Planned G07 adapter consumes qualified native evidence; no project checker is implemented in GOV-01.

PowerShell execution examples, **NOT_RUN**; run_id chosen by executor, all files/variables must be initialized and within scope. Execute/check exit sequentially; examples name future executable paths, not installed tools:

```powershell
$govRun = Join-Path 'C:\Reverie Saga\.pytest_cache' ('gov01-' + [guid]::NewGuid().ToString('N'))
$govPython = Join-Path $govRun 'venv\Scripts\python.exe'
$govLinter = Join-Path $govRun 'venv\Scripts\lint-imports.exe'
$env:PYTHONPATH = 'C:\Reverie Saga\src'
$env:PYTHONHASHSEED = '0'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
& $govPython -m pip check
& $govLinter --version
& $govLinter --config (Join-Path $govRun 'imports.toml') --no-cache --show-timings
$env:COVERAGE_RCFILE = Join-Path $govRun 'coverage.toml'
& $govPython -m coverage debug sys
$govGolden = @(
 'tests/replay/test_golden.py::test_core_trace',
 'tests/replay/test_trial.py::test_trial_core_trace',
 'tests/replay/test_encounter.py::test_encounter_core_trace',
 'tests/replay/test_encounter.py::test_encounter_death_trace',
 'tests/replay/test_watch.py::test_watch_core_trace',
 'tests/replay/test_watch.py::test_watch_passive_trace'
)
& $govPython -m pytest --collect-only -q @govGolden
& $govPython -m coverage run --rcfile (Join-Path $govRun 'coverage.toml') -m pytest -q @govGolden --basetemp (Join-Path $govRun 'golden-temp') --junitxml (Join-Path $govRun 'golden-junit.xml')
& $govPython -m coverage json --rcfile (Join-Path $govRun 'coverage.toml') --show-contexts -o (Join-Path $govRun 'golden-coverage.json')
& $govPython -m ruff check src tests
& $govPython -m mypy --strict --no-incremental src tests
& $govPython -m pytest -q tests --basetemp (Join-Path $govRun 'full-temp') --junitxml (Join-Path $govRun 'full-junit.xml')
```

Run from workspace; preserve/restore prior task environment in finally. Capture each command's actual exit immediately, do not continue a dependent measurement after failure. The strict mypy command uses the exact reviewed installed Python-source finder fallback if native DLL is denied, with root redirected to the **isolated venv** and all flags preserved. Report execution mode; do not assert compiled-mode PASS. Native coverage debug must use the same explicit rcfile/config as collection when certifying tracer settings. Independent coverage toy negative output cannot be merged with positive data. No executable reporter in current authoring; future GOV-03 must specify bounded JSON/context parsing, malformed/missing/stale/duplicate/zero-hit errors before READY.

## 7. Acceptance / Limits / Next Promotion

GOV-01 acceptance:complete unchanged original pins +hashed candidate closure; Windows interpreter/namespace/native import/branch/context interfaces qualified; every independently specified positive/negative probe demonstrates its intended condition; real six-root graph complete and compliant; six golden tests pass,20 public method body records CURRENT/PASS; separate9-node combined evidence attributable without conflating goldens/supplements; full regression/Ruff/strict types pass; raw artifacts/hash binding/refresh/scope review complete. No arbitrary performance cutoff blocks compatibility discovery, but measure elapsed/startup/tracer overhead. B08 G03/G07 each3s,58+2≤60s full11 and DEV12GB remain **TARGET/UNVERIFIED**; historical263.97s full suite is not a60s qualification.

Unavailable wheel/network/interpreter or blocked grimp DLL → actual tool-support UNVERIFIED; no fake Python fallback for Rust. Invalid native config/schema, missing roots/methods/ranges, original13-pin conflict or actual gameplay failure → preserve diagnostics, diagnose in scope; no weakening of assertions/contracts. Evidence-tool failures and gameplay regressions are separate. No STOP for mere routine file/private naming choices; stop dependent qualification when the requirement cannot be proven.

GOV-02 readiness gaps:actual lock/native support from GOV-01; exact final shared config/diff/commands/negative fixtures; reviewed external SDK/I/O root contract; full protected-scope review and explicit execution authorization. GOV-03 gaps:qualified native schema/context/method-body evidence; exact typed adapter path/signature/error contract and independent malformed/stale/missing/definition-only fixtures; registered-method inventory refresh and consumer/live call path; successful real golden coverage. No future tool/helper/test existence claim.

G08 exact cost counters and300s profile cannot be inferred from current1..16s wait cap; G09 current-format saves/future-package rejection do not demonstrate historical migration transforms (historical corpus0); G10 observed fields/unused declarations/unconsumed values are different from body hits; G11 approved artifact corpus absent. CUST01/02 remain planned2,current0,max3; G07 native-evidence harness is not a third custom AST checker. Reporter/CI/hooks/markers/mutmut/devicebench remain separate future orders. Preserve all11 gate IDs and applicability truth; only existing actual checks can claim executed support.

## 8. Official Compatibility Sources

Checked2026-10-06; selected candidates, not native compatibility claims. [Import-linter2.15 release](https://pypi.org/project/import-linter/2.15/), [Grimp3.17 release](https://pypi.org/project/grimp/3.17/), [Coverage7.16.2 configuration](https://coverage.readthedocs.io/en/7.16.2/config.html). Import-linter/Grimp published Python>=3.10 metadata; Grimp has a cp313 Windows wheel. Actual complete dependency hashes/platform loading remain GOV-01 deliverables.

[Multiple-root configuration](https://import-linter.readthedocs.io/en/stable/get_started/configure/), [layers](https://import-linter.readthedocs.io/en/stable/contract_types/layers/), [independence](https://import-linter.readthedocs.io/en/stable/contract_types/independence/), [native CLI](https://import-linter.readthedocs.io/en/stable/get_started/run/), [Coverage contexts](https://coverage.readthedocs.io/en/7.16.2/contexts.html), [native CoverageData API](https://coverage.readthedocs.io/en/7.16.2/api_coveragedata.html). Installed pinned tool help/schema wins over moving documentation; incompatible interfaces are diagnosed before shared activation.

## 9. Authoring Acceptance — 2026-10-06

NEW:this order/input inventory. MODIFY:BACKLOG/SESSION_HANDOFF/roadmap register factual status. All production/tests/config/locks/fixtures/reference/spec/previous acceptance artifacts preserved; native tools/installation/policy/gates NOT_RUN. Document/inventory/link/scope checks recorded at delivery. Next:execute GOV-01 isolated native qualification. Self-review only; parent GOV remains IN_PROGRESS and later stage readiness remains incomplete.

Actual authoring checks:five UTF-8 documents/JSON,three balanced code fences,two TOML candidate blocks parsed,PowerShell example parsed,54 local Markdown links resolved;20 source method/range/hash records match actual unchanged engines and contain no nested function/class/lambda bodies. Pytest `--collect-only -q` for exact inventory9 nodes:9 collected in0.26s,exit0;collection is not test execution or coverage measurement. Full regression is not rerun for documentation-only work;previous1113-test acceptance remains linked historical evidence.139 entry hashes:136 identical,exact three allowed existing document differences;exact two NEW order/inventory files;HEAD unchanged. `git diff --check` exit0;preexisting tracked prompt/MASTER line-ending advisories retained. All candidate native probes/installation/G03/G07 execution remain NOT_RUN.

## 10. GOV-01 Execution / Acceptance — 2026-10-06

Director follow-up "다음꺼 ㄱ" authorized this isolated qualification. **SELF-REVIEW ACCEPTED/DONE** for GOV-01. Actual [execution evidence](RS-P1-GOV_01_QUALIFICATION.json) + [20-package hash lock](RS-P1-GOV_01_TOOLCHAIN.lock);raw artifacts at `C:\Reverie Saga\.pytest_cache\gov01-38e897b8ec174c24a4385361cdddc446`. §9 is historical authoring-only evidence;this section supersedes its NOT_RUN statements for isolated qualification. Shared G03/G07 policy/config/CI activation remains NOT_STARTED.

| Acceptance / actual native output | Result |
|---|---|
| Windows11 AMD64,CPython3.13.12/SQLite3.50.4;import-linter2.15/grimp3.17/coverage7.16.2 | Native imports,CLI versions/help,pip check PASS |
| Complete binary closure |20 pinned wheels/official release SHA256 verified;all original13 exact versions/wheel hashes preserved;new3 tools+click8.5.0/rich15.0.0/markdown-it-py4.2.0/mdurl0.1.2;ensurepip pip25.3 separate bootstrap |
| Independent import probes | Allowed both contracts KEPT;reverse/indirect/engine/indirect-engine/TYPE_CHECKING violations real BROKEN/exit1;missing adapters fails explicit missing package;namespace root retained without init insertion |
| Real native graph |51 modules/286 dependencies;all actual source modules and both namespace adapter children accounted for;root edges exactly match inventory;both internal contracts KEPT/exit0,process0.431s |
| Branch/context/body interface | Coverage JSON format3,absolute Windows paths,branch data and test_function contexts qualified;live standard trace identifies coverage.pytracer.PyTracer;coverage debug sys before collection has core-none and is not active-tracer proof |
| Independent called/definition-only toy | Called(False/True) returns1/2,executes body2..5/both branches;import-only executes definition1/no body/no branches,pytest passes but manual body verdict ZERO_HIT |
| Required six golden traces |6passed14.92s/process20.446s;all10 registered production engine classes/20 public bodies have native executable-line hits in named successful golden contexts;manifest boot-property and evaluate turn-body records separate |
| Supplemental joined combat/save/fresh load/foreign Gauge | Exact3nodes collected;3passed29.20s with separate coverage/JUnit;do not fill required golden holes |
| Regression / lint / types |1113passed253.15s/process253.833s,JUnit1113cases/no fail/error/skip;Ruff PASS;**native** mypy2.4.0 --strict --no-incremental PASS87files,5.531s;no source-mode fallback needed in this fresh isolated installation |
| Freshness / complete native record |11 independently specified probe checks qualified;46 command records retain exact exits/argv/cwd/allowlisted env/timings/raw log hashes;source/config/fixture/tool/lock binding and copied stale-input identity distinguish CURRENT/STALE |
| Scope |141 execution-entry files;137 protected inputs identical,exact4 permitted delivery-doc edits,2NEW qualification/lock artifacts;HEAD unchanged;shared environment still original13+pip25.3 |

Native layer output lists minimal direct violations for the indirect case;standard Grimp.find_shortest_chain separately confirms `domain.value→contracts.port→app.entry`. Negative contract exit1 is expected detection,not a swallowed tool failure. All raw outputs retained. One-off native Coverage.analysis2 statements intersect the fixed method body ranges before context hits;definition/import lines never count. Windows JSON paths normalize within the workspace. Supplemental parametrizedFalse/True share a test_function context;exact collected nodes and native JUnit identify both,while the six required goldens are individually named/unparametrized.

Resolved entry diagnostics remain FAIL records with linked successful replacements:initial ensurepip couldn't access/clean sandbox temporary directory (WinError5),fixed by run-owned TEMP/TMP and qualified base3.13.12;one premature pip probe found no pip before environment creation;default sandbox DNS caused misleading resolver "no distribution/conflict" output and actual urllib Errno11001;authorized outside-sandbox download/official metadata reads succeeded. No version loosening. First metadata probe erroneously called sqlite3.sqlite_version as a function;corrected native probe succeeded. No OS-policy change. Historical shared compiled-mypy failure is not erased or represented as a current isolated failure;fresh native strict check is measured PASS.

Same-snapshot six-golden uninstrumented run:6passed3.19s/process3.686s. Pytrace process20.446s is about5.55x this local baseline;G07 3s/full11 60s/device budgets remain TARGET/UNQUALIFIED. Diagnostic native coverage:246/273 statements90.11%,59/82 branches71.95%,combined85.92%;required20 body hits are the compatibility criterion,not blanket branch/field/semantic completeness. Raw artifacts must remain hash-identical/available for reuse;otherwise stale/unavailable. Native tools are installed only in the run's isolated venv. Original source/tests/assertions/fixtures/reference/spec/pyproject/shared lock/shared environment retained;no production API/schema,permanent helper/checker,marker/CI/hook/commit/push changes.

**NEXT:**author bounded source-specific GOV-02 shared dependency-control instruction and reviewable20-pin lock/native config proposal,including exact external SDK/I/O prohibition scope/negative fixtures. GOV-02/03 remain DRAFT until their remaining concrete contracts/readiness are finalized and execution authorized. G08/G09/G10/G11/report/mutation/client/world/NPC cognition/emotion/persona/BDI/memory/performance/release remain later;parent GOV IN_PROGRESS,B09 #6/#34 PARTIAL. Self-review is not independent-person/full-game/full11 acceptance.

Metadata review:colorama/markdown-it-py/mdurl/pathspec publish blank License/License-Expression fields. Preserve their official release license classifiers plus exact wheel license files/SHA256;do not invent SPDX expressions. All20 records now have nonempty sourced license/Requires-Python evidence. This is metadata qualification,not new artifact/import/license policy activation.

Final delivery validation:6 UTF-8 delivery files,2candidate TOML blocks,PowerShell example syntax,65 local Markdown links,ephemeral Python AST,all native artifact/wheel-license hashes and20method/source bindings PASS. Exact141entry scope comparison:137unchanged inputs/four allowed doc changes/two additions,HEAD unchanged;git diff --check exit0 (preexisting prompt/MASTER line-ending advisories only). Execution JSON276315bytes/SHA25639c80442d5e4027795ecee1160d2c125d336d599dfb975063571046e1a975761. Initial metadata delivery validation exposed missing license expressions;classifier/wheel-text evidence fixed that gap. A subsequent aggregation validation caught an intermediate-state overwrite;final evidence rebuilt from preserved actual runs and retains status/full JUnit/46native records/11checks/20methods. No raw run/source/test/lock values changed to repair validation.
