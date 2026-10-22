from __future__ import annotations

import os
from pathlib import Path
import sqlite3
from typing import cast

import pytest

from adapters.sqlite_store import validate_save
from app.client_session import ClientSession
from app.client_worker import ClientWorker
from app.durable import create_durable
from app.engine_project import generate_wire
from app.watch_registry import watch_bundle
from contracts.persistence import SaveError, WorldUnavailable
from contracts.watch import WaitCommand
from domain.canonical import object_value, text_value
from tests.integration.test_durable_turn import UncertainPort
from tests.integration.test_engine_bridge import PipeClient, pipe as pipe, view
from tests.integration.test_memory_client_route import memory_pipe
from tests.integration.test_unity_slot_selection import send_slot
from tests.unit.durability_fixtures import checkpoint, io
from tests.unit.watch_fixtures import command


def test_corrupt_current_explicit_previous_branch_and_restart(tmp_path: Path) -> None:
    working = tmp_path / "game.sqlite"
    owner = ClientSession(working)
    try:
        owner.act("wait")
        owner.save("slot01")
        owner.act("wait", seconds=2)
        owner.save("slot01")
        owner.act("wait")
        current = tmp_path / "slots/slot01.sqlite"
        previous = tmp_path / "slots/slot01.previous.sqlite"
        assert owner.owner.inspect_slot("slot01").core.tick == 3
        assert owner.owner.inspect_slot("slot01", previous=True).core.tick == 1
        current.write_bytes(b"damaged-latest")
        originals = current.read_bytes(), previous.read_bytes(), working.read_bytes()
        state = owner.owner.snapshot(), owner.owner.protocol(), owner.owner.attachment_id
        preview = owner.inspect_slot("slot01", previous=True)
        assert preview.messages == ("slot01 이전 저장 정보 · 1초 · 진행 1",)
        assert not preview.reset_log
        with pytest.raises(SaveError, match="^SAVE_CORRUPT:"):
            owner.load("slot01")
        assert (owner.owner.snapshot(), owner.owner.protocol(), owner.owner.attachment_id) == state
        loaded = owner.load("slot01", previous=True)
        assert loaded.status == "LOADED" and loaded.reset_log
        assert loaded.view is not None and loaded.view.tick == 1
        assert "이전 저장" in loaded.messages[0]
        branch = Path(loaded.working_path)
        assert branch != working and branch.name.startswith(".loaded-")
        assert loaded.attachment_id != state[2]
        assert (current.read_bytes(), previous.read_bytes(), working.read_bytes()) == originals
        with pytest.raises(ValueError, match="^NO_RETRY$"):
            owner.retry()
        owner.act("wait")
        owner.save("slot08")
        expected = owner.owner.snapshot(), owner.owner.protocol()
    finally:
        owner.close()
    resumed = ClientSession(branch)
    try:
        assert (resumed.owner.snapshot(), resumed.owner.protocol()) == expected
        assert resumed.owner.inspect_slot("slot08").core.tick == 2
        assert (current.read_bytes(), previous.read_bytes(), working.read_bytes()) == originals
    finally:
        resumed.close()


