# Phase 0 — Frozen Implementation Contracts

Date:2026-10-03 | Author/reviewer:gpt-6.1-sol | Scope:instruction finalization, not implementation.
Read with [orders](IMPLEMENTATION_ROADMAP_ORDERS.md), [preflight](RS-PREFLIGHT-001_COMPATIBILITY.md), B02–05. These refinements settle the toy Phase0 schemas only; they do not select gameplay balance or complete Phase1. All listed source symbols are NEW/PLANNED. Private helper names may vary; public names/fields/semantics below may not.

## 1. Package / Ownership / Errors

Python imports are `domain`, `contracts`, `orchestration`, `engines`, `app` from `src/`; never `src.domain`. Regular empty `__init__.py` in each actual package; no `src/__init__.py`, no import-time registration. Tests use regular `tests` packages; pytest inserts `src` using configuration. No production dependency beyond the standard library in Phase0.

| Module | Sole public responsibility |
|---|---|
| domain/primitives.py | B02 EntityId/CommandId/EventId/Tick/WorldRevision/Phase/TypeKey/FieldFamily/FieldAddress/FrozenPayload; B03 ComponentAddress/FieldSpec aliases |
| domain/state_types.py | Immutable component storage, CoreSnapshot/SimulationPins; no contracts import |
| contracts/errors.py | Exception classes below; no domain state or I/O |
| contracts/read_views.py | B02 ComponentKey/ReadPort; B03 ViewEpoch/path/observation/factory; typed registration ports |
| contracts/turn.py | B02 action/manifest/engine/driver/schedule/result/receipt; B05 NodeActivation; B04 admission/protocol metadata |
| contracts/messages.py | B02 command/fact/presentation ABCs, event/diff/presenter; B03 EmittedFact/EventPolicy declarations |
| contracts/skeleton.py | Toy Step/Stepped/PositionDelta/CounterDelta/StepCue, read Protocols, keys, bundle/registration interfaces |
| domain/canonical.py | pack, canonical JSON and registered canonical document DTOs, SHA256; no contracts import |
| engines/skeleton.py | Stepper/Counter only, imports domain+contracts; no other engine imports |
| orchestration/read_views.py | Typed sealed-root adapters, wrapper caches, observations and expiry |
| orchestration/scheduler.py | Boot-only schedule compilation, declaration validation |
| orchestration/turn.py | Admission, sparse staging, barrier validation, in-memory COMMIT, result collection |
| orchestration/skeleton.py | Concrete toy read adapters/reducers/admission/codecs/presenter; no authoritative state owner |
| app/feature_registry.py | Explicit immutable feature bundles and toy schema pins |
| app/headless.py | Bootstrap and deterministic CLI; wiring only |
| contracts/replay.py | B03 replay/RNG contracts + recorder/fixture below |
| orchestration/rng.py, replay.py | Tested counter RNG and recording/replay; no engine discovery |

`CommandPayload` etc. inherit domain FrozenPayload but live in contracts/messages; domain storage never imports those payloads. Canonical documents use feature-converted immutable values, not engine objects. Generic codec dispatch belongs registered feature adapters, not a central feature union.

Errors in contracts/errors.py:

| Class / base | Raised boundary / result |
|---|---|
| ReadViewError / RuntimeError | Abstract family for proxy lifecycle/access failures |
| ReadOnlyViolation, ExpiredReadView, UnknownComponent, UnknownEntity, InvalidViewEpoch, ViewAlreadyOpen, ViewAlreadyClosed / ReadViewError | B03 exact operations; no backing mutation |
| BootstrapError / ValueError | `.code:str`, `.detail:str`; invalid registry/schedule/rights; boot fails |
| SchemaError / ValueError | `.code:str`, `.path:str`; malformed typed values/JSON; adapter rejects before driver |
| CandidateError / RuntimeError | `.code:str`, `.detail:str`; validation/reducer failure; driver returns TurnAborted |
| RngUnavailable / RuntimeError | Draw attempted before tested RNG installed; technical abort, never fabricated draw |
| ReplayFormatError / ValueError | Invalid fixture/checkpoint/pin/witness before execution |
| RngError / ValueError | Invalid address/purpose/range; candidate contract abort when inside engine |
| RngCounterExhausted / RuntimeError | Counter reaches2^64; deterministic failure |

P0-004 creates seven proxy subclasses + ReadViewError; P0-001 explicitly adds BootstrapError/SchemaError/CandidateError/RngUnavailable; P0-003 explicitly adds remaining three. Preserve causal exception chain in diagnostic, never include repr/address/time in CORE/outcome. Failure message key is `error.` + lowercase code. No player localization catalog in this headless order.

Admission failure codes:INVALID_COMMAND, UNSUPPORTED_SCHEMA, UNKNOWN_ACTOR, UNAUTHORIZED_ACTOR, UNKNOWN_STREAM, STREAM_RETIRED, INVALID_SEQUENCE, STALE_REVISION, COMMAND_ID_CONFLICT, RETRY_WINDOW_EXPIRED. Authenticated semantic failures include current_revision; malformed syntax/unresolved route uses None. Technical codes:ENGINE_EXCEPTION, UNDECLARED_READ, UNDECLARED_WRITE, DUPLICATE_TARGET, INVALID_DELTA, INVALID_FACT, INTEGER_OVERFLOW, CASCADE_LIMIT, RNG_UNAVAILABLE. Bootstrap codes:DUPLICATE_ENGINE, DUPLICATE_SCHEMA, UNKNOWN_NODE, INVALID_ACTIVATION, INVALID_LANE, WRITE_CONFLICT, DEPENDENCY_CYCLE, INVALID_EVENT_POLICY. Presentation failure is diagnostic PRESENTATION_FAILED on a committed result, never TurnAborted.

