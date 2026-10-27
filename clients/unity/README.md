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

QT-F39 adds the fixed **저장 관리** toggle beside dialogue focus. Its scrollable panel
selects slot01–08,inspects current/previous save metadata and memory comparisons,saves the
current progress,and explicitly loads either version. Saving over a valid slot retains
one previous version;an empty previous slot reports that fact. A damaged current save is
not silently replaced or loaded from a fallback. Choose **이전 저장 불러오기** to create
a private working branch from a validated backup;both source files remain unchanged.
Further saves use the selected slot,so choose another slot to preserve a damaged source.
Movement keys are suppressed while the panel is open;pending replies still arrive.
Escape closes it;opening dialogue focus closes it. The selected slot and manager mode
survive load/reconnect in the same room. This is local recovery,not cloud/version history
or deletion. [Contract](../../docs/work_orders/QT-F39_SAVE_MANAGER_RECOVERY.md).

QT-F32 adds **대화 크게 보기** above the scrollable controls. It expands the history in
the same compact window;**조작 화면으로** or Escape returns. WASD/arrows do not move the
player while reading. Pending responses still arrive;focus survives load/reconnect,while
slot/wait selection and independent controls scroll stay intact. A new room starts with
controls visible. Switching views opens the latest history without taking a turn.
[Contract](../../docs/work_orders/QT-F32_DIALOGUE_FOCUS.md).

QT-F28 opt-in work mode:before starting a new editor process,set
`REVERIE_UNITY_NPC_WORK=1`. With no other selectors,the approved harbor-memory preset is
used with work enabled and a separate default save at
tmp/unity-play/harbor-work/<catalog-pin>/game.sqlite. Only unset/0/1 are accepted;explicit
non-memory selections cannot enable work. An existing editor retains its environment;
do not restart an editor merely for verification. Use an already selected mode or a later
ordinary start. Explicit working paths must already have matching feature pins or be fresh.

The NPC prepares communal supplies at logical seconds4/8/12,then stops at3. Talk shows
current stock;NPC activity shows recent production with actual source times. Slot preview
shows saved stock;load/reconnect use their own committed branch. This is not player inventory,
trade or additional quest reward. The private wire fields remain unchanged.
[Contract](../../docs/work_orders/QT-F28_NPC_PROVISIONS.md).

QT-F29 adds factual work recollection to the same NPC talk button in work mode. It names
only actual production since the last retained conversation,then shows current stock.
If none is confirmed in that saved interval,the NPC says so. Loading/reconnecting uses that
branch's conversation history. Busy/retry behavior is unchanged;no new selection is required.

QT-F30 also recalls actual answered player calls since the previous retained conversation.
The history shows the confirmed count and latest3request/response times;periodic bells cannot
trim those call memories. Empty/truncated history is explicit. Work/call context uses one
verified replay;load/reconnect follows that branch and retry emits no repeated recollection.
[Contract](../../docs/work_orders/QT-F30_NPC_CALL_RECOLLECTION.md).

QT-F31 work-mode return dialogue also displays the latest saved player promise/report and
its original time. A received report is explicitly separate from witnessing a defeat.
The existing persistent anchor survives truncation of old replay steps;newer branch reports
do not leak through load/reconnect. No extra replay,turn,mode flag or save conversion.
[Contract](../../docs/work_orders/QT-F31_NPC_PLAYER_MEMORY.md).

Open C:/ReverieSaga/clients/unity with the installed editor,open
Assets/Reverie/Scenes/PlayRoom.unity and press Play. Use WASD/arrows or Korean buttons.

