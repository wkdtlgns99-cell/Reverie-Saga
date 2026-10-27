"""Independently specified current-plan precedence and selected-source failures."""

from dataclasses import replace

import pytest

from app.npc_cycle import bootstrap_cycle
from app.npc_support_status import supply_support_plan
from app.watch import WatchBootstrapSpec
from contracts.persistence import SaveError
from domain.encounter import GateRecord
from domain.npc_cycle import CycleRecord
from domain.npc_memory import NpcQuestMemoryRecord, QuestEvidence, source_identity
from domain.primitives import EntityId, Tick
from domain.state_types import CoreSnapshot
from tests.unit.quest_fixtures import content
from tests.unit.test_npc_cycle import WORLD, record_at


def source(*, heard: int = 1, tick: int = 8, opened: int = 0) -> CoreSnapshot:
    selected = content()
    initial = bootstrap_cycle(
        WatchBootstrapSpec("0" * 64, "1" * 32, "2" * 32),
        selected,
        npc_aid=True,
        npc_supply_aid=True,
    ).snapshot()
    layout = selected.definition.layout
    evidence = (
        QuestEvidence("accepted", 2, source_identity(WORLD, 2)),
        QuestEvidence("completion_reported", 3, source_identity(WORLD, 3)),
    )[:heard]
    return replace(
        initial,
        world_id=WORLD,
        tick=Tick(tick),
        components=(
            NpcQuestMemoryRecord(layout.npc_id, evidence),
            record_at(tick),
            GateRecord(layout.gate_id, layout.space_id, layout.gate_cell, opened),
        ),
        pending=(),
    )


@pytest.mark.parametrize(
    ("heard", "tick", "opened", "expected"),
    (
        (0, 8, 0, "의뢰를 직접 들은 뒤 통행 지원을 준비합니다."),
        (0, 16, 1, "의뢰를 직접 들은 뒤 통행 지원을 준비합니다."),
        (2, 4, 0, "완료 보고를 들어 통행 지원을 마쳤습니다."),
        (2, 16, 1, "완료 보고를 들어 통행 지원을 마쳤습니다."),
        (1, 4, 1, "통행문이 열려 있어 공동 물자 준비를 이어갑니다."),
        (1, 16, 1, "통행문이 열려 있어 공동 물자 준비를 이어갑니다."),
        (1, 3, 0, "공동 물자 2개를 더 확보하면 통행 지원을 준비합니다. (현재 0/3개)."),
        (1, 4, 0, "공동 물자 1개를 더 확보하면 통행 지원을 준비합니다. (현재 1/3개)."),
        (1, 8, 0, "공동 물자가 확보되어 통행 지원을 준비하고 있습니다."),
        (1, 16, 0, "공동 물자가 확보되어 통행 지원을 준비하고 있습니다."),
    ),
)
def test_literal_precedence_and_stock_boundaries(
    heard: int, tick: int, opened: int, expected: str
) -> None:
    core = source(heard=heard, tick=tick, opened=opened)
    before = core.components, core.tick, core.pins
    assert supply_support_plan(
        core, content().definition.layout, error_code="NPC_ACTIVITY_SOURCE"
    ) == ("NPC 지원 계획 · " + expected,)
    assert (core.components, core.tick, core.pins) == before


@pytest.mark.parametrize("error_code", ("NPC_ACTIVITY_SOURCE", "NPC_RECOLLECTION_SOURCE"))
@pytest.mark.parametrize("kind", ("memory", "supply", "gate"))
@pytest.mark.parametrize("mode", ("missing", "duplicate", "owner"))
def test_selected_source_must_be_exactly_one(error_code: str, kind: str, mode: str) -> None:
    core = source()
    selected_type = {"memory": NpcQuestMemoryRecord, "supply": CycleRecord, "gate": GateRecord}[
        kind
    ]
    target = next(record for record in core.components if type(record) is selected_type)
    remaining = tuple(record for record in core.components if record is not target)
    if mode == "missing":
        components = remaining
    elif mode == "duplicate":
        components = (*core.components, target)
    else:
        assert isinstance(target, (NpcQuestMemoryRecord, CycleRecord, GateRecord))
        components = (*remaining, replace(target, entity_id=EntityId("actor:other")))
    bad = replace(core, components=components)
    before = bad.components, bad.tick, bad.pins
    with pytest.raises(SaveError, match=error_code) as caught:
        supply_support_plan(bad, content().definition.layout, error_code=error_code)
    assert caught.value.code == error_code
    assert (bad.components, bad.tick, bad.pins) == before


@pytest.mark.parametrize("error_code", ("NPC_ACTIVITY_SOURCE", "NPC_RECOLLECTION_SOURCE"))
@pytest.mark.parametrize("mode", ("cell", "space", "open_range", "open_bool"))
def test_selected_gate_requires_exact_scenario_binding(error_code: str, mode: str) -> None:
    core = source()
    gate = next(record for record in core.components if isinstance(record, GateRecord))
    if mode == "cell":
        wrong = replace(gate, cell=gate.cell + 1)
    elif mode == "space":
        wrong = replace(gate, space_id=EntityId("space:other"))
    else:
        wrong = replace(gate, is_open=2 if mode == "open_range" else True)
    bad = replace(
        core, components=tuple(wrong if record is gate else record for record in core.components)
    )
    with pytest.raises(SaveError, match=error_code) as caught:
        supply_support_plan(bad, content().definition.layout, error_code=error_code)
    assert caught.value.code == error_code
    assert core.components[-1] is gate and gate.is_open == 0
