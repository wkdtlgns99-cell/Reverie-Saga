from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
from typing import Iterator

import pytest

from app.engine_bridge import EngineBridge, SCHEMA_HASH, read_exact, read_frame
from app.engine_project import build_sample
from domain.canonical import (
    JsonObject,
    JsonValue,
    array_value,
    canonical_json,
    object_value,
    decode_json,
)


class PipeClient:
    def __init__(self, process: subprocess.Popen[bytes]) -> None:
        self.process = process
        self.id = 0
        self.token = ""
        self.latest = self.read()

    def read(self) -> JsonObject:
        assert self.process.stdout is not None
        size = int.from_bytes(read_exact(self.process.stdout, 4), "big")
        value = object_value(decode_json(read_exact(self.process.stdout, size)))
        assert value["schema_hash"] == SCHEMA_HASH
        update = object_value(value["update"])
        token = update["attachment_id"]
        assert isinstance(token, str)
        self.token = token
        self.latest = value
        return value

    def send(
        self, intent: str, *, token: str | None = None, sequence: int | None = None
    ) -> JsonObject:
        self.id += 1
        body = canonical_json(
            {
                "kind": "request",
                "version": "1",
                "request_id": str(self.id if sequence is None else sequence),
                "attachment_id": self.token if token is None else token,
                "request": intent,
                "seconds": "1",
                "slot_id": "slot01",
            }
        )
        assert self.process.stdin is not None
        self.process.stdin.write(len(body).to_bytes(4, "big") + body)
        self.process.stdin.flush()
        return self.read()


@pytest.fixture
def pipe(tmp_path: Path) -> Iterator[PipeClient]:
    root = Path(__file__).resolve().parents[2]
    body, _ = build_sample(root)
    catalog = tmp_path / "catalog.json"
    catalog.write_bytes(body)
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "app.engine_bridge",
            "--working",
            str(tmp_path / "game.sqlite"),
            "--catalog",
            str(catalog),
            "--catalog-sha256",
            hashlib.sha256(body).hexdigest(),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=root / "src",
    )
    try:
        client = PipeClient(process)
        yield client
    finally:
        if process.stdin is not None:
            process.stdin.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
            pytest.fail("Brain orphaned after parent pipe EOF")
        assert process.returncode == 0
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()


def view(reply: JsonObject) -> JsonObject:
    return object_value(object_value(reply["update"])["view"])


def test_real_pipe_play_combat_save_load_and_exact_retry(pipe: PipeClient) -> None:
    assert view(pipe.latest)["actor_cell"] == "0"
    assert len(array_value(pipe.latest["narratives"])) == 6
    assert view(pipe.send("right"))["actor_cell"] == "0"
    assert view(pipe.send("down"))["actor_cell"] == "3"
    assert view(pipe.send("right"))["actor_cell"] == "3"
    pipe.send("open")
    pipe.send("right")
    pipe.send("down")
    hit = view(pipe.send("attack"))
    assert (hit["actor_hp"], hit["enemy_hp"], hit["stamina"]) == ("2", "3", "1")
    pipe.send("save")
    old_token = pipe.token
    pipe.send("attack")
    loaded = pipe.send("load")
    assert view(loaded) == hit
    assert pipe.token != old_token
    before = view(loaded)
    stale = pipe.send("attack", token=old_token)
    assert stale["error"] == "STALE_ATTACHMENT" and view(stale) == before
    hit_again = view(pipe.send("attack"))
    assert view(pipe.send("retry")) == hit_again
    pipe.send("rest")
    assert view(pipe.send("attack"))["enemy_hp"] == "0"
    assert view(pipe.send("right"))["actor_cell"] == "8"


def test_duplicate_transport_identity_does_not_apply_another_turn(pipe: PipeClient) -> None:
    first = pipe.send("down")
    duplicate = pipe.send("down", sequence=1)
    assert duplicate["error"] == "STALE_REQUEST"
    assert view(duplicate) == view(first)


def test_malformed_json_preserves_real_session_then_valid_command_works(pipe: PipeClient) -> None:
    before = view(pipe.latest)
    assert pipe.process.stdin is not None
    bad = b'{"kind":"request","kind":"request"}'
    pipe.process.stdin.write(len(bad).to_bytes(4, "big") + bad)
    pipe.process.stdin.flush()
    reply = pipe.read()
    assert reply["error"] == "INVALID_REQUEST" and view(reply) == before
    assert view(pipe.send("down"))["actor_cell"] == "3"


@pytest.mark.parametrize("header", [b"\x00\x00\x00\x00", (16385).to_bytes(4, "big")])
def test_frame_boundaries_reject_before_body_allocation(header: bytes) -> None:
    with pytest.raises(ValueError, match="^FRAME_LENGTH$"):
        read_frame(io.BytesIO(header))


def test_partial_frame_eof_is_explicit() -> None:
    with pytest.raises(EOFError, match="^TRUNCATED_FRAME$"):
        read_frame(io.BytesIO(b"\x00\x00\x00\x04ab"))


def test_numeric_wire_fields_are_canonical_and_bad_input_does_not_mutate(tmp_path: Path) -> None:
    bridge = EngineBridge(tmp_path / "direct.sqlite", ())
    try:
        before = bridge.last
        base: dict[str, JsonValue] = {
            "kind": "request",
            "version": "1",
            "request_id": "1",
            "attachment_id": bridge.last.attachment_id,
            "request": "down",
            "seconds": "1",
            "slot_id": "slot01",
        }
        for bad in (1, True, "01", "1.0", "+1", " 1", "-0"):
            base["request_id"] = bad
            with pytest.raises(ValueError, match="^WIRE_INTEGER$"):
                bridge.request(json.dumps(base).encode())
            assert bridge.last == before
    finally:
        bridge.close()
