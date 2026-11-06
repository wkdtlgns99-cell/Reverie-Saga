"""Versioned knowledge through real conversation, supply, save and replay boundaries."""

import gc
from pathlib import Path
import sqlite3
from threading import Event
import tkinter as tk

import pytest

from adapters.generation_budget import GenerationBudget
from adapters.sqlite_store import SqlValue, SqliteCommitStore
from adapters.world_conversation import GeminiConversation, generation_request, parse_reply
from app.client import main
from app.durable import DurableSession, create_durable
from app.headless import replay_runner
from app.world_catalog import load_social, load_transport, load_world
from app.world_client import WorldMapWindow
from app.world_session import open_world_session, world_command
from app.world_transport_registry import transport_world_bundle
from app.world_worker import WorldWorker
from contracts.dialogue import GenerationError
from contracts.messages import CommandPayload
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.replay import ReplayFixture
from contracts.turn import TurnCommitted, TurnRejected
from contracts.world_conversation import AssessedNpcReply, ContinueSpeech, PlayerSay
from contracts.world_supply import SupplyAction
from contracts.world_time import WorldWait
from domain.canonical import JsonObject, JsonValue, canonical_json
from domain.world import elaborate_place
from domain.world_conversation import (
    ConversationRecord,
    ConversationState,
    SpeechJudgment,
)
from domain.world_population import InventoryRecord
from domain.world_supply import SupplyRecord, SupplyScenario
from orchestration.world_conversation_context import context_from_core
from tests.integration.test_world_authored_supply import no_provider
from tests.integration.test_world_client import _settle, root as root


def commit(owner: DurableSession, payload: CommandPayload) -> None:
    result = owner.submit(
        world_command(owner.protocol(), payload), attachment_id=owner.attachment_id
    )
    assert isinstance(result.outcome, TurnCommitted), result


def conversation(owner: DurableSession) -> ConversationState:
    return next(c.state for c in owner.snapshot().components if isinstance(c, ConversationRecord))


def wait_until(owner: DurableSession, tick: int) -> None:
    while owner.snapshot().tick < tick:
        commit(owner, WorldWait(min(16, tick - owner.snapshot().tick)))


def response(importance: JsonValue, quote: str) -> JsonObject:
    return {
        "candidates": (
            {
                "finishReason": "STOP",
                "content": {
                    "parts": (
                        {
                            "text": canonical_json(
                                {
                                    "text_ko": "그런 이야기가 있었군요.",
                                    "proposal_operation": "none",
                                    "importance": importance,
                                    "repeat_quote": quote,
                                }
                            ).decode("utf-8")
                        },
                    )
                },
            },
        ),
        "modelVersion": "controlled-model",
    }


def test_ordinary_tk_speech_commits_a_validated_judgment(root: tk.Tk, tmp_path: Path) -> None:
    # Collect destroyed Tk variables on the UI thread before starting another worker.
    gc.collect()
    world = load_world()
    social, transport = load_social(world), load_transport(world)
    scenario = SupplyScenario(start_tick=1)
    requests: list[JsonObject] = []

    def send(request: JsonObject, key: str, cancelled: Event) -> JsonObject:
        assert key == "fixture-key" and not cancelled.is_set()
        requests.append(request)
        return response(3, "다시 돌아올게")

    worker = WorldWorker(
        tmp_path / "quest.sqlite",
        world,
        scenario=scenario,
        social=social,
        transport=transport,
        authored_supply=True,
        knowledge=True,
        generator_factory=lambda: GeminiConversation(
            "fixture-key",
            GenerationBudget(tmp_path / "budget", spacing_ms=0),
            free_tier_confirmed=True,
            free_data_use_confirmed=True,
            send=send,
        ),
    )
    try:
        window = WorldMapWindow(root, world, worker, now_ns=lambda: 0)
        _settle(root, window)
        assert window.update is not None and window.dialogue is not None
        panel = window.dialogue
        panel.selected.set(window.update.residents[0].name)
        panel.input.insert("1.0", "다시 돌아올게. 북쪽 창고는 비밀이야.")
        panel.buttons["send"].invoke()
        _settle(root, window)
        update = window.update
        assert update.conversation is not None
        entry = update.conversation.exchanges[-1]
        assert entry.judgment == SpeechJudgment(3, "다시 돌아올게")
        assert entry.reply_text == "그런 이야기가 있었군요."
        assert len(requests) == 1 and "repeat_quote" in canonical_json(requests[0]).decode("utf-8")
        window.dispose()
    finally:
        worker.close()


