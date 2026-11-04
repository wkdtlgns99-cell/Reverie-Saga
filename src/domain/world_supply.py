"""Bounded supply incident,resource conservation and deterministic scenario variation."""

from dataclasses import dataclass, replace
import hashlib
import re

from domain.primitives import EntityId, TypeKey, require_integer
from domain.state_types import ComponentRecord
from domain.world import Resident, WorldCatalog
from domain.world_population import InventoryState, ResidentActivity, resident_activity

SUPPLY_SCHEMA = TypeKey("world.supply", 1)
STOCK_CAP = 3
WAREHOUSE_CAP = 6
REPAIR_CRATES = 2
DELIVERY_REWARD = 5
INITIAL_TREASURY = 15
SUPPLY_INTERVAL_SECONDS = 20
CONSUMPTION_INTERVAL_SECONDS = 30


@dataclass(frozen=True, slots=True)
class SupplyScenario:
    place_id: str = "place:p0-a"
    start_tick: int = 30
    end_tick: int = 630

    def __post_init__(self) -> None:
        if type(self.place_id) is not str:
            raise ValueError("SUPPLY_SCENARIO_PLACE")
        require_integer(self.start_tick, 1)
        require_integer(self.end_tick, self.start_tick + 1)


@dataclass(frozen=True, slots=True)
class SupplyState:
    stock: int = STOCK_CAP
    warehouse: int = WAREHOUSE_CAP
    stage: int = 0
    claimed: int = 0
    repair_used: int = 0
    received: int = 0
    consumed: int = 0
    missed: int = 0
    treasury: int = INITIAL_TREASURY
    resolved_tick: int = 0

    def __post_init__(self) -> None:
        for value in (
            self.stock,
            self.warehouse,
            self.stage,
            self.claimed,
            self.repair_used,
            self.received,
            self.consumed,
            self.missed,
            self.treasury,
            self.resolved_tick,
        ):
            require_integer(value)
        if (
            self.stock > STOCK_CAP
            or self.warehouse > WAREHOUSE_CAP
            or self.stage > 3
            or self.claimed > REPAIR_CRATES
            or self.repair_used > self.claimed
            or self.treasury != INITIAL_TREASURY - (DELIVERY_REWARD if self.stage == 2 else 0)
            or (self.stage == 2) != bool(self.resolved_tick)
            or self.repair_used != (REPAIR_CRATES if self.stage == 2 else 0)
        ):
            raise ValueError("SUPPLY_STATE")
        if STOCK_CAP + WAREHOUSE_CAP + self.received != (
            self.stock + self.warehouse + self.consumed + self.claimed
        ):
            raise ValueError("SUPPLY_CONSERVATION")


@dataclass(frozen=True, slots=True)
class SupplyRecord(ComponentRecord):
    entity_id: EntityId
    state: SupplyState

    @property
    def schema(self) -> TypeKey:
        return SUPPLY_SCHEMA


def supply_item(place_id: str) -> str:
    return "item:supply-" + place_id.removeprefix("place:")


def blocked(scenario: SupplyScenario, place_id: str, state: SupplyState, tick: int) -> bool:
    return (
        place_id == scenario.place_id
        and scenario.start_tick <= tick < scenario.end_tick
        and state.stage != 2
    )


def advance_supply(
    before: SupplyState, scenario: SupplyScenario, place_id: str, tick: int
) -> SupplyState:
    require_integer(tick, 1)
    stock, warehouse = before.stock, before.warehouse
    consumed, received, missed = before.consumed, before.received, before.missed
    stage = before.stage
    if place_id == scenario.place_id and tick >= scenario.end_tick and stage != 2:
        stage = 3
    if tick % CONSUMPTION_INTERVAL_SECONDS == 0:
        if stock:
            stock -= 1
            consumed += 1
        else:
            missed += 1
    if tick % SUPPLY_INTERVAL_SECONDS == 0:
        if warehouse < WAREHOUSE_CAP:
            warehouse += 1
            received += 1
        if not blocked(scenario, place_id, before, tick) and warehouse and stock < STOCK_CAP:
            warehouse -= 1
            stock += 1
    return replace(
        before,
        stock=stock,
        warehouse=warehouse,
        stage=stage,
        consumed=consumed,
        received=received,
        missed=missed,
    )


def supply_action(
    before: SupplyState,
    inventory: InventoryState,
    scenario: SupplyScenario,
    place_id: str,
    operation: str,
    tick: int,
) -> tuple[SupplyState, InventoryState]:
    require_integer(tick, 1)
    if not blocked(scenario, place_id, before, tick):
        raise ValueError("SUPPLY_INACTIVE")
    if type(operation) is not str or operation not in ("accept", "collect", "deliver"):
        raise ValueError("INVALID_COMMAND")
    if operation == "accept":
        if before.stage != 0:
            raise ValueError("SUPPLY_QUEST_STAGE")
        return replace(before, stage=1), inventory
    if before.stage != 1:
        raise ValueError("SUPPLY_QUEST_STAGE")
    items = dict(inventory.items)
    item = supply_item(place_id)
    if operation == "collect":
        if before.claimed == REPAIR_CRATES:
            raise ValueError("SUPPLY_ALREADY_COLLECTED")
        if not before.warehouse:
            raise ValueError("SUPPLY_WAREHOUSE_EMPTY")
        items[item] = items.get(item, 0) + 1
        return (
            replace(before, warehouse=before.warehouse - 1, claimed=before.claimed + 1),
            InventoryState(inventory.gold, tuple(sorted(items.items()))),
        )
    if items.get(item, 0) < REPAIR_CRATES or before.claimed != REPAIR_CRATES:
        raise ValueError("SUPPLY_ITEMS_MISSING")
    left = items[item] - REPAIR_CRATES
    if left:
        items[item] = left
    else:
        del items[item]
    return (
        replace(
            before,
            stage=2,
            repair_used=REPAIR_CRATES,
            treasury=before.treasury - DELIVERY_REWARD,
            resolved_tick=tick,
        ),
        InventoryState(inventory.gold + DELIVERY_REWARD, tuple(sorted(items.items()))),
    )


def supply_activity(
    resident: Resident,
    index: int,
    tick: int,
    scenario: SupplyScenario,
    place_id: str,
    state: SupplyState,
) -> ResidentActivity:
    normal = resident_activity(resident, tick)
    if normal.activity == "잠자는 중":
        return normal
    if index == 0 and blocked(scenario, place_id, state, tick):
        return ResidentActivity(
            resident.id, resident.name, "대체 보급로 찾는 중", resident.workplace
        )
    if index == 1 and state.stock <= 1:
        return ResidentActivity(resident.id, resident.name, "물자 부족으로 판매 제한", "시장")
    if index >= 2 and state.stock == 0:
        return ResidentActivity(resident.id, resident.name, "배급 대기 중", "시장")
    return normal


def scenario_from_seed(world: WorldCatalog, seed_hex: str) -> SupplyScenario:
    if type(seed_hex) is not str or re.fullmatch("[0-9a-f]{64}", seed_hex) is None:
        raise ValueError("SUPPLY_SCENARIO_SEED")
    data = hashlib.sha256(("supply-scenario/v1:" + seed_hex).encode()).digest()
    place = world.places[int.from_bytes(data[:4]) % len(world.places)].id
    start = 30 + int.from_bytes(data[4:8]) % 61
    duration = 300 + int.from_bytes(data[8:12]) % 601
    return SupplyScenario(place, start, start + duration)
