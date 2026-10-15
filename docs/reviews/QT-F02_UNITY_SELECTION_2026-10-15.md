# QT-F02 Unity Selection — Execution Receipt

Date:2026-10-15 | Baseline:main1ad22446d48c50b8b72a6d3af8de3c9d775134ea plus preserved
uncommitted first room unit. [Order](../work_orders/QT-F02_UNITY_SELECTION.md).
Self/native evidence only;CP03 DEFERRED for exhausted quota,feedback NOT_RECEIVED.
Latest state:native unit DONE/self-accepted after director's play/build request. Actual45
editor checks,Windows release build/hook exclusion and standalone startup/save/shutdown PASS;
see final native section. CP03 remains DEFERRED;earlier blocked runs retained.

## Changes and boundaries

Canonical checkpoint procedure now requires a new-session root START_REVIEW.md in every
new review ZIP:copyable prompt,exact request,read order,environment route and findings format.
tools/build_cp04_packet.py implements and hashes the entry,accepts --request and rejects
existing archive/witness paths. Original delivered CP03/CP02/CP04 artifacts remain immutable.

Unity startup reads REVERIE_UNITY_SCENARIO;unset/empty selects legacy,courtyard selects its
separate default save. BrainConnection validates generated IDs before launching Python and
passes --scenario to engine_bridge. Current selection and loaded private branch survive
reconnect. Invalid ID fails before child/save IO. Wire DTO/hash and CORE/save format/rules
remain unchanged;only Wire.Generated.cs was regenerated,no narrative compilation/publication.
Editor/development-only verifier covers courtyard and invalid startup;legacy assertions stay.

## Python/tool acceptance

