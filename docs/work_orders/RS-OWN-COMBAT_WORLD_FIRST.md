# RS-OWN-COMBAT-WORLD-FIRST — First Durable Village Fight

READY for the first authored encounter. Baseline `465eb62c04c24bc560ec0fbfc331a7c16f9708d3`. The director confirmed both attack endpoints, spatial eligibility through obstacles, a world step per completed action, and a bandit ambush to open this encounter. [Initiative](RS-OWN-COMBAT_INITIATIVE.md) · [Time flow](RS-OWN-COMBAT_WORLD_TIME.md)

## Scope and ownership

Primary 2 simulation, with 3 data, 5 presentation, 6 persistence and 7 integration. Implement one authored skirmish in the existing district and durable knowledge world. Keep the isolated road trial available. At the south lane tile (9, 7), the bandit at (7, 7) lands the authored opening hit, which the target notices on impact. Ordinary movement and idle commands are gated while the attack is pending or combat is active. The village bridge submits the opening attack immediately after arrival or on reopening at that tile. The durable position and encounter record determine whether to submit it. The client presents the encounter after resolution.

Use the current village position and authored resident placements at the opening resolution. Keep resident coordinates shared with the village projection. Use Manhattan tile distance, inclusive radius 3 from either endpoint, once per unique living actor. Treat all residents with a physical placement as eligible. Order by the sum of authored integer speed, readiness and earned initiative modifiers, then stable entity ID. The radius and weights are tuning for this district. They do not establish global encounter balance.

The durable owner must commit the opening attack, resulting roster and tick together, then resolve one actor per admitted action. Each supported action takes one game second, including a resident holding position. While active, reject ordinary exploration and idle progression at registered admission. Use existing post-tick world rules. Allow active player input only for the current player turn and automatic action advancement only for the current NPC. Invalid or out-of-turn inputs preserve state. Persist the cursor, last actor/action and health. Enter or exit combat in the same transaction as the action that changes its phase.

## Boundaries

Initial actions are one attack or holding position. General combat movement, independent concurrent fights, late entry, local-law adjudication, general threat perception, sound and production balance are separate work. Publish only when the actual village caller can play the authored fight. The existing knowledge and village saves must stay readable and keep their world progress on migration.

## Acceptance

Verify an opening across multiple tiles with living characters near either endpoint, one in both regions, and one outside. Verify a wall does not change spatial eligibility. Demonstrate independent commits for an NPC action and a player action, no extra time or mutation for rejection and retry, ordinary idle blocked while active, and catch-up during committed actions. Close and reopen after an NPC action, compare state and replay the retained segment. Verify old and new saves, read-only views, and the normal Unity route. Use repository static checks and exact-head protected CI. No existing independent or native checkpoint is waived.
