# QT-F11 — Offline Memory Query Export

Date:2026-10-14 | State:ACCEPTED | Execution/self-review;primary4support,related3/6.
Director requests one similarly small task. Existing QT-F09/QT-F10 contracts govern memory/query.

| Field | Contract |
|---|---|
| goal/non_goals | Developer-only offline CLI exports filtered evidence with source/query provenance;no NPC/player journal/UI,CORE/save mutation,provider call,content approval/dependency |
| baseline/reads | Preserve current dirty work;rulebook/handoff/backlog/guide,actual query/reader/preparation/publish helpers and tests;existing Python/setup/README reused |
| edits | NEW src/app/npc_memory_export.py,tests/integration/test_npc_memory_export.py,this order,docs/reviews/QT-F11_EXECUTION_2026-10-14.md. MODIFY README,BACKLOG,SESSION_HANDOFF,GAME_SYSTEM_SUMMARY_KO;owned tmp/qt-f11 |
| API/wiring | export_memory(working:Path,content:QuestContent,npc_id:str,query:EvidenceQuery,output:Path)->NpcMemoryContext;python -m app.npc_memory_export with required working/catalog/SHA/output and optional npc-id/subject-id/kind/since/limit |
| algorithm/ownership | Validate query;reject occupied output/pending before source;canonical read_memory→select_evidence→source recheck→publish_fresh. Query filters/ranking unchanged;source file remains read-only |
| document | format reverie-npc-memory-query/v1,status SNAPSHOT,source full identity/hash,context_sha256,exact query,selected canonical evidence,count. Max8192UTF8bytes. A derived snapshot,not accepted dialogue or public UI knowledge |
| edges/examples | kindaccepted→accepted@2;since12/limit0→count0;default→report@11thenaccepted@2. Invalid flags/query reject before writing;foreign subject→empty. Source change→NPC_CONTEXT_STALE/no publication. Existing output/pending preserved;corrupt/missing save typed error;no overwrites or provider fallback |
| performance/verification | O(2)plus existing bounded source validation;actual standalone subprocess socket audit,query/source/output/error tests and affected prior query/provider tests;Ruff/format/mypy/imports/doc links. No CORE/full/native/live rerun for unchanged inputs |
| acceptance/checkpoint/delivery | Local CLI/checks pass;3progress files synchronized;CP05 NOT_TRIGGERED derived read-only support,CP06 held. No automatic next work/agents/publication/keys |

Acceptance:[receipt](../reviews/QT-F11_EXECUTION_2026-10-14.md);21affected tests and static checks PASS.