QT-F54:`REVERIE_UNITY_NPC_AID=1` with cycle+memory enables NPC passage support.
Unset/0retains prior behavior;other values reject before starting a Brain or save.
The approved no-selector harbor preset supplies memory;set `REVERIE_UNITY_NPC_CYCLE=1`
and `REVERIE_UNITY_NPC_AID=1` before starting Play. With explicit selectors,provide the
approved harbor catalog/hash and memory as usual. Default save is separately placed under
tmp/unity-play/harbor-cycle-aid/<catalog-pin>/game.sqlite;old saves are never repinned.
After hearing acceptance,the NPC opens the gate at its next wake while awaiting a report.
It may reopen a player-closed gate;after hearing completion it stops. An earlier movement
can still be blocked before the same tick's NPC opening;the player moves on the next input.
The board and Korean opening line show committed facts. [Contract/status](../../docs/work_orders/QT-F54_NPC_GATE_ASSISTANCE.md).
QT-F59 adds supply-prioritized aid with `--npc-supply-aid` in both Python clients.
It requires `--npc-memory --npc-cycle --npc-aid` and the approved harbor content.
The NPC waits for at least2communal items at its prior action barrier before opening
the passage. This readiness condition spends no stock;the ordinary4/10supply cycle
continues. In a fresh down1/talk2source,stock reaches2at8and the NPC opens at10;
ordinary consumption at10leaves1. Same-barrier preparation is considered at the next
wake. New mode/save identity;select a fresh working path rather than repinning saves.
Unity accepts `REVERIE_UNITY_NPC_SUPPLY_AID=1` with the same parent flags;unset/0keeps
prior modes,invalid values reject before creating a Brain/save. Its default path is
`tmp/unity-play/harbor-cycle-supply-aid/<catalog-pin>/game.sqlite`.
[Contract/status](../../docs/work_orders/QT-F59_NPC_SUPPLY_AID.md).

QT-F56 aid-mode **NPC 활동 기록** also shows the selected retained segment's total
confirmed NPC gate openings and latest3details. Player openings/current gate state do
not invent history. Previous-load/reconnect follows its selected branch;an open compacted
checkpoint without surviving events displays the explicit empty-history limit.
[Contract/status](../../docs/work_orders/QT-F56_NPC_ASSISTANCE_HISTORY.md).

QT-F58 aid-mode ordinary talk recalls only actual NPC openings after its previous retained
conversation(or explicit checkpoint),with total and latest3details. Same-talk wake
assistance is included;retry does not repeat it. Current local qualification:347affected Python checks,216native checks,13source-preserving
save readbacks and a fresh Windows build pass;standalone/release acceptance stays held.
[Contract/status](../../docs/work_orders/QT-F58_ASSISTANCE_RECOLLECTION.md).
QT-F24 adds **대기 시간** presets1/4/8/16seconds(default1) in the controls scroll area.
Choosing a preset changes only the next **대기** command;other actions keep their existing timing.
Selection is disabled while busy/connecting/failed and retained across load/reconnect in this room.
Retry repeats the original command even after the preset changes. A new room starts at1second.
[Acceptance](../../docs/reviews/QT-F24_EXECUTION_2026-10-16.md).
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
QT-F23 adds a **저장 슬롯** selector for slot01–slot08(default01),shared by save/load/preview.
Selection is local only;it is disabled during a request,connection or failure and retained across
load/reconnect in the same room. A new room starts at01. **slotNN 저장 정보** previews that selected slot.
Saved time,quest progress and registered NPC-memory count appear in the history,while current
stats and attachment stay unchanged. The slot is validated without loading a new branch;an empty
or unusable slot reports an error. Full/recent memory controls share one row to retain history
space. Slot selection does not identify retained working clones or permit deletion.
QT-F38 extends the same selected-slot action in memory modes:the history shows current/saved
times and shared/current-only/saved-only NPC conversation memories. Comparison uses exact
source identities,so distinct report events remain separate even when their kind matches.
This is read-only;it does not load the slot,consume a turn or imply forgetting/eyewitness
combat knowledge. Use **대화 크게 보기** to read the whole comparison.
[Preview acceptance](../../docs/reviews/QT-F20_EXECUTION_2026-10-15.md),
[slot selection](../../docs/reviews/QT-F23_EXECUTION_2026-10-16.md).

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

The controls,focused dialogue and save-manager panel use an opaque backing so board
geometry does not reduce text contrast. Existing panel size,scrolling and controls remain.
[Readability qualification](../../docs/work_orders/QT-F51_PANEL_OCCLUSION.md).

Incoming responses preserve the retained history row being read,including bounded history
eviction. At the bottom,new output is followed automatically;**최신 기록** in the history
header returns to the bottom without a game command. Load resets to the selected branch.

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

QT-F33 work mode extends the existing **NPC 활동 기록** button with a separate verified
production section and current stock. Mixed recent8records remain unchanged. Use
**대화 크게 보기** to read the source boundary,production times and historical/current stock.
No turn is submitted;load/reconnect follows the selected save's retained source. Stock
alone never reconstructs missing events. [Contract](../../docs/work_orders/QT-F33_NPC_WORK_INSPECTION.md).

