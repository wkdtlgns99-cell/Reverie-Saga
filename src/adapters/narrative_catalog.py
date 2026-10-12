"""Validate hash-pinned narrative catalogs before presenting any imported content."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
from pathlib import Path
from typing import cast

from contracts.narratives import MAX_NARRATIVES, Narrative, NarrativeCategory
from domain.canonical import (
    array_value,
    canonical_json,
    decode_json,
    exact_fields,
    seal,
    text_value,
)

MAX_CATALOG_BYTES = 64 * 1024
CATALOG_FORMAT = "reverie-narratives/v1"


def _validated(entries: tuple[Narrative, ...]) -> tuple[Narrative, ...]:
    if not 1 <= len(entries) <= MAX_NARRATIVES:
        raise ValueError("NARRATIVE_COUNT")
    if len({e.entry_id for e in entries}) != len(entries):
        raise ValueError("NARRATIVE_DUPLICATE_ID")
    return tuple(sorted(entries, key=lambda e: e.entry_id))


def compile_catalog(entries: tuple[Narrative, ...]) -> bytes:
    entries = _validated(entries)
    payload = seal(tuple(asdict(e) for e in entries))
    body = canonical_json(
        {
            "format": CATALOG_FORMAT,
            "entries": payload,
            "entries_sha256": hashlib.sha256(canonical_json(payload)).hexdigest(),
        }
    )
    if len(body) > MAX_CATALOG_BYTES:
        raise ValueError("NARRATIVE_CAPACITY")
    return body


def decode_catalog(body: bytes, expected_sha256: str) -> tuple[Narrative, ...]:
    if (
        not 1 <= len(body) <= MAX_CATALOG_BYTES
        or hashlib.sha256(body).hexdigest() != expected_sha256
    ):
        raise ValueError("NARRATIVE_CATALOG_HASH")
    document = exact_fields(decode_json(body), ("format", "entries", "entries_sha256"))
    if document["format"] != CATALOG_FORMAT:
        raise ValueError("NARRATIVE_FORMAT")
    payload = array_value(document["entries"])
    if hashlib.sha256(canonical_json(payload)).hexdigest() != document["entries_sha256"]:
        raise ValueError("NARRATIVE_ENTRIES_HASH")
    entries: list[Narrative] = []
    for item in payload:
        row = exact_fields(item, ("entry_id", "category", "name_ko", "description_ko"))
        entries.append(
            Narrative(
                text_value(row["entry_id"]),
                cast(NarrativeCategory, text_value(row["category"])),
                text_value(row["name_ko"]),
                text_value(row["description_ko"]),
            )
        )
    result = _validated(tuple(entries))
    if tuple(entries) != result:
        raise ValueError("NARRATIVE_ORDER")
    return result


def load_catalog(path: Path, expected_sha256: str) -> tuple[Narrative, ...]:
    with path.open("rb") as source:
        body = source.read(MAX_CATALOG_BYTES + 1)
    return decode_catalog(body, expected_sha256)
