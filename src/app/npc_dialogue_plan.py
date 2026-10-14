"""Offline preview and exact current-source/configuration validation for generation."""

from __future__ import annotations

import hashlib
from pathlib import Path

from adapters.gemini_dialogue import MODEL, generation_request
from adapters.quest_dialogue import publish_fresh
from app.npc_memory import read_memory
from app.npc_memory_brief import memory_brief
from app.npc_prepare import _target_available
from contracts.dialogue import DialogueBrief, GenerationError, QuestContent, hex_digest
from contracts.npc_memory import NpcMemoryContext
from domain.canonical import (
    JsonObject,
    canonical_json,
    decode_json,
    exact_fields,
    object_value,
    seal,
    text_value,
)

MAX_PLAN_BYTES = 16384


def plan_document(context: NpcMemoryContext) -> JsonObject:
    brief = memory_brief(context)
    return object_value(
        seal(
            {
                "format": "reverie-npc-dialogue-plan/v1",
                "status": "PREVIEW",
                "context": context.document(),
                "context_sha256": context.sha256,
                "brief_text": brief.text,
                "brief_sha256": hashlib.sha256(brief.text.encode()).hexdigest(),
                "provider": "gemini",
                "model": MODEL,
                "request_sha256": hashlib.sha256(
                    canonical_json(generation_request(brief))
                ).hexdigest(),
            }
        )
    )


def preview_memory(
    working: Path, content: QuestContent, npc_id: str, output: Path
) -> NpcMemoryContext:
    _target_available(output)
    context = read_memory(working, content, npc_id)
    body = canonical_json(plan_document(context))
    if len(body) > MAX_PLAN_BYTES:
        raise GenerationError("NPC_CONTEXT_CAPACITY")
    if read_memory(working, content, npc_id) != context:
        raise GenerationError("NPC_CONTEXT_STALE")
    publish_fresh(output, body)
    return context


def check_plan(
    working: Path, content: QuestContent, npc_id: str, plan_path: Path
) -> NpcMemoryContext:
    try:
        with plan_path.open("rb") as source:
            raw = source.read(MAX_PLAN_BYTES + 1)
    except OSError:
        raise GenerationError("NPC_DIALOGUE_PLAN_UNAVAILABLE") from None
    try:
        if len(raw) > MAX_PLAN_BYTES:
            raise ValueError("capacity")
        document = exact_fields(
            decode_json(raw),
            (
                "format",
                "status",
                "context",
                "context_sha256",
                "brief_text",
                "brief_sha256",
                "provider",
                "model",
                "request_sha256",
            ),
        )
        if document["format"] != "reverie-npc-dialogue-plan/v1" or document["status"] != "PREVIEW":
            raise ValueError("format/status")
        object_value(document["context"])
        DialogueBrief(text_value(document["brief_text"]))
        for name in ("context_sha256", "brief_sha256", "request_sha256"):
            hex_digest(text_value(document[name]))
        text_value(document["provider"])
        text_value(document["model"])
    except (ValueError, UnicodeError, RecursionError):
        raise GenerationError("NPC_DIALOGUE_PLAN_INVALID") from None
    context = read_memory(working, content, npc_id)
    if document["context_sha256"] != context.sha256:
        raise GenerationError("NPC_CONTEXT_STALE")
    if canonical_json(document) != canonical_json(plan_document(context)):
        raise GenerationError("NPC_DIALOGUE_PLAN_INVALID")
    if read_memory(working, content, npc_id) != context:
        raise GenerationError("NPC_CONTEXT_STALE")
    return context