## 2. Sealed Storage / Typed Views

`ComponentRecord(FrozenPayload, ABC)` in domain/state_types: annotated `entity_id:EntityId` field contract (no abstract property descriptor); concrete frozen dataclass supplies that field and implements the inherited schema property. This avoids an abstract property colliding with a dataclass field at runtime. `StoredRoot(components:tuple[ComponentRecord,...], root_token:int)` is frozen, canonical sorted `(schema.kind,schema.version,entity_id)`, unique addresses. root_token≥0 is DERIVED, never serialized. Admission validates immutable children and registered schema; unknown models/descriptors/callables rejected.

`ReadAdapter[ReadT]` Protocol in contracts/read_views:

```python
class ReadAdapter[ReadT](Protocol):
    @property
    def key(self) -> ComponentKey[ReadT]: ...
    def validate(self, record: ComponentRecord) -> None: ...
    def wrap(self, record: ComponentRecord, access: ViewAccess) -> ReadT: ...

class ViewAccess(Protocol):
    def check(self) -> None: ...
    def observe(self, target: FieldAddress,
                path: tuple[AccessPathSegment, ...], operation: AccessOperation) -> None: ...
    def strings(self, target: FieldAddress, values: tuple[str, ...]) -> Sequence[str]: ...
    def integers(self, target: FieldAddress,
                 values: tuple[tuple[str, int], ...]) -> Mapping[str, int]: ...
```

`AccessOperation` is the existing five Literal operations. Concrete adapters type-check/narrow their exact ComponentRecord class using isinstance and validate schema/entity/ranges; only their declared pure properties execute. No introspection of arbitrary descriptors. Scalar/property wrappers are feature-owned, factory-issued; every property calls check/observe.

Concrete factory constructor `ObservedReadViewFactory(root:StoredRoot)`; `register[ReadT](adapter:ReadAdapter[ReadT])->None` during boot only; `open/close` exactly B03. Registered keys are immutable singleton identities; same schema/key collision fails ValueError at this standalone port. P0-001 bootstrap checks registry collisions and reports BootstrapError(DUPLICATE_SCHEMA) before installing; it does not rewrite the existing factory. Registration freezes at first open. Unknown schema/key raises UnknownComponent; registered missing entity raises UnknownEntity. Root accepts only registered validated record types before first open.

Private registry erasure may use `object` exclusively as an opaque adapter slot; one `cast(ReadAdapter[ReadT], entry)` after **singleton key identity + schema validation** is the checked generic bridge. This is not a public object/Any wrapper and never returns erased storage. No cast of a component to an arbitrary requested read type; no Any/type-ignore whitelist. Constructor exposes no public raw/unwrap handle. Adapter and root are trusted orchestrator inputs, never engine capabilities. Tests must reject a newly constructed key with the same schema and a forged key for another Protocol.

Epoch validity:tick/root_token0..2^63−1, phase in VALIDATE/PRE_TICK/RESOLVE/REACT/CASCADE/POST_TICK/PRESENT, engine_id canonical namespace; non-CASCADE wave0, CASCADE0..7; root_token equals pinned root. One active epoch per factory; closing invalidates all aliases. Independent factories cannot use a different root's token; same numeric token is meaningful only within its factory. No reopening closed epoch; close never-opened/closed/active-other follows B03 errors. Closed observations remain immutable diagnostics; per-factory history bounded to this invocation; new factory per barrier/root, no campaign-long seen set.

Mapping backing is a sorted tuple of unique NFC string/int pairs; sequence backing tuple retains order. Mutation lookup (append/extend/insert/remove/pop/clear/update/setdefault), setattr/setitem/del emits one write before ReadOnlyViolation. For mutator lookup followed by call, lookup already raises. Stale lookup/read/write raises ExpiredReadView without a new successful observation. Missing key emits child read then KeyError. Normal negative index normalizes to n+i; invalid sequence index records read at normalized nonnegative attempted index (negative beyond length records container read), then IndexError. Bool index TypeError, zero-step slice ValueError; slice uses Python bounds, one iteration + selected child reads, returns epoch-bound view. Iterating mapping keys emits child read for each yielded key; membership records child path for mapping key and container path for sequence value query; invalid key type TypeError. Unknown property AttributeError; no raw mutable object escapes. Python list()/tuple() may add explicit length-hint observations; tests use manual iteration where exact minimal sequence matters.

Fixture-only records in tests/unit/view_fixtures.py:ProfileRecord(schema fixture.profile/v1,entity_id,traits tuple),PhysiologyRecord(schema fixture.physiology/v1,entity_id,hp0..2^63−1,reserves sorted pairs nonnegative64); matching B03 Protocols/adapters. Both fixture collections cap64,exact64allowed/65rejected ValueError before opening,emptyallowed; duplicate mapping keys rejected. No shipped physiology adopted. Mandatory example operations `p.hp; p.reserves; r['food']; len(r); 'food' in r` produce exactly read(hp,()),read(reserves,()),read(reserves,(MappingPath('food'),)),length(reserves,()),membership(reserves,(MappingPath('food'),)); values10,7,1,True. Container cache lookup twice has two acquisition reads even if identity reused. Sliced sequence views retain original backing indices in later child observations, including reversed/strided slices; slicing never renumbers evidence paths.

