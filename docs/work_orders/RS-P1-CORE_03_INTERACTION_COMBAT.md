# RS-P1-CORE / CORE-03 — Gate Interaction & Bounded Encounter

Date:2026-10-04 (Asia/Seoul) | Owner/executor/reviewer:Sol | Instruction:EXECUTED | Implementation:DONE
Director subsequently requested execution of this READY instruction. CORE-03 is implemented/accepted; actual evidence in §9 supersedes the retained authoring snapshot. Parent RS-P1-CORE remains IN_PROGRESS; CORE-04–05 DRAFT. Self-review is not independent-person review.

Inputs:[CORE-02 acceptance](RS-P1-CORE_02_GRID_MOVEMENT.md#9-core-02-execution--acceptance--2026-10-04), [parent slice](RS-P1-CORE_VERTICAL_SLICE.md), [source API](PHASE0_CONTRACTS.md#core-01-source-api-supersession--2026-10-04), [coding template](../prompts/SOL_CODING_WORK_ORDER.md), [MASTER](../MASTER_GAME_ARCHITECTURE.md) §§1–3/8–9/13, [B02](../../architecture/BLOCK_02.md) A1–A3, [B03](../../architecture/BLOCK_03.md) A5–A6, [B04](../../architecture/BLOCK_04.md) A7, [B05](../../architecture/BLOCK_05.md) A10–A11. Complete literal documents/normal/boundary/error traces/source:[RS-P1-CORE_03_REFERENCE_VECTORS.json](RS-P1-CORE_03_REFERENCE_VECTORS.json).

## 1. Actual Source / Design Decisions

HEAD efd2478ff8a6ed93ee833c3f8464a0efdd8a181a/main unchanged; primary prompt/MASTER contain preexisting tracked user edits, most runtime/tests/docs are untracked. Preserve all. Root AGENTS.md absent; historical AGENTS is reference. Remote freshness unchecked. Entry:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; pytest143passed in23.94s/exit0; Ruff exit0; strict mypy51files/exit0. Reuse Python3.13.12/Ruff0.16.6/mypy2.4.0/pytest9.1.1/13hashlocked packages. No new dependency/tool compatibility claim required for this pure-Python extension. Existing Python launcher location diagnostic remains stderr; checks/CLI pass.

Observed constraints and resolved conflicts:
- Driver/RegisteredStateIO require exactly one selected FeatureBundle, immutable registrations and exact descriptor/field/payload coverage. Build one encounter bundle, explicitly reusing qualified trial components/ports; never pass trial_bundle plus encounter_bundle or mutate the trial selection.
- Scheduler rejects two RESOLVE writers of the same field even with disjoint action kinds. Attack and rest cannot be separate stamina writers. NEW EncounterActions handles attack/interact/rest and owns HP/stamina/gate; NEW EncounterMovement owns position.cell. Their fields do not overlap.
- Generic driver disallows different same-component field writes in one phase; its sparse editor would otherwise overwrite records. Store HP, stamina and gate state in separate components. Attack updates HP for two different entity addresses plus stamina for the actor; no same-record merge. No generic driver/editor changes.
- TrialMapRecord/TrialMapAdapter stay fixed with wall1; existing MoveBlocked codec considers occupied only at wall1. A door/enemy needs NEW encounter facts/cues/movement, while geometry, map/position DTOs/keys/adapters/codecs/patch and cell projection remain reused. Do not broaden old fact semantics/pins/goldens.
- Original CellReducer/position field owner remains trial.movement. NEW EncounterMovement uses that stable owner ID within the explicit encounter selection; NEW EncounterCellReducer adds player-only subject checks to its public methods while delegating qualified cell behavior. Existing field descriptors/codecs/CellPatchRoute remain reusable without schema redefinition. No private trial helper import.
- HP0 means defeated; stamina0 means exhausted. Derive statuses from scalar owners; never store duplicate alive/exhausted flags or delete dead bodies. Enemy HP0 releases its cell for movement; dead player cannot initiate new actions. Existing retained receipt lookup precedes admission, so a death-causing attack can be retried safely after death.
- A7 admission validates starting range/resources/target. Invalid attack/interact has no time/cost/highwater; normal blocked movement is consuming. Repeat open/close to the already desired state and full-stamina rest are legal consuming no-ops with facts/cues/empty changes. No initial resource failure is hidden as success.
- Retaliation is deterministic inside one successful attack result, only when the target survives. It is not a separately scheduled NPC turn/event subscriber. CORE-04 will settle autonomous/delayed/passive behavior; this unit does not implement it.
- New encounter pins describe a separate explicit selection/world/checkpoint. Reused trial.map/position structural TypeKeys preserve their original field metadata/owner and codec meanings; new encounter components/payloads and expanded movement manifest have new complete fingerprints. Old trial fixtures remain readable only through their original selection. No implicit migration/hot reload/default registry change.

All new numerical values below are prototype requirements authored here, not v1 formulas/balance or final combat rules. MASTER's injuries/equipment/poise/survival/status effects/BDI/social/world capabilities remain required future work. This unit covers derived alive/defeated and ready/exhausted only.

## 2. Complete Work Order

| Required field | Concrete contract |
|---|---|
| task_id/title | RS-P1-CORE / CORE-03:one gate and one deterministic melee encounter through the accepted movement/turn/replay path |
| status/executor/review | DONE (CORE-03 only); Sol implementation/diagnosis/integration/self-review; independent-person review UNVERIFIED |
| goal/non_goals | Typed/JSON move→open/close gate→attack/counter→rest→enemy/player defeat→record/replay. Excludes autonomous NPC/pending/delayed events, variable duration, stochastic hit/crit, armor/skills/items/guard/loot/XP, persistent status effects/injury/healing/revival, multi-space/pathfinding, DB/save/migration, client/IPC/Factory/provider/governance |
| baseline/prerequisites | CORE-01/02 DONE; actual143tests/Ruff/mypy51files PASS; refresh all85input raw hashes in artifact and HEAD/status at execution entry |
| read_files | This order/artifact, parent §§1/5/6/11–13, listed architecture sections/template; actual domain/{primitives,state_types,canonical,trial}, contracts/{messages,turn,read_views,state_io,skeleton,trial,replay,errors}, engines/trial, orchestration/{turn,serialization,scheduler,trial,read_views,replay,rng}, app/{headless,trial,trial_registry,feature_registry}; all existing tests/config/lock/oracles READ |
| allowed_edit_paths/forbidden_paths | Exact §3;6NEW feature modules/4NEW test modules/2NEW fixtures and5delivery docs. All existing runtime/tests/init/config/lock/oracles/specs/reference/policy/CI/tool paths READ |
| public_contract | §4:three new records/views,23registered payloads (3reused/20NEW),two engines,exact trusted ports/selection/EncounterBootstrapSpec/bootstrap_encounter/main; unchanged generic APIs |
| behavior/algorithm_steps | §5:strict admission→one-second action→dynamic blockers or gate/attack/rest scalar deltas→facts→same atomic head COMMIT→guarded cues; exact damage/counter/zero-cost rejection/derived death semantics |
| edge_policy/examples | §5–6:IDs/profile/option/shape/resources/range/death/retry/clamp/identity/occupancy/failure ordering;112movement/30attack/30interaction/3rest vectors,24main+5death full steps/publications |
| wiring | encounter_registry→app.encounter builds explicit checkpoint/IO→existing app.headless._restore/Driver→registered ports/presenter→explicit IO Recorder/fixture codecs/restore_checkpoint/replay_runner; one selection/fresh owners |
| performance |7component records/2RESOLVE nodes;≤3deltas/2facts/2cues per admitted command,record_only/pending0/no draws. Inherited Brain512MiB/p95≤100ms/p99≤250ms/fast-feedback≤20s are TARGETs; record local Ruff+golden feedback only, no new benchmark/resource tooling |
| baseline_commands/verification_commands | §7; record actual exits/count/timing at entry/final, no implied future node execution |
| test_responsibilities/acceptance | §6–7:original143unchanged; independent integrated paths, precise rejected vs consuming/no-op semantics, two-entity HP atomicity/ownership/finally/presentation/checkpoint/source-pin/replay failures |
| stop_conditions | Unexplained source/hash/baseline drift, generic merge/multi-bundle/API change needed, source pins/independent expected bytes disagree, overlapping user edit/unexplained failure. Diagnose in-scope alternatives; unresolved evidence requires a focused refreshed order/one concrete decision |
| delivery | Exact source/APIs/callers/live CLI/full expected-publication/replay comparison and scope hashes; only CORE-03 DONE after real acceptance, parent IN_PROGRESS. No agent/install/dependency/commit/push/external write/new policy/CI/custom tool |

## 3. Exact Edit Scope

Historical AUTHORING scope:NEW this order/vector artifact;MODIFY BACKLOG/SESSION_HANDOFF/parent only. Subsequent director execution request activated the exact implementation scope below; actual delivery in §9. Existing runtime/tests/config/CORE-02 order/vectors/specs remain READ.

NEW production (created in execution):
```text
C:\Reverie Saga\src\domain\encounter.py
C:\Reverie Saga\src\contracts\encounter.py
C:\Reverie Saga\src\engines\encounter.py
C:\Reverie Saga\src\orchestration\encounter.py
C:\Reverie Saga\src\app\encounter_registry.py
C:\Reverie Saga\src\app\encounter.py
```

NEW tests/helper/independent fixtures (created in execution):
```text
C:\Reverie Saga\tests\unit\encounter_fixtures.py
C:\Reverie Saga\tests\unit\test_encounter.py
C:\Reverie Saga\tests\integration\test_encounter.py
C:\Reverie Saga\tests\replay\test_encounter.py
C:\Reverie Saga\tests\replay\fixtures\encounter_v1.json
C:\Reverie Saga\tests\replay\fixtures\encounter_death_v1.json
```

MODIFY delivery docs on future implementation only:
```text
C:\Reverie Saga\BACKLOG.md
C:\Reverie Saga\SESSION_HANDOFF.md
C:\Reverie Saga\docs\work_orders\RS-P1-CORE_03_INTERACTION_COMBAT.md
C:\Reverie Saga\docs\work_orders\RS-P1-CORE_VERTICAL_SLICE.md
C:\Reverie Saga\docs\work_orders\PHASE0_CONTRACTS.md
```

All other paths READ, especially previous trial sources/tests/fixtures, all shared orchestration/contracts, package initializers, three predecessor reference artifacts/Phase0 oracle, configs/lock, primary/MASTER/template/architecture/historical AGENTS, C:\Quilltale and policy/CI/assets/tools. Additional source/API edits require a focused order; do not broaden generic dispatch or replace old oracles/tests. Cache artifacts remain local/ignored.

## 4. Exact Feature Contracts

Frozen slotted dataclasses, immutable children, ordinary existing domain primitives/abstract payload families; no Any/new central union/duplicated primitive. Domain imports domain only; contracts imports domain/contracts; engines imports domain/contracts; trusted codecs/views/ports in orchestration.encounter; app composition only. JSON exists only at trusted I/O boundaries.

### 4.1 domain/encounter.py

Reuse ACTOR_ID=actor:trial,SPACE_ID=space:trial,TrialMapRecord(3,3,1000,(1,)),CellPositionRecord,cell_coordinates from domain.trial. NEW constants:ENEMY_ID=EntityId("actor:sentinel"),GATE_ID=EntityId("object:gate"),ATTACK_PROFILE_ID="attack:basic",GATE_CELL=4,ENEMY_CELL=8,ACTOR_HP_MAX=3,ENEMY_HP_MAX=5,STAMINA_MAX=2,ATTACK_DAMAGE=2,COUNTER_DAMAGE=1,ATTACK_COST=1,REST_RECOVERY=1.

| NEW frozen record / schema TypeKey(kind,1) | Exact fields / bounds |
|---|---|
| GateRecord / encounter.gate | entity_id:EntityId,space_id:EntityId,cell:int exact4,is_open:int0..1 (bool rejected) |
| HitPointsRecord / encounter.hp | entity_id:EntityId,hp:int0..5; policy additionally caps actor HP3 |
| StaminaRecord / encounter.stamina | entity_id:EntityId,value:int0..2; only player entity |

Pure public functions:
```python
def adjacent_cells(first: int, second: int) -> bool: ...
def resolve_basic_attack(actor_hp: int, target_hp: int, stamina: int) -> tuple[int, int, int]: ...
def life_status(hp: int) -> Literal["alive", "defeated"]: ...
def stamina_status(value: int) -> Literal["ready", "exhausted"]: ...
```

adjacent_cells requires exact ints0..8, returns Manhattan distance in cell coordinates==1 (same/diagonal/row-wrap false). Geometry includes wall cells; placement/access policy is separate. resolve_basic_attack requires actor_hp1..3,target_hp1..5,stamina1..2; returns(actor_after,target_after,stamina_after):target_after=max(0,target_hp−2),actor_after=max(0,actor_hp−(1 if target_after>0 else0)),stamina_after=stamina−1. life_status accepts exact0..5;0→defeated otherwisealive. stamina_status exact0..2;0→exhausted otherwiseready. All invalid bool/float/negative/out-of-range inputs raise ValueError, no clipping/coercion. Only the explicit damage/rest arithmetic clamps valid results.

### 4.2 contracts/encounter.py

Protocols:GateRead exposes properties space_id:EntityId,cell:int,is_open:int;HitPointsRead.hp:int;StaminaRead.value:int. Typed ComponentKeys GATE/HIT_POINTS/STAMINA use encounter.gate/hp/stamina v1. Reuse CELL_POSITION/TRIAL_MAP/MoveCommand/CellDelta/CellPatch from contracts.trial. Integer state flags remain integer0/1; do not expose mutable record/root or stored duplicate status.

Every payload below has @property schema returning its exact TypeKey(kind,1); fields are closed/required, no defaults/optional loose dict. Reused three payloads retain exact original schemas/fields/codecs; NEW20 are defined here:

| Class / abstract base / kind | Exact fields |
|---|---|
| InteractCommand / CommandPayload / encounter.interact | target_id:EntityId,option:Literal["open","close"] |
| AttackCommand / CommandPayload / encounter.attack | target_id:EntityId,profile_id:str |
| RestCommand / CommandPayload / encounter.rest | none; payload exactly{} |
| GateDelta / StateDelta / encounter.gate-delta | entity_id:EntityId,before_open:int,after_open:int;target=encounter.gate.is_open |
| GatePatch / ComponentPatch / encounter.gate-patch | is_open:int |
| HitPointsDelta / StateDelta / encounter.hp-delta | entity_id:EntityId,before_hp:int,after_hp:int;target=encounter.hp.hp |
| HitPointsPatch / ComponentPatch / encounter.hp-patch | hp:int |
| StaminaDelta / StateDelta / encounter.stamina-delta | entity_id:EntityId,before_stamina:int,after_stamina:int;target=encounter.stamina.value |
| StaminaPatch / ComponentPatch / encounter.stamina-patch | value:int |
| EncounterMoved / FactPayload / encounter.moved | actor_id:EntityId,space_id:EntityId,from_cell:int,to_cell:int |
| EncounterMoveBlocked / FactPayload / encounter.move-blocked | actor_id:EntityId,space_id:EntityId,from_cell:int,dx:int,dz:int,reason:Literal["boundary","wall","door","occupied"] |
| GateChanged / FactPayload / encounter.gate-changed | actor_id:EntityId,target_id:EntityId,before_open:int,after_open:int |
| AttackResolved / FactPayload / encounter.attack-resolved | actor_id:EntityId,target_id:EntityId,profile_id:str,actor_hp_before:int,actor_hp_after:int,target_hp_before:int,target_hp_after:int,stamina_before:int,stamina_after:int |
| Rested / FactPayload / encounter.rested | actor_id:EntityId,before_stamina:int,after_stamina:int |
| Defeated / FactPayload / encounter.defeated | entity_id:EntityId,killer_id:EntityId |
| EncounterMoveCue / PresentationPayload / encounter.move-cue | actor_id:EntityId,space_id:EntityId,from_cell:int,to_cell:int,from_x_mm:int,from_z_mm:int,to_x_mm:int,to_z_mm:int,result:Literal["moved","boundary","wall","door","occupied"] |
| GateCue / PresentationPayload / encounter.gate-cue | actor_id:EntityId,target_id:EntityId,cell:int,x_mm:int,z_mm:int,before_open:int,after_open:int |
| AttackCue / PresentationPayload / encounter.attack-cue | actor_id:EntityId,target_id:EntityId,actor_cell:int,target_cell:int,actor_hp_before:int,actor_hp_after:int,target_hp_before:int,target_hp_after:int,stamina_before:int,stamina_after:int,result:Literal["hit","actor_defeated","target_defeated"] |
| RestCue / PresentationPayload / encounter.rest-cue | actor_id:EntityId,before_stamina:int,after_stamina:int |
| DefeatCue / PresentationPayload / encounter.defeat-cue | entity_id:EntityId,killer_id:EntityId,cell:int,x_mm:int,z_mm:int |

Delta target includes its entity_id and exact family. Scalar payload bounds match component fields; identity/range-valid net compositions encode but cannot be published as net changes. Facts/cues use qualified player/space/gate/enemy IDs; Defeated permits (enemy,player) or(player,enemy) only. Command target/profile syntactically namespaced/NFC but may be unresolved so admission can return INVALID_TARGET/INVALID_ATTACK_PROFILE. Invalid option/shape/schema/bool/float remains INVALID_COMMAND at command boundary.

Codec semantic rules:EncounterMoved distinct adjacent base-free cells (exclude wall1; dynamic occupancy belongs engine/policy). EncounterMoveBlocked cardinal from base-free cell with boundary reason iff outside axis bounds; wall iff in-bounds target1;door iff target4;occupied iff target8. Dynamic gate/enemy state verified by engine/presenter, not read by codec. GateChanged flags0..1 include identity. AttackResolved exact pure attack formula above; all IDs/profile fixed. Rested after=min(2,before+1). Cues validate exact geometry/scalar formulas and result:blocked move equal endpoints;AttackCue adjacency to8 and exact formula/result; GateCue cell4/(1000,1000);DefeatCue enemycell8 or player base-free cell;RestCue same Rested formula. No arbitrary/default result/version/code or unreachable placeholder.

### 4.3 engines/encounter.py — Two Frozen Engines

Both phase RESOLVE,laneA,cost_class local,depends_on(),consumes(),on_matching_events=False,every_tick=False,no RNG/definition/clock access. They receive only existing EngineInvocation and return EngineResult.

| Class / engine_id | Action kinds / exact read families / writes / emits |
|---|---|
| EncounterActions / encounter.actions | actions encounter.attack/interact/rest; reads encounter.gate.{cell,is_open,space_id},encounter.hp.hp,encounter.stamina.value,trial.position.{cell,space_id}; writes encounter.gate.is_open,encounter.hp.hp,encounter.stamina.value; emits encounter.attack-resolved/defeated/gate-changed/rested |
| EncounterMovement / trial.movement | action trial.move; reads encounter.gate.{cell,is_open,space_id},encounter.hp.hp,trial.map.{blocked_cells,height,width},trial.position.{cell,space_id}; writes trial.position.cell; emits encounter.move-blocked/moved |

Global RESOLVE A ranks:actions0,movement1 even when only one is activated. Manifests include only these unions; actual action branches may read subsets. Engines recheck admitted actor alive/subjects/reference/range/resources at execution. Under this unit's two RESOLVE action-exclusive activations, no prior passive state change can invalidate admission. Unexpected admitted-condition disagreement raises CandidateError("INVALID_ACTION",detail) and aborts; future PRE_TICK fizzle semantics require CORE-04's own order, not silent resource failure here.

### 4.4 orchestration/encounter.py — Concrete Trusted Ports

All signatures exactly existing ReadAdapter/ComponentCodec/PayloadCodec/CommandRoute/DeltaRoute/PatchRoute/CheckpointPolicy/Presenter protocols; no new generic API.

- GateAdapter/HitPointsAdapter/StaminaAdapter validate exact frozen record classes/schema/entity syntax/scalar bounds, then wrap only their typed read Protocols. Gate space namespaced/cell4. Observe exact FieldAddress/path()/read before every property; setters/deleters observe write then ReadOnlyViolation. Retained aliases always ExpiredReadView after close. Reuse original trial typed adapters/membership guard unchanged.
- GateCodec/HitPointsCodec/StaminaCodec decode/encode exact record fields/versions/ranges; no defaults/coercion. GatePatchRoute/HitPointsPatchRoute/StaminaPatchRoute map exact patch schema to their family and immutable replacement of only that field. Reuse CellPatchRoute for position; no maps/space/placement mutation.
- EncounterPayloadCodec(schema:TypeKey) registers exactly the NEW20payloads. Feature-local concrete branching permitted; no fallback/import of core dispatch or central union. Reuse TrialPayloadCodec for trial.move/position-delta/position-patch only. Encoding checks exact class/schema and semantic rules; decoding verifies closed fields, immediately owned typed values. Unknown/mismatched class/schema errors SchemaError("UNSUPPORTED_SCHEMA",path); malformed shape/value raises ValueError.
- EncounterAdmission(schema:TypeKey) implements one route for each of4action kinds. Reads for all include encounter.hp.hp;move adds position.cell/space_id;rest adds stamina.value;interact adds gate.cell/is_open/space_id and position.cell/space_id;attack adds stamina.value and position.cell/space_id (reads target HP with same HP family). Existing Driver handles authorization/stream/revision/retry/overflow first. Semantic action key uses unchanged a1-/action-key/v1 framing of(world_id,target_tick,actor_id,payload_hash),payload_hash=hash_document(payload/v1,{schema,payload});one-second TurnPlan. Return TurnRejected(failure(code),command.expected_revision) for the exact §5 admission errors, no time/cost/stream mutation.
- EncounterCellReducer subclasses existing CellReducer public methods;schema trial.position-delta/1 and inherited owner_id trial.movement remain unchanged. Each public stage/compose/is_identity/validate_net first requires CellDelta/entity ACTOR_ID (compose checks every input),otherwise CandidateError INVALID_DELTA;then delegates existing qualified cell behavior. Do not read gate/HP/space from reducer;target-only observation/composition/identity semantics preserved.
- GateReducer/HitPointsReducer/StaminaReducer schemas correspond to their deltas;owner_id encounter.actions. stage validates exact class/schema/subject/scalar/expected old;reads ONLY delta.target. Gate stage requires0↔1;HP stage requires decreasing by1or2 (actor by1,enemy by1or2);stamina stage requires±1. Component/subject bounds retained. Empty/invalid/noncontiguous/different-target compositions raise CandidateError("INVALID_DELTA",detail);compose returns first.before→last.after,including identity. Encoders permit bounded net compositions without imposing per-stage step size. is_identity validates and returns exact bool. validate_net rejects identity,reads ONLY target,checks committed field==after. No reducer cross-record reads or stored damage/default assumptions in generic code.
- EncounterCheckpointPolicy.validate(core,protocol) enforces exactly7canonically ordered records shown in the artifact:one fixed TrialMapRecord(space),two CellPositionRecords(player/sentinel),GateRecord(gate),HitPointsRecord(player/sentinel),StaminaRecord(player). ActorHP0..3,targetHP0..5,stamina0..2,gateopen0/1;fixed gatecell4/enemycell8,allspace references==space:trial. Player base-free;cannot occupy4when closed or8while enemyHP>0. Enemy remains at8 even when defeated; HP0/body persistence/free occupancy intentional. Streams only actor:trial. Pending/packages/build artifacts empty; generic IO enforces canonical sorting/unique records/IDs/pins/world/protocol/receipts. No stored status fields or default filling.
- EncounterPresenter consumes all6facts,derives the5cue classes from committed guarded position/map/gate/HP/stamina; verifies subjects/result/scalar after-values/geometry and death. For AttackResolved,one AttackCue;Defeated adds a second DefeatCue. Iterate fact order,one cue each. p1-/cue-id/v1(source_event_id,encounter.presenter,local_sequence);PRESENT rank0/wave0/tick receipt.tick,caused_by=(source_event_id,),degraded(),priority important,coalesce keep_all,key"". Source facts are root due-now facts with caused_by()/degraded() until later event routing. Failure remains postcommit PRESENTATION_FAILED with receipt/facts/diff retained; no custom swallowing or rollback.

### 4.5 app/encounter_registry.py — One Explicit Selection

encounter_bundle()->FeatureBundle:feature_id encounter.local;two bindings;5component schemas with typed adapters/codecs;11FieldSpecs;4command routes;4delta routes;4patch routes;one presenter binding encounter.presenter;23payload codecs;6record_only event policies(PRESENT/priority0/late reject/empty subscribers+cancellers),producer actions except moved/move-blocked→movement;EncounterCheckpointPolicy. Exactly one descriptor for each schema/registered payload, no unused trial fact/cue/presenter/engine/policy.

All fields CORE/A,scale1,collection_capNone unless blocked_cells cap1. Field metadata exactly artifact:
| Family | Kind/unit/bounds | Owner | Actual consumer IDs |
|---|---|---|---|
| trial.map.width,height | integer/cell_count/3..3 | system.bootstrap | trial.movement,encounter.presenter |
| trial.map.cell_mm | integer/mm/1000..1000 | system.bootstrap | encounter.presenter |
| trial.map.blocked_cells | integer_tuple/cell/0..8,cap1 | system.bootstrap | trial.movement,encounter.presenter |
| trial.position.space_id | string/entity_id/no range | system.bootstrap | encounter.actions,trial.movement,encounter.presenter,system.admission |
| trial.position.cell | integer/cell/0..8 | trial.movement | encounter.actions,trial.movement,encounter.presenter,system.admission |
| encounter.gate.space_id | string/entity_id/no range | system.bootstrap | encounter.actions,trial.movement,encounter.presenter,system.admission |
| encounter.gate.cell | integer/cell/4..4 | system.bootstrap | encounter.actions,trial.movement,encounter.presenter,system.admission |
| encounter.gate.is_open | integer/boolean_integer/0..1 | encounter.actions | encounter.actions,trial.movement,encounter.presenter,system.admission |
| encounter.hp.hp | integer/hp/0..5 | encounter.actions | encounter.actions,trial.movement,encounter.presenter,system.admission |
| encounter.stamina.value | integer/stamina/0..2 | encounter.actions | encounter.actions,encounter.presenter,system.admission |

This table groups map width/height:total11fields. Actor/enemy HP share one family/owner at distinct addresses; enemy position family is writable in metadata but stage subject+checkpoint fix enemycell8. Frozen registry literals SCHEMA_DOCUMENT/RULES_DOCUMENT copied from artifact canonical bytes; schedule literal must match actual compile_schedule. No new package loader/RNG purposes/wire exporter/aggregate registration.

### 4.6 app/encounter.py — Qualified Owner / CLI

```python
@dataclass(frozen=True, slots=True)
class EncounterBootstrapSpec:
    seed_hex: str
    branch_id: str
    stream_id: str
    initial_cell: int = 0
    gate_open: int = 0
    actor_hp: int = 3
    enemy_hp: int = 5
    stamina: int = 2
    initial_tick: Tick = Tick(0)
    initial_revision: WorldRevision = WorldRevision(0)

def bootstrap_encounter(spec: EncounterBootstrapSpec, *, rng: RngService | None = None) -> HeadlessSession: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

Validate exact frozen spec/exact lowerhex seed64,branch32,stream32,exact bounded tick/revision0..2^63−1 and placement/scalar invariants above BEFORE authoritative owner construction. Invalid spec→BootstrapError("INVALID_INITIAL_STATE",detail). Rules initial values specify default setup, not restore invariants; qualified explicit initial HP0/free cell/gate/stamina overrides are recorded by the checkpoint/header. No override of enemy/gate placement/map/formulas.

Build bundle/StateIO/schedule once; world-id/v1 same seed+NEW rules+catalog framing. Build canonically sorted7records and active player stream/highwater0/receipts();no pending/packages. Share already-built IO with existing app.headless._restore;default CounterRngService(seed,world,()) with no draw. Private helper may return(session,io) for bootstrap/CLI, no HeadlessSession API changes.

main rejects flags,defaults zero seed/branch and stream all1;nonblank stdin newline JSON→session.submit_json→canonical io.encode_publication+newline/flush;return0. NEW PYTHONPATH=src python -m app.encounter. Old app.headless/app.trial unchanged. Existing public restore_checkpoint(...,bundles=(encounter_bundle(),)),replay_runner(...,bundles=(encounter_bundle(),)),state_io,Recorder(header,io=io),decode_fixture/encode_fixture(io=io) reuse qualified owners. Generic app RNG allowlist retained on replay is unused by encounter scopes. Fresh owner/services for every restore/run; no private head injection in production.

## 5. Admission / Resolution / Errors

Existing Driver order remains:command/actor/stream/schema/fingerprint→retained receipt/conflict→highwater/retired→stale revision→integer overflow→feature admission. Therefore duplicate checks precede actor HP admission; exact death-causing retries return original receipt,conflicting duplicates return COMMAND_ID_CONFLICT even when dead. All feature failures include current authorized revision; malformed JSON boundary INVALID_COMMAND/current_revisionNone. Typed unsupported schema UNSUPPORTED_SCHEMA.

Feature admission order (after structural codec validation):actor must be player and HP>0 else ACTOR_DEFEATED;each command's space/reference fields must match qualified topology,unexpected inconsistency CandidateError INVALID_ACTION. Move cardinal payload is already qualified;legal boundary/wall/door/live-enemy targets remain admitted. Rest permits any stamina0..2. Interact:target gate else INVALID_TARGET;close while playercell4→TARGET_OCCUPIED;then exact cardinal adjacency to4 else OUT_OF_RANGE. Attack:target sentinel else INVALID_TARGET;profile attack:basic else INVALID_ATTACK_PROFILE;targetHP0→TARGET_DEFEATED;then exact cardinal adjacency to8 else OUT_OF_RANGE;then stamina0→INSUFFICIENT_STAMINA. Unknown/malformed option is codec INVALID_COMMAND. No distance rounding/diagonal reach/client damage/time fields.

RESOLVE exactly one action at target_tick=start+1:
1. Movement reads actual player position/map/gate/enemy HP. Bounds x/z first→wall membership→closed gatecell4→enemycell8 withHP>0,priority boundary/wall/door/occupied. Blocked emits1EncounterMoveBlocked/no delta;success1CellDelta/EncounterMoved. Stamina unchanged, including exhausted movement. No out-of-range map membership call.
2. Interact reads current gate/player topology and adjacency. option open sets1,close sets0;never toggles implicitly. Changed state→1GateDelta,otherwise none. Both emit1GateChanged/cue and consume1second. Occupied closing rejects before execution;checkpoint prevents crushing/invalid actor placement.
3. Attack reads both positions/HP and player stamina. Apply fixed pure formula. Emit nonidentity HP deltas for enemy and,if counter changed it,player;one stamina delta. At most3deltas,distinct component addresses. Emit AttackResolved sequence0;target becomes0→Defeated(enemy,player) sequence1,otherwiseplayer becomes0→Defeated(player,enemy) sequence1. A lethal target hit suppresses counter,so no simultaneous mutual death. No independent enemy tick/attack,hit roll,skill,loot,XP/status record removal.
4. Rest reads HP/stamina,setsmin(2,old+1);1StaminaDelta if changed,else none;1Rested. Consumes1second,does not healHP or invoke counter. Enemy retaliates only during successful attacks;this bounded encounter timing is explicitly pinned,not general NPC behavior.
5. Existing Driver validates candidate/checkpoint/effects/net changes then swaps CORE+protocol once. Diff changes canonically ordered by(component family,field,entity). HP enemy precedes player lexically. Every admitted no-op/blocked action has non-null diff,empty changes,tick/revision+1/highwater/receipt/root advance. Reject/retry diffNone/no effects. Same-feature postcommit cues derived only after head publication.

| Trigger | Outcome |
|---|---|
| cell3 Right,gate0 | COMMITTED door blockage;position3,tick+1,stamina unchanged |
| cell3 open gate4 | COMMITTED gate0→1;repeat open1→1 is committed empty diff |
| cell4 close gate4 | TARGET_OCCUPIED,zero time/cost/highwater |
| cell7 Right,enemyHP>0 / enemyHP0 | occupied blockage / legal7→8 respectively |
| actorHP3,targetHP5,stamina2 attack in range | actorHP2,targetHP3,stamina1;3deltas,1fact/cue |
| actorHP1,targetHP1,stamina1 attack | actorHP1,targetHP0,stamina0;2deltas,AttackResolved+Defeated/2cues,no counter |
| actorHP1,targetHP5,stamina2 attack | actorHP0,targetHP3,stamina1;3deltas,AttackResolved+Defeated/2cues |
| new action when actorHP0 | ACTOR_DEFEATED;no time;queries/status projection remain pure |
| attack at distance0/diagonal/far or no stamina | OUT_OF_RANGE / INSUFFICIENT_STAMINA per priority;no time/cost |
| target/profile unknown,already defeated target | INVALID_TARGET / INVALID_ATTACK_PROFILE / TARGET_DEFEATED;no time |
| rest stamina2 | COMMITTED Rested2→2/empty changes;tick+1,no HP heal/counter |
| exact retained retry / same ID changed payload/revision | original receipt+optionalRESYNC_REQUIRED / COMMAND_ID_CONFLICT;no effects/time |
| unretained stale / rejected ID later corrected | STALE_REVISION/no highwater / same unused ID can commit under existing Driver convention |
| invalid map/HP/reference/duplicate/placement/pins/checkpoint | strict decode/policy before owner/replay execution;ReplayFormatError at public restore/replay boundary |
| engine/reducer/patch/policy/codec fault before COMMIT | TurnAborted/stable CandidateError code elseENGINE_EXCEPTION;old CORE+protocol/highwater/receipt retained |
| max tick/revision | INTEGER_OVERFLOW abort,old pair retained |
| presenter/cue codec failure | COMMITTED receipt/facts/diff retained,PRESENTATION_FAILED/cues empty |

No timing/RNG/UUID/global mutable state/event trimming. Unknown fields/version/classes never default. No target tie:one player/one named gate/enemy/exact option/profile. Empty command Rest has explicit semantics;emptycompose invalid. Candidate disagreement never clips/commits partial HP or invents a successful noop.

## 6. Independent Expectations / Prospective Tests

Reference artifact retains stdlib-only source written from these new requirements before implementation,85raw entry inputs,schema/rules/schedule literal bytes/UTF8/hex/digests and complete main/death publications/witnesses. Never generate an expected oracle with production/Recorder. On implementation copy canonical expected_fixture→NEW encounter_v1.json and death_fixture→NEW encounter_death_v1.json;retain artifact/predecessor fixtures READ. Helpers may parse authoring container with stdlib JSON then immediately seal requested domain sections;do not relax strict float/depth/NFC guards or deserialize its metadata as domain state.

Literal pins:schema a102520b5798c2410080d117cfc2ea41a608486673eac54fdbc567a47e9a7d0f;rules740189264a80c68b4641c1669184c0519340f8bbba657e7d483feab3bc99f77f;schedule706faf28c9673d473b3c771d324a932ac3fd7540c2a22974e62d25e837d7bac1;initial COREcad5f4174c24380d62ce1ecc029b1dd34e409e5a5192c6d8a01f52eede4df5aa. Actual schedule compiler compatibility/source-byte checks recorded at authoring delivery;future runtime bundle/CLI still NOT_RUN.

Main24steps fixes wall/door/open/repeat/no-crush/movement/occupied/combat/exhaustion/recovery/kill/freed-cell/retry/stale/conflict/cap/rest/far interaction. See artifact trace_summary for exact state/tick/revision each index. Key steps:

| Index | Exact result / resulting state (cell,gate,actorHP,enemyHP,stamina) / tick=revision |
|---|---|
|0|wall blocked;(0,0,3,5,2)/1|
|1|out-of-range open rejected;same/1;seq2 uncommitted|
|2–3|seq2 reused Down0→3/2,Right door blocked/3|
|4–6|open0→1/4,repeat open empty changes/5,move3→4/6|
|7–9|close while on gate rejected/6,seq7 reused Down4→7/7,enemy occupied attempt/8|
|10–11|attacks;(7,1,2,3,1)/9→(7,1,1,1,0)/10|
|12–14|attack exhausted rejected/10,seq11 reused rest/11,kill;(7,1,1,0,0)/12;2facts/cues|
|15–17|attack defeated target rejected/12,seq13 reusedmove7→8/13,old attackseq9retry originalreceipt9/no effects/RESYNC_REQUIRED|
|18–23|stale rest rejected/conflictingseq9rest rejected/13;seq14 reusedrest/14,restto2/15,fullrestno-op/16,farclose rejected/16|

Death5steps startcell7/gate0/actorHP1/enemyHP5/stamina2:attack→actorHP0/enemyHP3/stamina1/tick1 with2facts/cues;rest rejects ACTOR_DEFEATED;exact original attackretry retainsreceipt1/no extra time;changedseq1rest rejects COMMAND_ID_CONFLICT;newmove rejects ACTOR_DEFEATED. No fake transition to a separate game-over record.

112movement vectors enumerate4gate/enemy-life configurations × every legal player cell ×4directions;30attack vectors enumerateactorHP1..3 ×enemyHP1..5 ×stamina1..2;30interaction vectors enumerateopen/closed ×legal player cells with enemyHP0 ×open/close,including occupiedclose;3rest vectors cover0/1/2. Precise negative expectation:valid alternative3→6 on main step6 vs actualRight3→4,full updated CORE/protocol/receipt/fact/diff hashes;first mismatch step6 $core.components[6].fields.cell expected6/actual4. Dropping Defeated on mainkillstep14 preserveshead/protocol/diff but reports $facts[1] actual<missing>;retain realcues to verify witness/presentation separation. Dropped blocked fact step0 reports $facts[0]. Missing attack fact/counter HP delta must also be diagnosed,never masked by matching visible target HP.

| NEW planned file | Required meaningful nodes / responsibility |
|---|---|
|tests/unit/test_encounter.py|test_literal_pins_and_records;test_scalar_and_payload_validation;test_attack_vectors;test_status_and_geometry;test_guarded_reads;test_scalar_reducers;test_registry_ownership. Exactclosed fields/IDs/profile/option/zero/negative/bool/float/NFC/schema/class/identity/compose/old value;11metadata fields/23codec coverage;no two stamina writers/foreign delta target/protected field |
|tests/integration/test_encounter.py|test_movement_vectors;test_interaction_vectors;test_full_publications;test_attack_counter_atomicity;test_rejection_no_time;test_death_retry;test_noop_time;test_candidate_failures;test_postcommit_failure;test_cli_and_query. Real112movement/30interaction/30attackstates/3rest;29complete main/death publications;three-address staging/oldroot/faultafterrealcalculation,manifest and reducer-only-target access/finally expiry,postcommit cue errors/MAXclock guards |
|tests/replay/test_encounter.py|test_encounter_core_trace;test_encounter_death_trace;test_recorder_matches_independent_traces;test_defeat_fact_loss;test_wrong_cell;test_checkpoint_before_execution;test_fresh_registry_sessions. Exact29steps/witnesshashes,strictlastwitness/sourcepins/missingmap/invalidHP/occupiedclosedgate/live-enemycollocation fail before first factory command,freshowners/registration permutation/repeatedruns,explicitselectedregistry |
|tests/unit/encounter_fixtures.py|real qualified bundle/session/command/view helpers;purpose-built faulty ports wrapping real behavior;no runtime-derivedexpectedvalues or mocked domain results|

All old143tests/assertions/fixture bytes remain unchanged;never skip/xfail/remove assertions. Source-data vectors plus complete integration required,not DTO-only tests. Architecture-independent-person/product/performance qualification remains UNVERIFIED.

## 7. Implementation / Verification / Acceptance

Execution order:refreshbaseline/hashes/source→newdomainrecords/pure arithmetic→newtyped payloads/views→trusted codecs/reducers/admission/policy/presenter→two engines→oneexplicitregistry/bootstrap/CLI→copy both independentfixtures/add realtests→fullchecks/self-review→update deliverydocs. No new shared framework/helper package/default union/alternate Driver. Private organization inside6modules is discretionary;public schemas/values/errors/literal bytes are fixed.

Entry/final commands:
```powershell
git -c safe.directory='C:/Reverie Saga' rev-parse HEAD
git -c safe.directory='C:/Reverie Saga' status --short
git -c safe.directory='C:/Reverie Saga' diff --check
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.venv/Scripts/python.exe -m pytest -q tests
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m mypy --strict src tests
.venv/Scripts/python.exe -m pytest -q tests/replay/test_golden.py::test_core_trace tests/replay/test_trial.py::test_trial_core_trace
```

Only AFTER prospective files exist:
```powershell
.venv/Scripts/python.exe -m pytest -q tests/unit/test_encounter.py tests/integration/test_encounter.py tests/replay/test_encounter.py
.venv/Scripts/python.exe -m pytest -q tests/replay/test_encounter.py::test_encounter_core_trace tests/replay/test_encounter.py::test_encounter_death_trace
rg -n 'GateRecord|HitPointsRecord|StaminaRecord|encounter\.|actor:sentinel|object:gate' src/orchestration/serialization.py src/orchestration/turn.py src/orchestration/replay.py
$env:PYTHONPATH='src'
@'
{"command_id":"c1:00000000000000000000000000000000:11111111111111111111111111111111:1","actor_id":"actor:trial","expected_revision":0,"schema":{"kind":"trial.move","version":1},"payload":{"dx":1,"dz":0}}
'@ | .venv/Scripts/python.exe -m app.encounter
```

CLI first publication matches artifact mainstep0 completely:wall blockage/globalrank1/onefact+cue/empty changes/tick1/revision1. Also run main/death JSON traces through qualified sessions and exact full-publication comparisons;default CLI runs the main24steps;death5steps use explicit bootstrapHP/cell override. Search generic dispatch0matches/rawhashesunchanged;inspect all untracked NEW sources/tests/fixture bytes (git diff alone misses them). Compare every READ input hash to artifact entry,onlyexplicitdeliverydocs may differ. No new governance checkers/CI/dependency install.

Acceptance before DONE:real typed/JSON/CLI door/attack/rest/dynamic movement/death path;all normal/boundary/invalid/priorities/formulas;consuming no-op/blocked vs no-time rejection;exact inherited receipt/stale/conflict and deathretry order;two-entity HP+stamina sole-head atomicity/scalar-only reducers/protected map/reference/enemyposition;independent complete29step CORE/protocol/facts/diff/outcome and presentation;precise misseddefeat/blockedfact/wrongcell mismatches;lastinvalidwitness/sourcepins rejected beforefirstexecution;freshowners/finally/postcommit preservation;143previous tests/oracles/config/specs unchanged;Ruff/strictmypy/sourceonlyextension/scope checks. All CORE-03 production/tests/CLI results currently NOT_RUN.

## 8. Authoring Delivery Evidence

Entry143tests in23.94s/Ruff/strictmypy51files PASS; inspected actual one-bundle/schema/patch/reducer/phase/editor/replay/app ports. Two-engine writer layout and separated HP/stamina/gate avoid same-field/same-record conflicts without shared-code changes. Independent stdlib source fixes23payload descriptors/11field metadata/newrules/schedule,112movement/30attack/30interaction/3rest cases,main24+death5full steps/publications and a self-consistent wrong-cell prefix before implementation. Retains85raw existing input hashes. Runtime/fixtures/config/oracles/CORE-02/specs remain READ;future6production/4test/2fixture paths are absent.

Actual final reproduction/framing/scheduler/syntax/document/scope/hash checks and readiness decision appended after authoring verification. Full-game/bundle/device/performance/independent-person qualification UNVERIFIED;CORE-04–05 DRAFT. NEXT after this instruction passes:execute CORE-03,then author CORE-04 from its actual accepted source.

Actual authoring verification2026-10-04:retained stdlib source reexecuted and all result sections reproduced;independent struct.pack framing vs retained length.to_bytes recomputed literal UTF8/hex/tagged hashes,29full main/death steps and7step negative-prefix CORE/protocol/fact/diff/receipt/event/cue identities PASS. Actual compile_schedule with real CapabilityManifest/NodeActivation DTOs matches pinned706faf28c9673d473b3c771d324a932ac3fd7540c2a22974e62d25e837d7bac1;this is declaration/scheduler compatibility,not a future engine/bundle runtime claim. Original trial.map/position descriptors compare exactly equal to accepted trial selection;movement owner retained.11field/23payload coverage,2future Python declaration fences AST-parse/compile,12absent prospective source/test/fixture paths,links/fences/whitespace/current statuses PASS. Baseline85inputs matched before authoring;after final delivery-doc edits82remain identical and3changed are exactly BACKLOG/SESSION_HANDOFF/parent order. Runtime/tests/config/lock/original fixtures/oracles/CORE-02 order+vectors/protected specs unchanged. git diff --check exit0;preexisting primary/MASTER LF-to-CRLF notices only.

Vector summary:112movement=52moved/40boundary/10wall/6door/4occupied;30interaction=12admitted/17OUT_OF_RANGE/1TARGET_OCCUPIED;30attack/3rest cases;24main+5death full steps/publications. New artifact680807bytes/SHA2560cf2b2897ef123d8a7c0a30983f0e08558658a7a1a98036df58dee26fa4c01ba. Future canonical fixtures fixed at SHA256aa8cdc879e3bbcdadb19269496a13449f5f1096641226a7eacc29cc44105634c andd21e78ed1362ac2d6eda81eda79996f7081efefe4bcc7a13a7ceba140284919c. No future module/fixture/CLI/test was created or executed.

Decision:CORE-03_INSTRUCTION_ACCEPTED/READY;implementationNOT_STARTED. Exact authoring delivery NEW2(order/artifact)+MODIFY3(parent/BACKLOG/SESSION_HANDOFF). CORE-01/02 DONE,parent RS-P1-CORE IN_PROGRESS,CORE-04–05 DRAFT. NEXT:execute this complete CORE-03 order. No agent/install/dependency/policy/CI/commit/push/external write or performance/independent-person/full-game completion claim.


## 9. CORE-03 Execution / Acceptance — 2026-10-04

Director's subsequent "다음꺼 ㄱ" authorized execution of the READY instruction. This section supersedes the authoring snapshot in §8 and prospective NOT_RUN/NOT_STARTED statements. CORE-03 ACCEPTED/DONE; CORE-01/02 remain DONE, parent RS-P1-CORE IN_PROGRESS, CORE-04–05 DRAFT. Self-review only; independent-person/full-game/device/bundle/p95/p99/memory qualification UNVERIFIED. NEXT:author the source-specific CORE-04 delayed/passive/NPC order, then execute it after its own instruction acceptance/request.

Entry:HEAD efd2478ff8a6ed93ee833c3f8464a0efdd8a181a/main unchanged;143tests in24.01s/Ruff/strict mypy51files PASS. Artifact85historical input hashes differed only for the3prior authoring delivery docs (BACKLOG/SESSION_HANDOFF/parent);82other inputs matched. Artifact SHA2560cf2b2897ef123d8a7c0a30983f0e08558658a7a1a98036df58dee26fa4c01ba; instruction entry SHA256cf632b10e74d7e01209242ada77604bb27e41fdfbf7225060f2ecf27b9d39b60. Preexisting primary prompt/MASTER and uncommitted/untracked work preserved. No source-contract exception/shared API change was required.

Exact delivery:6NEW production modules in §3,4NEW test/helper modules,2NEW copied independent fixtures;5MODIFIED delivery docs=this order/parent/PHASE0_CONTRACTS/BACKLOG/SESSION_HANDOFF. Existing runtime/test/init/config/lock/oracle/spec/CORE-02 order/vector files remain READ. Production never reads the reference artifact. SCHEMA_DOCUMENT/RULES_DOCUMENT are literal canonical bytes fixed at authoring; fixture files copy independent expected_fixture/death_fixture, never Recorder output. No new helper package/tool/policy/CI/dependency/install/agent/commit/push/external write.

Actual wiring:domain encounter records/arithmetic/status→contracts typed payloads/keys→trusted adapters/codecs/admission/scalar routes/checkpoint/presenter→EncounterActions and EncounterMovement→encounter_bundle→EncounterBootstrapSpec/bootstrap_encounter/python -m app.encounter→existing app.headless._restore/Driver with one selected StateIO→explicit registered restore/Recorder/Runner. All23payload/11field registrations are covered. Immutable original trial.map/position ports, cell patch and stable trial.movement owner are reused. Two RESOLVE nodes retain global ranks0(actions)/1(movement);HP/stamina/gate and position have disjoint sole writers. Every admitted action consumes one second; pending remains empty and RNG unused.

Actual evidence:112real movement cases/30real interaction cases/30real attack-counter states/3rest states;24main+5death complete typed publications equal independent canonical bytes; main24JSON commands pass through real subprocess CLI, including first wall blockage/rank1/empty changes. Both canonical fixtures roundtrip exactly and replay without mismatches; Recorder captures all29expected steps. Source schema/rules/schedule and initial CORE hashes match §6 literals. Fixture bytes193858/SHA256aa8cdc879e3bbcdadb19269496a13449f5f1096641226a7eacc29cc44105634c and19058/SHA256d21e78ed1362ac2d6eda81eda79996f7081efefe4bcc7a13a7ceba140284919c.

Strict coverage:closed scalar/payload fields, exact classes/versions, bool/float/NFC/namespace/range/formula/geometry errors; derived status/query no time; dynamic wall/door/living-enemy priority; explicit open/close/occupied-close guard; no-time target/profile/defeated/range/stamina/dead admission priorities; rejected ID reuse; repeat/capped consuming no-ops; exact retry/stale/conflict/death receipt priority; lethal hits suppress counter and release enemy occupancy; actor defeat retains body and blocks new actions. Scalar reducers observe only delta.target, verify expected old, enforce stage steps, bounded net composition/identity and finally expiry; foreign subject/protected field/registry/duplicate writer checks pass. Actual three-address attack calculation/staging followed by engine/undeclared read/foreign target/foreign writer/duplicate/stage/net/policy faults leaves the old CORE+protocol/highwater/receipts/effects intact. Driver rejects a changed admission plan; engine independently rejects a changed admitted target. Postcommit presenter/cue-codec faults preserve committed HP/stamina/receipt/facts/diff and publish PRESENTATION_FAILED with no cues. MAX tick/revision abort without mutation.

Replay negatives:wrong movement step6 reports $core.components[6].fields.cell expected6/actual4; removed blocked fact step0→$facts[0] missing; removed attack fact step10→$facts[0] missing; removed defeat fact step14→$facts[1] missing, with actual committed cues/head intact. Deliberately omitted real counter delta first reports step10 $core.components[2].fields.hp expected2/actual3. Initial pins and malformed last witnesses (missing map, invalid HP/stamina/reference/enemy placement, closed-gate or live-enemy collocation) fail before first factory restore. Repeated runs use fresh owners; reversed bindings/routes/fields/adapters/codecs/event registration preserve pins and results.

Final commands after the final production/test changes:
- PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; .venv/Scripts/python.exe -m pytest -q tests:exit0,431passed in38.94s (143previous+288new),no skips/xfails/deleted assertions.
- .venv/Scripts/python.exe -m ruff check src tests:exit0,All checks passed.
- .venv/Scripts/python.exe -m mypy --strict src tests:exit0,61sourcefiles PASS.
- Ruff plus original/trial/encounter-main/encounter-death golden nodes:exit0,4passed in1.92s,2.7793083s local wall feedback; this is not latency/device qualification.
- Generic serialization/turn/replay search for GateRecord/HitPointsRecord/StaminaRecord/encounter./actor:sentinel/object:gate:0matches. All81READ historical inputs (85minus4editable delivery docs) retain raw hashes; CORE-03 artifact retains its entry SHA256. Original runtime/tests/config/specs/oracles unchanged.

Self-review checked all6new runtime modules/4test modules/fixture bytes and independent contracts; no runtime-derived expected oracle. Early test repairs corrected the actual WRITE_CONFLICT name, last rejected-turn cue expectation and the driver's stronger changed-admission guard; expectations/reference files were not changed. Final delivery-document links/fences/status/whitespace/source-hash checks recorded below after edits. Existing launcher location diagnostic remains stderr; test and JSON CLI exits are successful.

Final delivery-doc verification:UTF8 explicit read/declaration AST/links/fences/whitespace/current status PASS;all81READ historical hashes and CORE-03 artifact SHA256 unchanged;only4editable baseline delivery docs differ plus this instruction. git diff --check exit0;HEAD unchanged. Two preexisting tracked prompt/MASTER LF-to-CRLF notices remain historical. Exact17implementation-delivery paths covered;CORE-03 DONE,parent IN_PROGRESS,NEXT CORE-04 instruction.
