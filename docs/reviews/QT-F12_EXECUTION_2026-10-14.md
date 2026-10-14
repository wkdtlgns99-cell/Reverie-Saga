# QT-F12 — Snapshot Consistency Check Acceptance

Date:2026-10-14 | Acceptance:PASS;self-review,independent review NOT_RUN.
[Order](../work_orders/QT-F12_MEMORY_SNAPSHOT_CHECK.md);primary4support,related3/6.

Actual app.npc_memory_check CLI reads a bounded snapshot and validated current save,parses exact
envelope/query/count types and compares the complete canonical result reconstructed by shared
query_document. Different binding→NPC_CONTEXT_STALE;content mismatch→NPC_MEMORY_SNAPSHOT_INVALID;
unreadable snapshot→NPC_MEMORY_SNAPSHOT_UNAVAILABLE. Final source read rechecks freshness.
Whitespace-only JSON reencoding is allowed. Consistency is point-in-time,not signed authenticity,
locking,content approval or permission to use stale data later. No save/snapshot writes.

21affected tests PASS15.88s (tmp/qt-f12/tests.xml):11new checker cases+10existing export cases.
Real committed source verifies current/after-wait stale/reencoding;modified count/evidence/query/
source/status/extra fields,malformed/oversize/missing input reject and retain original file bytes.
Actual standalone subprocess with socket/urllib audit forbidden confirms offline/read-only behavior.
Shared/selective Ruff,3file format,strict mypy147files and imports3+1 PASS;no observed failures.
Export document construction extracted into shared helper;existing export regressions pass.
README/3progress files and local links checked. CORE/full/native/live NOT_RUN for unchanged inputs;
prior evidence retained. No API/key access/dependency/agents/UI/art/publication/further task.
