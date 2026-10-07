from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import logging
import re

from contracts.errors import BootstrapError, CandidateError, RngUnavailable, UnknownEntity
from contracts.messages import EventHeader, PresentationEvent, StateDelta, StateDiff, WorldEvent
from contracts.read_views import AccessObservation, ComponentKey, ComponentPatch, ViewEpoch
from contracts.persistence import (
    CommitUncertain,
    DurableCheckpoint,
    DurableCommitPort,
    DurableTurn,
    RecoveryAbsent,
    RecoveryCommitted,
    SaveError,
    SaveUnavailable,
    WorldUnavailable,
)
from contracts.skeleton import CommandRoute, FeatureBundle
from contracts.state_io import StateIO
from contracts.turn import (
    CapabilityManifest,
    CompiledSchedule,
    DefinitionReadPort,
    EngineInvocation,
    EngineRng,
    GameCommand,
    NodeActivation,
    NodeKey,
    ProtocolSnapshot,
    RandomStream,
    RngService,
    StoredReceipt,
    TurnAborted,
    TurnCommitted,
    TurnOutcome,
    TurnPublication,
    TurnRejected,
    failure,
    CommitReceipt,
    AdmittedCommand,
    AdmittedAction,
    EngineResult,
    StreamCursor,
)
from domain.canonical import hash_document, pack
from domain.primitives import (
    ComponentAddress,
    EntityId,
    EventId,
    FieldAddress,
    FieldFamily,
    MAX_INT,
    Phase,
    Tick,
    TypeKey,
    WorldRevision,
    require_integer,
    require_namespace,
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


@dataclass(frozen=True, slots=True)
class _CheckedCommand:
    route: CommandRoute
    cursor: StreamCursor
    sequence: int
    fingerprint: str


@dataclass(slots=True)
class _Candidate:
    """Private staging only; no authoritative publication until durability succeeds."""

    core: CoreSnapshot
    components: tuple[ComponentRecord, ...]
    changes: list[StateDelta]
    facts: list[WorldEvent]
    bus: CandidateEventBus | None


class _Editor:
    def __init__(self, root: StoredRoot, allowed: FieldAddress, io: StateIO) -> None:
        self._base = root
        self._allowed = allowed
        self._io = io
        self.changes: dict[ComponentAddress, ComponentRecord] = {}

    def apply_patch(self, address: ComponentAddress, patch: ComponentPatch) -> None:
        if (
            address.entity_id != self._allowed.entity_id
            or address.schema.kind != self._allowed.family.component
        ):
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
                raise BootstrapError(
                    "WRITE_CONFLICT", "same-phase component field merge unsupported"
                )
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
            if (
                policy.delivery_phase != Phase.PRESENT
                or policy.subscribers
                or policy.schema not in presenters
            ):
                raise BootstrapError("INVALID_EVENT_POLICY", "record-only ownership")
        else:
            if not policy.subscribers:
                raise BootstrapError("INVALID_EVENT_POLICY", "empty subscribers")
            for subscriber in policy.subscribers:
                node = NodeKey(policy.delivery_phase, subscriber)
                if (
                    node not in activations
                    or not activations[node].on_matching_events
                    or policy.schema not in manifests[subscriber].consumes
                ):
                    raise BootstrapError("INVALID_EVENT_POLICY", "subscriber node")


class Driver:
    def __init__(
        self,
        core: CoreSnapshot,
        protocol: ProtocolSnapshot,
        bundles: tuple[FeatureBundle, ...],
        schedule: CompiledSchedule,
        rng: RngService,
        definitions: DefinitionReadPort | None = None,
        *,
        io: StateIO,
        commit_port: DurableCommitPort | None = None,
    ) -> None:
        validate_registry(bundles, schedule)
        if io.schedule != schedule or io.pins != core.pins:
            raise BootstrapError("INVALID_ACTIVATION", "state IO/head schedule or pins")
        if (
            len(bundles) != 1
            or io.pins.schema_fingerprint != hash_document("schema/v1", bundles[0].schema_document)
            or io.pins.rules_fingerprint != hash_document("rules/v1", bundles[0].rules_document)
        ):
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
        # Cache frozen registration metadata, never epoch-bound read ports or observations.
        self._manifests = {key: binding.engine.manifest for key, binding in self._bindings.items()}
        self._command_routes = {r.schema: r for b in bundles for r in b.command_routes}
        self._delta_routes = {r.schema: r for b in bundles for r in b.delta_routes}
        self._policies = {p.schema: p for b in bundles for p in b.events}
        self._read_adapters = tuple(r for b in bundles for r in b.read_adapters)
        self._presenters = tuple(
            sorted((p for b in bundles for p in b.presenters), key=lambda p: p.presenter_id)
        )
        self._a_ranks = {
            node: rank
            for rank, node in enumerate(
                n for n in schedule.nodes if self._activations[n].lane == "A"
            )
        }
        self._token = 0
        self._busy = False
        self._publication: TurnPublication | None = None
        self._commit_port = commit_port
        self._uncertain: DurableTurn | None = None
        self._blocked_code: str | None = None
        self._detached = False
        self._logger = logging.getLogger(__name__)

    def compile(
        self, manifests: tuple[CapabilityManifest, ...], activations: tuple[NodeActivation, ...]
    ) -> CompiledSchedule:
        expected = tuple(self._manifests.values())
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
        self._publication = TurnPublication(
            TurnRejected(failure("INVALID_COMMAND")), (), None, (), ()
        )
        return self._publication

    def _active(self) -> None:
        if self._detached:
            raise WorldUnavailable("SESSION_DETACHED", "previous owner detached")
        if self._uncertain is not None or self._blocked_code is not None:
            raise WorldUnavailable(
                self._blocked_code or "SAVE_UNCERTAIN", "durable result unresolved"
            )

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
                if (
                    resolved.checkpoint != turn.next
                    or not isinstance(turn.publication.outcome, TurnCommitted)
                    or resolved.receipt != turn.publication.outcome.receipt
                ):
                    raise CommitUncertain("SAVE_UNCERTAIN", "recovered committed result differs")
                self._io.validate_checkpoint(resolved.checkpoint.core, resolved.checkpoint.protocol)
                return True
            if isinstance(resolved, RecoveryAbsent) and resolved.checkpoint == turn.previous:
                self._io.validate_checkpoint(resolved.checkpoint.core, resolved.checkpoint.protocol)
                return False
            raise CommitUncertain("SAVE_UNCERTAIN", "recovery did not prove previous or next")
        except Exception as error:
            # Without proof of either durable head,block admission rather than publish an abort.
            self._blocked_code = "SAVE_UNCERTAIN"
            raise WorldUnavailable("SAVE_UNCERTAIN", "durable result unavailable") from error

    def _persist_durable(self, turn: DurableTurn) -> bool:
        assert self._commit_port is not None
        try:
            receipt = self._commit_port.persist(turn)
            if (
                not isinstance(turn.publication.outcome, TurnCommitted)
                or receipt != turn.publication.outcome.receipt
            ):
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
            # An adapter can fail after SQL COMMIT;resolve durable truth before any publication.
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
                self._publication = TurnPublication(
                    TurnAborted(failure("SAVE_UNAVAILABLE")), (), None, (), ()
                )
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
        for adapter in self._read_adapters:
            adapter.install(factory)
        return factory

    def _observations(
        self, observations: tuple[AccessObservation, ...], allowed: tuple[FieldFamily, ...]
    ) -> None:
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

    def _check_command(self, command: GameCommand) -> _CheckedCommand | TurnOutcome:
        core, protocol = self._head.core, self._head.protocol
        try:
            require_integer(command.expected_revision)
            require_namespace(command.actor_id)
            match = re.fullmatch(
                r"c1:([0-9a-f]{32}):([0-9a-f]{32}):([1-9][0-9]{0,18})", command.command_id
            )
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
            route = self._command_routes.get(command.payload.schema)
            if route is None:
                return self._rejected("UNSUPPORTED_SCHEMA")
            document = self._io.encode_command(command)
        except (ValueError, TypeError, AttributeError):
            return self._rejected("INVALID_COMMAND")
        fingerprint = hash_document(
            "command/v1", {k: v for k, v in document.items() if k != "command_id"}
        )
        retained = next(
            (s for s in protocol.receipts if s.command.command_id == command.command_id), None
        )
        if retained is not None:
            if retained.command_fingerprint != fingerprint or retained.command != command:
                return self._rejected("COMMAND_ID_CONFLICT")
            outcome = TurnCommitted(retained.receipt)
            diagnostics = (
                (failure("RESYNC_REQUIRED"),)
                if retained.receipt.revision < protocol.revision
                else ()
            )
            self._publication = TurnPublication(outcome, (), None, (), diagnostics)
            return outcome
        if sequence <= cursor.highest_committed_sequence:
            return self._rejected("RETRY_WINDOW_EXPIRED")
        if cursor.status == "retired":
            return self._rejected("STREAM_RETIRED")
        if command.expected_revision != protocol.revision:
            return self._rejected("STALE_REVISION")
        return _CheckedCommand(route, cursor, sequence, fingerprint)

    def _admit(self, command: GameCommand, route: CommandRoute) -> AdmittedCommand | TurnRejected:
        core, protocol = self._head.core, self._head.protocol
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
        if (
            admission.plan.command != command
            or admission.plan.start_tick != core.tick
            or admission.action.actor_id != command.actor_id
            or admission.action.payload != command.payload
            or target <= core.tick
        ):
            raise CandidateError("INVALID_COMMAND", "admission plan")
        if limits.enable_simulation:
            if target - core.tick > limits.max_duration_seconds:
                raise CandidateError("TURN_LIMIT", "admission duration")
        elif target != core.tick + 1:
            raise CandidateError(
                "INVALID_COMMAND", "admission plan does not describe this one-tick action"
            )
        return admission

    def _invoke(
        self,
        node: NodeKey,
        action: AdmittedAction | None,
        tick: Tick,
        wave: int,
        components: tuple[ComponentRecord, ...],
        incoming: tuple[WorldEvent, ...],
    ) -> tuple[EngineInvocation, EngineResult]:
        factory = self._factory(components)
        epoch = ViewEpoch(tick, node.phase, wave, node.engine_id, self._token)
        port = factory.open(epoch)
        try:
            invocation = EngineInvocation(
                action,
                tick,
                node.phase,
                wave,
                port,
                self._definitions,
                self._rng.scoped(tick, node.phase, wave, node.engine_id),
                incoming,
            )
            result = self._bindings[node.engine_id].engine.evaluate(invocation)
        finally:
            observed = factory.close(epoch)
        self._observations(
            observed,
            tuple(a.family for a in self._manifests[node.engine_id].reads if a.phase == node.phase),
        )
        return invocation, result

    def _stage(
        self, delta: StateDelta, node: NodeKey, tick: Tick, wave: int, root: StoredRoot
    ) -> dict[ComponentAddress, ComponentRecord]:
        reducer = self._delta_routes.get(delta.schema)
        if reducer is None or reducer.owner_id != node.engine_id:
            raise CandidateError("INVALID_DELTA", "unregistered/wrong owner")
        editor = _Editor(root, delta.target, self._io)
        factory = self._factory(root.components)
        epoch = ViewEpoch(tick, node.phase, wave, "system.reducer", self._token)
        before = factory.open(epoch)
        try:
            reducer.stage(delta, before, editor)
        finally:
            observed = factory.close(epoch)
        if any(o.operation == "write" or o.target != delta.target for o in observed):
            raise CandidateError("UNDECLARED_READ", "reducer access outside target")
        if not editor.changes:
            raise CandidateError("INVALID_DELTA", "reducer did not stage")
        return editor.changes

    def _emit(
        self,
        candidate: _Candidate,
        node: NodeKey,
        invocation: EngineInvocation,
        result: EngineResult,
    ) -> None:
        activation, manifest = self._activations[node], self._manifests[node.engine_id]
        if candidate.bus is not None:
            if (activation.lane != "A" and (result.facts or result.degraded)) or any(
                f.payload.schema not in manifest.emits for f in result.facts
            ):
                raise CandidateError("INVALID_FACT", "manifest emit rights")
            if activation.lane == "A":
                candidate.facts.extend(
                    candidate.bus.emit(
                        invocation,
                        node.engine_id,
                        self._a_ranks[node],
                        result.facts,
                        result.degraded,
                    )
                )
            return
        # Legacy one-tick mode retains its event identity, not queued-event semantics.
        for index, fact in enumerate(result.facts):
            policy = self._policies.get(fact.payload.schema)
            if (
                activation.lane != "A"
                or policy is None
                or policy.mode != "record_only"
                or node.engine_id not in policy.producers
                or fact.payload.schema not in manifest.emits
                or fact.due_tick != invocation.logical_tick
                or fact.caused_by
            ):
                raise CandidateError(
                    "INVALID_FACT", "only due-now record-only root facts supported"
                )
            self._io.encode_payload(fact.payload)
            identifier = (
                "e1-"
                + hashlib.sha256(
                    pack(
                        (
                            "event-id/v1",
                            candidate.core.world_id,
                            str(invocation.logical_tick),
                            node.phase.name,
                            "0",
                            node.engine_id,
                            str(index),
                        )
                    )
                ).hexdigest()
            )
            candidate.facts.append(
                WorldEvent(
                    EventHeader(
                        EventId(identifier),
                        fact.payload.schema,
                        node.engine_id,
                        invocation.logical_tick,
                        node.phase,
                        0,
                        self._a_ranks[node],
                        index,
                        (),
                        result.degraded,
                    ),
                    invocation.logical_tick,
                    fact.payload,
                )
            )

    def _run_barrier(
        self, candidate: _Candidate, admission: AdmittedCommand, tick: Tick, phase: Phase, wave: int
    ) -> bool:
        bus = candidate.bus
        batch = bus.due(tick, phase, wave) if bus is not None else None
        if bus is not None and batch is not None and phase == Phase.CASCADE and not batch.events:
            bus.complete(batch, ())
            return False
        deliveries: list[tuple[str, tuple[EventId, ...]]] = []
        # Every node/reducer reads pre-barrier state; publish staged component writes only below.
        root = StoredRoot(candidate.components, self._token + 1)
        phase_changes: dict[ComponentAddress, ComponentRecord] = {}
        targets: set[FieldAddress] = set()
        for node in self._schedule.nodes:
            activation = self._activations[node]
            incoming = (
                tuple(
                    e
                    for e in batch.events
                    if node.engine_id in self._policies[e.header.type_key].subscribers
                )
                if batch is not None
                else ()
            )
            action_active = (
                tick == admission.plan.target_tick
                and admission.action.payload.schema in activation.action_kinds
            )
            if node.phase != phase or not (
                activation.every_tick or action_active or activation.on_matching_events and incoming
            ):
                continue
            invocation, result = self._invoke(
                node,
                admission.action if action_active else None,
                tick,
                wave,
                candidate.components,
                incoming,
            )
            manifest = self._manifests[node.engine_id]
            for delta in result.deltas:
                if delta.target in targets:
                    raise CandidateError("DUPLICATE_TARGET", "barrier target")
                targets.add(delta.target)
                if delta.target.family not in tuple(
                    a.family for a in manifest.writes if a.phase == phase
                ):
                    raise CandidateError("UNDECLARED_WRITE", "delta outside manifest")
                phase_changes.update(self._stage(delta, node, tick, wave, root))
                candidate.changes.append(delta)
            self._emit(candidate, node, invocation, result)
            if bus is not None and incoming:
                deliveries.append((node.engine_id, tuple(e.header.event_id for e in incoming)))
        candidate.components = tuple(
            phase_changes.get(ComponentAddress(c.schema, c.entity_id), c)
            for c in candidate.components
        )
        if bus is not None and batch is not None:
            bus.complete(batch, tuple(deliveries))
        return True

    def _simulate(self, admission: AdmittedCommand) -> _Candidate:
        core = self._head.core
        limits = self._io.execution_limits
        bus = (
            CandidateEventBus(
                tuple(self._policies.values()),
                io=self._io,
                limits=limits,
                world_id=core.world_id,
                start_tick=core.tick,
                pending=core.pending,
            )
            if limits.enable_simulation
            else None
        )
        candidate = _Candidate(core, core.components, [], [], bus)
        for second in range(core.tick + 1, admission.plan.target_tick + 1):
            tick = Tick(second)
            if bus is not None:
                bus.begin_tick(tick)
            for phase in (
                Phase.PRE_TICK,
                Phase.RESOLVE,
                Phase.REACT,
                Phase.CASCADE,
                Phase.POST_TICK,
            ):
                waves = limits.cascade_waves if bus is not None and phase == Phase.CASCADE else 1
                for wave in range(waves):
                    if not self._run_barrier(candidate, admission, tick, phase, wave):
                        break
            if bus is not None:
                bus.finish_tick(tick)
        return candidate

    def _compose(self, changes: list[StateDelta]) -> tuple[StateDelta, ...]:
        net: list[StateDelta] = []
        for target in sorted(
            {d.target for d in changes},
            key=lambda a: (a.family.component, a.family.field, a.entity_id),
        ):
            group = tuple(d for d in changes if d.target == target)
            reducer = self._delta_routes[group[0].schema]
            delta = reducer.compose(group)
            self._io.encode_payload(delta)
            identity = reducer.is_identity(delta)
            if (
                type(identity) is not bool
                or delta.target != target
                or delta.schema != group[0].schema
            ):
                raise CandidateError("INVALID_DELTA", "composed delta identity/target/schema")
            if not identity:
                net.append(delta)
        return tuple(net)

    def _prepare_commit(
        self, command: GameCommand, checked: _CheckedCommand, simulation: _Candidate, target: Tick
    ) -> tuple[_Head, TurnPublication]:
        core, protocol = self._head.core, self._head.protocol
        bus = simulation.bus
        candidate = replace(
            core,
            components=simulation.components,
            tick=target,
            pending=bus.finish(target) if bus is not None else core.pending,
        )
        receipt = CommitReceipt(
            command.command_id,
            protocol.revision,
            WorldRevision(protocol.revision + 1),
            target,
            self._io.hash_core(candidate),
        )
        next_protocol = replace(
            protocol,
            revision=receipt.revision,
            streams=tuple(
                replace(s, highest_committed_sequence=checked.sequence)
                if s.stream_id == checked.cursor.stream_id
                else s
                for s in protocol.streams
            ),
            receipts=(*protocol.receipts, StoredReceipt(command, checked.fingerprint, receipt))[
                -1024:
            ],
        )
        diff = StateDiff(receipt, self._compose(simulation.changes))
        outcome = TurnCommitted(receipt)
        prepared = TurnPublication(
            outcome, tuple(simulation.facts), diff, (), bus.diagnostics if bus is not None else ()
        )
        self._io.validate_checkpoint(candidate, next_protocol)
        encoded = self._io.encode_publication(prepared)
        self._io.validate_effects(
            command, outcome, candidate, next_protocol, encoded["facts"], encoded["diff"]
        )
        return _Head(candidate, next_protocol), prepared

    def _commit(
        self, command: GameCommand, head: _Head, prepared: TurnPublication
    ) -> TurnAborted | None:
        core, protocol = self._head.core, self._head.protocol
        if self._commit_port is not None:
            durable = DurableTurn(
                DurableCheckpoint(core, protocol),
                DurableCheckpoint(head.core, head.protocol),
                command,
                prepared,
            )
            if not self._persist_durable(durable):
                self._uncertain = None
                self._blocked_code = None
                aborted = TurnAborted(failure("SAVE_UNAVAILABLE"))
                self._publication = TurnPublication(aborted, (), None, (), ())
                return aborted
        self._head = head  # Sole authoritative publication, only after proven durability.
        self._publication = prepared
        self._uncertain = None
        self._blocked_code = None
        return None

    def _submit(self, command: GameCommand) -> TurnOutcome:
        checked = self._check_command(command)
        if not isinstance(checked, _CheckedCommand):
            return checked
        try:
            admission = self._admit(command, checked.route)
            if isinstance(admission, TurnRejected):
                return admission
            simulation = self._simulate(admission)
            head, prepared = self._prepare_commit(
                command, checked, simulation, admission.plan.target_tick
            )
            aborted = self._commit(command, head, prepared)
            if aborted is not None:
                return aborted
        except WorldUnavailable:
            raise
        except Exception as error:
            # Extension failures abort private staging, never leak partial state or fake success.
            code = (
                error.code
                if isinstance(error, CandidateError)
                else "RNG_UNAVAILABLE"
                if isinstance(error, RngUnavailable)
                else "UNKNOWN_ACTOR"
                if isinstance(error, UnknownEntity)
                else "ENGINE_EXCEPTION"
            )
            self._logger.error("candidate aborted: %s", code, exc_info=True)
            aborted = TurnAborted(failure(code))
            self._publication = TurnPublication(aborted, (), None, (), ())
            return aborted
        return self._present(prepared, head.core)

    def _present(self, prepared: TurnPublication, candidate: CoreSnapshot) -> TurnOutcome:
        outcome = prepared.outcome
        assert isinstance(outcome, TurnCommitted)
        receipt, target, produced = outcome.receipt, candidate.tick, prepared.facts
        cues: list[PresentationEvent] = []
        try:
            for presenter_binding in self._presenters:
                selected = tuple(
                    f for f in produced if f.header.type_key in presenter_binding.kinds
                )
                factory = self._factory(candidate.components)
                epoch = ViewEpoch(
                    target, Phase.PRESENT, 0, presenter_binding.presenter_id, self._token
                )
                port = factory.open(epoch)
                try:
                    cues.extend(presenter_binding.presenter.map(selected, receipt, port))
                finally:
                    factory.close(epoch)
            presented = replace(prepared, cues=tuple(cues))
            self._io.encode_publication(presented)
            self._publication = presented
        except Exception:
            # Already committed: presentation failures cannot roll back simulation.
            self._logger.error("presentation failed after commit", exc_info=True)
            self._publication = replace(
                prepared, diagnostics=(*prepared.diagnostics, failure("PRESENTATION_FAILED"))
            )
        return outcome
