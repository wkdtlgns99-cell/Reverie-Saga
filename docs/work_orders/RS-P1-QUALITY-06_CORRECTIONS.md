# RS-P1-QUALITY-06 — Independent Review Corrections

Status:ACCEPTED/DONE | Date:2026-10-08 | Executor/reviewer:Sol;patch self-review only.
Authorization:director supplied Claude review and explicitly asks to verify and fix valid issues.
Entry:HEAD564c11eb1eb9f7fd7d3e72745c67afb30d9e2848;24prior dirty paths preserved.
Ignored baseline hashes/before copies:`tmp/quality06-corrections/`.

## Scope / contracts

- Read AGENTS,ENGINEERING_RULES,handoff,backlog,Sol template,original QUALITY-06 order,
  reviewer text,actual authority statements,client poll/render/status helpers and callers/tests.
- F1:correct only the two current-workspace statements in prompt/MASTER to C:\ReverieSaga.
  Historical paths/archives stay intact;no product/architecture capability change.
- F2:ordinary rendering failures must be logged with traceback and shown as CLIENT_ERROR
  without reentering the failing renderer. Retain the delivered authoritative view/token/path;
  do not retry the Brain operation or invent rollback. Keep pending clearance,controls,
  scheduled poll and queued close alive. BaseException process-control signals propagate.
- Test the real submitted wait result,early render vs late draw failure,normal vs queued close;
  require visible status/details/logging,new timer and exactly-once tick/next action.
  Replace the prior expected propagation only under this explicit corrected requirement.
- Recommendation1 accepted:restore literal 'not arbitrary line counts' in rulebook.
  Other suggestions remain recommendations:tokenizer measurement unqualified,no new checker,
  native tests do not become remote CI acceptance. Existing deferred/protection holds remain.
- MODIFY:absolute C:\ReverieSaga paths ENGINEERING_RULES.md,src/app/client.py,
  tests/integration/test_client.py,tests/unit/test_engineering_rules.py,
  docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md,
  docs/MASTER_GAME_ARCHITECTURE.md,docs/ENGINEERING_ENFORCEMENT.md,
  docs/work_orders/RS-P1-QUALITY-06_TURN_RULEBOOK.md,BACKLOG.md,SESSION_HANDOFF.md,
  GAME_SYSTEM_SUMMARY_KO.md. NEW:this order,docs/reviews/RS-P1-QUALITY-06_FEEDBACK.txt,
  docs/reviews/RS-P1-QUALITY-06_DISPOSITIONS.md.
- MODIFY:.github/workflows/checks.yml adds the renderer process-control guard node;
  native window fixture collects retained Tk cycles on its owner thread before new workers.
  Both are bounded test-enforcement refinements;no suppressed warning or weakened assertion.
- Forbidden:CORE/domain/worker/save paths,public/save contracts,pins,goldens,archived records,
  original uploaded ZIP,test weakening,extra tools/dependencies/agents/remote settings/commit/push.
- Claude checkpoint:ad-hoc director review of QUALITY-06;not a new scheduled CP01–06 gate.
  Record reviewer scope/3doc passes/5Ruff NOT_RUN and patch rereview NOT_RECEIVED.

## Acceptance / repair loop

Reproduce F1/F2 with independently specified failing guards before production/doc fixes.
Run exact focused CI selection,full regression,README Ruff/format/types/imports,UTF8/link/scope
checks. Qualify workspace and process-control guards separately;preserve original error and
continuation obligations. Record commands/exits/results;update three progress records on acceptance.
Execution:

- F1/F2 guard-first initial run:5FAIL/1setup ERROR/1Tk unraisable warning17.39s. Failed-render
  traces retain Tk objects;test fixture now collects cycles on the owner thread before starting
  another worker. Same original production sources then6FAIL2.05s/no errors/warnings.
- First source/doc correction6PASS/2FAIL2.39s:incorrect new closing-case `not busy` expectation
  contradicted actual property `_pending is not None or _closing`. Corrected to pending cleared,
  closing still busy/open restored input;no production semantics/assertion weakening.
- Final targeted command:pytest -q two authority nodes/render failure node/render process-control
  node --basetemp .pytest_cache/quality06-corrections-final-focused:8PASS1.77s,exit0.
- Exact current workflow boundary command extracted and run with .venv/Scripts/python.exe:
 31PASS9.95s,exit0;workspace2+expanded renderer4+process-control2 included.
- README shared/selective Ruff PASS,format12PASS,mypy --no-native-parser97filesPASS;
  imports3kept/0broken79files502dependencies and runtime1kept/0broken56files317dependencies.
- Full `.venv/Scripts/python.exe -m pytest -q --basetemp .pytest_cache/quality06-corrections-full`:
  exit0,1270PASS311.94s,no skip/failure/pytest warning;all corrected tests and existing replays included.
- Rulebook469words≤550;original465word review/input archive remains historical. Token savings
  NOT_MEASURED. No new tool/checker/dependency or scheduled gate.
- Final doc/scope audit15paths/10Markdown/114local links/UTF8/fences/whitespace PASS;all unrelated bytes preserved,
  CORE/worker/save/schema/fixtures/locks/history untouched. Seven acceptance inputs pinned
  before full run and unchanged afterward;Git HEAD unchanged. Progress/status/diff/scope acceptance
  PASS;three progress records synchronized and corrections accepted. Original uploaded ZIP retained.
- Existing launcher real-location stderr retained;qualified executable/results recorded,
  no environment installation or policy change. Remote CI/patch external rereview UNVERIFIED.
