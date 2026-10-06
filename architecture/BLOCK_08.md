# BLOCK 8 — Eleven Gates, Scope & Session Rules

Task: RS-ARCH-002-B08 | Date:2026-10-03 | Mode:DESIGN | Owner:GPT-6.1 Sol
Authority: [v2.6 prompt](../docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md) B3–B5; [MASTER](../docs/MASTER_GAME_ARCHITECTURE.md). Previous contracts: [BLOCK6](BLOCK_06.md) budgets, [BLOCK7](BLOCK_07.md) residency/evidence.
All configurations/commands/test paths below PLANNED; no production code, CI workflow, gate runner, tests, report tool or active policy installed. Proposed policy/configuration activation still requires explicit director approval where the prompt requires it.

## B3. CI Gates — Exactly Eleven

### B3.1 Gate Table / Stage / Time

Commit gates =4 standard tools +5 harness checks +2 custom thin wrappers. Each gate consumes pinned actual code/config/fixtures/package evidence; unavailable evidence is NOT_RUN/UNVERIFIED, never implicit PASS. Complete Phase1 pipeline applies all11; phased bootstrap below preserves exactly four Phase0 implementation items. Tool versions/platform support are preflight prerequisites, not inferred from installed Python or documentation syntax.

| Gate ID / tool type | Check / evidence | Failure condition | Time TARGET |
|---|---|---|---:|
| G01 Ruff / standard L3 | Source/tests; configured E722,S110,S112,BLE001,TID251,PLW0603,RUF012,B006,ANN401 + ordinary undefined/unused/syntax checks | Any selected lint error; missing rule/config or unsupported version UNVERIFIED, not silent rule removal |3s|
| G02 mypy / standard L3 | --strict + disallow_any_explicit; typed engine/domain/contracts and public adapters; narrow reviewed I/O exceptions | Any type error/domain Any; absent stubs silently ignored or expanded whitelist not approved |6s|
| G03 import-linter / standard L3 | Layer contracts; later layers may import earlier, never reverse/same-layer cycles; engine-to-engine and SDK/I/O domain imports prohibited | Broken configured contract; missing/lax contract cannot claim pass |3s|
| G04 pytest / standard L2/L3 | Pure feature invariants/boundaries + live integration/adapter behavior; exact test scope/baseline/node IDs; domain mocks banned by G01 | Required test failure/error/skip/xfail/uncollected case; new regression or empty selection; unrelated passing tests insufficient |12s|
| G05 golden replay / harness L2 | Expected per-step CORE+protocol outcomes, accepted pins; fixed0/fixed1/randomized hashseed processes; rejected/aborted/time/composition/cache cases | Hash/outcome/receipt mismatch, missing package/required vector, lost A composition, live provider invocation |8s|
| G06 contamination / harness L2 | Same trace twice in one process; X→Y versus Y→X with fresh world/services for each run | Any trace differs from itself; reused mutable service/global/cache contaminates independent worlds |4s|
| G07 replay coverage / harness using coverage.py L2/L3 | Golden-trace method body hits for all registered public engine methods; exact current method inventory/ranges and native coverage evidence | Zero-hit required body/live path; definition/import-only hit, stale scope or absent required coverage |3s|
| G08 deterministic costs / harness L2 | Calls/leaf writes/produced facts/owned allocations; per-lane tick/job limits + recorded fixture baseline; wrappers subset; A13 site coverage | Any deterministic ceiling/reference-tolerance violation, uninstrumented owned site or false cheap no-op behavior |5s|
| G09 save migration / harness L2 | Every intentionally supported historical v2 fixture -> current schema; atomic/recovery/invariant/package/replay checks | Missing listed fixture/edge, wrong semantics/hash, partial mutation, unsupported version accepted, failed current round trip |5s|
| G10 manifest / CUST-01 L4 + L2 | Expanded engine/phase read/write declarations vs proxy/reducer observations; ownership/boot/routing and CORE consumers | Undeclared access/writer, invalid registration/schema/conflict; unresolved required reader/unused declaration under required trace scope |4s|
| G11 game-data/artifact / CUST-02 L4 | Strict A10 schemas/IDs/refs/chunks/hash pins; A14 license/provenance/approval/import/build associations | Invalid approved corpus/package, duplicate/cyclic/ref/path/hash conflict, unlicensed/unapproved artifact selected for import/build, fabricated lifecycle evidence |5s|

