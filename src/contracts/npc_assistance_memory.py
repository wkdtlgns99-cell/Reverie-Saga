"""Typed access and transactional changes for one NPC's own assistance memory."""

from dataclasses import dataclass
from typing import Protocol

from contracts.messages import StateDelta
from contracts.read_views import ComponentKey, ComponentPatch
from domain.npc_assistance_memory import ASSISTANCE_SCHEMA, AssistanceMemory
from domain.primitives import EntityId, FieldAddress, FieldFamily, TypeKey

ASSISTANCE_OWNER = "encounter.actions"
ASSISTANCE_FAMILY = FieldFamily(ASSISTANCE_SCHEMA.kind, "memory")


class AssistanceMemoryRead(Protocol):
    @property
    def state(self) -> AssistanceMemory: ...


ASSISTANCE_MEMORY = ComponentKey[AssistanceMemoryRead](ASSISTANCE_SCHEMA)


@dataclass(frozen=True, slots=True)
class AssistanceMemoryDelta(StateDelta):
    entity_id: EntityId
    before: AssistanceMemory
    after: AssistanceMemory
    SCHEMA = TypeKey("quest.assistance-memory-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(ASSISTANCE_FAMILY, self.entity_id)


@dataclass(frozen=True, slots=True)
class AssistanceMemoryPatch(ComponentPatch):
    state: AssistanceMemory
    SCHEMA = TypeKey("quest.assistance-memory-patch", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


ASSISTANCE_PAYLOADS = (AssistanceMemoryDelta, AssistanceMemoryPatch)
