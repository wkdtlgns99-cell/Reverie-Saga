# QT-F12 — Offline Memory Snapshot Check

Date:2026-10-14 | State:ACCEPTED | Self-review;primary4support,related3/6.
Director requests one similarly small task. Existing QT-F09–11 memory/query/export contracts apply.

| Field | Contract |
|---|---|
| goal/non_goals | Read-only CLI checks stored query snapshot against current validated save;no new memory/CORE/save schema/content approval/UI/provider/dependency |
| baseline/reads | Dirty work preserved;tmp/qt-f12/entry.json;rulebook/handoff/backlog/guide,actual query/export/reader/canonical publisher/tests;existing README/setup/tooling |
| edits | MODIFY src/app/npc_memory_export.py only to extract canonical query_document without changing export bytes;README,BACKLOG,SESSION_HANDOFF,GAME_SYSTEM_SUMMARY_KO. NEW src/app/npc_memory_check.py,tests/integration/test_npc_memory_check.py,this order,docs/reviews/QT-F12_EXECUTION_2026-10-14.md;owned tmp/qt-f12 |
| API/wiring | query_document(context,query)->JsonObject reused by export/check. check_snapshot(working:Path,content:QuestContent,npc_id:str,snapshot:Path)->NpcMemoryContext. python -m app.npc_memory_check with working/catalog/SHA/snapshot/optional npc-id |
| validation/algorithm | Read≤MAX_EXPORT_BYTES+1;exact envelope/format/status/query,count exact0..2 matching evidence length,objects/hash formats. Parse typed query;read current context;different context hash→NPC_CONTEXT_STALE. Compare entire canonical document to reconstructed expected query result→NPC_MEMORY_SNAPSHOT_INVALID;second source read rejects a concurrent commit |
| edges/examples | Current/whitespace-only reencoding→MEMORY_QUERY_CURRENT;actual wait after export→STALE;unchanged hash but edited evidence/count/query/source/extra fields→INVALID. Missing/unreadable file→NPC_MEMORY_SNAPSHOT_UNAVAILABLE;malformed/oversize→INVALID. Existing save/snapshot bytes never written |
| truth boundary | Point-in-time consistency,not signature/authority or automatic gameplay acceptance. A replaced binding hash may be classified STALE;not proof of historical authenticity. Later use still needs source freshness validation |
| performance/verification | O(2),bounded file/current-save reads;real current/stale/tamper/invalid/missing and network-forbidden subprocess tests plus affected export/query cases;Ruff/format/mypy/imports/doc links. Reuse unchanged CORE/full/native/live evidence |
| acceptance/checkpoints/delivery | All local checks pass,3progress files sync;CP05 NOT_TRIGGERED derived diagnostic tool,CP06 held;no agents/publication/keys/further task |

Acceptance:[receipt](../reviews/QT-F12_EXECUTION_2026-10-14.md);21affected tests/static checks PASS.
