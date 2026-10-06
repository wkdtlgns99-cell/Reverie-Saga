# Phase 0 — Complete Work Orders

Date:2026-10-03 | Executor/reviewer:gpt-6.1-sol | Instructions:FINALIZED | Execution:COMPLETE/SELF_REVIEW_ACCEPTED
These are the original four Phase0 items, in dependency order. [Frozen contracts](PHASE0_CONTRACTS.md) and [tool preflight](RS-PREFLIGHT-001_COMPATIBILITY.md) are normative inputs. Public declarations there+B02–05 are prospective NEW symbols, not claimed existing source. [Template](../prompts/SOL_CODING_WORK_ORDER.md) still governs entry/promotion.

The original prospective paths/baseline/commands below are retained as the instruction snapshot. The director's step3 request authorized execution; all four items now DONE. [Final results/live path/scope](#phase0-execution--acceptance-2026-10-03) supersede earlier waiting/planned language. Necessary admission metadata and codec ownership refinements are recorded in PHASE0_CONTRACTS; independent vectors/tool pins were preserved.

## Shared Required Fields

| Field | Concrete value |
|---|---|
| executor/review | gpt-6.1-sol; self-review; independent-person/runtime review UNVERIFIED until evidence |
| baseline | HEAD efd2478ff8a6ed93ee833c3f8464a0efdd8a181a/main; cumulative document edits uncommitted; src/tests only.gitkeep. Preflight artifact stores exact input hashes/dirty inventory. Refresh HEAD/status/hashes at entry; read actual predecessor files completely, inspect callers and diff, compare frozen interfaces; ordinary private choices allowed |
| read_files | C:\Reverie Saga\SESSION_HANDOFF.md; BACKLOG.md; docs/prompts/SOL_CODING_WORK_ORDER.md; docs/work_orders/PHASE0_WORK_ORDERS.md; PHASE0_CONTRACTS.md; RS-PREFLIGHT-001_COMPATIBILITY.md; PHASE0_TOOLCHAIN.json; PHASE0_REFERENCE_VECTORS.json; task-specific block sections/source below |
| forbidden_paths | All paths outside the explicit edit list; C:\Quilltale read-only; root AGENTS/.agents/.codex/core rules/CI/custom tools/report/legacy schema/test deletion/commits/push/provider calls |
| compatibility | Qualified CPython3.13.12 WinAMD64 + selected13-package closure; Ruff target/mypy Python3.12; no Phase0 runtime third party; other OS/patches/bundle UNVERIFIED |
| edge_policy | Exact frozen contracts; all integer schema checks reject bool/float, validate bounds; no fabricated default on missing field/type/schema; immutable own inputs; ordering canonical |
| performance | Brain512MiB/turn p95≤100ms,p99≤250ms,proxyCPU overhead≤10%,fast Ruff+golden≤20s TARGET; Phase0 functional evidence only. Benchmark not required before source; no fabricated performance qualification/counter tool |
| stop_conditions | Actual predecessor/public interface differs materially, pin/config cannot execute, new public field/extra path needed, unrelated user edits overlap, meaningful tests fail unexplained; inspect/resolve within scope first; update concrete instruction if authorized scope permits; no silent extra paths/schema/oracle relaxations |
| delivery | Exact files/diff, commands/exits/nodeIDs, actual state/events/results, acceptance+scope+live path+self-review; no commit/push authorization. Documentation status update to BACKLOG/SESSION_HANDOFF allowed after factual acceptance, no task deletion |

Shared baseline commands at **each** entry:

```powershell
git -c safe.directory='C:/Reverie Saga' rev-parse HEAD
git -c safe.directory='C:/Reverie Saga' status --short
git -c safe.directory='C:/Reverie Saga' diff --check
Get-ChildItem src, tests -Recurse -File
Get-FileHash docs/work_orders/PHASE0_WORK_ORDERS.md, docs/work_orders/PHASE0_CONTRACTS.md, docs/work_orders/PHASE0_TOOLCHAIN.json, docs/work_orders/PHASE0_REFERENCE_VECTORS.json -Algorithm SHA256
```

