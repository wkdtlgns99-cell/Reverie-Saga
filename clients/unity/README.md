# Unity Prototype

Unity6000.3.25f1 (e1dba0a9aba4),Windows x64,Mono,built-in renderer. Provisional engine;
Python remains authoritative. Source Assets/meta,Packages/lock and ProjectSettings are tracked.
Library,editor/license/account caches,local saves and builds are ignored. No engine plugin or
MCP server is required:edit project files,execute public editor methods,read actual logs/captures.

## Play

Open C:/ReverieSaga/clients/unity with the installed editor,open
Assets/Reverie/Scenes/PlayRoom.unity and press Play. Use WASD/arrows or Korean buttons.
Default save:C:/ReverieSaga/tmp/unity-play/game.sqlite. The view is a 3x3 test room.
The catalog browser displays6adapted Quilltale descriptions;it does not instantiate six worlds,
quest mechanics or old template stats. Loaded save branches retain their own working path.
The reconnect button resumes the current branch;reconnection appends a new attachment notice to the session-local history.

The local editor is C:/ReverieSaga/tmp/unity-editor/6000.3.25f1/Editor/Unity.exe.
Python environment and repository must exist at C:/ReverieSaga;this is a local development
harness,not a relocatable/bundled release. Catalog and generated DTOs are hash checked.

## Generate / verify / build

From repository root:

```powershell
$env:PYTHONPATH="$PWD/src"
.\.venv\Scripts\python.exe -m app.engine_project --root C:\ReverieSaga
$env:REVERIE_UNITY_WORKING="C:\ReverieSaga\tmp\unity-verification\run-$([guid]::NewGuid().ToString('N'))\game.sqlite"
& .\tmp\unity-editor\6000.3.25f1\Editor\Unity.exe -projectPath C:\ReverieSaga\clients\unity -executeMethod ReverieSaga.PlaytestBuild.BuildAndVerify -logFile C:\ReverieSaga\tmp\unity-check.log
```

Graphical verification opens the Game window,builds a Windows player and exercises17checks.
Wait for ENGINE_VERIFY_PASSED and editor exit0,not merely the launcher returning. Fresh empty
working directory is mandatory;old saves/slots are never deleted to make tests pass.
Actual screenshot,final view and120frame sample are under tmp/unity-verification.
Screen capture needs graphical mode;[Unity coroutine guidance](https://docs.unity3d.com/2021.3/Documentation/Manual/CLIBatchmodeCoroutines.html) excludes WaitForEndOfFrame in editor batch mode.
Build-only automation:

```powershell
& .\tmp\unity-editor\6000.3.25f1\Editor\Unity.exe -batchmode -projectPath C:\ReverieSaga\clients\unity -executeMethod ReverieSaga.PlaytestBuild.Build -quit -logFile C:\ReverieSaga\tmp\unity-build.log
```

Output:tmp/unity-build/ReverieSaga.exe and supporting files. Native player test is opt-in with
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
portable packaging and CP04 independent feedback are pending.
