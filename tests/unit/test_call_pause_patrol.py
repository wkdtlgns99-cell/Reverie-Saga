"""Call-response movement hold is opt-in with an isolated feature identity."""

from app.npc_cycle import cycle_bundle
from tests.integration.test_memory_client_route import approved_content

from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Iterator, cast

import pytest

from app.client_session import ClientSession
from app.client_worker import ClientWorker
from contracts.errors import CandidateError
from contracts.messages import EventHeader, WorldEvent
from contracts.read_views import AdapterBinding, ViewEpoch
from contracts.turn import EngineInvocation, PhaseAccess
from contracts.watch import NpcActed, WatchReplied, BellRung
from domain.npc_memory import NpcQuestMemoryRecord, QuestEvidence
from domain.primitives import EntityId, EventId, FieldFamily, MAX_INT, Phase, Tick, TypeKey
from domain.state_types import StoredRoot
from domain.trial import CellPositionRecord
from domain.watch import ECHO_DEPTH, ReplyRecord, WatchNpcRecord
from engines.watch import WatchNpc
from orchestration.npc_memory import MemoryAdapter
from orchestration.read_views import ObservedReadViewFactory
from orchestration.trial import CellPositionAdapter
from orchestration.turn import EmptyDefinitions, NoDrawRng
from orchestration.watch import ReplyAdapter, WatchNpcAdapter
from tests.unit.quest_fixtures import content
from tests.unit.test_talk_pause_patrol import spoken


def engine() -> WatchNpc:
    selected = content()
    return WatchNpc(
        selected.definition.layout,
        npc_patrol=True,
        talk_pause_quest=selected.definition.quest_id,
        quest_patrol=True,
        call_pause=True,
    )


def reply(at: int = 2) -> WorldEvent:
    payload = WatchReplied(content().definition.layout.npc_id, 0, 1)
    return WorldEvent(
        EventHeader(
            EventId("e1-" + "4" * 64),
            payload.schema,
            "watch.echo",
            Tick(at),
            Phase.CASCADE,
            ECHO_DEPTH,
            0,
            0,
            (EventId("e1-" + "3" * 64),),
            (),
        ),
        Tick(at),
        payload,
    )


