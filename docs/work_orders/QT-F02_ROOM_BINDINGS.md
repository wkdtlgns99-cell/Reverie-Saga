# QT-F02 — First Runtime Unit: Room Bindings

Date:2026-10-15 | State:DONE for this first runtime unit;parent IN_PROGRESS,CP03 feedback pending.
Executor:Sol;self-review/native checks,not independent review.
Parent:[QT-F02](QT-F02_SCENARIO_GENERALIZATION.md). This unit supersedes its runtime DRAFT
only for the exact contract below;larger maps,multiple targets,quests and bulk content stay later.
Authority:MASTER §§2–4/13;v2.6/A10;BLOCK04 A9/BLOCK05 A10;ENGINEERING_RULES.

## Baseline and scope

HEAD1ad22446d48c50b8b72a6d3af8de3c9d775134ea. Four existing dirty QT-F02 documents are prior
assistant work;preserve them and the pre-update stash. Refresh status before each delivery.
Prerequisites:CORE/CLIENT003/CP04 and QT-F06 six-description sample accepted;Python3.13.12/Tk8.6.
Read parent source map,README verification,WORKSTATION_SETUP,SOL_CODING_WORK_ORDER,actual
encounter/watch/trial registries/engines/orchestration,client session/worker/text and durability.
Goal:two different authored room layouts/role IDs run through shared existing rules,including
durable save/load/replay and Python client intent/projection. No legacy mechanics/content imports.
Non-goals:geometry beyond3x3,more than one instance per role,external JSON/package importer,
new combat balance,quest consequences,C# changes/final graphical acceptance or publication.

Allowed NEW under C:/Reverie Saga:src/domain/scenario.py;tests/unit/test_scenario.py;
tests/integration/test_scenario.py;this order;docs/reviews/QT-F02_ROOM_BINDINGS_2026-10-15.md.
Checkpoint deliverables also allowed:docs/reviews/RS-REVIEW-CP03_REQUEST.md;
docs/reviews/RS-REVIEW-CP03_INPUTS.json;docs/reviews/RS-REVIEW-CP03_DIFF.patch;
tmp/reviews/RS-REVIEW-CP03_2026-10-15.zip.
Local qualification repair:restore only the dossier's LF→CRLF representation when its exact
result matches the existing approved candidate_dossier_sha256;preserve original bytes in
ignored evidence. No narrative field,qualification,witness or Git-normalized blob may change.
Allowed MODIFY under that root:src/app/{encounter_registry,watch_registry,watch,client_session,
client_worker,client_text,client}.py;src/orchestration/{trial,encounter,watch}.py;
src/engines/{encounter,watch}.py;README.md;docs/WORKSTATION_SETUP.md;BACKLOG.md;
SESSION_HANDOFF.md;GAME_SYSTEM_SUMMARY_KO.md;parent order.
Forbidden:other runtime/config/locks,SQLite envelope/migration changes,old fixture/golden bytes,
reference checkout,compiled narratives/frozen witnesses/ZIPs,stash,remote settings/commit/push.

## Runtime contract

- Frozen exact-type `Scenario` fields:scenario_id:str;actor_id,space_id,gate_id,enemy_id,
  npc_id,lantern_id:EntityId;initial_cell,wall_cell,gate_cell,enemy_cell,npc_cell:int.
  No defaults for these fields. Role cardinality is exactly one per field;all six identities
  are distinct exact strings following require_namespace. scenario_id is also a namespace.
  All cells are exact integers0..8,bool/subclasses rejected. Wall/gate/enemy/NPC are distinct;
  initial actor differs from wall/gate/enemy;NPC remains nonblocking as in CORE04.
- Validation order:scenario_id;role IDs in field order;identity uniqueness;cells in field order;
  static occupancy;actor occupancy. Raise ValueError with stable `SCENARIO_ID`,
  `SCENARIO_ROLE_ID`, `SCENARIO_DUPLICATE_ID`, `SCENARIO_CELL`, `SCENARIO_OCCUPANCY`
  respectively. No coercion/truncation/automatic correction.
- Fixed geometry3x3,row-major cell=z*3+x,cell_mm1000. Exactly one wall,exposed as tuple.
  Original combat values/rules,one-second actions/wait bounds,NPC period2/charge cap3 retained.
  `LEGACY_SCENARIO` derives original role IDs/cells from canonical constants,initial0.
  `COURTYARD_SCENARIO`:scenario:courtyard;actor:courtyard-player;space:courtyard;
  object:courtyard-door;actor:courtyard-guard;actor:courtyard-bellkeeper;
  object:courtyard-lamp;initial6,wall7,gate2,enemy0,NPC8.
  `scenario_by_id(str)->Scenario` accepts exactly registered IDs;otherwise
  ValueError `UNKNOWN_SCENARIO`. Selection is explicit,never guessed from untrusted save text.
