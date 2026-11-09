"""Player-facing village placement and the existing authored supply offers."""

from dataclasses import dataclass

from app.world_supply import (
    AUTHORED_SUPPLY_COMPLETE,
    SUPPLY_ACTION_LABELS,
    SupplyOffer,
    authored_supply_line,
    supply_offers,
    supply_status,
)
from contracts.turn import ProtocolSnapshot
from domain.canonical import JsonObject, hash_document
from domain.state_types import CoreSnapshot
from domain.world import Resident
from domain.world_population import InventoryRecord, SettlementRecord
from domain.world_social import HOSTILE_THRESHOLD, SocialCatalog, SocialRecord, reaction
from domain.world_supply import (
    STOCK_CAP,
    REPAIR_CRATES,
    SupplyRecord,
    SupplyScenario,
    blocked,
    supply_item,
)
from domain.world_village import SUPPLY_RESIDENT_TILES, VillagePosition


@dataclass(frozen=True, slots=True)
class VillageResident:
    resident: Resident
    x: int
    y: int

    def adjacent(self, position: VillagePosition) -> bool:
        return abs(position.x - self.x) + abs(position.y - self.y) == 1

    def wire(self) -> JsonObject:
        return {"id": self.resident.id, "role": self.resident.occupation, "x": self.x, "y": self.y}


@dataclass(frozen=True, slots=True)
class VillageSupply:
    residents: tuple[VillageResident, ...]
    offer: SupplyOffer | None
    status: str
    cargo: int
    gold: int
    completed: bool
    stock: int
    road_blocked: bool

    def interaction(
        self, npc: VillageResident, position: VillagePosition, protocol: ProtocolSnapshot
    ) -> JsonObject:
        offer = self.offer
        resident = npc.resident
        if offer is not None and offer.action.npc_id == resident.id:
            token = hash_document(
                "village-supply-confirmation/v1",
                {
                    "branch": protocol.branch_id,
                    "revision": protocol.revision,
                    "position": (position.x, position.y),
                    "npc": resident.id,
                    "action": offer.action.operation,
                    "terms": offer.summary,
                },
            )
            return {
                "line": authored_supply_line(offer),
                "terms": offer.summary,
                "label": SUPPLY_ACTION_LABELS[offer.action.operation],
                "token": token,
            }
        line = (
            AUTHORED_SUPPLY_COMPLETE
            if self.completed and resident.occupation == "상인"
            else f"{resident.occupation}: “지금은 건넬 보급품이나 새 의뢰가 없어요.”"
        )
        return {"line": line, "terms": "", "label": "", "token": ""}

    def wire(self, *, local: bool) -> JsonObject:
        road = "blocked" if self.road_blocked else "restored" if self.completed else "open"
        return {
            "status": self.status if local else "마을에 도착하면 보급 의뢰를 확인할 수 있습니다.",
            "cargo": self.cargo,
            "cargo_required": REPAIR_CRATES,
            "gold": self.gold,
            "residents": tuple(npc.wire() for npc in self.residents) if local else (),
            "market": {"stock": self.stock, "capacity": STOCK_CAP, "road": road} if local else None,
        }


def village_supply(
    core: CoreSnapshot, scenario: SupplyScenario, social: SocialCatalog
) -> VillageSupply:
    place = scenario.place_id
    local = next(
        row.state
        for row in core.components
        if isinstance(row, SettlementRecord) and row.entity_id == place
    )
    city = next(
        row.state
        for row in core.components
        if isinstance(row, SupplyRecord) and row.entity_id == place
    )
    inventory = next(row.state for row in core.components if isinstance(row, InventoryRecord))
    opinion = next(row.state for row in core.components if isinstance(row, SocialRecord))
    residents: tuple[VillageResident, ...] = ()
    offers: tuple[SupplyOffer, ...] = ()
    if local is not None:
        residents = tuple(
            VillageResident(resident, x, y)
            for resident, (x, y) in zip(local.residents[:2], SUPPLY_RESIDENT_TILES, strict=True)
        )
        offers = supply_offers(local, city, inventory, scenario, core.tick)
        if reaction(opinion, social, place) <= HOSTILE_THRESHOLD:
            offers = tuple(offer for offer in offers if offer.action.operation != "accept")
    return VillageSupply(
        residents,
        next(iter(offers), None),
        supply_status(city, scenario, place, core.tick, authored=True),
        dict(inventory.items).get(supply_item(place), 0),
        inventory.gold,
        city.stage == 2,
        city.stock,
        blocked(scenario, place, city, core.tick),
    )
