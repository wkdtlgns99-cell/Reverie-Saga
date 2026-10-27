"""Independent call-source boundaries and opt-in presentation contracts."""

from dataclasses import replace
from typing import cast

import pytest

from app.headless import state_io
from app.npc_cycle import cycle_bundle
from contracts.encounter import GateDelta
from contracts.errors import CandidateError
from contracts.messages import EventHeader, WorldEvent
from contracts.npc_gate_aid import GateAidCue
from contracts.read_views import AdapterBinding, ViewEpoch
from contracts.turn import EngineInvocation, PhaseAccess
from contracts.watch import REPLY, NpcActed, WatchReplied
from domain.encounter import GateRecord
from domain.npc_memory import NpcQuestMemoryRecord, QuestEvidence, source_identity
from domain.npc_cycle import wake_identity
from domain.primitives import EntityId, EventId, FieldFamily, Phase, Tick, TypeKey
from domain.state_types import StoredRoot
from domain.watch import ReplyRecord
from engines.encounter import EncounterActions
from orchestration.encounter import EncounterPresenter, GateAdapter
from orchestration.npc_cycle import CycleAdapter
from orchestration.npc_gate_aid import GateAidPayloadCodec
from orchestration.npc_memory import MemoryAdapter
from orchestration.read_views import ObservedReadViewFactory
from orchestration.turn import EmptyDefinitions, NoDrawRng
from orchestration.watch import ReplyAdapter
from tests.unit.quest_fixtures import content
from tests.unit.test_npc_cycle import WORLD, record_at


def invocation(tick: int = 9, *, heard: int = 1, opened: int = 0) -> EngineInvocation:
    selected = content()
    layout = selected.definition.layout
    entries = (
        QuestEvidence("accepted", 2, source_identity(WORLD, 2)),
        QuestEvidence("completion_reported", 3, source_identity(WORLD, 3)),
    )[:heard]
    factory = ObservedReadViewFactory(
        StoredRoot(
            (
                GateRecord(layout.gate_id, layout.space_id, layout.gate_cell, opened),
                record_at(tick - 1),
                NpcQuestMemoryRecord(layout.npc_id, entries),
                ReplyRecord(layout.npc_id, 1),
            ),
            0,
        )
    )
    AdapterBinding(GateAdapter(layout=layout)).install(factory)
    AdapterBinding(MemoryAdapter(selected)).install(factory)
    AdapterBinding(CycleAdapter(selected)).install(factory)
    AdapterBinding(ReplyAdapter(layout=layout)).install(factory)
    payload = WatchReplied(layout.npc_id, 0, 1)
    header = EventHeader(
        EventId("e1-" + "2" * 64),
        payload.schema,
        "watch.echo",
        Tick(tick),
        Phase.CASCADE,
        1,
        0,
        0,
        (EventId("e1-" + "3" * 64),),
        (),
    )
    return EngineInvocation(
        None,
        Tick(tick),
        Phase.POST_TICK,
        0,
        factory.open(ViewEpoch(Tick(tick), Phase.POST_TICK, 0, "encounter.actions", 0)),
        EmptyDefinitions(),
        NoDrawRng(),
        (WorldEvent(header, Tick(tick), payload),),
    )


def engine() -> EncounterActions:
    return EncounterActions(
        content().definition.layout, npc_aid=True, npc_supply_aid=True, npc_call_aid=True
    )


@pytest.mark.parametrize(
    "tick,opens", ((4, False), (8, False), (9, True), (10, True), (12, False), (13, True))
)
def test_prior_stock_table(tick: int, opens: bool) -> None:
    call = invocation(tick)
    result = engine().evaluate(call)
    assert result.deltas == (
        (GateDelta(content().definition.layout.gate_id, 0, 1),) if opens else ()
    )
    assert len(result.facts) == int(opens)
    if opens:
        assert result.facts[0].caused_by == (call.incoming[0].header.event_id,)


@pytest.mark.parametrize("heard,opened", ((0, 0), (2, 0), (1, 1)))
def test_inactive_reported_or_already_open(heard: int, opened: int) -> None:
    result = engine().evaluate(invocation(heard=heard, opened=opened))
    assert result.deltas == ()
    assert result.facts == ()