- `watch_bundle(scenario=LEGACY_SCENARIO)` and `encounter_bundle(scenario=LEGACY_SCENARIO)`
  bind the same validated metadata into engines,admission,codecs,reducers,checkpoint and cues.
  No engine imports another engine. Read-only metadata is immutable;mutable state remains
  COMMIT-owned. Checkpoint role lookup uses schema/entity identity,not lexical role ordering.
- `bootstrap_watch(spec,*,rng=None,scenario=LEGACY_SCENARIO)` keeps explicit initial_cell
  semantics;client construction supplies the selected scenario's initial_cell. Validate before IO.
  `ClientSession(path,*,scenario=LEGACY_SCENARIO)` and ClientWorker same optional keyword;
  Tk CLI `--scenario` chooses the registered ID,default legacy. View/wire DTOs stay unchanged.
  Python client targets,names,stream actor and projection come from selected bindings.
- Legacy default schema/rules descriptors and all pins/golden bytes remain identical. Custom
  descriptors replace gate/NPC cell bounds and role/placement rules;include the entire Scenario
  under a version1 scenario marker in rules. World identity already hashes rules/catalog pins.
  This is shipped static rules metadata,not an external accepted gameplay package.
- SQLite format/envelope stays unchanged. Caller selects the same scenario when resuming.
  Wrong-scenario open/load rejects via existing pin boundary `UNSUPPORTED_RULESET`
  boundary,never silently repins. Load failure preserves attachment,view,protocol and files.
  Same-scenario slot load retains private-branch/retry-reset behavior. Existing worker ownership
  and failure handling retained. Unavailable registered scenario is UNKNOWN_SCENARIO before IO.

## Independent examples and checks

Courtyard from6:right is wall7,actor remains6 and tick advances1;up reaches3,then up is blocked
by living enemy0. From3:right4,up1;closed door2 blocks right. Open from1 yields gate2 cue at
(2000,0)mm. From3,attack enemy0 maps(3,5,2)->(2,3,1);next attack->(1,1,0);rest->(1,1,1);
third attack->(1,0,0),without counterattack. Bell yields one reply;NPC at8 cues(2000,2000)mm.
Legacy down/open/right/down still reaches7 next to enemy8. Reject old gate/enemy/NPC IDs in
the courtyard without mutation. Use opposite lexical actor/enemy ordering in an additional
programmatic scenario to detect positional checkpoint assumptions.

Algorithm:qualify tools/pins → record independent tests → parameterize existing paths →
wire explicit client selection → targeted regression/replay → README gates/full regression →
source/fixture preservation/self-review → synchronized progress/evidence.
Tests:unit/test_scenario.py exact types/IDs/cells/occupancy/pins/codecs;integration/test_scenario.py
literal outcomes,full client/worker/save/load/retry/recovery,replay fresh process/hashseed,
wrong-scenario failure-state preservation and lexical-order independence. Existing suites remain.
Performance:still10component records,1pending wake,3x3/1wall,existing execution/frame capacities;
no per-turn registry rebuilding/content IO. No new performance qualification claimed.
Verification:README Ruff shared/selective,format changed Python,strict mypy,imports3+1,
focused scenario plus encounter/watch/client/durable/replay tests,and full regression for CORE.
Actual results must be recorded separately;do not weaken old or new assertions to pass.
Acceptance:all examples/callers/pin compatibility/failure-state checks pass;unchanged historical
goldens;actual commands/limits;backlog/handoff/Korean summary updated together. Headless/Python
client acceptance does not imply native Tk interaction or Unity scene acceptance.
CP03:prepare actual packet after the first generalized playable segment/client qualification;
hold further scenario/world/bulk expansion for feedback/repair. This first Python unit does not
claim CP03 DONE. CP05 not triggered:SQLite format/quest/memory semantics unchanged.
Stop:unresolved contradictory contract,overlapping edits or unavailable verification after
safe alternatives;report actual evidence. Delivery:brief Korean implemented behavior/checks/
limits/position;no agents,publication or unrelated features.

Implementation note:legacy unformatted registry/watch/orchestration blocks retain their
existing layout to avoid unrelated formatting churn;format gates cover the original README
selection plus new files. All changed Python still passes shared/selective Ruff and strict
types. Class defaults retain legacy subclass behavior when an old subclass owns its own
constructor;normal configured registration passes the same frozen Scenario explicitly.

## Acceptance

[Execution receipt](../reviews/QT-F02_ROOM_BINDINGS_2026-10-15.md):38focusedPASS12.85s,
affected84PASS3.93s,final full1330PASS362.34s,Ruff/shared+selective/format15/strict mypy106/
imports3+1/20pins/pip check PASS. Exact frozen dossier bytes restored without content/hash
edits;initial failures retained. Real Tk buttons and SQLite recovery/fresh-process replay
qualified;Unity courtyard NOT_RUN. [CP03 packet](../reviews/RS-REVIEW-CP03_REQUEST.md)
prepared;actual feedback/verified repair required before expansion. No commit/push.
