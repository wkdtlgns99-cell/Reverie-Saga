# QT-F14 — Read-only Dialogue Candidate Review

Date:2026-10-14 | State:LOCAL_IMPLEMENTATION_ACCEPTED | Executor/self-review;independent review NOT_RUN.
Director requests next implementation and brief explanation;art/models/assets/camera deferred.
Primary4support;related3/6. Authority:rulebook,MASTER,QTF13 plan/preparation contracts.

| Field | Contract |
|---|---|
| goal/non_goals | Validate saved plan-bound candidate and render Korean human review with source evidence/provenance;no approval/import/provider/CORE/save/client change |
| baseline/prerequisites | Dirty HEAD1ad22446d48c50b8b72a6d3af8de3c9d775134ea;tmp/qt-f14/entry.json hashes;QTF09–13 local acceptance;Python3.13.12 existing venv |
| reads | ENGINEERING_RULES,SESSION_HANDOFF,BACKLOG,GAME_SYSTEM_SUMMARY_KO,guide,MASTER,prompt,template/setup/README;actual plan/prepare/generation metadata/candidate/canonical contracts and integration callers |
| edits | NEW src/app/npc_dialogue_review.py,tests/integration/test_npc_dialogue_review.py,this order,docs/reviews/QT-F14_EXECUTION_2026-10-14.md;MODIFY README,BACKLOG,SESSION_HANDOFF,GAME_SYSTEM_SUMMARY_KO;owned tmp/qt-f14 artifacts only |
| forbidden | All other sources/tests,CORE,C#,save/wire/schema,assets,keys,provider profile/dependencies,old witnesses/archives,policies/history/remote |
| public contract | review_preparation(working:Path,content:QuestContent,npc_id:str,plan:Path,preparation:Path)->DialogueReview immutable result;render_review(review)->str Korean Markdown;CLI working/catalog/SHA/plan/preparation required,npc-id default harbor,optional fresh output else stdout |
| input/edge policy | Exact preparation/v2 fields/status NEEDS_REVIEW/non-null generation;bounded32768bytes. Exact generation/usage fields;existing candidate decoder/order/IDs/limits;nullable exact-int token counts0..MAX_INT,attempts1..2,model exact current plan. Legacy v1/CONTEXT_ONLY/extra/duplicate/missing/invalid rejected;unknown counts displayed as unknown,never zero |
| behavior/algorithm | Bounded decode preparation;check current plan;reconstruct generation with accepted validator;compare raw output hash/full metadata,context/brief/plan/request against expected current plan;recheck source/plan before result. Read-only inputs;Markdown escapes candidate markup and keeps Korean literal prose. Four conditional intents shown with observed/report certainty and source identities;report explicitly requires editorial review |
| errors | Missing/unreadable preparation→NPC_DIALOGUE_REVIEW_UNAVAILABLE;malformed/inconsistent candidate→NPC_DIALOGUE_REVIEW_INVALID;source changed→NPC_CONTEXT_STALE;existing plan errors propagate. Occupied output/pending→GENERATION_TARGET_EXISTS;CLI IO errors→NPC_DIALOGUE_REVIEW_INPUT. No report publication on validation failure |
| examples | accepted@2/report@11→two memories,reported phase,favor1,four candidate lines. wait→STALE/no report. Modified candidate without updated raw hash→INVALID. Valid rewritten prose with consistent hash may pass structural check:hashes are consistency,not signatures or narrative approval |
| wiring/performance | Standalone review CLI after QTF13 generation;no ordinary-turn registration. Constant≤2evidence/4lines;input32KiB/plan16KiB;existing bounded save reads,30s subprocess test timeout,record actual verification timings |
| verification | Real saves available/accepted/reported,current/reencoding/hash/schema/model/usage tamper,missing/oversize/stale;real source commit during read;read-only and fresh output/pending preservation;standalone network-forbidden CLI with no key;QTF13 actual saved Gemini candidate reused without API;Ruff(shared/selective),affected format,strict mypy,both imports,affected regression |
| acceptance/checkpoints | Required checks PASS,real candidate review exported,inputs byte-identical,NEEDS_REVIEW retained. CP05 not triggered:derived preparation tool,authoritative contracts unchanged;CP06 held. CORE/full/native reused unchanged,NOT_RUN this task;self-review not independent review |
| stop/delivery | Overlap/unresolved contracts→stop with evidence;no agents/commit/push/admin/approval/further task. Sync3progress docs,concise Korean primary/related/status/results |

Acceptance:[execution](../reviews/QT-F14_EXECUTION_2026-10-14.md);39new+27regression PASS,
static/import checks PASS;prior actual Gemini candidate reviewed offline/API0,inputs unchanged.
