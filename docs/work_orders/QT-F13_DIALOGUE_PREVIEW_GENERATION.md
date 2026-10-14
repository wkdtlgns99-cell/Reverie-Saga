# QT-F13 — Previewed Memory Dialogue Generation

Date:2026-10-14 | State:LOCAL_IMPLEMENTATION_ACCEPTED | Executor/self-review;independent review NOT_RUN.
Director requests the next normal-sized task;art/models/assets/camera remain deferred.
Primary4(runtime AI preparation);related3(data)/6(provenance). Existing memory/quest truth unchanged.

| Field | Contract |
|---|---|
| goal/non_goals | Connect offline input preview to explicit generation using verified unchanged source/brief/request configuration;no automatic content approval/gameplay import/CORE/save/client/UI/memory expansion/vector/provider or billing change |
| baseline/prerequisites | Current dirty HEAD and input hashes tmp/qt-f13/entry.json;QT-F09–12 accepted;actual Gemini memory generation qualified;existing Python3.13.12/stdlib tooling reused |
| reads | Rulebook/handoff/backlog/guide,MASTER generation windows/BLOCK4 A8,QTF09 contracts,QTF12 freshness boundary,work-order template/setup/README;actual memory_brief/prepare_memory/reader/query/Gemini request/IO/publisher and callers/tests |
| edits | NEW src/app/npc_memory_brief.py,src/app/npc_dialogue_plan.py;tests/integration/test_npc_dialogue_plan.py,tests/adapters/test_npc_dialogue_plan_generation.py;this order/docs/reviews/QT-F13_EXECUTION_2026-10-14.md. MODIFY src/app/npc_memory_prepare.py,README,BACKLOG,SESSION_HANDOFF,GAME_SYSTEM_SUMMARY_KO. Owned tmp/qt-f13 and normal shared Gemini profile;primary.env read for authorized public-data live test only |
| forbidden | CORE/old save formats/other source/C#/wire/assets/goldens/old review manifests/archives/keys/dependencies/policies;no stale-plan fallback or edited prompt acceptance |
| public API | memory_brief moved unchanged to app.npc_memory_brief,reexport retained. plan_document(context)->JsonObject;preview_memory(working,content,npc_id,output)->NpcMemoryContext;check_plan(working,content,npc_id,plan_path)->NpcMemoryContext. prepare_memory gains keyword plan:Path\|None=None;no-plan v1 output unchanged |
| plan schema | reverie-npc-dialogue-plan/v1,status PREVIEW,full context/context_sha256,exact brief_text/brief_sha256,provider gemini/current MODEL,request_sha256 of canonical generation_request(brief). Max16384UTF8bytes;no key/path/token. Canonical hash represents semantic plan bytes,not signed approval |
| CLI | Existing npc_memory_prepare gains --preview and --plan PATH. Preview excludes --live/--plan and uses no key/provider. --plan validates before constructing provider and revalidates inside preparation. Offline plan consumption emits CONTEXT_ONLY;live requires existing key/free flags and max2requests/job/60s spacing |
| output contract | With plan only,preparation/v2 adds plan_sha256/request_sha256 to existing context/raw candidate/usage metadata. No-plan preparation/v1 bytes retained. Generated result NEEDS_REVIEW;offline generation null;fresh output never replaces existing output/pending/source/plan |
| algorithm/ownership | Freeze existing validated source;canonical brief/request fingerprint;recheck before preview publication. Load bounded plan/exact fields/hash shapes,compare source binding and entire expected document;prepare using equivalent current brief;post-generation source and plan recheck before existing atomic fresh publication. No source writes or authority transfer |
| edges/errors | Bad/missing/oversize plan→NPC_DIALOGUE_PLAN_INVALID/UNAVAILABLE;changed source→NPC_CONTEXT_STALE before provider. Edited brief/model/request/evidence/extra fields→INVALID. Current whitespace-only reencoding allowed. Occupied output/pending fails first. Provider failure/stale-after-real-commit retains prior source/plan/output and truthful usage;process-control propagates |
| examples | Preview accepted@2/report@11→PREVIEW with both memories;unchanged source+plan→v2candidate with plan/request hashes. Wait after preview→STALE/no send. Change brief with recomputed self-hash→INVALID/no send. Offline preview+plan validation→no network/no key |
| performance | Constant≤2records,existing bounded save reads;plan16KiB/brief4KiB/preparation32KiB. Existing≤180s job target/owned IO deadlines;record actual live usage/latency,not a throughput/tokenizer/account-tier guarantee |
| verification | Real stage0/2/3 previews,current/tampered/missing/oversize/read race;standalone socket-audited preview and offline plan consumption. Provider-boundary exact brief/stale/tamper zero calls/post-send source change/error/exclusive targets;actual public-data Gemini request+hash/source checks. Shared/quality Ruff,affected format,mypy,both imports,focused affected regressions;reuse unchanged CORE/full/native evidence |
| checkpoints/acceptance | CP05 NOT_TRIGGERED:derived optional preparation,existing authoritative contracts unchanged;CP06 retained. All local required checks pass;live reported independently with actual result and editorial NEEDS_REVIEW. Self-review is not independent review/production approval |
| stop/delivery | Preserve overlap/unrelated files;no agents/commit/push/upload/dependency/admin/automatic next task. Sync3progress files;concise Korean explanation with primary/related numbers and actual limits |

Acceptance:[execution](../reviews/QT-F13_EXECUTION_2026-10-14.md);98affected tests/static checks PASS.
Real preview→Gemini generation1attempt/2.149s/865tokens PASS;source/plan unchanged,candidate NEEDS_REVIEW.
