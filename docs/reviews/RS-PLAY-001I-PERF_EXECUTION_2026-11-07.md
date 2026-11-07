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

The earlier visible-window 39.539 s run remains a separate historical result. The matched hidden-window comparison establishes the improvement under the same conditions. See the post-merge visible qualification below.

## Regression and delivery

The retained six-profile witness matched the old saves, expected hashes and pins. Ruff (both configurations), scoped formatting, strict mypy across 360 source files, four import contracts and `pip check` passed. The first local full attempt showed 13 failures at the loopback HTTP fixture block and was stopped. A representative case timed out at `socket.accept` in the restricted environment and passed on the ordinary host in 0.30 s. The full run there passed 4,052 tests in 1,174.58 s, using process-scoped Git safe-directory settings. The delivery PR records final GitHub CI and main synchronization.

## Visible-window qualification — 2026-11-08

[PR46](https://github.com/wkdtlgns99-cell/Reverie-Saga/pull/46) merged at `c6484d8`. Both final CI runs passed 4,052 full tests and 32 boundary tests. Local and remote main matched the merge commit and the tested and merged trees matched.

After synchronization, the original visible Tk benchmark ran three times on the same workstation with a fresh isolated SQLite save and Python process per run. The only witness changes were unique file names and an assertion that the Tk window was mapped before starting the timer. The total runs from the first boarding request to the final displayed arrival, after startup and before slot export. The segment value measures the longest worker `advance` request from submission to its finished response. [Qualification order](../work_orders/RS-PLAY-001I-PERF_VISIBLE_QUALIFICATION.md)

| Visible run | Journey wall time (s) | Maximum advance request (s) | Requests | Final tick |
| --- | ---: | ---: | ---: | ---: |
| 1 | 11.4092 | 0.4161 | 35 | 93851 |
| 2 | 11.5649 | 0.4222 | 35 | 93851 |
| 3 | 11.4011 | 0.4881 | 35 | 93851 |

All three met the existing 30 s total and 2 s segment targets on this host. The 35-step traces, checkpoints and full SQLite bytes matched the PR46 baseline witness, and each replay completed with zero mismatches. Replay left each file unchanged. The original 39.539 s visible result is historical evidence, and the matched speedup estimate comes from the three pairs above. Raw visible results are under `tmp/rs-play-001i-visible-20261108/`. Other devices and release performance remain unqualified.