Runtime commands below use `.venv/Scripts/python.exe` explicitly; no accidental global pytest plugins. Set `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'` for verification; no domain environment reads. Package initializer files are empty; structural initializers do not create additional capabilities. They are explicitly authorized paths, not implicit edits.

Entry status:director requested step3; P0-002 passed before P0-004 entry, P0-004 passed before P0-001, and P0-001 passed before P0-003. All four implementations accepted below. Future phase orders remain DRAFT until actual relevant sources/schema/tool qualification exist.

## RS-P0-002 — Install Strict Configuration

| Field | Contract |
|---|---|
| task_id/title/status | RS-P0-002; strict lint/type config; DONE |
| goal/non_goals | Create exactly config+hashed dev lock; no runtime,CI,coverage/import/mutation/report/new smoke source |
| prerequisites | RS-ARCH-003 document review + RS-PREFLIGHT-001 Phase0 qualification; step3 request; no source predecessor |
| read_files | Shared reads; architecture/BLOCK_08.md B3§1 rule scope; exact config/probe evidence in preflight |
| allowed_edit_paths | NEW C:\Reverie Saga\pyproject.toml; NEW C:\Reverie Saga\requirements-dev.lock; installation/cache in .venv and task-owned temporary directory only (untracked artifacts, not source deliverables) |
| public_contract | No runtime API; exact preflight TOML block and13 normalized==version --hash rows from tool artifact; install only Windows-selected wheels with --require-hashes --only-binary |
| behavior | Parse strict config; baseline F/E syntax +9 named rules; no Any whitelist/broad ignore; package identities roots under src,tests fully checked |
| examples | Frozen typed point10→11 passes; broad/silent catch/Any/mutable-default/global write/engine random fail selected rules; mypy wrong return/missing attribute/explicit Any fail |
| algorithm_steps | Verify interpreter→create isolated venv with writable TEMP/TMP if needed→write exact TOML/lock→hash install→versions/pip check→repeat independent temporary config probes→inspect scope/diff |
| wiring | Later source/tests use same config; no game live path yet |
| baseline_commands | Shared commands; python --version; no mypy/runtime tests baseline on empty source (UNVERIFIED, no empty collection pass) |
| test_responsibilities | Temporary preflight probes reused from tool evidence, executed outside src/tests; do not create permanent artificial game tests |
| acceptance | Exact2files, selected closure and tool versions, required rules+strict positive/negative probes, source package resolution valid; actual empty-src limitation recorded; pip check0 |

Verification:

```powershell
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe -m ruff --version
.venv/Scripts/python.exe -m mypy --version
.venv/Scripts/python.exe -m pytest --version
.venv/Scripts/python.exe -m ruff check src tests
git -c safe.directory='C:/Reverie Saga' diff --check
```

No `.py` exists yet: mypy source check expected non-success/no inputs, pytest exit5; do not call either gameplay verification. Execute temporary typed/probe files instead, then P0-004 runs actual source/tests. No `.gitignore` policy edit implied; prevent tool artifacts from staging if a later commit is requested.

## RS-P0-004 — Typed Recursive Read-only Views

