# BLOCK 7 — Enforcement, Rule Residency & Evidence Reports

Task: RS-ARCH-002-B07 | Date:2026-10-03 | Mode:DESIGN | Owner:GPT-6.1 Sol
Authority: [v2.6 prompt](../docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md) B0–B2; [MASTER](../docs/MASTER_GAME_ARCHITECTURE.md). Historical inventory: [AGENTS_v1](../docs/reference/AGENTS_v1.md).
Extends [BLOCK1](BLOCK_01.md) mapping and [BLOCK6](BLOCK_06.md) runtime/Factory evidence. No production tooling, report generation or live governance activation in this task.

## B0. Four Enforcement Layers

Use the highest sufficient layer first. Automate facts/invariants; reserve human review for authority/product judgment. No custom substitute for standard lint/types/imports/profiling/tests. A rule may need several layers, but a report does not enforce the rule merely by displaying its result.

| Layer | Mechanism / owner | Incremental cost / practical limit |
|---|---|---|
| L1 structural | Brain-only COMMIT, frozen typed contracts, reserved ownership, registry, phase DAG, no provider/client SDK in engines | No extra checker; public architecture prevents invalid normal paths. Python malicious reflection is not a sandbox guarantee |
| L2 runtime | Recursive observed views, boundary/error guards, real replay/integration, deterministic counters, coverage/mutation, save/lifecycle tests | Measured runtime/test cost; visited-path evidence, not proof of all possible paths |
| L3 standard tools | Ruff, mypy, import-linter, pytest, coverage.py, selected mutation tool; Git/rg for review evidence | Existing capabilities/configuration; syntax/import/coverage evidence cannot establish all gameplay semantics |
| L4 custom thin wrapper | CUST-01 manifest/access comparison; CUST-02 data/artifact relationships over typed validators | Permanent maintenance; Phase1+ only when L1–L3 cannot supply project-specific comparison |

**Custom checkers planned2 / maximum3 / implemented0.** New custom checkers need a concrete unsolved requirement, L1–L3 rejection evidence and explicit director approval. Two planned wrappers already required by the prompt; this design does not authorize implementing/configuring them now. Observer/cost harness is L2, standard tools L3, report formatter aggregation; none is relabeled an AST checker.

| Wrapper | Why L1–L3 alone are insufficient / bounded responsibility |
|---|---|
| CUST-01 | Type/import checks cannot compare executed concrete field paths to declared phase capabilities. Consume A5 proxy + reducer observations and pinned manifests/schema; report four distinct categories below; no source AST reachability framework |
| CUST-02 | Shape validators cannot alone resolve project-wide IDs/refs/input-output hashes/license/approval/import associations. Reuse A10 Pydantic/JSON Schema + A14 validator output; project-specific joins only, no parallel domain rules or media engine |

Registration rejects unknown fields/types/cycles/ownership conflicts at boot; proxy/reducer guards reject undeclared read/write before COMMIT. CUST-01 aggregates proof, not a delayed replacement for runtime safety. Standard tools cannot prove every declared field was meaningfully consumed; meaningful replay/invariants/mutation supplement declared/access/coverage evidence.

| Category | Exact meaning / response |
|---|---|
| Undeclared access | Observed read/write outside expanded engine+phase manifest: contract failure, abort candidate; fail corresponding manifest test/gate |
| Unused declaration | Declared access not observed in the selected trace set: coverage gap or excess capability; report separately, resolve before engine acceptance; no automatic deletion of permissions |
| Unconsumed field | CORE field has no declared deterministic consumer. DERIVED-only fields outside this CORE requirement; real query/planner/reducer/reserved-system readers count, generic serialization/hashing is not a gameplay reader. Diagnose missing behavior vs intentionally retained data; unresolved new CORE field blocks integration |
| Zero-hit method | Registered public engine method has no executed body evidence in required replay coverage; definition/import lines alone are insufficient. Add meaningful trace/wiring or remove only through authorized scope; future dormant capability stays explicitly deferred/unregistered |

No universal grep, assignment AST, assert-count or Hypothesis-presence checker. Actual coverage of a path does not certify its meaning; mutation/invariant examples are necessary. Any intentional schema exception pins field/owner/purpose/reader/test and review, never a blanket unconsumed-field waiver.

## B1. Rule Residency / Complete Historical Mapping

