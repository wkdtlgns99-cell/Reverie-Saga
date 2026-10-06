from __future__ import annotations

from dataclasses import dataclass
from contracts.messages import WorldEvent
from domain.primitives import Phase, Tick


@dataclass(frozen=True, slots=True)
class ExecutionLimits:
    enable_simulation: bool
    max_duration_seconds: int
    cascade_waves: int
    max_events_per_tick: int
    max_pending: int


@dataclass(frozen=True, slots=True)
class QueuedEvent:
    event: WorldEvent
    delivery_phase: Phase
    priority: int


@dataclass(frozen=True, slots=True)
class DeliveryBatch:
    logical_tick: Tick
    phase: Phase
    wave: int
    events: tuple[WorldEvent, ...]
