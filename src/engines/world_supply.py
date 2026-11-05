"""Same-owner confirmed supply exchange and ordered off-screen city simulation."""

from dataclasses import dataclass

from contracts.errors import CandidateError
from contracts.messages import EmittedFact, StateDelta
from contracts.turn import (
    CapabilityManifest,
    EngineInvocation,
    EngineResult,
    PhaseAccess,
)
from contracts.world_population import INVENTORY, INVENTORY_FAMILY, SETTLEMENT_FAMILY
from contracts.world_supply import (
    SUPPLY,
    SUPPLY_FAMILY,
    SUPPLY_OWNER,
    InventoryDelta,
    SupplyAction,
    SupplyActed,
    SupplyDelta,
)
from contracts.world_travel import TRAVEL_FAMILY
from contracts.world_transport import SUPPLY_PROGRESS, SUPPLY_PROGRESS_FAMILY, SupplyProgressDelta
from domain.primitives import EntityId, Phase
from domain.world import WorldCatalog
from domain.world_supply import (
    SupplyScenario,
    advance_supply,
    advance_supply_interval,
    supply_action,
)
from domain.world_travel import WORLD_ACTOR


@dataclass(frozen=True, slots=True)
class WorldSupply:
    world: WorldCatalog
    scenario: SupplyScenario
    catch_up: bool = False

    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            SUPPLY_OWNER,
            (Phase.RESOLVE, Phase.POST_TICK),
            tuple(
                PhaseAccess(Phase.RESOLVE, family)
                for family in (SUPPLY_FAMILY, INVENTORY_FAMILY, TRAVEL_FAMILY, SETTLEMENT_FAMILY)
            )
            + (PhaseAccess(Phase.POST_TICK, SUPPLY_FAMILY),)
            + ((PhaseAccess(Phase.POST_TICK, SUPPLY_PROGRESS_FAMILY),) if self.catch_up else ()),
            (
                PhaseAccess(Phase.RESOLVE, SUPPLY_FAMILY),
                PhaseAccess(Phase.RESOLVE, INVENTORY_FAMILY),
                PhaseAccess(Phase.POST_TICK, SUPPLY_FAMILY),
            )
            + ((PhaseAccess(Phase.POST_TICK, SUPPLY_PROGRESS_FAMILY),) if self.catch_up else ()),
            (),
            (SupplyActed.SCHEMA,),
            (),
            "local",
        )

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        changes: list[StateDelta] = []
        if invocation.phase == Phase.POST_TICK:
            start = (
                invocation.state.component(SUPPLY_PROGRESS, WORLD_ACTOR).state
                if self.catch_up
                else invocation.logical_tick - 1
            )
            for place in self.world.places:
                entity = EntityId(place.id)
                before = invocation.state.component(SUPPLY, entity).state
                after = (
                    advance_supply_interval(
                        before, self.scenario, place.id, start, invocation.logical_tick
                    )
                    if self.catch_up
                    else advance_supply(before, self.scenario, place.id, invocation.logical_tick)
                )
                if before != after:
                    changes.append(SupplyDelta(entity, before, after))
            if self.catch_up:
                changes.append(SupplyProgressDelta(WORLD_ACTOR, start, invocation.logical_tick))
            return EngineResult(tuple(changes), (), ())
        action = invocation.action
        if action is None or not isinstance(action.payload, SupplyAction):
            raise CandidateError("INVALID_COMMAND", "supply invocation")
        payload = action.payload
        entity = EntityId(payload.place_id)
        # Admission binds actor,local NPC and current reach before the turn starts.
        before = invocation.state.component(SUPPLY, entity).state
        inventory = invocation.state.component(INVENTORY, WORLD_ACTOR).state
        after, items = supply_action(
            before,
            inventory,
            self.scenario,
            payload.place_id,
            payload.operation,
            invocation.logical_tick,
        )
        if before != after:
            changes.append(SupplyDelta(entity, before, after))
        if inventory != items:
            changes.append(InventoryDelta(WORLD_ACTOR, inventory, items))
        return EngineResult(
            tuple(changes),
            (
                EmittedFact(
                    SupplyActed(
                        action.actor_id, payload.place_id, payload.npc_id, payload.operation
                    ),
                    invocation.logical_tick,
                    (),
                ),
            ),
            (),
        )
