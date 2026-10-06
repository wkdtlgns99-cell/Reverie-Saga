from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from contracts.messages import (
    CommandPayload, EventPolicy, FactPayload, Presenter, PresentationPayload, StateDelta,
)
from contracts.read_views import ComponentKey, ComponentPatch, ReadPort, ReadRegistration, StagingEditor
from contracts.turn import AdmissionOutcome, EngineBinding, GameCommand
from contracts.state_io import CheckpointPolicy, ComponentCodec, PatchRoute
from domain.canonical import JsonObject
from domain.primitives import EntityId, FieldAddress, FieldFamily, FieldSpec, FrozenPayload, Tick, TypeKey


class PositionRead(Protocol):
    @property
    def x(self) -> int: ...


class CounterRead(Protocol):
    @property
    def visits(self) -> int: ...


POSITION = ComponentKey[PositionRead](TypeKey("skeleton.position", 1))
COUNTER = ComponentKey[CounterRead](TypeKey("skeleton.counter", 1))


@dataclass(frozen=True, slots=True)
class StepCommand(CommandPayload):
    dx: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("skeleton.step", 1)


@dataclass(frozen=True, slots=True)
class Stepped(FactPayload):
    from_x: int
    to_x: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("skeleton.stepped", 1)


@dataclass(frozen=True, slots=True)
class PositionDelta(StateDelta):
    entity_id: EntityId
    expected_old: int
    new: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("skeleton.position-delta", 1)

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(FieldFamily(POSITION.schema.kind, "x"), self.entity_id)


@dataclass(frozen=True, slots=True)
class CounterDelta(StateDelta):
    entity_id: EntityId
    expected_old: int
    new: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("skeleton.counter-delta", 1)

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(FieldFamily(COUNTER.schema.kind, "visits"), self.entity_id)


@dataclass(frozen=True, slots=True)
class StepCue(PresentationPayload):
    actor_id: EntityId
    from_x: int
    to_x: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("skeleton.step-cue", 1)


@dataclass(frozen=True, slots=True)
class PositionPatch(ComponentPatch):
    x: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("skeleton.position-patch", 1)


@dataclass(frozen=True, slots=True)
class CounterPatch(ComponentPatch):
    visits: int

    @property
    def schema(self) -> TypeKey:
        return TypeKey("skeleton.counter-patch", 1)


class CommandRoute(Protocol):
    @property
    def schema(self) -> TypeKey: ...
    @property
    def reads(self) -> tuple[FieldFamily, ...]: ...
    def admit(self, command: GameCommand, state: ReadPort, *,
              start_tick: Tick, world_id: str) -> AdmissionOutcome: ...


class DeltaRoute(Protocol):
    @property
    def schema(self) -> TypeKey: ...
    @property
    def owner_id(self) -> str: ...
    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None: ...
    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta: ...
    def is_identity(self, delta: StateDelta) -> bool: ...
    def validate_net(self, delta: StateDelta, after: ReadPort) -> None: ...


class PayloadCodec(Protocol):
    @property
    def schema(self) -> TypeKey: ...
    def decode(self, data: JsonObject) -> FrozenPayload: ...
    def encode(self, payload: FrozenPayload) -> JsonObject: ...


@dataclass(frozen=True, slots=True)
class PresenterBinding:
    presenter_id: str
    kinds: tuple[TypeKey, ...]
    presenter: Presenter


@dataclass(frozen=True, slots=True)
class FeatureBundle:
    feature_id: str
    bindings: tuple[EngineBinding, ...]
    read_adapters: tuple[ReadRegistration, ...]
    field_specs: tuple[FieldSpec, ...]
    events: tuple[EventPolicy, ...]
    command_routes: tuple[CommandRoute, ...]
    delta_routes: tuple[DeltaRoute, ...]
    presenters: tuple[PresenterBinding, ...]
    codecs: tuple[PayloadCodec, ...]
    schema_document: JsonObject
    rules_document: JsonObject
    component_codecs: tuple[ComponentCodec, ...]
    patch_routes: tuple[PatchRoute, ...]
    checkpoint_policy: CheckpointPolicy
