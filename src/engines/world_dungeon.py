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
from domain.world_combat import POMMEL, STAGGER, OpeningActor, perform_action, resolve_opening
from domain.world_dungeon import ENTRY, DungeonState, dungeon_step
from domain.world_dungeon_loadout import ORC_ENCOUNTER, SWITCH_USES_TURN
from domain.world_dungeon_loadout import DungeonOpponent, weapon_by_id, weapon_for_skill
from domain.world_travel import WORLD_ACTOR
from domain.world_village import DIRECTIONS
from domain.world_village_layout import DungeonBlueprint


@dataclass(frozen=True, slots=True)
class DungeonEngine:
    blueprint: DungeonBlueprint
    opponent: DungeonOpponent = ORC_ENCOUNTER

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
        return EngineResult((DungeonDelta(before, after),) if before != after else (), (), ())

    def _resolve(self, state: DungeonState, operation: str) -> DungeonState:
        if operation == "enter":
            return replace(state, tile=ENTRY, last_other_skill="")
        if operation == "exit":
            return replace(state, tile=None, last_other_skill="")
        tile = state.tile
        if tile is None:
            raise CandidateError("INVALID_COMMAND", "dungeon tile missing")
        if operation.startswith("equip:"):
            target = weapon_by_id(operation.removeprefix("equip:"))
            if target is None:
                raise CandidateError("INVALID_COMMAND", "dungeon weapon missing")
            if state.weapon_id == target.id:
                return state
            combat = state.combat
            if combat.order and SWITCH_USES_TURN:
                combat = perform_action(combat, "hold")
            return replace(state, weapon_id=target.id, combat=combat, last_other_skill="")
        if operation in DIRECTIONS:
            destination = dungeon_step(
                tile, operation, self.blueprint, orc_alive=state.combat.bandit_hp > 0
            )
            return replace(state, tile=destination)
        if operation == "engage":
            player = OpeningActor(WORLD_ACTOR, *tile, speed=3, readiness=1)
            enemy = OpeningActor(
                self.opponent.actor, self.blueprint.orc_x, self.blueprint.orc_y, self.opponent.speed
            )
            opening = resolve_opening((player, enemy), player, enemy, player_damage=state.weapon.damage)
            return replace(state, combat=opening)
        weapon = state.weapon
        if operation == weapon.skill_id:
            hit = perform_action(state.combat, "attack", player_damage=weapon.skill_damage)
            if operation == POMMEL:
                return replace(state, combat=replace(hit, last_action=POMMEL), pommel_used=True)
            return replace(
                state, combat=hit, last_other_skill=operation,
                other_skills_used=tuple(sorted((*state.other_skills_used, operation))),
            )
        previous = weapon_for_skill(state.last_skill)
        if operation == "advance" and previous is not None and previous.staggers:
            skipped = perform_action(state.combat, "hold")
            return replace(state, combat=replace(skipped, last_action=STAGGER), last_other_skill="")
        return replace(
            state,
            last_other_skill="",
            combat=perform_action(
                state.combat, "attack" if operation == "advance" else operation,
                player_damage=weapon.damage, opponent_damage=self.opponent.damage,
            ),
        )