### Reuse the editor — director preference 2026-10-16

QT-F26 current-host2026-10-18:[native NPC-activity acceptance](../../docs/reviews/QT-F26_EXECUTION_2026-10-18.md).
Actual143checks/2captures/5save readbacks and replays PASS;talk activity,quiet retry,loaded history
and reconnect qualified. Editor stayed open after Play stopped. This closes QT-F25's native gap.
Keep editor logs **outside the working save's parent directory**:Verify requires that parent
empty before starting. A sibling logs/ directory or a working/game.sqlite subdirectory preserves
the guard;use the menu for a new private save when the editor is already open.

Keep Unity open after ordinary local verification. Reuse the open project and choose
**Reverie → Verify Current Selection (Keep Editor Open)** for another run. This uses a new
private working-save directory,retains the selected mode,and stops Play mode on completion.
Do not relaunch the editor merely to repeat unchanged tests. The menu offers to save modified
scenes before preparing the test scene. Keep existing results;never delete saves to obtain freshness.

Success/failure remains explicit:ENGINE_VERIFY_RESULT code=0/1 and
ENGINE_VERIFY_EDITOR_IDLE code=0/1;the last code is retained in SessionState
Reverie.Verify.ExitCode. An open editor or a stopped Play session alone does not prove PASS.
For automated qualification that genuinely requires an editor process exit code,set
REVERIE_UNITY_VERIFY_EXIT=1 before launching the existing Verify methods. Standalone verification
still quits its player. Restart only for measured startup/environment/selection-isolation checks,
an unavailable editor,or a build workflow requiring its own process;state the reason.
Environment variables set in a new shell do not change an already running editor's environment.

The preference reduces startup time and repeated command/log inspection;token savings are not
measured and there is no claimed fixed token charge per Unity restart.

From repository root:

```powershell
$env:PYTHONPATH="$PWD/src"
.\.venv\Scripts\python.exe -m app.engine_project --root C:\ReverieSaga
# Only for this fresh-process automated qualification;ordinary menu runs keep Unity open.
$env:REVERIE_UNITY_VERIFY_EXIT="1"
$env:REVERIE_UNITY_WORKING="C:\ReverieSaga\tmp\unity-verification\run-$([guid]::NewGuid().ToString('N'))\game.sqlite"
& .\tmp\unity-editor\6000.3.25f1\Editor\Unity.exe -projectPath C:\ReverieSaga\clients\unity -executeMethod ReverieSaga.PlaytestBuild.BuildAndVerify -logFile C:\ReverieSaga\tmp\unity-check.log
```

Graphical verification opens the Game window,builds a Windows player and exercises24checks.
In explicit automated exit mode,wait for ENGINE_VERIFY_PASSED and editor exit0,not merely the launcher returning. Fresh empty
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
For that qualification without restarting the open editor,stop Play and use
Reverie → **Build Windows Player (Keep Editor Open)**. It runs the same build/check logic
into a fresh tmp/unity-builds/<GUID>/ReverieSaga.exe and logs ENGINE_BUILD_OUTPUT;
the existing CLI Build destination remains unchanged. This local build does not publish.
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

QT-F21 separates the controls and **행동·대화 기록** into independent scrolling regions.
Scroll over the upper region to reach save/load/retry/recovery and imported descriptions;
scroll over the lower region to read earlier messages. New messages follow the history bottom
without moving the control list. Short windows retain a dedicated history area,and action
buttons use two or three columns according to available width. The title stays visible.
This is a prototype layout repair;human UX acceptance and final HD-2D presentation remain open.
[Current layout qualification](../../docs/reviews/QT-F21_EXECUTION_2026-10-16.md).

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

## Courtyard Compatibility

Set REVERIE_UNITY_SCENARIO=scenario:courtyard for the original PR9 room;scenario:legacy
also retains the original explicit selector. Short current selectors remain supported.
The no-selector approved harbor-memory preset is unchanged. Original qualification:
[PR9 Unity selection](../../docs/reviews/QT-F02_UNITY_SELECTION_2026-10-15.md).

## Recent NPC Self-Activity (QT-F27)

