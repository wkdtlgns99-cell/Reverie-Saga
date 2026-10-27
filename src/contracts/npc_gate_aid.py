"""Actual NPC passage support, separate from player gate interactions."""

from dataclasses import dataclass

from contracts.messages import FactPayload, PresentationPayload
from domain.primitives import EntityId, TypeKey


@dataclass(frozen=True, slots=True)
class GateAssisted(FactPayload):
    npc_id: EntityId
    target_id: EntityId
    SCHEMA = TypeKey("quest.gate-assisted", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class GateAidCue(PresentationPayload):
    npc_id: EntityId
    target_id: EntityId
    logical_tick: int
    SCHEMA = TypeKey("quest.gate-aid-cue", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA
