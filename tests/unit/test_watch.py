from __future__ import annotations

from dataclasses import dataclass, replace
import pytest
from typing import Callable, cast
from app.headless import state_io
from app.watch_registry import watch_bundle
from contracts.errors import CandidateError, ExpiredReadView, ReadOnlyViolation
from contracts.messages import CommandPayload, StateDelta
from contracts.read_views import ComponentPatch
from contracts.skeleton import DeltaRoute
from contracts.watch import (WATCH_NPC, LANTERN, REPLY, WaitCommand, BellCommand, WatchWake, WatchRequested, WatchEcho, NpcActed, BellRung, WatchReplied, NpcCue, BellCue, ReplyCue, ChargeDelta, BellsDelta, ReplyDelta, ChargePatch, BellsPatch, ReplyPatch)
from domain.canonical import JsonValue, array_value, canonical_json, object_value
from domain.primitives import ComponentAddress, EntityId, FrozenPayload, MAX_INT, Tick, TypeKey
from domain.trial import ACTOR_ID
from domain.watch import NPC_ID, LANTERN_ID, next_wake, recover_charge, increment_count
from orchestration.watch import WatchPayloadCodec, ChargeReducer, BellsReducer, ReplyReducer
from tests.unit.watch_fixtures import reference, session, views

SAMPLES: tuple[FrozenPayload, ...] = (WaitCommand(1), BellCommand(NPC_ID), WatchWake(NPC_ID), WatchRequested(ACTOR_ID, NPC_ID), WatchEcho(NPC_ID, 1), NpcActed(NPC_ID, 0, 1), BellRung(ACTOR_ID, NPC_ID), WatchReplied(NPC_ID, 0, 1), NpcCue(NPC_ID, Tick(2), 0, 1, 6, 0, 2000), BellCue(ACTOR_ID, NPC_ID, Tick(1)), ReplyCue(NPC_ID, Tick(1), 0, 1), ChargeDelta(LANTERN_ID, 0, 3), BellsDelta(NPC_ID, 0, 8), ReplyDelta(NPC_ID, 0, 8), ChargePatch(3), BellsPatch(8), ReplyPatch(8))


def test_literal_pins() -> None:
    io = state_io((watch_bundle(),))
    pins = (io.pins.schema_fingerprint, io.pins.rules_fingerprint, io.pins.schedule_fingerprint)
    assert pins == tuple(object_value(d)["sha256"] for d in array_value(reference("literal_documents")))
    assert io.hash_core(session().snapshot()) == reference("initial_core_hash")
    assert (len(watch_bundle().codecs), len(watch_bundle().field_specs), len(io.schedule.nodes)) == (40, 16, 7)


@pytest.mark.parametrize("payload", SAMPLES)
def test_records_payloads(payload: FrozenPayload) -> None:
    codec = WatchPayloadCodec(payload.schema)
    data = codec.encode(payload)
    assert codec.decode(data) == payload
    with pytest.raises(ValueError):
        codec.decode({**data, "foreign": 1})
    for field in data:
        with pytest.raises(ValueError):
            codec.decode({k: v for k, v in data.items() if k != field})
    for field, old in data.items():
        bad: tuple[JsonValue, ...] = (True, cast(JsonValue, 0.0), -1, MAX_INT + 1) if type(old) is int else ("", "invalid space", "e\u0301")
        for value in bad:
            with pytest.raises(ValueError):
                codec.decode({**data, field: value})
    with pytest.raises(ValueError):
        WatchPayloadCodec(TypeKey(payload.schema.kind, 2))


@dataclass(frozen=True, slots=True)
class _ForeignWait(CommandPayload):
    seconds: int
    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.wait", 1)


