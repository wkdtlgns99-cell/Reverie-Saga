"""Bounded quest structure;world policy and content creation belong above domain."""

from __future__ import annotations

from dataclasses import dataclass

from domain.primitives import EntityId, TypeKey, require_integer, require_namespace
from domain.scenario import Scenario
from domain.state_types import ComponentRecord

QUEST_PROGRESS = TypeKey("quest.progress", 1)
SINGLE_STEPS = frozenset(((0, 1), (1, 2), (2, 3)))
NET_STEPS = SINGLE_STEPS | {(0, 2)}


@dataclass(frozen=True, slots=True)
class QuestDefinition:
    layout: Scenario
    quest_id: str
    reward_id: str = "favor:harbor-watch"
    reward_amount: int = 1

    def __post_init__(self) -> None:
        if type(self.layout) is not Scenario:
            raise ValueError("QUEST_DEFINITION")
        for value, prefix in ((self.quest_id, "quest:"), (self.reward_id, "favor:")):
            if type(value) is not str or not value.startswith(prefix):
                raise ValueError("QUEST_DEFINITION")
            require_namespace(value)
        if type(self.reward_amount) is not int or self.reward_amount != 1:
            raise ValueError("QUEST_DEFINITION")


@dataclass(frozen=True, slots=True)
class QuestRecord(ComponentRecord):
    entity_id: EntityId
    stage: int

    @property
    def schema(self) -> TypeKey:
        return QUEST_PROGRESS

    def __post_init__(self) -> None:
        if type(self.entity_id) is not str or not self.entity_id.startswith("quest:"):
            raise ValueError("QUEST_RECORD")
        require_namespace(self.entity_id)
        require_integer(self.stage, 0, 3)


def reward_for(stage: int) -> int:
    require_integer(stage, 0, 3)
    return 1 if stage == 3 else 0
