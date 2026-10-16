# CP03 — Verified Static Feedback Repair

Date:2026-10-13 | State:DONE for scoped repair/native acceptance | Executor/reviewer:Sol;self-review
Authority:director-supplied [actual feedback](../reviews/RS-REVIEW-CP03_FEEDBACK.txt),existing
[checkpoint procedure](../ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md#claude-checkpoints-and-defect-repair--director-rule-2026-10-07).
Original295packet inputs rehashed unchanged before repair. HEAD1ad22446 unchanged;preserve all
32prior task-owned dirty/new files and original CP03 witness/ZIP. Feedback SHA256:
31662747c53f5916e7fc2f14a073d452d9decda114d20eeb5d572c2d20de3bfd.

| Field | Contract |
|---|---|
| task_id/title/status | RS-REVIEW-CP03;verify feedback,repair F1–F4 and qualify test gaps;READY |
| goal/non_goals | Reject mismatched selected bindings/spec initialization/exact engine type;correct selected wait name. Preserve legacy defaults,pins,save/goldens;no next feature/bulk/publication |
| prerequisites/read_files | ENGINEERING_RULES,handoff/backlog/Korean summary,QT-F02 contract/receipt/input witness,actual feedback;scenario domain,watch bootstrap,encounter engines,serialization registry,client narration/session;existing scenario/durable/replay tests and README/setup |
| allowed_edit_paths | Under C:/ReverieSaga:MODIFY src/domain/scenario.py,src/app/watch.py,src/engines/encounter.py,src/orchestration/serialization.py,src/app/client_text.py,src/app/client_session.py;NEW tests/integration/test_cp03_repairs.py,this order,CP03_FEEDBACK.txt,CP03_DISPOSITIONS_2026-10-13.md and CP03_REPAIR_INPUTS.json in docs/reviews;MODIFY backlog/handoff/Korean summary,QT-F02 contracts/order,WORKSTATION_SETUP receipt pointer. Ignored new native/test/repaired ZIP evidence under tmp |
| forbidden_paths | Old witnesses/ZIP/source data/goldens/CI/pins/save store/turn driver/dependencies/reference;other user work |
| public_contract | Typed ScenarioConsumer exposes scenario_layout. At RegisteredStateIO boot,ScenarioConsumer registrations in a scenario-pinned bundle must have exact Scenario and canonical definition equal to pinned rules.scenario,else INVALID_SCENARIO_BINDING. Derived comparison avoids second binding SSOT;no assert or simulation-time validation |
| behavior/ownership | Inspect engines,read-adapter delegates,routes,presenters,codecs,patches/checkpoint before registration. Legacy unpinned feature behavior unchanged. Nonlegacy bootstrap initial_cell must match layout,else INVALID_INITIAL_STATE/SCENARIO_INITIAL_CELL. Both frozen encounter engines check exact layout type at construction. Narration adds optional actor_id=legacy actor;live session supplies selected actor;wait resolves through names. F5 generic label intentional for programmatic test layouts;unknown CLI selection still rejects |
| edge_policy/examples | Constructor-skipping harbor/grove extension→boot error before gameplay;legacy equivalent stays valid. Grove default initial0 vs pinned6→reject;explicit6→valid. None/subclass engine layout→SCENARIO_TYPE. names[selected actor]=traveler→selected wait name;legacy defaults preserved |
| algorithm_steps/wiring | Reproduce→small source repairs→targeted boundary/state-preservation tests→README gates/full regression→current-source Unity47 checks/build→verified dispositions/progress/checkpoint closure. No provider/agent call |
| performance | Boot-only static metadata validation;record current-host integration. No new release/device target or inferred improvement |
| baseline_commands | Original295hashes PASS;new reproduction6FAIL1PASS0.96s;Python3.13.12/pip check PASS |
| verification_commands | New repairs+scenario/durable/client/replay tests;README shared/selective Ruff,format,strict mypy,both imports,full pytest;native harbor/grove/legacy/corrupt/build per setup;document/hash/scope checks |
| test_responsibilities | Independently asserted normal/invalid IDs,pin mismatch directions,type/cell/wall boundaries,lexical-role SQLite,uncertain persistence real-store recovery and no repeated execution;no domain-outcome mocks |
| acceptance/checkpoints | Required repairs/test gaps pass;actual static feedback scope preserved,F5 rationale recorded;current-source full/native acceptance. CP03 may close only after dispositions/required repairs accepted;no full independent/runtime review claim |
| stop_conditions/delivery | New unresolved semantics or overlapping user edits require concrete evidence/decision. Report actual failures/results and remaining qualification;no publication/automatic next task |

Acceptance:[verified dispositions/results](../reviews/RS-REVIEW-CP03_DISPOSITIONS_2026-10-13.md).
1360full/133focused/47native/build/hook-absence/Ruff/format16/mypy107/imports3+1 PASS.
Actual static feedback preserved;external patch rereview NOT_RECEIVED. No publication/next task.