| Field | Contract |
|---|---|
| task_id/title/status | RS-P0-004; recursive observed views; DONE |
| goal/non_goals | Typed scalar/map/sequence views with exact attribution/cache/expiry; standalone safety item; no toy gameplay/save/manifest checker |
| prerequisites | P0-002 accepted, selected tools/config, frozen contracts§1–2; step3 request covers original Phase0 order |
| read_files | Shared; B02 A2; B03 A5.4; actual pyproject/lock; no nonexistent source treated as read |
| public_contract | Frozen §1–2 exact primitives,ComponentRecord/StoredRoot,ReadAdapter/ViewAccess/keys/factory/errors,seven proxy errors; no toy CoreSnapshot imports yet |
| behavior | Sealed typed record adapters,one activeepoch,identity-checked key registry,checked private generic cast,no Any; operations recorded before failures; close invalidates allaliases; cacheinvocation-local |
| examples | Fixture hp10/reservesfood7/traits quiet,alert; exact five-operation observation sequence; nested write blocked; empty collections; missingkeys/indices; closedepochstale; forgedsame-schema key fails |
| algorithm_steps | Primitives/sealed backing→typed adapter/wrapper implementation→observations/mutation guard→identitycache/lifetime→independent fixtures/tests→strict checks |
| wiring | ObservedReadViewFactory implements ReadViewFactory; fixture adapters registered explicitly. Engine/driver live integration waits P0-001 |
| baseline_commands | Shared; selected versions; Ruff checksrc/tests; no preexistinggame tests; configprobe baseline preserved |
| test_responsibilities | test_read_views.py:test_nested_mutation_preserves_backing,test_operation_order,test_cache_repeated_reads,test_expired_aliases,test_epoch_errors,test_missing_key_index,test_forged_key,test_factory_isolation; meaningful normal/boundary/error examples frozen§2 |
| acceptance | Actual tests+Ruff+mypy src/tests0; nested mutation/lifetime/order/backing unchanged; no public erased/rawstate handle,scopeinspect; standalone status explicitly reported |

Allowed NEW paths, all under this exact root:

```text
C:\Reverie Saga\src\domain\__init__.py
C:\Reverie Saga\src\domain\primitives.py
C:\Reverie Saga\src\domain\state_types.py
C:\Reverie Saga\src\contracts\__init__.py
C:\Reverie Saga\src\contracts\errors.py
C:\Reverie Saga\src\contracts\read_views.py
C:\Reverie Saga\src\orchestration\__init__.py
C:\Reverie Saga\src\orchestration\read_views.py
C:\Reverie Saga\tests\__init__.py
C:\Reverie Saga\tests\unit\__init__.py
C:\Reverie Saga\tests\unit\view_fixtures.py
C:\Reverie Saga\tests\unit\test_read_views.py
```