## 3. Toy Schemas / Registration / Headless API

Toy records in domain/state_types:PositionRecord(entity_id,x),CounterRecord(entity_id,visits),schema skeleton.position/1 and skeleton.counter/1. x signed64; visits0..2^63−1; unit step/count,scale1,CORE/A. Profiles above stay test-only. Shared primitives validate namespace IDs `[a-z][a-z0-9_.:-]{0,127}`, type kind `[a-z][a-z0-9_.-]{0,127}`, version1..2^31−1; integer fields reject bool and floats. Tick/revision0..2^63−1. Frozen dataclasses use slots; malformed direct construction is rejected by registered validators before use.

contracts/skeleton owns `POSITION:ComponentKey[PositionRead]`, `COUNTER:ComponentKey[CounterRead]`; properties x/visits only. StepCommand(dx:int),Stepped(from_x:int,to_x:int),PositionDelta(entity_id:EntityId,expected_old:int,new:int),CounterDelta(same fields),StepCue(actor_id:EntityId,from_x:int,to_x:int); schema keys skeleton.step/stepped/position-delta/counter-delta/step-cue version1. Delta.target derives the fixed family and entity. dx exactly−1/0/1; no extra fields/defaults. Stepped emits even dx0; zero delta is validated but omitted from StateDiff net changes. Counter always increases1, overflow aborts. Toy entity fixed actor:toy; other actor cannot execute.

Stepper manifest reads/writes skeleton.position.x at RESOLVE, emits skeleton.stepped/1, constant cost; activation step/1 only,laneA, no dependencies. Counter reads/writes skeleton.counter.visits at POST_TICK,every_tick=True,laneA, no event/action dependency. Same phase dependency orders invocation only. EventPolicy stepped:record_only,PRESENT,priority0,late_route reject,producers stepper,subscribers empty,cancellers empty. No simulation event subscription/pending events in toy; nonempty imported pending queue rejects unsupported toy checkpoint. Generic boot validation still checks B03 policy subscriber/node matching and cascade bound for declared test engines. Future event-bus/save functionality remains Phase1.

`FeatureBundle` frozen in contracts/skeleton (toy composition, not a universal plugin framework):`feature_id:str`, `bindings:tuple[EngineBinding,...]`, `read_adapters:tuple[ReadRegistration,...]`, `field_specs:tuple[FieldSpec,...]`, `events:tuple[EventPolicy,...]`, `command_routes:tuple[CommandRoute,...]`, `delta_routes:tuple[DeltaRoute,...]`, `presenters:tuple[PresenterBinding,...]`, `codecs:tuple[PayloadCodec,...]`, `schema_document:JsonObject`, `rules_document:JsonObject`. JsonObject is Mapping[str,JsonValue] with sealed owned data. CommandRoute/DeltaRoute/PayloadCodec are Protocols with schema:TypeKey property; public route methods immediately isinstance-narrow to the exact feature payload. CommandRoute also has reads:tuple[FieldFamily,...], `admit(command:GameCommand,state:ReadPort,*,start_tick:Tick,world_id:str)->AdmissionOutcome`; DeltaRoute also has owner_id:str, `stage(delta:StateDelta,before:ReadPort,editor:StagingEditor)->None`, `compose(changes:tuple[StateDelta,...])->StateDelta`. PayloadCodec has `decode(data:JsonObject)->FrozenPayload`, `encode(payload:FrozenPayload)->JsonObject`; each registered subclass fixes its payload type via explicit checks. Unknown payload/schema errors explicit. `PresenterBinding(presenter_id:str,kinds:tuple[TypeKey,...],presenter:Presenter)`.

ReadAdapterRegistry Protocol exposes only `register[ReadT](adapter:ReadAdapter[ReadT])->None`; ReadRegistration Protocol exposes schema:TypeKey and `install(registry:ReadAdapterRegistry)->None`. Frozen `AdapterBinding[ReadT](adapter:ReadAdapter[ReadT])` implements ReadRegistration without public erased object fields; FeatureBundle installs these into factory before first open. This keeps generic erasure private to the factory.

B03 ComponentPatch/StagingEditor/DeltaReducer declarations live contracts/read_views (added by P0-001). Toy PositionPatch(x:int),CounterPatch(visits:int) in contracts/skeleton have schema skeleton.position-patch/1,counter-patch/1 and validated ranges. Reducer checks owner/address/old value then passes one patch to trusted per-target editor; it cannot replace arbitrary root. compose accepts nonempty contiguous same-target changes, returns firstold→lastnew, otherwise INVALID_DELTA. Patch schemas participate in schema descriptor. Primitive storage types StoredRoot/ComponentRecord/FieldSpec exist P0-004; toy records,CoreSnapshot/SimulationPins/PackageDocument/PendingDocument are explicit P0-001 additions, no import of nonexistent canonical.py in P0-004.

Registration ports also carry typed schema descriptor canonical document bytes for fingerprints; constructors checked before freezing. `skeleton_bundle(actor_id:EntityId)->FeatureBundle` in app/feature_registry; `feature_bundles(actor_id:EntityId)->tuple[FeatureBundle,...]` returns this one bundle. Empty/missing routes fail boot. DefinitionReadPort is B05 contract; toy `EmptyDefinitions.definition[ReadT](key:ComponentKey[ReadT],entry_id:str)->ReadT` raises explicit KeyError, no fake definition. NoDrawRng implements EngineRng.stream and returns a stream whose draw raises RngUnavailable. No randomness needed in toy; opening a stream does not fake a draw.

