"""Independent readiness table and exact source/access qualification."""

from dataclasses import replace
from typing import cast

import pytest

from app.headless import state_io
from app.npc_cycle import cycle_bundle
from contracts.encounter import GateDelta
from contracts.errors import CandidateError
from contracts.messages import EventHeader, WorldEvent
from contracts.npc_cycle import CYCLE_FAMILY
from contracts.npc_gate_aid import GateAssisted
from contracts.read_views import AdapterBinding, ViewEpoch
from contracts.turn import EngineInvocation, PhaseAccess
from contracts.watch import NpcActed
from domain.encounter import GateRecord
from domain.npc_memory import NpcQuestMemoryRecord, QuestEvidence, source_identity
from domain.npc_cycle import wake_identity
from domain.npc_work import SUPPORT_STOCK_MIN
from domain.primitives import EventId, Phase, Tick
from domain.state_types import StoredRoot
from engines.encounter import EncounterActions
from orchestration.encounter import GateAdapter
from orchestration.npc_cycle import CycleAdapter
from orchestration.npc_memory import MemoryAdapter
from orchestration.read_views import ObservedReadViewFactory
from orchestration.turn import EmptyDefinitions, NoDrawRng
from tests.unit.quest_fixtures import content
from tests.unit.test_npc_cycle import WORLD, record_at


def call(tick: int, *, count: int = 1, opened: int = 0) -> EngineInvocation:
    selected = content()
    layout = selected.definition.layout
    memory = (
        QuestEvidence("accepted", 2, source_identity(WORLD, 2)),
        QuestEvidence("completion_reported", 3, source_identity(WORLD, 3)),
    )[:count]
    factory = ObservedReadViewFactory(
        StoredRoot(
            (
                GateRecord(layout.gate_id, layout.space_id, layout.gate_cell, opened),
                record_at(tick - 1),
                NpcQuestMemoryRecord(layout.npc_id, memory),
            ),
            0,
        )
    )
    AdapterBinding(GateAdapter(layout=layout)).install(factory)
    AdapterBinding(MemoryAdapter(selected)).install(factory)
    AdapterBinding(CycleAdapter(selected)).install(factory)
    read = factory.open(ViewEpoch(Tick(tick), Phase.POST_TICK, 0, "encounter.actions", 0))
    payload = NpcActed(layout.npc_id, tick // 2 - 1, tick // 2)
    header = EventHeader(
        EventId(wake_identity(WORLD, tick)),
        payload.schema,
        "watch.npc",
        Tick(tick),
        Phase.PRE_TICK,
        0,
        0,
        0,
        (),
        (),
    )
    return EngineInvocation(
        None,
        Tick(tick),
        Phase.POST_TICK,
        0,
        read,
        EmptyDefinitions(),
        NoDrawRng(),
        (WorldEvent(header, Tick(tick), payload),),
    )


@pytest.mark.parametrize(
    "tick,acts",
    (
        (4, False),
        (6, False),
        (8, False),
        (10, True),
        (12, False),
        (14, True),
        (18, True),
        (20, True),
        (22, True),
    ),
)
def test_prior_barrier_stock_independent_table(tick: int, acts: bool) -> None:
    layout = content().definition.layout
    invocation = call(tick)
    result = EncounterActions(layout, npc_aid=True, npc_supply_aid=True).evaluate(invocation)
    assert result.deltas == ((GateDelta(layout.gate_id, 0, 1),) if acts else ())
    assert result.degraded == ()
    if acts:
        assert len(result.facts) == 1 and result.facts[0].payload == GateAssisted(
            layout.npc_id, layout.gate_id
        )
        assert result.facts[0].caused_by == (invocation.incoming[0].header.event_id,)
    else:
        assert result.facts == ()


@pytest.mark.parametrize("count,opened", ((0, 0), (2, 0), (1, 1)))
def test_inactive_reported_or_open_gate_never_adds_aid(count: int, opened: int) -> None:
    result = EncounterActions(
        content().definition.layout, npc_aid=True, npc_supply_aid=True
    ).evaluate(call(10, count=count, opened=opened))
    assert result.deltas == ()
    assert result.facts == ()
    assert result.degraded == ()


def test_new_cycle_read_is_declared_without_new_writer_or_components() -> None:
    selected = content()
    old = cycle_bundle(selected, npc_aid=True)
    current = cycle_bundle(selected, npc_aid=True, npc_supply_aid=True)
    assert SUPPORT_STOCK_MIN == 2
    access = PhaseAccess(Phase.POST_TICK, CYCLE_FAMILY)
    engine = EncounterActions(selected.definition.layout, npc_aid=True, npc_supply_aid=True)
    assert access in engine.manifest.reads and access not in engine.manifest.writes
    assert access not in EncounterActions(selected.definition.layout, npc_aid=True).manifest.reads
    assert (
        next(s for s in current.field_specs if s.family == CYCLE_FAMILY).owner_id == "quest.cycle"
    )
    assert (
        "encounter.actions"
        in next(s for s in current.field_specs if s.family == CYCLE_FAMILY).consumers
    )
    assert tuple(c.schema for c in old.component_codecs) == tuple(
        c.schema for c in current.component_codecs
    )
    assert state_io((old,)).pins != state_io((current,)).pins
    assert (
        old.rules_document
        == cycle_bundle(selected, npc_aid=True, npc_supply_aid=False).rules_document
    )


@pytest.mark.parametrize("value", (True, 0, 1, None, "1", 2.0))
def test_exact_selection_before_engine_or_bundle(value: object) -> None:
    selected = content()
    with pytest.raises(ValueError, match="^NPC_SUPPLY_AID_CONTENT$"):
        EncounterActions(
            selected.definition.layout, npc_aid=value is not True, npc_supply_aid=cast(bool, value)
        )
    with pytest.raises(ValueError, match="^NPC_SUPPLY_AID_CONTENT$"):
        cycle_bundle(selected, npc_aid=value is not True, npc_supply_aid=cast(bool, value))


@pytest.mark.parametrize("damage", ("producer", "due", "occurred"))
def test_invalid_wake_is_rejected_before_eligible_stock_can_act(damage: str) -> None:
    invocation = call(10)
    event = invocation.incoming[0]
    if damage == "producer":
        event = replace(event, header=replace(event.header, producer_id="quest.cycle"))
    elif damage == "due":
        event = replace(event, due_tick=Tick(8))
    else:
        event = replace(event, header=replace(event.header, occurred_at=Tick(8)))
    with pytest.raises(CandidateError, match="^INVALID_FACT:"):
        EncounterActions(content().definition.layout, npc_aid=True, npc_supply_aid=True).evaluate(
            replace(invocation, incoming=(event,))
        )
