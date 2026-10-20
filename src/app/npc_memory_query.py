"""Small pure T0 selector for the existing scoped conversation evidence."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable

from contracts.dialogue import GenerationError
from contracts.npc_memory import NpcMemoryContext
from domain.npc_memory import MEMORY_CAPACITY, EvidenceKind, NpcQuestMemoryRecord, QuestEvidence
from domain.primitives import require_integer, require_namespace


@dataclass(frozen=True, slots=True)
class EvidenceQuery:
    subject_id: str | None = None
    kind: EvidenceKind | None = None
    since: int = 0
    limit: int = MEMORY_CAPACITY

    def __post_init__(self) -> None:
        try:
            require_integer(self.since)
            require_integer(self.limit, 0, MEMORY_CAPACITY)
            if self.subject_id is not None:
                if type(self.subject_id) is not str or not self.subject_id.startswith(
                    ("actor:", "quest:")
                ):
                    raise ValueError("subject")
                require_namespace(self.subject_id)
            if self.kind is not None and (
                type(self.kind) is not str or self.kind not in ("accepted", "completion_reported")
            ):
                raise ValueError("kind")
        except ValueError:
            raise ValueError("NPC_MEMORY_QUERY") from None


def select_evidence(context: NpcMemoryContext, query: EvidenceQuery) -> tuple[QuestEvidence, ...]:
    if type(context) is not NpcMemoryContext or type(query) is not EvidenceQuery:
        raise GenerationError("NPC_CONTEXT_INPUT")
    if query.subject_id is not None and query.subject_id not in (
        context.source.actor_id,
        context.source.quest_id,
    ):
        return ()
    matches = (
        entry
        for entry in context.entries
        if entry.observed_at >= query.since and (query.kind is None or entry.kind == query.kind)
    )
    return _ranked(matches, context.source.npc_id)[: query.limit]


def recent_evidence(record: NpcQuestMemoryRecord) -> tuple[QuestEvidence, ...]:
    if type(record) is not NpcQuestMemoryRecord:
        raise GenerationError("NPC_CONTEXT_INPUT")
    return _ranked(record.entries, record.entity_id)[:1]


def player_memory_recollection(record: NpcQuestMemoryRecord) -> tuple[str, ...]:
    """Describe the latest heard statement;objective combat state is not an input."""
    entries = recent_evidence(record)
    if not entries:
        return ("NPC 플레이어 기억 · 아직 기록된 의뢰 약속이나 완료 보고가 없습니다.",)
    entry = entries[0]
    statement = (
        "의뢰를 맡겠다는 말을 직접 들었습니다. 아직 완료 보고는 받지 못했습니다."
        if entry.kind == "accepted"
        else "플레이어에게 완료 보고를 받았습니다. 처치를 직접 본 기억은 아닙니다."
    )
    return (f"NPC 플레이어 기억 · {entry.observed_at}초: {statement}",)


def _ranked(entries: Iterable[QuestEvidence], npc_id: str) -> tuple[QuestEvidence, ...]:
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                -entry.observed_at,
                entry.memory_id(npc_id),
            ),
        )
    )
