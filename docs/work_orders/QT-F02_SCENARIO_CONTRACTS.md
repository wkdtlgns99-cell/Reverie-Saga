# QT-F02 — Embedded Scenario Contracts

Date:2026-10-13 | Director authorizes remaining design/implementation/tests in chat.
Coding state:first embedded implementation/native acceptance and CP03 scoped feedback/repair DONE.
Supersedes the parent order's unresolved §4 for the bounded embedded first stage.

## Scope / Compatibility Decision

Two embedded immutable configurations reuse the existing ten-record watch feature and rules.
No external gameplay package loader,accepted-package storage,save-format migration,quest or memory
behavior is introduced. Definitions are compiled into the selected feature's rules document;
existing rules/schema fingerprints pin every role and position before new-game creation.
Gameplay packages stay empty as in CORE-04/05. Existing incompatible-pin rejection and owner
swap behavior remain unchanged. This resolves CP05 applicability:NOT_TRIGGERED because no major
save/quest/memory contract or format changes;CP03 still gates further scenario/world expansion.
External user-editable gameplay packages require a later contract,not implicit acceptance here.

## Definition / Consumers

NEW `domain.scenario.Scenario`:frozen,slots,exact strings/integers/tuple;fields `scenario_id`,
`actor_id`,`space_id`,`gate_id`,`enemy_id`,`npc_id`,`lantern_id`,`initial_cell`,`gate_cell`,
`enemy_cell`,`npc_cell`,`blocked_cells`. Default roles/topology are existing canonical constants;
default scenario ID=`scenario:legacy`. IDs are exact namespaced strings≤128characters;role IDs
unique and prefixes actor/space/object appropriate. Cells0..8;exactly one wall in immutable tuple;
four initial occupied cells distinct and none in walls. Bool/float/subclass/coercion rejected.
Invalid shape/type/ID/topology→ValueError with `SCENARIO_*` code;wrong pinned save uses existing
`UNSUPPORTED_RULESET` and preserves source/owner. No zero/negative dimension allowed:3×3,1000mm fixed.

`ScenarioBound(layout=LEGACY)` retains one validated immutable definition;no ambient/global
switch or provider/I/O. Engines/admission/codecs/reducers/presenters/map adapters use the same
selected instance. Existing FieldSpec families/owners/consumers and manifests stay unchanged;
gate/NPC fixed-cell constraints become selected-cell constraints in the new feature only.
Legacy default produces identical schema/rules/schedule/catalog fingerprints and goldens.
`encounter_bundle(layout=LEGACY)`, `watch_bundle(layout=LEGACY)` build one selected feature;
the new definition is in rules_document,not a second mutable authority. Component ordering is
canonical by schema/version/entity,never by assumed lexical player/enemy role order.

`bootstrap_watch(spec,layout=LEGACY,rng=None)` keeps spec.initial_cell for legacy calls;nonlegacy
calls must explicitly match the selected initial_cell or reject INVALID_INITIAL_STATE/SCENARIO_INITIAL_CELL.
Scenario client creation sets it from the selected definition. Initial HP3/enemy5/stamina2/closed gate,
period2/echo1/charge3/wait1..16 and all combat arithmetic/order/errors remain existing contracts.
NPC remains nonblocking;player can later occupy its cell. Closed door/living enemy block movement;
defeated body does not. Wake/request/echo/reply subjects and coordinates follow selected roles.

`ClientSession(path,layout=LEGACY)`, `ClientWorker(path,layout=LEGACY)` use same selected bundle
for creation,resume,load,retry and recovery. Explicit selection on resume must match saved pins;
it cannot replace an existing file or reinterpret another scenario. `--scenario legacy|harbor|grove`
at Tk/bridge CLI selects before attachment. No in-world scenario switching. Separate fresh working
paths for new games;Unity keeps selected scenario on reconnect/loaded branch.
ClientUpdate adds trailing default strings `scenario_id`,`scenario_name`;generated wire schema
changes coherently with Python source. Display labels use accepted six descriptions by reference;
no legacy stats/behavior. Narration receives an immutable selected role-name map and preserves
default legacy text. No UI role ID decides authoritative outcomes.

CP03 repair:typed ScenarioConsumer.scenario_layout exposes boot metadata;RegisteredStateIO
compares every such registered consumer with the complete pinned rules.scenario value before
registration and raises INVALID_SCENARIO_BINDING on mismatch. Frozen encounter engine constructors
reject non-exact Scenario. Wait narration receives selected actor_id explicitly;legacy standalone
defaults remain compatible. Programmatic unregistered layouts intentionally retain a generic label.

## Independent Samples / Examples

| Scenario | Actor start / wall / door / enemy / NPC | Role prefix | Display source |
|---|---|---|---|
| harbor | 0 / 1 / 4 / 8 / 6 | a distinct actor/object/space namespace | accepted settlement06db229b88e2df71 |
| grove | 6 / 7 / 4 / 2 / 0 | another distinct namespace | accepted settlementd72c8ca84cee4ea9 |

Harbor:down→cell3,tick1;open→gate1,tick2;right→cell4,tick3;down→cell7,tick4;
attack→actorHP2/enemyHP3/stamina1,tick5;attack→1/1/0,tick6;rest→1/1/1,tick7;
attack→1/0/0,tick8,no last counter. Grove:up→cell3,open,right→4,up→1;
same attacks/rest give identical arithmetic/ticks with different IDs/cells.
Grove NPC cell0→(0,0)mm;enemy2→(2000,0)mm;harbor NPC6→(0,2000)mm.
Each bell consumes1second and replies once;wake count=tick//2;next wake is next even tick.
Attempt right from harbor0 or grove6 hits wall,consumes1tick;old enemy ID submitted in either
new scenario→INVALID_TARGET without tick/revision/resource change. Wrong scenario resume/load
cannot change saved bytes or current owner. Exact retry adds no attack/time/NPC response.

## Exact Edit Scope / Verification

NEW domain/scenario.py,app/scenarios.py,tests/integration/test_scenarios.py and this contract;
MODIFY app/watch.py,encounter_registry.py,watch_registry.py,client_session.py,client_worker.py,
client_text.py,client.py,engine_bridge.py;engines/encounter.py,watch.py;
orchestration/trial.py,encounter.py,watch.py;contracts/client.py. All source paths under C:/ReverieSaga/src;
tests under C:/ReverieSaga/tests. Unity:Assets/Reverie/Scripts/{BrainConnection,PlayRoom,
LiveVerification,Wire.Generated}.cs;Editor/PlaytestBuild.cs if scenario-native entry requires it;
clients/unity/README.md plus root README.md,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md,
parent order,docs/WORKSTATION_SETUP.md and NEW docs/reviews/RS-REVIEW-CP03_REQUEST.md/QT-F02_EXECUTION_2026-10-13.md
and QT-F02_INPUTS.json under C:/ReverieSaga.
Generated DTOs only via existing engine_project exporter. Runtime packages/goldens/save store/
turn driver/authority/pins/dependencies/CI/reference originals are forbidden edits.

Verify definition rejection boundaries,independent samples,swapped lexical roles,actual registered
save/load/resume/retry/replay and pipe callers. Run shared/selective Ruff,affected selective format,
strict mypy,both Import Linter configs,full pytest and actual Unity cases with fresh directories
per README. Record test/native performance facts;no second-device or standalone acceptance inference.
Self-review is not Claude acceptance. Prepare actual CP03 files/vectors/hashes/results for director
feedback after native qualification;hold further world/bulk expansion. No commit/push or external call.
