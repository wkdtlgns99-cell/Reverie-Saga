"""Actual worker/Tk speech,external transport fixtures and durable retry boundaries."""

from collections.abc import Callable, Iterator
from pathlib import Path
import gc
import sqlite3
from threading import Event
import time
import tkinter as tk

import pytest

from adapters.generation_budget import GenerationBudget
from adapters.sqlite_store import SqliteCommitStore
from adapters.world_conversation import GeminiConversation
from app.world_catalog import load_world
from app.world_client import WorldMapWindow
from app.world_worker import WorldAction, WorldUpdate, WorldWorker
from contracts.dialogue import GenerationError
from contracts.persistence import DurableTurn, RecoveryResult, SaveError
from contracts.turn import CommitReceipt
from contracts.world_conversation import ConversationGenerator, NpcReply, PlayerSay
from domain.canonical import JsonObject, canonical_json
from domain.world import elaborate_place
from domain.world_supply import SupplyScenario


@pytest.fixture
def root() -> Iterator[tk.Tk]:
    window = tk.Tk()
    try:
        yield window
    finally:
        window.destroy()
        gc.collect()


def factory(
    path: Path,
    *,
    text: str = "안녕하세요.",
    proposal: str = "none",
    send: Callable[[JsonObject, str, Event], JsonObject] | None = None,
) -> Callable[[], ConversationGenerator]:
    def transport(request: JsonObject, key: str, cancelled: Event) -> JsonObject:
        return {
            "candidates": (
                {
                    "finishReason": "STOP",
                    "content": {
                        "parts": (
                            {
                                "text": canonical_json(
                                    {"text_ko": text, "proposal_operation": proposal}
                                ).decode("utf-8"),
                            },
                        )
                    },
                },
            ),
            "modelVersion": "recorded-test",
            "usageMetadata": {"totalTokenCount": 123},
        }

    return lambda: GeminiConversation(
        "fixture",
        GenerationBudget(path, spacing_ms=0),
        free_tier_confirmed=True,
        free_data_use_confirmed=True,
        send=send or transport,
    )


def settle(root: tk.Tk, window: WorldMapWindow) -> None:
    deadline = time.monotonic() + 10
    while window.pending is not None and time.monotonic() < deadline:
        root.update()
        time.sleep(0.002)
    assert window.pending is None


def test_worker_segments_one_reply_save_load_restart_and_ack_identity(tmp_path: Path) -> None:
    world = load_world()
    path = tmp_path / "world.sqlite"
    npc = elaborate_place(world, world.places[0].id).residents[0]
    worker = WorldWorker(
        path, world, conversation=True, generator_factory=factory(tmp_path / "budget")
    )
    try:
        said = worker.request("say", npc_id=npc.id, text="가" * 100, request_key="say").result(10)
        assert (
            said.tick == 16 and said.conversation is not None and said.conversation.remaining == 1
        )
        assert (
            worker.request("say", npc_id=npc.id, text="가" * 100, request_key="say").result(10)
            == said
        )
        with pytest.raises(SaveError, match="WORLD_DIALOGUE_PENDING"):
            worker.request("say", npc_id=npc.id, text="다른 말", request_key="say").result(10)
        finished = worker.request("speech", request_key="finish").result(10)
        assert finished.tick == 17
        worker.request("save").result(10)
        generated = worker.request("generate", request_key="gen").result(10)
        assert generated.reply_ready and generated.tick == 17
        assert generated.inventory.gold == 0 and generated.inventory.items == ()
        replied = worker.request("reply", request_key="reply").result(10)
        assert replied.tick == 18 and replied.conversation is not None
        assert len(replied.conversation.exchanges) == 1
        assert replied.conversation.exchanges[0].reply_text == "안녕하세요."
        assert worker.request("reply", request_key="reply").result(10) == replied
        loaded = worker.request("load").result(10)
        assert loaded.tick == 17 and loaded.conversation == finished.conversation
        with pytest.raises(ValueError, match="DIALOGUE_CONTEXT_STALE"):
            worker.request("reply", request_key="stale").result(10)
    finally:
        worker.close()
    resumed = WorldWorker(
        path, world, conversation=True, generator_factory=factory(tmp_path / "budget")
    )
    try:
        restored = resumed.request("inspect").result(10)
        assert restored.tick == 17 and restored.conversation == finished.conversation
    finally:
        resumed.close()


