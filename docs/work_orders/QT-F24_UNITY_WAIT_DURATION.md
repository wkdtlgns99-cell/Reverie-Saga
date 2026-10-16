# QT-F24 — Select Existing Wait Durations in Unity

Date:2026-10-16 | State:LOCAL_ACCEPTED | Executor/review:self.
Authorization:director requests next bounded task. Primary5 graphical input;related2 existing time rules/7 wiring.

| Field | Contract |
|---|---|
| goal/non-goals | Expose wait presets1/4/8/16seconds in Unity instead of hardcoded1. Existing wait command/time/event/retry/save semantics remain authoritative. No CORE/Python production/wire/schema/content/save/asset/camera/provider/cleanup change |
| baseline | HEAD0e06577 plus prior F21–23/docs/R1dirty work. Before runtime edits capture tracked+nonignored hashes/scene bytes in tmp/qt-f24/entry.json;preserve all outside this scope |
| reads/prerequisites | Rulebook,handoff/backlog,guide,MASTER truth/time/client,template/setup,domain.watch.WAIT_MAX/current wait engine,client command projection and engine_bridge seconds validation,PlayRoom/BrainConnection/LiveVerification/PlaytestBuild/F23order;README commands and Korean progress. Existing Python3.13.12/Tk8.6/editor6000.3.25f1,pip PASS;actual host licensing/native readiness required |
| allowed | MODIFY clients/unity/Assets/Reverie/Scripts/PlayRoom.cs,BrainConnection.cs,LiveVerification.cs;clients/unity/README.md,docs/WORKSTATION_SETUP.md,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md. NEW tests/integration/test_unity_wait_duration.py,this order,docs/reviews/QT-F24_EXECUTION_2026-10-16.md. Owned tmp/qt-f24,.pytest_cache/qt-f24-* |
| forbidden | Python production/CORE/contracts/engine/domain/orchestration/adapters,generated wire/pins,content/config/locks,prior evidence. No agents/commit/push/provider/install/publication. Native scene reserialization must be proven equivalent then restored byte-exact |
| API | PlayRoom.SelectedWaitSeconds(int,default1),CanSelectWaitDuration(bool),SelectWaitDuration(int index)->bool. Indices0..3 map1/4/8/16. Invalid index→ArgumentOutOfRangeException,no mutation. Unattached/busy/connecting/failed→false,no mutation/request. BrainConnection.Send adds optional waitSeconds=1;only wait encodes it as invariant decimal,other intents keep seconds1 |
| semantics/edges | Presets are UI choices within canonical Python WAIT_MAX16,not a new limit authority. Choice alone submits no request or game write. Selection stays local across load/reconnect;new room defaults1. Retry replays original stored command even after UI choice changes. Invalid transport wait<=0 rejects before sending;other positive values remain subject to canonical receiver validation;UI exposes only four admitted presets |
| algorithm/wiring | Private preset/index/labels;four-column SelectionGrid in existing scrolling controls,next to action block with explicit wait label. Same readiness gate as slot selection. PlayRoom.Send forwards selection;BrainConnection writes existing seconds field conditionally. Busy gate fixes in-flight duration. No new polling/storage/cache |
| examples | Existing snapshot tickT;wait16→T+16(one command revision),select4then retry→stillT+16,no duplicate events;load existing slot08@T→T;reconnect retains UI16and saved state. Nonwait/save/preview/retry do not acquire selected wait duration |
| ownership/performance | UI main thread only,bounded4buttons. Logical elapsed seconds are not wall-clock sleeps. Parent/Brain timeout/framing/size/process lifecycle unchanged;no LLM or external network |
| tests | Real binary pipe all1/4/8/16values,revision/retry/save-load and invalid bounds under existing wire rules. Native all preset values/local-only/busy/invalid/failed/connecting gates,max actual wait+changed-choice retry,load/reconnect persistence;all7existing modes/native build/release-hook exclusion. Actual top/bottom capture and saved-state readback |
| verification | Targeted wait/watch/pipe/client/slot regressions;README Ruff both,scoped format,mypy,pip/import3+1;native modes7/build,original scene restoration,entry hashes/UTF8/local links/fences/three progress docs. Full suite only if shared CORE changes or affected failure requires it |
| acceptance | Existing wait simulation receives chosen duration via real C#→pipe→Python path;default/nonwait/retry behavior preserved;UI visible/reachable and gated;affected/native/build/static/scope/doc checks PASS |
| checkpoints/stops | Existing closed CP01–05contracts reused;no new gameplay rule/checkpoint. V3stopped PARTIAL,CP06release held. Stop only for unresolved authoritative timing or unavailable qualified native evidence after safe alternatives;no release/human UX/device/MIN-SPEC acceptance inferred |
| delivery | Local accepted feature,evidence,primary5/related2classification;no automatic further task/publication |

Accepted:[execution](../reviews/QT-F24_EXECUTION_2026-10-16.md). Python515/native519in7modes,
Windows build/release-hook exclusion,static/imports and24save readbacks PASS;prior work preserved.
