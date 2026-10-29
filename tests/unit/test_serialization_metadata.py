"""Metadata reuse must retain actual per-record and producer validation."""

from dataclasses import dataclass, replace
import hashlib
from typing import cast

import pytest

from app.headless import state_io
from app.npc_cycle import cycle_bundle
from app.watch_registry import watch_bundle
from contracts.errors import BootstrapError, SchemaError
from contracts.messages import EventHeader
from contracts.turn import (
    CapabilityManifest,
    EngineBinding,
    EngineInvocation,
    EngineResult,
    NodeActivation,
    NodeKey,
)
from domain.canonical import (
    array_value,
    JsonObject,
    canonical_json,
    object_value,
    pack,
    decode_json,
)
from domain.primitives import EntityId, EventId, Phase, Tick
from domain.state_types import ComponentRecord, PendingDocument
from orchestration.serialization import RegisteredStateIO, header_document
from tests.unit.quest_fixtures import content
from tests.unit.registered_io_fixtures import ACTOR, VALUE, GaugeCodec, GaugeRecord, bundle, session
from tests.unit.watch_fixtures import session as watch_session


class CountedCodec(GaugeCodec):
    def __init__(self) -> None:
        self.encodes = 0
        self.decodes = 0

    def encode(self, record: ComponentRecord) -> JsonObject:
        self.encodes += 1
        return super().encode(record)

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        self.decodes += 1
        return super().decode(entity_id, fields)


@dataclass(frozen=True, slots=True)
class Observer:
    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest("aaa.observer", (Phase.PRE_TICK,), (), (), (), (), (), "constant")

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        return EngineResult((), (), ())


def test_two_states_use_fresh_codec_checks_and_own_exact_fields() -> None:
    codec = CountedCodec()
    io = state_io((replace(bundle(), component_codecs=(codec,)),))
    first = session(value=2).snapshot()
    second = replace(first, components=(GaugeRecord(ACTOR, 5, "계기"),))
    assert io.encode_core(first)["components"] == (
        {
            "schema": {"kind": "fixture.gauge", "version": 1},
            "entity_id": ACTOR,
            "fields": {"value": 2, "label": "계기"},
        },
    )
    assert io.encode_core(second)["components"] == (
        {
            "schema": {"kind": "fixture.gauge", "version": 1},
            "entity_id": ACTOR,
            "fields": {"value": 5, "label": "계기"},
        },
    )
    assert (codec.encodes, codec.decodes) == (4, 2)
    assert first.components == (GaugeRecord(ACTOR, 2, "계기"),)


@pytest.mark.parametrize("value", (True, 10, -10))
def test_invalid_state_is_not_hidden_after_valid_state(value: int) -> None:
    io = state_io((bundle(),))
    core = session().snapshot()
    io.encode_core(core)
    bad = replace(core, components=(GaugeRecord(ACTOR, value, "계기"),))
    with pytest.raises(SchemaError, match="^INVALID_COMPONENT:"):
        io.encode_core(bad)
    assert io.decode_core(io.encode_core(core)) == core


@pytest.mark.parametrize(
    "rank,message",
    (
        (1, "unregistered event producer/rank"),
        (-1, "integer outside declared range"),
        (True, "integer required"),
        ("0", "integer required"),
    ),
)
def test_pending_rank_rejection_is_unchanged(rank: object, message: str) -> None:
    io = state_io((watch_bundle(),))
    raw = object_value(decode_json(watch_session().snapshot().pending[0].canonical_event_json))
    event = object_value(raw["event"])
    header = object_value(event["header"])
    # Rejected raw boundary values are deliberately injected before decoding.
    body = canonical_json(
        {**raw, "event": {**event, "header": {**header, "producer_rank": cast(int, rank)}}}
    )
    with pytest.raises(ValueError, match="^" + message + "$"):
        io.decode_pending(PendingDocument(body))


def test_b_node_before_first_a_node_does_not_shift_rank_zero() -> None:
    old = watch_bundle()
    extra = EngineBinding(
        Observer(),
        __name__,
        (NodeActivation(NodeKey(Phase.PRE_TICK, "aaa.observer"), (), False, True, "B"),),
    )
    io = state_io((replace(old, bindings=(*old.bindings, extra)),))
    assert io.schedule.nodes[0] == NodeKey(Phase.PRE_TICK, "aaa.observer")
    document = watch_session().snapshot().pending[0]
    event = io.decode_pending(document)
    assert event.event.header.producer_rank == 0
    assert event.event.header.producer_id == "watch.npc"
    assert io.encode_pending(event) == document


