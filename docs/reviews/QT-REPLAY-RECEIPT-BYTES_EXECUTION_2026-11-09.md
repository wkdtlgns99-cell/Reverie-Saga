# QT-REPLAY-RECEIPT-BYTES — Verification

2026-11-09. Local self-review on Windows with Python 3.13.12 and SQLite 3.50.4. Baseline `fe9d6fd0af32dc5c347a5d0dd34e334572879803`. Primary 2 internal calculation support, related to 5 query latency, 6 persistence and 7 integration. [Work order](../work_orders/QT-REPLAY-RECEIPT-BYTES.md)

The direct activity profile attributed 6.74 s of 12.20 s profiled wall time to registered checkpoint validation. The prior receipt fingerprint path built a canonical projection 35,508 times on one activity query. It computed the depth needed to compose a document and then used only the bytes. The new path uses the same checked field lookup and JSON encoder without constructing that document. Existing depth checks still apply when composing owned documents. Replay, receipt and fingerprint validation still run.

Three alternating fresh-process pairs per channel used the frozen QT-F96 264-command save. The baseline was exported from Git. Direct and framed processes asserted their canonical and serialization source paths, with canonical source hashes retained by the harness. Each pair matched the complete activity, movement, talk and retry updates after normalizing the working path and attachment ID. Core, protocol, pins, SQL dumps, final file hashes and read-only and retry byte preservation also matched. The input file remained unchanged.

| Query | Baseline median, s | Candidate median, s | Reduction |
|---|---:|---:|---:|
| Direct activity | 4.405 | 4.231 | 3.9% |
| Direct talk | 4.549 | 4.323 | 5.0% |
| Framed activity | 4.381 | 4.212 | 3.9% |
| Framed talk | 4.714 | 4.359 | 7.5% |

All four medians improved. The 2 s target remains open. Measurements are for this workstation and fixture. The matched samples exclude profilers, and absolute results from earlier hosts or load conditions are separate. Raw evidence is under the ignored `tmp/qt-replay-receipt-bytes-20261109` task directory.

The candidate profile counted 35,508 byte selections and the runtime caller no longer uses the projected-height operation. Literal Unicode and control bytes, duplicate keys, invalid types, missing-key precedence, fresh subclass validation and owned depth behavior were verified. The canonical, protocol, replay, durability, reach-gate and rulebook suite passed 246 tests in 139.61 s. Both Ruff profiles, scoped test formatting, strict mypy across 372 files, all four import contracts, `pip check` and staged whitespace passed. The PR records full protected regression and synchronization.
