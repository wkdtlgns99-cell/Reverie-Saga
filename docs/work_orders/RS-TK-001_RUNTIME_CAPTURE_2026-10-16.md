# RS-TK-001 — Repair Windows Tk test capture

Date:2026-10-16 | State:LOCAL_ACCEPTED | Executor/review:Sol,self-review.
Authorization:director requests root-cause repair of intermittent Tk failures and one next task.
Primary7 verification support;related5/6. No new gameplay semantics.

| Field | Contract |
|---|---|
| baseline | Clean main b2876a72a006f627b2e78268f1c1cd6daf54d341;local branch codex/tk-lifecycle-village-20261016. Read status before edits;preserve all prior sources/pins/evidence/private saves |
| goal/non_goals | Remove reproduced interference between pytest descriptor capture and Windows Tcl initialization. Preserve every test/assertion,real widgets/workers and failure propagation;no retries,Tcl copy,skip,installation or runtime pin change |
| prerequisites/read_files | ENGINEERING_RULES,SESSION_HANDOFF,BACKLOG,GAME_SYSTEM_SUMMARY_KO,README verification,WORKSTATION_SETUP,MASTER3.2–3.4,prompt quality/checkpoints;pyproject.toml,checks.yml,client/client_worker,all six real-Tk test modules |
| allowed_edit_paths | MODIFY C:/Reverie Saga/pyproject.toml,README.md,tests/integration/test_client.py,docs/WORKSTATION_SETUP.md,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md;NEW this order,docs/reviews/RS-TK-001_EXECUTION_2026-10-16.md,tests/integration/test_tk_runtime.py;owned ignored tmp/tk-* diagnostics |
| forbidden_paths | CORE,engines,contracts,save formats,approved content,frozen evidence,installed Tcl/Python,other checkout and credentials. No publication or dependency change |
| public_contract | Runtime APIs unchanged. pytest default capture=sys retains Python stdout/stderr capture without dup2 of process descriptors;explicit capfd users retain their own behavior. Native subprocess callers must retain explicit capture_output/log files |
| behavior/ownership | Keep process descriptors stable throughout Tcl lifetime. Each regression case owns one root/window/worker/fresh save;close and join worker before destroying interpreter. Add attach projection to failed assertion for truthful diagnostics |
| edge_policy | Missing Tcl or actual attach error fails immediately;never retry or convert to skip. Empty/malformed game state stays existing error. Invalid IDs,numeric boundaries/ties NOT_APPLICABLE:runtime contracts unchanged |
| examples | Same original installation:71affected tests→69PASS/1FAIL/1ERROR;30isolated root lifetimes under fd→29PASS/1FAIL;sys→30PASS;standalone100PASS. Failing paths vary init/treeview/menubutton despite existing bytes. Native handle alias mechanism needs evidence distinct from observed capture causality |
| algorithm_steps/wiring | Reproduce minimal root lifecycle;compare fd/sys with identical interpreter;set canonical pytest default used by local/CI commands;qualify independent captured test lifetimes and actual client sequence. Do not add auto-reruns |
| performance | No speed target;record measured elapsed. Same installation/source/config except capture mode in A/B probe |
| baseline_commands | python -m pytest -q four client modules --basetemp .pytest_cache/tk-baseline:1FAIL/69PASS/1ERROR46.82s. tmp/tk-fd-probe.log and tk-sys-probe.log preserve minimal A/B failures/results |
| verification_commands | New lifecycle regression,all Tk consumers,boundary suite;README both Ruff checks,scoped format,strict mypy source mode,both import contracts,pip check;full regression for unresolved cross-suite interference |
| test_responsibilities | NEW test_tk_runtime:independent interpreter/worker/real save lifetimes across separately captured test cases,valid attach/action/shutdown;existing render ordinary/fatal errors and all memory/slot/scenario routes unchanged |
| acceptance | No original-path errors in new lifecycle/all-Tk/full suite;no retry/copy env;explicit projection diagnostic on attach;static checks pass;record scope/platform limits |
| claude_checkpoints | NOT_APPLICABLE:repair test infrastructure without gameplay/public wire/save changes;CP01–05 bounded closures retained,V3 stopped,CP06 release held |
| stop_conditions/delivery | New evidence contradicting capture diagnosis requires investigation;do not claim all Tk causes fixed from a passing retry. Record exact commands/results/limits in receipt and synchronize3progress docs before next bounded task. No commit/push/merge/agents |

Acceptance:[execution receipt](../reviews/RS-TK-001_EXECUTION_2026-10-16.md).
Original installation121affected PASS;final integrated1971PASS1092.70s/exit0/static PASS.
