# RS-P1-CORE / CORE-04 — Canonical Time, Delayed Events & Autonomous Watcher

Date:2026-10-05 (Asia/Seoul) | Owner/executor/reviewer:Sol | Instruction:READY | Implementation:DONE/ACCEPTED
Director requested the next item after CORE-03 acceptance,then authorized execution with "다음거 ㄱ". §§1–9 retain the READY instruction/authoring evidence;§10 records current implementation acceptance and supersedes their historical NOT_STARTED/NOT_RUN/next-unit statements. Parent RS-P1-CORE remains IN_PROGRESS;CORE-05 DRAFT. Self-review is not independent-person review.

Inputs:[CORE-03 acceptance](RS-P1-CORE_03_INTERACTION_COMBAT.md#9-core-03-execution--acceptance--2026-10-04),[parent](RS-P1-CORE_VERTICAL_SLICE.md),[coding template](../prompts/SOL_CODING_WORK_ORDER.md),[MASTER](../MASTER_GAME_ARCHITECTURE.md) §§1–3/8–9/13,[B02](../../architecture/BLOCK_02.md) A1–A3,[B03](../../architecture/BLOCK_03.md) A4–A6,[B04](../../architecture/BLOCK_04.md) A7,[B05](../../architecture/BLOCK_05.md) A11. Literal descriptors/source/traces:[CORE-04 independent vectors](RS-P1-CORE_04_REFERENCE_VECTORS.json).

## 1. Actual Source / Decisions

HEAD efd2478ff8a6ed93ee833c3f8464a0efdd8a181a/main unchanged; primary prompt/MASTER contain preexisting tracked user edits; most source/tests/docs untracked. Preserve all. Root AGENTS absent; historical AGENTS is reference. Remote freshness unchecked. Entry:431tests in38.08s/Ruff/strict mypy61files PASS. Existing Python3.13.12/Ruff0.16.6/mypy2.4.0/pytest9.1.1/13hashlocked packages; no new dependency/install/other-OS compatibility claim. Existing launcher location diagnostic remains stderr; successful exits retained. Artifact records99raw existing inputs before authoring.

Observed gaps and bounded resolutions:
- Driver checks target==start+1, evaluates one phase program, supplies incoming=(), and supports only root record-only/due-now emissions. It already has one authoritative CORE+protocol publication and observed field/patch/net barriers. Extend that owner; no second NPC loop/driver.
- EngineInvocation.incoming, EventPolicy, NodeActivation.on_matching_events and CoreSnapshot.pending already exist. Add typed candidate routing over those ports; runtime must actually honor matching activation, due phases/waves, subscribers and causes.
- PendingDocument already owns canonical_event_json:bytes. Keep it and format_version1; add strict generic queue encode/decode, source policy checks and complete pending leaf hashing. Current hash_core_document only implements component leaves; empty queues previously made the missing pending leaves invisible. Complete pending-event/v1 leaves under the documented sha256-core-tree-v1 algorithm; all old empty-queue root bytes/hashes remain identical.
- Existing generic effects validation assumes one tick/wave0/empty causes and rank-only fact order. Extend it by logical tick/phase/wave/producer/sequence without adding watch/encounter dispatch. Replay/Recorder already use injected IO and full witnesses; their source API/format/callers stay unchanged.
- Original encounter policy rejects pending and exactly requires seven records. A new explicit watch selection registers the original qualified encounter ports plus three new components; its policy validates the original seven-record subprojection and its own queue/state. Never pass two bundles or broaden the original encounter selection.
- No NPC writes HP/stamina/gate/player position here. Existing action admission remains valid after intervening passive ticks, since autonomous owners write only their new fields. General interrupted combat/fizzle, NPC movement/collision/combat, cancellation and broad cognition require later orders.
- Use separate watch.lantern/watch.npc/watch.reply component scalars. A single writer owns each family; no unsupported same-phase same-component field merge. Subscriber engines process full sorted batches once per barrier, returning at most one net scalar delta for a repeated target.
- Reserve CORE clock/queue to system.clock/system.events, declared in the new schema.system descriptor. Engines return typed event drafts, never clock/queue deltas or direct engine calls. Queue and clock changes are part of the same candidate head/hash. StateDiff remains component net changes plus receipt; its role does not expand into a complete private CORE replacement. Full replay witnesses include clock/pending independently, as before.

Product scope:one station NPC rings a signal every2game seconds, independently of player intent; player can ring a shared bell and receive a deterministic event response. This supplies scheduling/causality for later emotion/stress/attitude/traits/BDI/memory/anchors, all still required by MASTER. It implements none of those cognition values/formulas and makes no per-turn LLM/provider call. The numeric station, period, charge and echo values below are new prototype rules, not v1 mechanics or final balance.

## 2. Complete Work Order

| Required field | Concrete contract |
|---|---|
| task_id/title | RS-P1-CORE/CORE-04:extend canonical tick/event execution and integrate a bounded autonomous watcher |
| status/executor/review | READY;Sol implementation/diagnosis/integration/self-review;independent-person UNVERIFIED |
| goal/non_goals | Actual delayed queue→PRE_TICK NPC→REACT→CASCADE response;exact1..16second waits/passive updates/one outer commit/replay. Excludes emotion/persona/BDI/memory,roaming/HP retaliation,NPC dialogue generation,cancellation,interruptible actions,LOD/idle skip,long jobs,save DB/migration,client/Factory/governance |
| baseline/prerequisites | CORE-01/02/03 DONE;431tests/Ruff/strict mypy61files PASS;refresh HEAD/status/99raw artifact inputs at implementation entry |
| read_files | This order/vector,parent,template and listed architecture;actual domain/{primitives,canonical,state_types,encounter,trial};contracts/{messages,turn,read_views,state_io,skeleton,encounter};orchestration/{turn,serialization,scheduler,read_views,replay,rng,encounter,trial};app/{headless,encounter_registry,encounter};all current tests/config/lock/oracles READ |
| allowed/forbidden paths | Exact §3;only the three shared production files named there may change. All old tests/feature modules/fixtures/config/reference/architecture/policy/CI/dependencies READ |
| public_contract | §4–6:NEW execution/queue DTOs,candidate bus,IO queue methods/limits,17watch payloads/3components/5engines,watch bootstrap/CLI;unchanged EngineInvocation/EngineResult/TurnPlan/StateDiff/replay signatures |
| behavior/algorithm | §5–6:dense canonical second ticks;final-tick action;phase/wave barriers;staged queue removal after full delivery;one commit;exact watcher recurrence/passive charge/echo response |
| edge_policy/examples | §5–7:due/late/phase/order/causes/duplicates/bounds/pins/batch/noop/reject/retry/abort/overflow/presentation;13main+1passive full steps,480composition cases,8cascade depths |
| wiring | watch_bundle→watch bootstrap/selected IO→same Driver→CandidateEventBus→registered watch engines/ports/presenter→explicit restore/Recorder/Runner;app.headless source unchanged |
| performance | Prototype1..16seconds,max512new events/tick,4096pending,8CASCADE waves;max8192publication facts. Fixed10records/7nodes,scoped NPC handler,no world scan. Brain512MiB/p95≤100ms/p99≤250ms/local Ruff+goldens≤20s TARGET;measure only local feedback,device/latency/memory UNVERIFIED |
| baseline/verification | §8;actual commands,full431old unchanged,focused new tests,all old/new goldens and CLI;no custom checker/benchmark framework |
| test responsibilities/acceptance | §7–8:live delivery+multitick+full queued witness/causal identity+all splits+limits/ownership/atomic fault/strict codecs+unchanged old outputs |
| stop conditions | Unexplained entry drift/failure,need for an unlisted shared change/schema default migration/second driver,overlapping user edit,independent byte/pin disagreement. Diagnose in-scope first;unresolved issue requires a focused refreshed order |
| delivery | Exact paths/results/source pins/live callers/scope hashes/self-review;CORE-04 DONE only after implementation acceptance,parent IN_PROGRESS;then author CORE-05 against actual supported pending state. No commit/push/external write |

## 3. Exact Scope

AUTHORING snapshot (before this execution):NEW this order and vector artifact;MODIFY BACKLOG.md,SESSION_HANDOFF.md,parent RS-P1-CORE_VERTICAL_SLICE.md only. Runtime/tests/PHASE0_CONTRACTS/config/oracles/specs remain READ. A subsequent execution request activates only the implementation scope below.

NEW production (absent at authoring;implemented in §10):
```text
C:\Reverie Saga\src\contracts\events.py
C:\Reverie Saga\src\orchestration\events.py
C:\Reverie Saga\src\domain\watch.py
C:\Reverie Saga\src\contracts\watch.py
C:\Reverie Saga\src\engines\watch.py
C:\Reverie Saga\src\orchestration\watch.py
C:\Reverie Saga\src\app\watch_registry.py
C:\Reverie Saga\src\app\watch.py
```
MODIFY production, existing:
```text
C:\Reverie Saga\src\contracts\state_io.py
C:\Reverie Saga\src\orchestration\serialization.py
C:\Reverie Saga\src\orchestration\turn.py
```
NEW tests/helper/fixtures (absent at authoring;implemented in §10):
```text
C:\Reverie Saga\tests\unit\watch_fixtures.py
C:\Reverie Saga\tests\unit\test_watch.py
C:\Reverie Saga\tests\unit\test_events.py
C:\Reverie Saga\tests\integration\test_watch.py
C:\Reverie Saga\tests\integration\test_event_turn.py
C:\Reverie Saga\tests\replay\test_watch.py
C:\Reverie Saga\tests\replay\fixtures\watch_v1.json
C:\Reverie Saga\tests\replay\fixtures\watch_passive_v1.json
```
MODIFY delivery docs on execution:this order,RS-P1-CORE_VERTICAL_SLICE.md,PHASE0_CONTRACTS.md,BACKLOG.md,SESSION_HANDOFF.md. Reference artifact stays READ. All other existing runtime/tests/init/config/lock/fixtures/oracles/architecture/specs/reference/policy/CI/tools READ;no dependency/new package/private second head. Inspect untracked files,not only git diff.

## 4. Generic Source Contracts

### 4.1 NEW contracts/events.py / StateIO additions

All DTOs frozen/slotted. Retain existing WorldEvent/EmittedFact/PendingDocument;no central payload union. New exact declarations:
```python
@dataclass(frozen=True, slots=True)
class ExecutionLimits:
    enable_simulation: bool
    max_duration_seconds: int
    cascade_waves: int
    max_events_per_tick: int
    max_pending: int

@dataclass(frozen=True, slots=True)
class QueuedEvent:
    event: WorldEvent
    delivery_phase: Phase
    priority: int

@dataclass(frozen=True, slots=True)
class DeliveryBatch:
    logical_tick: Tick
    phase: Phase
    wave: int
    events: tuple[WorldEvent, ...]
```
Append to contracts/state_io.StateIO only:
```python
@property
def execution_limits(self) -> ExecutionLimits: ...
def encode_pending(self, event: QueuedEvent) -> PendingDocument: ...
def decode_pending(self, document: PendingDocument) -> QueuedEvent: ...
```
No FeatureBundle field/signature change. RegisteredStateIO reads optional rules_document.execution. Absent→legacy ExecutionLimits(False,1,8,512,0),no simulation/nonempty pending,old effects semantics. Present→exact closed five keys above;bool exact;integers exact;this unit supports True,1≤duration≤16,1≤waves≤8,1≤events≤512,1≤pending≤4096. Prototype pins use True/16/8/512/4096. Wrong shape/value→BootstrapError INVALID_EVENT_POLICY. Require matching schema.system={clock_owner:system.clock,queue_owner:system.events,pending_format:queued-event/v1} and exact rules.event_policies canonical array matching all registered EventPolicy values (sort schema.kind/version and ID lists). This prevents hidden limit/policy drift under unchanged pins. Old rules/descriptors need no additions.

Strengthen enabled boot validation:exact allowed phases/priority0..255,unique nonempty authorized producers,runnable lane-A subscriber nodes with matching consumes/on_matching_events;every declared consume has a matching subscribed policy;producer emits/phase rights match;record_only/PRESENT presenter ownership;no engine clock/queue writes. Every_tick CASCADE is unsupported (empty cascade invokes nobody);enabled boot rejects it INVALID_ACTIVATION. Nonempty cancellers unsupported here→INVALID_EVENT_POLICY;no fake cancel success. Generic modules may not import watch/encounter or infer action duration from a concrete command class.

### 4.2 Pending representation / hash / strict IO

Canonical queue body exactly `{event:{header,due_tick,payload},delivery_phase,priority}`;header is the existing complete EventHeader JSON. PendingDocument.canonical_event_json is the canonical UTF8 encoding of this body,not an arbitrary blob/default. Core JSON pending is an array of these bodies,never bytes/base64. encode/decode use registered payload codecs and a FactPayload;schema/version/header.type_key equal payload.schema. Unknown fields/duplicate JSON keys/bool integer/float/NFC/unsupported class/policy fail;decode verifies bytes==canonical_json(parsed body). No reflection dispatch. Disabled selections reject nonempty pending as before.

Verify registered simulated policy,producer node/lane/rank/emits,delivery_phase/priority,header phase/wave/sequence,empty degradation,namespace IDs,e1-SHA256 identity using world ID when validating core,sorted unique cause IDs,non-self cause. Queue item must have due_tick>occurred_at. At a checkpoint require occurred_at≤core.tick<due_tick;no due/past stranded event. Causes stored in valid queued records do not require an infinite historical ledger;runtime emission checks their origin when first produced. No record-only pending items,duplicate event IDs,unregistered subscriber,extra routing fields or silent sorting. Queue array must already be ordered by:
`(due_tick,delivery_phase numeric,priority,occurred_at,emission_phase numeric,emission_wave,producer_rank,sequence,event_id)`.
encode_core/decode_core roundtrip all bodies and enforce max_pending;feature policy additionally checks scoped invariants. Priority/delivery metadata in saved items must equal source policy;never silently rewrite them.

Complete hash_core_document:component leaves unchanged;pending leaves in canonical queue order are exactly `{event_id:q.event.header.event_id,hash:hash_document("pending-event/v1",q)}`. Root tags/identity/pins/clock/field names stay unchanged. Empty pending remains [];all four original fixture files remain byte/hash identical. New watch schema/rules/schedule/world pins explicitly select the newly supported queue semantics;no reinterpretation of an old nonempty checkpoint (previously unsupported).

### 4.3 NEW orchestration/events.py — candidate-only bus

Public concrete signatures (private indexes/helpers discretionary):
```python
def queued_sort_key(event: QueuedEvent) -> tuple[int, int, int, int, int, int, int, int, str]: ...

class CandidateEventBus:
    def __init__(self, policies: tuple[EventPolicy, ...], *, io: StateIO,
                 limits: ExecutionLimits, world_id: str, start_tick: Tick,
                 pending: tuple[PendingDocument, ...]) -> None: ...
    def begin_tick(self, logical_tick: Tick) -> None: ...
    def due(self, logical_tick: Tick, phase: Phase, wave: int) -> DeliveryBatch: ...
    def emit(self, invocation: EngineInvocation, producer_id: str, producer_rank: int,
             facts: tuple[EmittedFact, ...], degraded: tuple[Degradation, ...] = ()) -> tuple[WorldEvent, ...]: ...
    def complete(self, batch: DeliveryBatch,
                 deliveries: tuple[tuple[str, tuple[EventId, ...]], ...]) -> None: ...
    def finish_tick(self, logical_tick: Tick) -> None: ...
    def finish(self, target_tick: Tick) -> tuple[PendingDocument, ...]: ...
    @property
    def diagnostics(self) -> tuple[Failure, ...]: ...
```
These are implementable refinements of the architecture's conceptual EventBus,not a second CORE owner. Constructor owns typed copies of the validated pending records;all mutation is transaction-local. No engine invocation/state-view access inside bus. begin_tick requires prior+1 and resets event budget (not outer segmentation);due outside CASCADE uses wave0,inside0..waves−1. due returns the complete sorted immutable inbox;Driver filters matching kinds per subscriber. Repeated request of the same barrier may return its cached batch but cannot duplicate actual handler delivery. Delivered input IDs become permissible causes for handlers of that batch.

emit preserves draft tuple order;sequence0.. per producer/tick/phase/wave invocation. Driver verifies actual manifest/node/lane and one invocation;bus validates payload/policy/tick/causes/duplicates and builds the existing e1 ID framing. Only empty degraded is supported,as in accepted sources. caused_by must be lexically sorted unique e1 IDs from delivered inputs or already emitted earlier candidate events;unknown/future/self causes→INVALID_CAUSE. A new ID may not collide with any initial pending/new event. Event-ID/rank/sequence are independent of command ID,revision,outer wait length,registration order,wall time or hash().

Routing:record_only must be due now and never enters an inbox/queue. Simulated due<logical_tick→EVENT_PAST_DUE. Future due enters CORE candidate queue,deliver at due tick/declared phase/wave0. Due-now later phase enters that inbox. Same-CASCADE emission enters wave+1;nonempty wave8→CASCADE_LIMIT. Same/past phase outside that case→EVENT_LATE for reject policy;next_tick policy retimes due to tick+1,preserves ID/header,and appends one EVENT_DEFERRED diagnostic per retimed emission in emission order. Overflow retiming→INTEGER_OVERFLOW. Prototype policies all reject late routing;conformance ports exercise next_tick.

complete verifies exact subscriber→event ID coverage/no duplicate handler delivery,after all successful invocations/delta barrier validation. Then remove delivered items only from candidate pending/inbox. Failed handler/patch/complete/limits/final validation never modifies committed queue. Newly emitted immediate events enter a later barrier,never the current frozen batch. finish_tick proves no undelivered due/current inbox remains;finish proves only future queue remains and encodes it canonically. Errors:INVALID_EVENT_POLICY at boot;runtime INVALID_FACT/INVALID_CAUSE/DUPLICATE_EVENT/DUPLICATE_DELIVERY/UNDELIVERED_EVENT/EVENT_PAST_DUE/EVENT_LATE/EVENT_LIMIT/EVENT_QUEUE_LIMIT/CASCADE_LIMIT/INTEGER_OVERFLOW. All runtime errors are CandidateError(code,detail),not clipping/drop/degradation. max_events_per_tick counts ALL newly emitted events including record-only (therefore also bounds simulation≤512);initial pending/delivery itself is not a new emission. Queue cap counts all simulated items awaiting delivery,including later-wave inboxes. During emit,exclude the current frozen batch that complete must fully acknowledge;after complete recheck the actual remaining queue. Thus consuming a wake at a full queue and scheduling its replacement does not falsely overflow;an incomplete acknowledgment still aborts the whole candidate. No active batch→exclude nothing. Internal due-now routing uses typed QueuedEvent values;only future records reach encode_pending/checkpoint. Limits cannot reset per outer command.

### 4.4 Driver / generic effects validation

Preserve generic authorization/schema/fingerprint/receipt-conflict/highwater/retired/stale ordering before admission. Keep old disabled one-tick validation/errors. Enabled admission requires original command/start/actor/payload,strict positive target-start≤max_duration_seconds;zero/backward→INVALID_COMMAND,valid over-duration→TURN_LIMIT,signed64 target overflow→INTEGER_OVERFLOW. No tick/event work on rejection or retained retry. Clock/queue metadata remain orchestration inputs;engines see only logical_tick.

After admission,create one bus and stage `(start,target]` dense seconds. Each second runs PRE_TICK→RESOLVE→REACT→CASCADE→POST_TICK. Non-CASCADE wave0;CASCADE only nonempty0..execution_limits.cascade_waves−1 (prototype0..7). At each phase/wave freeze root+incoming;eligible nodes are every_tick,final-tick matching action_kind,or matching subscribed incoming. Multiple reasons invoke once. EngineInvocation.action is admitted action only for its final-tick matching action node;otherwise None. incoming is the whole sorted matching batch,never arbitrary source scanning. Apply existing read observation/target-only reducers/checked patch and same-phase barrier rules;earlier nodes' writes are not visible in that barrier. Next phase/wave sees staged results. Retain stable compiled A ranks even for inactive nodes. Collect delivered acknowledgments and complete only after barrier succeeds. POST_TICK finishes each staged second;no early outer head/revision.

Net-compose component changes from original→final across all phases/waves/ticks,omit identities,validate target-only net reads. Stage final pending/tick then hash/policy/protocol/effects;one receipt/revision/highwater/head swap at target. TurnPublication.facts contains ALL new emitted envelopes (simulated including future + record-only),ordered `(occurred_at,phase,wave,producer_rank,sequence)`;do not republish an old pending envelope just because it was delivered. Its original ID/header instead appears in resulting causal links. Diff remains component net changes. Deferred diagnostics survive into publication. Presentation occurs once after final commit.

Enabled validate_effects uses per-(tick,phase,wave,producer) contiguous sequence,source node/rank/policy/activation-kind or matching-consumer rights,ID recomputation,proper phase/wave/due/routing/causal syntax and empty degradation. Timing is bounded by `core.tick-max_duration_seconds < occurred_at ≤ core.tick`;record-only due==occurred_at;simulated due≥occurred_at (including legal deferral). Static witness validation cannot reconstruct the infinite delivered history:bus checks actual cause membership;IO checks canonical IDs/uniqueness/self/earlier newly emitted references. Per-tick cap=execution_limits.max_events_per_tick;outer cap=max_duration_seconds*max_events_per_tick (prototype512/8192);full queue/hash/target metadata still validated. Old disabled selections retain exact accepted effect rules/output bytes. Replay signatures and Runner/Recorder implementation stay READ because existing injected IO/full witnesses suffice.

Presenter selection filters record-only kinds;simulation has no cue ownership in this selection. Existing cue header occurred_at remains receipt.tick/Phase.PRESENT/wave0/rank0;each new watch cue carries logical_tick from its source event,so several historical pulses in one wait remain distinct and ordered. Presentation failure preserves committed receipt/queue/clock/components/facts/diff with PRESENTATION_FAILED/cues empty. No silent fact trimming/rollback or reconstruction from prose.

## 5. NEW Watch Feature Contracts

### 5.1 Domain / typed payloads

Reuse qualified trial/encounter public DTOs/keys/geometry/codecs/adapters/routes/reducers and original encounter engines unchanged. NEW domain/watch.py constants:NPC_ID=EntityId("actor:watcher"),LANTERN_ID=EntityId("object:lantern"),NPC_CELL6,WAKE_PERIOD2,CHARGE_MAX3,WAIT_MAX16,ECHO_DEPTH1. Watcher is a fixed nonblocking station in space:trial,not a moving combat enemy. Three frozen/slotted ComponentRecords (TypeKey version1):

| Record/schema | Fields / invariants |
|---|---|
| WatchNpcRecord / watch.npc | entity_id:EntityId,space_id:EntityId,cell:int6,bells:int0..MAX_INT;only watcher/space:trial in feature policy |
| LanternRecord / watch.lantern | entity_id:EntityId,charge:int0..3;only object:lantern |
| ReplyRecord / watch.reply | entity_id:EntityId,count:int0..MAX_INT;only watcher |

Pure helpers:next_wake(tick:int)->Tick = (tick//2+1)*2,integer0..MAX_INT and overflow ValueError;recover_charge(charge:int)->int=min(3,charge+1),exact0..3;increment_count(value:int,amount:int=1)->int,exact value0..MAX_INT/amount1..512,overflow ValueError. Engines convert arithmetic overflow to CandidateError INTEGER_OVERFLOW. No float/bool/coercion. Status projections/observer queries consume no time.

NEW contracts/watch.py read Protocols:WatchNpcRead.space_id:EntityId/cell:int/bells:int,LanternRead.charge:int,ReplyRead.count:int;keys WATCH_NPC/LANTERN/REPLY with exact schemas. NEW17frozen/slotted payloads/properties:

| Class/schema suffix under watch. | Exact fields (EntityId unless noted) |
|---|---|
| WaitCommand / wait | seconds:int1..16 |
| BellCommand / bell | npc_id |
| WatchWake / wake | npc_id |
| WatchRequested / requested | actor_id,npc_id |
| WatchEcho / echo | npc_id,remaining:int0..7 |
| NpcActed / npc-acted | npc_id,before_bells:int,after_bells:int |
| BellRung / bell-rung | actor_id,npc_id |
| WatchReplied / replied | npc_id,before_count:int,after_count:int |
| NpcCue / npc-cue | npc_id,logical_tick:Tick,before_bells:int,after_bells:int,cell:int6,x_mm:int0,z_mm:int2000 |
| BellCue / bell-cue | actor_id,npc_id,logical_tick:Tick |
| ReplyCue / reply-cue | npc_id,logical_tick:Tick,before_count:int,after_count:int |
| ChargeDelta / charge-delta | entity_id,before_charge:int,after_charge:int;target watch.lantern.charge |
| ChargePatch / charge-patch | charge:int0..3 |
| BellsDelta / bells-delta | entity_id,before_bells:int,after_bells:int;target watch.npc.bells |
| BellsPatch / bells-patch | bells:int0..MAX_INT |
| ReplyDelta / reply-delta | entity_id,before_count:int,after_count:int;target watch.reply.count |
| ReplyPatch / reply-patch | count:int0..MAX_INT |

Base classes exactly existing CommandPayload/FactPayload/PresentationPayload/StateDelta/ComponentPatch. All count endpoints0..MAX_INT;actor facts fixed actor:trial,npc facts fixed watcher. BellCommand permits syntactically valid unknown npc_id for INVALID_TARGET admission;simulated payloads require fixed subject. NpcActed/NpcCue after=before+1;WatchReplied/ReplyCue after=before+1;cue ticks positive,and NPC cue logical_tick is even with after_bells==logical_tick//2. Deltas permit bounded net compositions/identity at encoding;stage rules below are stricter. Unknown fields/classes/schema/version→SchemaError UNSUPPORTED_SCHEMA or ValueError for malformed shape/value,following existing concrete codecs. Decode immediately owns exact values;no client clock/duration on Bell,damage/queue/producer/cause fields in commands.

### 5.2 NEW engines/watch.py — exact bindings

All frozen/slotted,local,lane A,depends_on empty,no RNG/definitions/wall time. Manifests match the complete literal schedule in the artifact;old encounter manifests unchanged.

| Class / engine_id / phase / rank | Reads → writes;activation;emits/consumes |
|---|---|
| WatchNpc / watch.npc / PRE_TICK /0 | watch.npc.{bells,cell,space_id}→bells;on_matching_events only;consumes wake;emits npc-acted,wake |
| existing EncounterActions / RESOLVE /1 | Original qualified manifest/action kinds/emits |
| existing EncounterMovement / RESOLVE /2 | Original qualified manifest/action kinds/emits |
| WatchBell / watch.bell / RESOLVE /3 | encounter.hp.hp,trial.position.space_id,watch.npc.{cell,space_id}→none;action watch.bell;emits requested,bell-rung |
| WatchRespond / watch.respond / REACT /4 | no component reads/writes;on_matching_events;consumes requested;emits echo |
| WatchEchoEngine / watch.echo / CASCADE /5 | watch.reply.count→count;on_matching_events;consumes echo;emits echo,replied |
| WatchPassive / watch.passive / POST_TICK /6 | watch.lantern.charge→charge;every_tick;no events |

WatchNpc receives exactly one correctly scoped Wake at its even due logical tick;no action,source due tick matches invocation,source ID preserved. Read count/topology;increment bells;emit NpcActed sequence0 and next WatchWake sequence1,due tick+2,both caused_by=(deliveredWakeID,). No hidden last-run cursor:next wake is CORE queue authority. Delayed event sequence/IDs are based on actual tick,not the outer wait boundary.

WatchBell requires admitted alive player/fixed watcher/same space;emit WatchRequested sequence0 then BellRung sequence1,due now,root causes empty. WatchRespond processes sorted requests and emits one WatchEcho(remaining1) per input,caused by its request ID,in input order. WatchEchoEngine processes the whole sorted inbox:remaining>0→emit Echo(remaining−1) for next wave;remaining0→emit WatchReplied using successive count endpoints. Draft order follows input order;return one ReplyDelta(old,total_final) when one or more replies complete. No duplicate target deltas for a batch. WatchPassive increments charge by1/caps3 each second,return one nonidentity ChargeDelta or none;no records/events for unchanged charge. PRE_TICK cannot invalidate encounter admission because it changes no encounter fields.

Policies:watch.wake simulate/PRE_TICK/priority10/producers watch.npc/subscribers watch.npc;watch.requested simulate/REACT/20/producers watch.bell/subscribers watch.respond;watch.echo simulate/CASCADE/30/producers watch.respond+watch.echo/subscribers watch.echo. watch.npc-acted/bell-rung/replied record_only/PRESENT/0,their named producers and watch.presenter. All late_route=reject,cancellers empty. Original6encounter record policies preserved. Explicit twelve-policy list in rules must equal registration.

### 5.3 NEW orchestration/watch.py — trusted concrete ports

WatchNpcAdapter/LanternAdapter/ReplyAdapter and corresponding Codec classes validate exact records/schema/entity syntax/scalars,closed fields,immutable reads. Observe exact FieldAddress/path()/read before every property;set/delete observe write then ReadOnlyViolation;all retained aliases expire. WatchPayloadCodec(schema:TypeKey) registers exactly17NEWpayloads with exact class/closed fields/arithmetic/IDs/geometry/ranges. Reuse original23codecs without broadening them.

WatchAdmission(schema:TypeKey) routes wait/bell. Wait reads encounter.hp.hp;Bell additionally reads watch.npc.cell/space_id and trial.position.space_id. Generic retry/stale etc first;actorHP0→ACTOR_DEFEATED before target checks;unknown bell NPC→INVALID_TARGET,unexpected fixed references→CandidateError INVALID_ACTION. Bell is a shared same-space signal,no distance requirement. Wait duration comes only from validated seconds;Bell1second. Use exact existing action-key/v1/payload/v1 framing with target_tick=start+duration;no rejected time/highwater/cost. Arithmetic target overflow→INTEGER_OVERFLOW. Wait has no action activation,so every engine receives action=None during it;it is the public passive catch-up path without another driver API.

ChargeReducer.owner watch.passive;BellsReducer.owner watch.npc;ReplyReducer.owner watch.echo. stage validates exact delta/schema/fixed subject/range/expected old and reads ONLY target. Charge step exactly+1 (not cap identity);bells+1;reply positive increase1..512 for batched replies. Patch routes replace only owned scalar. compose nonempty/same target/continuous,returns first→last endpoints;is_identity validates exact bool;validate_net rejects identity and matches after target using finally-closed observed reads. No reducer clock/queue/topology reads. Charge/Bells/ReplyPatchRoute component/schema/family exact,immutable reference fields protected.

WatchCheckpointPolicy exactly10sorted records:the unchanged seven encounter records,then LanternRecord(object:lantern),WatchNpcRecord(watcher,space:trial,6,bells),ReplyRecord(watcher,count). Validate original subprojection with EncounterCheckpointPolicy after excluding new records and passing pending=() only to that qualified subvalidator;validate full pending independently with StateIO. Watch count invariant bells==core.tick//2;charge==min(3,core.tick);reply count arbitrary0..MAX_INT (replay checks its actual history). Exactly one queued Wake for watcher,PRE_TICK/priority10,due=next_wake(core.tick);initial header at tick0/seq0/root,otherwise previous even tick/seq1/caused_by one e1 ID. No queued Request/Echo at commit. No packages,only original player streams;player body/death/dynamic gate/enemy occupancy retain encounter rules. At an even wake requiring next_tick beyond MAX_INT,engine aborts before commitment;unrepresentable successor queue never clips.

WatchPresenter.map uses new observed NPC/lantern/reply keys and emits NpcCue/BellCue/ReplyCue only for its three record kinds,in full source order. Validate topology,each fact's arithmetic,logical tick within committed time,monotone ordered per-turn count chains and last endpoints against final head. Earlier NPC pulses need not individually equal the final count. Cue occurred_at=receipt.tick but payload.logical_tick=source.header.occurred_at;source cause/e1→p1 cue framing unchanged. Cell6→(0,2000)mm. Preserve all pulses from multisecond waits;no cue coalescing. Presenter ID watch.presenter,local sequence from0,important/keep_all/empty coalesce key. Existing encounter presenter is separately selected inside the same bundle and remains unchanged.

## 6. Registry / App / Compatibility

NEW app/watch_registry.py `watch_bundle()->FeatureBundle` returns one feature_id watch.local. It may start from qualified encounter_bundle() and construct/replace its explicit registration tuples,not pass or aggregate two bundles. Add5bindings/3components/adapters/codecs/5metadata fields/2command routes/3delta routes/3patch routes/6event policies/1presenter/17payload codecs;totals7nodes,8component schemas,10records,16fields,40payloads,12event policies. Original routes have unchanged owners. Metadata CORE/A/scale1,no collection caps except inherited wall cap1;new scalar units charge/count;space_id entity_id and cell6 immutable bootstrap fields. watch.npc consumers watch.npc/watch.bell/watch.presenter/system.admission;lantern watch.passive/watch.presenter;reply watch.echo/watch.presenter. In the NEW bundle only,append watch.bell to the existing encounter.hp.hp and trial.position.space_id consumer tuples;preserve all previous consumers/owners/ranges/schema descriptors. Existing encounter_bundle source/selection stays READ. Exact descriptors and rules literal canonical bytes must be copied from the READ artifact,not generated from runtime/Recorder.

NEW app/watch.py frozen/slotted `WatchBootstrapSpec(seed_hex:str,branch_id:str,stream_id:str,initial_cell:int=0,gate_open:int=0,actor_hp:int=3,enemy_hp:int=5,stamina:int=2)`. Initial tick/revision always0 (no hidden elapsed-history bootstrap). Exact types/lowercase64/32/32hex/ranges/placement as encounter;invalid→BootstrapError INVALID_INITIAL_STATE before owner creation. `bootstrap_watch(spec,*,rng:RngService|None=None)->HeadlessSession` builds one IO/world ID,ten ordered records,original player protocol and genesis queue. Genesis is WatchWake(watcher),header occurred0/PRE_TICK/wave0/watch.npc/rank0/sequence0/empty causes,degraded(),due2,wrapped PRE_TICK/priority10. ID uses ordinary e1 framing (trusted bootstrap seed,not an executed turn). Default CounterRngService has no watch purposes. Do not bootstrap an old owner then inject a foreign private head.

Reuse unchanged app.headless._restore with io=selected_io;public restore_checkpoint/replay_runner explicitly bundles=(watch_bundle(),);Recorder/fixture codecs explicit IO;fresh owner/services every restore/run. `main(argv:Sequence[str]|None=None)->int` has no flags;zeros seed/branch,ones stream;nonblank stdin JSON→submit→canonical publication newline/flush;return0. New PYTHONPATH=src python -m app.watch. Old app CLIs/bundles/pins/canonical fixtures unchanged. No auto-migration/hot reload/default union;watch fixture with default/encounter selection rejects before execution.

## 7. Independent Examples / Planned Tests

Artifact retains stdlib requirements source written before implementation. Its prefix reuses the retained CORE-03 independent arithmetic (not production/test imports);new time/queue/identity/hash/response expectations use struct.pack length framing. Source includes exact40payload/16field/7node descriptors,all emitted headers/causes/due/pending leaf hashes/receipts/full publications/cues. Production never reads it. Copy only expected_fixture→NEWwatch_v1.json,passive_fixture→NEWwatch_passive_v1.json. Do not replace expected values with Recorder output. Parse authoring metadata with stdlib JSON then seal only requested domain sections,as in existing helpers.

Literal pins:schema968816692a49ab073433aefe4877c6a50a298990e88c9d2660efc2f2c3363397;rulesaae7ca96e70090ba755b869af126a127a7ec79f84775fe36f49ae7984fb02f68;scheduledbf42efc1f34f30846e4df3f6865306e0d17013a1d7f621279574701c8a3aedd;initial COREee640cdec8445cefdf1e66e3704af20b3a7e325f90ad306e8fab7808cad27097. Main canonical fixture SHA2565417a81e82ad04886d9e63fe7669e409da0a041ef99f80200fa323c7896a2b85;passiveb421e76e9a06b42bf993b251e448858f141454ce0739b7b34e94f46f577a41fb.

Main13steps (initial charge/bells/replies0,nextwake2;original encounter default):

| Index / command | Result;tick/revision;NPC bells/replies/charge,next due;new facts/cues |
|---|---|
|0 wait1 seq1 rev0|commit;1/1;0/0/1,due2;0/0;passive charge delta|
|1 bell seq2 rev1|commit;2/2;1/1/2,due4;7/3;NPC PRE→Bell RESOLVE→Respond REACT→Echo wave0→Reply wave1|
|2 wait3 seq3 rev2|commit;5/3;2/1/3,due6;2/1;wake at4,one outer receipt/net deltas|
|3 bell seq4 rev3|commit;6/4;3/2/3,due8;7/3|
|4 exact seq2/rev1 bell retry|original receipt2,head6/4;no time/effects;RESYNC_REQUIRED|
|5 seq5 wait2 rev0|STALE_REVISION;head unchanged|
|6 changed seq4 bell target|COMMAND_ID_CONFLICT;head unchanged|
|7 seq5 bell unknown watcher rev4|INVALID_TARGET;unused ID remains reusable|
|8 seq5 wait2 rev4 reused|commit;8/5;4/2/3,due10;2/1|
|9 seq6 Down rev5|commit;9/6;4/2/3,due10;1/1;player0→3,original movement at rank2|
|10 seq7 open gate rev6|commit;10/7;5/2/3,due12;3/2;NPC pulse and gate0→1|
|11 seq8 bell rev7|commit;11/8;5/3/3,due12;5/2|
|12 seq9 wait16 rev8|commit;27/9;13/3/3,due28;16/8;all eight scheduled pulses retained|

Independent passive one-step fixture:wait16 from0→16/revision1,bells8/charge3/replies0,nextwake18;16new events/8cues,net Charge0→3/Bells0→8,genesis removed,one future wake with original header tick16/seq1/cause from due16 input. Dead fixture section (not another copied fixture) has two rejected wait/bell commands,HP0 priority ACTOR_DEFEATED,initial queue/clock/receipt unchanged.

Composition480cases:start ticks0..3,duration1..16,every split1..duration−1. Prelude uses the same wait path for nonzero start. Single wait vs split waits must equal every CORE field/pending header+payload+cause/order/root hash and ordered autonomous emission IDs (concatenate facts);transport revisions/receipts/cue envelope target times differ explicitly. No active Bell/move is inserted into the split law. Eight independent cascade vectors vary initial remaining0..7 via a conforming response fixture,assert1..8nonempty waves/causal headers/finalreply1;the real WatchRespond uses remaining1. Queue-order input permutation has6valid delayed Request envelopes and exact sorted output,not insertion order.

Limits examples use purpose-built conforming generic bus/engine ports,not invalid WatchCheckpoint scopes:512new events/tick permitted,513→EVENT_LIMIT;4096initial future queue permitted,enqueue4097th→EVENT_QUEUE_LIMIT;the prototype policy itself permits only its single wake. Finishing wave7 with record-only reply permitted;valid self-feedback requiring wave8→CASCADE_LIMIT. Due-now PRE_TICK event emitted at POST_TICK tick3 rejects EVENT_LATE,or under explicit next_tick policy becomes due4 with EVENT_DEFERRED. Past due2 at tick3→EVENT_PAST_DUE;unknown/self/future cause→INVALID_CAUSE;collision→DUPLICATE_EVENT;missing/duplicate subscriber completion→UNDELIVERED_EVENT/DUPLICATE_DELIVERY. Repeat bus emission does not reset tick counters. Next wake arithmetic beyond signed64→INTEGER_OVERFLOW;all aborts retain old queue+CORE+protocol.

Self-consistent negative prefix changes mainstep1 reply count to0/removes corresponding Replied+ReplyDelta,recomputes full root/receipt/protocol/fact/diff hashes. First mismatch step1 `$core.components[9].fields.count` expected0/actual1. Losing NpcActed from publication reports `$facts[0]` on step1 with matching queue/head;changing/removing future Wake reports a pending CORE leaf/hash,not a visible-only success. Corrupt pending bytes/due/policy/source pins or invalid last witness must reject before the first factory restore. Dropped Reply at mainstep1 reports `$facts[6]` missing even when real cues remain.

| NEW planned path | Meaningful responsibilities / nodes |
|---|---|
| tests/unit/watch_fixtures.py | Explicit bundle/session/command/reference/view and real fault ports;no runtime-derived oracle |
| tests/unit/test_watch.py | test_literal_pins;test_records_payloads;test_scalar_reducers;test_observed_reads;test_registry_ownership. Exact17new codec/3component coverage,bool/float/NFC/class/version/bounds/steps/net/reference/expiry |
| tests/unit/test_events.py | test_pending_roundtrip_and_leaf_hash;test_queue_order;test_routing_causes_and_late;test_delivery_coverage;test_limits. Exact headers/policies/canonical bytes/cause sets/duplicates/boundaries |
| tests/integration/test_watch.py | test_full_publications;test_passive_composition (480cases);test_wait_and_bell_no_time_errors;test_npc_before_action;test_cli;test_dead_actor;test_recorded_queue_restore. Actual one outer receipt/final-tick action/ten-record path/no query catch-up |
| tests/integration/test_event_turn.py | test_cascade_vectors;test_multisubscriber_barrier;test_event_tick_budget;test_abort_restores_queue;test_registry_rights;test_postcommit_failure;test_overflow. Fault after real due consumption/HP staging/batch completion/cascade/net/policy,finally-expired aliases;POST cue failure retains pending/head;late deferral and malformed cause/duplicate coverage |
| tests/replay/test_watch.py | test_watch_core_trace;test_watch_passive_trace;test_recorder;test_fact_loss;test_pending_mismatch;test_wrong_reply;test_invalid_last_witness_before_execution;test_fresh_ordered_sessions. All14full copied fixture steps/full pending witnesses,precise leaf diagnostics,fresh/reordered registrations |

No mocks of domain outcomes/skip/xfail/old assertion deletion. A faulty port must first execute the real calculation/staging before injecting the contract fault where relevant. Independent-person/full cognition/full-game/latency/memory qualification UNVERIFIED.

## 8. Implementation / Verification / Acceptance

Order:refresh99entry hashes/source/tests→newgeneric queue/limits DTO+IO codecs/hash→candidate bus/phase-wave delivery and enabled boot rules→same Driver dense ticks/staged pending/effects→watch DTOs/ports/scalars/engines/registry/bootstrap→copy vetted fixtures/add live tests→full checks/self-review→five delivery docs. Shared files only change for generic time/queue support;no concrete gameplay branch. Preserve every old431test assertion and four canonical fixture bytes.

Baseline/final existing commands:
```powershell
git -c safe.directory='C:/Reverie Saga' rev-parse HEAD
git -c safe.directory='C:/Reverie Saga' status --short
git -c safe.directory='C:/Reverie Saga' diff --check
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.venv/Scripts/python.exe -m pytest -q tests
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m mypy --strict src tests
.venv/Scripts/python.exe -m pytest -q tests/replay/test_golden.py::test_core_trace tests/replay/test_trial.py::test_trial_core_trace tests/replay/test_encounter.py::test_encounter_core_trace tests/replay/test_encounter.py::test_encounter_death_trace
```
Only AFTER NEW paths exist:
```powershell
.venv/Scripts/python.exe -m pytest -q tests/unit/test_events.py tests/unit/test_watch.py tests/integration/test_event_turn.py tests/integration/test_watch.py tests/replay/test_watch.py
.venv/Scripts/python.exe -m pytest -q tests/replay/test_watch.py::test_watch_core_trace tests/replay/test_watch.py::test_watch_passive_trace
rg -n 'WatchNpcRecord|LanternRecord|ReplyRecord|watch\.|actor:watcher|object:lantern' src/orchestration/serialization.py src/orchestration/turn.py src/orchestration/events.py src/orchestration/replay.py
$env:PYTHONPATH='src'
@'
{"command_id":"c1:00000000000000000000000000000000:11111111111111111111111111111111:1","actor_id":"actor:trial","expected_revision":0,"schema":{"kind":"watch.wait","version":1},"payload":{"seconds":16}}
'@ | .venv/Scripts/python.exe -m app.watch
```
CLI wait16 must equal the full independent passive publication;also main13JSON commands through fresh CLI exactly equal main publications. Run old and new qualified replay/Recorder,source/pin prevalidation/permutation/fresh owners. Generic search0matches. Capture actual full count/exits/time;local Ruff+all core goldens feedback only,not p95/p99/memory proof. No check of a nonexistent future node is described as execution.

Acceptance:three named shared files extend registered generic contracts only;actual pending/tick/subscriber/phase-wave loop reaches independent NPC/call/response/wait/record/restore/replay;all full emitted facts/pending causes/IDs/hash values and14complete copied steps/publications match;all480splits preserve complete CORE/pending/autonomous IDs;limits/late/order/strict codecs/owner/batch/atomic/finally/postcommit/source pins/last witness diagnostics pass;old431tests/four fixtures/legacy pins unchanged;Ruff/strict typing pass;scope hashes explain only allowed changes. Mark CORE-04 DONE only then,parent IN_PROGRESS,next author CORE-05 durability/receipt recovery against accepted queued source.

## 9. Authoring Evidence / Readiness

Entry431tests in38.08s/Ruff/strict mypy61files PASS. Inspected actual Driver/IO/hash/protocol/replay/policy/binding and conceptual A4/A11 contracts. Settled previously missing incoming routing,queue codec/hash,one-tick restriction,static effects timing/causes,postcommit historical cues,scope-specific policy,sole writer/atomic queue rights and bounded passive example. No existing runtime/test/init/config/lock/oracle/spec/Phase0-contract change in this authoring task.

Independent source contains retained CORE-03 requirements arithmetic plus new struct-framed time/event calculation,not production imports. It fixes40payloads/16fields/7node ranks,13main+1passive complete publications/witnesses,two no-time dead cases,480composition cases,8cascade depths,queue permutation/boundary expectations and a valid wrong-reply prefix.99entry input raw hashes retained. Future source/test/fixture/CLI runtime NOT_RUN;emotion/BDI/memory/cancellation/save/full-game/performance/independent-person remain UNVERIFIED or unimplemented. NEXT:execute CORE-04,then author CORE-05.

Actual authoring verification (2026-10-05):
- Reexecuted retained requirements source with stdlib stdin Python:all23result sections exactly equal JSON expectations. Source imports only copy/hashlib/json/struct. Replaced struct.pack length framing with int.to_bytes in a separate execution;all23sections still identical. No runtime/Recorder oracle generation.
- Existing orchestration.scheduler.compile_schedule with real CapabilityManifest/NodeActivation/PhaseAccess/TypeKey DTOs compiled7prospective nodes to the exact literal schedule pin and A ranks0..6;reversed registration identical. This checks existing compiler compatibility,not execution of nonexistent watch engines.
- All original5component schema/23payload descriptors and encounter rule values match accepted actual encounter_bundle;2existing node access declarations unchanged. New descriptors total8schemas/40payloads/16fields;12policies cover every producer/consumer with the declared phase/activation.
- Recomputed18witness sets (13main+1passive+2dead+2negative),all CORE/protocol/facts/diff hashes and83event/pending ID occurrences;canonical unique causes and all publication cue IDs agree. All480composition cases/8cascade depths/6queue-order items consistent. Independent completed pending-leaf formula preserves all44CORE hashes across the four original fixtures.
- Three Python interface fences AST-parse under actual Python3.13.12.16prospective NEWruntime/test/fixture paths absent;3MODIFYruntime paths present. Canonical literal UTF8/hex/tagged pins agree with this order. UTF8/fences/local link targets/whitespace/Git diff check PASS.
- Artifact1519959raw bytes,SHA2561cbd41e8bb13f11292c6b1d260325f3f7c99eb7c64cf48d8d3e4c641de196fdb. All99entry inputs matched before delivery edits;final96READ hashes unchanged,only BACKLOG/SESSION_HANDOFF/parent differ as authorized. HEAD/main unchanged. Final authoring scope2NEWorder/artifact+3existing delivery docs;runtime/tests/config/lock/oracles/architecture/specs/PHASE0_CONTRACTS unchanged.

Reproduce the retained source/pins/READ scope check (not a new project tool):
```powershell
@'
import hashlib,json
from pathlib import Path
p=Path("docs/work_orders/RS-P1-CORE_04_REFERENCE_VECTORS.json")
v=json.loads(p.read_text(encoding="utf-8"));g={}
exec(compile(v["reference_source"],"<independent CORE04>","exec"),g)
for k,x in g["result"].items():assert v[k]==x,k
delivery={"BACKLOG.md","SESSION_HANDOFF.md","docs/work_orders/RS-P1-CORE_VERTICAL_SLICE.md"}
for name,digest in v["baseline"]["source_sha256"].items():
    if name not in delivery:assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,name
print("23 independent sections match;96 READ inputs retained")
'@ | .venv/Scripts/python.exe -
```

Decision:instruction READY;implementation NOT_STARTED. Sol self-review complete;independent-person review UNVERIFIED. CORE-01/02/03 DONE,parent IN_PROGRESS,CORE-05 DRAFT. No new source/tests/dependency/install/agent/policy/CI/commit/push/external write in this delivery.


## 10. CORE-04 Execution / Acceptance — 2026-10-05

Director's "다음거 ㄱ" executed this READY instruction. Entry HEAD/main unchanged;96READ authoring inputs matched before edits;the3historical delivery-doc differences were expected. Entry431tests in37.58s/Ruff/strict mypy61files PASS. Preserved preexisting primary/MASTER edits and all untracked prior work;no agents/install/dependency/policy/CI/commit/push/external write.

Actual exact delivery:8NEW production files,3MODIFY shared production files,6NEW test/helper modules,2NEW independent fixtures,5MODIFY delivery docs. All19source/test/fixture paths in §3 now exist. No other existing source/test/init/config/lock/oracle/architecture/spec change. Reference artifact1519959bytes/SHA2561cbd41e8bb13f11292c6b1d260325f3f7c99eb7c64cf48d8d3e4c641de196fdb READ unchanged. Relative to its99historical input hashes,final92READ match;only3shared production+4listed existing delivery docs differ. This order was NEW at authoring and is the fifth execution delivery doc. Original4fixtures/old reference artifacts/test assertions retain raw hashes. Two new fixtures are byte-for-byte canonical independent copies with the §7SHA256 values;never generated from Recorder.

Live wiring:contracts/events.ExecutionLimits/QueuedEvent/DeliveryBatch→StateIO.execution_limits/encode_pending/decode_pending→RegisteredStateIO strict policy pins/canonical pending/complete leaf hashing→same Driver dense seconds/frozen inbox/phase-wave barriers→CandidateEventBus staged routing/coverage/causal identity/bounds→registered watch engines/scalar ports→one outer CORE+queue+clock+protocol commit→record presenters. watch_bundle is one explicit qualified encounter extension;bootstrap_watch builds its own ten-record initial owner and trusted genesis wake. CLI PYTHONPATH=src;python -m app.watch accepts stdin command JSON. app.headless/replay/Recorder/Runner source APIs/implementation remain unchanged and select the watch bundle/IO explicitly. No new source imports/reference-oracle reads in runtime;generic source has0watch-concrete matches.

Delivered behavior:wait1..16 consumes exact canonical seconds;station NPC acts at every even due tick,queues its successor with the delivered cause ID and stable logical-tick identity. Bell request→REACT response→two CASCADE waves completes one reply. Passive charge increments each second/caps3. Only final-tick matching action executes;queries/rejections/retries do not catch up. Historical NPC cues preserve individual pulse ticks;queue+components+clock remain atomic on candidate failure;postcommit presenter failure retains committed effects.

Actual verification (all exit0):
- Full `.venv/Scripts/python.exe -m pytest -q tests` with PYTEST_DISABLE_PLUGIN_AUTOLOAD=1:1009passed in111.20s (431unchanged previous+578new). All480wait compositions preserve complete CORE/pending/hash/autonomous envelopes while transport revisions differ;all8cascade-depth vectors match full independent emissions. Main13/passive1/dead2 complete publications and witnesses match requirements exactly;real13command and passive16-second JSON CLI outputs match canonical expectations.
- `.venv/Scripts/python.exe -m ruff check src tests`:PASS. `.venv/Scripts/python.exe -m mypy --strict src tests`:PASS,75source files. All original4+new2qualified replay golden nodes:6passed in3.14s. Local Ruff+6goldens feedback3.8168596s (concurrent full-suite execution);this is not device/p95/p99/memory qualification.
- Real Recorder matches both independent traces/full queues,restore continues the exact next wake,repeat runs use fresh owners,reversed registry ordering preserves pins/replay. Initial/source pins and invalid last witness reject before the first factory restoration. Self-consistent wrong-reply prefix first mismatch is step1 `$core.components[9].fields.count`,expected0/actual1. Altered future Wake cause reports `$core.pending[0].event.header.caused_by[0]`. Dropped Reply reports step1 `$facts[6]` missing with real cues retained.
- Clarified one anticipated diagnostic without changing replay/reference behavior:removing just the first NpcActed compacts the array,so the unchanged recursive comparator reports step1 `$facts[0].due_tick` (expected2,actual4 on the following future Wake),rather than the authoring shorthand `$facts[0]`. The test removes exactly that NPC fact;CORE and actual cues remain unchanged. The independent wrong-reply oracle and all old assertions remain READ.
- Strict payload classes/closed fields/missing fields/bool/float/NFC/schema/version/IDs/count arithmetic/geometry,owned observed reads/mutation/expiry,target-only scalar stage/continuous net/replacement protection and registry/source-policy rights PASS. Queue roundtrip/canonical bytes/duplicate JSON keys/policy metadata/producer rank/wave/source identity/order/stranded due/non-self cause checks PASS.
- Bus boundary conformance:512new events/tick permitted,513and repeat over-budget emission fail EVENT_LIMIT;4096valid future items fit,4097fail EVENT_QUEUE_LIMIT;full4096-item frozen delivery releases capacity before replacement accounting. Exact16seconds with512events per tick produces8192facts/8184cues/one receipt,proving budgets reset per logical second and the outer cap accepts its boundary. These are purpose-built conforming ports,not extra prototype NPC behavior.
- Real subscriber batch conformance:observer and responder receive the same six ordered delayed requests once per REACT barrier;CASCADE returns one aggregated ReplyDelta0→6,one record/cue per reply,no republishing of old inputs. Late POST request rejects EVENT_LATE or defers to the next tick with preserved header and EVENT_DEFERRED,then actually triggers a reply. Wave8/self-feedback aborts CASCADE_LIMIT;negative/zero/bool plan target INVALID_COMMAND,17second target TURN_LIMIT,unrepresentable target/successor INTEGER_OVERFLOW. This found/fixed enabled negative-target classification;disabled legacy admission/error path remains unchanged.
- Candidate fault injection after real NPC calculation/consumption,real HP+stamina staging,invalid/duplicate delta/unknown cause/undeclared read,patch replacement,final policy/net validation retains old CORE+pending+protocol and finally-expired aliases. Postcommit real-presentation failure retains receipt/facts/diff/next wake. Dead actor rejects before unknown target;ID reuse/conflict/stale/retained retry priorities match the complete reference flow.
- Generic modules contain no watch NPC IDs/classes/dispatch;runtime imports no tests/Recorder/reference data. Final scope hashes,UTF8/fences/local links/whitespace/Git diff checks PASS. HEAD/main unchanged;all original user edits retained. Existing Python launcher location diagnostic and Git LF→CRLF warnings remain non-failing environment messages.

Sol self-review:single CORE owner/clock/queue writer,registered rights/pins,canonical ordering/budgets/causes,phase-root immutability,atomic publication/finally lifetimes and compatibility accepted. NPC cognition/emotion/persona/attitude/BDI/memory,cancellation/interruptible combat/roaming,LOD/idle skip,SQLite durability/save slots/client/full-game/performance/independent-person qualification remain outside this unit. No production per-turn LLM/provider call.

Decision:CORE-04 ACCEPTED/DONE;CORE-01/02/03/04 DONE,parent RS-P1-CORE IN_PROGRESS. NEXT:author CORE-05 durability/receipt-recovery/save-load instruction against these actual queued codecs and accepted Driver;CORE-05 remains DRAFT until its own contracts/crash/migration/independent examples are settled.
