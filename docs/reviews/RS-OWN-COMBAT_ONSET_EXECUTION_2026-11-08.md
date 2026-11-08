# RS-OWN-COMBAT-ONSET — Attack Recognition Verification

2026-11-08. Primary 2 simulation with 5 presentation and 7 integration verification. Current Windows workstation and local self-review. [Work order](../work_orders/RS-OWN-COMBAT_ONSET.md).

The rule takes an initiated-attack flag and the number of opposing members who recognized that attack. It requires both an initiated attack and at least one observer. A visible opponent and zero recognized attacks leave ordinary play running. An unseen threat's audible sound is a presentation cue with no warning text or notification. [Product decision](../MASTER_GAME_ARCHITECTURE.md#04-director-clarification--2026-11-03)

The current isolated road trial displays exploration at entry and while moving, opening the gate and standing near the enemy. A rejected out-of-range attack leaves that phase unchanged. A registered attack result with real enemy retaliation proves one opponent noticed it in this fixture and switches the trial to turn-based combat. The state is retained through victory and is reset on a fresh trial. Existing encounter resolution, save bytes and world clock remain intact. Production perception, audio playback and actual world encounter entry remain pending.

The affected Python regression passed 328 tests in 27.07 s, including the decision truth table, encounter pins and golden replay, and the live village pipe. Pinned Unity 6000.3.25f1 compiled and ran an isolated batch through the production window and pipe. It confirmed exploration after opening the gate and approaching the visible opponent, turn-based phase after retaliation, victory, and byte-identical village state on return. Physical controls and rendered appearance were outside the batch scope. The PR records exact protected CI and main synchronization.
