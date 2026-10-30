# RS-PUBLISH-001 — Publish each completed task

DONE2026-10-30;executor:current assistant;self-review. Primary7workflow support.
Authority:director explicitly requests a standing per-task PR/merge/main-sync rule and
one next task. This is not authorization for an indefinite development loop.

| Field | Contract |
|---|---|
| goal/non_goals | Persist per-task publication authority;finish pending F88publication,then publish this rule before the next implementation. No gameplay,CI/protection/dependency/release change |
| baseline | Clean21a707b on codex/qt-f88-conversation-support-20261029;main4cc0004. F88PR20created under this request;required run41017530781in progress |
| prerequisites/read_files | ENGINEERING_RULES,HANDOFF,BACKLOG,Korean companion,AUTONOMOUS_EXECUTION,WORKSTATION_SETUP,numbered guide,Sol template,MASTER,architecture review procedure,README,.github/workflows/checks.yml,test_engineering_rules,F88order/receipt |
| allowed_edit_paths | MODIFY C:/ReverieSaga/ENGINEERING_RULES.md,docs/AUTONOMOUS_EXECUTION.md,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md;NEW docs/work_orders/RS-PUBLISH-001_PER_TASK_MAIN.md,docs/reviews/RS-PUBLISH-001_EXECUTION_2026-10-30.md;owned ignored tmp/publication-rule |
| forbidden_paths | Runtime,old tests,CI,dependencies,protection/settings,reference and user files |
| public_contract/behavior | Rulebook links canonical detailed policy. Accepted coherent task -> scoped branch commit/push -> PR -> latest required CI/current-base/checkpoint eligibility -> ordinary merge -> fetch/fast-forward local main -> equality/clean check before next task |
| edge_policy | Related implementation/UI/tests/docs stay together. Later restrictions and pauses override default. Failed CI/conflict/gate blocks advancement;repair within scope without bypass/direct-main push/reset. Preserve unrelated changes. No standing agent/admin/release/feature-loop permission |
| examples/algorithm_steps | F88pending branch -> PR20required success -> merge -> local main equals remote;publish the rule using its own PR,then start one next bounded task. Missing checks -> wait,not merge |
| wiring | AGENTS -> ENGINEERING_RULES Delivery -> AUTONOMOUS_EXECUTION publish-each-completed-task;remove contradictory old batching default |
| performance | NOT_APPLICABLE:documentation only;keep existing550word rulebook bound |
| baseline_commands | Git clean and tools discovered. Reused local CPython3.13.12/Tk8.6/.venv. GitHub CLI auth failed;connected GitHub tools available instead |
| verification_commands/test_responsibilities | Existing tests/unit/test_engineering_rules.py,UTF8/local links,scope/git diff checks. Unchanged CI qualifies each published head. No new mirror tests for prose |
| acceptance | No conflicting active batching default;rulebook<=550words and10guards PASS;root trio updated;F88and rule PR merged without bypass;local main exactly remote |
| claude_checkpoints | NOT_APPLICABLE:new director workflow preference,no architecture/runtime boundary. Existing native/independent/device/CP06/release holds remain |
| stop_conditions/delivery | Preserve actual branch/PR/job on a blocker;do not begin next implementation until publication completes. User explicitly authorizes scoped commits/push/PR/merge/local sync |
