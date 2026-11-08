"""Player-facing terms derived from actual saved city goods and quest state."""

from dataclasses import dataclass

from contracts.world_supply import SupplyAction
from domain.world import LocalDetail
from domain.world_population import InventoryState
from domain.world_supply import (
    DELIVERY_REWARD,
    REPAIR_CRATES,
    STOCK_CAP,
    WAREHOUSE_CAP,
    SupplyScenario,
    SupplyState,
    blocked,
    available_supply_operation,
)


@dataclass(frozen=True, slots=True)
class SupplyOffer:
    action: SupplyAction
    npc_name: str
    summary: str


AUTHORED_SUPPLY_COMPLETE = "상인: “덕분에 보급로가 다시 열렸어요. 고맙습니다.”"
SUPPLY_ACTION_LABELS = {"accept": "의뢰 받기", "collect": "상자 받기", "deliver": "상자 전달하기"}


def authored_supply_line(offer: SupplyOffer) -> str:
    """Written lines for the action already offered by the committed world."""
    line = {
        "accept": f"길이 막혀 시장에 물자가 끊겼어요. 운송인에게 상자 {REPAIR_CRATES}개를 받아 제게 가져다주세요.",
        "collect": "복구에 쓸 상자를 하나 내드릴게요. 필요한 만큼 받으면 상인에게 가져가세요.",
        "deliver": "필요한 상자가 다 모였네요. 건네주시면 바로 길을 고치는 데 쓰겠습니다.",
    }[offer.action.operation]
    return f"{offer.npc_name}: “{line}”"


def supply_offers(
    local: LocalDetail,
    state: SupplyState,
    inventory: InventoryState,
    scenario: SupplyScenario,
    tick: int,
) -> tuple[SupplyOffer, ...]:
    operation = available_supply_operation(state, inventory, scenario, local.place_id, tick)
    if operation == "none":
        return ()
    npc = local.residents[0 if operation == "collect" else 1]
    terms = {
        "accept": f"보급로 복구 의뢰를 수락합니다. 운송인에게 보급품 {REPAIR_CRATES}개를 받아 상인에게 전달하세요. "
        f"전달 시 보급품은 복구에 소비되며 보상 {DELIVERY_REWARD}금을 한 번 받습니다.",
        "collect": f"도시 창고에서 복구용 보급품 1개를 받습니다. 현재 수령 {state.claimed}/{REPAIR_CRATES}개.",
        "deliver": f"복구용 보급품 {REPAIR_CRATES}개를 전달·소비하고 보상 {DELIVERY_REWARD}금을 받습니다. 보급로가 다시 열립니다.",
    }
    summary = (
        f"{npc.name} · {npc.occupation}\n{terms[operation]}\n"
        f"기한: 게임 경과 {scenario.end_tick}초 전 (현재 {tick}초). "
        "기한이 지나면 전달·보상은 불가능하고 이미 받은 짐은 소지품에 남습니다.\n"
        "확인 시 현재 위치·기한·재고·소지품을 다시 검증합니다. 행동 시간 1초."
    )
    return (SupplyOffer(SupplyAction(local.place_id, npc.id, operation), npc.name, summary),)


def supply_status(
    state: SupplyState,
    scenario: SupplyScenario,
    place_id: str,
    tick: int,
    *,
    authored: bool = False,
) -> str:
    situation = (
        "보급로 복구 완료"
        if state.stage == 2
        else "의뢰 기한 종료"
        if state.stage == 3
        else "보급 차질 발생"
        if blocked(scenario, place_id, state, tick)
        else "보급 정상"
    )
    status = f"{situation} · 시장 재고 {state.stock}/{STOCK_CAP} · 창고 {state.warehouse}/{WAREHOUSE_CAP} · 미충족 수요 {state.missed}"
    if authored and state.stage == 2:
        return f"{status}\n{AUTHORED_SUPPLY_COMPLETE}"
    if authored and place_id == scenario.place_id and tick < scenario.start_tick:
        return f"{status}\n잠시 기다리면 상인의 보급 의뢰 대화가 열립니다."
    return status


def item_label(item_id: str) -> str:
    return (
        "복구용 보급품 (" + item_id.removeprefix("item:supply-") + ")"
        if item_id.startswith("item:supply-")
        else item_id
    )


def supply_notice(code: str) -> str:
    return {
        "SUPPLY_INACTIVE": "기한이 끝났거나 이미 보급로가 복구되어 진행할 수 없습니다.",
        "SUPPLY_OUT_OF_REACH": "해당 도시로 돌아와야 진행할 수 있습니다.",
        "SUPPLY_WRONG_NPC": "이 주민은 해당 업무를 담당하지 않습니다.",
        "SUPPLY_QUEST_STAGE": "의뢰 진행 상태가 달라졌습니다. 현재 제안을 다시 확인하세요.",
        "SUPPLY_ALREADY_COLLECTED": "보급품을 이미 모두 받았습니다.",
        "SUPPLY_WAREHOUSE_EMPTY": "도시 창고에 남은 보급품이 없습니다.",
        "SUPPLY_ITEMS_MISSING": "이 도시의 복구용 보급품 2개가 필요합니다.",
    }.get(code, "진행하지 못했습니다: " + code)
