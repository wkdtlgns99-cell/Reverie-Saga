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
