# QT-F23 — Select Existing Save Slots in Unity

Date:2026-10-16 | State:LOCAL_ACCEPTED | Executor/review:self;Claude extra review stopped PARTIAL.
Authorization:director requests the next bounded task. Primary5 screen/input;related6 storage/7 wiring.

| Field | Contract |
|---|---|
| goal/non-goals | Expose existing slot01–08 through a Unity selector;save/load/preview target the same selected slot. No new save,CORE,wire DTO/hash,content,ownership,clone cleanup,provider,scene/camera or gameplay semantics |
| baseline | HEAD0e06577,prior F21/docs/R1/F22dirty work preserved. Capture tracked+nonignored file hashes and scene bytes in tmp/qt-f23/entry.json before runtime edits |
| reads/prerequisites | Rulebook,handoff/backlog,guide,MASTER display/persistence,template/setup,actual PlayRoom/BrainConnection/LiveVerification/PlaytestBuild,engine_bridge and existing slot/pipe contracts/tests. Current Python3.13.12/Tk8.6/pip PASS;editor6000.3.25f1 reused;verify actual local license/native readiness |
| allowed | MODIFY clients/unity/Assets/Reverie/Scripts/PlayRoom.cs,BrainConnection.cs,LiveVerification.cs;clients/unity/README.md,docs/WORKSTATION_SETUP.md,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md. NEW tests/integration/test_unity_slot_selection.py,this order,docs/reviews/QT-F23_EXECUTION_2026-10-16.md. Owned tmp/qt-f23,.pytest_cache/qt-f23-* |
| forbidden | Python production/contracts/domain/engines/orchestration/adapters,generated wire/pins,content,shared configs/locks,other user changes. No commit/push/agents/dependencies/provider call/checkpoint waiver. Generated scene changes must be proven equivalent then restored exactly |
| API | PlayRoom.SelectedSlot read-only string(default slot01),CanSelectSlot bool,SelectSlot(int index)->bool for zero-based0..7. Invalid index→ArgumentOutOfRangeException with no mutation. Valid index while unattached/busy/failed/connecting→false,no mutation/request. BrainConnection.Send(string intent,string slotId="slot01") preserves old callers and sets existing wire slot_id;invalid ID rejects before writing |
| algorithm/wiring | Private selection index/8labels. SelectionGrid4columns in existing controls scroll area;enabled only after attached/idle/healthy. Selecting changes local UI only. Existing Send routes selected ID;preview label includes it. No persistence of selection across new component/application start;load/reconnect within same room preserve selection |
| behavior/edges | Default and all old flows remain slot01. Choose slot08 missing→SAVE_NOT_FOUND,no fallback/mutation;save08@T then save02@T+1,preview08showsT while current T+1;load08restoresT and resets history per existing Brain;reconnect resumes loaded path/retains08. Existing slot01bytes preserved throughout. Other slots are separate choices,not shared working-save clones |
| ownership/performance | Main-thread local selector;no new disk work or polling. Bounded8buttons/2rows4columns;fixed-width labels. Busy gate prevents selection changing in-flight target. Snapshot/operation validation remains canonical Python authority |
| test responsibilities | Actual graphical native selection/busy/invalid index/missing nondefault/save-isolation/distinct previews/load/reconnect/state/file checks in legacy/harbor/grove/old quest/default+explicit memory. Existing initial missing-slot/default paths retained. Real binary pipe verifies existing slots02/08 distinct states;no fake domain outcomes. Release hooks remain excluded |
| checks | Targeted Python pipe/slot/client regressions and README static/import gates. Actual seven-mode native editor flow plus Windows build/hook exclusion;inspect top/bottom selected-slot screenshots. Native failures repaired;full Python regression only if shared CORE changes/affected concerns require |
| acceptance | Nondefault slots usable through actual room/Brain path,UI selection visible/reachable/default-compatible;unchanged wire/save/content pins,source/slot state preserved for read-only actions;native/build/affected/static/scope/docs checks PASS and three progress docs agree |
| checkpoints/stops | CP01–05 retain bounded closure;read-only selection over existing closed storage contracts triggers no new checkpoint. V3 remains stopped PARTIAL,CP06 holds release. Stop for unavailable qualified native access after safe alternatives or new save semantics;no release/human UX/other-device acceptance inferred |
| delivery | Local accepted UI with exact evidence and5/6classification;no automatic further task/publication |

Accepted:[execution](../reviews/QT-F23_EXECUTION_2026-10-16.md). Seven native modes452PASS,
Windows build/release-hook exclusion,46affected Python/static and24save readbacks PASS.
