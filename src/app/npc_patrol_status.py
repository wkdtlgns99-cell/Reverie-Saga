"""Describe a derived patrol goal from the already verified current snapshot."""

from contracts.persistence import SaveError
from domain.npc_memory import NpcQuestMemoryRecord
from domain.npc_patrol import patrol_cells, quest_patrol_target, ready_patrol_target
from domain.npc_cycle import CycleRecord, Supply, state_at
from domain.encounter import GateRecord
from domain.npc_work import SUPPORT_STOCK_MIN
from domain.scenario import Scenario
from domain.state_types import CoreSnapshot
from domain.watch import WatchNpcRecord
from domain.trial import CellPositionRecord
from domain.primitives import MAX_INT


READY_PATROL_POLICY = (
    "NPC 지원 준비 · 의뢰 진행 중 통행문이 닫혀 있고 공동 물자가 "
    f"{SUPPORT_STOCK_MIN}개 미만이면 원래 작업 지점 복귀·대기를 우선합니다."
)


def _quest_patrol_source(
    core: CoreSnapshot, layout: Scenario, *, error_code: str
) -> tuple[NpcQuestMemoryRecord, WatchNpcRecord, int]:
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
    ):
        raise SaveError(error_code, "quest patrol plan current source differs")
    try:
        target = quest_patrol_target(layout, npc.cell, memory.known_phase)
    except ValueError as error:
        raise SaveError(error_code, "quest patrol plan current source differs") from error
    return memory, npc, target


def quest_patrol_plan(core: CoreSnapshot, layout: Scenario, *, error_code: str) -> tuple[str, ...]:
    memory, npc, target = _quest_patrol_source(core, layout, error_code=error_code)
    if memory.known_phase == "available":
        plan = "수락을 직접 듣기 전에는 원래 작업 지점에서 기다립니다."
    elif memory.known_phase == "accepted":
        plan = "수락을 직접 들어 공동 작업 구역 순찰을 목표로 합니다."
    elif npc.cell != target:
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


def quest_patrol_next_step(
    core: CoreSnapshot, layout: Scenario, *, error_code: str, npc_ready_patrol: bool = False
) -> tuple[str, ...]:
    """Describe current movement conditions,without promising a future turn or stored pause."""
    if type(core.tick) is not int or not 0 <= core.tick <= MAX_INT:
        raise SaveError(error_code, "quest patrol step source tick differs")
    if type(npc_ready_patrol) is not bool:
        raise SaveError(error_code, "ready patrol step selection differs")
    memory, npc, target = _quest_patrol_source(core, layout, error_code=error_code)
    if npc_ready_patrol:
        target = _ready_source_target(core, layout, memory, npc, error_code=error_code)
    actors = tuple(
        record
        for record in core.components
        if type(record) is CellPositionRecord and record.entity_id == layout.actor_id
    )
    if len(actors) != 1:
        raise SaveError(error_code, "quest patrol step requires selected actor")
    actor = actors[0]
    if actor.space_id != layout.space_id or type(actor.cell) is not int or not 0 <= actor.cell <= 8:
        raise SaveError(error_code, "quest patrol step actor binding differs")
    label = "원래 작업 지점" if target == layout.npc_cell else "옆 작업 지점"
    if target == npc.cell:
        action = "현재 작업 지점에서 기다립니다. (현재 상태 기준)"
    elif target == actor.cell:
        action = f"{label}을 플레이어가 점유 중입니다. 현재 상태에서는 이동을 기다립니다."
    else:
        action = f"다음 행동 시점에 {label}으로 이동을 시도합니다. (현재 상태 기준)"
    return ("NPC 다음 순찰 행동 · " + action,)


def quest_patrol_step_slot_messages(
    saved: CoreSnapshot, current: CoreSnapshot, layout: Scenario, *, npc_ready_patrol: bool = False
) -> tuple[str, ...]:
    live = quest_patrol_next_step(
        current, layout, error_code="SAVE_INSPECT_FAILED", npc_ready_patrol=npc_ready_patrol
    )
    selected = quest_patrol_next_step(
        saved, layout, error_code="SAVE_INSPECT_FAILED", npc_ready_patrol=npc_ready_patrol
    )
    return (
        f"NPC 다음 순찰 행동 비교 · 현재 {current.tick}초 / 선택 저장 {saved.tick}초",
        *("현재 " + line for line in live),
        *("선택 저장 " + line for line in selected),
        *((READY_PATROL_POLICY,) if npc_ready_patrol else ()),
    )


def _ready_source_target(
    core: CoreSnapshot,
    layout: Scenario,
    memory: NpcQuestMemoryRecord,
    npc: WatchNpcRecord,
    *,
    error_code: str,
) -> int:
    cycles = tuple(
        record
        for record in core.components
        if type(record) is CycleRecord and record.entity_id == layout.npc_id
    )
    gates = tuple(
        record
        for record in core.components
        if type(record) is GateRecord and record.entity_id == layout.gate_id
    )
    if len(cycles) != 1 or len(gates) != 1:
        raise SaveError(error_code, "ready patrol step requires selected cycle/gate")
    supply, gate = cycles[0].state, gates[0]
    if type(supply) is not Supply or supply != state_at(core.tick):
        raise SaveError(error_code, "ready patrol step current cycle differs")
    if (
        gate.space_id != layout.space_id
        or type(gate.cell) is not int
        or gate.cell != layout.gate_cell
        or type(gate.is_open) is not int
        or gate.is_open not in (0, 1)
    ):
        raise SaveError(error_code, "ready patrol step gate binding differs")
    try:
        return ready_patrol_target(layout, npc.cell, memory.known_phase, supply.stock, gate.is_open)
    except ValueError as error:
        raise SaveError(error_code, "ready patrol step current target differs") from error
