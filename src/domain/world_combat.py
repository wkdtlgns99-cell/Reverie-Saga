"""Opening order and independent actions for the first durable village skirmish."""

from dataclasses import dataclass, replace

from domain.primitives import EntityId, TypeKey, require_integer, require_namespace
from domain.state_types import ComponentRecord
from domain.world import LocalDetail
from domain.world_travel import WORLD_ACTOR
from domain.world_village import SUPPLY_RESIDENT_TILES, VILLAGE_ROWS, VillagePosition

COMBAT_SCHEMA = TypeKey("world.village-combat", 1)
BANDIT = EntityId("actor:mulbeodeul-bandit")
BANDIT_POSITION = VillagePosition(7, 7)
AMBUSH_TILE = VillagePosition(9, 7)
JOIN_RADIUS = 3
ATTACK_RANGE = 3
ACTION_SECONDS = 1
MAX_HP = 5
PLAYER_DAMAGE = 2
BANDIT_DAMAGE = 1


@dataclass(frozen=True, slots=True)
class OpeningActor:
    actor_id: EntityId
    x: int
    y: int
    speed: int
    readiness: int = 0
    advantage: int = 0
    alive: bool = True

    def near(self, other: "OpeningActor", radius: int) -> bool:
        return abs(self.x - other.x) + abs(self.y - other.y) <= radius


def opening_order(
    actors: tuple[OpeningActor, ...], attacker: OpeningActor, target: OpeningActor
) -> tuple[EntityId, ...]:
    eligible = (
        actor
        for actor in actors
        if actor.alive and (actor.near(attacker, JOIN_RADIUS) or actor.near(target, JOIN_RADIUS))
    )
    return tuple(
        actor.actor_id
        for actor in sorted(
            eligible,
            key=lambda actor: (-(actor.speed + actor.readiness + actor.advantage), actor.actor_id),
        )
    )


def can_attack(position: VillagePosition) -> bool:
    """The initial attack profile requires a clear row or column."""
    x, y = position.x, position.y
    bx, by = BANDIT_POSITION.x, BANDIT_POSITION.y
    if x == bx and 0 < abs(y - by) <= ATTACK_RANGE:
        return all(VILLAGE_ROWS[i][x] == "." for i in range(min(y, by), max(y, by)))
    if y == by and 0 < abs(x - bx) <= ATTACK_RANGE:
        return all(VILLAGE_ROWS[y][i] == "." for i in range(min(x, bx), max(x, bx)))
    return False


@dataclass(frozen=True, slots=True)
class CombatState:
    order: tuple[EntityId, ...] = ()
    player_hp: int = MAX_HP
    bandit_hp: int = MAX_HP
    last_actor: EntityId = EntityId("")
    last_action: str = ""

    def __post_init__(self) -> None:
        require_integer(self.player_hp, 0, MAX_HP)
        require_integer(self.bandit_hp, 0, MAX_HP)
        if (
            type(self.order) is not tuple
            or len(self.order) > 4
            or len(set(self.order)) != len(self.order)
        ):
            raise ValueError("COMBAT_ORDER")
        for actor in self.order:
            require_namespace(actor)
        if self.order and (
            WORLD_ACTOR not in self.order
            or BANDIT not in self.order
            or min(self.player_hp, self.bandit_hp) == 0
        ):
            raise ValueError("COMBAT_ACTIVE")
        if type(self.last_action) is not str or self.last_action not in (
            "",
            "open",
            "attack",
            "hold",
        ):
            raise ValueError("COMBAT_ACTION")
        if bool(self.last_actor) != bool(self.last_action):
            raise ValueError("COMBAT_LAST_ACTION")
        if self.last_actor:
            require_namespace(self.last_actor)
        if not self.order and not self.resolved and self.last_action:
            raise ValueError("COMBAT_PHASE")

    @property
    def resolved(self) -> bool:
        return min(self.player_hp, self.bandit_hp) == 0

    @property
    def current(self) -> EntityId:
        return self.order[0] if self.order else EntityId("")

    def ambush_due(self, position: VillagePosition) -> bool:
        return position == AMBUSH_TILE and not self.order and not self.resolved


@dataclass(frozen=True, slots=True)
class CombatRecord(ComponentRecord):
    entity_id: EntityId
    state: CombatState

    @property
    def schema(self) -> TypeKey:
        return COMBAT_SCHEMA


def resolve_ambush(position: VillagePosition, local: LocalDetail) -> CombatState:
    player = OpeningActor(WORLD_ACTOR, position.x, position.y, speed=3, readiness=1)
    bandit = OpeningActor(BANDIT, BANDIT_POSITION.x, BANDIT_POSITION.y, speed=3, advantage=2)
    residents = tuple(
        OpeningActor(EntityId(resident.id), x, y, speed=2)
        for resident, (x, y) in zip(local.residents[:2], SUPPLY_RESIDENT_TILES, strict=True)
    )
    order = opening_order((player, bandit, *residents), bandit, player)
    return CombatState(
        order,
        MAX_HP - BANDIT_DAMAGE,
        MAX_HP,
        BANDIT,
        "open",
    )


def perform_action(state: CombatState, operation: str) -> CombatState:
    actor = state.current
    player_hp = max(
        0, state.player_hp - BANDIT_DAMAGE * int(actor == BANDIT and operation == "attack")
    )
    bandit_hp = max(
        0, state.bandit_hp - PLAYER_DAMAGE * int(actor == WORLD_ACTOR and operation == "attack")
    )
    return replace(
        state,
        order=(*state.order[1:], actor) if player_hp and bandit_hp else (),
        player_hp=player_hp,
        bandit_hp=bandit_hp,
        last_actor=actor,
        last_action=operation,
    )
