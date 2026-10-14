"""Two monotonic evidence slots for one NPC's one-shot quest conversations."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Literal

from domain.canonical import pack
from domain.primitives import EntityId, TypeKey, require_integer, require_namespace
from domain.state_types import ComponentRecord

MEMORY_SCHEMA = TypeKey("quest.npc-memory", 1)
MEMORY_CAPACITY = 2
MEMORY_LEVEL = 1
MEMORY_PRIORITY = 128
type EvidenceKind = Literal["accepted", "completion_reported"]


@dataclass(frozen=True, slots=True)
class QuestEvidence:
    kind: EvidenceKind
    observed_at: int
    source_event_id: str

    def __post_init__(self) -> None:
        if type(self.kind) is not str or self.kind not in ("accepted", "completion_reported"):
            raise ValueError("NPC_MEMORY_KIND")
        require_integer(self.observed_at, 1)
        if (
            type(self.source_event_id) is not str
            or re.fullmatch(r"e1-[0-9a-f]{64}", self.source_event_id) is None
        ):
            raise ValueError("NPC_MEMORY_SOURCE")

    def memory_id(self, owner: str) -> str:
        require_namespace(owner)
        return (
            "m1-"
            + hashlib.sha256(
                pack(("npc-quest-memory/v1", owner, self.kind, self.source_event_id))
            ).hexdigest()
        )


@dataclass(frozen=True, slots=True)
class NpcQuestMemoryRecord(ComponentRecord):
    entity_id: EntityId
    entries: tuple[QuestEvidence, ...]

    @property
    def schema(self) -> TypeKey:
        return MEMORY_SCHEMA

    def __post_init__(self) -> None:
        if type(self.entity_id) is not str or not self.entity_id.startswith("actor:"):
            raise ValueError("NPC_MEMORY_OWNER")
        require_namespace(self.entity_id)
        if (
            type(self.entries) is not tuple
            or len(self.entries) > MEMORY_CAPACITY
            or any(type(entry) is not QuestEvidence for entry in self.entries)
        ):
            raise ValueError("NPC_MEMORY_ENTRIES")
        if (
            tuple(entry.kind for entry in self.entries)
            != ("accepted", "completion_reported")[: len(self.entries)]
        ):
            raise ValueError("NPC_MEMORY_ORDER")
        if len(self.entries) == 2 and (
            self.entries[0].observed_at >= self.entries[1].observed_at
            or self.entries[0].source_event_id == self.entries[1].source_event_id
        ):
            raise ValueError("NPC_MEMORY_ORDER")


def source_identity(world_id: str, tick: int) -> str:
    return (
        "e1-"
        + hashlib.sha256(
            pack(("event-id/v1", world_id, str(tick), "RESOLVE", "0", "quest.rules", "0"))
        ).hexdigest()
    )


def append_evidence(before: NpcQuestMemoryRecord, entry: QuestEvidence) -> NpcQuestMemoryRecord:
    if type(before) is not NpcQuestMemoryRecord or type(entry) is not QuestEvidence:
        raise ValueError("NPC_MEMORY_INPUT")
    return NpcQuestMemoryRecord(before.entity_id, (*before.entries, entry))
