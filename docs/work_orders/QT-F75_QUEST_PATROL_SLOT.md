# QT-F75 — Compare current and selected-save quest patrol goals

Status:LOCAL_ACCEPTED2026-10-27. Local self-review,not independent/native acceptance.
Authority:explicit resumed automatic goal ACTIVE. Primary5presentation supporting2/6/7;
this is read-only presentation of F74behavior,not new NPC cognition.

| Field | Contract |
|---|---|
| goal/non_goals | Slot preview labels both current and selected saved quest patrol plans,including identical poses with different heard knowledge. No new goal logic,mode/flag/engine,DTO/schema/pins/CORE/save/wire,queries/replay/provider/IO/dependency,old-mode output/native/governance change |
| baseline | HEAD72c2d588d7f64c3e113cf462af35fb673bf82582,branch codex/cycle-call-recall-20261024. All137F74delivery hashes/index verified,staged empty,no live jobs;tmp/qtf75/entry.json/baseline. F74full3031PASS1245.55s reused only for unchanged inputs |
| prerequisites/read_files | ENGINEERING_RULES/handoff/backlog/Korean companion/numbered guide/MASTER2Brain-Body+save visibility/v2.6readonly contracts/Sol template/AUTONOMOUS_EXECUTION/WORKSTATION_SETUP/README/deferred/F74order-receipt-delivery;actual ClientSession.inspect_slot/current saved checkpoint validation/quest_patrol_plan/support_slot_messages/F72pose comparison/client-worker-bridge-Tk slot consumers |
| MODIFY absolute paths | C:/Reverie Saga/src/app/npc_patrol_status.py;C:/Reverie Saga/src/app/client_session.py;C:/Reverie Saga/BACKLOG.md;C:/Reverie Saga/SESSION_HANDOFF.md;C:/Reverie Saga/GAME_SYSTEM_SUMMARY_KO.md;C:/Reverie Saga/README.md;C:/Reverie Saga/clients/unity/README.md;C:/Reverie Saga/docs/DEFERRED_USER_DECISIONS.md;this order |
| NEW absolute paths | C:/Reverie Saga/tests/unit/test_quest_patrol_slot.py;C:/Reverie Saga/tests/integration/test_quest_patrol_slot.py;C:/Reverie Saga/docs/work_orders/QT-F75_QUEST_PATROL_SLOT.md;C:/Reverie Saga/docs/reviews/QT-F75_EXECUTION_2026-10-27.md;owned ignored tmp/qtf75 |
| forbidden_paths | All other production/engines/domain/CORE/contracts/checkpoint/codecs/reducers/presenters/old tests/goldens/G07tool-inventory-scope/governance/old receipts/orders/C#/scene/user files/reference. No agents/publication/commit/push/dependency/window/native/build |
| external_contract/behavior | Add quest_patrol_slot_messages(saved:CoreSnapshot,current:CoreSnapshot,layout:Scenario)->tuple[str,...] in existing app/npc_patrol_status. Reuse quest_patrol_plan twice,with existing SAVE_INSPECT_FAILED;no duplicated knowledge/pose logic or extra validation IO. Return exactly3lines:header NPC 의뢰 순찰 계획 비교 · 현재 {current.tick}초 / 선택 저장 {saved.tick}초,then 현재 +canonical current line,then 선택 저장 +canonical saved line. These describe plans at labeled snapshots,not historical causes or guaranteed arrival |
| wiring/ownership | ClientSession.inspect_slot uses its already validated checkpoint.core/current.core within existing npc_cycle branch,only if self._npc_quest_patrol. Insert immediately before existing patrol position comparison,keeping its established final3rows,catch/log SaveError as NPC quest patrol slot plan comparison failed and re-raise. Reuse existing SLOT_INSPECTED ClientUpdate/messages and worker/framed/Tk/Unity message consumers. Current/previous selection and load/reconnect require no new flag/wire. No mutation/caching/provider/replay/source query |
| edge_policy | Available/accepted/reported-neighbor/reported-home use existing canonical plan. Exact selected records/space/int/path/future memory/available-home checks delegate unchanged helper;SAVE_INSPECT_FAILED propagates for either bad source. Empty knowledge is valid waiting;equal ticks/poses/knowledge still produce labeled rows. Rewound current time is valid,never reorder snapshots or infer from parity. Existing missing/corrupt/foreign mode slot failures and selected previous-no-fallback behavior remain. Duplicate/missing/other-owner records cannot stand in;no new RNG/scales/negative handling beyond existing validated inputs |
| examples | Save0NPC6unheard then accept2NPC6:current2patrol goal versus selected0wait goal despite equal pose. Save reported22NPC7then current24NPC6:current24wait-home versus saved22prepare-return. Loading previous0while latest2remains reverses current/selected ticks truthfully;source save bytes remain. Old8modes append nothing |
| algorithm_steps | Reproduce2missing public-slot outputs before implementation. Add small wrapper using canonical current/saved plans and header;wire single guarded caller before existing pose block,keeping the existing pose tail intact. New boundary pairs/error propagation/read-only/current-previous/restart/loaded branch/retry/worker/framed/withdrawn Tk tests. Verify old8whole stable outputs and new ninth mode only3intended slot rows;all9pins/state/descriptors unchanged. Actual saved short/long before/current direct/framed slot measurement and source preservation. Static/affected/exactCI/docs/source/hash closure |
| performance | Two <=component-count scans per checkpoint delegated existing bounded plan helper,no new replay/SQL/IO. Measure actual7/263source slot previews before/current/direct/framed,full normalized output except3intentional rows and two transport identity fields;target2s/existing10sdeadline,retain all samples/global2sOPEN. Do not rerun timings just for green |
| baseline_commands | Verify137F74hashes/index and new public integration2expected missing3rows. Actual existing inspect_slot ends with pose rows;it has no quest patrol plan import/call |
| verification_commands | README Ruffboth/scopedformat53/strict source mypy249/import3+1/pip/new+affected slot/quest-patrol/support/cycle/recovery/client tests/exactCI31/document10. Old8whole stable output bytes/schema+rules/pins/core/protocol exact;new ninth only3declared slot rows differ. Actual before/current7/263direct/framed slot/read-only/state/source/timings. F74full3031reuse justified by exactly2app presentation deltas;fresh whole full only for new shared-CORE/engine failure or unresolved concern |
| test_responsibilities | NEW unit16goal pairs including same/reversed times and selected/current invalid source propagation;NEW integration equal-home different knowledge/report-return/current-previous/load/reconnect/no fallback/corruption/source bytes/quiet retry/real worker-framed-withdrawn Tk. Expected text independently derived from F74documented behavior;no mocked domain outcomes/old tests edits |
| acceptance | New exact3rows reachable through existing clients only quest mode;allprior rows/order/game state/source files unchanged. Current affected/static/CI/docs/old8parity/new9delta/runtime/source/index/hash checks pass. Prior129nonscope/all109other production preserved;dirty scope141. No G07source change;existing35/8/8/4witness/current engine coverage retained. LOCAL_ACCEPTED Python/query/source only,fresh native NOT_RUN AWAY-001 |
| claude_checkpoints | CP01-05not triggered:pure existing presentation boundary under same contracts,not new engine/pipeline. CP06held;D2/independent rereview/global2s/MIN-SPEC/standalone/release OPEN. No external feedback fabricated |
| stop_conditions/delivery | Preserve user overlap/uncertain source;record real decision dependencies and use other safe work,do not ask while away. Keep CUstop/no agents/publication. English order/receipt and synchronized Korean primary5support status,complete hashes/source diff/tests/limits/resume. Original unfinished goal ACTIVE after bounded task |

Placement settled before implementation:the existing selected-pose block is the final3
rows (actual F74test_reported_neighbor_save_reconnect_compact_and_physical_return).
Put the new plan group before that block so plans precede physical pose and existing
position consumers keep their established tail;no old test/oracle needs editing.

## Current local acceptance

New42included in current239PASS104.94s;Ruffboth/format53/strict249/import3+1/pip/exactCI31
PASS8.40s. Actual worker/framed/withdrawn Tk/current-previous/reconnect/rollback-free query/
corrupt selected no-fallback/retry cases pass. Old8stable outputs exact;new ninth only
3declared slot rows differ,excluding only2transport-local identity fields. Actual retained
7/263sources before/current direct/framed8samples0.062714–0.115212s,source/state/protocol
preserved. Two app display-only additions;all109other production/129non-scope preserved.
F74one full3031reused only unchanged engine/domain/CORE/G07;no new full/native claim.
Final document10/scope141/hash/index/scene/links closed in delivery.json. Global2s/F74
activity miss/independent review/CP06/release holds remain;original goal ACTIVE.