Concrete toy adapter classes in orchestration/skeleton:PositionAdapter/CounterAdapter implement ReadAdapter for the singleton keys; StepAdmission implements CommandRoute; PositionReducer/CounterReducer implement DeltaRoute; registered payload codecs implement PayloadCodec; StepPresenter implements Presenter. Constructors for adapters/codecs/reducers/presenter take no service; StepAdmission(actor_id:EntityId) pins control. Methods/fields exactly the above interfaces; no public extra helpers required. Registry composes these and EngineBinding for Stepper()/Counter(actor_id:EntityId); contracts contain DTOs/Protocols, not gameplay pipeline implementations. Private trusted checkpoint factory and owner are in orchestration/turn, injected by app; no orchestration→app dependency.

Headless planned public API:

```python
@dataclass(frozen=True)
class BootstrapSpec:
    seed_hex: str
    branch_id: str
    stream_id: str
    actor_id: EntityId = EntityId("actor:toy")
    initial_x: int = 0
    initial_visits: int = 0
    initial_tick: Tick = Tick(0)
    initial_revision: WorldRevision = WorldRevision(0)

@dataclass(frozen=True)
class TurnPublication:
    outcome: TurnOutcome
    facts: tuple[WorldEvent, ...]
    diff: StateDiff | None
    cues: tuple[PresentationEvent, ...]
    diagnostics: tuple[Failure, ...]

class HeadlessSession(Protocol):
    @property
    def driver(self) -> TurnDriver: ...
    def snapshot(self) -> CoreSnapshot: ...
    def protocol(self) -> ProtocolSnapshot: ...
    def last_publication(self) -> TurnPublication: ...
    def submit_json(self, body: bytes) -> TurnPublication: ...

def bootstrap(spec: BootstrapSpec, *,
              bundles: tuple[FeatureBundle, ...] | None = None,
              rng: RngService | None = None) -> HeadlessSession: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

RngService contract exists in contracts/turn in P0-001 and is re-exported, not redefined, by contracts/replay in P0-003. Bootstrap omitted bundles means feature_bundles; omitted RNG means NoDrawRng until P0-003 changes only that default to CounterRngService. Context carries scoped RNG facade even if zero draws. No global registry/session.

`python -m app.headless` creates seed64zeros/branch32zeros/stream32ones and accepts strict UTF-8 newline JSON commands on stdin; outputs one canonical JSON publication line per input; no banners. Blank lines ignored; EOF exits0; malformed line outputs rejected INVALID_COMMAND, remains usable. Unexpected bootstrap exception exits1 to stderr. CLI does no file/provider/network I/O beyond stdio.

Command internal JSON object has exactly actor_id,command_id,expected_revision,payload,schema; schema={kind:'skeleton.step',version:1},payload={dx:1}. These internal headless/fixture integers are JSON integers; IPC decimal-string adapter is Phase1. command ID B04 syntax branch/stream32lowerhex,sequence1..2^63−1. JSON body≤16KiB,depth≤32; malformed UTF8/duplicate/unknown/missing fields rejected, no normalization of non-NFC input. Check route before actor/duplicate; receipt lookup before stale/high-water. One initial active actor-bound stream; no session authentication in offline headless but spec pins branch/control. P0 tests can inject ProtocolSnapshot retired/high-water/window checkpoints; no registration UI or save service. Successful high-water updated atomically with head, globally1024 receipt eviction by revision thencommandID; failures do not consume IDs. Typed StepCommand with dx2 returns TurnRejected(INVALID_COMMAND,current_revision) while malformed JSON returns current_revisionNone. tick/revision increment overflow aborts before publication.

Driver.submit returns the B02 outcome. Session last_publication is an immutable bounded **last submission** result, reset each attempt; prior facts/cues cannot leak into reject/duplicate. Duplicate returns original receipt, facts(),diffNone,cues(), diagnostic RESYNC_REQUIRED when original receipt.revision<current revision. Reject/abort leave CORE/protocol identical, diagnostic preserves technical cause in noncanonical logging only. Presentation catch after head swap keeps committed outcome/facts/diff, empty cues+PRESENTATION_FAILED. Observations checked against declared reads/writes before each barrier; finally close views on every engine/admission/presenter path. One owner head pairs CORE+protocol; no partial swap between them.

## 4. Canonical Bytes / Pins / Independent Oracle

`JsonValue` recursive alias:None|bool|int|str|tuple[JsonValue,...]|Mapping[str,JsonValue]. Mapping is allowed only as typed immutable canonical DTO, never mutable engine payload; sealing recursively validates/owns it. `canonical_json(value:JsonValue)->bytes`:UTF-8,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False; reject float,duplicate keys at parsing,bad Unicode/non-NFC text/nonstring key/unknown field. `pack(tokens:tuple[str,...])->bytes`:B03 u32 BE byte lengths. `tagged_hash(tag:str,document:bytes)->str`:SHA256(pack((tag,strict_UTF8(document)))). DTO encoding feature-owned; no dataclasses.asdict/repr dispatch.

Domain CoreSnapshot frozen:world_id:str,world_seed_hex:str,tick:Tick,components:tuple[ComponentRecord,...],pending:tuple[PendingDocument,...],pins:SimulationPins. PendingDocument(canonical_event_json:bytes) owns immutable canonical event representation from registered encoder, not contracts import; Phase0 requires pendingempty and never instantiates it. SimulationPins frozen:schema_fingerprint,rules_fingerprint,schedule_fingerprint,rng_version,hash_version,gameplay_catalog_hash:str;gameplay_packages:tuple[PackageDocument,...]. PackageDocument fields package_id:str,version:int,sha256:str; build pins excluded CORE. state_types imports primitives only; canonical may import state_types, never reverse. Generic pending routing/codec indexing awaits Phase1.

Exact documents are supplied by [independent vectors](PHASE0_REFERENCE_VECTORS.json); schema descriptors/rules/schedule are literal source documents in that artifact, copied unchanged into registry, hashes derived. No hand-picked fake fingerprint. schema hash tagged schema/v1; rules rules/v1; schedule schedule/v1; gameplay catalog gameplay-catalog/v1 over empty[]; RNG sha256-counter-v1;hash sha256-core-tree-v1. WorldID B03 seed/rules/catalog. Pending empty toy; reject nonempty instead of accepting an unimplemented codec. Every integer remains canonical JSON integer internally.

Component document:{schema:{kind,version},entity_id,fields:{x or visits}}. Sort by(kind,version,entity_id). Leaf hash tagged component/v1. CORE witness document:{world_id,world_seed_hex,tick,components:[full component documents],pending:[],pins:{all SimulationPins fields}}. Root hash document has identical top-level identity/tick/pins but components:[{schema,entity_id,hash}],pending:[]; root tagged core-root/v1. Witness serializer reconstructs leaf hashes before validating root. Semantic CORE consists of all full component fields; DERIVED root token/cache/receipt/session/revision excluded.

Protocol document:{branch_id,revision,streams:[{stream_id,actor_id,highest_committed_sequence,status}],receipts:[{command_fingerprint,command,receipt}]}; sorted streams IDs,receipts(revision,command.command_id). Fingerprint tagged command/v1 over document exactly actor_id,expected_revision,payload,schema; command_id is the retained record lookup key. B04 full canonical command retry checks retained command_id key +fingerprint +full command equality. Protocol hash tagged protocol/v1. Receipt exact B02 fields. Protocol imports converted to domain JSON document before hashing; domain does not import contracts.

Payload hash for semantic action is tagged payload/v1 over {schema,payload}, excludes actor/protocol; B03 action key adds actor/targettick/worldID. Event full JSON:{header:{event_id,type_key:{kind,version},producer_id,occurred_at,phase:uppercase,wave,producer_rank,sequence,caused_by:[],degraded:[]},due_tick,payload:{from_x,to_x}}. Stepped tick=executiontarget,RESOLVE,wave0,rank0,sequence0. Counter is rank1 in A schedule but emits nothing. Event ID B03 e1+event-id/v1 pack. Presenter ID skeleton.presenter; cue ID p1-+SHA256(pack(('cue-id/v1',source_event_id,presenter_id,'0'))); header PRESENT/producer presenter/rank0/sequence0/caused_by=[sourceID],type skeleton.step-cue/1, otherwise matchingtick/wave. priority important/coalesce keep_all/keyempty. No event ID reuse for cue.

Diff JSON:{receipt,changes:[{schema:{kind:'skeleton.counter-delta' or 'skeleton.position-delta',version:1},entity_id,expected_old,new}]} sorted target(component,field,entity); unchanged netdelta omitted. Facts tagged turn-facts/v1 over ordered full events; diff tagged turn-diff/v1 over object or null. Outcome JSON:{kind:'committed',receipt} OR {kind:'rejected',failure:{code,message_key},current_revision} OR {kind:'aborted',failure:{code,message_key}}. Cues/diagnostics not in replay hashes.

Frozen vectors contain exact UTF8 documents, pack hex,leaf/root/protocol/fact/diff/command hashes,eventID and three command publications+duplicate/rejected witnesses,plus a fully self-consistent wrong-step1 negative fixture with exact expected path/values. Oracle derived from these rules by an isolated standard-library reference calculation **before any production source exists**; checked hash framing independently, plus SHA256 standard known digest. It is not implementation-run expected output. Runtime tests must compare literals, never regenerate expected from runtime canonical functions. Empty pack/('ab','c') versus('a','bc') explicitly differ; UTF8 non-ASCII length is bytes. Source independent means independently authored expectations; this Sol-authored artifact is not independent-person review.

## 5. Replay / RNG APIs and Acceptance

B03 ReplayHeader/Step/Trace/Witness/Mismatch exact fields remain. contracts/replay adds:

```python
@dataclass(frozen=True)
class ReplayFixture:
    initial_core: CoreSnapshot
    initial_protocol: ProtocolSnapshot
    trace: ReplayTrace

