"""Ordinary Tk confirmations,slow clock and durable social-command recovery."""

from collections.abc import Iterator
from pathlib import Path
import gc
import sqlite3
import time
import tkinter as tk

import pytest

from adapters.sqlite_store import SqliteCommitStore
from app.world_catalog import load_social, load_world
from app.world_client import WorldMapWindow
from app.world_worker import WorldUpdate, WorldWorker
from contracts.persistence import DurableTurn, RecoveryResult, SaveError
from contracts.turn import CommitReceipt
from contracts.world_conversation import ConversationContext, GeneratedReply
from contracts.world_social import SocialAction
from domain.world_supply import SupplyScenario


@pytest.fixture
def root() -> Iterator[tk.Tk]:
    window = tk.Tk()
    try:
        yield window
    finally:
        window.destroy()
        gc.collect()


def settle(root: tk.Tk, window: WorldMapWindow) -> None:
    deadline = time.monotonic() + 10
    while window.pending is not None and time.monotonic() < deadline:
        root.update()
        time.sleep(0.002)
    assert window.pending is None


def test_actual_panel_confirmation_map_idle_pause_and_identity(root: tk.Tk, tmp_path: Path) -> None:
    world = load_world()
    worker = WorldWorker(tmp_path / "social.sqlite", world, social=load_social(world))
    clock = [0]
    try:
        window = WorldMapWindow(root, world, worker, now_ns=lambda: clock[0])
        settle(root, window)
        panel = window.social_panel
        assert panel is not None and window.update is not None
        panel.show()
        assert not str(root.tk.call("grab", "current"))
        before = window.update
        window.map.select_place("place:p0-b")
        assert window.update == before and "평판" in window.details.get()
        panel.buttons["protest"].invoke()
        assert window.update.tick == 0 and "-15" in panel.terms.get()
        clock[0] = 20_000_000_000
        panel.confirm.invoke()
        clock[0] = 920_000_000_000
        settle(root, window)
        assert window.update.tick == 7  # prior idle2 + explicit protest5;processing0.
        assert window.update.social is not None
        assert dict(window.update.social.reputation)["faction:city-p0-a"] == -15
        panel.buttons["protest"].invoke()
        panel.confirm.invoke()
        settle(root, window)
        assert window.update.tick == 12
        window.map.select_place("place:p0-a")
        assert "새 의뢰 제한" in window.details.get()
        window.toggle_pause()
        clock[0] += 100_000_000_000
        window.advance_clock()
        assert window.update.tick == 12 and window.pending is None
        assert str(panel.buttons["reconcile"]["state"]) == "disabled"
        window.toggle_pause()
        for _ in range(2):
            panel.buttons["reconcile"].invoke()
            panel.confirm.invoke()
            settle(root, window)
        assert window.update.tick == 32 and "입장·새 의뢰 가능" in window.details.get()
        panel.ancestry.set("인간")
        panel.country.set("국적 없음")
        panel.buttons["identify"].invoke()
        assert not window.update.social.ancestry_id
        panel.confirm.invoke()
        settle(root, window)
        assert window.update.tick == 33 and "내 종족: 인간" in panel.info.get("1.0", "end")
        stored = worker.request("inspect").result(10).social
        assert stored is not None and stored.ancestry_id == "ancestry:human"
        assert str(panel.buttons["identify"]["state"]) == "disabled"
        assert "국가 간 외교" in panel.info.get("1.0", "end")
        window.dispose()
    finally:
        worker.close()


