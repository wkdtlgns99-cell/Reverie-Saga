# QT-F15 — Compile Approved Memory Dialogue

Date:2026-10-14 | State:LOCAL_IMPLEMENTATION_ACCEPTED | Executor/self-review;independent review NOT_RUN.
Director requests next task;art/models/assets/camera deferred. Primary3;related4/6;diagnostic7.
Authority:rulebook/MASTER/QTF07 existing approval/catalog contract,QTF13–14 current-source review.

| Field | Contract |
|---|---|
| goal/non_goals | Connect reviewed preparation/v2 to an explicit approval receipt and existing playable catalog;generate a non-approved receipt draft;no automatic approval/source save upgrade/provider/client/core/schema change |
| baseline/prerequisites | Dirty HEAD1ad22446d48c50b8b72a6d3af8de3c9d775134ea;313files snapshot tmp/qt-f15/entry.json;QTF14 accepted;existing Python3.13.12 venv |
| reads | Rulebook/handoff/backlog/Korean progress/guide,MASTER/prompt/work-order template/setup/README,QTF07 approval contract;actual review/prepare/plan/compile/catalog/client/memory/replay/save callers and tests |
| edits | NEW src/app/npc_dialogue_compile.py,tests/integration/test_npc_dialogue_compile.py,this order,docs/reviews/QT-F15_EXECUTION_2026-10-14.md;MODIFY README,BACKLOG,SESSION_HANDOFF,GAME_SYSTEM_SUMMARY_KO;owned tmp/qt-f15 only |
| forbidden | All other source/tests,CORE/engines/C#/wire/save/approval schemas,assets,keys/provider profile/dependencies/policy/history/old witnesses/archives/remote |
| public contract | draft_approval(working:Path,content:QuestContent,npc_id:str,plan:Path,preparation:Path,output:Path)->None;compile_preparation(same inputs,receipt:Path,output:Path)->QuestContent. CLI required working/catalog/SHA/plan/preparation/output,npc default harbor;--draft-approval excludes --receipt;otherwise receipt mandatory |
| draft | Existing six approval fields:artifact_id,current raw output_sha256,current brief_sha256,decision PENDING,approved_by empty,approved_utc empty. PENDING fails existing compiler;never invent director identity/time/decision |
| compilation | Existing explicit APPROVED receipt,matching raw output digest AND exact validated current brief digest;reuse compile_dialogue/decode_catalog,retain catalog/v1. Receipt exact six fields/UTC/nonempty approver/cap16KiB per existing contract;missing/unreadable→NPC_DIALOGUE_APPROVAL_UNAVAILABLE,invalid→NPC_DIALOGUE_APPROVAL_INVALID |
| algorithm/ownership | Fresh output precheck→review current preparation/plan→draft or bounded receipt validation/compile→repeat full review comparison including preparation raw digest→receipt byte recheck→exclusive atomic fresh publication. No input mutation,sidecar or approval creation during compile. Consistency is not signed approval authenticity |
| edge_policy | Missing extra duplicate fields,non-APPROVED,foreign IDs/hash/brief/invalidUTC/oversize reject. Changed source/plan propagate existing codes;changed preparation→NPC_DIALOGUE_INPUT_CHANGED or existing invalid;changed receipt→NPC_DIALOGUE_APPROVAL_CHANGED;occupied output/pending→GENERATION_TARGET_EXISTS. IO publication→NPC_DIALOGUE_COMPILE_INPUT,owned pending cleanup;process-control propagates |
| examples | Current candidate→PENDING draft,no game catalog. Same candidate+manual APPROVED matching receipt→existing catalog accepted by loader,new game only. Matching raw hash but wrong brief→INVALID/no file. wait before compile→STALE;existing saves never repinned |
| wiring/performance | Standalone CLI after QTF14 review;catalog consumed by existing ClientSession quest_content/npc_memory and durable replay. Constant4lines/2memories,receipt16KiB/preparation32KiB,existing bounded reads;subprocess timeout30s. No turn-time network/runtime job |
| verification | Draft/current compile/loader,explicit-only approval and brief binding,bad/missing/oversize receipts,stale/source/preparation/receipt races,pending/output preservation/IO cleanup;network-forbidden standalone draft+compile;real fresh memory game four intents/stages/reward1/retry/save/load/resume/replay;wrong catalog resume rejection/source preservation. Real QTF13 artifact gets only PENDING draft/API0. Shared/selective Ruff,affected format,mypy,both imports,affected review/compiler/client regression |
| acceptance/checkpoints | Local checks PASS,public fresh catalog/game path qualified using explicitly AUTOMATED_TEST_ONLY receipts;real provider artifact never approved by this task. CP05 not triggered:existing reviewed quest/memory/catalog contracts unchanged;CP06 held. CORE/full/native NOT_RUN,reused unchanged evidence;self-review only |
| stop/delivery | Preserve overlapping/unrelated changes;no agents/commit/push/admin/provider/new task. Sync3progress docs;brief Korean primary/related/status/results;actual editorial approval remains a director action |

Acceptance:[execution](../reviews/QT-F15_EXECUTION_2026-10-14.md);32new+62regression PASS,
static/import checks PASS;actual Gemini receipt PENDING/API0,no production catalog created.
