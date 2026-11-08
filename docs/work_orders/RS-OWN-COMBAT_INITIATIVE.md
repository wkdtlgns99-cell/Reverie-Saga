# RS-OWN-COMBAT-INITIATIVE — Establish the Opening Turn Order

**DRAFT.** The director confirmed the direction on 2026-11-08. Primary 2 simulation, with 7 integration verification. [Product authority](../MASTER_GAME_ARCHITECTURE.md#04-director-clarification--2026-11-03)

Use the committed result of the noticed opening attack to establish the point at which turn-based play starts. Include every nearby eligible character in the opening order, even if another character was the one who noticed the attack. Rank those participants using individual speed, readiness and earned initiative advantage. Starting turn-based play must preserve the completed opening attack result, including a deflection, evasion or hit. [Onset contract](RS-OWN-COMBAT_RESOLUTION_ONSET.md)

The current world owner stores player village position in `VillageRecord`. `VillageBridge` reads authored resident placements through `village_supply` for display and interaction, then opens a separate `RoadCombatTrial` attachment for the combat test. The trial's `ClientSession.act` submits player commands and `EncounterActions._attack` resolves retaliation in the same action. Those paths supply neither a production combat roster nor independent participant turns.

Before marking this order READY, define how authoritative positions select the encounter area and its participants at the committed opening resolution. Specify the speed and readiness inputs, how the opening attack affects readiness, the conditions and weight of earned initiative advantage, and deterministic tie-breaking. The production encounter owner must commit the opening order and execute the selected participant's turn. Later-round scheduling requires its own contract.

Verify a single noticed attack drawing in nearby characters who did and did not notice it, a distant character staying outside, and exclusion of defeated characters. Verify a faster participant acting first without surprise, earned initiative advantage changing the order, deterministic ties, and exact recovery and replay through the registered encounter. Cover deflection, evasion and hit transitions with one resolution each.
