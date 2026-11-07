# RS-PLAY-001I-PERF — Transport Barrier Cost Verification

2026-11-07. Primary 2 internal execution with 5 presentation, 6 persistence and 7 integration. The baseline was `59a673c0fc091a8046088d137c2a357e5f8a0763`. Local verification is self-reviewed. [Work order](../work_orders/RS-PLAY-001I-PERF_TRANSPORT_BARRIER_COST.md).

The Driver now selects the current phase's nodes from the validated schedule, builds the reducer's pre-barrier root on the first legal delta and keeps the component tuple when there are no writes. A reducer still sees the original pre-barrier root. The Driver runs every existing second, phase, bus batch and cascade wave under the same admission, event and publication rules. The optimization does not change schedule or rules pins.

## Matched measurements

The existing `tools/measure_world_transport.py` probe drove the same real carriage and longest sea route with Tk withdrawn and SQLite on this workstation. Each sample used a fresh owned save, a separate CPython 3.13.12 process and `PYTHONHASHSEED=0`. An initial multi-sample process ran the first sample but then failed during off-thread Tcl finalization. That attempt is excluded from the matched set. Running each sample in its own process avoided the failure without changing the measuring code or game logic.

| Measurement | Baseline three runs (s) | Candidate three runs (s) | Median change |
| --- | --- | --- | --- |
| Full route | 23.8603, 23.9704, 27.7033 | 6.5452, 6.5920, 6.8093 | 23.9704 → 6.5920 (72.5% lower) |
| Simulation stage | 20.4545, 20.5480, 24.0860 | 3.1183, 3.1402, 3.2000 | 20.5480 → 3.1402 (84.7% lower) |

Every paired run had 35 commands and ended at tick 93851. For all 35 positions the saved CORE, protocol, fact and diff hashes matched. Each final checkpoint digest matched, as did all complete SQLite file bytes (`1162e33a9a70280324b8d670e419babec532f010becbe91d4aad698f00363284`). The candidate replayed an existing baseline save with zero mismatches, and the source bytes stayed unchanged. Raw local measurements are under `tmp/rs-play-001i-perf-20261107/`.

The earlier visible-window 39.539 s run remains a separate measurement against the 30 s target. This change establishes the matched hidden-window improvement on this workstation. Visible-window qualification and other-device performance remain open.

## Regression and delivery

The retained six-profile witness matched the old saves, expected hashes and pins. Ruff (both configurations), scoped formatting, strict mypy across 360 source files, four import contracts and `pip check` passed. The first local full attempt showed 13 failures at the loopback HTTP fixture block and was stopped. A representative case timed out at `socket.accept` in the restricted environment and passed on the ordinary host in 0.30 s. The full run there passed 4,052 tests in 1,174.58 s, using process-scoped Git safe-directory settings. The delivery PR records final GitHub CI and main synchronization.