def test_delayed_rumor_has_source_and_stays_on_its_branch(tmp_path: Path) -> None:
    world = load_world()
    social, transport = load_social(world), load_transport(world)
    scenario = SupplyScenario(start_tick=1)
    place = world.places[0].id
    residents = sorted(elaborate_place(world, place).residents, key=lambda resident: resident.id)
    source, first, second, last = residents
    quote = "시장이 식량을 훔쳤대"
    path = tmp_path / "rumor.sqlite"
    bundles = (transport_world_bundle(world, social, transport, scenario, knowledge=True),)
    with open_world_session(
        path, world, supply=scenario, social=social, transport=transport, knowledge=True
    ) as owner:
        owner.export("slot01")
        commit(owner, PlayerSay(source.id, "내 은신처는 북쪽 창고야"))
        context = context_from_core(owner.snapshot(), world, scenario, social=social)
        commit(
            owner,
            AssessedNpcReply(
                context.current.speech_id,
                "네",
                "controlled",
                context.sha256,
                "none",
                SpeechJudgment(3, ""),
            ),
        )
        commit(owner, PlayerSay(source.id, quote + ". 창고는 비밀."))
        context = context_from_core(owner.snapshot(), world, scenario, social=social)
        assert context.memories[-1].player_text == "내 은신처는 북쪽 창고야"
        origin = context.current
        before = owner.snapshot(), owner.protocol()
        rejected = owner.submit(
            world_command(
                owner.protocol(),
                AssessedNpcReply(
                    origin.speech_id,
                    "네",
                    "controlled",
                    context.sha256,
                    "none",
                    SpeechJudgment(2, "꾸며낸 말"),
                ),
            ),
            attachment_id=owner.attachment_id,
        )
        assert (
            isinstance(rejected.outcome, TurnRejected)
            and rejected.outcome.failure.code == "DIALOGUE_JUDGMENT"
        )
        assert (owner.snapshot(), owner.protocol()) == before
        commit(
            owner,
            AssessedNpcReply(
                origin.speech_id,
                "네",
                "controlled",
                context.sha256,
                "none",
                SpeechJudgment(2, quote),
            ),
        )
        end = owner.snapshot().tick

        commit(owner, PlayerSay(first.id, "무슨 일이야"))
        commit(owner, WorldWait(end + 9 - owner.snapshot().tick))
        early = context_from_core(owner.snapshot(), world, scenario, social=social)
        assert not early.rumors and not early.memories and not early.observations
        commit(owner, WorldWait(1))
        later = context_from_core(owner.snapshot(), world, scenario, social=social)
        (rumor,) = later.rumors
        assert (rumor.speech_id, rumor.player_id, rumor.direct_listener_id, rumor.place_id) == (
            origin.speech_id,
            "actor:world-player",
            source.id,
            place,
        )
        assert (rumor.quote, rumor.heard_tick, rumor.learned_tick) == (
            quote,
            origin.player_end,
            end + 10,
        )
        request = canonical_json(generation_request(later)).decode("utf-8")
        assert quote in request and "북쪽 창고" not in request and "창고는 비밀" not in request
        assert not later.observations and not later.memories
        stale = owner.submit(
            world_command(
                owner.protocol(),
                AssessedNpcReply(
                    later.current.speech_id,
                    "네",
                    "controlled",
                    early.sha256,
                    "none",
                    SpeechJudgment(0, ""),
                ),
            ),
            attachment_id=owner.attachment_id,
        )
        assert (
            isinstance(stale.outcome, TurnRejected)
            and stale.outcome.failure.code == "DIALOGUE_CONTEXT_STALE"
        )
        for recipient, deadline in ((second, end + 20), (last, end + 30)):
            commit(owner, PlayerSay(recipient.id, "안녕"))
            commit(owner, WorldWait(deadline - 1 - owner.snapshot().tick))
            assert not context_from_core(owner.snapshot(), world, scenario, social=social).rumors
            commit(owner, WorldWait(1))
            result = context_from_core(owner.snapshot(), world, scenario, social=social)
            assert len(result.rumors) == 1 and result.rumors[0].learned_tick == deadline

        inventory = next(
            c.state for c in owner.snapshot().components if isinstance(c, InventoryRecord)
        )
        supply = next(
            c.state
            for c in owner.snapshot().components
            if isinstance(c, SupplyRecord) and c.entity_id == place
        )
        assert inventory.gold == 0 and not inventory.items and supply.stage == 0
        segment = owner.retained_segment()
        assert (
            replay_runner(
                ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace),
                bundles=bundles,
            ).run(segment.trace)
            == ()
        )
        owner.export("slot02")
        owner.load("slot01")
        wait_until(owner, end + 30)
        commit(owner, PlayerSay(last.id, "안녕"))
        assert not context_from_core(owner.snapshot(), world, scenario, social=social).rumors
        owner.load("slot02")
        assert (
            context_from_core(owner.snapshot(), world, scenario, social=social).rumors[0].quote
            == quote
        )


