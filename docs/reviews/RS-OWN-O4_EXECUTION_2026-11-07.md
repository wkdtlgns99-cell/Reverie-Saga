# RS-OWN-O4 — Read-Only Unity World Verification

2026-11-07. Primary 5 presentation with 3 data, 6 persistence and 7 integration. Self-reviewed on the current Windows workstation. [Work order](../work_orders/RS-OWN-O4_READ_ONLY_UNITY_WORLD.md).

## Behavior

The Unity editor menu **Reverie → 현재 월드 보기 (읽기 전용)** opens a separate panel. Opening it or pressing **새로고침** calls the short-lived `app.world_observer` reader. It follows the current `--world-knowledge` working file and active-branch reference, validates the committed state with existing registered save pins, and returns one bounded versioned document. The panel presents the logical tick and revision, current location, supply quest stage and completion time, and up to eight completed player-visible exchanges for the selected local resident. The same reader accepts an explicit working-file base path for isolated tests.

Unity sends no turn or save command. The reader uses SQLite read-only mode, including while the Python owner is open. It returns a retryable diagnostic if a concurrent writer makes the file unavailable. A changed branch during the read discards the result. Pending speech and private knowledge metadata are excluded from the response. The UI clears old data on refresh or error. Viewing the last committed progress does not require the Python window to stay open.

## Current-host Unity

- Unity 6000.3.25f1 (`e1dba0a9aba4`) compiled the panel. A temporary editor entry point selected an isolated SQLite fixture so the test did not read or edit player progress. The first launch ended before inspection. The second reused the same installed editor and project with an attached process session. The panel opened and rendered Korean text.
- At game tick 7, revision 4, the native panel showed **보급 의뢰 · 진행 중** and the courier's saved line. Registered Python supply commands collected two crates and delivered them in the same working file. Pressing refresh displayed **보급 의뢰 · 완료**, **보급로 복구 완료**, and the completion time at tick 10, revision 7. The SQLite SHA-256 matched immediately before and after the native read.
- Temporarily renaming the owned fixture produced `SAVE_NOT_FOUND` with no stale quest or dialogue on screen. Restoring the file and refreshing recovered the completed view. The native dropdown listed both roles. The Python integration test independently verifies each role's distinct transcript payload.
- The temporary native entry point and Unity's generated scene-recovery copies were preserved under `tmp/rs-own-o4/native-20261107/` outside tracked sources. The verification panel was closed and the Unity editor was left open. The editor run did not build a Windows player or qualify another device.

## Python verification

The integration regression uses actual registered commands, durable saves and the one-shot reader process. It checks visible progress during an open owner session, role-specific transcripts, branch loading, complete versus partial speech, the eight-exchange cap, and missing, corrupt, busy and changed-branch failures. Before and after reads it compares the durable file bytes, protocol and working directory inventory as applicable.

The final focused world, durability and rulebook run passed 206 tests in 105.89 s, including six observer cases. Both Ruff configurations, four-file formatting, strict mypy across 360 files, four import contracts, `pip check`, eight local documentation links and `git diff --check` passed. The delivery PR records final required CI and clean local main synchronization.