def test_gui_postcommit_render_failure_retries_same_social_action(
    root: tk.Tk, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    world = load_world()
    worker = WorldWorker(tmp_path / "ack.sqlite", world, social=load_social(world))
    try:
        window = WorldMapWindow(root, world, worker, now_ns=lambda: 0)
        settle(root, window)
        panel = window.social_panel
        assert panel is not None
        original = WorldMapWindow.render
        failed = [False]

        def render(view: WorldMapWindow, update: WorldUpdate) -> None:
            if view.pending_action == "social" and not failed[0]:
                failed[0] = True
                raise ValueError("injected social presentation failure")
            original(view, update)

        monkeypatch.setattr(WorldMapWindow, "render", render)
        panel.buttons["protest"].invoke()
        panel.confirm.invoke()
        settle(root, window)
        assert (
            failed[0] and window.social_error and window.social_command == SocialAction("protest")
        )
        window.advance_clock()
        assert window.pending is None
        panel.retry.invoke()
        settle(root, window)
        assert not window.social_error and window.social_command is None
        assert (
            window.update is not None
            and window.update.tick == 5
            and window.update.social is not None
        )
        assert dict(window.update.social.reputation)["faction:city-p0-a"] == -15
        window.dispose()
    finally:
        worker.close()


@pytest.mark.parametrize("uncertain", (False, True), ids=("confirmed-rollback", "uncertain-commit"))
def test_real_sqlite_social_retry_preserves_exact_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, uncertain: bool
) -> None:
    world = load_world()
    worker = WorldWorker(tmp_path / "retry.sqlite", world, social=load_social(world))
    try:
        worker.request("inspect").result(10)
        failed = [False]
        if uncertain:
            persist_original, recover_original = (
                SqliteCommitStore.persist,
                SqliteCommitStore.recover,
            )
            recovery_failed = [False]

            def persist(store: SqliteCommitStore, turn: DurableTurn) -> CommitReceipt:
                receipt = persist_original(store, turn)
                if isinstance(turn.command.payload, SocialAction) and not failed[0]:
                    failed[0] = True
                    raise OSError("after real social commit")
                return receipt

            def recover(store: SqliteCommitStore, turn: DurableTurn) -> RecoveryResult:
                if not recovery_failed[0]:
                    recovery_failed[0] = True
                    raise OSError("recovery unavailable once")
                return recover_original(store, turn)

            monkeypatch.setattr(SqliteCommitStore, "persist", persist)
            monkeypatch.setattr(SqliteCommitStore, "recover", recover)
        else:
            execute_original = SqliteCommitStore._execute

            def execute(
                store: SqliteCommitStore,
                query: str,
                values: tuple[None | int | float | str | bytes, ...] = (),
            ) -> sqlite3.Cursor:
                result = execute_original(store, query, values)
                if query.startswith("INSERT INTO replay") and not failed[0]:
                    failed[0] = True
                    raise sqlite3.IntegrityError("social replay insert rollback")
                return result

            monkeypatch.setattr(SqliteCommitStore, "_execute", execute)
        with pytest.raises(
            SaveError, match="^SAVE_UNCERTAIN:" if uncertain else "^SAVE_UNAVAILABLE:"
        ):
            worker.request(
                "social", social_action=SocialAction("protest"), request_key="fixed"
            ).result(10)
        with pytest.raises(SaveError, match="WORLD_DIALOGUE_PENDING"):
            worker.request(
                "social", social_action=SocialAction("reconcile"), request_key="other"
            ).result(10)
        restored = worker.request(
            "social", social_action=SocialAction("protest"), request_key="fixed"
        ).result(10)
        assert failed[0] and restored.tick == 5 and restored.social is not None
        assert dict(restored.social.reputation)["faction:city-p0-a"] == -15
        assert (
            worker.request(
                "social", social_action=SocialAction("protest"), request_key="fixed"
            ).result(10)
            == restored
        )
    finally:
        worker.close()


def test_worker_generation_and_reply_share_social_context(tmp_path: Path) -> None:
    contexts: list[ConversationContext] = []

    class RecordedProvider:
        def generate(self, context: ConversationContext) -> GeneratedReply:
            contexts.append(context)
            return GeneratedReply("현재 관계를 기억합니다.", "none", "fixture", context.sha256)

        def cancel(self) -> None:
            pass

    world = load_world()
    catalog = load_social(world)
    worker = WorldWorker(
        tmp_path / "context.sqlite", world, social=catalog, generator_factory=RecordedProvider
    )
    try:
        worker.request(
            "social",
            social_action=SocialAction("identify", "ancestry:human", "country:k2"),
            request_key="identity",
        ).result(10)
        npc = next(r for r in catalog.residents if r.place_id == "place:p0-a")
        worker.request(
            "say", npc_id=npc.npc_id, text="우리는 어떤 관계인가요?", request_key="say"
        ).result(10)
        ready = worker.request("generate", request_key="generate").result(10)
        assert ready.reply_ready and len(contexts) == 1
        facts = dict(contexts[0].public_facts)
        assert facts["player_ancestry"] == "인간" and facts["player_citizenship"] == "백로 공국"
        assert facts["social_reaction"] == "20"
        assert facts["npc_organization"] == "물버들 생활조합"
        assert "현재 관계: 우호" in facts["organization_public_standing"]
        assert facts["current_city_policy"] == "현재 관계로 인한 새 의뢰·입장 제한은 없다."
        accepted = worker.request("reply", request_key="reply").result(10)
        assert accepted.speech_committed and accepted.conversation is not None
        assert accepted.conversation.exchanges[-1].reply_text == "현재 관계를 기억합니다."
    finally:
        worker.close()


def test_hostility_keeps_existing_supply_collection_delivery_and_real_merit(tmp_path: Path) -> None:
    world = load_world()
    worker = WorldWorker(
        tmp_path / "cargo.sqlite",
        world,
        social=load_social(world),
        scenario=SupplyScenario(start_tick=1),
    )
    try:
        initial = worker.request("wait", seconds=1, request_key="start").result(10)
        assert initial.offers and initial.offers[0].action.operation == "accept"
        worker.request("supply", supply=initial.offers[0].action, request_key="accept").result(10)
        for i in range(2):
            hostile = worker.request(
                "social", social_action=SocialAction("protest"), request_key=f"protest-{i}"
            ).result(10)
        assert (
            hostile.social is not None
            and dict(hostile.social.reputation)["faction:city-p0-a"] == -30
        )
        assert hostile.offers[0].action.operation == "collect"
        update = hostile
        for i in range(3):
            update = worker.request(
                "supply", supply=update.offers[0].action, request_key=f"cargo-{i}"
            ).result(10)
        assert update.tick == 15 and update.inventory.gold == 5 and update.inventory.items == ()
        assert update.social is not None and update.social.credited_places == ("place:p0-a",)
        assert dict(update.social.reputation)["faction:city-p0-a"] == -10
        assert dict(update.social.reputation)["faction:nation-k0"] == -5
    finally:
        worker.close()
