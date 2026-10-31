# QT-F92 — Horizontal wheel navigation

LOCAL_ACCEPTED2026-11-01;begun2026-10-31;self-review,not independent review.
Primary5presentation support;related6save controls,7client lifecycle.
[Order](../work_orders/QT-F92_TK_HORIZONTAL_WHEEL.md).

Fresh fetch found clean local main exactly equal to origin/main
c690f2f44a0eb8e6861ae8025916471f7ea504cd,0ahead/behind,no tracked-file differences.
F91PR24is merged;actual PR workflow41061193448/run100/job124081066517SUCCESS,
including full regression. Prior publication receipt records full3658PASS791.0s;
this is historical F91evidence,not a new local full run. Corrected stale root F91notes.
Git ownership exception is command-local;initial restricted fetch lacked FETCH_HEADwrite
permission,then permitted same fetch succeeded. No global configuration change.
Reused local CPython3.13.12AMD64/Tk8.6and pinned tools;no install/native/security changes.

Eight independent mapped basic/reach tests reproduced Shift-wheel failing to move the
horizontal axis:8FAIL7.92s. The existing window-local MouseWheel callback now chooses the
existing horizontal canvas scroll method for Tk's Shift bit,otherwise the vertical method.
Ownership guards,zero/subnotch/multiple-notch magnitude,clamping and native input exclusions
are unchanged. No new binding,focus transfer,command,IO,replay,timer or backend mutation.

New12within109affected PASS76.09s (`python -m pytest -q -rP`,six files:
test_tk_horizontal_wheel,test_tk_focus_visibility,test_tk_compact_viewport,
test_tk_previous_save,test_client,test_pending_query_feedback;
basetemp .pytest_cache/f92-affected). They cover both directions/modes,zero/subnotch/multiple
notches,axis isolation/clamping,native inputs/history/other-window ownership,actual previous
save preview/restore with source bytes preserved,pending failure/next action/poll/close.

Initial static checks found one line-length/format finding and Tk's int|string event-state
type. The final handler explicitly checks numeric state before reading Shift;non-numeric
state follows ordinary scrolling. No suppression/configuration change. Final new12PASS11.59s
at .pytest_cache/f92-final-new. Actual40Shift-wheel callbacks0.301115s;committed view/token,
history,focus,pending Future and source bytes unchanged. Current-host UI sample only.

README commands:shared/selective Ruff PASS;format13PASS;strict mypy275files PASS;
type-inclusive imports3andruntime1contracts PASS;pip check PASS. Exact unchanged CI boundary
31PASS22.45s;UTF8/544local links/exact8pathscope/diff/empty-index/production AST audit PASS,
recorded under tmp/qtf92.
Only _scroll_play_area changes production AST;all other tracked sources/old tests unchanged.
Shared CORE/backend/save/contracts/pins/CI/native untouched;reuse unchanged main evidence.
Native/editor/render/build,human UX,independent review and other-device acceptance NOT_RUN.
CP06/release holds remain.

## Publication input snapshot

Current request plus the standing per-task rule authorizes scoped commit/push/PR/latest
required checks/ordinary protected-main merge/local fast-forward. Scope:the8declared paths.
Actual head/CI/review/merge/clean-main receipts live under tmp/qtf92/publication and the
attached PR;this precommit snapshot does not claim future publication success.
No force/bypass/administration/agents/dependencies or additional feature selection.
