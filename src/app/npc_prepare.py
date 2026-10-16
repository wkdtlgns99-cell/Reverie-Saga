"""Read-only checkpoint context and explicit bounded dialogue preparation."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import os
from pathlib import Path
import re
import sys
from typing import Sequence

from adapters.gemini_dialogue import GeminiDialogue
from adapters.generation_budget import GenerationBudget
from adapters.quest_dialogue import decode_candidate, load_dialogue, publish_fresh
from adapters.sqlite_store import validate_save
from app.dialogue_prepare import harbor_brief
from app.headless import state_io
from app.quest_definition import harbor_definition
from app.quest_registry import quest_bundle
from contracts.dialogue import (
    DialogueBrief,
    DialogueGenerator,
    GeneratedDialogue,
    GenerationError,
    QuestContent,
)
from contracts.npc_context import KnownQuestPhase, NpcQuestContext
from contracts.persistence import SaveError
from domain.canonical import JsonObject, canonical_json, object_value, seal
from domain.primitives import require_integer
from domain.quest import QuestRecord

MAX_PREPARATION_BYTES = 32768


def read_context(working: Path, content: QuestContent, npc_id: str) -> NpcQuestContext:
    if type(content) is not QuestContent or content.definition != harbor_definition():
        raise GenerationError("NPC_CONTEXT_CONTENT")
    definition = content.definition
    if type(npc_id) is not str or npc_id != definition.layout.npc_id:
        raise GenerationError("NPC_CONTEXT_OWNER")
    io = state_io((quest_bundle(content),))
    checkpoint = validate_save(working, io=io)  # Existing read-only consistent transaction.
    record = next(r for r in checkpoint.core.components if type(r) is QuestRecord)
    if not isinstance(record, QuestRecord) or record.entity_id != definition.quest_id:
        raise GenerationError("NPC_CONTEXT_CONTENT")
    phase: KnownQuestPhase = (
        "available" if record.stage == 0 else "accepted" if record.stage in (1, 2) else "reported"
    )
    return NpcQuestContext(
        checkpoint.core.world_id,
        checkpoint.protocol.branch_id,
        checkpoint.protocol.revision,
        checkpoint.core.tick,
        io.hash_core(checkpoint.core),
        content.catalog_sha256,
        npc_id,
        definition.layout.actor_id,
        definition.quest_id,
        phase,
        1 if phase == "reported" else 0,
    )


def context_brief(context: NpcQuestContext) -> DialogueBrief:
    if type(context) is not NpcQuestContext:
        raise GenerationError("NPC_CONTEXT_INPUT")
    definition = harbor_definition()
    if (context.npc_id, context.actor_id, context.quest_id) != (
        definition.layout.npc_id,
        definition.layout.actor_id,
        definition.quest_id,
    ):
        raise GenerationError("NPC_CONTEXT_OWNER")
    # Revision/source binding stays in provenance;only scoped known facts enter the prose job.
    facts = {
        name: context.document()[name]
        for name in (
            "npc_id",
            "actor_id",
            "quest_id",
            "known_phase",
            "recorded_favor",
            "known_facts",
        )
    }
    return DialogueBrief(
        harbor_brief().text
        + "\nNPC-known facts at the source snapshot: "
        + canonical_json(facts).decode()
        + "\nThese are derived from committed quest progress,not a full memory history. "
        "Acceptance does not prove the NPC witnessed an enemy defeat. Never invent witness/history details. "
        "Generate all four conditional branches;completion/gratitude apply only after a report. "
        "Name the reward 포구의 호의,not money/items/another grant."
    )


def _generation_document(generated: GeneratedDialogue) -> JsonObject:
    if type(generated) is not GeneratedDialogue or type(generated.candidate) is not bytes:
        raise GenerationError("GENERATION_OUTPUT")
    try:
        decode_candidate(generated.candidate)
        require_integer(generated.attempts, 1, 2)
        for count in (
            generated.prompt_tokens,
            generated.output_tokens,
            generated.thought_tokens,
            generated.total_tokens,
        ):
            if count is not None:
                require_integer(count)
    except (ValueError, UnicodeError, RecursionError):
        raise GenerationError("GENERATION_OUTPUT") from None
    if (
        type(generated.model) is not str
        or re.fullmatch(r"[A-Za-z0-9._:/-]{1,128}", generated.model) is None
    ):
        raise GenerationError("GENERATION_OUTPUT")
    values = asdict(generated)
    return object_value(
        seal(
            {
                "provider": "gemini",
                "model": generated.model,
                "candidate_raw": generated.candidate.decode("utf-8"),
                "output_sha256": hashlib.sha256(generated.candidate).hexdigest(),
                "usage": {
                    name: value
                    for name, value in values.items()
                    if name not in ("candidate", "model")
                },
            }
        )
    )


def _target_available(output: Path) -> None:
    pending = output.with_name(output.name + ".pending")
    if any(path.exists() or path.is_symlink() for path in (output, pending)):
        raise GenerationError("GENERATION_TARGET_EXISTS")


def prepare(
    working: Path,
    content: QuestContent,
    npc_id: str,
    output: Path,
    *,
    generator: DialogueGenerator | None = None,
) -> NpcQuestContext:
    _target_available(output)
    context = read_context(working, content, npc_id)
    brief = context_brief(context)
    generation = None if generator is None else _generation_document(generator.generate(brief))
    if read_context(working, content, npc_id) != context:
        raise GenerationError("NPC_CONTEXT_STALE")
    body = canonical_json(
        {
            "format": "reverie-npc-preparation/v1",
            "status": "CONTEXT_ONLY" if generation is None else "NEEDS_REVIEW",
            "context": context.document(),
            "context_sha256": context.sha256,
            "brief_sha256": hashlib.sha256(brief.text.encode("utf-8")).hexdigest(),
            "generation": generation,
        }
    )
    if len(body) > MAX_PREPARATION_BYTES:
        raise GenerationError("NPC_CONTEXT_CAPACITY")
    publish_fresh(output, body)
    return context


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare NPC-known context from an existing quest save"
    )
    parser.add_argument("--working", type=Path, required=True)
    parser.add_argument("--quest-catalog", type=Path, required=True)
    parser.add_argument("--quest-sha256", required=True)
    parser.add_argument("--npc-id", default=harbor_definition().layout.npc_id)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--free-tier-confirmed", action="store_true")
    parser.add_argument("--free-data-use-confirmed", action="store_true")
    args = parser.parse_args(argv)
    try:
        content = load_dialogue(args.quest_catalog, args.quest_sha256, harbor_definition())
        # Reject invalid source/owner/target before constructing a provider or spending quota.
        _target_available(args.output)
        read_context(args.working, content, args.npc_id)
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
        result = prepare(args.working, content, args.npc_id, args.output, generator=generator)
        print(
            ("CONTEXT_ONLY " if generator is None else "GENERATED_NEEDS_REVIEW ")
            + "context_sha256="
            + result.sha256
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
