# RS-CLIENT-003 — Unity / Unreal Engine 5 Integration and Play Verification

Date:2026-10-12 | Priority:P0,FIRST | State:READY_FOR_REVIEW / native prototype implemented;CP04 pending
Executor:gpt-6.1-sol | Review:director-requested plan,self-review only

## Director Scope

Director requests the highest-priority backlog entry:connect Unity or Unreal Engine 5 to
the agent workflow,build an actual small playable game scene and verify that the existing
game systems work through the engine. This supersedes the previous graphics-prototype
deferral and QT-F02-first scheduling for this bounded prototype. It does not select a final
engine or approve production art/bulk content. This delivery records and publishes the
plan;engine installation,connector setup and implementation have not run.

## Historical Draft Contract — superseded by executable slice

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

## Executable Prototype Slice — Director Resume 2026-10-12

Latest director instruction authorizes completing the unfinished implementation,not planning
only. Select Unity6000.3.25f1 provisionally;official installer downloaded to ignored tmp with
publisher-signature validation before execution. No final Unity/UE5 comparison or selection
claim. Plugin-directory search returned no relevant engine connector;use project files,
Unity batch editor commands,test logs and screenshot artifacts for direct automation.

Allowed NEW:C:/ReverieSaga/src/contracts/narratives.py;src/adapters/narrative_catalog.py;
src/app/engine_bridge.py;src/app/engine_project.py;tests/integration/test_engine_bridge.py;
tests/unit/test_narrative_catalog.py;clients/unity/**;content/**;docs/work_orders/QT-F06_NARRATIVE_IMPORT.md;
docs/reviews/RS-CLIENT-003_EXECUTION_2026-10-12.md under the repository root.
Allowed MODIFY:this order,BACKLOG,SESSION_HANDOFF,GAME_SYSTEM_SUMMARY_KO,.gitignore,README.
Allowed NEW:clients/unity/README,docs/reference/QUILLTALE_SELECTION_LEDGER_2026-10-12.json,
CP04 review packet/manifest/archive and sanitized native evidence under docs/reviews.
Reference,CORE/engines,existing tests/oracles/pins,accepted CP02 artifacts remain read-only.

Transport:private inherited stdin/stdout binary pipes owned by one Unity-launched Brain child,
u32 big-endian length plus canonical UTF8 JSON;1..1MiB frames,requests≤16KiB,depth≤32,
duplicate/nonfinite/extra fields rejected. This is the bounded prototype harness route,
not the planned production TCP/diff/chunk/ACK/deployment implementation in BLOCK5 A12.
No network listener or public token. EOF/quit closes the worker/SQLite;client shutdown closes
input,waits≤5s then terminates its own child. C# SDK types never enter Python Brain.

Request v1 exact fields:kind="request",version="1",request_id=canonical positive decimal
string,attachment_id=empty for first attach otherwise current32hex,request=ClientRequest or
"quit",seconds=canonical decimal0..16,slot_id=slot01..slot08. IDs must increase;stale attachment
cannot issue actions after load. Responses pin schema hash and contain full derived ClientUpdate,
request ID and a read-only narrative list. ClientUpdate integers become decimal strings;
bool/strings retain their types. C# DTO/view field declarations are generated from Python
dataclasses,not manually maintained second models. Same actions route through ClientWorker.

Narratives:strict frozen new definitions,hash-pinned provenance,descriptive text only;no
legacy entity bindings,stats,conditions,rewards or behavior. First6already qualified adaptations
are the integrated sample;broader per-entry screening/import queue recorded separately.
The content list is display-only and cannot affect CORE or save/replay. Malformed/mismatched
catalog fails startup;no fallback to unverified source templates.

Native Python verification must cover actual subprocess frames/partial reads,invalid inputs,
stale/duplicate IDs,combat/save/load/retry/resume and EOF cleanup with real durable sessions.
Unity verification must compile,build the scene,run the matching live flow/assertions and
capture actual frames before engine success/DONE. License/editor/account failures are recorded
as actual blockers while independent Python/content work continues. CP04 remains required
after this first integrated sample;bulk imports/final engine commitment held until dispositions.

## Native result

[Execution receipt](../reviews/RS-CLIENT-003_EXECUTION_2026-10-12.md):editor installed/active license,
real scene/build plus17fresh graphical checks PASS;6catalog descriptions actually loaded.
Standalone player OS launch BLOCKED;CP04 feedback pending. Historical planning NOT_RUN fields
above describe the pre-resume delivery,not current executable status.
