# Workstation Setup — Laptop and Other PC

Updated:2026-10-13. Installation/discovery SSOT for the two director-owned computers.
Task status:[BACKLOG](../BACKLOG.md);commands:[README](../README.md#verification),
[Unity run/build](../clients/unity/README.md). Source baseline:63670be2.

## Task Entry and Authorization

Current-host closure2026-10-14:[ledger](reviews/OPEN_WORK_CLOSURE_2026-10-14.md). Existing pinned
Python/editor reused;director-approved editorial dialogue and ordinary Unity memory route qualified:
51affected/1664full Python and94native checks/Windows build/release-hook absence PASS. Original
restricted licensing initialization failed;permitted current-host native runs succeeded without
license/security settings changes. Actual original/slot/loaded NPC memories and offline preview
checked. No-selector editor now uses approved harbor-memory preset;[Unity run](../clients/unity/README.md).
This is current-host evidence only;other computer/account tier/release acceptance still open.

QT-F07 director initially deferred live calls2026-10-13;on2026-10-14 supplied keys and authorized
testing now/any time. [Actual qualification](reviews/QT-F07_LIVE_GEMINI_2026-10-14.md):1call/7diagnostic checks PASS. API adapter/CLI uses existing stdlib runtime,
no SDK/dependency install. Director2026-10-14 requested a local .env with three blank Gemini key entries.
Current ignored file:C:/ReverieSaga/.env;GEMINI_API_KEY primary,GEMINI_API_KEY_2/_3 manual spares.
The obsolete empty tmp/gemini-api-key.txt placeholder was removed2026-10-15 during
[local cleanup](reviews/LOCAL_FILE_CLEANUP_2026-10-15.md);use the existing local .env.
The CLI reads only the primary process variable;no auto-load or key rotation was added.
The director can enter the keys there later,then load the primary into GEMINI_API_KEY using the
[README preparation command](../README.md#first-quest--prepared-gemini-dialogue).
Never put key contents into tracked docs,source,chat,logs or review ZIPs. The file is local-only;
the other device requires its own credential setup. Current complete Gemini request/STOP output/local validation PASS;actual project billing/remaining
quota remain UNVERIFIED. This deferred API qualification does not
block deterministic gameplay/replay using approved prepared content.

QT-F07 current-host acceptance2026-10-13:[execution](reviews/QT-F07_EXECUTION_2026-10-13.md).
Same installed tools reused;61native checks/Windows build/release-hook absence PASS;
quest120frames median1.870699ms/p952.767404ms on this host. Offline test-only dialogue catalog.
Live API/other-device/standalone acceptance remains deferred/unverified;no install or login change.

QT-F02 current-host receipt2026-10-13:[execution](reviews/QT-F02_EXECUTION_2026-10-13.md).
Reused Python3.13.12 AMD64/Tk8.6 and editor6000.3.25f1/e1dba0a9aba4;fresh permitted license
status success/active/signedIn=true. Two scenarios11+11,legacy24,corrupt1 native checks and
Windows build/release-hook absence PASS on observed Intel UHD750 host. No installation/version/
license-policy change. Named other-device readiness and new standalone launch remain UNVERIFIED/NOT_RUN.
Sandboxed initialization failure and successful permitted runs are distinct facts in the receipt.

CP03 repair2026-10-13:[current acceptance](reviews/RS-REVIEW-CP03_DISPOSITIONS_2026-10-13.md).
Same installed tools/current-host license reused;current-source47native checks plus Windows
build/release-hook absence PASS. No installation or other-device/standalone qualification change.

Director2026-10-12 authorizes an agent working on either computer to discover local tools,
reuse matching installations,and install missing **approved task-required prerequisites**
before resuming the authorized task. This is an agent procedure,not a background installer.
Read-only chat/document tasks need no Unity install. A note marked DONE on one computer
does not qualify the other. Read AGENTS/rulebook/handoff/backlog and the active order first.

1. Check current repository/path/Git status and the task's required tool versions. Preserve
   unrelated edits;never reset a checkout or existing environment to imitate another machine.
2. Inspect local evidence:project .venv/pyvenv.cfg and executable;PATH/Get-Command;known
   workspace installation paths below;existing Unity Hub editor registrations and standard
   Program Files/Unity/Hub/Editor installations. Inspect already available local receipts/caches
   only as evidence,then probe actual executables. Avoid scanning unrelated private data.
   A custom manual editor can be absent from a CLI/Hub inventory;inspect its actual path.
3. Reuse correct versions at discovered paths. If missing,download the pinned version from
   its official publisher,verify signature/hash as applicable,and install in an owned local
   path. Use verified cached installers when available. Do not upgrade pins/install both
   engines or change security policies as an incidental fix. Follow actual sandbox permissions.
4. Check login/active license on this computer using the installed public CLI or Hub/editor.
   Never infer activation from another device. The director enters credentials/interactive
   account consent personally;continue independent setup while waiting. No paid purchase or
   license eligibility assumption is authorized by this installation request.
5. Verify dependencies and the task's live consumers before claiming readiness. For Unity
   work use the linked graphical/native flow with fresh private save paths;record the machine,
   versions,actual paths,date,commands and PASS/FAIL/UNVERIFIED separately. Heavy jobs run
   sequentially. Reuse unchanged passing evidence within a host/session;do not reinstall
   on every chat or rerun native fault probes for document edits.
6. Any future tool installation/integration must update this document's required-tool table
   and a per-device receipt/pointer in backlog/handoff/Korean progress. State what the other
   computer still needs;never publish tokens,account details,serials or raw private logs.

## Approved Prerequisites

| Tool/data | When required | Version/source and verification |
|---|---|---|
| Git | Source synchronization/publication | Reuse installed Git;inspect remote/status before fetching;no force/reset. GitHub CLI or an authenticated connector only when publication needs it |
| CPython + Tk | Python development/tests or Unity Brain | Windows x64 CPython3.13.12,stdlib Tk locally validated8.6;[official release](https://www.python.org/downloads/release/python-31312/). Verify executable version/architecture/Tk;create a local .venv only if missing;install exact20pins using requirements-dev.lock and --require-hashes per README |
| Unity editor | Current graphical prototype | Exact6000.3.25f1 / e1dba0a9aba4 from tracked ProjectVersion.txt;[official release/installers](https://unity.com/releases/editor/whats-new/6000.3.25f1). Windows x64 editor/Mono player target;verify editor revision/build support and an actual project run |
| Unity authentication/license tooling | If needed to activate/run editor | Reuse working Hub/editor licensing or CLI. Current CLI1.0.0-beta.13;[official CLI instructions](https://docs.unity.com/en-us/unity-cli/use-unity-cli). Match pinned publisher manifest before execution;refresh login/license status locally |
| Unity integration | Unity development | Tracked Assets/meta,Packages/manifest+lock,ProjectSettings and Python bridge;public editor executeMethod/log/capture workflow. No engine MCP/plugin or separate .NET SDK required for this accepted slice |
| Quilltale source | A separately authorized source audit/selection | C:/Quilltale read-only reference;ordinary current prototype uses tracked content/narratives.json and does not need the old checkout. Do not invent/copy missing source or import unqualified templates |
| UE5 / other asset tools | Only a later approved order requiring them | NOT_REQUIRED for the current Unity prototype;not installed/qualified by this request. Add exact version/source/setup/evidence here when actually introduced |

Current clone/run instructions use C:/ReverieSaga and .venv/Scripts/python.exe;the development
player is not bundled/portable. Keep the documented layout on the second Windows machine.
If occupied by unrelated work or another layout is required,inspect real path assumptions
and report the path issue rather than move/delete data or claim portability.

## Verified Local Paths and Installer Witnesses

These are discovery candidates,not proof that they exist on the other computer:

- Python base:C:/ReverieSaga/venv/python-3.13.12;environment:C:/ReverieSaga/.venv.
- Editor:C:/ReverieSaga/tmp/unity-editor/6000.3.25f1/Editor/Unity.exe.
- CLI:C:/ReverieSaga/tmp/unity-cli/unity.exe. The Windows x64 publisher manifest records
 28,111,784bytes,SHA256 9a63636402d8a087e9b67621f31b15fbe0f48eba130a91bdefb88b68aa717b20.
- Official editor installer:[Windows x64](https://download.unity3d.com/download_unity/e1dba0a9aba4/Windows64EditorInstaller/UnitySetup64-6000.3.25f1.exe),
 4,201,959,888bytes;prior execution followed valid Unity Technologies SF Authenticode.
 Local ignored cache:tmp/engine-install/UnitySetup64-6000.3.25f1.exe. Recheck the cached
 binary before any reuse;size alone is not an integrity check.

Use a discovered editor path in the linked commands when it differs. Python .venv must be
created on that host;do not copy another computer's virtual environment. Current base-path
shim warning is recorded in handoff;actual Python runs succeed,so it is not a reinstall trigger.

## Git Transfer Versus Per-Computer State

| Travels through this repository | Must be discovered/created separately on each computer |
|---|---|
| Game source/tests/content,engine project Assets/meta/Packages/ProjectSettings,locks,orders and sanitized evidence | Editor/CLI/Python installations,.venv,package caches,Unity Library/import cache,local configuration |
| Public setup/run instructions and pinned versions | Unity/GitHub login,license activation,account/plugin connections and OS application-control behavior |
| Reviewed snapshots labeled historical | Private saves/builds/logs/captures under ignored tmp;copy saves only under a separately explicit request |

Git pull does not perform installation/login or synchronize ignored/private runtime state.
Keep .gitignore protections and frozen CP02/CP04 archives/witnesses;these new notes do not
refresh historical evidence. A fresh cache/import is expected after first opening Unity.

## Per-Device Evidence — 2026-10-12

| Device/evidence label | Installation | Runtime/license qualification | Next on that device |
|---|---|---|---|
| Current observed Windows host (prior native receipt:Intel UHD Graphics750;director laptop/other-PC mapping unconfirmed) | This turn re-probed Python3.13.12 AMD64/Tk8.6,editor6000.3.25.14801824 matching tracked6000.3.25f1 revision,CLI1.0.0-beta.13 | Prior CP04 receipt:24graphical+1corrupt checks PASS,release-hook absent. Fresh permitted CLI probe:success=true,active=true,signedIn=true. Final standalone launch blocked on this host | Retain working installations;recheck changed login/license state before Unity work;standalone acceptance stays pending |
| Laptop (recorded Lenovo LOQ/Ryzen7/RTX4050 specification,not measured by this turn) | UNVERIFIED as a named device | UNVERIFIED;no copied native/performance/license PASS | Discover/reuse/install required pins,login if needed,verify actual Unity/Brain on first authorized Unity task |
| Other/low-spec PC (director's second device) | UNVERIFIED as a named device | UNVERIFIED;current host may be this device but identity is not established | Same prerequisite discovery/setup;record measured results on that device |

The last two rows are the two intended computers;the first row preserves current evidence
without guessing their identity. Replace the mapping only when established. Never use the
laptop specification as a measurement of this host or transfer its PASS to another computer.
Initial sandboxed license/GitHub probes could not read/use local account state;the permitted
read-only retry confirmed existing Unity activation/login and GitHub authentication. No
credentials were copied and no reinstallation/login was needed on the current host.

Instruction-discovery reference:[OpenAI Docs AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
AGENTS is the entry route;BACKLOG is an explicit linked read,not an installer trigger itself.
