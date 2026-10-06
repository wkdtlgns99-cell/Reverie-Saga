from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from typing import Protocol

from app.headless import HeadlessSession, restore_checkpoint, state_io
from contracts.errors import CandidateError, ReadOnlyViolation
from contracts.messages import CommandPayload, EmittedFact, EventHeader, EventPolicy, FactPayload, PresentationEvent, PresentationPayload, StateDelta, WorldEvent
from contracts.read_views import AdapterBinding, ComponentKey, ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.skeleton import FeatureBundle, PresenterBinding
from contracts.turn import AdmittedAction, AdmittedCommand, AdmissionOutcome, CapabilityManifest, CommitReceipt, EngineBinding, EngineInvocation, EngineResult, GameCommand, NodeActivation, NodeKey, PhaseAccess, ProtocolSnapshot, StreamCursor, TurnPlan, TurnRejected, failure
from domain.canonical import JsonObject, decode_json, exact_fields, int_value, object_value, pack, seal, text_value
from domain.primitives import CommandId, ComponentAddress, EntityId, EventId, FieldAddress, FieldFamily, FieldSpec, FrozenPayload, Phase, Tick, TypeKey, WorldRevision, require_integer, require_namespace
from domain.state_types import ComponentRecord, CoreSnapshot

ACTOR = EntityId("actor:sample")
VALUE = FieldFamily("fixture.gauge", "value")
LABEL = FieldFamily("fixture.gauge", "label")


def key(kind: str) -> TypeKey:
    return TypeKey("fixture." + kind, 1)


@dataclass(frozen=True, slots=True)
class GaugeRecord(ComponentRecord):
    entity_id: EntityId
    value: int
    label: str

    @property
    def schema(self) -> TypeKey:
        return key("gauge")


class GaugeRead(Protocol):
    @property
    def value(self) -> int: ...
    @property
    def label(self) -> str: ...


GAUGE = ComponentKey[GaugeRead](key("gauge"))


class _GaugeView:
    def __init__(self, record: GaugeRecord, access: ViewAccess) -> None:
        object.__setattr__(self, "_record", record)
        object.__setattr__(self, "_access", access)

    _record: GaugeRecord
    _access: ViewAccess

    @property
    def value(self) -> int:
        self._access.observe(FieldAddress(VALUE, self._record.entity_id), (), "read")
        return self._record.value

    @property
    def label(self) -> str:
        self._access.observe(FieldAddress(LABEL, self._record.entity_id), (), "read")
        return self._record.label

    def __setattr__(self, name: str, value: object) -> None:
        self._access.observe(FieldAddress(FieldFamily("fixture.gauge", name), self._record.entity_id), (), "write")
        raise ReadOnlyViolation(name)


class GaugeAdapter:
    @property
    def key(self) -> ComponentKey[GaugeRead]:
        return GAUGE

    def validate(self, record: ComponentRecord) -> None:
        if not isinstance(record, GaugeRecord):
            raise ValueError("gauge class")
        require_namespace(record.entity_id)
        require_integer(record.value, -9, 9)
        seal(record.label)
        if not isinstance(record.label, str) or not 1 <= len(record.label.encode("utf-8")) <= 64:
            raise ValueError("gauge label")

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> GaugeRead:
        self.validate(record)
        assert isinstance(record, GaugeRecord)
        return _GaugeView(record, access)


class GaugeCodec:
    @property
    def schema(self) -> TypeKey:
        return GAUGE.schema

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        data = exact_fields(fields, ("value", "label"))
        return GaugeRecord(entity_id, int_value(data["value"]), text_value(data["label"]))

    def encode(self, record: ComponentRecord) -> JsonObject:
        GaugeAdapter().validate(record)
        assert isinstance(record, GaugeRecord)
        return {"value": record.value, "label": record.label}


@dataclass(frozen=True, slots=True)
class AdjustCommand(CommandPayload):
    amount: int

    @property
    def schema(self) -> TypeKey:
        return key("adjust")


@dataclass(frozen=True, slots=True)
class GaugeDelta(StateDelta):
    subject: EntityId
    before_value: int
    after_value: int

    @property
    def schema(self) -> TypeKey:
        return key("gauge-delta")

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(VALUE, self.subject)


