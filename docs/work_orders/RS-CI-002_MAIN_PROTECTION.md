# RS-CI-002 — Main Protection Enforcement

Status:ACCEPTED/DONE | Date:2026-10-12 | Executor/reviewer:Sol,self-review.
Authority:[turn rulebook](../../ENGINEERING_RULES.md),[template](../prompts/SOL_CODING_WORK_ORDER.md).
Director explicitly requested all three steps:inspect settings/witnesses,main protection and
actual blocking verification,then record completion in backlog/handoff.

| Contract field | Concrete scope |
|---|---|
| Goal/non-goals | Verify protected main requires PR and successful strict GitHub Actions `checks`,including administrator enforcement. No probe merge/gameplay change/protection weakening |
| Baseline | main `a5dca63e2903dc3a415cb8c5957cecfe71ab0312`;probe `51616c335718f9b738b2bd55932980b7bc9f8da3`;entry dirty files are this chat's backlog/handoff/Korean summary/reconciliation receipt |
| Prerequisites | CI-001 DONE;current director authorization includes administration/verification. Existing classic rule84462169 meets desired configuration |
| Read files | ENGINEERING_RULES,BACKLOG,SESSION_HANDOFF,GAME_SYSTEM_SUMMARY_KO,README,.github/workflows/checks.yml,prior remote receipt,template,prompt documentation/progress/checkpoint sections |
| Allowed edits | MODIFY C:/ReverieSaga/BACKLOG.md,C:/ReverieSaga/SESSION_HANDOFF.md,C:/ReverieSaga/GAME_SYSTEM_SUMMARY_KO.md,C:/ReverieSaga/docs/reviews/RS-CI-002_REMOTE_STATE_2026-10-12.md;NEW C:/ReverieSaga/docs/work_orders/RS-CI-002_MAIN_PROTECTION.md,C:/ReverieSaga/docs/reviews/RS-CI-002_ENFORCEMENT_2026-10-12.json |
| Forbidden paths | Production source/tests/workflow/pins,reference repository,unrelated local work. Remote main and original probe ref must remain unchanged |
| Public contract | GitHub classic main rule:PR required,approvals0,strict required context `checks` from app15368,admin enforcement ON,force pushes/deletions OFF |
| Behavior/ownership | Inspect current rule;retain matching settings. Create owned temporary negative-case branches at existing witness commits;open non-draft disposable PRs. Reopen original PR1 only for passing eligibility. Close all after observation |
| Edge policy | Missing check must show blocked/expected;failed check must show blocked/failure;successful check must permit merge without bypass. Unknown/transient API state means wait/reobserve. Existing-name collision means stop/reselect an unused owned name,never overwrite. No forced ref updates |
| Independent examples | Missing `d2e14581beee9615c2bafe533f665ce964401125` → no check and merge blocked;failed `3dce5d17383cfd0fab723ba03c7665e11ce65bfd` → failed checks and merge blocked;passing `51616c335718f9b738b2bd55932980b7bc9f8da3` → checks success and merge eligible |
| Algorithm | Confirm settings/main SHA;create missing then failing probes;inspect live GitHub merge widget and API states at matching head/base;reopen PR1 for clean/pass observation;close probes;verify final unchanged main/config;record exact evidence |
| Wiring | Real GitHub PRs targeting main exercise the actual saved branch rule and Actions workflow. No mocked domain/check outcomes |
| Performance | No new runtime target. Existing20min CI timeout;avoid redundant full tests if existing matching-head checks establish eligibility |
| Baseline commands | git status --short --branch;git rev-parse witness refs;GitHub GET main/rulesets/PR/check-runs;browser rule read. Prior App protection endpoint403 is an access limitation |
| Verification | Live UI missing/failed blocked messages plus disabled merge control/no bypass;API mergeable_state=blocked with exact head/base;passing clean/success enabled merge. Observe UI,never click merge/attempt unsafe invalid merge |
| Test responsibilities | GitHub performs merge admission/required CI evaluation;Sol collects settings/missing/failure/pass/final-state evidence. Local document UTF8/link/fence/scope checks;runtime tests NOT_APPLICABLE,no source change |
| Acceptance | Settings match;both negative cases blocked by required checks;positive case eligible;no admin bypass;all probes closed/unmerged;main unchanged;backlog/handoff/Korean summary synchronized |
| Claude checkpoint | NOT_APPLICABLE,infrastructure-only enforcement verification;CP02/rights/GOV-03/graphics holds retained |
| Stop conditions | Missing authority,unrelated ref/setting drift,unexpected merge eligibility for a negative case,unavailable verification. Do not merge invalid code to test rejection |
| Delivery | User authorized scoped verification PR/branch mutations and administration. Local completion records only;no production commit/push/merge or unrelated task. Retain remote witnesses,close PRs;no branch deletion without necessity |

Acceptance evidence:[portable receipt](../reviews/RS-CI-002_ENFORCEMENT_2026-10-12.json).
Historical configuration observation:[reconciliation](../reviews/RS-CI-002_REMOTE_STATE_2026-10-12.md).

## Acceptance — 2026-10-12

- Existing saved main rule matches the contract;retained without redundant setting writes.
  Current director request explicitly authorizes this administration/verification scope;
  the original setting-change actor/time remains unverified historical provenance only.
- [PR2](https://github.com/wkdtlgns99-cell/Reverie-Saga/pull/2):missing check,API `blocked`,
  required `checks` Expected,owner's Merge pull request disabled.
- [PR3](https://github.com/wkdtlgns99-cell/Reverie-Saga/pull/3):actual Ruff invalid-syntax
  rejection at disposable input line2;PR run38186970010 and push run38186963160 FAILURE;
  API `blocked`,2required failing checks,owner's Merge pull request disabled.
- [PR1](https://github.com/wkdtlgns99-cell/Reverie-Saga/pull/1):reopened at unchanged head;
  new [run38186978420](https://github.com/wkdtlgns99-cell/Reverie-Saga/actions/runs/38186978420)
  all steps SUCCESS,31focusedPASS11.21s/full1270PASS403.03s,mypy97/lint/format/imports PASS.
  After completion:API `clean`,Ready to merge,2successful checks,Merge pull request enabled.
  While its fresh check ran,old success did not unlock merging.
- All three PRs closed/unmerged after observation;main remains a5dca63,original probe51616c3.
  Branch witnesses retained. No force updates,main pushes,source/test/workflow/pin edits.
- Verification is actual server admission plus authenticated owner UI,not an attempted
  merge-endpoint write. Direct-push/force-push/deletion rejection was NOT_RUN;those protections
  were inspected as settings. No invalid code or probe was merged.
- Workflow for future changes:feature branch → PR to main → latest required `checks` green
  and branch current → merge. Solo approvals are not required;administrators cannot bypass.
- Backlog/handoff/Korean progress and portable receipt synchronized. Local document
  validation only;no local runtime rerun or production publication. Holds unchanged.
- Delivery audit:Python exit0,6UTF8 documents/JSON,110local links/fragments,fences/whitespace,
  unchanged non-CI002 task rows,exact allowed diff/closed probes/main SHA PASS;
  `git diff --check` exit0. Existing venv launcher location warning remained nonfatal;
  no reinstall/environment change.
