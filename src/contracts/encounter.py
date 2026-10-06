from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from contracts.messages import CommandPayload, FactPayload, PresentationPayload, StateDelta
from contracts.read_views import ComponentKey, ComponentPatch
from domain.primitives import EntityId, FieldAddress, FieldFamily, TypeKey


class GateRead(Protocol):
    @property
    def space_id(self) -> EntityId: ...
    @property
    def cell(self) -> int: ...
    @property
    def is_open(self) -> int: ...


class HitPointsRead(Protocol):
    @property
    def hp(self) -> int: ...


class StaminaRead(Protocol):
    @property
    def value(self) -> int: ...


GATE = ComponentKey[GateRead](TypeKey("encounter.gate", 1))
HIT_POINTS = ComponentKey[HitPointsRead](TypeKey("encounter.hp", 1))
STAMINA = ComponentKey[StaminaRead](TypeKey("encounter.stamina", 1))


@dataclass(frozen=True, slots=True)
class InteractCommand(CommandPayload):
    target_id: EntityId
    option: Literal["open", "close"]

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.interact", 1)


@dataclass(frozen=True, slots=True)
class AttackCommand(CommandPayload):
    target_id: EntityId
    profile_id: str

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.attack", 1)


@dataclass(frozen=True, slots=True)
class RestCommand(CommandPayload):

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.rest", 1)


@dataclass(frozen=True, slots=True)
class GateDelta(StateDelta):
    entity_id: EntityId
    before_open: int
    after_open: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.gate-delta", 1)

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(FieldFamily("encounter.gate", "is_open"), self.entity_id)


@dataclass(frozen=True, slots=True)
class HitPointsDelta(StateDelta):
    entity_id: EntityId
    before_hp: int
    after_hp: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.hp-delta", 1)

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(FieldFamily("encounter.hp", "hp"), self.entity_id)


@dataclass(frozen=True, slots=True)
class StaminaDelta(StateDelta):
    entity_id: EntityId
    before_stamina: int
    after_stamina: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.stamina-delta", 1)

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(FieldFamily("encounter.stamina", "value"), self.entity_id)


@dataclass(frozen=True, slots=True)
class GatePatch(ComponentPatch):
    is_open: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.gate-patch", 1)


@dataclass(frozen=True, slots=True)
class HitPointsPatch(ComponentPatch):
    hp: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.hp-patch", 1)


@dataclass(frozen=True, slots=True)
class StaminaPatch(ComponentPatch):
    value: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.stamina-patch", 1)


@dataclass(frozen=True, slots=True)
class EncounterMoved(FactPayload):
    actor_id: EntityId
    space_id: EntityId
    from_cell: int
    to_cell: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.moved", 1)


@dataclass(frozen=True, slots=True)
class EncounterMoveBlocked(FactPayload):
    actor_id: EntityId
    space_id: EntityId
    from_cell: int
    dx: int
    dz: int
    reason: Literal["boundary", "wall", "door", "occupied"]

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.move-blocked", 1)


@dataclass(frozen=True, slots=True)
class GateChanged(FactPayload):
    actor_id: EntityId
    target_id: EntityId
    before_open: int
    after_open: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.gate-changed", 1)


@dataclass(frozen=True, slots=True)
class AttackResolved(FactPayload):
    actor_id: EntityId
    target_id: EntityId
    profile_id: str
    actor_hp_before: int
    actor_hp_after: int
    target_hp_before: int
    target_hp_after: int
    stamina_before: int
    stamina_after: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.attack-resolved", 1)


@dataclass(frozen=True, slots=True)
class Rested(FactPayload):
    actor_id: EntityId
    before_stamina: int
    after_stamina: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.rested", 1)


@dataclass(frozen=True, slots=True)
class Defeated(FactPayload):
    entity_id: EntityId
    killer_id: EntityId

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.defeated", 1)


@dataclass(frozen=True, slots=True)
class EncounterMoveCue(PresentationPayload):
    actor_id: EntityId
    space_id: EntityId
    from_cell: int
    to_cell: int
    from_x_mm: int
    from_z_mm: int
    to_x_mm: int
    to_z_mm: int
    result: Literal["moved", "boundary", "wall", "door", "occupied"]

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.move-cue", 1)


@dataclass(frozen=True, slots=True)
class GateCue(PresentationPayload):
    actor_id: EntityId
    target_id: EntityId
    cell: int
    x_mm: int
    z_mm: int
    before_open: int
    after_open: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.gate-cue", 1)


@dataclass(frozen=True, slots=True)
class AttackCue(PresentationPayload):
    actor_id: EntityId
    target_id: EntityId
    actor_cell: int
    target_cell: int
    actor_hp_before: int
    actor_hp_after: int
    target_hp_before: int
    target_hp_after: int
    stamina_before: int
    stamina_after: int
    result: Literal["hit", "actor_defeated", "target_defeated"]

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.attack-cue", 1)


@dataclass(frozen=True, slots=True)
class RestCue(PresentationPayload):
    actor_id: EntityId
    before_stamina: int
    after_stamina: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.rest-cue", 1)


@dataclass(frozen=True, slots=True)
class DefeatCue(PresentationPayload):
    entity_id: EntityId
    killer_id: EntityId
    cell: int
    x_mm: int
    z_mm: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("encounter.defeat-cue", 1)
