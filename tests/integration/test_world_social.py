"""Actual social-profile admission,COMMIT,persistence and conversation revalidation."""

from dataclasses import replace
from pathlib import Path

import pytest

from app.headless import restore_checkpoint, state_io
from app.durable import DurableSession
from app.world_catalog import load_social, load_world
from app.world_session import foot_command, open_world_session, world_checkpoint, world_command
from app.world_social_registry import social_world_bundle
from contracts.turn import TurnCommitted, TurnRejected
from contracts.world_conversation import NpcReply, PlayerSay
from contracts.world_social import SocialAction
from contracts.world_supply import SupplyAction
from contracts.world_time import WorldWait
from domain.world import elaborate_place
from domain.world_social import SocialRecord
from domain.world_supply import SupplyScenario
from domain.world_travel import TravelerRecord
from orchestration.world_conversation_context import context_from_core


def _wait(session: DurableSession, seconds: int) -> None:
    while seconds:
        duration = min(16, seconds)
        result = session.submit(
            world_command(session.protocol(), WorldWait(duration)),
            attachment_id=session.attachment_id,
        )
        assert isinstance(result.outcome, TurnCommitted), result
        seconds -= duration


def test_real_actions_exact_duration_contract_gate_save_restart_and_retry(tmp_path: Path) -> None:
    world = load_world()
    catalog = load_social(world)
    path = tmp_path / "social.sqlite"
    place = "place:p0-a"
    npc = elaborate_place(world, place).residents[1].id
    with open_world_session(path, world, social=catalog) as session:
        first = world_command(session.protocol(), SocialAction("protest"))
        committed = session.submit(first, attachment_id=session.attachment_id)
        assert isinstance(committed.outcome, TurnCommitted), committed
        assert session.snapshot().tick == 5
        assert (
            session.submit(first, attachment_id=session.attachment_id).outcome == committed.outcome
        )
        second = session.submit(
            world_command(session.protocol(), SocialAction("protest")),
            attachment_id=session.attachment_id,
        )
        assert isinstance(second.outcome, TurnCommitted), second
        assert session.snapshot().tick == 10
        state = next(c.state for c in session.snapshot().components if isinstance(c, SocialRecord))
        assert dict(state.reputation)["faction:city-p0-a"] == -30
        _wait(session, 30)
        before = session.snapshot(), session.protocol()
        rejected = session.submit(
            world_command(session.protocol(), SupplyAction(place, npc, "accept")),
            attachment_id=session.attachment_id,
        )
        assert (
            isinstance(rejected.outcome, TurnRejected)
            and rejected.outcome.failure.code == "SOCIAL_CONTRACT_DENIED"
        )
        assert (session.snapshot(), session.protocol()) == before

        session.export("slot01")
    with open_world_session(path, world, social=catalog) as session:
        assert (
            next(c.state for c in session.snapshot().components if isinstance(c, SocialRecord))
            == state
        )
        for _ in range(2):
            result = session.submit(
                world_command(session.protocol(), SocialAction("reconcile")),
                attachment_id=session.attachment_id,
            )
            assert isinstance(result.outcome, TurnCommitted), result
        assert session.snapshot().tick == 60
        result = session.submit(
            world_command(session.protocol(), SupplyAction(place, npc, "accept")),
            attachment_id=session.attachment_id,
        )
        assert isinstance(result.outcome, TurnCommitted), result
        session.load("slot01")
        assert (
            next(c.state for c in session.snapshot().components if isinstance(c, SocialRecord))
            == state
        )
        assert session.snapshot().tick == 40


def test_actual_delivery_credits_once_in_same_checkpoint_and_dialogue_context(
    tmp_path: Path,
) -> None:
    world = load_world()
    catalog = load_social(world)
    place = "place:p0-a"
    residents = elaborate_place(world, place).residents
    with open_world_session(tmp_path / "delivery.sqlite", world, social=catalog) as session:
        _wait(session, 40)
        for operation, index in (("accept", 1), ("collect", 0), ("collect", 0), ("deliver", 1)):
            command = world_command(
                session.protocol(), SupplyAction(place, residents[index].id, operation)
            )
            result = session.submit(command, attachment_id=session.attachment_id)
            assert isinstance(result.outcome, TurnCommitted), result
        state = next(c.state for c in session.snapshot().components if isinstance(c, SocialRecord))
        assert state.credited_places == (place,)
        assert dict(state.reputation)["faction:city-p0-a"] == 20
        assert dict(state.reputation)["faction:nation-k0"] == 5
        assert (
            session.submit(command, attachment_id=session.attachment_id).outcome == result.outcome
        )
        _wait(session, 20)
        assert (
            next(c.state for c in session.snapshot().components if isinstance(c, SocialRecord))
            == state
        )
        said = session.submit(
            world_command(session.protocol(), PlayerSay(residents[1].id, "도움을 기억하나요?")),
            attachment_id=session.attachment_id,
        )
        assert isinstance(said.outcome, TurnCommitted), said
        context = context_from_core(session.snapshot(), world, SupplyScenario(), social=catalog)
        assert dict(context.public_facts)["earned_local_reputation"] == "20"
        reply = NpcReply(
            context.current.speech_id, "도움을 기억합니다.", "test", context.sha256, "none"
        )
        accepted = session.submit(
            world_command(session.protocol(), reply), attachment_id=session.attachment_id
        )
        assert isinstance(accepted.outcome, TurnCommitted), accepted
        io = state_io((social_world_bundle(world, catalog),))
        io.validate_checkpoint(session.snapshot(), session.protocol())
        corrupted = replace(
            session.snapshot(),
            components=tuple(
                replace(c, state=replace(c.state, credited_places=()))
                if isinstance(c, SocialRecord)
                else c
                for c in session.snapshot().components
            ),
        )
        with pytest.raises(ValueError, match="^latest receipt does not match head$"):
            io.validate_checkpoint(corrupted, session.protocol())
        policy = social_world_bundle(world, catalog).checkpoint_policy
        assert policy is not None
        with pytest.raises(ValueError, match="^SOCIAL_DELIVERY_BINDING$"):
            policy.validate(corrupted, session.protocol())


