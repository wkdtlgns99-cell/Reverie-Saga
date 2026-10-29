# QT-F87 — Identify the pending query or conversation in the Python player

LOCAL_ACCEPTED2026-10-29;executor local Codex,self-review.
[Receipt](../reviews/QT-F87_EXECUTION_2026-10-29.md). Exactly one further task authorized
after [F86acceptance](../reviews/QT-F86_EXECUTION_2026-10-29.md). Primary5screen/presentation
support;related2truthful command results,6read-only queries,7actual worker/Tk boundary.

| Field | Contract |
|---|---|
| goal/non_goals | Replace generic pending text for talk and four read inspections with a truthful operation-specific Korean message. No new action/state/progress percentage/ETA/history row/replay/IO/worker/wire/native behavior |
| baseline | main5fa348b plus40preserved F82–86paths;F86frozen full3599PASS784.22s. tmp/qtf86/final-inputs.json;tmp/qtf87/client-before.py. All current affected methods call _begin_request with generic 처리 중… |
| prerequisites/read_files | ENGINEERING_RULES,HANDOFF,BACKLOG,Korean progress,MASTER,numbered guide,Sol template,WORKSTATION_SETUP;src/app/client.py:_send/_inspect_*/_begin_request/_poll/close;src/app/client_worker.py actual methods;src/contracts/client.py;tests/integration/test_client.py failure/poll/close fixtures |
| allowed_edit_paths | MODIFY C:/ReverieSaga/src/app/client.py;BACKLOG.md;SESSION_HANDOFF.md;GAME_SYSTEM_SUMMARY_KO.md;README.md. NEW C:/ReverieSaga/tests/integration/test_pending_query_feedback.py;docs/work_orders/QT-F87_PENDING_QUERY_FEEDBACK.md;docs/reviews/QT-F87_EXECUTION_2026-10-29.md. Owned tmp/qtf87/.pytest_cache/f87-* |
| forbidden_paths | All other production/contracts/old tests/goldens/checkers/content/CI/policies/native/reference/user files. Preserve prior40paths/index. No agents/dependencies/security/native/commit/push/goal action |
| public_contract | No changed public DTO/signature. Private _begin_request gains optional message:str with existing default. Existing Futures and polling/close/error boundaries remain the only execution path |
| behavior | Each actual UI caller chooses its pending message and submits the same worker operation once. Set the two existing status fields immediately;disable existing controls. Keep current view/path/history unchanged until actual update. Ordinary actions retain generic pending text. No domain success inferred from pending state |
| edge_policy | Busy reentry ignored;missing data returns existing error status;ordinary failure/cancellation logs/reports CLIENT_ERROR and restores input;process-control propagation and closing behavior unchanged. No new numeric/range/duplicate-ID semantics;existing request validation precedes beginning work |
| examples | talk -> 대화 결과를 확인하는 중입니다.;activity -> NPC 활동 기록을 확인하는 중입니다. 게임 시간은 흐르지 않습니다.;slot -> 저장 슬롯 정보를 확인하는 중입니다. 현재 진행은 유지됩니다.;memory/recent -> NPC 대화 기억/최근 NPC 대화 기억을 확인하는 중입니다. 게임 시간은 흐르지 않습니다. |
| algorithm_steps/wiring | New live Tk tests reproduce absent pending labels first. Add optional private message parameter and choose text at five actual callbacks. Retain default path for attach/save/load/retry/recover/movement. Run source-preserving real worker/Tk success and error/cancellation recovery plus existing client boundaries |
| performance | No new replay/query or timer. Immediate StringVar assignment in existing callback;F86query timings remain valid because every query/worker source is unchanged. No claimed reduction in simulation latency |
| baseline_commands | pytest new success vectors on unchanged client -> five explicit pending-label assertion failures;real worker still executes actual domain/query results |
| verification_commands | pytest new file + tests/integration/test_client.py + reach/call-feedback integration;Ruffboth/format/strict/import3+1/pip/exactCI31;UTF8/local links/input hashes/scope/diff check. Reuse F86full for unchanged shared CORE;no second full for presentation-only change |
| test_responsibilities | NEW test_pending_query_feedback.py exercises actual selected-mode worker/Tk callbacks,delaying only Future delivery;no domain outcomes mocked. Independent expected statuses/readonly ticks/source bytes;exact history/view ownership while pending,busy reentry,normal completion,ordinary Future error/cancellation,next action and shutdown |
| acceptance | All five callbacks immediately display specified text;readonly queries preserve source/tick;real talk commits normally;completion/errors replace pending status and controls/poll/close remain usable. Old generic behavior and all required checks pass;root trio synchronized |
| claude_checkpoints | No new engine/format/ownership/concurrency/public contract;CP01–05not triggered. Independent patch review/CP06/native/device/release holds remain |
| stop_conditions/delivery | Escalate only overlap/new semantic authority/unavailable checks after safe alternatives. English evidence/Korean result;self-review only. Exactly this one next task then stop;no publication/general automatic loop |
