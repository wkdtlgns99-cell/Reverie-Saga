"""New reach selection and registered capability boundaries;no new geometry formula."""

from typing import cast
from contextlib import contextmanager
from collections.abc import Iterator
from contracts.errors import CandidateError, UnknownEntity
from contracts.encounter import GateDelta
from contracts.messages import EventHeader, WorldEvent
from contracts.read_views import AdapterBinding, ViewEpoch
from contracts.turn import EngineInvocation
from contracts.watch import WatchReplied
from domain.encounter import GateRecord
from domain.npc_memory import NpcQuestMemoryRecord, QuestEvidence, source_identity
from domain.primitives import EntityId, EventId, Tick
from domain.state_types import ComponentRecord, StoredRoot
from domain.watch import ECHO_DEPTH, ReplyRecord, WatchNpcRecord
from orchestration.encounter import GateAdapter
from orchestration.npc_cycle import CycleAdapter
from orchestration.npc_memory import MemoryAdapter
from orchestration.read_views import ObservedReadViewFactory
from orchestration.turn import EmptyDefinitions, NoDrawRng
from orchestration.watch import ReplyAdapter, WatchNpcAdapter
from tests.unit.test_npc_cycle import WORLD, record_at

import pytest

from app.npc_cycle import cycle_bundle
from contracts.turn import PhaseAccess
from domain.primitives import FieldFamily, Phase
from engines.encounter import EncounterActions
from tests.unit.quest_fixtures import content


@pytest.mark.parametrize("kind", ("engine", "bundle"))
@pytest.mark.parametrize(
    "value,parent", ((True, False), (0, True), (1, True), ("1", True), (None, True))
)
def test_reach_selection_requires_exact_bool_and_its_actual_parent(
    kind: str,
    value: object,
    parent: bool,
) -> None:
    with pytest.raises(ValueError, match="^NPC_REACH_AID_CONTENT$"):
        if kind == "engine":
            EncounterActions(
                content().definition.layout,
                npc_aid=True,
                npc_supply_aid=True,
                npc_call_aid=parent,
                npc_reach_aid=cast(bool, value),
            )
        else:
            cycle_bundle(
                content(),
                npc_aid=True,
                npc_supply_aid=True,
                npc_call_aid=True,
                npc_patrol=True,
                npc_talk_pause=True,
                npc_quest_patrol=True,
                npc_call_pause=True,
                npc_ready_patrol=parent,
                npc_reach_aid=cast(bool, value),
            )


def test_new_capabilities_read_prior_pose_without_another_writer_or_subscriber() -> None:
    old = EncounterActions(
        content().definition.layout, npc_aid=True, npc_supply_aid=True, npc_call_aid=True
    ).manifest
    current = EncounterActions(
        content().definition.layout,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_reach_aid=True,
    ).manifest
    new_reads = {
        PhaseAccess(Phase.POST_TICK, FieldFamily("watch.npc", "cell")),
        PhaseAccess(Phase.POST_TICK, FieldFamily("watch.npc", "space_id")),
    }
    assert set(current.reads) - set(old.reads) == new_reads
    assert set(old.reads) <= set(current.reads)
    assert (current.writes, current.emits, current.consumes, current.phases) == (
        old.writes,
        old.emits,
        old.consumes,
        old.phases,
    )
    bundle = cycle_bundle(
        content(),
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
        npc_ready_patrol=True,
        npc_reach_aid=True,
    )
    for address in (FieldFamily("watch.npc", "cell"), FieldFamily("watch.npc", "space_id")):
        field = next(x for x in bundle.field_specs if x.family == address)
        assert "encounter.actions" in field.consumers
    assert bundle.feature_id == "quest.harbor-reach-aid-v1"


