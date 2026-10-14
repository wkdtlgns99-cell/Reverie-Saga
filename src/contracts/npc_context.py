"""Bounded derived NPC knowledge;not an authoritative memory component."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import re
from typing import Literal

from contracts.dialogue import hex_digest
from domain.canonical import JsonObject, canonical_json, object_value, seal
from domain.primitives import require_integer, require_namespace

type KnownQuestPhase = Literal["available", "accepted", "reported"]
CONTEXT_FORMAT = "reverie-npc-quest-context/v1"
MAX_CONTEXT_BYTES = 2048


@dataclass(frozen=True, slots=True)
class NpcQuestContext:
    world_id: str
    branch_id: str
    revision: int
    tick: int
    core_hash: str
    catalog_sha256: str
    npc_id: str
    actor_id: str
    quest_id: str
    known_phase: KnownQuestPhase
    recorded_favor: int

    def __post_init__(self) -> None:
        for value, pattern in (
            (self.world_id, r"w1-[0-9a-f]{64}"),
            (self.branch_id, r"[0-9a-f]{32}"),
        ):
            if type(value) is not str or re.fullmatch(pattern, value) is None:
                raise ValueError("NPC_CONTEXT_ID")
        for number in (self.revision, self.tick):
            require_integer(number)
        for value in (self.core_hash, self.catalog_sha256):
            hex_digest(value)
        for value, prefix in (
            (self.npc_id, "actor:"),
            (self.actor_id, "actor:"),
            (self.quest_id, "quest:"),
        ):
            if type(value) is not str or not value.startswith(prefix):
                raise ValueError("NPC_CONTEXT_ID")
            require_namespace(value)
        if self.npc_id == self.actor_id:
            raise ValueError("NPC_CONTEXT_ID")
        if type(self.known_phase) is not str or self.known_phase not in (
            "available",
            "accepted",
            "reported",
        ):
            raise ValueError("NPC_CONTEXT_PHASE")
        require_integer(self.recorded_favor, 0, 1)
        if self.recorded_favor != (1 if self.known_phase == "reported" else 0):
            raise ValueError("NPC_CONTEXT_PHASE")

    def document(self) -> JsonObject:
        facts = (
            ("quest_available",)
            if self.known_phase == "available"
            else ("quest_accepted",)
            if self.known_phase == "accepted"
            else ("quest_accepted", "completion_reported", "favor_recorded")
        )
        data = object_value(
            seal(
                {
                    "format": CONTEXT_FORMAT,
                    **asdict(self),
                    "source_kind": "quest.progress/v1",
                    "known_facts": facts,
                }
            )
        )
        if len(canonical_json(data)) > MAX_CONTEXT_BYTES:
            raise ValueError("NPC_CONTEXT_CAPACITY")
        return data

    @property
    def sha256(self) -> str:
        return hashlib.sha256(canonical_json(self.document())).hexdigest()
