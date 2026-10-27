"""Boot-time patrol bounds;authoritative position remains in the existing NPC record."""

from domain.primitives import require_integer
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


class NpcScope(ScenarioBound):
    def __init__(self, layout: Scenario = LEGACY, *, npc_patrol: bool = False) -> None:
        super().__init__(layout)
        self._npc_cells = patrol_cells(layout, npc_patrol)
        self._npc_patrol = npc_patrol
