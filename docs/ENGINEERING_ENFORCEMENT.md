# Engineering Rules — Enforcement / Residency

Approved2026-10-08 under [RS-P1-QUALITY-06](work_orders/RS-P1-QUALITY-06_TURN_RULEBOOK.md).
Execution policy:[ENGINEERING_RULES](../ENGINEERING_RULES.md). Read this map only when changing
governance/checks or investigating their coverage;it is not additional every-turn input.
Runtime/product contracts retain the authority of the engineering prompt/MASTER.

## Residency / deduplication audit

| Owner | Single responsibility / treatment |
|---|---|
| Root AGENTS | Mandatory per-turn disk-read route,authority/context pointers;repeated implementation/verification bullets removed |
| Root ENGINEERING_RULES | Canonical five-stage execution/repair policy;short enough for every turn |
| Prompt quality heading | Stable redirect;former10numbered process rules relocated,not competing policy |
| Prompt AP/F/C/B0–B5 and architecture BLOCKs | Detailed engineering invariants,IDs,contracts,limits,planned enforcement;preserved. Mapping summaries/reference examples are intentional,not parallel execution checklists |
| Sol work-order template | Concrete contract/edge/example/wiring/acceptance schema;duplicated executor checklist replaced by rulebook route |
| README / actual configs / CI | Human-readable commands / executable settings / ordered native job;necessary copies qualified by tests and actual command execution |
| BACKLOG / HANDOFF / Korean companion | Task/status / resume context / human progress;shared process reminders route to canonical policy |
| Historical orders,reviews,archives,v1 references,CP01 inputs | Immutable acceptance/provenance,not current per-turn rules;no retroactive deletion or relabeling |

Audit:repository-wide text search for quality/repair/source/caller/oracle/failure/read directives,
then review of AGENTS,prompt quality/checkpoints/AP/B0–B5,template,README,root context,
MASTER and architecture enforcement/roadmap. Repeated task-specific contracts/acceptance,
review provenance and product boundaries remain necessary. No product/architecture
requirement,rule ID,task history or stored oracle is deleted to save tokens.
Handoff's unconditional full-prompt/MASTER/v1 reread is replaced by applicable source-contract
reads;historical v1 is loaded only for evidence/mapping audits. Every-turn input remains the
short rulebook,not the full architecture/archives/enforcement map.

### Original quality policy traceability

| Former item | Current residence |
|---|---|
| 1 actual sources/callers/legal reuse | Preflight |
| 2 resolve required semantics | Preflight;work-order contract schema |
| 3 deterministic/barrier/atomic/retry/view/static-cache | Implementation |
| 4 domain constants/responsibility/exceptions/diagnostics | Preflight + Implementation;approved tool configuration owns thresholds |
| 5 runtime validation/exact types/internal-bug classification | Implementation |
| 6 reproduce/independent expectations/diagnostics/state/integration | Verification + Failure Handling |
| 7 baseline classification/autonomous repair/retest/escalation | Failure Handling |
| 8 no weakened assertions/goldens/suppressions;reviewed exception/oracle authority | Failure Handling |
| 9 appropriate checks/full CORE/doc-only/evidence/format separation | Verification + Implementation + Delivery |
| 10 self-review/DONE/progress/scope/review independence | Delivery;canonical checkpoint procedure retained in prompt |

## Active controls

