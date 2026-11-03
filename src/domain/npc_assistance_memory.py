"""Bounded, authoritative memory of an NPC's own committed passage assistance."""

from dataclasses import dataclass
import hashlib
import re
from typing import Literal

from domain.canonical import pack
from domain.primitives import EntityId, TypeKey, require_integer, require_namespace
from domain.state_types import ComponentRecord
from domain.watch import ECHO_DEPTH, WAKE_PERIOD

ASSISTANCE_SCHEMA = TypeKey("quest.assistance-memory", 1)
ASSISTANCE_CAPACITY = 4
type AssistanceSource = Literal["wake", "answered_call"]


@dataclass(frozen=True, slots=True)
class AssistanceEntry:
    tick: int
    target_id: EntityId
    source_kind: AssistanceSource
    cause_event_id: str

    def __post_init__(self) -> None:
        try:
            require_integer(self.tick, 1)
        except ValueError as error:
            raise ValueError("NPC_ASSISTANCE_MEMORY_INPUT") from error
        if type(self.target_id) is not str or not self.target_id.startswith("object:"):
            raise ValueError("NPC_ASSISTANCE_MEMORY_OWNER")
        try:
            require_namespace(self.target_id)
        except ValueError as error:
            raise ValueError("NPC_ASSISTANCE_MEMORY_OWNER") from error
        if (
            type(self.source_kind) is not str
            or self.source_kind not in ("wake", "answered_call")
            or type(self.cause_event_id) is not str
            or re.fullmatch(r"e1-[0-9a-f]{64}", self.cause_event_id) is None
        ):
            raise ValueError("NPC_ASSISTANCE_MEMORY_SOURCE")
        if self.source_kind == "wake" and self.tick % WAKE_PERIOD:
            raise ValueError("NPC_ASSISTANCE_MEMORY_SOURCE")


@dataclass(frozen=True, slots=True)
class AssistanceMemory:
    total_assists: int
    entries: tuple[AssistanceEntry, ...]

    def __post_init__(self) -> None:
        try:
            require_integer(self.total_assists)
        except ValueError as error:
            raise ValueError("NPC_ASSISTANCE_MEMORY_INPUT") from error
        if (
            type(self.entries) is not tuple
            or len(self.entries) != min(self.total_assists, ASSISTANCE_CAPACITY)
            or any(type(entry) is not AssistanceEntry for entry in self.entries)
        ):
            raise ValueError("NPC_ASSISTANCE_MEMORY_ENTRIES")
        for entry in self.entries:
            AssistanceEntry(entry.tick, entry.target_id, entry.source_kind, entry.cause_event_id)
        if (
            any(a.tick >= b.tick for a, b in zip(self.entries, self.entries[1:]))
            or len({entry.cause_event_id for entry in self.entries}) != len(self.entries)
            or any(
                entry.tick < self.total_assists - len(self.entries) + index + 1
                for index, entry in enumerate(self.entries)
            )
        ):
            raise ValueError("NPC_ASSISTANCE_MEMORY_ORDER")


@dataclass(frozen=True, slots=True)
class AssistanceMemoryRecord(ComponentRecord):
    entity_id: EntityId
    state: AssistanceMemory

    @property
    def schema(self) -> TypeKey:
        return ASSISTANCE_SCHEMA

    def __post_init__(self) -> None:
        if type(self.entity_id) is not str or not self.entity_id.startswith("actor:"):
            raise ValueError("NPC_ASSISTANCE_MEMORY_OWNER")
        try:
            require_namespace(self.entity_id)
        except ValueError as error:
            raise ValueError("NPC_ASSISTANCE_MEMORY_OWNER") from error
        if type(self.state) is not AssistanceMemory:
            raise ValueError("NPC_ASSISTANCE_MEMORY_INPUT")
        AssistanceMemory(self.state.total_assists, self.state.entries)


def append_assistance(before: AssistanceMemory, entry: AssistanceEntry) -> AssistanceMemory:
    if type(before) is not AssistanceMemory or type(entry) is not AssistanceEntry:
        raise ValueError("NPC_ASSISTANCE_MEMORY_INPUT")
    AssistanceMemory(before.total_assists, before.entries)
    if before.entries and entry.tick <= before.entries[-1].tick:
        raise ValueError("NPC_ASSISTANCE_MEMORY_ORDER")
    return AssistanceMemory(
        before.total_assists + 1, (*before.entries, entry)[-ASSISTANCE_CAPACITY:]
    )


def validate_transition(
    before: AssistanceMemory, after: AssistanceMemory, *, single: bool = False
) -> None:
    if type(before) is not AssistanceMemory or type(after) is not AssistanceMemory:
        raise ValueError("NPC_ASSISTANCE_MEMORY_INPUT")
    AssistanceMemory(before.total_assists, before.entries)
    AssistanceMemory(after.total_assists, after.entries)
    count = after.total_assists - before.total_assists
    if count <= 0 or single and count != 1:
        raise ValueError("NPC_ASSISTANCE_MEMORY_ORDER")
    added = after.entries[-min(count, ASSISTANCE_CAPACITY) :]
    kept = max(0, len(after.entries) - len(added))
    if (
        (kept and before.entries[-kept:] != after.entries[:kept])
        or before.entries
        and added[0].tick <= before.entries[-1].tick
        or before.entries
        and any(
            entry.tick < before.entries[-1].tick + count - len(added) + index + 1
            for index, entry in enumerate(added)
        )
    ):
        raise ValueError("NPC_ASSISTANCE_MEMORY_ORDER")


def validate_checkpoint(
    record: AssistanceMemoryRecord,
    world_id: str,
    tick: int,
    *,
    accepted_at: int | None,
    reported_at: int | None,
) -> None:
    if type(record) is not AssistanceMemoryRecord:
        raise ValueError("NPC_ASSISTANCE_MEMORY_INPUT")
    AssistanceMemoryRecord(record.entity_id, record.state)
    state = record.state
    if state.total_assists > tick or state.total_assists and accepted_at is None:
        raise ValueError("NPC_ASSISTANCE_MEMORY_SOURCE")
    for index, entry in enumerate(state.entries):
        if (
            accepted_at is None
            or entry.tick > tick
            or entry.tick < accepted_at + state.total_assists - len(state.entries) + index + 1
            or reported_at is not None
            and entry.tick > reported_at
        ):
            raise ValueError("NPC_ASSISTANCE_MEMORY_SOURCE")
        phase, wave, producer = (
            ("PRE_TICK", 0, "watch.npc")
            if entry.source_kind == "wake"
            else ("CASCADE", ECHO_DEPTH, "watch.echo")
        )
        expected = (
            "e1-"
            + hashlib.sha256(
                pack(("event-id/v1", world_id, str(entry.tick), phase, str(wave), producer, "0"))
            ).hexdigest()
        )
        if entry.cause_event_id != expected:
            raise ValueError("NPC_ASSISTANCE_MEMORY_SOURCE")
