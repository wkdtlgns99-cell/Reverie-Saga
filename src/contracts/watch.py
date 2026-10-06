from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from contracts.messages import CommandPayload, FactPayload, PresentationPayload, StateDelta
from contracts.read_views import ComponentKey, ComponentPatch
from domain.primitives import EntityId, FieldAddress, FieldFamily, Tick, TypeKey


class WatchNpcRead(Protocol):
    @property
    def space_id(self) -> EntityId: ...
    @property
    def cell(self) -> int: ...
    @property
    def bells(self) -> int: ...


class LanternRead(Protocol):
    @property
    def charge(self) -> int: ...


class ReplyRead(Protocol):
    @property
    def count(self) -> int: ...


WATCH_NPC = ComponentKey[WatchNpcRead](TypeKey("watch.npc", 1))
LANTERN = ComponentKey[LanternRead](TypeKey("watch.lantern", 1))
REPLY = ComponentKey[ReplyRead](TypeKey("watch.reply", 1))


@dataclass(frozen=True, slots=True)
class WaitCommand(CommandPayload):
    seconds: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.wait", 1)


@dataclass(frozen=True, slots=True)
class BellCommand(CommandPayload):
    npc_id: EntityId

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.bell", 1)


@dataclass(frozen=True, slots=True)
class WatchWake(FactPayload):
    npc_id: EntityId

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.wake", 1)


@dataclass(frozen=True, slots=True)
class WatchRequested(FactPayload):
    actor_id: EntityId
    npc_id: EntityId

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.requested", 1)


@dataclass(frozen=True, slots=True)
class WatchEcho(FactPayload):
    npc_id: EntityId
    remaining: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.echo", 1)


@dataclass(frozen=True, slots=True)
class NpcActed(FactPayload):
    npc_id: EntityId
    before_bells: int
    after_bells: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.npc-acted", 1)


@dataclass(frozen=True, slots=True)
class BellRung(FactPayload):
    actor_id: EntityId
    npc_id: EntityId

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.bell-rung", 1)


@dataclass(frozen=True, slots=True)
class WatchReplied(FactPayload):
    npc_id: EntityId
    before_count: int
    after_count: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.replied", 1)


@dataclass(frozen=True, slots=True)
class NpcCue(PresentationPayload):
    npc_id: EntityId
    logical_tick: Tick
    before_bells: int
    after_bells: int
    cell: int
    x_mm: int
    z_mm: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.npc-cue", 1)


@dataclass(frozen=True, slots=True)
class BellCue(PresentationPayload):
    actor_id: EntityId
    npc_id: EntityId
    logical_tick: Tick

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.bell-cue", 1)


@dataclass(frozen=True, slots=True)
class ReplyCue(PresentationPayload):
    npc_id: EntityId
    logical_tick: Tick
    before_count: int
    after_count: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.reply-cue", 1)


@dataclass(frozen=True, slots=True)
class ChargeDelta(StateDelta):
    entity_id: EntityId
    before_charge: int
    after_charge: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.charge-delta", 1)

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(FieldFamily("watch.lantern", "charge"), self.entity_id)


@dataclass(frozen=True, slots=True)
class ChargePatch(ComponentPatch):
    charge: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.charge-patch", 1)


@dataclass(frozen=True, slots=True)
class BellsDelta(StateDelta):
    entity_id: EntityId
    before_bells: int
    after_bells: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.bells-delta", 1)

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(FieldFamily("watch.npc", "bells"), self.entity_id)


@dataclass(frozen=True, slots=True)
class BellsPatch(ComponentPatch):
    bells: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.bells-patch", 1)


@dataclass(frozen=True, slots=True)
class ReplyDelta(StateDelta):
    entity_id: EntityId
    before_count: int
    after_count: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.reply-delta", 1)

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(FieldFamily("watch.reply", "count"), self.entity_id)


@dataclass(frozen=True, slots=True)
class ReplyPatch(ComponentPatch):
    count: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("watch.reply-patch", 1)
