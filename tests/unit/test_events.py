from __future__ import annotations

from dataclasses import replace
import hashlib
import pytest
from app.headless import state_io
from app.watch_registry import watch_bundle
from contracts.errors import CandidateError
from contracts.events import QueuedEvent
from contracts.messages import EmittedFact, EventHeader, WorldEvent
from contracts.turn import EngineInvocation
from contracts.watch import WatchRequested, WatchWake, NpcActed
from domain.canonical import JsonValue, array_value, canonical_json, decode_json, object_value, pack
from domain.primitives import EventId, Phase, Tick
from domain.state_types import PendingDocument
from domain.trial import ACTOR_ID
from domain.watch import NPC_ID
from orchestration.events import CandidateEventBus, queued_sort_key
from orchestration.turn import EmptyDefinitions, NoDrawRng
from tests.unit.watch_fixtures import reference, session, views


def request(sequence: int, due: int = 8) -> QueuedEvent:
    world = session().snapshot().world_id
    identifier = EventId("e1-" + hashlib.sha256(pack(("event-id/v1", world, "1", "RESOLVE", "0", "watch.bell", str(sequence)))).hexdigest())
    payload = WatchRequested(ACTOR_ID, NPC_ID)
    return QueuedEvent(WorldEvent(EventHeader(identifier, payload.schema, "watch.bell", Tick(1), Phase.RESOLVE, 0, 3, sequence, (), ()), Tick(due), payload), Phase.REACT, 20)


def test_pending_roundtrip_and_leaf_hash() -> None:
    io = state_io((watch_bundle(),))
    core = session().snapshot()
    document = core.pending[0]
    q = io.decode_pending(document)
    assert io.encode_pending(q) == document
    assert io.decode_core(io.encode_core(core)) == core
    altered = io.encode_pending(replace(q, event=replace(q.event, due_tick=Tick(4))))
    assert io.hash_core(replace(core, pending=(altered,))) != reference("initial_core_hash")
    with pytest.raises(ValueError):
        io.decode_pending(PendingDocument(document.canonical_event_json + b" "))
    value = object_value(decode_json(document.canonical_event_json))
    for changed in ({**value, "priority": True}, {**value, "priority": 11}, {**value, "delivery_phase": "REACT"}, {**value, "unexpected": 1}):
        with pytest.raises(ValueError):
            io.decode_pending(PendingDocument(canonical_json(changed)))
    event = object_value(value["event"])
    header = object_value(event["header"])
    changes: tuple[tuple[str, JsonValue], ...] = (("wave", 1), ("producer_rank", 1), ("sequence", True), ("caused_by", (header["event_id"],)), ("type_key", {"kind": "watch.npc-acted", "version": 1}), ("event_id", "e1-"+"f"*64))
    for key, val in changes:
        raw = PendingDocument(canonical_json({**value, "event": {**event, "header": {**header, key: val}}}))
        with pytest.raises(ValueError):
            io.encode_core(replace(core, pending=(raw,)))
    with pytest.raises(ValueError):
        io.encode_core(replace(core, tick=Tick(2)))
    with pytest.raises(ValueError):
        io.decode_pending(PendingDocument(document.canonical_event_json.replace(b'"priority":10', b'"priority":10,"priority":10')))


def test_queue_order() -> None:
    io = state_io((watch_bundle(),))
    input_docs = tuple(PendingDocument(canonical_json(q)) for q in array_value(reference("ordering_input")))
    queue = tuple(io.decode_pending(d) for d in input_docs)
    assert tuple(object_value(decode_json(io.encode_pending(q).canonical_event_json)) for q in sorted(queue, key=queued_sort_key)) == array_value(reference("ordering_expected"))
    core = replace(session().snapshot(), tick=Tick(7), pending=input_docs)
    with pytest.raises(ValueError):
        io.encode_core(core)
    canonical_docs = tuple(io.encode_pending(q) for q in sorted(queue, key=queued_sort_key))
    assert io.decode_core(io.encode_core(replace(core, pending=canonical_docs))).pending == canonical_docs
    bus = CandidateEventBus(watch_bundle().events, io=io, limits=io.execution_limits, world_id=core.world_id, start_tick=Tick(7), pending=canonical_docs)
    bus.begin_tick(Tick(8))
    batch = bus.due(Tick(8), Phase.REACT, 0)
    assert batch.events == tuple(q.event for q in sorted(queue, key=queued_sort_key))
    assert bus.due(Tick(8), Phase.REACT, 0) is batch
    bus.complete(batch, (("watch.respond", tuple(e.header.event_id for e in batch.events)),))
    assert bus.finish(Tick(8)) == ()


