"""Typed social identity/actions and single-owner reputation changes."""

from dataclasses import dataclass
from typing import Protocol

from contracts.messages import CommandPayload, StateDelta
from contracts.read_views import ComponentKey, ComponentPatch
from domain.primitives import EntityId, FieldAddress, FieldFamily, TypeKey
from domain.world_social import SOCIAL_SCHEMA, SocialState

SOCIAL_OWNER = "world.social"
SOCIAL_FAMILY = FieldFamily(SOCIAL_SCHEMA.kind, "state")


class SocialRead(Protocol):
    @property
    def state(self) -> SocialState: ...


SOCIAL = ComponentKey[SocialRead](SOCIAL_SCHEMA)


@dataclass(frozen=True, slots=True)
class SocialAction(CommandPayload):
    operation: str
    ancestry_id: str = ""
    country_id: str = ""
    SCHEMA = TypeKey("world.social-action", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class SocialDelta(StateDelta):
    entity_id: EntityId
    before: SocialState
    after: SocialState
    SCHEMA = TypeKey("world.social-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(SOCIAL_FAMILY, self.entity_id)


@dataclass(frozen=True, slots=True)
class SocialPatch(ComponentPatch):
    state: SocialState
    SCHEMA = TypeKey("world.social-patch", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


SOCIAL_PAYLOADS = (SocialAction, SocialDelta, SocialPatch)