Memory mode adds **NPC 활동 기록**. It retrieves the latest8 own bell/reply events from
verified isolated replay of the current retained save,then displays them chronologically.
No turn,save write or provider call occurs. Existing conversation memories remain separate.
The private pipe adds `activity`;Wire.Generated.cs has the corresponding regenerated pin.
Final native acceptance2026-10-19:169checks/0failures,actual display and5save/replay readbacks PASS;
see the [receipt](../../docs/reviews/QT-F27_EXECUTION_2026-10-18.md). Editor retained after Play stopped.
Long-save latency is unqualified.

## Optional supply-cycle mode (F40–44)

Before launching the editor set `$env:REVERIE_UNITY_NPC_CYCLE='1'` and leave NPC_WORK
unset/0. The approved no-selector harbor-memory preset supplies the required content.
Explicit selections require NPC_MEMORY=1 and the approved harbor catalog/pin. Other values
than unset/0/1 reject;cycle and work are mutually exclusive. The selected mode appears next
to the scenario. Default saves use `tmp/unity-play/harbor-cycle/<catalog-pin>/game.sqlite`;
explicit old-mode saves reject without conversion. Prepare4s/use10s,capacity3,consume before
prepare on ties;four own action memories persist. Existing activity,talk,and current/previous
slot controls inspect or restore them. No live API calls or extra player rewards.
[Contract](../../docs/work_orders/QT-F40_44_NPC_CYCLE_BATCH.md).

### Opt-in answered-call support (QT-F65)

Add `--npc-call-aid` to the existing Python memory/cycle/aid/supply-aid flags.
With the Unity approved harbor preset,set `REVERIE_UNITY_NPC_CYCLE=1`,
`REVERIE_UNITY_NPC_AID=1`,`REVERIE_UNITY_NPC_SUPPLY_AID=1` and
`REVERIE_UNITY_NPC_CALL_AID=1` (work mode unset/0). Invalid values reject before
startup. The NPC may open the passage after an actual answered call,including odd
seconds,when previously available communal stock is at least2and the NPC has heard
acceptance without a completion report. Support spends no stock;routine supply
preparation/consumption continues. The default Unity save directory is the distinct
`tmp/unity-play/harbor-call-aid/<catalog-sha256>/game.sqlite`;older mode saves retain
their pins and reject incompatible selection without overwrite. Existing bell action,
save format and wire envelope are reused. Fresh native/build qualification is deferred
under AWAY-001 while Computer Use remains stopped;Python verification is separate.


### Answered-call native verification preparation (QT-F68)

The development-only verifier now selects CallAidFlow before SupplyAidFlow when
NpcCallAidEnabled is true. The old supply scenario remains specific to its old mode.
With the approved harbor preset and all four cycle/aid/supply-aid/call-aid variables
above set to1,use a fresh empty working directory and the existing PlaytestBuild.Verify
entry point. The dedicated scenario checks calls8/9,exact retry,prior-save preview,
loaded-branch reconnect,calls12/13,and report23followed by suppressed support25.
Activity queries check actual retained call/aid rows and preserve view/save bytes.
The previous slot restores head8with its original retained checkpoint0and call8.
At13the retained total is4while recent rows are9/12/13;at25the total is5while
recent rows are12/13/25. The three-row display cap does not discard older retained
facts. QT-F71corrects these prepared-source expectations;ordinary slot backups and
explicit checkpoint-only clones have different retained-history boundaries.
[Source repair and evidence](../../docs/reviews/QT-F71_EXECUTION_2026-10-27.md).

For negative cases,use a separate fresh working path per case:
REVERIE_UNITY_CASE=invalid-call-aid with call-aid1and supply-aid0 expects
NPC_CALL_AID_CONTENT;invalid-call-aid-selection with call-aid2expects
NPC_CALL_AID_SELECTION. Both require no Brain child and no save. Clear the case selector
and restore the valid flags for the positive scenario. Existing invalid aid/supply cases
remain separate. Follow the editor reuse/input isolation/cleanup workflow above.

This is prepared source and Python scenario evidence only. Fresh Unity compilation,
native execution,captures and Windows build remain NOT_RUN under AWAY-001 while
Computer Use is stopped. Do not treat the Python oracle as native acceptance.

## Optional NPC patrol (QT-F69)

Add `--npc-patrol` to the approved harbor memory/cycle/aid/supply-aid/call-aid
Python client selection. All six older modes keep their existing behavior and save pins.
The patrol variant has a distinct `quest.harbor-call-patrol-v1` identity;incompatible
older selections reject its saves without overwriting them.

