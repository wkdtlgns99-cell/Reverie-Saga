# QT-F93 — Preserve movement-key modifier ownership

LOCAL_ACCEPTED2026-11-01after READY execution;
[receipt](../reviews/QT-F93_EXECUTION_2026-11-01.md).
Current assistant executor;self-review,not independent review.
Primary5input presentation support;related2existing moves,6state preservation,7live client.

| Field | Contract |
|---|---|
| task_id/title | QT-F93;keep shortcut chords out of movement and support uppercase WASD |
| goal/non_goals | Ctrl/Alt movement-key chords must not issue gameplay;Shift/CapsLock WASD must use existing movement. No new shortcuts,domain behavior,worker,save/schema/pins,native,dependencies,CI or policy |
| baseline | Clean main8c02ed6a4b55e373ae6fa8465610d5b6ffe62e57equals freshly fetched origin/main,0ahead/behind. F92PR25merged;PR103SUCCESS confirmed. Prior receipt records both required runs102/103full3670PASS. Correct stale F92root publication notes |
| prerequisites/read_files | ENGINEERING_RULES,HANDOFF,BACKLOG,Korean companion,MASTER input,prompt A7/ownership/checkpoints,numbered guide,AUTONOMOUS_EXECUTION,WORKSTATION_SETUP,Sol template,README,checks.yml,client.py::_key/_send/_enable,actual client/F36/F91/F92/pending fixtures,trial topology and ClientView. Existing local Python3.13.12AMD64/Tk8.6qualified;no install |
| allowed_edit_paths | MODIFY C:/Reverie Saga/src/app/client.py;C:/Reverie Saga/README.md;C:/Reverie Saga/BACKLOG.md;C:/Reverie Saga/SESSION_HANDOFF.md;C:/Reverie Saga/GAME_SYSTEM_SUMMARY_KO.md. NEW C:/Reverie Saga/tests/integration/test_tk_keyboard_modifiers.py;C:/Reverie Saga/docs/work_orders/QT-F93_TK_KEYBOARD_MODIFIERS.md;C:/Reverie Saga/docs/reviews/QT-F93_EXECUTION_2026-11-01.md. Owned tmp/qtf93 and .pytest_cache/f93-* |
| forbidden_paths | All other sources,old tests/goldens,contracts,content,settings,CI,native,reference/private user files. No agents,installation,administration or release |
| public_contract | No public API changes. Root KeyPress->_key->existing KEYS->_send->worker remains authoritative. Ignore Control(bit2),Mod1/Alt(bit3 or Win32bit17)on movement lookup. Preserve editing-widget early return. Match single-character keysyms case-insensitively;arrow keysyms retain exact existing names |
| behavior/algorithm_steps | Return for existing input/text widgets. Return when numeric Tk state contains a shortcut modifier. Otherwise normalize only one-character keysyms to lowercase,look up existing KEYS and call existing _send once. No event consumption,focus change,new bindings or direct state mutation |
| edge_policy | Shift(bit0),Lock(bit1),NumLock/unrelated state bits retain ordinary mapping. Non-numeric Tk state has no known shortcut modifier. Unknown/empty/unmapped keys remain no-op. Busy/closing _send guard remains owner;input/history/native class bindings remain owner. Ctrl+Shift/Alt+Shift cannot evade guard. No new IDs,domain units/errors/order or retry semantics |
| examples | Legacy0+Ctrl-s/Alt-Down ->no pending request,unchanged tick/view/token/history/source. Legacy0+Shift-S ->existing down to3,tick1. At open center4/tick3:uppercase W/S/A/D ->cell4/7/3/5,tick4 (Wblocked by wall1). Arrow movement and lowercase WASD retain existing results |
| wiring | Existing window KeyPress binding only;private _key updates. Real mapped native event_generate with recorded keysyms/state,real worker/SQLite and ordinary save/retry/load consumers |
| performance | Constant-time mask/single-character normalization/lookup;no new IO/replay/timer. TARGET40ignored actual shortcut chords<2s on this host,zero requests and unchanged source/view/history. Not device/MIN-SPEC qualification |
| baseline_commands | New real Ctrl/Alt/basic/reach and Shift/CapsLock uppercase cases fail against unchanged client;record actual delivered state/keysyms under tmp/qtf93/baseline.log |
| verification_commands | New plus client/F91/F92/compact/previous-save/pending affected pytest;both Ruff configs;README format selection+new test;strict mypy;both import contracts;pip check;exact CI boundary;UTF8/local links/exact8pathscope/diff/AST audit. Both published-head workflows before ordinary merge |
| test_responsibilities | Actual Ctrl/Alt letter/arrow basic/reach state preservation;uppercase4directions under Shift/Lock;ordinary keys/unrelated modifiers;native entry/slot/history ownership;save/retry/load after movement;busy/error/next input/close;40ignored chords preserve focus/source |
| acceptance | Reproduced baseline bugs;only private keyboard handler changes production behavior;all local checks pass;root trio corrects F92publication and records F93evidence. Both latest CI workflows succeed,current base/review gates permit normal PR merge,local main equal and clean |
| claude_checkpoints | NOT_APPLICABLE:private input mapping repair under accepted CP01/04/05client ownership;no new public/domain/format/concurrency boundary. Independent/native/device/CP06/release holds remain |
| stop_conditions/delivery | Repair scoped failures;escalate new semantics/overlap/unavailable checks after alternatives. User next-task request plus Director2026-10-30standing publication authority covers exact scoped commit/push/PR/ordinary merge/local sync. Complete one task;no indefinite continuation |
