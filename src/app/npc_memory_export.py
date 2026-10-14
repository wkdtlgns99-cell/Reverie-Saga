"""Developer-only offline export of a source-bound memory query snapshot."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
import sys
from typing import Sequence, cast

from adapters.quest_dialogue import load_dialogue, publish_fresh
from app.npc_memory import read_memory
from app.npc_memory_query import EvidenceQuery, select_evidence
from app.npc_prepare import _target_available
from app.quest_definition import harbor_definition
from contracts.dialogue import GenerationError, QuestContent
from contracts.npc_memory import NpcMemoryContext
from contracts.persistence import SaveError
from domain.canonical import JsonObject, array_value, canonical_json, object_value, seal, text_value
from domain.npc_memory import MEMORY_CAPACITY, EvidenceKind

MAX_EXPORT_BYTES = 8192


def query_document(context: NpcMemoryContext, query: EvidenceQuery) -> JsonObject:
    selected = select_evidence(context, query)
    documents = {
        text_value(object_value(value)["memory_id"]): value
        for value in array_value(context.document()["evidence"])
    }
    return object_value(
        seal(
            {
                "format": "reverie-npc-memory-query/v1",
                "status": "SNAPSHOT",
                "source": context.source.document(),
                "context_sha256": context.sha256,
                "query": asdict(query),
                "count": len(selected),
                "evidence": tuple(
                    documents[entry.memory_id(context.source.npc_id)] for entry in selected
                ),
            }
        )
    )


def export_memory(
    working: Path,
    content: QuestContent,
    npc_id: str,
    query: EvidenceQuery,
    output: Path,
) -> NpcMemoryContext:
    if type(query) is not EvidenceQuery:
        raise GenerationError("NPC_CONTEXT_INPUT")
    _target_available(output)
    context = read_memory(working, content, npc_id)
    body = canonical_json(query_document(context, query))
    if len(body) > MAX_EXPORT_BYTES:
        raise GenerationError("NPC_CONTEXT_CAPACITY")
    if read_memory(working, content, npc_id) != context:
        raise GenerationError("NPC_CONTEXT_STALE")
    publish_fresh(output, body)
    return context


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export an offline NPC memory query snapshot")
    parser.add_argument("--working", type=Path, required=True)
    parser.add_argument("--quest-catalog", type=Path, required=True)
    parser.add_argument("--quest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--npc-id", default=harbor_definition().layout.npc_id)
    parser.add_argument("--subject-id")
    parser.add_argument("--kind", choices=("accepted", "completion_reported"))
    parser.add_argument("--since", type=int, default=0)
    parser.add_argument("--limit", type=int, default=MEMORY_CAPACITY)
    args = parser.parse_args(argv)
    try:
        query = EvidenceQuery(
            args.subject_id, cast(EvidenceKind | None, args.kind), args.since, args.limit
        )
        _target_available(args.output)
        content = load_dialogue(args.quest_catalog, args.quest_sha256, harbor_definition())
        context = export_memory(args.working, content, args.npc_id, query, args.output)
        print("MEMORY_QUERY_SNAPSHOT context_sha256=" + context.sha256)
    except (ValueError, OSError, UnicodeError, RecursionError, SaveError) as error:
        code = (
            error.code
            if isinstance(error, (GenerationError, SaveError))
            else ("NPC_MEMORY_QUERY" if str(error) == "NPC_MEMORY_QUERY" else "NPC_CONTEXT_INPUT")
        )
        print(code, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
