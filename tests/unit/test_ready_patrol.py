"""Independent readiness-priority examples and declared read/selection boundaries."""

from typing import cast
from contextlib import contextmanager
from dataclasses import replace
from collections.abc import Iterator

from app.npc_patrol_status import quest_patrol_next_step, quest_patrol_step_slot_messages
from contracts.errors import CandidateError, UnknownEntity
from contracts.read_views import AdapterBinding, ViewEpoch
from contracts.turn import EngineInvocation
from domain.encounter import GateRecord
from domain.npc_memory import NpcQuestMemoryRecord, QuestEvidence
from domain.npc_cycle import CycleRecord
from domain.primitives import Tick
from domain.state_types import ComponentRecord, CoreSnapshot, StoredRoot
from domain.trial import CellPositionRecord
from domain.watch import WatchNpcRecord, ReplyRecord
from orchestration.encounter import GateAdapter
from orchestration.npc_cycle import CycleAdapter
from orchestration.npc_memory import MemoryAdapter
from orchestration.read_views import ObservedReadViewFactory
from orchestration.trial import CellPositionAdapter
from orchestration.watch import ReplyAdapter, WatchNpcAdapter
from orchestration.turn import EmptyDefinitions, NoDrawRng
from contracts.persistence import SaveError
from tests.unit.test_call_pause_patrol import wake, reply
from tests.unit.test_npc_cycle import record_at
from tests.unit.test_patrol_next_step import core as old_core
from tests.integration.test_patrol_next_step import IDLE, FREE_NEIGHBOR

import pytest

from app.npc_cycle import cycle_bundle
from contracts.npc_cycle import CYCLE_FAMILY
from contracts.turn import PhaseAccess
from domain.npc_patrol import QuestPatrolPhase, ready_patrol_target
from domain.primitives import FieldFamily, Phase
from engines.watch import WatchNpc
from tests.unit.quest_fixtures import content


@pytest.mark.parametrize(
    "phase,current,stock,opened,target",
    (
        ("available", 6, 0, 0, 6),
        ("available", 6, 3, 1, 6),
        ("accepted", 6, 0, 0, 6),
        ("accepted", 6, 1, 0, 6),
        ("accepted", 6, 2, 0, 7),
        ("accepted", 6, 3, 0, 7),
        ("accepted", 6, 0, 1, 7),
        ("accepted", 6, 1, 1, 7),
        ("accepted", 7, 0, 0, 6),
        ("accepted", 7, 3, 0, 6),
        ("accepted", 7, 0, 1, 6),
        ("accepted", 7, 3, 1, 6),
        ("reported", 7, 0, 0, 6),
        ("reported", 7, 3, 1, 6),
        ("reported", 6, 0, 0, 6),
        ("reported", 6, 3, 1, 6),
    ),
)
def test_priority_uses_own_quest_stock_and_gate(
    phase: QuestPatrolPhase, current: int, stock: int, opened: int, target: int
) -> None:
    assert ready_patrol_target(content().definition.layout, current, phase, stock, opened) == target


@pytest.mark.parametrize("stock", (True, False, -1, 4, 2**63, 1.0, "1", None))
def test_invalid_exact_stock_is_not_interpreted_as_readiness(stock: object) -> None:
    with pytest.raises(ValueError, match="^NPC_READY_PATROL_TARGET$"):
        ready_patrol_target(content().definition.layout, 6, "accepted", cast(int, stock), 0)


@pytest.mark.parametrize("opened", (True, False, -1, 2, 1.0, "0", None))
def test_invalid_exact_gate_is_not_interpreted_as_closed(opened: object) -> None:
    with pytest.raises(ValueError, match="^NPC_READY_PATROL_TARGET$"):
        ready_patrol_target(content().definition.layout, 6, "accepted", 1, cast(int, opened))


@pytest.mark.parametrize("bad", (True, -1, 8, 6.0, "6"))
def test_invalid_current_cell_cannot_choose_home(bad: object) -> None:
    with pytest.raises(ValueError, match="^NPC_READY_PATROL_TARGET$"):
        ready_patrol_target(content().definition.layout, cast(int, bad), "accepted", 1, 0)


def test_unheard_neighbor_and_unknown_phase_do_not_become_a_new_goal() -> None:
    layout = content().definition.layout
    with pytest.raises(ValueError, match="^NPC_READY_PATROL_TARGET$"):
        ready_patrol_target(layout, 7, "available", 1, 0)
    with pytest.raises(ValueError, match="^NPC_READY_PATROL_TARGET$"):
        ready_patrol_target(layout, 6, cast(QuestPatrolPhase, "completed"), 1, 0)


@pytest.mark.parametrize("bad", (True, 0, 1, None, "ready"))
def test_missing_parent_or_nonbool_rejects_new_selection(bad: object) -> None:
    with pytest.raises(ValueError, match="^NPC_READY_PATROL_CONTENT$"):
        cycle_bundle(content(), npc_ready_patrol=cast(bool, bad))


