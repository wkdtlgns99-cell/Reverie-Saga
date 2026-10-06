from __future__ import annotations

import hashlib
import re
from contracts.events import DeliveryBatch, ExecutionLimits, QueuedEvent
from contracts.errors import CandidateError
from contracts.messages import EmittedFact, EventHeader, EventPolicy, FactPayload, WorldEvent
from contracts.state_io import StateIO
from contracts.turn import Degradation, EngineInvocation, Failure, failure
from domain.canonical import pack
from domain.primitives import EventId, Phase, Tick, require_integer
from domain.state_types import PendingDocument


def queued_sort_key(event: QueuedEvent) -> tuple[int, int, int, int, int, int, int, int, str]:
    h = event.event.header
    return (event.event.due_tick, int(event.delivery_phase), event.priority, h.occurred_at, int(h.phase), h.wave, h.producer_rank, h.sequence, h.event_id)


class CandidateEventBus:
    def __init__(self, policies: tuple[EventPolicy, ...], *, io: StateIO,
                 limits: ExecutionLimits, world_id: str, start_tick: Tick,
                 pending: tuple[PendingDocument, ...]) -> None:
        self._policies = {p.schema: p for p in policies}
        self._io = io
        self._limits = limits
        self._world = world_id
        self._tick = start_tick
        self._items = {q.event.header.event_id: (q, 0) for q in (io.decode_pending(d) for d in pending)}
        if len(self._items) != len(pending) or len(pending) > limits.max_pending:
            raise CandidateError("EVENT_QUEUE_LIMIT", "initial queue")
        self._ids = set(self._items)
        self._known: set[EventId] = set()
        self._count = 0
        self._batches: dict[tuple[Tick, Phase, int], DeliveryBatch] = {}
        self._completed: set[tuple[Tick, Phase, int]] = set()
        self._active: DeliveryBatch | None = None
        self._diagnostics: list[Failure] = []
        self._started = False

    @property
    def diagnostics(self) -> tuple[Failure, ...]:
        return tuple(self._diagnostics)

    def begin_tick(self, logical_tick: Tick) -> None:
        require_integer(logical_tick)
        if logical_tick != self._tick + 1 or self._active is not None:
            raise CandidateError("UNDELIVERED_EVENT", "tick transition")
        self._tick = logical_tick
        self._count = 0
        self._started = True

    def due(self, logical_tick: Tick, phase: Phase, wave: int) -> DeliveryBatch:
        require_integer(wave)
        if logical_tick != self._tick or not self._started or type(phase) is not Phase or phase not in (Phase.PRE_TICK, Phase.RESOLVE, Phase.REACT, Phase.CASCADE, Phase.POST_TICK):
            raise CandidateError("UNDELIVERED_EVENT", "barrier time/phase")
        if wave >= self._limits.cascade_waves or (phase != Phase.CASCADE and wave != 0):
            raise CandidateError("CASCADE_LIMIT", "barrier wave")
        key = (logical_tick, phase, wave)
        if key in self._completed:
            raise CandidateError("DUPLICATE_DELIVERY", "completed barrier")
        if self._active is not None and self._active != self._batches.get(key):
            raise CandidateError("UNDELIVERED_EVENT", "uncompleted barrier")
        if key not in self._batches:
            selected = sorted((q for q, w in self._items.values() if q.event.due_tick == logical_tick and q.delivery_phase == phase and w == wave), key=queued_sort_key)
            self._batches[key] = DeliveryBatch(logical_tick, phase, wave, tuple(q.event for q in selected))
        batch = self._batches[key]
        self._active = batch
        self._known.update(e.header.event_id for e in batch.events)
        return batch

    def emit(self, invocation: EngineInvocation, producer_id: str, producer_rank: int,
             facts: tuple[EmittedFact, ...], degraded: tuple[Degradation, ...] = ()) -> tuple[WorldEvent, ...]:
        if invocation.logical_tick != self._tick or not self._started or type(facts) is not tuple or type(degraded) is not tuple or degraded or type(invocation.phase) is not Phase:
            raise CandidateError("INVALID_FACT", "emission context")
        result: list[WorldEvent] = []
        for sequence, fact in enumerate(facts):
            policy = self._policies.get(fact.payload.schema)
            if policy is None or producer_id not in policy.producers or not isinstance(fact.payload, FactPayload):
                raise CandidateError("INVALID_FACT", "producer/payload")
            try:
                self._io.encode_payload(fact.payload)
                require_integer(fact.due_tick)
                require_integer(producer_rank)
                require_integer(invocation.wave, 0, self._limits.cascade_waves - 1)
            except (ValueError, TypeError) as error:
                raise CandidateError("INVALID_FACT", "event draft") from error
            if self._count >= self._limits.max_events_per_tick:
                raise CandidateError("EVENT_LIMIT", "tick emissions")
            identifier = EventId("e1-" + hashlib.sha256(pack(("event-id/v1", self._world, str(self._tick), invocation.phase.name, str(invocation.wave), producer_id, str(sequence)))).hexdigest())
            if identifier in self._ids:
                raise CandidateError("DUPLICATE_EVENT", "event identity")
            causes = fact.caused_by
            if type(causes) is not tuple or any(type(c) is not str for c in causes):
                raise CandidateError("INVALID_CAUSE", "cause DTO")
            if causes != tuple(sorted(set(causes))) or identifier in causes or any(type(c) is not str or re.fullmatch("e1-[0-9a-f]{64}", c) is None or c not in self._known for c in causes):
                raise CandidateError("INVALID_CAUSE", "unknown/future/self/noncanonical cause")
            due, wave = fact.due_tick, 0
            if policy.mode == "record_only":
                if due != self._tick:
                    raise CandidateError("INVALID_FACT", "record due")
            elif due < self._tick:
                raise CandidateError("EVENT_PAST_DUE", "simulated due")
            elif due == self._tick:
                if invocation.phase == policy.delivery_phase == Phase.CASCADE:
                    wave = invocation.wave + 1
                    if wave >= self._limits.cascade_waves:
                        raise CandidateError("CASCADE_LIMIT", "nonempty next wave")
                elif policy.delivery_phase <= invocation.phase:
                    if policy.late_route != "next_tick":
                        raise CandidateError("EVENT_LATE", "phase passed")
                    try:
                        require_integer(self._tick + 1)
                    except ValueError as error:
                        raise CandidateError("INTEGER_OVERFLOW", "late route") from error
                    due = Tick(self._tick + 1)
                    self._diagnostics.append(failure("EVENT_DEFERRED"))
            event = WorldEvent(EventHeader(identifier, fact.payload.schema, producer_id, self._tick, invocation.phase, invocation.wave, producer_rank, sequence, causes, ()), due, fact.payload)
            if policy.mode == "simulate":
                self._items[identifier] = (QueuedEvent(event, policy.delivery_phase, policy.priority), wave)
                excluded = {e.header.event_id for e in self._active.events} if self._active is not None else set()
                if len(self._items.keys() - excluded) > self._limits.max_pending:
                    raise CandidateError("EVENT_QUEUE_LIMIT", "pending cap")
            self._ids.add(identifier)
            self._known.add(identifier)
            self._count += 1
            result.append(event)
        return tuple(result)

    def complete(self, batch: DeliveryBatch, deliveries: tuple[tuple[str, tuple[EventId, ...]], ...]) -> None:
        key = (batch.logical_tick, batch.phase, batch.wave)
        if key in self._completed:
            raise CandidateError("DUPLICATE_DELIVERY", "completed batch")
        if batch != self._active:
            raise CandidateError("UNDELIVERED_EVENT", "unknown batch")
        expected = {(subscriber, e.header.event_id) for e in batch.events for subscriber in self._policies[e.header.type_key].subscribers}
        actual = [(engine, identifier) for engine, ids in deliveries for identifier in ids]
        if len(actual) != len(set(actual)) or len({engine for engine, _ in deliveries}) != len(deliveries):
            raise CandidateError("DUPLICATE_DELIVERY", "duplicate acknowledgment")
        if set(actual) != expected:
            raise CandidateError("UNDELIVERED_EVENT", "subscriber coverage")
        for e in batch.events:
            del self._items[e.header.event_id]
        if len(self._items) > self._limits.max_pending:
            raise CandidateError("EVENT_QUEUE_LIMIT", "completed queue")
        self._completed.add(key)
        self._active = None

    def finish_tick(self, logical_tick: Tick) -> None:
        if logical_tick != self._tick or self._active is not None or any(q.event.due_tick <= logical_tick for q, _ in self._items.values()):
            raise CandidateError("UNDELIVERED_EVENT", "stranded event")

    def finish(self, target_tick: Tick) -> tuple[PendingDocument, ...]:
        self.finish_tick(target_tick)
        return tuple(self._io.encode_pending(q) for q, _ in sorted(self._items.values(), key=lambda item: queued_sort_key(item[0])))
