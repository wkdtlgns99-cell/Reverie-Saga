# QT-F26 — Native Unity NPC activity acceptance

Date:2026-10-18 | State:LOCAL_ACCEPTED | Executor/review:Sol,self-review.
[Order](../work_orders/QT-F26_UNITY_NPC_ACTIVITY.md). Primary7;participants2/3/5/6.
Baseline:b2876a7 plus16prior dirty paths from RS-TK-001/QT-F25,preserved outside declared docs.

## Result and wiring

Closed QT-F25's explicit native-display qualification gap. Existing
ClientSession→ClientUpdate.messages→binary BrainConnection→PlayRoom history renders the factual
activity line. Production Python,C# client,wire,approved dialogue,engines and save formats unchanged.
Only the editor/development verification hook gained independent literal checks and two capture points.

Native143checks PASS/0FAIL:128existing/default-memory guards(including explicit memory-mode check)
plus15activity/cardinality/retry/file-preservation/load/reconnect/capture guards.
ENGINE_VERIFY_PASSED,RESULT code=0,EDITOR_RETAINED code=0,EDITOR_IDLE code=0 all observed.
EditorPID5088 remained alive/responsive in Edit mode;no process exit code claimed and no restart.

| Actual native point | Tick | Bells | Reward | Activity message |
|---|---|---|---|---|
| Rejected distant talk |0|0|0|Absent|
| Accept |2|1|0|Exactly one;history suffix matches|
| Reminder |3|1|0|Exactly one|
| Report |12|6|1|Exactly one;actual screenshot/response/history captured|
| Exact retry |12|6|1|No new activity or dialogue;save bytes/view unchanged|
| Gratitude |13|6|1|Exactly one|
| Slot load/reconnect |10|5|0|Later12/13activity history cleared;no new talk|
| Restored-branch report |12|6|1|Exactly one;second screenshot/response/history captured|

This existing native route includes reminder at3;its12/6report is distinct from QT-F25's
16-second Python route27/13. All previous native numeric oracles/actions remain unchanged.
Existing wait selection additionally verifies12→28→loaded12,retry once and selected16retained.

## Execution and initial failure

Reused installed CPython3.13.12 AMD64/Tk8.6 and pinned editor6000.3.25f1/e1dba0a9aba4
(file6000.3.25.14801824). pip check PASS. Process discovery confirmed Unity closed at entry,
as the director stated. Actual editor startup resolved existing Personal entitlement;no installation,
login,credential,license-policy or security change. No provider/agent/publication operation.

One editor launch used existing PlaytestBuild.Verify with VERIFY_EXIT=0 and a fresh owned path.
The runner mistakenly placed editor.log in the same parent as game.sqlite. Existing empty-directory
guard correctly rejected it **before play**:IOException,verification NOT_RUN. No save was deleted,
guard weakened or failure erased. The ignored launcher now puts game.sqlite under working/.
Actual recovery used the **same** open editor's Reverie→Verify Current Selection(Keep Editor Open)
menu through the computer-use skill;it created its normal fresh GUID directory and ran successfully.
No Unity shutdown/relaunch. Initial failure and successful run share the retained original editor log.

```powershell
& 'C:/Reverie Saga/tmp/qt-f26-20261018/launch.ps1'
# Recovery:existing editor menu,not another process;poll explicit result/retained/idle markers.
$env:PYTHONPATH="$PWD/src"; $env:PYTHONHASHSEED='0'; $env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m pytest -q tests/integration/test_npc_activity_return.py tests/unit/test_client_text.py tests/unit/test_engineering_rules.py --basetemp .pytest_cache/qt-f26-focused
.\.venv\Scripts\python.exe tmp/qt-f26-20261018/readback.py
```

Focused Python28PASS12.04s,exit0. Shared/selective Ruff PASS,scoped format6files PASS,strict mypy177
files PASS using existing pinned source mode,import contracts3+1kept/0broken. Actual Unity Csc/Bee
compile succeeded before the native run. No Python/shared CORE change:full1971PASS1092.70s from
QT-F25 is reused for byte-identical production/test/config inputs;full suite NOT_RERUN here.

## Captures and durable evidence

Owned runtime output:tmp/unity-verification/d2bb0f4bde4e4716938c9a5829ea1182/evidence/.
Both activity-reported.png and activity-branch-reported.png were visually inspected at actual642x500:
readable bottom line `NPC 활동 현황 · 12초 · 종 6회 · 호출 응답 0회.`;quest complete/favor1 visible.
Matched corresponding *-response.json and *-history.txt;capture preserved response/history/save bytes.
Images can be identical because the final view and visible tail are the same;the separate complete
history witnesses differ(original2689bytes/restored654bytes). No synthetic UI/frame was supplied.
Controls368x242/history368x162,scrolling controls594pixels;existing scene/HUD composition retained.
120editor frames:median2.095302ms/p95 2.919402ms on this host,not target-device/MIN-SPEC evidence.

| Actual save | Tick/revision | Stage/bells | Evidence records | Offline replay steps |
|---|---|---|---|---|
| Original working |13/13|3/6|accepted2,completion_reported12|13|
| Final loaded branch |12/12|3/6|accepted2,completion_reported12|12|
| slot01 |10/10|2/5|accepted2|10|
| slot02 |13/13|3/6|accepted2,completion_reported12|13|
| slot08 |12/12|3/6|accepted2,completion_reported12|12|

All five validate against the accepted content/bundle and equal simulation pins;replay mismatches0.
All five raw save hashes unchanged by validation/context reads/replay. Evidence remains reported,
not witnessed defeat;one favor derives from stage3. Original/loaded branch are distinct files.

Ignored receipts:tmp/qt-f26-20261018/entry.json,readback.json,readback.log,native-result.json,
python-focused.log,mypy.log,imports.log,runtime-imports.log. Original editor log is under that
directory's native-d95cac0c35504efea0ef5f6c5c27b765/editor.log. No raw licensing/account logs published.
Native Prepare regenerated only scene-local identifiers and one empty-name trailing space;
normalized whole-scene topology/fields matched before byte-exact restoration. Both tracked
ProjectSettings files remained identical to entry. Prior Python/tests/config/raw G07 sources and
approved catalog preserved. Final UTF8/links/diff/progress/source-preservation checks PASS.
Final document-entry guards10PASS1.42s. Read-only final process check:editor5088responsive,
no remaining Python Brain process for this run. Fifteen new activity checks are included in143,
not additional to it. All prior production/test/config entry hashes remain equal.

Limits:current-host editor verification/self-review only;no new release build,standalone,other-device,
human UX or independent review acceptance. D2broader world/NPC/retrieval remains OPEN,V3stopped,
CP06release held. Local edits only;no commit/push/merge or automatic further task.