def test_identity_road_rejection_and_old_profile_pins(tmp_path: Path) -> None:
    world = load_world()
    catalog = load_social(world)
    old = world_checkpoint(world, conversation=True)
    social = world_checkpoint(world, social=catalog)
    assert old.core.pins != social.core.pins
    assert not any(isinstance(c, SocialRecord) for c in old.core.components)
    with open_world_session(tmp_path / "identity.sqlite", world, social=catalog) as session:
        for payload in (SocialAction("identify", "ancestry:human", "none"),):
            result = session.submit(
                world_command(session.protocol(), payload), attachment_id=session.attachment_id
            )
            assert isinstance(result.outcome, TurnCommitted), result
        before = session.snapshot(), session.protocol()
        bad = session.submit(
            world_command(session.protocol(), SocialAction("identify", "ancestry:sylvan", "none")),
            attachment_id=session.attachment_id,
        )
        assert (
            isinstance(bad.outcome, TurnRejected)
            and bad.outcome.failure.code == "SOCIAL_IDENTITY_LOCKED"
        )
        assert (session.snapshot(), session.protocol()) == before
        result = session.submit(
            foot_command(session.protocol(), "place:p0-b"), attachment_id=session.attachment_id
        )
        assert isinstance(result.outcome, TurnCommitted), result
        before = session.snapshot(), session.protocol()
        bad = session.submit(
            world_command(session.protocol(), SocialAction("protest")),
            attachment_id=session.attachment_id,
        )
        assert (
            isinstance(bad.outcome, TurnRejected)
            and bad.outcome.failure.code == "SOCIAL_OUT_OF_REACH"
        )
        assert (session.snapshot(), session.protocol()) == before


def test_hostile_new_entry_is_rejected_but_existing_road_remains_usable() -> None:
    world = load_world()
    catalog = load_social(world)
    bundles = (social_world_bundle(world, catalog),)
    checkpoint = world_checkpoint(world, social=catalog)
    target = "place:p0-b"
    components = tuple(
        replace(
            c,
            state=replace(
                c.state,
                reputation=tuple(
                    (key, -30 if key == "faction:city-p0-b" else score)
                    for key, score in c.state.reputation
                ),
            ),
        )
        if isinstance(c, SocialRecord)
        else c
        for c in checkpoint.core.components
    )
    session = restore_checkpoint(
        replace(checkpoint.core, components=components), checkpoint.protocol, bundles=bundles
    )
    before = session.snapshot(), session.protocol()
    denied = session.driver.submit(foot_command(session.protocol(), target))
    assert isinstance(denied, TurnRejected) and denied.failure.code == "SOCIAL_ENTRY_DENIED"
    assert (session.snapshot(), session.protocol()) == before
    on_road = tuple(
        replace(c, state=replace(c.state, destination_id=target, offset_m=1))
        if isinstance(c, TravelerRecord)
        else c
        for c in components
    )
    session = restore_checkpoint(
        replace(checkpoint.core, components=on_road), checkpoint.protocol, bundles=bundles
    )
    assert isinstance(
        session.driver.submit(foot_command(session.protocol(), target, -1)), TurnCommitted
    )
    assert (
        next(
            c.state for c in session.snapshot().components if isinstance(c, TravelerRecord)
        ).destination_id
        == ""
    )


def test_social_and_accepted_reply_replay_hashes_match_without_provider() -> None:
    world = load_world()
    catalog = load_social(world)
    bundles = (social_world_bundle(world, catalog),)
    checkpoint = world_checkpoint(world, social=catalog)
    first = restore_checkpoint(checkpoint.core, checkpoint.protocol, bundles=bundles)
    second = restore_checkpoint(checkpoint.core, checkpoint.protocol, bundles=bundles)
    npc = elaborate_place(world, "place:p0-a").residents[1]
    for payload in (
        SocialAction("identify", "ancestry:human", "country:k2"),
        SocialAction("protest"),
        PlayerSay(npc.id, "나는 항의했어요"),
    ):
        command = world_command(first.protocol(), payload)
        committed = first.driver.submit(command)
        assert isinstance(committed, TurnCommitted), committed
        assert second.driver.submit(command) == committed
    context = context_from_core(first.snapshot(), world, SupplyScenario(), social=catalog)
    command = world_command(
        first.protocol(),
        NpcReply(
            context.current.speech_id, "항의를 들었습니다.", "recorded", context.sha256, "none"
        ),
    )
    committed = first.driver.submit(command)
    assert isinstance(committed, TurnCommitted), committed
    assert second.driver.submit(command) == committed
    io = state_io(bundles)
    assert io.hash_core(first.snapshot()) == io.hash_core(second.snapshot())
