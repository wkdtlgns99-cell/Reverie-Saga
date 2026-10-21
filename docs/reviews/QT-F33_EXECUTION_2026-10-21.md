# QT-F33 — Work activity inspection evidence

Date:2026-10-21 | Status:LOCAL_ACCEPTED | Self-review,not independent.
Order:[QT-F33](../work_orders/QT-F33_NPC_WORK_INSPECTION.md).
Primary4retrieval support;related5/6/7. D2OPEN;CP06release held.

## Scope / baseline

Clean fetched main c00a2ad9e9ccae46f69290c2f1732787a22c0c4c(PR11merged),branch
codex/npc-work-inspection-20261021. Earlier5-edit stash/tmp sync backup preserved.
Director requests one next increment,all tests until ready for main. Actual publication
is not performed by this increment;required remote checks cannot be inferred from local tests.
No agents,provider calls,CORE/rules/schema/wire/catalog/dependency/policy changes.

Original HEAD app modules extracted into ignored tmp/qt-f33/baseline and actually executed
against unchanged surrounding sources. Two valid16-second waits reach32:original inspection
contains only bells18..32and no production. tmp/qt-f33/baseline-reproduction.log records it.

## Change / source truth

ClientSession.inspect_activity → activity_messages → existing _verified_activity/Runner.
Exactly one isolated replay verifies all retained steps and exact current core/protocol.
Existing recent_activity API,mixed8ordering and ordinary memory-mode text stay unchanged.
Work mode appends checkpoint boundary,separate work3actual ProvisionPrepared events and
canonical current stock from the verified snapshot. All counts/times have actual sources;
checkpoint stock never becomes invented lost production. No query command or save write.
Read failures log explicitly;ordinary source failures stay visible and recoverable.
Fatal/process-control exceptions propagate. Unity/Tk/worker/binary pipe use existing callers.

## Python / static verification

- New integration file:22PASS14.98s,last targeted run tmp/qt-f33/targeted5.log.
  Independently expected0/3/4/8/12/32,all work despite mixed eviction,unchanged owner/core/
  protocol/trace/bytes/retry,slot/load/restart,checkpoint6/32without historical fabrication,
  hash/header/current/owner/duplicate rejection,one real replay,IO/hash error recovery,
  process-control propagation,real binary pipe and actual Tk display.
- Initial development tests had invalid single32/28-second wait setup(max16),then a helper/
  parameter name collision;corrected test inputs/helpers without changing assertions/rules.
  First run also exposed missing failure logging;actual inspection now logs and tests verify it.
- Ruff shared/selective PASS;README scoped formatting plus changed Python14files PASS;
  strict mypy190files PASS;import contracts3+1PASS;pip check PASS. Final individual
  results are in tmp/qt-f33/static-final.log. Its batched exit1was only generated scene
  whitespace;normalized-equal original-byte restoration followed by git diff --check PASS.
- Fresh full regression,not a union of reruns:2101PASS778.80s/exit0,
  `python -m pytest -q --basetemp .pytest_cache/qt-f33-full`,tmp/qt-f33/full.log.
  Used normal sys capture and permitted loopback/link access;no skipped/weakened cases.
- Exact current .github/workflows/checks.yml boundary selection:31PASS10.46s/exit0,
  tmp/qt-f33/ci-boundaries.log. Includes rulebook,SQLite/clone ownership,worker/Tk ordinary
  and process-control errors,rollback/uncertain commit/postcommit presentation boundaries.

## Native Unity

Current observed Windows host;device identity/MIN-SPEC/other computers unqualified.
Reused installed Python3.13.12 AMD64/Tk8.6/editor6000.3.25f1(e1dba0a9aba4).
No editor running at entry(one permitted process inventory and CUA inventory);one launch
PID18656,retained through menu rerun,no restart. No installation/login/policy changes.

First run133PASS0FAIL;capture showed clipped heading at547x376. Shortened work rows while
retaining actual time,+1and historical stock. Same editor menu rerun:final133PASS0FAIL,
including all prior116and17new busy/read-only/exact-work/capture checks. These are133
distinct checks rerun,not266distinct tests. Result/retained/idle codes all0.
Final native root:tmp/unity-verification/2a12c9ec9574499ba1a20708a905ab31.
First root:tmp/unity-verification/5a01d0998adc40a8b3182e97a8170917.
Logs:tmp/qt-f33/native-first.log,native-final.log,editor.log.