def test_new_read_capabilities_and_consumers_are_registered_only_in_ready_mode() -> None:
    selected = content()
    kwargs = dict(
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
    )
    ready = cycle_bundle(selected, **kwargs, npc_ready_patrol=True)
    old = cycle_bundle(selected, **kwargs)
    new_engine = next(
        binding.engine
        for binding in ready.bindings
        if binding.engine.manifest.engine_id == "watch.npc"
    )
    old_engine = next(
        binding.engine
        for binding in old.bindings
        if binding.engine.manifest.engine_id == "watch.npc"
    )
    families = (
        CYCLE_FAMILY,
        *(FieldFamily("encounter.gate", field) for field in ("space_id", "cell", "is_open")),
    )
    for family in families:
        assert PhaseAccess(Phase.POST_TICK, family) in new_engine.manifest.reads
        assert PhaseAccess(Phase.POST_TICK, family) not in old_engine.manifest.reads
        spec = next(spec for spec in ready.field_specs if spec.family == family)
        assert spec.consumers.count("watch.npc") == 1
    assert ready.schema_document == old.schema_document
    assert ready.feature_id != old.feature_id
    assert old_engine.manifest.writes == new_engine.manifest.writes
    assert old_engine.manifest.emits == new_engine.manifest.emits
    with pytest.raises(ValueError, match="^NPC_READY_PATROL_CONTENT$"):
        WatchNpc(selected.definition.layout, ready_patrol=True)


@contextmanager
def guarded_source(bad: str = "", answered: bool = False) -> Iterator[EngineInvocation]:
    selected = content()
    layout = selected.definition.layout
    tick = 8
    memory = NpcQuestMemoryRecord(layout.npc_id, (QuestEvidence("accepted", 1, "e1-" + "5" * 64),))
    cycle = record_at(7)
    gate = GateRecord(layout.gate_id, layout.space_id, layout.gate_cell, 0)
    if bad == "cycle_future":
        cycle = record_at(8)
    elif bad == "cycle_stale":
        cycle = record_at(0)
    elif bad == "gate_bool":
        gate = replace(gate, is_open=True)
    elif bad == "gate_high":
        gate = replace(gate, is_open=2)
    elif bad == "gate_negative":
        gate = replace(gate, is_open=-1)
    elif bad == "gate_cell_bool":
        gate = replace(gate, cell=True)
    elif bad == "gate_cell":
        gate = replace(gate, cell=3)
    elif bad == "gate_space":
        gate = replace(gate, space_id=layout.npc_id)
    elif bad == "future_memory":
        memory = replace(memory, entries=(QuestEvidence("accepted", 9, "e1-" + "5" * 64),))
    records: list[ComponentRecord] = [
        memory,
        cycle,
        gate,
        CellPositionRecord(layout.actor_id, layout.space_id, 0),
        WatchNpcRecord(layout.npc_id, layout.space_id, 6, 4),
        ReplyRecord(layout.npc_id, 1),
    ]
    if bad == "missing_cycle":
        records.remove(cycle)
    elif bad == "missing_gate":
        records.remove(gate)
    ordered = tuple(
        sorted(
            records,
            key=lambda record: (record.schema.kind, record.schema.version, record.entity_id),
        )
    )
    factory = ObservedReadViewFactory(StoredRoot(ordered, 0))
    AdapterBinding(MemoryAdapter(selected)).install(factory)
    AdapterBinding(CycleAdapter(selected)).install(factory)
    AdapterBinding(GateAdapter(layout=layout)).install(factory)
    AdapterBinding(CellPositionAdapter(layout)).install(factory)
    AdapterBinding(WatchNpcAdapter(layout, npc_patrol=True)).install(factory)
    AdapterBinding(ReplyAdapter(layout)).install(factory)
    epoch = ViewEpoch(Tick(tick), Phase.POST_TICK, 0, "watch.npc", 0)
    call = EngineInvocation(
        None,
        Tick(tick),
        Phase.POST_TICK,
        0,
        factory.open(epoch),
        EmptyDefinitions(),
        NoDrawRng(),
        (wake(tick), reply(tick)) if answered else (wake(tick),),
    )
    try:
        yield call
    finally:
        assert all(access.operation != "write" for access in factory.close(epoch))


def ready_engine() -> WatchNpc:
    selected = content()
    return WatchNpc(
        selected.definition.layout,
        npc_patrol=True,
        talk_pause_quest=selected.definition.quest_id,
        quest_patrol=True,
        call_pause=True,
        ready_patrol=True,
    )


@pytest.mark.parametrize("answered", (False, True))
@pytest.mark.parametrize("bad", ("cycle_future", "cycle_stale", "gate_space"))
def test_present_bad_new_source_rejects_before_idle_or_reply_hold(bad: str, answered: bool) -> None:
    with guarded_source(bad, answered) as call:
        with pytest.raises(CandidateError) as caught:
            ready_engine().evaluate(call)
        assert caught.value.code == "INVALID_FACT"
        assert (
            "ready patrol cycle source" if bad.startswith("cycle") else "ready patrol gate source"
        ) in caught.value.detail


