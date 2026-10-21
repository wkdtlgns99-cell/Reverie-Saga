# QT-F37 — Match NPC activity completion text to current output

Date:2026-10-21 | Status:LOCAL_ACCEPTED | Executor/review:self,not independent.

| Field | Contract |
|---|---|
| Goal / baseline | NPC activity success uses plain Korean completion text without limiting the whole inspection to8records. Primary5screen support;related4retrieval display. main d7f3217plus accepted F34–36dirty work(6modified/6new),preserved |
| Reads / prerequisites | ENGINEERING_RULES,handoff,backlog,numbered guide,MASTER/prompt authority,Sol template,README/workstation;client_text.STATUS_TEXT/status_text,ClientSession.inspect_activity,PlayWindow._render,_verified_activity and F33inspection contract |
| Allowed edits | MODIFY C:/Reverie Saga/src/app/client_text.py,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md;NEW this order and docs/reviews/QT-F37_EXECUTION_2026-10-21.md. Owned ignored tmp/qt-f37/pytest outputs |
| Excluded | Existing F34–36production/test/evidence files,CORE,contracts,worker,save format,Unity,dependencies,private saves/reference checkout. No query/ordering/replay changes |
| Contract / wiring | status_text(ACTIVITY_INSPECTED)->저장에 남은 NPC 활동 기록을 확인했습니다. 게임 시간은 흐르지 않습니다. Existing status/debug code remains ACTIVITY_INSPECTED;only Korean display suppresses its suffix like other successful inspections |
| Edges / examples | Memory/work modes and empty/populated outputs use the same truthful generic notice. Actual mixed8and work3results stay unchanged. Error/unknown statuses retain their diagnostic codes. No new field,input,IDs,sorting or numeric policy |
| Steps / ownership / performance | Edit one status text and add code to existing success set. No mutation beyond display formatting;constant dictionary/set lookup unchanged. Native Tk smoke checks actual session inspection in both modes before/after32seconds,unchanged view/save bytes,technical code retained and errors/unknown codes visible |
| Verification / acceptance | Existing client/text/self-activity/work-inspection/rulebook tests;README lint/scoped format/types/import commands;native UI smoke. No committed test for this low-impact text fix. Exact scope,UTF-8/diff and three root status docs must agree |
| Checkpoints / stop / delivery | No new integration/checkpoint;D2OPEN,CP06held. Stop on overlapping edits or unavailable verification. Local/uncommitted only;preserve frozen Claude F34–36ZIP. F37is outside that review snapshot;no agents/commit/push/PR/merge |