@pytest.mark.parametrize(
    "damage",
    (
        "producer",
        "phase",
        "wave",
        "bool_wave",
        "sequence",
        "bool_sequence",
        "type",
        "due",
        "occurred",
        "npc",
        "before",
        "bool_before",
        "bool_after",
        "after",
        "count_mismatch",
        "cause_missing",
        "cause_duplicate",
        "duplicate",
        "empty",
        "invocation_wave",
        "unknown",
        "tick_zero",
        "tick_bool",
    ),
)
def test_malformed_call_rejected_before_effect(damage: str) -> None:
    call = invocation()
    event = call.incoming[0]
    payload = cast(WatchReplied, event.payload)
    header = event.header
    headers = {
        "producer": replace(header, producer_id="watch.respond"),
        "phase": replace(header, phase=Phase.REACT),
        "wave": replace(header, wave=0),
        "bool_wave": replace(header, wave=True),
        "sequence": replace(header, sequence=1),
        "bool_sequence": replace(header, sequence=False),
        "type": replace(header, type_key=TypeKey("watch.echo", 1)),
        "occurred": replace(header, occurred_at=Tick(8)),
        "cause_missing": replace(header, caused_by=()),
        "cause_duplicate": replace(header, caused_by=header.caused_by * 2),
    }
    if damage in headers:
        event = replace(event, header=headers[damage])
    elif damage == "due":
        event = replace(event, due_tick=Tick(8))
    elif damage == "npc":
        event = replace(event, payload=replace(payload, npc_id=EntityId("actor:other")))
    elif damage in ("before", "bool_before", "bool_after", "after", "count_mismatch"):
        values = {
            "before": (-1, 0),
            "bool_before": (False, 1),
            "bool_after": (0, True),
            "after": (0, 2),
            "count_mismatch": (1, 2),
        }
        before, after = values[damage]
        event = replace(event, payload=replace(payload, before_count=before, after_count=after))
    elif damage == "unknown":
        event = replace(event, payload=NpcActed(payload.npc_id, 3, 4))
    call = replace(call, incoming=(event,))
    if damage == "duplicate":
        call = replace(call, incoming=(event, event))
    elif damage == "empty":
        call = replace(call, incoming=())
    elif damage == "invocation_wave":
        call = replace(call, wave=1)
    elif damage in ("tick_zero", "tick_bool"):
        call = replace(call, logical_tick=Tick(0 if damage == "tick_zero" else True))
    with pytest.raises(CandidateError, match="^INVALID_FACT:"):
        engine().evaluate(call)


@pytest.mark.parametrize("reverse", (False, True))
@pytest.mark.parametrize("bad_wake", (False, True))
def test_mixed_sources_validate_both_and_prefer_call(reverse: bool, bad_wake: bool) -> None:
    call = invocation(10)
    payload = NpcActed(content().definition.layout.npc_id, 4, 5)
    wake = WorldEvent(
        EventHeader(
            EventId(wake_identity(WORLD, 10)),
            payload.schema,
            "watch.npc",
            Tick(10),
            Phase.PRE_TICK,
            0,
            0,
            int(bad_wake),
            (),
            (),
        ),
        Tick(10),
        payload,
    )
    events = (wake, *call.incoming) if reverse else (*call.incoming, wake)
    if bad_wake:
        with pytest.raises(CandidateError, match="^INVALID_FACT:"):
            engine().evaluate(replace(call, incoming=events))
    else:
        result = engine().evaluate(replace(call, incoming=events))
        assert len(result.deltas) == len(result.facts) == 1
        assert result.facts[0].caused_by == (call.incoming[0].header.event_id,)


@pytest.mark.parametrize("tick", (1, 3, 9))
def test_odd_cue_permission_is_new_mode_only(tick: int) -> None:
    selected = content()
    layout = selected.definition.layout
    cue = GateAidCue(layout.npc_id, layout.gate_id, tick)
    old = GateAidPayloadCodec(cue.schema, selected)
    with pytest.raises(ValueError, match="^NPC_AID_PAYLOAD$"):
        old.encode(cue)
    current = GateAidPayloadCodec(cue.schema, selected, npc_call_aid=True)
    assert current.decode(current.encode(cue)) == cue


@pytest.mark.parametrize("value", (True, 0, 1, None, "1", 2.0))
def test_selection_is_exact_and_requires_supply(value: object) -> None:
    selected = content()
    kwargs = {
        "npc_aid": True,
        "npc_supply_aid": value is not True,
        "npc_call_aid": cast(bool, value),
    }
    with pytest.raises(ValueError, match="^NPC_CALL_AID_CONTENT$"):
        EncounterActions(selected.definition.layout, **kwargs)
    with pytest.raises(ValueError, match="^NPC_CALL_AID_CONTENT$"):
        cycle_bundle(selected, **kwargs)


def test_declared_existing_reply_read_and_distinct_pins() -> None:
    selected = content()
    old = cycle_bundle(selected, npc_aid=True, npc_supply_aid=True)
    explicit = cycle_bundle(selected, npc_aid=True, npc_supply_aid=True, npc_call_aid=False)
    current = cycle_bundle(selected, npc_aid=True, npc_supply_aid=True, npc_call_aid=True)
    assert old.schema_document == explicit.schema_document
    assert old.rules_document == explicit.rules_document
    assert state_io((old,)).pins == state_io((explicit,)).pins
    assert state_io((old,)).pins != state_io((current,)).pins
    assert current.feature_id == "quest.harbor-call-aid-v1"
    assert tuple(c.schema for c in old.component_codecs) == tuple(
        c.schema for c in current.component_codecs
    )
    access = PhaseAccess(Phase.POST_TICK, FieldFamily(REPLY.schema.kind, "count"))
    assert access in engine().manifest.reads and access not in engine().manifest.writes
    spec = next(s for s in current.field_specs if s.family == access.family)
    assert spec.owner_id == "watch.echo" and "encounter.actions" in spec.consumers
    with pytest.raises(CandidateError, match="^INVALID_FACT:"):
        EncounterActions(selected.definition.layout, npc_aid=True, npc_supply_aid=True).evaluate(
            invocation()
        )
    with pytest.raises(ValueError, match="^NPC_CALL_AID_CONTENT$"):
        EncounterPresenter(npc_call_aid=True)
