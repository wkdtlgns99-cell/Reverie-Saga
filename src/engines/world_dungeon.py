"""Resolve one committed dungeon movement or combat action."""

from dataclasses import dataclass, replace

from contracts.errors import CandidateError
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from contracts.world_dungeon import (
    DUNGEON,
    DUNGEON_FAMILY,
    DUNGEON_OWNER,
    DungeonAction,
    DungeonDelta,
)
from domain.primitives import Phase
from domain.world_combat import OpeningActor, perform_action, resolve_opening
from domain.world_dungeon import ENTRY, ORC, DungeonState, dungeon_step
from domain.world_travel import WORLD_ACTOR
from domain.world_village import DIRECTIONS
from domain.world_village_layout import DungeonBlueprint


@dataclass(frozen=True, slots=True)
class DungeonEngine:
    blueprint: DungeonBlueprint

    @property
    def manifest(self) -> CapabilityManifest:
        access = (PhaseAccess(Phase.RESOLVE, DUNGEON_FAMILY),)
        return CapabilityManifest(
            DUNGEON_OWNER, (Phase.RESOLVE,), access, access, (), (), (), "local"
        )

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        action = invocation.action
        if (
            invocation.phase != Phase.RESOLVE
            or action is None
            or not isinstance(action.payload, DungeonAction)
        ):
            raise CandidateError("INVALID_COMMAND", "dungeon invocation")
        before = invocation.state.component(DUNGEON, WORLD_ACTOR).state
        if action.payload.operation == "wait":
            return EngineResult((), (), ())
        after = self._resolve(before, action.payload.operation)
        return EngineResult((DungeonDelta(before, after),), (), ())

    def _resolve(self, state: DungeonState, operation: str) -> DungeonState:
        if operation == "enter":
            return replace(state, tile=ENTRY)
        if operation == "exit":
            return replace(state, tile=None)
        tile = state.tile
        if tile is None:
            raise CandidateError("INVALID_COMMAND", "dungeon tile missing")
        if operation in DIRECTIONS:
            destination = dungeon_step(
                tile, operation, self.blueprint, orc_alive=state.combat.bandit_hp > 0
            )
            return replace(state, tile=destination)
        if operation == "engage":
            player = OpeningActor(WORLD_ACTOR, *tile, speed=3, readiness=1)
            orc = OpeningActor(ORC, self.blueprint.orc_x, self.blueprint.orc_y, speed=3)
            return replace(state, combat=resolve_opening((player, orc), player, orc))
        return replace(
            state,
            combat=perform_action(state.combat, "attack" if operation == "advance" else operation),
        )
