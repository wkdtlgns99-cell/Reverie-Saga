# Reverie Saga

An AI-produced HD-2D / 2.5D graphical turn-based RPG in development.
Current implementation:deterministic 3×3 movement,doors,combat/rest,timed NPC/events,
SQLite save/load,recovery,replay,and a provisional 2D playable boundary harness.
Not a finished HD-2D graphical game.

## Runtime

Validated development runtime:CPython3.13.12,Windows AMD64. Ruff/mypy currently
analyze Python3.12-compatible syntax/APIs;this is not a tested Python3.12 support claim.
Existing environment:`.venv`. Fresh setup requires Python3.13.12:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.lock
$env:PYTHONPATH = "$PWD/src"
.\.venv\Scripts\python.exe -m app.durable --working tmp/game.db --create
```

The durable CLI reads framed JSON-line command/export/load/recover requests;
it is a diagnostic interface,not the playable window. Never use `--create`
to replace an existing game. Keep local saves under ignored `tmp/`.

## Play the prototype

```powershell
$env:PYTHONPATH = "$PWD/src"
.\.venv\Scripts\python.exe -m app.client --working tmp/client/game.sqlite
```

Requires stdlib Tk (validated locally8.6). A new path creates the representative
world;an existing path resumes it without overwriting. WASD/arrows or buttons move;
stand beside the door/enemy to interact/attack. Rest restores stamina,not HP.
Wait/NPC call/save/load/retry/recovery are exposed as buttons;the Brain decides outcomes.
Example:Down → Open → Right → Down → Attack → Save → Attack → Rest → Attack.

The bottom Korean action/history panel explains who attacked whom,actual damage,
counterattacks,movement/blockers,rest,NPC responses and rejected actions. It uses
committed facts,not an LLM or predicted outcomes. The read-only scrollable panel
keeps the latest200lines;this display history is not stored in saves. Exact retries
confirm the previous result without repeating attack narration. A successful load
clears the displayed history and identifies the new branch;failed loads preserve it.
Technical schema/status details remain available under the diagnostic checkbox.

Save slots slot01..slot08 retain current/previous generations. Loading creates a
private working clone and changes the attachment token;the window shows its path.
To resume that loaded branch after exit,pass the displayed path to --working.
The original working file remains a separate branch. Closing drains accepted work
and closes SQLite on its single owner thread;game/save work never runs on the Tk thread.
This placeholder tests the boundary,not final HD-2D art/camera/gamepad/MIN-SPEC or release QA.

## Verification

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff check --config ruff-quality.toml src tests
.\.venv\Scripts\python.exe -m ruff format --check src/orchestration/turn.py src/contracts/encounter.py src/engines/encounter.py tests/replay/test_encounter.py src/contracts/client.py src/app/client.py src/app/client_session.py src/app/client_worker.py src/app/client_text.py tests/integration/test_client.py tests/unit/test_client_text.py
.\.venv\Scripts\python.exe -m mypy --no-native-parser
.\.venv\Scripts\python.exe -c "from importlinter.cli import lint_imports_command; lint_imports_command()" --config pyproject.toml --no-cache
.\.venv\Scripts\python.exe -c "from importlinter.cli import lint_imports_command; lint_imports_command()" --config .importlinter-runtime.toml --no-cache
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/local-run
```

The shared import config includes TYPE_CHECKING imports;the runtime config excludes
them to permit annotation-only sibling cycles. Both are intentional and required.
The source tree is currently run via PYTHONPATH,not an installable package.
Selective E501/PT011 checks cover the changed core/replay/client paths;they do not
claim repository-wide complexity cleanup. Windows GitHub Actions runs these native
gates after publication;the configuration is locally checked,remote execution not yet verified.

## Navigation

- [Agent entry](AGENTS.md),[backlog](BACKLOG.md),[handoff](SESSION_HANDOFF.md),[Korean game progress](GAME_SYSTEM_SUMMARY_KO.md).
- [Engineering rules](docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md),[product requirements](docs/MASTER_GAME_ARCHITECTURE.md).
- [Implementation template](docs/prompts/SOL_CODING_WORK_ORDER.md),[current quality/client order](docs/work_orders/RS-P1-QUALITY.md),[reference location](REFERENCE_REPOSITORY.txt).
- [Historical backlog](docs/history/BACKLOG_2026-10-07.md),[historical handoff](docs/history/SESSION_HANDOFF_2026-10-07.md):complete pre-compaction records;their old NEXT instructions are not current. Root backlog/handoff contain current state and resume context.

`architecture/` contains design/contracts;`docs/work_orders/` contains bounded orders
and acceptance evidence. Historical v1 material is read-only reference,not active rules.
