# QT-F72 — Current and selected saved NPC patrol positions

Status:LOCAL_ACCEPTED2026-10-27. Local self-review;not independent/native acceptance.
[Order](../work_orders/QT-F72_PATROL_SLOT_POSITION.md). Primary5presentation support;
related2/6/7. This projects existing saved state,not a new NPC action or historical memory.

## Delivered behavior and wiring

Existing ClientSession.inspect_slot now appends three position lines in patrol mode:
current/selected ticks,current NPC endpoint,selected saved NPC endpoint. A private
_patrol_slot_messages receives the two already available snapshots and canonical layout.
It requires one exact selected WatchNpcRecord per snapshot,same space and exact integer
cell in canonical patrol_cells. Missing/duplicate/wrong-subject/foreign-space/non-int/
unknown endpoint fails SAVE_INSPECT_FAILED;the public boundary logs and propagates it.
No partial update or state mutation. Other NPC records cannot replace the selected subject.

Labels name the original or adjacent work point;no raw cells or inferred movement history.
Current4/saved2,different/current slots,rewound2/selected future4,reconnect and blocked
NPC7at4all use actual records. Older modes add nothing. A current tick never predicts pose.
One canonical import/private formatter/guarded existing caller only;no public signature,
engine,CORE,action,persistent field,schema,pin,save envelope,wire or C#change. No additional
replay,restore,IO,query or cache. Existing worker/Tk/framed/Unity message consumers are wired.

## Actual verification

- Entry:all121F71delivery hashes/index verified;HEAD72c2d58/branch
  codex/cycle-call-recall-20261024,staged empty. Actual pre-resume124in-progress hashes and
  byte index revalidated. Baseline/source inputs in tmp/qtf72;unrelated work preserved.
- Missing public output baseline2FAIL2.83s;new focused22PASS4.63s then expanded final
  25PASS8.13s. Current affected9files179PASS64.59s(wrapper65.07s),all25new included,
  JUnit zero failures/errors/skips. Actual direct/framed current/previous/rewound future/
  restart/source-byte preservation,blocked pose,stationary no-op and invalid selected-NPC
  source logging/state preservation/quiet retry/next query qualified.
- Actual worker and withdrawn Tk preview show all three lines without changing view/files;
  owned workers/windows joined/closed. This is not native Unity rendering evidence.
- Current Ruffboth/format46/strict242/import3+1/pip/exactCI31PASS7.57s. Frozen Python inputs
  preserved through the repaired run. First errors repaired as below;no skipped test.
- Seven-mode frozen/current whole-output comparison:six older modes x16updates exact,
  patrol19updates exact after removing only the strictly checked three new slot rows.
  All7schema/rules bytes,pins,core and protocol exact. Process source paths asserted.
- Existing F69source8/265copied with slots;no new source gameplay. Six actual queries:
  short before0.059253/current0.059379/framed0.059219s;long before0.088324/current0.090845/
  framed0.094860s. Old whole update exact except3declared rows,current direct/framed exact,
  core/protocol/source and all saved files preserved. Samples,not a global2s/MIN-SPEC result.
- Source audit:other module ASTexact after removing only the canonical import/private
  formatter/guarded caller.109baseline production sources and115prior non-scope paths
  unchanged. F69full2803evidence281inputs has277unchanged and4deltas:native verifier,
  ClientSession,F70npc_activity and call-native test oracle. No fresh whole regression.
  G07/engine/CORE/contracts/scene/C#unchanged. Final files/index/links/doc checks:delivery.json.

## Retained failures and repairs

First owned baseline copy failed because copying ClientSession had already created
baseline/src;all121prior hashes were revalidated and the exact owned directory reused.
No product edit occurred before that repair. Initial focused21PASS1FAIL4.80s:new test
attempted retry immediately after load,which intentionally clears retry identity. Quiet
retry is now tested before load and exact NO_RETRY after;no production change.
First strict run found2new-test empty-tuple inference errors;explicit record-tuple type
repaired. Expanded focused22PASS1FAIL6.27s:new test guessed ClientWorker.save instead of
actual request("save");source/API corrected. Next strict run found4new-test naming/kwargs
types:reused before variable changed bytes→inventory dict,and untyped **bool mapping could
target Scenario. Rename restarted_before and use six explicit existing flag keywords.
First logs/results retained;all old assertions/goldens/thresholds preserved.

## Quota interruption and limits

After usage99%,an attempted metadata write was not executed because automatic approval
review could not complete due the five-hour usage limit;the dependent poll was not reached.
The already started session79657continued independently and was later observed terminal1
with the two test typing errors. After reset,ordinary usage allowed/primary0% and original
supported goal ACTIVE were verified at2026-10-27 02:58:10UTC. Exact handle resumed without
restarting based on timeout. No timed wake was registered;this does not qualify a scheduler.
Subsequent85894and43776terminal0;slot runtime terminal0,no live jobs at delivery.

Fresh Unity compile/native/render/layout/capture/Windows build NOT_RUN AWAY-001;
Computer Use STOPPED. No question,agent,publication,dependency or release. CP06held,
D2/independent rereview/global2s/MIN-SPEC/standalone/release OPEN. Original objective
remains unfinished and ACTIVE;continue bounded authorized NPC/world development.