def test_same_engine_in_two_phases_has_distinct_exact_event_ranks() -> None:
    io = cast(RegisteredStateIO, state_io((cycle_bundle(content(), npc_aid=True),)))
    nodes = tuple(n for n in io.schedule.nodes if n.engine_id == "encounter.actions")
    assert {n.phase for n in nodes} == {Phase.RESOLVE, Phase.POST_TICK}
    # Different phase keys are required even for the same producer identity.
    ranks = {node: index for index, node in enumerate(io.schedule.nodes)}
    assert ranks[nodes[0]] != ranks[nodes[1]]
    from contracts.encounter import GateChanged
    from contracts.npc_gate_aid import GateAssisted

    selected = content().definition.layout
    for node in nodes:
        payload = (
            GateChanged(selected.actor_id, selected.gate_id, 0, 1)
            if node.phase == Phase.RESOLVE
            else GateAssisted(selected.npc_id, selected.gate_id)
        )
        causes = () if node.phase == Phase.RESOLVE else (EventId("e1-" + "2" * 64),)
        identifier = (
            "e1-"
            + hashlib.sha256(
                pack(
                    (
                        "event-id/v1",
                        "w1-" + "1" * 64,
                        "4",
                        node.phase.name,
                        "0",
                        node.engine_id,
                        "0",
                    )
                )
            ).hexdigest()
        )
        header = EventHeader(
            EventId(identifier),
            payload.schema,
            node.engine_id,
            Tick(4),
            node.phase,
            0,
            ranks[node],
            0,
            causes,
            (),
        )
        body: JsonObject = {
            "header": header_document(header),
            "due_tick": 4,
            "payload": io.encode_payload(payload),
        }
        assert io._event(body).header == header
        other = next(ranks[n] for n in nodes if n != node)
        with pytest.raises(ValueError, match="^unregistered event producer/rank$"):
            io._event({**body, "header": {**header_document(header), "producer_rank": other}})


def test_component_bounds_remain_per_io_for_the_same_schema() -> None:
    wide = bundle()
    schema = dict(wide.schema_document)
    component = object_value(array_value(schema["components"])[0])
    fields = dict(object_value(component["fields"]))
    fields["value"] = {**object_value(fields["value"]), "maximum": 8}
    schema["components"] = ({**component, "fields": fields},)
    narrow = replace(
        wide,
        schema_document=schema,
        field_specs=tuple(
            replace(s, maximum=8) if s.family == VALUE else s for s in wide.field_specs
        ),
    )
    wide_io, narrow_io = state_io((wide,)), state_io((narrow,))
    wide_core, narrow_core = session(wide, value=8).snapshot(), session(narrow, value=8).snapshot()
    assert wide_io.pins != narrow_io.pins
    nine = GaugeRecord(ACTOR, 9, "계기")
    assert wide_io.decode_core(
        wide_io.encode_core(replace(wide_core, components=(nine,)))
    ).components == (nine,)
    with pytest.raises(SchemaError, match="^INVALID_COMPONENT:"):
        narrow_io.encode_core(replace(narrow_core, components=(nine,)))
    assert narrow_io.decode_core(narrow_io.encode_core(narrow_core)) == narrow_core


@pytest.mark.parametrize("mode", ("bool_scale", "reversed_bounds", "missing_descriptor_field"))
def test_invalid_registration_still_rejects_before_use(mode: str) -> None:
    base = bundle()
    if mode == "bool_scale":
        base = replace(
            base,
            field_specs=tuple(
                replace(s, scale=True) if s.family == VALUE else s for s in base.field_specs
            ),
        )
    elif mode == "reversed_bounds":
        base = replace(
            base,
            field_specs=tuple(
                replace(s, minimum=10) if s.family == VALUE else s for s in base.field_specs
            ),
        )
    else:
        schema = dict(base.schema_document)
        component = object_value(array_value(schema["components"])[0])
        schema["components"] = (
            {**component, "fields": {"value": object_value(component["fields"])["value"]}},
        )
        base = replace(base, schema_document=schema)
    with pytest.raises(BootstrapError, match="^DUPLICATE_SCHEMA:"):
        state_io((base,))
