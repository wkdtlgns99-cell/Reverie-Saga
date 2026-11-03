# Product Alignment Review — 2026-11-03

Status:READ_ONLY_SOURCE_REVIEW + PROPOSED_SEQUENCE;self-review,not independent review.
Follow-up2026-11-03:director subsequently adopted the [clarification policy](../CLARIFICATION_POLICY.md)
and reserved RS-PLAN-001 as the first next-task action. The proposal below records the earlier review;
ENGINEERING_RULES/policy and BACKLOG own current rule/task state. Current publication request covers
these session documents;no runtime implementation is authorized.
Primary7design support;related1–6. Current director request:compare the whole design/runtime
against confirmed intent,explain missing/misaligned work and a completion-oriented sequence;
no implementation. Clarification-rule text below is a proposal,not an active governance edit.
Authority:[MASTER §0.4](../MASTER_GAME_ARCHITECTURE.md#04-director-clarification--2026-11-03).

## Baseline and limits

- Local HEAD3f84796;source baseline unchanged since the prior representative test selection.
- Entry dirty documents:MASTER,v2.6 prompt,both structure guides,BACKLOG,HANDOFF,Korean companion.
  Preserve that already-recorded director clarification. This delivery adds this review and updates
  only its three progress routes;no src/tests/content/client/config/policy/dependency change.
- Inspected actual command fields/mapping,quest rules/codecs,scenario bindings,local memory/query,
  supply/patrol logic,turn driver and graphical placeholder path;compared BLOCK04/05/06/09,
  MASTER,work-order template,current delivery and historical sequencing findings.
- Previous same-session selection:10PASS8.74s,including quest/real framed offline flow,
  partitioned off-screen supply,reward separation,reach-aid full quest,assistance replay,
  watch replay and SQLite backup. First attempt3PASS/7setupERROR from inaccessible default
  temp root;unchanged selection passed with workspace-owned basetemp. Evidence is reused,
  not a new run or whole-product qualification. No new runtime test required for this document work.
- No live provider call,new native Unity run,benchmark,full regression,external review or remote CI
  was performed here. Source inspection cannot establish future simulation scale or dialogue quality.

## Findings

Classification:MISMATCH=earlier design assumption conflicts with clarified intent;
MISSING=capability/design absent;BOUNDED=valid limited implementation,not a product defect;
UNVERIFIED=missing execution/quality evidence. Detailed requirements are not implied by labels.

| ID / area | Design and actual evidence | Assessment / necessary disposition |
|---|---|---|
| A01 / live NPC conversation,4;2/3/5/6 | BLOCK04 A8.3/BLOCK06 A14.4 restrict generation to windows/offline optional use. MASTER now supersedes this. [ClientAction](../../src/contracts/client.py) has a talk intent;[QuestTalkCommand](../../src/contracts/quest.py) has only npc_id;[client mapping](../../src/app/client_session.py) passes no user utterance. [QuestRules](../../src/engines/quest.py) selects offer/reminder/completion/gratitude and advances quest stages | MISMATCH + MISSING. Existing prepared dialogue is valid prototype behavior,not required free conversation. Need text input,conversation lifecycle,own-knowledge context,response acceptance/persistence,latency/error/cancel rules and validated gameplay-action proposals. Do not mutate old quest-talk semantics in place without an explicit compatibility contract |
| A02 / personality/social cognition,2/3;4/6 | MASTER retains traits/attitude/persona/BDI;BLOCK04 A8.1 explicitly defers detailed cognition calculations. Existing patrol uses heard quest phase,supply and occupancy through [npc_patrol](../../src/domain/npc_patrol.py) and watch rules | MISSING detailed design/runtime;BOUNDED current behavior. Need persistent individual personality,goals/relations and rule-defined updates that affect both choices and dialogue. Final cognition capabilities stay pending until actually covered;persona labels alone do not complete behavior |
| A03 / memory and knowledge,2/6;4 | [npc_memory](../../src/domain/npc_memory.py) capacity2/level1,accepted/completion_reported only;[npc_cycle](../../src/domain/npc_cycle.py) latest4own supply anchors;assistance has its own bounded causes. [query](../../src/app/npc_memory_query.py) filters these scoped facts | BOUNDED + MISSING general model. Need event participants/subjects,own witnessed/heard/believed evidence,priority/protected anchors,conversational continuity and lawful retirement. Latest4retention is valid for its current contract;not a general biography/forgetting policy |
| A04 / initial world,2/3/6 | MASTER has L0–L5 vision;[scenarios](../../src/app/scenarios.py) explicitly lists four embedded room layouts,not generated geography. [ClientSession](../../src/app/client_session.py) starts one selected layout with fixed seed | MISSING design/runtime. Need initial world-wide baseline,stable identity/seed/content pins,hierarchy,connections and consistent local detail. Coverage,density and generation/loading timing are director decisions;no assumption of zero-time generation or every distant actor materialized |
| A05 / travel and expansion,2/3/6 | Current moves remain within one3x3space;BLOCK05 A11 requires separately defined multi-leg/interruptible travel. No actual inter-location world generator/expansion path found in current runtime inventory | MISSING. Need route cost,time,arrival/interruption and changes outside player location;define refinement of existing geography versus creation of new geography. Already established facts cannot be silently rewritten during expansion |
| A06 / world causality,economy,factions,2/3/6 | Event queue/durable pending/replay foundations exist. [supply cycle](../../src/engines/npc_cycle.py) is one NPC's fixed4/10-second production/use loop,not road trade,prices,factions or regional propagation | BOUNDED + MISSING gameplay. Implement one actual cross-location cause chain with alternatives for intervention/neglect and independent expectations;then expand breadth. A narrated change without authoritative state is insufficient |
| A07 / quest and failure,2/3;4/6 | [QuestRules](../../src/engines/quest.py) implements one enemy objective,monotonic stages and one favor. Any talk at relevant stage accepts/reports | BOUNDED. General quest conditions/failure/deadlines/consequences/reward kinds missing. Free conversation needs explicit action/consent semantics:asking about a quest must not automatically mean accepting it. Exact new behavior awaits design |
| A08 / simulation scale,2;6/7 | BLOCK05 A11 defines exact off-screen semantics and proven no-op skip. [Driver._simulate](../../src/orchestration/turn.py) still iterates each game second/barrier. No representative large-world runtime established | BOUNDED reference implementation;UNVERIFIED scale. Retain as correctness reference. Measure actual proposed populations/travel lengths early;design scheduled/exact transitions and catch-up before broad content. No unsupported claim that Python/current loop cannot work or that universal per-second approximation is necessary |
| A09 / typed data and content,3;1/2/4/6 | Scenario/quest/catalog bindings are specialized;descriptive catalog has6adapted entries. Prior v1 inventory is not a working new-world catalog | BOUNDED + MISSING domain definitions. Define only fields/effects consumed by the next playable capability;world/NPC/item/faction/quest expansion needs new typed contracts. Do not import old mechanics or bulk-generate unsupported behavior |
| A10 / graphical input and presentation,5 | [PlayRoom](../../clients/unity/Assets/Reverie/Scripts/PlayRoom.cs) checks3x3bounds and uses primitives/fixed camera;recent leaf-mode native execution remains NOT_RUN | BOUNDED + UNVERIFIED. Required world navigation,NPC selection,free-text conversation and visible consequences must be ordinary graphical paths. HD-2D/camera/modularity/gamepad/audio remain later product work,not silently removed. Do not repeatedly ship unrelated Tk polish as evidence of these capabilities |
| A11 / persistence/replay,6;2/3/4 | Durable commit,slots,previous generations,branch restore and retry exist. Current version-isolated optional modes do not already store general world/persona/conversation schemas | Foundation ALIGNED;MISSING new domain integration. Persist new accepted dialogue/world/personality/memory/action consequences as each feature is built;replay uses accepted dialogue bytes/results,not regenerated text. General migration needs explicit new contracts;old saves retain truthful support limits |
| A12 / API independence and failure,4;5/6 | MASTER requires BYOK and independent simulation. Old optional-window complete cached fallback cannot establish complete required live dialogue | DESIGN TENSION. Keep deterministic simulation playable without a provider;do not claim identical free-conversation capability from cached lines. Director must settle unsupported/offline/key/quota/error experience and acceptable latency before production order. No automatic paid relay/new local-model requirement |
| A13 / assets,production,release,1/5/7 | AI-factory/art/audio/rig/import/build and standalone/min-spec remain planned or unqualified. Art/camera previously deferred by director;CP06/native/device holds remain | MISSING/UNVERIFIED,not newly discovered omission against a narrow completed task. Qualify a small representative asset/render/import path before bulk,then scale and release. Existing holds are not waived by this proposal |
| A14 / work progression,7support | [2026-10-16direction](../../BACKLOG.md#adopted-architecture-direction--2026-10-16) prioritizes an end-to-end village. Later work repeatedly adds factual comparisons/leaf flags/UI/performance. [Earlier audit](OPEN_WORK_AUDIT_2026-10-14.md) already identified tool completion preceding actual prose delivery | Completion/selection weakness. Individual scoped acceptance remains valid;it does not prove the core experience. Tie future bounded orders to a shared playable milestone and explicit director demonstration. No measured claim about total wasted hours or all support work being unnecessary |

## Proposed development sequence — not an executable work order

Each milestone contains small implementation orders,but closes only on the ordinary graphical
play path,its required save/restart/error/replay paths,and a concrete director-visible result.
Save/replay/UI are integrated within each milestone,not postponed to a final wiring project.
Preserve compatible runtime services;no blanket rewrite or old-save promise.

| Milestone | Deliverable / dependencies | Completion demonstration |
|---|---|---|
| M0 / resolve product-sensitive contracts,7support | Only blocking choices:initial world coverage/density/loading;expansion meaning;dialogue input/knowledge/lying/commitment/time rules;API/latency/failure UX. Author concrete proposals and examples;retain unresolved items as DRAFT | Director can compare specific player experiences and choose;no large new governance framework. No runtime completion claimed |
| M1 / initial world and travel,2/3/5/6 | Generate/persist accepted world baseline with stable places/connections;detail the starting area and traversable connected locations. Make initial broad map inspectable. Define/qualify travel duration and off-screen time. Exact population/geography await M0 | Start→inspect existing world→visit connected locations→save/restart with same identities/connections. Different seeds demonstrate declared variation. Bounded prototype world must not be presented as final scale |
| M2 / first complete NPC conversation,2/3/4/5/6 | Using M1world,provide distinct NPCs with persistent personality,own knowledge,relationships/goals and relevant memory;live free text→context retrieval→provider→validated/accepted recorded reply→UI. Supported action proposals cross typed rule boundaries. Use existing provider/storage where suitable,do not build another preparation-tool ladder | Converse freely with different NPCs;reference past interaction;encounter different knowledge/personality responses;restart and continue coherently. Ordinary play errors/cancel/retry/stale replies handled;accepted output replays without a live call. Director assesses characterization;actual defined live evaluation required before completion |
| M3 / one autonomous social/world consequence chain,2/3/4/5/6/7 | Extend M1/M2with actual scheduled goal-driven activity,one linked resource/route/settlement conflict,intervention and neglect consequences,knowledge transmission and an executable quest/action path. Proposed harbor trade disruption is an example,not an adopted balance/formula | Ignore problem→travel/time passes→world/resources/NPC choices change→return/free conversation reveals only what NPC knows. Intervention produces separately specified consequences. Save/restart and partitions retain truth;demonstrate before further polish |
| M4 / coherent expansion and breadth,2/3/4/6 | Add local detail/content consistently with established world facts;broaden economy/factions/rumors,NPC cognition/memory tiers,quest variety,combat/environment/survival. Introduce each through a new usable case;retain every MASTER capability on the remaining-work register | Explore/refine without contradicting prior maps,memory,travel or history;remote consequences reach new detail;compare multiple playthroughs. Capabilities remain partial until their own behavior/quality criteria pass |
| M5 / production visuals and repeatable assets,1/3/5/7 | Representative approved image/model/rig/animation/audio→actual import/render/build before bulk. Finalize engine/style/camera/control fit with director;then scale approved libraries | Ordinary gameplay with representative approved art,HD-2D/camera/portraits/audio/gamepad and actual performance measurements. Small feasibility samples may be done earlier if an actual dependency justifies them;no blanket delay of all graphics until M4 |
| M6 / balance,qualification,shipping,5/6/7 | Full regression/replay/crash/lifecycle/offline/device/min-spec/packaging/license and existing CP06requirements after integrated feature freeze | Standalone player launch and director UX acceptance;required independent feedback/dispositions and remaining release gates satisfied. Earlier test/build counts are not substitutes |

M3 is the first proposed acceptance of the core combined experience,not a claim that the whole RPG
or all personality/survival/economy requirements are complete. M1/M2must each be usable deliveries;
do not wait until M3to show the director what was built. Representative performance checks start
with M1/M2;M6is final qualification,not the first time performance is examined.

## Proposed prioritization practice

This is advice for the next plan,not an active rule change:

- Each bounded order names its parent playable milestone,remaining player-visible gap and concrete exit.
- Support work needs an actual current blocker,correctness requirement or measured budget failure of
  that milestone. Explain why the milestone cannot proceed without it;retain necessary repair/testing.
- After necessary repair returns the flow to its declared acceptance,resume the parent milestone.
  No arbitrary optimization percentage or test count becomes the default next objective.
- Developer experiment switches/legacy pins may remain where useful;give the director one clear
  supported demo entry instead of requiring a growing manual flag chain. Do not break old identities
  merely to simplify the demo;settle profile/save compatibility in a bounded future order.
- Show playable results at milestones and classify pending capabilities honestly. Production line
  acceptance may use standing scoped policies;new product semantics still need explicit decisions.

## Clarification-rule proposal — not applied

Existing ENGINEERING_RULES preflight already says to resolve conflicting inputs;failure handling
requires escalation of unresolved semantics. Missing distinction:when a question is necessary
and when reversible technical judgment should continue. Suggested insertion into Preflight:

> Before asking,inspect current instructions,canonical contracts,actual sources and prior answers.
> If materially different plausible interpretations would change player experience,product scope,
> public/save contracts,irreversible effects,or substantial rework,ask the director before dependent
> design/implementation;do not silently omit,downgrade or replace a requested capability.
> State the ambiguity,a recommended interpretation and its concrete effect;bundle related questions.
> Proceed autonomously with reversible local technical choices within settled contracts and report
> material assumptions. Reuse prior answers/delegation;do not ask again without new conflicting evidence.
> While awaiting a required answer,continue independent authorized work;do not execute the dependent
> branch or treat silence as approval.

Examples:live conversation versus prepared lines,initial-world scope,generation delay,and world
expansion semantics require product clarification. Local helper naming,settled codec reuse,
ordinary test selection and routine error diagnosis do not require new permission.
Do not create an every-turn question/checklist or use subjective confidence alone as the trigger.

## Delivery

Review document and three progress-route updates only. Verify UTF8,local links and diff scope.
No code,active rule change,implementation approval,new mandatory checkpoint,agent,provider call,
commit/push or automatic continuation. The proposed sequence is not READY until its actual
product-sensitive choices and source-specific contracts have been settled.