| Class | Proposed residence / decision rule |
|---|---|
| ENFORCED | Highest sufficient L1–L4 mechanism; implementation/evidence must exist before claiming active enforcement |
| GATED | Bounded work-order/PR review with linked facts, exact authorization and decision; supporting tools do not make a human decision |
| JUDGMENT | Short prose in approved instructions; scope/communication/product judgment, not invented automated certainty |

The following **single mapping table** covers AP-01..AP-11 plus all48 historical items:43 numbered rules,4 report entries and the critical preamble. IDs V1-* are traceability labels for this inventory, not new active policies. Multiple classes separate automated fact checks from human acceptance; `—` means no truthful automated layer. L3 marked evidence-only supports review without enforcing it.
Historical module paths/class names/Two-Pass execution restrictions are superseded by the user's v2 direction and current authorities. B1 classifications are proposed implementation residency, not permission to mutate governance. Existing prompt-required approval rules remain effective; no new rule file/CI/backlog policy introduced here.

| Rule ID / historical source | v2 treatment / evidence | Class | Layer(s) |
|---|---|---|---|
| AP-01 | Typed engines/events/state; immediate I/O conversion; Any boundary whitelist change requires approval | ENFORCED + GATED | L1,L3 |
| AP-02 | Propagate error or explicit degraded fallback; boundary records failure; no silent catch | ENFORCED | L1,L2,L3 |
| AP-03 | Pure state-in/result-out engine tests; mocks only external adapter boundaries | ENFORCED | L3 |
| AP-04 | Protocol/ABC ellipsis allowed; actual incomplete code raises named TODO; real registration/replay before completion | ENFORCED + GATED | L1,L2,L3; review for semantic stubs |
| AP-05 | Inject instance-owned state; deeply immutable constants; same-process repeat/reversed trace evidence; Final is not deep freeze | ENFORCED | L1,L2,L3 |
| AP-06 | Canonical order/tick/semantic RNG/fixed-point; quantize before branching; no domain wall time/env/random UUID | ENFORCED | L1,L2,L3 |
| AP-07 | Refactor preserves pinned golden hashes; intentional behavior change separate reason/version; test deletion needs approval | ENFORCED + GATED | L2; L3 Git evidence-only |
| AP-08 | Deeply frozen DTOs + recursive observed views; deltas; COMMIT owns writes; proxy overhead measured separately | ENFORCED | L1,L2 |
| AP-09 | One-way imports; no same-layer cycles; type-only forward references are not runtime cycles | ENFORCED | L1,L3 |
| AP-10 | Meaningful state/integration invariants; mutation detects weak tests; no assert-count acceptance | ENFORCED + GATED | L2; independent oracle review |
| AP-11 | Independently derived boundaries/composition cases; engine-only mutation; report survivors/equivalence/timeouts distinctly | ENFORCED + GATED | L2; oracle/equivalence review |
| V1-CRITICAL / preamble | Preserve safeguards; respond to violation with scoped repair. No automatic destructive rollback/reset of shared user work | GATED | L3 Git evidence-only |
| V1-DOD-01 / DoD1 | Actual relevant pytest/full stage regression, command/exit/output retained; no fabricated execution; document-only work uses document checks | ENFORCED + GATED | L2,L3 |
| V1-DOD-02 / DoD2 | New v2 replay/invariants replace legacy state.py/world-engine/eval_runner triggers; invalid transition evidence when its contract exists | ENFORCED | L2; old path requirement retired |
| V1-DOD-03 / DoD3 | >=1 meaningful test per new feature; normal/boundary/error/integration obligations from bounded order; no artificial doc tests | GATED | L2,L3 evidence |
| V1-DOD-04 / DoD4 | Fix logic; no altered/skipped assertions just to pass; changed expected behavior explicit; deletion approval | GATED | L3 diff evidence-only; L2 mutation |
| V1-DOD-05 / DoD5 | Capture baseline/new failures, no regression; relevant full stage suite/replay; unchanged failure count alone is insufficient | ENFORCED + GATED | L2,L3 |
| V1-HYGIENE-01 / Hygiene1 | Production edits in allowed source paths; exploratory scripts isolated, not production generators | GATED | L3 diff/path evidence-only |
| V1-HYGIENE-02 / Hygiene2 | Direct file edits; inspect complete reviewable diff, no omitted implementation; short chat links full artifact | GATED | L3 Git evidence-only |
| V1-HYGIENE-03 / Hygiene3 | Scratch untracked; tests use pytest tmp_path for file isolation; no fixed scratch architecture copied | ENFORCED + GATED | L3 ignore/status; test review |
| V1-HYGIENE-04 / Hygiene4 | Exclude pycache/pyc and accidental empty implementations; intentional .gitkeep allowed, no blanket zero-byte ban | ENFORCED + GATED | L3 ignore/status; review |
| V1-HYGIENE-05 / Hygiene5 | Ruff + mypy strict; zero configured lint/type errors; no redundant pyflakes wrapper | ENFORCED | L3 |
| V1-HYGIENE-06 / Hygiene6 | Client mapping/I/O/render only; Brain rules, nonblocking UI; natural Korean player text. No mandatory app.py | ENFORCED + JUDGMENT | L1,L2,L3; language quality review |
| V1-DUP-01 / Dup1 | Search existing responsibility/schema/IDs before class/engine/template; no mechanical class-per-capability | GATED | L3 rg evidence-only |
| V1-DUP-02 / Dup2 | Reject duplicate/new-schema IDs/ref collisions in approved corpus; legacy paths not runtime inputs | ENFORCED | L1,L4 CUST-02 |
| V1-DUP-03 / Dup3 | Versioned supported migrations/fixtures; unsupported input rejected; no perpetual optional/default field debt | ENFORCED + GATED | L1,L2 |
| V1-DUP-04 / Dup4 | Explicit UTF-8 at file/wire boundaries, Korean round-trip/error cases; English compact AI prose | ENFORCED + JUDGMENT | L1,L2; prose review |
| V1-DUP-05 / Dup5 | Avoid confusing filenames within responsibility; namespaced modules allowed, no global basename-uniqueness checker | GATED | L3 rg evidence-only |
| V1-DUP-06 / Dup6 | Inspect all current callers/consumers before public signature/schema change; types/integration verify migration | ENFORCED + GATED | L2,L3 |
| V1-TWO-01 / TwoPass1 | Deterministic Python truth; authoritative rules/formulas never delegated to live LLM | ENFORCED | L1,L2,L3 |
| V1-TWO-02 / TwoPass2 | Presentation separation retained; mandatory Pass2/per-turn LLM retired. Graphical events + approved content | ENFORCED | L1 |
| V1-TWO-03 / TwoPass3 | Bounded memory/context; protected anchors CORE; derived summaries cannot replace facts; explicit capacity failure | ENFORCED | L1,L2 |
| V1-TWO-04 / TwoPass4 | Bounded network/asset retries, accepted fallback/defer + degraded; never fake successful generation/import | ENFORCED | L1,L2 |
| V1-SCOPE-01 / Scope1 | Active AGENTS/governance/CI/backlog/test-deletion/custom-checker policy changes require explicit director approval | GATED | — human authority |
| V1-SCOPE-02 / Scope2 | One responsibility per authorized task/atomic commit; several requested BLOCKs may share a chat; no mixed unrelated refactor | GATED | L3 Git evidence-only |
| V1-SCOPE-03 / Scope3 | No backlog deletion without explicit approval; authorized task/status/evidence updates preserve IDs/history | GATED | L3 diff evidence-only |
| V1-HANDOFF-01 / Handoff1 | Code acceptance links files, exact passing tests/live-path evidence; document DONE links actual document checks; summaries are not runtime proof | GATED | L2,L3 evidence |
| V1-HANDOFF-02 / Handoff2 | Verify actual HEAD/status/path/hash/start markers before adopting saved completion | GATED | L3 Git/rg evidence-only |
| V1-HANDOFF-03 / Handoff3 | Missing external/tool/platform evidence UNVERIFIED; old Qdrant/Docker not mandatory; never infer pass from environment absence | GATED | L2,L3 evidence |
| V1-WIRING-01 / Wiring1 | Feature requires actual v2 command->scheduler->engine->COMMIT->consumer live path; no old TwoPass/GameMaster wiring | ENFORCED + GATED | L1,L2 |
| V1-WIRING-02 / Wiring2 | Runtime replay body coverage + explicit registry/callers; grep supports search, cannot prove reachability | ENFORCED | L1,L2,L3 |
| V1-WIRING-03 / Wiring3 | Declared deterministic CORE readers/writers + observed access; unresolved write-only CORE fields block integration | ENFORCED | L1,L2,L4 CUST-01 |
| V1-WIRING-04 / Wiring4 | Search responsibilities before engine creation; extend/split based on ownership, not filename alone | GATED | L3 rg evidence-only |
| V1-WIRING-05 / Wiring5 | >=1 meaningful live-path integration test/new engine through v2 pipeline; standalone tests do not prove wiring | ENFORCED + GATED | L2,L3 |
| V1-WIRING-06 / Wiring6 | Schema caps/retirement/expiry for growing lists/queues/context; protected A facts not silently dropped | ENFORCED | L1,L2,L4 CUST-02 |
| V1-WIRING-07 / Wiring7 | Verify named paths/symbols/results before implemented claim; PLANNED interfaces remain design, not false implementation | GATED | L3 rg/Git evidence-only |
| V1-WIRING-08 / Wiring8 | Resolve concrete wiring/zero-hit defects before accepting affected capability; no blanket freeze on all new engine files | ENFORCED + GATED | L1,L2 |
| V1-OPS-01 / Ops1 | Brief clear Korean chat; no historical caveman persona; English compact AI documents | JUDGMENT | — prose quality |
| V1-OPS-02 / Ops2 | Preserve approved fixed facts/hardware/tasks; detailed contracts linked; authorized status updates only | GATED | L3 diff evidence-only |
| V1-OPS-03 / Ops3 | Corrected DEV-A laptop + separate DEV-B/MIN-SPEC; no historical lab role/environment assumption | GATED | L2 device evidence; authority review |
| V1-OPS-04 / Ops4 | Search and explain design choices; routine in-scope classes need no extra approval. Protected policy/scope expansion still gated | GATED + JUDGMENT | L3 rg evidence-only |
| V1-OPS-05 / Ops5 | Preserve entity/content traits semantics in typed feature schema, immutable tuple[str,...]; no v1 dataclass/default or traits on protocol/metric DTOs | ENFORCED | L1,L4 CUST-02 |
| V1-OPS-06 / Ops6 | State concrete what/why for material decisions/necessary questions; concise chat, detail linked | JUDGMENT | — explanation quality |
| V1-OPS-07 / Ops7 | Sol all coding, not skeleton-only or lower-model delegation; Astra blocker advice; modality tools bounded under A14 | GATED | L1 adapter/ownership support |
| V1-OPS-08 / Ops8 | Unit module -> actual v2 integration -> stage baseline/full regression; no historical TwoPass integration slot | ENFORCED + GATED | L2,L3 |
| V1-REPORT-01 / Report1 | Actual modified paths/full diff linked, concise Korean result; exact old headings retired | GATED | L3 Git evidence-only |
| V1-REPORT-02 / Report2 | Retain raw pytest stdout/exit/counts/node IDs in evidence; NOT_RUN explicit; no long verbatim chat requirement | GATED | L2,L3 evidence |
| V1-REPORT-03 / Report3 | Actual test node IDs/purpose/source hashes linked; planned tests marked PLANNED | GATED | L3 pytest/source evidence |
| V1-REPORT-04 / Report4 | Actual doc/code alignment, conflicts/remaining work; proposals distinct from applied policy | GATED + JUDGMENT | L3 diff/search evidence-only |

