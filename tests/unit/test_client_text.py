from __future__ import annotations

import pytest

from app.client_text import fact_messages, npc_activity_text, status_text, turn_messages
from contracts.client import ClientView
from contracts.encounter import AttackResolved, Defeated, EncounterMoveBlocked, GateChanged, Rested
from contracts.messages import EventHeader, WorldEvent
from contracts.trial import Moved
from contracts.turn import TurnAborted, TurnPublication, failure
from domain.encounter import ATTACK_PROFILE_ID, ENEMY_ID, GATE_ID
from domain.primitives import EntityId, EventId, Phase, Tick
from domain.trial import ACTOR_ID, SPACE_ID


@pytest.mark.parametrize(
    "tick,bells,replies,expected",
    (
        (0, 0, 0, "NPC 활동 현황 · 0초 · 종 0회 · 호출 응답 0회."),
        (27, 13, 7, "NPC 활동 현황 · 27초 · 종 13회 · 호출 응답 7회."),
    ),
)
def test_npc_activity_formats_supplied_committed_values(
    tick: int, bells: int, replies: int, expected: str
) -> None:
    view = ClientView(3, 3, (), 3, 4, True, 8, 1, 0, 0, 6, bells, replies, 3, tick, 12)
    assert npc_activity_text(view) == expected


@pytest.mark.parametrize(
    ("target_before", "target_after", "actor_before", "actor_after", "expected"),
    [
        (5, 3, 3, 2, ("피해 2", "반격, 피해 1")),
        (1, 0, 1, 1, ("피해 1",)),
    ],
    ids=["attack-and-counter", "finishing-blow-no-counter"],
)
def test_attack_text_uses_actual_committed_values(
    target_before: int,
    target_after: int,
    actor_before: int,
    actor_after: int,
    expected: tuple[str, ...],
) -> None:
    payload = AttackResolved(
        ACTOR_ID,
        ENEMY_ID,
        ATTACK_PROFILE_ID,
        actor_before,
        actor_after,
        target_before,
        target_after,
        2,
        1,
    )
    text = "\n".join(fact_messages(payload))
    assert "플레이어 → 적: 공격" in text
    assert all(part in text for part in expected)
    assert "스태미나 2 → 1" in text
    assert ("반격" in text) == (actor_before != actor_after)


@pytest.mark.parametrize("reason", ["boundary", "wall", "door", "occupied"])
def test_blocked_move_has_specific_reason(reason: str) -> None:
    reasons = {"boundary": "맵 경계", "wall": "벽", "door": "닫힌 문", "occupied": "적"}
    # Parameter values are runtime checked rather than weakening the payload's Literal type.
    payloads = (
        EncounterMoveBlocked(ACTOR_ID, SPACE_ID, 0, 1, 0, "boundary"),
        EncounterMoveBlocked(ACTOR_ID, SPACE_ID, 0, 1, 0, "wall"),
        EncounterMoveBlocked(ACTOR_ID, SPACE_ID, 0, 1, 0, "door"),
        EncounterMoveBlocked(ACTOR_ID, SPACE_ID, 0, 1, 0, "occupied"),
    )
    payload = next(p for p in payloads if p.reason == reason)
    assert reasons[reason] in fact_messages(payload)[0]


def test_noop_text_does_not_claim_resource_change() -> None:
    assert "이미 열려" in fact_messages(GateChanged(ACTOR_ID, GATE_ID, 1, 1))[0]
    assert "변하지 않았" in fact_messages(Rested(ACTOR_ID, 2, 2))[0]
    assert "쓰러졌" in fact_messages(Defeated(ENEMY_ID, ACTOR_ID))[0]


@pytest.mark.parametrize("code", ["OUT_OF_RANGE", "INSUFFICIENT_STAMINA", "SAVE_UNCERTAIN"])
def test_aborted_turn_explains_failure_without_success(code: str) -> None:
    publication = TurnPublication(TurnAborted(failure(code)), (), None, (), ())
    assert turn_messages(publication) == (status_text(code),)
    assert "공격," not in turn_messages(publication)[0]


def test_unknown_status_retains_diagnostic_identity() -> None:
    assert "NEW_STATUS" in status_text("NEW_STATUS")
    payload = Defeated(EntityId("actor:unknown"), ACTOR_ID)
    assert "actor:unknown" in fact_messages(payload)[0]


def test_aborted_publication_does_not_narrate_supplied_success_fact() -> None:
    payload = Defeated(ENEMY_ID, ACTOR_ID)
    event = WorldEvent(
        EventHeader(
            EventId("event:test"),
            payload.schema,
            "encounter.actions",
            Tick(1),
            Phase.RESOLVE,
            0,
            0,
            0,
            (),
            (),
        ),
        Tick(1),
        payload,
    )
    publication = TurnPublication(TurnAborted(failure("SAVE_UNAVAILABLE")), (event,), None, (), ())
    assert turn_messages(publication) == (status_text("SAVE_UNAVAILABLE"),)
    assert "쓰러졌" not in turn_messages(publication)[0]


def test_unhandled_fact_remains_visible_without_invented_description() -> None:
    messages = fact_messages(Moved(ACTOR_ID, SPACE_ID, 0, 3))
    assert messages == ("설명이 준비되지 않은 사건입니다. (trial.moved)",)