Time sum **58s +2s runner headroom =60s total TARGET** on qualified DEV-A/DEV-B Windows jobs; actual NOT_MEASURED. No estimated speed/MEASURED label. Reuse evidence from one snapshot to avoid duplicate heavy runs; no whole performance benchmark/image/model job in commit path. More content/fixtures may exceed target: optimize caching/scoped execution with equivalence evidence or revise target transparently; never weaken required checks to manufacture speed.
Wall-clock ms and process MB remain soft trends, not hard commit-CI gates. Targets are not per-gate kill timers. Infrastructure watchdog cancellation reports INCOMPLETE/UNVERIFIED; a hung job cannot pass, but timeout is not a deterministic gameplay-budget finding. Device/release performance qualification remains A13's separate measured acceptance.

### B3.2 Standard-tool Configuration Boundaries

Future `pyproject.toml`/import-linter contracts belong approved bounded orders. Select required rules explicitly, not assume tool defaults. Ruff TID251 bans domain imports/access to global random/real time/UUID/env/filesystem interfaces and unittest.mock/pytest-mock in `tests/engines/`; adapter-only exceptions individually scoped/reviewed. Some tests require real infrastructure; no rule that all tests use mocks. Existing aliases/re-exports and dynamic access are covered by typed ownership/replay, not claimed completely solved by lint.
Strict mypy flags are version-pinned; no global ignore-missing-imports, ignore-errors or broad #type:ignore masking. Explicit Any allowed only immediate typed conversion in reviewed JSON/LLM/template/IPC boundaries. G02 checks tests/public adapters under the selected typed scope; third-party SDK untyped internals stay outside domain. Any whitelist change remains GATED. Ruff alone cannot prove absence of semantic stubs, complete exception behavior or meaningful tests; registry/integration/replay/mutation supply evidence.
Layer order [BLOCK1](BLOCK_01.md) is low-to-high: domain -> contracts -> engines -> orchestration -> adapters -> app; **import permission runs from higher to lower**. Domain/contracts cannot import engines/adapters/client SDK/tools; engines cannot import each other; reporter/Factory tooling cannot become engine dependencies. Protocol ports/injection avoid orchestration needing concrete persistence/client adapters.

