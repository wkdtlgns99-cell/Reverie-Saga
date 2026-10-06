from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
import re
from typing import Literal, NewType

EntityId = NewType("EntityId", str)
CommandId = NewType("CommandId", str)
EventId = NewType("EventId", str)
Tick = NewType("Tick", int)
WorldRevision = NewType("WorldRevision", int)
MAX_INT = 2**63 - 1
MIN_INT = -(2**63)


def require_integer(value: int, minimum: int = 0, maximum: int = MAX_INT) -> None:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("integer outside declared range")


def require_namespace(value: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[a-z][a-z0-9_.:-]{0,127}", value) is None:
        raise ValueError("invalid namespace")


class Phase(IntEnum):
    VALIDATE = 0
    PRE_TICK = 1
    RESOLVE = 2
    REACT = 3
    CASCADE = 4
    POST_TICK = 5
    COMMIT = 6
    PRESENT = 7


@dataclass(frozen=True, slots=True)
class TypeKey:
    kind: str
    version: int

    def __post_init__(self) -> None:
        if re.fullmatch(r"[a-z][a-z0-9_.-]{0,127}", self.kind) is None:
            raise ValueError("invalid kind")
        require_integer(self.version, 1, 2**31 - 1)


class FrozenPayload(ABC):
    __slots__ = ()

    @property
    @abstractmethod
    def schema(self) -> TypeKey: ...


@dataclass(frozen=True, slots=True)
class FieldFamily:
    component: str
    field: str


@dataclass(frozen=True, slots=True)
class FieldAddress:
    family: FieldFamily
    entity_id: EntityId


@dataclass(frozen=True, slots=True)
class ComponentAddress:
    schema: TypeKey
    entity_id: EntityId


StorageClass = Literal["CORE", "DERIVED"]
DeterminismTier = Literal["A", "B", "C"]


@dataclass(frozen=True, slots=True)
class FieldSpec:
    family: FieldFamily
    storage_class: StorageClass
    tier: DeterminismTier
    owner_id: str
    consumers: tuple[str, ...]
    value_kind: str
    unit: str
    scale: int
    minimum: int | None
    maximum: int | None
    collection_cap: int | None
