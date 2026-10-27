from dataclasses import replace
from typing import cast

import pytest

from app.headless import state_io
from app.npc_cycle import cycle_bundle
from contracts.encounter import GateDelta
from contracts.errors import CandidateError
from contracts.messages import EventHeader, WorldEvent
from contracts.npc_gate_aid import GateAidCue, GateAssisted
from contracts.read_views import AdapterBinding, ViewEpoch
from contracts.turn import EngineInvocation
from contracts.watch import NpcActed
from domain.encounter import GateRecord
from domain.npc_memory import NpcQuestMemoryRecord, QuestEvidence, source_identity
from domain.npc_cycle import wake_identity
from domain.primitives import EntityId, EventId, Phase, Tick
from domain.state_types import StoredRoot
from engines.encounter import EncounterActions
from orchestration.encounter import GateAdapter
from orchestration.npc_gate_aid import GateAidPayloadCodec
from orchestration.npc_memory import MemoryAdapter
from orchestration.read_views import ObservedReadViewFactory
from orchestration.turn import EmptyDefinitions, NoDrawRng
from tests.unit.quest_fixtures import content

WORLD = "w1-" + "1" * 64


def invocation(count: int = 1, opened: int = 0) -> EngineInvocation:
    selected = content()
    layout = selected.definition.layout
    evidence = (
        QuestEvidence("accepted", 2, source_identity(WORLD, 2)),
        QuestEvidence("completion_reported", 3, source_identity(WORLD, 3)),
    )[:count]
    factory = ObservedReadViewFactory(
        StoredRoot(
            (
                GateRecord(layout.gate_id, layout.space_id, layout.gate_cell, opened),
                NpcQuestMemoryRecord(layout.npc_id, evidence),
            ),
            0,
        )
    )
    AdapterBinding(GateAdapter(layout=layout)).install(factory)
    AdapterBinding(MemoryAdapter(selected)).install(factory)
    read = factory.open(ViewEpoch(Tick(4), Phase.POST_TICK, 0, "encounter.actions", 0))
    payload = NpcActed(layout.npc_id, 1, 2)
    header = EventHeader(
        EventId(wake_identity(WORLD, 4)),
        payload.schema,
        "watch.npc",
        Tick(4),
        Phase.PRE_TICK,
        0,
        0,
        0,
        (),
        (),
    )
    return EngineInvocation(
        None,
        Tick(4),
        Phase.POST_TICK,
        0,
        read,
        EmptyDefinitions(),
        NoDrawRng(),
        (WorldEvent(header, Tick(4), payload),),
    )


@pytest.mark.parametrize(
    "count,opened,acts", ((0, 0, False), (1, 0, True), (1, 1, False), (2, 0, False))
)
def test_direct_memory_and_gate_decide_real_action(count: int, opened: int, acts: bool) -> None:
    selected = content()
    layout = selected.definition.layout
    call = invocation(count, opened)
    result = EncounterActions(layout, npc_aid=True).evaluate(call)
    if acts:
        assert result.deltas == (GateDelta(layout.gate_id, 0, 1),)
        assert len(result.facts) == 1
        assert result.facts[0].payload == GateAssisted(layout.npc_id, layout.gate_id)
        assert result.facts[0].caused_by == (call.incoming[0].header.event_id,)
    else:
        assert result.deltas == ()
        assert result.facts == ()