@contextmanager
def reach_source(damage: str = "", *, cell: int = 7) -> Iterator[EngineInvocation]:
    selected = content()
    layout = selected.definition.layout
    cycle = record_at(14 if damage not in ("stale", "future") else 8 if damage == "stale" else 16)
    npc = WatchNpcRecord(
        layout.npc_id, EntityId("space:foreign") if damage == "space" else layout.space_id, cell, 7
    )
    records: list[ComponentRecord] = [
        GateRecord(layout.gate_id, layout.space_id, layout.gate_cell, 0),
        cycle,
        npc,
        NpcQuestMemoryRecord(
            layout.npc_id, (QuestEvidence("accepted", 2, source_identity(WORLD, 2)),)
        ),
        ReplyRecord(layout.npc_id, 1),
    ]
    if damage == "missing_npc":
        records.remove(npc)
    elif damage == "missing_cycle":
        records.remove(cycle)
    root = StoredRoot(
        tuple(
            sorted(
                records,
                key=lambda value: (value.schema.kind, value.schema.version, value.entity_id),
            )
        ),
        0,
    )
    factory = ObservedReadViewFactory(root)
    AdapterBinding(GateAdapter(layout)).install(factory)
    AdapterBinding(CycleAdapter(selected)).install(factory)
    AdapterBinding(MemoryAdapter(selected)).install(factory)
    AdapterBinding(WatchNpcAdapter(layout, npc_patrol=True)).install(factory)
    AdapterBinding(ReplyAdapter(layout)).install(factory)
    tick = Tick(15)
    payload = WatchReplied(layout.npc_id, 0, 1)
    header = EventHeader(
        EventId("e1-" + "2" * 64),
        payload.schema,
        "watch.echo",
        tick,
        Phase.CASCADE,
        ECHO_DEPTH,
        0,
        0,
        (EventId("e1-" + "3" * 64),),
        (),
    )
    epoch = ViewEpoch(tick, Phase.POST_TICK, 0, "encounter.actions", 0)
    call = EngineInvocation(
        None,
        tick,
        Phase.POST_TICK,
        0,
        factory.open(epoch),
        EmptyDefinitions(),
        NoDrawRng(),
        (WorldEvent(header, tick, payload),),
    )
    try:
        yield call
    finally:
        assert all(access.operation != "write" for access in factory.close(epoch))


def reach_engine() -> EncounterActions:
    return EncounterActions(
        content().definition.layout,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_reach_aid=True,
    )


@pytest.mark.parametrize(
    "damage,detail",
    (
        ("stale", "reach aid cycle source"),
        ("future", "reach aid cycle source"),
        ("space", "reach aid NPC source"),
    ),
)
def test_malformed_reach_sources_keep_precise_errors(damage: str, detail: str) -> None:
    with reach_source(damage) as call:
        with pytest.raises(CandidateError) as caught:
            reach_engine().evaluate(call)
        assert caught.value.code == "INVALID_FACT" and caught.value.detail == detail


@pytest.mark.parametrize("damage", ("missing_npc", "missing_cycle"))
def test_missing_reach_source_keeps_structural_entity_error(damage: str) -> None:
    with reach_source(damage) as call:
        with pytest.raises(UnknownEntity):
            reach_engine().evaluate(call)


@pytest.mark.parametrize("cell,opens", ((6, False), (7, True)))
def test_canonical_physical_pose_controls_existing_gate_delta(cell: int, opens: bool) -> None:
    with reach_source(cell=cell) as call:
        result = reach_engine().evaluate(call)
        assert result.deltas == (
            (GateDelta(content().definition.layout.gate_id, 0, 1),) if opens else ()
        )
        assert len(result.facts) == int(opens)
        if opens:
            assert result.facts[0].caused_by == (call.incoming[0].header.event_id,)


@pytest.mark.parametrize("cell", (-1, 8))
def test_registered_adapter_rejects_out_of_patrol_pose_before_engine(cell: int) -> None:
    with pytest.raises(ValueError, match="^integer outside declared range$"):
        with reach_source(cell=cell):
            pytest.fail("out-of-patrol pose reached the engine")
