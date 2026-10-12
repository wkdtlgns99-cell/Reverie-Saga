# RS-CLIENT-003 — Unity / Unreal Engine 5 Integration and Play Verification

Date:2026-10-12 | Priority:P0,FIRST | State:DRAFT / implementation NOT_STARTED
Executor:gpt-6.1-sol | Review:director-requested plan,self-review only

## Director Scope

Director requests the highest-priority backlog entry:connect Unity or Unreal Engine 5 to
the agent workflow,build an actual small playable game scene and verify that the existing
game systems work through the engine. This supersedes the previous graphics-prototype
deferral and QT-F02-first scheduling for this bounded prototype. It does not select a final
engine or approve production art/bulk content. This delivery records and publishes the
plan;engine installation,connector setup and implementation have not run.

## Draft Contract

| Field | Contract / missing prerequisite |
|---|---|
| Goal | Agent-accessible engine project,repeatable editor/build/test/log/screenshot workflow,and one playable room exercising existing Brain functionality |
| Non-goals | Whole game,dual-engine full implementation,Python CORE rewrite,legacy engines/schema port,bulk art/content,final engine commitment or release |
| Baseline | Current headless Python Brain plus Tk prototype;refresh Git HEAD/status/source fingerprints before execution. Publication-entry HEAD a5dca63e2903dc3a415cb8c5957cecfe71ab0312 |
| Prerequisites | Engine/editor version,license/account availability,project path,usable automation/connector access and live Brain/client transport contracts must be established before READY. Engine choice is Unity OR UE5,candidates currently unselected |
| Read files | ENGINEERING_RULES,AGENTS,BACKLOG,SESSION_HANDOFF,GAME_SYSTEM_SUMMARY_KO,MASTER §§2/4–6/11,architecture/BLOCK_01.md client prototype gate,architecture/BLOCK_05.md A12,src/contracts/client.py,src/app/client_session.py,src/app/client_worker.py,and existing CORE/save/replay contracts/tests |
| Allowed edit paths | This planning delivery:C:/ReverieSaga/BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md and this NEW order. Runtime/editor-project/test paths UNRESOLVED:specify before READY |
| Forbidden | Reference writes,client-owned rule/state authority,SDK types in Brain,whole legacy template/code/formula/oracle port,unapproved production assets |
| Public contract | Preserve Python Brain authority. Typed commands enter Brain;only committed results/projections drive client positions,UI and animation. Concrete transport/version/session/retry/lifecycle interfaces require a bounded execution order |
| Behavior / ownership | Start one scene/session;send movement/door/attack/rest/NPC/save/load commands;render confirmed state;report actual errors;retain offline deterministic Brain behavior |
| Edge policy | Wrong input,blocked move,duplicate commands,disconnect/reconnect,failed save/load and exit/crash must not duplicate or partially apply actions or leave an orphan backend. Exact error codes/timeouts/ordering unresolved until transport contract |
| Examples | Closed door blocks movement;opening permits movement. Killing attack gives no counterattack. Exact retry preserves state and avoids duplicate animation/history. Successful load restores Brain facts and rebuilds client view |
| Algorithm steps | Discover available engine/access → select provisional candidate → finalize transport/lifecycle/order → create room with simple placeholder assets → connect commands/projections → automate tests and capture actual playback/logs → repair/retest → submit CP04 evidence |
| Wiring | Engine input/UI/render adapter to existing Brain;no replacement of calculations by client physics. Current engine connection NOT_IMPLEMENTED |
| Performance | Measure editor memory/start/build costs on current laptop and scene frame times. MASTER/BLOCK1 targets retained;actual fit/MIN-SPEC UNVERIFIED,no engine performance ranking asserted |
| Baseline / verification commands | Existing README Python gates retained. Engine-specific executable/project/test commands UNRESOLVED until version/path selected;no guessed commands treated as evidence |
| Test responsibilities | PLANNED engine integration tests:movement/blockers/door/combat/rest/NPC/save-load/retry/lifecycle;same Brain trace across headless/client;visual/input checks and actual failure recovery. Exact test paths required before READY |
| Acceptance | Repeatable agent edit/run/test/read-log/capture access;playable room demonstrates stated flow;independently expected Brain results agree with rendered view;failure/retry/load/exit checks pass;actual engine/build/performance evidence recorded;director UX acceptance separate |
| Claude checkpoint | CP04 after first Brain↔engine playable room,before final engine choice/bulk assets. Prepare actual contracts/source/test/log/capture hashes;record feedback,validate findings,repair/retest. CP03 remains applicable if content-generalization scope is later added |
| Stop conditions | Missing engine/access/transport contract keeps DRAFT;no fake successful engine tests or speculative READY status. Resolve concrete choices before implementation |
| Delivery | Engine connection/implementation/test result NOT_RUN in this planning publication. BACKLOG/handoff/Korean summary synchronized;director authorizes publishing all this session's project changes |

Future first playable flow:move → blocked door → open → move → attack/counterattack →
NPC event → save → alter state → load → retry without duplicate effects → normal exit.
Use simple geometry/placeholders first;no modeling subscription or bulk asset generation is
required merely to verify these systems. Later QT-F02/broad narrative migration/GOV-03/release
tasks remain recorded after this first-priority prototype.
