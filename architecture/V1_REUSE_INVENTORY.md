# v1 Content Reuse Inventory

Date: 2026-10-02 | Owner: GPT-6.1 Sol
Format: prompt **AI Documentation Format**. Current director restriction supersedes earlier broad migration proposals.

## Policy

Reuse individually reviewed descriptive content only. Author new architecture/engines/formulas/balance/schema/tests from v2 requirements.
`C:\Quilltale` stays read-only; rejection never means deleting originals.

| Material | Treatment |
|---|---|
| Names/lore/place descriptions/appearance/quest premises | Curate/edit individual fields |
| Python/classes/wiring/state/formulas/physics/combat/economy/NPC calculations | No porting |
| Test code/fixtures/oracles | Historical failure evidence only |
| Embedded stats/DC/coefficients/cost/time/conditions/rewards/behavior | Strip |
| Old nation/region/NPC/item IDs/types/schema bindings | Strip |
| Unreviewed templates/DB/saves/cache/secrets | No bulk copy |
| Map/icon/audio settings | Not adopted in this selection |

## Six Curated Candidates

File: `docs/reference/QUILLTALE_CONTENT_CANDIDATES.json`.
State: CURATED_REFERENCE; runtime_imported=false.
Four source files, selected narrative fields only; no source JSON wholesale or runtime/importer connection.
Korean names below are source/content data, not AI instructions.

| Source name | Retained concept | Removed |
|---|---|---|
| 소금눈물 포구 | Misty hidden harbor; wary residents | Nation/region IDs, population/security/defense |
| 빈뿌리 쉼터 | Rope-bridge canopy village | Parent links, operation stats |
| 타는 모래 오아시스 | Caravan rest; water conflict | Absolute world claim, trade/survival values |
| 달빛 나그네 주점 | Travel/rest/rumor setting | Facility type, construction/light/noise/durability/upkeep/service logic |
| 달빛 아래 피는 약초 | Herbalist requests a night flower | NPC/stages/branches/deadline/reward/failure effects |
| 동판 비늘의 벼락 메기 | Copper scales/brass tail silhouette | Grounding/immunity/weakness/DC/AI/combat/drop |

Selection: concise/readable, visually distinct, independent of formulas, adaptable to new world.
Editorial judgment, not measured literary/game quality; reject later if unsuitable.
Per-entry `source_path/source_entry_id/source_fields` + source SHA-256 preserve origin. Source entry IDs are provenance, not new runtime bindings.

## Inspection Evidence / Exclusions

Source HEAD: `9f2ec20a7a06fedf01dd141b740bf4da8c3fc3ec`.
Pre-existing tracked changes: `D ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.1_LEAN_EN.md`, `M MASTER_GAME_ARCHITECTURE.md`. No source writes.

| Evidence | Finding / limitation |
|---|---|
| Templates | 23 JSON, 5,661,063bytes; syntax parses; semantic/schema/ID/ref quality UNVERIFIED |
| Array counts | Cosmology57, continents120, regions304, nations134, settlements215, facilities14, monsters82, companions67, skills69, quests15, recipes8 |
| Embedded mechanics | Monster immunity/weakness/behavior; facility noise/durability/upkeep; recipe conditions/cost |
| Code | dice global random; ration list(set), direct mutation/exceptions; rumor uuid4; no formulas adopted |
| Tests | `tests/test_p0_p2_fixes.py::test_invalid_action_zero_mutation_guaranteed` illustrates failure class; no copied inputs/expected values |
| README | Historical689passed; pytest NOT_RUN here |
| Saved audit | 71world modules/606methods=498live+82test-only+26never; earlier prompt80/692 differs; no rerun audit |
| Audio | BGM7+SFX13=20references; actual files0; no reusable audio imported |
| Visual files | Map JPG/icon/CSS exist; not copied; usage rights/provenance checked before actual import |
| Legacy | Only.gitkeep; no assumed save fixtures |

Read: README/audit/handoff excerpts/requirements/file inventory/representative templates/source/tests.
Executed inspection: ConvertFrom-Json23, bytes, Test-Path20 audio paths, source HEAD/status, four source SHA-256 checks.
Candidate checks: six unique IDs, narrative whitelist, source entry/name/fields/hash. No game validator/runtime introduced.
pytest/coverage/replay/v2 importer/integration/final product approval: NOT_RUN.

## Integration Order

Task authority: [BACKLOG](../BACKLOG.md).
BLOCK1 complete → BLOCK2–9 new contracts → review/preflight → authorized four-item Phase0 → suitable importer/new schema → assign new IDs/effects/numbers → playtest small segment.
Use descriptions only; expand selection when needed. No wholesale corpus/code/formula/test migration.
