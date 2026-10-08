# RS-P1-QUALITY-06 — Compact Per-Turn Engineering Rules

Status:ACCEPTED/DONE | Date:2026-10-08 | Executor/reviewer:Sol;self-review only.
Authorization:director explicitly requests a compact English per-turn rulebook,AGENTS routing,
deduplication of active process instructions,and feasible standard-test/CI enforcement.
No dependency,gameplay,public/save contract,remote setting,agent,commit or push change.

## Contract / scope

- Baseline:HEAD564c11eb1eb9f7fd7d3e72745c67afb30d9e2848;14prior dirty paths belong to
  CP01 preparation/repair. Preserve those repairs and original review packet/history.
  Local entry hash inventory:ignored `tmp/engineering-rules/baseline.json`.
- Reads:AGENTS,handoff,backlog,Korean progress,engineering quality/AP/B0/B1/B3/B5,
  MASTER,Sol template,README,actual workflow/configs,CP01 dispositions and regression callers.
- NEW:`C:\ReverieSaga\ENGINEERING_RULES.md`,
  `C:\ReverieSaga\docs\ENGINEERING_ENFORCEMENT.md`,
  `C:\ReverieSaga\tests\unit\test_engineering_rules.py`,this order.
- MODIFY:AGENTS,engineering prompt quality/checkpoint routing,Sol template,README,
  `.github/workflows/checks.yml`,`ruff-quality.toml`,BACKLOG,SESSION_HANDOFF,Korean progress.
- MODIFY:`C:\ReverieSaga\tests\integration\test_client.py` by appending only process-control
  propagation and renderer-failure/poll/input/close guards;existing assertions stay intact.
  Scope refinement after actual worker/poll/export inspection;no production repair needed.
- Forbidden:production sources,existing test assertions/goldens,locks,product/contracts,
  historical orders/reviews/manifests/archives,remote branch protection and held GOV-03.
- Rulebook is canonical for execution/repair;engineering/product contracts retain their
  authority. Preserve the existing quality heading as a stable inbound-link router.
  Every assistant turn rereads the short file from disk,including status/chat/resume;
  only relevant actions run. Contracts are loaded on task entry/scope change.
- Budget:at most550whitespace-separated words;not a measured tokenizer claim.
  Five operational sections:Preflight,Implementation,Verification,Failure Handling,Delivery.
- Standard pytest guards:mandatory entry route/local links/compactness and positive/negative
  Ruff probes for silent catches,nondeterminism,Any,global mutation and broad error assertions.
  No new custom engine/artifact checker or framework. CI runs named CP01 regression nodes
  and atomic/postcommit cases before full regression;missing selection must fail.
- Failure semantics:precommit state unchanged;postcommit/uncertain errors retain recovery
  evidence,never pretend rollback or success. Ordinary UI-boundary failures are logged;
  process-control exceptions propagate. Owned resources only;exact clone identity.
- Expected tool outcomes:each invalid source exits1 with its intended configured diagnostic;
  valid counterpart exits0. Before wiring,entry/link guards fail because the book is absent.
  These derive from approved rules and CP01 evidence,not production output.
- Claude checkpoint:NOT_APPLICABLE;governance-only delivery,no held expansion/import/release.
  CP01 historical acceptance and all later holds remain intact.

## Acceptance / execution

Capture baseline;qualify new guards before/after routing;validate local links,UTF8,stable
heading,process-policy relocation and scope. Run README lint/format/types/both dependency
contracts,risk-focused CI selection and full regression including existing replays.
Diagnose in-scope failures without weakening checks;report unavailable remote execution.
DONE requires actual results,scope self-review and synchronized three progress records.
Execution/results:

- Before routing:new standard guards3FAIL/5PASS1.79s,exit1. The three failures are intended
  missing mandatory route/rulebook checks,not gameplay defects;five lint rejection/acceptance
  probes already PASS against the existing shared/selective configuration.
- After routing:additions11PASS2.32s,exit0. Initial new-module E501/format diagnostics repaired
  by scoped formatting/literal wrapping;no assertion/config suppression or oracle change.
- Exact folded workflow guard invocation extracted from checks.yml and executed with
  `.venv/Scripts/python.exe`:24PASS8.62s,exit0. Includes8standard/document guards,10CP01 cases,
  3new process-control/render cases and3existing durable atomic/postcommit cases.
- Intentional missing-node `pytest -q --collect-only tests/unit/test_engineering_rules.py::missing_guard_probe`
  exits4;empty `pytest -q tests/unit/test_engineering_rules.py -k missing_guard_probe` exits5.
  These are qualified rejection probes,not accepted baseline failures.
- README commands:shared+selective Ruff PASS;formatter12PASS;`mypy --no-native-parser`
  PASS97files;type-inclusive imports3kept/0broken79files502dependencies;runtime imports
  1kept/0broken56files317dependencies. Existing pinned environment unchanged.
- Full `.venv/Scripts/python.exe -m pytest -q --basetemp .pytest_cache/rules-full-20261008`:
  exit0,1263PASS311.12s;no failures/skips. Existing replay/integration and all11new cases included.
- Final document audit10UTF8 Markdown/132local links+fragments/fences/whitespace PASS;rulebook465words,
  cap550. Tokenizer savings NOT_MEASURED. README/CI formatter lists match12paths;
  guard step is between temporary-parent preparation and full suite,no continue-on-error.
- Preservation:14task paths(10modified/4new);entry14dirty paths retained. All56production
  sources byte-identical to task entry,prior client tests reconstructed exactly by removing
  append-only new cases;other existing tests/fixtures/locks/contracts/history/reference/
  CP01 source feedback/input manifest unchanged. Git HEAD unchanged;diff check PASS.
- Process audit:10former quality obligations mapped in enforcement document;stable quality
  heading and task field schema retained. Repeated executable checklist removed from AGENTS,
  prompt and template;root process reminders now route. Required applicable contracts remain,
  default full historical v1 reads removed. Deferred governance/review/rights holds intact.
- Launcher stderr still reports the historical venv real-location warning;all commands above
  use actual qualified Python and retain exit/results. No reinstall/policy bypass.
- Self-review only;actual AI read/compliance cannot be measured by CI. New remote Actions
  UNVERIFIED:no commit/push/settings/provider/agent/dependency/gameplay/save-format change.
- Final rulebook/test/config/CI fingerprints unchanged after native acceptance;all14task
  files UTF8/scope-preserved and original test prefix reconstructed exactly. DONE/status and
  all three progress records synchronized;existing holds and Git HEAD retained.

## Subsequent independent review — 2026-10-08

Director returned Claude PASS WITH CORRECTIONS for the uploaded snapshot:two current-workspace
authority statements and missing renderer error reporting require bounded repairs.
[Feedback/dispositions](../reviews/RS-P1-QUALITY-06_DISPOSITIONS.md)/
[correction order](RS-P1-QUALITY-06_CORRECTIONS.md) own later execution/evidence.
Original465words/24focused/1263full results above remain historical,not corrected-byte results.
