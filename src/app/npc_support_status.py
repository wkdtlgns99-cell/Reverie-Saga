"""Project the existing supply-aid plan from an already verified current checkpoint."""

from contracts.persistence import SaveError
from domain.encounter import GateRecord
from domain.npc_cycle import CycleRecord
from domain.npc_memory import NpcQuestMemoryRecord
from domain.npc_work import STOCK_CAP, SUPPORT_STOCK_MIN
from domain.scenario import Scenario
from domain.state_types import CoreSnapshot


def supply_support_plan(
    core: CoreSnapshot, layout: Scenario, *, error_code: str, npc_call_aid: bool = False
) -> tuple[str, ...]:
    if type(npc_call_aid) is not bool:
        raise ValueError("NPC_CALL_AID_CONTENT")
    memories = tuple(
        record
        for record in core.components
        if type(record) is NpcQuestMemoryRecord and record.entity_id == layout.npc_id
    )
    supplies = tuple(
        record
        for record in core.components
        if type(record) is CycleRecord and record.entity_id == layout.npc_id
    )
    gates = tuple(
        record
        for record in core.components
        if type(record) is GateRecord and record.entity_id == layout.gate_id
    )
    if len(memories) != 1 or len(supplies) != 1 or len(gates) != 1:
        raise SaveError(error_code, "support plan requires selected NPC memory/supply/gate")
    memory, supply, gate = memories[0], supplies[0].state, gates[0]
    if (
        gate.space_id != layout.space_id
        or gate.cell != layout.gate_cell
        or type(gate.is_open) is not int
        or gate.is_open not in (0, 1)
    ):
        raise SaveError(error_code, "support plan gate binding differs from selected scenario")
    # Current readiness is neither a historical aid fact nor a promised execution time.
    if not memory.entries:
        plan = "의뢰를 직접 들은 뒤 통행 지원을 준비합니다."
    elif memory.entries[-1].kind == "completion_reported":
        plan = "완료 보고를 들어 통행 지원을 마쳤습니다."
    elif gate.is_open:
        plan = "통행문이 열려 있어 공동 물자 준비를 이어갑니다."
    elif supply.stock < SUPPORT_STOCK_MIN:
        plan = (
            f"공동 물자 {SUPPORT_STOCK_MIN - supply.stock}개를 더 확보하면 통행 지원을 준비합니다. "
            f"(현재 {supply.stock}/{STOCK_CAP}개)."
        )
    else:
        plan = (
            "공동 물자가 확보되어 NPC 호출로 통행 지원을 요청할 수 있습니다."
            if npc_call_aid
            else "공동 물자가 확보되어 통행 지원을 준비하고 있습니다."
        )
    return ("NPC 지원 계획 · " + plan,)


def support_slot_messages(
    saved: CoreSnapshot, current: CoreSnapshot, layout: Scenario, *, npc_call_aid: bool = False
) -> tuple[str, ...]:
    """Label plans after the slot caller validates both checkpoint identities."""
    live = supply_support_plan(
        current, layout, error_code="SAVE_INSPECT_FAILED", npc_call_aid=npc_call_aid
    )
    selected = supply_support_plan(
        saved, layout, error_code="SAVE_INSPECT_FAILED", npc_call_aid=npc_call_aid
    )
    return (
        f"NPC 지원 계획 비교 · 현재 {current.tick}초 / 선택 저장 {saved.tick}초",
        *("현재 " + line for line in live),
        *("선택 저장 " + line for line in selected),
    )