Verification:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/unit/test_read_views.py
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m mypy --strict src tests
git -c safe.directory='C:/Reverie Saga' diff --check
```

## RS-P0-001 — Complete Two-engine Headless Turn

| Field | Contract |
|---|---|
| task_id/title/status | RS-P0-001; input→COMMIT→presentation; DONE |
| goal/non_goals | Real Stepper+Counter,toy admission/DAG/barriers/COW/atomic in-memory owner+protocol,presentation/CLI; no combat/NPC/event-bus product/save/client/Factory |
| prerequisites | P0-002/004 accepted; frozen§1–4,literal oracle; actual proxy source+tests read/matchinginterfaces |
| read_files | Shared; B02 A1–3,B03 A4/A5/A6,B04 A7,B05 NodeActivation/DefinitionReadPort; all predecessor source/tests listed above; no v1 mechanics |
| public_contract | Exact frozen§1/3/4,B02/B04 declarations; no generic publicdict payload; TurnPublication belongs contracts/turn; BootstrapSpec/HeadlessSession/main belong app/headless; domain canonical never imports contracts |
| behavior | Bootonce topological stablephase/engine ordering; action only RESOLVE,targettick+1; CounterPOSTeverytick; samephasecommonview; declaredread/write/deltaowner check; preCOMMIT abort atomic; pairedCORE/protocolswap; postCOMMITpresentationfail committed |
| examples | initialx0v0t0r0 +1→1,1,1,1;-1→0,2,2,2;0→0,3,3,3 still Stepped,no positiondiff; exactretry originalreceipt/no newfact; dx2/stale/missingroute reject; testengineexception/duplicatewrite abort |
| algorithm_steps | InternalA:DTO/canonical/storage/errors→B:toyadapters/reducers/engine/scheduler→C:owner/registry/bootstrap/presenter/CLI→realintegration→literalhash/error/atomicity checks; each delivery≤5behavior modules TARGET, not new Phase0 IDs |
| wiring | feature_bundles→bootstrap→driver.compileonce; driver.submit→registeredadmission→observedengine.evaluate→reducers/staging→receipt/head→presenter.map→TurnPublication→CLI/integration; no direct engine-to-engine calls |
| baseline_commands | Shared; completeproxy verification before changes; selected lint/types baselineresults saved |
| test_responsibilities | test_schedule.py:test_registry_permutation,test_writer_conflict,test_cycle,test_activation_rights,test_same_phase_visibility; test_canonical.py:test_literal_vectors,test_pack_utf8,test_core_protocol_separation; test_skeleton.py:test_two_turns_and_zero,test_admission_errors,test_retry_conflict_expired,test_abort_atomicity,test_view_finally_expiry,test_presenter_failure,test_headless_cli; faulty engines use real contracts |
| acceptance | Live CLI+integrated path+exact independent state/fact/diff/hash/receipt tests pass; noheadmutation onreject/abort; duplicate originalreceipt; observationrightsfail beforecommit; compiledscheduleonce; allscope/lint/types+predecessortests0 |

Allowed NEW:

```text
C:\Reverie Saga\src\domain\canonical.py
C:\Reverie Saga\src\contracts\turn.py
C:\Reverie Saga\src\contracts\messages.py
C:\Reverie Saga\src\contracts\skeleton.py
C:\Reverie Saga\src\engines\__init__.py
C:\Reverie Saga\src\engines\skeleton.py
C:\Reverie Saga\src\orchestration\scheduler.py
C:\Reverie Saga\src\orchestration\skeleton.py
C:\Reverie Saga\src\orchestration\turn.py
C:\Reverie Saga\src\app\__init__.py
C:\Reverie Saga\src\app\feature_registry.py
C:\Reverie Saga\src\app\headless.py
C:\Reverie Saga\tests\unit\test_schedule.py
C:\Reverie Saga\tests\unit\test_canonical.py
C:\Reverie Saga\tests\integration\__init__.py
C:\Reverie Saga\tests\integration\test_skeleton.py
```

Allowed MODIFY:C:\Reverie Saga\src\domain\state_types.py (toyrecords/CoreSnapshot/pins only); C:\Reverie Saga\src\contracts\errors.py (four named families only); C:\Reverie Saga\src\contracts\read_views.py (ReadRegistration/AdapterBinding/registry +B03 patch/reducer/editor declarations only). Factory behavior changes outside the already-authorized typed adapter port require focused contract refresh; no implicit edit to factory. Tests/unit/view_fixtures.py remains READ. B02 turn/messages mutual annotations use future annotations+TYPE_CHECKING where necessary; no runtime circular imports or duplicate primitive declarations.

Verification:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/unit/test_read_views.py tests/unit/test_schedule.py tests/unit/test_canonical.py tests/integration/test_skeleton.py
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m mypy --strict src tests
$rsPreviousPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = 'src'
'{"actor_id":"actor:toy","command_id":"c1:00000000000000000000000000000000:11111111111111111111111111111111:1","expected_revision":0,"schema":{"kind":"skeleton.step","version":1},"payload":{"dx":1}}' | .venv/Scripts/python.exe -m app.headless
$env:PYTHONPATH = $rsPreviousPythonPath
git -c safe.directory='C:/Reverie Saga' diff --check
```

CLI expected committed x1/visits1/tick1/revision1, literal step1 hashes/event/diff/cue from oracle. Set `$env:PYTHONPATH='src'` for this manual CLI because package not installed; pytest uses configpythonpath. Restore previous environment after invocation. No stubbed successful RNG draws; NoDrawRng raises until nextitem.

## RS-P0-003 — Deterministic RNG / Golden Replay

