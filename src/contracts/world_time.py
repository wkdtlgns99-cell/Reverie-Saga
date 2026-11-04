"""Recorded explicit whole-second world-time commands and presentation."""

from dataclasses import dataclass

from contracts.messages import CommandPayload, FactPayload, PresentationPayload
from domain.primitives import TypeKey


@dataclass(frozen=True, slots=True)
class WorldWait(CommandPayload):
    seconds: int
    SCHEMA = TypeKey("world.wait", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class TimePassed(FactPayload):
    start: int
    end: int
    SCHEMA = TypeKey("world.time-passed", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class TimeCue(PresentationPayload):
    start: int
    end: int
    SCHEMA = TypeKey("world.time-cue", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


TIME_PAYLOADS = (WorldWait, TimePassed, TimeCue)
