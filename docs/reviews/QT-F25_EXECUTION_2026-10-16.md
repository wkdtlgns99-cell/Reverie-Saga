# QT-F25 — NPC activity on return

Date:2026-10-16 | Executor/self-review | Baseline:b2876a7+RS-TK-001.
Order:[QT-F25](../work_orders/QT-F25_NPC_ACTIVITY_RETURN.md).
State:LOCAL_ACCEPTED. Targeted/static and combined full regression PASS.

## Delivered behavior

Successful committed NPC talk appends system information from that same ClientUpdate.view:
`NPC 활동 현황 · 27초 · 종 13회 · 호출 응답 0회.`
Approved dialogue remains byte-identical. It describes existing committed watcher activity;
no new memory,AI call,simulation rule,clock advance,save/wire field or compatibility identity.
Rejected talk/unrelated actions/exact retries do not append this information.
Primary5 presentation;related2 existing rules,3 approved definitions,6 saves,7 connected flow.

ClientSession._publication detects an actual QuestSpoken in a committed publication,then
appends npc_activity_text(view). ClientWorker and EngineBridge carry unchanged messages[].
Actual Tk log and binary pipe receive the line;unchanged Unity PlayRoom adds these generic
messages to its existing history. Native Unity display of this new line is NOT_RUN;editor
16520 remained open,with no C# changes/rebuild/restart. Do not infer human UX/release acceptance.

## Independent numeric route and actual checks

| Point | Tick/revision | NPC bells | Quest/reward | Memory |
|---|---|---|---|---|
| Down,accept |2/2|1|1/0|accepted2|
| Open,right,down |5/5|2|1/0|accepted2|
| Wait16 while player7,NPC6 |21/6|10|1/0|accepted2|
| Attack,attack,rest,attack |25/10|12|2/0|accepted2,not witnessed defeat|
| Left,report |27/12|13|3/1|accepted2,completion_reported27|
| Exact retry |27/12|13|3/1|identical entries,bytes/view unchanged|
| Gratitude |28/13|14|3/1|identical two entries|
| Load pre-report slot,new window/process |25/10|12|2/0|accepted2|
| Return/report restored branch |27/12|13|3/1|completion_reported27|

The sixteen-second wait emits eight ordered bell messages(counts3..10),covering historical
ticks6,8,...20 under existing two-second scheduling. This is the existing one-room3x3prototype
with player distant from NPC,not camera-visibility/region streaming or general world simulation.
Original completed working save bytes survive branch load/reopen/replay unchanged. Persisted
NPC context labels completion as reported;it does not grant knowledge of unseen combat.

- Before implementation,new expected-line test FAIL1in1.08s;original approved line present,
  new factual line absent. No old expectation was changed.
- New real Tk/second-window/replay journey,actual length-prefixed pipe/second-process restore,
  rejection/reminder/retry checks and text tests:18PASS9.06s.
- Shared/selective Ruff,format14files,strict mypy177files,import contracts3+1 PASS.
- Combined full regression:1971PASS1092.70s(18:12),exit0 in tmp/tk-f25-full.log;
  no warnings,Tcl errors or callback exceptions. Includes existing replay goldens/boundary tests.

Commands use README's PYTHONHASHSEED=0/PYTHONUTF8=1/source-path setup and the original
installation. Full regression runs on the permitted host so existing hardlink tests execute.
Strict types use the same pinned mypy's existing source copy per WORKSTATION_SETUP.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/integration/test_npc_activity_return.py tests/unit/test_client_text.py --basetemp .pytest_cache/qt-f25-flow
.\.venv\Scripts\python.exe -m pytest -q -o faulthandler_timeout=120 --basetemp .pytest_cache/tk-f25-full
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff check --config ruff-quality.toml src tests
# README's scoped format list plus test_tk_runtime.py and test_npc_activity_return.py:14files
.\.venv\Scripts\python.exe -m mypy --no-native-parser
.\.venv\Scripts\python.exe -c "from importlinter.cli import lint_imports_command; lint_imports_command()" --config pyproject.toml --no-cache
.\.venv\Scripts\python.exe -c "from importlinter.cli import lint_imports_command; lint_imports_command()" --config .importlinter-runtime.toml --no-cache
```

The pipe fixture disallows network access through its existing audit hook. No Gemini call or
credential operation. Existing G07 pinned sources,fixtures/catalog hashes and Unity assets are
unchanged. No commit/push/merge/agent/release. D2world autonomy/retrieval/more memories remain
OPEN;this completes one bounded display/connection step toward the adopted village direction.