@pytest.mark.parametrize(
    "case",
    (
        "wave",
        "missing",
        "duplicate",
        "producer",
        "phase",
        "due",
        "occurred",
        "subject",
        "bells",
        "bool_bells",
        "sequence",
        "odd_tick",
    ),
)
def test_bad_wake_rejected_before_state_change(case: str) -> None:
    call = invocation()
    event = call.incoming[0]
    payload = cast(NpcActed, event.payload)
    if case == "wave":
        call = replace(call, wave=1)
    elif case == "missing":
        call = replace(call, incoming=())
    elif case == "duplicate":
        call = replace(call, incoming=(event, event))
    elif case == "producer":
        call = replace(
            call,
            incoming=(replace(event, header=replace(event.header, producer_id="quest.rules")),),
        )
    elif case == "phase":
        call = replace(
            call, incoming=(replace(event, header=replace(event.header, phase=Phase.RESOLVE)),)
        )
    elif case == "due":
        call = replace(call, incoming=(replace(event, due_tick=Tick(2)),))
    elif case == "occurred":
        call = replace(
            call, incoming=(replace(event, header=replace(event.header, occurred_at=Tick(2))),)
        )
    elif case == "subject":
        call = replace(
            call,
            incoming=(replace(event, payload=replace(payload, npc_id=EntityId("actor:other"))),),
        )
    elif case == "bells":
        call = replace(call, incoming=(replace(event, payload=replace(payload, after_bells=3)),))
    elif case == "bool_bells":
        call = replace(
            call, incoming=(replace(event, payload=replace(payload, before_bells=True)),)
        )
    elif case == "sequence":
        call = replace(call, incoming=(replace(event, header=replace(event.header, sequence=1)),))
    else:
        call = replace(call, logical_tick=Tick(3))
    with pytest.raises(CandidateError, match="^INVALID_FACT:"):
        EncounterActions(content().definition.layout, npc_aid=True).evaluate(call)


def test_payload_roundtrips_and_exact_fields() -> None:
    selected = content()
    layout = selected.definition.layout
    for value in (
        GateAssisted(layout.npc_id, layout.gate_id),
        GateAidCue(layout.npc_id, layout.gate_id, 4),
    ):
        codec = GateAidPayloadCodec(value.schema, selected)
        encoded = codec.encode(value)
        assert codec.decode(encoded) == value
        for bad in ({**encoded, "extra": 0}, {k: v for k, v in encoded.items() if k != "npc_id"}):
            with pytest.raises(ValueError, match="^missing or unknown fields$"):
                codec.decode(bad)
    with pytest.raises(ValueError, match="^NPC_AID_PAYLOAD$"):
        GateAidPayloadCodec(GateAssisted.SCHEMA, selected).encode(
            GateAssisted(EntityId("actor:wrong"), layout.gate_id)
        )


@pytest.mark.parametrize("tick", (0, -2, True, 3, 4.0, "4"))
def test_invalid_cue_tick(tick: object) -> None:
    selected = content()
    layout = selected.definition.layout
    with pytest.raises(ValueError, match="^NPC_AID_PAYLOAD$"):
        GateAidPayloadCodec(GateAidCue.SCHEMA, selected).encode(
            GateAidCue(layout.npc_id, layout.gate_id, cast(int, tick))
        )


def test_default_schedule_identity_and_new_variant_single_gate_writer() -> None:
    selected = content()
    old = cycle_bundle(selected)
    assert old.schema_document == cycle_bundle(selected, npc_aid=False).schema_document
    assert old.rules_document == cycle_bundle(selected, npc_aid=False).rules_document
    old_io = state_io((old,))
    # Frozen from HEAD with this unit fixture (the approved catalog has a different pin).
    assert (
        old_io.pins.rules_fingerprint
        == "b05de28a3e1fcc088c19372cd29f408608c365f7389eb08d9240e1c1a69f7d48"
    )
    aid = cycle_bundle(selected, npc_aid=True)
    assert state_io((aid,)).pins != old_io.pins
    assert tuple(
        s.owner_id
        for s in aid.field_specs
        if s.family.component == "encounter.gate" and s.family.field == "is_open"
    ) == ("encounter.actions",)
    assert tuple(c.schema for c in aid.component_codecs) == tuple(
        c.schema for c in old.component_codecs
    )


@pytest.mark.parametrize("value", (0, 1, None, "1"))
def test_mode_rejects_non_bool(value: object) -> None:
    with pytest.raises(ValueError, match="^NPC_AID_CONTENT$"):
        cycle_bundle(content(), npc_aid=cast(bool, value))
