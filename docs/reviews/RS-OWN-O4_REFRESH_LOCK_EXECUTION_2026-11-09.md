# RS-OWN-O4-REFRESH-LOCK — Verification

2026-11-09. Primary 6 persistence with 5 presentation and 7 integration. Current Windows workstation, Python 3.13.12, SQLite 3.50.4. Baseline `e216b551cb457a6d3d4143716b3aa2b76bea32d8`. Local self-review. [Work order](../work_orders/RS-OWN-O4_REFRESH_LOCK.md)

The SQLite reader captures bounded, ordered rows under one read transaction and releases it before Python decoding and validation. The shared read path retains SQLite integrity and foreign-key checks, strict state decoding, retained history and protocol validation. One observer result describes the captured committed revision. Lock contention remains possible during SQL capture.

The new test pauses the actual observer at its first checkpoint decode. On the baseline, delivering two collected crates through the registered owner returned `TurnAborted(SAVE_UNAVAILABLE)`. With the change, the command commits during the pause. The paused refresh returns revision 3 with two crates, and the next refresh returns revision 4 with a completed quest and zero crates. Resubmitting the exact command returns the same outcome with identical file bytes. The file inventory is preserved. [Integration test](../../tests/integration/test_world_observer.py)

Five warmed `read_world` calls per fixture used the same SQLite bytes before and after. The fixtures were generated through registered one-second world waits. The lock proxy measures `_read` on the baseline and `_capture_rows` including transaction release on the candidate. Total storage validation measures `_read_file` and excludes catalog load, projection, process startup and Unity rendering. One separate `tracemalloc` run at 300 commands measured peak Python allocation during `read_world`.

| Committed waits | File bytes | Lock proxy median before → after, ms | Validation median before → after, ms |
|---:|---:|---:|---:|
| 0 | 73,728 | 43.89 → 1.04 | 47.04 → 44.13 |
| 100 | 253,952 | 124.16 → 1.41 | 127.81 → 96.54 |
| 300 | 614,400 | 194.24 → 2.08 | 199.51 → 186.17 |

At 300 commands the lock proxy decreased 98.9% and peak Python allocation rose from 2,345,306 to 2,837,250 bytes (21.0%). All thresholds in the work order passed. The fixtures returned the expected revisions and preserved their bytes and directory inventory. Large-save RSS and field collision frequency remain unmeasured.

The observer, village, supply bridge, save slots, durable turn, SQLite recovery and header checks, durable replay and rulebook suite passed 117 tests in 134.01 s. The final observer and rulebook rerun passed 18 in 8.54 s. Both Ruff profiles, observer test formatting, strict mypy (372 source files), four import contracts and `pip check` passed. The initial static invocation exposed a test import through an implicit re-export and an omitted source path for the import-linter command. The test now imports the decoder directly and the dependency checks passed with `PYTHONPATH=src`. The PR records protected CI and synchronization.
