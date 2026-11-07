"""O3 plays one supply quest with two residents through the knowledge profile."""

from dataclasses import replace
import gc
from pathlib import Path
from threading import Event
import tkinter as tk
from typing import Literal

import pytest

from adapters.generation_budget import GenerationBudget
from adapters.sqlite_store import SqliteCommitStore
from adapters.world_conversation import GeminiConversation
from app.headless import replay_runner, restore_checkpoint
from app.world_catalog import load_social, load_transport, load_world
from app.world_client import WorldMapWindow
from app.world_session import open_world_session, world_checkpoint, world_command
from app.world_transport_registry import transport_world_bundle
from app.world_worker import WorldWorker
from contracts.dialogue import GenerationError
from contracts.persistence import DurableTurn, RecoveryResult
from contracts.replay import ReplayFixture
from contracts.turn import CommitReceipt, TurnCommitted
from contracts.world_conversation import PlayerSay
from contracts.world_supply import SupplyAction
from contracts.world_time import WorldWait
from domain.canonical import (
    JsonObject,
    array_value,
    canonical_json,
    decode_json,
    object_value,
    text_value,
)
from domain.state_types import CoreSnapshot
from domain.world import elaborate_place
from domain.world_conversation import ConversationRecord, SpeechJudgment
from domain.world_social import SocialRecord
from domain.world_supply import SupplyRecord, SupplyScenario
from orchestration.world_conversation_context import context_from_core
from tests.integration.test_world_authored_supply import authored_choice, no_provider
from tests.integration.test_world_client import _settle, root as root
from tests.integration.test_world_knowledge import commit, wait_until

LIE = "보급로가 이미 열렸어요"
PRIVATE = "은신처는 북쪽 창고예요"
ASK = "길 열렸나요?"


class QuestTransport:
    """Control provider output while recording the actual serialized input."""

    def __init__(self, *, timeout: bool) -> None:
        self.timeout = timeout
        self.contexts: list[JsonObject] = []
        self.replies = iter(
            (
                ("상자부터 받으세요", "collect", 2, LIE),
                ("아직요", "none", 0, ""),
                ("이미 길이 열렸어요", "deliver", 0, ""),
                ("네", "none", 0, ""),
                ("네", "none", 0, ""),
            )
        )

    def send(self, request: JsonObject, key: str, cancelled: Event) -> JsonObject:
        assert key == "fixture-key" and not cancelled.is_set()
        content = object_value(array_value(request["contents"])[0])
        part = object_value(array_value(content["parts"])[0])
        self.contexts.append(object_value(decode_json(text_value(part["text"]).encode("utf-8"))))
        if self.timeout:
            raise GenerationError("GENERATION_TIMEOUT")
        text, proposal, importance, quote = next(self.replies)
        body = canonical_json(
            {
                "text_ko": text,
                "proposal_operation": proposal,
                "importance": importance,
                "repeat_quote": quote,
            }
        ).decode("utf-8")
        return {
            "candidates": ({"finishReason": "STOP", "content": {"parts": ({"text": body},)}},),
            "modelVersion": "controlled-o3",
        }


def advance_to(root: tk.Tk, window: WorldMapWindow, now: list[int], tick: int) -> None:
    assert window.update is not None and window.update.tick <= tick
    now[0] += (tick - window.update.tick) * 10_000_000_000
    window.advance_clock()
    _settle(root, window)
    assert window.update.tick == tick


def speak(root: tk.Tk, window: WorldMapWindow, name: str, text: str) -> None:
    panel = window.dialogue
    assert panel is not None
    panel.selected.set(name)
    panel.input.insert("1.0", text)
    panel.buttons["send"].invoke()
    _settle(root, window)
    assert window.update is not None and window.update.conversation is not None
    assert window.update.conversation.exchanges[-1].player_text == text