class ReplayRecorder(Protocol):
    def record(self, command: GameCommand, publication: TurnPublication,
               core: CoreSnapshot, protocol: ProtocolSnapshot) -> ReplayStep: ...
    def finish(self) -> ReplayTrace: ...

class ReplaySession(Protocol):
    @property
    def driver(self) -> TurnDriver: ...
    def snapshot(self) -> CoreSnapshot: ...
    def protocol(self) -> ProtocolSnapshot: ...
    def last_publication(self) -> TurnPublication: ...

class ReplaySessionFactory(Protocol):
    def restore(self, core: CoreSnapshot,
                protocol: ProtocolSnapshot) -> ReplaySession: ...

def decode_fixture(body: bytes) -> ReplayFixture: ...
def encode_fixture(fixture: ReplayFixture) -> bytes: ...
```

Execution refinement (2026-10-03):the frozen DTOs/Protocols live in `contracts/replay.py`; concrete `decode_fixture`/`encode_fixture` and `validate_checkpoint(core:CoreSnapshot,protocol:ProtocolSnapshot)->None` live in `orchestration/replay.py`. Importing orchestration from contracts to implement those functions would reverse the declared dependency, so contracts contain no executable codec stubs or lazy reverse imports. Fixture decoding validates exact structure, supported toy schemas/algorithms, world identity, internal pins/hash/receipt/witness consistency; the injected app checkpoint factory additionally compares schema/rules/schedule against the registered source before the first command. Phase0 supports actor:toy only, as pinned in the literal rules; arbitrary component/pending/package checkpoints await Phase1. RNG `scoped` keyword remains `tick`, reusing contracts/turn.RngService.

Concrete `Recorder(header:ReplayHeader)` rejects pins/hash mismatch; captures postsubmission full witnesses and exact emitted facts/netdiff/outcome including rejects/aborts/duplicates; bounded4096steps raises ReplayFormatError on step4097 rather than truncate. `Runner(initial_core:CoreSnapshot,initial_protocol:ProtocolSnapshot,*,factory:ReplaySessionFactory)` implements run(trace); reinstantiates fresh owner/services on **every** run, validates initial hashes/pins/packages before first command. Factory loading arbitrary fixture object is never engine input. App headless `replay_runner(fixture:ReplayFixture)->ReplayRunner` wires Runner with a trusted factory using the same private bootstrap/owner initialization as normal play. Orchestration never imports app or independently chooses feature bundles. Checkpointrestore wiring is required privately in P0-001 for acceptance; P0-003 adds this adapter port/entry, not a second simulation path or public load/save feature.

Fixture object keys exactly format_version:1,initial_core,initial_protocol,trace:{header,steps}; each step command,outcome,core_hash,protocol_hash,facts_hash,diff_hash,witness:{core,protocol,facts,diff}. Witness values full typed JSON documents, not base64/digests; convert to four canonical UTF8 byte fields. Header fields exactly B03; package/build arrays empty; unsupported format/pins/schema/hash/inconsistent receipt/corrupt witness raises ReplayFormatError, no partial execution. Golden runtime fixture NEW tests/replay/fixtures/skeleton_v1.json copies vetted artifact's golden_fixture, not recorder output. Recorder-generated trace is useful roundtrip evidence only, never new golden oracle.

Mismatch walks normalized JSON:object keys sorted,array semanticorder; missing item explicit `<missing>`,values rendered canonicalJSON; report first mismatch per CORE/protocol/facts/diff/outcome, step_index0based. Paths `$core.components[...].fields.x`, `$facts[0]...`, `$protocol...`, `$diff...`, `$outcome...`; report witness leaf before hash-only mismatch when available. If expected witness internally inconsistent, decode fails; a precise-leaf test uses an independently authored **self-consistent** alternate step1 expectation x2 with its matchingCOREhash/receipt/protocol/diff/fact payloads and every corresponding digest updated, then asserts first CORE mismatch fields.x versus actualx1. It need not assert the intentionally wrong gameplay expectation passes. Use this as a one-step trace; unchanged later receipts cannot be attached. Without witness report digestpath only. Return all divergent steps in execution order; actualdriver follows actual current head regardless expected outcomes.

Concrete CounterRngService(seed_hex:str,world_id:str,purposes:tuple[tuple[str,tuple[str,...]],...]); scoped B03, new facade per invocation. Purpose allowlist supplied by app.feature_registry `rng_purposes()->tuple[tuple[str,tuple[str,...]],...]`, declared with rules_document in P0-001 and consumed in P0-003; fixture purposes toy.sample/test.reject for skeleton.stepper; no toy production draw. Table is already in the pinned literal rules, so P0-003 does not silently alter rules/goldens. Validate addressints/ranges/current phase+engine+entity/purpose/causalnamespace; action causalkey a1-,event e1-, autonomous `auto:<namespace>`; wave bounds §2. scoped accepts only PRE_TICK/RESOLVE/REACT/CASCADE/POST_TICK, never VALIDATE/PRESENT; duplicate engine/purpose registration invalid. Same address returns same cursor within facade; fresh facade restarts. Counter consumed even rejected u; exhaustion fails before u64 encoding.

Artifact RNG vectors include key bytes/digest,counter0..3 u/draws, interval[7,8),negative-low range,forced-rejection span2^63+1 and total consumed counters. Constructor low/high may be any Python integer but span1..2^64; bool excluded. Engine schema must bound returned domainvalues separately. A white-box cursor seeded at2^64−1 proves last draw/exhaustion; do not expose counter mutation to engines.

Required checks (EXECUTED/PASS 2026-10-03):full proxy mutation/order/lifetime tests; boot writer/cycle/registryorder; real two-engine path ±1/0; malformed/stale/missing/duplicate/conflict/evicted/retired; same-phase visibility with purpose-built engines; abort after Stepper beforeCounter leaves oldhead; finallyexpiry; postcommit presentererror; full literal canonical/RNG vectors; golden test_core_trace; delete Stepped corruption caught independently from x/visits; repeat/reversed-world/cachewarmcold; fresh childprocess PYTHONHASHSEED0,1,and externally generated/logged integer. Randomized seed never enters domain and command order inside a trace unchanged. No mocks of domain outcomes; faulty test engines implement the real Engine contract. No import-linter/coverage/cost/mutation/migration/custom checker added in Phase0. [Actual acceptance](PHASE0_WORK_ORDERS.md#phase0-execution--acceptance-2026-10-03).

Implementation refinement (step3):CommandRoute.admit receives explicit keyword-only start_tick/world_id. ReadPort has no clock/world identity, so returning AdmittedCommand without these inputs would fabricate a plan/semantic key. Inputs are pinned committed metadata, pure/no mutation; frozen gameplay/canonical vectors unchanged. No governance change.


## CORE-01 Source API Supersession — 2026-10-04

Historical Phase0 declarations/evidence above remain unchanged; in-process source APIs now follow [CORE-01 §5/§11](RS-P1-CORE_VERTICAL_SLICE.md#5-new--modified-public-contracts). Save/replay format_version1, pins and canonical golden bytes remain unchanged.

NEW contracts/state_io.py:ComponentCodec,PatchRoute,CheckpointPolicy,StateIO. FeatureBundle appends required component_codecs/patch_routes/checkpoint_policy; DeltaRoute appends is_identity/validate_net. Generic serialization has one owner, orchestration.serialization.RegisteredStateIO; toy codecs/policy/routes stay explicitly registered in app.feature_registry. Old skeleton command/core/protocol/publication helper imports are superseded by io.encode_command/encode_core/hash_core/encode_protocol/encode_publication; no implicit toy fallback remains.

Driver preserves its original parameters and definitions default, adds required keyword-only io:StateIO. Concrete replay decode_fixture/encode_fixture/validate_checkpoint and Recorder take required keyword-only io; Runner takes factory and io explicitly. Contracts/replay DTO/Protocol fields remain unchanged. App adds state_io(bundles), restore_checkpoint(core,protocol,*,bundles,rng=None); replay_runner(fixture,*,bundles=None) defaults to the original toy registry and requires explicit bundles for foreign schemas. BootstrapSpec/HeadlessSession/CLI contracts are unchanged.

CORE-01 supports one bundle with its registered component schemas/entities and explicit checkpoint policy; pending/packages/build artifacts remain unsupported. Required source pins are checked before execution, every candidate is validated before COMMIT, net validators use finally-expired candidate-root PRESENT views, and presentation-codec failure preserves committed effects. Final original37+new22tests PASS,Ruff PASS,strict mypy41files PASS; exact evidence and bounded limitations in the linked order.


## CORE-02 Registered Feature — 2026-10-04

[CORE-02 acceptance](RS-P1-CORE_02_GRID_MOVEMENT.md#9-core-02-execution--acceptance--2026-10-04) adds trial-only domain/contracts/engine/orchestration/registry/app modules. No Phase0/CORE-01 shared API, format, schema, golden or default toy behavior changed. New TrialBootstrapSpec/bootstrap_trial and python -m app.trial select the fixed map/position bundle; one StateIO is shared with existing private app.headless._restore. Public restore_checkpoint/replay_runner with explicit bundles=(trial_bundle(),) and io-injected Recorder/fixture codecs reuse existing owners. Trial state/schema/rules/schedule pins differ explicitly; passing the trial fixture to the default toy registry is rejected.143tests/Ruff/strict mypy51files PASS; exact six payloads, map/position views, ownership, one-second blocked commits and source pin/independent evidence in the linked order. CORE-03 interaction/combat, CORE-04 pending/NPC and CORE-05 durable save remain DRAFT/unimplemented. Historical predecessor evidence above is retained.


## CORE-03 Registered Feature — 2026-10-04

[CORE-03 acceptance](RS-P1-CORE_03_INTERACTION_COMBAT.md#9-core-03-execution--acceptance--2026-10-04) adds encounter-only domain/contracts/engines/orchestration/registry/app modules. EncounterBootstrapSpec/bootstrap_encounter/python -m app.encounter build exactly seven ordered records under one explicit encounter_bundle()/StateIO and reuse existing app.headless._restore/Driver. Public restore_checkpoint/replay_runner select bundles=(encounter_bundle(),);Recorder/fixture codecs receive the same explicit IO. No shared API/format/default toy/original trial schema,codec,owner or golden behavior changed. Reused immutable trial map/position/CellPatchRoute retain trial.movement owner;new qualified movement facts and HP/stamina/gate sole writers cover doors/attack/counter/rest/derived defeat and exhaustion. New pins explicitly distinguish the selection;no hot reload/migration/aggregation. Both independent main/death fixtures match29complete steps/publications,431tests/Ruff/strict mypy61files PASS. CORE-01/02/03 DONE;parent IN_PROGRESS;NEXT author CORE-04 delayed/passive/NPC order,CORE-04–05 DRAFT. Historical predecessor prospective statements above are superseded for CORE-03 only;pending/packages/durability/client/full-game systems remain unimplemented. Exact23payload/11field metadata,strict admission/no-op/retry/atomicity/guard/failure evidence and new public contract in the linked order. Self-review only;performance/bundle/device/independent-person qualification UNVERIFIED.


## CORE-04 Time / Event API Supersession — 2026-10-05

[CORE-04 acceptance](RS-P1-CORE_04_EVENTS_NPC.md#10-core-04-execution--acceptance--2026-10-05) extends exactly contracts/state_io.py,orchestration/serialization.py and orchestration/turn.py with registered generic time/event support. NEW contracts/events.py provides frozen ExecutionLimits(enable_simulation,max_duration_seconds,cascade_waves,max_events_per_tick,max_pending),QueuedEvent(event,delivery_phase,priority),DeliveryBatch(logical_tick,phase,wave,events). StateIO appends execution_limits and encode_pending/decode_pending;no changes to EngineInvocation/EngineResult/TurnPlan/StateDiff/replay/FeatureBundle fields/signatures. NEW orchestration/events.py owns only transaction-local CandidateEventBus routing/coverage/causes/budgets;the existing Driver retains sole authoritative CORE+protocol publication.

Absent rules.execution keeps legacy one-tick/root record-only/empty-pending semantics and all old canonical fixtures/pins. Explicit enabled rules/configured policies and schema.system reserve clock/queue to system.clock/system.events;source registration cannot drift under unchanged policy pins. Enabled bounds are1..16canonical seconds,1..8CASCADE waves,1..512new events per second,1..4096queued items;prototype16/8/512/4096. All new emitted envelopes,including future simulation,are publication/replay facts;delivered old inputs are not republished. Enabled execution uses dense seconds,final-tick matching action,immutable per-barrier inbox+component root,sorted subscribers/batched deltas,complete coverage before candidate queue removal and one outer head/revision/receipt. Queue cap excludes the frozen batch being fully consumed during replacement accounting;failed coverage/patch/final validation discards the candidate.

PendingDocument still holds canonical_event_json:bytes;core JSON pending items are exact {event:{header,due_tick,payload},delivery_phase,priority} bodies. Future-only checkpoints strictly validate source metadata/IDs/policies/timing/unique ordered causes/events and canonical bytes. sha256-core-tree-v1 now includes pending leaves {event_id,hash:hash_document("pending-event/v1",body)} in documented order;old empty pending leaves remain[] and all old root bytes/hashes stay identical. IO bounds/order effects by logical tick/phase/wave/producer/sequence,actual bus emission validates delivered/previously emitted causes;static witnesses need no infinite delivered ledger. Clock/queue are not ordinary engine deltas;StateDiff remains component net changes,while complete CORE witnesses retain pending/tick.

NEW watch feature modules register3components/17payloads/5engines on qualified encounter/trial ports,one watch.local bundle,ten ordered records/40payloads/16fields/7nodes/12policies and a trusted genesis Wake. WatchBootstrapSpec/bootstrap_watch/python -m app.watch own the initial head;explicit bundles=(watch_bundle(),) selects restore/replay/Recorder. New NPC cues retain historical pulse tick in payload.logical_tick while envelope occurred_at remains final receipt.tick. Original default/toy/trial/encounter selections/CLIs/replay source/fixture format_version1 remain unchanged.1009tests/Ruff/strict mypy75files and all6qualified replay goldens PASS. CORE-01/02/03/04 DONE,parent IN_PROGRESS;NEXT author CORE-05 durability/save-load/receipt recovery,CORE-05 DRAFT. Historical prospective/unsupported-pending statements above are superseded for the explicitly enabled selection only. Emotion/BDI/memory/cancellation/roaming/durable save/client/full-game/performance/independent-person qualification remain later.


## CORE-05 Durable API Supersession — 2026-10-05

[CORE-05 acceptance](RS-P1-CORE_05_DURABILITY_SAVE.md#11-core-05-execution--acceptance--2026-10-05) adds contracts/persistence frozen DurableCheckpoint,DurableTurn,RecoveryCommitted/RecoveryAbsent,SaveSegment,SaveExportReceipt,SaveLoadReceipt;typed DurableCommitPort.persist/recover and SaveError/SaveUnavailable/CommitUncertain/WorldUnavailable. Driver retains every prior constructor parameter/default and appends optional keyword-only commit_port:DurableCommitPort|None=None;private app.headless._restore forwards the same optional port. Driver.recover_pending() resolves a retained prepared turn without simulation;detach() permanently blocks submission/recovery while immutable historical snapshots remain readable. No persistence selected preserves the memory-only path.

NEW orchestration/persistence owns checkpoint_document/decode_checkpoint,prepare_turn/decode_segment using explicitly selected StateIO and existing canonical/replay DTOs. NEW adapters/sqlite_store owns first save format1/exact seven STRICT tables/sparse SQL COMMIT/receipt recovery/lifetime sidecar/backup;adapters/save_slots owns slot01..slot08/current+previous/private clone staging. NEW app/durable owns create_durable/resume_durable explicit bundles,attachment-token-gated submit/submit_json,export/load/recover/retained_segment/close and python -m app.durable --working PATH [--create]. Successful load atomically swaps the private working store/Driver/token;the old Driver detaches.

Durable SQL COMMIT precedes the existing sole _Head publication and presentation. Proved absence gives SAVE_UNAVAILABLE/empty effects;unresolved results block commands/queries/export/load with SAVE_UNCERTAIN until recover/close;postcommit presentation failures retain committed effects. Startup loads fully validated current CORE+protocol+causal queue without replaying engines.1024receipt retention,4096step checkpoint rotation,compact optional Runner replay and exact version/rules/package rejection preserve old formats/pins/goldens. Current-only save support/empty migration chain/unsupported accepted package blobs are explicit limits. Windows directory_synced=False;physical power loss/native hardlink/platform/performance qualification remains UNVERIFIED.

Final1111tests (271.79s;1009prior+102new),Ruff PASS,strict mypy86files PASS,six original qualified goldens PASS. Original default toy/trial/encounter/watch behavior/public formats and prior assertions remain unchanged. This section supersedes earlier durability-unimplemented statements;all previous Phase0/CORE-01–04 evidence is historical. CORE-01/02/03/04/05 DONE;parent IN_PROGRESS pending separate representative-slice review,not full-game completion.
