# Mulbeodeul Dungeon Play — Verification

Primary 2 simulation, with 5 presentation, 6 persistence and 7 integration. Baseline `a1a584d64e24c0296274319115a9dcf8b8cb7103`. [Work order](../work_orders/RS-OWN-UNITY_DUNGEON_PLAY.md)

- The framed integration tests exercised the ordinary seeded world bridge. They checked gate admission, walls, live-orc occupancy, cardinal reach, exploration on sight, opening damage, action order, action time, victory and exit. They also checked old-save upgrade, recovery, duplicate requests and replay. The targeted world, combat, village, seed and engineering suites passed 29 tests. Ruff, Ruff quality, strict mypy and both import checks passed.
- Unity 6000.3.25f1 graphics batch used the production Unity window and Python bridge with a fresh seed. It entered the generated room, walked two interior steps, committed the opening strike, rendered the blade trail and hit sparks, reopened at the same turn, finished the fight and exited into the village. `DUNGEON_PLAY_NATIVE_PASS` is in `tmp/native-dungeon-play/editor.log`. The exploration and hit captures are in the same local directory. This run used programmatic input and self-review.

The playable area is one room with one orc. Exploration permits walking. In combat, the existing attack and hold actions are available. Protected exact-head CI is required for merge.
