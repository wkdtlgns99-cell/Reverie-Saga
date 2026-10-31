# QT-F92 — Horizontal wheel navigation in the Tk play area

LOCAL_ACCEPTED2026-11-01after READY execution begun2026-10-31;
[receipt](../reviews/QT-F92_EXECUTION_2026-10-31.md).
Current assistant executor;self-review,not independent review.
Primary5presentation support;related6save controls,7client lifecycle.

| Field | Contract |
|---|---|
| task_id/title | QT-F92;route Shift+wheel to the existing horizontal play viewport |
| goal/non_goals | Reach clipped map/controls horizontally using Shift+wheel. No gameplay,worker,save/schema/pins,native,dependency,CI or governance changes |
| baseline | Clean main c690f2f44a0eb8e6861ae8025916471f7ea504cd equals freshly fetched origin/main,0ahead/behind. PR24merged;head c8cda31 PR workflow41061193448/run100 SUCCESS. Root F91publication notes are stale and will be corrected |
| prerequisites/read_files | ENGINEERING_RULES,SESSION_HANDOFF,BACKLOG,GAME_SYSTEM_SUMMARY_KO,MASTER input/presentation,architecture ownership/checkpoints,numbered guide,AUTONOMOUS_EXECUTION,WORKSTATION_SETUP,Sol template,README verification,client.py::_scroll_play_area and real client/F89/F90/F91/pending tests. Existing local CPython3.13.12AMD64/Tk8.6;reuse pinned tools |
| allowed_edit_paths | MODIFY C:/Reverie Saga/src/app/client.py;C:/Reverie Saga/README.md;C:/Reverie Saga/BACKLOG.md;C:/Reverie Saga/SESSION_HANDOFF.md;C:/Reverie Saga/GAME_SYSTEM_SUMMARY_KO.md. NEW C:/Reverie Saga/tests/integration/test_tk_horizontal_wheel.py;C:/Reverie Saga/docs/work_orders/QT-F92_TK_HORIZONTAL_WHEEL.md;C:/Reverie Saga/docs/reviews/QT-F92_EXECUTION_2026-10-31.md. Owned tmp/qtf92 and .pytest_cache/f92-* |
| forbidden_paths | All other sources,old tests,goldens,content,settings,CI,native,reference and private user files. No agents,installation,administration or release |
| public_contract | Existing API,bindings and commands unchanged. Existing window-local additive MouseWheel callback routes only its own viewport/content descendants. Tk state Shift bit0selects x;otherwise y |
| behavior/algorithm_steps | Preserve existing ownership/exclusion guard. For nonzero delta compute units=max(1,abs(delta)//120),negative when delta>0. Shift scrolls xview;ordinary wheel scrolls yview. Only selected axis changes;Tk clamps to existing bounds. Return break only for owned play scrolling |
| edge_policy | Zero delta no-op. Positive/negative,subnotch and multiple notches use existing magnitude rule. Tk non-numeric state has no known modifier and follows ordinary vertical handling. Spinbox/Combobox retain native wheel handling even with Shift. History/status/other-window wheel never scrolls play area. Busy UI can scroll without commands;close/poll/error/recovery unchanged. No new domain IDs,errors,numeric units or mutation ownership |
| examples | At600x600,leftmost viewport,Shift+delta-120 ->xstart>0,ystart unchanged. At rightmost viewport Shift+delta120 ->xstart decreases. Ordinary delta-120 ->ystart increases,x unchanged. Shift+delta0 ->both unchanged |
| wiring | PlayWindow._build existing root MouseWheel additive binding ->_scroll_play_area ->existing canvas.xview_scroll/yview_scroll. No global binding,focus transfer,extra replay/IO/timer |
| performance | O(widget ancestry),one canvas scroll per wheel,zero backend requests. TARGET40actual Shift-wheel callbacks<2s on current host;state/source bytes unchanged. Not device/MIN-SPEC qualification |
| baseline_commands | New basic/reach Shift-wheel axis cases fail against unchanged client.py;retain log under tmp/qtf92. git status/diff and Python/Tk readiness probes |
| verification_commands | New+client/F89/F90/F91/pending affected pytest;both Ruff configs;README formatting+new test;strict mypy;both import contracts;pip check;exact CI boundary;UTF8/local links/exact scope/diff. Required published-head CI before ordinary merge |
| test_responsibilities | Real mapped basic/reach narrow windows;both directions/subnotch/multiple/zero;selected-axis isolation/clamping;native inputs/history/other-window isolation;actual previous-save restore after navigation;pending error/next action/close;40callbacks source/view/token/history preservation |
| acceptance | Baseline demonstrates missing horizontal behavior;all current checks pass. Only client.py production wheel routing changes. Root trio includes F91actual publication and F92truthful evidence. Ordinary PR/latest required CI/merge/local main SHA equality and clean worktree |
| claude_checkpoints | NOT_APPLICABLE:private UI input routing under accepted CP01/04/05ownership;no new public/domain/format/concurrency boundary. Independent/native/device/CP06/release holds remain |
| stop_conditions/delivery | Repair scoped failures;escalate unresolved semantics/overlap/unavailable checks after safe alternatives. Current user request plus standing publication rule authorizes scoped commit/push/PR/ordinary protected-main merge/local sync. Complete this one next task;no automatic further selection |
