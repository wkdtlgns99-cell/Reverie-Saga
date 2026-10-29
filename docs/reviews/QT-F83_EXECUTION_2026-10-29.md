# QT-F83 — Current support feedback after actual NPC replies

LOCAL_ACCEPTED2026-10-29,local Codex self-review;not independent acceptance.
Primary5presentation support;related2existing calculation,6durability,7delivery.
[Order](../work_orders/QT-F83_CALL_SUPPORT_FEEDBACK.md).

Only ClientSession production changes:reuse supply_support_plan after selected-NPC
WatchReplied in a committed publication,only when reach mode is enabled. Existing fact
scan/current snapshot,no separate replay/query/IO/cache/state. Each row is explicitly
post-response current state,not an inference about the prior-barrier cause. Generic
ClientWorker/framed/Tk/native message consumers retain their existing schema.

Baseline actual direct/framed bell11low-stock,13far-stock-ready,15adjacent-open cases:
6FAIL6.45s because the row was absent. After implementation,new7including exact retry
byte/state/no-extra-row guards and injected ordinary projection failure PASS within
54affectedPASS84.90s. Projection failure occurs after committed aid/reply;the persisted
state remains true,retry has no new facts,and a later action works. Existing tests and
domain outcomes are unchanged. Exact workflow CI boundary selection31PASS7.46s.
Ruffdefault/quality,strict263andscopedformat12PASS. Final import/document/source-scope
checks are owned by logs under tmp/qtf83;no new whole-suite run is implied.

F82's original3518passing cases plus all24recovered cases and5additional qualified
vectors remain distinct evidence,not a single green full run. F83adds7new cases.
F82performance remains12samples,mean2.014210s/max5.380210s,4miss2sTARGET/all<10s.
No global performance/native/independent/device/release claim. Native compile/editor/
render/build NOT_RUN AWAY001;no new remote CI/push/commit/PR. CP06andprior holds remain.
Human's exactly-one-further-task request is complete;no next feature or automatic loop.

Evidence:tmp/qtf83/baseline.log,affected.log,boundaries.log and final-checks.log.
