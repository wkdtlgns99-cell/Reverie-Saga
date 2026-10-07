# RS-CLIENT-002 — Korean Action / Dialogue History

State:ACCEPTED/DONE | Date:2026-10-07 | Review:Sol self-review,not independent review
Authorization:director explicitly requested backlog entry and immediate execution;graphics may wait. No engine/asset/provider/dependency/policy/commit/push changes.
Goal:bottom readable,scrollable action/result history in the existing Tk client,not an LLM dialogue system or final graphical client.
Prerequisites:CLIENT-001 accepted;QT-F01 negative feedback recorded;existing immutable publications and durable session.
Baseline:HEAD b0f98e2aa19c5db11d0c746226d4bf321b34dee8;preserve existing dirty changes. Client baseline15PASS4.55s outside sandbox. Two sandbox runs14PASS/1Tk init.tcl setup error despite file existence;same unchanged tests passed natively. Do not suppress/skip that test or alter Tk installation.

## Read / edit scope

- Read:root AGENTS/BACKLOG/SESSION_HANDOFF/GAME_SYSTEM_SUMMARY_KO,canonical quality policy,MASTER Brain/client boundaries,work-order template,client/session/worker/client DTO,encounter/watch/messages/turn contracts and existing client tests.
- MODIFY:src/contracts/client.py,src/app/client.py,src/app/client_session.py,src/app/client_worker.py,tests/integration/test_client.py,README.md,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md,QT-F01 review and this order.
- NEW:src/app/client_text.py,tests/unit/test_client_text.py.
- Preserve domain/engines/orchestration/rules/pins/save codecs/fixtures/lock/CI/AGENTS/shared lint policy. Additive client projection fields are authorized by this feature;they are not persisted CORE/save formats.

## Settled contracts / algorithms

1. Add `ClientUpdate.messages:tuple[str,...]=()` and `reset_log:bool=False`;immutable,derived,worker-to-UI only. Retain status codes/notices for diagnostics and existing callers.
2. App-side pure text formatting reads committed publication facts in their existing order. Use participants and actual HP/stamina before/after,not hardcoded damage or predicted command effects. Reject/abort emits explanation only,never success/action facts. Wait summary uses actual committed tick advance. Internal routing facts are not invented NPC dialogue.
3. Explain move/block reason,gate changes/consuming no-ops,attack/counter/defeat/rest,NPC bell/reply/wait. Prototype names map existing IDs to player/enemy/NPC/door;unknown IDs retain identity. Unsupported records/statuses stay diagnosable,not fabricated success.
4. Translate known rejection/save/recovery/client errors to Korean;retain technical code and debug details. Worker error updates must replace messages and clear reset_log,never repeat stale successful narration.
5. Exact committed retry without new facts adds a confirmation only,not repeated attack/damage or time. Successful save adds slot notice;successful load resets display history and explains the branch change. Failed load preserves history/state. Session reopen starts a fresh display history;history is not a save-file feature.
6. Bottom read-only Text plus scrollbar holds the latest200display lines,each≤500characters. Prefix with current game tick/revision;truncate only derived display history,not authoritative events/replays. Re-rendering the same update instance cannot append twice. Selection/scrolling inside Text must not trigger movement shortcuts.
7. Keep worker ownership and COMMIT-before-narration. Default status label is Korean;technical details are available separately. Invalid wait text adds a useful line without time/state change. No new game rule,LLM call,free-form input or 3D work.

## Independent examples / acceptance

- First attack:playerHP3→2,enemyHP5→3,stamina2→1 → player attacks enemy for2;enemy counters player for1;show actual HP and stamina changes.
- Finishing attack:enemyHP1→0,playerHP1→1 → damage1,defeat,NO counter narration.
- Insufficient stamina/range/occupied door/invalid wait → specific rejection with unchanged CORE/protocol.
- Rest at full stamina/repeated open → report unchanged resource/already-open,time-consuming result,not a fictitious change.
- Save → change → load → earlier state restored and later display messages removed;retry immediately after load reports NO_RETRY,not prior damage. Exact retry after an attack preserves head and produces confirmation only.
- Real withdrawn Tk tests inspect visible text widget content/scrollbar/read-only state,history bounds,duplicate render,keyboard focus and close drain. Pure formatting tests include abort with supplied facts,unknown records/statuses and precise attack values.
- Run focused client/text tests,shared/selective Ruff,formatter on edited/new Python files,strict mypy,both native import-linter configs and full regression. Preserve all old assertions/goldens;no shared CORE changes planned. Use native escalation for Tk only if the same sandbox environment failure persists.
- Document links/UTF8/diff/status synchronization must pass before DONE. Actual desktop capture is supplementary when available;manual UX/final graphics/device/release remain UNVERIFIED unless separately evidenced.
- Stop for unresolved semantics,overlapping unrelated changes,new dependencies,save/CORE changes or unavailable verification after safe alternatives. Routine scoped fixes/retests are authorized.

