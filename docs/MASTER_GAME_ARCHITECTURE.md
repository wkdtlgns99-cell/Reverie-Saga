# MASTER GAME ARCHITECTURE — Reverie Saga

Purpose: canonical product requirements. Engineering constraints: [v2.6 prompt](ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md).
Format: structured English for all AI-facing material;only essential human-facing notices/decisions/actions in concise Korean. No parallel Korean technical translation;preserve Korean player/source data. Follow the prompt's **AI Documentation Format** rule.
Updated: 2026-10-02. Translation/compression preserves requirements; no implementation authorization.

## Current Project Overrides

- Workspace: `C:\Reverie Saga`. Reference: `C:\Quilltale`, read-only.
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
- Optional runtime LLM runs in new-game/world-generation, chapter transition, loading/preparation, or explicit large-content windows.
- Runtime output: structured data → schema/rule validation → accept/reject → cache/persist → ordinary gameplay data.
- Normal turns require neither LLM prose nor live image/3D/audio generation.

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
Optional natural-language input stays outside simulation and maps to the same command contract.

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

### 7.1 Optional Use

World packages, chapter quests, NPC backgrounds, dialogue bundles, event content in explicit windows only. No LLM per move/combat action.

### 7.2 Business Rule

Player supplies supported API key. No mandatory developer-paid central relay.
Provider/model/tier quotas are mutable, not fixed capacity promises. “1,500 turns/day” and “unlimited free play” are not guarantees.

### 7.3 Window UX

New game / chapter transition → generate or load → validate → save/cache → play.
Failure: bounded retry, defer, accepted cached fallback, or explicit error/status; never fake success.

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
Fixed: graphical HD-2D/2.5D turn RPG; deterministic truth; human-director/AI-production workflow; pre-generated 3D/audio/voice; SD1.5+LoRA+ADetailer; Windows standalone; no mandatory per-turn LLM.

## 15. Clarifications

- v1 text-TRPG supplies historical ideas/failure evidence, not v2 runtime architecture.
- Combat outcomes use animation/VFX/UI/dialogue presentation.
- Runtime loads/selects/combines approved assets; audio libraries are consistent with AI pre-generation.
- Human directs, prioritizes, specifies acceptance, reviews, playtests, approves.

## 16. Definition

A procedural HD-2D/2.5D graphical turn RPG directed by a human and produced through AI-generated, validated, approved, integrated code/content/2D/3D/animation/audio.
