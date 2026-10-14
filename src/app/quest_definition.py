"""First content policy instance;domain validates structure without importing app."""

from app.scenarios import select_scenario
from domain.quest import QuestDefinition


def harbor_definition() -> QuestDefinition:
    return QuestDefinition(select_scenario("harbor").layout, "quest:harbor-sentinel")