Names/commands are actual [CI steps](../.github/workflows/checks.yml) and [README invocations](../README.md#verification).
All use existing pinned standard tools;no new dependency/custom engine or artifact checker.

| Rule / boundary | Automated mechanism / actual tests | Limit / review still required |
|---|---|---|
| Entry discoverability/compact input | `tests/unit/test_engineering_rules.py`:mandatory AGENTS route,stable quality link,local targets/fragments,five nonempty stages,≤550words | Cannot observe an AI's actual disk read,comprehension or obedience;AGENTS directs that behavior. Word limit is not a tokenizer measurement |
| Current workspace authority | Added `test_current_workspace_authorities_agree` for prompt/MASTER vs handoff | Current declarations only;historical producer paths remain valid evidence |
| Silent catch/nondeterminism/domain Any/global mutation | Existing Ruff S110/TID251/ANN401/PLW0603 +positive/negative stdin probes in that module | Qualified examples,not complete semantic/static reachability proof |
| Precise error assertions | Existing selective PT011 +positive/negative probe;new guard module included in selective scope | Selected paths only;expected error/state meaning needs contract review |
| Strict types/layers/engine independence/runtime cycles | Existing mypy and both import-linter steps | Dynamic misuse and actual game semantics require runtime tests |
| SQLite export/load errors,cleanup,owner preservation | `test_sqlite_backup_connect_failure_preserves_owner_and_slots` (export/load/previous) | Injects real external-library errors,does not mock domain outcomes |
| Exact managed-clone count | `test_clone_limit_counts_eight_files_across_sessions`;`test_clone_count_excludes_directories_and_nonclone_names` | Eight real clones incl.lock sidecars;9th fails without owner/file mutation |
| Async ordinary errors/cancellation/continued close | `test_worker_fault_projects_error_and_next_request_works`;`test_real_tk_failed_future_keeps_input_and_close_alive` | Native withdrawn Tk boundary,not final renderer/device qualification |
| Process-control propagation/owned export cleanup | Added `test_worker_process_control_exception_propagates` (KeyboardInterrupt/SystemExit) | Does not imply cancellation/termination at every possible IO instruction was tested |
| Render failure/reporting/poll/input/close | Expanded `test_real_tk_render_failure_rearms_poll_and_restores_input`:early/draw×open/closing;`test_real_tk_render_process_control_propagates` | Logs traceback,shows CLIENT_ERROR outside renderer,retains committed view/token/path;real timer/next-action/close checks. Does not promise recovery of destroyed widgets |
| Atomic rollback,uncertain COMMIT,postcommit failure truth | `test_confirmed_rollback_atomic_after_real_wake`;`test_real_commit_then_exception_resolves_new`;`test_postcommit_real_presentation_failure` | Existing durable contract,not permission to retry postcommit gameplay or claim rollback |
| Determinism/read ownership/replay/save recovery | Existing unit/integration/replay suite in full CI | Visited scenarios;future content/contract changes need new independent cases |

The new **Rulebook and integration boundary guards** step runs the small named selection
before full regression. Missing node,empty selection or failing test exits nonzero;there is no
`continue-on-error`/skip fallback. The existing full suite still runs every required test and
golden. Same-job bounded guard overlap is intentional early diagnosis,not a new numbered
G01–G11 gate or a second full heavy suite.

## Judgment / deferred controls

- Contract completeness,oracle independence,appropriate scope/reuse/architecture quality,
  exception rationale,review independence and truthful reporting remain review obligations.
  Passing lint/tests cannot prove these;review actual diff/callers/evidence.
- G07 replay-body coverage implementation remains DEFERRED/NOT_ACTIVE;mutation,custom
  manifest/artifact joins,counter/report expansion and device qualification retain their
  existing orders/limits. Do not advertise all11planned gates as implemented.
- RS-CI-002 main protection/required remote checks remains TODO;no remote setting changes.
  Remote acceptance requires actual successful required jobs on the published commit SHA;
  local qualification/workflow text/old runs cannot establish it.
- CP01[confirmed findings/residual risks](reviews/RS-REVIEW-CP01_DISPOSITIONS.md#findings)
  supplied the boundary lessons. F4 remains nonblocking in RS-STRUCT-001;this rulebook does
  not invent a demonstrated trigger or implement an unauthorized product change.
- Every BACKLOG edit still requires the Korean progress delivery;the prompt's dedicated
  companion rule owns detailed language/history semantics. Process routes need no parallel
  translation. New review findings become concise general rules only after verification,
  with an existing or new meaningful test when automatable;never copy entire feedback here.

QUALITY-06 [Claude dispositions](reviews/RS-P1-QUALITY-06_DISPOSITIONS.md) confirm two bounded
corrections;original ten-obligation preservation/deduplication remains accepted. Historical
465word/1263PASS evidence belongs to that snapshot,not the corrected files.