@pytest.mark.parametrize("method", ("inspect_slot", "load"))
@pytest.mark.parametrize("bad", (0, 1, None, "previous", (), 0.0))
def test_exact_version_type_preserves_owner(tmp_path: Path, method: str, bad: object) -> None:
    with create_durable(tmp_path / "game.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        owner.export("slot01")
        before = owner.snapshot(), owner.protocol(), owner.attachment_id
        with pytest.raises(SaveError, match="^INVALID_SLOT_VERSION:"):
            getattr(owner, method)("slot01", previous=cast(bool, bad))
        assert (owner.snapshot(), owner.protocol(), owner.attachment_id) == before
        assert not list(tmp_path.glob(".loaded-*.sqlite"))


@pytest.mark.parametrize("method", ("inspect_slot", "load"))
@pytest.mark.parametrize("bad", ("slot00", "slot09", "../slot01", True))
def test_previous_invalid_slot(tmp_path: Path, method: str, bad: object) -> None:
    with create_durable(tmp_path / "game.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        with pytest.raises(SaveError, match="^INVALID_SLOT:"):
            getattr(owner, method)(bad, previous=True)
        assert owner.snapshot().tick == 0
        assert not list((tmp_path / "slots").iterdir())


@pytest.mark.parametrize("method", ("inspect_slot", "load"))
def test_missing_corrupt_alias_and_busy_previous_do_not_fallback(
    tmp_path: Path, method: str
) -> None:
    with create_durable(tmp_path / "game.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        owner.export("slot01")
        selected = getattr(owner, method)
        previous = tmp_path / "slots/slot01.previous.sqlite"
        before = owner.snapshot(), owner.protocol(), owner.attachment_id
        with pytest.raises(SaveError, match="^PREVIOUS_SAVE_NOT_FOUND:"):
            selected("slot01", previous=True)
        previous.write_bytes(b"corrupt-backup")
        with pytest.raises(SaveError, match="^SAVE_CORRUPT:"):
            selected("slot01", previous=True)
        assert previous.read_bytes() == b"corrupt-backup"
        previous.unlink()
        owner.export("slot01")
        alias = tmp_path / "alias.sqlite"
        os.link(previous, alias)
        try:
            with pytest.raises(SaveError, match="^INVALID_PATH:"):
                selected("slot01", previous=True)
        finally:
            alias.unlink()
        for target in (owner, owner._attachment.slots):
            target._busy = True
            try:
                with pytest.raises(SaveError, match="^SAVE_BUSY:"):
                    selected("slot01", previous=True)
            finally:
                target._busy = False
        assert (owner.snapshot(), owner.protocol(), owner.attachment_id) == before
        assert not list(tmp_path.glob(".loaded-*.sqlite"))


@pytest.mark.parametrize("commit", (False, True))
def test_previous_operations_respect_uncertain_commit(tmp_path: Path, commit: bool) -> None:
    with create_durable(tmp_path / "game.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        owner.export("slot01")
        owner.export("slot01")
        port = UncertainPort(owner._attachment.store, commit=commit, unreadable=True)
        owner._attachment.owner._driver._commit_port = port
        with pytest.raises(WorldUnavailable, match="^SAVE_UNCERTAIN:"):
            owner.submit(command(WaitCommand(16)), attachment_id=owner.attachment_id)
        for method in (owner.inspect_slot, owner.load):
            with pytest.raises(WorldUnavailable, match="^SAVE_UNCERTAIN:"):
                method("slot01", previous=True)
        assert not list(tmp_path.glob(".loaded-*.sqlite"))
        port.unreadable = False
        owner.recover()
        assert owner.snapshot().tick == (16 if commit else 0)
        assert owner.inspect_slot("slot01", previous=True).core.tick == 0


@pytest.mark.parametrize("failure", ("backup", "connect", "prepare", "limit"))
def test_previous_load_failure_cleans_only_owned_resources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    with create_durable(tmp_path / "game.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        owner.export("slot01")
        owner.export("slot01")
        before = owner.snapshot(), owner.protocol(), owner.attachment_id
        originals = {p: p.read_bytes() for p in tmp_path.rglob("*.sqlite")}

        def unavailable(*args: object, **kwargs: object) -> None:
            raise sqlite3.OperationalError("injected previous-load failure")

        if failure == "limit":
            for index in range(8):
                (tmp_path / f".loaded-{index:032x}.sqlite").write_bytes(b"unowned")
        with monkeypatch.context() as patch:
            if failure == "backup":
                patch.setattr("adapters.save_slots._backup_file_reserved", unavailable)
            elif failure == "connect":
                patch.setattr("adapters.save_slots.SqliteCommitStore.open", unavailable)
            elif failure == "prepare":
                patch.setattr("app.durable._owner", unavailable)
            with pytest.raises(
                SaveError, match="^SAVE_" + ("LIMIT:" if failure == "limit" else "LOAD_FAILED:")
            ):
                owner.load("slot01", previous=True)
        assert (owner.snapshot(), owner.protocol(), owner.attachment_id) == before
        assert all(p.read_bytes() == body for p, body in originals.items())
        assert len(list(tmp_path.glob(".loaded-*.sqlite"))) == (8 if failure == "limit" else 0)
        assert owner._attachment.slots._owned == set()


def test_previous_worker_registered_route_and_unattached_guard(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    worker = ClientWorker(path)
    try:
        assert (
            worker.inspect_previous_slot().result(timeout=30).status
            == "SLOT_INSPECTION_UNAVAILABLE"
        )
        assert not path.exists()
        worker.request("attach").result(timeout=30)
        assert (
            worker.request("load_previous").result(timeout=30).status == "PREVIOUS_SAVE_NOT_FOUND"
        )
        worker.request("save").result(timeout=30)
        worker.request("wait").result(timeout=30)
        worker.request("save").result(timeout=30)
        assert (
            worker.inspect_previous_slot()
            .result(timeout=30)
            .messages[0]
            .startswith("slot01 이전 저장 정보 · 0초")
        )
        assert worker.request("load_previous").result(timeout=30).status == "LOADED"
    finally:
        worker.join()


def test_actual_pipe_previous_corruption_and_stale_requests(pipe: PipeClient) -> None:
    assert (
        object_value(pipe.send("slot_previous_inspect")["update"])["status"]
        == "PREVIOUS_SAVE_NOT_FOUND"
    )
    pipe.send("wait")
    pipe.send("save")
    pipe.send("wait")
    pipe.send("save")
    token = pipe.token
    working = Path(text_value(object_value(pipe.latest["update"])["working_path"]))
    current = working.parent / "slots/slot01.sqlite"
    backup = working.parent / "slots/slot01.previous.sqlite"
    current.write_bytes(b"corrupt-latest")
    bodies = current.read_bytes(), backup.read_bytes(), working.read_bytes()
    assert object_value(pipe.send("load")["update"])["status"] == "SAVE_CORRUPT"
    preview = pipe.send("slot_previous_inspect")
    assert object_value(preview["update"])["messages"] == ("slot01 이전 저장 정보 · 1초 · 진행 1",)
    assert view(preview)["tick"] == "2"
    loaded = pipe.send("load_previous")
    assert view(loaded)["tick"] == "1" and pipe.token != token
    branch = Path(text_value(object_value(loaded["update"])["working_path"]))
    clones = tuple(working.parent.glob(".loaded-*.sqlite"))
    assert pipe.send("load_previous", sequence=pipe.id)["error"] == "STALE_REQUEST"
    assert pipe.send("load_previous", token=token)["error"] == "STALE_ATTACHMENT"
    assert tuple(working.parent.glob(".loaded-*.sqlite")) == clones
    assert (current.read_bytes(), backup.read_bytes(), working.read_bytes()) == bodies
    assert branch != working and validate_save(branch, io=io()).core.tick == 1


def test_memory_previous_pipe_fresh_process_retains_pins(tmp_path: Path) -> None:
    working = tmp_path / "memory.sqlite"
    with memory_pipe(tmp_path, working) as client:
        client.send("down")
        client.send("talk")
        send_slot(client, "save", "slot08")
        client.send("wait")
        send_slot(client, "save", "slot08")
        preview = send_slot(client, "slot_previous_inspect", "slot08")
        assert "NPC 기억 비교" in "\n".join(
            cast(tuple[str, ...], object_value(preview["update"])["messages"])
        )
        loaded = send_slot(client, "load_previous", "slot08")
        assert view(loaded)["tick"] == "2"
        branch = Path(text_value(object_value(loaded["update"])["working_path"]))
        client.send("wait")
        expected = view(client.latest)
    original = branch.read_bytes()
    with memory_pipe(tmp_path, branch) as resumed:
        assert view(resumed.latest) == expected
        assert branch.read_bytes() == original
        assert object_value(resumed.send("memory")["update"])["status"] == "MEMORY_INSPECTED"
        assert branch.read_bytes() == original


def test_previous_request_generated_schema_matches_source() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "clients/unity/Assets/Reverie/Scripts/Wire.Generated.cs").read_text(
        encoding="utf-8"
    ) == generate_wire()
