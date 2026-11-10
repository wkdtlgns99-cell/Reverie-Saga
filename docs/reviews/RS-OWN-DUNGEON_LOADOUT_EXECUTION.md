# Dungeon Loadout — Verification

Primary 2 simulation with 3 data, 5 presentation, 6 persistence and 7 integration. Baseline `47910f61eab152db3e1808e47f4aff5a0a55f184`. [Work order](../work_orders/RS-OWN-DUNGEON_LOADOUT.md)

- The registered bridge tests checked one-second equipment changes in and out of combat, exactly one turn rotation, retry, wrong-turn and wrong-weapon rejection, and a spent skill across swapping and reopening. An actual prior-profile save retained its HP, tile, pending orc action and spent pommel, with the source file unchanged. The affected world and engineering suite passed 34 tests. Ruff, quality lint, strict mypy and both import checks passed.
- Unity 6000.3.25f1 graphics batch used the production Python bridge and 3D preview. The orc fixture switched to a spear in combat, took the orc's separate turn and landed the precision thrust. The faster slime acted first after the opening and lost its next action after a pommel strike. The hammer dealt two damage and staggered the guard, whose later attack dealt two damage. All three equipped models and skill effects rendered. `DUNGEON_LOADOUT_NATIVE_PASS`, the temporary probe and the three captures are under `tmp/native-dungeon-loadout`.
- In the visible editor, both experiment windows loaded from the Reverie menu and showed their committed stagger result. The normal seeded orc room showed a spear-equipped victory. The editor remained open with the isolated sessions.

The room has a fixed starter selection. Spear, hammer, slime and guard are prototype visuals, using existing rig animation and primitive shapes. The two experiment opponents have separate saves. Protected exact-head CI is required for merge.