@pytest.mark.parametrize(
    "importance, quote", ((4, ""), (True, ""), (1, "없는 말"), (2, "가" * 161))
)
def test_provider_rejects_invalid_judgment(
    importance: JsonValue, quote: str, tmp_path: Path
) -> None:
    world = load_world()
    scenario = SupplyScenario()
    npc = elaborate_place(world, world.places[0].id).residents[0]
    with open_world_session(
        tmp_path / "strict.sqlite", world, supply=scenario, conversation=True, knowledge=True
    ) as owner:
        commit(owner, PlayerSay(npc.id, "가" * 161))
        while conversation(owner).remaining:
            commit(owner, ContinueSpeech(conversation(owner).exchanges[-1].speech_id))
        context = context_from_core(owner.snapshot(), world, scenario)
        with pytest.raises(GenerationError, match="^GENERATION_OUTPUT$"):
            parse_reply(response(importance, quote), context)


def test_ranked_retention_and_delivery_observation_survive_checkpoint(tmp_path: Path) -> None:
    world = load_world()
    social, transport = load_social(world), load_transport(world)
    scenario = SupplyScenario(start_tick=1)
    place = world.places[0].id
    courier, merchant, *_ = elaborate_place(world, place).residents
    bundles = (transport_world_bundle(world, social, transport, scenario, knowledge=True),)
    with open_world_session(
        tmp_path / "source.sqlite",
        world,
        supply=scenario,
        social=social,
        transport=transport,
        knowledge=True,
    ) as owner:
        commit(owner, WorldWait(1))
        for npc, operation in (
            (merchant, "accept"),
            (courier, "collect"),
            (courier, "collect"),
            (merchant, "deliver"),
        ):
            commit(owner, SupplyAction(place, npc.id, operation))
        delivery_tick = owner.snapshot().tick
        for index in range(40):
            commit(owner, PlayerSay(merchant.id, "기억"))
            context = context_from_core(owner.snapshot(), world, scenario, social=social)
            importance = 3 if index == 0 else 2 if index <= 8 else 0
            commit(
                owner,
                AssessedNpcReply(
                    context.current.speech_id,
                    "네",
                    "controlled",
                    context.sha256,
                    "none",
                    SpeechJudgment(importance, "기억" if index in (0, 9) else ""),
                ),
            )
        entries = conversation(owner).exchanges
        assert len(entries) == 40
        commit(owner, PlayerSay(courier.id, "안녕"))
        other = conversation(owner).exchanges[-1]
        checkpoint = DurableCheckpoint(owner.snapshot(), owner.protocol())

    path = tmp_path / "checkpoint.sqlite"
    with create_durable(path, checkpoint, bundles=bundles) as owner:
        assert not owner.retained_segment().trace.steps
        commit(owner, PlayerSay(merchant.id, "가" * 100))
        pending = conversation(owner)
        assert pending.remaining == 1
        assert pending.exchanges[:-2] == (entries[0], *entries[2:])
        assert pending.exchanges[-2] == other
        commit(owner, ContinueSpeech(pending.exchanges[-1].speech_id))
        context = context_from_core(owner.snapshot(), world, scenario, social=social)
        (observation,) = context.observations
        assert (observation.event, observation.observer_id, observation.tick) == (
            "observed_supply_delivery",
            merchant.id,
            delivery_tick,
        )
        assert not context.rumors and all(entry.npc_id == merchant.id for entry in context.memories)
        commit(owner, PlayerSay(merchant.id, "안녕"))
        assert entries[9] not in conversation(owner).exchanges
        assert entries[0] in conversation(owner).exchanges
        commit(owner, PlayerSay(courier.id, "안녕"))
        courier_context = context_from_core(owner.snapshot(), world, scenario, social=social)
        assert not courier_context.observations
        assert tuple(r.speech_id for r in courier_context.rumors) == (entries[0].speech_id,)
    with open_world_session(
        path, world, supply=scenario, social=social, transport=transport, knowledge=True
    ) as owner:
        assert (
            entries[0] in conversation(owner).exchanges and other in conversation(owner).exchanges
        )


