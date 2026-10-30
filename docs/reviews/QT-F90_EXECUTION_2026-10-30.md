# QT-F90 — Compact Tk play viewport

LOCAL_ACCEPTED2026-10-30;self-review,primary5presentation support;related6/7.
[Order](../work_orders/QT-F90_TK_COMPACT_VIEWPORT.md).

Entry clean main/origin-main57aa240after PR22merge;fetched refs agree. Reused installed
CPython3.13.12/Tk8.6/.venv/pinned tools on this PC;no install/settings changes.
Actual baseline basic900x600:requested height931,history y782,previous-load y607outside
the client. Initial reach probe omitted its harbor scenario and returned QUEST_DEFINITION;
exclude that invalid runtime probe. Proper existing reach fixture then reproduces clipping.
All four independent basic/reach600/768geometry tests fail on the old UI,2.20s.

Only production client.pychanges. One scrollable canvas embeds the existing full-size
map and controls;both scrollbars expose clipped content. Play/history grid rows can shrink
to120/60px;mode description wraps. Geometry follows actual content and viewport requests.
A private owned embed-width field prevents redundant Configure cycles. It is UI geometry,
not a domain cache. Window-local wheel routing leaves history and input fields independent;
zero delta is ignored and fractional notches still scroll. No domain/replay/IO path added.

Initial new9PASS4.01s. Expanded12new within104affected PASS45.72s;strict types identified
untyped standard-Tk itemcget and nullable test widget parents. Replaced the geometry read
with explicitly owned embed width and narrowed test parents,without suppressions or changes
to old tests. Final same104affected PASS45.91s on final source. Actual existing keyboard,
history reading/eviction,previous-save restore,pending-query/render/error/cancel/close and
F88support-history callers are included. No baseline failures or environment reruns here.

Current measured rectangles in both basic/reach modes:900x600history y497,height60;
900x768history y633,height92. Status and path labels are wholly inside the client.
Actual scrollbar commands expose the previous-load button;real worker/SQLite restore
preserves source bytes. Play/history wheel isolation,input wheel isolation,zero/sub-notch/
large wheel input,resize/pending-result preservation,subsequent action and close all pass.
Mapped windows are positioned off-screen for geometry tests;this is automated geometry
qualification,not human UX or final renderer acceptance. No native Unity run/build.

Static:both README Ruff configurations PASS;changed-file format2PASS;strict273files PASS;
type-inclusive import contracts3PASS/runtime1PASS;pip check PASS.
Final full README formatting selection plus new test:13PASS. Exact unchanged twelve-node
CI boundary selection:31PASS5.58s. UTF8/local links/whitespace/scope9paths PASS;only
client.pyproduction changes,all pre-existing tests/contracts/CI/native inputs preserved.
Shared CORE/backend/contracts/pins/old tests/CI/native sources remain unchanged.
F89publication records are corrected using actual PR22/jobs/refs,not inferred from notes.
Existing independent/device/CP06/release holds remain.

## Publication input snapshot

Actual PR/CI/merge/main synchronization is tracked separately from local acceptance above.
The director authorizes the scoped
commit/push/PR/latest required checks/ordinary merge/local fast-forward under the standing
per-task rule. Preserve actual final evidence in ignored tmp/qtf90/publication;do not claim
success before observing it. Finish this one task;no automatic next feature.
