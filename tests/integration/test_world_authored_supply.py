"""Authored and AI dialogue through the same real supply transaction."""

from pathlib import Path
import sqlite3
import tkinter as tk
from tkinter import ttk
from typing import Literal

import pytest

from adapters.sqlite_store import SqlValue, SqliteCommitStore
from app.client import main
from app.headless import replay_runner, restore_checkpoint
from app.world_catalog import load_social, load_transport, load_world
from app.world_client import WorldMapWindow
from app.world_session import open_world_session, world_checkpoint, world_command
from app.world_transport_registry import transport_world_bundle
from app.world_worker import WorldWorker
from contracts.dialogue import GenerationError
from contracts.replay import ReplayFixture
from contracts.turn import TurnCommitted
from contracts.world_conversation import ConversationContext, ConversationGenerator, GeneratedReply
from contracts.world_supply import SupplyAction
from contracts.world_time import WorldWait
from domain.world_conversation import ConversationRecord
from domain.world_social import SocialRecord
from domain.world_supply import SupplyRecord, SupplyScenario
from tests.integration.test_world_client import _offer_button, _settle, root as root


def no_provider() -> ConversationGenerator:
    raise AssertionError("the authored route initialized a provider")


def authored_choice(root: tk.Tk, window: WorldMapWindow, line: str) -> None:
    before = window.update
    window.offer_button.invoke()
    assert window.offer_panel is not None and window.offer_panel.winfo_exists()
    assert any(
        line in str(widget.cget("text"))
        for widget in window.offer_panel.winfo_children()
        if isinstance(widget, ttk.Label)
    )
    assert window.pending is None and window.update is before
    _offer_button(window, "확인하고 진행").invoke()
    _settle(root, window)


class ControlledReply:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.contexts: list[ConversationContext] = []

    def generate(self, context: ConversationContext) -> GeneratedReply:
        self.contexts.append(context)
        if self.mode == "timeout":
            raise GenerationError("GENERATION_TIMEOUT")
        proposal = "deliver" if self.mode == "wrong_role" else "collect"
        return GeneratedReply("여기요", proposal, "controlled", context.sha256)

    def cancel(self) -> None:
        pass


