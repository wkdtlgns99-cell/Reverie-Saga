"""One canonical own-knowledge context for generation and reply revalidation."""

from contracts.read_views import ReadPort
from contracts.world_conversation import CONVERSATION, ConversationContext
from contracts.world_population import INVENTORY, SETTLEMENT
from contracts.world_supply import SUPPLY
from contracts.world_travel import TRAVELER
from contracts.world_social import SOCIAL
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
from domain.world_transport import JourneyRecord
from domain.world_social import (
    HOSTILE_THRESHOLD,
    SocialCatalog,
    SocialRecord,
    SocialState,
    reaction,
)


def build_context(
    world: WorldCatalog,
    scenario: SupplyScenario,
    conversation: ConversationState,
    travel: TravelState,
    local: LocalDetail | None,
    supply: SupplyState,
    inventory: InventoryState,
    tick: int,
    *,
    social: SocialCatalog | None = None,
    social_state: SocialState | None = None,
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
    available = available_supply_operation(
        supply, inventory, scenario, local.place_id, tick, resident_index=index
    )
    if social is not None:
        if social_state is None:
            raise ValueError("SOCIAL_CONTEXT_MISSING")
        identity = next(r for r in social.residents if r.npc_id == resident.id)
        ancestry = next(a for a in social.ancestries if a.id == identity.ancestry_id)
        city_score = reaction(social_state, social, place.id)
        local_merit = dict(social_state.reputation)[social.local(place.id).id]
        standing = (
            "적대"
            if city_score <= HOSTILE_THRESHOLD
            else "우호"
            if city_score >= 20
            else "불편"
            if city_score < 0
            else "중립"
        )
        facts.extend(
            (
                ("npc_ancestry", ancestry.name),
                ("npc_culture", ancestry.culture),
                ("npc_organization", social.local(place.id).name),
                (
                    "organization_public_standing",
                    f"소속 조직이 공개한 현재 관계: {standing}. 해당 조직에 대한 실제 행동 평판은 {local_merit:+d}. 개인적 사건의 세부 사정이나 다른 주민의 사적인 대화는 포함하지 않는다.",
                ),
                (
                    "current_city_policy",
                    "적대 관계로 새 의뢰와 도시 입장을 제한 중. 기존 운송품은 수령·전달 가능하며 화해 요청은 가능하다."
                    if city_score <= HOSTILE_THRESHOLD
                    else "현재 관계로 인한 새 의뢰·입장 제한은 없다.",
                ),
                (
                    "player_ancestry",
                    next(
                        (a.name for a in social.ancestries if a.id == social_state.ancestry_id),
                        "미선택",
                    ),
                ),
                (
                    "player_citizenship",
                    next(
                        (c.name for c in world.countries if c.id == social_state.country_id),
                        "국적 없음" if social_state.country_id == "none" else "미선택",
                    ),
                ),
                (
                    "earned_local_reputation",
                    str(dict(social_state.reputation)[social.local(place.id).id]),
                ),
                (
                    "earned_national_reputation",
                    str(dict(social_state.reputation)[social.national(country.id).id]),
                ),
                ("social_reaction", str(reaction(social_state, social, place.id, resident.id))),
                (
                    "national_diplomacy",
                    " / ".join(
                        f"{c.name}:{social.diplomatic_score(country.id, c.id)}"
                        for c in world.countries
                    ),
                ),
                (
                    "social_basis",
                    "종족·소속은 인격이나 도덕성을 결정하지 않으며 평판은 실제 행동 기록이다.",
                ),
            )
        )
        if available == "accept" and city_score <= HOSTILE_THRESHOLD:
            available = "none"
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
        available,
        current,
        retrieve_memories(conversation, resident.id, current.player_text),
    )


def context_from_read(
    state: ReadPort,
    world: WorldCatalog,
    scenario: SupplyScenario,
    tick: int,
    *,
    social: SocialCatalog | None = None,
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
        social=social,
        social_state=state.component(SOCIAL, WORLD_ACTOR).state if social is not None else None,
    )


def context_from_core(
    core: CoreSnapshot,
    world: WorldCatalog,
    scenario: SupplyScenario,
    *,
    social: SocialCatalog | None = None,
) -> ConversationContext:
    if any(isinstance(c, JourneyRecord) and c.state.phase != "idle" for c in core.components):
        raise ValueError("DIALOGUE_OUT_OF_REACH")
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
    social_state = next((c.state for c in core.components if isinstance(c, SocialRecord)), None)
    return build_context(
        world,
        scenario,
        conversation,
        travel,
        local,
        supply,
        inventory,
        core.tick,
        social=social,
        social_state=social_state,
    )
