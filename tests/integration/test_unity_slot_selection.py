from __future__ import annotations

from pathlib import Path

import pytest

from domain.canonical import JsonObject, canonical_json, object_value, text_value
from tests.integration.test_engine_bridge import PipeClient, pipe as pipe, view


def send_slot(client: PipeClient, intent: str, slot: str) -> JsonObject:
    client.id += 1
    body = canonical_json(
        {
            "kind": "request",
            "version": "1",
            "request_id": str(client.id),
            "attachment_id": client.token,
            "request": intent,
            "seconds": "1",
            "slot_id": slot,
        }
    )
    assert client.process.stdin is not None
    client.process.stdin.write(len(body).to_bytes(4, "big") + body)
    client.process.stdin.flush()
    return client.read()


def test_actual_pipe_selected_slots_are_distinct_and_restore_selected_state(
    pipe: PipeClient,
) -> None:
    working = Path(text_value(object_value(pipe.latest["update"])["working_path"]))
    original = working.read_bytes()
    assert (
        object_value(send_slot(pipe, "slot_inspect", "slot08")["update"])["status"]
        == "SAVE_NOT_FOUND"
    )
    assert working.read_bytes() == original
    send_slot(pipe, "save", "slot08")
    pipe.send("wait")
    send_slot(pipe, "save", "slot02")
    root = working.parent / "slots"
    assert (root / "slot02.sqlite").is_file() and (root / "slot08.sqlite").is_file()
    assert not (root / "slot01.sqlite").exists()
    before = (
        working.read_bytes(),
        (root / "slot02.sqlite").read_bytes(),
        (root / "slot08.sqlite").read_bytes(),
    )
    response = send_slot(pipe, "slot_inspect", "slot08")
    assert view(response)["tick"] == "1"
    update = object_value(response["update"])
    assert update["messages"] == ("slot08 저장 정보 · 0초 · 진행 0",)
    assert (
        working.read_bytes(),
        (root / "slot02.sqlite").read_bytes(),
        (root / "slot08.sqlite").read_bytes(),
    ) == before
    loaded = send_slot(pipe, "load", "slot08")
    assert view(loaded)["tick"] == "0"
    assert object_value(loaded["update"])["reset_log"] is True
    assert text_value(object_value(loaded["update"])["working_path"]) != str(working)
    assert object_value(send_slot(pipe, "slot_inspect", "slot02")["update"])["messages"] == (
        "slot02 저장 정보 · 1초 · 진행 1",
    )
    assert view(send_slot(pipe, "load", "slot02"))["tick"] == "1"


@pytest.mark.parametrize("slot", ("slot00", "slot09", "../slot01", "slot1"))
def test_invalid_slot_does_not_advance_or_write(pipe: PipeClient, slot: str) -> None:
    before = view(pipe.latest)
    working = Path(text_value(object_value(pipe.latest["update"])["working_path"]))
    original = working.read_bytes()
    reply = send_slot(pipe, "slot_inspect", slot)
    assert reply["error"] == "INVALID_REQUEST"
    assert object_value(reply["update"])["status"] == "ATTACHED"
    assert view(reply) == before and working.read_bytes() == original
    assert not list((working.parent / "slots").iterdir())
