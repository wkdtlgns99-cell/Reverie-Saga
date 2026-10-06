from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import logging
import re

from contracts.errors import BootstrapError, CandidateError, RngUnavailable, UnknownEntity
from contracts.messages import EventHeader, PresentationEvent, StateDelta, StateDiff, WorldEvent
from contracts.read_views import AccessObservation, ComponentKey, ComponentPatch, ViewEpoch
from contracts.persistence import (
    CommitUncertain, DurableCheckpoint, DurableCommitPort, DurableTurn, RecoveryAbsent,
    RecoveryCommitted, SaveError, SaveUnavailable, WorldUnavailable,
)
from contracts.skeleton import FeatureBundle
from contracts.state_io import StateIO
from contracts.turn import (
    CapabilityManifest, CompiledSchedule, DefinitionReadPort, EngineInvocation, EngineRng,
    GameCommand, NodeActivation, NodeKey, ProtocolSnapshot, RandomStream, RngService,
    StoredReceipt, TurnAborted, TurnCommitted, TurnOutcome, TurnPublication, TurnRejected, failure,
    CommitReceipt,
)
from domain.canonical import hash_document, pack
from domain.primitives import (
    ComponentAddress, EntityId, EventId, FieldAddress, FieldFamily, MAX_INT, Phase, Tick,
    TypeKey, WorldRevision, require_integer, require_namespace,
)
from domain.state_types import ComponentRecord, CoreSnapshot, StoredRoot
from orchestration.events import CandidateEventBus
from orchestration.read_views import ObservedReadViewFactory


class EmptyDefinitions:
    def definition[ReadT](self, key: ComponentKey[ReadT], entry_id: str) -> ReadT:
        raise KeyError((key.schema.kind, entry_id))


class _NoDrawStream:
    def draw_bounded(self, low: int, high_exclusive: int) -> int:
        raise RngUnavailable("RS-P0-003: no tested RNG installed")


class NoDrawRng:
    def scoped(self, tick: Tick, phase: Phase, wave: int, engine_id: str) -> EngineRng:
        return self
    def stream(self, entity_id: EntityId, purpose: str, causal_key: str) -> RandomStream:
        return _NoDrawStream()


@dataclass(frozen=True)
class _Head:
    core: CoreSnapshot
    protocol: ProtocolSnapshot


class _Editor:
    def __init__(self, root: StoredRoot, allowed: FieldAddress, io: StateIO) -> None:
        self._base = root
        self._allowed = allowed
        self._io = io
        self.changes: dict[ComponentAddress, ComponentRecord] = {}

    def apply_patch(self, address: ComponentAddress, patch: ComponentPatch) -> None:
        if address.entity_id != self._allowed.entity_id or address.schema.kind != self._allowed.family.component:
            raise CandidateError("UNDECLARED_WRITE", "editor target")
        for record in self._base.components:
            if record.entity_id != address.entity_id or record.schema != address.schema:
                continue
            self.changes[address] = self._io.apply_patch(address, self._allowed, record, patch)
            return
        raise CandidateError("INVALID_DELTA", "patch entity")


