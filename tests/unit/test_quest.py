from __future__ import annotations

from dataclasses import replace

import pytest

from app.headless import state_io
from app.quest import bootstrap_quest
from app.quest_registry import quest_bundle
from app.watch import WatchBootstrapSpec
from contracts.errors import BootstrapError, CandidateError
from contracts.quest import QuestStageDelta, QuestTalkCommand
from contracts.turn import GameCommand, TurnRejected
from domain.primitives import CommandId, EntityId
from domain.quest import QuestRecord
from engines.quest import QuestRules
from orchestration.quest import QuestPayloadCodec, QuestReducer
from tests.unit.quest_fixtures import content


@pytest.mark.parametrize("bad", (True, 1.0, -1, 4))
def test_exact_stage_and_bounds(bad: object) -> None:
    from typing import cast

    with pytest.raises(ValueError):
        QuestRecord(EntityId("quest:harbor-sentinel"), cast(int, bad))


@pytest.mark.parametrize("before,after", ((0, 3), (1, 3), (2, 1), (1, 1)))
def test_forged_persisted_net_diff_rejected(before: int, after: int) -> None:
    from contracts.read_views import ReadPort, ViewEpoch
    from domain.primitives import Phase, Tick
    from domain.state_types import StoredRoot
    from orchestration.read_views import ObservedReadViewFactory
    from contracts.read_views import AdapterBinding
    from orchestration.quest import QuestAdapter

    selected = content()
    reducer = QuestReducer(selected)
    factory = ObservedReadViewFactory(
        StoredRoot((QuestRecord(EntityId(selected.definition.quest_id), after),), 0)
    )
    AdapterBinding(QuestAdapter(selected)).install(factory)
    epoch = ViewEpoch(Tick(1), Phase.PRESENT, 0, "test", 0)
    port: ReadPort = factory.open(epoch)
    try:
        with pytest.raises(CandidateError, match="INVALID_DELTA"):
            reducer.validate_net(
                QuestStageDelta(EntityId(selected.definition.quest_id), before, after), port
            )
    finally:
        factory.close(epoch)


def test_net_codec_accepts_composed_step_but_stager_does_not() -> None:
    selected = content()
    reducer = QuestReducer(selected)
    entity = EntityId(selected.definition.quest_id)
    result = reducer.compose((QuestStageDelta(entity, 0, 1), QuestStageDelta(entity, 1, 2)))
    assert result == QuestStageDelta(entity, 0, 2)
    assert QuestPayloadCodec(result.schema, selected).encode(result)["after_stage"] == 2
    with pytest.raises(CandidateError, match="INVALID_DELTA"):
        reducer.compose((result,))


def test_skipped_constructor_rejected_before_scenario_guard() -> None:
    class Uninitialized(QuestRules):
        def __init__(self) -> None:
            pass

    bundle = quest_bundle(content())
    bundle = replace(
        bundle,
        bindings=(*bundle.bindings[:-1], replace(bundle.bindings[-1], engine=Uninitialized())),
    )
    with pytest.raises(BootstrapError, match="INVALID_QUEST_BINDING"):
        state_io((bundle,))


@pytest.mark.parametrize("consumer", ("honest", "mismatched", "uninitialized"))
def test_quest_declaration_cannot_be_removed_to_bypass_binding(consumer: str) -> None:
    from orchestration.quest import QuestPresenter

    bundle = quest_bundle(content())
    rules = dict(bundle.rules_document)
    del rules["quest"]
    bundle = replace(bundle, rules_document=rules)
    if consumer == "mismatched":
        selected = content()
        different = replace(
            selected,
            dialogue=replace(
                selected.dialogue,
                lines=(
                    replace(selected.dialogue.lines[0], text_ko="다른 승인 대사"),
                    *selected.dialogue.lines[1:],
                ),
            ),
        )
        bundle = replace(
            bundle,
            presenters=(
                *bundle.presenters[:-1],
                replace(bundle.presenters[-1], presenter=QuestPresenter(different)),
            ),
        )
    elif consumer == "uninitialized":

        class Uninitialized(QuestRules):
            def __init__(self) -> None:
                pass

        bundle = replace(
            bundle,
            bindings=(
                *bundle.bindings[:-1],
                replace(bundle.bindings[-1], engine=Uninitialized()),
            ),
        )
    with pytest.raises(BootstrapError, match="INVALID_QUEST_BINDING"):
        state_io((bundle,))


def test_quest_declaration_without_quest_registrations_is_rejected() -> None:
    from app.watch_registry import watch_bundle

    bundle = watch_bundle()
    rules = dict(bundle.rules_document)
    rules["quest"] = quest_bundle(content()).rules_document["quest"]
    with pytest.raises(BootstrapError, match="INVALID_QUEST_BINDING"):
        state_io((replace(bundle, rules_document=rules),))


@pytest.mark.parametrize(
    "dead,actor,npc,code",
    (
        (True, "actor:foreign", "actor:foreign-npc", "UNAUTHORIZED_ACTOR"),
        (True, "actor:harbor-player", "actor:foreign-npc", "ACTOR_DEFEATED"),
        (False, "actor:harbor-player", "actor:foreign-npc", "INVALID_TARGET"),
        (False, "actor:harbor-player", "actor:harbor-watcher", "OUT_OF_RANGE"),
    ),
)
def test_admission_precedence_preserves_state(dead: bool, actor: str, npc: str, code: str) -> None:
    selected = content()
    live = bootstrap_quest(
        WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32, actor_hp=0 if dead else 3), selected
    )
    original = live.snapshot(), live.protocol()
    outcome = live.driver.submit(
        GameCommand(
            CommandId(f"c1:{'0' * 32}:{'1' * 32}:1"),
            EntityId(actor),
            live.protocol().revision,
            QuestTalkCommand(EntityId(npc)),
        )
    )
    assert isinstance(outcome, TurnRejected) and outcome.failure.code == code
    assert (live.snapshot(), live.protocol()) == original
