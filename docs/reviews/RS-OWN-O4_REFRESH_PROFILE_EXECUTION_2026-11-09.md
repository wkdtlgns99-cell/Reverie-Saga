# RS-OWN-O4-REFRESH-PROFILE — Verification

2026-11-09. Primary 6 persistence with 5 presentation and 7 integration. Current Windows workstation, Python 3.13.12, SQLite 3.50.4. Local self-review. Baseline `d49d207b86bc69e4517856c33b7ea028fcd5148c`. [Work order](../work_orders/RS-OWN-O4_REFRESH_PROFILE.md)

The live observer first tries the legacy knowledge pins and lazily tries the village pins on `UNSUPPORTED_RULESET`. The SQLite adapter decodes both against the rows captured by a single read transaction. It uses the full validation path for the selected profile. An unsupported save still fails, and other SQLite and decode errors propagate with their existing codes.

The integration test counted two real read-only connections when refreshing a village save on the baseline. It now counts one connection for both supported profiles and sees the same committed tick and revision. A third, valid world profile still returns `UNSUPPORTED_RULESET`. The cases verify file bytes and inventory preservation. [Observer regression](../../tests/integration/test_world_observer.py)

Five warmed in-process reads used the same 614,400-byte village save with 300 committed one-second waits. Each baseline refresh captured rows twice. Each final candidate refresh captured once. Observer wall time median went from 209.80 ms (206.32–210.98 ms) to 200.28 ms (197.73–210.59 ms). A candidate run alongside local regressions measured a 213.16 ms median and still captured once per refresh. These samples exclude process startup and Unity display latency.

The observer, village, supply bridge, SQLite recovery, save slots and rulebook selection passed 95 tests in 129.38 s. The final observer, SQLite header and rulebook rerun passed 26 tests in 10.80 s. Both Ruff profiles, changed application and test formatting, strict mypy (372 source files), all four import contracts and whitespace passed. The PR records protected full regression, retained replay and synchronization.