def test_real_gui_speech_idle_and_provider_time_no_unconfirmed_action(
    root: tk.Tk, tmp_path: Path
) -> None:
    clock = [0]
    worker = WorldWorker(
        tmp_path / "world.sqlite",
        load_world(),
        conversation=True,
        scenario=SupplyScenario(start_tick=1),
        generator_factory=factory(
            tmp_path / "budget", text="복구 의뢰를 도와주시겠어요?", proposal="accept"
        ),
    )
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: clock[0])
        settle(root, window)
        panel = window.dialogue
        assert panel is not None
        panel.selected.set(tuple(panel.identifiers)[1])
        panel.input.insert("1.0", "의뢰를 알려주세요")
        clock[0] = 20_000_000_000
        panel.buttons["send"].invoke()
        clock[0] = 920_000_000_000  # Processing/provider wait contributes no extra90seconds.
        settle(root, window)
        assert window.update is not None and window.update.conversation is not None
        state = window.update.conversation
        assert len(state.exchanges) == 1 and state.exchanges[0].player_start == 2
        assert window.update.tick == state.exchanges[0].reply_end < 20
        assert panel.text() == "" and panel.offer is not None
        assert window.update.inventory.gold == 0 and window.update.inventory.items == ()
        assert "확인" in panel.terms.get() and panel.offer.action.operation == "accept"
        tick = window.update.tick
        panel.confirm.invoke()
        settle(root, window)
        assert window.update.tick == tick + 1
        assert window.update.offers[0].action.operation == "collect"
        assert window.update.inventory.gold == 0
    finally:
        worker.close()


def test_real_gui_pause_between_segments_and_restart_continue(root: tk.Tk, tmp_path: Path) -> None:
    path = tmp_path / "world.sqlite"
    worker = WorldWorker(
        path, load_world(), conversation=True, generator_factory=factory(tmp_path / "budget")
    )
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: 0)
        settle(root, window)
        panel = window.dialogue
        assert panel is not None
        panel.input.insert("1.0", "가" * 100)
        panel.buttons["send"].invoke()
        window.toggle_pause()
        settle(root, window)
        assert window.update is not None and window.update.tick == 16
        assert window.update.conversation is not None and window.update.conversation.remaining == 1
        assert window.dialogue_next == "speech" and window.pending is None
        window.close()
    finally:
        worker.close()
    resumed = WorldWorker(
        path, load_world(), conversation=True, generator_factory=factory(tmp_path / "budget")
    )
    try:
        restored = resumed.request("inspect").result(10)
        assert restored.tick == 16 and not restored.reply_ready
        continued = resumed.request("speech", request_key="explicit").result(10)
        assert continued.tick == 17 and continued.conversation is not None
        assert not continued.conversation.exchanges[0].reply_text
    finally:
        resumed.close()


def test_real_gui_provider_error_preserves_input_and_retry_does_not_repeat_speech(
    root: tk.Tk, tmp_path: Path
) -> None:
    attempts = [0]
    good = factory(tmp_path / "budget")

    def fail(request: JsonObject, key: str, cancelled: Event) -> JsonObject:
        raise GenerationError("GENERATION_TIMEOUT")

    bad = factory(tmp_path / "budget", send=fail)

    def generators() -> ConversationGenerator:
        attempts[0] += 1
        return bad() if attempts[0] == 1 else good()

    worker = WorldWorker(
        tmp_path / "world.sqlite", load_world(), conversation=True, generator_factory=generators
    )
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: 0)
        settle(root, window)
        panel = window.dialogue
        assert panel is not None
        panel.input.insert("1.0", "가")
        panel.buttons["send"].invoke()
        settle(root, window)
        assert "시간이 초과" in panel.status.get() and not window.dialogue_recovery
        assert window.update is not None and window.update.tick == 1
        assert window.update.conversation is not None
        assert window.update.conversation.exchanges[0].player_text == "가"
        panel.input.insert("1.0", "다음 발언 초안")
        panel.buttons["retry"].invoke()
        settle(root, window)
        assert attempts == [2] and len(window.update.conversation.exchanges) == 1
        assert window.update.tick == 2 and panel.text() == "다음 발언 초안"
        panel.input.delete("1.0", "end")
        panel.input.insert("1.0", " " * 5)
        panel.buttons["send"].invoke()
        assert panel.text() == " " * 5 and window.update.tick == 2
    finally:
        worker.close()