Actual command with PYTHONPATH=src:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/integration/test_review_packet.py tests/integration/test_unity_scenario.py tests/integration/test_engine_bridge.py tests/unit/test_narrative_catalog.py tests/integration/test_scenario.py tests/unit/test_scenario.py tests/unit/test_engineering_rules.py --basetemp .pytest_cache/qtf02-unity-acceptance --tb=short
```

75PASS28.12s,exit0. Includes real pipe subprocess courtyard positions/combat/save/load/retry/
branch reopen,wrong-scenario byte preservation and invalid CLI no-save rejection;existing
default pipe/catalog/Tk/scenario contracts and rulebook guards. Initial packet-tool guards
failed3cases against the old CLI,then3PASS1.57s after implementation. Earlier focused pipe/
packet/catalog suite27PASS6.98s. No mocked domain outcomes or skipped assertions.

Shared Ruff `check src tests tools/build_cp04_packet.py`,selective Ruff config and format
check of5changed Python files PASS. Strict pinned mypy source-mode PASS108files;Import Linter
both configs PASS3+1contracts. Setup/native-module restriction follows
[workstation setup](../WORKSTATION_SETUP.md). Earlier full1330PASS362.34s is reused only for
unchanged CORE/domain/durability/goldens;it is not a new full run of this Unity unit.

## Native qualification

Exact editor6000.3.25f1 was absent;older6000.3.4f1/6000.3.9f1 preserved.
Official installer downloaded4,201,959,888bytes,valid Unity Technologies SF Authenticode;
SHA256 d70a5d8f9a7a463017c056a838fe393c97207f34972732794543c53368bfbf01.
Install target:ignored tmp/unity-editor/6000.3.25f1,installer exit0,file version
6000.3.25.14801824,without OS-policy changes. Setup receipt records the duplicate-start
discovery mistake and denied termination;both installers subsequently completed.
39tracked non-code Unity inputs captured before editor execution;authored C#/README excluded.
Actual graphical launch used the pinned editor with -projectPath clients/unity,
-executeMethod ReverieSaga.PlaytestBuild.VerifyCourtyard and a fresh REVERIE_UNITY_WORKING,
REVERIE_UNITY_SCENARIO=scenario:courtyard. It exited198 before project/game execution:
"No valid Unity Editor license found. Please activate your license."
Log:ignored tmp/qtf02-unity/logs/courtyard-01.log;exit sidecar198. Licensing reports missing
access token/0entitlements;no credentials/tokens are reproduced. Director was asked to log
in/activate Personal through Hub. No license/security checks were disabled or bypassed.

Additional compile-only qualification uses that installed editor's NetCoreRuntime/dotnet.exe,
DotNetSdkRoslyn/csc.dll and shipped unity-4.8-api/UnityEngine/module references:all project
scripts plus Editor/PlaytestBuild with UNITY_EDITOR compile exit0;runtime scripts with no
editor/development define compile exit0. Outputs/response files/logs:ignored
tmp/qtf02-unity/compile/{editor,release}.{rsp,dll,log}. Initial local harness failed decoding
localized diagnostics and then included duplicate facade/module references;fixed the harness
encoding/reference list only. Project C# required no repair. This proves C# compilation,
not editor imports,rendering,play mode,player build or native gameplay acceptance.

Native courtyard/legacy/invalid-scenario/release-build checks remain NOT_RUN because the
editor cannot pass licensing. No ENGINE_VERIFY_PASSED/capture/release-hook result is claimed.
39captured non-code Unity inputs remain byte-identical;no incidental restore was needed.
Earlier runtime input witness117of119remain byte-identical;only the two scoped app bridge/
generator files changed. Earlier full evidence is therefore reused for unchanged CORE only.

## Review and delivery

Director2026-10-15 explicitly deferred CP03 and permitted this bounded Unity continuation.
Fresh [resume request](RS-REVIEW-CP03_RESUME_REQUEST.md) is for a new chat with no prior context.
This does not accept CP03,waive CP05/06 or authorize larger maps,quests,bulk content/rights,
final engine/art/human UX or release topology. Pre-update stash preserved;no agents,external
messages,upload,commit or push. Implementation/tool checks accepted;unit NOT_DONE/native
acceptance BLOCKED on local login/license. Resume only the pending pinned-editor checks with
fresh working paths after activation;no automatic next feature.

Final self-review:source/caller/constant wiring and scope checked;UTF8/fences/local links in
15changed/new documents(238links) PASS,Git whitespace PASS. Historical CP03 archive SHA
3470daf4ed6e67d4ee6e4b42d5f7362f28682271f60e594f8069e59b768f2ef2 and witness SHA
db0322e231db052f02e661fadc90e00a0a992d8f15300c27e9755060087330fd remain unchanged.
Fresh-session packet is a separately named current snapshot with generated root entry and
external digest sidecar;it carries the native blocker rather than claiming full acceptance.

## Director-requested next-step retry — 2026-10-15

Resumed QT-F02 internal step3(client integration),pending native acceptance. Started the
same pinned editor/VerifyCourtyard with a new GUID working path and a distinct resume log.
Actual exit198 again:No valid Unity Editor license found;access token unavailable/0entitlements.
Log:tmp/qtf02-unity/logs/courtyard-resume-20261015.log;matching exit sidecar198. Gameplay,
legacy/invalid-ID verification and player build remain NOT_RUN;no new code acceptance claim.
Next action requires director's local Hub login/license activation per workstation setup;
ordinary next-task authorization supplies no credentials or license eligibility evidence.
No feature expansion,license bypass,source changes or rerun of unchanged Python checks.
Earlier review ZIP/witness/sidecar remain immutable snapshots from before this retry note.

## Project opening after director's Hub setup — 2026-10-15

Director requested opening the registered existing project. Discovered matching editor
C:/Program Files/Unity/Hub/Editor/6000.3.25f1/Editor/Unity.exe,version6000.3.25.14801824;
reused it without reinstalling. No prior editor held the project;Hub's separate serve helper
was not counted as an editor. Started it with correctly quoted -projectPath and a unique
-logFile. Actual log:tmp/qtf02-unity/logs/open-3669c4c22b824330bc26d25b4cf2a6fc.log.
Unity recognized Personal entitlements,initialized6000.3.25f1/e1dba0a9aba4,compiled project
scripts(exit0) and finished Initial Refresh22.169s. No error CS/no-valid-license diagnostics.
PID31948/window responding:unity - Untitled - Windows, Mac, Linux - Unity6.3LTS6000.3.25f1.

This resolves the earlier startup/license blocker for this actual installed editor/host.
It proves project import/compilation/window opening only;courtyard/legacy/invalid-ID play
and release build remain pending. Editor left open for the director;no forced close,scene
replacement or gameplay fault probe in this opening request. Old ZIPs/witnesses remain
immutable earlier snapshots;current evidence supersedes their license-blocked status only.

## Actual play/build acceptance — 2026-10-15

Director explicitly requested completing actual play/build verification. Closed the owned
interactive editor normally after confirming its Untitled window had no dirty marker;no force
close or user save discard. Captured39non-code Unity files under ignored
tmp/qtf02-unity/native-before-d2c50cca056c427c99d37a510b482201. Used the licensed Program Files
6000.3.25f1/e1dba0a9aba4 editor,graphical mode for play,real Python Brain and a fresh GUID save
parent per case. Local runner:tmp/qtf02-unity/run-native.ps1;it sets scenario/case,starts the
public executeMethod,waits for actual exit and records markers/results. Reproduction uses
the same public methods documented in clients/unity/README.md;the ignored runner is optional.

| Case / method | Run suffix under tmp/qtf02-unity/logs | Checks / actual result |
|---|---|---|
| Courtyard / VerifyCourtyard | courtyard-5d262fb2366d4707837ae0d89009a69c | 17PASS/0FAIL,ENGINE_VERIFY_PASSED,exit0 |
| Default legacy / Verify | legacy-a9db839c70e74ae1a2e94d8d4d1e0249 | 24PASS/0FAIL,ENGINE_VERIFY_PASSED,exit0 |
| Unknown ID / VerifyInvalidScenario | invalid-00bd1fddc8e34b04b558a2635626a51d | 3PASS/0FAIL,ENGINE_VERIFY_PASSED,exit0 |
| Fresh corrupt save / VerifyCorrupt | corrupt-8a8d6a062b69475798df6aeeafc0e591 | 1PASS/0FAIL,ENGINE_VERIFY_PASSED,exit0 |
| Release / Build, -batchmode -quit | build-f7d9ff5540254d97a93f8f05e03c64f4 | ENGINE_BUILD_PASSED,RELEASE_VERIFICATION_HOOK_ABSENT,exit0 |

Each suffix has .log and .log.result.json. Corresponding working paths use
tmp/qtf02-unity/runs/<suffix>/game.sqlite. Set REVERIE_UNITY_SCENARIO=scenario:courtyard for
VerifyCourtyard;scenario:unknown for VerifyInvalidScenario;unset for default/corrupt;
REVERIE_UNITY_CASE=corrupt for VerifyCorrupt. All use -projectPath <checkout>/clients/unity,
-executeMethod ReverieSaga.PlaytestBuild.<method> and a distinct -logFile. Never reuse/delete
an existing save parent to satisfy freshness. Graphical methods exit themselves;Build uses -quit.

Courtyard17labels:catalog_loaded,initial_positions,initial_capture,wall_blocks,movement,
attack_counter,load_branch,retry_once,kill_no_counter,defeated_cell_passable,npc_reply,
door_blocks,door_opens,disconnect_visible,reconnect_same_scenario,input_after_reconnect,
final_capture(all prefixed courtyard_). Final literal state:actor2/gate2open/enemy0HP0,
actorHP1/stamina0/NPC8/replies1/tick15/revision15. Legacy24 includes failed load preservation,
malformed pipe child survival,fixed-board guards,in-flight attack crash(pre-or-single commit),
load/retry/kill,committed-branch reconnect and input afterward. Unknown ID:no child/no save;
corrupt case:visible SAVE_CORRUPT. Deliberate Brain-disconnect,UNKNOWN_SCENARIO and SAVE_CORRUPT
exception logs are expected probes,not hidden failures. No source/assertion changes required.

Inspected actual courtyard initial/final PNGs under tmp/qtf02-unity/native/<courtyard suffix>;
legacy screenshots/view/performance are under tmp/cp04-native. Captured Game view642x500:
the existing380px UI overlaps much of the room at this small viewport. Record as a presentation/
human-UX limitation,not final art/layout acceptance;the existing UX_NOT_ACCEPTED gate remains.
Measured120editor frames on NVIDIA GeForce RTX4050 Laptop GPU:median1.523802ms,p95 1.786997ms,
batch_mode=false. This is this prototype/editor sample,not MIN-SPEC or another-device evidence.

Release output:tmp/unity-build/ReverieSaga.exe plus supporting files;reported total89,477,040
bytes. EXE SHA2563070e580e019576b9afcdebfec18d03cebc119f6ae84d597412905c749ad653;
Managed/Assembly-CSharp.dll SHA25633b2da447ffdb3e43d5bc5ee4e9fb048369d692d45291f53b9c517785d3e0874.
Actual Build inspects its emitted assembly and confirms LiveVerification type absent.

Standalone smoke:started that release EXE with scenario:courtyard and fresh
tmp/qtf02-unity/runs/player-30c99c86cb654b3c8ec8a1fa85e91a72/game.sqlite;log with same suffix
under logs. Player responded,one real Python child and valid working save existed;no fatal
or Brain failure. D3D12 info-queue diagnostic0x80004002 was nonfatal. Hidden-window launch
made Process.CloseMainWindow returnfalse;normal taskkill /PID18300(without /F) then delivered
termination and Unity logged subsystem cleanup. Player18300/Brain32284 both exited;no forced
termination. Reopened save through existing ClientSession/courtyard:actor6/enemy0/gate2/NPC8,
HP3/enemyHP5/stamina2/tick0/revision0;file SHA unchanged by reopen. This is standalone startup/
save/shutdown smoke,not a full standalone input/fault suite or portable packaging acceptance.
Unlike historical blocked launches,this exact player started on this actual host;no OS policy
or licensing workaround. Local .venv/source/catalog still required by this development build.

Prepare rewrote only the editor-owned PlayRoom scene. Restored that scene to captured pre-run
bytes;all39non-code inputs now match,source/catalog/locks/goldens unchanged during these runs.
Reuse earlier75Python/tool checks and1330CORE full acceptance for unchanged inputs;no invented
new full run. QT-F02 Unity unit DONE,self/native only;parent IN_PROGRESS,CP03 quota-deferred.
No next-feature activation,external review/upload,agents,commit or push.
All127runtime/test/content/lock/C# inputs in the earlier FRESH_SESSION witness remain
byte-identical. Original and FRESH_SESSION archive/witness SHA256 anchors still match.
Reopened the normal editor after checks,with verification/case/scenario environment cleared.
PID34292 responds with PlayRoom title;log
tmp/qtf02-unity/logs/reopen-after-native-48c2da2a61304d8dbd0d3a572df60efe.log confirms loading
Assets/Reverie/Scenes/PlayRoom.unity and initial refresh completion. Editor left open.
Final15document UTF8/fence/240local-link and Git whitespace checks PASS. A distinct NATIVE
review snapshot refreshes actual evidence;prior archives/witnesses remain unchanged.
