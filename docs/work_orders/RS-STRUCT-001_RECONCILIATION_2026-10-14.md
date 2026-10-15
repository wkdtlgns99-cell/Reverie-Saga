# RS-STRUCT-001 — Truthful Boundary Failure Reconciliation

Date:2026-10-14 | Resumed:2026-10-15 | State:LOCAL_ACCEPTED | Executor/self-review;independent feedback NOT_RECEIVED.
Authority:[closure](OPEN_WORK_CLOSURE_2026-10-14.md),
[residual findings](../reviews/RS-REVIEW-CP01_DISPOSITIONS.md#findings).
Primary6;related5/7. Director authorized completing D5;images/modeling/camera excluded.

| Field | Contract |
|---|---|
| goal | Reconcile worker errors against the live committed attachment without rerunning commands;retain failed retired-store close ownership for shutdown retry;assess codec failure boundary |
| baseline | HEAD0f53820e2ba7996de0490115de2b9c9b97d1ff41;only V3request document initially untracked. Record exact current inputs before edits. A1–3/V1qualified;V2CI pending has no code dependency |
| prerequisites | Existing deterministic commit/recovery,ClientUpdate schema,slot atomic prepare/swap,normal Tk/Unity routes;reuse pinned Python/tool closure;no installation |
| read_files | ENGINEERING_RULES,SESSION_HANDOFF,BACKLOG,GAME_SYSTEM_SUMMARY_KO,guide/template/setup;src/app/{durable,client_session,client_worker,client,engine_bridge}.py;src/adapters/{sqlite_store,save_slots}.py;contracts/{client,persistence,state_io,turn};orchestration/{turn,serialization};tests/integration/{client,save_slots,durable_turn,sqlite_recovery,memory_client_route} and relevant replay tests |
| allowed edits | MODIFY src/app/client_worker.py,client_session.py,durable.py;src/adapters/sqlite_store.py. NEW tests/integration/test_client_reconciliation.py. This order;NEW docs/reviews/RS-STRUCT-001_EXECUTION_2026-10-14.md;closure ledger/BACKLOG/SESSION_HANDOFF/GAME_SYSTEM_SUMMARY_KO;owned tmp/open-work-closure/struct-001 witnesses |
| forbidden | CORE/engines/codec behavior,public DTO/wire/save formats,assets/scene/camera,old goldens/provider bytes/approval/checkpoint ZIPs,rules/shared tooling/locks;no delegated agents |
| public contract | Existing signatures and exact ClientUpdate fields unchanged. Error status remains explicit original SaveError code or CLIENT_ERROR;no fabricated COMMITTED/LOADED message. ClientSession.load clears prior retry iff attachment actually changed,including failure after swap |
| reconciliation | On ordinary request error,worker attempts owner.update with error status/messages/notices. No submit/recover/IO reload. Fresh view/token/path/quest facts replace cache;reset_log iff previous nonempty token differs. If fresh projection also fails,log with traceback and retain cached view plus explicit error/reset_log=false. BaseException propagates |
| load ownership | New prepared attachment remains authoritative after swap. Queue previous store by exact object before close;ordinary close failure propagates while queued ownership survives. Never undo swap/delete active clone. Successful close removes retired reference and uses existing owned-clone cleanup policy. Cleanup failures remain logged and actual files count toward existing8clone bound |
| close | SqliteCommitStore marks writes closed before IO and always retries actual connection/lock close on subsequent close;native repeated close is harmless. DurableSession shutdown attempts all queued retired and active stores;log ordinary failures,retain failed store references,raise first ordinary failure,mark session closed only when all close operations succeeded. Fatal process control propagates;no false cleanup guarantee after fatal interruption |
| examples | Real wait from tick0→1 then publication failure:CLIENT_ERROR/view tick1/revision1/disk1;retry returns original receipt/no second tick. Save at1,advance2,load swap then old-close fault:CLIENT_ERROR/view1/new token/new path/reset=true/NO_RETRY;new wait reaches2. Before-swap error retains token/path/retry/log. Persistent projection error retains cache/error until next valid attach |
| codec assessment | Inject RuntimeError only at actual registered encode_command after real valid encoding:exception explicit,head/disk/protocol unchanged,driver busy released,next valid command succeeds. Current malformed input remains existing INVALID_COMMAND behavior. No hypothetical extension bug normalized into player rejection and no speculative CORE rewrite |
| edges | Empty/unavailable owner→existing cached explicit error;same attachment→no history reset;save/load/act/retry routes use same worker boundary. No numerical formula/RNG/order changes. Resource identities owned exactly;no broad directory cleanup. KeyboardInterrupt/SystemExit not ordinary errors |
| steps | Record baseline;add independent tests/reproduce failures;small adapter/owner/worker fixes;focused failure/retry/Tk+pipe/memory/save/recovery/replay checks;static/import/full regression;self-review and synchronized progress |
| performance | No extra model/network/turn submission;at most one pure projection per ordinary error. No new device performance claim |
| verification | Existing README shared/selective Ruff;scoped format of changed files;mypy --no-native-parser;imports3+1;pytest new module+client/save_slots/durable_turn/sqlite_recovery/memory_client_route/engine_bridge+tests/replay;fresh full suite after source changes |
| acceptance | Reproduced failures become passing without weakened oracles;actual SQLite and worker lifecycle exercised;old paths/pins/goldens unchanged;errors/retry/history/token/disk truth and retired ownership verified;all required checks pass and3progress documents agree |
| checkpoints | CP01residual assessment/repair within director D5request;CP01–05remain closed,not reopened. V3independent patch rereview pending;CP06release hold retained. No new checkpoint schedule or automatic provider call |
| stops/delivery | Unknown outcome never implies rollback/success;overlapping edits/new public semantics/access limits require evidence. Publication permission for PR8 exists but any later code qualified before publication. Never mark D2/D3/D4/D6/D7complete from this bounded D5repair |

Interim:[evidence](../reviews/RS-STRUCT-001_EXECUTION_2026-10-14.md). Director explicitly stopped
for usage budget and requested Git save.55client tests/static/import PASS;full interrupted,
D5not DONE. Publish this reviewable partial state to PR8;do not wait/poll or automatically resume.

Director2026-10-15explicitly resumes the unfinished work before file cleanup/backlog delivery,
and supersedes prior publication permission:DO_NOT_COMMIT_OR_PUSH. Qualify the retained D5source
locally,reuse unchanged passing evidence,and record actual outcome before cleanup. No automatic
broader feature expansion,agents or provider call. The earlier pause/publication text is historical.

Accepted2026-10-15:unchanged retained source/test inputs,fresh full1675PASS549.13s. Earlier55client/
Tk/static/import evidence reused unchanged;current local acceptance complete. Remote publication
and independent review not claimed. [Receipt](../reviews/RS-STRUCT-001_EXECUTION_2026-10-14.md).
