"""Literal saved/current plan labels and failures preserve both input snapshots."""

from dataclasses import replace

import pytest

from app.npc_support_status import support_slot_messages
from contracts.persistence import SaveError
from domain.encounter import GateRecord
from domain.npc_cycle import CycleRecord
from domain.npc_memory import NpcQuestMemoryRecord
from domain.primitives import EntityId
from tests.unit.quest_fixtures import content
from tests.unit.test_npc_support_status import source


@pytest.mark.parametrize(
    ("old_heard", "old_tick", "live_tick", "live_open", "old_text", "live_text"),
    (
        (
            1,
            3,
            8,
            0,
            "공동 물자 2개를 더 확보하면 통행 지원을 준비합니다. (현재 0/3개).",
            "공동 물자가 확보되어 통행 지원을 준비하고 있습니다.",
        ),
        (
            1,
            8,
            10,
            1,
            "공동 물자가 확보되어 통행 지원을 준비하고 있습니다.",
            "통행문이 열려 있어 공동 물자 준비를 이어갑니다.",
        ),
        (
            2,
            19,
            8,
            0,
            "완료 보고를 들어 통행 지원을 마쳤습니다.",
            "공동 물자가 확보되어 통행 지원을 준비하고 있습니다.",
        ),
        (
            1,
            3,
            3,
            0,
            "공동 물자 2개를 더 확보하면 통행 지원을 준비합니다. (현재 0/3개).",
            "공동 물자 2개를 더 확보하면 통행 지원을 준비합니다. (현재 0/3개).",
        ),
    ),
)
def test_literal_current_then_saved_order_even_for_future_or_equal_snapshots(
    old_heard: int,
    old_tick: int,
    live_tick: int,
    live_open: int,
    old_text: str,
    live_text: str,
) -> None:
    saved = source(heard=old_heard, tick=old_tick)
    current = source(heard=1, tick=live_tick, opened=live_open)
    before = saved.components, current.components, saved.pins, current.pins
    assert support_slot_messages(saved, current, content().definition.layout) == (
        f"NPC 지원 계획 비교 · 현재 {live_tick}초 / 선택 저장 {old_tick}초",
        "현재 NPC 지원 계획 · " + live_text,
        "선택 저장 NPC 지원 계획 · " + old_text,
    )
    assert (saved.components, current.components, saved.pins, current.pins) == before


@pytest.mark.parametrize("side", ("saved", "current"))
@pytest.mark.parametrize("kind", ("memory", "cycle", "gate"))
def test_malformed_selected_source_fails_without_partial_output_or_mutation(
    side: str, kind: str
) -> None:
    saved, current = source(tick=4), source(tick=8)
    selected = saved if side == "saved" else current
    typ = {"memory": NpcQuestMemoryRecord, "cycle": CycleRecord, "gate": GateRecord}[kind]
    bad = replace(selected, components=tuple(r for r in selected.components if type(r) is not typ))
    before = saved.components, current.components, bad.components
    with pytest.raises(SaveError, match="SAVE_INSPECT_FAILED") as caught:
        support_slot_messages(
            bad if side == "saved" else saved,
            bad if side == "current" else current,
            content().definition.layout,
        )
    assert caught.value.code == "SAVE_INSPECT_FAILED"
    assert (saved.components, current.components, bad.components) == before


@pytest.mark.parametrize("side", ("saved", "current"))
def test_gate_binding_failure_in_either_plan_preserves_exact_code(side: str) -> None:
    saved, current = source(tick=4), source(tick=8)
    selected = saved if side == "saved" else current
    bad = replace(
        selected,
        components=tuple(
            replace(r, space_id=EntityId("space:other")) if isinstance(r, GateRecord) else r
            for r in selected.components
        ),
    )
    with pytest.raises(SaveError, match="SAVE_INSPECT_FAILED") as caught:
        support_slot_messages(
            bad if side == "saved" else saved,
            bad if side == "current" else current,
            content().definition.layout,
        )
    assert caught.value.code == "SAVE_INSPECT_FAILED"
