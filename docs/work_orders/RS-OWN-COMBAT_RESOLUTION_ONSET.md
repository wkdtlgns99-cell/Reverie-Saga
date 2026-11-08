# RS-OWN-COMBAT-RESOLUTION-ONSET — Resolve the Opening Attack Before Turn-Based Combat

READY 2026-11-08. Baseline `27c2cc851d2a1f49cf4bef0989b61ae85d90a624`. The director clarified that the opening attack finishes before turn-based play starts, including deflection, evasion and a hit. Primary 2 simulation with 7 integration verification. Local self-review. [Prior onset order](RS-OWN-COMBAT_ONSET.md).

Require a committed resolution of the same attack that at least one opposing member noticed. An observed attack still in progress does not start turn-based combat. A completed attack qualifies regardless of damage. The caller supplies resolution and notice evidence. The isolated road trial already receives a committed `AttackResolved` fact and uses its actual retaliation as proof of notice. Preserve that adapter and the public trial response. This order changes neither attack mechanics, armor, dodge, projectile behavior, perception, sound playback, save profile nor production encounter entry.

Edit the current predicate, its actual trial caller and focused tests, plus MASTER, the root progress trio and this order and receipt. Reuse the existing trial and registered replay. Verify pending and completed attacks with and without notice, invalid inputs, the committed hit and unchanged return, static checks, both protected CI runs, ordinary merge and clean main sync.
