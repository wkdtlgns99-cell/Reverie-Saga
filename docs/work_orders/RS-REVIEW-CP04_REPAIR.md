# RS-REVIEW-CP04 — Verified Findings Repair

Date:2026-10-12 | State:DONE / bounded repair accepted | Executor:Sol | Baseline:36ebc5e541a4f7900258feef568232a30f83224b,clean273files.
Director returned requested independent CP04 feedback;canonical checkpoint procedure authorizes bounded verification/repair.

Goal:fix concrete error/schema/qualification gaps,qualify native failure paths,and make the review packet runnable.
Reads:ENGINEERING_RULES,handoff/backlog,RS-CLIENT-003/QT-F06,actual source/tests,received CP04,client/save contracts.
Allowed MODIFY:src/app/engine_bridge.py,engine_project.py;src/adapters/narrative_catalog.py;
new tests/integration/test_engine_bridge.py,tests/unit/test_narrative_catalog.py;
clients/unity/**;content/narratives.manifest.json;QUILLTALE_SELECTION_LEDGER_2026-10-12.json;
V1_REUSE_INVENTORY.md;BACKLOG,SESSION_HANDOFF,GAME_SYSTEM_SUMMARY_KO,README;
RS-CLIENT-003/QT-F06 current pointers. NEW:CP04 feedback/dispositions/repair evidence/repaired packet,
byte witness and packet build tool. Root paths are C:/ReverieSaga. No agents/new provider calls.
Forbidden:reference writes,existing CORE/save contracts/tests/oracles/pins,original CP02/CP04 witnesses/ZIPs,
original candidate dossier and generation evidence. No broad import/final engine/release or OS-policy changes.

Contracts:
- Preserve no-view status/Korean messages;recoverable transport rejection is visibly labeled while polling/input remain usable.
- INVALID_REQUEST id0 is an explicit error envelope,not a normal identity response;one pending action is completed as rejected.
- Shutdown runs owned-child waits off Unity's main thread;reconnect waits asynchronously for cleanup before reopening the same working branch.
- Fixed room supports exactly3x3 and immutable width/height/walls;later geometry mismatch rejects visibly before rendering mutation.
- Verification hooks compile only in editor/development;release assembly inspection must prove absence.
- Schema hash includes native view/update/narrative declarations and response fields;generator maps by declared type and rejects unsupported types.
- Catalog cap64KiB leaves substantial1MiB frame headroom;max accepted catalog plus real update must fit.
- Compiler checks exact qualified candidate set,per-row qualification/source/adaptation binding and source decision scope;
  derived manifest separates source qualification from actual QT-F06 import authority.
-320other ledger rows explicitly NONE/NOT_QUALIFIED;historical raw hashes mean git-blob bytes,not present worktree bytes.
- New packet includes all tracked baseline diff/source/tests/fixtures/vectors/enforcement/lock files;private logs/saves/credentials excluded.

Verification:reproduce C-11/C-14/C-15 in Python tests before fixes;native corrupt-file diagnostic,
malformed request recovery,immutable-board rejection,strong failed-load/tick oracles,in-flight child kill/reconnect,
release-hook absence and actual captures. README shared/selective Ruff/format/strict types/import3+1,
focused tests and full regression;fresh extracted repaired packet runs the same suite with locked prerequisites.
Disposition every actual reviewer ID;no invented C-2/C-13. Close CP04 after feedback recorded,valid findings repaired/retested;
external patch rereview remains distinct. Standalone OS launch/CP03/bulk/rights limits retained.
Delivery:sync backlog/handoff/Korean progress,retain original evidence,report real results.

Acceptance:[dispositions](../reviews/RS-REVIEW-CP04_DISPOSITIONS_2026-10-12.md). Python22focused/local1292/extracted1292PASS,native24+corrupt1PASS/release-hook absence,mypy103/Ruff/format18/import3+1/source preservation PASS. No external patch rereview or standalone runtime certification.
