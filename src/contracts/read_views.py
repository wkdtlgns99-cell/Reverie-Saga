from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol, TYPE_CHECKING
from abc import ABC

from domain.primitives import ComponentAddress, EntityId, FieldAddress, FrozenPayload, Phase, Tick, TypeKey
from domain.state_types import ComponentRecord
if TYPE_CHECKING:
    from contracts.messages import StateDelta


@dataclass(frozen=True, slots=True)
class ComponentKey[ReadT]:
    schema: TypeKey


class ReadPort(Protocol):
    def component[ReadT](self, key: ComponentKey[ReadT], entity_id: EntityId) -> ReadT: ...


@dataclass(frozen=True, slots=True)
class ViewEpoch:
    logical_tick: Tick
    phase: Phase
    wave: int
    engine_id: str
    root_token: int


@dataclass(frozen=True, slots=True)
class AttributePath:
    name: str


@dataclass(frozen=True, slots=True)
class MappingPath:
    key: str


@dataclass(frozen=True, slots=True)
class SequencePath:
    index: int


type AccessPathSegment = AttributePath | MappingPath | SequencePath
type AccessOperation = Literal["read", "membership", "length", "iteration", "write"]


@dataclass(frozen=True, slots=True)
class AccessObservation:
    epoch: ViewEpoch
    target: FieldAddress
    path: tuple[AccessPathSegment, ...]
    operation: AccessOperation


class ViewAccess(Protocol):
    def check(self) -> None: ...
    def observe(self, target: FieldAddress, path: tuple[AccessPathSegment, ...],
                operation: AccessOperation) -> None: ...
    def strings(self, target: FieldAddress, values: tuple[str, ...]) -> Sequence[str]: ...
    def integers(self, target: FieldAddress,
                 values: tuple[tuple[str, int], ...]) -> Mapping[str, int]: ...


class ReadAdapter[ReadT](Protocol):
    @property
    def key(self) -> ComponentKey[ReadT]: ...
    def validate(self, record: ComponentRecord) -> None: ...
    def wrap(self, record: ComponentRecord, access: ViewAccess) -> ReadT: ...


class ReadViewFactory(Protocol):
    def open(self, epoch: ViewEpoch) -> ReadPort: ...
    def close(self, epoch: ViewEpoch) -> tuple[AccessObservation, ...]: ...


class ReadAdapterRegistry(Protocol):
    def register[ReadT](self, adapter: ReadAdapter[ReadT]) -> None: ...


class ReadRegistration(Protocol):
    @property
    def schema(self) -> TypeKey: ...
    def install(self, registry: ReadAdapterRegistry) -> None: ...


@dataclass(frozen=True, slots=True)
class AdapterBinding[ReadT]:
    adapter: ReadAdapter[ReadT]

    @property
    def schema(self) -> TypeKey:
        return self.adapter.key.schema

    def install(self, registry: ReadAdapterRegistry) -> None:
        registry.register(self.adapter)


class ComponentPatch(FrozenPayload, ABC):
    __slots__ = ()


class StagingEditor(Protocol):
    def apply_patch(self, address: ComponentAddress, patch: ComponentPatch) -> None: ...


class DeltaReducer[DeltaT: StateDelta](Protocol):
    def stage(self, delta: DeltaT, before: ReadPort, editor: StagingEditor) -> None: ...
    def compose(self, changes: tuple[DeltaT, ...]) -> DeltaT: ...