@dataclass(frozen=True, slots=True)
class GaugeChanged(FactPayload):
    subject: EntityId
    before_value: int
    after_value: int

    @property
    def schema(self) -> TypeKey:
        return key("gauge-changed")


@dataclass(frozen=True, slots=True)
class GaugeCue(PresentationPayload):
    subject: EntityId
    before_value: int
    after_value: int

    @property
    def schema(self) -> TypeKey:
        return key("gauge-cue")


@dataclass(frozen=True, slots=True)
class GaugePatch(ComponentPatch):
    value: int

    @property
    def schema(self) -> TypeKey:
        return key("gauge-patch")


@dataclass(frozen=True, slots=True)
class GaugePayloadCodec:
    schema: TypeKey

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if payload.schema != self.schema:
            raise ValueError("payload schema")
        if isinstance(payload, AdjustCommand):
            require_integer(payload.amount, -3, 3)
            return {"amount": payload.amount}
        if isinstance(payload, GaugePatch):
            require_integer(payload.value, -9, 9)
            return {"value": payload.value}
        if not isinstance(payload, (GaugeDelta, GaugeChanged, GaugeCue)):
            raise ValueError("payload class")
        require_namespace(payload.subject)
        require_integer(payload.before_value, -9, 9)
        require_integer(payload.after_value, -9, 9)
        return {"subject": payload.subject, "before_value": payload.before_value, "after_value": payload.after_value}

    def decode(self, data: JsonObject) -> FrozenPayload:
        if self.schema == key("adjust"):
            return AdjustCommand(int_value(exact_fields(data, ("amount",))["amount"]))
        if self.schema == key("gauge-patch"):
            return GaugePatch(int_value(exact_fields(data, ("value",))["value"]))
        d = exact_fields(data, ("subject", "before_value", "after_value"))
        subject = EntityId(text_value(d["subject"]))
        before, after = int_value(d["before_value"]), int_value(d["after_value"])
        if self.schema == key("gauge-delta"):
            return GaugeDelta(subject, before, after)
        if self.schema == key("gauge-changed"):
            return GaugeChanged(subject, before, after)
        if self.schema == key("gauge-cue"):
            return GaugeCue(subject, before, after)
        raise ValueError("payload schema")


class GaugePatchRoute:
    @property
    def schema(self) -> TypeKey:
        return key("gauge-patch")

    @property
    def component_schema(self) -> TypeKey:
        return GAUGE.schema

    @property
    def family(self) -> FieldFamily:
        return VALUE

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        if not isinstance(before, GaugeRecord) or not isinstance(patch, GaugePatch):
            raise ValueError("patch class")
        return replace(before, value=patch.value)


class GaugeReducer:
    @property
    def schema(self) -> TypeKey:
        return key("gauge-delta")

    @property
    def owner_id(self) -> str:
        return "fixture.adjuster"

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        if not isinstance(delta, GaugeDelta) or before.component(GAUGE, delta.subject).value != delta.before_value:
            raise CandidateError("INVALID_DELTA", "old gauge value")
        editor.apply_patch(ComponentAddress(GAUGE.schema, delta.subject), GaugePatch(delta.after_value))

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes or any(not isinstance(d, GaugeDelta) for d in changes):
            raise CandidateError("INVALID_DELTA", "gauge composition")
        first, last = changes[0], changes[-1]
        assert isinstance(first, GaugeDelta) and isinstance(last, GaugeDelta)
        for before, after in zip(changes, changes[1:]):
            assert isinstance(before, GaugeDelta) and isinstance(after, GaugeDelta)
            if before.target != after.target or before.after_value != after.before_value:
                raise CandidateError("INVALID_DELTA", "noncontiguous gauge composition")
        return replace(first, after_value=last.after_value)

    def is_identity(self, delta: StateDelta) -> bool:
        if not isinstance(delta, GaugeDelta):
            raise CandidateError("INVALID_DELTA", "gauge delta class")
        GaugePayloadCodec(self.schema).encode(delta)
        return delta.before_value == delta.after_value

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        if not isinstance(delta, GaugeDelta) or self.is_identity(delta) or after.component(GAUGE, delta.subject).value != delta.after_value:
            raise CandidateError("INVALID_DELTA", "gauge committed value")


