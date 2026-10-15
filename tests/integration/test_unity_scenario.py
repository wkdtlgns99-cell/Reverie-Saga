from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import subprocess
import sys
from typing import Iterator

from app.engine_project import build_sample
from domain.canonical import JsonObject, object_value
from tests.integration.test_engine_bridge import PipeClient


ROOT = Path(__file__).resolve().parents[2]


def arguments(path: Path, catalog: Path, digest: str, scenario: str) -> list[str]:
    return [
        sys.executable,
        "-m",
        "app.engine_bridge",
        "--working",
        str(path),
        "--catalog",
        str(catalog),
        "--catalog-sha256",
        digest,
        "--scenario",
        scenario,
    ]


@contextmanager
def connected(path: Path, catalog: Path, digest: str, scenario: str) -> Iterator[PipeClient]:
    process = subprocess.Popen(
        arguments(path, catalog, digest, scenario),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    try:
        yield PipeClient(process)
    finally:
        if process.stdin is not None:
            process.stdin.close()
        try:
            process.wait(timeout=15)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=15)
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()


def state(response: JsonObject) -> JsonObject:
    return object_value(object_value(response["update"])["view"])


def test_real_courtyard_pipe_save_retry_reconnect_and_wrong_scenario(tmp_path: Path) -> None:
    body, _ = build_sample(ROOT)
    catalog = tmp_path / "catalog.json"
    catalog.write_bytes(body)
    digest = hashlib.sha256(body).hexdigest()
    path = tmp_path / "game.sqlite"
    with connected(path, catalog, digest, "scenario:courtyard") as pipe:
        initial = state(pipe.latest)
        assert (
            initial["actor_cell"],
            initial["enemy_cell"],
            initial["gate_cell"],
            initial["npc_cell"],
            initial["walls"],
        ) == ("6", "0", "2", "8", ("7",))
        assert state(pipe.send("up"))["actor_cell"] == "3"
        attacked = state(pipe.send("attack"))
        assert (attacked["actor_hp"], attacked["enemy_hp"], attacked["stamina"]) == ("2", "3", "1")
        saved = state(pipe.send("save"))
        pipe.send("attack")
        loaded = pipe.send("load")
        assert state(loaded) == saved
        once = state(pipe.send("attack"))
        assert state(pipe.send("retry")) == once
        branch = Path(str(object_value(loaded["update"])["working_path"]))
    with connected(branch, catalog, digest, "scenario:courtyard") as pipe:
        assert state(pipe.latest) == once
        assert state(pipe.send("rest"))["stamina"] == "1"
    before = branch.read_bytes()
    with connected(branch, catalog, digest, "scenario:legacy") as pipe:
        assert pipe.latest["has_view"] is False
        assert object_value(pipe.latest["update"])["status"] == "UNSUPPORTED_RULESET"
    assert branch.read_bytes() == before


def test_invalid_scenario_cli_does_not_create_save(tmp_path: Path) -> None:
    body, _ = build_sample(ROOT)
    catalog = tmp_path / "catalog.json"
    catalog.write_bytes(body)
    path = tmp_path / "never-created.sqlite"
    result = subprocess.run(
        arguments(path, catalog, hashlib.sha256(body).hexdigest(), "not-registered"),
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        input=b"",
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 1
    assert b"UNKNOWN_SCENARIO" in result.stderr
    assert result.stdout == b""
    assert not path.exists()