def validate_registry(bundles: tuple[FeatureBundle, ...], schedule: CompiledSchedule) -> None:
    if not bundles:
        raise BootstrapError("DUPLICATE_SCHEMA", "empty feature registry")
    bindings = tuple(binding for bundle in bundles for binding in bundle.bindings)
    manifests = {b.engine.manifest.engine_id: b.engine.manifest for b in bindings}
    activations = {a.node: a for b in bindings for a in b.activations}
    fields = {s.family: s for bundle in bundles for s in bundle.field_specs}
    spec_count = sum(len(b.field_specs) for b in bundles)
    write_families: dict[tuple[Phase, str], FieldFamily] = {}
    for manifest in manifests.values():
        for access in manifest.writes:
            group = (access.phase, access.family.component)
            if group in write_families and write_families[group] != access.family:
                raise BootstrapError("WRITE_CONFLICT", "same-phase component field merge unsupported")
            write_families[group] = access.family
    if len(fields) != spec_count or len({b.feature_id for b in bundles}) != len(bundles):
        raise BootstrapError("DUPLICATE_SCHEMA", "feature/field collision")
    categories: tuple[tuple[str, tuple[TypeKey, ...]], ...] = (
        ("read_adapters", tuple(a.schema for b in bundles for a in b.read_adapters)),
        ("codecs", tuple(c.schema for b in bundles for c in b.codecs)),
        ("command_routes", tuple(r.schema for b in bundles for r in b.command_routes)),
        ("delta_routes", tuple(r.schema for b in bundles for r in b.delta_routes)),
    )
    for category, schemas in categories:
        if len(set(schemas)) != len(schemas):
            raise BootstrapError("DUPLICATE_SCHEMA", category)
    codecs = {c.schema for b in bundles for c in b.codecs}
    commands = {r.schema for b in bundles for r in b.command_routes}
    policies = {p.schema: p for b in bundles for p in b.events}
    if len(policies) != sum(len(b.events) for b in bundles):
        raise BootstrapError("DUPLICATE_SCHEMA", "event policy")
    presenters = {k for b in bundles for p in b.presenters for k in p.kinds}
    for node in schedule.nodes:
        manifest, active = manifests[node.engine_id], activations[node]
        for access in (*manifest.reads, *manifest.writes):
            if access.family not in fields:
                raise BootstrapError("DUPLICATE_SCHEMA", "unknown field")
            spec = fields[access.family]
            writing = access in manifest.writes
            if writing and spec.owner_id != manifest.engine_id:
                raise BootstrapError("WRITE_CONFLICT", "wrong field owner")
            if active.lane == "A" and (spec.tier != "A" or spec.storage_class != "CORE"):
                raise BootstrapError("INVALID_LANE", "A accesses B/C")
            if active.lane == "B" and writing and spec.tier != "B":
                raise BootstrapError("INVALID_LANE", "B writes A/C")
        if any(k not in commands for k in active.action_kinds):
            raise BootstrapError("INVALID_ACTIVATION", "unregistered action")
        for kind in (*manifest.emits, *manifest.consumes):
            if kind not in codecs or kind not in policies:
                raise BootstrapError("INVALID_EVENT_POLICY", "unregistered fact")
    for policy in policies.values():
        for producer in policy.producers:
            if producer not in manifests or policy.schema not in manifests[producer].emits:
                raise BootstrapError("INVALID_EVENT_POLICY", "producer")
        if policy.mode == "record_only":
            if policy.delivery_phase != Phase.PRESENT or policy.subscribers or policy.schema not in presenters:
                raise BootstrapError("INVALID_EVENT_POLICY", "record-only ownership")
        else:
            if not policy.subscribers:
                raise BootstrapError("INVALID_EVENT_POLICY", "empty subscribers")
            for subscriber in policy.subscribers:
                node = NodeKey(policy.delivery_phase, subscriber)
                if node not in activations or not activations[node].on_matching_events or policy.schema not in manifests[subscriber].consumes:
                    raise BootstrapError("INVALID_EVENT_POLICY", "subscriber node")


