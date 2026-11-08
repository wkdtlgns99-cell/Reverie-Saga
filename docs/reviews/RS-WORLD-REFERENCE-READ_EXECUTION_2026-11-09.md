# RS-WORLD-REFERENCE-READ — Verification

2026-11-09. Primary 6 persistence with 5 presentation and 7 integration. Local self-review on Windows and Python 3.13.12. Baseline `2b8efaf93d0a50718585e5e738bbba0151396cac`. [Work order](../work_orders/RS-WORLD-REFERENCE-READ.md)

The active-reference reader now reads a bounded stream and rechecks the reference once if the selected target is missing. A changed reference reports `WORLD_VIEW_CHANGED`, while an unchanged reference to a missing file still reports `WORLD_ATTACHMENT_MISSING`. The existing base-path default and size, format and path checks remain. The normal path uses one reference read.

The new observer case pauses before initial target lookup while the registered world worker loads another slot and removes its former clone. The baseline reports `WORLD_ATTACHMENT_MISSING` in that case. The fix reports `WORLD_VIEW_CHANGED`, then the next explicit refresh reads the new branch and leaves the saved bytes and file inventory intact. The existing case after target resolution still passes. The 1,024-byte reference boundary, malformed and stable missing cases run in the reference unit suite. [Observer regression](../../tests/integration/test_world_observer.py)

The reference, observer, world client, village, supply bridge, slot and rulebook suite passed 93 tests in 70.11 s. Both Ruff profiles, changed-file formatting, strict mypy across 372 files, all four import contracts, `pip check` and staged whitespace passed. Native Unity execution was outside this verification. The PR records protected CI and main synchronization.
