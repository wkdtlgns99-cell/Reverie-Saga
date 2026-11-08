"""Read the current knowledge world through its real registered durable state."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import subprocess
import sys
from threading import Event, current_thread

import pytest

from adapters import sqlite_store, world_attachment
from adapters.world_attachment import current_world, remember_world
from app.world_catalog import AUTHORED_SUPPLY_SCENARIO, load_social, load_transport, load_world
from app.world_observer import read_world
from app.world_session import open_world_session, world_command
from app.world_village_session import open_knowledge_world
from app.world_worker import WorldWorker
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.state_io import StateIO
from contracts.turn import TurnCommitted
from contracts.world_conversation import AssessedNpcReply, ContinueSpeech, PlayerSay
from contracts.world_supply import SupplyAction
from contracts.world_time import WorldWait
from domain.canonical import JsonObject, array_value, decode_json, object_value
from domain.world import WorldCatalog, elaborate_place
from domain.world_conversation import SpeechJudgment
from orchestration.persistence import decode_checkpoint
from orchestration.world_conversation_context import context_from_core
from tests.integration.test_world_knowledge import commit, conversation


def dialogues(view: JsonObject) -> dict[str, tuple[JsonObject, ...]]:
    return {
        str(row["id"]): tuple(object_value(entry) for entry in array_value(row["exchanges"]))
        for value in array_value(view["residents"])
        for row in (object_value(value),)
    }


def run_reader(path: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, "-B", "-m", "app.world_observer", "--working", str(path)],
        capture_output=True,
        check=False,
        timeout=15,
    )


def test_cli_refreshes_live_commits_and_follows_the_loaded_branch(tmp_path: Path) -> None:
    world = load_world()
    social, transport = load_social(world), load_transport(world)
    scenario = AUTHORED_SUPPLY_SCENARIO
    place = scenario.place_id
    courier, merchant, *_ = elaborate_place(world, place).residents
    path = tmp_path / "game.sqlite"
    with open_world_session(
        path, world, supply=scenario, social=social, transport=transport, knowledge=True
    ) as owner:
        commit(owner, WorldWait(1))
        commit(owner, SupplyAction(place, merchant.id, "accept"))
        owner.export("slot01")
        commit(owner, PlayerSay(courier.id, "상자 받으러 왔어요."))
        commit(owner, PlayerSay(merchant.id, "의뢰 확인했어요."))
        before = owner.protocol(), path.read_bytes(), set(tmp_path.iterdir())
        output = run_reader(path)
        assert output.returncode == 0 and not output.stderr
        ongoing = object_value(decode_json(output.stdout))
        assert (
            ongoing["format"],
            ongoing["tick"],
            ongoing["revision"],
            ongoing["quest_phase"],
        ) == (
            "reverie-world-observer/v1",
            6,
            4,
            "진행 중",
        )
        assert ongoing["cargo"] == 0 and ongoing["cargo_required"] == 2
        assert dialogues(ongoing)[courier.id] == (
            {"tick": 4, "player": "상자 받으러 왔어요.", "reply": ""},
        )
        assert dialogues(ongoing)[merchant.id] == (
            {"tick": 6, "player": "의뢰 확인했어요.", "reply": ""},
        )
        assert (owner.protocol(), path.read_bytes(), set(tmp_path.iterdir())) == before

        for action in (
            SupplyAction(place, courier.id, "collect"),
            SupplyAction(place, courier.id, "collect"),
        ):
            commit(owner, action)
        assert read_world(path)["cargo"] == 2
        commit(owner, SupplyAction(place, merchant.id, "deliver"))
        delivered = read_world(path)
        assert (delivered["quest_phase"], delivered["resolved_tick"], delivered["cargo"]) == (
            "완료",
            9,
            0,
        )
        assert "보급로 복구 완료" in str(delivered["quest_status"])
        assert dialogues(delivered) == dialogues(ongoing)

        owner.load("slot01")
        remember_world(path, owner.working_path)
        paths = tuple(tmp_path.iterdir())
        bytes_before = path.read_bytes(), owner.working_path.read_bytes()
        earlier = read_world(path)
        assert (earlier["tick"], earlier["revision"], earlier["quest_phase"]) == (2, 2, "진행 중")
        assert not any(dialogues(earlier).values())
        assert (path.read_bytes(), owner.working_path.read_bytes()) == bytes_before
        assert set(tmp_path.iterdir()) == set(paths)


def test_observer_shows_only_finished_speech_and_bounds_transcript(tmp_path: Path) -> None:
    world = load_world()
    scenario = AUTHORED_SUPPLY_SCENARIO
    courier = elaborate_place(world, scenario.place_id).residents[0]
    social = load_social(world)
    path = tmp_path / "game.sqlite"
    with open_world_session(
        path, world, supply=scenario, social=social, transport=load_transport(world), knowledge=True
    ) as owner:
        commit(owner, PlayerSay(courier.id, "가" * 100))
        assert not dialogues(read_world(path))[courier.id]
        context_speech = read_world(path)
        assert context_speech["tick"] == 16
        commit(owner, ContinueSpeech(conversation(owner).exchanges[-1].speech_id))
        context = context_from_core(owner.snapshot(), world, scenario, social=social)
        long_reply = "나" * 120
        commit(
            owner,
            AssessedNpcReply(
                context.current.speech_id,
                long_reply,
                "fixture",
                context.sha256,
                "none",
                SpeechJudgment(3, "가"),
            ),
        )
        (partial,) = dialogues(read_world(path))[courier.id]
        assert partial == {"tick": 17, "player": "가" * 100, "reply": ""}
        commit(owner, ContinueSpeech(context.current.speech_id))
        (finished,) = dialogues(read_world(path))[courier.id]
        assert finished == {"tick": 17, "player": "가" * 100, "reply": long_reply}
        for index in range(9):
            commit(owner, PlayerSay(courier.id, f"대화 {index}"))
        rows = dialogues(read_world(path))[courier.id]
        assert tuple(row["player"] for row in rows) == tuple(f"대화 {i}" for i in range(1, 9))
        assert all(set(row) == {"tick", "player", "reply"} for row in rows)


@pytest.mark.parametrize(
    ("content", "error"), ((None, "SAVE_NOT_FOUND"), (b"invalid", "SAVE_CORRUPT"))
)
def test_reader_fails_without_creating_or_repairing_a_save(
    tmp_path: Path, content: bytes | None, error: str
) -> None:
    path = tmp_path / "game.sqlite"
    if content is not None:
        path.write_bytes(content)
    result = run_reader(path)
    assert result.returncode == 2 and not result.stdout
    assert result.stderr.decode().strip() == error
    assert set(tmp_path.iterdir()) == ({path} if content is not None else set())
    if content is not None:
        assert path.read_bytes() == content


def test_reader_drops_snapshot_if_the_active_branch_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    world = load_world()
    path = tmp_path / "game.sqlite"
    with open_world_session(
        path,
        world,
        supply=AUTHORED_SUPPLY_SCENARIO,
        social=load_social(world),
        transport=load_transport(world),
        knowledge=True,
    ):
        files = iter((path, tmp_path / "other.sqlite"))
        monkeypatch.setattr("app.world_observer.current_world", lambda _: next(files))
        with pytest.raises(SaveError, match="^WORLD_VIEW_CHANGED"):
            read_world(path)


@pytest.mark.parametrize("before_target_lookup", (False, True))
def test_refresh_reports_branch_change_when_slot_load_retires_selected_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, before_target_lookup: bool
) -> None:
    world = load_world()
    path = tmp_path / "game.sqlite"
    worker = WorldWorker(
        path,
        world,
        scenario=AUTHORED_SUPPLY_SCENARIO,
        social=load_social(world),
        transport=load_transport(world),
        knowledge=True,
    )
    selected, release = Event(), Event()

    def wait_for_replacement() -> None:
        selected.set()
        if not release.wait(timeout=10):
            raise TimeoutError("observer source selection barrier timed out")

    def pause_after_selection() -> WorldCatalog:
        wait_for_replacement()
        return world

    try:
        worker.request("wait", seconds=1).result(timeout=10)
        worker.request("save").result(timeout=10)
        worker.request("load").result(timeout=10)
        worker.request("wait", seconds=2).result(timeout=10)
        former = current_world(path)
        assert former != path
        target = world_attachment._target

        def pause_before_target(base: Path, name: str) -> Path:
            if name == former.name:
                wait_for_replacement()
            return target(base, name)

        with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=1) as reader:
            if before_target_lookup:
                patch.setattr(world_attachment, "_target", pause_before_target)
            else:
                patch.setattr("app.world_observer.load_world", pause_after_selection)
            refresh = reader.submit(read_world, path)
            try:
                assert selected.wait(timeout=10)
                loaded = worker.request("load").result(timeout=10)
                active = current_world(path)
                assert active != former and not former.exists()
                before = active.read_bytes(), set(tmp_path.iterdir())
            finally:
                release.set()
            with pytest.raises(SaveError, match="^WORLD_VIEW_CHANGED"):
                refresh.result(timeout=10)

        view = read_world(path)
        assert (view["tick"], view["revision"]) == (loaded.tick, loaded.protocol.revision) == (1, 1)
        assert (active.read_bytes(), set(tmp_path.iterdir())) == before
        advanced = worker.request("wait", seconds=1).result(timeout=10)
        assert read_world(path)["tick"] == advanced.tick == 2
    finally:
        worker.close()


def test_reader_reports_a_busy_save_and_can_refresh_after_release(tmp_path: Path) -> None:
    world = load_world()
    path = tmp_path / "game.sqlite"
    with open_world_session(
        path,
        world,
        supply=AUTHORED_SUPPLY_SCENARIO,
        social=load_social(world),
        transport=load_transport(world),
        knowledge=True,
    ):
        before = path.read_bytes(), set(tmp_path.iterdir())
        writer = sqlite3.connect(path, timeout=0, autocommit=True)
        try:
            writer.execute("BEGIN EXCLUSIVE")
            result = run_reader(path)
            assert result.returncode == 2 and not result.stdout
            assert result.stderr.decode().strip() == "WORLD_VIEW_BUSY"
            writer.execute("ROLLBACK")
        finally:
            writer.close()
        assert read_world(path)["tick"] == 0
        assert (path.read_bytes(), set(tmp_path.iterdir())) == before


def test_observer_releases_read_lock_before_validating_captured_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    world = load_world()
    scenario = AUTHORED_SUPPLY_SCENARIO
    place = scenario.place_id
    courier, merchant, *_ = elaborate_place(world, place).residents
    path = tmp_path / "game.sqlite"
    decoding, release = Event(), Event()
    writer_thread = current_thread()

    def pause_reader(document: JsonObject, *, io: StateIO) -> DurableCheckpoint:
        if current_thread() is not writer_thread and not decoding.is_set():
            decoding.set()
            if not release.wait(timeout=10):
                raise TimeoutError("checkpoint decode barrier timed out")
        return decode_checkpoint(document, io=io)

    with open_world_session(
        path,
        world,
        supply=scenario,
        social=load_social(world),
        transport=load_transport(world),
        knowledge=True,
    ) as owner:
        commit(owner, SupplyAction(place, merchant.id, "accept"))
        commit(owner, SupplyAction(place, courier.id, "collect"))
        commit(owner, SupplyAction(place, courier.id, "collect"))
        before = set(tmp_path.iterdir())
        delivery = world_command(owner.protocol(), SupplyAction(place, merchant.id, "deliver"))
        monkeypatch.setattr(sqlite_store, "decode_checkpoint", pause_reader)
        with ThreadPoolExecutor(max_workers=1) as reader:
            pending = reader.submit(read_world, path)
            try:
                assert decoding.wait(timeout=10)
                result = owner.submit(delivery, attachment_id=owner.attachment_id)
                assert isinstance(result.outcome, TurnCommitted), result.outcome
            finally:
                release.set()
            captured = pending.result(timeout=10)

        assert (captured["revision"], captured["quest_phase"], captured["cargo"]) == (
            3,
            "진행 중",
            2,
        )
        fresh = read_world(path)
        assert (fresh["revision"], fresh["quest_phase"], fresh["cargo"]) == (4, "완료", 0)
        saved = path.read_bytes()
        duplicate = owner.submit(delivery, attachment_id=owner.attachment_id)
        assert duplicate.outcome == result.outcome
        assert owner.protocol().revision == 4 and path.read_bytes() == saved
        assert set(tmp_path.iterdir()) == before


@pytest.mark.parametrize("village", (False, True))
def test_observer_validates_profiles_from_one_sqlite_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, village: bool
) -> None:
    world = load_world()
    scenario = AUTHORED_SUPPLY_SCENARIO
    path = tmp_path / "game.sqlite"
    connect = sqlite_store._connect
    read_paths: list[Path] = []

    def track_connect(source: Path, *, readonly: bool = False) -> sqlite3.Connection:
        if readonly:
            read_paths.append(source)
        return connect(source, readonly=readonly)

    with open_knowledge_world(
        path, world, scenario, load_social(world), load_transport(world), village=village
    ) as owner:
        commit(owner, WorldWait(1))
        before = path.read_bytes(), set(tmp_path.iterdir())
        monkeypatch.setattr(sqlite_store, "_connect", track_connect)
        view = read_world(path)
        assert (view["tick"], view["revision"]) == (1, 1)
        assert read_paths == [path.resolve()]
        assert (path.read_bytes(), set(tmp_path.iterdir())) == before


def test_observer_rejects_an_unsupported_world_without_modifying_it(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with open_world_session(path, load_world()):
        before = path.read_bytes(), set(tmp_path.iterdir())
        with pytest.raises(SaveError, match="^UNSUPPORTED_RULESET"):
            read_world(path)
        assert (path.read_bytes(), set(tmp_path.iterdir())) == before
