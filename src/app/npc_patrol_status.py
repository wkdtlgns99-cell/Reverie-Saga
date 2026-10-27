"""Describe a derived patrol goal from the already verified current snapshot."""

from contracts.persistence import SaveError
from domain.npc_memory import NpcQuestMemoryRecord
from domain.npc_patrol import patrol_cells
from domain.scenario import Scenario
from domain.state_types import CoreSnapshot
from domain.watch import WatchNpcRecord


def quest_patrol_plan(core: CoreSnapshot, layout: Scenario, *, error_code: str) -> tuple[str, ...]:
    memories = tuple(
        record
        for record in core.components
        if type(record) is NpcQuestMemoryRecord and record.entity_id == layout.npc_id
    )
    npcs = tuple(
        record
        for record in core.components
        if type(record) is WatchNpcRecord and record.entity_id == layout.npc_id
    )
    if len(memories) != 1 or len(npcs) != 1:
        raise SaveError(error_code, "quest patrol plan requires selected memory/NPC")
    memory, npc = memories[0], npcs[0]
    if (
        npc.space_id != layout.space_id
        or type(npc.cell) is not int
        or npc.cell not in patrol_cells(layout, True)
        or any(entry.observed_at > core.tick for entry in memory.entries)
        or memory.known_phase == "available"
        and npc.cell != layout.npc_cell
    ):
        raise SaveError(error_code, "quest patrol plan current source differs")
    if memory.known_phase == "available":
        plan = "수락을 직접 듣기 전에는 원래 작업 지점에서 기다립니다."
    elif memory.known_phase == "accepted":
        plan = "수락을 직접 들어 공동 작업 구역 순찰을 목표로 합니다."
    elif npc.cell != layout.npc_cell:
        plan = "완료 보고를 들어 원래 작업 지점으로 돌아갈 준비를 합니다."
    else:
        plan = "완료 보고를 들어 원래 작업 지점에서 기다립니다."
    return ("NPC 의뢰 순찰 계획 · " + plan,)


def quest_patrol_slot_messages(
    saved: CoreSnapshot, current: CoreSnapshot, layout: Scenario
) -> tuple[str, ...]:
    """Label each snapshot's existing goal without loading either saved branch."""
    live = quest_patrol_plan(current, layout, error_code="SAVE_INSPECT_FAILED")
    selected = quest_patrol_plan(saved, layout, error_code="SAVE_INSPECT_FAILED")
    return (
        f"NPC 의뢰 순찰 계획 비교 · 현재 {current.tick}초 / 선택 저장 {saved.tick}초",
        *("현재 " + line for line in live),
        *("선택 저장 " + line for line in selected),
    )
