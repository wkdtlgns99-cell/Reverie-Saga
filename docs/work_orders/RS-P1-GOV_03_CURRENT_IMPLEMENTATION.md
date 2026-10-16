# GOV-03 — Current Replay Body Coverage Implementation

Date:2026-10-16 | LOCAL_ACCEPTED,self-reviewed | Implementation:DONE,local command | CI activation:NOT_ACTIVE.
Authored under [GOV-03R](RS-P1-GOV_03_SCOPE_REFRESH_2026-10-16.md);executed on the director's next-task request.
Primary7 engineering support;no gameplay/CI/release/independent-review acceptance.

## Contract and Baseline

The [original producer/assessor order](RS-P1-GOV_03_REPLAY_BODY_COVERAGE.md#4-public-typed-contract--formats)
supplies all DTOs,CLI,ownership,strict parsing,bounds,error precedence,native API,freshness,
negative tests and acceptance requirements. Apply the replacements below;all other obligations
remain mandatory. Old20method/four-source/six-trace/no-nested assumptions are historical.
Scope SSOT:[current authoring manifest](RS-P1-GOV_03_SCOPE_2026-10-16.json).

Reviewed scope baseline:0e06577;execution baseline:4257d4f864867541772237922c9acd70da926e78,clean checkout.
Previous F21–24/docs/R1/F22work is preserved in that local commit;no remote publication occurred.
At execution refresh actual HEAD/status,installed package set and whole input hashes before edits.
Require reviewed source/factory/nested identities to match;never regenerate inventory from hits.
No new dependency/marker/shared config/CI/runtime/save/approval change is authorized by this order.

Entry correction2026-10-16:the live selected tests also read five JSON fixtures under docs.
The architecture's [executed-input freshness contract](../../architecture/BLOCK_07.md#b22-evidence-identity--truth--three-way-verification)
requires these actual transitive inputs;the previous blanket docs exclusion was incorrect.
Include exactly docs/work_orders/PHASE0_REFERENCE_VECTORS.json,
docs/work_orders/RS-P1-CORE_02_REFERENCE_VECTORS.json,
docs/work_orders/RS-P1-CORE_03_REFERENCE_VECTORS.json,
docs/work_orders/RS-P1-CORE_04_REFERENCE_VECTORS.json and
docs/reviews/QT-F07_DIALOGUE_EXAMPLE.json in both input snapshots/current checks.
Their contents and independent expected values remain read-only;other delivery docs remain excluded.
Add a source-drift negative for each file. Schema/result/error/API contracts are unchanged.
Keep pytest-owned cache/temp in the exclusive run:both pytest phases add
-o cache_dir=<run>/pytest-cache;golden adds --basetemp <run>/pytest-temp.
These fixed producer-owned operands are part of exact phase validation,not caller-selected options.
Delivery routing correction:docs/ENGINEERING_ENFORCEMENT.md may receive a factual local-command
availability pointer only. Existing automated CI/check activation and all other policy stay unchanged.

## Current Binding Replacements

| Contract | Current value |
|---|---|
| inventory |12concrete classes,35public member obligations,8resolved source files;full concrete module.class.member key. Never deduplicate on engine_id;shared factories do not duplicate a key |
| factories | skeleton_bundle(actor:toy),trial_bundle(),encounter_bundle(),watch_bundle(),quest_bundle(approved_content),memory_bundle(approved_content). Actual production EngineBinding sites reviewed;new/unlisted factory/member→INVENTORY_MISMATCH |
| content | Discover quest/memory using content/dialogue/harbor-memory-v1.json,its tracked .sha256 and canonical harbor definition. Replay fixture catalogs retain their own independent pins;never repin content or saves |
| source paths | Six engines modules plus domain/scenario.py and contracts/dialogue.py;exact8hashes in runtime_inventory.source_sha256. Inherited getters remain concrete-class obligations with explicit resolved implementation |
| selection | Exactly8ordered node/context/registry rows in runtime_inventory.golden_nodes:original6goldens plus current quest vector replay and NPC-memory retry/save/load/offline replay. No caller-supplied selection |
| qualified contexts | Union nodes whose registry occurs in the method's complete registries list:skeleton1,trial1,encounter6,watch4,quest2,memory1. New2traces are mandatory coverage,not supplemental substitutes |
| native config | source=["src/engines","src/domain","src/contracts"],branch=true,core=pytrace,dynamic_context=test_function,owned absolute data_file. No omit/exclude/filter/plugin/parallel/append override;other measured files diagnostic only;require8resolved files |
| body criterion | Native analysis2statements intersect reviewed inclusive body range;qualified nonempty H required. Definition/decorator/import/nonstatement/empty-context hits remain invalid. No percentage threshold or missing-property exemption |
| nested objects | Only3exact reviewed <genexpr> entries admitted within enclosing body/source hash. Compare name,qualname,first_line,policy and nested-object set exactly. Missing/extra/changed nested code→INVALID_RANGE/INVENTORY_MISMATCH or STALE_INPUT per existing stage precedence;no named/lambda/helper exemption |
| limits | Same MethodHit/ReplayCoverageResult/result/run descriptor/CLI/error schemas and original caps,with35method/8node/8file obligations. Same freshness/error stage ordering and final recheck |

Reviewed generators:Movement.manifest builds read tuples;QuestRules.manifest builds phase accesses;
QuestRules.evaluate wraps emitted facts. All lie within enclosing reviewed bodies. This is a
source-bound allowance,not a general nested-code waiver. Native source-line/context evidence
does not prove every branch,generator iteration,instance or read/write access;shared getter hits
qualify the reviewed member without asserting separately observed per-instance invocations.

## Exact Runtime Manifest and Freshness

Create tools/replay_body_inventory.json from the authoring manifest's runtime_inventory object,
not its provenance/native_probe wrapper. Exact root keys:schema_version=2,source_sha256,golden_nodes,
methods. Source map has exactly8POSIXpaths. Eight ordered node objects have exact keys node_id,
context,registry.35sorted method objects have exact keys key,implementation,path,definition_line,
body_start,body_end,registries,engine_id,nested_code. Nested objects have exact name,first_line,
qualname,policy;policy literal=reviewed_generator_expression_within_enclosing_body. Preserve
original strict UTF8/duplicate/unknown/nonfinite/exact-type/range/cardinality/path checks.
Native observed statement/hit lists are evidence,never expected-output oracles.

Run descriptor/result retain schema_version1;inventory_sha256binds this runtime schema2file.
MethodHit.path is the resolved implementation file,including inherited files. Whole executed-input
snapshots include all regular src/tests/tools/content files,excluding __pycache__/bytecode only,
plus pyproject.toml,.importlinter-runtime.toml,requirements-dev.lock. This includes new factory
catalog/pin dependencies. Source/config/content/test/tool set changes mean STALE_INPUT;do not
include other docs/Unity/private ignored saves/credentials as gate inputs. The five executed
document fixtures listed in the entry correction are mandatory. Original path/case/reparse/
artifact/cap/package protections remain. No current total input count is a permanent oracle.

Collect/golden/JUnit require exactly8nodes/pairs once,zero failures/errors/skips/XPASS;native
contexts may be empty plus exactly8. Require one authentic active PyTracer7.16.2marker and branch
data;use public coverage APIs. Preserve original run.jsonphase/artifact/environment contracts.
Missing evidence is UNKNOWN,source drift STALE,qualified zero-hit FAIL;never fold them into PASS.

## Files, Tests and Acceptance

NEW under C:/ReverieSaga:tools/__init__.py,tools/replay_body_coverage.py,
tools/replay_body_inventory.json,tests/governance/test_replay_body_coverage.py,
docs/work_orders/RS-P1-GOV_03_ACTIVATION.json. Allowed factual delivery updates:this order,original
current-entry note,staged controls,IMPLEMENTATION_ROADMAP_ORDERS.md,BACKLOG.md,SESSION_HANDOFF.md,
GAME_SYSTEM_SUMMARY_KO.md,and the factual enforcement-map pointer specified above.
Existing production/tests/fixtures/authorities/config/locks/old inventories
remain protected. Owned runs retain original direct .pytest_cache/gov03-32hex boundary;no erase/
cached reuse. No production import of tools and no source/fixture changes to manufacture hits.

Apply original §7native toy/negative/CLI/freshness/error tests and §8commands against current scope.
Add missing quest/memory/getter owners,foreign implementation,missing/extra new contexts,changed
inherited source/content,and unreviewed nested callable negatives. Exact3generators and inherited
getters need positive cases;six-only evidence must reject rather than omit15obligations. Native
APIs and independent literal oracles remain mandatory;no mocked domain outcomes/probe-hit oracles.

At entry run actual full pytest baseline/collection;1787currently collected is not a full-suite
pass or permanent count. Preserve every existing case plus actual additions. Qualify new governance
tests,real producer+read-only assess equivalence and full regression;README Ruff both/scoped format/
strict mypy/imports/pip,including tools explicitly. Preserve baseline/failure/environment evidence.
Acceptance needs35positive bodies from8successful traces,current full input/package/artifact closure,
independent rejection tests,full/static PASS,self-reviewed scope and three-progress consistency.

Original §9stops remain,plus unresolved current factory/content/nested semantics. Native scope
probe covered process52.96s;3s/all11/device budgets remain TARGET/UNQUALIFIED. CP01–05unchanged,
V3stopped PARTIAL,CP06held. No independent review/CI/counters/release/commit/push/agent/provider or
next gate activation. Local command acceptance does not install CI/hooks or activate all11gates.

## Execution — 2026-10-16

[Actual evidence](RS-P1-GOV_03_ACTIVATION.json):LOCAL_ACCEPTED,self-review;primary7support,related2/6.
Typed producer/read-only assessor/CLI and schema2runtime inventory implemented;110new tests PASS.
Actual root run8213054a9755e1b67cbdf2e8e64664e4:8replays/35positive bodies,PASS/CURRENT;
200executed inputs unchanged,183prior inputs preserved. Producer52.979s;assessor0.808s returns
identical JSON and leaves every owned file unchanged. No probe hits became expected-output oracles.
Full1897PASS616.61s;Ruff both/format16/mypy173files/pip/native imports3+1/supplements3PASS.
Full qualification uses1027byte-identical relocated Tcl/Tk8.6.15scripts via child-process
TCL_LIBRARY/TK_LIBRARY;original installation unchanged. Original-path1896PASS/1Tk setup ERROR
and entry212PASS/1ERROR are retained;their script-read root cause remains unproved.
Windows symlink creation unavailable(WinError1314),recorded in JUnit;that real branch UNVERIFIED.
Early multiline-header/config-newline/test-line/environment-file defects were repaired and
failed/interrupted evidence retained. External COVERAGE_FILE cannot select the assessor's data.
3s/all11/device/independent review/release remain unqualified;CP06held. No commit/push/agent/provider.
Next unmet GOV item:author a current bounded deterministic-cost order;no automatic execution.

Manual invocation from the workspace with README's Python environment:
```powershell
$g07Run=Join-Path "$PWD/.pytest_cache" ('gov03-'+[guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -m tools.replay_body_coverage run --project-root "$PWD" --run-dir $g07Run
.\.venv\Scripts\python.exe -m tools.replay_body_coverage assess --project-root "$PWD" --run-dir $g07Run
```
Runs are exclusive and retained;choose a new ID for each producer run. Assessment is read-only.
