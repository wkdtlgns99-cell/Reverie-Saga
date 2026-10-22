"""Source-bound memory differences for offline export and read-only slot previews."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Sequence

from adapters.quest_dialogue import load_dialogue, publish_fresh
from app.npc_memory import read_memory
from app.npc_memory_export import MAX_EXPORT_BYTES, query_document
from app.npc_memory_query import EvidenceQuery
from app.npc_prepare import _target_available
from app.quest_definition import harbor_definition
from contracts.dialogue import GenerationError, QuestContent
from contracts.npc_memory import NpcMemoryContext
from contracts.persistence import DurableCheckpoint, SaveError
from domain.canonical import JsonObject, canonical_json, object_value, seal
from domain.npc_memory import NpcQuestMemoryRecord, QuestEvidence
from domain.primitives import EntityId

MAX_COMPARISON_BYTES = 3 * MAX_EXPORT_BYTES


@dataclass(frozen=True, slots=True)
class MemoryDifference:
    added: tuple[QuestEvidence, ...]
    removed: tuple[QuestEvidence, ...]
    retained: tuple[QuestEvidence, ...]


def memory_difference(
    before: NpcQuestMemoryRecord, after: NpcQuestMemoryRecord
) -> MemoryDifference:
    if type(before) is not NpcQuestMemoryRecord or type(after) is not NpcQuestMemoryRecord:
        raise GenerationError("NPC_CONTEXT_INPUT")
    if before.entity_id != after.entity_id:
        raise GenerationError("NPC_MEMORY_COMPARISON_OWNER")
    # Record validation guarantees strictly ascending times;offline queries rank newest first.
    previous = {entry.memory_id(before.entity_id): entry for entry in reversed(before.entries)}
    current = {entry.memory_id(after.entity_id): entry for entry in reversed(after.entries)}
    if any(previous[key] != current[key] for key in previous.keys() & current.keys()):
        raise GenerationError("NPC_MEMORY_COMPARISON_IDENTITY")
    return MemoryDifference(
        tuple(value for key, value in current.items() if key not in previous),
        tuple(value for key, value in previous.items() if key not in current),
        tuple(value for key, value in previous.items() if key in current),
    )


def slot_memory_messages(
    saved: DurableCheckpoint, current: DurableCheckpoint, npc_id: EntityId
) -> tuple[str, ...]:
    if type(saved) is not DurableCheckpoint or type(current) is not DurableCheckpoint:
        raise GenerationError("NPC_CONTEXT_INPUT")
    if saved.core.world_id != current.core.world_id:
        raise GenerationError("NPC_MEMORY_COMPARISON_OWNER")
    memories = tuple(
        tuple(
            record
            for record in checkpoint.core.components
            if type(record) is NpcQuestMemoryRecord and record.entity_id == npc_id
        )
        for checkpoint in (saved, current)
    )
    if any(len(records) != 1 for records in memories):
        raise GenerationError("NPC_CONTEXT_INPUT")
    difference = memory_difference(memories[0][0], memories[1][0])
    facts = tuple(
        f"{label} · {entry.observed_at}초: "
        + (
            "의뢰를 맡겠다는 말을 직접 들었습니다."
            if entry.kind == "accepted"
            else "플레이어에게 완료 보고를 받았습니다. 처치를 직접 본 기억은 아닙니다."
        )
        for label, entries in (
            ("공통 기억", difference.retained),
            ("현재에만 있는 기억", difference.added),
            ("저장에만 있는 기억", difference.removed),
        )
        for entry in reversed(entries)
    )
    return (
        f"NPC 기억 비교 · 현재 {current.core.tick}초 / 선택 저장 {saved.core.tick}초",
        f"공통 {len(difference.retained)}개 · 현재에만 {len(difference.added)}개 · "
        f"저장에만 {len(difference.removed)}개",
        "저장 시점·진행 분기의 차이이며, NPC가 기억을 잊었다는 뜻은 아닙니다.",
        *(facts or ("양쪽 진행에 기록된 NPC 의뢰 대화 기억이 없습니다.",)),
    )


def comparison_document(before: NpcMemoryContext, after: NpcMemoryContext) -> JsonObject:
    if type(before) is not NpcMemoryContext or type(after) is not NpcMemoryContext:
        raise GenerationError("NPC_CONTEXT_INPUT")
    old, new = before.source, after.source
    if (old.world_id, old.catalog_sha256, old.npc_id, old.actor_id, old.quest_id) != (
        new.world_id,
        new.catalog_sha256,
        new.npc_id,
        new.actor_id,
        new.quest_id,
    ):
        raise GenerationError("NPC_MEMORY_COMPARISON_OWNER")
    query = EvidenceQuery()
    difference = memory_difference(
        NpcQuestMemoryRecord(EntityId(old.npc_id), before.entries),
        NpcQuestMemoryRecord(EntityId(new.npc_id), after.entries),
    )
    return object_value(
        seal(
            {
                "format": "reverie-npc-memory-comparison/v1",
                "status": "SNAPSHOT_COMPARISON",
                "before": query_document(before, query),
                "after": query_document(after, query),
                "added": tuple(entry.memory_id(new.npc_id) for entry in difference.added),
                "removed": tuple(entry.memory_id(old.npc_id) for entry in difference.removed),
                "retained": tuple(entry.memory_id(old.npc_id) for entry in difference.retained),
            }
        )
    )


def export_comparison(
    before: Path,
    after: Path,
    content: QuestContent,
    npc_id: str,
    output: Path,
) -> tuple[NpcMemoryContext, NpcMemoryContext]:
    _target_available(output)
    previous = read_memory(before, content, npc_id)
    current = read_memory(after, content, npc_id)
    body = canonical_json(comparison_document(previous, current))
    if len(body) > MAX_COMPARISON_BYTES:
        raise GenerationError("NPC_CONTEXT_CAPACITY")
    # Separate reads are point-in-time witnesses,not an atomic transaction across saves.
    if read_memory(before, content, npc_id) != previous:
        raise GenerationError("NPC_CONTEXT_STALE")
    if read_memory(after, content, npc_id) != current:
        raise GenerationError("NPC_CONTEXT_STALE")
    publish_fresh(output, body)
    return previous, current


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare two offline NPC memory snapshots")
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--quest-catalog", type=Path, required=True)
    parser.add_argument("--quest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--npc-id", default=harbor_definition().layout.npc_id)
    args = parser.parse_args(argv)
    try:
        _target_available(args.output)
        content = load_dialogue(args.quest_catalog, args.quest_sha256, harbor_definition())
        previous, current = export_comparison(
            args.before, args.after, content, args.npc_id, args.output
        )
        print(
            "MEMORY_COMPARISON_SNAPSHOT before_sha256="
            + previous.sha256
            + " after_sha256="
            + current.sha256
        )
    except (ValueError, OSError, UnicodeError, RecursionError, SaveError) as error:
        code = (
            error.code if isinstance(error, (GenerationError, SaveError)) else "NPC_CONTEXT_INPUT"
        )
        print(code, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
