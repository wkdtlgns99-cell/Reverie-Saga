# QUALITY-08 — Resume automatic work after quota reset

Status:READY,2026-10-23. Executor:self-review,current Codex;not independent review.
Director requests the existing continuation policy to include five-hour quota recovery
at the reported reset time,then Git publication. Existing main publication authorization
applies to this follow-up;broader development remains explicitly paused.
Support across1–7,no gameplay/runtime capability added by this document change.

| Field | Contract |
|---|---|
| goal/non_goals | Record precise quota-only same-work recovery without new user prompts;no current goal resume,scheduler creation,runtime/CI/dependency/security change or fabricated capability |
| baseline/prerequisites | Clean main926cfcb includes PR16/F48+QUALITY-07;existing rulebook535words/five stages,policy,document guards and protected main checks |
| reads | ENGINEERING_RULES,AGENTS,AUTONOMOUS_EXECUTION,handoff/backlog/Korean progress,SOL_CODING_WORK_ORDER,numbered guide,ENGINEERING_ENFORCEMENT,actual goal/Git/PR state;official scheduled-task/goal documentation already checked in this conversation |
| MODIFY | C:/ReverieSaga/ENGINEERING_RULES.md;C:/ReverieSaga/docs/AUTONOMOUS_EXECUTION.md;C:/ReverieSaga/docs/ENGINEERING_ENFORCEMENT.md;C:/ReverieSaga/BACKLOG.md;C:/ReverieSaga/SESSION_HANDOFF.md;C:/ReverieSaga/GAME_SYSTEM_SUMMARY_KO.md;this order |
| NEW | C:/ReverieSaga/docs/work_orders/RS-P1-QUALITY-08_QUOTA_RESET_RESUME.md;owned tmp/quality08/evidence |
| forbidden | Production/test/CI files,credentials/private saves,frozen evidence,goal resume or live scheduled wake-up while user-paused |
| public contract/behavior | Actual five-hour resetsAt and causal interruption reason guide a supported same-chat follow-up;recheck eligibility/user pause before resuming unfinished work. Prepare registration before hard-limit tool unavailability when necessary. No arbitrary now+5h or fixed30minute loop |
| edges/examples | Quota stop/reset/usage allowed/no user pause→resume recorded task;manual pause/reset→stay paused. Weekly cap or unavailable host→no bypass/no false recovery. Lost turn/uncertain commit→inspect actual state before retry. Unsupported scheduler→report limitation,not success |
| wiring/steps | Add detail under the existing canonical policy and a compact rulebook route;state enforcement limits;record current paused goal/progress;document checks,self-review,commit/push/PR/required CI and ordinary main sync |
| performance/tests | Documentation-only;retain≤550words/five-stage guard,run existing10document/standard-guard cases,UTF-8/local-link/scope/whitespace checks and actual goal read. No fake runtime test for prose;no actual quota-exhaustion/recovery claim |
| acceptance/checkpoints | Requested recovery rule discoverable,manual pause preserved,capability limits truthful,progress synchronized and publication verified. No new risky runtime boundary/checkpoint;existing holds remain |
| stop/delivery | Resolve document/CI/permission failures or overlapping edits. Record exact evidence;leave automatic development paused after this bounded publication |

## Local execution evidence

LOCAL_ACCEPTED2026-10-23,self-review. Added the quota-specific recovery section and
compact every-turn route;existing pause/quality/checkpoint constraints remain. Actual
get_goal returned PAUSED;no live goal resume or scheduled follow-up was performed.
This verifies policy and preserved state,not an actual quota-exhaustion/recovery run.

README .venv Python3.13.12/environment reused. Existing
`python -m pytest -q tests/unit/test_engineering_rules.py --basetemp .pytest_cache/quality08-docs`:
exit0,10PASS0.99s. Rulebook545words/five stages;≤550bound retained without changing tests.
Root progress trio synchronized. Final scope/UTF-8/local-link/whitespace and document checks
are recorded under tmp/quality08/. Required published-head CI/main results remain owned
by actual Git/GitHub state,not inferred from prior revision evidence.
