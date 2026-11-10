# MASTER GAME ARCHITECTURE — Reverie Saga

Purpose: canonical product requirements. Engineering constraints: [v2.6 prompt](ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md).
Format: structured English for all AI-facing material;only essential human-facing notices/decisions/actions in concise Korean. No parallel Korean technical translation;preserve Korean player/source data. The director-authorized [Korean game progress companion](../GAME_SYSTEM_SUMMARY_KO.md) is a human-facing exception and follows the prompt's **Korean Game Progress Companion** rule. Follow the prompt's **AI Documentation Format** rule.
Updated: 2026-11-05 (director decisions in §0.4 and implementation authorization below). Requirements are not runtime-completion evidence.

## Current Project Overrides

- Director2026-11-05:[accepted Option C and execution order](PRODUCT_DIRECTION_2026-11-05.md) supersede conflicting mandatory-provider/live-dialogue and BYOK-only statements. Complete authored base game without additional AI payment;optional state-grounded free-form conversations. API payment/access design is HOLD. Finish transport publication,then data ownership review before graphical integration/expansion;existing qualification holds remain.

- Director implementation authorization2026-11-04 supersedes this session's earlier planning-only and branch-only restrictions:implement confirmed D01-D07 through actual playable behavior,verification and integration,then ordinary protected-main publication. Ask only blocking material product decisions one at a time;continue coding without repeated permission once answered. Historical review-only/no-coding statements below describe the earlier decision-recording stage,not a current prohibition. Individual new schemas/contracts must still be specified and verified before implementation. No gameplay completion is claimed by this authorization.
- Workspace: `C:\ReverieSaga`. Reference: `C:\Quilltale`, read-only.
- GPT-6.1 Sol owns architecture, all simple/complex coding, tests, diagnosis/repair, integration, and technical review. Astra: advice only when Sol is blocked; never mandatory. Earlier Sol/Luna split is superseded.
- Historical `ASTRA_...` filename preserves links, not model authority. Documents do not change the app model or launch agents.
- Use actual laptop (§11.0). Current Windows 11 is temporary development OS; prioritize portable core and defer OS-specific implementation to deployment. Windows desktop release remains a separate requirement.
- Chat: brief Korean results/decisions/next action. Detailed contracts: files. Design-only requests do not authorize production code.
- v1 reuse: individually reviewed names/lore/descriptions/visual concepts/quest premises only. No code, formulas, balance, test oracles, state/schema, embedded stats/damage/cost/timing/behavior, or old entity bindings.
- Curated reference: `docs/reference/QUILLTALE_CONTENT_CANDIDATES.json`; six entries, not runtime-imported. Preserve v1 originals.

## 0. Product Definition

### 0.1 Identity

| Aspect | Requirement |
|---|---|
| Genre | Procedural HD-2D / 2.5D graphical turn-based RPG |
| Release | Windows 11 standalone desktop; Steam-style distribution |
| Visuals | Low-poly/modular 3D assets with pixel/toon rendering |
| Camera | Free rotation/360° coverage where gameplay/presentation requires |
| Controls | Keyboard/gamepad/UI mapped to typed commands |
| World | Procedural generation, persistent change, autonomous NPCs, delayed causality |
| Truth | Deterministic simulation; LLM never decides authoritative outcomes |

Art references: Octopath Traveler (lighting/depth + pixel character); Threads of Time (dimensional pixels/camera); Dead Cells (3D assets/animation rendered as pixels); Baldur's Gate/Disco Elysium (field visuals separated from dialogue portraits).
These are aesthetic references, not claims about reproducing their implementations.

### 0.2 AI Game Factory

Human = director/planner/approver: direction, requirements, style, acceptance criteria, review, playtests, priorities.
AI/tools = production workforce: code, bulk data, 2D, 3D, animation, BGM/SFX/voice, QA/import/build.
Baseline workflow MUST NOT require the human to hand-code, draw pixels, model, keyframe, compose, or author bulk data.

Flow: brief/criteria → assigned production job → candidate → validation → approval → import → build verification.
Lifecycle: `PLANNED → GENERATED → VALIDATED → APPROVED → IMPORTED → BUILD_VERIFIED`; failures: `REJECTED / RETRY / NEEDS_REVIEW`.
Generation success alone is not completion.

### 0.3 Production vs Runtime AI

