# QT-F72 — Compare current and selected saved NPC patrol positions

Status:LOCAL_ACCEPTED2026-10-27. Current Codex;local self-review,not independent.
Primary5presentation support;related2/6/7. Explicit human `더 해`;original goal ACTIVE.

| Field | Contract |
|---|---|
| goal/non_goals | Existing selected-slot preview shows the current and saved NPC patrol endpoint. No authoritative behavior/history/prediction/LLM/public API/engine/CORE/schema/pin/save/wire changes |
| baseline | HEAD72c2d588d7f64c3e113cf462af35fb673bf82582,branch codex/cycle-call-recall-20261024;121F71delivery hashes and index0e05744b90eb694a97901c60b41da40dcc2bd4b8e63c0b36268559fe37b82574 verified;staged empty,no live jobs;tmp/qtf72/entry.json and baseline/src |
| prerequisites/read_files | ENGINEERING_RULES,handoff/backlog/Korean summary,numbered guide,Sol template,MASTER2Brain/Body/NPC state,execution policy,WORKSTATION_SETUP/README,F69patrol/F70recollection/F71delivery. Actual ClientSession.inspect_slot/_record,domain.npc_patrol.patrol_cells,domain.watch.WatchNpcRecord;F69saved-moving-position test and support-slot comparison tests |
| MODIFY absolute paths | C:/Reverie Saga/src/app/client_session.py;C:/Reverie Saga/clients/unity/README.md;C:/Reverie Saga/BACKLOG.md;C:/Reverie Saga/SESSION_HANDOFF.md;C:/Reverie Saga/GAME_SYSTEM_SUMMARY_KO.md;C:/Reverie Saga/docs/DEFERRED_USER_DECISIONS.md;this order |
| NEW absolute paths | C:/Reverie Saga/tests/integration/test_patrol_slot_position.py;C:/Reverie Saga/tests/unit/test_patrol_slot_position.py;C:/Reverie Saga/docs/reviews/QT-F72_EXECUTION_2026-10-27.md;owned ignored tmp/qtf72 scripts/evidence/saves |
| forbidden_paths | Other code/engine/CORE/contracts/goldens/G07/C#/scene/old tests/orders/receipts/README/governance/user files/reference C:/Quilltale. No agents/publication/dependencies/native/window/editor operations |
| public_contract/wiring | ClientSession.inspect_slot signature/update/status unchanged. Add a private module formatter _patrol_slot_messages(saved:CoreSnapshot,current:CoreSnapshot,layout:Scenario)->tuple[str,...]. Call only when self._npc_patrol inside existing cycle preview,after support plan,using the already inspected selected checkpoint and existing current checkpoint. Existing worker/Tk/framed/Unity message consumers receive ordinary messages;no transport field changes |
| behavior/algorithm | For each actual checkpoint independently,require exactly one exact WatchNpcRecord for layout.npc_id;require actual same space and exact-int cell in canonical patrol_cells(layout,True). Format its endpoint label. Do not derive pose from tick,bells or history;equal poses may have different histories. No new replay/restore/query/IO/cache. Log ordinary SaveError at the slot boundary and propagate SAVE_INSPECT_FAILED |
| exact text | NPC 순찰 위치 비교 · 현재 {current.tick}초 / 선택 저장 {saved.tick}초;현재 NPC 위치 · {label};선택 저장 NPC 위치 · {label}. First canonical endpoint label 원래 작업 지점입니다.;second 옆 작업 지점입니다. Append exactly3lines,old messages/order unchanged |
| edge_policy | Missing/duplicate NPC,foreign-space,unknown cell,bool/float cell reject SAVE_INSPECT_FAILED;no partial update or mutation. Other NPC records ignored. Current/saved can share tick/pose or selected save can be later after rewind;label each actual snapshot,do not infer a difference or history. Six older modes add no messages. Empty slot/bad rules retain existing errors before formatter. Numeric units integer game seconds;ordering current then selected;RNG/duplicate actions NOT_APPLICABLE:read-only projection |
| examples | Save2with NPC7;current4NPC6:current 원래/selected 옆. Current slot4and previous2must differ. Load previous2then inspect current slot4:current 옆/selected 원래,ticks2/4. Occupied destination may leave NPC7at4;must show옆despite even-tick parity. No movement history claim from pose |
| algorithm_steps | Public missing-output baseline2tests first. Add private formatter/canonical bounds and one guarded existing caller insertion. Unit source/reference failures;actual direct/framed current/previous/rewind/restart/read-only/retry/blocked position and old-mode checks. Review normalized module AST and precise scope;update root trio/receipt/deferred after acceptance |
| performance | Zero additional replay/IO/query;bounded scan2existing snapshots and3lines. Target existing10soperation deadline;measure actual current preview sample if useful. Existing long-talk performance/global2snot newly qualified |
| baseline_commands | Actual121hashes/index PASS;canonical capture=sys pytest new integration2expected missing-output FAIL before source changes. F71source/static/37affected and F70runtime reused only unchanged inputs |
| verification_commands | README Ruffboth,formatincluding new tests,strictmypy source fallback/import3+1/pip and exactCI31where affected;canonical capture=sys new unit/integration and existing patrol/support-slot/memory/cycle-slot suites. Actual worker/real framed/hidden Tk if new wiring concerns;all consumers already use same messages. Compare six old-mode whole output/state and patrol old text after removing exactly declared3lines using frozen source;no fresh full required for app-only projection. Final document10/hash/index/scene/UTF8/links/diff check |
| test_responsibilities | NEW integration test_patrol_slot_position:direct/framed saved2/current4/previous2/rewind2selected4/reconnect/source-byte/query/retry;blocked position and old modes. NEW unit test_patrol_slot_position:actual checkpoint endpoint combinations/unchanged source and explicit missing/duplicate/foreignspace/non-int/out-of-bounds errors. No mocked game outcomes |
| acceptance | Independent examples/read-only/oldmode/error/real client tests and static/source/docs pass. Other module ASTexact except declared import/private formatter/guarded caller. All prior non-scope/index/scene preserved. LOCAL_ACCEPTED limited to actual Python presentation;fresh Unity compile/native/layout/build NOT_RUN AWAY-001 |
| claude_checkpoints | CP01–05not newly triggered:existing validated snapshot/message path,no new gameplay engine/save/schema/provider boundary. CP06held;D2/independent review/global2s/MIN-SPEC/standalone/release OPEN |
| stop_conditions/delivery | Record real decision dependencies and select safe work while user away;no question or native relaunch. Preserve exact handles/hashes at quota. English order/receipt+Korean category5support status;no agents/commit/push/PR/merge/publication/original-goal completion |

## Actual acceptance

Missing public rows reproduced2FAIL2.83s before source changes. Final new25PASS8.13s;
current9files179PASS64.59s,all25included/JUnit zero failures/errors/skips. Current
Ruffboth/format46/strict242/import3+1/pip/exactCI31PASS7.57s. Real worker/withdrawn Tk/
framed save+previous/reconnect/rewound future/error logging+state/retry/source preservation
qualified. Six modes x16whole updates exact;patrol19updates only3declared slot rows;
all7descriptor bytes/pins/core/protocol exact. Actual source8/265copied,not regenerated:
long preview before0.088324/current0.090845/framed0.094860s;whole outputs/state/source
exact except3rows,current direct/framed exact. Not global2s/native qualification.
Other module ASTexact after declared import/private formatter/guarded caller removal;
109old-source/115prior non-scope preserved. Prior full281has277unchanged/4deltas,no fresh
full claim. First baseline-copy/test assumption/type errors retained in receipt/evidence.
Final doc/scope/hash/index/scene closure in delivery.json. Native NOT_RUN AWAY-001;
Computer Use STOPPED,goal ACTIVE,no agents/publication/timed wake.
