"""Harbor policy factory and bootstrap using the existing watch initialization."""

from __future__ import annotations

from pathlib import Path
from adapters.quest_dialogue import load_dialogue

from app.headless import HeadlessSession
from app.quest_definition import harbor_definition as harbor_definition
from app.watch import WatchBootstrapSpec, _bootstrap
from contracts.dialogue import QuestContent
from domain.primitives import EntityId
from domain.quest import QuestRecord
from domain.scenario import Scenario


def client_quest(layout: Scenario, path: Path | None, digest: str | None) -> QuestContent | None:
    if path is None and digest is None:
        return None
    if path is None or digest is None or layout != harbor_definition().layout:
        raise ValueError("QUEST_CONTENT_UNAVAILABLE")
    return load_dialogue(path, digest, harbor_definition())


def bootstrap_quest(spec: WatchBootstrapSpec, content: QuestContent) -> HeadlessSession:
    from app.quest_registry import quest_bundle

    bundle = quest_bundle(content)
    return _bootstrap(
        spec,
        None,
        content.definition.layout,
        bundle=bundle,
        extra_records=(QuestRecord(EntityId(content.definition.quest_id), 0),),
    )[0]
