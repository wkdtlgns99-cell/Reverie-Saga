"""Small pure T0 selector for the existing scoped conversation evidence."""

from __future__ import annotations

from dataclasses import dataclass

from contracts.dialogue import GenerationError
from contracts.npc_memory import NpcMemoryContext
from domain.npc_memory import MEMORY_CAPACITY, EvidenceKind, QuestEvidence
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
    return tuple(
        sorted(
            matches,
            key=lambda entry: (
                -entry.observed_at,
                entry.memory_id(context.source.npc_id),
            ),
        )
    )[: query.limit]
