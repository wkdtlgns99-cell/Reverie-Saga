# QT-F34 — Preserve Tk log reading position

Date:2026-10-21 | Status:LOCAL_ACCEPTED | Executor/review:self,not independent.

| Field | Contract |
|---|---|
| Goal / classification | Preserve the visible logical record when new messages arrive while reading older Tk history. Primary5screen support;related4NPC text and6load presentation |
| Baseline / prerequisites | Clean main d7f3217,PR12merged and synchronized in the preceding task. Reuse local Python3.13.12/Tk8.6;no new tools |
| Reads | ENGINEERING_RULES,handoff,backlog,numbered guide,MASTER/prompt authority,workstation,README;PlayWindow._append_messages/_render and real Tk fixtures |
| Allowed edits | MODIFY C:/Reverie Saga/src/app/client.py,tests/integration/test_client.py,README.md,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md;NEW this order and docs/reviews/QT-F34_EXECUTION_2026-10-21.md |
| Forbidden / non-goals | CORE,contracts,save format,worker,Unity,dependencies,reference checkout,private saves. No new gameplay or log persistence |
| Public contract / wiring | Existing _append_messages(tuple[str,...])->None called by _render and input errors;no signature/DTO change |
| Behavior / ownership | Before rebuilding Text,capture tail visibility and top logical line. Existing empty history means follow tail. Account for deque eviction by subtracting discarded lines;otherwise restore surviving top logical line. At tail follow latest output. Load's existing history.clear resets to tail |
| Edge policy / examples | 80records,top20,+1=>same record;200records,top80,+2=>old record80 at new78;evicted top=>oldest retained line. Empty messages preserve position;empty/reset history follows tail. Wrapping may align to the start of that logical record;no exact pixel guarantee. Existing truncation/order/limit unchanged |
| Steps / tests | Reproduce with actual mapped Tk widget;normal append and bounded eviction;tail following and actual save/load reset. Assert state/file bytes unchanged during read-only append |
| Performance | O(existing200records) redraw remains;constant extra bookkeeping,no benchmark threshold for this UI fix |
| Commands / acceptance | New failing real Tk cases before fix;README Ruff shared/selective,scoped format,mypy,both import contracts,affected test_client plus document guards. Shared CORE unchanged;reuse prior full CI for unchanged logic,do not claim a new full run |
| Checkpoints / stop | No new first integration or risky boundary;CP06held,D2OPEN. Stop on overlapping edits or unavailable native Tk after safe alternatives |
| Delivery | Local acceptance,receipt and three progress docs together. No commit/push/PR/merge authorized for this increment |