@pytest.mark.parametrize("duplicate", (False, True))
def test_delivery_coverage(duplicate: bool) -> None:
    io = state_io((watch_bundle(),))
    core = session().snapshot()
    bus = CandidateEventBus(watch_bundle().events, io=io, limits=io.execution_limits, world_id=core.world_id, start_tick=Tick(1), pending=core.pending)
    bus.begin_tick(Tick(2))
    batch = bus.due(Tick(2), Phase.PRE_TICK, 0)
    delivery = ("watch.npc", (batch.events[0].header.event_id,))
    with pytest.raises(CandidateError) as error:
        bus.complete(batch, (delivery, delivery) if duplicate else ())
    assert error.value.code == ("DUPLICATE_DELIVERY" if duplicate else "UNDELIVERED_EVENT")
    assert core.pending == session().snapshot().pending
    bus.complete(batch, (delivery,))
    with pytest.raises(CandidateError) as error:
        bus.complete(batch, (delivery,))
    assert error.value.code == "DUPLICATE_DELIVERY"


@pytest.mark.parametrize("case", ("past", "late", "unknown", "self", "future", "duplicate"))
def test_routing_causes_and_late(case: str) -> None:
    io = state_io((watch_bundle(),))
    core = session().snapshot()
    future = io.encode_pending(replace(io.decode_pending(core.pending[0]), event=replace(io.decode_pending(core.pending[0]).event, due_tick=Tick(10))))
    bus = CandidateEventBus(watch_bundle().events, io=io, limits=io.execution_limits, world_id=core.world_id, start_tick=Tick(2), pending=(future,))
    bus.begin_tick(Tick(3))
    factory, epoch = views(phase=Phase.PRE_TICK, tick=3)
    port = factory.open(epoch)
    invocation = EngineInvocation(None, Tick(3), Phase.PRE_TICK, 0, port, EmptyDefinitions(), NoDrawRng(), ())
    due = 2 if case == "past" else 3 if case == "late" else 4
    causes: tuple[EventId, ...] = ()
    if case in ("unknown", "self"):
        identifier = "e1-"+hashlib.sha256(pack(("event-id/v1", core.world_id, "3", "PRE_TICK", "0", "watch.npc", "0"))).hexdigest() if case == "self" else "e1-"+"f"*64
        causes = (EventId(identifier),)
    elif case == "future":
        causes = (io.decode_pending(core.pending[0]).event.header.event_id,)
    try:
        if case == "duplicate":
            bus.emit(invocation, "watch.npc", 0, (EmittedFact(WatchWake(NPC_ID), Tick(due), ()),))
        with pytest.raises(CandidateError) as error:
            bus.emit(invocation, "watch.npc", 0, (EmittedFact(WatchWake(NPC_ID), Tick(due), causes),))
        assert error.value.code == {"past": "EVENT_PAST_DUE", "late": "EVENT_LATE", "duplicate": "DUPLICATE_EVENT"}.get(case, "INVALID_CAUSE")
    finally:
        factory.close(epoch)


