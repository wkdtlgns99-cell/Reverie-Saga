# QT-F27 — Implementation and native qualification

Updated:2026-10-19 | Status:LOCAL_ACCEPTED (final native acceptance completed2026-10-19).
Primary4 runtime retrieval;related2/3/5/6/7. Self-review only;D2 remains OPEN.
Order:[QT-F27](../work_orders/QT-F27_NPC_SELF_ACTIVITY.md).

Implemented recent8 self-activity retrieval through isolated canonical replay of compact
retained save steps. All core/protocol/fact/diff hashes and outcomes must match before
publication;final replay state must equal the live attachment. Only typed NpcActed and
WatchReplied for this NPC are eligible. Historical due times are retained. Selection ranks
newest-first;UI displays the selected records chronologically so newest lines remain visible.
No CORE,save format,conversation-memory capacity or live provider changes.
Session → serialized worker → private pipe/activity → generated Unity schema and actual
Unity/Tk controls are wired. Inspection does not advance time or modify retry/save state.

## Final native acceptance — 2026-10-19

Director explicitly resumes final validation,PR/checks and ordinary main merge;keep Unity open.
No editor process/window existed at entry (CIM and Computer Use inventory both empty for Unity).
Launched the existing pinned editor once,PID30672,without closing/restarting an editor.
Final unchanged runtime sources at a0c9217:169native PASS,0FAIL;result/retained/idle0.
All8 activity inspection points passed,including exact chronological lines,busy gating,
read-only current state and save bytes,rewind/reconnect and16-second wait selection.
Actual642x500 self-activity capture inspected:latest8/10/12-second records visible at history end.
Latency96.85–538.48ms,target<2s PASS on this host. Long-save/MIN-SPEC qualification remains open.
Five original/loaded/slot01/02/08 saves passed checkpoint/memory/activity readbacks and offline
replays,with identical before/after bytes. Scene normalized equality PASS;entry bytes restored.
Same editor PID30672 remained responsive in Edit mode. No installation/login/security changes.
Owned evidence:tmp/qt-f27-final-20261019/result.json,readback.py,python-check.log and
native-514a2feb01dc47d689b8fda5ee423e25/working/evidence;editor.log is outside the working parent.
Fresh Python integration/document checks17PASS12.08s;strict179files/both Ruff configurations PASS.
This closes the earlier interruption;historical attempts below retain their original status.
Release build,independent review and other-device performance remain outside this acceptance.
PR CI must pass on the final published head before ordinary merge;no waiver or CP06 release.

## Earlier evidence and limits

- New real session/worker/pipe/Tk suite7PASS;final source-binding/display revision7PASS11.68s:
  tmp/qt-f27-20261018/final-new.log.
- Related client/memory/activity/Tk/text/document regression121PASS77.71s:
  tmp/qt-f27-20261018/affected.log (includes the original7 new cases).
- Additional existing scenario/slot/memory regression67PASS,1sandbox hardlink denial;
  exact denied test rerun on permitted host1PASS0.79s. remaining.log and hardlink-host.log.
  Combined distinct affected tests189PASS,with revision-specific evidence as above.
- Both Ruff configurations,format15,strict mypy179files,import contracts3+1 and pip check
  passed during implementation. Publication turn reruns relevant checks separately.
- Publication2026-10-19:engineering document guards plus final new integration suite17PASS
  12.15s;both Ruff configurations,format7,together with exact generated wire comparison and
  git diff --check PASS. No native UI operation or new native acceptance on this turn.
- Initial native implementation passed with result/retained/idle0 in existing editor5088;
  no editor restart. Evidence:tmp/unity-verification/da4090d677694bd9990878af335aa54a.
  Actual self-activity screenshot inspected;observed request latency112–677ms on this host.
  This predates final live-state binding and chronological display adjustment:NOT final
  native acceptance. User's physical Escape stopped Computer Use;no further UI automation.
- Initial direct witness extraction failed because compact saves omit witness bodies;
  replaced with canonical replay,not synthetic counter histories. Initial pytest temp-root
  permission errors repaired with a workspace basetemp;no tests skipped/weakened.
- Scene regeneration changed only local IDs/empty-name whitespace;whole normalized scene
  equality checked and entry bytes restored on publication turn. Runtime evidence/tmp saves
  remain local ignored artifacts,not source files for publication.
- At the interrupted attempt,long retained-save replay latency,final native display/readbacks,
  release build and remote CI were UNVERIFIED/NOT_RUN;final native closure is recorded above. Earlier full1971PASS belongs to RS-TK-001/QT-F25 inputs.

## Publication authorization

Director2026-10-19 explicitly requests all this session's work committed and pushed.
Include RS-TK-001,QT-F25,QT-F26 and this partial QT-F27 with truthful status. This supersedes
prior local-only publication wording;no merge or CP06 release authorization is implied.

Latest authorization2026-10-19 also includes PR creation,passing checks and main merge. This supersedes earlier no-merge wording;CP06release hold remains.
