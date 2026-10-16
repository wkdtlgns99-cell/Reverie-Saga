"""Bounded validation/compilation of explicitly approved dialogue artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import os
import sys
from pathlib import Path

from contracts.dialogue import (
    ARTIFACT_ID,
    CANDIDATE_FORMAT,
    CATALOG_FORMAT,
    MAX_DIALOGUE_BYTES,
    DialogueLine,
    QuestContent,
    QuestDialogue,
    hex_digest,
)
from domain.canonical import (
    array_value,
    canonical_json,
    decode_json,
    exact_fields,
    seal,
    text_value,
)
from domain.primitives import EntityId
from domain.quest import QuestDefinition


def decode_candidate(body: bytes) -> QuestDialogue:
    if type(body) is not bytes or not 1 <= len(body) <= MAX_DIALOGUE_BYTES:
        raise ValueError("DIALOGUE_CAPACITY")
    data = exact_fields(decode_json(body), ("format", "quest_id", "npc_id", "lines"))
    if data["format"] != CANDIDATE_FORMAT:
        raise ValueError("DIALOGUE_FORMAT")
    lines = []
    for value in array_value(data["lines"]):
        row = exact_fields(value, ("intent", "text_ko"))
        lines.append(DialogueLine(text_value(row["intent"]), text_value(row["text_ko"])))
    return QuestDialogue(
        text_value(data["quest_id"]), EntityId(text_value(data["npc_id"])), tuple(lines)
    )


def compile_dialogue(candidate: bytes, receipt: bytes) -> bytes:
    dialogue = decode_candidate(candidate)
    if not 1 <= len(receipt) <= MAX_DIALOGUE_BYTES:
        raise ValueError("DIALOGUE_CAPACITY")
    approval = exact_fields(
        decode_json(receipt),
        (
            "artifact_id",
            "output_sha256",
            "brief_sha256",
            "decision",
            "approved_by",
            "approved_utc",
        ),
    )
    output_hash, brief_hash = (
        text_value(approval["output_sha256"]),
        text_value(approval["brief_sha256"]),
    )
    hex_digest(output_hash)
    hex_digest(brief_hash)
    if (
        approval["artifact_id"] != ARTIFACT_ID
        or approval["decision"] != "APPROVED"
        or hashlib.sha256(candidate).hexdigest() != output_hash
        or not text_value(approval["approved_by"]).strip()
    ):
        raise ValueError("DIALOGUE_APPROVAL")
    stamp = text_value(approval["approved_utc"])
    parsed = datetime.fromisoformat(stamp)
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("DIALOGUE_APPROVAL")
    document = seal(
        {
            "format": CATALOG_FORMAT,
            "candidate": dialogue.document(),
            "approval": {
                "artifact_id": ARTIFACT_ID,
                "output_sha256": output_hash,
                "brief_sha256": brief_hash,
            },
        }
    )
    result = canonical_json(document)
    if len(result) > MAX_DIALOGUE_BYTES:
        raise ValueError("DIALOGUE_CAPACITY")
    return result


def decode_catalog(body: bytes, expected_sha256: str, definition: QuestDefinition) -> QuestContent:
    hex_digest(expected_sha256)
    if (
        not 1 <= len(body) <= MAX_DIALOGUE_BYTES
        or hashlib.sha256(body).hexdigest() != expected_sha256
    ):
        raise ValueError("DIALOGUE_CATALOG_HASH")
    data = exact_fields(decode_json(body), ("format", "candidate", "approval"))
    if data["format"] != CATALOG_FORMAT:
        raise ValueError("DIALOGUE_FORMAT")
    approval = exact_fields(data["approval"], ("artifact_id", "output_sha256", "brief_sha256"))
    if approval["artifact_id"] != ARTIFACT_ID:
        raise ValueError("DIALOGUE_APPROVAL")
    content = QuestContent(
        definition,
        decode_candidate(canonical_json(data["candidate"])),
        text_value(approval["output_sha256"]),
        text_value(approval["brief_sha256"]),
    )
    if canonical_json(content.document()) != body:
        raise ValueError("DIALOGUE_ORDER")
    return content


def load_dialogue(path: Path, expected_sha256: str, definition: QuestDefinition) -> QuestContent:
    with path.open("rb") as source:
        body = source.read(MAX_DIALOGUE_BYTES + 1)
    return decode_catalog(body, expected_sha256, definition)


def publish_fresh(path: Path, body: bytes) -> None:
    """Exclusive creation avoids overwriting an existing accepted artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(path.name + ".pending")
    owned = False
    try:
        with pending.open("xb") as target:
            owned = True
            target.write(body)
            target.flush()
            os.fsync(target.fileno())
        # Windows rename is atomic and refuses an existing destination. POSIX rename replaces
        # existing files,so its publication uses an exclusive hard link instead.
        if sys.platform == "win32":
            os.rename(pending, path)
        else:
            os.link(pending, path)
    finally:
        if owned:
            pending.unlink(missing_ok=True)
