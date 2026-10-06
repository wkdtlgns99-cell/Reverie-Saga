from __future__ import annotations

from abc import ABC
from dataclasses import dataclass

from domain.primitives import ComponentAddress, EntityId, FrozenPayload, Tick, TypeKey, require_integer


class ComponentRecord(FrozenPayload, ABC):
    __slots__ = ()
    entity_id: EntityId


@dataclass(frozen=True, slots=True)
class StoredRoot:
    components: tuple[ComponentRecord, ...]
    root_token: int

    def __post_init__(self) -> None:
        require_integer(self.root_token)
        addresses = tuple(ComponentAddress(c.schema, c.entity_id) for c in self.components)
        if len(set(addresses)) != len(addresses):
            raise ValueError("duplicate component address")
        if self.components != tuple(sorted(
            self.components, key=lambda c: (c.schema.kind, c.schema.version, c.entity_id)
        )):
            raise ValueError("components must be canonically ordered")


@dataclass(frozen=True, slots=True)
class PositionRecord(ComponentRecord):
    entity_id: EntityId
    x: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("skeleton.position", 1)


@dataclass(frozen=True, slots=True)
class CounterRecord(ComponentRecord):
    entity_id: EntityId
    visits: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("skeleton.counter", 1)


@dataclass(frozen=True, slots=True)
class PackageDocument:
    package_id: str
    version: int
    sha256: str


@dataclass(frozen=True, slots=True)
class PendingDocument:
    canonical_event_json: bytes


@dataclass(frozen=True, slots=True)
class SimulationPins:
    schema_fingerprint: str
    rules_fingerprint: str
    schedule_fingerprint: str
    rng_version: str
    hash_version: str
    gameplay_catalog_hash: str
    gameplay_packages: tuple[PackageDocument, ...]


@dataclass(frozen=True, slots=True)
class CoreSnapshot:
    world_id: str
    world_seed_hex: str
    tick: Tick
    components: tuple[ComponentRecord, ...]
    pending: tuple[PendingDocument, ...]
    pins: SimulationPins
