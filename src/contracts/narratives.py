"""Descriptive-only content;no legacy gameplay schema or state bindings."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal
import unicodedata

type NarrativeCategory = Literal["settlement", "creature", "facility", "quest"]
NARRATIVE_CATEGORIES: tuple[NarrativeCategory, ...] = (
    "settlement",
    "creature",
    "facility",
    "quest",
)
MAX_NARRATIVES = 4096
MAX_NAME_BYTES = 256
MAX_DESCRIPTION_BYTES = 4096


def narrative_text(value: str, maximum: int) -> None:
    if (
        type(value) is not str
        or not value.strip()
        or unicodedata.normalize("NFC", value) != value
        or len(value.encode("utf-8")) > maximum
        or any(ord(c) < 32 for c in value)
    ):
        raise ValueError("NARRATIVE_TEXT")


@dataclass(frozen=True, slots=True)
class Narrative:
    entry_id: str
    category: NarrativeCategory
    name_ko: str
    description_ko: str

    def __post_init__(self) -> None:
        if (
            type(self.entry_id) is not str
            or re.fullmatch(r"narrative:[a-z]+-[0-9a-f]{16}", self.entry_id) is None
        ):
            raise ValueError("NARRATIVE_ID")
        if self.category not in NARRATIVE_CATEGORIES:
            raise ValueError("NARRATIVE_CATEGORY")
        narrative_text(self.name_ko, MAX_NAME_BYTES)
        narrative_text(self.description_ko, MAX_DESCRIPTION_BYTES)