def test_worker_reply_rollback_retries_the_same_judgment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    world = load_world()
    scenario = SupplyScenario()
    npc = elaborate_place(world, world.places[0].id).residents[0]
    path = tmp_path / "retry.sqlite"
    worker = WorldWorker(
        path,
        world,
        scenario=scenario,
        knowledge=True,
        generator_factory=lambda: GeminiConversation(
            "fixture-key",
            GenerationBudget(tmp_path / "budget", spacing_ms=0),
            free_tier_confirmed=True,
            free_data_use_confirmed=True,
            send=lambda *_: response(1, "안녕"),
        ),
    )
    try:
        heard = worker.request("say", npc_id=npc.id, text="안녕", request_key="say").result(10)
        worker.request("generate", request_key="generate").result(10)
        before = path.read_bytes()
        original = SqliteCommitStore._execute

        def execute(
            store: SqliteCommitStore, query: str, values: tuple[SqlValue, ...] = ()
        ) -> sqlite3.Cursor:
            if query.startswith("INSERT INTO replay"):
                raise sqlite3.OperationalError("injected judgment rollback")
            return original(store, query, values)

        with monkeypatch.context() as patch:
            patch.setattr(SqliteCommitStore, "_execute", execute)
            with pytest.raises(SaveError, match="SAVE_UNAVAILABLE"):
                worker.request("reply", request_key="reply").result(10)
        assert path.read_bytes() == before
        recovered = worker.request("reply", request_key="reply").result(10)
        assert recovered.tick > heard.tick and recovered.conversation is not None
        assert len(recovered.conversation.exchanges) == 1
        assert recovered.conversation.exchanges[0].judgment == SpeechJudgment(1, "안녕")
        assert worker.request("reply", request_key="reply").result(10) == recovered
    finally:
        worker.close()


def test_knowledge_cli_uses_separate_save(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(tk.Tk, "mainloop", lambda self: None)
    for flags in (["--world-knowledge"], ["--world-knowledge", "--npc-ai"]):
        assert main(flags) == 0
        gc.collect()
    assert (tmp_path / "tmp/world-knowledge-play/game.sqlite").is_file()
    assert not (tmp_path / "tmp/world-authored-supply-play").exists()
    assert not (tmp_path / "tmp/world-transport-play").exists()
    with pytest.raises(SystemExit, match="2"):
        main(["--world-knowledge", "--world-authored"])


def test_timeout_preserves_unassessed_speech_and_offline_does_not_generate(tmp_path: Path) -> None:
    world = load_world()
    path = tmp_path / "timeout.sqlite"
    npc = elaborate_place(world, world.places[0].id).residents[0]

    def timeout(*_args: object) -> JsonObject:
        raise GenerationError("GENERATION_TIMEOUT")

    worker = WorldWorker(
        path,
        world,
        knowledge=True,
        generator_factory=lambda: GeminiConversation(
            "fixture-key",
            GenerationBudget(tmp_path / "budget", spacing_ms=0),
            free_tier_confirmed=True,
            free_data_use_confirmed=True,
            send=timeout,
        ),
    )
    try:
        worker.request("say", npc_id=npc.id, text="들었어?", request_key="say").result(10)
        with pytest.raises(GenerationError, match="^GENERATION_TIMEOUT$"):
            worker.request("generate", request_key="generate").result(10)
    finally:
        worker.close()

    offline = WorldWorker(
        path, world, knowledge=True, live_npc=False, generator_factory=no_provider
    )
    try:
        with pytest.raises(ValueError, match="^WORLD_NPC_AI_DISABLED$"):
            offline.request("generate", request_key="offline").result(10)
        update = offline.request("inspect").result(10)
        assert update.tick == 1 and update.conversation is not None
        (entry,) = update.conversation.exchanges
        assert entry.player_text == "들었어?" and not entry.reply_text and entry.judgment is None
    finally:
        offline.close()