class GaugeAdmission:
    @property
    def schema(self) -> TypeKey:
        return key("adjust")

    @property
    def reads(self) -> tuple[FieldFamily, ...]:
        return (VALUE,)

    def admit(self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str) -> AdmissionOutcome:
        if not isinstance(command.payload, AdjustCommand) or not -9 <= state.component(GAUGE, command.actor_id).value + command.payload.amount <= 9:
            return TurnRejected(failure("INVALID_COMMAND"), command.expected_revision)
        target = Tick(start_tick + 1)
        semantic = hashlib.sha256(pack(("fixture-action/v1", world_id, str(target), command.actor_id, str(command.payload.amount)))).hexdigest()
        return AdmittedCommand(TurnPlan(command, start_tick, target), AdmittedAction(command.actor_id, command.payload, semantic))


@dataclass
class GaugeEngine:
    phase: Phase = Phase.RESOLVE
    retained: GaugeRead | None = None

    @property
    def manifest(self) -> CapabilityManifest:
        access = PhaseAccess(self.phase, VALUE)
        return CapabilityManifest("fixture.adjuster", (self.phase,), (access,), (access,), (), (key("gauge-changed"),), (), "constant")

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        assert invocation.action is not None and isinstance(invocation.action.payload, AdjustCommand)
        subject = invocation.action.actor_id
        view = invocation.state.component(GAUGE, subject)
        self.retained = view
        before, after = view.value, view.value + invocation.action.payload.amount
        return EngineResult((GaugeDelta(subject, before, after),),
                            (EmittedFact(GaugeChanged(subject, before, after), invocation.logical_tick, ()),), ())


class GaugePolicy:
    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        if len(core.components) != 1 or core.components[0].schema != GAUGE.schema or core.components[0].entity_id != ACTOR or any(s.actor_id != ACTOR for s in protocol.streams):
            raise ValueError("required gauge/actor membership")


class GaugePresenter:
    def __init__(self) -> None:
        self.retained: GaugeRead | None = None

    def map(self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt, committed: ReadPort) -> tuple[PresentationEvent, ...]:
        cues: list[PresentationEvent] = []
        for fact in facts:
            assert isinstance(fact.payload, GaugeChanged)
            p = fact.payload
            self.retained = committed.component(GAUGE, p.subject)
            assert self.retained.value == p.after_value and self.retained.label == "계기"
            cue = GaugeCue(p.subject, p.before_value, p.after_value)
            identifier = "p1-" + hashlib.sha256(pack(("cue-id/v1", fact.header.event_id, "fixture.presenter", str(len(cues))))).hexdigest()
            header = EventHeader(EventId(identifier), cue.schema, "fixture.presenter", receipt.tick, Phase.PRESENT, 0, 0, len(cues), (fact.header.event_id,), ())
            cues.append(PresentationEvent(header, cue, "important", "keep_all", ""))
        return tuple(cues)


# New test requirements, independent of the Phase0 schema and rules literals.
SCHEMA = b'{"version":1,"components":[{"schema":{"kind":"fixture.gauge","version":1},"fields":{"value":{"minimum":-9,"maximum":9,"owner":"fixture.adjuster","storage":"CORE","tier":"A","unit":"count","scale":1},"label":{"owner":"system.bootstrap","storage":"CORE","tier":"A","unit":"utf8","scale":1,"maximum_bytes":64}}}],"payloads":[{"schema":{"kind":"fixture.adjust","version":1},"fields":["amount"]},{"schema":{"kind":"fixture.gauge-delta","version":1},"fields":["subject","before_value","after_value"]},{"schema":{"kind":"fixture.gauge-changed","version":1},"fields":["subject","before_value","after_value"]},{"schema":{"kind":"fixture.gauge-cue","version":1},"fields":["subject","before_value","after_value"]},{"schema":{"kind":"fixture.gauge-patch","version":1},"fields":["value"]}]}'
RULES = b'{"version":1,"actor_id":"actor:sample","duration_seconds":1,"amount_range":[-3,3],"value_range":[-9,9],"initial_value":2,"blocked":"reject","record_only":true}'


