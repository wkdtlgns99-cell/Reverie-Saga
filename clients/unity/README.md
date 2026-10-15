# Unity Prototype

Unity6000.3.25f1 (e1dba0a9aba4),Windows x64,Mono,built-in renderer. Provisional engine;
Python remains authoritative. Source Assets/meta,Packages/lock and ProjectSettings are tracked.
Library,editor/license/account caches,local saves and builds are ignored. No engine plugin or
MCP server is required:edit project files,execute public editor methods,read actual logs/captures.

On another computer,start with [workstation setup](../../docs/WORKSTATION_SETUP.md).
Discover/reuse the exact editor version or install missing approved prerequisites;verify local
Python/login/license and actual editor/Brain execution. Git does not deliver those installations.
Current-host PASS and application-control failures are per-device evidence,not results for both PCs.

## Play

Open C:/ReverieSaga/clients/unity with the installed editor,open
Assets/Reverie/Scenes/PlayRoom.unity and press Play. Use WASD/arrows or Korean buttons.
With no scenario/quest/memory selectors,the ordinary editor starts the director-approved harbor
quest with persisted NPC memory. Catalog:content/dialogue/harbor-memory-v1.json;trusted pin in
harbor-memory-v1.sha256. Save:tmp/unity-play/harbor-memory/<catalog-pin>/game.sqlite. The view is a 3x3 test room.
The catalog browser displays6adapted Quilltale descriptions;it does not instantiate six worlds,
quest mechanics or old template stats. Loaded save branches retain their own working path.
The reconnect button resumes the current branch;reconnection appends a new attachment notice to the session-local history.
Memory modes also show **최근 대화 기억**(QT-F19). This read-only action shows one newest recorded
conversation;the original full-memory button keeps all records in time order. A received completion
report remains a report,not eyewitness evidence. Both buttons share busy/load/reconnect behavior
and take no turn. [Acceptance](../../docs/reviews/QT-F19_EXECUTION_2026-10-15.md).
**slot01 저장 정보**(QT-F20) previews the same slot01used by the prototype's save/load controls.
Saved time,quest progress and registered NPC-memory count appear in the history,while current
stats and attachment stay unchanged. The slot is validated without loading a new branch;an empty
or unusable slot reports an error. Full/recent memory controls share one row to retain history
space. [Acceptance](../../docs/reviews/QT-F20_EXECUTION_2026-10-15.md).

QT-F02 selectors:`REVERIE_UNITY_SCENARIO=legacy|harbor|grove` before starting the editor.
Explicit legacy retains tmp/unity-play/game.sqlite;harbor/grove get separate default subdirectories.
REVERIE_UNITY_NPC_MEMORY=1 enables memory for an explicitly selected harbor quest catalog;0keeps
the old quest mode;unset with explicit old selectors also keeps old behavior. Other values reject.
Changing a selector does not convert an existing save. Explicit resume selection must match saved
rule/schema fingerprints. Two new placeholder rooms vary role IDs,wall/enemy/NPC positions;
their settlement labels refer to accepted descriptions,not complete towns or quest mechanics.

The local editor is C:/ReverieSaga/tmp/unity-editor/6000.3.25f1/Editor/Unity.exe.
Python environment and repository must exist at C:/ReverieSaga;this is a local development
harness,not a relocatable/bundled release. Catalog and generated DTOs are hash checked.

## First Quest

