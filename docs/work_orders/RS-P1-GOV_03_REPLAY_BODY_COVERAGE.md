# RS-P1-GOV / GOV-03 — Native Golden Replay Body Coverage

Date:2026-10-07 | Executor/reviewer:Sol | Order:READY,self-reviewed | Implementation:NOT_STARTED | G07:NOT_ACTIVE | Parent:IN_PROGRESS

Director request "다음꺼 ㄱㄱ" completes the recorded NEXT **authoring** item. This document is an executable proposal, not execution authorization inferred from its text. NEXT:execute this bounded order when directed. No gameplay completion, independent review, CI deployment or eleven-gate activation.

## 1. Goal / Entry

One responsibility:provide a typed developer-only G07 command that collects the six existing successful golden replays with pinned coverage.py, then proves a nonempty executed-statement intersection for every registered public engine method body. A function definition/import/decorator hit, a high overall percentage, a passing unrelated test or a supplemental trace cannot satisfy it.

Prerequisites:[GOV-02 acceptance](RS-P1-GOV_02_DEPENDENCY_CONTROL.md#10-gov-02-execution--native-corrections--2026-10-07), [execution evidence](RS-P1-GOV_02_ACTIVATION.json), [staged controls](RS-P1-GOV_STAGED_CONTROLS.md), accepted representative CORE. Workspace C:\ReverieSaga;HEAD/main 35f3c45dbd73291879c92044cba52f99d13987d3. [Current input inventory](RS-P1-GOV_03_INPUT_INVENTORY.json) records151 entry hashes, existing dirty changes,20 reviewed body ranges, six exact node/context pairs and independent fixture expectations. Preserve prior dirty work.

Installed Windows CPython3.13.12/SQLite3.50.4;project interpreter C:\ReverieSaga\.venv\Scripts\python.exe, base C:\ReverieSaga\venv\python-3.13.12. Keep both. coverage7.16.2,pytest9.1.1,mypy2.4.0,Ruff0.16.6,import-linter2.15,grimp3.17;20 pinned dev packages plus pip25.3. No install/upgrade or shared configuration change.

Prior GOV-02 baseline:1192 tests PASS262.07s,Ruff PASS,strict mypy89files PASS with --no-native-parser,3 type-inclusive+1 runtime-only native import contracts PASS. These are historical baseline results, not rerun by authoring. Refresh exact hashes/installed versions/HEAD/status and run §8 baseline before implementation. An unexplained source/test/fixture/config/lock change stops execution; factual delivery-document differences are recorded separately.

## 2. Required Reads / Actual Consumers

Absolute prefix C:\ReverieSaga\ applies to every repository-relative path below.

- BACKLOG.md,SESSION_HANDOFF.md,docs\prompts\SOL_CODING_WORK_ORDER.md;architecture\BLOCK_01.md (AP-09/developer boundaries),BLOCK_07.md (native evidence/freshness),BLOCK_08.md (G03/G07/authority);staged order/GOV-02 acceptance and inventory.
- src\engines\skeleton.py,trial.py,encounter.py,watch.py:all10 registered classes,manifest properties/evaluate methods and their reviewed bodies.
- src\app\feature_registry.py:skeleton_bundle(EntityId("actor:toy"));trial_registry.py:trial_bundle();encounter_registry.py:encounter_bundle();watch_registry.py:watch_bundle().
- src\contracts\skeleton.py:FeatureBundle.bindings;src\contracts\turn.py:Engine,EngineBinding;src\app\headless.py:state_io,restore_checkpoint,replay_runner;src\orchestration\turn.py:Driver submit path;src\orchestration\replay.py:Runner.run.
- tests\replay\test_golden.py,test_trial.py,test_encounter.py,test_watch.py:the six nodes in inventory;their helper imports and independent fixture/hash/empty-mismatch assertions. Read tests\unit\{trial,encounter,watch}_fixtures.py and all referenced golden/vector inputs. All current src/tests/fixtures are fingerprinted, not just HEAD.
- pyproject.toml,.importlinter-runtime.toml,requirements-dev.lock;installed .venv\Lib\site-packages\coverage\{control,sqldata,jsonreport}.py pinned interfaces and native artifacts linked in inventory.

Live path:registry factory → FeatureBundle.bindings → headless.state_io reads engine.manifest → replay_runner injects _CheckpointFactory → Runner.run restores the same registered driver and submits original trace commands → orchestration.turn reads binding.engine.manifest and calls binding.engine.evaluate(invocation). Each selected test asserts replay mismatches == ();fixture/hash assertions remain unchanged. The developer command consumes coverage of this existing path;it is not called by production.

Deduplicate by full module.class.method key, NOT engine_id. Movement and EncounterMovement both use trial.movement. encounter/watch share two concrete classes;count each class once with both registry owners. Current10 classes/20 methods must all be present. Protocol/ABC/generated constructors/non-engine utilities are outside this inventory;real registered engine methods, including currently simple/stub-like bodies, receive no zero-hit exemption. Private watch helpers are not public engine methods.

## 3. Exact Future Edit Scope

NEW, not created by this authoring task:

| Absolute path | Sole role |
|---|---|
| C:\ReverieSaga\tools\__init__.py | Empty developer package marker |
| C:\ReverieSaga\tools\replay_body_coverage.py | Typed G07 producer/native adapter/CLI and tracer observation hook;no AST checker/framework/general gate runner |
| C:\ReverieSaga\tools\replay_body_inventory.json | Reviewed schema1 method/registry/source/node inventory defined below;copy approved ranges,not empirical hit lists |
| C:\ReverieSaga\tests\governance\test_replay_body_coverage.py | Independent boundary/negative/native toy and real-command integration tests |
| C:\ReverieSaga\docs\work_orders\RS-P1-GOV_03_ACTIVATION.json | Actual execution summary,not a fabricated current evidence file |

MODIFY only factual dated acceptance/status/next-action sections: C:\ReverieSaga\docs\work_orders\RS-P1-GOV_03_REPLAY_BODY_COVERAGE.md,RS-P1-GOV_STAGED_CONTROLS.md,IMPLEMENTATION_ROADMAP_ORDERS.md;C:\ReverieSaga\BACKLOG.md,SESSION_HANDOFF.md.

Owned ephemeral outputs:NEW uniquely named C:\ReverieSaga\.pytest_cache\gov03-<32-lowercase-hex> directory,created exclusively after containment checks;native configs/logs/JUnit/data/JSON/results/toy cases belong there. The run ID is an execution value,not an unresolved design placeholder. Never reuse/overwrite another run or recursively clean it.

READ ONLY:all existing src/tests/fixtures/oracles/specs/reference/architecture/prompt/AGENTS,shared TOML/lock/.venv/base Python,previous evidence/authoring inventories. No skip/delete/xfail/assertion weakening,markers,CI/hooks,agents,commit/push,OS-policy changes,report framework,G08–11/custom checker or gameplay/schema change. No extra modules without re-review.

tools is a developer-only root,not a seventh production layer. Include tools explicitly in Ruff/mypy invocations;production G03 already forbids core imports of tools/coverage/pytest. Do not alter native contracts to grant exemptions. For Ruff's globally banned time/os.environ APIs,use perf_counter via a local import and a copied subprocess environment through os.environ.copy() with a narrowly justified inline TID251 suppression at those developer-boundary uses only. No file-wide ignore/Any/mypy ignore or shared rule weakening.

## 4. Public Typed Contract / Formats

Implement these frozen,slots DTOs and signatures in the NEW developer module. No mutable input/output aliases or domain Any. Internal helper names are executor discretion.

```python
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import pytest

@dataclass(frozen=True, slots=True)
class MethodHit:
    key: str
    path: str
    body_start: int
    body_end: int
    executable_lines: tuple[int, ...]
    hit_lines: tuple[int, ...]
    golden_contexts: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class ReplayCoverageResult:
    status: Literal["PASS", "FAIL", "UNVERIFIED"]
    freshness: Literal["CURRENT", "STALE", "UNKNOWN"]
    code: str | None
    detail: str
    methods: tuple[MethodHit, ...]

def run_gate(project_root: Path, run_dir: Path) -> ReplayCoverageResult: ...
def assess_run(project_root: Path, run_dir: Path) -> ReplayCoverageResult: ...
def pytest_sessionstart(session: pytest.Session) -> None: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

run_gate is the sole writer/producer:creates an exclusively owned run,invokes native subprocesses,records evidence and returns a result. assess_run reads ONLY and never runs tests,changes source/data or reconstructs missing evidence. The hook is loaded only by the explicit covered child with -p tools.replay_body_coverage;it observes sys.gettrace(),prints one RS_G07_TRACER JSON line containing module="coverage.pytracer",class="PyTracer",version="7.16.2". sys.gettrace().__self__ type provides in-flight proof;configured core alone or pre-run debug core=None is insufficient. No collection/outcome mutation by the hook. main:required subcommand run|assess and required --project-root/--run-dir;no ambient path/data fallback. Module entry uses SystemExit(main()).

CLI exit0=PASS/CURRENT;exit1=valid current evidence with any ZERO_HIT;exit2=UNVERIFIED or CLI/input/tool/freshness error. Print exactly one result JSON object to stdout;native output goes to files. Error details bounded4096 characters,contain path/phase/key but no environment dump/credentials. run writes result.json even on a recorded failed child;assess prints only. Missing/uncreatable run directory may yield an error on stdout without a file;never claim that evidence was written. Unexpected programmer exceptions are not swallowed into PASS.

Runtime inventory JSON exact keys:schema_version=1,source_sha256:{the four POSIX engine source paths:64 lowercase hex},golden_nodes:[{node_id:str,context:str}],methods:[{key:str,path:str,definition_line:int,body_start:int,body_end:int,registries:list[str],engine_id:str}]. Exactly the20 authoring inventory records and six pairs;arrays methods sorted by key,node pairs preserve §7 command order,registries sorted/unique. body_start/end are inclusive,1-based source line numbers;definition_line<body_start<=body_end<=actual file line count. For current manifests,body_start==body_end is valid. No hit lists become required-output oracles.

Run descriptor run.json exact schema1 keys:
schema_version,run_id,project_root,baseline_head,python,packages,inputs_before,inputs_after,inventory_sha256,config_sha256,phases,artifacts.
python={executable:str,version:str};packages={normalized_distribution_name:str_version};baseline_head=40hex informational provenance,not sole freshness key.
inputs_before/after={POSIX_relative_path:64hex};include all regular files recursively in src/tests/tools,excluding __pycache__/bytecode only,plus pyproject.toml,.importlinter-runtime.toml,requirements-dev.lock. Compare the whole enumerated set,not just listed hashes. docs are delivery,not executed inputs. No symlink/reparse escape or case-fold collision.
phases is exactly collect,golden,json,each {id:str,argv:list[str],cwd:str,environment:{allowlisted_key:str},exit_code:int|null,elapsed_seconds:finite nonnegative float}. Null exit only never-started/interrupted child;cannot qualify. Required environment keys PYTHONPATH,PYTHONHASHSEED,PYTEST_DISABLE_PLUGIN_AUTOLOAD,PYTHONIOENCODING,TEMP,TMP.
artifacts is exactly {relative_owned_filename:{sha256:64hex,bytes:int}|null} for coverage.toml,collect.log,golden.log,golden.junit.xml,golden.coverage,golden.coverage.json,json.log. Null means not produced after a real recorded failed/not-started phase;successful assessment rejects null as ARTIFACT_MISSING. Never fill null with invented bytes/hashes. run/result JSON are not self-hashed. Record actual versions with importlib.metadata,including bootstrap pip;compare current set/versions when assessing. Fixed Python3.13.12/coverage7.16.2/pytest9.1.1 are mandatory.

Result JSON exact keys schema_version=1,gate="G07",status,freshness,code,detail,methods;method records have all MethodHit fields,tuples encoded as arrays. code=None only PASS;FAIL code=ZERO_HIT with all zero-hit keys listed in sorted detail. On preflight invalidity methods=[];do not present partial observations as all-method acceptance.

Boundary decoding:UTF-8 JSON,duplicate object keys/nonfinite constants/unknown descriptor or inventory fields rejected;immediately narrow json.loads output through checked object values into the DTOs. Native coverage JSON is retained/hash-bound for audit,not parsed into a second parallel coverage algorithm. Its observed format3/version7.16.2 has Windows-backslash keys and legitimate empty-string regions;those are NOT malformed inventory IDs. SQLite data is read only through coverage public APIs,not direct SQL/private tables.

Bound artifacts16MiB each,total64MiB;descriptor/inventory4MiB each;input paths1024;methods256;contexts4096;positive source lines<=1,000,000;argv128 entries/4096 characters per entry. Current inputs fit. Reject bool as int,negative size/elapsed/nonpositive line,duplicates in identity lists,empty inventory/nodes/denominators,invalid hex,unexpected/missing fields. Whitespace-only/invalid UTF-8 JSON/XML and empty/malformed binary native data are errors;SQLite coverage data is not UTF-8 text. These are developer evidence caps,not gameplay caps or measured device budgets.

## 5. Native Adapter / Freshness / Error Policy

Use public pinned coverage.Coverage(config_file=str(run_dir/"coverage.toml"));load();get_data();CoverageData.has_arcs(),measured_files(),measured_contexts(),set_query_contexts(None),contexts_by_lineno(filename);Coverage.analysis2(filename)->(filename,statements,excluded,missing,missing_text). Never replace native executable-line analysis with custom AST/reachability,overall percentages,JSON function start_line or executed definitions.

Supported interfaces were read in the installed7.16.2 source and exercised by the current probe. Dynamic test_function contexts exclude the empty import-time context. Exact context equality is required,not regex substring or startswith. See [coverage context contract](https://coverage.readthedocs.io/en/7.16.2/contexts.html) and [public CoverageData interface](https://coverage.readthedocs.io/en/7.16.2/api_coveragedata.html). Native JSON format3 is diagnostic provenance;unsupported installed/native versions cannot silently pass.

Assess in order:

1. Validate root/run ownership,versions,schema/types/caps and required artifacts. Resolve project_root to its absolute canonical directory;production invocation uses this actual workspace. run_dir must be its direct .pytest_cache/gov03-32hex child. Isolated test projects may exercise read-only helpers/assessment with fully pinned copied inputs and actual current interpreter provenance;they do not redirect the production command. Reject traversal,absolute artifact names,drive/UNC substitutes,symlinks/reparse points and case-colliding paths. Normalize native measured Windows paths to exact current engine paths;reject outside roots/collisions rather than merging filenames case-insensitively. Return UNVERIFIED/UNKNOWN on error.
2. Validate artifact bytes/hashes,inventory/config hashes,exact phase commands/cwd/env,whole current input set against both snapshots and installed package set/versions. Before==after==current required. Different current source/config/test/fixture/tool/input set:UNVERIFIED/STALE STALE_INPUT. Unavailable evidence:UNKNOWN,not STALE or FAIL/ZERO_HIT. Documentation-only drift does not invalidate executed inputs.
3. Compare runtime registry union with reviewed manifest. Enumerate the actual four bundle factories and engine concrete class identities;public callable/property methods including inherited methods must match the entire reviewed key set. Resolve property.fget/callables with inspect;check source filename/hash and names. Generated constructors/private helpers do not count. Reject unsupported callable types or code objects nested in method code constants;current methods have none. Source/range changes need re-review,not automatic manifest regeneration. No imports of test-only Gauge engines and no deduplication on engine_id.
4. Require collect exit0 and exact six collected node lines/no extras/duplicates;golden exit0;all six exact native JUnit classname/name pairs once,zero failure/error/skipped elements and six counted cases. Reject DTD/entity declarations before stdlib ElementTree parsing;no network/external entities. Failed setup/teardown/skip/xfail/xpass/count0/extra case cannot qualify even with positive data. Also reject native golden summary XPASS/xpassed diagnostics:JUnit alone can encode non-strict XPASS as success. Existing pinned six golden tests have no xfail markers. json phase must exit0. Require exactly one authentic producer-bound tracer marker with the pinned active type/version.
5. Coverage branch data present;measured contexts may include empty plus these exact six only. All six qualified contexts must be present. Unexpected contexts,filtered/foreign data,unmeasured required file,no executable statement for a reviewed body or invalid native line data are UNVERIFIED. Require the four measured engine source paths;optional measured __init__.py is ignored for method counting.
6. For each method,let S=native statements intersect [body_start,body_end]. Verify no excluded line within its reviewed body;reject an exclusion rather than silently removing obligation. H={line in S whose native contexts contain at least one of that method's qualified golden contexts}. Qualified contexts are node pairs whose bundle owns that class:skeleton1,trial1,encounter4,watch2. Sort S,H and union of contributing qualified contexts. Definition/decorator/import/nonstatement/empty-context/unrelated/supplemental hits do not count. H nonempty means method body HIT,not100% line/branch coverage. Report manifest boot-method and evaluate turn-method separately.
7. Empty H for any current method returns FAIL/CURRENT/ZERO_HIT with complete20 method observations;all positive yields PASS/CURRENT/code=None. Recheck current fingerprints/artifact hashes after read/analysis;change during assessment is STALE,not a raced PASS.

Error codes,deterministic precedence following the above sequence:INVALID_PATH,UNSUPPORTED_VERSION,MALFORMED_EVIDENCE,BOUNDS,ARTIFACT_MISSING,ARTIFACT_HASH,STALE_INPUT,INVENTORY_MISMATCH,INVALID_RANGE,SELECTION_MISMATCH,REPLAY_FAILED,TRACER_MISMATCH,NATIVE_ERROR,MISSING_FILE,MISSING_CONTEXT,EMPTY_BODY,EXCLUDED_BODY,ZERO_HIT. Multiple errors:report first stage then lexical path/key;no uncontrolled exception text. Normal IO/Unicode/JSON/XML/CoverageException/value/schema failures become the applicable typed error;programming bugs remain visible nonzero. Source/config drift is not a gameplay replay failure. This is accidental-staleness detection,not malicious tamper-proof signing.

## 6. Producer / Wiring / Ownership

run_gate rejects existing run_dir,creates it and private temp directory exclusively;no erase/combine/cached-data reuse. Freeze all executed inputs and installed package versions before collection;validate reviewed inventory/live registries before spawning. Build allowlisted recorded environment,inherit OS essentials,override PYTHONPATH=<project>/src;<project>,PYTHONHASHSEED=0,PYTEST_DISABLE_PLUGIN_AUTOLOAD=1,PYTHONIOENCODING=utf-8,TEMP/TMP=<owned>/temp;remove inherited PYTEST_ADDOPTS and COVERAGE_* overrides. No parent environment mutation. Native subprocess argv are lists,shell=False,cwd=project_root,sys.executable must equal the explicit project interpreter. Capture elapsed perf_counter seconds and exits;failure stops subsequent phases,which retain null exit/zero not-run duration and intended argv.

Private coverage.toml literal below;substitute only the owned absolute golden.coverage path. No shared coverage activation.

```toml
[tool.coverage.run]
branch = true
core = "pytrace"
source = ["src/engines"]
dynamic_context = "test_function"
data_file = ".pytest_cache/gov03-00000000000000000000000000000000/golden.coverage"

[tool.coverage.report]
ignore_errors = false
```

The all-zero ID above demonstrates TOML syntax only;producer always uses its own unique supplied ID and absolute data path. Compare parsed config to exactly these keys/values with the actual data path;no exclude/filter/omit/plugin/parallel/append override.

Execute:
collect:python -m pytest --collect-only -q <six nodes>.
golden:python -m coverage run --rcfile <owned coverage.toml> -m pytest -q -s -p tools.replay_body_coverage --junitxml <owned golden.junit.xml> <six nodes>.
json:python -m coverage json --rcfile <owned coverage.toml> --show-contexts -o <owned golden.coverage.json>.
The <> operands here are fixed producer-owned path/node substitutions described above,not discretionary test selection.

Freeze after inputs,write run descriptor atomically inside owned directory,then call the same assess_run used by read-only CLI and integration tests. On earlier failure retain actual logs/exits/input snapshots and UNVERIFIED result;do not manufacture missing native files to reach assessment. Public APIs never open a game DB/change an engine/rewrite a fixture.

G07 is a stage-local developer command consuming real goldens,not an installed hook or full gate orchestrator. No new pytest marker. G05/G07 evidence reuse in the later11-gate runner is deferred;current runner collects its own exact six and cannot accept a caller-supplied selection. Supplemental integration/Gauge traces remain distinct regression only.

## 7. Independent Tests / Examples

NEW test module tests\governance\test_replay_body_coverage.py. Use literal requirements from inventory,not adapter-produced expected values or patched production outcomes.

- test_body_intersection_cases:CALLED_BOTH lines2,3,4,5→H=(2,3,4,5);PARTIAL_BODY_COUNTS→H=(2,3) still HIT;definition-only line1,empty context only,and nonstatement hit→H=(),ZERO_HIT. SINGLE_LINE_BODY53..53→(53,),valid boundary. One qualified executed statement is enough;percentage threshold NOT_APPLICABLE.
- test_native_called_and_import_only:write the independent five-line branch fixture in tmp_path,run actual pinned coverage/pytest with branch/pytrace/test_function in separate new data files;True returns1,False returns2;analysis2/body intersection lines2..5 present for called tests;import-only test succeeds but no body lines. Preserve native logs;do not forge SQL or mock coverage outputs. These test-only contexts never fill production holes.
- test_schema_and_bounds:duplicate JSON keys/unknown/missing fields/bool lines/badhex/NaN/zero or inverted ranges/excess16MiB artifact/4MiB descriptor,at-cap accepted scalar inputs then cap+1 rejected;immutable DTO/order deterministic. No fake gameplay tests.
- test_freshness_and_paths:copy fixture evidence to isolated test project,change one exact source byte or config/fixture/tool/hash/add/delete input;STALE_INPUT/STALE. Missing raw file→ARTIFACT_MISSING/UNKNOWN;changed hash→ARTIFACT_HASH;../,absolute/UNC,outside root/case-collision→INVALID_PATH. Symlink case either proves rejection when creation permitted or records unsupported test capability explicitly;never silently claims that branch tested.
- test_collection_and_replay_results:omit/add/duplicate a node/JUnit pair,0cases,skip/xfail/failure/error/setup/teardownfailed,exitnonzero despite hits→SELECTION_MISMATCH or REPLAY_FAILED as stage order specifies. DTD/entity malformed→MALFORMED_EVIDENCE. Exact six success required.
- test_native_data_rejections:malformed database/unsupported version/branch absent→NATIVE_ERROR or UNSUPPORTED_VERSION;unmeasured file→MISSING_FILE;missing qualified context→MISSING_CONTEXT;no native executable statements→EMPTY_BODY;excluded body→EXCLUDED_BODY;positive hits under foreign/supplemental contexts are rejected,not a PASS.
- test_registry_completeness:two distinct Movement classes with same engine_id remain four obligations;encounter/watch shared classes do not duplicate;omitted/additional public method/class→INVENTORY_MISMATCH,not allowed exemption;nested code→INVALID_RANGE.
- test_cli_real_golden_gate:one actual producer invocation in new owned run,all six pass,exact20 observations all hit in their qualified contexts,before/after source hashes unchanged;read-only assess gives same result and does not change files. CLI0/1/2 verified using valid/zero-hit/invalid evidence fixtures;existing directory rejected,preserving prior sentinel bytes. Test subprocess uses actual native tools,not engine monkeypatches.
- test_failure_retains_evidence:actual malformed owned config/invalid child invocation produces recorded nonzero/tool error,no PASS,no invented artifacts;assess missing descriptor fails safely. Do not change shared config to induce errors.

Golden nodes fixed command order:
```text
tests/replay/test_golden.py::test_core_trace
tests/replay/test_trial.py::test_trial_core_trace
tests/replay/test_encounter.py::test_encounter_core_trace
tests/replay/test_encounter.py::test_encounter_death_trace
tests/replay/test_watch.py::test_watch_core_trace
tests/replay/test_watch.py::test_watch_passive_trace
```

Method scalar units:source lines integer1-based;hash bytes SHA256;elapsed seconds floating finite;artifact caps bytes. Gameplay units/fixed-point/tie RNG/math NOT_APPLICABLE:runtime unchanged. Sort methods/contexts/line sets deterministically;no source-order tie for duplicate identity—reject it.

## 8. Baseline / Execution Verification Commands

PowerShell cwd C:\ReverieSaga. Use explicit interpreter;do not use denied generated lint-imports.exe or the blocked mypy native parser. Run baseline before implementation with src/tests;after implementation include tools.

```powershell
$env:PYTHONPATH = 'C:\ReverieSaga\src;C:\ReverieSaga'
$env:PYTHONHASHSEED = '0'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$gov03Python = 'C:\ReverieSaga\.venv\Scripts\python.exe'
& $gov03Python -m pip check
& $gov03Python -m ruff check src tests
& $gov03Python -m mypy --strict --no-incremental --no-native-parser src tests
& $gov03Python -c 'from importlinter.cli import lint_imports_command; lint_imports_command()' --config pyproject.toml --no-cache
& $gov03Python -c 'from importlinter.cli import lint_imports_command; lint_imports_command()' --config .importlinter-runtime.toml --no-cache
& $gov03Python -m pytest -q
```

Each command must exit0,full baseline1192 with no fail/error/skip;record each separately,do not let a later PowerShell success hide earlier failures. After editing:

```powershell
& $gov03Python -m ruff check src tests tools
& $gov03Python -m mypy --strict --no-incremental --no-native-parser src tests tools
& $gov03Python -m pytest -q tests/governance/test_replay_body_coverage.py
& $gov03Python -m pytest -q
$gov03RunPath = Join-Path 'C:\ReverieSaga\.pytest_cache' ('gov03-' + [guid]::NewGuid().ToString('N'))
& $gov03Python -m tools.replay_body_coverage run --project-root 'C:\ReverieSaga' --run-dir $gov03RunPath
& $gov03Python -m tools.replay_body_coverage assess --project-root 'C:\ReverieSaga' --run-dir $gov03RunPath
git diff --check
```

Also rerun both native import contract commands after edits and the three existing supplemental nodes listed in GOV-02 input inventory,without folding their hits into G07. Full suite must preserve1192 existing cases plus actual new collected tests;do not invent a required new count before implementation. Report strict type-file count observed,not guessed.

Performance:record native phases and total run duration honestly;G07 3s/full11 60s remain TARGET,not acceptance timeouts. Current covered goldens12.82s/process13.2852s do NOT qualify3s;no shortening/skipping tests or changing core/version to meet target. Memory/device performance NOT_MEASURED;do not infer laptop qualification from timings.

## 9. Acceptance / Stops / Delivery

Accept code only with all four NEW developer/test files,exact typed public contract/native API use,independent rejection cases,fresh real CLI and read-only assessment PASS/all20 body hits,whole1192+new regression,Ruff/strict mypy/native G03 PASS,reviewed diff and protected input hashes. Source/test fixture bytes and all shared policies/config/lock/environment unchanged except expressly NEW files. Record all actual subprocess commands/exits/timings/log hashes and limitations in NEW activation JSON schema1:{task_id,baseline_head,run_id,status,input_sha256,runs,artifacts,methods,verification,scope,limitations};fields hold actual facts,not a second gate decision algorithm. Preserve raw logs;later unavailability remains UNKNOWN.

Stop with concrete evidence if baseline fails,registered inventory/ranges change,versions/native support unavailable,caps insufficient,protected inputs overlap,real goldens fail or zero-hit,tool root needs unapproved global exemption,or implementation needs another public interface/module/policy. Exhaust safe in-scope diagnostics first;no native-version upgrade/source rewrite/assertion weakening/unapproved agent. ZERO_HIT is genuine failure;missing evidence is UNVERIFIED. Order text never authorizes commit/push or later controls.

Acceptance means only local G07 command and its tests;shared G03 remains accepted,parent GOV remains IN_PROGRESS. Timing/hardware/full11/CI/counters/access/migration/artifacts/reports/full-game and independent-person review remain UNQUALIFIED. State the next bounded unmet item from source/evidence,not automatic activation of another gate.

## 10. Authoring Evidence / Current Outcome

Authoring current probe:owned .pytest_cache/gov03-authoring-a40b98cd07f240a2af8f09db38b2c66b. Real six nodes collected exit0/0.10s;coverage goldens exit0/6passed12.82s,process13.2852s,JUnit6/0fail/0error/0skip. Running tracer coverage.pytracer.PyTracer7.16.2 observed during pytest_sessionstart. Native branch data/empty+six exact contexts/public analysis2 verified;all20 current bodies have qualified positive hits. Native JSON export exit0/format3/show_contexts/branch true;Windows backslash filenames/empty-string regions verified. One-off AST inspection enumerated reviewed source ranges only;no permanent checker added.

[Input/evidence inventory](RS-P1-GOV_03_INPUT_INVENTORY.json) pins151 entry files,exact20 reviewed ranges/current native statements and observations,actual commands/environment/elapsed/log/raw hashes and independent fixture expectations. Observations are not newly invented gameplay oracles. Six native files are existing goldens;no source/test edit or supplemental coverage substitution.

Authoring checks PASS:6 UTF-8 deliverables,strict JSON/3 TOML fences/1 Python interface compile/3 PowerShell parses,100 existing local links,20 exact source ranges/native positive bodies and6 independently specified example intersections. All151 entry hashes compared:147 protected inputs unchanged,exact4 factual-doc changes plus2 NEW authoring artifacts;HEAD unchanged,git diff --check exit0. Future harness/test/runtime inventory/activation files confirmed absent. Current task-specific added/changed delivery lines self-reviewed against entry snapshots;prior dirty work preserved.

Validation logs/command/provenance are recorded in inventory.authoring_validation. The six example intersection arithmetic checks validate literal requirements only,not the future G07 implementation/rejection test suite. No full-suite/Ruff/mypy rerun for this documentation-only authoring;previous1192 results are explicitly historical. GOV-03 order READY does not mean harness implemented/G07 active. Self-review only.
