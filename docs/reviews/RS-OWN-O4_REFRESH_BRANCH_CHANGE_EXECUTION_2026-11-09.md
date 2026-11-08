# RS-OWN-O4-REFRESH-BRANCH-CHANGE — Verification

2026-11-09. Primary 6 persistence with 5 presentation and 7 integration. Local self-review on Windows and Python 3.13.12. Baseline `8cbe15522f96f6006598d60d39eebdb6a038cd2a`. [Work order](../work_orders/RS-OWN-O4_REFRESH_BRANCH_CHANGE.md)

A real world worker loaded a slot twice while the real observer was paused after selecting the first loaded clone. The second load retired that clone. The baseline returned `SAVE_NOT_FOUND` from SQLite validation. The observer now rechecks source identity on validation errors as well as successful reads. The overlapping refresh reports `WORLD_VIEW_CHANGED` and a separate refresh sees the committed tick and revision 1. A subsequent real wait reaches tick 2. The observer leaves the current save bytes and directory inventory intact. [Integration regression](../../tests/integration/test_world_observer.py)

The successful path still checks the active reference once after validation, and a failed validation adds one reference check. The CLI response format, write path and one-refresh behavior stay compatible. This test covers retirement after source selection. Native Unity execution was outside this verification.

The observer, supply bridge, world client, village, save slots, reference and rulebook suite passed 89 tests in 67.85 s. Both Ruff profiles, changed-file formatting, strict mypy across 372 files, all four import contracts, `pip check` and staged whitespace passed. The PR records full protected regression and main synchronization.
