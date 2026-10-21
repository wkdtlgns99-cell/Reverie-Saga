# QT-F36 — Submit Tk wait input with Enter

Date:2026-10-21 | Status:LOCAL_ACCEPTED | Executor/review:self,not independent.

| Field | Contract |
|---|---|
| Goal / baseline | Enter in the Tk wait Spinbox submits existing wait action;show the shortcut in its label. Primary5input support;related2existing wait execution. main d7f3217with accepted F34/F35uncommitted(6modified/4new paths);preserve all |
| Reads / prerequisites | ENGINEERING_RULES,handoff,backlog,MASTER/prompt authority,numbered guide,Sol template,README/workstation;PlayWindow._build/_send/_key/_enable,_payload,WaitCommand,WAIT_MAX16. Reuse Python3.13.12/Tk8.6 |
| Allowed edits | MODIFY C:/Reverie Saga/src/app/client.py,README.md,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md;NEW this order and docs/reviews/QT-F36_EXECUTION_2026-10-21.md. Owned ignored tmp/qt-f36 and unique pytest paths |
| Excluded | Other production/tests,CORE,worker,contracts,save format,Unity,dependencies,private saves/reference checkout;no new gameplay or publication |
| API / wiring | wait_input.bind(Return) calls existing _send(wait);unchanged seconds parsing,worker request and canonical validation. Only focused wait input gets shortcut;root key handler still ignores editing widgets |
| Behavior / examples | Text4+Return advances4seconds once;text16 advances16;textabc/empty => existing INVALID_INPUT;text0/-1/17 => existing INVALID_COMMAND without advancing. Pending request => existing busy no-op;repeated Return before polling retains same Future. Ordinary Enter outside the field does not wait |
| Edges / ownership | Existing int conversion and canonical1..16range/exact-type checks remain authoritative;no new validation/parser/default. No shortcut alters slot/retry/attachment/state directly. Error preserves selected text for correction. Ordering/IDs/ties unchanged |
| Steps / performance | Bind Return,add label hint,run actual focused mapped-Tk keyboard smoke(valid/boundary/invalid/duplicate/outside-field) and existing affected suite. No extra work relative to button;no benchmark claim |
| Verification / acceptance | Native smoke plus existing client/text/rulebook tests;README lint/format/types/import checks and exact scope/diff/docs consistency. No committed tests for this low-impact input convenience |
| Checkpoints / stop / delivery | No first integration or new authority;D2OPEN,CP06held. Stop on overlapping external changes/unavailable native Tk after alternatives. Local acceptance/receipt/root docs only;no commit/push/PR/merge/agents |
