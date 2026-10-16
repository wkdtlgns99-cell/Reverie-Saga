"""Immutable dialogue metadata;no provider,clock or filesystem dependencies."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Protocol, runtime_checkable

from contracts.narratives import narrative_text
from domain.canonical import JsonObject, canonical_json, object_value, seal
from domain.primitives import EntityId
from domain.quest import QuestDefinition
from domain.scenario import Scenario

INTENTS = ("completion", "gratitude", "offer", "reminder")
ARTIFACT_ID = "dialogue:harbor-sentinel-v1"
CANDIDATE_FORMAT = "reverie-quest-dialogue-candidate/v1"
CATALOG_FORMAT = "reverie-quest-dialogue/v1"
MAX_DIALOGUE_BYTES = 16 * 1024


def hex_digest(value: str) -> None:
    if type(value) is not str or re.fullmatch("[0-9a-f]{64}", value) is None:
        raise ValueError("DIALOGUE_HASH")


@dataclass(frozen=True, slots=True)
class DialogueLine:
    intent: str
    text_ko: str

    def __post_init__(self) -> None:
        if type(self.intent) is not str or self.intent not in INTENTS:
            raise ValueError("DIALOGUE_INTENTS")
        try:
            narrative_text(self.text_ko, 1024)
        except ValueError as error:
            raise ValueError("DIALOGUE_TEXT") from error


@dataclass(frozen=True, slots=True)
class QuestDialogue:
    quest_id: str
    npc_id: EntityId
    lines: tuple[DialogueLine, ...]

    def __post_init__(self) -> None:
        if (
            type(self.quest_id) is not str
            or type(self.npc_id) is not str
            or self.quest_id != "quest:harbor-sentinel"
            or self.npc_id != "actor:harbor-watcher"
        ):
            raise ValueError("DIALOGUE_BINDING")
        if (
            type(self.lines) is not tuple
            or any(type(line) is not DialogueLine for line in self.lines)
            or tuple(line.intent for line in self.lines) != INTENTS
        ):
            raise ValueError("DIALOGUE_INTENTS")

    def text(self, intent: str) -> str:
        return next(line.text_ko for line in self.lines if line.intent == intent)

    def document(self) -> JsonObject:
        return object_value(
            seal(
                {
                    "format": CANDIDATE_FORMAT,
                    "quest_id": self.quest_id,
                    "npc_id": self.npc_id,
                    "lines": tuple(
                        {"intent": line.intent, "text_ko": line.text_ko} for line in self.lines
                    ),
                }
            )
        )


@dataclass(frozen=True, slots=True)
class QuestContent:
    definition: QuestDefinition
    dialogue: QuestDialogue
    output_sha256: str
    brief_sha256: str

    def __post_init__(self) -> None:
        if type(self.definition) is not QuestDefinition or type(self.dialogue) is not QuestDialogue:
            raise ValueError("DIALOGUE_BINDING")
        if (
            self.definition.quest_id != self.dialogue.quest_id
            or self.definition.layout.npc_id != self.dialogue.npc_id
        ):
            raise ValueError("DIALOGUE_BINDING")
        hex_digest(self.output_sha256)
        hex_digest(self.brief_sha256)

    def document(self) -> JsonObject:
        return object_value(
            seal(
                {
                    "format": CATALOG_FORMAT,
                    "candidate": self.dialogue.document(),
                    "approval": {
                        "artifact_id": ARTIFACT_ID,
                        "output_sha256": self.output_sha256,
                        "brief_sha256": self.brief_sha256,
                    },
                }
            )
        )

    @property
    def catalog_sha256(self) -> str:
        return hashlib.sha256(canonical_json(self.document())).hexdigest()


@runtime_checkable
class QuestConsumer(Protocol):
    @property
    def quest_content(self) -> QuestContent: ...


class QuestBound:
    """No default binding:skipped construction is rejected by required boot-role validation."""

    _content: QuestContent

    def __init__(self, content: QuestContent) -> None:
        if type(content) is not QuestContent:
            raise ValueError("DIALOGUE_BINDING")
        self._content = content

    @property
    def quest_content(self) -> QuestContent:
        return self._content

    @property
    def scenario_layout(self) -> Scenario:
        return self._content.definition.layout


@dataclass(frozen=True, slots=True)
class DialogueBrief:
    text: str

    def __post_init__(self) -> None:
        if type(self.text) is not str or not self.text.strip() or len(self.text.encode()) > 4096:
            raise ValueError("GENERATION_INPUT")


@dataclass(frozen=True, slots=True)
class GeneratedDialogue:
    candidate: bytes
    model: str
    prompt_tokens: int | None
    output_tokens: int | None
    thought_tokens: int | None
    total_tokens: int | None
    attempts: int = 1


class DialogueGenerator(Protocol):
    def generate(self, brief: DialogueBrief) -> GeneratedDialogue: ...


class GenerationError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)
