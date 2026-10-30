# QT-F91 — Reveal focused Tk controls in compact windows

LOCAL_ACCEPTED2026-10-30after READY execution;[receipt](../reviews/QT-F91_EXECUTION_2026-10-30.md).
Current assistant executor;self-review,not independent review.
Primary5presentation support;related6save controls,7actual keyboard/client lifecycle.

| Field | Contract |
|---|---|
| goal/non_goals | Keyboard focus within the F90scrollable play region must reveal its target. No gameplay,command mapping,worker,IO,save/wire/pin/native/CI/dependency changes |
| baseline | Clean main/origin-main0dde4a6after fetching missing F89/F90and per-task publication rule;PR23merged. Preserve all tracked src/test entry hashes and client-before.py under tmp/qtf91 |
| prerequisites/reads | ENGINEERING_RULES,HANDOFF,BACKLOG,Korean companion,AUTONOMOUS_EXECUTION publication rule,MASTER presentation/input requirements,architecture checkpoints/ownership,numbered guide,Sol template,WORKSTATION_SETUP,README,client.py and real client/F89/F90/pending tests |
| allowed_edit_paths | MODIFY C:/Reverie Saga/src/app/client.py;README.md;BACKLOG.md;SESSION_HANDOFF.md;GAME_SYSTEM_SUMMARY_KO.md. NEW C:/Reverie Saga/tests/integration/test_tk_focus_visibility.py;docs/work_orders/QT-F91_TK_FOCUS_VISIBILITY.md;docs/reviews/QT-F91_EXECUTION_2026-10-30.md. Owned tmp/qtf91 and .pytest_cache/f91-* |
| forbidden_paths | Other source/contracts/old tests/goldens/content/CI/settings/native/reference/user files. No agents,installation,administration,release or new domain semantics |
| public_contract | Existing PlayWindow/worker/session APIs and controls unchanged. Private window-local FocusIn callback may adjust only play_viewport x/y views;default Tk focus traversal remains authoritative |
| behavior/algorithm_steps | For a mapped focused descendant of play_content,measure its rectangle in content coordinates. For each axis,scroll the minimum amount needed to show its full extent. If a target exceeds viewport extent,show its leading edge. Leave already visible targets alone. No focus transfer,command,history/state change,global binding,extra IO/replay or new timer |
| edge_policy | Focus outside play content,unmapped target,closed/closing window ->no viewport change. History/other-window focus cannot scroll play area. Zero/small viewport dimensions must not divide by zero. Existing entry editing,button activation,busy/error/poll/shutdown behavior retained. Focus has no numeric gameplay units or new ID/error semantics |
| examples | At900x600and900x768,basic/reach focus on previous-load button below visible play area ->button rectangle inside viewport. Tab from previous-info to previous-load follows Tk order and reveals the result;reverse traversal returns upward. Top control focus scrolls back only as needed |
| wiring | _build binds FocusIn on this root with add semantics;new private handler recognizes only its own play_content descendants and adjusts the existing canvas. Existing callbacks/worker results remain unchanged |
| performance | O(widget ancestry)UI work and two bounded canvas adjustments per focus;no polling/update recursion or domain work. Measured actual callback repetitions must complete without a new query;preserve exact SQLite bytes/view/token/history |
| baseline_commands | New real mapped Tk basic/reach600/768focus cases fail against unchanged client because target remains clipped;retain baseline log. Current Python3.13.12AMD64/Tk8.6reused |
| verification_commands | New+client/F89/F90/pending/F88affected pytest;both Ruff configs,README format selection plus new test,strict types,both import contracts,pip;exact31CIboundary,UTF8/local links/scope/diff. Reuse existing full for unchanged CORE;actual latest push/PR required server CI before ordinary merge |
| test_responsibilities | Actual focused geometry for basic/reach sizes;forward/reverse Tab traversal;horizontal/vertical visibility;already-visible no jump;history/unmapped/other-window isolation;entry ownership;pending/error/next action/close;real previous-slot preview/restore after keyboard navigation;source/state preservation |
| acceptance | Focused controls reachable and visible without extra gameplay,history/time mutation or focus theft;all local checks pass;root trio includes actual PR23publication correction and F91evidence;PR/latest required checks/reviews/ordinary merge/local main equal and clean |
| claude_checkpoints | NOT_APPLICABLE:new private scrolling behavior under existing CP01/04/05UI/async ownership,no new public/domain/format/concurrency boundary. Native/independent/device/CP06/release holds retained |
| stop_conditions/delivery | Repair task failures autonomously;escalate new semantic authority/overlap/unavailable checks after safe alternatives. Current explicit request+standing per-task rule authorizes GitHub wkdtlgns99-cell/Reverie-Saga task branch commit/push/PR/CI/ordinary main merge/local sync. Finish one task;no automatic next feature |
