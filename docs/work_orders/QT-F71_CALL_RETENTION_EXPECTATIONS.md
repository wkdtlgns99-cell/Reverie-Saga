# QT-F71 — Correct retained-call expectations in the prepared native verifier

Status:LOCAL_SOURCE_ACCEPTED2026-10-27. Executor:current Codex;local self-review,not independent.
Authority:explicit human `더 해`,original supported goal ACTIVE. Primary7end-to-end
verification support;related2/5/6. No new gameplay or storage behavior.

| Field | Contract |
|---|---|
| task_id/title | QT-F71;repair prepared CallAidFlow retention expectations |
| goal/non_goals | Fix two unexecuted native verifier call totals/source boundaries and independently strengthen its actual Python direct/framed oracle. No production Python,engine,CORE,save/schema/pin/wire/provider/native execution change |
| baseline | HEAD72c2d588d7f64c3e113cf462af35fb673bf82582,branch codex/cycle-call-recall-20261024;all119F70delivery hashes verified,real index0e05744b90eb694a97901c60b41da40dcc2bd4b8e63c0b36268559fe37b82574,staged empty,no live jobs. tmp/qtf71/entry.json and baseline freeze actual inputs |
| prerequisites/read_files | ENGINEERING_RULES,handoff/backlog/Korean companion,SOL template,numbered guide,MASTER2.1Brain/Body,v2.6checkpoint rules,execution policy,WORKSTATION_SETUP/README,deferred memo,F68order/receipt and F70delivery/probe. Actual LiveVerification.CallAidActivity/CallAidFlow/PatrolFlow;test_call_native_scenario.driver/read_activity/test_answered_call_native_scenario_contract;SqliteSlots.export/stage_load full backup helpers |
| MODIFY absolute paths | C:/Reverie Saga/clients/unity/Assets/Reverie/Scripts/LiveVerification.cs;C:/Reverie Saga/clients/unity/README.md;C:/Reverie Saga/tests/integration/test_call_native_scenario.py;C:/Reverie Saga/BACKLOG.md;C:/Reverie Saga/SESSION_HANDOFF.md;C:/Reverie Saga/GAME_SYSTEM_SUMMARY_KO.md;C:/Reverie Saga/docs/DEFERRED_USER_DECISIONS.md;this order |
| NEW absolute paths | C:/Reverie Saga/docs/reviews/QT-F71_EXECUTION_2026-10-27.md;owned ignored C:/Reverie Saga/tmp/qtf71 scripts/logs/saves |
| forbidden_paths | All other code/contracts/engine/CORE/persistence/G07/goldens/tests/README/old orders/receipts/scenes/user files/reference C:/Quilltale. No agents/publication/commit/push/PR/merge/dependencies/window interaction/editor relaunch/native/build |
| public_contract | No public API changes. Existing development-only CallAidActivity(summary,calls,callTotal,aid,checkpoint=0) and Run dispatch unchanged. Change only two CallAidFlow call argument literals. Existing private Python read_activity adds independently supplied call_total:int and asserts checkpoint0heading for this fixed ordinary-slot scenario |
| behavior/ownership | Ordinary slot export/previous load copies the entire retained SQLite trace,not a checkpoint-only reconstruction. Source head8still has checkpoint0and call8. Branch calls9/12/13are additional;at13total4/recent9,12,13. At25total5/recent12,13,25. Cap3trims displayed rows only. Aid openings9/13and prior talk2remain. Retain all existing state/view/source-byte/retry/branch/reconnect/reward/suppression checks |
| edge_policy | This fixed scenario only:totals1at8,2at9,4at13,5at25;checkpoint0through ordinary previous load/reconnect. Empty aid at8remains empty. Ordering chronological and max3as existing. Negative/duplicates/invalid IDs/error codes NOT_APPLICABLE:no new input boundary or runtime algorithm;existing tests unchanged. No general assertion that all saves have checkpoint0;explicit checkpoint-only clones retain their own checkpoint semantics |
| examples | Call8before save survives loaded head8. At13actual retained calls8,9,12,13 => confirmed4/recent3. At25retained8,9,12,13,25 => confirmed5/recent3. Aid source header NPC 의뢰 지원 · 0초 이후 저장 구간의 최근 최대 3건입니다. Wrong totals3/4or source8must fail |
| algorithm_steps | Freeze all prior hashes;record failing prepared-source comparison against independent literal expectations. Add total and boundary assertions to actual full direct/framed scenario. Repair only two native call sites and misleading current Unity usage paragraph. Run affected scenario/static/docs,review exact source diff,prove production/history/index/scene preserved;retain old F68evidence |
| wiring | Existing Run→CallAidFlow→CallAidActivity actual activity messages;Python ClientSession and real framed child through current driver. PatrolFlow and helper body unchanged. Source repair qualifies prepared assertions only,not C#compilation/native behavior |
| performance | No runtime algorithm change or additional production queries;same scenario query count. Target existing10soperation deadline;reuse F70actual short/long timings only unchanged production inputs,not new native or global2sacceptance |
| baseline_commands | Host Git/all119hashes/index PASS;tmp/qtf71/source_oracle.py before repair expected2mismatches/exit1. F70read-only actual F68source25probe checkpoint0/5replies corroborates independent scenario. F70static/CI/imports/pip/full-input subset evidence reused only unchanged inputs |
| verification_commands | README Ruffboth,format44including changed test,strict240 via approved mypy source fallback. Canonical capture=sys pytest tests/integration/test_call_native_scenario.py tests/integration/test_npc_call_aid.py tests/integration/test_call_support_plan.py with owned flat basetemp/JUnit. Engineering document10after docs. Final source oracle PASS;exact native2line diff,all production source and prior non-scope files/index/scene/hash/UTF8/links/diff-check preserved |
| test_responsibilities | MODIFY existing direct+real-pipe native scenario oracle:assert confirmed total and exact retained aid checkpoint at all4existing activity queries while preserving every old assertion. No new mirrored source tests;source oracle is an auxiliary diff check backed by actual gameplay outcomes. Source failure evidence retained |
| acceptance | Actual direct/framed scenario and affected/static/docs pass;at8/9/13/25totals1/2/4/5and checkpoint0. Native exactly two call-site changes,total4/5and default0. Old helper/flows/dispatch and all production Python unchanged. Root trio/English evidence/deferred synchronized. LOCAL_SOURCE_ACCEPTED only;native/build NOT_RUN AWAY-001 |
| claude_checkpoints | CP01–05not newly triggered:repair prepared dev-only assertions under existing contracts,no new boundary/engine/schema/behavior. CP06held,D2/independent rereview/global2s/MIN-SPEC/standalone/release OPEN. Self-review is not independent acceptance |
| stop_conditions | Overlapping edits/unsettled authority pauses dependent work. Physical Escape CUstop remains;do not ask absent user or resume native. Quota state retained;no timed wake absent actual interruption |
| delivery | English order/receipt,Korean category7support summary,actual results/hash manifest/resume. No agents/publication or original-goal completion;continue supported authorized objective |

## Actual acceptance

Source-before2mismatches/exit1;source-after0/exit0. Actual direct/framed full scenario
asserts totals1/2/4/5and source0through ordinary previous-load/reconnect;all old assertions
remain. Related37PASS37.74s(wrapper38.22s),Ruffboth/format44/strict240PASS. Production
Python110unchanged;old test ASTexact after removing only declared total argument and two
assertions. Native binary/text delta exactly two declared call sites. F70input240has239
unchanged/test-only delta;reuse unchanged import3+1/pip/CI31evidence. F69full281has278
unchanged and3deltas(native verifier,prior F70app,test oracle);no fresh whole-run claim.
Initial audit inventory expectation omitted the native source and was corrected;first
failure retained. Final documents/scope/index/scene/UTF8/links recorded in delivery.json.
Fresh Unity compile/native/build NOT_RUN AWAY-001;CU STOPPED;goal ACTIVE.
