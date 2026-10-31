# QT-F93 — Movement-key modifier ownership

LOCAL_ACCEPTED2026-11-01;self-review,not independent review.
Primary5input presentation support;related2existing moves,6state preservation,7live client.
[Order](../work_orders/QT-F93_TK_KEYBOARD_MODIFIERS.md).

Entry clean main8c02ed6a4b55e373ae6fa8465610d5b6ffe62e57equals freshly fetched origin/main,
0ahead/behind. Actual F92PR25is merged. Fresh PR103run41213118648SUCCESS confirmed;
prior publication receipt records both102/103full3670PASS. Correct stale F92root notes.
Reused current-host CPython3.13.12AMD64/Tk8.6and pinned tools;no install/settings/native
Unity/other-device qualification. Git ownership exception remains command-local.

Baseline16FAIL16.90s:8basic/reach Ctrl/Alt letter/arrow chords submitted unintended
movement;8Shift/Lock uppercase WASD cases left center4/tick3unchanged instead of issuing
the existing move. Tests record actual native event delivery:Controlstate4,
WindowsAltstate131072,Shiftstate1,Lockstate2and uppercase keysyms.

Only _key changes production behavior. Existing editing-widget ownership remains first.
Numeric Tk Control/Alt/Mod1state prevents movement lookup;Shift/Lock remain allowed.
Only single-character keysyms are normalized to lowercase before the existing KEYS lookup.
Arrow names,unknown keys,_send busy guard,worker/command/retry/save contracts are unchanged.
No new binding,event consumption,focus transfer,IO/replay/timer or authoritative mutation.

README checks:both Ruff configurations PASS;format13PASS;strict mypy276files PASS;
type-inclusive imports3andruntime1contracts PASS;pip check PASS. Initial new-test unused
import/local and formatting findings were corrected without production/old-test workaround.
New19within128affected PASS98.41s (`python -m pytest -q -rP`,seven files:
test_tk_keyboard_modifiers,test_client,test_tk_focus_visibility,test_tk_horizontal_wheel,
test_tk_compact_viewport,test_tk_previous_save,test_pending_query_feedback;
basetemp .pytest_cache/f93-affected). Real native Ctrl/Alt letter/arrow ownership is
qualified in basic/reach modes. Independently specified center4/tick3uppercase W/S/A/D
expect cell4/7/3/5,tick4under Shift/Lock;the wall1blocks W without bypassing its real turn.
NumLock/lowercase/arrows,retry/save/load,new attachment/source preservation,native editing,
slot/history,modified uppercase/unknown keys,pending error/next input/close also pass.
Self-review strengthened the new save test to require a nonempty exported-generation set,
excluding the mutable working file before the assertion. Final new19PASS17.20s at
.pytest_cache/f93-final-new;new-test Ruff/format and strict276PASSagain.
40actual ignored shortcut chords complete in0.004079s and preserve source bytes,committed
view/token,history and focus. This is
input routing,not a new movement rule or simulation speedup. Current-host qualification only.
Exact unchanged CI boundary31PASS13.93s. UTF8/local links/exact8pathscope/diff/empty-index
and remaining production AST audit PASS;receipts live under tmp/qtf93.
Only _key changes production AST;all other sources/old tests unchanged. Shared CORE,
contracts/backend/save/pins/CI/native Unity remain unchanged;reuse current main evidence.

## Publication input snapshot

Current request plus Director2026-10-30standing authority covers the8declared paths for
commit/push/PR/both latest required workflows/ordinary protected-main merge/local sync.
Finish local acceptance before publication. Actual head/CI/review/merge/main receipts live
under tmp/qtf93/publication and the attached PR;this snapshot does not claim future success.
No force/bypass/administration/agents/dependencies or additional feature selection.
Independent/native Unity/device/CP06/release holds remain.