def bundle(phase: Phase = Phase.RESOLVE) -> FeatureBundle:
    engine = GaugeEngine(phase)
    return FeatureBundle("fixture.gauge", (EngineBinding(engine, "tests.unit.registered_io_fixtures", (
        NodeActivation(NodeKey(phase, "fixture.adjuster"), (key("adjust"),), False, False, "A"),)),),
        (AdapterBinding(GaugeAdapter()),),
        (FieldSpec(VALUE, "CORE", "A", "fixture.adjuster", ("fixture.adjuster", "fixture.presenter"), "integer", "count", 1, -9, 9, None),
         FieldSpec(LABEL, "CORE", "A", "system.bootstrap", ("fixture.presenter",), "string", "utf8", 1, None, None, None)),
        (EventPolicy(key("gauge-changed"), "record_only", Phase.PRESENT, 0, "reject", ("fixture.adjuster",), (), ()),),
        (GaugeAdmission(),), (GaugeReducer(),), (PresenterBinding("fixture.presenter", (key("gauge-changed"),), GaugePresenter()),),
        tuple(GaugePayloadCodec(key(k)) for k in ("adjust", "gauge-delta", "gauge-changed", "gauge-cue", "gauge-patch")),
        object_value(decode_json(SCHEMA)), object_value(decode_json(RULES)), (GaugeCodec(),), (GaugePatchRoute(),), GaugePolicy())


def command(sequence: int = 1, amount: int = 3, revision: int = 0) -> GameCommand:
    return GameCommand(CommandId(f"c1:{'0'*32}:{'1'*32}:{sequence}"), ACTOR, WorldRevision(revision), AdjustCommand(amount))


def session(selected: FeatureBundle | None = None, value: int = 2) -> HeadlessSession:
    selected = bundle() if selected is None else selected
    io = state_io((selected,))
    seed = "0" * 64
    world = "w1-" + hashlib.sha256(pack(("world-id/v1", seed, io.pins.rules_fingerprint, io.pins.gameplay_catalog_hash))).hexdigest()
    core = CoreSnapshot(world, seed, Tick(0), (GaugeRecord(ACTOR, value, "계기"),), (), io.pins)
    protocol = ProtocolSnapshot("0" * 32, WorldRevision(0), (StreamCursor("1" * 32, ACTOR, 0, "active"),), ())
    return restore_checkpoint(core, protocol, bundles=(selected,))