Primary capabilities checked: [Ruff rules](https://docs.astral.sh/ruff/rules/), [TID251](https://docs.astral.sh/ruff/rules/banned-api/), [mypy flags](https://mypy.readthedocs.io/en/stable/command_line.html), [import-linter](https://import-linter.readthedocs.io/en/stable/). These support candidate configuration, not concrete Python3.13/Windows/tool-lock compatibility. Unsupported required flags/rules stop preflight rather than auto-relax policy.

### B3.3 Harness / Selection / Evidence

PLANNED pytest markers: golden, contamination, replay_coverage, counters, migration, manifest, artifact. G04 runs remaining ordinary pure/integration/adapter tests; G05–G11 select required groups explicitly and attach collected node IDs. Every test has one owning gate; shared fixtures may serve several. G04 excluding other groups is valid only after the complete approved selection inventory proves no test is omitted. Zero selected tests is NOT_RUN/FAIL for an active required gate; no empty-suite pass.
G05 base fixed0 golden run may collect coverage/proxy/counter facts once. G07/G10 consume its current native evidence; G08 uses its dedicated fixed small cost trace. Evidence reuse requires exact code/config/fixture/package/tool fingerprint and actual run result; failing replay cannot yield passing access/coverage evidence. Producers preserve failures/attempted reads/costs for diagnostics. B2 report merely aggregates results, does not re-run checks or certify DONE.

| Gate detail | Required fixed inputs / qualification |
|---|---|
| G05 | New v2 committed fixtures and independently derived expected values; three child-process hashseed modes0/1/logged random integer0..2^32−1. Random generation outside Brain; log exact seed. Never reverse commands inside a trace or randomize dependency order as contamination test |
| G06 | Two distinct named traces X,Y plus same trace twice; order X,Y vs Y,X; each run new world/services/read/RNG/context caches, same-process executable. Compare full CORE/protocol results to each trace's own expected trace |
| G07 | Registered public engine-method inventory + qualified source body ranges; exclude only Protocol/ABC declarations, generated constructors and non-engine utilities. Real completed engine stubs are not exemptions. Report percentages if available; required body hits are the gate condition |
| G08 | COST-CI-01: pinned A13 synthetic world;32 one-second commands +one passive300-second catch-up to exercise remote wakes/delayed facts, both active A/exact B lanes. Real invariant/hash expectations + exact reviewed reference counts; never auto-record implementation output as a golden oracle |
| G09 | Explicit supported-version/fixture list; original hash/expected semantic result/migration edges. v1 saves unsupported; curated descriptions not migrations. All listed fixtures included, plus current round-trip/reject/rollback cases; zero historical fixtures reported0 intentionally supported, not proof of historical compatibility |
| G10 | Boot manifest/schema/DAG fingerprints; required golden access set. Four categories separate per B0. Narrow unused-declaration cases require real satisfying trace before engine acceptance; no new blanket waiver |
| G11 | Approved new corpus + frozen accepted runtime packages + artifacts actually selected for import/build. PLANNED/GENERATED/rejected candidates counted but not required to have fake approval/build proof; their state/schema completeness rules still checked |

G08 inherits A13 per-lane calls128/writes2048/owned allocations32768/wrappers8192 per executed tick; total A facts512/tick, pending4096, cascade8, B simulation facts0; job/staging limits unchanged. Time/MB peaks recorded but cannot fail this gate. Real PERF-TURN/CATCHUP/CLIENT/FACTORY full benchmarks stay asynchronous/device qualification; small cost trace is not final-world performance proof.
Coverage/access/cost result interpretation is small test/harness binding over standard runtime/native outputs, not new custom AST checkers. G10/G11 are the only planned custom checkers. No scope-checker/TODO-checker/coverage god framework; use standard search for suspicious stubs/TODOs as review evidence, actual behavior determines acceptance.

PLANNED command families (entrypoints/paths exact only after corresponding approved work order):

```text
python -m ruff check src tests
python -m mypy --strict src tests
lint-imports
python -m pytest tests -m "not (golden or contamination or replay_coverage or counters or migration or manifest or artifact)"
python -m pytest tests/replay -m golden
python -m pytest tests/replay -m contamination
python -m pytest tests/governance -m replay_coverage
python -m pytest tests/performance -m counters
python -m pytest tests/persistence -m migration
python -m pytest tests/governance -m manifest
python -m pytest tests/content -m artifact
```

Config supplies required extra Ruff/mypy flags; command display is not complete configuration. When Phase1 adds tools/other approved Python roots, include those actual roots in G01/G02 scope rather than leaving validators/report code unchecked; concrete scope belongs that implementation order. Hashseed environment/child-process launching uses ordinary pytest adapter fixtures, not shell-specific chained commands. Native evidence/log paths under PLANNED `reports/evidence/`; capture exact argv/cwd/exit/node IDs/versions/fingerprint. These paths/tools/tests **do not exist yet**; no command above executed here. Full Windows native suite mandatory after applicability exists, including UTF-8/paths and later packaged IPC/lifecycle; platform-specific implementation deferred to deployment as director requested.

### B3.4 Fast Local / Activation / Async

Fast local before authorized commit: Ruff +one core golden trace, TARGET<=20s incl startup; proposed replay selection `tests/replay/test_golden.py::test_core_trace`. Actual node/file created by skeleton/replay order later; currently PLANNED. Fast subset is feedback, not replacement for full activated commit gates.
Phase0: **Ruff+mypy -> recursive read-only proxy ->1–2 dummy-engine walking skeleton ->golden replay**. G01/G02 and initial G04/G05/G06 behavior support these items, no separate extra deliverable. No import-linter/coverage/counter/migration/manifest/data/report/mutation tool front-loading. Phase1 activates G03/G07/G08/G10 with corresponding real code/evidence, G09 with save/migration, G11 with new content/Factory foundations. Before full activation report stage/applicability explicitly; do not claim all11 pass. Explicit inactive/deferred stage states are not a permanent waiver of any gate.
Windows is required for the activated11 commit gates; Python3.13 preferred, actual tested version/locks/wheels recorded. DEV-B full suite and MIN-SPEC playable release are separate qualifications; DEV-A passing does not certify either. Optional Linux text-demo path needs separate approval/scope; Linux may independently host the async mutation job regardless of demo existence.

| Async job, not commit gate | Scope / acceptance / TARGET |
|---|---|
| Mutation | Weekly or phase completion, only `src/engines/`, per-engine invariant/boundary tests. Initial score>=80% per engine; qualified below. Initial duration<=30min/job TARGET; heavy CPU job serialized with local AI/import work, process-tree RAM within12GB |
| Report drift | B2 planned renderer --check at scheduled collection/phase end; exit0 equality,1 drift,2 invalid input. Duration<=5s TARGET; refresh pinned evidence index/as-of, not arbitrary stale files |
| Full profiling/device/media/lifecycle | A13 exact profiles + A12 deployment matrix + A14 imports/builds; measured environment/results. Not new commit gates or permission to start bulk jobs |

Mutation candidate **mutmut PROVISIONAL**, cosmic-ray alternative after concrete compatibility review. Current [mutmut documentation](https://mutmut.readthedocs.io/en/latest/#requirements) requires fork support/WSL for Windows; async job may run approved WSL/Linux CI. Selected pinned version/wheels/config/runtime still UNVERIFIED; do not install WSL/Linux/toolchains here or require them on the player's machine.
Per-engine score =100*killed/(killed+survived), excluding only independently explained/reviewed equivalent mutants. Timed-out/unrun/invalid/tool-error mutants remain unresolved; never counted as killed/equivalent or used to claim qualification. **Qualification requires score>=80%, no unresolved meaningful survivors untriaged, no unresolved timeout/unrun/tool error, at least one non-equivalent measured mutant and an independently specified engine invariant.** Zero denominator NOT_APPLICABLE only with explicit justified no-mutable-logic review; otherwise UNVERIFIED. Retain survivor identities and boundary-test gaps even above80%.
Source/config/test/schema/package fingerprint pins async results; code change -> stale. Latest matching result older than7days -> stale per B2 weekly schedule; phase-end qualification requires current matching completed results. Limit mutation workers initially1 on DEV-A; capture killed/survived/ignored/timeout/unrun/version/platform/duration/bytes. Equivalent decisions cannot be auto-inferred from test passes; a triaged actual gameplay defect still requires repair even when aggregate score>=80%. No `mutmut apply` against shared work: mutation operates in isolated disposable test copies; fixes are reviewed source changes by Sol. No task-wide reset/delete to repair mutation side effects.
Any async failure is visible in B2 and blocks relevant phase/release qualification until resolved, **not a twelfth commit gate**. Cancellation/30min excess records partial/UNVERIFIED; resume/reduce scope without claiming measurement complete. Score/CLI/platform/time actually NOT_MEASURED/NOT_RUN.

## B4. Scope Gate — Review Checklist

No checker. New gameplay engine approval uses a concrete work-order/PR checklist; application follows existing authorized task scope. Required capabilities remain MASTER outcomes, not a file-per-capability mandate.

| Checklist item | Required evidence / rejection |
|---|---|
| Trigger | Actual typed command/due autonomous event/phase consumer in the playable path; planned wiring named for implementation order. Pure speculative capability without live trigger rejected |
| Existing responsibility | Search current modules/manifests/callers/schema; explain why extending existing ownership cleanly cannot satisfy need. Renaming/splitting a god engine without ownership evidence insufficient |
| Need | Real playtest absence/defect + reproducible trace **or** exact non-negotiable MASTER section/capability; no invented playtest evidence |
| Boundaries | Precise fields/A-B-C ownership, reads/writes/events/RNG/tick/activation, integration consumer and invariant; no new central optional DTO/growing union |
| Cost | Number of files/contracts/config dependencies, memory/calls/CI/profile impact, reversible integration plan; numbers TARGET until measured |
| Acceptance | Meaningful unit -> live integration -> baseline regression/replay; independent expected values, source/test/evidence paths, no TODO-only completed engine |

Resolve B4's apparent playtest conflict explicitly: a mandatory MASTER capability can justify the first playable implementation **before playtests exist**; record exact requirement and missing playtest status, implement smallest live slice, schedule playtest afterward. Discretionary capability requires actual playtest evidence. Both routes require trigger + responsibility search/justified extension choice. Do not drop MASTER physics/NPC/social/survival/world functionality merely because current implementation is absent; stage it by dependencies and playable evidence.
Walking skeleton's1–2 dummy engines are explicit Phase0 architecture-test scaffolding, not a claim of product/gameplay capability or license to add speculative engines. A schema-only/template/media expansion remains a content/asset task when it uses existing approved effects/import profiles; embedding a new formula/behavior/handler inside data is a new system change and needs this review.

| Task kind | Route / completion boundary |
|---|---|
| Existing-schema content | New valid IDs/refs/traits/lore + approval, same compiler/rules; G11 + relevant integration; no v1 stats/formulas/schema/oracles |
| Existing-profile asset batch | A14 specs/bounded jobs/license/style approval/import/build + A13 hardware; no new pipeline capability or early bulk production |
| New system/engine/pipeline | B4 checklist + precise architecture/order/evidence; resolve APIs/ownership/consumer before READY |
| Behavior-preserving refactor | Same accepted packages/seed/trace/schema outcomes and golden hashes; record caller/access changes, no unrelated new behavior |
| Intentional behavior change | Separate scoped rationale/rules/version/expected vectors and commit if authorized; never hide changed outcomes under refactor |

No approval per routine helper/class when already within a complete authorized order. Any protected policy/test/backlog/destructive-schema/Any/custom-checker decision remains B5 gated. Reversible bug diagnosis/repair of authorized code proceeds; scope expansion gets a concrete proposal only after existing safe work/evidence is prepared.
Chosen: small evidence-backed capability slices + checklist, with mandatory-product bootstrap route. Rejected: desk-theory module growth, every capability a new engine, copying poor v1 calculations, new scope checker, dropping required gameplay to avoid work. Escape: reorganize approved ownership after behavior-preserving replay/caller evidence; keep product requirement.
Mapped: F-01/F-02/F-03/F-04/F-09/F-10; AP-04/AP-07/AP-09/AP-10/AP-11; C-03/C-04/C-06.

## B5. Sessions / Authority / Completion

### B5.1 Scope / Baseline / Atomic Delivery

Proposed coding-session cap: **one active bounded work order**, at most5 production modules and one gameplay capability; tests/docs/generated approved-schema content are supporting artifacts with explicit path lists. This is an initial planning cap, not an excuse to stop halfway through authorized necessary work. Larger work is split into complete dependency-ordered slices before READY, or the user's explicit scoped authorization overrides the default. Routine repair within the same goal includes affected callers/tests/docs; do not create new permission steps for every safe edit.
Design progression remains one requested BLOCK/turn; a chat may contain several completed requested BLOCKs. New chat is optional at coherent boundaries; no automatic fork/model switch. B2 routine read TARGET8000tokens, full required primary/contracts override size target. Sol owns all coding/testing/repair/review, Astra named concrete blocker advice only, human direction/approval; specialty jobs retain A14 roles. No subagents launched without explicit authorized delegation.

| Session step | Required evidence / action |
|---|---|
| Start | Actual cwd/HEAD/branch/remotes/status, source+order hashes, saved task markers/prerequisites, tool/runtime versions and stage; original primary reads for first architecture entry |
| Baseline | Actual applicable tests/replay/lint/type command/result before code edit; distinguish existing failing node IDs from new ones. Document-only baseline file/hash/link checks; do not invent pytest |
| Scope | Exact allowed/new paths, contract/signature/error/unit/owner/ordering/oracle/live path/acceptance, dependencies/deferred items; search responsibilities/callers first |
| Implement | Direct scoped edits, complete reviewable diff, no fake success/stubs/input mutation/silent catch; preserve unrelated user work; no broad reset/delete/reformat |
| Verify | Actual necessary checks/real integration + stage coverage/replay; diagnose/repair new failures; do not game/delete tests or loosen policy to green a run |
| Finish | Refresh source fingerprint/results/diff; record file/test/live-path evidence and missing support, update authorized factual task/context records. Self-review not independent audit |

Atomic commit =one coherent responsibility +associated tests/docs, only when commit authorized; no mixed unrelated refactor. Never stage unrelated preexisting changes, force-push or overwrite remote work. This task does not commit/push. Uncommitted changes remain a valid reviewable delivery with truthful status. A refactor commit attaches old/new pinned replay hashes proving same behavior; changed hash requires separate intentional behavior change rationale/approval where applicable.
After interrupt/new steering/restart, re-check mutable source/status/evidence before dependent edits; don't assume cached baseline still current. Startup marker mismatch -> inspect actual files and refresh/reconcile in-scope evidence, not blindly accept DONE. Test failure identity/status matters, not pass-count alone; failures cannot disappear via narrowed selection and still claim full regression.

### B5.2 Protected Changes / Concrete Approval

| Protected action | Exact approval scope / preparation |
|---|---|
| Governance/rules/CI policy | Specific proposed diff/config/impact + source authority; architecture proposal does not activate it |
| Backlog deletion | Exact IDs/history/dependency impact; current factual status/links/evidence updates already authorized |
| Test deletion | Exact tests/purpose/coverage/mutation/regression replacement evidence; no silent skip/assertion weakening |
| Destructive schema change | Data affected, supported fixtures/backup/migration/rollback/recovery proof; no truncation/drop to fit budget |
| Any whitelist entry | Exact I/O module/function/rationale/immediate DTO conversion and typed no-leak evidence |
| New custom checker | Unsolved requirement/L1–L3 failure/cost/maintenance + proposed count<=3; no hidden extra AST checker |

These approvals are required by existing prompt B1/B5, not newly inferred risk. Reuse prior specific user authorization; don't re-ask for authorized work. Current block request authorizes design and status records only. If later approval is required, first produce concrete reviewable proposal/diff and independent evidence within authorized scope; then identify exact rule/source and necessary decision. No hypothetical warning/permission request during this design.
No automatic active-rule editing just because historical architecture differs. Existing director overrides remain effective; historical AGENTS/source references unchanged. Sol technical acceptance cannot grant human policy/artifact approval. Independent review, if unavailable, UNVERIFIED; Astra advice alone never execution proof.

### B5.3 Completion / Defect Repair / End Report

Code completion: actual file/live path +required passing tests +coverage/body hit from same snapshot, plus applicable pinned replay/schema/migration/manifest/import/build acceptance. Follow B2 VERIFIED_3WAY semantics; missing/stale evidence => ACCEPTANCE_UNVERIFIED/FAIL, never invented green. Document-only DONE uses real artifact/content/link/diff checks, no artificial runtime tests. Manual Phase0 bounded item evidence remains explicit; report/coverage tooling not a fifth item.
READY=complete order/prerequisites, not implemented. Sol may mark DONE only after actual scoped review/acceptance and honest evidence; future capability not made DONE by registering a stub/dummy engine. Technical/product/director approval statuses distinct.
For defects: reproduce exact trigger/input/expected-versus-actual; identify root cause and affected source/callers/contracts; prepare bounded repair +independently derived regression; apply/verify repair/full appropriate regression/replay. Don't silently broaden into new engines/refactors. Astra consultation only if concrete diagnosis/remedy remains blocked: give attempted fixes/results/contracts and one focused question, then Sol validates advice. Missing external/hardware support UNVERIFIED with actual limitation; complete unaffected authorized work.
End report: concise Korean result +linked changed files, actual checks/limits, remaining issue and next task. Detailed stdout/test IDs/diff/live path/version/hash evidence linked in task record/B2 inputs; do not paste full logs in chat. Planned checks never described as executed. Default max6 short lines, combine equivalent facts; material blockers/errors/approval explanation may exceed brevity target. Model/task names don't launch tooling/change actual model.

```text
TASK_ID / STATUS: DONE | READY_FOR_REVIEW | BLOCKED | UNVERIFIED
CHANGED: actual paths / review link
VERIFIED: actual command/exit/result / NOT_RUN + reason
ACCEPTANCE: file + required tests + live coverage/replay / document checks
LIMITS: remaining error, missing hardware/provider/independent proof
NEXT: one task ID/action; explicit protected approval only if needed
```

This is a bounded report schema, not mandatory verbose six-line chat for trivial work; concise combined prose may carry the same facts. Handoff/backlog records updated with paths/results; no task-history deletion/report-generator enactment. Runtime code/tests/tool/config/CI implementation still NOT_STARTED.

### B5.4 Interface-level Specification

Shared declarations from BLOCK2–7; frozen developer-workflow DTOs outside authoritative Brain. This specifies future interpretation, not a gate runner implementation.

```python
GateId: TypeAlias = Literal[
    "G01", "G02", "G03", "G04", "G05", "G06", "G07",
    "G08", "G09", "G10", "G11"
]

@dataclass(frozen=True)
class GateSpec:
    gate_id: GateId
    tool_type: Literal["standard", "harness", "custom"]
    required_source_kinds: tuple[str, ...]
    required_test_node_ids: tuple[str, ...]
    time_target_seconds: int
    activation_stage: str
    policy_hash: str

@dataclass(frozen=True)
class GateResult:
    gate_id: GateId
    evidence: tuple[EvidenceRef, ...]
    status: EvidenceStatus
    findings: tuple[Failure, ...]

@dataclass(frozen=True)
class ScopeEvidence:
    task_id: str
    live_trigger_reference: str
    existing_responsibility_search: str
    extension_rejection_reason: str
    need_basis: Literal["playtest", "mandatory_master", "phase0_scaffold"]
    need_reference: str
    allowed_paths: tuple[str, ...]
    acceptance_reference: str

@dataclass(frozen=True)
class SessionBaseline:
    task_id: str
    head: str
    source_fingerprint: str
    dirty_paths: tuple[str, ...]
    stage: str
    baseline_evidence: tuple[EvidenceRef, ...]
    approved_order_hash: str

@dataclass(frozen=True)
class SessionDelivery:
    task_id: str
    baseline: SessionBaseline
    final_source_fingerprint: str
    changed_paths: tuple[str, ...]
    gate_results: tuple[GateResult, ...]
    acceptance: BacklogEvidence
    independent_review: EvidenceStatus
    next_task_id: str | None
```

Exactly one GateSpec/result per activated ID; duplicate/unknown/missing ID prevents a full11-pass claim. Deferred gates retain stage/reason/evidence status, never PASS on zero observations. Time_target_seconds is diagnostic TARGET, not hard failure threshold. GateResult PASS only from current complete required evidence; producer FAIL/stale/hash conflict cannot be overridden by summary. ScopeEvidence is reviewed checklist data, not automatic approval/new checker. phase0_scaffold basis confined to explicit1–2 dummy skeleton scope. SessionBaseline pins authorized order and unrelated dirty paths; SessionDelivery cannot silently claim they were committed or independently reviewed.
Chosen: stage-appropriate11 checks +separate async qualification, bounded authorized tasks and evidence-backed delivery. Rejected: timing-flaky commit gate, twelve-plus checks, all tools in Phase0, automatic policy/approval/DONE, one-chat-one-task restriction, fabricated baseline/coverage, unbounded speculative engine creation. Escape: replace pinned tool/parser/runner through equivalent evidence and approved configuration, preserving required gate families/authority and product outcomes.
Mapped: F-01..F-10 through gate/scope/evidence references; AP-01..AP-11 via B1/G01–G11 +async mutation; C-01/C-02/C-03/C-04/C-05/C-06 via workload/offline/runtime/platform/progression limits.

## PLANNED Acceptance Examples

| Case | Expected result |
|---|---|
| Gate IDs1–11/time sum | Exactly11,4standard/5harness/2custom;58+2=60s TARGET, no measured claim |
| Counter passes, wall-time target exceeded | G08 passes actual deterministic conditions, timing regression reported; device qualification handled separately |
| Golden hashseed0/1/random or X,Y vsY,X mismatch | G05/G06 fail corresponding identity/contamination condition; no baseline reset |
| Required body has import lines only | G07 fails actual body/live-hit requirement |
| Metadata present, no current proxy evidence | G10 UNVERIFIED/fail complete-gate claim; cannot certify access from declaration alone |
| Unsupported/v1 save or missing required fixture | Explicit rejection/G09 failure; no v1 compatible-save claim |
| Generated candidate not approved vs unapproved asset in build | Candidate state reported; build selection fails G11 |
| Mutation killed8/survived2 |80% measured score; qualifying only if no unresolved conditions and independent invariant/triage present |
| Mutation timeout/unrun/zero denominator | Separate unresolved/UNVERIFIED, no kill credit/passing qualification |
| Discretionary engine without playtest | B4 rejected; existing-schema data expansion may proceed within its authorized order |
| Mandatory MASTER feature before first playtest | Requirement+trigger/search justify minimal implementation, playtest still NOT_RUN/scheduled |
| New Any/custom checker/policy/test deletion | Prepare concrete protected proposal; explicit authorized scope required before enactment |
| Baseline stale or changed unrelated user files | Reconcile actual source/results; preserve user work, no destructive reset |
| Interface/dummy/docs exist but feature evidence missing | No gameplay DONE; document verification remains separate |

## Completion / Next

B3–B5 designs/interfaces/alternatives/mappings specified. Gate types/time/failure/activation/platform; async80% mutation conditions; scope evidence routes; baseline/authority/atomic delivery/repair/report contracts explicit. CI/pytest/mypy/replay/coverage/mutation/tool-lock/platform/performance execution NOT_RUN/UNVERIFIED; seconds are TARGETS only.
No active policy/tool/CI/dependency/test/code changes. Primary documents/historical v1/candidates preserved. Phase0 exactly4; custom planned2/max3/current0; commit gates exactly11; report drift/mutation async. [BACKLOG](../BACKLOG.md)/[handoff](../SESSION_HANDOFF.md) record actual document checks.
Next **RS-ARCH-002-B09 / BLOCK9 implementation roadmap/orders, risks, architecture self-check**. Stop after BLOCK8; no implementation or final architectural approval implied.

--- BLOCK 8/9 END. Enter "continue" for the next block. ---
