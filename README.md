# Reverie Saga

AI-produced HD-2D/2.5D graphical turn-based RPG in development.
Current prototype:Python deterministic rules,3x3rooms,combat/NPC events,one quest,two NPC conversation
records,SQLite save/load/recovery/replay,Tk and provisional Unity. [Current status](BACKLOG.md).

## Runtime

Commands run from `C:\Reverie Saga` in PowerShell. Reuse local `.venv`;for another computer
follow [workstation setup](docs/WORKSTATION_SETUP.md). Git excludes tools,licenses,keys and private saves.
Validated host:CPython3.13.12 x64,Tk8.6;Ruff/mypy target3.12syntax,not tested3.12runtime support.

Fresh environment only:
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.lock
$env:PYTHONPATH = "$PWD/src"
```

## Play the prototype

Basic Tk room:
```powershell
$env:PYTHONPATH = "$PWD/src"
.\.venv\Scripts\python.exe -m app.client --working tmp/client/game.sqlite
```

A new path creates a game;an existing path resumes it. WASD/arrows/buttons move;stand beside
doors/enemies/NPCs to interact. Rest restores stamina,not HP. Add `--scenario harbor` or
`--scenario grove` with a separate working path for the other embedded rooms.

In Tk,press Return or keypad Enter while editing the wait-time field to run the existing wait action.
The accepted range remains1–16game seconds;invalid input keeps the current progress.
Repeated identical invalid-text errors occupy one adjacent log entry,so they do not evict gameplay history.

Approved harbor quest+NPC memory:
```powershell
$taskDialoguePin=(Get-Content -LiteralPath content/dialogue/harbor-memory-v1.sha256 -Raw).Trim()
.\.venv\Scripts\python.exe -m app.client --working tmp/client-harbor-memory/game.sqlite --scenario harbor --quest-catalog content/dialogue/harbor-memory-v1.json --quest-sha256 $taskDialoguePin --npc-memory
```

| Control / state | Behavior |
|---|---|
| Quest | Accept→defeat→report→one favor;ordinary turns use prepared approved text without API calls |
| NPC memory | Full/recent conversation inspection;reported evidence remains distinguished from direct observation |
| Slot info | Preview saved metadata;current stats/retry remain current |
| Save/load | slot01..slot08;load creates a private branch and clears later display history. Resume using displayed working path and original scenario/catalog/memory selectors |
| History/retry | Latest200lines,not persisted display history;exact retry does not repeat gameplay or narration |
| Close | Drains accepted work;SQLite/session remains owned by worker thread |

Tk history follows new output while at the bottom. Scroll up to keep reading the same
retained record as messages arrive;evicted records yield to the oldest remaining record.
Click `최신 기록으로` beside the history heading to return to the bottom and follow new output.
Loading a save resets history and returns to the latest output.

In NPC-memory modes,selected-slot information also compares that slot's memories with
the current game:shared,current-only and saved-only conversations,with their actual times.
Differences describe save/branch history,not NPC forgetting;received reports remain distinct
from witnessed events. Inspection does not load a branch or advance the game.

Successful harbor NPC conversations include committed activity counts in the action log.
They use the restored save's current state;exact command retries do not repeat the line.
The bounded return/report/save/restart route and its limits are recorded in
[QT-F25](docs/reviews/QT-F25_EXECUTION_2026-10-16.md).

## Unity graphical prototype

[Unity play/build/native verification](clients/unity/README.md):editor6000.3.25f1.
No-selector Unity starts the approved harbor-memory preset in a catalog-pin-specific save directory;
explicit legacy/scenario/quest selectors preserve their existing modes.
Independent control/history scrolling is qualified at1101x506on the observed host.
Human UX,final art/camera/engine,gamepad,MIN-SPEC,portable standalone and other-device acceptance remain open.

## First quest / prepared Gemini dialogue

[CLI workflows](docs/CLI_WORKFLOWS.md) contain key loading,explicit preparation,offline review/approval/
compilation,NPC context,query export/check/comparison and plan-based generation.
Normal play needs no key/network. New generated content stays NEEDS_REVIEW until actual director approval;
existing games retain their content pins. [Current qualification limits](BACKLOG.md#qt-f07-deferred-qualification).

## Verification

Unity **저장 관리** opens a dedicated slot01–08 panel with current/previous save
inspection and explicit previous-save loading. Overwriting a valid slot retains one
previous save. Loading either version continues in a private working branch and preserves
both source files;corrupt latest saves never trigger automatic fallback. Inspect the
previous version,then choose **이전 저장 불러오기** when recovery is wanted. Missing or
invalid backups report their own errors. The panel blocks movement keys while polling
continues;Escape closes it. Selection and panel mode survive load/reconnect.
[Contract](docs/work_orders/QT-F39_SAVE_MANAGER_RECOVERY.md).

QT-F28 adds an explicit harbor NPC work mode. It prepares one communal supply at logical
seconds4/8/12,then stops at capacity3. Travel/combat time counts;wall time does not.
Talk shows committed stock;NPC activity and slot preview remain read-only. No player inventory
or extra quest reward is granted. Existing modes/saves are never upgraded.

```powershell
$questPin = (Get-Content content/dialogue/harbor-memory-v1.sha256 -Raw).Trim()
$env:PYTHONPATH = "$PWD/src"
.\.venv\Scripts\python.exe -m app.client --scenario harbor --working tmp/npc-work/game.sqlite --quest-catalog content/dialogue/harbor-memory-v1.json --quest-sha256 $questPin --npc-memory --npc-work
```

Use a fresh work path;an older memory save intentionally rejects with UNSUPPORTED_RULESET.
[Work contract](docs/work_orders/QT-F28_NPC_PROVISIONS.md).

QT-F40–44 adds a separate optional supply-cycle mode. In the command above use a fresh
`tmp/npc-cycle/game.sqlite` and replace `--npc-work` with `--npc-cycle` (keep `--npc-memory`).
The NPC uses one communal supply every10 logical seconds and prepares one every4 up to3;
at a tie it uses before preparing. Player rewards are unchanged. The latest four actual own
work memories and cumulative counts persist across checkpoint,save/load and reconnect.
Talk/activity show those stored anchors;slot previews explicitly label saved memories.
The header shows the selected mode. Old work/memory saves retain their original identities;
cycle mode rejects them unchanged. [Batch contract](docs/work_orders/QT-F40_44_NPC_CYCLE_BATCH.md).

QT-F45 cycle-mode slot previews also compare current/saved own work memories by actual
causal source and within-wake sequence. Common/current-only/saved-only groups preserve both
consume/prepare actions at a tied second. Each snapshot retains only its latest four own
actions;the view labels that scope and cumulative totals. Missing entries do not prove an
action never occurred or that the NPC forgot. Current/previous previews remain read-only.
[Comparison contract](docs/work_orders/QT-F45_CYCLE_SLOT_MEMORY_COMPARISON.md).

QT-F46 cycle-mode conversations also recall the newest persistent player quest statement:
the heard promise or received completion report,with its original game time. Enemy defeat
alone does not become a received report or eyewitness memory. Restoring an older save
selects that branch's memories;retry adds no duplicate context. This reuses existing
committed anchors without another replay or live API call.
[Recall contract](docs/work_orders/QT-F46_CYCLE_PLAYER_MEMORY.md).

QT-F47 cycle-mode **NPC 활동 기록** keeps those persistent supply memories and also shows
the selected save segment's latest eight bell/reply events,verified through one isolated
replay. It labels the source checkpoint boundary;missing retained events are never rebuilt
from cumulative counters. Inspection advances no time and preserves source files/retry.
[Activity contract](docs/work_orders/QT-F47_CYCLE_SELF_ACTIVITY.md).

QT-F29 work-mode dialogue also recalls the NPC's verified production since the previous
retained conversation. Work is collected separately from frequent bell events,so those
events do not hide production. Only actual retained facts are recalled;missing earlier
history is labeled as the current saved segment. Same-turn production is included once;
retry adds no duplicate recall. This adds no new save/rules/wire format or live API call.

QT-F30 adds answered-player-call recollection to that same work-mode return dialogue.
It follows actual request→echo→response event identities,shows the range's confirmed
response count and most recent3,and survives save/load/reconnect. Frequent periodic bells
cannot hide these calls;missing checkpoint history is never reconstructed from counters.
Work and call context share one verified replay. [Contract](docs/work_orders/QT-F30_NPC_CALL_RECOLLECTION.md).

QT-F31 return context also selects the newest persistent player statement:the heard quest
promise or received completion report,with its original time. Objective enemy defeat alone
does not become a received report or eyewitness memory. These existing CORE anchors survive
retained-trace truncation;work/call evidence keeps its explicitly retained-history boundary.
[Contract](docs/work_orders/QT-F31_NPC_PLAYER_MEMORY.md).

QT-F32 Unity **대화 크게 보기** expands NPC history within the existing window. The fixed
header button or Escape restores controls;movement keys are suppressed while reading.
This is local presentation only,preserving turns/save data and ongoing response polling.
[Contract](docs/work_orders/QT-F32_DIALOGUE_FOCUS.md).

QT-F33 work-mode **NPC 활동 기록** keeps a separate retained production section after
the unchanged mixed recent8activities. Repeated bells cannot hide verified work4/8/12;
the final line shows current committed stock. A compacted checkpoint may retain stock
without old work events:the display states that limit instead of inventing history.
Inspection shares one isolated replay,advances no time,and preserves saves/retry identity.
[Contract](docs/work_orders/QT-F33_NPC_WORK_INSPECTION.md).

Use the applicable order for affected tests;shared CORE changes require full regression.
The environment setup below applies to all commands,including both import checks.
```powershell
$env:PYTHONPATH = "$PWD/src"
$env:PYTHONHASHSEED = '0'
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff check --config ruff-quality.toml src tests
.\.venv\Scripts\python.exe -m ruff format --check src/orchestration/turn.py src/contracts/encounter.py src/engines/encounter.py tests/replay/test_encounter.py src/contracts/client.py src/app/client.py src/app/client_session.py src/app/client_worker.py src/app/client_text.py tests/integration/test_client.py tests/unit/test_client_text.py tests/unit/test_engineering_rules.py
.\.venv\Scripts\python.exe -m mypy --no-native-parser
.\.venv\Scripts\python.exe -c "from importlinter.cli import lint_imports_command; lint_imports_command()" --config pyproject.toml --no-cache
.\.venv\Scripts\python.exe -c "from importlinter.cli import lint_imports_command; lint_imports_command()" --config .importlinter-runtime.toml --no-cache
New-Item -ItemType Directory -Path .pytest_cache -Force -ErrorAction Stop | Out-Null
if (-not (Test-Path -LiteralPath .pytest_cache -PathType Container)) { throw 'Pytest temporary parent is not a directory' }
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/local-run
```

Shared imports include TYPE_CHECKING;runtime imports exclude it. Both checks are required.
Pytest uses `--capture=sys` from pyproject.toml. Keep this default for Windows Tk tests:
descriptor capture replaces native standard handles between test phases and reproduced
false missing-Tcl-file errors. Python output remains captured;subprocess checks capture their
own output explicitly. Do not retry,skip,copy Tcl libraries or override with `--capture=fd`.
Root-cause evidence:[RS-TK-001](docs/reviews/RS-TK-001_EXECUTION_2026-10-16.md).
Source mode uses PYTHONPATH;the project is not an installable package.
[CI](.github/workflows/checks.yml) owns the exact named boundary selection;
[enforcement map](docs/ENGINEERING_ENFORCEMENT.md) distinguishes active/deferred guards.
For a broader local boundary run:
```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/unit/test_engineering_rules.py tests/integration/test_client.py tests/integration/test_save_slots.py tests/integration/test_durable_turn.py --basetemp .pytest_cache/local-boundaries
```

## Navigation

| Need | Read |
|---|---|
| Agent/session entry | [AGENTS](AGENTS.md)→[rules](ENGINEERING_RULES.md),[handoff](SESSION_HANDOFF.md),[backlog](BACKLOG.md) |
| Product/architecture | [MASTER](docs/MASTER_GAME_ARCHITECTURE.md),[engineering prompt](docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md),[numbered structure](docs/GAME_STRUCTURE_GUIDE_EN.md) |
| Task contracts/evidence | [order template](docs/prompts/SOL_CODING_WORK_ORDER.md),docs/work_orders/,docs/reviews/ |
| Human progress | [Korean companion](GAME_SYSTEM_SUMMARY_KO.md) |
| Past commands/results | [README snapshot](docs/history/README_2026-10-16.md);historical instructions are non-operative |

## PR09 Integration

Preserve the courtyard room and its V1 rules/save identity through the shared current layout path.
Original [room evidence](docs/reviews/QT-F02_ROOM_BINDINGS_2026-10-15.md) and
[Unity evidence](docs/reviews/QT-F02_UNITY_SELECTION_2026-10-15.md) remain historical;
[PR08 repair](docs/reviews/PR08_CI_REPAIR_2026-10-16.md) records current integration acceptance.
