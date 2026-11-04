"""Saved local definitions and ordinary activities grounded in logical time."""

from dataclasses import dataclass

from domain.primitives import EntityId, MAX_INT, TypeKey, require_integer, require_namespace
from domain.state_types import ComponentRecord
from domain.world import LocalDetail, Resident, WorldCatalog, elaborate_place

SETTLEMENT_SCHEMA = TypeKey("world.settlement", 1)
INVENTORY_SCHEMA = TypeKey("world.inventory", 1)
DAY_ORIGIN_SECONDS = 8 * 3600
DAY_SECONDS = 24 * 3600


@dataclass(frozen=True, slots=True)
class SettlementRecord(ComponentRecord):
    entity_id: EntityId
    state: LocalDetail | None

    @property
    def schema(self) -> TypeKey:
        return SETTLEMENT_SCHEMA


def validate_settlement(world: WorldCatalog, record: SettlementRecord) -> None:
    if type(record) is not SettlementRecord or type(record.entity_id) is not str:
        raise ValueError("WORLD_SETTLEMENT_RECORD")
    world.place(record.entity_id)
    detail = record.state
    if detail is not None:
        if (
            type(detail) is not LocalDetail
            or type(detail.place_id) is not str
            or type(detail.sites) is not tuple
            or type(detail.residents) is not tuple
            or len(detail.sites) != 4
            or len(detail.residents) != 4
            or any(type(site) is not str for site in detail.sites)
        ):
            raise ValueError("WORLD_LOCAL_DEFINITION")
        for resident in detail.residents:
            if type(resident) is not Resident:
                raise ValueError("WORLD_LOCAL_DEFINITION")
            if any(
                type(value) is not str
                for value in (
                    resident.id,
                    resident.name,
                    resident.occupation,
                    resident.disposition,
                    resident.workplace,
                )
            ):
                raise ValueError("WORLD_LOCAL_DEFINITION")
            require_integer(resident.work_start_hour, 0, 23)
            require_integer(resident.work_end_hour, resident.work_start_hour + 1, 24)
    if record.state is not None and record.state != elaborate_place(world, record.entity_id):
        raise ValueError("WORLD_LOCAL_DEFINITION")


@dataclass(frozen=True, slots=True)
class InventoryState:
    gold: int
    items: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        require_integer(self.gold, 0, MAX_INT)
        if type(self.items) is not tuple or len(self.items) > 128:
            raise ValueError("WORLD_INVENTORY_ITEMS")
        for entry in self.items:
            if type(entry) is not tuple or len(entry) != 2:
                raise ValueError("WORLD_INVENTORY_ITEMS")
            identifier, count = entry
            if type(identifier) is not str:
                raise ValueError("WORLD_INVENTORY_ITEMS")
            require_namespace(identifier)
            require_integer(count, 1, MAX_INT)
        ids = tuple(item[0] for item in self.items)
        if ids != tuple(sorted(set(ids))):
            raise ValueError("WORLD_INVENTORY_ORDER")


@dataclass(frozen=True, slots=True)
class InventoryRecord(ComponentRecord):
    entity_id: EntityId
    state: InventoryState

    @property
    def schema(self) -> TypeKey:
        return INVENTORY_SCHEMA


@dataclass(frozen=True, slots=True)
class ResidentActivity:
    resident_id: str
    name: str
    activity: str
    site: str


def resident_activity(resident: Resident, tick: int) -> ResidentActivity:
    require_integer(tick)
    hour = ((tick + DAY_ORIGIN_SECONDS) % DAY_SECONDS) // 3600
    if resident.work_start_hour <= hour < resident.work_end_hour:
        activity, site = "일하는 중", resident.workplace
    elif 6 <= hour < 22:
        activity, site = "자유 시간", "시장"
    else:
        activity, site = "잠자는 중", "주거지"
    return ResidentActivity(resident.id, resident.name, activity, site)
