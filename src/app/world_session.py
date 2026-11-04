"""World bootstrap and command construction over existing durable sessions."""

import hashlib
from pathlib import Path

from app.durable import DurableSession, create_durable, resume_durable
from app.headless import state_io
from app.world_registry import world_bundle
from app.world_time_registry import timed_world_bundle
from app.world_population_registry import population_world_bundle
from app.world_supply_registry import supply_world_bundle
from contracts.messages import CommandPayload
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


def world_checkpoint(
    world: WorldCatalog,
    *,
    timed: bool = False,
    living: bool = False,
    supply: SupplyScenario | None = None,
) -> DurableCheckpoint:
    bundle = (
        supply_world_bundle(world, supply)
        if supply is not None
        else population_world_bundle(world)
        if living or supply is not None
        else (timed_world_bundle(world) if timed else world_bundle(world))
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
    if living or supply is not None:
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
    if supply is not None:
        components = tuple(
            sorted(
                (*components, *(SupplyRecord(EntityId(p.id), SupplyState()) for p in world.places)),
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
) -> DurableSession:
    bundles = (
        supply_world_bundle(world, supply)
        if supply is not None
        else population_world_bundle(world)
        if living or supply is not None
        else (timed_world_bundle(world) if timed else world_bundle(world)),
    )
    if path.exists():
        return resume_durable(path, bundles=bundles)
    return create_durable(
        path, world_checkpoint(world, timed=timed, living=living, supply=supply), bundles=bundles
    )


def world_command(protocol: ProtocolSnapshot, payload: CommandPayload) -> GameCommand:
    cursor = next(s for s in protocol.streams if s.actor_id == WORLD_ACTOR and s.status == "active")
    sequence = cursor.highest_committed_sequence + 1
    identifier = CommandId(f"c1:{protocol.branch_id}:{cursor.stream_id}:{sequence}")
    return GameCommand(identifier, WORLD_ACTOR, protocol.revision, payload)


def foot_command(protocol: ProtocolSnapshot, destination: str, direction: int = 1) -> GameCommand:
    return world_command(protocol, Footstep(destination, direction))