Additional current rules: human director approves A14 artifact scope; Sol performs all development/technical acceptance; Astra only unresolved-blocker advice. Automation may validate facts/import current approvals, not invent approval or independent review. English AI documentation and brief Korean chat follow the director override; JUDGMENT includes clear evidence-based disagreement instead of automatic agreement. No agent launch/model change authorized by these documents.

Governance mutation boundary: current request authorizes this design and factual handoff/backlog updates only. New active governance/CI/Any whitelist/custom-checker/backlog/test-deletion policy remains a **PROPOSAL_PENDING_APPROVAL** until explicit director approval. User-authorized existing overrides need no repeated permission. Phase1 implementation must materialize a concrete diff/config/checklist for any still-unapproved policy before approval becomes necessary; do not ask now for a hypothetical rule change. Historical AGENTS untouched; no new root AGENTS or CI config.
Destructive schema/test/backlog changes remain gated under the prompt; ordinary in-scope repairs and non-destructive document/status updates proceed under existing authorization. Approval record must identify exact proposed scope; self-review/Astra advice does not grant human permission.

## B2. Generated Progress Report

### B2.1 Inputs / Required Sections

Bootstrap: root [SESSION_HANDOFF](../SESSION_HANDOFF.md) retains concise current context; [BACKLOG](../BACKLOG.md) remains task/dependency authority. Detailed decisions/orders stay linked. Runtime/tooling absent, so **generated report NOT_AVAILABLE**, tool execution NOT_RUN. Report aggregator starts Phase1+, supplements manual records and never rewrites/deletes backlog or handoff automatically.
Later one canonical report: PLANNED `reports/PROGRESS.generated.md`. Inputs are native evidence/logs plus a small index, not separately hand-maintained status systems. Read only; never imports/boots application modules, runs tests/network, approves artifacts or edits policy during report generation.

