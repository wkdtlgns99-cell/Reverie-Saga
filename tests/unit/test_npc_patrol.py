"""Independent patrol source,cell-codec and net-composition boundary checks."""

from dataclasses import replace
from typing import cast

import pytest

from contracts.errors import CandidateError
from contracts.messages import EventHeader, WorldEvent
from contracts.npc_patrol import NpcCellDelta, NpcCellPatch, NpcPatrolled, NpcPatrolCue
from contracts.read_views import AdapterBinding, ViewEpoch
from contracts.turn import EngineInvocation, PhaseAccess
from contracts.watch import NpcActed, NpcCue
from domain.npc_patrol import patrol_cells
from domain.primitives import EntityId, EventId, FieldFamily, Phase, Tick, TypeKey
from domain.state_types import StoredRoot
from domain.scenario import LEGACY, COURTYARD_SCENARIO, Scenario
from domain.trial import CellPositionRecord
from domain.watch import WatchNpcRecord
from engines.watch import WatchNpc
from orchestration.read_views import ObservedReadViewFactory
from orchestration.trial import CellPositionAdapter
from orchestration.turn import EmptyDefinitions, NoDrawRng
from orchestration.watch import (
    NpcCellPatchRoute,
    NpcCellReducer,
    WatchNpcAdapter,
    WatchPayloadCodec,
)
from tests.unit.quest_fixtures import content


def invocation(*, current: int = 6, actor: int = 0) -> EngineInvocation:
    layout = content().definition.layout
    factory = ObservedReadViewFactory(
        StoredRoot(
            (
                CellPositionRecord(layout.actor_id, layout.space_id, actor),
                WatchNpcRecord(layout.npc_id, layout.space_id, current, 1),
            ),
            0,
        )
    )
    AdapterBinding(WatchNpcAdapter(layout, npc_patrol=True)).install(factory)
    AdapterBinding(CellPositionAdapter(layout)).install(factory)
    fact = NpcActed(layout.npc_id, 0, 1)
    header = EventHeader(
        EventId("e1-" + "2" * 64),
        fact.schema,
        "watch.npc",
        Tick(2),
        Phase.PRE_TICK,
        0,
        0,
        0,
        (EventId("e1-" + "3" * 64),),
        (),
    )
    return EngineInvocation(
        None,
        Tick(2),
        Phase.POST_TICK,
        0,
        factory.open(ViewEpoch(Tick(2), Phase.POST_TICK, 0, "watch.npc", 0)),
        EmptyDefinitions(),
        NoDrawRng(),
        (WorldEvent(header, Tick(2), fact),),
    )


@pytest.mark.parametrize("current,actor,target", ((6, 0, 7), (7, 0, 6), (6, 6, 7), (7, 7, 6)))
def test_actual_current_cell_selects_other_endpoint(current: int, actor: int, target: int) -> None:
    layout = content().definition.layout
    call = invocation(current=current, actor=actor)
    engine = WatchNpc(layout, npc_patrol=True)
    result = engine.evaluate(call)
    assert result.deltas == (NpcCellDelta(layout.npc_id, current, target),)
    assert len(result.facts) == 1
    assert result.facts[0].payload == NpcPatrolled(layout.npc_id, layout.space_id, current, target)
    assert result.facts[0].caused_by == (call.incoming[0].header.event_id,)
    assert result.facts[0].due_tick == 2
    assert PhaseAccess(Phase.POST_TICK, FieldFamily("watch.npc", "cell")) in engine.manifest.writes
    assert (
        PhaseAccess(Phase.POST_TICK, FieldFamily("trial.position", "cell")) in engine.manifest.reads
    )


@pytest.mark.parametrize("current,actor", ((6, 7), (7, 6)))
def test_occupied_destination_has_no_movement_fact(current: int, actor: int) -> None:
    result = WatchNpc(content().definition.layout, npc_patrol=True).evaluate(
        invocation(current=current, actor=actor)
    )
    assert result.deltas == ()
    assert result.facts == ()
    assert result.degraded == ()


