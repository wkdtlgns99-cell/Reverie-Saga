"""Actual conversation source guards and unchanged wake/path authority."""

from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from app.client_session import ClientSession
from app.client_worker import ClientWorker
from app.npc_cycle import cycle_bundle
from contracts.errors import CandidateError
from contracts.messages import EventHeader, WorldEvent
from contracts.npc_patrol import NpcPatrolled
from contracts.quest import QuestSpoken
from contracts.watch import BellRung
from domain.primitives import EntityId, EventId, Phase, Tick, TypeKey
from engines.watch import WatchNpc
from tests.unit.quest_fixtures import content
from tests.unit.test_npc_patrol import invocation
from tests.integration.test_memory_client_route import approved_content


def spoken(intent: str = "offer", at: int = 2) -> WorldEvent:
    layout = content().definition.layout
    payload = QuestSpoken(content().definition.quest_id, layout.npc_id, intent)
    sequence = {"offer": 1, "completion": 1, "reminder": 0, "gratitude": 0}[intent]
    return WorldEvent(
        EventHeader(
            EventId("e1-" + "4" * 64),
            payload.schema,
            "quest.rules",
            Tick(at),
            Phase.RESOLVE,
            0,
            2,
            sequence,
            (),
            (),
        ),
        Tick(at),
        payload,
    )


def engine() -> WatchNpc:
    selected = content()
    return WatchNpc(
        selected.definition.layout, npc_patrol=True, talk_pause_quest=selected.definition.quest_id
    )


@pytest.mark.parametrize("intent", ("offer", "reminder", "completion", "gratitude"))
@pytest.mark.parametrize("reverse", (False, True))
def test_actual_spoken_and_wake_hold_in_either_input_order(intent: str, reverse: bool) -> None:
    call = invocation(actor=0)
    facts = (call.incoming[0], spoken(intent))
    result = engine().evaluate(replace(call, incoming=tuple(reversed(facts)) if reverse else facts))
    assert result.deltas == () and result.facts == () and result.degraded == ()
    # No lasting pause:the same actual wake alone still decides from its real cell.
    resumed = engine().evaluate(call)
    assert len(resumed.facts) == 1 and type(resumed.facts[0].payload) is NpcPatrolled


@pytest.mark.parametrize("intent", ("offer", "reminder", "completion", "gratitude"))
def test_odd_spoken_validates_without_inventing_a_wake(intent: str) -> None:
    call = invocation()
    result = engine().evaluate(replace(call, logical_tick=Tick(3), incoming=(spoken(intent, 3),)))
    assert result.deltas == () and result.facts == ()


@pytest.mark.parametrize(
    "damage",
    (
        "quest",
        "npc",
        "intent",
        "producer",
        "phase",
        "wave",
        "bool_wave",
        "sequence",
        "bool_sequence",
        "schema",
        "occurred",
        "due",
        "cause",
        "duplicate_spoken",
        "duplicate_wake",
        "missing_even_wake",
        "unknown",
        "bad_wake",
        "bad_invocation_wave",
        "odd_wake",
        "empty",
    ),
)
def test_malformed_source_never_becomes_an_ordinary_pause(damage: str) -> None:
    call = invocation(actor=7)
    event = spoken()
    payload = event.payload
    assert isinstance(payload, QuestSpoken)
    header = event.header
    headers = {
        "producer": replace(header, producer_id="quest.memory"),
        "phase": replace(header, phase=Phase.POST_TICK),
        "wave": replace(header, wave=1),
        "bool_wave": replace(header, wave=False),
        "sequence": replace(header, sequence=0),
        "bool_sequence": replace(header, sequence=True),
        "schema": replace(header, type_key=TypeKey("watch.npc-acted", 1)),
        "occurred": replace(header, occurred_at=Tick(1)),
        "cause": replace(header, caused_by=(EventId("e1-" + "5" * 64),)),
    }
    if damage in headers:
        event = replace(event, header=headers[damage])
    elif damage == "quest":
        event = replace(event, payload=replace(payload, quest_id="quest:foreign"))
    elif damage == "npc":
        event = replace(event, payload=replace(payload, npc_id=EntityId("actor:foreign")))
    elif damage == "intent":
        event = replace(event, payload=replace(payload, intent="invented"))
    elif damage == "due":
        event = replace(event, due_tick=Tick(1))
    wake = call.incoming[0]
    if damage == "bad_wake":
        wake = replace(wake, header=replace(wake.header, producer_id="watch.echo"))
    facts: tuple[WorldEvent, ...] = (wake, event)
    if damage == "duplicate_spoken":
        facts = (event, event)
    elif damage == "duplicate_wake":
        facts = (wake, wake)
    elif damage == "missing_even_wake":
        facts = (event,)
    elif damage == "unknown":
        layout = content().definition.layout
        foreign = BellRung(layout.actor_id, layout.npc_id)
        facts = (
            wake,
            replace(event, payload=foreign, header=replace(event.header, type_key=foreign.schema)),
        )
    elif damage == "empty":
        facts = ()
    call = replace(call, incoming=facts)
    if damage == "bad_invocation_wave":
        call = replace(call, wave=False)
    elif damage == "odd_wake":
        call = replace(
            call,
            logical_tick=Tick(3),
            incoming=(replace(wake, due_tick=Tick(3)), spoken("offer", 3)),
        )
    with pytest.raises(CandidateError) as caught:
        engine().evaluate(call)
    assert caught.value.code == "INVALID_FACT"