| Required section | Evidence source / exact distinction |
|---|---|
| Snapshot | Actual HEAD + working-source/config/fixture/content/schema fingerprint, run IDs/tool versions/environment, evidence freshness/status; dirty source cannot masquerade as committed build |
| Engines | Runtime registration/schedule dump: engine IDs, active phases/dependencies/activation/ownership/cost lanes; planned engines separate, no source-scanning invention |
| Access | CUST-01 declared/observed paths with engine/phase/trace; undeclared, unused declaration, unconsumed field and zero-hit method separate |
| Replay | Real pytest/harness outcomes, initial/per-step CORE+protocol hashes/pins, contamination/hashseed/composition/DERIVED cases; missing cases UNKNOWN, never implicit pass |
| Coverage | coverage.py data + explicit registered method source ranges; body lines hit under required golden traces, plus pure/integration test evidence; import/definition hits do not establish method execution |
| Mutation | Latest engine-only mutmut or chosen cosmic-ray evidence; killed/survived/equivalent/timed-out/unrun counts, denominator/score/config/platform/engine hash, below approved threshold engines; async freshness explicit |
| Deterministic costs | A13 fixture/build/hash + per-lane tick/job calls/writes/events/owned allocations/wrappers/depth/retained bytes; baseline/current/delta/profile; unknown site coverage visible |
| Wall/memory trends | A13 benchmark environment/commands/samples/percentiles/peaks; same-device/profile comparison only, no hard timing commit gate or fabricated estimate |
| Backlog evidence | Task ID/status/dependency; actual outputs+hashes; required test node IDs/pass status; actual coverage/body/live-path hit; document evidence separate |
| Factory | Manifest counts for every A14 state, required validation FAIL/UNVERIFIED, unapproved/unlicensed artifacts, import/build associations, unresolved/retry reasons; spec/input/output/approval hashes checked by CUST-02 |
| Next work intent | Exactly one human paragraph, bounded below; priorities/intended task IDs only, cannot override generated facts |