The NPC walks between its station and the neighboring communal-work tile on ordinary
NPC wakes. If the player occupies its destination,it stays until a later wake. The NPC
remains nonblocking:the player may enter its current tile. Talk uses the actual current
NPC position before that turn's movement. After it walks away,move nearby to talk again.
Read-only activity/memory/slot inspection does not advance time or move the NPC.
Saved positions restore exactly;within the retained save segment,long waits preserve
actual intermediate movement even when the NPC ends where it began. Supply/call aid
and directly heard quest memory retain their existing conditions and writers.

With the approved Unity harbor preset,set `REVERIE_UNITY_NPC_PATROL=1` together with
`REVERIE_UNITY_NPC_CYCLE=1`,`REVERIE_UNITY_NPC_AID=1`,
`REVERIE_UNITY_NPC_SUPPLY_AID=1` and `REVERIE_UNITY_NPC_CALL_AID=1`;
work mode stays unset/0. Patrol accepts only absent/0/1 and requires call aid before
Brain/save creation. Its default working path is
`tmp/unity-play/harbor-call-patrol/<catalog-sha256>/game.sqlite`.
Existing public `npc_cell` updates drive both Tk markers and the Unity NPC transform;
no wire field/envelope was added.

The prepared development-only PatrolFlow is selected before CallAidFlow. Its positive
scenario checks moving positions/talk range/player-blocked destinations/answered aid,
loaded-branch reconnect and intermediate moves during a16second wait. It compares the
actual NPC transform with the expected public position. Use the existing editor reuse/
input-isolation/verification entry point and a fresh empty working path per case.
For negative cases,`REVERIE_UNITY_CASE=invalid-patrol` with patrol1and call aid0expects
`NPC_PATROL_CONTENT`;`invalid-patrol-selection` with patrol2expects
`NPC_PATROL_SELECTION`. Both require no Brain child and no save. Restore valid flags
and clear the case selector before the positive scenario.

Fresh Unity compilation,native execution,captures and Windows build remain NOT_RUN
under AWAY-001 while Computer Use is stopped. Prepared source and Python/hidden Tk/
framed verification are separate evidence;they do not qualify the native renderer.


### Actual patrol context (QT-F70)

Patrol-mode activity inspection now shows the latest3actual retained moves and their
retained total. Ordinary talk recalls only movements after the previous retained talk,
or after the retained checkpoint when no earlier conversation remains. Same-turn movement
is included once;blocked wakes do not count. Current pose,bells and stock never reconstruct
missing history. A checkpoint-only moved pose explicitly has no older movement;ordinary
slot backups retain their actual older trace. This is derived factual context,not new
permanent memory or an LLM call. Existing message consumers need no new wire fields.
Fresh Unity/native/layout/build qualification remains deferred under AWAY-001.


### Saved patrol position comparison (QT-F72)

Patrol-mode selected-slot preview appends current and saved NPC endpoint labels from
each actual checkpoint. The original work point and neighboring work point are named
without exposing raw cell IDs. Current/previous slots and saves later than a rewound
branch keep their own positions;blocked movement is never inferred from clock parity.
This is a read-only preview and adds no movement or history claim. The older six modes
keep their existing messages. Existing client messages need no new wire fields.
Fresh Unity/native/layout/build qualification remains NOT_RUN under AWAY-001;current
Python/worker/real framed/withdrawn Tk results are separate evidence.
[Scope and verification](../../docs/reviews/QT-F72_EXECUTION_2026-10-27.md).


### Conversation-aware patrol preparation (QT-F73)

Set `REVERIE_UNITY_NPC_TALK_PAUSE=1` with memory/cycle/aid/supply-aid/call-aid/patrol enabled.
The approved harbor preset labels this NPC 대화 대기·순찰·호출 지원·물자·반복 작업·기억 모드
and uses `harbor-talk-patrol/<catalog-pin>/game.sqlite`. Unset/0keeps the older mode;
invalid selectors reject NPC_TALK_PAUSE_SELECTION and missing immediate patrol rejects
NPC_TALK_PAUSE_CONTENT before starting a Brain or creating a working directory.