Final evidence/work-inspect-late.png visually inspected:source heading,work4/8/12and
historical stocks1/2/3plus current3/3all readable together at547x376. Exact tick27response
and history recorded next to capture. Inspections at0/16/7/10/27preserve current state,
attachment,working file,quest/reward and busy gates. Measured120–490ms on this host.
Unrelated foreground windows briefly occluded CUA;only Unity was activated/interacted with.
One coordinate menu attempt dismissed without running;fresh accessibility selection invoked
the actual verification item. No implied success from the dismissed click.

## Save / build / delivery

All7actual managed final saves qualified:game16,loaded branches35/38/39/35,current slot35
and previous slot27. Explicitly exclude .lock.sqlite sidecars;actual inventory equals these
7paths. validate_save plus canonical replay plus new actual activity query all PASS;work4/8/12,
stock3,quest stages and original promise/report times match independent expected values.
Every file SHA unchanged before/after;tmp/qt-f33/readback.py and readback.json. After UI
work,the7saved hashes and all4qualified source/test/native files were rechecked unchanged.

An attempted menu Build selection instead entered ordinary Play on this task's own source16;
no gameplay input was submitted. Stopped it with Ctrl+P;source/save hashes remain unchanged.
Menu state was unstable across UI actions;no success inferred. Kept editor18656open and used
the existing public Build CLI on a new isolated project copy:46tracked Unity input files copied
byte-for-byte/hashed before preparation,tmp/qt-f33/build-copy-hashes.json. One temporary
build-only editor process ran sequentially after full tests and exited0;original editor never
restarted. No settings/dependencies/license changes. Command:

```powershell
tmp/unity-editor/6000.3.25f1/Editor/Unity.exe -batchmode -quit -projectPath C:/ReverieSaga/tmp/qt-f33-build/clients/unity -executeMethod ReverieSaga.PlaytestBuild.Build -logFile C:/ReverieSaga/tmp/qt-f33/build.log
```

Actual Windows build89,483,696bytes PASS;RELEASE_VERIFICATION_HOOK_ABSENT and
ENGINE_BUILD_PASSED logged. Output:tmp/qt-f33-build/tmp/unity-build/ReverieSaga.exe.
This qualifies compilation/release-hook exclusion,not portable standalone startup or release.
All Unity C#inputs are the qualified source bytes;Python/content remain external development
dependencies. Do not launch this copied-layout player as if a standalone package were qualified.

Original scene serialization compared equal after local-ID/trailing-space normalization;
restored exact entry bytes SHA2563157e6272f93a108ce80848f9d1352fdaa15f3ecae3e750e525763818b011b94.
tmp/qt-f33/scene-restoration.json;scene has no final diff. Final fetch:HEAD and origin/main
both c00a2ad;original editor18656responding,temporary build process exited. Earlier stash kept.

Self-review:only the11allowed app/test/native-verification/docs paths;no change to engine,
domain,contracts,format/pins,production Unity body,dependencies or governance. Source hashes
in tmp/qt-f33/qualified-source-hashes.json. Final rulebook/document guards10PASS1.04s;
exact11path scope and git diff --check PASS. Original editor responds and owned native Brain
count0;temporary build process exited. Acceptance PASS for source truth,read-only/retry,
actual callers,static/full/native/build/save evidence and synchronized progress documents.
Local changes are ready for commit/PR publication. No remote CI/push/PR/merge,independent
review,other-device/MIN-SPEC/human UX or release acceptance claimed. CP06held,D2OPEN.

## PR-only publication follow-up

Director2026-10-21now explicitly requests commit,push and PR creation only;do not merge or
enable auto-merge,and do not wait for remote CI. This supersedes the earlier local-only
publication limit. All11delivery file hashes matched the accepted snapshot at this turn
entry;production/test/native inputs are unchanged,so reuse full2101/boundary31/native133/
save7/build/static evidence. Only publication status documents changed;rerun document guards.
Git/GitHub record actual commit,PR and check state;remote CI success is not inferred.
