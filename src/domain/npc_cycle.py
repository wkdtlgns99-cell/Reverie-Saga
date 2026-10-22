"""Bounded communal supply and actual causal anchors for one NPC's own actions."""

from dataclasses import dataclass
import hashlib
import re

from domain.canonical import pack
from domain.npc_work import STOCK_CAP, WORK_PERIOD
from domain.primitives import EntityId, TypeKey, require_integer, require_namespace
from domain.state_types import ComponentRecord

CYCLE_SCHEMA = TypeKey("quest.cycle", 1)
USE_PERIOD = 10
MEMORY_CAP = 4


@dataclass(frozen=True, slots=True)
class Supply:
    stock: int
    produced: int
    consumed: int

    def __post_init__(self) -> None:
        require_integer(self.stock, 0, STOCK_CAP)
        require_integer(self.produced)
        require_integer(self.consumed)
        if self.produced - self.consumed != self.stock:
            raise ValueError("NPC_CYCLE_BALANCE")


def state_at(tick: int) -> Supply:
    """Independent closed-form checkpoint oracle for the fixed 4/10-second rules."""
    require_integer(tick)
    stock = (
        tick // WORK_PERIOD - tick // USE_PERIOD
        if tick < 16
        else (2 if tick % 20 in (10, 11) else STOCK_CAP)
    )
    return Supply(stock, stock + tick // USE_PERIOD, tick // USE_PERIOD)


def actions_at(tick: int, before: Supply) -> tuple[Supply, ...]:
    require_integer(tick, 1)
    if type(before) is not Supply:
        raise ValueError("NPC_CYCLE_STATE")
    values: list[Supply] = []
    current = before
    if tick % USE_PERIOD == 0 and current.stock:
        current = Supply(current.stock - 1, current.produced, current.consumed + 1)
        values.append(current)
    if tick % WORK_PERIOD == 0 and current.stock < STOCK_CAP:
        current = Supply(current.stock + 1, current.produced + 1, current.consumed)
        values.append(current)
    return tuple(values)


def wake_identity(world_id: str, tick: int) -> str:
    return (
        "e1-"
        + hashlib.sha256(
            pack(("event-id/v1", world_id, str(tick), "PRE_TICK", "0", "watch.npc", "0"))
        ).hexdigest()
    )


@dataclass(frozen=True, slots=True)
class SupplyEvidence:
    tick: int
    sequence: int
    source_event_id: str
    before: Supply
    after: Supply

    def __post_init__(self) -> None:
        require_integer(self.tick, 1)
        require_integer(self.sequence, 0, 1)
        if (
            type(self.source_event_id) is not str
            or re.fullmatch(r"e1-[0-9a-f]{64}", self.source_event_id) is None
        ):
            raise ValueError("NPC_CYCLE_SOURCE")
        if type(self.before) is not Supply or type(self.after) is not Supply:
            raise ValueError("NPC_CYCLE_STATE")
        Supply(self.before.stock, self.before.produced, self.before.consumed)
        Supply(self.after.stock, self.after.produced, self.after.consumed)
        increments = (
            self.after.produced - self.before.produced,
            self.after.consumed - self.before.consumed,
        )
        if increments not in ((1, 0), (0, 1)):
            raise ValueError("NPC_CYCLE_TRANSITION")

    @property
    def prepared(self) -> bool:
        return self.after.produced > self.before.produced


@dataclass(frozen=True, slots=True)
class CycleRecord(ComponentRecord):
    entity_id: EntityId
    state: Supply
    entries: tuple[SupplyEvidence, ...]

    @property
    def schema(self) -> TypeKey:
        return CYCLE_SCHEMA

    def __post_init__(self) -> None:
        if type(self.entity_id) is not str or not self.entity_id.startswith("actor:"):
            raise ValueError("NPC_CYCLE_OWNER")
        require_namespace(self.entity_id)
        if type(self.state) is not Supply or type(self.entries) is not tuple:
            raise ValueError("NPC_CYCLE_STATE")
        Supply(self.state.stock, self.state.produced, self.state.consumed)
        total = self.state.produced + self.state.consumed
        if len(self.entries) != min(MEMORY_CAP, total) or any(
            type(e) is not SupplyEvidence for e in self.entries
        ):
            raise ValueError("NPC_CYCLE_MEMORY")
        if self.entries and self.entries[-1].after != self.state:
            raise ValueError("NPC_CYCLE_MEMORY")
        for entry in self.entries:
            SupplyEvidence(
                entry.tick, entry.sequence, entry.source_event_id, entry.before, entry.after
            )
        for left, right in zip(self.entries, self.entries[1:]):
            if (left.tick, left.sequence) >= (
                right.tick,
                right.sequence,
            ) or left.after != right.before:
                raise ValueError("NPC_CYCLE_ORDER")


def advance(before: CycleRecord, tick: int, source: str) -> CycleRecord:
    current = before.state
    entries = before.entries
    for sequence, after in enumerate(actions_at(tick, current)):
        entries = (*entries, SupplyEvidence(tick, sequence, source, current, after))[-MEMORY_CAP:]
        current = after
    return CycleRecord(before.entity_id, current, entries)


def validate_chain(before: CycleRecord, after: CycleRecord, *, staged: bool) -> None:
    if type(before) is not CycleRecord or type(after) is not CycleRecord:
        raise ValueError("NPC_CYCLE_RECORD")
    count = (
        after.state.produced + after.state.consumed - before.state.produced - before.state.consumed
    )
    if before.entity_id != after.entity_id or count <= 0 or staged and count > 2:
        raise ValueError("NPC_CYCLE_TRANSITION")
    if after.state.produced < before.state.produced or after.state.consumed < before.state.consumed:
        raise ValueError("NPC_CYCLE_TRANSITION")
    if staged:
        appended = after.entries[-count:]
        if (
            appended[0].before != before.state
            or after.entries != (*before.entries, *appended)[-MEMORY_CAP:]
        ):
            raise ValueError("NPC_CYCLE_MEMORY")
        tick, source = appended[0].tick, appended[0].source_event_id
        if advance(before, tick, source) != after:
            raise ValueError("NPC_CYCLE_TRANSITION")


def validate_checkpoint(record: CycleRecord, world_id: str, tick: int) -> None:
    if record.state != state_at(tick):
        raise ValueError("NPC_CYCLE_CHECKPOINT")
    expected: tuple[SupplyEvidence, ...] = ()
    for at in range(max(1, tick - 40), tick + 1):
        before = state_at(at - 1)
        for sequence, after in enumerate(actions_at(at, before)):
            expected = (
                *expected,
                SupplyEvidence(at, sequence, wake_identity(world_id, at), before, after),
            )[-MEMORY_CAP:]
            before = after
    if record.entries != expected:
        raise ValueError("NPC_CYCLE_CHECKPOINT")