def deliver_with_uncertain_commit(
    root: tk.Tk, window: WorldMapWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_persist = SqliteCommitStore.persist
    original_recover = SqliteCommitStore.recover
    committed: list[DurableTurn] = []
    failed_recovery: list[DurableTurn] = []

    def persist(store: SqliteCommitStore, turn: DurableTurn) -> CommitReceipt:
        original_persist(store, turn)
        committed.append(turn)
        raise OSError("lost delivery acknowledgement after SQLite commit")

    def recover(store: SqliteCommitStore, turn: DurableTurn) -> RecoveryResult:
        if not failed_recovery:
            failed_recovery.append(turn)
            raise OSError("delivery recovery unavailable once")
        return original_recover(store, turn)

    with monkeypatch.context() as patch:
        patch.setattr(SqliteCommitStore, "persist", persist)
        patch.setattr(SqliteCommitStore, "recover", recover)
        authored_choice(root, window, "필요한 상자가 다 모였네요")
        assert len(committed) == len(failed_recovery) == 1
        assert committed[0].command == failed_recovery[0].command
        failed = window.supply_error
        assert failed and window.supply_command is not None
        assert window.update is not None and window.update.inventory.gold == 0
        key = window.supply_request_key
        window.retry_supply.invoke()
        _settle(root, window)
        assert not window.supply_error and window.supply_request_key == key and len(committed) == 1


def objective(core: CoreSnapshot) -> CoreSnapshot:
    return replace(
        core, components=tuple(c for c in core.components if not isinstance(c, ConversationRecord))
    )


@pytest.mark.parametrize("mode", ("ai", "offline", "timeout"))
def test_two_npc_supply_quest_resolves_only_on_confirmed_delivery(
    root: tk.Tk,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: Literal["ai", "offline", "timeout"],
) -> None:
    gc.collect()  # Finalize destroyed Tk variables on the UI thread.
    world = load_world()
    social, transport = load_social(world), load_transport(world)
    scenario = SupplyScenario(start_tick=1)
    place = world.places[0].id
    courier, merchant, *_ = elaborate_place(world, place).residents
    assert (courier.occupation, merchant.occupation) == ("운송인", "상인")
    path = tmp_path / "quest.sqlite"
    external = QuestTransport(timeout=mode == "timeout")
    worker = WorldWorker(
        path,
        world,
        scenario=scenario,
        social=social,
        transport=transport,
        knowledge=True,
        authored_supply=True,
        live_npc=mode != "offline",
        generator_factory=no_provider
        if mode == "offline"
        else lambda: GeminiConversation(
            "fixture-key",
            GenerationBudget(tmp_path / "budget", spacing_ms=0),
            free_tier_confirmed=True,
            free_data_use_confirmed=True,
            send=external.send,
        ),
    )
    now = [0]
    window = None
    try:
        window = WorldMapWindow(root, world, worker, now_ns=lambda: now[0])
        _settle(root, window)
        advance_to(root, window, now, 1)
        authored_choice(root, window, "운송인에게 상자 2개")
        assert window.update is not None and window.update.tick == 2
        window.buttons[2].invoke()  # Save the branch before the claim.
        _settle(root, window)
        assert "저장했습니다" in window.status.get()
        panel = window.dialogue
        assert panel is not None

        if mode == "offline":
            assert str(panel.buttons["send"]["state"]) == "disabled"
        else:
            speak(root, window, courier.name, f"{LIE}. {PRIVATE}.")
            (initial,) = external.contexts
            heard = object_value(initial["current"])
            assert heard["player_text"] == f"{LIE}. {PRIVATE}." and initial["npc_id"] == courier.id
            assert ("supply_route", "blocked") in array_value(initial["public_facts"])
            assert not initial["rumors"] and not window.update.inventory.items
            if mode == "timeout":
                assert "보급 의뢰 대화" in panel.status.get() and not window.dialogue_recovery
        advance_to(root, window, now, 9)
        if mode == "ai":
            assert panel.offer is not None and panel.offer.action.operation == "collect"
            panel.confirm.invoke()
            _settle(root, window)
            speak(root, window, merchant.name, ASK)
            early = external.contexts[1]
            assert early["npc_id"] == merchant.id and early["logical_tick"] == 12
            assert not early["rumors"] and not early["memories"] and not early["observations"]
            assert LIE not in canonical_json(early).decode("utf-8")
        else:
            authored_choice(root, window, "상자를 하나 내드릴게요")
        assert window.update.inventory.items == (("item:supply-p0-a", 1),)
        advance_to(root, window, now, 13)
        authored_choice(root, window, "상자를 하나 내드릴게요")
        assert window.update.tick == 14

        if mode == "ai":
            advance_to(root, window, now, 17)
            speak(root, window, merchant.name, ASK)
            late = external.contexts[2]
            (raw_rumor,) = array_value(late["rumors"])
            rumor = object_value(raw_rumor)
            assert rumor["quote"] == LIE and rumor["direct_listener_id"] == courier.id
            assert rumor["player_id"] == "actor:world-player"
            assert rumor["speech_id"] == object_value(external.contexts[0]["current"])["speech_id"]
            assert rumor["learned_tick"] == late["logical_tick"] == 19
            assert PRIVATE not in canonical_json(late).decode("utf-8")
            assert ("supply_route", "blocked") in array_value(late["public_facts"])
            assert ("assignment_stage", "1") in array_value(late["public_facts"])
            assert not late["observations"] and late["available_action"] == "deliver"
            transcript = window.update.conversation
            assert (
                transcript is not None
                and transcript.exchanges[-1].reply_text == "이미 길이 열렸어요"
            )
        before_delivery = window.update.inventory
        assert before_delivery.gold == 0 and before_delivery.items == (("item:supply-p0-a", 2),)
        assert "보급 차질 발생" in window.supply_text.get()
        advance_to(root, window, now, 22)
        if mode == "ai":
            assert panel.offer is not None and panel.offer.action.operation == "deliver"
            panel.confirm.invoke()
            _settle(root, window)
        elif mode == "timeout":
            deliver_with_uncertain_commit(root, window, monkeypatch)
        else:
            authored_choice(root, window, "필요한 상자가 다 모였네요")
        assert window.update.tick == 23 and not window.update.offers
        assert "덕분에 보급로가 다시 열렸어요" in window.supply_text.get()

        if mode == "ai":
            speak(root, window, merchant.name, "고마워")
            speak(root, window, courier.name, "고마워")
            merchant_after, courier_after = external.contexts[3:]
            (observed,) = array_value(merchant_after["observations"])
            assert observed == {
                "event": "observed_supply_delivery",
                "observer_id": merchant.id,
                "place_id": place,
                "tick": 23,
            }
            assert not courier_after["observations"]
            assert PRIVATE in canonical_json(courier_after).decode("utf-8")
            assert PRIVATE not in canonical_json(merchant_after).decode("utf-8")
            for context in (merchant_after, courier_after):
                assert ("supply_route", "open") in array_value(context["public_facts"])
                assert context["available_action"] == "none"
        advance_to(root, window, now, 27)
        final_inventory = window.update.inventory
        assert final_inventory.gold == 5 and not final_inventory.items
    finally:
        if window is not None:
            window.dispose()
        worker.close()

    bundles = (transport_world_bundle(world, social, transport, scenario, knowledge=True),)
    actions = (
        SupplyAction(place, merchant.id, "accept"),
        SupplyAction(place, courier.id, "collect"),
        SupplyAction(place, courier.id, "collect"),
        SupplyAction(place, merchant.id, "deliver"),
    )
    initial_checkpoint = world_checkpoint(
        world, supply=scenario, social=social, transport=transport, knowledge=True
    )
    direct = restore_checkpoint(
        initial_checkpoint.core, initial_checkpoint.protocol, bundles=bundles
    )
    for tick, action in zip((1, 9, 13, 22), actions, strict=True):
        assert isinstance(
            direct.driver.submit(
                world_command(direct.protocol(), WorldWait(tick - direct.snapshot().tick))
            ),
            TurnCommitted,
        )
        assert isinstance(
            direct.driver.submit(world_command(direct.protocol(), action)), TurnCommitted
        )
    assert isinstance(
        direct.driver.submit(world_command(direct.protocol(), WorldWait(4))), TurnCommitted
    )

    with open_world_session(
        path, world, supply=scenario, social=social, transport=transport, knowledge=True
    ) as owner:
        core = owner.snapshot()
        assert objective(core) == objective(direct.snapshot())
        city = next(
            c.state for c in core.components if isinstance(c, SupplyRecord) and c.entity_id == place
        )
        assert (city.stage, city.repair_used, city.treasury, city.resolved_tick) == (2, 2, 10, 23)
        merit = next(c.state for c in core.components if isinstance(c, SocialRecord))
        assert merit.credited_places == (place,)
        assert dict(merit.reputation)["faction:city-p0-a"] == 20
        assert dict(merit.reputation)["faction:nation-k0"] == 5
        speech = next(c.state for c in core.components if isinstance(c, ConversationRecord))
        assert len(speech.exchanges) == {"ai": 5, "offline": 0, "timeout": 1}[mode]
        assert len(external.contexts) == len(speech.exchanges)
        if mode == "ai":
            assert speech.exchanges[0].judgment == SpeechJudgment(2, LIE)
        elif mode == "timeout":
            (utterance,) = speech.exchanges
            assert utterance.player_text == f"{LIE}. {PRIVATE}." and not utterance.reply_text
            assert utterance.judgment is None
        segment = owner.retained_segment()
        supply_steps = tuple(
            step for step in segment.trace.steps if isinstance(step.command.payload, SupplyAction)
        )
        assert tuple(step.command.payload for step in supply_steps) == actions
        ticks = []
        for step in supply_steps:
            assert isinstance(step.expected_outcome, TurnCommitted)
            ticks.append(step.expected_outcome.receipt.tick)
        assert ticks == [2, 10, 14, 23]
        assert (
            replay_runner(
                ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace),
                bundles=bundles,
            ).run(segment.trace)
            == ()
        )
        if mode == "ai":
            owner.export("slot02")
            owner.load("slot01")
            assert owner.snapshot().tick == 2
            wait_until(owner, 17)
            commit(owner, PlayerSay(merchant.id, ASK))
            old = context_from_core(owner.snapshot(), world, scenario, social=social)
            assert old.logical_tick == 19 and not old.rumors and not old.observations
            owner.load("slot02")
            assert owner.snapshot() == core
