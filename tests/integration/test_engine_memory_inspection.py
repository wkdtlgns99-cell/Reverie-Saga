from __future__ import annotations

from pathlib import Path

from app.engine_project import generate_wire
from domain.canonical import JsonObject, array_value, object_value, text_value
from tests.integration.test_engine_bridge import PipeClient, pipe as pipe, view
from tests.integration.test_memory_client_route import memory_pipe
from tests.integration.test_quest import GOAL


def inspect(pipe: PipeClient) -> JsonObject:
    before = object_value(pipe.latest["update"])
    path = Path(text_value(before["working_path"]))
    source = path.read_bytes()
    reply = pipe.send("memory")
    update = object_value(reply["update"])
    assert reply["error"] == "" and update["status"] == "MEMORY_INSPECTED"
    assert update["view"] == before["view"]
    for key in ("attachment_id", "working_path", "quest_stage", "quest_reward", "dialogue_sha256"):
        assert update[key] == before[key]
    assert update["reset_log"] is False and path.read_bytes() == source
    return update


def test_actual_pipe_memory_queries_preserve_turn_reward_retry_and_branch(tmp_path: Path) -> None:
    working = tmp_path / "memory.sqlite"
    with memory_pipe(tmp_path, working) as pipe:
        empty = inspect(pipe)
        assert array_value(empty["messages"]) == (
            "NPC에게 아직 기록된 플레이어와의 의뢰 대화가 없습니다.",
        )
        for action in GOAL[:2]:
            pipe.send(action)
        accepted = inspect(pipe)
        assert len(array_value(accepted["messages"])) == 1
        assert "2초:" in text_value(array_value(accepted["messages"])[0])
        assert view(pipe.latest)["tick"] == "2"
        retried = pipe.send("retry")
        assert view(retried)["tick"] == "2"
        pipe.send("save")
        for action in GOAL[2:]:
            pipe.send(action)
        unreported = inspect(pipe)
        assert unreported["messages"] == accepted["messages"]
        assert view(pipe.latest)["tick"] == "9"
        pipe.send("left")
        pipe.send("talk")
        reported = inspect(pipe)
        lines = array_value(reported["messages"])
        assert len(lines) == 2
        assert "11초:" in text_value(lines[1])
        assert "완료 보고를 받았습니다" in text_value(lines[1])
        assert "직접 본 기억은 아닙니다" in text_value(lines[1])
        assert reported["quest_reward"] == "1"
        retry = pipe.send("retry")
        assert view(retry) == reported["view"]
        assert object_value(retry["update"])["quest_reward"] == "1"
        stale_token = pipe.token
        loaded = pipe.send("load")
        active_path = Path(text_value(object_value(loaded["update"])["working_path"]))
        assert active_path != working and pipe.token != stale_token
        stale = pipe.send("memory", token=stale_token)
        assert stale["error"] == "STALE_ATTACHMENT" and view(stale) == view(loaded)
        restored = inspect(pipe)
        assert restored["messages"] == accepted["messages"]
        assert restored["quest_reward"] == "0"
        duplicate = pipe.send("memory", sequence=pipe.id)
        # pipe.send increments its ID;the supplied old ID repeats the preceding query.
        assert duplicate["error"] == "STALE_REQUEST" and view(duplicate) == restored["view"]
        assert view(pipe.send("wait"))["tick"] == "3"
    with memory_pipe(tmp_path, active_path) as resumed:
        assert inspect(resumed)["messages"] == accepted["messages"]


def test_memory_unavailable_over_real_legacy_pipe_is_explicit_and_nonfatal(
    pipe: PipeClient,
) -> None:
    before = view(pipe.latest)
    path = Path(text_value(object_value(pipe.latest["update"])["working_path"]))
    source = path.read_bytes()
    reply = pipe.send("memory")
    assert reply["error"] == ""
    assert object_value(reply["update"])["status"] == "NPC_MEMORY_UNAVAILABLE"
    assert view(reply) == before and path.read_bytes() == source
    assert view(pipe.send("wait"))["tick"] == "1"


def test_current_generated_wire_pins_the_added_memory_request() -> None:
    from app.engine_bridge import REQUEST_NAMES, SCHEMA_HASH

    root = Path(__file__).resolve().parents[2]
    assert REQUEST_NAMES.count("memory") == 1
    assert SCHEMA_HASH != "b7b0820833f1e644fc946ff3a7e4c5544eb3efffd03c81f21feaef50d078b069"
    assert (root / "clients/unity/Assets/Reverie/Scripts/Wire.Generated.cs").read_text(
        encoding="utf-8"
    ) == generate_wire()
