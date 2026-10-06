from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import cast, overload

from contracts.errors import (
    ExpiredReadView, InvalidViewEpoch, ReadOnlyViolation, UnknownComponent,
    UnknownEntity, ViewAlreadyClosed, ViewAlreadyOpen,
)
from contracts.read_views import (
    AccessObservation, AccessOperation, AccessPathSegment, ComponentKey, MappingPath,
    ReadAdapter, ReadPort, SequencePath, ViewEpoch,
)
from domain.primitives import (
    ComponentAddress, EntityId, FieldAddress, Phase, TypeKey, require_integer, require_namespace,
)
from domain.state_types import StoredRoot


@dataclass
class _Access:
    epoch: ViewEpoch
    active: bool = True
    observations: list[AccessObservation] = field(default_factory=list)
    cache: dict[FieldAddress, Sequence[str] | Mapping[str, int]] = field(default_factory=dict)

    def check(self) -> None:
        if not self.active:
            raise ExpiredReadView("closed invocation")

    def observe(self, target: FieldAddress, path: tuple[AccessPathSegment, ...],
                operation: AccessOperation) -> None:
        self.check()
        self.observations.append(AccessObservation(self.epoch, target, path, operation))

    def strings(self, target: FieldAddress, values: tuple[str, ...]) -> Sequence[str]:
        self.check()
        cached = self.cache.get(target)
        if cached is None:
            cached = _Strings(self, target, values, tuple(range(len(values))))
            self.cache[target] = cached
        if not isinstance(cached, _Strings):
            raise ValueError("conflicting adapter field")
        return cached

    def integers(self, target: FieldAddress, values: tuple[tuple[str, int], ...]) -> Mapping[str, int]:
        self.check()
        cached = self.cache.get(target)
        if cached is None:
            cached = _Integers(self, target, values)
            self.cache[target] = cached
        if not isinstance(cached, _Integers):
            raise ValueError("conflicting adapter field")
        return cached


class _Guard:
    __slots__ = ("_access", "_target")
    _access: _Access
    _target: FieldAddress

    def __setattr__(self, name: str, value: object) -> None:
        self._deny(())

    def __delattr__(self, name: str) -> None:
        self._deny(())

    def __getattr__(self, name: str) -> object:
        self._access.check()
        if name in ("append", "extend", "insert", "remove", "pop", "clear", "update", "setdefault"):
            self._deny(())
        raise AttributeError(name)

    def _deny(self, path: tuple[AccessPathSegment, ...]) -> None:
        self._access.observe(self._target, path, "write")
        raise ReadOnlyViolation("sealed view")


class _Strings(_Guard, Sequence[str]):
    __slots__ = ("_values", "_indices")

    def __init__(self, access: _Access, target: FieldAddress, values: tuple[str, ...],
                 indices: tuple[int, ...]) -> None:
        object.__setattr__(self, "_access", access)
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_values", values)
        object.__setattr__(self, "_indices", indices)
    _values: tuple[str, ...]
    _indices: tuple[int, ...]

    def __len__(self) -> int:
        self._access.observe(self._target, (), "length")
        return len(self._indices)

    @overload
    def __getitem__(self, index: int) -> str: ...
    @overload
    def __getitem__(self, index: slice[int | None, int | None, int | None]) -> Sequence[str]: ...
    def __getitem__(self, index: int | slice[int | None, int | None, int | None]) -> str | Sequence[str]:
        self._access.check()
        if isinstance(index, slice):
            selected = self._indices[index]
            self._access.observe(self._target, (), "iteration")
            for original in selected:
                self._access.observe(self._target, (SequencePath(original),), "read")
            return _Strings(self._access, self._target, self._values, selected)
        if type(index) is not int:
            raise TypeError("integer index required")
        normalized = index if index >= 0 else len(self._indices) + index
        path = (SequencePath(normalized),) if normalized >= 0 else ()
        if 0 <= normalized < len(self._indices):
            original = self._indices[normalized]
            self._access.observe(self._target, (SequencePath(original),), "read")
            return self._values[original]
        self._access.observe(self._target, path, "read")
        raise IndexError(index)

    def __iter__(self) -> Iterator[str]:
        self._access.observe(self._target, (), "iteration")
        return self._iterate()

    def _iterate(self) -> Iterator[str]:
        for index in self._indices:
            self._access.observe(self._target, (SequencePath(index),), "read")
            yield self._values[index]

    def __contains__(self, value: object) -> bool:
        self._access.observe(self._target, (), "membership")
        return any(self._values[i] == value for i in self._indices)

    def __setitem__(self, index: int, value: str) -> None:
        self._deny((SequencePath(index),) if index >= 0 else ())

    def __delitem__(self, index: int) -> None:
        self._deny((SequencePath(index),) if index >= 0 else ())


