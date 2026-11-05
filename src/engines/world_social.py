"""Reputation from explicit actions and actual committed-world supply success."""

from dataclasses import dataclass

from contracts.errors import CandidateError
from contracts.turn import (
    CapabilityManifest,
    Dependency,
    EngineInvocation,
    EngineResult,
    NodeKey,
    PhaseAccess,
)
from contracts.world_social import SOCIAL, SOCIAL_FAMILY, SOCIAL_OWNER, SocialAction, SocialDelta
from contracts.world_supply import SUPPLY, SUPPLY_FAMILY, SUPPLY_OWNER
from contracts.world_travel import TRAVELER, TRAVEL_FAMILY
from domain.primitives import EntityId, Phase
from domain.world_social import SocialCatalog, credit_delivery, social_action
from domain.world_travel import WORLD_ACTOR


@dataclass(frozen=True, slots=True)
class WorldSocial:
    catalog: SocialCatalog

    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            SOCIAL_OWNER,
            (Phase.RESOLVE, Phase.POST_TICK),
            (
                PhaseAccess(Phase.RESOLVE, SOCIAL_FAMILY),
                PhaseAccess(Phase.RESOLVE, TRAVEL_FAMILY),
                PhaseAccess(Phase.POST_TICK, SOCIAL_FAMILY),
                PhaseAccess(Phase.POST_TICK, SUPPLY_FAMILY),
            ),
            (
                PhaseAccess(Phase.RESOLVE, SOCIAL_FAMILY),
                PhaseAccess(Phase.POST_TICK, SOCIAL_FAMILY),
            ),
            (Dependency(Phase.POST_TICK, NodeKey(Phase.POST_TICK, SUPPLY_OWNER)),),
            (),
            (),
            "local",
        )

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        before = invocation.state.component(SOCIAL, WORLD_ACTOR).state
        if invocation.phase == Phase.POST_TICK:
            after = before
            for faction in self.catalog.factions:
                if faction.place_id:
                    supply = invocation.state.component(SUPPLY, EntityId(faction.place_id)).state
                    if supply.stage == 2:
                        after = credit_delivery(after, self.catalog, faction.place_id)
        else:
            action = invocation.action
            if (
                action is None
                or type(action.payload) is not SocialAction
                or not isinstance(action.payload, SocialAction)
            ):
                raise CandidateError("INVALID_COMMAND", "social invocation")
            payload = action.payload
            travel = invocation.state.component(TRAVELER, WORLD_ACTOR).state
            after = social_action(
                before,
                self.catalog,
                travel.place_id,
                payload.operation,
                payload.ancestry_id,
                payload.country_id,
            )
        return EngineResult(
            () if before == after else (SocialDelta(WORLD_ACTOR, before, after),), (), ()
        )