class Driver:
    def __init__(self, core: CoreSnapshot, protocol: ProtocolSnapshot,
                 bundles: tuple[FeatureBundle, ...], schedule: CompiledSchedule,
                 rng: RngService, definitions: DefinitionReadPort | None = None, *, io: StateIO,
                 commit_port: DurableCommitPort | None = None) -> None:
        validate_registry(bundles, schedule)
        if io.schedule != schedule or io.pins != core.pins:
            raise BootstrapError("INVALID_ACTIVATION", "state IO/head schedule or pins")
        if len(bundles) != 1 or io.pins.schema_fingerprint != hash_document("schema/v1", bundles[0].schema_document) or io.pins.rules_fingerprint != hash_document("rules/v1", bundles[0].rules_document):
            raise BootstrapError("DUPLICATE_SCHEMA", "state IO/registry pins")
        io.validate_checkpoint(core, protocol)
        self._io = io
        self._head = _Head(core, protocol)
        self._bundles = bundles
        self._schedule = schedule
        self._rng = rng
        self._definitions = definitions if definitions is not None else EmptyDefinitions()
        self._bindings = {b.engine.manifest.engine_id: b for f in bundles for b in f.bindings}
        self._activations = {a.node: a for b in self._bindings.values() for a in b.activations}
        self._token = 0
        self._busy = False
        self._publication: TurnPublication | None = None
        self._commit_port = commit_port
        self._uncertain: DurableTurn | None = None
        self._blocked_code: str | None = None
        self._detached = False
        self._logger = logging.getLogger(__name__)
        self.compile(tuple(b.engine.manifest for b in self._bindings.values()),
                     tuple(a for b in self._bindings.values() for a in b.activations))

    def compile(self, manifests: tuple[CapabilityManifest, ...],
                activations: tuple[NodeActivation, ...]) -> CompiledSchedule:
        expected = tuple(b.engine.manifest for b in self._bindings.values())
        registered = tuple(a for b in self._bindings.values() for a in b.activations)
        if set(manifests) != set(expected) or set(activations) != set(registered):
            raise BootstrapError("INVALID_ACTIVATION", "boot registry is frozen")
        return self._schedule

    def snapshot(self) -> CoreSnapshot:
        if not self._detached:
            self._active()
        return self._head.core

    def protocol(self) -> ProtocolSnapshot:
        if not self._detached:
            self._active()
        return self._head.protocol

    def last_publication(self) -> TurnPublication:
        self._active()
        if self._publication is None:
            raise RuntimeError("no submission yet")
        return self._publication

    def reject_malformed(self) -> TurnPublication:
        self._active()
        self._publication = TurnPublication(TurnRejected(failure("INVALID_COMMAND")), (), None, (), ())
        return self._publication

    def _active(self) -> None:
        if self._detached:
            raise WorldUnavailable("SESSION_DETACHED", "previous owner detached")
        if self._uncertain is not None or self._blocked_code is not None:
            raise WorldUnavailable(self._blocked_code or "SAVE_UNCERTAIN", "durable result unresolved")

    def detach(self) -> None:
        if self._busy:
            raise SaveError("SAVE_BUSY", "cannot detach an active turn")
        self._detached = True

    def _resolve_durable(self, turn: DurableTurn) -> bool:
        self._uncertain = turn
        self._publication = None
        assert self._commit_port is not None
        try:
            resolved = self._commit_port.recover(turn)
            if isinstance(resolved, RecoveryCommitted):
                if resolved.checkpoint != turn.next or not isinstance(turn.publication.outcome, TurnCommitted) or resolved.receipt != turn.publication.outcome.receipt:
                    raise CommitUncertain("SAVE_UNCERTAIN", "recovered committed result differs")
                self._io.validate_checkpoint(resolved.checkpoint.core, resolved.checkpoint.protocol)
                return True
            if isinstance(resolved, RecoveryAbsent) and resolved.checkpoint == turn.previous:
                self._io.validate_checkpoint(resolved.checkpoint.core, resolved.checkpoint.protocol)
                return False
            raise CommitUncertain("SAVE_UNCERTAIN", "recovery did not prove previous or next")
        except Exception as error:
            self._blocked_code = "SAVE_UNCERTAIN"
            raise WorldUnavailable("SAVE_UNCERTAIN", "durable result unavailable") from error

    def _persist_durable(self, turn: DurableTurn) -> bool:
        assert self._commit_port is not None
        try:
            receipt = self._commit_port.persist(turn)
            if not isinstance(turn.publication.outcome, TurnCommitted) or receipt != turn.publication.outcome.receipt:
                raise CommitUncertain("SAVE_UNCERTAIN", "persist returned another receipt")
            return True
        except SaveUnavailable:
            return False
        except WorldUnavailable as error:
            if error.code == "SAVE_STALE":
                self._blocked_code = error.code
                self._publication = None
                raise
            return self._resolve_durable(turn)
        except Exception:
            return self._resolve_durable(turn)

    def recover_pending(self) -> TurnPublication:
        if self._detached:
            raise WorldUnavailable("SESSION_DETACHED", "previous owner detached")
        if self._busy:
            raise SaveError("SAVE_BUSY", "active turn")
        turn = self._uncertain
        if turn is None:
            raise SaveError("NO_RECOVERY_PENDING", "no unresolved durable turn")
        self._busy = True
        try:
            committed = self._resolve_durable(turn)
            if committed:
                self._head = _Head(turn.next.core, turn.next.protocol)
                self._publication = turn.publication
            else:
                self._publication = TurnPublication(TurnAborted(failure("SAVE_UNAVAILABLE")), (), None, (), ())
            self._uncertain = None
            self._blocked_code = None
            if committed:
                self._present(turn.publication, turn.next.core)
            assert self._publication is not None
            return self._publication
        finally:
            self._busy = False

    def _factory(self, components: tuple[ComponentRecord, ...]) -> ObservedReadViewFactory:
        self._token += 1
        factory = ObservedReadViewFactory(StoredRoot(components, self._token))
        for bundle in self._bundles:
            for adapter in bundle.read_adapters:
                adapter.install(factory)
        return factory

    def _observations(self, observations: tuple[AccessObservation, ...], allowed: tuple[FieldFamily, ...]) -> None:
        for observation in observations:
            if observation.operation == "write":
                raise CandidateError("UNDECLARED_WRITE", "mutation attempt")
            if observation.target.family not in allowed:
                raise CandidateError("UNDECLARED_READ", "read outside manifest")

    def _rejected(self, code: str, authorized: bool = True) -> TurnOutcome:
        outcome = TurnRejected(failure(code), self._head.protocol.revision if authorized else None)
        self._publication = TurnPublication(outcome, (), None, (), ())
        return outcome

    def submit(self, command: GameCommand) -> TurnOutcome:
        self._active()
        if self._busy:
            raise RuntimeError("one authoritative turn at a time")
        self._busy = True
        try:
            return self._submit(command)
        finally:
            self._busy = False

    def _submit(self, command: GameCommand) -> TurnOutcome:
        core, protocol = self._head.core, self._head.protocol
        try:
            require_integer(command.expected_revision)
            require_namespace(command.actor_id)
            match = re.fullmatch(r"c1:([0-9a-f]{32}):([0-9a-f]{32}):([1-9][0-9]{0,18})", command.command_id)
            if match is None or match[1] != protocol.branch_id:
                return self._rejected("INVALID_COMMAND", False)
            sequence = int(match[3])
            require_integer(sequence, 1)
            cursor = next((s for s in protocol.streams if s.stream_id == match[2]), None)
            if cursor is None:
                return self._rejected("UNKNOWN_STREAM", False)
            if command.actor_id != cursor.actor_id:
                return self._rejected("UNAUTHORIZED_ACTOR")
            if not any(c.entity_id == command.actor_id for c in core.components):
                return self._rejected("UNKNOWN_ACTOR")
            route = next((r for b in self._bundles for r in b.command_routes if r.schema == command.payload.schema), None)
            if route is None:
                return self._rejected("UNSUPPORTED_SCHEMA")
            document = self._io.encode_command(command)
        except (ValueError, TypeError, AttributeError):
            return self._rejected("INVALID_COMMAND")
        fingerprint = hash_document("command/v1", {k: v for k, v in document.items() if k != "command_id"})
        retained = next((s for s in protocol.receipts if s.command.command_id == command.command_id), None)
        if retained is not None:
            if retained.command_fingerprint != fingerprint or retained.command != command:
                return self._rejected("COMMAND_ID_CONFLICT")
            outcome = TurnCommitted(retained.receipt)
            diagnostics = (failure("RESYNC_REQUIRED"),) if retained.receipt.revision < protocol.revision else ()
            self._publication = TurnPublication(outcome, (), None, (), diagnostics)
            return outcome
        if sequence <= cursor.highest_committed_sequence:
            return self._rejected("RETRY_WINDOW_EXPIRED")
        if cursor.status == "retired":
            return self._rejected("STREAM_RETIRED")
        if command.expected_revision != protocol.revision:
            return self._rejected("STALE_REVISION")
        try:
            if core.tick == MAX_INT or protocol.revision == MAX_INT:
                raise CandidateError("INTEGER_OVERFLOW", "tick/revision")
            factory = self._factory(core.components)
            epoch = ViewEpoch(core.tick, Phase.VALIDATE, 0, "system.admission", self._token)
            port = factory.open(epoch)
            try:
                admission = route.admit(command, port, start_tick=core.tick, world_id=core.world_id)
            finally:
                observed = factory.close(epoch)
            self._observations(observed, route.reads)
            if isinstance(admission, TurnRejected):
                self._publication = TurnPublication(admission, (), None, (), ())
                return admission
            target = admission.plan.target_tick
            limits = self._io.execution_limits
            if limits.enable_simulation:
                if type(target) is not int or target <= core.tick:
                    raise CandidateError("INVALID_COMMAND", "nonpositive/invalid admission target")
                if target > MAX_INT:
                    raise CandidateError("INTEGER_OVERFLOW", "admission target")
            require_integer(target)
            if admission.plan.command != command or admission.plan.start_tick != core.tick or admission.action.actor_id != command.actor_id or admission.action.payload != command.payload or target <= core.tick:
                raise CandidateError("INVALID_COMMAND", "admission plan")
            if limits.enable_simulation:
                if target - core.tick > limits.max_duration_seconds:
                    raise CandidateError("TURN_LIMIT", "admission duration")
            elif target != core.tick + 1:
                raise CandidateError("INVALID_COMMAND", "admission plan does not describe this one-tick action")
            bus = CandidateEventBus(tuple(p for b in self._bundles for p in b.events), io=self._io, limits=limits, world_id=core.world_id, start_tick=core.tick, pending=core.pending) if limits.enable_simulation else None
            components = core.components
            produced: list[WorldEvent] = []
            changes: list[StateDelta] = []
            a_nodes = tuple(n for n in self._schedule.nodes if self._activations[n].lane == "A")
            for logical_second in range(core.tick + 1, target + 1):
                logical_tick = Tick(logical_second)
                if bus is not None:
                    bus.begin_tick(logical_tick)
                for phase in (Phase.PRE_TICK, Phase.RESOLVE, Phase.REACT, Phase.CASCADE, Phase.POST_TICK):
                    for wave in range(limits.cascade_waves if bus is not None and phase == Phase.CASCADE else 1):
                        batch = bus.due(logical_tick, phase, wave) if bus is not None else None
                        if bus is not None and batch is not None and phase == Phase.CASCADE and not batch.events:
                            bus.complete(batch, ())
                            break
                        deliveries: list[tuple[str, tuple[EventId, ...]]] = []
                        root = StoredRoot(components, self._token + 1)
                        phase_changes: dict[ComponentAddress, ComponentRecord] = {}
                        targets: set[FieldAddress] = set()
                        for node in self._schedule.nodes:
                            activation = self._activations[node]
                            incoming = tuple(e for e in batch.events if node.engine_id in next(p for b in self._bundles for p in b.events if p.schema == e.header.type_key).subscribers) if batch is not None else ()
                            action_active = logical_tick == target and command.payload.schema in activation.action_kinds
                            if node.phase != phase or not (activation.every_tick or action_active or activation.on_matching_events and incoming):
                                continue
                            binding = self._bindings[node.engine_id]
                            manifest = binding.engine.manifest
                            factory = self._factory(components)
                            epoch = ViewEpoch(logical_tick, phase, wave, node.engine_id, self._token)
                            port = factory.open(epoch)
                            try:
                                invocation = EngineInvocation(admission.action if action_active else None,
                                                              logical_tick, phase, wave, port, self._definitions,
                                                              self._rng.scoped(logical_tick, phase, wave, node.engine_id), incoming)
                                result = binding.engine.evaluate(invocation)
                            finally:
                                observed = factory.close(epoch)
                            self._observations(observed, tuple(a.family for a in manifest.reads if a.phase == phase))
                            for delta in result.deltas:
                                if delta.target in targets:
                                    raise CandidateError("DUPLICATE_TARGET", "barrier target")
                                targets.add(delta.target)
                                if delta.target.family not in tuple(a.family for a in manifest.writes if a.phase == phase):
                                    raise CandidateError("UNDECLARED_WRITE", "delta outside manifest")
                                reducer = next((r for b in self._bundles for r in b.delta_routes if r.schema == delta.schema), None)
                                if reducer is None or reducer.owner_id != node.engine_id:
                                    raise CandidateError("INVALID_DELTA", "unregistered/wrong owner")
                                editor = _Editor(root, delta.target, self._io)
                                reducer_factory = self._factory(components)
                                reducer_epoch = ViewEpoch(logical_tick, phase, wave, "system.reducer", self._token)
                                before = reducer_factory.open(reducer_epoch)
                                try:
                                    reducer.stage(delta, before, editor)
                                finally:
                                    reducer_observed = reducer_factory.close(reducer_epoch)
                                if any(o.operation == "write" or o.target != delta.target for o in reducer_observed):
                                    raise CandidateError("UNDECLARED_READ", "reducer access outside target")
                                if not editor.changes:
                                    raise CandidateError("INVALID_DELTA", "reducer did not stage")
                                phase_changes.update(editor.changes)
                                changes.append(delta)
                            if bus is not None:
                                if (activation.lane != "A" and (result.facts or result.degraded)) or any(f.payload.schema not in manifest.emits for f in result.facts):
                                    raise CandidateError("INVALID_FACT", "manifest emit rights")
                                if activation.lane == "A":
                                    produced.extend(bus.emit(invocation, node.engine_id, a_nodes.index(node), result.facts, result.degraded))
                                if incoming:
                                    deliveries.append((node.engine_id, tuple(e.header.event_id for e in incoming)))
                            else:
                                for index, fact in enumerate(result.facts):
                                    policy = next((p for b in self._bundles for p in b.events if p.schema == fact.payload.schema), None)
                                    if activation.lane != "A" or policy is None or policy.mode != "record_only" or node.engine_id not in policy.producers or fact.payload.schema not in manifest.emits or fact.due_tick != target or fact.caused_by:
                                        raise CandidateError("INVALID_FACT", "only due-now record-only root facts supported")
                                    self._io.encode_payload(fact.payload)
                                    identifier = "e1-" + hashlib.sha256(pack(("event-id/v1", core.world_id, str(target),
                                                                             phase.name, "0", node.engine_id, str(index)))).hexdigest()
                                    produced.append(WorldEvent(EventHeader(EventId(identifier), fact.payload.schema, node.engine_id,
                                                                           target, phase, 0, a_nodes.index(node), index, (), result.degraded),
                                                               target, fact.payload))
                        components = tuple(phase_changes.get(ComponentAddress(c.schema, c.entity_id), c) for c in components)
                        if bus is not None and batch is not None:
                            bus.complete(batch, tuple(deliveries))
                if bus is not None:
                    bus.finish_tick(logical_tick)
            candidate = replace(core, components=components, tick=target, pending=bus.finish(target) if bus is not None else core.pending)
            receipt = CommitReceipt(command.command_id, protocol.revision,
                                    WorldRevision(protocol.revision + 1), target, self._io.hash_core(candidate))
            net: list[StateDelta] = []
            for target_address in sorted({d.target for d in changes}, key=lambda a: (a.family.component, a.family.field, a.entity_id)):
                group = tuple(d for d in changes if d.target == target_address)
                reducer = next(r for b in self._bundles for r in b.delta_routes if r.schema == group[0].schema)
                delta = reducer.compose(group)
                self._io.encode_payload(delta)
                identity = reducer.is_identity(delta)
                if type(identity) is not bool or delta.target != target_address or delta.schema != group[0].schema:
                    raise CandidateError("INVALID_DELTA", "composed delta identity/target/schema")
                if not identity:
                    net.append(delta)
            next_protocol = replace(protocol, revision=receipt.revision,
                                    streams=tuple(replace(s, highest_committed_sequence=sequence) if s.stream_id == cursor.stream_id else s for s in protocol.streams),
                                    receipts=(*protocol.receipts, StoredReceipt(command, fingerprint, receipt))[-1024:])
            diff = StateDiff(receipt, tuple(net))
            outcome = TurnCommitted(receipt)
            prepared = TurnPublication(outcome, tuple(produced), diff, (), bus.diagnostics if bus is not None else ())
            self._io.validate_checkpoint(candidate, next_protocol)
            encoded = self._io.encode_publication(prepared)
            self._io.validate_effects(command, outcome, candidate, next_protocol, encoded["facts"], encoded["diff"])
            prepared_head = _Head(candidate, next_protocol)
            if self._commit_port is not None:
                durable = DurableTurn(DurableCheckpoint(core, protocol), DurableCheckpoint(candidate, next_protocol), command, prepared)
                if not self._persist_durable(durable):
                    self._uncertain = None
                    self._blocked_code = None
                    aborted = TurnAborted(failure("SAVE_UNAVAILABLE"))
                    self._publication = TurnPublication(aborted, (), None, (), ())
                    return aborted
            self._head = prepared_head  # Sole authoritative publication, after durability when selected.
            self._publication = prepared
            self._uncertain = None
            self._blocked_code = None
        except WorldUnavailable:
            raise
        except Exception as error:
            code = error.code if isinstance(error, CandidateError) else "RNG_UNAVAILABLE" if isinstance(error, RngUnavailable) else "UNKNOWN_ACTOR" if isinstance(error, UnknownEntity) else "ENGINE_EXCEPTION"
            self._logger.error("candidate aborted: %s", code, exc_info=True)
            aborted = TurnAborted(failure(code))
            self._publication = TurnPublication(aborted, (), None, (), ())
            return aborted
        return self._present(prepared, candidate)

    def _present(self, prepared: TurnPublication, candidate: CoreSnapshot) -> TurnOutcome:
        outcome = prepared.outcome
        assert isinstance(outcome, TurnCommitted)
        receipt, target, produced = outcome.receipt, candidate.tick, prepared.facts
        cues: list[PresentationEvent] = []
        try:
            for presenter_binding in sorted((p for b in self._bundles for p in b.presenters), key=lambda p: p.presenter_id):
                selected = tuple(f for f in produced if f.header.type_key in presenter_binding.kinds)
                factory = self._factory(candidate.components)
                epoch = ViewEpoch(target, Phase.PRESENT, 0, presenter_binding.presenter_id, self._token)
                port = factory.open(epoch)
                try:
                    cues.extend(presenter_binding.presenter.map(selected, receipt, port))
                finally:
                    factory.close(epoch)
            presented = replace(prepared, cues=tuple(cues))
            self._io.encode_publication(presented)
            self._publication = presented
        except Exception:
            self._logger.error("presentation failed after commit", exc_info=True)
            self._publication = replace(prepared, diagnostics=(*prepared.diagnostics, failure("PRESENTATION_FAILED")))
        return outcome
