# RS-OWN-COMBAT-RESOLUTION-ONSET — Opening Attack Verification

2026-11-08. Primary 2 simulation with 7 integration verification. Current Windows workstation and local self-review. [Work order](../work_orders/RS-OWN-COMBAT_RESOLUTION_ONSET.md).

The director clarified that turn-based combat starts after the noticed opening attack finishes. Deflecting, evading and taking a hit all count as a completed attack. The predicate now takes resolution, rather than initiation, and the count of opposing members who noticed the same attack. A completed attack with zero observers and an attack still in progress with an observer both leave the transition closed. The predicate needs no damage input.

The isolated road trial invokes the predicate from the committed `AttackResolved` fact and uses its existing retaliation to prove notice. A real attack response includes the resolved health change before the engaged phase is projected. The trial does not have a deflection or evasion action. Those outcomes are covered by the resolution contract, with production mechanics still pending. Existing action rules, save pins and presentation remain intact.

The related Python regression passed 328 tests in 27.96 s, including strict input checks, the pending/complete truth table, encounter golden replay and the real village pipe. Pinned Unity 6000.3.25f1 batch passed with the registered client and isolated fixture. It verified exploration before the first attack, the engaged phase with resolved damage, victory and byte-identical village state on return. The PR records both protected CI results and main synchronization.
