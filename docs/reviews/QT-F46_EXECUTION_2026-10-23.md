# QT-F46 — Cycle-mode player memory execution

Date:2026-10-23. Status:LOCAL_ACCEPTED.
Executor/self-review:current Codex;not independent review.
[Order](../work_orders/QT-F46_CYCLE_PLAYER_MEMORY.md).
Primary4retrieval support;related5/6/7. D2OPEN,CP06held.

## Inputs and change

Entry main6dc918e,clean,synchronized with origin/main after PR14 merge. Actual checkout
C:/Reverie Saga. Existing F31 player_memory_recollection and F40–45 committed records reused.
Only ClientSession._publication changes production behavior:after a new cycle-mode
QuestSpoken,select the current NPC's latest persistent quest statement and append its
existing Korean line after cycle memory. No new replay/IO/command,authoritative mutation,
content/feature/schema/pin/save/wire change or live provider call.

GenerationError is logged and mapped to existing NPC_RECOLLECTION_SOURCE after COMMIT;
worker reports live committed view and preserves retry/save/polling. Unexpected failures
retain existing boundary handling;process-control exceptions propagate. Work-mode recall
and non-cycle views retain their prior paths. Unity verification adds two explicit memory
checks and one real dialogue capture without changing its command vector or production C#.

## Reproduction and Python evidence

Reused installed .venv CPython3.13.12/Tk8.6;no install/settings change. Base Python lacks
mypy;the configured repository .venv has all required packages. Native mypy works here.

| Command/selection | Actual result |
|---|---|
| pytest new test_cycle_uses_original_heard_statement_not_objective_enemy_state,before fix | exit1,1FAIL:expected promise2 but cycle talk returned no player-memory context |
| pytest test_cycle_player_memory.py,first full new run | exit1,6PASS/2FAIL;new fixtures incorrectly treated inventory string keys as Paths and used nonexistent PlayWindow.log. Corrected to root-relative Paths/log_text;no domain outcome changed |
| pytest test_cycle_player_memory.py --basetemp .pytest_cache/qtf46-new-fixed | exit0,8PASS20.68s |
| README shared Ruff and ruff-quality.toml src/tests | both exit0,PASS |
| README scoped format plus new test file | exit0,13already formatted |
| mypy --no-native-parser | exit0,204source files,PASS;initial new-fixture attribute errors repaired |
| Import Linter pyproject.toml / .importlinter-runtime.toml --no-cache | exit0,3+1contracts KEPT |
| pip check | exit0,no broken requirements |
| exact CI rulebook/boundary selection | exit0,31PASS20.02s;process-only exact safe.directory=C:/Reverie Saga,no global Git change |

New cases cover original accepted2/report11 time,unobserved objective defeat,quiet exact
retry,checkpoint-only restoration(two states) with retained-segment access forbidden,
current/previous slot restoration and private branch/restart,unchanged source bytes,
postcommit projection failure/recovery/save/activity,process control,real binary-pipe
new-process route and actual Tk history. Existing pure-selector empty/type vectors reused.

Affected command and retained log:tmp/qtf46/affected.log;selection includes new tests,cycle,
player memory,work/work recollection,cycle-slot/quest-slot comparison,previous recovery,
client,engine bridge,memory-client route and cycle comparison unit tests. Actual exit1:
198PASS/2FAIL267.86s. Both failures are unchanged previous-slot alias fixtures at os.link,
WinError5 sandbox access denied. Permitted rerun of the exact two parameterized cases,
test_missing_corrupt_alias_and_busy_previous_do_not_fallback,exit0:2PASS1.86s;retained
tmp/qtf46/hardlinks.log. No test/production/security modification to obtain that result.
Combined200distinct affected cases qualify;initial environment failures remain recorded.

## Actual Unity and save qualification

Elevated read-only discovery found no running editor. Reused installed
C:/Program Files/Unity/Hub/Editor/6000.3.25f1/Editor/Unity.exe,file6000.3.25.14801824.
Started exactly one editor34400,graphical Verify in cycle mode,exit mode0;license resolved
through existing installation. No restart/install/login/security change. Editor remains open.

- tmp/qtf46/unity.log:80VERIFY_PASS,0VERIFY_FAIL;ENGINE_VERIFY_PASSED and
  RESULT/EDITOR_RETAINED/EDITOR_IDLE all code0. Verified accepted22 and reported31,own
  supply memories,retry,load/reconnect,current/previous save handling,corrupt latest refusal,
  source preservation and private recovery. No extra player reward.
- Actual642x500 cycle-player-report.png inspected:original31second report and explicit
  non-eyewitness wording readable in dialogue focus,alongside retained own supply actions.
  Evidence response/history are siblings under tmp/qtf46/native/evidence/.
- tmp/qtf46/readback.py / readback.json:all9owned managed saves validate,isolated replay
  matches,original memory times/wording and source bytes preserved. Lock sidecars excluded.
  Intentional corruption/refusal is asserted by native flow;final readbacks all validate.
- 9000pure selector samples from actual persisted records:mean0.008217ms,max0.234ms,
  below added-selection TARGET2ms. This measures selection only,not whole UI latency.
- Entry scene restored byte-exact,SHA256
  3157e6272f93a108ce80848f9d1352fdaa15f3ecae3e750e525763818b011b94.

No fresh full regression or Windows build. Historical F40–44full2216PASS/build evidence
applies only to unchanged authoritative and Unity production sources;this receipt's
affected/static/native checks qualify the new presentation wiring. No other-device,
final-art,human UX,MIN-SPEC,standalone release or independent review claim.

## Delivery

Affected/static/boundary/native/save acceptance PASS. Backlog,handoff and Korean progress
updated together. Changed scope:9paths;production behavior only client_session.py;
LiveVerification.cs is editor/development-only evidence. Final UTF-8/local-link/scope
and whitespace checks PASS;owned tmp/qtf46/delivery.json records final path hashes.
No commit,push,PR,merge,agent,external send
or automatic next implementation. Earlier patch rereview stays DEFERRED;CP06 stays held.