def wake(at: int = 2) -> WorldEvent:
    payload = NpcActed(content().definition.layout.npc_id, at // 2 - 1, at // 2)
    return WorldEvent(
        EventHeader(
            EventId("e1-" + "2" * 64),
            payload.schema,
            "watch.npc",
            Tick(at),
            Phase.PRE_TICK,
            0,
            0,
            0,
            (EventId("e1-" + "1" * 64),),
            (),
        ),
        Tick(at),
        payload,
    )


@contextmanager
def observed(
    *,
    tick: int = 2,
    count: int = 1,
    current: int = 6,
    actor: int = 0,
    reply_count: int = 1,
    future: bool = False,
) -> Iterator[EngineInvocation]:
    selected = content()
    layout = selected.definition.layout
    entries = (
        QuestEvidence("accepted", 3 if future else 1, "e1-" + "5" * 64),
        QuestEvidence("completion_reported", 2, "e1-" + "6" * 64),
    )[:count]
    factory = ObservedReadViewFactory(
        StoredRoot(
            (
                NpcQuestMemoryRecord(layout.npc_id, entries),
                CellPositionRecord(layout.actor_id, layout.space_id, actor),
                WatchNpcRecord(layout.npc_id, layout.space_id, current, tick // 2),
                ReplyRecord(layout.npc_id, reply_count),
            ),
            0,
        )
    )
    AdapterBinding(MemoryAdapter(selected)).install(factory)
    AdapterBinding(CellPositionAdapter(layout)).install(factory)
    AdapterBinding(WatchNpcAdapter(layout, npc_patrol=True)).install(factory)
    AdapterBinding(ReplyAdapter(layout)).install(factory)
    epoch = ViewEpoch(Tick(tick), Phase.POST_TICK, 0, "watch.npc", 0)
    call = EngineInvocation(
        None,
        Tick(tick),
        Phase.POST_TICK,
        0,
        factory.open(epoch),
        EmptyDefinitions(),
        NoDrawRng(),
        (wake(tick),) if tick % 2 == 0 else (),
    )
    try:
        yield call
    finally:
        accesses = factory.close(epoch)
        assert all(access.operation != "write" for access in accesses)


@pytest.mark.parametrize("reverse", (False, True))
@pytest.mark.parametrize("count,current", ((0, 6), (1, 6), (1, 7), (2, 6), (2, 7)))
def test_answer_holds_existing_goal_in_either_source_order(
    reverse: bool,
    count: int,
    current: int,
) -> None:
    with observed(count=count, current=current) as call:
        sources = (*call.incoming, reply())
        held = engine().evaluate(
            replace(call, incoming=tuple(reversed(sources)) if reverse else sources)
        )
        assert held.deltas == () and held.facts == () and held.degraded == ()
        resumed = engine().evaluate(call)
        if count == 1 or count == 2 and current == 7:
            assert len(resumed.deltas) == len(resumed.facts) == 1
        else:
            assert resumed.deltas == () and resumed.facts == ()


def test_odd_answer_does_not_create_a_wake_or_saved_pause() -> None:
    with observed(tick=3) as call:
        result = engine().evaluate(replace(call, incoming=(reply(3),)))
        assert result.deltas == () and result.facts == () and result.degraded == ()
    with observed() as call:
        assert len(engine().evaluate(call).deltas) == 1


def test_manifest_and_bundle_register_only_new_reply_read_and_consumer() -> None:
    family = FieldFamily("watch.reply", "count")
    new = engine().manifest
    old = WatchNpc(
        content().definition.layout,
        npc_patrol=True,
        talk_pause_quest=content().definition.quest_id,
        quest_patrol=True,
    ).manifest
    access = PhaseAccess(Phase.POST_TICK, family)
    assert access in new.reads and access not in old.reads and access not in new.writes
    assert reply().payload.schema in new.consumes and reply().payload.schema not in old.consumes


@pytest.mark.parametrize(
    "damage",
    (
        "producer",
        "phase",
        "wave",
        "bool_wave",
        "sequence",
        "bool_sequence",
        "rank_bool",
        "rank_negative",
        "rank_large",
        "schema",
        "occurred",
        "due",
        "cause_empty",
        "cause_two",
        "npc",
        "before_negative",
        "before_bool",
        "before_max",
        "after_wrong",
        "after_bool",
        "after_large",
        "current_count",
        "duplicate_reply",
        "missing_even_wake",
        "odd_with_wake",
        "mixed_spoken",
        "unknown",
        "bad_wake",
        "invocation_wave",
        "invocation_bool_wave",
        "tick_zero",
        "tick_negative",
        "tick_bool",
        "tick_large",
        "empty",
    ),
)
def test_malformed_answer_never_becomes_an_ordinary_hold(damage: str) -> None:
    with observed(reply_count=2 if damage == "current_count" else 1) as call:
        event = reply()
        payload, header = event.payload, event.header
        assert isinstance(payload, WatchReplied)
        headers = {
            "producer": replace(header, producer_id="watch.npc"),
            "phase": replace(header, phase=Phase.RESOLVE),
            "wave": replace(header, wave=ECHO_DEPTH + 1),
            "bool_wave": replace(header, wave=True),
            "sequence": replace(header, sequence=1),
            "bool_sequence": replace(header, sequence=False),
            "rank_bool": replace(header, producer_rank=False),
            "rank_negative": replace(header, producer_rank=-1),
            "rank_large": replace(header, producer_rank=MAX_INT + 1),
            "schema": replace(header, type_key=TypeKey("watch.echo", 1)),
            "occurred": replace(header, occurred_at=Tick(3)),
            "cause_empty": replace(header, caused_by=()),
            "cause_two": replace(
                header, caused_by=(EventId("e1-" + "1" * 64), EventId("e1-" + "2" * 64))
            ),
        }
        if damage in headers:
            event = replace(event, header=headers[damage])
        payloads = {
            "npc": replace(payload, npc_id=EntityId("actor:other")),
            "before_negative": replace(payload, before_count=-1),
            "before_bool": replace(payload, before_count=False),
            "before_max": replace(payload, before_count=MAX_INT),
            "after_wrong": replace(payload, after_count=2),
            "after_bool": replace(payload, after_count=True),
            "after_large": replace(payload, after_count=MAX_INT + 1),
        }
        if damage in payloads:
            event = replace(event, payload=payloads[damage])
        if damage == "due":
            event = replace(event, due_tick=Tick(3))
        sources = (*call.incoming, event)
        if damage == "duplicate_reply":
            sources = (event, event)
        elif damage == "missing_even_wake":
            sources = (event,)
        elif damage == "odd_with_wake":
            call = replace(call, logical_tick=Tick(3))
            sources = (wake(3), reply(3))
        elif damage == "mixed_spoken":
            sources = (event, spoken())
        elif damage == "unknown":
            unknown = BellRung(
                content().definition.layout.actor_id, content().definition.layout.npc_id
            )
            sources = (
                replace(event, header=replace(header, type_key=unknown.schema), payload=unknown),
            )
        elif damage == "bad_wake":
            sources = (
                replace(
                    call.incoming[0],
                    header=replace(call.incoming[0].header, producer_id="watch.echo"),
                ),
                event,
            )
        elif damage in ("invocation_wave", "invocation_bool_wave"):
            call = replace(call, wave=1 if damage == "invocation_wave" else False)
        elif damage.startswith("tick_"):
            bad = {
                "tick_zero": 0,
                "tick_negative": -1,
                "tick_bool": True,
                "tick_large": MAX_INT + 1,
            }[damage]
            call = replace(call, logical_tick=cast(Tick, bad))
        elif damage == "empty":
            sources = ()
        with pytest.raises(CandidateError) as caught:
            engine().evaluate(replace(call, incoming=sources))
        assert caught.value.code == "INVALID_FACT"


@pytest.mark.parametrize("damage", ("future", "unheard_neighbor"))
def test_even_answer_does_not_hide_bad_memory_or_pose(damage: str) -> None:
    with observed(
        future=damage == "future",
        count=1 if damage == "future" else 0,
        current=7 if damage == "unheard_neighbor" else 6,
    ) as call:
        with pytest.raises(CandidateError) as caught:
            engine().evaluate(replace(call, incoming=(*call.incoming, reply())))
        assert caught.value.code == "INVALID_FACT"
        assert caught.value.detail == (
            "quest patrol future memory" if damage == "future" else "quest patrol unheard position"
        )


@pytest.mark.parametrize("bad", (None, 0, 1, "true"))
@pytest.mark.parametrize("target", ("bundle", "session", "worker"))
def test_invalid_selection_rejects_before_creating_resources(
    bad: object,
    target: str,
    tmp_path: Path,
) -> None:
    selected = approved_content()
    path = tmp_path / "absent/game.sqlite"
    with pytest.raises(ValueError, match="^NPC_CALL_PAUSE_CONTENT$"):
        if target == "bundle":
            cycle_bundle(selected, npc_call_pause=cast(bool, bad))
        elif target == "session":
            ClientSession(
                path,
                selected.definition.layout,
                quest_content=selected,
                npc_call_pause=cast(bool, bad),
            )
        else:
            ClientWorker(
                path,
                selected.definition.layout,
                quest_content=selected,
                npc_call_pause=cast(bool, bad),
            )
    assert not path.parent.exists()


@pytest.mark.parametrize("target", ("bundle", "session", "worker"))
def test_missing_immediate_parent_is_explicit_before_resources(target: str, tmp_path: Path) -> None:
    selected = approved_content()
    path = tmp_path / "absent/game.sqlite"
    with pytest.raises(ValueError, match="^NPC_CALL_PAUSE_CONTENT$"):
        if target == "bundle":
            cycle_bundle(selected, npc_call_pause=True)
        elif target == "session":
            ClientSession(
                path, selected.definition.layout, quest_content=selected, npc_call_pause=True
            )
        else:
            ClientWorker(
                path, selected.definition.layout, quest_content=selected, npc_call_pause=True
            )
    assert not path.parent.exists()


def test_explicit_call_pause_has_distinct_feature_identity() -> None:
    selected = cycle_bundle(
        approved_content(),
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
    )
    assert selected.feature_id == "quest.harbor-call-pause-v1"
