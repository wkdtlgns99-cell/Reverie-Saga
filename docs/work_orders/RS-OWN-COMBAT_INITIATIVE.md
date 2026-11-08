# RS-OWN-COMBAT-INITIATIVE — Choose the First Turn

**DRAFT.** The director confirmed the direction on 2026-11-08. Primary 2 simulation, with 7 integration verification. [Product authority](../MASTER_GAME_ARCHITECTURE.md#04-director-clarification--2026-11-03)

Use the committed result of the noticed opening attack to establish the point at which turn-based play starts. Choose the first eligible participant using their speed and readiness and any earned ambush advantage. A deflected, evaded or landed opening strike can already satisfy the onset rule. Starting turn-based play must preserve that completed result. [Onset contract](RS-OWN-COMBAT_RESOLUTION_ONSET.md)

The isolated trial's `RoadCombatTrial.act` observes a committed `AttackResolved` with retaliation after `ClientSession.act`. The encounter engine resolves that retaliation inside `EncounterActions._attack`. A live initiative order needs a production encounter entry with eligible participants, an authoritative source of their speed and readiness, and a command path that can execute the selected participant's turn. Specify those contracts and the evidence that earns an ambush advantage before marking this order READY.

Resolve how surprise interacts with speed and readiness, how the opening action affects readiness, and how ties are broken. Then verify a faster participant acting first without surprise, the effect of an earned ambush advantage, deterministic ties, exclusion of defeated participants, and exact recovery and replay through the registered encounter. Test the transition after a deflection, an evasion and a hit to ensure the opening attack resolves once. This draft covers first-turn selection. Later-round scheduling requires its own contract.
