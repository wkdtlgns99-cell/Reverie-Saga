# RS-P1-CORE — First Gameplay Slice / Entry Order

Date:2026-10-06 (Asia/Seoul) | Owner/executor/reviewer:Sol | First units:DONE | Implementation:CORE-01/02/03/04/05_ACCEPTED | Parent:DONE/FIRST_REPRESENTATIVE_HEADLESS_SLICE
Current parent review acceptance/status/evidence is §20; the original CORE-01 entry instructions/history below remain preserved. Director authorized authoring the next concrete implementation order ("ㄱㄱ" after backlog/next-order discussion). This delivery creates instructions and independent examples; production changes require execution of the order. Self-review is not independent-person review.

Normative inputs:[MASTER](../MASTER_GAME_ARCHITECTURE.md) §§1–3/8–9/13; [coding template](../prompts/SOL_CODING_WORK_ORDER.md); [B02](../../architecture/BLOCK_02.md) A1–A3; [B03](../../architecture/BLOCK_03.md) A5–A6; [B04](../../architecture/BLOCK_04.md) A7/A9; [B05](../../architecture/BLOCK_05.md) A10/A11. [Phase0 evidence](PHASE0_WORK_ORDERS.md#phase0-execution--acceptance-2026-10-03) remains valid. No new root policy/CI/custom checker/dependency/asset/provider/commit/push is authorized by this order.

## 1. Slice / Dependency Decisions

First gameplay goal:one local space, one controlled actor, legal/blocked movement, an interactable obstacle, a small combat encounter, an autonomous NPC/delayed consequence, then durable save/load and replay of that path. This is a representative MASTER path, not completion of its physics/survival/cognition/economy/world systems. Full six-level places, NPC trait/attitude/persona/BDI/memory/anchors, procedural generation, injuries/equipment/environment and social/economy remain required future capabilities.

| Internal unit under existing RS-P1-CORE | Purpose | Entry / status |
|---|---|---|
| CORE-01 | Registered component/payload serialization, checked patch application and replay checkpoint validation on the actual driver | This complete order; DONE (2026-10-04) |
| CORE-02 | Local grid movement with successful and time-consuming blocked attempts | [Source-specific order/acceptance](RS-P1-CORE_02_GRID_MOVEMENT.md#9-core-02-execution--acceptance--2026-10-04) DONE (2026-10-04) |
| CORE-03 | Interaction and bounded combat/status path | [Source-specific acceptance](RS-P1-CORE_03_INTERACTION_COMBAT.md#9-core-03-execution--acceptance--2026-10-04) DONE (2026-10-04) |
| CORE-04 | Typed pending events,passive seconds and one autonomous NPC/consequence | [Source-specific acceptance](RS-P1-CORE_04_EVENTS_NPC.md#10-core-04-execution--acceptance--2026-10-05) DONE (2026-10-05) |
| CORE-05 | DurableCommitStore.persist, receipt recovery, validated slots and save/load replay | [Source-specific acceptance](RS-P1-CORE_05_DURABILITY_SAVE.md#11-core-05-execution--acceptance--2026-10-05) DONE (2026-10-05) |

These are subdivisions of the existing backlog parent,not extra backlog tasks. CORE-01/02/03/04 are accepted after separate complete orders and director execution requests. CORE-05 ACCEPTED/DONE;parent representative-goal review accepted2026-10-06. NEXT author staged RS-P1-GOV source-specific instructions. No implied full-Phase1 readiness. RS-P1-GOV adds applicable import/coverage/evidence/cost/migration controls against real code;eleven gates/custom tools are not installed wholesale here. Client/Factory/assets follow the existing roadmap.

CORE-02 seed, now implemented under its source-specific order:3×3 local trial space, row-major cell=3*z+x, 0≤x,z≤2; 1cell=1000mm; fixed-point coordinates derived from cell, no floats. Actor starts cell0; wall cell1. Four cardinal intents (±1,0)/(0,±1), no diagonal/zero/multi-cell jump. One attempt=1game second (1/60minute); valid blocked attempt commits tick/revision with MoveBlocked and no position delta; malformed direction rejects without time. Down:0→3 succeeds; Right:0→1 blocked by wall; Left at0 blocked by boundary. One mutable position cell field prevents unimplemented same-component field merges. Geometry/rule constants belong the new pinned trial schema/rules/checkpoint; they are new prototype values, not v1 balance or final movement cost. Query/menu/camera do not consume time. Dynamic entities/pathfinding/diagonal movement/variable durations remain later design tasks. Exact paths/types/binding/independent full trace and acceptance are in the CORE-02 source-specific order.

## 2. Actual Baseline / Observed Gap

HEAD:`efd2478ff8a6ed93ee833c3f8464a0efdd8a181a`, branch main. Existing tracked dirty files:primary prompt and MASTER (preexisting user edits). Existing untracked files:BACKLOG/SESSION_HANDOFF, architecture and order/reference docs, Phase0 config/lock and production/tests. Preserve all; remote freshness unchecked. No root AGENTS.md was found in the inspected workspace. Archived AGENTS_v1 is historical reference.

On2026-10-04 before authoring:with PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, `.venv/Scripts/python.exe -m pytest -q tests` exit0/37passed in6.89s; Ruff check exit0; strict mypy exit0/35files. Current launcher prints a preexisting location diagnostic; subprocess JSON CLI and all checks pass. Exact selected versions/13-wheel closure remain those of Phase0; no new compatibility/other-OS/bundle/performance claim or tool install. First-unit entry must refresh this baseline rather than trust the saved result.

Actual source-specific reasons for CORE-01:
- `orchestration/skeleton.py`:core_document/core_hash branch on PositionRecord/CounterRecord; command/protocol/publication encoders call the toy payload converter.
- `orchestration/turn.py:_Editor.apply_patch`:recognizes only PositionPatch/CounterPatch and concrete records. Driver fingerprints, fact validation and netdiff currently call toy converters.
- `orchestration/replay.py:_core/_command/_validate_witness`:requires actor:toy/exactly two components, ToyCodec, skeleton.stepper/RESOLVE/rank0 and feature-specific delta field names.
- `app/headless.py:_restore/_CheckpointFactory`:chooses the toy bundle and validates toy checkpoints; normal bootstrap deliberately creates two toy records.
- `contracts/skeleton.py:FeatureBundle` already registers read adapters, fields, policies, routes, presenters and payload codecs, but has no component codec, patch route or feature checkpoint policy.

Extending those central type switches for each gameplay family would defeat B02/A10 registration. First remove these dispatch assumptions through explicit ports while preserving the original simulation, canonical format and golden outputs. Retain the existing FeatureBundle module location for this bounded unit; a separate module relocation is unnecessary.

Baseline raw-byte hashes/prototype vectors: [RS-P1-CORE_REFERENCE_VECTORS.json](RS-P1-CORE_REFERENCE_VECTORS.json). Its component/command literals and tagged digests are independently derived with stdlib framing before production changes. It is not a gameplay golden or independent-person review.

## 3. CORE-01 — Complete Work Order

| Required field | Concrete contract |
|---|---|
| task_id/title | RS-P1-CORE / CORE-01:replace toy-specific state I/O and patch dispatch with registered adapters |
| status/executor/review | DONE (CORE-01 only); Sol implementation/diagnosis/integration/self-review; independent-person review UNVERIFIED |
| goal | A different registered component/command/delta/fact can pass real headless submit→COMMIT→publication→record/replay without adding a concrete branch to generic orchestration |
| non_goals | Gameplay production, multi-feature aggregation, pending/simulate routing/catch-up/variable durations, DB/save schema/migration, public IPC, Pydantic/export, client/Factory/provider, new tooling/policy/CI/dependencies |
| prerequisites | P0-002/004/001/003 DONE; source-entry checks and baseline37tests/Ruff/strict mypy pass; contracts below agree with actual source |
| read_files | Full actual files in §4, this order/vectors, BACKLOG/SESSION_HANDOFF, coding template, Phase0 contracts/work-orders/preflight/toolchain, B02 A1–A3/B03 A5–A6/B04 A7/B05 A10; MASTER §§1–3/8–9/13 |
| public_contract | NEW StateIO/ComponentCodec/PatchRoute/CheckpointPolicy; append FeatureBundle registrations; DeltaRoute.validate_net; explicit StateIO injection into Driver/replay; app state_io/restore_checkpoint entries in §5 |
| behavior | Freeze registrations→validate schema/field/patch ownership→strict typed conversion→feature policy→unchanged canonical hashing→checked sparse patch→sole existing head COMMIT→registered output encoding/replay comparison |
| edge_policy | §6:empty/duplicate/missing/schema/fields/bounds/ownership/order/pin/failure/compatibility; no invented defaults/coercion |
| examples | §7 and independent vector artifact; original five-step Phase0 golden remains byte/semantics identical |
| algorithms/wiring | §8; one serializer owner, no alternate simulation path, no hidden default registry in orchestration |
| performance | Brain512MiB/p95≤100ms/p99≤250ms and local Ruff+coregolden≤20s are inherited TARGETs, not qualification here. Record local fast-check feedback; no benchmark harness/resource counter before its own order |
| baseline_commands | §9; preserve and distinguish baseline failures; inspect callers before changing signatures |
| test_responsibilities | §7/§9; meaningful real fixture engine/reducer/presenter/policy, no mocked domain outcomes or runtime-generated golden |
| acceptance | All original37tests/complete publications/five golden steps pass unchanged expectations; new third-schema real path+strict rejection/patch guard+fresh replay pass; types/lint pass; generic modules have no concrete toy/fixture dispatch |
| stop_conditions | Protected inputs/oracle/format need changes; predecessor unexpectedly differs; unresolved target ownership/record merge/pin/package/event policy; overlapping user edit; unexplained test failure. Inspect safe in-scope fixes; otherwise report actual evidence and one needed decision |
| delivery | Exact paths/signature changes/live path/commands/results/mismatch evidence/self-review; update existing parent progress and handoff after factual acceptance; no task deletion/new parent/commit/push |

## 4. Exact Future Implementation Edit Scope

NEW production:
```text
C:\Reverie Saga\src\contracts\state_io.py
C:\Reverie Saga\src\orchestration\serialization.py
```

MODIFY production (only the named registration/I/O/patch/validation/wiring responsibility):
```text
C:\Reverie Saga\src\contracts\skeleton.py
C:\Reverie Saga\src\orchestration\skeleton.py
C:\Reverie Saga\src\orchestration\turn.py
C:\Reverie Saga\src\orchestration\replay.py
C:\Reverie Saga\src\app\feature_registry.py
C:\Reverie Saga\src\app\headless.py
```

NEW tests (prospective names, not claims that source exists):
```text
C:\Reverie Saga\tests\unit\registered_io_fixtures.py
C:\Reverie Saga\tests\unit\test_registered_io.py
C:\Reverie Saga\tests\integration\test_registered_state.py
C:\Reverie Saga\tests\replay\test_registered_replay.py
```

MODIFY tests for explicit registry/signature wiring only; retain all assertions/expected values:
```text
C:\Reverie Saga\tests\unit\test_canonical.py
C:\Reverie Saga\tests\integration\test_skeleton.py
C:\Reverie Saga\tests\replay\test_golden.py
C:\Reverie Saga\tests\replay\test_contamination.py
```

MODIFY delivery docs: `C:\Reverie Saga\BACKLOG.md`, `C:\Reverie Saga\SESSION_HANDOFF.md`, `C:\Reverie Saga\docs\work_orders\RS-P1-CORE_VERTICAL_SLICE.md` (actual results), `C:\Reverie Saga\docs\work_orders\PHASE0_CONTRACTS.md` (dated source API supersession only; preserve old Phase0 format/evidence). All other paths READ. In particular domain records/primitives/canonical, view factory, scheduler, engines, error/turn/replay/message DTOs, config/lock, original vectors/golden fixture, primary specs/template/historical AGENTS, C:\Quilltale, policies/CI/tools/assets remain READ. Cache artifacts from existing tools remain local/ignored. Additional source paths require a focused refreshed order; no implicit helper package or test deletion.

## 5. NEW / Modified Public Contracts

Types below import existing domain/contracts types; no duplicate primitive, growing component union, Any or engine-facing JSON. Concrete codec/policy/patch implementations are trusted feature boundary adapters, never engine input. JSON exists only at strict serialization/checkpoint boundaries; immediately own/seal it with existing canonical validators. Domain value/state imports stay below contracts; feature codec and PatchRoute implementations may inspect frozen concrete records at this trusted boundary.

NEW `contracts/state_io.py`:
```python
from __future__ import annotations
from typing import Protocol

class ComponentCodec(Protocol):
    @property
    def schema(self) -> TypeKey: ...
    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord: ...
    def encode(self, record: ComponentRecord) -> JsonObject: ...

class PatchRoute(Protocol):
    @property
    def schema(self) -> TypeKey: ...  # patch schema
    @property
    def component_schema(self) -> TypeKey: ...
    @property
    def family(self) -> FieldFamily: ...
    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord: ...

class CheckpointPolicy(Protocol):
    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None: ...

class StateIO(Protocol):
    @property
    def pins(self) -> SimulationPins: ...
    @property
    def schedule(self) -> CompiledSchedule: ...
    def validate_checkpoint(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None: ...
    def encode_core(self, core: CoreSnapshot) -> JsonObject: ...
    def decode_core(self, document: JsonObject) -> CoreSnapshot: ...
    def hash_core(self, core: CoreSnapshot) -> str: ...
    def encode_payload(self, payload: FrozenPayload) -> JsonObject: ...
    def encode_command(self, command: GameCommand) -> JsonObject: ...
    def decode_command(self, document: JsonObject) -> GameCommand: ...
    def encode_protocol(self, protocol: ProtocolSnapshot) -> JsonObject: ...
    def decode_protocol(self, document: JsonObject, core: CoreSnapshot) -> ProtocolSnapshot: ...
    def encode_publication(self, publication: TurnPublication) -> JsonObject: ...
    def decode_outcome(self, document: JsonObject) -> TurnOutcome: ...
    def validate_effects(self, command: GameCommand, outcome: TurnOutcome,
                         core: CoreSnapshot, protocol: ProtocolSnapshot,
                         facts: JsonValue, diff: JsonValue) -> None: ...
    def apply_patch(self, address: ComponentAddress, allowed: FieldAddress,
                    before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord: ...
```

`FeatureBundle` keeps all existing fields/types/order; append three required fields, no fabricated empty defaults: `component_codecs:tuple[ComponentCodec,...]`, `patch_routes:tuple[PatchRoute,...]`, `checkpoint_policy:CheckpointPolicy`. Sole production constructor `app.feature_registry.skeleton_bundle` explicitly supplies Position/Counter codecs, matching scalar patch routes and SkeletonCheckpointPolicy. Existing dataclass.replace-based test bundles inherit these registrations. Read keys/adapters/FieldSpecs/command routes/delta routes/presenters/payload codecs remain explicit.

`DeltaRoute` appends `is_identity(self,delta:StateDelta)->bool` and `validate_net(self, delta:StateDelta, after:ReadPort)->None`. is_identity validates the concrete delta and returns exact bool for a net no-op; Driver calls it after compose and omits only identity deltas. The pure validate_net validator rejects no-op/invalid published netdelta and checks the committed target value using its typed read key; it does not stage/edit/emit. Generic replay supplies a finally-expired observed read view, allowing only delta.target reads and no writes. PositionReducer/CounterReducer implement both using their already-settled old/new/range semantics. This replaces central assumptions about `expected_old`, `new`, `x` and `visits`; new payloads may use different field names. A legitimate zero Step still stages/commits its Counter change and emits Stepped; it must not abort merely because the composed Position delta is identity.

Concrete NEW `orchestration.serialization.RegisteredStateIO(bundles:tuple[FeatureBundle,...],schedule:CompiledSchedule)` implements the whole StateIO protocol; one immutable registration index per instance, no process-global registry/cache. Unit supports exactly one feature bundle, arbitrarily many of its registered component schemas/entities subject to explicit policy/caps. Multi-feature fingerprint aggregation awaits its own order. It seals descriptor/rule documents, derives the same existing schema/rules/catalog/schedule/algorithm pins and dispatches by exact TypeKey. No fallback ToyCodec, reflection/class discovery for schema dispatch or component-specific branch. Structural frozen-dataclass traversal checks immutable DTO children only; it never discovers registrations or selects codecs/routes.

Existing `orchestration.turn.Driver(core,protocol,bundles,schedule,rng,definitions=None)` adds required keyword-only `io:StateIO`. Verify IO pins/schedule match the selected registry/head before admission; retain original optional definitions argument and all submit/outcome/publication semantics. `_Editor` gets that IO; patch application returns validated immutable replacement. No engine sees IO, component records, patches, headers, protocol receipts, root handles or bytes.

Existing replay DTO/Protocol fields do not change. Concrete signatures become:
```python
def decode_fixture(body: bytes, *, io: StateIO) -> ReplayFixture: ...
def encode_fixture(fixture: ReplayFixture, *, io: StateIO) -> bytes: ...
def validate_checkpoint(core: CoreSnapshot, protocol: ProtocolSnapshot, *, io: StateIO) -> None: ...
# Recorder(header:ReplayHeader,*,io:StateIO)
# Runner(initial_core:CoreSnapshot,initial_protocol:ProtocolSnapshot,
#        *,factory:ReplaySessionFactory,io:StateIO)
```

Explicit injection is an intentional in-process API change, not a save/replay format change. Update every actual caller in the listed app/tests; old signatures in PHASE0_CONTRACTS describe the historical implementation. No hidden orchestration default imports app or chooses a feature. Recorder/Runner must use their injected IO for every core/command/protocol/publication/witness validation/hash path; fresh factory session each run remains required.

App NEW/modified entries:
```python
def state_io(bundles: tuple[FeatureBundle, ...]) -> StateIO: ...
def restore_checkpoint(core: CoreSnapshot, protocol: ProtocolSnapshot, *,
                       bundles: tuple[FeatureBundle, ...],
                       rng: RngService | None = None) -> HeadlessSession: ...
def replay_runner(fixture: ReplayFixture, *,
                  bundles: tuple[FeatureBundle, ...] | None = None) -> ReplayRunner: ...
```

`state_io` compiles the supplied explicit registry once and returns RegisteredStateIO. Bootstrap assembles its original toy records, then shares that IO/schedule with private owner initialization (do not compile twice per session). restore_checkpoint validates strict registered state/protocol/pins before publishing a head, initializes the same Driver/_Session, and creates default qualified CounterRngService with existing app purposes; no disk API/durability or schema migration is promised. replay_runner omitted bundles retains the normal toy feature; a foreign fixture must supply its explicit registry. `_CheckpointFactory` stores selected frozen bundles and calls this same validated owner path afresh; orchestration never imports app. BootstrapSpec/HeadlessSession/CLI stdin contract and original bootstrap parameters remain unchanged.

Generic canonical serialization helpers currently in orchestration/skeleton move to RegisteredStateIO/serialization; remove duplicate generic implementations and update listed callers. Keep feature-local payload_document/ToyCodec and toy adapters/admission/reducers/presenter, plus key helpers if still used by those feature codecs. Old generic helper imports must not retain an implicit toy registry fallback. Existing CLI emits the same publications using its session IO; different registered checkpoint session.submit_json exercises exactly that decoder/driver/encoder path.

## 6. Algorithms / Errors / Limits

Registration at boot:
1. Resolve selected engine bindings/compiled schedule, codecs, field specs, adapters, reducers/presenters/policies. Freeze/own registrations and descriptor/rule values.
2. Duplicate feature/schema/component/patch schema/target-family or missing codec/adapter/field/owner is BootstrapError(DUPLICATE_SCHEMA/WRITE_CONFLICT as applicable). One active component version per kind in this unit; multiple active versions need a separate migration/reader contract. Every component codec's encoded fields exactly match its FieldSpec families, including immutable/read-only fields; validate storage/tier/units/ranges through codec + metadata. Every patch family references one registered component schema/declared field and its owner/reducer. Immutable checkpoint-only fields may name the explicit reserved owner system.bootstrap with no turn writer; mutable fields require a declared engine owner. Do not fabricate a bootstrap engine or empty route for immutable fields.
3. First unit preserves conservative staging:at most one mutable field family of a component kind per phase. Reject multiple families even from one engine with WRITE_CONFLICT until record merge semantics have a separate contract. Different entities of that one family can be patched independently; duplicate concrete target remains DUPLICATE_TARGET. This prevents `_Editor` replacements at a shared phase root from overwriting another field's staged change.
4. Pins equal the original single-bundle documents/schedule; adding runtime codec objects does not add fields to hashed source descriptors or change pinned rules. Unsupported schema versions are never treated as current.

Component/checkpoint conversion:
- CORE document exactly the existing format:world_id/world_seed_hex/tick/components/pending/pins; component document schema/entity_id/fields. Hash leaf tag component/v1, root core-root/v1 over schema/entity/hash entries; same pack framing/canonical JSON, not a new hash algorithm/version. Component sort=(kind,version,entity); duplicate address/unsorted incoming document rejected rather than silently collapsed/reordered. Empty components permitted only if explicit feature policy permits and no protocol actor is orphaned; Skeleton policy requires the existing two toy records. Registry permutation yields equal pins/documents/hash.
- Strict JSON UTF8/NFC, duplicate/unknown/missing fields, bool/float/int/range, immutable children/depth checks preserve Phase0. Codec returns exact registered schema and requested entity, encoding is owned canonical JsonObject, unsupported class or version fails SchemaError(UNSUPPORTED_SCHEMA,path); malformed registered shape fails SchemaError(INVALID_COMPONENT/INVALID_PAYLOAD,path). No untyped default record from missing fields. Existing view adapter validates decoded records before any engine reads.
- Tick/revision/sequence bounds, stream16/receipts1024, branch/stream syntax/actor ownership/high-water/retirement/fingerprint/receipt consistency stay as Phase0. CheckpointPolicy owns feature-specific required components, actor membership, bounds and cross-record references. Common serializer owns IDs/order/hash/tree/protocol structure. Validate actual registered pins/world identity before execution, not just a self-consistent arbitrary fixture header.
- pending/gameplay_packages/build_artifacts remain empty for this unit; simulate delivery, nonzero waves/causes/degradation and package/migration readers remain explicitly unsupported. Keep RNG/hash versions and scope behavior unchanged. Do not accept these fields through a fake fallback.

Checked patch:
1. Find exact registered patch schema; require its component_schema/family match address and allowed target; require before has that address.
2. Call pure feature PatchRoute.apply on the immutable before record. Verify original remains unchanged; replacement schema/entity unchanged; component codec validates ranges/shape/immutability.
3. Encode before/after with that component codec; key sets identical and only `allowed.family.field` may differ. Reject identity/field/owner/range violation with CandidateError(INVALID_DELTA or UNDECLARED_WRITE), causal error retained. Editor stores sparse replacements only, and existing phase barrier publishes them to the next phase; `_head` assignment remains the sole authoritative commit. No mutable record pointer is given to engines.

Facts/diff/outcome:
- Decode each payload using its exact registered PayloadCodec; verify CommandPayload/FactPayload/StateDelta/PresentationPayload family as appropriate. Envelope shapes/ordered facts/netdiff/receipt/failure format stay unchanged.
- For record-only facts, validate registered EventPolicy producer/emitted kind and actual emitting schedule node `(phase,producer_id)`, A-only global producer rank, tick/wave0/local sequence/event ID formula, empty causes/degradation and due-now rule. Do not hardcode skeleton.stepper or RESOLVE; a legitimate registered POST_TICK producer also validates. Facts cap512 remains; no trimming. Generic cancellation/late routing awaits CORE-04.
- Diff receipt matches committed outcome/head; retained duplicate original receipt is valid only with no new facts/null diff. Failed submissions publish no effects. Decode each delta by its codec; validate registered reducer ownership/target and canonical unique target order; reject is_identity(delta)=True in a published diff, then invoke DeltaRoute.validate_net using a finally-expired after view. Corrupt/unknown/inconsistent witness/checkpoint remains ReplayFormatError before factory restore/first command.
- Technical engine/serialization/reducer failure before COMMIT aborts old CORE+protocol atomically; postcommit presentation error retains committed effects. JSON malformed command remains INVALID_COMMAND/current_revisionNone; supported typed route errors preserve existing admission/retry behavior. No diagnostics repr/time/address enters CORE or outcome hashes.

## 7. Independent Examples / Planned Tests

Fixture-only types NEW in tests/unit/registered_io_fixtures.py (not gameplay schemas):GaugeRecord(entity_id,value,label), GaugeRead.value/label, AdjustCommand(amount), GaugeDelta(subject,before_value,after_value), GaugePatch(value), GaugeChanged(subject,before_value,after_value). Namespace fixture.gauge/adjust/gauge-delta/gauge-patch/gauge-changed, version1. Value -9..9, amount -3..3 exact integer, label NFC1..64UTF8bytes. GaugePatch changes value only. Mutable value CORE/A owned by fixture.adjuster; immutable label CORE/A owned by system.bootstrap, codec/policy and read wrapper consume it. Fixture label "계기"; registered CheckpointPolicy permits exactly GaugeRecord(actor:sample) and corresponding actor-bound protocol. Engine fixture.adjuster, one RESOLVE node, action fixture.adjust, reads/writes gauge.value, emits GaugeChanged record-only due-now. Fixture presenter consumes it and returns a cue with the same independent subject/before/after values (feature-owned schema fixture.gauge-cue/v1); it must use guarded committed reads. Purpose-built fixtures implement real ports; no patching/mocking the driver/outcome.

Examples settled BEFORE implementing:
- value2 + amount3 → value5,tick0→1,revision0→1; one delta/fact/cue; label identical. Original record value2 remains immutable and old aliases expire. Full component/command canonical UTF8 and tagged hashes are in the vector artifact.
- value5 + amount−3 → value2 at tick2/revision2. Exact retry of first command returns receipt1/no effects, current state stays2; stale sequence3 expected_revision0 rejects without changes. Different amount under retained first ID rejects COMMAND_ID_CONFLICT.
- value9 + amount1 is rejected by fixture admission with INVALID_COMMAND/current revision and no time; amountTrue/float4.0/unknown field/missing label/non-NFC label/version2 rejected strictly. No clamping/default filling.
- PatchRoute that changes label too, changes entity/schema, returns out-of-range10 or uses unregistered patch schema aborts before CORE/protocol/high-water mutation. Same-phase declarations for value+label reject boot until field merge semantics are implemented.
- Reversed registry order preserves documents/pins; duplicated codec/family fails boot. Different codec/policy fixture can support multiple registered component records; common serializer never assumes two toy records or actor:toy. Snapshot/witness omission of a required field/entity fails before commands.
- Registered POST_TICK emitting variant must validate rank/node/IDs by the real schedule, not a hardcoded phase/producer. Removing GaugeChanged alone fails `$facts[0]` while state/protocol/diff match. Repeated replay/fresh sessions and per-instance registry isolation preserve outputs. Self-consistent field tampering reports the actual first leaf path; inconsistent witness fails load.

Planned meaningful nodes:
| File | Nodes / responsibility |
|---|---|
| tests/unit/test_registered_io.py | test_component_literal_vectors; test_exact_schema_fields_and_ranges; test_duplicate_registration; test_registry_order; test_policy_required_records; test_patch_single_field_guard; test_same_component_write_conflict |
| tests/integration/test_registered_state.py | test_foreign_schema_real_turn; test_foreign_json_submit; test_foreign_retry_and_abort_atomicity; test_registered_post_tick_fact; test_finally_expiry_and_presenter |
| tests/replay/test_registered_replay.py | test_registered_roundtrip_trace; test_registered_fact_loss; test_registered_wrong_leaf; test_registered_pins_before_execution; test_fresh_registry_sessions |

Existing assertion/expected-byte preservation is mandatory:tests/unit/test_read_views.py (READ), canonical vectors, test_skeleton complete publication comparisons, original five-step test_core_trace/negative witness and contamination nodes. Adapt explicit IO call wiring only; no expected-hash rewrite, test removal/skip/xfail, or weakened assertion. New component literals must come from the independent artifact; full fixture trace state values/outcomes are authored from this section, not Recorder output. If an independent full trace needs byte/hash construction, use a separately authored stdlib reference calculation and retain its source as evidence outside runtime; never use the new serializer/driver to generate expected results. Recorder-generated trace alone is roundtrip evidence.

## 8. Implementation Steps / Live Path

1. Refresh HEAD/status/input hashes/callers, run baseline; compare actual Phase0 behavior and signatures with this order. Preserve all unrelated edits.
2. Add contracts/state_io protocols; append FeatureBundle registrations and DeltaRoute.validate_net. Implement toy component codecs/patch routes/policy in orchestration/skeleton and register explicitly in app/feature_registry; preserve schema/rules literal bytes.
3. Implement RegisteredStateIO strict owned dispatch/metadata/common envelopes/hash/policy and guarded netdelta validation. Keep domain canonical unchanged; relocate common helper responsibility without duplicate fallback implementations.
4. Inject IO into Driver/_Editor, replace toy fingerprint/fact/diff/hash calls with IO.encode_command/encode_payload/hash_core; compose net changes using reducer.is_identity, add conservative same-component write-family boot rejection. Before the sole head assignment, validate candidate checkpoint and prepared effects through IO; any codec/policy/netdelta failure aborts the old head. Validate encoded cues/publication inside the existing postcommit presentation try boundary so a bad cue codec becomes PRESENTATION_FAILED without losing receipt/facts/diff. Phase barriers, schedule, views, RNG, COMMIT and retry semantics remain intact.
5. Route app state_io/bootstrap/restore_checkpoint/_Session through the same frozen registry, schedule and owner. CLI default still toy; foreign registered fixture is reached through actual restore_checkpoint and submit_json.
6. Make all replay functions/Recorder/Runner use injected IO and selected factory. Prevalidate all initial/header/step witnesses before first command, preserve precise mismatch paths and fresh sessions. Update every listed caller explicitly.
7. Add fixture-only real alternate engine/adapter/reducer/presenter/policy and independent tests; verify type/registration/ownership/atomicity, alternate phase and replay/fact-loss. Do not modify the original oracle or generic dispatch to recognize the fixture.
8. Run §9, inspect complete changed source/diff/allowed scope/layers/callers and final live path; record actual evidence. Only then CORE-01 accepted; author CORE-02 against this actual source.

## 9. Commands / Acceptance Evidence

At source entry and final acceptance (actual results REQUIRED, not implied by these commands):
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

Future focused nodes only AFTER files exist:
```powershell
.venv/Scripts/python.exe -m pytest -q tests/unit/test_registered_io.py tests/integration/test_registered_state.py tests/replay/test_registered_replay.py
rg -n 'PositionRecord|CounterRecord|PositionPatch|CounterPatch|ToyCodec|skeleton\.stepper|actor:toy' src/orchestration/serialization.py src/orchestration/turn.py src/orchestration/replay.py
```

The latter search should have no concrete dispatch match in those three generic modules. Inspect imports/branches/callers manually; this search is not a custom governance checker or proof of all dependency properties. Toy feature adapters/app may legitimately contain their own types. Compare original fixture/oracle/config/lock/protected-input raw hashes with the saved baseline; inspect new/untracked source/doc whitespace too (git diff --check alone does not include it). Fast Ruff+core golden timing is local feedback only.

Acceptance matrix:explicit component/patch/policy registration; old golden and hash/framing stability; foreign schema real turn/JSON/replay; strict component/command/protocol/witness rejection; one-field patch and owner/identity guard; correct non-toy event node/rank/sequence; precise fact/leaf mismatches; fresh session/registry isolation; sole COMMIT and finally-expired reads; layer direction/no central type union; no protected-input/scope drift. Every row requires actual evidence during implementation. Actual CORE-01 results are in §11; later gameplay units remain NOT_RUN.

## 10. Authoring Delivery Evidence

This section records documentation authoring only. The saved Phase0 baseline was reexecuted (37tests/Ruff/mypy PASS); source tests/config/reference fixture remain unchanged. New order paths/ports have been compared with actual source and callers; all prospective paths clearly NEW, all future nodes PLANNED, and only CORE-01 promoted. Independent vector source and baseline hashes are retained in the linked JSON. Document links/fences/interface syntax/required fields/status/protected-source hashes are checked before delivery; actual authoring check results are appended here after execution. No production feature or later unit is marked implemented. For reference-source reproduction on Windows, set PYTHONIOENCODING=utf-8 before running its Unicode stdout; this is outside the domain/runtime. Initial artifact generation wrote valid UTF8 JSON then exited1 only while printing its Korean label through cp1252 stdout; subsequent strict load/label/hash checks verified the artifact and used ASCII diagnostic output.

Actual authoring verification2026-10-04:one-off stdlib document inspection exit0;3Python declaration fences AST-parse/compile; required work-order fields, existing source/caller paths and future edit scope, document links/fences/whitespace PASS; all45source/config/fixture/protected-input hashes remain identical to the captured baseline. Independent canonical UTF8/u32/SHA256 values recomputed with length.to_bytes framing (separate from reference struct.pack framing) PASS; retained reference_source executed under a captured Unicode stream and matched all3literal output lines. New production paths contracts/state_io.py and orchestration/serialization.py are still absent. `git -c safe.directory='C:/Reverie Saga' diff --check` exit0; preexisting primary/MASTER LF→CRLF warnings only, their raw hashes unchanged. Review additionally settled explicit encode_payload and DeltaRoute.is_identity so zero Step compatibility cannot be broken by a generic netdelta validator.

Authoring changed exactly NEW2files (this order,its vectors) +MODIFY3existing docs (roadmap,BACKLOG,SESSION_HANDOFF). No runtime/test/config/primary/oracle/policy edit. Decision:CORE-01_INSTRUCTION_ACCEPTED/READY; parent gameplay implementation and later unit tests NOT_RUN. Next is execution of CORE-01, then source-based CORE-02 authoring.


## 11. CORE-01 Execution / Acceptance — 2026-10-04

Director request "다음 ㄱ" authorized execution of the settled CORE-01 order. Source entry:HEAD efd2478ff8a6ed93ee833c3f8464a0efdd8a181a/main unchanged; all45 baseline raw hashes matched; original37tests PASS in6.92s, Ruff PASS, strict mypy35files PASS. Existing primary/MASTER edits and all unrelated files preserved. This section supersedes authoring-only status above; historical authoring evidence is retained.

Delivered exact allowed scope:NEW contracts/state_io.py and orchestration/serialization.py; MODIFY contracts/skeleton.py, orchestration/skeleton.py/turn.py/replay.py, app/feature_registry.py/headless.py. NEW tests/unit/registered_io_fixtures.py/test_registered_io.py, tests/integration/test_registered_state.py, tests/replay/test_registered_replay.py. Existing four listed tests changed only explicit IO/factory/signature wiring and the fault-injection refinement below; all expected hashes/bytes/assertions retained. Delivery docs updated within §4. No domain/canonical/view-factory/scheduler/engine/error/replay-DTO/config/lock/original oracle/protected-spec/policy/CI/other path edit.

Actual live path:app.state_io compiles once→RegisteredStateIO owns sealed schema/rules and immutable registration indexes→same Driver validates head→pure admission/guarded engines→registered reducer/editor/patch→candidate codec/policy/effect/net-validator checks→sole authoritative head COMMIT→registered presentation encoding. restore_checkpoint uses that owner path; foreign Gauge submit_json decodes through injected IO; default CLI still uses the original toy bundle. Replay decoding/Recorder/Runner explicitly use selected IO and prevalidate every witness before a fresh factory restore. Generic serialization/turn/replay contain no toy/fixture concrete dispatch or implicit app imports. Original format_version1, canonical framing/tree hashes and literal pins/publications/five-step golden are unchanged.

Execution refinements, no public-format change:
- Existing UNKNOWN_ACTOR test formerly restored an intentionally orphaned private checkpoint. Strict public restore now correctly rejects that state. The test first restores a valid owner, then injects the same missing-actor head privately; both original assertions remain. No production validation bypass was added.
- Read-view factory forbids COMMIT epochs. Net validation uses a private candidate/committed-root PRESENT read epoch, finally closes it and permits only delta.target reads/no writes. It does not move the head or expose IO to engines.
- Registered frozen-dataclass child inspection verifies immutability/depth, never discovers a schema/codec/route. Codec documents are owned/sealed. Runtime component/payload descriptor coverage and field owner/unit/scale/bounds must match the pinned descriptors; missing route codec/adapter/owner and ambiguous patch family fail boot.
- Replay witnesses exclude presentation. Runner serializes simulation effects with cues omitted so removal of a fact is reported as a facts mismatch even when its real cue remains. Driver validates complete cue/source/codec encoding inside the postcommit try boundary; Recorder validates actual complete publication before append.
- Identity patches remain permissible for zero actions; composed net identity deltas are omitted. Zero actions retain their existing tick/counter/fact semantics.

Independent evidence:preimplementation component/command vectors remain READ and match exact UTF8/hex/tagged digests. NEW fixture helper reference_body is a separately authored requirements calculation using only stdlib JSON/u32 framing/SHA256 for full five-step Gauge expectations (2→5→2→retry→stale→conflict), including a self-consistent wrong6 witness. It calls no driver/serializer/Recorder to derive expectations and lives outside production. Real recorded steps equal that independent trace. Wrong leaf:step0 $core.components[0].fields.value expected6/actual5. Dropped GaugeChanged:steps0/1 $facts[0] actual<missing>, with matching simulation head/protocol/diff. This is self-review and independent calculation, not independent-person review.

Final commands/results (after final production/test changes):
- PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; `.venv/Scripts/python.exe -m pytest -q tests --tb=short`:exit0,59passed in22.19s (all37original+22new).
- `.venv/Scripts/python.exe -m ruff check src tests`:exit0,All checks passed.
- `.venv/Scripts/python.exe -m mypy --strict src tests`:exit0,41sourcefiles PASS.
- Focused new unit/integration/replay suite:22passed in0.62s; no skips/xfails/mocked domain outcomes.
- `.venv/Scripts/python.exe -m pytest -q tests/replay/test_golden.py::test_core_trace`:exit0,1passed in0.18s. Ruff+this core golden measured0.8756656s locally; p95/p99/memory/device/bundle qualification remains UNVERIFIED.
- Generic dispatch search has0matches; input-hash/scope/link/fence/whitespace and git diff --check checks recorded after delivery-doc edits. Existing Python launcher location diagnostic remains on stderr; JSON CLI and checks pass.

Acceptance covered:third-schema actual turns/JSON/replay; multiple registered entities under explicit policy; strict bool/float/fields/NFC/version/order rejection; owned descriptors/registry permutation/registration errors; same-component phase writer conflict; patch label/entity/schema/range/unknown-type atomic failures; policy/net-validator atomic failure; net read/write observation and finally expiry; POST_TICK producer at global A rank1 after a real observer; expired engine/presenter aliases; postcommit cue-codec failure retains receipt/facts/diff; original ±1/0/abort/retry/retired/golden/RNG/hashseed/cache/world isolation. Review found and repaired registration coverage/metadata and Recorder error-boundary gaps before final checks.

Decision:CORE-01 ACCEPTED/DONE; parent RS-P1-CORE IN_PROGRESS. NEXT:author CORE-02 grid movement against this source, then execute its complete order. CORE-02–05 gameplay/pending/durability and full-game systems remain unimplemented; no later READY/DONE claim. No agents/new dependency/install/governance/commit/push/external write.

Delivery-doc verification:35protected baseline inputs retain their raw hashes; changed baseline inputs are exactly the6allowed production+4allowed test files. One-off AST/whitespace/document links/fences inspection PASS after excluding fenced/inline code from Markdown link parsing (initial regex falsely treated a historical generic Protocol declaration as a file link). Generic dispatch search0matches; git diff --check exit0 (preexisting primary/MASTER LF-to-CRLF notices only). Final document headers/parent/next-unit status agree with acceptance; no skipped/deleted tests or future-unit completion claim.


## 12. CORE-02 Instruction Successor — 2026-10-04

Director requested the next item after CORE-01 acceptance. [CORE-02](RS-P1-CORE_02_GRID_MOVEMENT.md) instruction READY; [independent vectors](RS-P1-CORE_02_REFERENCE_VECTORS.json) retain current56input hashes,32cardinal boundary/wall/success cases,9coordinate examples and10complete replay/publication steps. The source-specific order adds6feature modules/4test modules/1fixture on future execution while existing generic/runtime/tests/config/oracles remain READ. It settles fixed map/position ownership, typed views/membership observation, blocked consuming attempts/empty diffs, registry/app bootstrap/CLI, strict errors/ports and full independent expectations. Current59tests/Ruff/strict mypy41files PASS; actual scheduler matches the new independent schedule literal. Authoring changes docs only; movement production/tests NOT_RUN. CORE-01 remains DONE; parent RS-P1-CORE IN_PROGRESS; CORE-03–05 DRAFT. NEXT:execute CORE-02.


## 13. CORE-02 Execution Successor — 2026-10-04

Director request "다음꺼 ㄱ" executed [CORE-02](RS-P1-CORE_02_GRID_MOVEMENT.md#9-core-02-execution--acceptance--2026-10-04):6new feature modules/4test modules/1independent fixture,5delivery docs; original runtime/tests/config/lock/oracles/specs preserved. Real cardinal grid movement/blocked consuming commits/strict errors/retry/atomicity/derived cues/CLI and explicit registered restore/Recorder/Runner are wired through the same Driver.32movement cases/10complete literal publications/replay/precise fact-loss and wrong-leaf diagnostics PASS.143tests (59previous+84new) in24.02s,Ruff PASS,strict mypy51files PASS; original+trial goldens2passed in0.45s. Detailed exact scope/source pins/byte/hash/limits are in the linked acceptance. §§11–12 retain historical predecessor/authoring evidence; this section supersedes their next-unit statuses. CORE-01/02 DONE,parent RS-P1-CORE IN_PROGRESS,CORE-03–05 DRAFT. NEXT:author CORE-03 interaction/bounded combat against actual accepted source; numerical resources/status/targets/death/ownership and independent examples must settle before READY. Self-review only; no agents/install/dependency/commit/push/external write.


## 14. CORE-03 Instruction Successor — 2026-10-04

Director requested the next item after accepted CORE-02. [CORE-03 gate/encounter order](RS-P1-CORE_03_INTERACTION_COMBAT.md) READY;[independent vectors](RS-P1-CORE_03_REFERENCE_VECTORS.json) retain85entry inputs,11field/23payload descriptors,112movement/30attack/30interaction/3rest cases,24main+5death complete trace/publication steps and a self-consistent wrong-cell prefix. Two RESOLVE nodes use disjoint writers:actions owns separate HP/stamina/gate components,movement retains original trial.movement position owner. Trial map/position/codecs/geometry reused unchanged;dynamic blocker facts/cues and explicit encounter bundle/CLI are NEW prospective paths. Single-turn attack/counter atomically updates both entities and stamina;derived death frees enemy occupancy;invalid target/range/resources/dead actor reject without time;blocked/repeat/full-rest consume1second. Exact contracts/scope/failure/pins/independent expected bytes settled. Baseline143tests in23.94s/Ruff/strict mypy51files PASS. Authoring edits2NEW docs/artifact +3existing delivery docs only;no runtime/tests/config/oracle/spec edits. CORE-01/02 DONE,parent IN_PROGRESS,CORE-03 instructionREADY/implementationNOT_STARTED,CORE-04–05 DRAFT. NEXT:execute CORE-03,then author CORE-04 from accepted actual source. Historical §§11–13 remain evidence for their entry scopes;this section supersedes their next-unit statuses. Self-review only;independent-person/performance/full-game qualification UNVERIFIED.


## 15. CORE-03 Execution Successor — 2026-10-04

Director's subsequent "다음꺼 ㄱ" executed [CORE-03 gate/encounter](RS-P1-CORE_03_INTERACTION_COMBAT.md#9-core-03-execution--acceptance--2026-10-04),ACCEPTED/DONE. Six new feature/four test modules/two copied independent fixtures/five delivery docs;all previous source/tests/config/oracles/specs unchanged. Door/attack/counter/rest/death/dynamic occupancy use one explicit encounter bundle/IO and existing Driver/restore/Recorder/Runner;two disjoint RESOLVE writers atomically update HP for both entities and player stamina.112movement/30interaction/30attack/3rest cases,29full independent publications/replay/Recorder and24JSON CLI outputs PASS.431tests in38.94s (143previous+288new),Ruff PASS,strict mypy61files PASS;4coregoldens1.92s/Ruff+goldens2.7793083s local feedback. Strict admission/receipt/death/no-op/atomic fault/target-only reducer/finally/postcommit/MAX/checkpoint/source-pin/precise missing-fact/counter/wrong-cell coverage PASS.81READ historical hashes and reference artifact/original fixtures retained. Exact contracts/source pins/scope/limits in the linked acceptance;§§11–14 retain history,this section supersedes their next statuses. CORE-01/02/03 DONE,parent RS-P1-CORE IN_PROGRESS,CORE-04–05 DRAFT. NEXT:author CORE-04 typed pending/passive/autonomous NPC order against actual accepted source;future queue/clock/wave/causal routing scope/errors/independent expectations must settle before READY. Self-review only;no agent/dependency/install/policy/CI/commit/push/external write or full-game/performance/independent-person qualification.


## 16. CORE-04 Instruction Successor — 2026-10-05

Director requested the stated next item after CORE-03 acceptance and an explanation of its relation to NPC emotion. [CORE-04 time/events/autonomous watcher order](RS-P1-CORE_04_EVENTS_NPC.md) READY;implementation NOT_STARTED. [Independent vectors](RS-P1-CORE_04_REFERENCE_VECTORS.json) retain99entry raw hashes,40payload/16field/7node descriptors,13main+1passive full publications/witnesses,2no-time dead cases,480composition/8cascade/6ordering/11limit cases and a self-consistent wrong-reply prefix. Settled typed pending codec/leaf hashes,clock/queue sole authority,canonical dense seconds/final-tick action/subscriber phase-wave routing/causes/limits/late errors/full batches/atomic queue+CORE+protocol and historical NPC cues. One stationary watcher pulses every2seconds and responds to a Bell;passive charge caps3. These are scheduling/event foundations for later emotion/attitude/persona/BDI/memory,which remain required and unimplemented.

Authoring edits only2NEW order/artifact+3delivery docs;future exact8NEW production/3MODIFY generic source/6NEW test-helper/2NEW fixtures/5delivery docs declared,other runtime/tests/config/oracles/specs remain READ. Entry431tests38.08s/Ruff/strict mypy61files PASS. Independent23result sections reproduce and alternate length framing agrees;actual scheduler compiles exact7nodes/pin/reversed registration;old5schemas/23payloads/encounter rules preserved;all44old fixture CORE hashes stay identical under completed pending formula.96READ entry hashes retained/3allowed delivery-doc differences;artifact1519959bytes/SHA2561cbd41e8bb13f11292c6b1d260325f3f7c99eb7c64cf48d8d3e4c641de196fdb. Interface syntax/prospective paths/literal UTF8/pins/links/scope checks PASS;future source/tests/CLI NOT_RUN. Detailed readiness evidence in order §9. §§11–15 remain historical evidence;this section supersedes their next-unit statuses. CORE-01/02/03 DONE,parent RS-P1-CORE IN_PROGRESS,CORE-05 DRAFT;NEXT execute CORE-04,then author CORE-05 against accepted queued execution. Self-review only;no agent/dependency/install/commit/push/external write/full-game/performance/independent-person qualification.


## 17. CORE-04 Execution Successor — 2026-10-05

Director authorized execution with "다음거 ㄱ". [CORE-04](RS-P1-CORE_04_EVENTS_NPC.md#10-core-04-execution--acceptance--2026-10-05) ACCEPTED/DONE.8NEW production/3MODIFY generic runtime/6NEW test-helper modules/2independent fixtures/5delivery docs;other previous source/tests/config/oracles/specs unchanged. Same Driver/selected IO now provide canonical1..16second dense ticks,causal delayed/subscriber/phase-wave queues,sole clock/queue authority and one outer atomic commit. Stationary watcher acts every2seconds,Bell triggers REACT/CASCADE reply,passive charge caps3. Registered full pending hashes/restore/Recorder/Runner/JSON CLI match complete independent main/passive/dead traces;480wait compositions/8cascade vectors and event512tick/8192outer/4096queue bounds pass,as do sorted multisubscriber batches/late deferral/overflow/strict codecs/finally/atomic/postcommit/pin and negative leaf diagnostics.1009tests111.20s (431old+578new),Ruff/strict mypy75files PASS;6goldens3.14s/local Ruff+goldens3.8168596s.92READ input hashes/original fixtures/old assertions/READ artifact retained;exact scope/pins/refinement/limits in linked acceptance. §§11–16 retain history;this section supersedes their next-unit statuses. CORE-01/02/03/04 DONE,parent IN_PROGRESS,CORE-05 DRAFT;NEXT author CORE-05 durability/save-load/receipt-recovery against actual supported queues. Emotion/persona/BDI/memory remain required later systems;no mandatory per-turn LLM. Self-review only;no agents/install/dependency/policy/CI/commit/push/external write/full-game/performance/independent-person qualification.


## 18. CORE-05 Instruction Successor — 2026-10-05

Director requested the next item after accepted CORE-04. [CORE-05](RS-P1-CORE_05_DURABILITY_SAVE.md) instruction READY;implementation NOT_STARTED. Five new contract/orchestration/SQLite-slot/app modules,two optional Driver/_restore wiring edits,six new test/helper modules,two independent row-vector fixtures and five delivery docs on execution;all old gameplay engines/IO/replay/DTOs/config/fixtures READ. Same Driver prepares once,SQLite changed-row transaction commits CORE/pending/protocol/receipt/compact step/header,then existing sole head publication/presentation. Proven old/new recovery prevents action re-evaluation;unreadable result blocks commands.1024receipts/4096segment rotation,quiescent backup/eight slots/two validated generations/private load/new token,explicit first-save-format1/current-only version rejection/empty migration registry/unsupported accepted packages and file/row limits settled.

[Independent vectors](RS-P1-CORE_05_REFERENCE_VECTORS.json) retain117entry raw hashes,READ CORE-04 requirement inputs,13main/9new commits+passive full canonical rows/sparse differences,ten retention/rotation and ten crash contracts/five version/seven slot cases/exact seven-table DDL. Stdlib reference reproduction/alternate u32 framing/public declaration syntax/callers/fixture hashes PASS. Artifact557856bytes/SHA2565f1c69051d76b55d8d207e70d5ea9fe3aa2a23841dd10202956d01398fd4e988. Baseline1009tests110.88s/Ruff/strict mypy75files PASS;installed Python3.13.12/SQLite3.50.4 real primitive DDL/sparse nine-transition/integrity/rollback/backup/exclusive attachment/two subprocess before-after-COMMIT probes PASS. Application durability/slots/full crash matrix remains NOT_RUN until execution;power-loss/platform/performance/older migration/package/independent-person qualification UNVERIFIED. Current-only compatibility is a deliberate first format,not a fabricated migration implementation.

Authoring changes exactly2NEW order/artifact+3existing delivery docs;114READ hashes retained. §§11–17 remain historical evidence;this section supersedes their next-unit statuses. CORE-01/02/03/04 DONE,parent RS-P1-CORE IN_PROGRESS,NEXT execute CORE-05. After accepted execution,review parent representative-goal completion separately;full-game/NPC cognition/client/Factory/assets/remaining backlog capabilities remain future. Self-review only;no agents/dependency/install/policy/CI/commit/push/external write.


## 19. CORE-05 Execution / Acceptance — 2026-10-05

Executed CORE-05,ACCEPTED/DONE:typed durable checkpoint/commit/recovery contracts,pure sparse projection,seven STRICT SQLite tables,SQL COMMIT before the existing single Driver head publication,native rollback-journal recovery without engine re-evaluation,blocked uncertainty,1024receipts/4096step rotation,eight validated slots/current+previous generations,private load/new attachment token and current-only version/package rejection. [Full acceptance](RS-P1-CORE_05_DURABILITY_SAVE.md#11-core-05-execution--acceptance--2026-10-05). 1111tests in 271.79s (1009previous+102new),new focused102tests148.72s,Ruff PASS,strict mypy86files PASS; six explicit goldens3.68s/local Ruff+goldens4.5598222s. Exact5NEW production/2MODIFY optional runtime wiring/6NEW test-helper/2NEW independent fixtures/5delivery docs. 111of117historical input hashes unchanged;exact six authorized historical differences are BACKLOG/SESSION_HANDOFF/parent/PHASE0_CONTRACTS and Driver/headless. Old1009assertions/six goldens/config/lock/READ reference bytes preserved. Artifact557856bytes/SHA2565f1c69051d76b55d8d207e70d5ea9fe3aa2a23841dd10202956d01398fd4e988. CORE-01/02/03/04/05 DONE,parent RS-P1-CORE IN_PROGRESS;NEXT review representative parent-slice completion against its existing goal. No invented CORE-06/full-game completion. Emotion/persona/BDI/memory/packages/migration transforms/client/performance remain later. Self-review only;no agents/install/dependency/policy/CI/commit/push/external write.

Coverage correction2026-10-06:the registered watch main path traverses movement/gate/NPC events and durable save/load/replay;CORE-05 validated encounter combat separately in a generic selected-bundle path. The main vector contains no attack or blocked movement;§20 adds actual combined coverage.  complete independent publications/rows and queued future wakes survive exit and fresh resume. Actual eight live process-kill boundaries,second-process lock/release,proved uncertainty without re-evaluation,rotation/receipt bounds,strict corrupt-file rejection,staged slot faults and real JSON CLI pass. §§11–18 retain historical readiness/results;this section supersedes their next-unit statuses. Physical power loss,Windows directory fsync/native hardlink qualification,package preservation/migration transformations,release/performance and remaining game systems are not completed by this unit. Parent representative-goal acceptance is intentionally a separate next review.


## 20. Parent Representative Slice Integration Acceptance — 2026-10-06

Reviewed the first representative gameplay slice and closed IR-001 coverage/document overclaim:the old watch main trace had no combat;NEW two real combined tests cover wall/door blocking,gate opening,attacks/counters/exhaustion/rest/defeat,NPC wake/reply,mid-combat save/load before and after fresh resume,old-token/receipt retry,exact continuation and positive/negative compact replay. [Review/independent scenario/results](RS-P1-CORE_INTEGRATION_REVIEW.md). 1113tests in 263.97s (1111previous+2new),final combined2tests6.66s,six original qualified goldens3.15s,Ruff PASS,strict mypy2.4.0 installed Python-source mode87files PASS. NEW one integration test module/two parametrized cases and one review record;MODIFY only BACKLOG/SESSION_HANDOFF/parent. All production/prior tests/config/lock/fixtures/reference/spec bytes unchanged;130of133entry files identical,exact three authorized existing documentation differences. No dependency/install/CI/checker/agent/commit/push/external write. RS-P1-CORE DONE for the first representative headless slice;CORE-01/02/03/04/05 DONE. NEXT author a source-specific staged RS-P1-GOV order against actual dependency/coverage/access evidence;existing packet remains DRAFT,no wholesale eleven-gate installation. Graphical client/full world/NPC cognition/emotion/persona/BDI/memory/packages/migration transforms/performance/release remain later;ARCH-002 IN_PROGRESS/B09 #6/#34 PARTIAL. Self-review only,no independent-person/full-game qualification.

All parent §1 representative criteria PASS in a real joined flow:one local space/single actor,wall/door time-consuming blocked movement,gate opening,HP/stamina/counter/defeat,autonomous delayed wake/Bell response,mid-combat save/load/retry and fresh compact replay. Twelve committed seconds with an extra exhausted rejection follow the independently reasoned literal state table;both live load and close/fresh-resume-before-load converge to exact final CORE/protocol/publications. Old queued cause/ID/order survive and Wake8 fires once;an omitted NPC fact expectation is detected separately from unchanged state hashes. IR-001 CLOSED;no production rule/API/save-format/source edit. Native compiled mypy remains Windows-policy-blocked;strict unchanged installed Python-source checks PASS.

Parent RS-P1-CORE DONE only for this first representative headless slice. §§11–19 retain dated predecessor status/results and are superseded by this review for current NEXT/parent state. Remaining full world/physics/survival/economy/cognition/client/content/performance requirements stay open on the existing roadmap. No new CORE-06,parent ID or entire-Phase1/full-game completion claim.
