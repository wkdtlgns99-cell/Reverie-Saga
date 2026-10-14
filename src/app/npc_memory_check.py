"""Read-only point-in-time consistency check;no snapshot grants content approval."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence, cast

from adapters.quest_dialogue import load_dialogue
from app.npc_memory import read_memory
from app.npc_memory_export import MAX_EXPORT_BYTES, query_document
from app.npc_memory_query import EvidenceQuery
from app.quest_definition import harbor_definition
from contracts.dialogue import GenerationError, QuestContent, hex_digest
from contracts.npc_memory import NpcMemoryContext
from contracts.persistence import SaveError
from domain.canonical import (
    array_value,
    canonical_json,
    decode_json,
    exact_fields,
    int_value,
    object_value,
    text_value,
)
from domain.npc_memory import MEMORY_CAPACITY, EvidenceKind
from domain.primitives import require_integer


def check_snapshot(
    working: Path,
    content: QuestContent,
    npc_id: str,
    snapshot: Path,
) -> NpcMemoryContext:
    try:
        with snapshot.open("rb") as source:
            raw = source.read(MAX_EXPORT_BYTES + 1)
    except OSError:
        raise GenerationError("NPC_MEMORY_SNAPSHOT_UNAVAILABLE") from None
    try:
        if len(raw) > MAX_EXPORT_BYTES:
            raise ValueError("capacity")
        document = exact_fields(
            decode_json(raw),
            (
                "format",
                "status",
                "source",
                "context_sha256",
                "query",
                "count",
                "evidence",
            ),
        )
        if document["format"] != "reverie-npc-memory-query/v1" or document["status"] != "SNAPSHOT":
            raise ValueError("format/status")
        row = exact_fields(document["query"], ("subject_id", "kind", "since", "limit"))
        subject = None if row["subject_id"] is None else text_value(row["subject_id"])
        kind = None if row["kind"] is None else text_value(row["kind"])
        query = EvidenceQuery(
            subject,
            cast(EvidenceKind | None, kind),
            int_value(row["since"]),
            int_value(row["limit"]),
        )
        count = int_value(document["count"])
        require_integer(count, 0, MEMORY_CAPACITY)
        evidence = array_value(document["evidence"])
        if len(evidence) != count:
            raise ValueError("count")
        for value in evidence:
            object_value(value)
        object_value(document["source"])
        hex_digest(text_value(document["context_sha256"]))
    except (ValueError, UnicodeError, RecursionError):
        raise GenerationError("NPC_MEMORY_SNAPSHOT_INVALID") from None
    context = read_memory(working, content, npc_id)
    if document["context_sha256"] != context.sha256:
        raise GenerationError("NPC_CONTEXT_STALE")
    if canonical_json(document) != canonical_json(query_document(context, query)):
        raise GenerationError("NPC_MEMORY_SNAPSHOT_INVALID")
    if read_memory(working, content, npc_id) != context:
        raise GenerationError("NPC_CONTEXT_STALE")
    return context


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check an offline NPC memory query snapshot")
    parser.add_argument("--working", type=Path, required=True)
    parser.add_argument("--quest-catalog", type=Path, required=True)
    parser.add_argument("--quest-sha256", required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--npc-id", default=harbor_definition().layout.npc_id)
    args = parser.parse_args(argv)
    try:
        content = load_dialogue(args.quest_catalog, args.quest_sha256, harbor_definition())
        context = check_snapshot(args.working, content, args.npc_id, args.snapshot)
        print("MEMORY_QUERY_CURRENT context_sha256=" + context.sha256)
    except (ValueError, OSError, UnicodeError, RecursionError, SaveError) as error:
        code = (
            error.code
            if isinstance(error, (GenerationError, SaveError))
            else "NPC_MEMORY_SNAPSHOT_INVALID"
        )
        print(code, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