- Production AI generates and validates code/data/images/3D/animation/audio before shipping; suitable paid services are allowed.
- Runtime LLM supports optional live free-form NPC conversation (approved Option C,2026-11-05), plus optional new-game/world-generation, chapter transition, loading/preparation, or explicit large-content windows.
- Runtime output: structured data → schema/rule validation → accept/reject → cache/persist → ordinary gameplay data.
- Ordinary movement/combat turns require neither LLM prose nor live image/3D/audio generation. Optional free-form NPC conversation is a distinct live-generation interaction;state-aware scripted dialogue supports the complete base game.

### 0.4 Director Clarification — 2026-11-03

Source:direct director answers during the product/design/implementation alignment review.
Except for the superseding2026-11-05 Option C/payment decision,this clarification supersedes conflicting language in earlier design documents;it records intended product behavior,not completed implementation or a new coding order.

- Highest-priority experience:a world and NPC society that change autonomously,player intervention,and later encounters with the consequences. The director may stop and redirect development after inspecting results.
- Superseded2026-11-05:Option C requires a complete authored base game with state-aware scripted dialogue plus optional live free-form conversation reflecting each NPC's own memories and personality. Prepared lines alone do not complete the optional free-form capability;API absence must not block main-story completion. LLM speech cannot directly overwrite objective world facts,damage,rewards or authoritative state;accepted dialogue/context must remain traceable and replay must not call a live provider.
- On pressing Play,the player expects a world-wide baseline already established to some degree. Subsequent player actions change the world and guide its further expansion. A starting-room-only world does not meet this requirement. This does not require every distant entity or visual detail to be materialized/simulated at full resolution.
- RS-PLAN-001 D01 confirmed2026-11-04:the director selected option1,world-wide structure plus detailed starting area. Establish countries,major cities,roads and faction relationships before play;materialize local residents,buildings and incidents as areas become relevant,consistent with established facts. A distant trade city already exists on the map and can be affected by disrupted trade before the player visits. This settles the initial breadth/detail strategy;it does not require all distant residents or facilities to be generated at startup.
- RS-PLAN-001 D02 confirmed2026-11-04:the director selected option1 and clarified that the large-scale structure is prepared first;smaller-scale structures and details of the large-scale structure become concrete as play progresses. Later elaboration may establish small settlements,caves,ruins and local settings within the existing framework,consistent with established geography,history and committed events. Elaboration is distinct from an actual world-changing event;the framework may change through gameplay consequences rather than being silently rewritten during elaboration. These examples specify permitted scope,not mandatory content or population targets.
- RS-PLAN-001 D03 confirmed2026-11-04:the director chose a hybrid of coarse distant simulation and detailed nearby individual simulation. Ordinary residents follow recurring routines grounded in their stored data;without a relevant event,their daily activities remain broadly similar. Relevant events may change those routines. Distant regions retain autonomous aggregate developments;nearby regions resolve individual behavior in detail. Stored resident data and established consequences constrain both levels. This does not require stepping every distant resident through every action. Exact update cadence,detail-transition boundaries,event eligibility and any special treatment of important NPCs remain implementation/design contracts to settle,not inferred numeric rules.
- RS-PLAN-001 D04 confirmed2026-11-04:the director approved action/utterance duration plus slow idle time,excluding AI-response waiting. [Time flow](#24-time-flow--director-decision-2026-11-04) owns the rules and remaining implementation details.
- RS-PLAN-001 D05 confirmed2026-11-04:ESC explicit pause completely stops game time;inventory and map views retain the D04 one-tenth idle progression. See §2.4.
- RS-PLAN-001 D06 confirmed2026-11-04:the director chose explicit confirmation of supported gameplay actions proposed through conversation. [Conversation action confirmation](#25-conversation-action-confirmation--director-decision-2026-11-04) owns the flow and limits.
- RS-PLAN-001 D07 confirmed2026-11-04:submitted dialogue is speech actually delivered to the NPC;social response and memory do not require a second confirmation. [Speech consequences](#26-speech-consequences--director-decision-2026-11-04) owns the distinction from D06 action execution.
- RS-PLAY-001 world scale confirmed2026-11-04:6continents,6countries,12major cities,with clearly distinct regional characteristics. Generate and retain one development world for ongoing tests;do not regenerate AI setting text on every run. This supersedes earlier proposed numeric profiles.
- RS-PLAY-001 travel decision confirmed2026-11-04:direct walking is the default;special transport such as carriage or train uses time-summary journeys with interruptions. Neither world-map inspection nor selecting a destination is on-foot teleportation. Particular transport implementations and balance remain separate from this chosen interaction model.
- RS-PLAY-001I QI01 confirmed2026-11-05:when a time-summary journey encounters a problem,stop and let the player directly choose a supported response such as waiting or returning. Do not silently resolve the problem and continue. The existing walking-default/hybrid transport model remains binding;the bounded order owns precise event,time,persistence and interaction contracts.
- Director decision2026-11-08:either side can start turn-based combat. At least one member of the opposing side must notice the opening attack. Resolve that attack before starting turn-based play, whether the target deflects it, evades it or is hit. Merely seeing an opponent leaves ordinary play running. An unseen ambush can start combat automatically after the noticed attack resolves. Detection inputs and handling of an attack that remains unnoticed remain open. Prototype encounter setup is delegated to the implementer.
- Director decision2026-11-08:when a threat is out of sight but makes an audible noise, present the sound by itself. Do not add warning text or a threat notification for the sound. The presentation leaves recognition to the player.
- The director confirmed the opening initiative direction on 2026-11-08. When the opening attack has resolved and the onset condition is met, all nearby characters enter the initial turn order. A character's awareness of the opening attack is relevant to the onset condition and any ambush advantage. Nearby characters can enter the order without personally noticing the attack. Individual speed, readiness and any earned initiative advantage affect who acts first. Baldur's Gate 3 is a design reference. Reverie Saga will define its own initiative rules. [Implementation prerequisites](work_orders/RS-OWN-COMBAT_INITIATIVE.md)
- Director decision 2026-11-09: a nearby fight the player perceives switches the world to combat-driven time when the opening attack resolves and the onset condition is met. Nearby characters enter the initial order even when a locked door separates them from the fight. The door still constrains their movement. Unperceived or distant fights leave the player's time flow running normally. [Combat time and late entry](#24-time-flow--director-decision-2026-11-04)
- Director clarification: the opening order covers the area near either the attacker or the target at the opening resolution. Turn eligibility is spatial. A guard in that order fights when they discover someone they know is an outlaw or witness violence against an innocent civilian or otherwise unlawful violence under the laws they enforce. Use the guard's own recognition and observation. If the guard initiates an attack outside turn-based combat, the usual onset condition still applies. [Opening order and guard response](work_orders/RS-OWN-COMBAT_INITIATIVE.md)
- The director chose a bandit ambush to open Mulbeodeul's first authored world encounter. Resolve the opening attack before presenting the turn order. [First village encounter](work_orders/RS-OWN-COMBAT_WORLD_FIRST.md)
- For Mulbeodeul's first dungeon, the director chose a player-initiated attack. Seeing the orc leaves exploration active. The player can initiate combat with a nearby attack, and the turn order follows the committed hit. [First dungeon encounter](work_orders/RS-OWN-UNITY_DUNGEON_PLAY.md)
- The first dungeon equips a short sword with a normal slash and one pommel strike that can stagger the orc. The simulation commits damage and turns. Unity constrains animated bodies to their playable positions and depicts recoil on the committed hit. [Contact and starter skill](work_orders/RS-OWN-DUNGEON_CONTACT.md)
- The first dungeon lets players switch between the short sword, spear and hammer. A combat switch spends the player's turn. The equipment definition supplies the switch duration and the weapon's basic and one-use special attacks. Slime and guard variants are isolated experiments. [Loadout contract](work_orders/RS-OWN-DUNGEON_LOADOUT.md)
- RS-PLAY-001H QF01 answered2026-11-05:the director requires species,countries,regional groups and action consequences together,and delegates a suitable concrete design to the executor. The earlier country-only recommendation is not the selected scope. Keep ancestry,political membership and earned reputation distinct;implement observable reactions and persistence,not merely setting descriptions. The bounded social order owns initial content,balance,compatibility and verification;broader social simulation remains required beyond its actual acceptance.
- RS-PLAY-001 first incident confirmed2026-11-04:the director accepts the proposed supply-disruption case and delegates the better testing approach. Preserve a fixed reusable world and representative regression while exercising deterministic variants of supported incidents;do not require fresh AI content generation for each test. Detailed balance and implementation contracts belong to the bounded incident order.
- RS-PLAY-001G failure behavior confirmed2026-11-04:already delivered player speech and its elapsed time remain after an AI response error. Offer response-only retry or continuing without a reply;retry does not repeat the utterance or charge its speaking time again.
- RS-PLAY-001G runtime cadence confirmed2026-11-04:one explicit generation job per player send/retry,without preparation tools' artificial60-second interval. Latest director follow-up supplies three keys and requests ordered exhaustion fallback:only provider429advances key1→2→3,at most once each per job;all exhausted is explicit. Preserve preparation defaults,usage accounting and provider limits. No paid fallback or repeated background retry. Technical configuration/qualification:[completion order](work_orders/RS-PLAY-001G_UI_COMPLETION.md).
- Remaining local density,generation timing/loading budget,NPC dialogue latency/characterization,and detailed expansion/social rules remain unresolved beyond bounded implementation orders. Speech rates/limits in the Gorder are executor prototype tuning,not additional director answers. Current implementation and remaining work:[BACKLOG](../BACKLOG.md#current-delivery).
- The original2026-11-03alignment review is historical. Latest2026-11-04director instruction resumes PR verification/ordinary merge/main synchronization and remaining settled backlog implementation. PR35foundation is merged;Gcompletion remains separately qualified. Existing bounded acceptances and independent/native/device/release holds retain their scopes.

## 1. Game Vision

### 1.1 Procedural World

Each playthrough may vary world/continent/region structure, nations/factions, settlements/facilities, roads/routes, dungeons/hazards, NPC personality/relations/memory, economy, weather/environment, quests/events, history, and long-term butterfly effects.
Persist state and causal consequences; a random map alone is insufficient.

### 1.2 Macro-to-Micro Stack

`L0 Cosmology → L1 Continent → L2 Region → L3 Nation → L4 Settlement → L5 Facility`.
Influence is bidirectional. Example: drought → food loss → settlement prices → dissatisfaction → bandit/revolt risk → national tax/military change.
v1 counts are scale references, not v2 population targets.

### 1.3 Required Capabilities

Capabilities may share modules; one capability does not imply one engine file.

| Domain | Capabilities |
|---|---|
| Physics/environment | Object/material interaction; attack physics; distance/range; destruction/collapse; lighting/visibility; noise/stealth; ambient/body temperature; weather; oxygen/enclosed spaces; environmental hazards |
| Combat/survival | Turn combat; stamina/poise; status/injury; toxicology/disease; food/ration/spoilage; sleep/fatigue; equipment weight/encumbrance; harvesting/body-part consequences where enabled |
| NPC/social | Personality; emotion/stress; attitude; goals/intent; memory; faction/social relations; rumor propagation; trade/economy; autonomous off-screen action |
| Space/infrastructure | Hierarchical places; road/network graph; settlements/facilities; dungeons; routes; time/calendar; quest/event consequences |

NPC cognition references: 12-axis traits, 10-factor interpersonal attitude, 20-factor deep persona, BDI beliefs/desires/intentions, 5-level semantic memory, permanent high-priority anchors.
Preserve these capabilities through a new maintainable model; numbers do not mandate v1 classes or formulas.
Historical content scale: 57 cosmology / 120 continents / 304 regions; not fixed v2 counts.
Merge/split technical responsibilities according to product need and playtests; do not silently remove capabilities.

## 2. Runtime — Brain & Body

### 2.1 Authoritative Brain

Python Brain owns WorldState, turns/combat/world/NPC rules, events, persistence/migration, procedural generation, and validated content ingestion.
Flow: input → typed GameCommand → validation → deterministic simulation → delta/events → COMMIT → presentation/diff → client.
Pre-COMMIT presentation is non-authoritative.

### 2.2 Graphical Client

Sol compares clients (e.g. Unity/Godot/Unreal) and makes a provisional choice.
Required: HD-2D/3D-to-pixel, modular 3D, combat presentation, animation/VFX/UI, camera, keyboard/gamepad, dialogue portraits, BGM/SFX/gibberish, MIN-SPEC budgets.
Brain domain types MUST NOT depend on client SDK types.

### 2.3 Input

Keyboard/gamepad/UI → client mapping → typed GameCommand.
Examples: Attack, Skill, Guard, Item, Move, Interact, Talk, Inspect, Travel.
Raw free-form NPC conversation input stays outside authoritative rule execution. Accepted speech duration and elapsed idle time affect the world through the validated time-advancement boundary (§2.4);LLM prose does not directly mutate world state. Any supported gameplay action proposed through conversation must map to the same typed command/validation boundary;natural-language control of other gameplay is optional.

### 2.4 Time Flow — Director Decision 2026-11-04

RS-PLAN-001 D04;approved product behavior,not implemented runtime acceptance.

- Movement,interaction and speech advance game time by their in-world duration. Resolve each action or utterance turn with its own duration;turns need not have equal duration.
- For player speech,use the submitted utterance's character count to determine speaking duration. For NPC speech,use utterance length and speaking rate. A longer utterance takes more time at the same speaking rate. This is speaking time,not the player's real reading or typing time;no AI semantic classification of conversation importance is required to assign duration.
- While the player is idle,reading,thinking or composing input,game time advances at one tenth of real elapsed time:10 real seconds equal1 game second.
- ESC explicit pause stops game time completely. Merely opening the inventory or map does not pause the world:these views advance at the one-tenth idle rate. This decision does not settle background/unfocused-app behavior or combat-specific menu rules.
- Time spent waiting for an AI response is excluded from game-time advancement,including the slow-idle contribution. Provider latency must not consume world time.
- Count each interval once:normal action/speech duration and slow-idle progression must not both charge for the same interval. World/NPC activity and delayed consequences advance consistently with the resulting game time.
- Director decision 2026-11-09: during a player-perceived nearby turn-based fight, each completed combat action advances world time by its in-world duration. Ordinary continuous progression is suspended while the fight is active. Characters outside the encounter order use each step for ordinary activities or reactions such as fleeing. If they intervene, they receive combat turns from their entry onward. After the fight, ordinary time flow resumes from the time the world reached through combat. [Implementation prerequisites](work_orders/RS-OWN-COMBAT_WORLD_TIME.md)
- Illustrative arithmetic:NPC speech lasting10 game seconds,followed by20 real seconds of player thought,followed by player speech lasting3 game seconds,advances15 game seconds. An intervening AI-response wait adds zero. These speech durations illustrate accounting,not fixed dialogue costs.
- Still unresolved:exact character-count and speaking-rate rules,action durations,clock precision/rounding,streamed-response phase boundaries,other menu/background behavior,combat timing integration and implementation/persistence/replay contracts. Preserve deterministic authoritative execution;record accepted time inputs for replay rather than consulting the live wall clock during replay. No save-format or runtime change is authorized by this product decision alone.

### 2.5 Conversation Action Confirmation — Director Decision 2026-11-04

RS-PLAN-001 D06;approved product behavior,not implemented runtime acceptance.

- Free-form conversation may negotiate supported transactions,quest acceptance,item transfers or hiring. Discussion or an NPC's spoken agreement alone does not execute these actions.
- Once a concrete supported proposal exists,show an action summary alongside the dialogue:the actual payment/items,objective or destination and applicable conditions,with explicit execution,continued-negotiation and refusal choices. Prefer an inline dialogue choice over a separate popup;not every utterance requires a confirmation.
- Example only:an NPC agrees to guide the player to a mine entrance for100gold,excluding combat support. Show those terms and an explicit pay-and-hire choice before transferring money or creating the hire. Names,price and available mechanics are illustrative,not adopted content or balance.
- Only supported,validated game actions and conditions may be offered for execution. LLM prose cannot invent executable rewards,resources or mechanics. Explicit confirmation crosses the existing typed command/validation boundary.
- At execution,revalidate current resources,NPC availability and other applicable conditions. If circumstances have changed,explain why execution cannot proceed;do not claim a payment or accepted hire that did not occur. Successful execution commits the applicable state and persistence through the authoritative path.
- Reading or considering the action summary uses the D04 one-tenth idle progression;ESC pause and AI-response waiting retain their existing exceptions.
- Confirmation controls transaction/action execution,it does not erase words already spoken. D07 (§2.6) permits social response and memory from speech itself without an additional confirmation;exact social rules remain to be designed. Not confirming a proposed transaction is not retroactive withdrawal of speech.
- Exact supported action set,proposal lifecycle/expiry,formal promise semantics and implementation/storage/replay contracts require bounded implementation orders. No runtime or save-format change is authorized by this product decision alone.

### 2.6 Speech Consequences — Director Decision 2026-11-04

RS-PLAN-001 D07;approved product behavior,not implemented runtime acceptance.

- Submitting an utterance delivers it as player speech. No second confirmation is required before the addressed NPC can hear,react to or remember it,including insults,disclosed secrets,claims and informal promises.
- Responses depend on the NPC's personality,own knowledge,relationship/trust and context. A statement does not guarantee a fixed attitude penalty,belief change or rumor. Exact interpretation and social-effect rules require later contracts;LLM prose cannot directly overwrite authoritative state.
- Preserve the difference between an utterance received,a belief held and an objective world fact. Hearing the player accuse a mayor of theft does not establish that the theft actually occurred. Depending on context,the NPC may doubt,ask for evidence,believe or later relay the claim;these are illustrative possibilities,not mandatory outcomes.
- A later correction or claim that the remark was a joke is further speech,not deletion of what was heard. Interpretation must account for context,including quotation,hypotheticals,jokes and retractions;do not automatically treat each mentioned proposition as an assertion.
- An informal promise may create personal expectation or memory without accepting a formal quest. Actual payment,item transfer,hiring and formal quest acceptance retain D06 explicit action confirmation and authoritative validation. Declining an action proposal does not erase its preceding conversation.
- This decision does not settle NPC intentional deception,rumor transmission rules,memory retention,numeric social effects or formal obligation mechanics. It introduces no unrestricted natural-language action execution and no runtime/save-format change.

## 3. Determinism & Causality

### 3.1 SSOT

WorldState is authoritative. UI/animation visualize; LLM proposes content; asset AI creates files. None may overwrite gameplay truth.

### 3.2 Replay

Same seed + accepted content package + command trace MUST reproduce authoritative state.
Control RNG, turn index, ordering, clocks, content hash, schema version.
Persist/accept generated content before use; replay freezes that package and never calls live LLMs.

### 3.3 Delayed Causality

First-class delayed events support off-screen consequences.
Example: turn10 ignored bandits → turn20 disrupted trade → turn30 supply loss → turn40 prices/security change → turn60 faction response/collapse.
Do not simulate every world entity at full resolution every turn.

### 3.4 Simulation LOD

A=strict persistent state; B=bounded divergence for crowds/rumors/some encounters; C=recomputable visual/cache state.
Catch up off-screen changes when needed. Engineering guarantees follow prompt C-03/A11.

## 4. AI Production Factory

### 4.1 Orchestration

Jobs carry ID, brief, acceptance criteria, dependencies, AI/tool role, output path, validation, approval, provenance.
Separate modality/tool responsibilities; architecture/code ownership remains entirely Sol.

### 4.2 Code / Architecture

Sol: architecture → bounded order → all implementation/tests → repair/integration/review/verification.
Astra: focused unresolved-blocker advice. Self-check is not independent review; independent review, if used, is separate.
Use [SOL_CODING_WORK_ORDER](prompts/SOL_CODING_WORK_ORDER.md): baseline, paths, prerequisites, exact I/O/errors, independently derived examples, wiring, steps, commands, acceptance, stop conditions.
One responsibility per task; resolve design before implementation. Verify actual diff/live path/results before DONE. Revalidate Astra advice.
Context: root `SESSION_HANDOFF.md`; task/dependency authority: root `BACKLOG.md`.
Before runtime evidence exists, use concise manual records. Generated aggregation/report tooling starts Phase 1+.

### 4.3 Structured Content

Generate NPC/personality/dialogue/quest/item/faction/location/lore/encounter/world/procedural templates as typed JSON.
Brief → generation → schema → duplicate/rule validation → review → approved data. Free text alone is not production truth.

### 4.4 2D Images — FIXED

**SD 1.5 + LoRA + ADetailer** for consistent fantasy portraits/illustrations and suitable UI images.
Visual spec → prompt/tags → SD/project LoRA → ADetailer → technical checks → style/identity review → approval → import.
Track source spec/character ID, model/LoRA version, parameter reference, hash, resolution, approval, target entity.
Pre-generate and ship; no normal-play live image requirement.

### 4.5 3D Models

Pre-generate body bases/hair/armor/clothing/weapons/furniture/buildings/props/landmarks/rocks/trees with suitable paid AI/services.
Use replaceable provider adapters/standard import contracts.
Brief → generation/download → technical checks → retopo/optimization if needed → material/texture/rig checks → approval → engine import.
Check polygons, scale, pivots, normals, material count, texture size, skeleton, collision, format, license/provenance.
Free/CC0 libraries may supplement; AI pre-generation + review + import remains primary.

### 4.6 Animation

Define skeleton contract before clips. Candidates: Mixamo, AI motion, prebuilt/marketplace libraries, paid services.
Check skeleton mapping, root motion, loops, clip length, event timing, hand/weapon alignment, successful import.
Manual keyframing is not the baseline.

### 4.7 Audio

| Type | Production / playback |
|---|---|
| BGM | Pre-generated paid AI/service tracks; region/combat/event/mood/danger tags; runtime selection + crossfade |
| SFX | Pre-generated/service/library combat, weapons, footsteps, environment, magic, UI, creatures |
| Gibberish/short voice | Pre-generated phonemes/exclamations/chatter; character/personality/species tags; runtime selection, small pitch/tempo/EQ/reverb variations |

Short chatter references: Octopath/Zelda/Animal Crossing. Full-sentence live TTS is not the default.
Ship an approved audio library; do not generate every spoken line at runtime.

### 4.8 Artifact Manifest

Track `artifact_id / artifact_type / source_brief_id / source_spec_hash / provider/tool / model/version / input_dependencies / output_hash / license/provenance / validation_status / approval_status / import_target / importer_version / build_version`.
Every generated repository artifact needs traceable origin.

## 5. HD-2D / 3D-to-Pixel Rendering

### 5.1 Approach

Pre-generated 3D pool → modular assembly → runtime lighting → low-resolution target → point sampling → toon quantization → pixel outline.
Supports camera rotation, equipment/outfit swaps, changing light, procedural environments, and AI 3D assets.
Do not depend on hand-drawing all directional sprites.

### 5.2 Requirements

- Optimize sub-mesh/draw-call growth through selected-engine mesh combining, atlasing, batching, instancing; exact APIs are candidates.
- Upscale low-resolution targets with point/nearest sampling.
- Stabilize pixel grid to control movement crawl/jitter.
- Quantize shading (e.g. light/mid/shadow).
- Use suitable depth/normal/screen-space pixel outlines where appropriate.

### 5.3 Lighting / Depth

Candidate effects: point/torch/moon lighting, fog, depth of field, restrained bloom, volumetric/light shafts when affordable.
Pixel readability takes priority; validate effects against hardware budgets.

## 6. Character Visuals

### 6.1 Field Characters

Modular body/race proportions/hair/face details/upper-lower clothes/armor/cloak/weapon/accessories.
Map world/NPC visual tags to asset selection. Preserve equivalent `traits: list[str]` semantics for UI summaries, content rules, generation, and visuals; exact v2 classes are redesigned.

### 6.2 Dialogue Portraits

NPC visual profile → approved portrait ID → pre-generated SD1.5+LoRA+ADetailer image → dialogue UI.
Maintain each NPC's identity consistency; field models need not render all portrait detail.

## 7. Runtime Content & BYOK

### 7.1 Complete Base Game / Optional Conversation and Content

Approved2026-11-05 Option C:complete authored base campaign and state-aware scripted conversations without required API access;optional live free-form conversations grounded in each NPC's personality and memories. Optional world packages,chapter quests,NPC backgrounds and events use explicit generation windows. No LLM per move/combat action. Existing preparation tools do not establish live-conversation or complete-base-game acceptance. See [direction and sequencing](PRODUCT_DIRECTION_2026-11-05.md).

### 7.2 Business Rule

HOLD2026-11-05:commercial API payment/service access is deferred. Prior mandatory player-key/BYOK rule is superseded;neither direct provider billing nor a developer-funded relay is selected. Existing developer-key use is qualification only. Complete base gameplay must not require additional AI payment. Resolve Steam/provider requirements before shipping a payment design.
Provider/model/tier quotas are mutable, not fixed capacity promises. “1,500 turns/day” and “unlimited free play” are not guarantees.

### 7.3 Window UX

New game / chapter transition → generate or load → validate → save/cache → play.
For optional content windows:bounded retry,defer,accepted cached fallback,or explicit error/status;never fake success. Optional live-conversation provider/latency/failure UX requires its own design contract;the complete base game uses authored,state-aware dialogue. Optional AI failure must not falsely appear to be generated speech.

## 8. Memory & Retrieval

Authoritative: relationship facts, memories/events, personality, goals, trauma/stress, factions.
Derived: full-text index, embeddings, reranking, cached summaries.
Sol selects retrieval infrastructure; normal players must not install DB servers/Docker.

## 9. Persistence

Save CORE WorldState, delayed events, RNG/replay metadata, package IDs/hashes, accepted runtime data, schema/version metadata.
Keep production image/3D/audio binaries in build assets, not duplicated into ordinary saves.
Use versioned migration; prevent partial commits.

## 10. Standalone Packaging

### 10.1 Player UX

Steam/executable → client/runtime startup → game window.
No visible Python console, DB service, Docker, or manual server setup.
Packaging candidates: PyInstaller, Nuitka, embedded runtime, other justified Windows bundle.

### 10.2 Lifecycle

Separate Brain/client processes MUST handle startup, heartbeat, normal exit, Alt+F4, crashes, Task Manager kill, Steam forced termination. No orphan backend.

## 11. Performance

### 11.0 Actual Development Laptop

Lenovo LOQ-E 15.6 inch ARP10e; AMD Ryzen 7 7735HS; NVIDIA RTX 4050 Laptop GPU 6GB; RAM16GB DDR5; NVMe512GB.
Current Windows11: temporary development OS.
Development TARGET: tools/job private commit ≤12GB; local generation VRAM ≤4.5GB; regenerable cache ≤30GB.
Measure representative jobs with versions/peak RAM/VRAM/cache. Fit/performance remain UNVERIFIED.
Heavy jobs run sequentially. Do not assume simultaneous SD + large local LLM + graphics editor.
Validate SD1.5+LoRA+ADetailer before choosing batch size; reduce batch/unload/use external production when over budget.
Keep approved originals/provenance separate from evictable cache.

### 11.1 MIN-SPEC

Release direction: 4-core CPU / RAM8GB / iGPU.
Architecture sets numeric frame/turn/memory TARGETs; prototype measures them. Development limits do not replace release gates.
Production costs are separate from runtime costs. Loading pre-generated assets is not AI inference. Measure simulation separately from LLM latency.

## 12. Development Rules

### 12.1 Truth

Deterministic Brain owns truth; client cannot invent outcomes; generated data enters only after validation/acceptance; live LLM cannot directly mutate state.

### 12.2 Production Evidence

Every artifact/code/data task needs output path, provenance, validation, completion evidence, duplicate avoidance, and explicit human-approval scope.

### 12.3 Workflow

Director requirements → Sol architecture/orders → Sol implementation/tests → Sol repair/integration/review → Astra only for blockers.
Specialized content/asset tools retain separate modality responsibilities.

### 12.4 Scalable Production

Scale through templates/generators/jobs/importers/validators; do not require the human to craft all code/art/audio.
AI-facing documentation follows the prompt's **AI Documentation Format** rule.

## 13. Scope Gates / Order

| Gate | Required progression |
|---|---|
| 0 Architecture / skeleton | Deterministic turn, typed command, ownership, replay, client boundary, staged build/test governance; Phase0 scope is exactly the prompt's four items |
| 1 Core gameplay | Combat, movement/interactions, state/events, save/load, representative NPC/world systems |
| 2 Client prototype | Provisional engine, pixel look, camera, modular character/environment, performance; then final client selection |
| 3 Factory integration | Artifact manifest; content/image/3D/animation/audio import; validation/reporting |
| 4 Bulk production | Large approved asset/portrait/audio/voice/content libraries |
| 5 Polish/release | Optimization, balance, QA, packaging, Steam preparation |

Do not bulk-produce final assets before stable contracts/import gates.

## 14. Technology Authority

MASTER defines product outcomes; v2.6 prompt defines engineering invariants/decision freedom; Sol designs.
Client, IPC, persistence, retrieval, and packaging infrastructure may be replaced with justified alternatives.
Fixed: graphical HD-2D/2.5D turn RPG; deterministic truth; human-director/AI-production workflow; pre-generated 3D/audio/voice; SD1.5+LoRA+ADetailer; Windows standalone;no mandatory LLM per movement/combat turn;complete authored base game,optional memory/personality-grounded live NPC conversation and initial world baseline (§0.4 and approved2026-11-05 direction).

## 15. Clarifications

- v1 text-TRPG supplies historical ideas/failure evidence, not v2 runtime architecture.
- Combat outcomes use animation/VFX/UI/dialogue presentation.
- Runtime loads/selects/combines approved assets; audio libraries are consistent with AI pre-generation.
- Human directs, prioritizes, specifies acceptance, reviews, playtests, approves.

## 16. Definition

A procedural HD-2D/2.5D graphical turn RPG directed by a human and produced through AI-generated, validated, approved, integrated code/content/2D/3D/animation/audio.