@pytest.mark.parametrize("reply", (False, True), ids=("player", "npc"))
def test_uncertain_real_sqlite_speech_retry_is_exactly_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reply: bool,
) -> None:
    worker = WorldWorker(
        tmp_path / "world.sqlite",
        load_world(),
        conversation=True,
        generator_factory=factory(tmp_path / "budget"),
    )
    npc = elaborate_place(load_world(), "place:p0-a").residents[0]
    try:
        worker.request("inspect").result(10)
        if reply:
            worker.request("say", npc_id=npc.id, text="안녕", request_key="say").result(10)
            worker.request("generate", request_key="gen").result(10)
        persist_original, recover_original = SqliteCommitStore.persist, SqliteCommitStore.recover
        persisted, recovery_failed = [False], [False]

        def persist(store: SqliteCommitStore, turn: DurableTurn) -> CommitReceipt:
            receipt = persist_original(store, turn)
            if not persisted[0] and isinstance(
                turn.command.payload, NpcReply if reply else PlayerSay
            ):
                persisted[0] = True
                raise OSError("after real speech commit")
            return receipt

        def recover(store: SqliteCommitStore, turn: DurableTurn) -> RecoveryResult:
            if not recovery_failed[0]:
                recovery_failed[0] = True
                raise OSError("speech recovery unavailable once")
            return recover_original(store, turn)

        monkeypatch.setattr(SqliteCommitStore, "persist", persist)
        monkeypatch.setattr(SqliteCommitStore, "recover", recover)
        action: WorldAction = "reply" if reply else "say"
        with pytest.raises(SaveError):
            worker.request(action, npc_id=npc.id, text="안녕", request_key="uncertain").result(10)
        result = worker.request(action, npc_id=npc.id, text="안녕", request_key="uncertain").result(
            10
        )
        assert persisted[0] and recovery_failed[0]
        assert result.tick == (2 if reply else 1) and result.conversation is not None
        assert len(result.conversation.exchanges) == 1
        assert bool(result.conversation.exchanges[0].reply_text) is reply
    finally:
        worker.close()


def test_real_gui_reply_ack_failure_retries_saved_generated_reply_without_new_call(
    root: tk.Tk,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = [0]
    make = factory(tmp_path / "budget")

    def generator() -> ConversationGenerator:
        calls[0] += 1
        return make()

    worker = WorldWorker(
        tmp_path / "world.sqlite", load_world(), conversation=True, generator_factory=generator
    )
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: 0)
        settle(root, window)
        panel = window.dialogue
        assert panel is not None
        original = WorldMapWindow.render
        failed = [False]

        def render(w: WorldMapWindow, update: WorldUpdate) -> None:
            if (
                update.conversation
                and update.conversation.exchanges
                and update.conversation.exchanges[-1].reply_text
                and not failed[0]
            ):
                failed[0] = True
                raise ValueError("injected reply acknowledgement failure")
            original(w, update)

        monkeypatch.setattr(WorldMapWindow, "render", render)
        panel.input.insert("1.0", "안녕")
        panel.buttons["send"].invoke()
        settle(root, window)
        assert failed[0] and window.dialogue_recovery and calls == [1]
        panel.buttons["recover"].invoke()
        settle(root, window)
        assert not window.dialogue_recovery and calls == [1]
        assert window.update is not None and window.update.tick == 2
        assert (
            window.update.conversation is not None
            and len(window.update.conversation.exchanges) == 1
        )
    finally:
        worker.close()


