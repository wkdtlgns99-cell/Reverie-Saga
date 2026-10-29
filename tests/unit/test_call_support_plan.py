"""Literal availability/priority and checkpoint labels,without state prediction."""

from dataclasses import replace
from typing import cast

import pytest

from app.npc_support_status import supply_support_plan, support_slot_messages
from contracts.persistence import SaveError
from domain.encounter import GateRecord
from tests.unit.quest_fixtures import content
from tests.unit.test_npc_support_status import source

HINT = "NPC 지원 계획 · 공동 물자가 확보되어 NPC 호출로 통행 지원을 요청할 수 있습니다."
OLD = "NPC 지원 계획 · 공동 물자가 확보되어 통행 지원을 준비하고 있습니다."


@pytest.mark.parametrize(
    "heard,tick,opened,ready",
    (
        (0, 8, 0, False),
        (0, 16, 1, False),
        (2, 8, 0, False),
        (2, 16, 1, False),
        (1, 4, 1, False),
        (1, 16, 1, False),
        (1, 3, 0, False),
        (1, 4, 0, False),
        (1, 8, 0, True),
        (1, 16, 0, True),
    ),
)
def test_only_ready_closed_unreported_heard_state_has_call_instruction(
    heard: int,
    tick: int,
    opened: int,
    ready: bool,
) -> None:
    core = source(heard=heard, tick=tick, opened=opened)
    before = core.components, core.tick, core.pins
    old = supply_support_plan(core, content().definition.layout, error_code="NPC_ACTIVITY_SOURCE")
    current = supply_support_plan(
        core, content().definition.layout, error_code="NPC_ACTIVITY_SOURCE", npc_call_aid=True
    )
    assert current == ((HINT,) if ready else old)
    if ready:
        assert old == (OLD,)
    assert (core.components, core.tick, core.pins) == before


@pytest.mark.parametrize("opened", (0, 1))
def test_slot_labels_use_each_snapshot_readiness(opened: int) -> None:
    saved = source(tick=8)
    live = source(tick=16, opened=opened)
    current_line = (
        HINT if not opened else "NPC 지원 계획 · 통행문이 열려 있어 공동 물자 준비를 이어갑니다."
    )
    assert support_slot_messages(saved, live, content().definition.layout, npc_call_aid=True) == (
        "NPC 지원 계획 비교 · 현재 16초 / 선택 저장 8초",
        "현재 " + current_line,
        "선택 저장 " + HINT,
    )
    assert support_slot_messages(saved, saved, content().definition.layout, npc_call_aid=True) == (
        "NPC 지원 계획 비교 · 현재 8초 / 선택 저장 8초",
        "현재 " + HINT,
        "선택 저장 " + HINT,
    )


@pytest.mark.parametrize("value", (0, 1, None, "1", 2.0))
def test_flag_is_exact_bool_before_projection(value: object) -> None:
    core = source()
    bad = replace(core, components=())
    with pytest.raises(ValueError, match="^NPC_CALL_AID_CONTENT$"):
        supply_support_plan(
            bad,
            content().definition.layout,
            error_code="NPC_ACTIVITY_SOURCE",
            npc_call_aid=cast(bool, value),
        )
    with pytest.raises(ValueError, match="^NPC_CALL_AID_CONTENT$"):
        support_slot_messages(
            core, bad, content().definition.layout, npc_call_aid=cast(bool, value)
        )


@pytest.mark.parametrize("side", ("current", "saved"))
def test_source_error_code_is_preserved_before_any_hint(side: str) -> None:
    core = source()
    bad = replace(core, components=tuple(c for c in core.components if type(c) is not GateRecord))
    before = core.components, core.tick, core.pins, bad.components
    with pytest.raises(SaveError, match="^SAVE_INSPECT_FAILED:") as error:
        support_slot_messages(
            bad if side == "saved" else core,
            bad if side == "current" else core,
            content().definition.layout,
            npc_call_aid=True,
        )
    assert error.value.code == "SAVE_INSPECT_FAILED"
    assert (core.components, core.tick, core.pins, bad.components) == before