@pytest.mark.parametrize("bad", (0, 1, True, "", "actor:wrong", "quest:bad space"))
def test_engine_configuration_rejects_unbound_quest(bad: object) -> None:
    with pytest.raises(ValueError, match="^NPC_TALK_PAUSE_CONTENT$"):
        WatchNpc(content().definition.layout, npc_patrol=True, talk_pause_quest=cast(str, bad))


def test_engine_requires_patrol_and_declares_only_the_new_subscription() -> None:
    selected = content()
    with pytest.raises(ValueError, match="^NPC_TALK_PAUSE_CONTENT$"):
        WatchNpc(selected.definition.layout, talk_pause_quest=selected.definition.quest_id)
    old = WatchNpc(selected.definition.layout, npc_patrol=True).manifest
    new = engine().manifest
    assert new.consumes == (*old.consumes, QuestSpoken.SCHEMA)
    assert (new.reads, new.writes, new.emits, new.phases) == (
        old.reads,
        old.writes,
        old.emits,
        old.phases,
    )


@pytest.mark.parametrize("factory", (ClientSession, ClientWorker))
@pytest.mark.parametrize("flag", (True, 0, 1, None, "1", 2.0))
def test_invalid_selection_precedes_save_or_thread(
    factory: type[ClientSession] | type[ClientWorker], flag: object, tmp_path: Path
) -> None:
    selected = approved_content()
    path = tmp_path / "missing/game.sqlite"
    with pytest.raises(ValueError, match="^NPC_TALK_PAUSE_CONTENT$"):
        factory(
            path,
            selected.definition.layout,
            quest_content=selected,
            npc_memory=True,
            npc_cycle=True,
            npc_aid=True,
            npc_supply_aid=True,
            npc_call_aid=True,
            npc_talk_pause=cast(bool, flag),
        )
    assert not path.parent.exists()


def test_new_bundle_reuses_schema_and_changes_only_selected_rules_identity() -> None:
    selected = approved_content()
    old = cycle_bundle(
        selected, npc_aid=True, npc_supply_aid=True, npc_call_aid=True, npc_patrol=True
    )
    new = cycle_bundle(
        selected,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
    )
    assert old.schema_document == new.schema_document
    assert (
        old.feature_id == "quest.harbor-call-patrol-v1"
        and new.feature_id == "quest.harbor-talk-patrol-v1"
    )
    event = next(p for p in new.events if p.schema == QuestSpoken.SCHEMA)
    assert (
        event.mode == "simulate"
        and event.delivery_phase is Phase.POST_TICK
        and event.subscribers == ("watch.npc",)
    )


@pytest.mark.parametrize("bad", ("npc_space", "actor_space", "bells"))
def test_pause_still_validates_current_references_before_noop(bad: str) -> None:
    from contracts.read_views import AdapterBinding, ViewEpoch
    from domain.state_types import StoredRoot
    from domain.trial import CellPositionRecord
    from domain.watch import WatchNpcRecord
    from orchestration.read_views import ObservedReadViewFactory
    from orchestration.trial import CellPositionAdapter
    from orchestration.watch import WatchNpcAdapter

    layout = content().definition.layout
    npc_space = EntityId("space:foreign") if bad == "npc_space" else layout.space_id
    actor_space = EntityId("space:foreign") if bad == "actor_space" else layout.space_id
    factory = ObservedReadViewFactory(
        StoredRoot(
            (
                CellPositionRecord(layout.actor_id, actor_space, 0),
                WatchNpcRecord(layout.npc_id, npc_space, 6, 0 if bad == "bells" else 1),
            ),
            0,
        )
    )
    AdapterBinding(WatchNpcAdapter(layout, npc_patrol=True)).install(factory)
    AdapterBinding(CellPositionAdapter(layout)).install(factory)
    call = invocation()
    view = factory.open(ViewEpoch(Tick(2), Phase.POST_TICK, 0, "watch.npc", 0))
    with pytest.raises(CandidateError) as caught:
        engine().evaluate(replace(call, state=view, incoming=(*call.incoming, spoken())))
    assert caught.value.code == "INVALID_FACT"


@pytest.mark.parametrize("field", ("due", "occurred"))
def test_bool_equal_to_odd_tick_is_not_valid_source_time(field: str) -> None:
    event = spoken("reminder", 1)
    event = (
        replace(event, due_tick=cast(Tick, True))
        if field == "due"
        else replace(event, header=replace(event.header, occurred_at=cast(Tick, True)))
    )
    with pytest.raises(CandidateError) as caught:
        engine().evaluate(replace(invocation(), logical_tick=Tick(1), incoming=(event,)))
    assert caught.value.code == "INVALID_FACT"