class _Integers(_Guard, Mapping[str, int]):
    __slots__ = ("_values",)
    _values: tuple[tuple[str, int], ...]

    def __init__(self, access: _Access, target: FieldAddress, values: tuple[tuple[str, int], ...]) -> None:
        object.__setattr__(self, "_access", access)
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_values", values)

    def __getitem__(self, key: str) -> int:
        self._access.check()
        if not isinstance(key, str):
            raise TypeError("string key required")
        self._access.observe(self._target, (MappingPath(key),), "read")
        for name, value in self._values:
            if name == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        self._access.observe(self._target, (), "iteration")
        return self._iterate()

    def _iterate(self) -> Iterator[str]:
        for name, _ in self._values:
            self._access.observe(self._target, (MappingPath(name),), "read")
            yield name

    def __len__(self) -> int:
        self._access.observe(self._target, (), "length")
        return len(self._values)

    def __contains__(self, key: object) -> bool:
        self._access.check()
        if not isinstance(key, str):
            raise TypeError("string key required")
        self._access.observe(self._target, (MappingPath(key),), "membership")
        return any(name == key for name, _ in self._values)

    def __setitem__(self, key: str, value: int) -> None:
        self._deny((MappingPath(key),))

    def __delitem__(self, key: str) -> None:
        self._deny((MappingPath(key),))


class ObservedReadViewFactory:
    def __init__(self, root: StoredRoot) -> None:
        self._root = root
        self._registry: dict[TypeKey, tuple[object, object]] = {}
        self._access: _Access | None = None
        self._closed: ViewEpoch | None = None
        self._frozen = False
        self._wrappers: dict[ComponentAddress, object] = {}

    def register[ReadT](self, adapter: ReadAdapter[ReadT]) -> None:
        if self._frozen or adapter.key.schema in self._registry:
            raise ValueError("registry frozen or duplicate schema")
        self._registry[adapter.key.schema] = (adapter.key, adapter)
        for record in self._root.components:
            if record.schema == adapter.key.schema:
                adapter.validate(record)

    def open(self, epoch: ViewEpoch) -> ReadPort:
        try:
            require_integer(epoch.logical_tick)
            require_integer(epoch.root_token)
            require_namespace(epoch.engine_id)
            require_integer(epoch.wave, 0, 7 if epoch.phase == Phase.CASCADE else 0)
        except ValueError as error:
            raise InvalidViewEpoch("invalid epoch values") from error
        if not isinstance(epoch.phase, Phase) or epoch.phase == Phase.COMMIT:
            raise InvalidViewEpoch("invalid read phase")
        if epoch.root_token != self._root.root_token:
            raise InvalidViewEpoch("wrong root pin")
        if self._closed is not None:
            if epoch == self._closed:
                raise ViewAlreadyClosed("closed epoch")
            raise InvalidViewEpoch("factory is invocation-local")
        if self._access is not None:
            raise ViewAlreadyOpen("active epoch")
        if any(c.schema not in self._registry for c in self._root.components):
            raise UnknownComponent("unregistered backing")
        self._frozen = True
        self._access = _Access(epoch)
        return _Port(self)

    def close(self, epoch: ViewEpoch) -> tuple[AccessObservation, ...]:
        if epoch == self._closed:
            raise ViewAlreadyClosed("closed epoch")
        if self._access is None or self._access.epoch != epoch:
            raise InvalidViewEpoch("not the active epoch")
        self._access.active = False
        result = tuple(self._access.observations)
        self._closed = epoch
        self._access = None
        self._wrappers.clear()
        return result

    def _component[ReadT](self, key: ComponentKey[ReadT], entity_id: EntityId) -> ReadT:
        access = self._access
        if access is None:
            raise ExpiredReadView("closed port")
        access.check()
        entry = self._registry.get(key.schema)
        if entry is None or entry[0] is not key:
            raise UnknownComponent(key.schema.kind)
        adapter = cast(ReadAdapter[ReadT], entry[1])
        address = ComponentAddress(key.schema, entity_id)
        for record in self._root.components:
            if record.schema == key.schema and record.entity_id == entity_id:
                adapter.validate(record)
                cached = self._wrappers.get(address)
                if cached is None:
                    cached = adapter.wrap(record, access)
                    self._wrappers[address] = cached
                return cast(ReadT, cached)
        raise UnknownEntity(entity_id)


class _Port:
    def __init__(self, factory: ObservedReadViewFactory) -> None:
        self._factory = factory

    def component[ReadT](self, key: ComponentKey[ReadT], entity_id: EntityId) -> ReadT:
        return self._factory._component(key, entity_id)
