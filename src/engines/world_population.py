"""Commit local detail when the player actually arrives,not when inspecting a map."""

from dataclasses import dataclass

from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from contracts.world_population import MATERIALIZER, SETTLEMENT, SETTLEMENT_FAMILY, SettlementDelta
from contracts.world_travel import TRAVELER, TRAVEL_FAMILY
from domain.primitives import EntityId, Phase
from domain.world import WorldCatalog, elaborate_place
from domain.world_travel import WORLD_ACTOR


@dataclass(frozen=True, slots=True)
class LocalMaterializer:
    world: WorldCatalog

    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            MATERIALIZER,
            (Phase.POST_TICK,),
            (
                PhaseAccess(Phase.POST_TICK, TRAVEL_FAMILY),
                PhaseAccess(Phase.POST_TICK, SETTLEMENT_FAMILY),
            ),
            (PhaseAccess(Phase.POST_TICK, SETTLEMENT_FAMILY),),
            (),
            (),
            (),
            "local",
        )

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        traveler = invocation.state.component(TRAVELER, WORLD_ACTOR).state
        place_id = EntityId(traveler.place_id)
        before = invocation.state.component(SETTLEMENT, place_id).state
        if traveler.destination_id or before is not None:
            return EngineResult((), (), ())
        after = elaborate_place(self.world, place_id)
        return EngineResult((SettlementDelta(place_id, before, after),), (), ())
