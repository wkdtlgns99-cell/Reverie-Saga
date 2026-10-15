# Reverie Saga

An AI-produced HD-2D / 2.5D graphical turn-based RPG in development.
Current implementation:deterministic 3×3 movement,doors,combat/rest,timed NPC/events,
SQLite save/load,recovery,replay,Tk boundary harness and a provisional Unity graphical room.
Not a finished HD-2D graphical game.

## Runtime

When switching computers or resuming a task with local tools,follow [workstation setup](docs/WORKSTATION_SETUP.md):
discover/reuse matching installations,install missing approved prerequisites,and verify on this host.
Git transfers project files,not editors/environments/login/license/private saves.

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

The first QT-F02 unit also supplies a courtyard with different wall,door,enemy,NPC and role
identities through the same rules. Start it with its own working path:

```powershell
$env:PYTHONPATH = "$PWD/src"
.\.venv\Scripts\python.exe -m app.client --scenario scenario:courtyard --working tmp/client-courtyard/game.sqlite
```

Courtyard example:Up → Attack → Attack → Rest → Attack. To reach its door from the starting
cell:Up → Right → Up → Open → Right. Resuming this save requires the same --scenario;
loading a different scenario's slot rejects the mismatch and preserves current progress.
The default is scenario:legacy and retains the existing saves/replays. Both rooms remain3x3
with one door/enemy/NPC;larger worlds and multi-target selection are later work. This selection
is available in the Tk/Python client and Unity through the startup selection below.

## Unity graphical prototype

Unity6000.3.25f1 is installed on the observed host and connected to the same Python Brain.
[Project/run/build/native verification](clients/unity/README.md);6adapted descriptions are loaded
from content/narratives.json. CP04 feedback/repair accepted:24play/failure checks plus1corrupt-save check PASS;
release verification hook absent. Standalone launch is blocked by current-host Windows application control.
Other-device setup/native verification and final-engine/HD-2D release acceptance remain pending.
The2026-10-15 courtyard selection unit has75focused Python/tool checks and editor/release C#
compile PASS. After Hub setup,the pinned Program Files editor recognized Personal and opened
this project with successful initial import/script compilation;earlier exit198 is resolved.
Latest courtyard17/default24/invalid3/corrupt1=45native checks PASS;Windows release build and
verification-hook exclusion PASS. Actual standalone startup/save/shutdown smoke also PASS
on this host. This supersedes earlier blocked launch evidence for this run;small-viewport UI
overlap/human UX,portable packaging and full standalone fault/input acceptance remain pending.
[Current receipt](docs/reviews/QT-F02_UNITY_SELECTION_2026-10-15.md);older CP04 results above
are historical and do not qualify this host's courtyard.

## Verification

```powershell
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

The shared import config includes TYPE_CHECKING imports;the runtime config excludes
them to permit annotation-only sibling cycles. Both are intentional and required.
The source tree is currently run via PYTHONPATH,not an installable package.
Selective E501/PT011 checks cover the changed core/replay/client and rulebook-guard paths;they do not
claim repository-wide complexity cleanup. Windows GitHub Actions runs these native
gates after publication. Patched commit8d90592 [run37581088580](https://github.com/wkdtlgns99-cell/Reverie-Saga/actions/runs/37581088580)
passed all steps and1242tests393.67s;fresh native qualification1242PASS280.99s.
Baseline run37578176533 (commit99786af) failed because the pytest parent was absent;
that historical failure remains recorded,not hidden by the successful repair.
Repair/protection follow-ups:[fact check](docs/reviews/GPT_STRUCTURAL_PLAN_REVIEW_2026-10-07.md).
The [RS-CI-001 repair](docs/work_orders/RS-CI-001_CLEAN_RUN.md) explicitly prepares
that ignored parent and aligns all11formatter targets;local/remote acceptance is recorded
in the linked order,not inferred from the workflow file alone.

The [per-turn rulebook](ENGINEERING_RULES.md) owns execution/repair policy;
[enforcement map](docs/ENGINEERING_ENFORCEMENT.md) distinguishes active checks from review/deferred work.
CI now runs named **Rulebook and integration boundary guards** before full regression:
entry/link/compactness and real Ruff rejection/acceptance probes,SQLite/clone cleanup,
worker/Future/Tk continuation,process-control propagation and atomic/postcommit truth.
The exact small selection lives in [checks.yml](.github/workflows/checks.yml);a missing node
fails collection. To inspect the guard families locally,run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/unit/test_engineering_rules.py tests/integration/test_client.py tests/integration/test_save_slots.py tests/integration/test_durable_turn.py --basetemp .pytest_cache/local-boundaries
```

This broader local selection is distinct from the CI's bounded named selection.
The published workflow at0708483 passed [Native checks37746111893](https://github.com/wkdtlgns99-cell/Reverie-Saga/actions/runs/37746111893):
31focused guards and1270full regression tests,lint/format/strict types/imports all PASS.
See the [session receipt](docs/reviews/SESSION_2026-10-08.md) for exact SHA/evidence;future changes require their own remote acceptance.

## Navigation

- [Agent entry](AGENTS.md),[backlog](BACKLOG.md),[handoff](SESSION_HANDOFF.md),[Korean game progress](GAME_SYSTEM_SUMMARY_KO.md).
- [Every-turn rules](ENGINEERING_RULES.md),[enforcement/residency](docs/ENGINEERING_ENFORCEMENT.md),[engineering contracts](docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md),[product requirements](docs/MASTER_GAME_ARCHITECTURE.md).
- [Implementation template](docs/prompts/SOL_CODING_WORK_ORDER.md),[current quality/client order](docs/work_orders/RS-P1-QUALITY.md),[reference location](REFERENCE_REPOSITORY.txt).
- [Historical backlog](docs/history/BACKLOG_2026-10-07.md),[historical handoff](docs/history/SESSION_HANDOFF_2026-10-07.md):complete pre-compaction records;their old NEXT instructions are not current. Root backlog/handoff contain current state and resume context.

`architecture/` contains design/contracts;`docs/work_orders/` contains bounded orders
and acceptance evidence. Historical v1 material is read-only reference,not active rules.
