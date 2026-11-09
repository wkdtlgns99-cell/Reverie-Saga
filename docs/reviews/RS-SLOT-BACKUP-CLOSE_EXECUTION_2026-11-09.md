# RS-SLOT-BACKUP-CLOSE — Verification

2026-11-09. Primary 6 persistence with 7 integration. Local self-review on Windows and Python 3.13.12. Baseline `958a032ef89bd6251dc37b078190263c4add481c`. [Work order](../work_orders/RS-SLOT-BACKUP-CLOSE.md)

The baseline slot loader leaked the destination connection when the source close raised after a real SQLite backup. The regression observed that the destination still accepted queries, and Windows refused to delete the owned staging file because the handle was open. The backup now manages both connections in nested close scopes. Both close paths are attempted, and the existing load error and owned cleanup apply.

With the fault injected, the real slot owner reports `SAVE_LOAD_FAILED` and the staging connection rejects queries as closed. Working core, protocol, token, working bytes and slot bytes agree with their pre-load values. No staged clone remains. With the fault removed, loading the same slot restores revision 0. [Slot integration](../../tests/integration/test_save_slots.py)

The slot, SQLite recovery and header, durable turn, client reconciliation, world client, village, durable replay and rulebook suite passed 142 tests in 132.11 s. The final close, connect and document rerun passed 15 tests. Both Ruff profiles, the repository's scoped formatting, strict mypy across 372 files, all four import contracts, `pip check` and staged whitespace passed. The initial type check caught the fault injector's overly narrow progress callback return annotation, which was corrected to match SQLite's typing. The PR records full protected regression and main synchronization.
