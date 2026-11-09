# Mulbeodeul Seeded Art — Verification

Primary 5 presentation, with 1 asset intake, 3 world data and 7 integration. Baseline `71027a33b757b6a2fdc450dc901dcf3c608064b1`. [Work order](../work_orders/RS-OWN-UNITY_SEEDED_VILLAGE.md)

- An explicit seed uses the existing generated world catalog and a separate working save. The versioned Python placement plan uses the committed world seed, regional terrain, settlement identity and authored walkable rows. Unity projects it into the existing preview. Kenney CC0 modules provide the gate, stone floor, walls and orc. [Asset sources](../../clients/unity/VILLAGE_ART_SOURCES.md)
- The framed integration test created two fresh saves from one seed and compared their complete canonical plans byte for byte. Another seed produced different village and dungeon plans. A step and reopen preserved the plan and the committed tick. The test also checked the gate approach, roads and the orc's floor placement. The affected Python suite passed 27 tests. Ruff, strict mypy and both import checks passed.
- Unity 6000.3.25f1 graphics batch opened the normal seeded village window on a fresh save and walked four tiles to the generated gate. It rendered the village and room, verified one orc in the preview scene and verified that inspecting the room did not submit time. Reopening retained tick 4 and the identical placement plan. Captures and log are under `tmp/native-seeded-village-final`.

The topology is the existing walkable district. Variants, gate location and room content are generated from the seed. The chamber is an inspection view. Dungeon movement and monster encounters remain separate work. The graphics check used programmatic input and self-review. Protected exact-head CI is required for merge.
