# QT-F02 — Bounded Scenario Generalization

Date:2026-10-15 | Executor:Sol | Review:self-review,not independent acceptance.
State:order authoring DONE;parent IN_PROGRESS;first bounded runtime unit DONE,CP03 pending.
Latest director authorization now permits proceeding under Sol's judgment. The concrete
[room-bindings unit](QT-F02_ROOM_BINDINGS.md) supersedes this document's earlier DRAFT only
for3x3/one-instance bindings;larger maps/multiple targets/external packages remain later.
Authorization:director requests reading the current handoff/backlog and executing the next
recorded action. That action is authoring this order after RS-CLIENT-003/CP04,not bulk import.
Authority:[MASTER](../MASTER_GAME_ARCHITECTURE.md#13-scope-gates--order),
[work-order template](../prompts/SOL_CODING_WORK_ORDER.md),
[turn rules](../../ENGINEERING_RULES.md),[backlog](../../BACKLOG.md).

## Original authoring scope and baseline

Goal:replace the single-room assumptions with content-owned scenario identities and geometry,
then demonstrate two independently authored scenarios through the same authoritative path.
The original authoring delivery established the source map,dependency order and acceptance requirements only.
That authoring delivery installed no tools,changed no gameplay/public contracts,and made no
executable READY claim. The linked runtime unit now supplies its own exact contract/evidence.
Non-goals:procedural continents,new combat balance,quests/NPC cognition,bulk narratives/assets,
final engine selection,standalone release,LLM integration or governance changes.

Baseline:main1ad22446d48c50b8b72a6d3af8de3c9d775134ea,clean tracked/untracked tree on entry.
Actual workspace:C:/Reverie Saga;older documents' C:/ReverieSaga is another documented layout.
Prior local work remains in stash `pre-update-local-work-20261015`;it is not part of this
baseline or evidence. Preserve it;do not automatically apply it over the newer main.
Before implementation refresh HEAD/status and all relevant source fingerprints;this source
inspection does not qualify a different checkout or an old stashed repair.

Prerequisites:RS-P1-CORE representative slice,QT-F06 six-description compiler/sample,and
RS-CLIENT-003/CP04 first reviewed prototype DONE. CP03 remains DEFERRED/not received.
Documentation tools:local CPython3.13.12 and Git;Unity is unnecessary for this delivery.
For later native work follow [per-device setup](../WORKSTATION_SETUP.md);another host's
Unity/license/native PASS cannot qualify this workspace.

Reads:AGENTS,ENGINEERING_RULES,SESSION_HANDOFF,BACKLOG,GAME_SYSTEM_SUMMARY_KO,README;
MASTER §§2–4/13;v2.6 overrides/AI-documentation/checkpoint rules;
[original finding](../reviews/CLAUDE_QUILLTALE_FEEDBACK_2026-10-07.md),
[QT-F06](QT-F06_NARRATIVE_IMPORT.md),[CP04 dispositions](../reviews/RS-REVIEW-CP04_DISPOSITIONS_2026-10-12.md);
the actual source/callers in the table below and existing encounter/watch/durable/client tests.

Allowed NEW:C:/Reverie Saga/docs/work_orders/QT-F02_SCENARIO_GENERALIZATION.md.
Allowed MODIFY:C:/Reverie Saga/BACKLOG.md;C:/Reverie Saga/SESSION_HANDOFF.md;
C:/Reverie Saga/GAME_SYSTEM_SUMMARY_KO.md.
Forbidden this delivery:all runtime/tests/config/locks,reference checkout,compiled catalogs,
frozen CP02/CP04 witnesses/archives,stash contents and remote settings/publication.
Future runtime allowed paths must be enumerated in a separate complete implementation unit.

## Observed live consumers

| Boundary | Actual source/symbol | Constraint to resolve together |
|---|---|---|
| Bootstrap | src/app/watch.py:WatchBootstrapSpec/_bootstrap | Fixed gate4/enemy8/NPC6,3x3 map,role IDs and initial wake event |
| Registration/pins | src/app/encounter_registry.py:encounter_bundle;src/app/watch_registry.py:watch_bundle | Literal rules/schema descriptors and field bounds encode the same room |
| Geometry/rules | src/domain/trial.py:cell_coordinates;src/domain/encounter.py:adjacent_cells;src/engines/encounter.py | Coordinates,actor/target IDs,gate/enemy cells and adjacency use fixed metadata |
| NPC/events | src/engines/watch.py;src/orchestration/watch.py | Fixed NPC/lantern IDs,cell,event validation and pending-event checkpoint invariants |
| Admission/serialization | src/orchestration/trial.py;src/orchestration/encounter.py | Codecs,fact/delta/cue checks,checkpoint policy and presenters also enforce fixed IDs/cells |
| Durable ownership | src/app/durable.py:create_durable/resume_durable;src/contracts/state_io.py:StateIO | Caller supplies registered bundles;load/replay must reconstruct the same pinned rules |
| Input/projection | src/app/client_session.py:_payload/ClientSession.update;src/app/client_worker.py | Requests and view select fixed roles;all SQLite/session work has one worker owner |
| Text | src/app/client_text.py:NAMES | Player-visible names resolve fixed entity IDs |
| Engine wire | src/app/engine_bridge.py:schema_fingerprint;src/app/engine_project.py:generate_wire | Public DTO changes require fingerprint/codegen and real framing/capacity checks |
| Unity scene | clients/unity/Assets/Reverie/Scripts/PlayRoom.cs:Apply | Explicitly rejects non3x3 or changed board geometry under accepted CP04 policy |

Six QT-F06 descriptions are UI text,not scenario definitions or quest logic. Replacing only
client constants or adding a scenario JSON reader cannot satisfy this task. Existing
SimulationPins/PackageDocument are the starting point for identity/pinning design;do not add
an independent mutable configuration SSOT or bypass existing checkpoint validation.

## Dependency order and readiness

The following table bounds the broader parent. The linked first runtime unit resolves its
own subset;do not treat remaining larger-map/package questions as blockers for that unit.

1. **Contract unit,next design work:**specify immutable scenario definitions,role bindings,
   geometry/occupancy,accepted-content identity and version routing. Resolve the readiness
   table below into exact signatures/schema/bounds/error codes and independent examples.
   Link applicable A10/save/replay contracts before making any new public contract effective.
2. **Headless implementation unit,not READY:**register validated metadata through legal
   layers;update bootstrap,admission,engines,reducers,codecs,checkpoint policy and presenters
   together. Preserve existing published schemas/pins/fixtures;qualify compatibility explicitly.
3. **Client integration unit,not READY:**carry authoritative roles/selection through
   ClientWorker/ClientSession/text and generated wire DTOs into Tk/Unity. Replace the CP04
   fixed-board guard only with an explicitly specified geometry lifetime/resync policy.
4. **Evidence/checkpoint:**exercise two independent scenarios,save/load/retry/recovery and
   replay,then prepare RS-REVIEW-CP03 with actual sources/tests/commands/failures/hashes.
   Obtain director-forwarded Claude feedback,verify findings,repair/retest before expansion.

| Required runtime contract | Decision required before READY | Acceptance condition |
|---|---|---|
| Public I/O | Exact definition fields/types/versions;compile/bootstrap/select API;who owns selection | All registered callers and construction/resume paths specified |
| Cardinality/targets | First-unit actor/door/enemy/NPC counts;explicit target vs unique-role selection | Zero/multiple/missing/stale target behavior has exact diagnostics,no fallback to old constants |
| Geometry | Width/height/cell-mm bounds;row-major conversion;walls;collisions;NPC blocking policy | Invalid/overlapping/out-of-range entities reject before state creation or view mutation |
| Ordering/errors | Closed fields,exact integer types,bool rejection,duplicate IDs,canonical order,first error | Empty/negative/boundary/duplicate/unknown/missing cases have exact code/path or justified N/A |
| Ownership | Immutable accepted metadata vs COMMIT-owned mutable state;pending-event references | No engine-to-engine imports,no unvalidated cache,state writes remain COMMIT-only |
| Persistence | Package bytes/hash/version binding;legacy save route;cross-scenario load;failure cleanup | No silent repinning or new-content reconstruction of old saves;failed load preserves attachment |
| Replay | Genesis/world identity,rule/catalog pins,package availability and mismatch handling | Same accepted package/seed/trace gives identical state/facts;wrong package rejects explicitly |
| Presentation | Role/name IDs,view cardinality,geometry lifetime,wire schema/version/capacity | No local predicted outcomes;load/reconnect rebuild or reject before partial geometry change |

No proposed type,formula,bound or error in this document is an active runtime contract.
Missing semantics above mean DRAFT under the work-order template,not guessed TODOs.
Quest consequence schemas are outside this first unit. If a later unit changes major
NPC-memory/quest/save contracts,apply the CP05 preimplementation trigger separately.

## Independent verification requirements

Test responsibilities for later concrete units,not tests added by this delivery:

- Two original fixtures must use different IDs and placements,not merely renamed prose or
  a changed seed. At least one must omit every historical role ID to expose target leakage.
  Geometry variability must match the approved first-unit bounds;do not claim untested sizes.
- Derive exact movement/blocker/adjacency,damage/stamina and wake/reply outcomes from the
  approved new contract. Keep existing mechanics unless a separately scoped change is approved.
  Assert fact/delta/cue entity IDs as well as HP/tick;reuse no v1 or newly generated oracle.
- Trace each scenario through registered headless callers and the client boundary. Save at
  a pending event,load the branch,continue/retry/recover,and replay in fresh processes/hashseeds.
  Check old golden fixtures unchanged,matching pins,wrong-package rejection and unchanged
  attachment/files/state on precommit failures. Test postcommit truth separately.
- Cover unknown/duplicate IDs,missing roles,invalid cells/walls,noncanonical inputs,exact types,
  wrong versions/hashes and unavailable content. Exact error codes/paths must come from the
  completed contract,not from observing implementation output.
- Run [README gates](../../README.md#verification) and affected tests. Shared CORE changes
  require full regression. Unity changes require fresh native scene/error/reconnect/save/load
  evidence on this computer;headless PASS alone is not graphical acceptance.
- Performance:reuse accepted execution/frame capacities;define package/entity/geometry caps
  and a named measurement before READY. New performance numbers are UNVERIFIED here.

CP03 trigger:after generalized content and the first small playable segment,before further
scenario/world/engine or bulk-content expansion. Packet:exact HEAD/diff/input hashes,contracts,
all necessary source/tests/fixtures/locks,independent expectations,actual results/limitations.
No checkpoint triggered or external feedback requested by order authoring alone. CP04 remains
DONE for its accepted prototype;320other narratives remain unqualified/outside runtime.

## This delivery's acceptance

Public contract/behavior/formulas:wiring/source-map documentation only;no runtime API or
numeric behavior changed. Empty/invalid/ordering policies for runtime are readiness items
above. Documentation output is one order and three synchronized progress records;links
must resolve,English technical prose/Korean companion remain separated,history retained.
Algorithm:inspect actual entry/status/callers → bound order and dependencies → record DRAFT
gaps honestly → synchronize progress → strict UTF8/link/fence/scope/whitespace checks.

Baseline commands:git status --short --branch,git rev-parse HEAD,Python --version;clean main
and Python3.13.12 observed. Verification:strict UTF8/local links/fragments/fences for four
changed Markdown files;git diff --check;the five existing document-guard cases in
tests/unit/test_engineering_rules.py. Runtime/full/Unity tests NOT_RUN for documentation.
Acceptance:source map matches current callers;next units/checkpoints distinguish plan from
implementation;all required work-order fields are addressed or explicitly DRAFT;only four
allowed documents change;backlog/handoff/Korean progress agree;document checks PASS.
Stop conditions:overlapping user edits,baseline drift or absent contract evidence;preserve
the tree and report concrete evidence. Do not broaden this task into a runtime repair.
Delivery:brief Korean result and roadmap/checkpoint position. No commit/push/agent launch.

## Acceptance receipt — 2026-10-15

Order-authoring acceptance PASS,self-review only. Existing document guards:
`.venv/Scripts/python.exe -m pytest -q tests/unit/test_engineering_rules.py -k 'not standard_lint'`
exit0,5PASS/5deselected0.05s;the deselected subprocess lint probes are outside this document-only
selection. Strict UTF8/154local links/8fragments/balanced fences/exact4file scope PASS;
git diff --check PASS. Python emits a base-location shim warning while version/tests/checks
return success;no reinstall or claim of full environment qualification. Runtime/full/Unity
tests NOT_RUN. Parent remains IN_PROGRESS,runtime DRAFT;no CP03 feedback or gameplay acceptance.
