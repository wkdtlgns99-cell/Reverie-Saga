"""Observed reads and typed atomic updates for bounded quest evidence."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Protocol

from contracts.messages import StateDelta
from contracts.npc_context import NpcQuestContext
from contracts.read_views import ComponentKey, ComponentPatch
from domain.npc_memory import (
    MEMORY_SCHEMA,
    MEMORY_LEVEL,
    MEMORY_PRIORITY,
    NpcQuestMemoryRecord,
    QuestEvidence,
    source_identity,
)
from domain.canonical import JsonObject, canonical_json, object_value, seal
from domain.primitives import EntityId, FieldAddress, FieldFamily, TypeKey

MEMORY_FAMILY = FieldFamily(MEMORY_SCHEMA.kind, "entries")


class NpcMemoryRead(Protocol):
    @property
    def accepted_at(self) -> int: ...
    @property
    def acceptance_source(self) -> str: ...
    @property
    def reported_at(self) -> int: ...
    @property
    def report_source(self) -> str: ...


MEMORY = ComponentKey[NpcMemoryRead](MEMORY_SCHEMA)


def read_record(owner: EntityId, view: NpcMemoryRead) -> NpcQuestMemoryRecord:
    accepted, source, reported, report = (
        view.accepted_at,
        view.acceptance_source,
        view.reported_at,
        view.report_source,
    )
    entries: tuple[QuestEvidence, ...] = ()
    if source:
        entries += (QuestEvidence("accepted", accepted, source),)
    if report:
        entries += (QuestEvidence("completion_reported", reported, report),)
    if (not source and accepted != 0) or (not report and reported != 0):
        raise ValueError("NPC_MEMORY_EMPTY")
    return NpcQuestMemoryRecord(owner, entries)


@dataclass(frozen=True, slots=True)
class MemoryDelta(StateDelta):
    before: NpcQuestMemoryRecord
    after: NpcQuestMemoryRecord
    SCHEMA = TypeKey("quest.npc-memory-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(MEMORY_FAMILY, self.before.entity_id)


@dataclass(frozen=True, slots=True)
class MemoryPatch(ComponentPatch):
    value: NpcQuestMemoryRecord
    SCHEMA = TypeKey("quest.npc-memory-patch", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class NpcMemoryContext:
    source: NpcQuestContext
    entries: tuple[QuestEvidence, ...]

    def __post_init__(self) -> None:
        if type(self.source) is not NpcQuestContext:
            raise ValueError("NPC_CONTEXT_INPUT")
        record = NpcQuestMemoryRecord(EntityId(self.source.npc_id), self.entries)
        expected = (
            0
            if self.source.known_phase == "available"
            else 2
            if self.source.known_phase == "reported"
            else 1
        )
        if len(record.entries) != expected or any(
            entry.observed_at > self.source.tick
            or entry.source_event_id != source_identity(self.source.world_id, entry.observed_at)
            for entry in self.entries
        ):
            raise ValueError("NPC_MEMORY_CONTEXT")

    def document(self) -> JsonObject:
        result = object_value(
            seal(
                {
                    "format": "reverie-npc-evidence-context/v1",
                    "source": self.source.document(),
                    "evidence": tuple(
                        {
                            "memory_id": entry.memory_id(self.source.npc_id),
                            "kind": entry.kind,
                            "observed_at": entry.observed_at,
                            "source_event_id": entry.source_event_id,
                            "owner_id": self.source.npc_id,
                            "subjects": (self.source.actor_id, self.source.quest_id),
                            "level": MEMORY_LEVEL,
                            "priority": MEMORY_PRIORITY,
                            "protected": False,
                            "certainty": "observed" if entry.kind == "accepted" else "reported",
                        }
                        for entry in self.entries
                    ),
                }
            )
        )
        if len(canonical_json(result)) > 4096:
            raise ValueError("NPC_CONTEXT_CAPACITY")
        return result

    @property
    def sha256(self) -> str:
        return hashlib.sha256(canonical_json(self.document())).hexdigest()