@pytest.mark.parametrize("count", (512, 513))
def test_limits(count: int) -> None:
    io = state_io((watch_bundle(),))
    bus = CandidateEventBus(watch_bundle().events, io=io, limits=io.execution_limits, world_id=session().snapshot().world_id, start_tick=Tick(0), pending=())
    bus.begin_tick(Tick(1))
    factory, epoch = views(phase=Phase.PRE_TICK, tick=1)
    port = factory.open(epoch)
    invocation = EngineInvocation(None, Tick(1), Phase.PRE_TICK, 0, port, EmptyDefinitions(), NoDrawRng(), ())
    drafts = tuple(EmittedFact(NpcActed(NPC_ID, 0, 1), Tick(1), ()) for _ in range(count))
    try:
        if count == 513:
            with pytest.raises(CandidateError) as error:
                bus.emit(invocation, "watch.npc", 0, drafts)
            assert error.value.code == "EVENT_LIMIT"
        else:
            assert len(bus.emit(invocation, "watch.npc", 0, drafts)) == 512
            with pytest.raises(CandidateError) as error:
                bus.emit(invocation, "watch.npc", 0, drafts[:1])
            assert error.value.code == "EVENT_LIMIT"
            assert bus.finish(Tick(1)) == ()
    finally:
        factory.close(epoch)


def test_pending_limit() -> None:
    io = state_io((watch_bundle(),))
    # Conforming generic queue ports;the prototype checkpoint itself only permits one Wake.
    world = session().snapshot().world_id
    q = request(0)
    docs: list[PendingDocument] = []
    for seq in range(4096):
        identifier = EventId("e1-"+hashlib.sha256(pack(("event-id/v1", world, str(seq // 512 + 1), "RESOLVE", "0", "watch.bell", str(seq % 512)))).hexdigest())
        event = replace(q.event, header=replace(q.event.header, event_id=identifier, occurred_at=Tick(seq // 512 + 1), sequence=seq % 512), due_tick=Tick(20))
        docs.append(io.encode_pending(replace(q, event=event)))
    bus = CandidateEventBus(watch_bundle().events, io=io, limits=io.execution_limits, world_id=world, start_tick=Tick(9), pending=tuple(docs))
    bus.begin_tick(Tick(10))
    factory, epoch = views(phase=Phase.PRE_TICK, tick=10)
    port = factory.open(epoch)
    try:
        invocation = EngineInvocation(None, Tick(10), Phase.PRE_TICK, 0, port, EmptyDefinitions(), NoDrawRng(), ())
        with pytest.raises(CandidateError) as error:
            bus.emit(invocation, "watch.npc", 0, (EmittedFact(WatchWake(NPC_ID), Tick(22), ()),))
        assert error.value.code == "EVENT_QUEUE_LIMIT"
    finally:
        factory.close(epoch)
    with pytest.raises(CandidateError):
        CandidateEventBus(watch_bundle().events, io=io, limits=io.execution_limits, world_id=world, start_tick=Tick(9), pending=(*docs, docs[0]))


def test_full_queue_delivery_releases_capacity() -> None:
    io = state_io((watch_bundle(),))
    world = session().snapshot().world_id
    q = request(0)
    docs: list[PendingDocument] = []
    for seq in range(4096):
        tick, index = seq//512+1, seq%512
        identifier = EventId("e1-"+hashlib.sha256(pack(("event-id/v1", world, str(tick), "RESOLVE", "0", "watch.bell", str(index)))).hexdigest())
        event = replace(q.event, header=replace(q.event.header, event_id=identifier, occurred_at=Tick(tick), sequence=index), due_tick=Tick(20))
        docs.append(io.encode_pending(replace(q, event=event)))
    bus = CandidateEventBus(watch_bundle().events, io=io, limits=io.execution_limits, world_id=world, start_tick=Tick(19), pending=tuple(docs))
    bus.begin_tick(Tick(20))
    batch = bus.due(Tick(20), Phase.REACT, 0)
    factory, epoch = views(phase=Phase.REACT, tick=20)
    port = factory.open(epoch)
    try:
        from contracts.watch import WatchEcho
        invocation = EngineInvocation(None, Tick(20), Phase.REACT, 0, port, EmptyDefinitions(), NoDrawRng(), batch.events)
        emitted = bus.emit(invocation, "watch.respond", 4, (EmittedFact(WatchEcho(NPC_ID, 1), Tick(22), (batch.events[0].header.event_id,)),))
        assert len(emitted) == 1
        bus.complete(batch, (("watch.respond", tuple(e.header.event_id for e in batch.events)),))
        pending = bus.finish(Tick(20))
        assert len(pending) == 1 and io.decode_pending(pending[0]).event == emitted[0]
    finally:
        factory.close(epoch)
