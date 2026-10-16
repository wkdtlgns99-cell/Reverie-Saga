# QT-F08 — Read-Only NPC Quest Context / Preparation

Date:2026-10-14 | State:LOCAL_IMPLEMENTATION_ACCEPTED;LIVE_CONTEXT_GENERATION UNVERIFIED;Sol execution/self-review.
Director asks to select and execute the next task. After qualified QT-F07/CP05/live generation,
select the first read-only T0 context slice under BLOCK4 A8 and MASTER §§2/7/8.
Classification:primary4(runtime AI);related3(data)/6(persistence). This is a small generation-context
foundation,not implemented long-term memory,relationship updates,BDI or vector retrieval.

| Field | Concrete contract |
|---|---|
| task_id/goal | QT-F08;read validated committed harbor quest state,project only NPC-known propositions,bind source revision/branch/hash and optionally generate a candidate |
| non_goals | No new authoritative memory component/engine/level/capacity/anchor policy,save format,rules pins,client protocol/UI,production content approval,other NPCs/vector service/new provider/dependency |
| baseline | HEAD1ad22446d48c50b8b72a6d3af8de3c9d775134ea;exact dirty input hashes in tmp/qt-f08/entry.json;prior1451full/CP05 repair/native qualification retained;old review witnesses/ZIPs frozen |
| prerequisites/reads | Rulebook/numbered guide/handoff/backlog/Korean progress,MASTER,BLOCK4 A8,QT-F07 contracts,README/setup,work-order template;actual validate_save/state_io/quest_bundle/core/protocol/quest records and Gemini/approval boundary |
| allowed_edit_paths | NEW C:/ReverieSaga/src/contracts/npc_context.py,src/app/npc_prepare.py;tests/unit/test_npc_context.py,tests/integration/test_npc_context.py,tests/adapters/test_npc_prepare.py;this order,docs/reviews/QT-F08_EXECUTION_2026-10-14.md. MODIFY README.md,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md. Owned tmp/qt-f08 evidence/diagnostic files;existing tmp/gemini-profile for one optional authorized live job;read .env primary only without output |
| forbidden_paths | Existing production Python/C#/generated wire,CORE/save/slots/contracts/pins/goldens,policies/dependencies,reference corpus/production catalog,keys/old review inputs;no live output auto-approval/key rotation |
| public_contract | Frozen NpcQuestContext(world_id,branch_id,revision,tick,core_hash,catalog_sha256,npc_id,actor_id,quest_id,known_phase,recorded_favor);exact strings,world w1-64hex/branch32hex,nonnegative exact ints,digests64hex,namespaced IDs;phase available/accepted/reported with favor0/0/1 |
| context semantics | Source is validated quest.progress/v1,not an event-history/observation timestamp. Stage0→available;stage1/2→accepted;stage3→reported. Do not export stage2 target death,enemyHP,positions,other entities,seed,save paths,session/attachment secrets. NPC knows acceptance/report,not unreported victory |
| document/signatures | context.document() canonical format reverie-npc-quest-context/v1 plus fields and deterministic known_facts;sha256 property. read_context(working:Path,content:QuestContent,npc_id:str)->NpcQuestContext uses existing read-only validate_save and merged state_io;no owner/writer attachment created |
| preparation API | context_brief(context)->DialogueBrief reuses harbor four-intent brief plus scoped NPC-known facts/constraints. prepare(working,content,npc_id,output,*,generator:DialogueGenerator|None=None)->NpcQuestContext;capture source,generate optional result,re-read/compare context before exclusive single-file publication |
| output contract | canonical format reverie-npc-preparation/v1;status CONTEXT_ONLY/NEEDS_REVIEW;context/source hash/brief hash;generation null offline or raw candidate text+raw hash/model/attempts/prompt/output/thought/total usage. Envelope≤32768bytes,context≤2048UTF8,brief≤4096UTF8;single-file publish_fresh,never overwrite |
| CLI/wiring | python -m app.npc_prepare --working EXISTING --quest-catalog FILE --quest-sha256 HEX --output FRESH;harbor only,npc defaults harbor watcher. Offline default;--live --free-tier-confirmed --free-data-use-confirmed + process GEMINI_API_KEY uses existing GeminiDialogue/default shared budget. No normal-turn provider imports/calls |
| edge_policy | Missing/invalid/wrong-pin/legacy save rejects before provider/output;foreign NPC rejects before save read;existing target/pending sibling or dangling link rejects before provider;changed branch/revision/tick/core/content→NPC_CONTEXT_STALE and no publication;failure preserves committed state/old outputs;process-control propagates |
| examples | Stage2/tick9 enemydead→accepted/favor0/quest_accepted only;no kill observation. Stage3/tick11→reported/favor1/acceptance+report+recorded favor. Load preserves saved protocol/facts in a private working copy,same snapshot→same context;later copy action changes hash while original stays unchanged. A genuinely different branch_id changes context hash. Exact retry does not change context;new talk changes revision and invalidates old binding |
| ownership/algorithm | App performs pure read-only projection from checkpoint validated by canonical registry;contracts only immutable data/canonical serialization. No engine queries DB/provider. Result is a bounded derived snapshot;future acceptance must recheck source freshness,not trust file existence or hashes alone |
| performance | Constant projection over existing11records;read validation inherits existing bounded retained-save checks. Measure current small-case context/brief bytes and actual job usage/latency;not A8 full tokenizer/100-query quality or all-world scale qualification |
| verification | Unit exact-type/hash/phase/boundary checks;real state/save/load/retry/legacy/wrong NPC/corruption/privacy,network-forbidden offline subprocess;adapter generator boundary stale-after-real-commit/failure/exclusive target/unknown usage;README Ruff/selective/format/mypy/imports and focused tests;optional one real remaining-budget call and actual source equality |
| checkpoint | CP05 NOT_TRIGGERED:no new authoritative memory/progress/reward/persistence/public game protocol. Existing first quest CP05 DONE. First authoritative memory/relationship addition requires separately completed contracts/checkpoint routing;this derived T0 slice cannot bypass it |
| acceptance/stop/delivery | All required paths/tests/static checks and actual standalone CLI pass;truthful status/limits/current byte hashes,3progress files. Stop on overlap/out-of-scope semantics or missing provider credentials/budget for live only;no publication/agents/install/remote admin/budget bypass |

The source reader is already an accepted read-only SQLite transaction. A second source check
rejects changes during generation;candidate publication is not atomic acceptance into a running
world. Published outputs remain CONTEXT_ONLY/NEEDS_REVIEW. Any later approval/import must verify
the binding again and obey current content/pin contracts. There is no claim that a quest-stage
projection implements episodic memory,all five semantic levels or the NPC's complete knowledge.

Acceptance:[execution receipt](../reviews/QT-F08_EXECUTION_2026-10-14.md);100focused/30new cases,
Ruff/format/mypy132/imports3+1 PASS;actual read-only CLI output and identical source bytes.
One primary-key live request failed;existing timeout/transient retry path then hit shared local
daily2attempt cap. No generated candidate,spare-key bypass or success claim. Optional live-context
success remains UNVERIFIED;the read-only implementation/CLI scope is locally accepted.
