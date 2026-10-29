from __future__ import annotations

from dataclasses import asdict, fields, is_dataclass
from collections.abc import Mapping
import hashlib
import re
from types import MappingProxyType
from typing import cast
from functools import lru_cache

from contracts.events import ExecutionLimits, QueuedEvent
from contracts.dialogue import QuestConsumer, QuestContent
from contracts.errors import BootstrapError, CandidateError, SchemaError
from contracts.messages import CommandPayload, EventHeader, FactPayload, PresentationPayload, StateDelta, WorldEvent
from contracts.read_views import AdapterBinding, ComponentPatch, ViewEpoch
from domain.scenario import scenario_document, Scenario, ScenarioConsumer
from contracts.replay import PackagePin
from contracts.skeleton import FeatureBundle
from contracts.state_io import CoreEncoding, CheckpointEncoding
from contracts.turn import (CommitReceipt, CompiledSchedule, Failure, GameCommand, NodeKey,
    ProtocolSnapshot, StoredReceipt, StreamCursor, TurnAborted, TurnCommitted, TurnOutcome,
    TurnPublication, TurnRejected)
from domain.canonical import (JsonObject, JsonValue, CanonicalDocument, array_value, canonical_json, decode_json, exact_fields,
    hash_document, int_value, object_value, pack, seal, text_value, tagged_hash)
from domain.primitives import (CommandId, ComponentAddress, EntityId, FieldAddress, FieldSpec, FrozenPayload,
    EventId, Phase, Tick, TypeKey, WorldRevision, require_integer, require_namespace)
from domain.state_types import ComponentRecord, CoreSnapshot, PendingDocument, SimulationPins, StoredRoot
from orchestration.read_views import ObservedReadViewFactory

def key_document(key: TypeKey) -> JsonObject:
    return {"kind": key.kind, "version": key.version}


def decode_key(value: JsonValue) -> TypeKey:
    data = exact_fields(value, ("kind", "version"))
    return TypeKey(text_value(data["kind"]), int_value(data["version"]))


def _number(value: JsonValue, minimum: int = 0) -> int:
    result = int_value(value)
    require_integer(result, minimum)
    return result


_HEX64 = re.compile(r"[0-9a-f]{64}")
_HEX32 = re.compile(r"[0-9a-f]{32}")
_COMMAND_ID = re.compile(r"c1:([0-9a-f]{32}):([0-9a-f]{32}):([1-9][0-9]*)")


def _hex(value: JsonValue, size: int = 64) -> str:
    result = text_value(value)
    matched = (_HEX64.fullmatch(result) if size == 64 else _HEX32.fullmatch(result)
               if size == 32 else re.fullmatch(f"[0-9a-f]{{{size}}}", result))
    if matched is None:
        raise ValueError("invalid lowercase hex")
    return result


def _namespace(value: JsonValue) -> str:
    result = text_value(value)
    require_namespace(result)
    return result


def _packages(value: JsonValue) -> tuple[PackagePin, ...]:
    packages: list[PackagePin] = []
    for item in array_value(value):
        d = exact_fields(item, ("package_id", "version", "sha256"))
        packages.append(PackagePin(_namespace(d["package_id"]), _number(d["version"], 1), _hex(d["sha256"])))
    if len({p.package_id for p in packages}) != len(packages):
        raise ValueError("duplicate package")
    if packages != sorted(packages, key=lambda p: p.package_id):
        raise ValueError("unsorted package pins")
    return tuple(packages)


def _command_parts(identifier: str) -> tuple[str, str, int]:
    match = _COMMAND_ID.fullmatch(identifier)
    if match is None:
        raise ValueError("invalid command identity")
    sequence = int(match[3])
    require_integer(sequence, 1)
    return match[1], match[2], sequence


def _receipt(value: JsonValue) -> CommitReceipt:
    d = exact_fields(value, ("command_id", "previous_revision", "revision", "tick", "core_hash"))
    identifier = text_value(d["command_id"])
    _command_parts(identifier)
    old, revision = _number(d["previous_revision"]), _number(d["revision"], 1)
    if revision != old + 1:
        raise ValueError("receipt revision transition")
    return CommitReceipt(CommandId(identifier), WorldRevision(old), WorldRevision(revision),
                         Tick(_number(d["tick"], 1)), _hex(d["core_hash"]))


def _outcome(value: JsonValue) -> TurnOutcome:
    d = object_value(value)
    kind = text_value(d["kind"])
    if kind == "committed":
        d = exact_fields(d, ("kind", "receipt"))
        return TurnCommitted(_receipt(d["receipt"]))
    if kind not in ("rejected", "aborted"):
        raise ValueError("unsupported outcome")
    d = exact_fields(d, ("kind", "failure", "current_revision") if kind == "rejected" else ("kind", "failure"))
    f = exact_fields(d["failure"], ("code", "message_key"))
    code = text_value(f["code"])
    if re.fullmatch("[A-Z][A-Z0-9_]*", code) is None or f["message_key"] != "error." + code.lower():
        raise ValueError("invalid failure")
    failure = Failure(code, text_value(f["message_key"]))
    if kind == "rejected":
        revision = None if d["current_revision"] is None else WorldRevision(_number(d["current_revision"]))
        return TurnRejected(failure, revision)
    return TurnAborted(failure)


def receipt_document(receipt: CommitReceipt) -> JsonObject:
    return {"command_id": receipt.command_id, "previous_revision": receipt.previous_revision,
            "revision": receipt.revision, "tick": receipt.tick, "core_hash": receipt.core_hash}


def hash_core_document(document: JsonObject) -> str:
    return _hash_core_documents(document)


def _hash_core_documents(document: JsonObject, components: tuple[CanonicalDocument, ...] | None = None,
                         queue: tuple[CanonicalDocument, ...] | None = None) -> str:
    leaves: list[JsonValue] = []
    for index, child in enumerate(array_value(document["components"])):
        component = object_value(child)
        schema, entity = component["schema"], component["entity_id"]
        body = canonical_json(component) if components is None else components[index].to_bytes()
        leaves.append({"schema": schema, "entity_id": entity,
                       "hash": tagged_hash("component/v1", body)})
    pending: list[JsonValue] = []
    for index, child in enumerate(array_value(document["pending"])):
        q = object_value(child)
        header = object_value(object_value(q["event"])["header"])
        event_id = header["event_id"]
        body = canonical_json(q) if queue is None else queue[index].to_bytes()
        pending.append({"event_id": event_id, "hash": tagged_hash("pending-event/v1", body)})
    root = CanonicalDocument({**document, "components": tuple(leaves), "pending": tuple(pending)})
    return tagged_hash("core-root/v1", root.to_bytes())


def header_document(header: EventHeader) -> JsonObject:
    return {"event_id": header.event_id, "type_key": key_document(header.type_key),
            "producer_id": header.producer_id, "occurred_at": header.occurred_at,
            "phase": header.phase.name, "wave": header.wave, "producer_rank": header.producer_rank,
            "sequence": header.sequence, "caused_by": header.caused_by,
            "degraded": tuple({"producer_id": d.producer_id, "code": d.code} for d in header.degraded)}


