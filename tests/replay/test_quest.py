from __future__ import annotations

from pathlib import Path
from typing import cast

from app.client_session import ClientSession
from app.headless import replay_runner, state_io
from app.quest_registry import quest_bundle
from contracts.client import ClientAction
from domain.canonical import array_value, decode_json, object_value
from tests.unit.quest_fixtures import content


def test_independent_vector_then_real_durable_offline_replay(tmp_path: Path) -> None:
    selected = content()
    reference = object_value(
        decode_json((Path(__file__).parent / "fixtures/quest_harbor_vector_v1.json").read_bytes())
    )
    session = ClientSession(
        tmp_path / "game.sqlite", selected.definition.layout, quest_content=selected
    )
    from contracts.replay import ReplayFixture

    try:
        initial_core, initial_protocol = session.owner.snapshot(), session.owner.protocol()
        facts: list[tuple[object, ...]] = []
        for raw in array_value(reference["steps"]):
            row = array_value(raw)
            result = session.act(cast(ClientAction, row[0]))
            assert result.view is not None and result.status == "COMMITTED"
            v = result.view
            assert (
                v.tick,
                v.actor_cell,
                v.actor_hp,
                v.enemy_hp,
                v.stamina,
                result.quest_stage,
                result.quest_reward,
            ) == row[1:]
            for event in session.owner.last_publication().facts:
                payload = event.payload
                if payload.schema.kind.startswith("quest."):
                    from contracts.quest import QuestSpoken, QuestCompleted

                    suffix: tuple[object, ...] = (
                        (payload.intent,)
                        if isinstance(payload, QuestSpoken)
                        else (payload.amount,)
                        if isinstance(payload, QuestCompleted)
                        else ()
                    )
                    facts.append((v.tick, payload.schema.kind, *suffix))
        assert tuple(facts) == array_value(reference["quest_facts"])
        trace = session.owner.retained_segment().trace
        fixture = ReplayFixture(initial_core, initial_protocol, trace)
        assert replay_runner(fixture, bundles=(quest_bundle(selected),)).run(trace) == ()
        assert state_io((quest_bundle(selected),)).pins == initial_core.pins
    finally:
        session.close()