| Field | Contract |
|---|---|
| task_id/title/status | RS-P0-003; record/replay/hashcompare; DONE |
| goal/non_goals | Tested addressable RNG +record/replayonrealdriver,witness mismatch,contamination/hashseed; no coverage/mutation/cost/migration/customreport/checker |
| prerequisites | P0-001 accepted with literalcanonicalvectors; frozen§4–5; selectedtools; actual bootstrap/driver/collector read,matchinginterfaces |
| read_files | Shared; B03 A6,B04 protocol; actualskeletonsource+tests+canonical+bootstrap; fixture source is independent artifact golden_fixture |
| public_contract | Exact B03 RNG/replayDTOs plus frozenReplayFixture/Recorder/Runner/decode_fixture/encode_fixture; reexportexistingRngService,notduplicate; canonicalunchanged |
| behavior | RNGpack→SHA256key→u64counterdigest→rejectionsamplingwithattemptconsumption; freshrunnerstateeveryrun; verifyfullCORE/protocol/outcome/facts/diff; failinconsistentwitnessbeforeexecution; preciseleafonlywithwitness |
| examples | Literal4draws/ranges and forcedrejection8attempts;5stepgolden +1,-1,0,duplicate,stale; removeStepped→factmismatch despitecorrectCORE; valid independently alteredxwitness→leaf; no-witness→digestonly |
| algorithm_steps | Typedfixturecodecs+pinvalidation→counterRNG+literalvectors→boundedrecorder→freshrunner/mismatch→defaultbootstrapRNGwiring→golden/repeat/reverse/cache/hashseed→allPhase0checks |
| wiring | bootstrap default CounterRngService; everyinvocationscopedfacade; sessionlastpublication recorderconsumer; app.headless.replay_runner injects ReplaySessionFactory→Runner trustedcheckpoint→samebootstrap/driver→submit→canonicalcompare; orchestration never imports app; no alternatetoyexecution path |
| baseline_commands | Shared; fullP0-001proxy/scheduler/canonical/integration tests+lint/types saved beforeedit |
| test_responsibilities | test_rng_vectors.py:test_literal_draws,test_rejection_consumes_counter,test_address_isolation,test_invalid_range_purpose,test_counter_exhaustion; test_golden.py:test_core_trace,test_pin_witness_validation,test_fact_diff_mismatch,test_leaf_mismatch,test_recorder_roundtrip; test_contamination.py:test_repeat,test_reverse_world_order,test_cache_warm_cold,test_hashseed_processes |
| acceptance | Allfivegoldensteps actuallyexecuted,witness/fullhash/outcomeexact; corruptiondetected; independentvectorsmatched; hashseed0/1/loggedrandomchildprocesspass; noenvironment/globalrandom/liveAI entersdomain; allPhase0source/types/lint0 |

Allowed NEW:

```text
C:\Reverie Saga\src\contracts\replay.py
C:\Reverie Saga\src\orchestration\rng.py
C:\Reverie Saga\src\orchestration\replay.py
C:\Reverie Saga\tests\unit\test_rng_vectors.py
C:\Reverie Saga\tests\replay\__init__.py
C:\Reverie Saga\tests\replay\test_golden.py
C:\Reverie Saga\tests\replay\test_contamination.py
C:\Reverie Saga\tests\replay\fixtures\skeleton_v1.json
```

Allowed MODIFY:C:\Reverie Saga\src\contracts\errors.py (three replay/RNG families); C:\Reverie Saga\src\app\headless.py (defaultRNG+validatedcheckpoint factory injection+replay_runner only). domain/canonical.py,orchestration/turn.py,app/feature_registry.py **READ**; contracts/turn.RngService reexportonly. If actualsourcecannotrestorecheckpointorcollectpublications underfrozenAPI, resolvepredecessorcontractduringP0-001acceptance; nohiddenlatercanonicalrewrite. Existing registry.rng_purposes and rules pins unchanged. Registered RNG version already sha256-counter-v1 inP0-001; zero-drawplaceholderdoesnotclaim RNGverified.

