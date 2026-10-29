# QT-F85 — Current next movement feedback after actual NPC replies

LOCAL_ACCEPTED2026-10-29,self-review. Primary5presentation support;related2existing NPC
calculation,6postcommit truth,7real direct/framed delivery.
[Order](../work_orders/QT-F85_CALL_PATROL_FEEDBACK.md).

Only ClientSession production changes:reach-mode selected-NPC actual reply projection
captures current snapshot once,then reuses supply_support_plan and quest_patrol_next_step.
Existing prefix marks post-response current state. No new movement goal/event/action,
record/cache/replay/query/IO/format/pin/flag or worker/native schema. Generic message
consumers already transport/display the same field. Helper failures retain the existing
logged NPC_RECOLLECTION_SOURCE postcommit boundary;no partial successful plan publication.

Independent expected vectors:actual call11low stock ->FREE_HOME;13far and stock-ready
->FREE_NEIGHBOR;15adjacent assistance opens gate ->FREE_HOME;after down15/down16occupies
home6andNPC7cannot return,call17 ->BLOCKED_HOME. Before implementation,all8actual direct/
framed cases fail because the next-step row is absent(8.73s). After implementation,new10
within62affectedPASS92.77s. Existing support row stays once;exact retry preserves view/raw
save and adds no row. Old ready mode has no new feedback. Injected ordinary plan failure
occurs after actual gate/reply commit;state stays truthful,retry and a later action succeed.
No mocked domain outcomes or changes to old tests/goldens/checkers.

Ruffdefault/quality,strict265andscoped formatting PASS. Final currentCI31/imports3+1/docs10/
pip/links/scope/UTF-8 evidence is recorded in tmp/qtf85. Shared serialization/engine/replay
sources are unchanged from F84full3562PASS984.82s;no new full run is implied by the
presentation-only continuation. Expensive queries unchanged;reuse F84paired12measurements,
including4remaining2sTARGET misses(max3.726747s),all<10sdeadline. Native/editor/compile/
render/build NOT_RUN;CP06/independent/device/release/MIN-SPEC/global2s remain held/open.
No agents,publication,dependencies,security or goal action. Exactly one further task done.

Artifacts:tmp/qtf85/client_session-before.py,baseline.log,affected.log and final-checks.
