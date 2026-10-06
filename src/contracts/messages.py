from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Protocol, TYPE_CHECKING

from contracts.read_views import ReadPort
from domain.primitives import EventId, FieldAddress, FrozenPayload, Phase, Tick, TypeKey
if TYPE_CHECKING:
    from contracts.turn import CommitReceipt, Degradation


class CommandPayload(FrozenPayload, ABC):
    __slots__ = ()


class FactPayload(FrozenPayload, ABC):
    __slots__ = ()


class PresentationPayload(FrozenPayload, ABC):
    __slots__ = ()


class StateDelta(FrozenPayload, ABC):
    __slots__ = ()
    @property
    @abstractmethod
    def target(self) -> FieldAddress: ...


@dataclass(frozen=True, slots=True)
class EmittedFact:
    payload: FactPayload
    due_tick: Tick
    caused_by: tuple[EventId, ...]


@dataclass(frozen=True, slots=True)
class EventHeader:
    event_id: EventId
    type_key: TypeKey
    producer_id: str
    occurred_at: Tick
    phase: Phase
    wave: int
    producer_rank: int
    sequence: int
    caused_by: tuple[EventId, ...]
    degraded: tuple[Degradation, ...]


@dataclass(frozen=True, slots=True)
class WorldEvent:
    header: EventHeader
    due_tick: Tick
    payload: FactPayload


@dataclass(frozen=True, slots=True)
class StateDiff:
    receipt: CommitReceipt
    changes: tuple[StateDelta, ...]


@dataclass(frozen=True, slots=True)
class PresentationEvent:
    header: EventHeader
    payload: PresentationPayload
    priority: Literal["essential", "important", "ambient"]
    coalesce_policy: Literal["keep_all", "replace_latest"]
    coalesce_key: str


class Presenter(Protocol):
    def map(self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt,
            committed: ReadPort) -> tuple[PresentationEvent, ...]: ...


@dataclass(frozen=True, slots=True)
class EventPolicy:
    schema: TypeKey
    mode: Literal["simulate", "record_only"]
    delivery_phase: Phase
    priority: int
    late_route: Literal["reject", "next_tick"]
    producers: tuple[str, ...]
    subscribers: tuple[str, ...]
    cancellers: tuple[str, ...]