The ordinary no-selector preset now runs QT-F07 with the approved editorial catalog and memory.
For a different explicitly selected catalog,use a validated approved catalog from the root
[preparation instructions](../../README.md#first-quest--prepared-gemini-dialogue).
Before starting the editor:

```powershell
$env:REVERIE_UNITY_SCENARIO="harbor"
$env:REVERIE_UNITY_QUEST_CATALOG="C:\ReverieSaga\tmp\dialogue\harbor-v1.json"
$env:REVERIE_UNITY_QUEST_SHA256="<printed-catalog-sha256>"
```

Both catalog/hash are required. Default quest working path is tmp/unity-play/harbor-quest/game.sqlite;
use a fresh path for different content pins. Talk beside the NPC:accept,defeat the target,return
and report. The Brain records one favor;the screen selects prepared dialogue from committed facts.
Load/reconnect retain the current branch and catalog pins. Gameplay does not need GEMINI_API_KEY
or a network call. Unset both quest variables to return to the earlier quest-less rooms.

For native qualification,set those same selectors with a fresh REVERIE_UNITY_WORKING directory,
then call ReverieSaga.PlaytestBuild.Verify. QuestFlow exercises mode-specific checks and captures public state,
screenshot and120frames. Local [QT-F07 acceptance](../../docs/reviews/QT-F07_EXECUTION_2026-10-13.md):
quest14+legacy24+harbor11+grove11+corrupt1=61PASS,Windows build/release-hook absence PASS.
That run used an offline automated-test-only receipt/catalog,not production content approval
or an actual Gemini response. Director deferred live preparation;setup instructions are in the root README.

## NPC Conversation Memories

QT-F17 adds **NPC 대화 기억** to the ordinary approved memory preset and explicit memory mode.
The button is available after attach and disabled during a pending request or connection failure.
It appends the NPC's recorded conversations with this player to the existing Korean history:
directly heard quest acceptance and a received completion report,with their game times. A received
report is explicitly distinguished from witnessing the enemy's death. No turn/reward/last-command
change or API call occurs. Empty memories are explicit;non-memory modes hide the button.

Load restores the selected slot's memories and clears later history;reconnect reads that loaded
branch. These remain the same two scoped records,not broader cognition or private NPC knowledge.
The pipe adds only `memory`;existing attachment/request identities and limits apply. Regenerate
the C#wire pin with engine_project when updating the protocol;older wire pins reject the mismatch.
No save migration is needed. Native Verify now checks inspection/busy/state/file preservation
at empty,accepted,unreported,reported,loaded,reconnected and branch-reported states and captures
the real screen. [Current acceptance](../../docs/reviews/QT-F17_EXECUTION_2026-10-15.md).

## Generate / verify / build

From repository root:

```powershell
$env:PYTHONPATH="$PWD/src"
.\.venv\Scripts\python.exe -m app.engine_project --root C:\ReverieSaga
$env:REVERIE_UNITY_WORKING="C:\ReverieSaga\tmp\unity-verification\run-$([guid]::NewGuid().ToString('N'))\game.sqlite"
& .\tmp\unity-editor\6000.3.25f1\Editor\Unity.exe -projectPath C:\ReverieSaga\clients\unity -executeMethod ReverieSaga.PlaytestBuild.BuildAndVerify -logFile C:\ReverieSaga\tmp\unity-check.log
```

Graphical verification opens the Game window,builds a Windows player and exercises24checks.
Wait for ENGINE_VERIFY_PASSED and editor exit0,not merely the launcher returning. Fresh empty
working directory is mandatory;old saves/slots are never deleted to make tests pass.
Actual initial/final screenshots,final view and120frame sample are under tmp/cp04-native.
Additional corrupt-file case:REVERIE_UNITY_CASE=corrupt with a fresh working directory,then
execute ReverieSaga.PlaytestBuild.VerifyCorrupt. Reset the case to normal for the full flow.
Screen capture needs graphical mode;[Unity coroutine guidance](https://docs.unity3d.com/2021.3/Documentation/Manual/CLIBatchmodeCoroutines.html) excludes WaitForEndOfFrame in editor batch mode.
For QT-F02:set REVERIE_UNITY_SCENARIO to harbor or grove,use a new empty REVERIE_UNITY_WORKING
directory per run,and call ReverieSaga.PlaytestBuild.Verify. The dedicated scenario path checks
selected positions,combat,load/retry,NPC and loaded-branch reconnect and records a screenshot,
final response and120-frame sample in that working directory's evidence subdirectory.
Run legacy separately for the retained full boundary/fault matrix. Verify does not build;
BuildAndVerify/Build still own release-build and hook-absence qualification.
Build-only automation:

```powershell
& .\tmp\unity-editor\6000.3.25f1\Editor\Unity.exe -batchmode -projectPath C:\ReverieSaga\clients\unity -executeMethod ReverieSaga.PlaytestBuild.Build -quit -logFile C:\ReverieSaga\tmp\unity-build.log
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
