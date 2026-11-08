# RS-WORLD-WALK-RECOVERY — Verification

2026-11-09. Primary 6 persistence with 2 movement, 5 player input and 7 integration. Local self-review on Windows with Python 3.13.12. Baseline `a6364067c23794a6a6970be355f805343d9b0e1c`. [Work order](../work_orders/RS-WORLD-WALK-RECOVERY.md)

On the baseline, a footstep with an uncertain durable result left the actual map showing `SAVE_UNCERTAIN` without a recovery action. The worker now gates unrelated requests while a footstep needs confirmation. The map offers **이동 결과 확인**, reserves no idle time while waiting, and shows the outcome returned by the existing durable recovery method. Confirmation submits no game command. An absent result resumes at the original position and tick. A committed result resumes at the new position and tick.

Two real Tk cases inject a failure around the first SQLite write acknowledgement and two recovery-read failures. One case completes the first SQLite commit and the other leaves it absent. Both exercise the recovery button, guard a competing wait, advance the fake wall clock without charging idle time, and verify the exact number of writes. The next manual footstep advances once. The restarted worker reads the same saved protocol and position. [Integration regression](../../tests/integration/test_world_client.py)

The world client, conversation, observer, knowledge, supply, durability, SQLite recovery, durable replay and rulebook suite passed 125 tests in 152.41 s. Both Ruff profiles, scoped formatting, strict mypy across 372 files, all four import contracts, `pip check` and staged whitespace passed. Native Unity execution was outside this verification. The PR records the full protected regression and main synchronization.
