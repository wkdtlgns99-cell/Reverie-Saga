"""Offline differences between two independently source-bound NPC memory snapshots."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from adapters.quest_dialogue import load_dialogue, publish_fresh
from app.npc_memory import read_memory
from app.npc_memory_export import MAX_EXPORT_BYTES, query_document
from app.npc_memory_query import EvidenceQuery, select_evidence
from app.npc_prepare import _target_available
from app.quest_definition import harbor_definition
from contracts.dialogue import GenerationError, QuestContent
from contracts.npc_memory import NpcMemoryContext
from contracts.persistence import SaveError
from domain.canonical import JsonObject, canonical_json, object_value, seal

MAX_COMPARISON_BYTES = 3 * MAX_EXPORT_BYTES


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
    previous = {entry.memory_id(old.npc_id): entry for entry in select_evidence(before, query)}
    current = {entry.memory_id(new.npc_id): entry for entry in select_evidence(after, query)}
    if any(previous[key] != current[key] for key in previous.keys() & current.keys()):
        raise GenerationError("NPC_MEMORY_COMPARISON_IDENTITY")
    return object_value(
        seal(
            {
                "format": "reverie-npc-memory-comparison/v1",
                "status": "SNAPSHOT_COMPARISON",
                "before": query_document(before, query),
                "after": query_document(after, query),
                "added": tuple(key for key in current if key not in previous),
                "removed": tuple(key for key in previous if key not in current),
                "retained": tuple(key for key in previous if key in current),
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