Verification:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/unit tests/integration tests/replay
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m mypy --strict src tests
.venv/Scripts/python.exe -m pytest -q tests/replay/test_golden.py::test_core_trace
git -c safe.directory='C:/Reverie Saga' diff --check
```

Contamination test launches exactsamepytestgoldennode in freshprocesses with externallychosen/loggedPYTHONHASHSEED and guarded flag preventing childrespawn; actualargv/seed/exit recorded. Fastlocalcheck Ruff+coregolden timing is feedback TARGETonly; all11Phase1gates remaininactiveuntilapplicablecode exists.

## Phase0 Execution / Acceptance (2026-10-03)

Director request:"3 ㄱ". All four items DONE after implementation, actual verification and Sol self-review. HEAD remains `efd2478ff8a6ed93ee833c3f8464a0efdd8a181a` on main; no commit/push. Existing primary/MASTER modifications and untracked architecture/preflight docs were preserved. Later implementation/independent-person review is not implied by this acceptance.

Entry evidence:P0-002 exact13package wheel/hash install and repeated isolated native/config probes passed before source work; P0-004 accepted9tests/Ruff/strict mypy12files before P0-001; P0-001 accepted25tests/Ruff/strict mypy28files before P0-003. No empty-source pytest success was used as a baseline. Initial standard venv/pip attempts encountered restricted Windows TEMP (WinError5) and sandbox networking; task-owned workspace TEMP and authorized hash-only network install resolved them. Selected `.venv` remains local; task-owned temporary probe directory removed after checks. Global tools were not updated.

Necessary contract/source refinements within the authorized implementation scope:
- Pure StepAdmission requires actual `start_tick` and `world_id`; these are explicit keyword inputs, never fake tick0/empty semantic identity. Contracts/skeleton, its implementation/caller and PHASE0_CONTRACTS agree; existing independently authored bytes/hashes/outcomes unchanged.
- Concrete replay codecs stay in orchestration; contracts/replay contains frozen DTOs/Protocols and reexports the original RngService. App supplies checkpoint factory; no contracts→orchestration or orchestration→app import.
- P0-001 acceptance review replaced reflected registry schema enumeration with typed tuples, checked that the admission plan is the submitted one-tick action, enclosed RNG-context construction in the same finally-expiry scope as evaluation, and made CLI arguments follow the specified rejection behavior. These repairs use the original P0-001 allowed paths and were reverified with final P0-003 checks; no canonical/hash/rules rewrite or new gameplay capability.

Actual source/config/fixture manifest (all paths were NEW at entry):
- `pyproject.toml`, `requirements-dev.lock`.
- `src/domain/{__init__,primitives,state_types,canonical}.py`.
- `src/contracts/{__init__,errors,read_views,messages,turn,skeleton,replay}.py`.
- `src/orchestration/{__init__,read_views,scheduler,skeleton,turn,rng,replay}.py`.
- `src/engines/{__init__,skeleton}.py`; `src/app/{__init__,feature_registry,headless}.py`.
- `tests/__init__.py`; `tests/unit/{__init__,view_fixtures,test_read_views,test_schedule,test_canonical,test_rng_vectors}.py`.
- `tests/integration/{__init__,test_skeleton}.py`; `tests/replay/{__init__,test_golden,test_contamination}.py`; `tests/replay/fixtures/skeleton_v1.json`.
- Documentation MODIFY:BACKLOG,SESSION_HANDOFF,PHASE0_CONTRACTS and this order's statuses/evidence. Preflight TOOLCHAIN/REFERENCE_VECTORS/compatibility record, architecture, primary specs/template/historical AGENTS/content reference unchanged by step3. No root policy/CI/custom tools/client/save/Factory/README generated.

Live path:`app.headless.bootstrap` → explicit `app.feature_registry.feature_bundles` → `compile_schedule` once → Driver/ObservedReadViewFactory/registered admission → Stepper RESOLVE and every-tick Counter POST_TICK → registered reducers at phase barriers → single `_head` assignment for CORE+protocol → committed receipt/facts/netdiff → presenter. ±1 changes position, zero still emits Stepped and increments visits; rejected/aborted submissions leave both heads and retry high-water unchanged. Duplicate returns original receipt without effects; retired/evicted/conflicting/stale paths are explicit. Presenter failure retains committed effects and reports PRESENTATION_FAILED.

Replay wiring:`app.headless.replay_runner` → injected checkpoint factory → same `_restore`/Driver path, fresh session on each run → actual submit/last_publication → full CORE/protocol/facts/diff/outcome comparison. All five independently authored steps execute (+1,−1,0,exact retry,stale). Recorder bounds4096 and captures actual failed/duplicate publications; recorder output is roundtrip evidence only, never a new oracle. Initial CORE hash `1c477fb6d8ccdaf252583858c00a696ce619535236e7d1141b2eca34da9957e4`; first committed CORE hash `c2c46ea39dc67dc75f06a171fdd93a5b7f70768df06f8601469699ac5d1eb44d`. Literal complete publications and hashes match the preproduction vectors.

Final executed commands (exit0 each):

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.venv/Scripts/python.exe -m pytest -q -s tests
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m mypy --strict src tests
.venv/Scripts/python.exe -m pytest -q tests/replay/test_golden.py::test_core_trace
git -c safe.directory='C:/Reverie Saga' diff --check
```