def reference_body(*, first_value: int = 5) -> bytes:
    """Requirements-authored full trace; stdlib JSON/SHA256 only, never runtime outputs.

    The first_value override deliberately creates a self-consistent wrong witness.
    The fixed flow is 2+3=5, 5-3=2, retry1, stale3, conflict1.
    """
    def canon(value: object) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def frame(*tokens: str) -> bytes:
        result = b""
        for token in tokens:
            raw = token.encode("utf-8")
            result += len(raw).to_bytes(4, "big") + raw
        return result

    def digest(tag: str, value: object) -> str:
        return hashlib.sha256(frame(tag, canon(value))).hexdigest()

    def schema(kind: str) -> dict[str, object]:
        return {"kind": "fixture." + kind, "version": 1}

    schedule = {"version": 1, "nodes": [{"phase": "RESOLVE", "engine_id": "fixture.adjuster", "lane": "A",
        "reads": ["fixture.gauge.value"], "writes": ["fixture.gauge.value"], "depends_on": [], "action_kinds": [schema("adjust")],
        "on_matching_events": False, "every_tick": False, "emits": [schema("gauge-changed")], "consumes": [], "cost_class": "constant"}]}
    rules_hash, catalog = digest("rules/v1", json.loads(RULES)), digest("gameplay-catalog/v1", [])
    pins = {"schema_fingerprint": digest("schema/v1", json.loads(SCHEMA)), "rules_fingerprint": rules_hash,
        "schedule_fingerprint": digest("schedule/v1", schedule), "rng_version": "sha256-counter-v1", "hash_version": "sha256-core-tree-v1",
        "gameplay_catalog_hash": catalog, "gameplay_packages": []}
    world = "w1-" + hashlib.sha256(frame("world-id/v1", "0"*64, rules_hash, catalog)).hexdigest()

    def core(tick: int, value: int) -> dict[str, object]:
        return {"world_id": world, "world_seed_hex": "0"*64, "tick": tick, "components": [{"schema": schema("gauge"),
            "entity_id": "actor:sample", "fields": {"value": value, "label": "계기"}}], "pending": [], "pins": pins}

    def corehash(tick: int, value: int) -> str:
        doc = core(tick, value)
        component = {"schema": schema("gauge"), "entity_id": "actor:sample", "fields": {"value": value, "label": "계기"}}
        return digest("core-root/v1", {**doc, "components": [{"schema": schema("gauge"), "entity_id": "actor:sample", "hash": digest("component/v1", component)}]})

    def cmd(seq: int, amount: int, revision: int) -> dict[str, object]:
        return {"command_id": f"c1:{'0'*32}:{'1'*32}:{seq}", "actor_id": "actor:sample", "expected_revision": revision, "schema": schema("adjust"), "payload": {"amount": amount}}

    receipts: list[dict[str, object]] = []

    def protocol(revision: int) -> dict[str, object]:
        return {"branch_id": "0"*32, "revision": revision, "streams": [{"stream_id": "1"*32, "actor_id": "actor:sample", "highest_committed_sequence": revision, "status": "active"}], "receipts": list(receipts)}

    initial_core, initial_protocol = core(0, 2), protocol(0)
    header = {"world_id": world, "world_seed_hex": "0"*64, "initial_core_hash": corehash(0, 2), "initial_protocol_hash": digest("protocol/v1", initial_protocol),
        "schema_fingerprint": pins["schema_fingerprint"], "rules_fingerprint": rules_hash, "schedule_fingerprint": pins["schedule_fingerprint"],
        "rng_version": pins["rng_version"], "hash_version": pins["hash_version"], "gameplay_packages": [], "build_artifacts": []}
    steps: list[dict[str, object]] = []
    for index, (seq, amount, expected_rev) in enumerate(((1, 3, 0), (2, -3, 1), (1, 3, 0), (3, 1, 0), (1, -3, 0))):
        command_doc = cmd(seq, amount, expected_rev)
        facts: list[dict[str, object]] = []
        diff: object = None
        if index < 2:
            tick, old, value = index + 1, (2 if index == 0 else first_value), (first_value if index == 0 else 2)
            receipt = {"command_id": command_doc["command_id"], "previous_revision": index, "revision": tick, "tick": tick, "core_hash": corehash(tick, value)}
            receipts.append({"command": command_doc, "command_fingerprint": digest("command/v1", {k: v for k, v in command_doc.items() if k != "command_id"}), "receipt": receipt})
            outcome: dict[str, object] = {"kind": "committed", "receipt": receipt}
            identifier = "e1-" + hashlib.sha256(frame("event-id/v1", world, str(tick), "RESOLVE", "0", "fixture.adjuster", "0")).hexdigest()
            payload = {"subject": "actor:sample", "before_value": old, "after_value": value}
            facts = [{"header": {"event_id": identifier, "type_key": schema("gauge-changed"), "producer_id": "fixture.adjuster", "occurred_at": tick,
                "phase": "RESOLVE", "wave": 0, "producer_rank": 0, "sequence": 0, "caused_by": [], "degraded": []}, "due_tick": tick, "payload": payload}]
            diff = {"receipt": receipt, "changes": [{"schema": schema("gauge-delta"), **payload}]}
        else:
            tick, value = 2, 2
            if index == 2:
                outcome = {"kind": "committed", "receipt": receipts[0]["receipt"]}
            else:
                code = "STALE_REVISION" if index == 3 else "COMMAND_ID_CONFLICT"
                outcome = {"kind": "rejected", "failure": {"code": code, "message_key": "error." + code.lower()}, "current_revision": 2}
        core_doc, protocol_doc = core(tick, value), protocol(tick)
        steps.append({"command": command_doc, "outcome": outcome, "core_hash": corehash(tick, value), "protocol_hash": digest("protocol/v1", protocol_doc),
            "facts_hash": digest("turn-facts/v1", facts), "diff_hash": digest("turn-diff/v1", diff), "witness": {"core": core_doc, "protocol": protocol_doc, "facts": facts, "diff": diff}})
    return canon({"format_version": 1, "initial_core": initial_core, "initial_protocol": initial_protocol, "trace": {"header": header, "steps": steps}}).encode("utf-8")