def test_paused_provider_result_waits_for_resume_before_reply_commit(
    root: tk.Tk, tmp_path: Path
) -> None:
    entered, release = Event(), Event()

    def transport(request: JsonObject, key: str, cancelled: Event) -> JsonObject:
        entered.set()
        assert release.wait(5)
        return {
            "candidates": (
                {
                    "finishReason": "STOP",
                    "content": {
                        "parts": ({"text": '{"text_ko":"안녕","proposal_operation":"none"}'},)
                    },
                },
            ),
            "usageMetadata": {"totalTokenCount": 10},
        }

    worker = WorldWorker(
        tmp_path / "world.sqlite",
        load_world(),
        conversation=True,
        generator_factory=factory(tmp_path / "budget", send=transport),
    )
    clock = [0]
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: clock[0])
        settle(root, window)
        panel = window.dialogue
        assert panel is not None
        panel.input.insert("1.0", "안녕")
        panel.buttons["send"].invoke()
        deadline = time.monotonic() + 5
        while not entered.is_set() and time.monotonic() < deadline:
            root.update()
            time.sleep(0.002)
        assert entered.is_set() and window.pending_action == "generate"
        window.toggle_pause()
        clock[0] = 600_000_000_000
        release.set()
        settle(root, window)
        assert window.update is not None and window.update.tick == 1
        assert window.update.reply_ready and window.dialogue_next == "reply"
        assert (
            window.update.conversation is not None
            and not window.update.conversation.exchanges[0].reply_text
        )
        window.toggle_pause()
        settle(root, window)
        assert window.update.tick == 2
        assert [e.reply_text for e in window.update.conversation.exchanges] == ["안녕"]
    finally:
        release.set()
        worker.close()


def test_worker_cancel_and_close_interrupt_only_owned_provider_wait(tmp_path: Path) -> None:
    entered = Event()
    calls: list[str] = []

    def transport(request: JsonObject, key: str, cancelled: Event) -> JsonObject:
        calls.append(key)
        entered.set()
        assert cancelled.wait(5)
        raise GenerationError("GENERATION_CANCELLED")

    worker = WorldWorker(
        tmp_path / "world.sqlite",
        load_world(),
        conversation=True,
        generator_factory=factory(tmp_path / "budget", send=transport),
    )
    npc = elaborate_place(load_world(), "place:p0-a").residents[0]
    worker.request("say", npc_id=npc.id, text="안녕", request_key="say").result(10)
    pending = worker.request("generate", request_key="gen")
    assert entered.wait(5)
    start = time.monotonic()
    worker.close()
    assert time.monotonic() - start < 2 and calls == ["fixture"]
    with pytest.raises(GenerationError, match="GENERATION_CANCELLED"):
        pending.result(2)
    resumed = WorldWorker(tmp_path / "world.sqlite", load_world(), conversation=True)
    try:
        result = resumed.request("inspect").result(10)
        assert result.tick == 1 and result.conversation is not None
        assert result.conversation.exchanges[0].player_text == "안녕"
        assert not result.conversation.exchanges[0].reply_text
    finally:
        resumed.close()


def test_long_npc_speech_pauses_at_segment_and_resumes_exact_duration(
    root: tk.Tk,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker = WorldWorker(
        tmp_path / "world.sqlite",
        load_world(),
        conversation=True,
        generator_factory=factory(tmp_path / "budget", text="답" * 100),
    )
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: 0)
        settle(root, window)
        panel = window.dialogue
        assert panel is not None
        panel.selected.set(tuple(panel.identifiers)[1])  # Saved cautious merchant:4codepoints/s.
        original = WorldMapWindow.render
        held = [False]

        def render(w: WorldMapWindow, update: WorldUpdate) -> None:
            original(w, update)
            if update.conversation and update.conversation.speaker == "npc" and not held[0]:
                held[0] = True
                w.toggle_pause()

        monkeypatch.setattr(WorldMapWindow, "render", render)
        panel.input.insert("1.0", "안녕")  # Player2/6ceil=1s;NPC100/4=25s.
        panel.buttons["send"].invoke()
        settle(root, window)
        assert held[0] and window.update is not None and window.update.tick == 17
        assert window.update.conversation is not None and window.update.conversation.remaining == 9
        window.toggle_pause()
        settle(root, window)
        assert window.update.tick == 26 and window.update.conversation.remaining == 0
        assert len(window.update.conversation.exchanges) == 1
        assert window.update.conversation.exchanges[0].reply_text == "답" * 100
    finally:
        worker.close()