Pytest provides [JUnit XML](https://docs.pytest.org/en/stable/how-to/output.html#creating-junitxml-format-files); coverage.py provides [JSON output](https://coverage.readthedocs.io/en/latest/commands/cmd_json.html). Preserve their native files plus actual command/exit/stdout; adapter normalizes pinned versions, not an invented cross-tool native JSON format. [Import-linter](https://import-linter.readthedocs.io/en/stable/) supplies import-contract evidence, not runtime wiring proof. Mutation output format/platform/version remains UNVERIFIED until preflight; selected parser requires actual supported samples.
No extra pytest plugin just to count tests; JUnit normalization maps test cases to actual collected node IDs, including parameterized cases, using collection output if needed. Skips/xfail/empty selection are not passing required tests. XML parsing must disable external entities/network; bounded native file parsing through reviewed adapters, raw source preserved. Coverage percentages alone do not certify required paths or independent expected values.

### B2.2 Evidence Identity / Truth / Three-way Verification

Each input: producer/type/version, exact argv/cwd/environment reference, exit code, observed status, run ID, source fingerprint, tool output path/hash, measured time/environment if relevant. No secrets/raw API keys. Normalize relative paths to project root with traversal/case collision rejection; external native outputs copied/pinned only by their authorized producer. Report metadata is DERIVED, not CORE/replay state.
Fingerprint covers executed source and relevant transitive contracts/config/fixtures/accepted packages, not HEAD alone. Hash every applicable input in stable path order; input catalog/version defines scope. If scope completeness cannot be established, freshness UNVERIFIED. A report cannot mix a prior passing test with changed implementation and call it verified. Tool output/checksum is reproducibility evidence, not protection against a malicious actor rewriting files.

| Evidence condition | Report result / action |
|---|---|
| Same fingerprint, required run complete, exit/result agree | PASS/FAIL as actual producer reports; retain exact evidence reference |
| Not executed / missing producer | NOT_RUN; truth status UNKNOWN; NOT_APPLICABLE only with approved scoped reason |
| Old fingerprint / changed dependency/profile | STALE; retain last result separately; current result UNKNOWN; no green acceptance |
| Wrong hash/path/schema, conflicting same-snapshot results | UNVERIFIED + explicit parse/integrity failure; never discard failed source in favor of passing summary |
| Scheduled mutation matches code but older than7days | STALE for weekly schedule; retain latest observed score/time; current qualification UNKNOWN; no added commit gate |
| Environment differs | Separate series; no comparison trend until device/runtime/profile equivalence established |

Observed status PASS/FAIL/NOT_RUN/UNVERIFIED/NOT_APPLICABLE and freshness CURRENT/STALE/UNKNOWN are independent. Zero findings/count0 is valid only with a complete executed scope; absent Factory manifests/tooling is NOT_RUN, not zero unlicensed artifacts. Latest run chosen by explicit index/run sequence per source, not arbitrary filesystem mtime. Same-snapshot failures remain linked, even after documented repair/new run.
Code **VERIFIED_3WAY** requires all: (1) output file exists with expected hash/real implementation, (2) required exact tests actually pass on that snapshot, (3) required replay/integration method body/live-path coverage hits. Add applicable replay/hash/migration/manifest/Factory criteria from the order; three facts are necessary, not sufficient for product acceptance. Existing file, test existence, assertion count, import hit or skeleton alone cannot certify a feature.
Document tasks use DOCUMENT_VERIFIED with real path/content/link/diff checks; coverage NOT_APPLICABLE with reason. Phase0 remains exactly its four manual bounded implementation acceptances; no report/coverage tool added as a fifth item. If line coverage does not yet exist, report cannot claim VERIFIED_3WAY; manual Phase0 unit/live integration/replay evidence remains explicit rather than fabricating percentages. Report never sets task DONE: Sol reviews acceptance and updates factual backlog under authorized scope; discrepancies between declared DONE and evidence are visible ACCEPTANCE_UNVERIFIED/FAIL.
Intentional pending/deferred schema fields/methods and incomplete live capabilities are reported separately, not hidden to reduce zero-hit counts. Equivalent mutants require reason/review; timed-out/unrun excluded from measured kill denominator but remain unresolved and cannot produce a passing qualification. Initial80% mutation score is BLOCK1 TARGET; B3 finalizes exact denominator/failure/time rules in BLOCK8, no new policy enacted here.

### B2.3 Planned Command / Outputs / Drift

All paths below **PLANNED**, none created/executable in this task. Run from `C:\Reverie Saga` with selected development Python after the approved Phase1 aggregator order exists.

```text
python -m tools.progress_report --evidence reports/evidence/index.json --backlog BACKLOG.md --intent docs/NEXT_INTENT.md --output reports/PROGRESS.generated.md
python -m tools.progress_report --evidence reports/evidence/index.json --backlog BACKLOG.md --intent docs/NEXT_INTENT.md --output reports/PROGRESS.generated.md --check
```

PLANNED implementation `tools/progress_report.py`: input adapters -> typed evidence index -> joins/derived summaries -> canonical Markdown. No scheduler/validator/test runner embedded; does not duplicate CUST-01/CUST-02 logic. Project-specific reporter is ordinary aggregation, not a third custom checker. Native producers emit facts; report cannot repair/rerun them or alter their pass/fail rules. CLI/entry point packaging requires preflight/order; planned commands are specification, not successful executed commands.
Normal mode reads pinned evidence, produces truthful PASS/FAIL/UNKNOWN sections, atomically replaces report only on complete parse/render. Partial parse/invalid input returns exit2, leaves previous output intact; stale/absent observations rendered visibly rather than fabricated. Planned input schemas distinguish an explicit unavailable source entry from a missing/corrupt required index entry. Rendered tool failures do not make formatting fail; underlying existing gate/qualification retains failure.
`--check`: read-only recompute expected canonical bytes, compare existing output; exit0 equal,1 missing/drift,2 malformed inputs/intent/integrity; no writes/no live tool/API calls. No current wall clock/generation timestamp/random ID in rendered bytes; source timestamps/run IDs retained from evidence. Sort IDs/paths/categories canonically, English UTF-8/LF; deterministic renderer version pinned. Mutation freshness evaluated against frozen as-of timestamp in the producer index, not time read during rendering. Producer refreshes that index at scheduled collection so old scores cannot remain CURRENT forever.
Report drift runs asynchronously/scheduled or at phase-end, **not a twelfth commit gate**. Exactly11 later commit gates remain B3's scope; block8 defines full gate/config/time details. Failed `--check` identifies input/output difference; regenerate from verified inputs in authorized scope, no auto-commit/push or bypass of failing tests. Runtime report generator/resources NOT_MEASURED.

### B2.4 Bounds / Reading Order / Token Budget

Human-written report section: `docs/NEXT_INTENT.md`, exactly one nonempty paragraph, max120 English whitespace-delimited words **and**1024 UTF-8 bytes, no headings/lists/status edits. Name intended task IDs/goals, link details in orders. Empty file/extra paragraph/over-limit -> exit2; if no next action, one short explicit sentence. Factory human approvals are separate decision records, not this paragraph. All other report facts machine-derived; no hand-edited generated rows.
Report compact profile TARGET<=3000 selected-model tokens: required categories always present; show total counts/status and at most10 detail rows/category, with exact omitted counts and pinned raw evidence links. Never truncate away FAIL/UNKNOWN/STALE totals or claim displayed subset is full evidence. Active task failures get reading priority; complete raw outputs remain accessible. If mandatory totals/context exceed token target, emit truthful larger report + SIZE_TARGET_EXCEEDED, not silent omission. No tokenizer configured yet; token size/savings NOT_MEASURED. Stream native evidence where possible; no unbounded world/source copies or media in report.

| Resume step | Read / budget TARGET |
|---|---|
|1| Actual HEAD/status/files and root handoff:<=1000 tokens summary; verify saved markers |
|2| BACKLOG current/dependencies/evidence for requested task:<=600 tokens; full source still authoritative |
|3| If available, canonical generated report + active-task linked raw evidence:<=3000 tokens summary |
|4| Task work order + relevant contract excerpts:<=2400 tokens target, overflow explicitly allowed for complete required contracts |
| First architecture entry | Read all three primary documents completely in prescribed order; full authority overrides compact startup target |
| Missing/mismatched input | Inspect actual original/producer evidence; status UNVERIFIED until resolved; summaries never replace omitted required reads |

Routine resumed-task initial context TARGET<=8000 tokens: four reads7000 + headroom1000; measured with selected model's tokenizer only when available. Required contract/oracle/error/approval clauses are never dropped to fit. Bootstrap has no generated report, so skip step3 with explicit NOT_AVAILABLE; do not spend tokens inventing one. No automatic new chat on every block or tool invocation; session cap/end format B5 belong BLOCK8.
Manual handoff remains context; backlog remains task dependency/status source. Generated report exposes measured state and mismatches; it is neither approval nor task authority. Later reduce duplicated historical prose by separately approved document maintenance, never delete backlog history or replace handoff silently.

### B2.5 Interface-level Specification

Shared types from BLOCK2–6; frozen boundary evidence after strict decoding. Report interfaces are developer tooling outside Brain/domain dependency layers; no import from engine into tools.

```python
EvidenceStatus: TypeAlias = Literal[
    "PASS", "FAIL", "NOT_RUN", "UNVERIFIED", "NOT_APPLICABLE"
]
EvidenceFreshness: TypeAlias = Literal["CURRENT", "STALE", "UNKNOWN"]

@dataclass(frozen=True)
class EvidenceRef:
    producer: str
    tool_version: str
    run_id: str
    source_fingerprint: str
    relative_path: str | None
    sha256: str | None
    argv: tuple[str, ...]
    cwd_reference: str
    environment_reference: str
    exit_code: int | None
    observed_status: EvidenceStatus
    freshness: EvidenceFreshness
    reason: str | None

@dataclass(frozen=True)
class MethodEvidence:
    engine_id: str
    method_name: str
    source_path: str
    body_hit: bool | None
    required_trace_ids: tuple[str, ...]
    coverage_source: EvidenceRef

@dataclass(frozen=True)
class OutputEvidence:
    expected_file: ArtifactFile
    exists: bool
    actual_sha256: str | None

@dataclass(frozen=True)
class BacklogEvidence:
    task_id: str
    declared_status: str
    output_files: tuple[OutputEvidence, ...]
    required_test_node_ids: tuple[str, ...]
    test_source: EvidenceRef
    methods: tuple[MethodEvidence, ...]
    acceptance: Literal[
        "VERIFIED_3WAY", "DOCUMENT_VERIFIED", "ACCEPTANCE_FAIL",
        "ACCEPTANCE_UNVERIFIED", "DEFERRED"
    ]

class ProgressSection(FrozenPayload, ABC):
    """Concrete section schema: native facts/totals/rows and source pins."""

@dataclass(frozen=True)
class ReportInputIndex:
    schema: TypeKey
    source_fingerprint: str
    as_of_utc: str
    renderer_version: str
    sources: tuple[EvidenceRef, ...]
    sections: tuple[ProgressSection, ...]
    tasks: tuple[BacklogEvidence, ...]
    next_intent: str

@dataclass(frozen=True)
class RenderedProgress:
    utf8_markdown: bytes
    input_index_hash: str
    diagnostics: tuple[Failure, ...]

class ProgressRenderer(Protocol):
    def render(self, inputs: ReportInputIndex) -> RenderedProgress: ...
```

Each EvidenceRef with bytes requires path+hash; unavailable source has neither, NOT_RUN/UNVERIFIED and explicit reason. Exit0 alone cannot override producer FAIL or skipped tests. Freshness/current fingerprint is derived/revalidated by input adapter, never trusted solely from hand-written index. Body_hit=None means unknown, false means measured no body hit; require every named mandatory trace/method evidence, not any unrelated hit. OutputEvidence compares actual existence/hash against A14 ArtifactFile expected path/hash/bytes, no Factory lifecycle implied. ProgressSection concrete schemas carry all required category facts/counts/source references; missing mandatory category rejects input, unavailable category has explicit status/reason. New tool-specific native formats normalize through these typed schemas, not a growing central union/Any. Pure renderer consumes fully decoded sections/tasks/intent, performs no file/tool/API I/O; outer adapter handles confined reading/atomic writing.
Chosen: thin typed aggregation of existing producer facts + short manual intent/context. Rejected: god report system, AST reachability audit, fake empty counts/coverage, manual measured status, auto-DONE/approval, report tool in Phase0, drift as12th gate. Escape: replace native parser/render format with pinned conformance samples while retaining source hashes/semantics/manual task authority.
Mapped: F-03/F-04/F-05/F-07/F-08/F-09/F-10; AP-01..AP-11 via complete matrix; C-01/C-02/C-03/C-04/C-05/C-06 through referenced contracts/evidence limits.

## PLANNED Acceptance Examples

| Case | Expected result |
|---|---|
| New undeclared hp read | Runtime abort before COMMIT; CUST-01 lists exact engine/phase/field, not unused declaration |
| Declared hp unused in trace | Unused declaration/coverage gap; do not falsely call unauthorized access or silently remove permission |
| New CORE write-only field / import-only method hit | Unconsumed / zero-hit body evidence; no feature completion |
| Feature file + passing unrelated test | ACCEPTANCE_UNVERIFIED; required exact test and body/live-path evidence missing |
| Old pass after code/config/package change | STALE/current UNKNOWN; old pass retained separately |
| Test skipped / no tests collected / hash conflict | No passing required test/acceptance; integrity conflict explicit |
| Document-only task | Actual document checks -> DOCUMENT_VERIFIED; no fabricated pytest/coverage |
| Factory ledger unavailable vs actual executed count0 | NOT_RUN/unknown vs valid measured zero; never conflated |
| Manifest GENERATED / VALIDATED / APPROVED | Distinct A14 states/counts; no inferred import/build success |
| Mutation timeout/equivalent/unrun | Separate counts, unresolved qualification; no fake kill credit |
| Same frozen index+intent -> render twice | Identical UTF-8/LF bytes independent of wall time/filesystem iteration |
|121-word/1025-byte intent or two paragraphs | exit2; no output replacement |
| --check changed source/input/intent vs report | exit1 drift; no writes/provider calls/tests/extra commit gate |
| Missing/corrupt required index | exit2; prior report retained; optional unavailable entry explicitly NOT_RUN |
| More than10 detail rows/category | All status/count totals preserved; omitted count/raw evidence links; no concealment |
| Historical AGENTS/path demands conflict | Apply current v2/director authority; inventory historical rule; no v1 copy/policy rewrite |

## Completion / Next

B0–B2 design: four layers, complete AP/v1 residency inventory, two thin-wrapper boundaries, report sources/identity/commands/drift/bounds/reading order/interfaces. Current enforcement/tool/parser/report execution UNVERIFIED; no generated evidence fabricated. Report tokens/runtime/mutation/schema/lint/coverage behavior NOT_MEASURED/NOT_RUN.
Only architecture and authorized factual handoff/backlog changes; active governance/CI/backlog/test/Any/custom-checker policies untouched. Phase0 exactly4; custom planned2/max3/current0; later commit gates11. B3/B4/B5 not authored here.
Checks recorded in [BACKLOG](../BACKLOG.md)/[handoff](../SESSION_HANDOFF.md). Next **RS-ARCH-002-B08 / BLOCK8 eleven gates, scope gates, session rules**. Stop after BLOCK7.

--- BLOCK 7/9 END. Enter "continue" for the next block. ---