@pytest.mark.parametrize("answered", (False, True))
@pytest.mark.parametrize(
    "bad", ("gate_bool", "gate_high", "gate_negative", "gate_cell_bool", "gate_cell")
)
def test_invalid_gate_range_rejects_at_registered_adapter_before_engine(
    bad: str, answered: bool
) -> None:
    with pytest.raises(ValueError, match="^integer outside declared range$"):
        with guarded_source(bad, answered):
            pytest.fail("invalid gate was admitted by its registered adapter")


@pytest.mark.parametrize("bad", ("missing_cycle", "missing_gate"))
def test_missing_core_entity_keeps_structural_read_error(bad: str) -> None:
    with guarded_source(bad) as call:
        with pytest.raises(UnknownEntity):
            ready_engine().evaluate(call)


def test_future_own_memory_still_rejects_before_new_priority() -> None:
    with guarded_source("future_memory") as call:
        with pytest.raises(CandidateError) as caught:
            ready_engine().evaluate(call)
        assert (
            caught.value.code == "INVALID_FACT"
            and caught.value.detail == "quest patrol future memory"
        )


def source_core(*, opened: int = 0) -> CoreSnapshot:
    value = old_core("accepted", tick=4)
    layout = content().definition.layout
    return replace(
        value,
        components=(
            *value.components,
            record_at(4),
            GateRecord(layout.gate_id, layout.space_id, layout.gate_cell, opened),
        ),
    )


def test_same_tick_stock_and_pose_but_own_gate_selects_different_saved_goal() -> None:
    current, saved = source_core(opened=1), source_core(opened=0)
    rows = quest_patrol_step_slot_messages(
        saved, current, content().definition.layout, npc_ready_patrol=True
    )
    assert "현재 " + FREE_NEIGHBOR in rows and "선택 저장 " + IDLE in rows


def corrupt_core(kind: str) -> CoreSnapshot:
    core = source_core()
    layout = content().definition.layout
    records = list(core.components)
    cycle = next(x for x in records if type(x) is CycleRecord)
    gate = next(x for x in records if type(x) is GateRecord)
    if kind == "missing_cycle":
        records.remove(cycle)
    elif kind == "duplicate_cycle":
        records.append(cycle)
    elif kind == "foreign_cycle":
        records[records.index(cycle)] = replace(cycle, entity_id=layout.actor_id)
    elif kind == "stale_cycle":
        records[records.index(cycle)] = record_at(0)
    elif kind == "future_cycle":
        records[records.index(cycle)] = record_at(8)
    elif kind == "missing_gate":
        records.remove(gate)
    elif kind == "duplicate_gate":
        records.append(gate)
    elif kind == "foreign_gate":
        records[records.index(gate)] = replace(gate, entity_id=layout.actor_id)
    elif kind == "gate_space":
        records[records.index(gate)] = replace(gate, space_id=layout.npc_id)
    elif kind == "gate_cell":
        records[records.index(gate)] = replace(gate, cell=3)
    elif kind == "gate_cell_bool":
        records[records.index(gate)] = replace(gate, cell=True)
    elif kind == "gate_bool":
        records[records.index(gate)] = replace(gate, is_open=True)
    elif kind == "gate_high":
        records[records.index(gate)] = replace(gate, is_open=2)
    else:
        assert kind == "gate_negative"
        records[records.index(gate)] = replace(gate, is_open=-1)
    return replace(core, components=tuple(records))


BROKEN = (
    "missing_cycle",
    "duplicate_cycle",
    "foreign_cycle",
    "stale_cycle",
    "future_cycle",
    "missing_gate",
    "duplicate_gate",
    "foreign_gate",
    "gate_space",
    "gate_cell",
    "gate_cell_bool",
    "gate_bool",
    "gate_high",
    "gate_negative",
)


@pytest.mark.parametrize("kind", BROKEN)
@pytest.mark.parametrize("error_code", ("NPC_ACTIVITY_SOURCE", "NPC_RECOLLECTION_SOURCE"))
def test_new_projection_source_errors_keep_exact_registered_caller_code(
    kind: str, error_code: str
) -> None:
    with pytest.raises(SaveError) as caught:
        quest_patrol_next_step(
            corrupt_core(kind),
            content().definition.layout,
            error_code=error_code,
            npc_ready_patrol=True,
        )
    assert caught.value.code == error_code


@pytest.mark.parametrize("kind", BROKEN)
@pytest.mark.parametrize("saved_side", (False, True))
def test_either_saved_ready_source_cannot_borrow_current_gate_or_stock(
    kind: str, saved_side: bool
) -> None:
    valid, invalid = source_core(), corrupt_core(kind)
    with pytest.raises(SaveError) as caught:
        quest_patrol_step_slot_messages(
            invalid if saved_side else valid,
            valid if saved_side else invalid,
            content().definition.layout,
            npc_ready_patrol=True,
        )
    assert caught.value.code == "SAVE_INSPECT_FAILED"
