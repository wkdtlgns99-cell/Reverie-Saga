"""One canonical own-knowledge context for generation and reply revalidation."""

from contracts.read_views import ReadPort
from contracts.world_conversation import CONVERSATION, ConversationContext
from contracts.world_population import INVENTORY, SETTLEMENT
from contracts.world_supply import SUPPLY
from contracts.world_travel import TRAVELER
from domain.primitives import EntityId
from domain.state_types import CoreSnapshot
from domain.world import LocalDetail, WorldCatalog
from domain.world_conversation import ConversationRecord, ConversationState, retrieve_memories
from domain.world_population import InventoryRecord, InventoryState, SettlementRecord
from domain.world_supply import (
    SupplyRecord,
    SupplyScenario,
    SupplyState,
    available_supply_operation,
    blocked,
    supply_activity,
)
from domain.world_travel import WORLD_ACTOR, TravelerRecord, TravelState


def build_context(
    world: WorldCatalog,
    scenario: SupplyScenario,
    conversation: ConversationState,
    travel: TravelState,
    local: LocalDetail | None,
    supply: SupplyState,
    inventory: InventoryState,
    tick: int,
) -> ConversationContext:
    if conversation.remaining:
        raise ValueError("DIALOGUE_SPEAKING")
    if not conversation.exchanges:
        raise ValueError("DIALOGUE_NO_UTTERANCE")
    current = conversation.exchanges[-1]
    if travel.destination_id or travel.place_id != current.place_id or local is None:
        raise ValueError("DIALOGUE_OUT_OF_REACH")
    index = next((i for i, r in enumerate(local.residents) if r.id == current.npc_id), None)
    if index is None:
        raise ValueError("DIALOGUE_WRONG_NPC")
    resident = local.residents[index]
    activity = supply_activity(resident, index, tick, scenario, local.place_id, supply)
    if activity.activity == "잠자는 중":
        raise ValueError("DIALOGUE_NPC_UNAVAILABLE")
    place = world.place(local.place_id)
    country = next(c for c in world.countries if c.id == place.country_id)
    continent = next(c for c in world.continents if c.id == country.continent_id)
    facts = [
        ("market_stock", str(supply.stock)),
        ("supply_route", "blocked" if blocked(scenario, local.place_id, supply, tick) else "open"),
    ]
    if index in (0, 1):
        facts.extend(
            (("warehouse", str(supply.warehouse)), ("assignment_stage", str(supply.stage)))
        )
    return ConversationContext(
        resident.id,
        resident.name,
        resident.occupation,
        resident.disposition,
        place.name,
        country.name,
        country.livelihood,
        continent.environment,
        tick,
        activity.activity,
        activity.site,
        tuple(facts),
        available_supply_operation(
            supply, inventory, scenario, local.place_id, tick, resident_index=index
        ),
        current,
        retrieve_memories(conversation, resident.id, current.player_text),
    )


def context_from_read(
    state: ReadPort, world: WorldCatalog, scenario: SupplyScenario, tick: int
) -> ConversationContext:
    travel = state.component(TRAVELER, WORLD_ACTOR).state
    entity = EntityId(travel.place_id)
    return build_context(
        world,
        scenario,
        state.component(CONVERSATION, WORLD_ACTOR).state,
        travel,
        state.component(SETTLEMENT, entity).state,
        state.component(SUPPLY, entity).state,
        state.component(INVENTORY, WORLD_ACTOR).state,
        tick,
    )


def context_from_core(
    core: CoreSnapshot, world: WorldCatalog, scenario: SupplyScenario
) -> ConversationContext:
    conversation = next(c.state for c in core.components if isinstance(c, ConversationRecord))
    travel = next(c.state for c in core.components if isinstance(c, TravelerRecord))
    local = next(
        c.state
        for c in core.components
        if isinstance(c, SettlementRecord) and c.entity_id == travel.place_id
    )
    supply = next(
        c.state
        for c in core.components
        if isinstance(c, SupplyRecord) and c.entity_id == travel.place_id
    )
    inventory = next(c.state for c in core.components if isinstance(c, InventoryRecord))
    return build_context(world, scenario, conversation, travel, local, supply, inventory, core.tick)