Results:37tests PASS in9.19s; Ruff all checks passed; strict mypy no issues in35sourcefiles; isolated core golden1test PASS in0.13s. Timed local Ruff+core golden1.194s versus20s TARGET; this is one local feedback run, not Brain p95/p99/resource/min-spec qualification. Native package consistency/pip check and required9-rule/strict/generic/package/pytest-subprocess probes PASS. Full config text/TOML semantics equal the preflight block; Windows CRLF output was normalized to the exact frozen LF bytes, SHA256 `147a3f5fb8135d9d7ce641cb7269e2fcc735b8b915666fbb827da73eb2ae15a8`.

Actual acceptance nodes/evidence:
- `tests/unit/test_read_views.py`:9tests validate exact read order, recursive mutation guard, cache acquisitions, sliced original paths, expired wrappers/iterators/ports, epochs, forged keys, missing entities and collection caps.
- `tests/unit/test_schedule.py`:registry permutation, writer conflict, dependency cycle and activation/lane validation. `tests/unit/test_canonical.py`:all literal documents/UTF8/hash framing/pack vectors, invalid canonical inputs and CORE/protocol separation.
- `tests/integration/test_skeleton.py`:9tests validate complete literal turn publications, malformed/stale/unauthorized/missing actor, retry/conflict/evicted/retired, abort after Stepper, duplicate concrete targets, signed overflow, finally-expiry, postcommit presenter failure, same-phase snapshot visibility, actual stdin CLI recovery/argument rejection and invalid plan/undeclared read/caught write attempts.
- `tests/unit/test_rng_vectors.py`:3tests validate all4literal vectors (including4draws consuming8rejection attempts), exact key/unsigned samples, cache/fresh/address isolation, ranges/purposes/phases/waves, last unsigned64 counter and exhaustion.
- `tests/replay/test_golden.py`:4tests validate real five-step golden/codec roundtrip, self-consistent wrong leaf (`$core.components[1].fields.x`,expected2,actual1), digest-only path, corrupt initial pins/witness/JSON and real bounded recording.
- `tests/replay/test_contamination.py`:4tests validate dropped record-only facts while CORE/protocol/diff remain correct, repeated runner with fresh owners, warmed/expired versus cold views, X→Y/Y→X world isolation and fresh processes. Publication observation proves5actual submissions per run. Seed selection uses external test-process entropy only; no domain input/randomness.
- Hashseed child argv each:`['C:\\Reverie Saga\\.venv\\Scripts\\python.exe','-m','pytest','-q','tests/replay/test_golden.py::test_core_trace']`; PYTHONHASHSEED0,1,2249326019 each exit0/1test passed; guard `RS_P0_HASHSEED_CHILD=1`. Earlier development run0/1/2411571747 also passed. Trace command order unchanged.

Final review:actual live paths/public types/registration/sole COMMIT/abort/finally boundaries inspected; independent oracle copied unchanged and runtime source never reads it. Protected primary/MASTER/template/historical AGENTS/content and independent vector raw-byte hashes match previous evidence. Tracked diff whitespace check passes; new source/docs explicitly inspected too. Current Python installation emits an existing "Failed to find real location" launcher diagnostic, but native tool exits are0 and CLI stdout remains strict JSON (subprocess test passes).

Remaining:Phase1 source-specific orders, generic event routing/cascade/catch-up/save/migration/NPC/client/IPC/Factory/bundle/device/resource/performance and staged governance are deferred. B09 #6/#34 later-order readiness remains PARTIAL; parent ARCH-002 IN_PROGRESS. No independent-person or full-game qualification claim.
