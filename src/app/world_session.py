"""World bootstrap and command construction over existing durable sessions."""

import hashlib
from pathlib import Path

from app.durable import DurableSession, create_durable, resume_durable
from app.headless import state_io
from app.world_registry import world_bundle
from app.world_time_registry import timed_world_bundle
from app.world_population_registry import population_world_bundle
from app.world_supply_registry import supply_world_bundle
from app.world_conversation_registry import conversation_world_bundle
from app.world_social_registry import social_world_bundle
from app.world_transport_registry import transport_world_bundle
from contracts.messages import CommandPayload
from contracts.skeleton import FeatureBundle
from contracts.persistence import DurableCheckpoint
from contracts.turn import GameCommand, ProtocolSnapshot, StreamCursor
from contracts.world_travel import Footstep
from domain.canonical import pack
from domain.primitives import CommandId, Tick, WorldRevision, EntityId
from domain.state_types import ComponentRecord, CoreSnapshot
from domain.world import WorldCatalog, elaborate_place
from domain.world_population import InventoryRecord, InventoryState, SettlementRecord
from domain.world_travel import WORLD_ACTOR, TravelState, TravelerRecord
from domain.world_supply import SupplyRecord, SupplyScenario, SupplyState
from domain.world_conversation import ConversationRecord, ConversationState
from domain.world_social import SocialCatalog, SocialRecord, initial_social
from domain.world_transport import JourneyRecord, JourneyState, SupplyProgressRecord, TransportRules


def _bundle(
    world: WorldCatalog,
    *,
    timed: bool,
    living: bool,
    supply: SupplyScenario | None,
    conversation: bool,
    social: SocialCatalog | None = None,
    transport: TransportRules | None = None,
    knowledge: bool = False,
) -> FeatureBundle:
    if transport is not None:
        if social is None:
            raise ValueError("TRANSPORT_SOCIAL_REQUIRED")
        return transport_world_bundle(
            world, social, transport, supply or SupplyScenario(), knowledge=knowledge
        )
    if social is not None:
        return social_world_bundle(world, social, supply or SupplyScenario(), knowledge=knowledge)
    if conversation:
        return conversation_world_bundle(world, supply or SupplyScenario(), knowledge=knowledge)
    if knowledge:
        raise ValueError("WORLD_KNOWLEDGE_REQUIRES_CONVERSATION")
    if supply is not None:
        return supply_world_bundle(world, supply)
    if living:
        return population_world_bundle(world)
    return timed_world_bundle(world) if timed else world_bundle(world)


def world_checkpoint(
    world: WorldCatalog,
    *,
    timed: bool = False,
    living: bool = False,
    supply: SupplyScenario | None = None,
    conversation: bool = False,
    social: SocialCatalog | None = None,
    transport: TransportRules | None = None,
    knowledge: bool = False,
) -> DurableCheckpoint:
    if social is not None:
        conversation = True
    bundle = _bundle(
        world,
        timed=timed,
        living=living,
        supply=supply,
        conversation=conversation,
        social=social,
        transport=transport,
        knowledge=knowledge,
    )
    io = state_io((bundle,))
    identifier = (
        "w1-"
        + hashlib.sha256(
            pack(
                (
                    "world-id/v1",
                    world.seed_hex,
                    io.pins.rules_fingerprint,
                    io.pins.gameplay_catalog_hash,
                )
            )
        ).hexdigest()
    )
    first = world.places[0].id
    components: tuple[ComponentRecord, ...] = (
        TravelerRecord(WORLD_ACTOR, TravelState(first, "", 0, (first,))),
    )
    if living or supply is not None or conversation:
        components = tuple(
            sorted(
                (
                    *components,
                    InventoryRecord(WORLD_ACTOR, InventoryState(0, ())),
                    *(
                        SettlementRecord(
                            EntityId(p.id), elaborate_place(world, p.id) if p.id == first else None
                        )
                        for p in world.places
                    ),
                ),
                key=lambda c: (c.schema.kind, c.schema.version, c.entity_id),
            )
        )
    if supply is not None or conversation:
        components = tuple(
            sorted(
                (*components, *(SupplyRecord(EntityId(p.id), SupplyState()) for p in world.places)),
                key=lambda c: (c.schema.kind, c.schema.version, c.entity_id),
            )
        )
    if conversation:
        components = tuple(
            sorted(
                (*components, ConversationRecord(WORLD_ACTOR, ConversationState(), knowledge)),
                key=lambda c: (c.schema.kind, c.schema.version, c.entity_id),
            )
        )
    if social is not None:
        components = tuple(
            sorted(
                (*components, SocialRecord(WORLD_ACTOR, initial_social(social))),
                key=lambda c: (c.schema.kind, c.schema.version, c.entity_id),
            )
        )
    if transport is not None:
        components = tuple(
            sorted(
                (
                    *components,
                    JourneyRecord(WORLD_ACTOR, JourneyState()),
                    SupplyProgressRecord(WORLD_ACTOR, 0),
                ),
                key=lambda c: (c.schema.kind, c.schema.version, c.entity_id),
            )
        )
    core = CoreSnapshot(
        identifier,
        world.seed_hex,
        Tick(0),
        components,
        (),
        io.pins,
    )
    protocol = ProtocolSnapshot(
        "0" * 32, WorldRevision(0), (StreamCursor("1" * 32, WORLD_ACTOR, 0, "active"),), ()
    )
    io.validate_checkpoint(core, protocol)
    return DurableCheckpoint(core, protocol)


def open_world_session(
    path: Path,
    world: WorldCatalog,
    *,
    timed: bool = False,
    living: bool = False,
    supply: SupplyScenario | None = None,
    conversation: bool = False,
    social: SocialCatalog | None = None,
    transport: TransportRules | None = None,
    knowledge: bool = False,
) -> DurableSession:
    bundles = (
        _bundle(
            world,
            timed=timed,
            living=living,
            supply=supply,
            conversation=conversation,
            social=social,
            transport=transport,
            knowledge=knowledge,
        ),
    )
    if path.exists():
        return resume_durable(path, bundles=bundles)
    return create_durable(
        path,
        world_checkpoint(
            world,
            timed=timed,
            living=living,
            supply=supply,
            conversation=conversation,
            social=social,
            transport=transport,
            knowledge=knowledge,
        ),
        bundles=bundles,
    )


def world_command(protocol: ProtocolSnapshot, payload: CommandPayload) -> GameCommand:
    cursor = next(s for s in protocol.streams if s.actor_id == WORLD_ACTOR and s.status == "active")
    sequence = cursor.highest_committed_sequence + 1
    identifier = CommandId(f"c1:{protocol.branch_id}:{cursor.stream_id}:{sequence}")
    return GameCommand(identifier, WORLD_ACTOR, protocol.revision, payload)


def foot_command(protocol: ProtocolSnapshot, destination: str, direction: int = 1) -> GameCommand:
    return world_command(protocol, Footstep(destination, direction))
