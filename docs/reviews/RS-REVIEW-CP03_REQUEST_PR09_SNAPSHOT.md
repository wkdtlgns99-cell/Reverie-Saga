# RS-REVIEW-CP03 — First Generalized Room Unit

State:PREPARED;feedback NOT_RECEIVED. Reviewer:director-forwarded Claude;no automatic dispatch.
Date:2026-10-15 | Baseline HEAD1ad22446d48c50b8b72a6d3af8de3c9d775134ea,uncommitted patch.
Request independent review of this exact qualified snapshot;first-unit self/native acceptance DONE.
Scope:QT-F02 first bounded Python/Tk unit;not broader quest/world/bulk/release acceptance.
Authority:[backlog checkpoint register](../../BACKLOG.md#claude-checkpoints-and-defect-repair--2026-10-07).

## Read and reproduce

Packet:[ZIP](../../tmp/reviews/RS-REVIEW-CP03_2026-10-15.zip),
[input witness](RS-REVIEW-CP03_INPUTS.json),[tracked patch](RS-REVIEW-CP03_DIFF.patch).
New files are included in full and hashed in the witness;the tracked patch does not pretend
they existed at baseline. External digest sidecar:tmp/reviews/RS-REVIEW-CP03_2026-10-15_SHA256.json,
outside the hashed source set. No private saves/accounts/caches or nested review archives.
Actual acceptance:38focusedPASS12.85s/full1330PASS362.34s;strict types106/Ruff/format15/
imports3+1 PASS. Initial failures and the exact-byte dossier restoration are in the receipt.

Read [runtime contract](../work_orders/QT-F02_ROOM_BINDINGS.md),
[actual commands/results/failures](QT-F02_ROOM_BINDINGS_2026-10-15.md),
[MASTER](../MASTER_GAME_ARCHITECTURE.md),[README](../../README.md#verification),
[per-device qualification](../WORKSTATION_SETUP.md#qt-f02-current-workspace-qualification--2026-10-15).
The parent QT-F02 document retains the earlier authoring receipt;this unit is its bounded
runtime extension. Earlier CP04/CP02 witnesses describe other immutable historical snapshots.

Actual sources:domain/scenario;app/watch,encounter_registry,watch_registry,client_session,
client_worker,client_text,client;engines/encounter,watch;orchestration/trial,encounter,watch.
Read surrounding state_io/serialization/turn/read_views/persistence/save-slot/SQLite contracts
and consumers too;all tracked current source/tests/fixtures/vectors/locks/docs are in the packet.
Inspect tests/unit/test_scenario.py and tests/integration/test_scenario.py plus original
encounter/watch/durable/client/replay cases;independent literal expectations are in the order.

Prerequisites:Windows x64 CPython3.13.12 with stdlibTk;create a local environment and install
20exact packages via unchanged requirements-dev.lock/--require-hashes. Do not copy a .venv.
Follow README parent/PYTHONPATH setup;run focused tests,full regression,Ruff/format,mypy/imports.
The originating host needs documented source-mode mypy due to blocked native modules;other
hosts should reuse their functioning pinned checker. Unity is not required for this unit's
Python/Tk verification;no new Unity result is claimed. Label missing tools/execution explicitly.

## Focused questions

1. Do all configured command/fact/delta/cue/checkpoint paths use selected roles/placements,
   including codecs and subclass defaults,without leaking historical IDs or weakening old checks?
2. Are complete immutable settings pinned before use,and are default legacy pins and historical
   golden bytes genuinely preserved? Check custom initial placement/role identity differences.
3. Do wrong-scenario open/load and invalid targets preserve authoritative state,attachment,
   files and UI truth? Check replay/uncertain-commit retry and canonical entity ordering.
4. Are exactly3x3/one wall/one role restrictions,geometry coordinates,bell time/count invariants,
   no-counter-on-kill and error precedence consistent across every consumer and independent test?
5. Are the partial Qt-F02 scope,Tk evidence,Unity limitation and pending CP03 status honest?
   Quest consequences remain unimplemented product requirements,not accepted by a bell demo.

Do not infer full world/content/rights/final-engine/release acceptance. Report exact paths and
concrete failing cases;distinguish confirmed defects,latent extension risks and scope exclusions.
State files inspected,commands actually run,environment failures and missing context. Sol must
verify findings,perform bounded repairs/retests and record dispositions before expansion.
