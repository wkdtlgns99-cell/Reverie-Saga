"""Actual village pipe, legacy save upgrade, slots, and retained replay."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import subprocess
import sys
from typing import IO

import pytest

from app import world_village_session
from app.engine_bridge import read_exact, write_frame
from app.headless import replay_runner
from app.world_catalog import AUTHORED_SUPPLY_SCENARIO, load_social, load_transport, load_world
from app.world_observer import read_world
from app.world_session import foot_command
from app.world_supply_bridge import exchange
from app.world_transport_registry import transport_world_bundle
from app.world_village_registry import village_world_bundle
from app.world_village_session import open_knowledge_world
from contracts.replay import ReplayFixture
from contracts.turn import TurnCommitted
from contracts.world_supply import SupplyAction
from contracts.world_time import WorldWait
from domain.canonical import JsonObject, array_value, decode_json, object_value, text_value
from domain.world import elaborate_place
from domain.world_village import ENTRANCE, VillagePosition, VillageRecord
from tests.integration.test_world_knowledge import commit


@contextmanager
def pipe(path: Path) -> Iterator[tuple[IO[bytes], IO[bytes]]]:
    with subprocess.Popen(
        [sys.executable, "-B", "-m", "app.world_village_bridge", "--working", str(path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as process:
        assert (
            process.stdin is not None and process.stdout is not None and process.stderr is not None
        )
        try:
            yield process.stdin, process.stdout
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=15)
                raise
        assert process.returncode == 0, process.stderr.read()


def send(
    streams: tuple[IO[bytes], IO[bytes]], sequence: int, action: str, value: str = ""
) -> JsonObject:
    source, sink = streams
    write_frame(
        source,
        {
            "format": "reverie-world-village/v1",
            "id": sequence,
            "action": action,
            "value": value,
        },
    )
    size = int.from_bytes(read_exact(sink, 4), "big")
    assert 1 <= size <= 16 * 1024
    response = object_value(decode_json(read_exact(sink, size)))
    assert response["format"] == "reverie-world-village/v1" and response["id"] == sequence
    return response


def test_village_pipe_commits_cardinal_steps_rejects_walls_and_reopens(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with pipe(path) as streams:
        start = send(streams, 1, "inspect")
        assert (start["x"], start["y"], start["tick"], start["revision"]) == (1, 7, 0, 0)
        blocked = send(streams, 2, "step", "left")
        assert blocked == {**start, "id": 2, "error": "VILLAGE_BLOCKED"}
        assert send(streams, 3, "step", "north-east") == {
            **start,
            "id": 3,
            "error": "INVALID_COMMAND",
        }
        moved = send(streams, 4, "step", "right")
        assert (moved["x"], moved["y"], moved["tick"], moved["revision"]) == (2, 7, 1, 1)
        assert send(streams, 4, "step", "right") == moved
        assert send(streams, 4, "step", "up") == {**moved, "error": "STALE_REQUEST"}
        moved = send(streams, 5, "step", "up")
        assert (moved["x"], moved["y"], moved["tick"], moved["revision"]) == (2, 6, 2, 2)
        idle = send(streams, 6, "idle", "1")
        assert (idle["x"], idle["y"], idle["tick"], idle["revision"]) == (2, 6, 3, 3)
        assert read_world(path)["tick"] == 3
    before = path.read_bytes()
    with pipe(path) as streams:
        assert send(streams, 1, "inspect") == {**idle, "id": 1}
    assert path.read_bytes() == before


def test_upgrade_preserves_legacy_world_and_slots_and_supports_replay(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    world = load_world()
    scenario, social, transport = (
        AUTHORED_SUPPLY_SCENARIO,
        load_social(world),
        load_transport(world),
    )
    courier, merchant, *_ = elaborate_place(world, scenario.place_id).residents
    with open_knowledge_world(path, world, scenario, social, transport) as owner:
        commit(owner, WorldWait(2))
        commit(owner, SupplyAction(scenario.place_id, merchant.id, "accept"))
        commit(owner, SupplyAction(scenario.place_id, courier.id, "collect"))
        owner.export("slot01")
        before = owner.snapshot()
        branch = owner.protocol().branch_id
    old = path.read_bytes()
    slot = tmp_path / "slots" / "slot01.sqlite"
    old_slot = slot.read_bytes()
    with pipe(path) as streams:
        start = send(streams, 1, "inspect")
        assert (start["x"], start["y"], start["tick"], start["revision"]) == (1, 7, 4, 3)
        send(streams, 2, "step", "right")
    assert path.read_bytes() == old and slot.read_bytes() == old_slot
    assert read_world(path)["cargo"] == 1
    with open_knowledge_world(path, world, scenario, social, transport) as owner:
        assert owner.working_path != path and owner.protocol().branch_id != branch
        retained = owner.retained_segment()
        upgraded = retained.checkpoint.core
        assert upgraded.tick == before.tick and upgraded.pending == before.pending
        assert (
            tuple(c for c in upgraded.components if not isinstance(c, VillageRecord))
            == before.components
        )
        bundle = village_world_bundle(
            transport_world_bundle(world, social, transport, scenario, knowledge=True),
            scenario.place_id,
        )
        assert (
            replay_runner(
                ReplayFixture(upgraded, retained.checkpoint.protocol, retained.trace),
                bundles=(bundle,),
            ).run(retained.trace)
            == ()
        )
        owner.export("slot01")
        assert (tmp_path / "slots" / "slot01.previous.sqlite").read_bytes() == old_slot
        owner.load("slot01", previous=True)
        assert owner.snapshot().tick == 4 and owner.protocol().revision == 3
        assert (
            next(c.state for c in owner.snapshot().components if isinstance(c, VillageRecord))
            == ENTRANCE
        )
        owner.load("slot01")
        assert next(
            c.state for c in owner.snapshot().components if isinstance(c, VillageRecord)
        ) == VillagePosition(2, 7)


def test_existing_supply_bridge_can_play_in_village_world(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with pipe(path) as streams:
        send(streams, 1, "step", "right")
    progress = exchange(path)
    for _ in range(4):
        offer = object_value(progress["offer"])
        progress = exchange(path, text_value(offer["token"]))
    assert (progress["cargo"], progress["gold"], progress["revision"]) == (0, 5, 5)
    assert read_world(path)["quest_phase"] == "완료"
    with pipe(path) as streams:
        view = send(streams, 1, "inspect")
        assert (view["x"], view["y"], view["tick"]) == (2, 7, 5)


def test_village_requires_exclusive_owner_and_does_not_walk_on_the_road(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    world = load_world()
    scenario = AUTHORED_SUPPLY_SCENARIO
    with open_knowledge_world(
        path, world, scenario, load_social(world), load_transport(world)
    ) as owner:
        before = path.read_bytes()
        result = subprocess.run(
            [sys.executable, "-B", "-m", "app.world_village_bridge", "--working", str(path)],
            input=b"",
            capture_output=True,
            timeout=15,
            check=False,
        )
        assert result.returncode == 2 and result.stderr.strip() == b"SAVE_LOCKED"
        assert result.stdout == b"" and path.read_bytes() == before
        neighbor, _ = world.neighbors(scenario.place_id)[0]
        command = foot_command(owner.protocol(), neighbor.id)
        assert isinstance(
            owner.submit(command, attachment_id=owner.attachment_id).outcome, TurnCommitted
        )
    with pipe(path) as streams:
        start = send(streams, 1, "inspect")
        assert start["available"] is False and start["tick"] == 1
        assert send(streams, 2, "step", "right") == {
            **start,
            "id": 2,
            "error": "VILLAGE_OUT_OF_REACH",
        }
        assert send(streams, 3, "idle", "1") == {**start, "id": 3, "error": "VILLAGE_INACTIVE"}


def test_failed_active_reference_switch_preserves_the_old_save(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "game.sqlite"
    world = load_world()
    args = path, world, AUTHORED_SUPPLY_SCENARIO, load_social(world), load_transport(world)
    with open_knowledge_world(*args) as owner:
        commit(owner, WorldWait(2))
    before = path.read_bytes(), set(tmp_path.iterdir())

    def unavailable(base: Path, active: Path) -> None:
        assert base == path and active.is_file()
        raise OSError("active reference unavailable")

    monkeypatch.setattr(world_village_session, "remember_world", unavailable)
    with pytest.raises(OSError, match="active reference unavailable"):
        open_knowledge_world(*args, village=True)
    assert (path.read_bytes(), set(tmp_path.iterdir())) == before
    with open_knowledge_world(*args) as owner:
        assert owner.working_path == path and owner.snapshot().tick == 2


def test_walk_up_and_complete_supply_in_one_village_session(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with pipe(path) as streams:
        sequence = 0

        def act(action: str, value: str = "") -> JsonObject:
            nonlocal sequence
            sequence += 1
            return send(streams, sequence, action, value)

        def walk(*directions: str) -> None:
            for direction in directions:
                assert act("step", direction)["error"] == ""

        def talk(npc: str, label: str) -> str:
            view = act("talk", npc)
            assert view["error"] == "" and view["has_interaction"] is True
            offer = object_value(view["interaction"])
            assert offer["label"] == label and text_value(offer["terms"])
            return text_value(offer["token"])

        def inventory(view: JsonObject) -> tuple[object, object]:
            row = object_value(view["supply"])
            return row["cargo"], row["gold"]

        start = act("inspect")
        roster = {
            npc["role"]: text_value(npc["id"])
            for npc in map(object_value, array_value(object_value(start["supply"])["residents"]))
        }
        merchant, courier = roster["상인"], roster["운송인"]
        denied = act("talk", merchant)
        assert denied["error"] == "VILLAGE_NPC_OUT_OF_REACH" and denied["revision"] == 0
        walk(*("right",) * 5, *("up",) * 5, "left")
        assert act("talk", merchant)["error"] == "VILLAGE_NPC_OUT_OF_REACH"  # diagonal
        walk("right")
        token = talk(merchant, "의뢰 받기")
        canceled = act("close")
        assert canceled["has_interaction"] is False
        assert act("confirm", token)["error"] == "VILLAGE_OFFER_STALE"
        token = talk(merchant, "의뢰 받기")
        walk("left")
        assert act("confirm", token)["error"] == "VILLAGE_OFFER_STALE"
        walk("right")
        token = talk(merchant, "의뢰 받기")
        waited = act("idle", "1")
        assert waited["has_interaction"] is True
        assert act("confirm", token)["error"] == "VILLAGE_OFFER_STALE"
        refreshed = text_value(object_value(waited["interaction"])["token"])
        assert act("confirm", refreshed)["error"] == ""
        walk("down", "right", "right", "down")
        first = talk(courier, "상자 받기")
        collected = act("confirm", first)
        assert inventory(collected) == (1, 0)
        assert send(streams, sequence, "confirm", first) == collected
        assert act("confirm", first)["error"] == "VILLAGE_OFFER_STALE"
        assert inventory(act("confirm", talk(courier, "상자 받기"))) == (2, 0)
        walk("up", "left", "left", "up")
        final = talk(merchant, "상자 전달하기")
        delivered = act("confirm", final)
        assert inventory(delivered) == (0, 5)
        assert delivered["has_interaction"] is False
        assert act("confirm", final)["revision"] == delivered["revision"]

    assert read_world(path)["quest_phase"] == "완료"
    with pipe(path) as streams:
        reopened = send(streams, 1, "inspect")
        assert inventory(reopened) == (0, 5)
        assert (reopened["x"], reopened["y"], reopened["revision"]) == (6, 2, delivered["revision"])
    world = load_world()
    scenario, social, transport = (
        AUTHORED_SUPPLY_SCENARIO,
        load_social(world),
        load_transport(world),
    )
    bundle = village_world_bundle(
        transport_world_bundle(world, social, transport, scenario, knowledge=True),
        scenario.place_id,
    )
    with open_knowledge_world(path, world, scenario, social, transport) as owner:
        segment = owner.retained_segment()
        actions = tuple(
            step.command.payload.operation
            for step in segment.trace.steps
            if isinstance(step.command.payload, SupplyAction)
        )
        assert actions == ("accept", "collect", "collect", "deliver")
        assert (
            replay_runner(
                ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace),
                bundles=(bundle,),
            ).run(segment.trace)
            == ()
        )
