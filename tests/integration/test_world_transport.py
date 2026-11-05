"""Registered long-duration travel keeps normal limits and actual world consequences."""

from dataclasses import replace
from pathlib import Path

import pytest

from app.headless import HeadlessSession, restore_checkpoint, state_io
from app.world_catalog import load_social, load_transport, load_world
from app.world_session import open_world_session, world_checkpoint, world_command
from app.world_transport_registry import transport_world_bundle
from contracts.errors import BootstrapError
from contracts.skeleton import CommandRoute
from contracts.read_views import ReadPort
from contracts.turn import (
    AdmittedCommand,
    AdmissionOutcome,
    GameCommand,
    TurnAborted,
    TurnCommitted,
    TurnRejected,
)
from contracts.world_time import WorldWait
from contracts.world_social import SocialAction
from contracts.world_conversation import PlayerSay
from contracts.world_transport import TransportAction
from domain.canonical import JsonValue, object_value, seal
from domain.primitives import Tick, TypeKey
from domain.world_population import SettlementRecord
from domain.world_supply import SupplyRecord
from domain.world_transport import JourneyRecord, SupplyProgressRecord, plan_journey
from domain.world_travel import TravelerRecord
from domain.world import elaborate_place
from domain.world_social import SocialRecord


def _command(session: HeadlessSession, operation: str, destination: str = "") -> GameCommand:
    world = load_world()
    rules = load_transport(world)
    journey = next(c.state for c in session.snapshot().components if isinstance(c, JourneyRecord))
    travel = next(c.state for c in session.snapshot().components if isinstance(c, TravelerRecord))
    plan = plan_journey(
        world, rules, journey, travel, session.snapshot().tick, operation, destination
    )
    return world_command(session.protocol(), TransportAction(operation, destination, plan.seconds))


def test_summary_duration_is_opt_in_and_stops_at_actual_checkpoint() -> None:
    world = load_world()
    social, rules = load_social(world), load_transport(world)
    bundle = transport_world_bundle(world, social, rules)
    cp = world_checkpoint(world, social=social, transport=rules)
    session = restore_checkpoint(cp.core, cp.protocol, bundles=(bundle,))
    board = session.driver.submit(
        world_command(session.protocol(), TransportAction("board", "place:p0-b", 1))
    )
    assert isinstance(board, TurnCommitted), board
    journey = next(c.state for c in session.snapshot().components if isinstance(c, JourneyRecord))
    travel = next(c.state for c in session.snapshot().components if isinstance(c, TravelerRecord))
    plan = plan_journey(world, rules, journey, travel, session.snapshot().tick, "advance")
    assert plan.seconds == 500
    outcome = session.driver.submit(
        world_command(session.protocol(), TransportAction("advance", "", 500))
    )
    assert isinstance(outcome, TurnCommitted), outcome
    assert session.snapshot().tick == 501
    saved = next(c.state for c in session.snapshot().components if isinstance(c, JourneyRecord))
    assert saved.phase == "blocked" and saved.progress_m == 2500


def test_actual_arrival_wait_and_world_catchup_replay_match() -> None:
    world = load_world()
    social, rules = load_social(world), load_transport(world)
    bundle = transport_world_bundle(world, social, rules)
    cp = world_checkpoint(world, social=social, transport=rules)
    first = restore_checkpoint(cp.core, cp.protocol, bundles=(bundle,))
    replay = restore_checkpoint(cp.core, cp.protocol, bundles=(bundle,))
    for operation, destination in (
        ("board", "place:p0-b"),
        ("advance", ""),
        ("wait", ""),
        ("resume", ""),
        ("advance", ""),
    ):
        command = _command(first, operation, destination)
        outcome = first.driver.submit(command)
        assert isinstance(outcome, TurnCommitted), outcome
        assert replay.driver.submit(command) == outcome
    assert first.snapshot().tick == 2301
    traveler = next(c.state for c in first.snapshot().components if isinstance(c, TravelerRecord))
    assert traveler.place_id == "place:p0-b" and traveler.visited == ("place:p0-a", "place:p0-b")
    local = next(
        c
        for c in first.snapshot().components
        if isinstance(c, SettlementRecord) and c.entity_id == "place:p0-b"
    )
    assert local.state is not None and len(local.state.residents) == 4
    for supply in (c.state for c in first.snapshot().components if isinstance(c, SupplyRecord)):
        assert supply.consumed + supply.missed == 76
    assert (
        next(c.state for c in first.snapshot().components if isinstance(c, SupplyProgressRecord))
        == 2301
    )
    io = state_io((bundle,))
    assert io.hash_core(first.snapshot()) == io.hash_core(replay.snapshot())


