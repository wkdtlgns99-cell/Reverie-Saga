# RS-SLOT-BACKUP-CLOSE — Close Both SQLite Backup Connections

**READY 2026-11-09.** Clean baseline `958a032ef89bd6251dc37b078190263c4add481c`. Primary 6 persistence with 7 integration. Local self-review. [Slot ownership and load contract](RS-P1-CORE_05_DURABILITY_SAVE.md) and [SQLite boundary repairs](RS-REVIEW-CP01_REPAIR.md).

In `_backup_file_reserved`, manage source and destination connections with independent close guarantees. If opening the destination fails, close the source. If the backup or either close raises, still attempt to close all acquired handles. Let ordinary errors reach the existing slot caller and classification, and do not publish or validate the destination after a failed backup or close. Keep the live owner, prior generations, immutable save profile and exclusive file ownership rules. No new save contract or gameplay behavior.

Read `adapters/sqlite_store.py`, `adapters/save_slots.py`, `app/durable.py` and the slot/recovery tests. Edit only the SQLite adapter, slot integration tests, root progress trio, this order and its matching receipt under `C:/Reverie Saga`. Use the installed Windows Python 3.13 environment and isolated SQLite files. Native Unity, independent checkpoints and release remain outside scope.

Exercise the real slot loader and SQLite backup while injecting an exception after the source connection closes. Observe that the destination is also closed, the failed load leaves the old attachment active, the owned clone is cleaned, and the same slot can be loaded after the fault is removed. Keep the existing backup-connect, export, replay and durability cases passing. Run standard lint, typing, formatting, import and related tests. Publish through an ordinary protected PR after both full runs and synchronize main.
