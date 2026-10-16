from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from typing import Callable, cast

import pytest

from app.npc_prepare import context_brief
from contracts.dialogue import GenerationError
from contracts.npc_context import MAX_CONTEXT_BYTES, KnownQuestPhase, NpcQuestContext
from domain.canonical import canonical_json


def context() -> NpcQuestContext:
    return NpcQuestContext(
        "w1-" + "a" * 64,
        "b" * 32,
        11,
        11,
        "c" * 64,
        "d" * 64,
        "actor:harbor-watcher",
        "actor:harbor-player",
        "quest:harbor-sentinel",
        "reported",
        1,
    )


@pytest.mark.parametrize(
    "factory",
    (
        lambda: replace(context(), world_id="a" * 64),
        lambda: replace(context(), branch_id="B" * 32),
        lambda: replace(context(), revision=True),
        lambda: replace(context(), tick=-1),
        lambda: replace(context(), core_hash="C" * 64),
        lambda: replace(context(), npc_id="quest:wrong"),
        lambda: replace(context(), quest_id="actor:wrong"),
        lambda: replace(context(), known_phase=cast(KnownQuestPhase, "defeated")),
        lambda: replace(context(), recorded_favor=True),
        lambda: replace(context(), recorded_favor=0),
    ),
)
def test_invalid_context_identity_types_and_knowledge(
    factory: Callable[[], NpcQuestContext],
) -> None:
    with pytest.raises(ValueError):
        factory()


def test_context_is_immutable_bounded_and_branch_bound() -> None:
    selected = context()
    with pytest.raises(FrozenInstanceError):
        setattr(selected, "tick", 12)
    assert len(canonical_json(selected.document())) <= MAX_CONTEXT_BYTES
    assert selected.sha256 != replace(selected, branch_id="e" * 32).sha256
    assert selected.sha256 != replace(selected, revision=12).sha256
    assert selected.document()["known_facts"] == (
        "quest_accepted",
        "completion_reported",
        "favor_recorded",
    )


def test_phase_requires_exact_string_and_cannot_claim_unreported_reward() -> None:
    class Text(str):
        pass

    with pytest.raises(ValueError, match="NPC_CONTEXT_PHASE"):
        replace(context(), known_phase=cast(KnownQuestPhase, Text("reported")))
    with pytest.raises(ValueError, match="NPC_CONTEXT_PHASE"):
        replace(context(), known_phase="accepted")


@pytest.mark.parametrize("subject", ("npc", "actor", "quest"))
def test_brief_rejects_other_entities_before_generation(subject: str) -> None:
    bad = (
        replace(context(), npc_id="actor:foreign")
        if subject == "npc"
        else replace(context(), actor_id="actor:foreign")
        if subject == "actor"
        else replace(context(), quest_id="quest:foreign")
    )
    with pytest.raises(GenerationError, match="NPC_CONTEXT_OWNER"):
        context_brief(bad)
