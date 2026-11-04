"""Accepted free-text speech through real admission,duration,COMMIT and replay."""

from pathlib import Path

import pytest

from app.headless import restore_checkpoint, state_io
from app.world_catalog import load_world
from app.world_conversation_registry import conversation_world_bundle
from app.world_session import foot_command, open_world_session, world_checkpoint, world_command
from contracts.turn import TurnCommitted, TurnRejected
from contracts.world_conversation import ContinueSpeech, NpcReply, PlayerSay
from contracts.world_supply import SupplyAction
from contracts.world_time import WorldWait
from domain.world import elaborate_place
from domain.world_conversation import ConversationRecord
from domain.world_population import InventoryRecord
from domain.world_supply import SupplyRecord, SupplyScenario
from orchestration.world_conversation_context import context_from_core


def test_long_speech_exact_segments_retry_save_restart_and_no_automatic_reward(
    tmp_path: Path,
) -> None:
    world = load_world()
    scenario = SupplyScenario(start_tick=1)
    npc = elaborate_place(world, "place:p0-a").residents[1]
    path = tmp_path / "dialogue.sqlite"
    with open_world_session(path, world, supply=scenario, conversation=True) as session:
        command = world_command(session.protocol(), PlayerSay(npc.id, "가" * 100))
        result = session.submit(command, attachment_id=session.attachment_id)
        assert isinstance(result.outcome, TurnCommitted), result
        assert session.snapshot().tick == 16
        conversation = next(
            c.state for c in session.snapshot().components if isinstance(c, ConversationRecord)
        )
        assert conversation.remaining == 1 and len(conversation.exchanges) == 1
        assert (
            session.submit(command, attachment_id=session.attachment_id).outcome == result.outcome
        )
        before = session.snapshot(), session.protocol()
        blocked = session.submit(
            foot_command(session.protocol(), "place:p0-b"), attachment_id=session.attachment_id
        )
        assert (
            isinstance(blocked.outcome, TurnRejected)
            and blocked.outcome.failure.code == "DIALOGUE_SPEAKING"
        )
        assert (session.snapshot(), session.protocol()) == before
        session.export("slot01")
    with open_world_session(path, world, supply=scenario, conversation=True) as session:
        result = session.submit(
            world_command(session.protocol(), ContinueSpeech(conversation.exchanges[-1].speech_id)),
            attachment_id=session.attachment_id,
        )
        assert isinstance(result.outcome, TurnCommitted), result
        assert session.snapshot().tick == 17
        context = context_from_core(session.snapshot(), world, scenario)
        assert context.available_action == "accept"
        result = session.submit(
            world_command(
                session.protocol(),
                NpcReply(context.current.speech_id, "알겠어요", "test", context.sha256, "accept"),
            ),
            attachment_id=session.attachment_id,
        )
        assert isinstance(result.outcome, TurnCommitted), result
        assert session.snapshot().tick == 18
        supply = next(
            c.state
            for c in session.snapshot().components
            if isinstance(c, SupplyRecord) and c.entity_id == "place:p0-a"
        )
        inventory = next(
            c.state for c in session.snapshot().components if isinstance(c, InventoryRecord)
        )
        assert supply.stage == 0 and inventory.gold == 0 and inventory.items == ()
        result = session.submit(
            world_command(session.protocol(), SupplyAction("place:p0-a", npc.id, "accept")),
            attachment_id=session.attachment_id,
        )
        assert isinstance(result.outcome, TurnCommitted), result
        assert (
            next(
                c.state.stage
                for c in session.snapshot().components
                if isinstance(c, SupplyRecord) and c.entity_id == "place:p0-a"
            )
            == 1
        )
        session.load("slot01")
        assert session.snapshot().tick == 16
        restored = next(
            c.state for c in session.snapshot().components if isinstance(c, ConversationRecord)
        )
        assert restored == conversation


def test_stale_or_unsupported_generated_reply_preserves_heard_speech_and_time(
    tmp_path: Path,
) -> None:
    world = load_world()
    scenario = SupplyScenario(start_tick=1)
    npc = elaborate_place(world, "place:p0-a").residents[2]
    with open_world_session(
        tmp_path / "stale.sqlite", world, supply=scenario, conversation=True
    ) as session:
        result = session.submit(
            world_command(session.protocol(), PlayerSay(npc.id, "안녕")),
            attachment_id=session.attachment_id,
        )
        assert isinstance(result.outcome, TurnCommitted), result
        context = context_from_core(session.snapshot(), world, scenario)
        assert context.available_action == "none"
        for proposal, digest, code in (
            ("deliver", context.sha256, "DIALOGUE_PROPOSAL"),
            ("none", "0" * 64, "DIALOGUE_CONTEXT_STALE"),
        ):
            before = session.snapshot(), session.protocol()
            result = session.submit(
                world_command(
                    session.protocol(),
                    NpcReply(context.current.speech_id, "안녕하세요", "test", digest, proposal),
                ),
                attachment_id=session.attachment_id,
            )
            assert isinstance(result.outcome, TurnRejected) and result.outcome.failure.code == code
            assert (session.snapshot(), session.protocol()) == before
        result = session.submit(
            world_command(session.protocol(), WorldWait(1)), attachment_id=session.attachment_id
        )
        assert isinstance(result.outcome, TurnCommitted), result
        fresh = context_from_core(session.snapshot(), world, scenario)
        assert fresh.sha256 != context.sha256
        assert fresh.current.player_text == "안녕"


def test_accepted_conversation_replays_without_any_provider() -> None:
    world = load_world()
    scenario = SupplyScenario(start_tick=1)
    bundles = (conversation_world_bundle(world, scenario),)
    cp = world_checkpoint(world, supply=scenario, conversation=True)
    a = restore_checkpoint(cp.core, cp.protocol, bundles=bundles)
    b = restore_checkpoint(cp.core, cp.protocol, bundles=bundles)
    npc = elaborate_place(world, "place:p0-a").residents[0]
    say = world_command(a.protocol(), PlayerSay(npc.id, "비밀 암호는 파란도토리야"))
    first = a.driver.submit(say)
    assert isinstance(first, TurnCommitted), first
    assert b.driver.submit(say) == first
    context = context_from_core(a.snapshot(), world, scenario)
    reply = world_command(
        a.protocol(),
        NpcReply(
            context.current.speech_id, "기억해 둘게요.", "recorded-model", context.sha256, "none"
        ),
    )
    first = a.driver.submit(reply)
    assert isinstance(first, TurnCommitted), first
    assert b.driver.submit(reply) == first
    assert state_io(bundles).hash_core(a.snapshot()) == state_io(bundles).hash_core(b.snapshot())


@pytest.mark.parametrize(
    "text,code", [("", "DIALOGUE_TEXT"), ("a" * 513, "DIALOGUE_TEXT"), ("가", "INVALID_COMMAND")]
)
def test_invalid_speech_never_advances_or_creates_memory(
    tmp_path: Path, text: str, code: str
) -> None:
    world = load_world()
    npc = elaborate_place(world, "place:p0-a").residents[0]
    with open_world_session(tmp_path / "invalid.sqlite", world, conversation=True) as session:
        before = session.snapshot(), session.protocol()
        result = session.submit(
            world_command(session.protocol(), PlayerSay(npc.id, text)),
            attachment_id=session.attachment_id,
        )
        assert isinstance(result.outcome, TurnRejected) and result.outcome.failure.code == code
        assert (session.snapshot(), session.protocol()) == before