def test_durable_stop_slot_restart_return_and_rejected_duration(tmp_path: Path) -> None:
    world = load_world()
    social, rules = load_social(world), load_transport(world)
    path = tmp_path / "journey.sqlite"
    with open_world_session(path, world, social=social, transport=rules) as owner:
        for payload in (
            TransportAction("board", "place:p0-b", 1),
            TransportAction("advance", "", 500),
        ):
            outcome = owner.submit(
                world_command(owner.protocol(), payload), attachment_id=owner.attachment_id
            )
            assert isinstance(outcome.outcome, TurnCommitted), outcome
        owner.export("slot01")
    with open_world_session(path, world, social=social, transport=rules) as owner:
        assert owner.snapshot().tick == 501
        before = owner.snapshot(), owner.protocol()
        rejected = owner.submit(
            world_command(owner.protocol(), TransportAction("wait", "", 300)),
            attachment_id=owner.attachment_id,
        )
        assert (
            isinstance(rejected.outcome, TurnRejected)
            and rejected.outcome.failure.code == "JOURNEY_DURATION"
        )
        assert (owner.snapshot(), owner.protocol()) == before
        for payload in (TransportAction("return", "", 1), TransportAction("advance", "", 500)):
            result = owner.submit(
                world_command(owner.protocol(), payload), attachment_id=owner.attachment_id
            )
            assert isinstance(result.outcome, TurnCommitted), result
        assert owner.snapshot().tick == 1002
        assert next(
            c.state for c in owner.snapshot().components if isinstance(c, TravelerRecord)
        ).visited == ("place:p0-a",)
        owner.load("slot01")
        assert owner.snapshot().tick == 501
        assert (
            next(c.state for c in owner.snapshot().components if isinstance(c, JourneyRecord)).phase
            == "blocked"
        )


@pytest.mark.parametrize(
    "summary",
    [
        {"maximum_seconds": True, "commands": ()},
        {"maximum_seconds": 16, "commands": ()},
        {"maximum_seconds": 3601, "commands": ()},
        {"maximum_seconds": 3600, "commands": ()},
        {"maximum_seconds": 3600, "commands": ({"kind": "unknown.command", "version": 1},)},
        {
            "maximum_seconds": 3600,
            "commands": ({"kind": "world.transport-action", "version": 1},) * 2,
        },
        {"maximum_seconds": 3600, "commands": (), "extra": 1},
    ],
)
def test_summary_rule_rejects_malformed_or_unregistered_configuration(summary: JsonValue) -> None:
    world = load_world()
    bundle = transport_world_bundle(world, load_social(world), load_transport(world))
    altered = replace(
        bundle,
        rules_document=object_value(seal({**bundle.rules_document, "time_summary": summary})),
    )
    with pytest.raises(BootstrapError, match="^INVALID_EVENT_POLICY:"):
        state_io((altered,))


class _TooLong:
    def __init__(self, inner: CommandRoute, duration: int) -> None:
        self.inner, self.duration, self.schema, self.reads = (
            inner,
            duration,
            inner.schema,
            inner.reads,
        )

    def admit(
        self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str
    ) -> AdmissionOutcome:
        result = self.inner.admit(command, state, start_tick=start_tick, world_id=world_id)
        if isinstance(result, AdmittedCommand):
            return replace(
                result, plan=replace(result.plan, target_tick=Tick(start_tick + self.duration))
            )
        return result


