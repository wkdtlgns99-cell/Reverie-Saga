"""Patrol pose labels use selected snapshot records,never clock parity or history."""

from dataclasses import replace
from typing import cast

import pytest

from app.client_session import _patrol_slot_messages
from app.npc_cycle import bootstrap_cycle
from app.watch import WatchBootstrapSpec
from contracts.persistence import SaveError
from domain.primitives import EntityId, Tick
from domain.state_types import CoreSnapshot
from domain.watch import WatchNpcRecord
from tests.unit.quest_fixtures import content


def source(cell: int = 6, tick: int = 4) -> CoreSnapshot:
    selected = content()
    initial = bootstrap_cycle(
        WatchBootstrapSpec("0" * 64, "1" * 32, "2" * 32),
        selected,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
    ).snapshot()
    layout = selected.definition.layout
    return replace(
        initial,
        tick=Tick(tick),
        components=(WatchNpcRecord(layout.npc_id, layout.space_id, cell, 0),),
    )


@pytest.mark.parametrize(("live", "saved"), ((6, 6), (6, 7), (7, 6), (7, 7)))
def test_actual_endpoint_pairs_even_when_clock_order_is_reversed(live: int, saved: int) -> None:
    current, old = source(live, 2), source(saved, 4)
    before = current, old
    assert _patrol_slot_messages(old, current, content().definition.layout) == (
        "NPC 순찰 위치 비교 · 현재 2초 / 선택 저장 4초",
        "현재 NPC 위치 · " + ("원래" if live == 6 else "옆") + " 작업 지점입니다.",
        "선택 저장 NPC 위치 · " + ("원래" if saved == 6 else "옆") + " 작업 지점입니다.",
    )
    assert (current, old) == before


@pytest.mark.parametrize("saved_side", (False, True))
@pytest.mark.parametrize(
    "bad", ("missing", "duplicate", "foreign", "owner", "bool", "float", "outside")
)
def test_invalid_selected_record_fails_explicitly_without_source_mutation(
    saved_side: bool, bad: str
) -> None:
    good = source()
    layout = content().definition.layout
    npc = WatchNpcRecord(layout.npc_id, layout.space_id, 6, 0)
    records: tuple[WatchNpcRecord, ...]
    if bad == "missing":
        records = ()
    elif bad == "duplicate":
        records = (npc, npc)
    else:
        npc = (
            replace(npc, space_id=EntityId("space:foreign"))
            if bad == "foreign"
            else replace(npc, entity_id=EntityId("actor:foreign"))
            if bad == "owner"
            else replace(
                npc, cell=cast(int, True if bad == "bool" else 6.0 if bad == "float" else 8)
            )
        )
        records = (npc,)
    invalid = replace(good, components=records)
    before = good, invalid
    with pytest.raises(SaveError) as caught:
        _patrol_slot_messages(
            invalid if saved_side else good, good if saved_side else invalid, layout
        )
    assert caught.value.code == "SAVE_INSPECT_FAILED"
    assert (good, invalid) == before


def test_other_npc_records_do_not_replace_selected_subject() -> None:
    current = source(7)
    saved = source(6)
    other = WatchNpcRecord(EntityId("actor:other"), EntityId("space:other"), 8, 0)
    assert _patrol_slot_messages(
        replace(saved, components=(*saved.components, other)),
        replace(current, components=(other, *current.components)),
        content().definition.layout,
    ) == _patrol_slot_messages(saved, current, content().definition.layout)
