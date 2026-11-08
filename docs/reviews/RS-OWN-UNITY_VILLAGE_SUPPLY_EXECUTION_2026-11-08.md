# RS-OWN-UNITY-VILLAGE-SUPPLY — Walk to the Supply NPCs

2026-11-08. Primary 5 presentation with 2 gameplay, 3 data, 6 persistence and 7 integration. Current Windows workstation and local self-review. [Work order](../work_orders/RS-OWN-UNITY_VILLAGE_SUPPLY.md).

In **Reverie → 마을 걷기**, the market and workshop mark the existing merchant and courier. From exactly one cardinal tile away, E opens the resident's authored line and current terms. A distinct confirmation sends the existing typed supply action to the durable owner. Closing a conversation sends no turn. A committed step away closes it. Idle time refreshes the terms and token. The walking panel shows carried crates, gold and committed supply status. The separate supply panel retains its earlier interaction scope.

The village bridge checks the actor's committed position and current offer at confirmation. A token binds branch, revision, position, resident, action and displayed terms. A mismatched or canceled token does not mutate state. Duplicate request IDs return the original response without reapplying the command. The authoritative supply admission still checks the world and applies the one-second commit, inventory change and reward. Save pins and slot formats are unchanged.

## Verification

Pinned Unity 6000.3.25f1 compiled and ran the production window and pipe against a private SQLite file. The batch used the production E key handler and confirmation method, verified a remote E press sends no request, walked to each resident, and committed acceptance, two distinct collections and delivery at revisions 11, 16, 17 and 22. It verified zero remaining crates, one 5-gold reward, completion, and position/reward recovery at (6, 2) after reopening. Physical key input and live screen appearance were outside the batch measurement.

The registered pipe test covers cardinal reach, diagonal rejection, closing or walking away before confirmation, time-driven token refresh, duplicate collection, final delivery, reopen, observer agreement and replay. Its retained history contains exactly accept, collect, collect and deliver. The separate supply, read-only observer and current-world durability regressions passed as part of the 77-case local run. The PR records final protected CI and synchronization.