def test_class_and_arithmetic() -> None:
    with pytest.raises(ValueError):
        WatchPayloadCodec(TypeKey("watch.wait", 1)).encode(_ForeignWait(1))
    for payload in (NpcActed(NPC_ID, 0, 2), WatchReplied(NPC_ID, 1, 1), NpcCue(NPC_ID, Tick(3), 0, 1, 6, 0, 2000), BellRung(EntityId("actor:other"), NPC_ID)):
        with pytest.raises(ValueError):
            WatchPayloadCodec(payload.schema).encode(payload)
    assert next_wake(0) == 2 and next_wake(1) == 2 and next_wake(2) == 4
    assert next_wake(MAX_INT - 2) == MAX_INT - 1
    for tick in (-1, True, MAX_INT - 1, MAX_INT):
        with pytest.raises(ValueError):
            next_wake(tick)
    assert recover_charge(3) == 3 and increment_count(0, 512) == 512
    with pytest.raises(ValueError):
        increment_count(MAX_INT)


def test_observed_reads() -> None:
    factory, epoch = views()
    port = factory.open(epoch)
    npc = port.component(WATCH_NPC, NPC_ID)
    lantern = port.component(LANTERN, LANTERN_ID)
    reply = port.component(REPLY, NPC_ID)
    assert (npc.space_id, npc.cell, npc.bells, lantern.charge, reply.count) == ("space:trial", 6, 0, 0, 0)
    with pytest.raises(ReadOnlyViolation):
        setattr(npc, "bells", 1)
    with pytest.raises(ReadOnlyViolation):
        delattr(lantern, "charge")
    observations = factory.close(epoch)
    assert {o.target.family.field for o in observations if o.operation == "read"} == {"space_id", "cell", "bells", "charge", "count"}
    assert sum(o.operation == "write" for o in observations) == 2
    readers: tuple[Callable[[], int], ...] = (lambda: npc.bells, lambda: lantern.charge, lambda: reply.count)
    for read in readers:
        with pytest.raises(ExpiredReadView):
            read()


class _Editor:
    def __init__(self) -> None:
        self.patches: list[tuple[ComponentAddress, ComponentPatch]] = []
    def apply_patch(self, address: ComponentAddress, patch: ComponentPatch) -> None:
        self.patches.append((address, patch))


@pytest.mark.parametrize("reducer,delta,following", ((ChargeReducer(), ChargeDelta(LANTERN_ID, 0, 1), ChargeDelta(LANTERN_ID, 1, 2)), (BellsReducer(), BellsDelta(NPC_ID, 0, 1), BellsDelta(NPC_ID, 1, 2)), (ReplyReducer(), ReplyDelta(NPC_ID, 0, 1), ReplyDelta(NPC_ID, 1, 2))))
def test_scalar_reducers(reducer: DeltaRoute, delta: StateDelta, following: StateDelta) -> None:
    factory, epoch = views()
    before = factory.open(epoch)
    editor = _Editor()
    try:
        reducer.stage(delta, before, editor)
    finally:
        observed = factory.close(epoch)
    assert len(editor.patches) == 1 and all(o.target == delta.target and o.operation == "read" for o in observed)
    net = reducer.compose((delta, following))
    assert not reducer.is_identity(net) and net.target == delta.target
    with pytest.raises(CandidateError):
        reducer.compose(())
    with pytest.raises(CandidateError):
        reducer.compose((following, delta))
    factory, epoch = views()
    before = factory.open(epoch)
    try:
        with pytest.raises(CandidateError):
            reducer.stage(following, before, _Editor())
    finally:
        factory.close(epoch)
    io = state_io((watch_bundle(),))
    original = next(r for r in session().snapshot().components if r.entity_id == delta.target.entity_id and r.schema.kind == delta.target.family.component)
    address, patch = editor.patches[0]
    assert io.apply_patch(address, delta.target, original, patch) != original
    with pytest.raises(CandidateError):
        io.apply_patch(replace(address, entity_id=EntityId("actor:other")), delta.target, original, patch)


def test_registry_ownership() -> None:
    selected = watch_bundle()
    for reducer in selected.delta_routes:
        assert reducer.owner_id in {b.engine.manifest.engine_id for b in selected.bindings}
    assert canonical_json(selected.schema_document) == canonical_json(reference("schema_document"))
