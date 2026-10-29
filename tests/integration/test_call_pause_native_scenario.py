"""Full prepared native call-pause/occupancy/quest flow through actual Brain paths."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import sqlite3
import time

import pytest

from adapters.sqlite_store import read_segment
from app.engine_bridge import wire
from app.headless import state_io
from contracts.client import ClientAction
from domain.canonical import JsonObject, canonical_json, hash_document, object_value, text_value
from tests.integration.test_call_pause_patrol import bundle, call_pipe, replay, session
from tests.integration.test_cycle_slot_comparison import inventory
from tests.integration.test_call_native_scenario import lines
from tests.integration.test_patrol_next_step import BLOCKED, FREE_HOME, FREE_NEIGHBOR, IDLE


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@contextmanager
def driver(
    path: Path,
    framed: bool,
    history: list[JsonObject],
    timings: list[tuple[str, float]],
    output: Path,
) -> Iterator[Callable[[str], JsonObject]]:
    def measured(raw: Callable[[str], JsonObject]) -> Callable[[str], JsonObject]:
        def send(action: str) -> JsonObject:
            start = time.perf_counter()
            update = raw(action)
            elapsed = time.perf_counter() - start
            stable = dict(update)
            stable.pop("attachment_id")
            stable.pop("working_path")
            history.append(stable)
            timings.append((action, elapsed))
            output.write_text(json.dumps(timings, indent=2), encoding="utf-8")
            assert elapsed < 10, (action, elapsed)
            return update

        return send

    if framed:
        with call_pipe(path) as pipe:
            yield measured(lambda action: object_value(pipe.send(action)["update"]))
        return
    owner = session(path)
    actions: dict[str, ClientAction] = {
        "up": "up",
        "down": "down",
        "left": "left",
        "right": "right",
        "talk": "talk",
        "bell": "bell",
        "wait": "wait",
        "attack": "attack",
        "rest": "rest",
    }

    def raw(action: str) -> JsonObject:
        if action == "attach":
            update = owner.update(reset_log=True)
        elif action == "save":
            update = owner.save("slot01")
        elif action == "load":
            update = owner.load("slot01")
        elif action == "activity":
            update = owner.inspect_activity()
        elif action == "slot_inspect":
            update = owner.inspect_slot("slot01")
        elif action == "slot_previous_inspect":
            update = owner.inspect_slot("slot01", previous=True)
        elif action == "retry":
            update = owner.retry()
        else:
            update = owner.act(actions[action])
        return object_value(wire(asdict(update)))

    try:
        yield measured(raw)
    finally:
        owner.close()


def check(update: JsonObject, tick: int, cell: int, replies: int = 2, reward: int = 0) -> None:
    view = object_value(update["view"])
    assert view["tick"] == str(tick) and view["npc_cell"] == str(cell)
    assert view["npc_replies"] == str(replies) and update["quest_reward"] == str(reward)


def read_only(
    send: Callable[[str], JsonObject],
    request: str,
    root: Path,
    current: JsonObject,
    expected: tuple[str, ...],
) -> JsonObject:
    before = inventory(root)
    update = send(request)
    assert update["view"] == current["view"] and inventory(root) == before
    assert all(line in lines(update) for line in expected)
    return update


@pytest.mark.parametrize("framed", (False, True), ids=("direct", "real-pipe"))
def test_full_call_pause_native_contract(tmp_path: Path, framed: bool) -> None:
    path = tmp_path / "game.sqlite"
    history: list[JsonObject] = []
    timings: list[tuple[str, float]] = []
    timing_path = tmp_path / "timings.json"
    with driver(path, framed, history, timings, timing_path) as send:
        send("attach")
        send("down")
        assert FREE_NEIGHBOR in lines(send("talk"))
        send("up")
        answered = send("bell")
        check(answered, 4, 6, 1)
        assert "NPC가 공동 작업 구역을 순찰했습니다." not in lines(answered)
        send("save")
        read_only(send, "activity", tmp_path, answered, (FREE_NEIGHBOR,))
        send("wait")
        moved = send("wait")
        check(moved, 6, 7, 1)
        read_only(
            send,
            "slot_inspect",
            tmp_path,
            moved,
            (
                "NPC 다음 순찰 행동 비교 · 현재 6초 / 선택 저장 4초",
                "현재 " + FREE_HOME,
                "선택 저장 " + FREE_NEIGHBOR,
            ),
        )
        original, original_bytes = path, digest(path)
        loaded = send("load")
        check(loaded, 4, 6, 1)
        branch = Path(text_value(loaded["working_path"]))
        assert branch != original and digest(original) == original_bytes
    with driver(branch, framed, history, timings, timing_path) as send:
        attached = send("attach")
        check(attached, 4, 6, 1)
        read_only(send, "activity", tmp_path, attached, (FREE_NEIGHBOR,))
        send("wait")
        check(send("wait"), 6, 7, 1)
        send("wait")
        second = send("bell")
        check(second, 8, 7)
        read_only(send, "activity", tmp_path, second, (FREE_HOME,))
        before = inventory(tmp_path)
        retried = send("retry")
        check(retried, 8, 7)
        assert retried["view"] == second["view"] and inventory(tmp_path) == before
        assert "NPC가 공동 작업 구역을 순찰했습니다." not in lines(retried)
        send("wait")
        check(send("wait"), 10, 6)
        assert digest(original) == original_bytes
        send("wait")
        check(send("wait"), 12, 7)
        send("down")
        blocked = send("down")
        check(blocked, 14, 7)
        assert object_value(blocked["view"])["actor_cell"] == "6"
        send("save")
        read_only(send, "activity", tmp_path, blocked, (BLOCKED,))
        free = send("up")
        check(free, 15, 7)
        read_only(
            send,
            "slot_inspect",
            tmp_path,
            free,
            (
                "NPC 다음 순찰 행동 비교 · 현재 15초 / 선택 저장 14초",
                "현재 " + FREE_HOME,
                "선택 저장 " + BLOCKED,
            ),
        )
        read_only(
            send,
            "slot_previous_inspect",
            tmp_path,
            free,
            (
                "NPC 다음 순찰 행동 비교 · 현재 15초 / 선택 저장 4초",
                "현재 " + FREE_HOME,
                "선택 저장 " + FREE_NEIGHBOR,
            ),
        )
        returned = send("wait")
        check(returned, 16, 6)
        read_only(
            send,
            "slot_inspect",
            tmp_path,
            returned,
            (
                "현재 " + FREE_NEIGHBOR,
                "선택 저장 " + BLOCKED,
            ),
        )
        branch_source, branch_bytes = branch, digest(branch)
        loaded = send("load")
        check(loaded, 14, 7)
        branch = Path(text_value(loaded["working_path"]))
        assert branch != branch_source and digest(branch_source) == branch_bytes
        slot, previous = tmp_path / "slots/slot01.sqlite", tmp_path / "slots/slot01.previous.sqlite"
        slot_bytes = digest(slot), digest(previous)
    with driver(branch, framed, history, timings, timing_path) as send:
        attached = send("attach")
        check(attached, 14, 7)
        read_only(send, "activity", tmp_path, attached, (BLOCKED,))
        send("up")
        check(send("wait"), 16, 6)
        for action in ("right", "down", "attack", "attack", "rest"):
            assert send(action)["status"] == "COMMITTED"
        defeated = send("attack")
        check(defeated, 22, 6)
        assert object_value(defeated["view"])["enemy_hp"] == "0"
        assert defeated["quest_stage"] == "2" and defeated["quest_reward"] == "0"
        send("up")
        check(send("left"), 24, 7)
        send("down")
        report = send("talk")
        check(report, 26, 7, reward=1)
        assert BLOCKED in lines(report)
        assert report["quest_stage"] == "3"
        send("wait")
        pending = send("wait")
        check(pending, 28, 7, reward=1)
        read_only(send, "activity", tmp_path, pending, (BLOCKED,))
        free = send("up")
        read_only(send, "activity", tmp_path, free, (FREE_HOME,))
        arrived = send("wait")
        check(arrived, 30, 6, reward=1)
        grateful = send("talk")
        check(grateful, 31, 6, reward=1)
        assert IDLE in lines(grateful)
        read_only(send, "activity", tmp_path, grateful, (IDLE,))
        read_only(
            send,
            "slot_inspect",
            tmp_path,
            grateful,
            (
                "NPC 다음 순찰 행동 비교 · 현재 31초 / 선택 저장 14초",
                "현재 " + IDLE,
                "선택 저장 " + BLOCKED,
            ),
        )
        assert digest(original) == original_bytes and digest(branch_source) == branch_bytes
        assert (digest(slot), digest(previous)) == slot_bytes
    owner = session(branch)
    try:
        io = state_io((bundle(),))
        segment = owner.owner.retained_segment()
        assert segment.checkpoint.core.tick == 0
        assert read_segment(branch, io=io) == segment
        state = io.hash_core(owner.owner.snapshot())
        protocol = hash_document("protocol/v1", io.encode_protocol(owner.owner.protocol()))
        replay(owner)
    finally:
        owner.close()
    with sqlite3.connect(branch.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        bodies = connection.execute("SELECT body FROM checkpoint WHERE singleton=1").fetchone()
        assert bodies is not None
        records = connection.execute(
            "SELECT revision,body,sha256 FROM replay ORDER BY revision"
        ).fetchall()
    persisted = canonical_json(
        {
            "checkpoint": bodies[0].hex(),
            "records": tuple({"revision": n, "body": b.hex(), "hash": h} for n, b, h in records),
        }
    )
    (tmp_path / "scenario-result.json").write_bytes(
        canonical_json(
            {
                "updates": tuple(history),
                "core": state,
                "protocol": protocol,
                "persisted_bodies_sha256": hashlib.sha256(persisted).hexdigest(),
                "source_checkpoint_tick": 0,
                "source_preserved": True,
                "steps": len(history),
            }
        )
    )