def test_real_dialogue_cancel_remains_responsive_and_keeps_heard_speech(
    root: tk.Tk, tmp_path: Path
) -> None:
    entered = Event()

    def transport(request: JsonObject, key: str, cancelled: Event) -> JsonObject:
        entered.set()
        assert cancelled.wait(5)
        raise GenerationError("GENERATION_CANCELLED")

    worker = WorldWorker(
        tmp_path / "world.sqlite",
        load_world(),
        conversation=True,
        generator_factory=factory(tmp_path / "budget", send=transport),
    )
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: 0)
        settle(root, window)
        panel = window.dialogue
        assert panel is not None
        panel.input.insert("1.0", "안녕")
        panel.buttons["send"].invoke()
        deadline = time.monotonic() + 5
        while not entered.is_set() and time.monotonic() < deadline:
            root.update()
            time.sleep(0.002)
        assert entered.is_set()
        panel.buttons["cancel"].invoke()
        settle(root, window)
        assert "취소" in panel.status.get()
        assert window.update is not None and window.update.tick == 1
        assert (
            window.update.conversation is not None
            and not window.update.conversation.exchanges[0].reply_text
        )
        panel.buttons["skip"].invoke()
        window.buttons[0].invoke()
        settle(root, window)
        assert window.update.tick == 2 and window.update.state.offset_m == 1
        window.close()
        assert window.closed
    finally:
        worker.close()


def test_dialogue_minimum_geometry_keeps_terms_input_and_controls_accessible(
    root: tk.Tk, tmp_path: Path
) -> None:
    worker = WorldWorker(
        tmp_path / "world.sqlite",
        load_world(),
        conversation=True,
        scenario=SupplyScenario(start_tick=1),
        generator_factory=factory(
            tmp_path / "budget", text="의뢰를 제안합니다.", proposal="accept"
        ),
    )
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: 0)
        settle(root, window)
        panel = window.dialogue
        assert panel is not None
        panel.selected.set(tuple(panel.identifiers)[1])
        panel.input.insert("1.0", "의뢰")
        panel.buttons["send"].invoke()
        settle(root, window)
        panel.panel.geometry("450x600")
        root.update()
        assert panel.offer is not None
        for widget in (panel.input, panel.confirm, *panel.buttons.values()):
            assert widget.winfo_ismapped()
            assert widget.winfo_rootx() >= panel.panel.winfo_rootx()
            assert widget.winfo_rooty() >= panel.panel.winfo_rooty()
            assert (
                widget.winfo_rootx() + widget.winfo_width()
                <= panel.panel.winfo_rootx() + panel.panel.winfo_width()
            )
            assert (
                widget.winfo_rooty() + widget.winfo_height()
                <= panel.panel.winfo_rooty() + panel.panel.winfo_height()
            )
    finally:
        worker.close()


def test_confirmed_reply_sql_rollback_keeps_generated_reply_for_storage_retry(
    root: tk.Tk,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = [0]
    make = factory(tmp_path / "budget")

    def generator() -> ConversationGenerator:
        calls[0] += 1
        return make()

    worker = WorldWorker(
        tmp_path / "world.sqlite", load_world(), conversation=True, generator_factory=generator
    )
    try:
        window = WorldMapWindow(root, load_world(), worker, now_ns=lambda: 0)
        settle(root, window)
        panel = window.dialogue
        assert panel is not None
        original = SqliteCommitStore._execute
        writes = [0]

        def execute(
            store: SqliteCommitStore,
            query: str,
            values: tuple[None | int | float | str | bytes, ...] = (),
        ) -> sqlite3.Cursor:
            result = original(store, query, values)
            if query.startswith("INSERT INTO replay"):
                writes[0] += 1
                if writes[0] == 2:  # Real player commit succeeds;NPC replay insert rolls back.
                    raise sqlite3.IntegrityError("injected reply transaction rollback")
            return result

        monkeypatch.setattr(SqliteCommitStore, "_execute", execute)
        panel.input.insert("1.0", "안녕")
        panel.buttons["send"].invoke()
        settle(root, window)
        assert window.dialogue_recovery and calls == [1]
        assert window.update is not None and window.update.tick == 1
        panel.buttons["recover"].invoke()
        settle(root, window)
        assert not window.dialogue_recovery and calls == [1]
        assert window.update.tick == 2 and window.update.conversation is not None
        assert len(window.update.conversation.exchanges) == 1
        assert window.update.conversation.exchanges[0].reply_text == "안녕하세요."
    finally:
        worker.close()