@pytest.mark.parametrize(
    "schema,duration", [(WorldWait.SCHEMA, 17), (TransportAction.SCHEMA, 3601)]
)
def test_new_profile_keeps_normal_and_summary_bounds(schema: TypeKey, duration: int) -> None:
    world = load_world()
    social, rules = load_social(world), load_transport(world)
    bundle = transport_world_bundle(world, social, rules)
    cp = world_checkpoint(world, social=social, transport=rules)
    altered = replace(
        bundle,
        command_routes=tuple(
            _TooLong(r, duration) if r.schema == schema else r for r in bundle.command_routes
        ),
    )
    session = restore_checkpoint(cp.core, cp.protocol, bundles=(altered,))
    payload = (
        WorldWait(1) if schema == WorldWait.SCHEMA else TransportAction("board", "place:p0-b", 1)
    )
    before = session.snapshot(), session.protocol()
    outcome = session.driver.submit(world_command(session.protocol(), payload))
    assert isinstance(outcome, TurnAborted) and outcome.failure.code == "TURN_LIMIT"
    assert (session.snapshot(), session.protocol()) == before


def test_hostile_boarding_arrival_and_in_transit_actions_preserve_state() -> None:
    world = load_world()
    social, rules = load_social(world), load_transport(world)
    bundle = transport_world_bundle(world, social, rules)
    cp = world_checkpoint(world, social=social, transport=rules)
    session = restore_checkpoint(cp.core, cp.protocol, bundles=(bundle,))
    for _ in range(7):
        result = session.driver.submit(world_command(session.protocol(), SocialAction("protest")))
        assert isinstance(result, TurnCommitted), result
    before = session.snapshot(), session.protocol()
    result = session.driver.submit(_command(session, "board", "place:p0-b"))
    assert isinstance(result, TurnRejected) and result.failure.code == "SOCIAL_ENTRY_DENIED"
    assert (session.snapshot(), session.protocol()) == before

    session = restore_checkpoint(cp.core, cp.protocol, bundles=(bundle,))
    result = session.driver.submit(_command(session, "board", "place:p0-b"))
    assert isinstance(result, TurnCommitted), result
    npc = elaborate_place(world, "place:p0-a").residents[1].id
    for payload in (SocialAction("protest"), PlayerSay(npc, "안녕")):
        before = session.snapshot(), session.protocol()
        result = session.driver.submit(world_command(session.protocol(), payload))
        assert isinstance(result, TurnRejected) and result.failure.code == "JOURNEY_ACTIVE"
        assert (session.snapshot(), session.protocol()) == before
    for operation in ("advance", "wait", "resume"):
        result = session.driver.submit(_command(session, operation))
        assert isinstance(result, TurnCommitted), result
    # A synthetic initial checkpoint exercises arrival-time policy. Use a fresh
    # protocol:altering facts under the old committed receipt must remain invalid.
    # This slice has no autonomous diplomacy writer;do not pretend this is one.
    core = session.snapshot()
    changed = replace(
        core,
        components=tuple(
            replace(
                c,
                state=replace(
                    c.state,
                    reputation=tuple(
                        (key, -40 if key == "faction:nation-k0" else value)
                        for key, value in c.state.reputation
                    ),
                ),
            )
            if isinstance(c, SocialRecord)
            else c
            for c in core.components
        ),
    )
    session = restore_checkpoint(changed, cp.protocol, bundles=(bundle,))
    before = session.snapshot(), session.protocol()
    result = session.driver.submit(_command(session, "advance"))
    assert isinstance(result, TurnRejected) and result.failure.code == "SOCIAL_ENTRY_DENIED"
    assert (session.snapshot(), session.protocol()) == before
    for operation in ("return", "advance"):
        result = session.driver.submit(_command(session, operation))
        assert isinstance(result, TurnCommitted), result
    assert (
        next(c.state for c in session.snapshot().components if isinstance(c, JourneyRecord)).phase
        == "idle"
    )
    assert next(
        c.state for c in session.snapshot().components if isinstance(c, TravelerRecord)
    ).visited == ("place:p0-a",)
