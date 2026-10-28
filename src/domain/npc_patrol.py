"""Boot-time patrol bounds;authoritative position remains in the existing NPC record."""

from typing import Literal

from domain.primitives import require_integer
from domain.npc_work import STOCK_CAP, SUPPORT_STOCK_MIN
from domain.scenario import LEGACY, Scenario, ScenarioBound


def patrol_cells(layout: Scenario, enabled: bool) -> tuple[int, ...]:
    if type(enabled) is not bool:
        raise ValueError("NPC_PATROL_CONTENT")
    if not enabled:
        return (layout.npc_cell,)
    first, second = layout.npc_cell, layout.npc_cell + 1
    require_integer(first, 0, 8)
    require_integer(second, 0, 8)
    if first // 3 != second // 3 or second in (
        *layout.blocked_cells,
        layout.gate_cell,
        layout.enemy_cell,
    ):
        raise ValueError("NPC_PATROL_CONTENT")
    return first, second


type QuestPatrolPhase = Literal["available", "accepted", "reported"]


def quest_patrol_target(layout: Scenario, current: int, known_phase: QuestPatrolPhase) -> int:
    """Choose only the existing goal cell;wake,conversation and occupancy stay with callers."""
    home, neighbor = patrol_cells(layout, True)
    if (
        type(current) is not int
        or current not in (home, neighbor)
        or type(known_phase) is not str
        or known_phase not in ("available", "accepted", "reported")
        or known_phase == "available"
        and current != home
    ):
        raise ValueError("NPC_QUEST_PATROL_TARGET")
    if known_phase == "accepted":
        return neighbor if current == home else home
    return home


def ready_patrol_target(
    layout: Scenario, current: int, known_phase: QuestPatrolPhase, stock: int, is_open: int
) -> int:
    """Prefer the existing support work point while its own required supplies are short."""
    if (
        type(stock) is not int
        or not 0 <= stock <= STOCK_CAP
        or type(is_open) is not int
        or is_open not in (0, 1)
    ):
        raise ValueError("NPC_READY_PATROL_TARGET")
    try:
        target = quest_patrol_target(layout, current, known_phase)
    except ValueError as error:
        raise ValueError("NPC_READY_PATROL_TARGET") from error
    if known_phase == "accepted" and is_open == 0 and stock < SUPPORT_STOCK_MIN:
        return layout.npc_cell
    return target


class NpcScope(ScenarioBound):
    def __init__(self, layout: Scenario = LEGACY, *, npc_patrol: bool = False) -> None:
        super().__init__(layout)
        self._npc_cells = patrol_cells(layout, npc_patrol)
        self._npc_patrol = npc_patrol
