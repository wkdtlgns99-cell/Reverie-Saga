# QT-F11 — Offline Query Export Acceptance

Date:2026-10-14 | Acceptance:PASS;self-review,independent review NOT_RUN.
[Order](../work_orders/QT-F11_MEMORY_QUERY_EXPORT.md);primary4support,related3/6.

Actual python -m app.npc_memory_export reuses existing read-only reader/typed selector/fresh publisher.
It emits bounded SNAPSHOT JSON with source identity/hash,query,selected evidence and count.
Developer diagnostic output is not approved dialogue/public journal or authoritative memory.

21affected tests PASS7.15s (tmp/qt-f11/tests.xml):10new export cases plus11existing query cases.
Real standalone subprocesses with socket/urllib audit forbidden verify default ordering,accepted-only,
inclusive since/zero-limit empty results,context hash and unchanged save bytes. Invalid query creates
no source/output;occupied output/pending is preserved;an actual commit between source reads rejects
the export as stale and preserves that committed state. No domain outcomes are mocked.
Ruff(shared/selective),2file format,strict mypy145files and imports3+1 PASS;no observed failures.
README and3progress files synchronized;local document links checked.
CORE/full/native/live NOT_RUN:existing authoritative modules/contracts unchanged and prior evidence
retained. No API call/credential access/dependency/agents/UI/assets/publication or further task.
