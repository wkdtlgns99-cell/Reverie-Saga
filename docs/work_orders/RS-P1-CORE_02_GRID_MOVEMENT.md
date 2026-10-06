# RS-P1-CORE / CORE-02 — Local Grid Movement

Date:2026-10-04 (Asia/Seoul) | Owner/executor/reviewer:Sol | Instruction:ACCEPTED | Implementation:DONE
Director request "다음꺼 ㄱ" authorized execution after instruction finalization. CORE-02 is ACCEPTED/DONE; §9 records actual implementation/verification. §§1–8 preserve the accepted order and dated authoring evidence; prospective/NOT_STARTED/NOT_RUN statements there describe authoring entry. Parent RS-P1-CORE remains IN_PROGRESS; no extra backlog parent. Self-review is not independent-person review.

Inputs:[CORE-01 acceptance](RS-P1-CORE_VERTICAL_SLICE.md#11-core-01-execution--acceptance--2026-10-04), [API supersession](PHASE0_CONTRACTS.md#core-01-source-api-supersession--2026-10-04), [coding template](../prompts/SOL_CODING_WORK_ORDER.md), [MASTER](../MASTER_GAME_ARCHITECTURE.md) §§0–3/8–9/13, [B02](../../architecture/BLOCK_02.md) A1–A3, [B03](../../architecture/BLOCK_03.md) A5–A6, [B04](../../architecture/BLOCK_04.md) A7, [B05](../../architecture/BLOCK_05.md) A10–A11. Detailed literal inputs/expected outputs/source: [RS-P1-CORE_02_REFERENCE_VECTORS.json](RS-P1-CORE_02_REFERENCE_VECTORS.json).

## 1. Baseline / Source Decisions

HEAD efd2478ff8a6ed93ee833c3f8464a0efdd8a181a/main. Primary prompt/MASTER are preexisting tracked user edits; docs/config/src/tests are already untracked working content. Preserve all. Root AGENTS.md absent; historical AGENTS is reference, not active policy. Remote freshness unchecked. Vector artifact records56raw input hashes including all41current Python files, original fixture/config/lock and protected documents. At execution entry refresh these hashes and actual checks, not just HEAD: most current source is untracked.

Authoring entry,2026-10-04:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; pytest59passed in22.12s/exit0; Ruff check exit0; strict mypy41files/exit0. Same qualified Python3.13.12/Ruff0.16.6/mypy2.4.0/pytest9.1.1 and13hashlocked packages; no new dependency/version/compatibility research is needed for this pure-Python unit. Existing launcher location diagnostic is stderr; CLI/checks pass. No independent-person/device/bundle/performance qualification implied.

Actual integration constraints:
- FeatureBundle remains in contracts/skeleton.py with explicit component_codecs,patch_routes,checkpoint_policy plus typed read/payload/command/delta/presenter/event registrations. Exactly one bundle per StateIO; trial is a separate selection, never aggregated with skeleton or Gauge.
- RegisteredStateIO owns sealed schema/rules/pins, exact descriptor coverage/metadata, guarded registered patches, checkpoint/effect validation and canonical serialization. Trial adapters must satisfy it unchanged; no central type switch or implicit fallback.
- Driver admits exactly one second, supports record-only due-now root facts and commits CORE+protocol once. It allows a committed empty changes tuple, so blocked attempts need no fake delta/counter/writer. Rejected commands consume no time; retained duplicate lookup precedes stale-revision checks.
- Reducer stage/net read observations permit only delta.target. Trial reducer cannot read map or position.space_id; the engine/policy/presenter own those checks. One component field family per phase; only position.cell is mutable.
- Existing observed factory has no integer-sequence export method. TrialMapRead exposes is_blocked(cell)->bool, observing blocked_cells membership through ViewAccess; it never returns the tuple/record. No generic wrapper extension is necessary.
- app.headless.bootstrap constructs toy records; do not call it with the trial bundle. NEW app.trial builds the trial checkpoint then calls existing private app.headless._restore with its already-built IO. This app-to-app owner call preserves one schedule compilation per session. Existing public restore_checkpoint and replay_runner(...,bundles=(trial_bundle(),)) already support its schemas.

This is the first movement prototype, not the complete MASTER world/physics/placement/pathfinding model. All dimensions/costs below are new trial values inherited from the settled CORE-02 seed, not v1 code/formulas/balance or final movement cost. CORE-03 interaction/combat, CORE-04 delayed/NPC and CORE-05 durable save remain DRAFT until their own source-specific orders.

## 2. Complete Work Order

| Required field | Concrete contract |
|---|---|
| task_id/title | RS-P1-CORE / CORE-02:register one trial map/actor and execute cardinal movement with time-consuming blocked attempts |
| status/executor/review | READY; Sol implementation/diagnosis/integration/self-review; independent-person review UNVERIFIED |
| goal/non_goals | Real trial CLI/typed submit→same Driver→COMMIT→facts/diff/cues→record/replay. Excludes dynamic occupancy, multi-space transfer, pathfinding/diagonal movement, variable durations/energy/AP, combat/interactions/NPC, pending/simulate/DB/save/migration, client/UI/IPC/Factory/assets/provider and governance |
| baseline/prerequisites | CORE-01 DONE; actual59tests/Ruff/strict mypy41files PASS; §1 hashes/dirty inventory; settled registered source APIs and exact vectors below |
| read_files | This order/vector; parent order §1/§5/§6/§11; listed normative sections; full actual src/domain/{primitives,state_types,canonical}.py, contracts/{read_views,messages,turn,skeleton,state_io,replay,errors}.py, orchestration/{scheduler,read_views,serialization,turn,replay,rng,skeleton}.py, app/{headless,feature_registry}.py and existing59tests/config/lock/oracles |
| allowed_edit_paths/forbidden_paths | §3; feature modules and new tests only, plus delivery docs. Existing runtime/tests/config/lock/goldens/core oracles/specs/policies/reference repository READ |
| public_contract | §4:TrialMapRecord/CellPositionRecord, typed map/position views/keys, six payload schemas, Movement engine/ports, trial_bundle, TrialBootstrapSpec/bootstrap_trial/main. Existing public/generic APIs unchanged |
| behavior/algorithm_steps | §5:strict cardinal admission; actual map/position reads; x/z bounds before row-major target; wall membership; one delta on success/none on blockage; one root fact; existing receipt/head COMMIT; guarded derived cue |
| edge_policy/examples | §5/§6:bool/float/shape/schema/IDs/ranges/zero/negative/row-wrap/wall/time/duplicate/errors/ownership; artifact32movement cases,9coordinates,10full replay steps and publications |
| wiring | trial_registry registrations→app.trial bootstrap/private owner/CLI→same Driver→registered reducers/codecs→Presenter→explicit-IO Recorder/Runner via qualified existing restore/replay factory |
| performance | One actor/two components,1fact,≤1delta,1cue per admitted attempt; pending0/no draw; collection cap1. Inherited Brain512MiB/p95≤100ms/p99≤250ms and Ruff+coregolden≤20s are TARGETs; no new benchmark/resource tooling. Record local fast-check feedback only |
| baseline_commands/verification_commands | §7; actual exit/count/timing required at source entry and delivery |
| test_responsibilities/acceptance | §6/§7:all original59expectations unchanged; independent complete trial path and boundaries; ownership/atomicity/finally/precise replay mismatches/source-pin rejection; lint/types and no protected-source drift |
| stop_conditions | Entry baseline/hashes differ without explanation; generic contract/second field merge/multi-feature registry change needed; oracle/pins/schema drift; overlapping user edit or unexplained failure. Diagnose safe in-scope alternatives; if unresolved report concrete evidence and one needed decision |
| delivery | Exact new files/APIs/live path, commands/results/self-review, complete publication/golden comparison and scope hashes; mark only CORE-02 DONE after actual acceptance; parent stays IN_PROGRESS. No agent/commit/push/external messaging/new policy/CI/custom checker/tool/dependency install |

## 3. Exact Implementation Edit Scope

NEW production at authorized implementation entry (now delivered; §9):
```text
C:\Reverie Saga\src\domain\trial.py
C:\Reverie Saga\src\contracts\trial.py
C:\Reverie Saga\src\engines\trial.py
C:\Reverie Saga\src\orchestration\trial.py
C:\Reverie Saga\src\app\trial_registry.py
C:\Reverie Saga\src\app\trial.py
```

NEW tests/helpers/fixture at authorized implementation entry (now delivered; §9):
```text
C:\Reverie Saga\tests\unit\trial_fixtures.py
C:\Reverie Saga\tests\unit\test_trial.py
C:\Reverie Saga\tests\integration\test_trial.py
C:\Reverie Saga\tests\replay\test_trial.py
C:\Reverie Saga\tests\replay\fixtures\trial_v1.json
```

MODIFY delivery docs only:
```text
C:\Reverie Saga\BACKLOG.md
C:\Reverie Saga\SESSION_HANDOFF.md
C:\Reverie Saga\docs\work_orders\RS-P1-CORE_02_GRID_MOVEMENT.md
C:\Reverie Saga\docs\work_orders\RS-P1-CORE_VERTICAL_SLICE.md
C:\Reverie Saga\docs\work_orders\PHASE0_CONTRACTS.md
```

All other paths READ, including existing __init__.py files (packages already exist), all existing runtime/tests, original skeleton fixture, CORE-01/Phase0 vectors, new CORE-02 vector artifact, config/lock, primary/MASTER/template/architecture/historical AGENTS, C:\Quilltale and policies/CI/assets/tools. Trial functionality must fit the already-qualified generic ports; do not add feature branches to serialization/turn/replay or grow the shared message union. Additional paths/public contract changes need a focused refreshed order before implementation. No test removal/skip/xfail/oracle rewrite.

Current AUTHORING delivery scope is NEW this order+its vector artifact, MODIFY parent order/BACKLOG/SESSION_HANDOFF only. The future source paths and their delivery-doc scope do not imply production changes in this authoring turn.

## 4. Exact NEW Contracts / Registrations

All DTOs are frozen slotted dataclasses with no mutable children. Reuse EntityId/Tick/WorldRevision/TypeKey/ComponentRecord and existing abstract payload families; no duplicate primitive/Any/growing central union. Domain imports domain only; contracts imports domain/contracts; engines imports only domain/contracts; trusted adapters/codecs/presenter live in orchestration.trial; app is composition root. Engine never receives JSON, records, patches, headers, receipts, IO or protocol cursors.

### 4.1 Domain — domain/trial.py

Constants:ACTOR_ID=EntityId("actor:trial"),SPACE_ID=EntityId("space:trial"),WIDTH=3,HEIGHT=3,CELL_MM=1000,BLOCKED_CELLS=(1,). Names/values are new trial requirements. Actor initially cell0 unless explicitly qualified initial_cell overrides it to another free cell for boundary tests.

The pinned rules initial_cell0 specifies the canonical/default setup, not an invariant of every later checkpoint. Explicit bootstrap/restore may start at another qualified free cell; that difference is recorded in its initial CORE/hash/replay header. All sessions still use the same fixed geometry/rules and explicit initial checkpoint.

```python
@dataclass(frozen=True, slots=True)
class TrialMapRecord(ComponentRecord):
    entity_id: EntityId
    width: int
    height: int
    cell_mm: int
    blocked_cells: tuple[int, ...]
    @property
    def schema(self) -> TypeKey: ...  # trial.map/1

@dataclass(frozen=True, slots=True)
class CellPositionRecord(ComponentRecord):
    entity_id: EntityId
    space_id: EntityId
    cell: int
    @property
    def schema(self) -> TypeKey: ...  # trial.position/1

def cell_coordinates(cell: int) -> tuple[int, int]: ...
```

cell_coordinates validates exact int0..8 (bool excluded), returns `(cell%3*1000,cell//3*1000)` as `(x_mm,z_mm)`; ValueError for invalid values, including negative/9/float/bool. Pure derived geometry, no stored duplicate coordinates/time mutation. Cell1 is valid geometry for drawing the wall although invalid actor placement.

Map component body requires exact fields width,height,cell_mm,blocked_cells:width/height exact3,cell_mm exact1000; blocked tuple exactly(1,), sorted unique exact ints0..8, cap1. Empty/duplicate/unsorted/out-of-bounds/boolean blocks are rejected, never replaced with defaults. Position body requires space_id/cell; namespaced space_id, exact int0..8. Checkpoint policy enforces the actual fixed IDs/reference/free placement.

### 4.2 Contracts — contracts/trial.py

```python
class TrialMapRead(Protocol):
    @property
    def width(self) -> int: ...
    @property
    def height(self) -> int: ...
    @property
    def cell_mm(self) -> int: ...
    def is_blocked(self, cell: int) -> bool: ...

class CellPositionRead(Protocol):
    @property
    def space_id(self) -> EntityId: ...
    @property
    def cell(self) -> int: ...

TRIAL_MAP = ComponentKey[TrialMapRead](TypeKey("trial.map", 1))
CELL_POSITION = ComponentKey[CellPositionRead](TypeKey("trial.position", 1))
```

is_blocked returns exact bool membership against the immutable tuple after observing FieldAddress(trial.map.blocked_cells,map_entity),path=(),operation="membership". Guard observation occurs before argument checks; invalid cell ValueError while live, any retained alias operation after close ExpiredReadView. Other properties observe their exact family with read; setters/deleters observe write and raise ReadOnlyViolation. No tuple/list/record/root export; no extension of existing ViewAccess methods.

Six required payload DTOs:
| Frozen class / base | Exact fields / TypeKey(kind,1) |
|---|---|
| MoveCommand / CommandPayload | dx:int,dz:int / trial.move |
| CellDelta / StateDelta | entity_id:EntityId,before_cell:int,after_cell:int / trial.position-delta; target=FieldAddress(FieldFamily("trial.position","cell"),entity_id) |
| CellPatch / ComponentPatch | cell:int / trial.position-patch |
| Moved / FactPayload | actor_id:EntityId,space_id:EntityId,from_cell:int,to_cell:int / trial.moved |
| MoveBlocked / FactPayload | actor_id:EntityId,space_id:EntityId,from_cell:int,dx:int,dz:int,reason:Literal["boundary","occupied"] / trial.move-blocked |
| MoveCue / PresentationPayload | actor_id:EntityId,space_id:EntityId,from_cell:int,to_cell:int,from_x_mm:int,from_z_mm:int,to_x_mm:int,to_z_mm:int,result:Literal["moved","boundary","occupied"] / trial.move-cue |

MoveCommand allows exactly(-1,0),(0,-1),(0,1),(1,0), with exact integers. No zero,diagonal,multi-cell jump, extra/missing field, bool/float/null/coercion. CellDelta/CellPatch use exact cell ints0..8; delta identity is encodable for composition/is_identity but never published. Moved requires distinct adjacent free cells under this fixed map. MoveBlocked requires a free from_cell/cardinal direction and a reason consistent with the fixed geometry/wall. IDs must be the qualified trial actor/space for facts/cues; component identities additionally verified by policy. Cue coordinates must be exact geometry of from/to cells; moved has distinct adjacent free cells, blocked has equal from/to cells and a supported result. No arbitrary code/default/unknown version.

### 4.3 Engines / Trusted Boundary — engines/trial.py,orchestration/trial.py

`Movement` implements Engine; manifest engine_id=trial.movement, phases=(RESOLVE,),lane A, action_kinds=(trial.move/1,),on_matching_events=False,every_tick=False,cost_class="local",depends_on=(),consumes=(),emits=(trial.move-blocked/1,trial.moved/1).

Exact RESOLVE read families:trial.position.cell/space_id,trial.map.width/height/blocked_cells. Sole write:trial.position.cell,owner trial.movement. Only actual reads/writes at that phase; no clock/map mutation, definition/RNG draw or autonomous work. One admitted action→one fact; zero or one CellDelta.

Trusted concrete ports NEW in orchestration.trial, signatures from current protocols without adaptation:
- CellPositionAdapter/TrialMapAdapter implement ReadAdapter[CellPositionRead]/ReadAdapter[TrialMapRead], validate exact frozen class/schema/scalars/tuple shape; wrap uses ViewAccess as above.
- CellPositionCodec/TrialMapCodec implement ComponentCodec, strictly decode/encode exact registered fields; no default filling/lossy conversions. TrialPayloadCodec(schema:TypeKey) implements PayloadCodec for the six trial classes only at this feature boundary; strict exact fields/version/class/semantic shape, owned JsonObject encoding.
- MoveAdmission implements CommandRoute: schema trial.move/1,reads=(trial.position.cell,trial.position.space_id); `admit(command,state,*,start_tick,world_id)->AdmissionOutcome`. Validate actor/cardinal payload and position/reference, but never reject a legal blocked attempt. Return TurnPlan(start_tick,start_tick+1) and AdmittedAction. Semantic action key is the unchanged `a1-` SHA256(pack(action-key/v1,world_id,str(target_tick),actor_id,payload_hash)); payload_hash=hash_document(payload/v1,{schema:key_document(payload.schema),payload:{dx,dz}}), exactly as the settled generic action-address convention.
- CellReducer implements DeltaRoute: schema trial.position-delta/1,owner trial.movement; stage reads only CELL_POSITION.cell at delta.entity_id, checks expected old, distinct cardinal/free before→after, then applies CellPatch via StagingEditor. No map/space read in reducer. compose requires nonempty all-CellDelta/same target/contiguous old/new, returns first.before_cell→last.after_cell. Composition may produce identity; is_identity validates shape and returns exact bool; validate_net rejects identity and reads only target cell, requiring it equals after_cell. Numeric encoders permit valid range identity/nonadjacent net composition; per-stage movement enforces adjacency. No central old/new-name assumption.
- CellPatchRoute implements PatchRoute: patch schema trial.position-patch/1,component trial.position/1,family trial.position.cell; immutable replacement changes only cell, preserving entity/schema/space_id. Generic registered editor checks codec bounds/field ownership.
- TrialCheckpointPolicy.validate(core,protocol):exactly one TrialMapRecord(space:trial) and one CellPositionRecord(actor:trial), reference equals map ID, fixed geometry/blocks, position free, every stream actor=actor:trial; common IO checks sorting/duplicates/IDs/stream caps/receipt/pins/world. No pending/packages/build artifacts.
- MovePresenter implements Presenter. Binding trial.presenter consumes both fact kinds; guarded committed position/map verify subject/reference/result/cells then derive the exact cue and mm coordinates. Cue source header IDs use existing p1-/cue-id/v1 framing, presenter ID and local sequence, Phase.PRESENT/rank0/wave0/current receipt tick; caused_by=(source_event_id,),degraded=(). Priority important,coalesce keep_all,key="" for both outcomes. Postcommit exception/codec failure retains commit/facts/diff under existing PRESENTATION_FAILED behavior; no new error swallowing.

### 4.4 Registry / App — app/trial_registry.py,app/trial.py

`trial_bundle()->FeatureBundle` returns feature_id trial.movement; registers the Movement RESOLVE binding, two typed adapters, all six FieldSpecs, two EventPolicies(record_only,PRESENT,priority0,late_route reject,producer trial.movement,empty subscribers/cancellers), MoveAdmission,CellReducer,MovePresenter, six payload codecs, two component codecs, one CellPatchRoute and TrialCheckpointPolicy.

Field metadata all CORE/A/scale1. Map width/height integer min=max3/unit cell_count;cell_mm integer min=max1000/unit mm;blocked_cells value_kind integer_tuple,min0,max8,collection_cap1,unit cell. All map fields owned by reserved system.bootstrap; position.space_id string/unit entity_id,range/cap None,system.bootstrap. Position.cell integer min0,max8,cap None,unit cell,trial.movement. Consumers are actual movement/presenter users:width/height/blocks both;cell_mm presenter;position.space_id/cell both. No fake bootstrap engine/route or aggregate feature. Schema/rules/schedule documents exactly the literal artifact; FieldSpecs must agree with descriptor metadata. All runtime registrants are private to each frozen bundle selection.

```python
@dataclass(frozen=True, slots=True)
class TrialBootstrapSpec:
    seed_hex: str
    branch_id: str
    stream_id: str
    initial_cell: int = 0
    initial_tick: Tick = Tick(0)
    initial_revision: WorldRevision = WorldRevision(0)

def bootstrap_trial(spec: TrialBootstrapSpec, *, rng: RngService | None = None) -> HeadlessSession: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

Qualified bootstrap:exact lowerhex seed64/branch32/stream32; exact bounded tick/revision0..2^63−1; initial_cell exact0..8 and not1. Invalid spec fails BootstrapError("INVALID_INITIAL_STATE",detail) before constructing an authoritative owner. Build one bundle/StateIO/schedule; world_id uses unchanged world-id/v1 seed+rules+catalog framing. Create canonically ordered TrialMapRecord then CellPositionRecord, pending/packages empty, protocol one active stream/highwater0/receipts empty. Share IO with `_restore(core,protocol,bundles,rng,io=io)`; default qualified CounterRngService(seed,world,()) (no fake RNG/no trial draw).

Private app.trial helper may return `(HeadlessSession,StateIO)` to share initialization between bootstrap_trial and CLI; no HeadlessSession API change. main accepts no flags, defaults all-zero seed/branch and stream all1; reads nonblank newline command JSON through session.submit_json, emits io.encode_publication canonical JSON+newline, flushes, returns0. NEW runnable entry `PYTHONPATH=src python -m app.trial`; original `app.headless` CLI remains toy and unchanged.

Restore/record/replay:existing restore_checkpoint(...,bundles=(trial_bundle(),),rng=qualified_rng_or_None),state_io((trial_bundle(),)),Recorder(header,io=io),decode_fixture/encode_fixture(...,io=io),replay_runner(fixture,bundles=(trial_bundle(),)). Selected trial engine scopes have no RNG purposes/draws even when the generic app factory retains its unrelated toy allowlist entries; those entries are never used by trial. No new restore/simulation path or implicit orchestration default. Every run creates fresh CORE/protocol/view/IO owners.

## 5. Movement / Failure Algorithms

VALIDATE is pure:typed cardinal/authorized actor/reference/expected revision; existing Driver handles command ID/stream/schema/highwater/retained retry/stale and MAX tick/revision. A structurally legal blocked attempt is admitted for exactly1game second=1/60minute. No AP/energy/speed/balance table introduced; query/snapshot/cell_coordinates/menu/camera do not submit/advance time.

At RESOLVE:
1. Require admitted MoveCommand. Read actor position.space_id/cell; acquire TRIAL_MAP for that space, read width/height.
2. x=cell%width,z=cell//width; target_x=x+dx,target_z=z+dz. Check both axis bounds first. Never use flattened cell±1 before the bounds check (prevents2→3/5→6 row wrap).
3. Outside→MoveBlocked(actor,space,cell,dx,dz,"boundary"),no delta. Do not call is_blocked with an out-of-range cell.
4. Otherwise target=target_z*width+target_x. is_blocked(target) true→MoveBlocked(...,"occupied"),no delta; else CellDelta(actor,cell,target)+Moved(actor,space,cell,target).
5. EmittedFact due_tick=invocation.logical_tick,caused_by=(),EngineResult.degraded=(). Existing driver assigns event/header/rank/sequence, validates candidate, creates receipt/non-null diff (changes empty on blocked), advances tick/revision/highwater and swaps one head. A blocked first attempt has unchanged component leaves but a changed CORE root because tick1 is authoritative.
6. Presenter reads the committed candidate; success cue endpoints old/new, blocked endpoints equal current cell with reason=result and derived coordinates. Effects remain committed if presentation fails.

| Case | Exact outcome / time |
|---|---|
| Cell0 Right | COMMITTED;occupied,position0,tick+1,revision+1;1fact,0delta,1cue |
| Cell0 Down | COMMITTED;0→3,oneCellDelta/Moved/cue;tick+1,revision+1 |
| Cell0 Left/Up | COMMITTED;boundary,position0;tick+1,revision+1 |
| Cell2 Right,cell5 Right | Boundary;position2/5; never wrap to3/6 |
| Cell4 Up | Occupied target1;position4;time consumed |
| dx=dz=0/diagonal/abs(dx)+abs(dz)>1/bool/float/missing/extra/version2 | Typed driver rejection INVALID_COMMAND/current authorized revision (unsupported typed schema UNSUPPORTED_SCHEMA); JSON boundary INVALID_COMMAND/current_revisionNone; no effects/time/highwater |
| Retained exact blocked/moved retry | Original receipt before stale check;current head unchanged;facts()/diffNone/cues();RESYNC_REQUIRED if original revision<current |
| Retained ID with other direction/revision/body | COMMAND_ID_CONFLICT;no effects/time |
| Unretained stale expected revision | STALE_REVISION/current revision;no highwater/receipt/time; ID can later succeed with corrected revision |
| Invalid map/missing component/reference/wall placement/snapshot pins | Before owner publication/replay execution:strict schema/checkpoint failure (ReplayFormatError at qualified replay/restore boundary). Bootstrap bad spec INVALID_INITIAL_STATE |
| Engine/reducer/patch/policy/serialization failure | TurnAborted;old CORE+protocol+highwater unchanged;no effects;existing stable CandidateError code or ENGINE_EXCEPTION |
| Tick/revision2^63−1 | Existing INTEGER_OVERFLOW abort;old pair retained |
| Cues/presenter fail | COMMITTED receipt/facts/diff retained;PRESENTATION_FAILED;cues empty |

No nondeterministic clock/RNG/UUID/process environment in engines/domain; no clipping/tie resolution/event trimming. Tie not applicable:single actor/cardinal intent/static one-wall map. Multi-entity occupancy/shared writers/transfer/ambiguous targets require later contracts. Unknown registry/schema/classes and duplicate fields/components/patch target remain errors, never default coercion.

## 6. Independent Examples / Test Responsibilities

Artifact derives every byte/hash from these new requirements with retained stdlib reference_source. No production/Recorder output was used as an oracle. Implementation copies expected_fixture as canonical bytes into NEW tests/replay/fixtures/trial_v1.json; do not regenerate expected values through runtime or edit the authoring artifact. expected_publications additionally fixes exact cues/diagnostics outside the replay witness. Existing skeleton/Gauge fixtures and assertions remain READ.

The authoring container includes floating-point elapsed-time metadata outside domain documents. Test helpers extract the needed sections with stdlib JSON and immediately seal/type them, or load the standalone copied fixture through decode_fixture. Do not pass the whole authoring artifact to domain.decode_json or relax its strict float/depth/shape rules.

| Trace step (0-based index) | Command / from→current cell | Resulting tick/revision |
|---|---|---|
| 0 | seq1 Right,expected0:0→0;occupied | 1/1;receipt1,empty changes |
| 1 | seq2 Down,expected1:0→3;Moved | 2/2 |
| 2 | seq3 Right,expected2:3→4;Moved | 3/3 |
| 3 | seq4 Up,expected3:4→4;occupied | 4/4 |
| 4 | seq5 Left,expected4:4→3;Moved | 5/5 |
| 5 | seq6 Left,expected5:3→3;boundary | 6/6 |
| 6 | Retry seq1 Right,expected0;originalreceipt1 | 6/6;no effects,RESYNC_REQUIRED |
| 7 | seq7 Down,expected0;STALE_REVISION | 6/6;no effects |
| 8 | seq1 Down,expected0;COMMAND_ID_CONFLICT | 6/6;no effects |
| 9 | seq7 Down,expected6:3→6;reuse previously rejected ID | 7/7 |

All32walkable-cell×cardinal cases are enumerated independently:18moved,11boundary,3occupied. Nine coordinate examples include cell3→(0,1000),cell4→(1000,1000),cell8→(2000,2000). Literal pins:schema1710269a9d64c442fac450e009de954d1d1701edea193ade4a9abea76e60b8aa,rulesdbe7a3c61e1d75b4b7b02b693f90dcaa8202d9b878ed321db767bf3098dbf3a3,scheduled6c54291fd7a0b6ff5e06f1ba1b8b3b7e061ca21ee2d132c4b0632838277d6db. InitialCORE e15eab8bd8e4d27b8ac9d0a652a616cb74bd91820befe53dca06118fddaa56aa; full canonical documents/framing/leaf/hashes are in the artifact, not copied from an implementation.

Negative self-consistent trace prefix changes only the third expected movement to adjacent3→6, with correct witness/outcome/protocol/diff hashes; real Right is3→4. First mismatch:step_index2,$core.components[1].fields.cell,expected"6",actual"4". Deliberately dropped MoveBlocked on first commit must produce step0 $facts[0] actual<missing> despite equal CORE/protocol/diff; keep real cues in the observed publication to prove simulation-witness separation. This is corruption testing via an observation wrapper, not mocking domain outcomes.

NEW planned nodes, execute only after implementation creates them:
| File | Nodes / actual responsibility |
|---|---|
| tests/unit/test_trial.py | test_literal_pins_and_components;test_exact_payload_shapes;test_fixed_map_and_position_validation;test_cell_coordinates;test_read_observation_and_expiry;test_cell_reducer_old_value_composition;test_patch_and_registry_ownership |
| tests/integration/test_trial.py | test_movement_vectors (32independent cases through real Engine/Driver);test_full_publications (10literal publications incl cues/diagnostics);test_blocked_attempt_time_and_empty_diff;test_invalid_command_no_time;test_row_boundary_no_wrap;test_retry_stale_conflict_and_rejected_id_reuse;test_candidate_abort_atomicity;test_postcommit_presentation_failure;test_trial_cli_and_snapshot_no_time |
| tests/replay/test_trial.py | test_trial_core_trace (exact10step golden/hash/outcome/complete witness);test_trial_recorder_matches_independent_trace;test_trial_blocked_fact_loss;test_trial_wrong_leaf;test_trial_invalid_checkpoint_before_execution;test_trial_fresh_sessions_and_registry_order |
| tests/unit/trial_fixtures.py | Real qualified bundle/session/command helpers and purpose-built failing Engine/PatchRoute/Presenter wrappers when needed; no fake result generation or implicit toy fallback |

Tests must cover strict bool/float/non-NFC/unknown/missing/version/IDs/tuple-cap/order; invalid initialcell1 and reference/missingmap before commands; exact committed empty diff vs rejected/retry null diff; old-root immutability/expired aliases; fixed read-family membership observation and undeclared access; no invalid target membership call at boundary; final MAX tick/revision guard; private faulty ports abort after evaluation with old protocol retained; policy/codec/presenter boundaries; literal UTF8/framing/pins; fresh restore owners/registry permutation and original59regressions. Test supported shapes directly and use minimal meaningful purpose-built ports for fault paths. No weak mirror tests or coverage/custom tool claims.

## 7. Implementation / Verification / Acceptance

Implementation sequence:refresh source/hash baseline→add domain records/constants/coordinates→typed feature DTO/views/keys→adapters/codecs/reducer/policy/presenter→pure Movement engine→literal trial registry/owner bootstrap/CLI→copy independent fixture/add real tests→run full checks/self-review→update exact delivery docs. Source-code private organization is implementation discretion within these six modules; no new helper package/framework/default union or alternate Driver.

Entry and final commands:
```powershell
git -c safe.directory='C:/Reverie Saga' rev-parse HEAD
git -c safe.directory='C:/Reverie Saga' status --short
git -c safe.directory='C:/Reverie Saga' diff --check
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.venv/Scripts/python.exe -m pytest -q tests
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m mypy --strict src tests
.venv/Scripts/python.exe -m pytest -q tests/replay/test_golden.py::test_core_trace
```

Prospective focused commands AFTER the files exist:
```powershell
.venv/Scripts/python.exe -m pytest -q tests/unit/test_trial.py tests/integration/test_trial.py tests/replay/test_trial.py
.venv/Scripts/python.exe -m pytest -q tests/replay/test_trial.py::test_trial_core_trace
rg -n 'TrialMapRecord|CellPositionRecord|MoveCommand|CellPatch|trial\.movement|actor:trial' src/orchestration/serialization.py src/orchestration/turn.py src/orchestration/replay.py
$env:PYTHONPATH='src'
@'
{"command_id":"c1:00000000000000000000000000000000:11111111111111111111111111111111:1","actor_id":"actor:trial","expected_revision":0,"schema":{"kind":"trial.move","version":1},"payload":{"dx":1,"dz":0}}
'@ | .venv/Scripts/python.exe -m app.trial
```

CLI example must be first committed occupied blockage with position0/tick1/revision1,one fact/one cue/empty changes; compare whole literal publication rather than only kind. Original app.headless CLI and59tests keep exact behavior. Generic dispatch search must have0matches and those three files' raw hashes unchanged. Validate every READ source/config/fixture/oracle/spec hash against the56input baseline; only explicitly named delivery docs may differ. Inspect all NEW source/tests/fixture whitespace/import direction/API callers/finally blocks and exact independent bytes; git diff alone excludes untracked source. No imported numeric v1 data or implementation-generated oracle.

Acceptance matrix, actual evidence required before DONE:real CLI+typed/JSON movement;all32boundary/obstacle/success cases;blocked tick/revision/receipt/core-root change despite unchanged position;strict invalid/no-time vs committed blockage;precise retry/stale/conflict semantics;registered state/component/patch/event/presenter ownership and immutable map;independent complete10step replay/publications;missing-fact and exact wrong-leaf mismatch;invalid last witness/source pins fail before first factory command;fresh owners/finally expiry/atomic abort/postcommit preservation;original59tests and protected inputs unchanged;lint/strict types;new source-only feature extension; bounded feedback/qualification limits. At instruction authoring all CORE-02 production/test results were NOT_RUN; actual execution results are in §9.

## 8. Authoring Delivery Evidence

Authoring only:current59tests in22.12s/Ruff/strict mypy41files PASS; actual ports/callers/read observations/single-field guard/no-time and committed-empty-diff behavior inspected. New literal prototype descriptors/rules/schedule,32movement cases,9coordinate projections,10complete replay steps and10full publications derived with retained stdlib source before movement implementation. The artifact retains56raw inputs and a self-consistent wrong-cell example. No future module/test/CLI is claimed to exist; CORE-02 readiness is bounded to this complete order, later units remain DRAFT.

Document/source/reference-byte verification and final status are appended after authoring checks. No production/config/lock/original fixture/oracle/protected-spec/policy/CI/agent/commit/push/external write in this authoring delivery.

Actual authoring verification2026-10-04:retained reference_source reexecuted and every output section matched artifact; independent struct.pack framing vs reference length.to_bytes digest/UTF8/hex checks PASS; current compile_schedule called with actual CapabilityManifest/NodeActivation types matched the independent schedule fingerprint.32cases=18moved/11boundary/3occupied;10step cells/ticks/outcomes/receipt flow and changed first blocked root verified. Three NEW declaration fences AST-parse/compile; all15work-order fields,11absent prospective source/test/fixture paths, actual existing consumers, links/fences/whitespace/status consistency PASS. Initial56input hashes matched; after final delivery-doc updates53remain identical and changed3are exactly parent order/BACKLOG/SESSION_HANDOFF. `git -c safe.directory='C:/Reverie Saga' diff --check` exit0; preexisting primary/MASTER LF-to-CRLF notices only. No source/test/config/oracle changed. New JSON artifact190896bytes; original independent fixtures/pins retained.

Decision:CORE-02_INSTRUCTION_ACCEPTED/READY; gameplay implementation and new tests NOT_RUN. NEXT:execute this complete CORE-02 order, then author CORE-03 against accepted movement source. Parent RS-P1-CORE IN_PROGRESS,CORE-01 DONE,CORE-03–05 DRAFT; full-game/performance/independent-person qualification UNVERIFIED.


## 9. CORE-02 Execution / Acceptance — 2026-10-04

Director request "다음꺼 ㄱ" executed the READY order. HEAD efd2478ff8a6ed93ee833c3f8464a0efdd8a181a/main unchanged. Source entry:59tests PASS in21.98s;53of56historical input hashes identical,3differences are exactly prior instruction-authoring BACKLOG/SESSION_HANDOFF/parent-order edits recorded in §8. No unexplained source drift; preexisting primary/MASTER user edits preserved. Existing toolchain/13-package lock reused without installation. Production after initial wiring:Ruff/strict mypy47files PASS.

Delivered exactly §3:NEW6production modules,4test modules,1independent fixture; MODIFY5delivery documents. Every existing runtime/test/config/lock/oracle/spec remains READ and unchanged. The reference artifact remains READ. No package initializer, shared message union, generic serializer/Driver/replay, policy/CI/helper tool/dependency/agent/commit/push/external write.

Actual APIs/live path:domain.trial supplies frozen TrialMapRecord/CellPositionRecord and pure cell_coordinates; contracts.trial supplies typed map/position keys and six payload DTOs; engines.trial.Movement receives observed state only. orchestration.trial implements exact codecs/adapters/admission/reducer/patch/checkpoint/presenter ports. app.trial_registry.trial_bundle selects those registrations and pinned literal descriptors/rules. app.trial.bootstrap_trial validates TrialBootstrapSpec, creates one StateIO and the trial CORE/protocol, shares IO with existing app.headless._restore, uses CounterRngService with no draw purposes. Same Driver performs guarded movement→registered staging→candidate validation→sole-head COMMIT→derived cue. CLI:PYTHONPATH=src; python -m app.trial reads newline commands and emits canonical publications. Existing headless toy CLI remains unchanged.

One legal attempt consumes1second and increments revision once. Boundary checks precede row-major target/occupancy. Wall/boundary commits publish exactly1MoveBlocked/1MoveCue and non-null diff with empty changes; position remains unchanged while tick/root/receipt/highwater advance. Success publishes1CellDelta/Moved/MoveCue with derived mm endpoints. Typed/JSON invalid commands, stale/conflict and retained retries preserve head; retry returns original receipt with no effects. Rejected IDs can later commit. Checkpoint policy enforces fixed map/reference/free actor/stream IDs, permitting qualified nondefault free initial cells. Reducer stage/net observes only cell target; membership guards precede argument validation and retained aliases expire in finally.

Independent expectations were copied from the READ authoring artifact, never generated by runtime. tests/replay/fixtures/trial_v1.json equals expected_fixture canonical bytes/SHA256. All32walkable-cell/cardinal cases pass:18moved/11boundary/3occupied. All9coordinate examples and10complete publications match exact literal bytes, including facts/diff/cues/diagnostics and original receipts. Recorder produces each exact independent step; Runner replays10steps through fresh real checkpoint owners. Pins/initial CORE match the literals in §6. Dropped first MoveBlocked reports only step0 $facts[0] actual<missing> while real cues remain; self-consistent wrong3→6 expectation reports first mismatch step2 $core.components[1].fields.cell expected6/actual4. Last-witness malformed schema/map/reference/wall/pins fail before first factory execution; explicit foreign registry required. Repeated fresh sessions and reversed registration order reproduce the same path/pins.

Fault checks:real Movement evaluated before purpose-built fault ports; undeclared engine read, engine exception, protected-space patch, undeclared net read, and candidate-policy failure retain exact old CORE/protocol/highwater/receipts and publish no effects. Engine/net aliases expire after failures. Postcommit presenter/cue-codec failure retains receipt/facts/diff and committed position with PRESENTATION_FAILED/no cues. Invalid bool/float/NFC/version/fields/IDs/range/tuple geometry/fact/cue semantics, old-cell and composition identity/contiguity, field/patch ownership, MAX tick/revision, row-boundary and live CLI/query no-time checks pass. Test ports wrap real behavior and inject bounded faults; no domain-result mocks/skips/xfails.

Final commands, after final source/test edits:
- PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; .venv/Scripts/python.exe -m pytest -q tests:exit0,143passed in24.02s (59original+84new).
- Focused new unit/integration/replay:exit0,84passed in2.17s.
- .venv/Scripts/python.exe -m ruff check src tests:exit0,All checks passed.
- .venv/Scripts/python.exe -m mypy --strict src tests:exit0,51sourcefiles PASS.
- Original test_core_trace + new test_trial_core_trace:exit0,2passed in0.45s; Ruff+both goldens measured1.1720115s local feedback only. p95/p99/memory/device/bundle/full-game/independent-person qualification UNVERIFIED.
- Generic dispatch search0matches;52READ historical inputs raw-hash identical (4allowed delivery docs excluded). Original skeleton fixture/config/lock and all41predecessor Python files retained. Reference artifact raw hash and full entry inventory checked at delivery.

Self-review repaired test-only frozen-engine subclass wiring using composition, precise exception expectations and JSON/port type annotations before final verification. No production workaround or old assertion/oracle change. Final scope/import-direction/links/fences/whitespace/git diff --check evidence appended below after document verification. Existing Python launcher diagnostic persists on stderr; CLI and checks exit0.

Decision:CORE-02 ACCEPTED/DONE. Parent RS-P1-CORE IN_PROGRESS; CORE-01 DONE; CORE-03–05 DRAFT. NEXT:author the CORE-03 interaction/bounded-combat order against accepted movement source, with explicit target/resource/status/death/numerical/ownership contracts and independent examples before implementation.

Delivery verification:52READ historical hashes identical;exact11NEW source/test/fixture paths exist, AST compilation/import direction/whitespace and5delivery-document links/fences/current status PASS. Fixture canonical SHA256 ae6834a21be298a4015f9309bf7b710f977e39e84f3bf1a57679d6c866d59a07 equals the preimplementation literal. READ reference artifact190896bytes/SHA256 8fee27767c8059449161ece6f8a3b9c68b1126314d31dddaca034c9d667caa48. Generic dispatch0matches; git diff --check exit0 (preexisting primary/MASTER LF-to-CRLF notices only). No source/test change after final143test/Ruff/mypy checks. Current statuses agree:CORE-02 DONE,parent IN_PROGRESS,next CORE-03 instruction; historical authoring sections retained.
