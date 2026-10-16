# QT-F16 — NPC Conversation Memory Inspection

Date:2026-10-15 | Status:LOCAL_ACCEPTED | Review:self-review,not independent Claude feedback.
Order:[QT-F16](../work_orders/QT-F16_NPC_MEMORY_INSPECTION.md). Primary5;related2/6.
Director explicitly continues implementation while Claude V3 remains pending.

## Behavior / Live Wiring

Memory-enabled Tk has an NPC conversation-memory button. It queues ClientWorker.inspect_memory,
uses ClientSession's existing committed snapshot on the SQLite owner thread,and returns existing
ClientUpdate messages to the ordinary Tk poll/render/bounded history path. No command is submitted.
Only this player's two already recorded conversations are displayed:heard acceptance and received
completion report,with logical game seconds. Received report is explicitly not eyewitness death.
Empty history is explicit. Slot load/new worker resume use the actual attached branch.
Inspection before attach returns NPC_MEMORY_UNAVAILABLE without creating/opening a game;disabled
mode also returns an explicit error. Ordinary failures log and remain recoverable;process-control
exceptions propagate. Busy/close disables the button;polling and subsequent input remain functional.

## Baseline / Scope

HEAD:e32cf3e08a44d327b7ed091650bec7f74716676f. Entry:only BACKLOG.md,SESSION_HANDOFF.md,
GAME_SYSTEM_SUMMARY_KO.md dirty from local pause;their notes are retained. Tracked byte inventory:
tmp/qt-f16/entry.json. Existing Windows AMD64 CPython3.13.12/Tk8.6/SQLite3.50.4 reused;
pytest9.1.1/Ruff0.16.6/mypy2.4.0/import-linter2.15. No installation/dependency change.

Four app sources changed;one new integration module,order/receipt,README and three progress docs.
All other tracked production/contract/engine/fixture/golden/lock/Unity/content files byte-identical
to entry. Existing ClientRequest/ClientUpdate and pipe fingerprint remain unchanged;no new remote
request registered. Current pipe fingerprint:b7b0820833f1e644fc946ff3a7e4c5544eb3efffd03c81f21feaef50d078b069.

## Commands / Evidence

Use .venv/Scripts/python.exe from C:/ReverieSaga. Pytest sets PYTHONHASHSEED=0,
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1;native import CLI uses PYTHONPATH=C:/ReverieSaga/src.

| Actual check | Result |
|---|---|
| Baseline `-m pytest -q tests/integration/test_memory_client_route.py tests/unit/test_client_text.py --basetemp .pytest_cache/qt-f16-baseline --junitxml tmp/qt-f16/baseline.xml` |20PASS6.33s |
| Final `-m pytest -q tests/integration/test_client_memory_inspection.py tests/integration/test_client.py tests/integration/test_memory_client_route.py tests/integration/test_engine_bridge.py tests/integration/test_npc_memory.py tests/integration/test_quest.py tests/unit/test_client_text.py tests/unit/test_engineering_rules.py --basetemp .pytest_cache/qt-f16-final --junitxml tmp/qt-f16/final.xml` |126PASS44.24s;0fail/error/skip |
| `-m ruff check src tests`;`-m ruff check --config ruff-quality.toml src tests` |both exit0 |
| README scoped `-m ruff format --check` plus new integration module |13files formatted/exit0 |
| `-m mypy --no-native-parser` |158files/exit0 |
| README native import CLI,pyproject.toml then .importlinter-runtime.toml,--no-cache |3+1contracts KEPT/exit0 |
| `-m pip check` |no broken requirements/exit0 |

Final static command argv/exits/log hashes:tmp/qt-f16/static.json and individual logs.
Delivery byte/UTF8/link witness:tmp/qt-f16/delivery-checks.json;403protected tracked files unchanged,
11delivery files decode as UTF8,12added local links resolve;git diff --check exit0. Original HEAD
unchanged;Git's two existing CRLF checkout advisories do not report whitespace errors.
New15cases cover empty/accepted/unreported victory/reported states;exact snapshot/protocol/file/
trace preservation,original retry/no duplicate reward,older slot/new worker resume,disabled and
unattached queries,thread ownership,error recovery,process-control and real Tk use. Three native
Tk cases exercise memory/non-memory visibility and real button→worker→log,disabled busy/close,
load history reset,error recovery and continued input. These use actual approved tracked content,
real Brain/SQLite/Tk,no mocked domain outcomes. Withdrawn Tk proves widget/callback behavior,
not human visual acceptance or Unity functionality.

## Diagnostics / Limits

First new-test draft:5FAIL/5PASS6.40s;second:3FAIL/7PASS6.48s. New expectations incorrectly
assumed retry has no acknowledgement and unavailable status omits its diagnostic suffix;
corrected only new expectations to existing client contracts. Original tests/goldens unchanged.
Initial selective Ruff found one101-character line;split/grouped prose fixed it. Initial direct
import CLI lacked PYTHONPATH and could not find app;explicit documented source path fixed both
invocations. Intermediate124PASS43.23s preceded self-review's no-create-before-attach guard;
final126PASS qualifies that guard and two additional independent cases. Earlier diagnostics remain
in their own JUnit/tool output;not represented as a first-run all-green result.

Shared CORE unchanged;full suite not rerun for this bounded presentation task. Unity/native build,
Linux,live provider,new CI and human UX NOT_RUN. No provider/key/ledger/network/admin/agent/Git
publication action. V3all-source Claude review remains pending at published e32cf3e;this local patch
is outside that snapshot/CI and has no independent review. CP06release held. Existing NPC memory
remains two scoped records,not five-level cognition/personality/relations/vector retrieval.