@pytest.mark.parametrize(
    "damage",
    (
        "producer",
        "phase",
        "wave",
        "bool_wave",
        "sequence",
        "bool_sequence",
        "schema",
        "occurred",
        "cause_missing",
        "cause_extra",
        "due",
        "npc",
        "before",
        "after",
        "bool_before",
        "bool_after",
        "unknown",
        "empty",
        "duplicate",
        "invocation_wave",
        "invocation_bool_wave",
        "invocation_tick",
        "invocation_bool_tick",
    ),
)
def test_bad_source_rejected_even_when_destination_blocked(damage: str) -> None:
    call = invocation(actor=7)
    source = call.incoming[0]
    header = source.header
    fact = cast(NpcActed, source.payload)
    headers = {
        "producer": replace(header, producer_id="watch.echo"),
        "phase": replace(header, phase=Phase.POST_TICK),
        "wave": replace(header, wave=1),
        "bool_wave": replace(header, wave=False),
        "sequence": replace(header, sequence=1),
        "bool_sequence": replace(header, sequence=False),
        "schema": replace(header, type_key=TypeKey("watch.wake", 1)),
        "occurred": replace(header, occurred_at=Tick(1)),
        "cause_missing": replace(header, caused_by=()),
        "cause_extra": replace(header, caused_by=header.caused_by * 2),
    }
    if damage in headers:
        source = replace(source, header=headers[damage])
    elif damage == "due":
        source = replace(source, due_tick=Tick(1))
    elif damage == "npc":
        source = replace(source, payload=replace(fact, npc_id=EntityId("actor:other")))
    elif damage in ("before", "after", "bool_before", "bool_after"):
        before, after = {
            "before": (1, 2),
            "after": (0, 2),
            "bool_before": (False, 1),
            "bool_after": (0, True),
        }[damage]
        source = replace(source, payload=replace(fact, before_bells=before, after_bells=after))
    elif damage == "unknown":
        source = replace(
            source, payload=NpcPatrolled(fact.npc_id, content().definition.layout.space_id, 6, 7)
        )
    call = replace(call, incoming=(source,))
    if damage == "empty":
        call = replace(call, incoming=())
    elif damage == "duplicate":
        call = replace(call, incoming=(source, source))
    elif damage == "invocation_wave":
        call = replace(call, wave=1)
    elif damage == "invocation_bool_wave":
        call = replace(call, wave=False)
    elif damage == "invocation_tick":
        call = replace(call, logical_tick=Tick(3))
    elif damage == "invocation_bool_tick":
        call = replace(call, logical_tick=Tick(True))
    with pytest.raises(CandidateError, match="INVALID_FACT"):
        WatchNpc(content().definition.layout, npc_patrol=True).evaluate(call)


def test_net_cancellation_and_patch_preserve_bells_and_binding() -> None:
    layout = content().definition.layout
    reducer = NpcCellReducer(layout, npc_patrol=True)
    first, second = NpcCellDelta(layout.npc_id, 6, 7), NpcCellDelta(layout.npc_id, 7, 6)
    net = reducer.compose((first, second))
    assert net == NpcCellDelta(layout.npc_id, 6, 6) and reducer.is_identity(net)
    with pytest.raises(CandidateError, match="INVALID_DELTA"):
        reducer.compose(())
    with pytest.raises(CandidateError, match="INVALID_DELTA"):
        reducer.compose((first, first))
    original = WatchNpcRecord(layout.npc_id, layout.space_id, 6, 18)
    assert NpcCellPatchRoute(layout, npc_patrol=True).apply(original, NpcCellPatch(7)) == replace(
        original, cell=7
    )
    assert original.cell == 6 and original.bells == 18


@pytest.mark.parametrize("cell", (-1, 0, 5, 8, 9, True, False))
def test_invalid_cell_payload_is_rejected(cell: int) -> None:
    codec = WatchPayloadCodec(NpcCellPatch.SCHEMA, content().definition.layout, npc_patrol=True)
    with pytest.raises(ValueError, match="integer|NPC cell"):
        codec.encode(NpcCellPatch(cell))


@pytest.mark.parametrize("tick", (0, 1, 3, True, -2))
def test_movement_cue_requires_actual_even_time(tick: int) -> None:
    layout = content().definition.layout
    codec = WatchPayloadCodec(NpcPatrolCue.SCHEMA, layout, npc_patrol=True)
    with pytest.raises(ValueError, match="integer|patrol cue time"):
        codec.encode(NpcPatrolCue(layout.npc_id, Tick(tick), 6, 7, 1000, 2000))


def test_opt_in_payloads_and_static_path_boundaries() -> None:
    layout = content().definition.layout
    assert patrol_cells(layout, False) == (6,) and patrol_cells(layout, True) == (6, 7)
    with pytest.raises(ValueError, match="NPC_PATROL_CONTENT"):
        patrol_cells(layout, cast(bool, 1))
    with pytest.raises(ValueError, match="NPC_PATROL_CONTENT"):
        patrol_cells(replace(layout, npc_cell=7, enemy_cell=6, gate_cell=8), True)
    with pytest.raises(ValueError, match="UNSUPPORTED_SCHEMA"):
        WatchPayloadCodec(NpcPatrolled.SCHEMA, layout)
    codec = WatchPayloadCodec(NpcPatrolled.SCHEMA, layout, npc_patrol=True)
    value = NpcPatrolled(layout.npc_id, layout.space_id, 6, 7)
    assert codec.decode(codec.encode(value)) == value
    with pytest.raises(ValueError, match="change cell"):
        codec.encode(replace(value, after_cell=6))
    with pytest.raises(ValueError, match="patrol space"):
        codec.encode(replace(value, space_id=EntityId("space:other")))


@pytest.mark.parametrize("layout", (LEGACY, COURTYARD_SCENARIO, content().definition.layout))
def test_stationary_cue_keeps_existing_declared_range_error(layout: Scenario) -> None:
    cell = layout.npc_cell
    cue = NpcCue(layout.npc_id, Tick(2), 0, 1, cell, cell % 3 * 1000, cell // 3 * 1000)
    codec = WatchPayloadCodec(cue.schema, layout)
    assert codec.decode(codec.encode(cue)) == cue
    with pytest.raises(ValueError, match="^integer outside declared range$"):
        codec.encode(replace(cue, cell=(cell + 1) % 9))
