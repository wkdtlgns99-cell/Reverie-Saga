# Reverie Saga — Work Classification 1–7

Purpose:locate project work in the final structure;not implementation authorization or completion evidence.
Authority:[MASTER](MASTER_GAME_ARCHITECTURE.md). Detail:[Korean guide](GAME_STRUCTURE_KO.md).
Current status:[BACKLOG](../BACKLOG.md),relevant sources/callers and execution receipts.
Read this compact file for location questions;open detailed references only for unresolved scope.

## Classify and Answer

1. Classify the actual responsibility,not filename,language or whether AI wrote it.
2. Select the primary category;add related categories only when directly involved.
3. Verify current status from relevant code/evidence;do not treat final targets as implemented.
4. Answer in Korean:primary number/name → concrete purpose → related numbers → actual status.
5. Label documentation,configuration and developer tooling as support for the relevant categories.
   These seven categories are not seven required source modules. Keep IDs/meanings aligned with the Korean guide.

## Category Map

| ID | Korean name | Scope |
|---|---|---|
| 1 | 외부 제작 | Prepare images/portraits/icons,3D characters/equipment/environments,animation,BGM/SFX/short voice,lore/story/character premises. Candidate → validation/approval → import/build check. “External” means before ordinary play,not necessarily a remote service. |
| 2 | 내부 계산 | Authoritative Python rules:movement/range/combat,materials/destruction,visibility/noise/weather,hazards/injury/disease/food/fatigue,clock/delayed events,economy/trade/factions,NPC cognition/off-screen actions,quest stages/rewards. Accepted formulas execute as code. VS Code only edits source. |
| 3 | 내부 데이터 | Structured NPC/monster/item/equipment/skill/status/material/place/faction/quest/event/dialogue definitions;fields,IDs,conditions,effects and asset bindings. Examples are not finalized schemas. Text proposals require supported mechanics and valid bindings. |
| 4 | 플레이 중 AI | Optional LLM world/NPC/dialogue/quest/event generation in new-game,chapter/loading/preparation windows. Context includes committed state,NPC personality/goals/relations/memories and retrieved records. Keyword/vector search/summaries supply derived context. Validate/accept/persist output before use. |
| 5 | 화면·연출 | Graphical input → game commands;approved asset assembly,HD-2D/pixel/toon rendering,lighting,camera,animation/VFX,UI/portraits/dialogue and audio playback. Unity is the prototype;final engine needs qualification. Present committed facts. |
| 6 | 저장 | Persist/restore world state,events,NPC memories,accepted content/packages;save/load/recovery/retry identity. Manage media/provenance and rebuildable search indexes separately. Large assets are not duplicated in each save. Standalone packaging hides backend/tool setup from players. |
| 7 | 전체 연결 | Explain/verify an end-to-end playable flow across1–6. Not another simulation engine,and not the default label for every unit test. Identify the participating categories. |

## Boundaries That Prevent Misclassification

| Work | Primary;related |
|---|---|
| Portrait/offline story or dialogue library production |1;3bindings,5display |
| Quest objective/reward or NPC behavioral calculation |2;3definitions,6persistence |
| Quest/NPC schema,fields,IDs or conditions |3;2execution |
| Gemini generation or memory retrieval context |4;3validation,6retention |
| Unity talk button,quest status or portrait display |5;2facts,3bindings |
| Durable save/load,uncertain recovery or exact retry |6;2state truth |
| Full AI-content → quest → client → save demonstration |7;list participating1–6 |
| API-key setup |Support for4;not a new gameplay capability |
| This guide/rule maintenance |Support across1–7;not gameplay implementation |

Authoritative visibility/noise effects are2;visual/audio expression is5. NPC factual memory/state
belongs to2+6;retrieval for generation is4. AI-assisted engine coding still belongs to2.
Normal turns need no live LLM or live image/model/audio generation. Per-conversation free-form AI
is not a fixed requirement. AI cannot invent damage,rewards or past facts;replay uses saved accepted
content without live calls. User directs/approves production. Optional runtime AI follows player-supplied
keys;provider/tier/quota and tool choices require their own qualification,not assumptions here.

## Example Flow

Harbor bandits:assets/lore(1) → entity/road/trade/quest definitions(3) → disrupted supply/prices/security(2)
→ context-based validated quest/dialogue candidates(4) → player combat/report/reward/relations(2)
→ graphical/audio presentation(5) → saved facts/content(6). The combined demonstration is7.

No dated implementation snapshot here:read current evidence. This map preserves the final vision;
it does not certify broad world/NPC/memory/retrieval/asset-factory systems as completed.
