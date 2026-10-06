from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol
import unicodedata

from contracts.errors import ReadOnlyViolation
from contracts.read_views import ComponentKey, ReadAdapter, ViewAccess, ViewEpoch
from domain.primitives import EntityId, FieldAddress, FieldFamily, Phase, Tick, TypeKey, require_integer
from domain.state_types import ComponentRecord, StoredRoot
from orchestration.read_views import ObservedReadViewFactory

ACTOR = EntityId("actor:toy")


class EntityProfileRead(Protocol):
    @property
    def entity_id(self) -> EntityId: ...
    @property
    def traits(self) -> Sequence[str]: ...


class PhysiologyRead(Protocol):
    @property
    def hp(self) -> int: ...
    @property
    def reserves(self) -> Mapping[str, int]: ...


PROFILE = ComponentKey[EntityProfileRead](TypeKey("fixture.profile", 1))
PHYSIOLOGY = ComponentKey[PhysiologyRead](TypeKey("fixture.physiology", 1))


@dataclass(frozen=True, slots=True)
class ProfileRecord(ComponentRecord):
    entity_id: EntityId
    traits: tuple[str, ...]

    @property
    def schema(self) -> TypeKey:
        return PROFILE.schema


@dataclass(frozen=True, slots=True)
class PhysiologyRecord(ComponentRecord):
    entity_id: EntityId
    hp: int
    reserves: tuple[tuple[str, int], ...]

    @property
    def schema(self) -> TypeKey:
        return PHYSIOLOGY.schema


class _View:
    def __init__(self, record: ProfileRecord | PhysiologyRecord, access: ViewAccess) -> None:
        object.__setattr__(self, "_record", record)
        object.__setattr__(self, "_access", access)
    _record: ProfileRecord | PhysiologyRecord
    _access: ViewAccess

    def __setattr__(self, name: str, value: object) -> None:
        self._access.observe(self._target(name), (), "write")
        raise ReadOnlyViolation(name)

    def __delattr__(self, name: str) -> None:
        self.__setattr__(name, None)

    def _target(self, name: str) -> FieldAddress:
        return FieldAddress(FieldFamily(self._record.schema.kind, name), self._record.entity_id)


class _Profile(_View):
    @property
    def entity_id(self) -> EntityId:
        self._access.observe(self._target("entity_id"), (), "read")
        return self._record.entity_id

    @property
    def traits(self) -> Sequence[str]:
        assert isinstance(self._record, ProfileRecord)
        self._access.observe(self._target("traits"), (), "read")
        return self._access.strings(self._target("traits"), self._record.traits)


class _Physiology(_View):
    @property
    def hp(self) -> int:
        assert isinstance(self._record, PhysiologyRecord)
        self._access.observe(self._target("hp"), (), "read")
        return self._record.hp

    @property
    def reserves(self) -> Mapping[str, int]:
        assert isinstance(self._record, PhysiologyRecord)
        self._access.observe(self._target("reserves"), (), "read")
        return self._access.integers(self._target("reserves"), self._record.reserves)


class ProfileAdapter(ReadAdapter[EntityProfileRead]):
    @property
    def key(self) -> ComponentKey[EntityProfileRead]:
        return PROFILE

    def validate(self, record: ComponentRecord) -> None:
        if not isinstance(record, ProfileRecord) or type(record.traits) is not tuple:
            raise ValueError("invalid profile")
        if len(record.traits) > 64 or any(
            not isinstance(t, str) or unicodedata.normalize("NFC", t) != t for t in record.traits
        ):
            raise ValueError("invalid traits")

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> EntityProfileRead:
        self.validate(record)
        assert isinstance(record, ProfileRecord)
        return _Profile(record, access)


class PhysiologyAdapter(ReadAdapter[PhysiologyRead]):
    @property
    def key(self) -> ComponentKey[PhysiologyRead]:
        return PHYSIOLOGY

    def validate(self, record: ComponentRecord) -> None:
        if not isinstance(record, PhysiologyRecord) or type(record.reserves) is not tuple:
            raise ValueError("invalid physiology")
        require_integer(record.hp)
        if len(record.reserves) > 64 or record.reserves != tuple(sorted(record.reserves)):
            raise ValueError("invalid reserves")
        if len({k for k, _ in record.reserves}) != len(record.reserves):
            raise ValueError("duplicate keys")
        for key, value in record.reserves:
            if not isinstance(key, str) or unicodedata.normalize("NFC", key) != key:
                raise ValueError("invalid key")
            require_integer(value)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> PhysiologyRead:
        self.validate(record)
        assert isinstance(record, PhysiologyRecord)
        return _Physiology(record, access)


def fixture(traits: tuple[str, ...] = ("quiet", "alert"),
            reserves: tuple[tuple[str, int], ...] = (("food", 7),)
            ) -> tuple[ObservedReadViewFactory, ViewEpoch, StoredRoot]:
    root = StoredRoot((PhysiologyRecord(ACTOR, 10, reserves), ProfileRecord(ACTOR, traits)), 1)
    factory = ObservedReadViewFactory(root)
    factory.register(PhysiologyAdapter())
    factory.register(ProfileAdapter())
    return factory, ViewEpoch(Tick(0), Phase.RESOLVE, 0, "fixture.engine", 1), root
