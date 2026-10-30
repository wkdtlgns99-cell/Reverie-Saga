# QT-F91 — Keyboard focus visibility in the Tk play area

LOCAL_ACCEPTED2026-10-30;self-review. Primary5presentation support;related6/7.
[Order](../work_orders/QT-F91_TK_FOCUS_VISIBILITY.md).

Fetched the missing per-task publication rule,F89andF90into this actual checkout
C:/Reverie Saga. Entry branch21a707b was already contained in origin/main0dde4a6.
Fast-forwarded clean local main to0dde4a6before creating the F91task branch.
Actual PR23merged0dde4a6;its PR workflow41024446802/run97/job123959115963finished SUCCESS,
including the full regression step. This corrects root notes that still described pending
F90publication;no older local measurement is relabelled. Reused this host's existing
CPython3.13.12AMD64/Tk8.6and pinned tools;no install/native/editor/settings changes.

The four independent basic/reach900x600and900x768tests reproduced focused previous-load
buttons remaining clipped after actual focus transfer:4FAIL5.14s. Only client.pyproduction
changes:one window-local additive FocusIn binding and a private callback. It recognizes
mapped descendants of its own play content,measures target bounds and reveals only clipped
axes. Oversized targets align their leading edge. Outside/unmapped/closing targets do not
scroll;the callback never transfers focus,submits work,changes history or enters an update
loop. Existing focus traversal,entry editing,worker/durable/query callbacks remain owners.

Initial four plus unchanged F90tests16PASS10.84s. Expanded new tests first10PASS/1FAIL9.83s:
the test set entry text without positioning the caret and expected insertion at the end;
native Tk correctly inserted at the beginning. Explicitly position the test caret at end,
as existing keyboard fixtures do. No product workaround or old-test change.

Final new11within115affected PASS84.92s (`python -m pytest -q -rP`,six files:
test_tk_focus_visibility,test_tk_compact_viewport,test_tk_previous_save,test_client,
test_pending_query_feedback,test_conversation_support_plan;basetemp .pytest_cache/f91-affected).
This exercises actual mapped Tk focus,Tab/reverse Tab,Space-triggered previous-save restore,
both axes,upper/lower controls,already-visible and oversized targets,history reading,
another window,unmapped widgets,entry keyboard ownership,pending error recovery,next action
and close. Real worker/SQLite source bytes and last committed view/history are preserved.
The40native focus-update sample also preserves source/state and completes in0.339082s.
This is UI callback work,not a simulation speedup or device/UX acceptance.

README commands:shared/selective Ruff PASS;format13PASS;strict mypy274files PASS;
type-inclusive imports3andruntime1contracts PASS;pip check PASS. Exact unchanged CI boundary
selection31PASS12.51s;UTF8/local537links/input hashes/exact8pathallowlist/diff/index checks PASS.
Remaining production AST is identical after removing only the new binding/callback.
All284entry tracked source/test inputs are preserved except
client.py;CORE/backend/contracts/pins/old tests/CI/native sources remain unchanged.
Do not infer fresh native/editor/render/build or human UX/other-device acceptance.

## Publication input snapshot

Current human request and the canonical per-task rule authorize scoped GitHub
wkdtlgns99-cell/Reverie-Saga commit/push/PR/latest required checks/ordinary protected-main
merge/local fast-forward. Scope:the8declared paths only. Actual final head/CI/review/merge
and clean/equal main receipts live under tmp/qtf91/publication and the attached PR;this
precommit document does not claim future publication success. No force/protection bypass,
administration,agents,dependency/CI changes or additional feature selection.
Existing independent/native/device/CP06/release holds remain.
