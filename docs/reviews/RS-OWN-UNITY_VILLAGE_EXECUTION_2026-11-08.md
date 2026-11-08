# RS-OWN-UNITY-VILLAGE — Current-World Walking Verification

2026-11-08. Primary 5 presentation with 2 simulation, 3 data, 6 persistence and 7 integration. Current Windows workstation and local self-review. [Work order](../work_orders/RS-OWN-UNITY_VILLAGE.md).

## Player behavior and ownership

The editor panel **Reverie → 마을 걷기** displays a bounded district of 물버들, including the entrance, market, housing, administration and workshop. WASD and arrows request one cardinal tile. Holding a direction repeats. Movement interpolates between committed positions. Walls and edges leave the actor and clock in place. ESC pauses the panel. Ten focused idle seconds advance one game second and a committed walking step takes one game second. A connection owns the current working world until the panel closes.

Python registers the local position and step under separate versioned pins. The ordinary turn pipeline owns admission, the single position update, time and deterministic replay. The Unity editor owns the key mapping, repeat cadence and visual interpolation. The server sends map and landmark data with the committed position. Future movement changes can edit those responsibilities independently.

On first opening an older current world, the existing file is fully validated and retained. Its committed state becomes a new starting checkpoint at the same game tick and revision on a different branch. The position defaults to the entrance. Existing historical receipts and replay remain with the original. The active working pointer changes after validation. Old slots can be loaded as private upgraded copies, and the ordinary slot export retains the previous version. The Python world and supply/read-only Unity panels can reopen upgraded progress through their registered paths.

## Current-host Unity

Pinned Unity 6000.3.25f1 compiled the production editor window and ran a temporary batch entry on an isolated SQLite fixture. The probe passed actual Unity key events into the production input handler and used the normal framed Python process and response handling. It checked that the wall left tick 0 unchanged, a direction press committed the first tile, a held key repeated to the next tile, and a committed change set the animation interval. ESC suppressed an injected idle interval. Ten idle seconds after resume advanced one game second. Closing and reopening restored tile (3, 7) at tick and revision 3. The temporary editor entry and logs stay outside the tracked change.

The batch drove keyboard events and timing programmatically. Physical keyboard input, interactive rendering, a Windows player build and other devices were outside this qualification.

## Python and publication

The real pipe tests check bounds, cardinal stepping, exact duplicate replies, pause-supporting idle submission, restart, owner exclusion, road rejection, failed upgrade publication, legacy working and slot byte preservation, upgrade of in-progress supply cargo, and retained segment replay. The existing authored supply bridge and read-only observer complete against the upgraded world.

The related Python regression passed 122 tests in 142.73 s. The final Unity batch passed again, followed by 27 bridge, observer, supply and rulebook cases in 48.80 s. Both Ruff profiles, eight-file formatting, strict mypy across 370 source files, four import contracts, `pip check`, eight documentation links and whitespace passed. The PR records the exact final CI and main synchronization.
