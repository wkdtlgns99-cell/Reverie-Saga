"""Quest commands,committed facts and family-confined patches."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Protocol

from contracts.messages import CommandPayload, FactPayload, PresentationPayload, StateDelta
from contracts.read_views import ComponentKey, ComponentPatch
from domain.primitives import EntityId, FieldAddress, FieldFamily, TypeKey
from domain.quest import QUEST_PROGRESS


class QuestRead(Protocol):
    @property
    def stage(self) -> int: ...


QUEST = ComponentKey[QuestRead](QUEST_PROGRESS)
STAGE_FAMILY = FieldFamily(QUEST_PROGRESS.kind, "stage")


class _Schema:
    __slots__ = ()
    SCHEMA: ClassVar[TypeKey]

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class QuestTalkCommand(_Schema, CommandPayload):
    SCHEMA: ClassVar[TypeKey] = TypeKey("quest.talk", 1)
    npc_id: EntityId


@dataclass(frozen=True, slots=True)
class QuestStageDelta(_Schema, StateDelta):
    SCHEMA: ClassVar[TypeKey] = TypeKey("quest.stage-delta", 1)
    entity_id: EntityId
    before_stage: int
    after_stage: int

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(STAGE_FAMILY, self.entity_id)


@dataclass(frozen=True, slots=True)
class QuestStagePatch(_Schema, ComponentPatch):
    SCHEMA: ClassVar[TypeKey] = TypeKey("quest.stage-patch", 1)
    stage: int


@dataclass(frozen=True, slots=True)
class QuestAccepted(_Schema, FactPayload):
    SCHEMA: ClassVar[TypeKey] = TypeKey("quest.accepted", 1)
    quest_id: str
    actor_id: EntityId
    npc_id: EntityId


@dataclass(frozen=True, slots=True)
class GoalMet(_Schema, FactPayload):
    SCHEMA: ClassVar[TypeKey] = TypeKey("quest.goal-met", 1)
    quest_id: str
    target_id: EntityId


@dataclass(frozen=True, slots=True)
class QuestCompleted(_Schema, FactPayload):
    SCHEMA: ClassVar[TypeKey] = TypeKey("quest.completed", 1)
    quest_id: str
    actor_id: EntityId
    npc_id: EntityId
    reward_id: str
    amount: int


@dataclass(frozen=True, slots=True)
class QuestSpoken(_Schema, FactPayload):
    SCHEMA: ClassVar[TypeKey] = TypeKey("quest.spoken", 1)
    quest_id: str
    npc_id: EntityId
    intent: str


@dataclass(frozen=True, slots=True)
class QuestCue(_Schema, PresentationPayload):
    SCHEMA: ClassVar[TypeKey] = TypeKey("quest.cue", 1)
    quest_id: str
    npc_id: EntityId
    intent: str


QUEST_PAYLOADS = (
    QuestTalkCommand,
    QuestStageDelta,
    QuestStagePatch,
    QuestAccepted,
    GoalMet,
    QuestCompleted,
    QuestSpoken,
    QuestCue,
)