@pytest.mark.parametrize("mode", ("offline", "timeout", "recorded", "wrong_role"))
def test_authored_quest_and_ai_suggestion_match_objective_effects(
    root: tk.Tk,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: Literal["offline", "timeout", "recorded", "wrong_role"],
) -> None:
    world = load_world()
    social, transport = load_social(world), load_transport(world)
    scenario = SupplyScenario(start_tick=1)
    provider = ControlledReply(mode)
    path = tmp_path / "authored.sqlite"
    worker = WorldWorker(
        path,
        world,
        scenario=scenario,
        social=social,
        transport=transport,
        authored_supply=True,
        live_npc=mode != "offline",
        generator_factory=no_provider if mode == "offline" else lambda: provider,
    )
    now = [0]
    try:
        if mode == "offline":
            for disabled in ("say", "generate", "reply"):
                with pytest.raises(ValueError, match="^WORLD_NPC_AI_DISABLED$"):
                    worker.request(disabled).result(10)
            assert not path.exists()
        window = WorldMapWindow(root, world, worker, now_ns=lambda: now[0])
        _settle(root, window)
        assert window.update is not None and window.update.tick == 0
        assert str(window.offer_button["state"]) == "disabled"
        now[0] += 10_000_000_000
        window.advance_clock()
        _settle(root, window)
        assert window.update.tick == 1
        assert str(window.offer_button["text"]) == "보급 의뢰 대화"
        authored_choice(root, window, "운송인에게 상자 2개")
        assert window.update.tick == 2 and window.update.inventory.gold == 0
        dialogue = window.dialogue
        assert dialogue is not None
        if mode != "offline":
            courier = window.update.residents[0]
            dialogue.selected.set(courier.name)
            dialogue.input.insert("1.0", "상자 주세요")
            dialogue.buttons["send"].invoke()
            _settle(root, window)
            assert len(provider.contexts) == 1
            assert provider.contexts[0].available_action == "collect"
            assert window.update.inventory.items == ()
            if mode == "timeout":
                assert window.update.tick == 3 and not window.dialogue_recovery
                assert "보급 의뢰 대화" in dialogue.status.get()
            elif mode == "wrong_role":
                assert window.update.tick == 3 and window.update.notice == "DIALOGUE_PROPOSAL"
            else:
                assert window.update.tick == 4 and dialogue.offer is not None
        else:
            assert str(dialogue.buttons["send"]["state"]) == "disabled"

        # Align the starting tick of each confirmed supply action for the state comparison.
        now[0] += (4 - window.update.tick) * 10_000_000_000
        window.advance_clock()
        _settle(root, window)
        assert window.update.tick == 4
        if mode == "recorded":
            dialogue.confirm.invoke()
            _settle(root, window)
        else:
            authored_choice(root, window, "상자를 하나 내드릴게요")
        assert window.update.tick == 5 and window.update.inventory.items == (
            ("item:supply-p0-a", 1),
        )
        authored_choice(root, window, "상자를 하나 내드릴게요")
        assert window.update.tick == 6 and window.update.inventory.items == (
            ("item:supply-p0-a", 2),
        )

        if mode == "offline":
            original = SqliteCommitStore._execute
            previous_bytes = path.read_bytes()
            failures: list[str] = []

            def execute(
                store: SqliteCommitStore, query: str, values: tuple[SqlValue, ...] = ()
            ) -> sqlite3.Cursor:
                if query.startswith("INSERT INTO replay") and not failures:
                    failures.append(query)
                    raise sqlite3.OperationalError("injected before supply COMMIT")
                return original(store, query, values)

            with monkeypatch.context() as patch:
                patch.setattr(SqliteCommitStore, "_execute", execute)
                authored_choice(root, window, "필요한 상자가 다 모였네요")
            failed = window.supply_error
            assert failures and failed and window.supply_command is not None
            assert path.read_bytes() == previous_bytes
            assert window.update.tick == 6 and window.update.inventory.gold == 0
            key = window.supply_request_key
            window.retry_supply.invoke()
            _settle(root, window)
            assert not window.supply_error and window.supply_request_key == key
        else:
            authored_choice(root, window, "필요한 상자가 다 모였네요")

        assert window.update.tick == 7
        delivered_inventory = window.update.inventory
        assert delivered_inventory.gold == 5 and not delivered_inventory.items
        assert not window.update.offers
        assert "덕분에 보급로가 다시 열렸어요" in window.supply_text.get()
        assert len(provider.contexts) == int(mode != "offline")
        window.buttons[2].invoke()
        _settle(root, window)
        assert "저장했습니다" in window.status.get()
        window.dispose()
    finally:
        worker.close()

    bundles = (transport_world_bundle(world, social, transport, scenario),)
    with open_world_session(
        path, world, supply=scenario, social=social, transport=transport
    ) as owner:
        core = owner.snapshot()
        speech = next(c.state for c in core.components if isinstance(c, ConversationRecord))
        assert len(speech.exchanges) == int(mode != "offline")
        if mode != "offline":
            assert speech.exchanges[0].player_text == "상자 주세요"
            assert speech.exchanges[0].reply_text == ("여기요" if mode == "recorded" else "")
        city = next(
            c.state
            for c in core.components
            if isinstance(c, SupplyRecord) and c.entity_id == scenario.place_id
        )
        assert (city.stage, city.repair_used, city.treasury, city.resolved_tick) == (2, 2, 10, 7)
        merit = next(c.state for c in core.components if isinstance(c, SocialRecord))
        assert merit.credited_places == ("place:p0-a",)
        assert dict(merit.reputation)["faction:city-p0-a"] == 20
        assert dict(merit.reputation)["faction:nation-k0"] == 5
        segment = owner.retained_segment()
        fixture = ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace)
        assert replay_runner(fixture, bundles=bundles).run(segment.trace) == ()
        supply_commands = tuple(
            step.command.payload
            for step in segment.trace.steps
            if isinstance(step.command.payload, SupplyAction)
        )
        assert tuple(c.operation for c in supply_commands) == (
            "accept",
            "collect",
            "collect",
            "deliver",
        )
        owner.load("slot01")
        assert owner.snapshot() == core

    initial = world_checkpoint(world, supply=scenario, social=social, transport=transport)
    direct = restore_checkpoint(initial.core, initial.protocol, bundles=bundles)
    accept, collect_one, collect_two, deliver = supply_commands
    for action in (WorldWait(1), accept, WorldWait(2), collect_one, collect_two, deliver):
        assert isinstance(
            direct.driver.submit(world_command(direct.protocol(), action)), TurnCommitted
        )
    assert direct.snapshot().tick == core.tick == 7
    assert tuple(c for c in core.components if not isinstance(c, ConversationRecord)) == tuple(
        c for c in direct.snapshot().components if not isinstance(c, ConversationRecord)
    )


def test_reopening_offline_can_finish_saved_speech(root: tk.Tk, tmp_path: Path) -> None:
    world = load_world()
    scenario = SupplyScenario(start_tick=1)
    path = tmp_path / "speech.sqlite"
    worker = WorldWorker(
        path, world, scenario=scenario, conversation=True, generator_factory=no_provider
    )
    try:
        update = worker.request("wait", seconds=1).result(10)
        worker.request(
            "say", npc_id=update.residents[1].resident_id, text="가" * 100, request_key="say"
        ).result(10)
    finally:
        worker.close()
    worker = WorldWorker(
        path,
        world,
        scenario=scenario,
        conversation=True,
        authored_supply=True,
        live_npc=False,
        generator_factory=no_provider,
    )
    try:
        window = WorldMapWindow(root, world, worker, now_ns=lambda: 0)
        _settle(root, window)
        assert window.update is not None and window.update.tick == 17
        assert window.dialogue is not None
        window.dialogue.buttons["speech"].invoke()
        _settle(root, window)
        assert window.update.tick == 18
        assert window.update.conversation is not None and window.update.conversation.remaining == 0
        assert not window.update.conversation.exchanges[0].reply_text
        authored_choice(root, window, "운송인에게 상자 2개")
        assert window.update.tick == 19 and window.update.offers[0].action.operation == "collect"
        window.dispose()
    finally:
        worker.close()


def test_authored_cli_opens_its_own_save_and_rejects_other_options(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(tk.Tk, "mainloop", lambda self: None)
    assert main(["--world-authored"]) == 0
    assert main(["--world-authored", "--npc-ai"]) == 0
    assert (tmp_path / "tmp/world-authored-supply-play/game.sqlite").is_file()
    assert not (tmp_path / "tmp/world-transport-play").exists()
    for flags in (
        ["--npc-ai"],
        ["--world", "--world-authored"],
        ["--world-authored", "--npc-ai", "--npc-ai"],
        ["--world-authored", "--npc-memory"],
    ):
        with pytest.raises(SystemExit, match="2"):
            main(flags)
