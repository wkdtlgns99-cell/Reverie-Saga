"""Public direct/framed oracle for the deferred Unity answered-call scenario."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
import hashlib

import pytest

from app.engine_bridge import wire
from contracts.client import ClientAction
from domain.canonical import JsonObject, array_value, object_value, text_value
from tests.integration.test_npc_call_aid import call_pipe, session

OPENED = "NPC가 의뢰를 돕기 위해 통행문을 열었습니다."
READY = "NPC 지원 계획 · 공동 물자가 확보되어 NPC 호출로 통행 지원을 요청할 수 있습니다."


@contextmanager
def driver(path: Path, framed: bool) -> Iterator[Callable[[str], JsonObject]]:
    if framed:
        with call_pipe(path) as pipe:
            yield lambda action: object_value(pipe.send(action)["update"])
        return
    owner = session(path)
    actions: dict[str, ClientAction] = {
        "down": "down",
        "up": "up",
        "left": "left",
        "right": "right",
        "attack": "attack",
        "rest": "rest",
        "wait": "wait",
        "talk": "talk",
        "bell": "bell",
        "close": "close",
    }

    def send(action: str) -> JsonObject:
        if action == "save":
            update = owner.save("slot01")
        elif action == "load_previous":
            update = owner.load("slot01", previous=True)
        elif action == "slot_previous_inspect":
            update = owner.inspect_slot("slot01", previous=True)
        elif action == "activity":
            update = owner.inspect_activity()
        elif action == "retry":
            update = owner.retry()
        else:
            update = owner.act(actions[action])
        return object_value(wire(asdict(update)))

    try:
        yield send
    finally:
        owner.close()


def lines(update: JsonObject) -> tuple[str, ...]:
    return tuple(text_value(line) for line in array_value(update["messages"]))


def position(update: JsonObject, tick: int, opened: bool) -> None:
    view = object_value(update["view"])
    assert view["tick"] == str(tick)
    assert view["gate_open"] is opened
    assert view["npc_cell"] == "6"
    assert update["status"] == "COMMITTED"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_activity(
    send: Callable[[str], JsonObject],
    path: Path,
    current: JsonObject,
    summary: str,
    calls: tuple[int, ...],
    call_total: int,
    aid: tuple[int, ...],
) -> None:
    before = digest(path)
    result = send("activity")
    assert result["status"] == "ACTIVITY_INSPECTED"
    assert result["view"] == current["view"] and digest(path) == before
    text = lines(result)
    assert text[0] == summary
    assert f"확인한 호출 응답 {call_total}건 중 최근 {len(calls)}건입니다." in text
    assert "NPC 의뢰 지원 · 0초 이후 저장 구간의 최근 최대 3건입니다." in text
    assert tuple(
        line for line in text if line.startswith("NPC 호출 회상 · ") and "초의" in line
    ) == tuple(
        f"NPC 호출 회상 · {tick}초의 플레이어 호출에 {tick}초에 응답했습니다." for tick in calls
    )
    assert tuple(line for line in text if line.startswith("NPC 의뢰 지원 기록 · ")) == tuple(
        f"NPC 의뢰 지원 기록 · {tick}초: 통행문을 열었습니다." for tick in aid
    )


@pytest.mark.parametrize("framed", (False, True), ids=("direct", "real-pipe"))
def test_answered_call_native_scenario_contract(tmp_path: Path, framed: bool) -> None:
    path = tmp_path / "game.sqlite"
    original = path
    with driver(path, framed) as send:
        send("down")
        position(send("talk"), 2, False)
        send("save")
        for _ in range(5):
            send("wait")
        low = send("bell")
        position(low, 8, False)
        assert OPENED not in lines(low)
        read_activity(
            send, path, low, "NPC 반복 작업: 물자 2/3개 · 준비 2회 · 사용 0회.", (8,), 1, ()
        )
        send("save")
        opened = send("bell")
        position(opened, 9, True)
        assert lines(opened).count(OPENED) == 1
        before = digest(path)
        retry = send("retry")
        assert retry["view"] == opened["view"] and OPENED not in lines(retry)
        assert digest(path) == before
        read_activity(
            send, path, opened, "NPC 반복 작업: 물자 2/3개 · 준비 2회 · 사용 0회.", (8, 9), 2, (9,)
        )
        send("save")
        position(send("talk"), 10, True)
        before = digest(path)
        selected = send("slot_previous_inspect")
        assert selected["status"] == "SLOT_INSPECTED" and digest(path) == before
        assert "NPC 지원 계획 비교 · 현재 10초 / 선택 저장 8초" in lines(selected)
        assert "선택 저장 " + READY in lines(selected)
        loaded = send("load_previous")
        assert object_value(loaded["view"])["tick"] == "8"
        assert object_value(loaded["view"])["gate_open"] is False
        path = Path(text_value(loaded["working_path"]))
        assert path != original and digest(original) == before
        source_bytes = before

    with driver(path, framed) as send:
        opened = send("bell")
        position(opened, 9, True)
        assert lines(opened).count(OPENED) == 1
        position(send("wait"), 10, True)
        position(send("close"), 11, False)
        low = send("bell")
        position(low, 12, False)
        assert OPENED not in lines(low)
        opened = send("bell")
        position(opened, 13, True)
        assert lines(opened).count(OPENED) == 1
        read_activity(
            send,
            path,
            opened,
            "NPC 반복 작업: 물자 2/3개 · 준비 3회 · 사용 1회.",
            (9, 12, 13),
            4,
            (9, 13),
        )
        send("save")
        talk = send("talk")
        position(talk, 14, True)
        assert tuple(line for line in lines(talk) if line.startswith("NPC 의뢰 지원 회상 · ")) == (
            "NPC 의뢰 지원 회상 · 지난 대화(2초) 뒤에 도운 기록입니다.",
            "NPC 의뢰 지원 회상 · 9초: 통행문을 열었습니다.",
            "NPC 의뢰 지원 회상 · 13초: 통행문을 열었습니다.",
        )
        for action in ("right", "down", "attack", "attack", "rest", "attack", "up", "left"):
            send(action)
        report = send("talk")
        position(report, 23, True)
        assert report["quest_reward"] == "1"
        position(send("close"), 24, False)
        after = send("bell")
        position(after, 25, False)
        assert OPENED not in lines(after)
        read_activity(
            send,
            path,
            after,
            "NPC 반복 작업: 물자 3/3개 · 준비 5회 · 사용 2회.",
            (12, 13, 25),
            5,
            (9, 13),
        )

    assert digest(original) == source_bytes