@lru_cache(maxsize=128)
def _frozen_field_names(kind: type[object]) -> tuple[str, ...]:
    if not is_dataclass(kind):
        raise ValueError("record class is not a dataclass")
    return tuple(field.name for field in fields(kind))


def _immutable(value: object, depth: int = 0) -> None:
    if depth > 32:
        raise ValueError("record nesting exceeds32")
    kind = type(value)
    if value is None or kind in (bool, int, str):
        # Preserve the legacy seal path for types with custom equality.
        if value is not None and kind is not bool and kind is not int:
            seal(value)
    elif isinstance(value, tuple):
        for child in value:
            _immutable(child, depth + 1)
    elif isinstance(value, MappingProxyType):
        for key, child in value.items():
            seal(key)
            _immutable(child, depth + 1)
    elif is_dataclass(value) and not isinstance(value, type) and getattr(value, "__dataclass_params__").frozen:
        for name in _frozen_field_names(type(value)):
            _immutable(getattr(value, name), depth + 1)
    else:
        raise ValueError("mutable or unsupported record child")



def _validate_scenario_binding(bundle: FeatureBundle) -> None:
    descriptor = bundle.rules_document
    if "scenario" not in descriptor and "encounter" in descriptor:
        descriptor = object_value(descriptor["encounter"])
    if "scenario" not in descriptor:
        return  # Legacy feature descriptors have no selected-scenario extension.
    expected = canonical_json(object_value(descriptor["scenario"]))
    consumers: tuple[object, ...] = (
        *(b.engine for b in bundle.bindings),
        *(r.adapter if isinstance(r, AdapterBinding) else r for r in bundle.read_adapters),
        *bundle.command_routes, *bundle.delta_routes,
        *(p.presenter for p in bundle.presenters), *bundle.codecs,
        *bundle.component_codecs, *bundle.patch_routes, bundle.checkpoint_policy,
    )
    for consumer in consumers:
        if isinstance(consumer, ScenarioConsumer):
            layout = consumer.scenario_layout
            if type(layout) is not Scenario or canonical_json(scenario_document(layout)) != expected:
                raise BootstrapError("INVALID_SCENARIO_BINDING", type(consumer).__name__)


def _validate_quest_binding(bundle: FeatureBundle) -> None:
    roles: list[tuple[str, object]] = []
    roles.extend(("engine:" + b.engine.manifest.engine_id, b.engine) for b in bundle.bindings
                 if b.engine.manifest.engine_id.startswith("quest."))
    roles.extend(("adapter:" + r.schema.kind, r.adapter if isinstance(r, AdapterBinding) else r)
                 for r in bundle.read_adapters if r.schema.kind.startswith("quest."))
    for category, routes in (("admission", bundle.command_routes), ("reducer", bundle.delta_routes),
                            ("patch", bundle.patch_routes), ("component", bundle.component_codecs),
                            ("payload", bundle.codecs)):
        roles.extend((category + ":" + r.schema.kind, r) for r in routes
                     if r.schema.kind.startswith("quest."))
    roles.extend(("presenter:" + p.presenter_id, p.presenter) for p in bundle.presenters
                 if p.presenter_id.startswith("quest."))
    present = bool(roles) or any(p.schema.kind.startswith("quest.") for p in bundle.events) or any(
        spec.family.component.startswith("quest.") for spec in bundle.field_specs
    )
    if ("quest" in bundle.rules_document) != present:
        raise BootstrapError("INVALID_QUEST_BINDING", "quest declaration/registration mismatch")
    if not present:
        return
    quest = object_value(bundle.rules_document["quest"])
    expected_roles = tuple(text_value(v) for v in array_value(quest["consumer_roles"]))
    expected_definition = canonical_json(quest["definition"])
    expected_catalog = hashlib.sha256(canonical_json(bundle.rules_document["dialogue"])).hexdigest()
    roles.append(("checkpoint:quest.progress", bundle.checkpoint_policy))
    if tuple(sorted(role for role, _ in roles)) != expected_roles:
        raise BootstrapError("INVALID_QUEST_BINDING", "required quest consumer roles")
    for role, consumer in roles:
        if not isinstance(consumer, QuestConsumer):
            raise BootstrapError("INVALID_QUEST_BINDING", role + ":missing property")
        try:
            content = consumer.quest_content
        except AttributeError as error:
            raise BootstrapError("INVALID_QUEST_BINDING", role + ":uninitialized") from error
        if (type(content) is not QuestContent
                or canonical_json(seal({**asdict(content.definition), "layout": scenario_document(content.definition.layout)})) != expected_definition
                or content.catalog_sha256 != expected_catalog):
            raise BootstrapError("INVALID_QUEST_BINDING", role + ":mismatch")


