# RS-SLOT-EXPORT-PROOF — Verification

2026-11-09. Primary 6 persistence with 7 integration. Local self-review on Windows and Python 3.13.12. Baseline `71a0765660e96f2a33a09758085564da96607a70`. [Work order](../work_orders/RS-SLOT-EXPORT-PROOF.md)

The real durable slot export fault case injects failure before the final file replacement and denies the follow-up hash read of the old slot. The baseline loses the original failure classification and exposes the second `PermissionError`. The adapter now logs the unavailable proof and returns `SAVE_EXPORT_UNCERTAIN` chained to the original replacement error. A failed follow-up destination diagnostic is also logged without overriding the result.

The fixture verifies unchanged working core, protocol, attachment, file bytes and old current slot bytes. Only the normal current and previous generations remain after cleanup. An explicit save with the fault removed writes revision 1. The existing ordinary pre-replacement and committed-uncertain cases still pass. [Slot integration](../../tests/integration/test_save_slots.py)

The slot, SQLite recovery, durable turn, client reconciliation, world client, village, durable replay and rulebook suite passed 136 tests in 130.31 s. The focused export fault matrix passed seven tests. Both Ruff profiles, the repository's scoped formatting, strict mypy across 372 files, all four import contracts, `pip check` and staged whitespace passed. No native Unity run was required. The PR records full protected regression and main synchronization.
