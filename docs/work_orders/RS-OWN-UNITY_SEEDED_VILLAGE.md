# RS-OWN-UNITY-SEEDED-VILLAGE — Place World Art from a Seed

READY. Baseline `71027a33b757b6a2fdc450dc901dcf3c608064b1`. Primary 5 presentation, with 1 asset intake, 3 world data and 7 integration. Scope is Mulbeodeul's existing walkable district, one small dungeon room and one orc placement.

The Unity seed menu accepts exactly 64 lowercase hexadecimal digits or generates a seed. The Python village process generates the existing world catalog for that seed, validates the template social and transport rules against it and opens a separate working save. Reopening that seed resumes its working state. The default authored world remains available.

Generate a versioned visual placement plan from world seed, settlement ID, regional terrain and the existing walkable rows. Preserve authoritative movement, terrain roles, positions and the authored ambush. Select building and road variants by coordinate, place one entrance on the southern border alongside a walkable tile, and generate one 5 × 5 stone room with an orc on a valid interior floor. Derive all placements without mutable RNG, elapsed time, revision or save state. Unity validates and projects the plan with the tracked CC0 assets. The dungeon is a preview accessible at the entrance.

Verify equal complete plans from two separate fresh saves with the same seed, a changed plan from another seed, a stable plan after moving and reopening, and role/entrance/orc invariants. Verify the actual Unity seeded window, world movement to the entrance, rendered town and room, and protected CI. Dungeon navigation and monster combat are separate scopes.