class RegisteredStateIO:
    def __init__(self, bundles: tuple[FeatureBundle, ...], schedule: CompiledSchedule) -> None:
        from orchestration.turn import validate_registry
        if len(bundles) != 1:
            raise BootstrapError("DUPLICATE_SCHEMA", "one feature bundle required")
        bindings = tuple(b for f in bundles for b in f.bindings)
        if set(schedule.nodes) != {a.node for b in bindings for a in b.activations} or len(schedule.nodes) != sum(len(b.activations) for b in bindings):
            raise BootstrapError("INVALID_ACTIVATION", "registered schedule differs")
        validate_registry(bundles, schedule)
        bundle = bundles[0]
        _validate_quest_binding(bundle)
        _validate_scenario_binding(bundle)
        self._schedule = schedule
        self._registrations = tuple(bundle.read_adapters)
        self._component_registrations = (
            MappingProxyType({r.schema: r for r in self._registrations})
            if all(type(r) is AdapterBinding for r in self._registrations) else None
        )
        self._policy = bundle.checkpoint_policy
        self._components = MappingProxyType({c.schema: c for c in bundle.component_codecs})
        self._payloads = MappingProxyType({c.schema: c for c in bundle.codecs})
        self._patches = MappingProxyType({p.schema: p for p in bundle.patch_routes})
        self._deltas = MappingProxyType({r.schema: r for r in bundle.delta_routes})
        self._commands = frozenset(r.schema for r in bundle.command_routes)
        self._fields = MappingProxyType({s.family: s for s in bundle.field_specs})
        self._events = MappingProxyType({p.schema: p for p in bundle.events})
        self._manifests = MappingProxyType({b.engine.manifest.engine_id: b.engine.manifest for b in bindings})
        self._active = MappingProxyType({a.node: a for b in bindings for a in b.activations})
        self._presenters = MappingProxyType({p.presenter_id: p for p in bundle.presenters})
        if len(self._presenters) != len(bundle.presenters):
            raise BootstrapError("DUPLICATE_SCHEMA", "presenter identity")
        if not (set(self._commands) | set(self._deltas)).issubset(self._payloads):
            raise BootstrapError("DUPLICATE_SCHEMA", "route payload codec missing")
        if any(r.owner_id not in self._manifests for r in self._deltas.values()):
            raise BootstrapError("WRITE_CONFLICT", "reducer engine owner missing")
        for schemas, count in ((self._components, len(bundle.component_codecs)),
                               (self._patches, len(bundle.patch_routes))):
            if len(schemas) != count:
                raise BootstrapError("DUPLICATE_SCHEMA", "duplicate codec/patch")
        kinds = {k.kind for k in self._components}
        if len(kinds) != len(self._components) or not kinds:
            raise BootstrapError("DUPLICATE_SCHEMA", "component kind/version")
        if set(self._components) != {a.schema for a in self._registrations} or kinds != {f.component for f in self._fields}:
            raise BootstrapError("DUPLICATE_SCHEMA", "component codec/adapter/field coverage")
        families = [p.family for p in self._patches.values()]
        if len(set(families)) != len(families):
            raise BootstrapError("WRITE_CONFLICT", "duplicate patch family")
        for spec in self._fields.values():
            if spec.owner_id == "system.bootstrap":
                if spec.family in families or any(a.family == spec.family for m in self._manifests.values() for a in m.writes):
                    raise BootstrapError("WRITE_CONFLICT", "immutable bootstrap field writer")
            elif spec.owner_id not in self._manifests or spec.family not in families or not any(
                a.family == spec.family for a in self._manifests[spec.owner_id].writes
            ):
                raise BootstrapError("WRITE_CONFLICT", "mutable field owner/patch missing")
            try:
                require_integer(spec.scale, 1)
                if spec.collection_cap is not None:
                    require_integer(spec.collection_cap)
                for bound in (spec.minimum, spec.maximum):
                    if bound is not None:
                        require_integer(bound, -(2**63))
            except ValueError as error:
                raise BootstrapError("DUPLICATE_SCHEMA", "invalid field metadata integer") from error
            if spec.minimum is not None and spec.maximum is not None and spec.minimum > spec.maximum:
                raise BootstrapError("DUPLICATE_SCHEMA", "invalid field range")
            if spec.storage_class != "CORE" or spec.tier != "A" or not spec.unit:
                raise BootstrapError("DUPLICATE_SCHEMA", "unsupported component metadata")
        for patch in self._patches.values():
            patch_spec = self._fields.get(patch.family)
            if patch.component_schema not in self._components or patch.family.component != patch.component_schema.kind or patch_spec is None or patch.schema not in self._payloads:
                raise BootstrapError("DUPLICATE_SCHEMA", "patch component/field/codec")
            if not any(r.owner_id == patch_spec.owner_id for r in self._deltas.values()):
                raise BootstrapError("WRITE_CONFLICT", "patch reducer owner")
        try:
            self._schema_document = object_value(seal(bundle.schema_document))
            self._rules_document = object_value(seal(bundle.rules_document))
            # Runtime registrations cannot silently change the behavior under unchanged pins.
            component_specs: dict[str, tuple[FieldSpec, ...]] = {}
            descriptors: dict[TypeKey, JsonObject] = {}
            for item in array_value(self._schema_document["components"]):
                child = exact_fields(item, ("schema", "fields"))
                schema = decode_key(child["schema"])
                if schema in descriptors:
                    raise BootstrapError("DUPLICATE_SCHEMA", "component descriptor")
                descriptors[schema] = object_value(child["fields"])
            if set(descriptors) != set(self._components):
                raise BootstrapError("DUPLICATE_SCHEMA", "descriptor/component registration differs")
            for schema, descriptor in descriptors.items():
                specs = tuple(s for f, s in self._fields.items() if f.component == schema.kind)
                component_specs[schema.kind] = specs
                if set(descriptor) != {s.family.field for s in specs}:
                    raise BootstrapError("DUPLICATE_SCHEMA", "descriptor field coverage")
                for spec in specs:
                    field = object_value(descriptor[spec.family.field])
                    metadata: JsonObject = {"owner": spec.owner_id, "storage": spec.storage_class,
                                           "tier": spec.tier, "scale": spec.scale, "unit": spec.unit}
                    if any(k not in field or canonical_json(field[k]) != canonical_json(v) for k, v in metadata.items()):
                        raise BootstrapError("DUPLICATE_SCHEMA", "descriptor field metadata differs")
                    if spec.value_kind == "integer" and (canonical_json(field.get("minimum")) != canonical_json(spec.minimum) or canonical_json(field.get("maximum")) != canonical_json(spec.maximum)):
                        raise BootstrapError("DUPLICATE_SCHEMA", "descriptor field bounds differ")
            payload_schemas = tuple(decode_key(object_value(p)["schema"]) for p in array_value(self._schema_document["payloads"]))
            if len(set(payload_schemas)) != len(payload_schemas) or set(payload_schemas) != set(self._payloads):
                raise BootstrapError("DUPLICATE_SCHEMA", "descriptor payload codec coverage")
        except BootstrapError:
            raise
        except (ValueError, TypeError, KeyError) as error:
            raise BootstrapError("DUPLICATE_SCHEMA", "malformed pinned descriptor/rules") from error
        self._component_specs = MappingProxyType(component_specs)
        self._configure_execution()
        # These frozen declarations do not depend on the decoded event or component state.
        a_nodes = (node for node in self._schedule.nodes if self._active[node].lane == "A")
        self._a_node_ranks = MappingProxyType({node: rank for rank, node in enumerate(a_nodes)})
        self._pins = SimulationPins(hash_document("schema/v1", self._schema_document),
                                    hash_document("rules/v1", self._rules_document), schedule.fingerprint,
                                    "sha256-counter-v1", "sha256-core-tree-v1",
                                    hash_document("gameplay-catalog/v1", ()), ())

    def _configure_execution(self) -> None:
        self._limits = ExecutionLimits(False, 1, 8, 512, 0)
        if "execution" not in self._rules_document:
            return
        try:
            d = exact_fields(self._rules_document["execution"], ("enable_simulation", "max_duration_seconds", "cascade_waves", "max_events_per_tick", "max_pending"))
            if d["enable_simulation"] is not True:
                raise ValueError("simulation must be enabled")
            numbers = tuple(int_value(d[k]) for k in ("max_duration_seconds", "cascade_waves", "max_events_per_tick", "max_pending"))
            for n, bound in zip(numbers, (16, 8, 512, 4096), strict=True):
                require_integer(n, 1, bound)
            self._limits = ExecutionLimits(True, *numbers)
            if canonical_json(self._schema_document.get("system")) != canonical_json({"clock_owner": "system.clock", "queue_owner": "system.events", "pending_format": "queued-event/v1"}):
                raise ValueError("system ownership")
            if any(engine in ("system.clock", "system.events") for engine in self._manifests) or any(a.family.component in ("system.clock", "system.events") for m in self._manifests.values() for a in m.writes):
                raise ValueError("reserved clock/queue owner")
            policies: list[JsonValue] = []
            for policy in sorted(self._events.values(), key=lambda p: (p.schema.kind, p.schema.version)):
                if policy.mode not in ("simulate", "record_only") or policy.late_route not in ("reject", "next_tick") or policy.cancellers:
                    raise ValueError("unsupported event policy")
                require_integer(policy.priority, 0, 255)
                if type(policy.delivery_phase) is not Phase or not policy.producers or len(set(policy.producers)) != len(policy.producers) or len(set(policy.subscribers)) != len(policy.subscribers):
                    raise ValueError("event policy identities")
                if policy.mode == "simulate" and policy.delivery_phase not in (Phase.PRE_TICK, Phase.RESOLVE, Phase.REACT, Phase.CASCADE, Phase.POST_TICK):
                    raise ValueError("simulation phase")
                for producer in policy.producers:
                    if any(self._active[NodeKey(p, producer)].lane != "A" for p in self._manifests[producer].phases):
                        raise ValueError("producer lane")
                for subscriber in policy.subscribers:
                    if self._active[NodeKey(policy.delivery_phase, subscriber)].lane != "A":
                        raise ValueError("subscriber lane")
                policies.append({"schema": key_document(policy.schema), "mode": policy.mode, "delivery_phase": policy.delivery_phase.name, "priority": policy.priority, "late_route": policy.late_route, "producers": tuple(sorted(policy.producers)), "subscribers": tuple(sorted(policy.subscribers)), "cancellers": ()})
            if canonical_json(tuple(policies)) != canonical_json(self._rules_document.get("event_policies")):
                raise ValueError("pinned policies differ")
            for node, active in self._active.items():
                for kind in self._manifests[node.engine_id].emits:
                    if node.engine_id not in self._events[kind].producers:
                        raise ValueError("unauthorized declared emission")
                if node.phase == Phase.CASCADE and active.every_tick:
                    raise BootstrapError("INVALID_ACTIVATION", "every-tick cascade unsupported")
                for kind in self._manifests[node.engine_id].consumes:
                    policy = self._events[kind]
                    if node.engine_id not in policy.subscribers or not any(p == policy.delivery_phase for p in self._manifests[node.engine_id].phases):
                        raise ValueError("unsubscribed consume")
        except BootstrapError:
            raise
        except (ValueError, TypeError, KeyError) as error:
            raise BootstrapError("INVALID_EVENT_POLICY", str(error)) from error

    @property
    def execution_limits(self) -> ExecutionLimits:
        return self._limits

    def _event(self, value: JsonValue) -> WorldEvent:
        f = exact_fields(value, ("header", "due_tick", "payload"))
        h = exact_fields(f["header"], ("event_id", "type_key", "producer_id", "occurred_at", "phase", "wave", "producer_rank", "sequence", "caused_by", "degraded"))
        schema = decode_key(h["type_key"])
        payload = self._decode_payload(schema, object_value(f["payload"]))
        producer = _namespace(h["producer_id"])
        try:
            phase = Phase[text_value(h["phase"])]
        except KeyError as error:
            raise ValueError("unknown event phase") from error
        node = NodeKey(phase, producer)
        nodes = self._a_node_ranks
        policy = self._events.get(schema)
        rank, wave, sequence = _number(h["producer_rank"]), _number(h["wave"]), _number(h["sequence"])
        if not isinstance(payload, FactPayload) or policy is None or producer not in policy.producers or node not in nodes or schema not in self._manifests[producer].emits or rank != nodes[node]:
            raise ValueError("unregistered event producer/rank")
        if (phase != Phase.CASCADE and wave != 0) or wave >= self._limits.cascade_waves or array_value(h["degraded"]):
            raise ValueError("event wave/degradation")
        identifier = text_value(h["event_id"])
        causes = tuple(EventId(text_value(c)) for c in array_value(h["caused_by"]))
        if re.fullmatch("e1-[0-9a-f]{64}", identifier) is None or causes != tuple(sorted(set(causes))) or identifier in causes or any(re.fullmatch("e1-[0-9a-f]{64}", c) is None for c in causes):
            raise ValueError("event identity/causes")
        tick, due = Tick(_number(h["occurred_at"])), Tick(_number(f["due_tick"]))
        if due < tick or (policy.mode == "record_only" and due != tick):
            raise ValueError("event due tick")
        return WorldEvent(EventHeader(EventId(identifier), schema, producer, tick, phase, wave, rank, sequence, causes, ()), due, payload)

    def _event_identity(self, event: WorldEvent, world_id: str) -> None:
        h = event.header
        identifier = "e1-" + hashlib.sha256(pack(("event-id/v1", world_id, str(h.occurred_at), h.phase.name, str(h.wave), h.producer_id, str(h.sequence)))).hexdigest()
        if h.event_id != identifier:
            raise ValueError("event identity")

    def encode_pending(self, event: QueuedEvent) -> PendingDocument:
        if type(event) is not QueuedEvent or type(event.event) is not WorldEvent or type(event.event.header) is not EventHeader or type(event.delivery_phase) is not Phase:
            raise ValueError("pending DTO class")
        h = event.event.header
        value: JsonObject = {"event": {"header": header_document(h), "due_tick": event.event.due_tick, "payload": self.encode_payload(event.event.payload)}, "delivery_phase": event.delivery_phase.name, "priority": event.priority}
        document = PendingDocument(canonical_json(value))
        if self.decode_pending(document) != event:
            raise ValueError("pending roundtrip")
        return document

    def decode_pending(self, document: PendingDocument) -> QueuedEvent:
        if not self._limits.enable_simulation or type(document) is not PendingDocument or type(document.canonical_event_json) is not bytes:
            raise SchemaError("UNSUPPORTED_SCHEMA", "pending")
        d = exact_fields(decode_json(document.canonical_event_json), ("event", "delivery_phase", "priority"))
        if canonical_json(d) != document.canonical_event_json:
            raise ValueError("noncanonical pending")
        event = self._event(d["event"])
        policy = self._events[event.header.type_key]
        try:
            phase = Phase[text_value(d["delivery_phase"])]
        except KeyError as error:
            raise ValueError("unknown delivery phase") from error
        priority = _number(d["priority"])
        if policy.mode != "simulate" or phase != policy.delivery_phase or priority != policy.priority or event.due_tick <= event.header.occurred_at:
            raise ValueError("pending routing")
        return QueuedEvent(event, phase, priority)

    @property
    def pins(self) -> SimulationPins:
        return self._pins

    @property
    def schedule(self) -> CompiledSchedule:
        return self._schedule

    def _factory(self, components: tuple[ComponentRecord, ...]) -> ObservedReadViewFactory:
        factory = ObservedReadViewFactory(StoredRoot(components, 0))
        for registration in self._registrations:
            registration.install(factory)
        return factory

    def _component_fields(self, record: ComponentRecord) -> JsonObject:
        return object_value(self._encode_component(record)[0].value)

    def _encode_component(self, record: ComponentRecord) -> tuple[CanonicalDocument, ComponentRecord]:
        codec = self._components.get(record.schema)
        if codec is None:
            raise SchemaError("UNSUPPORTED_SCHEMA", "core.component.schema")
        try:
            require_namespace(record.entity_id)
            _immutable(record)
            document = CanonicalDocument(codec.encode(record))
            data = object_value(document.value)
            specs = self._component_specs.get(record.schema.kind, ())
            exact_fields(data, tuple(s.family.field for s in specs))
            for spec in specs:
                value = data[spec.family.field]
                if spec.value_kind == "integer":
                    integer = int_value(value)
                    require_integer(integer, spec.minimum if spec.minimum is not None else -(2**63),
                                    spec.maximum if spec.maximum is not None else 2**63 - 1)
                elif spec.value_kind == "string":
                    text_value(value)
                if spec.collection_cap is not None and isinstance(value, (tuple, Mapping)) and len(value) > spec.collection_cap:
                    raise ValueError("component collection cap")
            decoded = codec.decode(record.entity_id, data)
            if type(decoded) is not type(record) or decoded.schema != record.schema or decoded.entity_id != record.entity_id:
                raise ValueError("component codec type/identity")
            _immutable(decoded)
            # The byte comparison validates and owns its JSON tree;no sealed temporary escapes.
            if canonical_json(object_value(codec.encode(decoded))) != document.to_bytes():
                raise ValueError("component codec is not lossless")
            if self._component_registrations is None:
                self._factory((record,))
            else:
                # Builtin bindings only install static metadata;record validation stays fresh.
                factory = ObservedReadViewFactory(StoredRoot((record,), 0))
                self._component_registrations[record.schema].install(factory)
            return document, decoded
        except (ValueError, TypeError, AttributeError) as error:
            raise SchemaError("INVALID_COMPONENT", "core.component.fields") from error

    def encode_core(self, core: CoreSnapshot) -> JsonObject:
        return object_value(self._encode_core(core)[0].value)

    def _encode_core(self, core: CoreSnapshot) -> tuple[CanonicalDocument, CoreSnapshot, tuple[CanonicalDocument, ...], tuple[CanonicalDocument, ...]]:
        StoredRoot(core.components, 0)
        require_integer(core.tick)
        seed = _hex(core.world_seed_hex)
        if core.pins != self.pins or (core.pending and not self._limits.enable_simulation):
            raise SchemaError("UNSUPPORTED_SCHEMA", "core.pins/pending")
        world_id = "w1-" + hashlib.sha256(pack(("world-id/v1", seed, self.pins.rules_fingerprint,
                                              self.pins.gameplay_catalog_hash))).hexdigest()
        if core.world_id != world_id:
            raise ValueError("world identity does not match seed/rules/catalog")
        from orchestration.events import queued_sort_key
        queue = tuple(self.decode_pending(d) for d in core.pending)
        if len(queue) > self._limits.max_pending or len({q.event.header.event_id for q in queue}) != len(queue) or queue != tuple(sorted(queue, key=queued_sort_key)):
            raise ValueError("pending cap/identity/order")
        for q in queue:
            self._event_identity(q.event, world_id)
            if not q.event.header.occurred_at <= core.tick < q.event.due_tick:
                raise ValueError("pending checkpoint time")
        p = self.pins
        components: list[CanonicalDocument] = []
        decoded: list[ComponentRecord] = []
        for record in core.components:
            fields, checked = self._encode_component(record)
            components.append(CanonicalDocument({"schema": key_document(record.schema),
                "entity_id": record.entity_id, "fields": fields}, children=(fields,)))
            decoded.append(checked)
        pending = tuple(CanonicalDocument(decode_json(d.canonical_event_json)) for d in core.pending)
        owned = CanonicalDocument({"world_id": core.world_id, "world_seed_hex": seed, "tick": core.tick,
            "components": tuple(components), "pending": pending, "pins": {"schema_fingerprint": p.schema_fingerprint,
                "rules_fingerprint": p.rules_fingerprint, "schedule_fingerprint": p.schedule_fingerprint,
                "rng_version": p.rng_version, "hash_version": p.hash_version,
                "gameplay_catalog_hash": p.gameplay_catalog_hash, "gameplay_packages": ()}},
            children=(*components, *pending))
        checked_core = CoreSnapshot(core.world_id, seed, core.tick, tuple(decoded),
                                   tuple(PendingDocument(q.to_bytes()) for q in pending), p)
        return owned, checked_core, tuple(components), pending


    def decode_core(self, document: JsonObject) -> CoreSnapshot:
        return self._decode_core_document(document)[0]

    def _decode_core_document(self, document: JsonObject) -> tuple[CoreSnapshot, CanonicalDocument]:
        d = exact_fields(seal(document), ("world_id", "world_seed_hex", "tick", "components", "pending", "pins"))
        components: list[ComponentRecord] = []
        for item in array_value(d["components"]):
            child = exact_fields(item, ("schema", "entity_id", "fields"))
            key = decode_key(child["schema"])
            codec = self._components.get(key)
            if codec is None:
                raise SchemaError("UNSUPPORTED_SCHEMA", "core.component.schema")
            try:
                entity = EntityId(_namespace(child["entity_id"]))
                record = codec.decode(entity, object_value(child["fields"]))
                if record.schema != key or record.entity_id != entity:
                    raise ValueError("decoded component identity")
                if canonical_json(self._component_fields(record)) != canonical_json(child["fields"]):
                    raise ValueError("component decoder coerced fields")
                components.append(record)
            except (ValueError, TypeError, AttributeError) as error:
                raise SchemaError("INVALID_COMPONENT", "core.component.fields") from error
        core = CoreSnapshot(text_value(d["world_id"]), _hex(d["world_seed_hex"]), Tick(_number(d["tick"])),
                            tuple(components), tuple(PendingDocument(canonical_json(q)) for q in array_value(d["pending"])), self.pins)
        encoded, _, _, _ = self._encode_core(core)
        if encoded.to_bytes() != canonical_json(d):
            raise ValueError("checkpoint pins/shape mismatch")
        return core, encoded

    def _decode_checkpoint(self, core: JsonObject, protocol: JsonObject) -> CheckpointEncoding:
        checked_core, core_document = self._decode_core_document(core)
        core_hash = hash_core_document(object_value(core_document.value))
        checked_protocol, protocol_document = self._decode_protocol_document(protocol, checked_core, head_hash=core_hash)
        return CheckpointEncoding(self, checked_core, checked_protocol, core_document, protocol_document, core_hash)

    def _validate_decoded_checkpoint(self, checkpoint: CheckpointEncoding) -> None:
        if checkpoint.owner is not self:
            raise ValueError("foreign decoded checkpoint")
        self._policy.validate(checkpoint.core, checkpoint.protocol)

    def _protocol_document(self, protocol: ProtocolSnapshot) -> CanonicalDocument:
        return cast(CanonicalDocument, self._encode_protocol(protocol, own=True)[0])

    def _encode_core_for_commit(self, core: CoreSnapshot) -> CoreEncoding:
        document, checked, components, pending = self._encode_core(core)
        core_hash = _hash_core_documents(object_value(document.value), components, pending)
        return CoreEncoding(self, core, checked, document, components, pending, core_hash)

    def hash_core(self, core: CoreSnapshot) -> str:
        return self._hash_core_encoding(self._encode_core_for_commit(core))

    def _hash_core_encoding(self, core: CoreEncoding) -> str:
        if core.owner is not self:
            raise ValueError("foreign core encoding")
        return core.core_hash

    def validate_checkpoint(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        self._validate_core_encoding(self._encode_core_for_commit(core), protocol)

    def _validate_core_encoding(self, core: CoreEncoding, protocol: ProtocolSnapshot) -> CheckpointEncoding:
        if core.owner is not self:
            raise ValueError("foreign core encoding")
        checked = core.checked
        self._factory(checked.components)
        document, commands = self._encode_protocol(protocol, own=True)
        verified = self._decode_protocol(document, checked, commands=commands, head_hash=core.core_hash)
        if verified != protocol:
            raise ValueError("protocol roundtrip mismatch")
        self._policy.validate(checked, verified)
        return CheckpointEncoding(self, core.source, protocol, core.document, cast(CanonicalDocument, document), core.core_hash)

    def _decode_payload(self, schema: TypeKey, data: JsonObject) -> FrozenPayload:
        if schema not in self._payloads:
            raise SchemaError("UNSUPPORTED_SCHEMA", "payload.schema")
        try:
            owned = CanonicalDocument(data)
        except (ValueError, TypeError, AttributeError) as error:
            raise SchemaError("INVALID_PAYLOAD", "payload") from error
        return self._decode_owned_payload(schema, owned)

    def _decode_owned_payload(self, schema: TypeKey, document: CanonicalDocument) -> FrozenPayload:
        # Only freshly owned DTOs from this conversion operation reach this helper.
        codec = self._payloads.get(schema)
        if codec is None:
            raise SchemaError("UNSUPPORTED_SCHEMA", "payload.schema")
        try:
            owned = object_value(document.value)
            payload = codec.decode(owned)
            _immutable(payload)
            if payload.schema != schema or canonical_json(object_value(codec.encode(payload))) != document.to_bytes():
                raise ValueError("payload codec identity/roundtrip")
            return payload
        except (ValueError, TypeError, AttributeError) as error:
            raise SchemaError("INVALID_PAYLOAD", "payload") from error

    def encode_payload(self, payload: FrozenPayload) -> JsonObject:
        return object_value(self._encode_payload(payload)[0].value)

    def _encode_payload(self, payload: FrozenPayload) -> tuple[CanonicalDocument, FrozenPayload]:
        codec = self._payloads.get(payload.schema)
        if codec is None:
            raise SchemaError("UNSUPPORTED_SCHEMA", "payload.schema")
        try:
            _immutable(payload)
            data = CanonicalDocument(codec.encode(payload))
            decoded = self._decode_owned_payload(payload.schema, data)
            if type(decoded) is not type(payload):
                raise ValueError("unsupported payload class")
            return data, decoded
        except (ValueError, TypeError, AttributeError) as error:
            raise SchemaError("INVALID_PAYLOAD", "payload") from error

    def encode_command(self, command: GameCommand) -> JsonObject:
        return object_value(self._encode_command(command)[0].value)

    def _encode_command(self, command: GameCommand) -> tuple[CanonicalDocument, GameCommand]:
        _command_parts(command.command_id)
        require_namespace(command.actor_id)
        require_integer(command.expected_revision)
        if command.payload.schema not in self._commands or not isinstance(command.payload, CommandPayload):
            raise SchemaError("UNSUPPORTED_SCHEMA", "command.schema")
        data, decoded = self._encode_payload(command.payload)
        if not isinstance(decoded, CommandPayload):
            raise SchemaError("INVALID_PAYLOAD", "command.payload")
        document = CanonicalDocument({"command_id": command.command_id, "actor_id": command.actor_id,
            "expected_revision": command.expected_revision, "schema": key_document(command.payload.schema),
            "payload": data}, children=(data,))
        return document, GameCommand(command.command_id, command.actor_id, command.expected_revision, decoded)

    def decode_command(self, document: JsonObject) -> GameCommand:
        return self._decode_command(document)[0]

    def _decode_command(self, document: JsonObject) -> tuple[GameCommand, CanonicalDocument]:
        d = exact_fields(seal(document), ("command_id", "actor_id", "expected_revision", "schema", "payload"))
        key = decode_key(d["schema"])
        if key not in self._commands:
            raise SchemaError("UNSUPPORTED_SCHEMA", "command.schema")
        payload = self._decode_owned_payload(key, CanonicalDocument(object_value(d["payload"])))
        if not isinstance(payload, CommandPayload):
            raise SchemaError("INVALID_PAYLOAD", "command.payload")
        command = GameCommand(CommandId(text_value(d["command_id"])), EntityId(_namespace(d["actor_id"])),
                              WorldRevision(_number(d["expected_revision"])), payload)
        encoded, _ = self._encode_command(command)
        return command, encoded

    def decode_outcome(self, document: JsonObject) -> TurnOutcome:
        return _outcome(seal(document))

    def apply_patch(self, address: ComponentAddress, allowed: FieldAddress,
                    before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        route = self._patches.get(patch.schema)
        if route is None:
            raise CandidateError("INVALID_DELTA", "unregistered patch")
        if route.component_schema != address.schema or route.family != allowed.family or address.entity_id != allowed.entity_id:
            raise CandidateError("UNDECLARED_WRITE", "patch target/field")
        if ComponentAddress(before.schema, before.entity_id) != address:
            raise CandidateError("INVALID_DELTA", "before address")
        try:
            old = self._component_fields(before)
            self.encode_payload(patch)
            after = route.apply(before, patch)
            if ComponentAddress(after.schema, after.entity_id) != address:
                raise ValueError("replacement address")
            new = self._component_fields(after)
            if canonical_json(self._component_fields(before)) != canonical_json(old):
                raise ValueError("patch mutated original")
            if any(canonical_json(old[k]) != canonical_json(new[k]) for k in old if k != allowed.family.field):
                raise CandidateError("UNDECLARED_WRITE", "patch changed another field")
            return after
        except (ValueError, TypeError, AttributeError) as error:
            raise CandidateError("INVALID_DELTA", "invalid patch replacement") from error

    def validate_effects(self, command: GameCommand, outcome: TurnOutcome, core: CoreSnapshot,
                         protocol: ProtocolSnapshot, facts: JsonValue, diff: JsonValue) -> None:
        self._validate_effects(command, outcome, core, protocol, facts, diff)

    def _validate_effects_encoding(self, checkpoint: CheckpointEncoding, command: GameCommand,
                                   outcome: TurnOutcome, facts: JsonValue, diff: JsonValue) -> None:
        if checkpoint.owner is not self:
            raise ValueError("foreign checkpoint encoding")
        self._validate_effects(command, outcome, checkpoint.core, checkpoint.protocol, facts, diff,
                               core_hash=checkpoint.core_hash)

    def _validate_effects(self, command: GameCommand, outcome: TurnOutcome, core: CoreSnapshot,
                         protocol: ProtocolSnapshot, facts: JsonValue, diff: JsonValue, *, core_hash: str | None = None) -> None:
        values = array_value(seal(facts))
        if len(values) > self._limits.max_events_per_tick * self._limits.max_duration_seconds:
            raise ValueError("fact cap")
        if isinstance(outcome, TurnCommitted):
            retained = next((r for r in protocol.receipts if r.command.command_id == command.command_id), None)
            if outcome.receipt.command_id != command.command_id or retained is None or retained.command != command or retained.receipt != outcome.receipt:
                raise ValueError("committed receipt absent/inconsistent")
        elif values or diff is not None:
            raise ValueError("failed submission cannot publish effects")
        if diff is None:
            if values:
                raise ValueError("facts without committed diff")
            return
        if not isinstance(outcome, TurnCommitted):
            raise ValueError("diff without commit")
        d = exact_fields(seal(diff), ("receipt", "changes"))
        if _receipt(d["receipt"]) != outcome.receipt or outcome.receipt.revision != protocol.revision or outcome.receipt.core_hash != (self.hash_core(core) if core_hash is None else core_hash) or outcome.receipt.tick != core.tick:
            raise ValueError("diff/head receipt inconsistent")
        if self._limits.enable_simulation:
            self._enabled_effects(command, core, values)
        else:
            a_nodes = self._a_node_ranks
            sequences: dict[NodeKey, int] = {}
            last_order = (-1, -1)
            for item in values:
                f = exact_fields(item, ("header", "due_tick", "payload"))
                h = exact_fields(f["header"], ("event_id", "type_key", "producer_id", "occurred_at", "phase", "wave",
                                              "producer_rank", "sequence", "caused_by", "degraded"))
                schema = decode_key(h["type_key"])
                payload = self._decode_payload(schema, object_value(f["payload"]))
                policy = self._events.get(schema)
                producer = _namespace(h["producer_id"])
                phase = Phase[text_value(h["phase"])]
                node = NodeKey(phase, producer)
                if not isinstance(payload, FactPayload) or policy is None or policy.mode != "record_only" or producer not in policy.producers or node not in a_nodes or schema not in self._manifests[producer].emits:
                    raise ValueError("unregistered fact producer/phase")
                active = self._active[node]
                if not (active.every_tick or command.payload.schema in active.action_kinds):
                    raise ValueError("inactive fact producer")
                rank, sequence = _number(h["producer_rank"]), _number(h["sequence"])
                if rank != a_nodes[node] or sequence != sequences.get(node, 0) or (rank, sequence) <= last_order:
                    raise ValueError("fact rank/order/sequence")
                sequences[node] = sequence + 1
                last_order = (rank, sequence)
                if _number(h["occurred_at"]) != core.tick or _number(f["due_tick"]) != core.tick or _number(h["wave"]) != 0 or array_value(h["caused_by"]) or array_value(h["degraded"]):
                    raise ValueError("fact timing/causes/degradation")
                identifier = "e1-" + hashlib.sha256(pack(("event-id/v1", core.world_id, str(core.tick), phase.name,
                                                          "0", producer, str(sequence)))).hexdigest()
                if h["event_id"] != identifier:
                    raise ValueError("fact identity")
        ordered: list[tuple[str, str, str]] = []
        for item in array_value(d["changes"]):
            change = object_value(item)
            schema = decode_key(change["schema"])
            delta = self._decode_payload(schema, {k: v for k, v in change.items() if k != "schema"})
            route = self._deltas.get(schema)
            if not isinstance(delta, StateDelta) or route is None:
                raise ValueError("unregistered delta")
            spec = self._fields.get(delta.target.family)
            if spec is None or route.owner_id != spec.owner_id or not any(
                a.family == delta.target.family for a in self._manifests[route.owner_id].writes
            ) or route.is_identity(delta) is not False:
                raise ValueError("delta owner/identity")
            ordered.append((delta.target.family.component, delta.target.family.field, delta.target.entity_id))
            factory = self._factory(core.components)
            epoch = ViewEpoch(core.tick, Phase.PRESENT, 0, "system.net-validator", 0)
            after = factory.open(epoch)
            try:
                route.validate_net(delta, after)
            finally:
                observed = factory.close(epoch)
            if any(o.operation == "write" or o.target != delta.target for o in observed):
                raise ValueError("net validator access outside target")
        if ordered != sorted(set(ordered)):
            raise ValueError("net delta target order/uniqueness")

    def _enabled_effects(self, command: GameCommand, core: CoreSnapshot, values: tuple[JsonValue, ...]) -> None:
        events = tuple(self._event(v) for v in values)
        ids = {e.header.event_id for e in events}
        if len(ids) != len(events):
            raise ValueError("duplicate event")
        seen: set[EventId] = set()
        counts: dict[int, int] = {}
        sequences: dict[tuple[int, Phase, int, str], int] = {}
        last = (-1, -1, -1, -1, -1)
        for e in events:
            h = e.header
            self._event_identity(e, core.world_id)
            active = self._active[NodeKey(h.phase, h.producer_id)]
            if not (active.every_tick or (h.occurred_at == core.tick and command.payload.schema in active.action_kinds) or (active.on_matching_events and self._manifests[h.producer_id].consumes)):
                raise ValueError("inactive event producer")
            if not core.tick - self._limits.max_duration_seconds < h.occurred_at <= core.tick:
                raise ValueError("event time range")
            if any(c in ids and c not in seen for c in h.caused_by):
                raise ValueError("future emitted cause")
            policy = self._events[h.type_key]
            if policy.mode == "simulate" and e.due_tick == h.occurred_at and not (policy.delivery_phase > h.phase or policy.delivery_phase == h.phase == Phase.CASCADE and h.wave + 1 < self._limits.cascade_waves):
                raise ValueError("late event routing")
            order = (h.occurred_at, int(h.phase), h.wave, h.producer_rank, h.sequence)
            key = (h.occurred_at, h.phase, h.wave, h.producer_id)
            if order <= last or h.sequence != sequences.get(key, 0):
                raise ValueError("event order/sequence")
            last = order
            sequences[key] = h.sequence + 1
            counts[h.occurred_at] = counts.get(h.occurred_at, 0) + 1
            if counts[h.occurred_at] > self._limits.max_events_per_tick:
                raise ValueError("event tick cap")
            seen.add(h.event_id)

    def encode_protocol(self, protocol: ProtocolSnapshot) -> JsonObject:
        document, _ = self._encode_protocol(protocol)
        return object_value(document.value) if isinstance(document, CanonicalDocument) else document

    def _encode_protocol(self, protocol: ProtocolSnapshot, *, own: bool = False) -> tuple[JsonObject | CanonicalDocument, tuple[tuple[GameCommand, CanonicalDocument], ...]]:
        # Retain operation-local roundtrip results;no validation survives this call.
        streams: tuple[JsonValue, ...] = tuple({"stream_id": s.stream_id, "actor_id": s.actor_id,
                         "highest_committed_sequence": s.highest_committed_sequence,
                         "status": s.status} for s in protocol.streams)
        receipts: list[JsonValue] = []
        owned_receipts: list[object] = []
        owned_commands: list[CanonicalDocument] = []
        commands: list[tuple[GameCommand, CanonicalDocument]] = []
        for stored in protocol.receipts:
            document, decoded = self._encode_command(stored.command)
            commands.append((decoded, document))
            metadata: JsonObject = {"command_fingerprint": stored.command_fingerprint,
                                    "receipt": receipt_document(stored.receipt)}
            receipts.append({"command": document.value, **metadata})
            if own:
                owned_commands.append(document)
                owned_receipts.append({"command": document, **metadata})
        result: JsonObject = {"branch_id": protocol.branch_id, "revision": protocol.revision,
                              "streams": streams, "receipts": tuple(receipts)}
        return (CanonicalDocument({**result, "receipts": owned_receipts}, children=tuple(owned_commands))
                if own else result), tuple(commands)

    def decode_protocol(self, document: JsonObject, core: CoreSnapshot) -> ProtocolSnapshot:
        return self._decode_protocol(document, core)

    def _decode_protocol(self, document: JsonObject | CanonicalDocument, core: CoreSnapshot,
                         *, commands: tuple[tuple[GameCommand, CanonicalDocument], ...] | None = None, head_hash: str | None = None) -> ProtocolSnapshot:
        return self._decode_protocol_document(document, core, commands=commands, head_hash=head_hash)[0]

    def _decode_protocol_document(self, document: JsonObject | CanonicalDocument, core: CoreSnapshot,
                         *, commands: tuple[tuple[GameCommand, CanonicalDocument], ...] | None = None, head_hash: str | None = None) -> tuple[ProtocolSnapshot, CanonicalDocument]:
        owned = document if commands is not None and isinstance(document, CanonicalDocument) else CanonicalDocument(document)
        d = exact_fields(owned.value, ("branch_id", "revision", "streams", "receipts"))
        branch, revision = _hex(d["branch_id"], 32), WorldRevision(_number(d["revision"]))
        streams: list[StreamCursor] = []
        actors = {c.entity_id for c in core.components}
        for item in array_value(d["streams"]):
            s = exact_fields(item, ("stream_id", "actor_id", "highest_committed_sequence", "status"))
            status = text_value(s["status"])
            if status not in ("active", "retired"):
                raise ValueError("stream status")
            actor = EntityId(_namespace(s["actor_id"]))
            if actor not in actors:
                raise ValueError("stream actor absent")
            streams.append(StreamCursor(_hex(s["stream_id"], 32), actor,
                                        _number(s["highest_committed_sequence"]), "active" if status == "active" else "retired"))
        if not 1 <= len(streams) <= 16 or len({s.stream_id for s in streams}) != len(streams):
            raise ValueError("stream cap/identity")
        if streams != sorted(streams, key=lambda s: s.stream_id):
            raise ValueError("unsorted streams")
        receipts: list[StoredReceipt] = []
        for index, item in enumerate(array_value(d["receipts"])):
            r = exact_fields(item, ("command", "command_fingerprint", "receipt"))
            if commands is None:
                command, command_document = self._decode_command(object_value(r["command"]))
            else:
                command, command_document = commands[index]
            receipt = _receipt(r["receipt"])
            route_branch, stream_id, sequence = _command_parts(command.command_id)
            cursor = next((s for s in streams if s.stream_id == stream_id), None)
            if route_branch != branch or cursor is None or cursor.actor_id != command.actor_id or sequence > cursor.highest_committed_sequence:
                raise ValueError("receipt stream ownership/high-water")
            if receipt.command_id != command.command_id or receipt.previous_revision != command.expected_revision or receipt.revision > revision or receipt.tick > core.tick:
                raise ValueError("receipt command/revision/tick")
            fingerprint = tagged_hash("command/v1", command_document.select(("actor_id", "expected_revision", "schema", "payload")).to_bytes())
            if _hex(r["command_fingerprint"]) != fingerprint:
                raise ValueError("receipt fingerprint")
            if receipt.revision == revision and (receipt.core_hash != (self.hash_core(core) if head_hash is None else head_hash) or receipt.tick != core.tick):
                raise ValueError("latest receipt does not match head")
            receipts.append(StoredReceipt(command, fingerprint, receipt))
        if len(receipts) > 1024 or len({r.command.command_id for r in receipts}) != len(receipts) or len({r.receipt.revision for r in receipts}) != len(receipts):
            raise ValueError("receipt cap/identity")
        if receipts != sorted(receipts, key=lambda r: (r.receipt.revision, r.command.command_id)):
            raise ValueError("unsorted receipts")
        return ProtocolSnapshot(branch, revision, tuple(streams), tuple(receipts)), owned


    def encode_publication(self, publication: TurnPublication) -> JsonObject:
        from contracts.turn import TurnCommitted, TurnRejected
        outcome = publication.outcome
        result: JsonObject
        if isinstance(outcome, TurnCommitted):
            result = {"kind": "committed", "receipt": receipt_document(outcome.receipt)}
        else:
            data: dict[str, JsonValue] = {"kind": "rejected" if isinstance(outcome, TurnRejected) else "aborted",
                                        "failure": {"code": outcome.failure.code, "message_key": outcome.failure.message_key}}
            if isinstance(outcome, TurnRejected):
                data["current_revision"] = outcome.current_revision
            result = data
        diff = publication.diff
        document: JsonObject = {"outcome": result,
                "facts": tuple({"header": header_document(e.header), "due_tick": e.due_tick,
                                "payload": self.encode_payload(e.payload)} for e in publication.facts),
                "diff": None if diff is None else {
                    "receipt": receipt_document(diff.receipt), "changes": tuple({
                        "schema": key_document(d.schema), **self.encode_payload(d)} for d in diff.changes)},
                "cues": tuple({"header": header_document(e.header), "payload": self.encode_payload(e.payload),
                               "priority": e.priority, "coalesce_policy": e.coalesce_policy,
                               "coalesce_key": e.coalesce_key} for e in publication.cues),
                "diagnostics": tuple({"code": f.code, "message_key": f.message_key} for f in publication.diagnostics)}
        self.decode_outcome(result)
        sequences: dict[str, int] = {}
        source = {f.header.event_id: f for f in publication.facts}
        for cue in publication.cues:
            h = cue.header
            for number in (h.occurred_at, h.wave, h.producer_rank, h.sequence):
                require_integer(number)
            binding = self._presenters.get(h.producer_id)
            if not isinstance(cue.payload, PresentationPayload) or h.type_key != cue.payload.schema or binding is None or not isinstance(outcome, TurnCommitted):
                raise ValueError("invalid registered cue")
            index = sequences.get(h.producer_id, 0)
            if h.phase != Phase.PRESENT or h.occurred_at != outcome.receipt.tick or h.wave != 0 or h.producer_rank != 0 or h.sequence != index or h.degraded or len(h.caused_by) != 1:
                raise ValueError("invalid cue header")
            fact = source.get(h.caused_by[0])
            if fact is None or fact.header.type_key not in binding.kinds:
                raise ValueError("cue source ownership")
            identifier = "p1-" + hashlib.sha256(pack(("cue-id/v1", h.caused_by[0], h.producer_id, str(index)))).hexdigest()
            if h.event_id != identifier or cue.priority not in ("essential", "important", "ambient") or cue.coalesce_policy not in ("keep_all", "replace_latest"):
                raise ValueError("invalid cue identity/policy")
            sequences[h.producer_id] = index + 1
        return object_value(seal(document))
