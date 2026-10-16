"""Explicit preparation from persisted evidence;never called by ordinary turns."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import sys
from typing import Sequence

from adapters.gemini_dialogue import GeminiDialogue
from adapters.generation_budget import GenerationBudget
from adapters.quest_dialogue import load_dialogue, publish_fresh
from app.npc_memory import read_memory
from app.npc_memory_brief import memory_brief as memory_brief
from app.npc_dialogue_plan import check_plan, plan_document, preview_memory
from app.npc_prepare import MAX_PREPARATION_BYTES, _generation_document, _target_available
from app.quest_definition import harbor_definition
from contracts.dialogue import DialogueGenerator, GenerationError, QuestContent
from contracts.npc_memory import NpcMemoryContext
from contracts.persistence import SaveError
from domain.canonical import JsonObject, canonical_json


def prepare_memory(
    working: Path,
    content: QuestContent,
    npc_id: str,
    output: Path,
    *,
    generator: DialogueGenerator | None = None,
    plan: Path | None = None,
) -> NpcMemoryContext:
    _target_available(output)
    context = (
        read_memory(working, content, npc_id)
        if plan is None
        else check_plan(working, content, npc_id, plan)
    )
    brief = memory_brief(context)
    generation = None if generator is None else _generation_document(generator.generate(brief))
    if read_memory(working, content, npc_id) != context:
        raise GenerationError("NPC_CONTEXT_STALE")
    if plan is not None and check_plan(working, content, npc_id, plan) != context:
        raise GenerationError("NPC_CONTEXT_STALE")
    document: JsonObject = {
        "format": "reverie-npc-memory-preparation/v1",
        "status": "CONTEXT_ONLY" if generation is None else "NEEDS_REVIEW",
        "context": context.document(),
        "context_sha256": context.sha256,
        "brief_sha256": hashlib.sha256(brief.text.encode()).hexdigest(),
        "generation": generation,
    }
    if plan is not None:
        preview = plan_document(context)
        document = {
            **document,
            "format": "reverie-npc-memory-preparation/v2",
            "plan_sha256": hashlib.sha256(canonical_json(preview)).hexdigest(),
            "request_sha256": preview["request_sha256"],
        }
    body = canonical_json(document)
    if len(body) > MAX_PREPARATION_BYTES:
        raise GenerationError("NPC_CONTEXT_CAPACITY")
    publish_fresh(output, body)
    return context


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare dialogue from persisted NPC quest evidence"
    )
    parser.add_argument("--working", type=Path, required=True)
    parser.add_argument("--quest-catalog", type=Path, required=True)
    parser.add_argument("--quest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--npc-id", default=harbor_definition().layout.npc_id)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--free-tier-confirmed", action="store_true")
    parser.add_argument("--free-data-use-confirmed", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.preview and (args.live or args.plan is not None):
            raise GenerationError("GENERATION_INPUT")
        content = load_dialogue(args.quest_catalog, args.quest_sha256, harbor_definition())
        _target_available(args.output)
        if args.preview:
            context = preview_memory(args.working, content, args.npc_id, args.output)
            print("DIALOGUE_PLAN_PREVIEW context_sha256=" + context.sha256)
            return 0
        if args.plan is None:
            read_memory(args.working, content, args.npc_id)
        else:
            check_plan(args.working, content, args.npc_id, args.plan)
        generator = (
            None
            if not args.live
            else GeminiDialogue(
                os.environ.get("GEMINI_API_KEY", ""),
                GenerationBudget(Path("tmp/gemini-profile")),
                free_tier_confirmed=args.free_tier_confirmed,
                free_data_use_confirmed=args.free_data_use_confirmed,
            )
        )
        context = prepare_memory(
            args.working, content, args.npc_id, args.output, generator=generator, plan=args.plan
        )
        print(
            ("CONTEXT_ONLY " if generator is None else "GENERATED_NEEDS_REVIEW ")
            + "context_sha256="
            + context.sha256
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
