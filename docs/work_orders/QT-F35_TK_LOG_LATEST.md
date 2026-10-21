# QT-F35 — Return to latest Tk history

Date:2026-10-21 | Status:LOCAL_ACCEPTED | Executor/review:self,not independent.

| Field | Contract |
|---|---|
| Goal / scope | Add a Korean latest-record button beside the Tk history heading. Primary5screen support;related4NPC reading |
| Baseline | main d7f3217with accepted uncommitted F34:6modified and2new files. Preserve these changes;inspect Git before delivery |
| Prerequisites / reads | F34accepted;ENGINEERING_RULES,handoff,backlog,MASTER/prompt authority,numbered guide,workstation,README,Sol template;PlayWindow._build/_append_messages/_enable/_render and existing real Tk fixtures |
| Allowed paths | MODIFY C:/Reverie Saga/src/app/client.py,README.md,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md;NEW this order and docs/reviews/QT-F35_EXECUTION_2026-10-21.md. Owned ignored tmp/qt-f35 and unique .pytest_cache outputs |
| Excluded | CORE,worker,contracts,save format,Unity,dependencies,private saves,reference checkout;no new command/gameplay/publication |
| API / wiring | Existing PlayWindow builds a ttk.Button named log_latest_button with label 최신 기록으로;callback only calls existing Text.see(end). Heading/button share a frame at existing row7 |
| Behavior / ownership | Button scrolls displayed history to its end. F34then follows new output. No request,history mutation,view/time/save write or pending-future change;available during pending gameplay because it only scrolls |
| Edges / examples | Empty/short history:harmless. Repeated clicks:idempotent. Reading middle of80records→button→yview bottom1.0→real wait result remains followed. Busy request keeps same pending Future. Load reset remains F34behavior. IDs/numbers/error/order policies unchanged;no new external input |
| Steps / performance | Add header frame/button;native Tk smoke for mapped widget,read-only/repeated/busy/follow behavior. O(widget viewport),no new replay/IO;no benchmark claim |
| Verification / acceptance | Reuse installed Python3.13.12/Tk8.6. Run native smoke and existing test_client/document guards,README lint/format/types/import checks. No new committed tests for this low-impact UI addition. Verify exact scope and synchronized root docs |
| Checkpoints / stop | No first integration or new authority;no new checkpoint. D2OPEN,CP06held. Stop for overlapping external edits or native Tk unavailable after safe alternatives |
| Delivery | Local acceptance and receipt. No commit/push/PR/merge/agents authorized |