## Execution evidence

- Added immutable message/reset projection,pure fact-based Korean explanations,postcommit session wiring,error message replacement and bounded read-only UI history. Exact retry confirms only;load starts a clean display branch;unknown diagnostics retain identity. No CORE/save/fixture writes.
- Test-first unit collection failed because the new formatter did not exist. First implementation31PASS7.07s. Added abort-with-facts,unknown event,finishing hit,worker NO_RETRY and log focus/line-bound tests;21new cases relative to the prior15client cases.
- Strict mypy initially caught tuple-length inference in the formatter;explicit `tuple[str,...]` fixed it without Any/suppression. Dependency check initially lacked PYTHONPATH;documented environment resolved it,3+1contracts PASS. Shared/selective lint PASS.
- Tcl setup errors also appeared natively,so the initial sandbox-only diagnosis was incomplete. Minimal twelve raw Tk create/destroy cycles and the failing old test alone passed. GUI fixtures now share one module-owned Tk interpreter with a fresh Toplevel/widgets/worker/save per test;all existing assertions remain. This follows the [official threading guidance](https://docs.python.org/3.13/library/tkinter.html#threading-model);the exact low-level intermittent Tcl cause is not proven. No Tk reinstall/settings/skip/retry suppression.
- After lifetime correction:focused36PASS8.49s and repeat36PASS8.10s;strict mypy96files PASS. Initial full run began before that correction and is not final acceptance. Final regression/visual/document checks pending. Graphics deferred by the director,not removed from MASTER.
- Initial pre-correction full run:1241PASS/1Tcl setup error276.59s. Final corrected full regression is a separate run,not a relabeling of this failure.
- Windows Computer Use inspected the actual desktop and executed Down→Open→Right→Down→Attack→Save→Attack→Load. Visible attack2/counter1/stamina2→1 matched committed values;load restored tick5/playerHP2/enemyHP3 and cleared later combat history while showing the new working path. A subsequent retry input was refused due to user input;automation stopped,no additional interactive retry coverage claimed. Automated retry tests remain PASS.
- Explicit replay modules `test_golden/test_trial/test_encounter/test_watch`:45PASS40.89s. Six UTF8 documents/93local prose links/fences PASS before final status synchronization. Test saves/probe remain ignored;no unrequested cleanup/deletion.
- Final corrected full regression:`.venv/Scripts/python.exe -m pytest -q --basetemp .pytest_cache/client002-final-full`,native execution,exit0,1242PASS283.95s. No skips;21new cases relative to1221. Shared/selective Ruff PASS;all11documented scoped files format PASS;strict mypy96files PASS;type-inclusive dependencies3kept/0broken,runtime siblings1kept/0broken. All7implementation/test SHA256 values stayed unchanged during final verification.
- Acceptance:postcommit narration,attack/counter/defeat values,rejection/no-op behavior,retry/load/error isolation,bounds/focus/read-only widgets,worker lifetime and old regression PASS. Actual desktop rendering/combat/save/load observed;new manual UX satisfaction,final graphics/device/release/remote CI UNVERIFIED. User input prevented interactive retry;no invented coverage.
- Scope:one new app formatter,one new unit test module,four existing client production files and existing client integration tests extended;README/order/review/backlog/handoff/Korean companion synchronized. No task writes to CORE rules/engines/orchestration/save formats/fixtures/lock/shared configs/CI/AGENTS. No providers/assets/dependencies/agents/commit/push. NEXT:QT-F03 documentation compaction;graphics remains deferred by the director.
