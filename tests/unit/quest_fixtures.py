"""Explicit offline test content;not a Gemini result or production approval."""

from __future__ import annotations

import hashlib
from pathlib import Path

from adapters.quest_dialogue import compile_dialogue, decode_catalog
from app.quest import harbor_definition
from contracts.dialogue import ARTIFACT_ID, QuestContent
from domain.canonical import canonical_json


def candidate() -> bytes:
    return (
        Path(__file__).resolve().parents[2] / "docs/reviews/QT-F07_DIALOGUE_EXAMPLE.json"
    ).read_bytes()


def receipt(body: bytes) -> bytes:
    return canonical_json(
        {
            "artifact_id": ARTIFACT_ID,
            "output_sha256": hashlib.sha256(body).hexdigest(),
            "brief_sha256": "0" * 64,
            "decision": "APPROVED",
            "approved_by": "automated-test-only",
            "approved_utc": "2026-10-13T00:00:00+00:00",
        }
    )


def catalog() -> bytes:
    body = candidate()
    return compile_dialogue(body, receipt(body))


def content() -> QuestContent:
    body = catalog()
    return decode_catalog(body, hashlib.sha256(body).hexdigest(), harbor_definition())
