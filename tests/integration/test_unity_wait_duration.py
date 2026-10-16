from __future__ import annotations

from pathlib import Path

import pytest

from domain.canonical import JsonObject, canonical_json, object_value, text_value
from domain.watch import WAIT_MAX
from tests.integration.test_engine_bridge import PipeClient, pipe as pipe, view


def send_seconds(client: PipeClient, intent: str, seconds: str) -> JsonObject:
    client.id += 1
    body = canonical_json(
        {
            "kind": "request",
            "version": "1",
            "request_id": str(client.id),
            "attachment_id": client.token,
            "request": intent,
            "seconds": seconds,
            "slot_id": "slot01",
        }
    )
    assert client.process.stdin is not None
    client.process.stdin.write(len(body).to_bytes(4, "big") + body)
    client.process.stdin.flush()
    return client.read()


@pytest.mark.parametrize("seconds", (1, 4, 8, 16))
def test_actual_pipe_wait_presets_retry_and_slot_restore(pipe: PipeClient, seconds: int) -> None:
    assert seconds <= WAIT_MAX
    pipe.send("save")
    waited = send_seconds(pipe, "wait", str(seconds))
    update = object_value(waited["update"])
    assert waited["error"] == "" and update["status"] == "COMMITTED"
    assert view(waited)["tick"] == str(seconds)
    assert view(waited)["revision"] == "1"
    current = Path(text_value(update["working_path"]))
    before = current.read_bytes()
    # A different duration in the retry envelope cannot replace the retained command.
    replayed = send_seconds(pipe, "retry", "4" if seconds != 4 else "16")
    assert view(replayed) == view(waited)
    assert current.read_bytes() == before
    loaded = pipe.send("load")
    assert view(loaded)["tick"] == "0"
    assert object_value(loaded["update"])["reset_log"] is True
    assert object_value(pipe.send("retry")["update"])["status"] == "NO_RETRY"


@pytest.mark.parametrize("seconds", ("-1", "17", "01", "1.0"))
def test_invalid_wire_wait_has_no_write_and_client_continues(
    pipe: PipeClient, seconds: str
) -> None:
    working = Path(text_value(object_value(pipe.latest["update"])["working_path"]))
    before = working.read_bytes(), view(pipe.latest)
    rejected = send_seconds(pipe, "wait", seconds)
    assert rejected["error"] == "INVALID_REQUEST"
    assert (working.read_bytes(), view(rejected)) == before
    assert view(pipe.send("wait"))["tick"] == "1"


def test_zero_wait_is_gameplay_rejection_without_advance(pipe: PipeClient) -> None:
    original = view(pipe.latest)
    reply = send_seconds(pipe, "wait", "0")
    assert reply["error"] == ""
    assert object_value(reply["update"])["status"] == "INVALID_COMMAND"
    assert view(reply) == original