Only an actual admitted conversation suppresses same-turn movement. A later non-talk
wake resumes;no pause flag is saved. Existing messages/positions/history/slot comparisons
work through the same wire fields. The prepared TalkPausePatrolFlow runs before PatrolFlow
and covers repeated talk holds,real later movement,rejected talk read-only,answered-call
aid,previous-load/reconnect and8actual moves during a16-second wait. Use separate fresh
paths for invalid-talk-pause and invalid-talk-pause-selection negative cases.

This is startup/verifier source preparation and current Python evidence. Fresh Unity
compile/native/render/capture/Windows build remains NOT_RUN AWAY-001. Existing native
flow bodies are preserved;current Python/runtime scope has one2950PASSfull run,not native acceptance.
[Execution status](../../docs/reviews/QT-F73_EXECUTION_2026-10-27.md).


### Own-knowledge quest patrol preparation (QT-F74)

Set `REVERIE_UNITY_NPC_QUEST_PATROL=1` with the approved harbor memory/cycle/aid/
supply-aid/call-aid/patrol/talk-pause selection. The label is
NPC 의뢰 순찰·대화 대기·호출 지원·물자·반복 작업·기억 모드 and the default directory is
`harbor-quest-patrol/<catalog-pin>/game.sqlite`. Unset/0keeps the prior selection;
invalid selectors reject NPC_QUEST_PATROL_SELECTION and a missing immediate talk-pause
parent rejects NPC_QUEST_PATROL_CONTENT before a Brain child or working-save IO.
Use separate fresh paths for invalid-quest-patrol and invalid-quest-patrol-selection.

The prepared QuestPatrolFlow runs before TalkPausePatrolFlow. It waits unheard through4,
hears acceptance6,patrols8,retains the ordinary call aid10,and still patrols after the
unreported enemy defeat16. Report20holds the neighbor position;the occupied home blocks
return through22. Save/load/reconnect retains that physical position and derives the
return from existing own memory. Leaving the home allows return24;wait16to40stays home.
Current talk/activity plans describe intent,not inferred history or a promised deadline.

Current Python/runtime/source scope has one3031PASSfull run;the2sactivity-target miss
remains recorded/global2sOPEN. The startup/verifier sources are prepared
only;fresh C#compile/native/render/capture/Windows build is NOT_RUN AWAY-001 while
Computer Use remains STOPPED. Existing earlier flow bodies remain unchanged.
[Contract](../../docs/work_orders/QT-F74_QUEST_PATROL.md);
[execution](../../docs/reviews/QT-F74_EXECUTION_2026-10-27.md).


### Saved/current quest patrol plan preview (QT-F75)

In the existing quest-aware patrol mode,slot preview now labels the current plan and
the selected save's plan before the physical-position comparison. Equal positions can
have different heard quest knowledge;reported NPCs can still be waiting to return.
Previous-save inspection and loaded-branch reconnect retain their actual selected times.
The preview neither loads a save nor changes either source. Existing eight modes,
authoritative rules,pins,save format and wire are unchanged. Current Python/query scope
is locally accepted with42new in239affected plus static/CI31;unchanged F74engine full
3031is reused,not a new F75whole run. Fresh Unity/layout/build remains NOT_RUN AWAY-001.
[Contract](../../docs/work_orders/QT-F75_QUEST_PATROL_SLOT.md);[evidence](../../docs/reviews/QT-F75_EXECUTION_2026-10-27.md).


## F77answered-call patrol hold source checkpoint

`REVERIE_UNITY_NPC_CALL_PAUSE=1` requires `REVERIE_UNITY_NPC_QUEST_PATROL=1` and its
existing parent selectors. Unset/0 preserves old modes;other strings reject with
NPC_CALL_PAUSE_SELECTION before child/save creation. Missing parent rejects with
NPC_CALL_PAUSE_CONTENT. Default isolated path:tmp/unity-play/harbor-call-pause/<catalog-pin>/
game.sqlite unless an explicit working path is supplied. Reconnect forwards the mode.
Prepared CallPausePatrolFlow checks actual answer/hold,next wake,retry,save/load/reconnect
and source preservation;selection error cases precede ordinary mode dispatch. Source-only
qualification retains all older method text after declared additions are removed.
Fresh Unity compile/native/render/capture/build remains NOT_RUN AWAY-001. Current Python
535related/31boundary/168replay-G07PASS does not establish native or human UX acceptance.
Automatic development is PAUSED;[checkpoint](../../docs/reviews/DEVELOPMENT_CHECKPOINT_2026-10-27.md).
