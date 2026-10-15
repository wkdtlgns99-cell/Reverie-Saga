# Unity Prototype

Unity6000.3.25f1 (e1dba0a9aba4),Windows x64,Mono,built-in renderer. Provisional engine;
Python remains authoritative. Source Assets/meta,Packages/lock and ProjectSettings are tracked.
Library,editor/license/account caches,local saves and builds are ignored. No engine plugin or
MCP server is required:edit project files,execute public editor methods,read actual logs/captures.

On another computer,start with [workstation setup](../../docs/WORKSTATION_SETUP.md).
Discover/reuse the exact editor version or install missing approved prerequisites;verify local
Python/login/license and actual editor/Brain execution. Git does not deliver those installations.
Current-host PASS and application-control failures are per-device evidence,not results for both PCs.

Latest2026-10-15 qualification:[receipt](../../docs/reviews/QT-F02_UNITY_SELECTION_2026-10-15.md).
45graphical checks(courtyard17/default24/invalid3/corrupt1),Windows release build/hook exclusion
and standalone startup/save/shutdown smoke PASS on the observed RTX4050 Laptop GPU host.
This supersedes older launch-blocked statements below for these actual runs. Small Game-view
UI overlap,human UX and full portable/standalone input/fault acceptance remain unqualified.

## Play

Open this checkout's clients/unity with the installed editor,open
Assets/Reverie/Scenes/PlayRoom.unity and press Play. Use WASD/arrows or Korean buttons.
Default save:tmp/unity-play/game.sqlite under this checkout. The view is a 3x3 test room.
The catalog browser displays6adapted Quilltale descriptions;it does not instantiate six worlds,
quest mechanics or old template stats. Loaded save branches retain their own working path.
The reconnect button resumes the current branch;reconnection appends a new attachment notice to the session-local history.

The approved local editor path is tmp/unity-editor/6000.3.25f1/Editor/Unity.exe.
Python .venv must exist in this checkout;this is a local development
harness,not a relocatable/bundled release. Catalog and generated DTOs are hash checked.

Set the environment before launching a new editor process to select the courtyard:

```powershell
$env:REVERIE_UNITY_SCENARIO='scenario:courtyard'
```

Unset/empty selects scenario:legacy. Courtyard defaults to tmp/unity-play-courtyard/game.sqlite;
REVERIE_UNITY_WORKING overrides either default. Existing saves require their original scenario.
Unknown IDs display UNKNOWN_SCENARIO before starting Brain or creating a save. Selection stays
fixed through load/reconnect;restart the editor with another selection to change rooms.
Courtyard starts bottom-left;Up approaches the enemy,while Right meets its wall. Both rooms
use the same authoritative combat/time/save rules;no larger world or quest system is implied.

## Generate / verify / build

From repository root:

```powershell
$env:PYTHONPATH="$PWD/src"
.\.venv\Scripts\python.exe -m app.engine_project --root "$PWD"
$env:REVERIE_UNITY_WORKING="$PWD\tmp\unity-verification\run-$([guid]::NewGuid().ToString('N'))\game.sqlite"
Remove-Item Env:REVERIE_UNITY_SCENARIO -ErrorAction SilentlyContinue
Remove-Item Env:REVERIE_UNITY_CASE -ErrorAction SilentlyContinue
& .\tmp\unity-editor\6000.3.25f1\Editor\Unity.exe -projectPath "$PWD\clients\unity" -executeMethod ReverieSaga.PlaytestBuild.BuildAndVerify -logFile "$PWD\tmp\unity-check.log"
```

Graphical verification opens the Game window,builds a Windows player and exercises24checks.
Wait for ENGINE_VERIFY_PASSED and editor exit0,not merely the launcher returning. Fresh empty
working directory is mandatory;old saves/slots are never deleted to make tests pass.
Actual initial/final screenshots,final view and120frame sample are under tmp/cp04-native.
Additional corrupt-file case:REVERIE_UNITY_CASE=corrupt with a fresh working directory,then
execute ReverieSaga.PlaytestBuild.VerifyCorrupt. Reset the case to normal for the full flow.
Screen capture needs graphical mode;[Unity coroutine guidance](https://docs.unity3d.com/2021.3/Documentation/Manual/CLIBatchmodeCoroutines.html) excludes WaitForEndOfFrame in editor batch mode.
For courtyard verification,set REVERIE_UNITY_SCENARIO=scenario:courtyard,use another fresh
REVERIE_UNITY_WORKING,and execute ReverieSaga.PlaytestBuild.VerifyCourtyard. Its actual
captures/final view go to tmp/qtf02-unity/native/<working-parent-name>. Invalid-ID case:
set scenario:unknown with a fresh working path and execute VerifyInvalidScenario;it checks
visible error,no Brain and no save. Clear scenario/case afterward for default legacy tests.
Build-only automation:

```powershell
& .\tmp\unity-editor\6000.3.25f1\Editor\Unity.exe -batchmode -projectPath "$PWD\clients\unity" -executeMethod ReverieSaga.PlaytestBuild.Build -quit -logFile "$PWD\tmp\unity-build.log"
```

Output:tmp/unity-build/ReverieSaga.exe and supporting files. Verification class/hook compile only in editor or DEVELOPMENT_BUILD;release assembly inspection
proves the hook absent. Development player test is opt-in with
REVERIE_UNITY_VERIFY=1 and a fresh REVERIE_UNITY_WORKING before launching;ordinary players
never run destructive fault probes. Current Windows application-control policy blocked the
final unsigned standalone executable. Editor verification passes;standalone runtime acceptance
remains UNVERIFIED. No security policy or license settings were weakened.

## Boundary / limitations

BrainConnection owns one Python subprocess/private binary pipe;engine_bridge routes intents
through existing ClientWorker. Full derived views drive every displayed position,HP and event.
Request identity,attachment change after load,frame/JSON bounds and generated schema hash are
checked. Responses contain canonical decimal strings;Unity floats affect rendering only.
The pipe route is a bounded prototype,not BLOCK5's production TCP/diff/chunk/ACK topology.
Malformed catalogs fail startup;compiler checks the frozen QT-F04 qualification dossier.

Own geometry and built-in shader material are placeholders. No external models/art/fonts are
copied into the project;Malgun Gothic is used from the installed OS for Korean UI.
First startup can log a Unity SearchDatabase indexing exception;it is separate from project
compilation/gameplay checks and remains recorded. User UX,final HD-2D art,gamepad,MIN-SPEC,
portable packaging and human UX are pending. CP04 source feedback/repair are accepted;external patch rereview NOT_RECEIVED.

CP04 repair:room geometry is fixed3x3/immutable walls;changed views reject before rendering.
Transport errors remain visibly recoverable;no-view failures retain status and Korean messages.
Timeout/shutdown waits run off-thread,reconnect waits by coroutine;recovery button submits the
existing Brain recover request. Catalog cap64KiB leaves1MiB-frame headroom. Wire hash covers
view/update/narrative/response fields,and generator uses declared types.
