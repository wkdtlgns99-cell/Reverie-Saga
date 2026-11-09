# RS-OWN-COMBAT-WORLD-TIME — Advance the World During Combat

**DRAFT for runtime.** Primary 2 simulation, with 6 persistence and 7 integration verification. On 2026-11-09 the director confirmed the time flow, participation and per-action cadence. [Product authority](../MASTER_GAME_ARCHITECTURE.md#24-time-flow--director-decision-2026-11-04)

## Boundaries

- Build on the production [opening resolution](RS-OWN-COMBAT_RESOLUTION_ONSET.md) and [initial roster](RS-OWN-COMBAT_INITIATIVE.md). The player may observe a fight involving other characters. A distant or unperceived encounter does not switch the player's clock mode.
- Resolve each combat action before advancing world activity for its recorded logical duration. An attack and the next participant's action have separate boundaries. An input wait or rejected action does not create a step. Charge the opening attack's duration once across the transition. The durable world owner must gate ordinary idle advancement and use the registered world time and catch-up path. Combat order, elapsed time and resulting world activity must publish together. Retries and replay must reproduce the same tick and order.
- Outside the order, residents progress through world activity and reactions. Establish which committed intervention enters a resident into the encounter, when they get their first turn, and how they stop receiving ordinary activity for the same interval. Resolve insertion and ties deterministically. Ordinary time resumes at the advanced tick when the encounter ends.

## Readiness

- First establish a production encounter in the durable world owner, with authoritative positions and perceived opening resolution, an initial order and independently resolved participant actions. The current village bridge runs road combat in an isolated trial session. Its attack and retaliation are bundled in one command, and its isolation test requires the village tick, revision and save bytes to remain unchanged.
- Then bind admitted combat actions to recorded durations and the existing world catch-up path in the same transaction. Specify duration bounds, zero-time actions, clock-mode persistence and the handoff at the opening attack. The timed world already commits elapsed time through `WorldTime`, and world catch-up consumes the new tick at `POST_TICK`. Commit the final combat action's elapsed time together with encounter exit.
- Specify the authoritative intervention event and entry/exit contracts. Define when the resident's ordinary activity ends and the first turn becomes available, including simultaneous entries at one action boundary.

## Acceptance

Verify the registered path from opening resolution to exit, including observation of an NPC fight and an unrelated distant or unperceived fight. Wait for player input during combat and verify zero idle advancement. Resolve a scheduled combat step and verify one time advance and observable activity for a nonparticipant. Include a nearby character behind a locked door in the initial order and keep movement validation in effect. Use an intervening resident to verify entry happens once, the first turn is awarded at the documented position, and the same resident has no overlapping ordinary and combat action. After restart, retry, and replay, assert identical committed time, participant order and world activity. On exit verify ordinary time picks up from the committed combat tick.

An acceptance fixture can start combat at tick 100 after the opening attack has already been charged. A bandit action with a recorded duration of 2 advances the world to tick 102 and lets an outside resident react before the next participant acts. A move with a recorded duration of 1 then advances to tick 103. Input wait, replay of a submitted command through retry, and rejected input leave the committed tick unchanged. These durations illustrate the accounting, while action balance belongs to the production action contracts.
