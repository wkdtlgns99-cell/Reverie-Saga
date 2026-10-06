from __future__ import annotations

from pathlib import Path
import os
import sqlite3
import subprocess
import sys
from threading import Timer

import pytest

from adapters.save_slots import file_sha256
from adapters.sqlite_store import validate_save
from app.durable import create_durable, resume_durable
from app.watch_registry import watch_bundle
from contracts.persistence import DurableCheckpoint, SaveError, WorldUnavailable
from contracts.watch import WaitCommand
from tests.unit.durability_fixtures import ROOT, checkpoint, io, requirements
from tests.unit.watch_fixtures import command


def test_export_previous_generation_and_atomic_load(tmp_path: Path) -> None:
    original = tmp_path / "work.sqlite"
    owner = create_durable(original, checkpoint(), bundles=(watch_bundle(),))
    try:
        first = owner.export("slot01")
        current = tmp_path / "slots/slot01.sqlite"
        assert first.file_sha256 == file_sha256(current)
        assert first.directory_synced is (os.name != "nt")
        saved = DurableCheckpoint(owner.snapshot(), owner.protocol())
        owner.submit(command(WaitCommand(2)), attachment_id=owner.attachment_id)
        second = owner.export("slot01")
        assert second.revision == 1 and first.revision == 0
        assert validate_save(tmp_path / "slots/slot01.previous.sqlite", io=io()) == saved
        newer = DurableCheckpoint(owner.snapshot(), owner.protocol())
        owner.submit(command(sequence=2, revision=1), attachment_id=owner.attachment_id)
        old_token = owner.attachment_id
        old_driver = owner._attachment.owner._driver
        receipt = owner.load("slot01")
        assert receipt.revision == 1 and receipt.attachment_id != old_token
        assert DurableCheckpoint(owner.snapshot(), owner.protocol()) == newer
        assert original.exists() and owner.working_path != original
        with pytest.raises(SaveError, match="STALE_ATTACHMENT"):
            owner.submit(command(sequence=2, revision=1), attachment_id=old_token)
        with pytest.raises(WorldUnavailable, match="SESSION_DETACHED"):
            old_driver.submit(command(sequence=2, revision=1))
        first_clone = owner.working_path
        owner.load("slot01")
        assert not first_clone.exists() and original.exists()
        active = owner.working_path
    finally:
        owner.close()
    assert active.exists()
    with resume_durable(active, bundles=(watch_bundle(),)) as resumed:
        assert DurableCheckpoint(resumed.snapshot(), resumed.protocol()) == newer
        resumed.submit(command(sequence=2, revision=1), attachment_id=resumed.attachment_id)
        assert resumed.snapshot().tick == 3


@pytest.mark.parametrize("slot", ["slot00", "slot09", "slot1", "SLOT01", "", "../slot01", " slot01"])
def test_slot_ids_exact(tmp_path: Path, slot: str) -> None:
    with create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        for operation in (owner.export, owner.load):
            with pytest.raises(SaveError, match="INVALID_SLOT"):
                operation(slot)
        assert owner.protocol().revision == 0


@pytest.mark.parametrize("point", ["backup", "flush", "previous_replace", "final_replace", "directory_sync", "after_replace"])
def test_export_fault_matrix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, point: str) -> None:
    from adapters import save_slots
    with create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        owner.export("slot01")
        current = tmp_path / "slots/slot01.sqlite"
        old = file_sha256(current)
        owner.submit(command(WaitCommand(2)), attachment_id=owner.attachment_id)
        core = owner.snapshot()
        if point == "backup":
            def failed_backup(destination: Path) -> None:
                raise OSError("injected backup failure")
            monkeypatch.setattr(owner._attachment.store, "_backup_reserved", failed_backup)
        elif point == "flush":
            def failed_flush(path: Path) -> None:
                raise OSError("injected file flush failure")
            monkeypatch.setattr(save_slots, "sync_file", failed_flush)
        elif point == "directory_sync":
            def failed_directory(path: Path) -> bool:
                raise OSError("injected directory sync failure")
            monkeypatch.setattr(save_slots, "sync_directory", failed_directory)
        else:
            original_replace = os.replace

            def failed_replace(source: Path, destination: Path) -> None:
                selected = destination.name.endswith("previous.sqlite") if point == "previous_replace" else destination.name == "slot01.sqlite"
                if selected:
                    if point == "after_replace":
                        original_replace(source, destination)
                    raise OSError("injected replace failure")
                original_replace(source, destination)

            monkeypatch.setattr(os, "replace", failed_replace)
        expected = "SAVE_EXPORT_UNCERTAIN" if point in ("directory_sync", "after_replace") else "SAVE_EXPORT_FAILED"
        with pytest.raises(SaveError, match=expected):
            owner.export("slot01")
        assert owner.snapshot() == core
        if expected == "SAVE_EXPORT_FAILED":
            assert file_sha256(current) == old
        else:
            assert validate_save(current, io=io()).core == core
        assert not tuple((tmp_path / "slots").glob(".export-*.sqlite"))


@pytest.mark.parametrize("change,code", [("future", "NEWER_SAVE_VERSION"), ("older", "UNSUPPORTED_SAVE_VERSION"), ("legacy", "UNSUPPORTED_LEGACY_SAVE"), ("schema", "SAVE_CORRUPT"), ("pins", "UNSUPPORTED_RULESET")])
def test_version_pin_rejection_keeps_active_world(tmp_path: Path, change: str, code: str) -> None:
    from domain.canonical import canonical_json
    from orchestration.persistence import canonical_object
    with create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        owner.export("slot01")
        slot = tmp_path / "slots/slot01.sqlite"
        con = sqlite3.connect(slot, autocommit=True)
        try:
            if change == "future":
                con.execute("PRAGMA user_version=2")
            elif change == "older":
                con.execute("PRAGMA user_version=0")
            elif change == "legacy":
                con.execute("PRAGMA application_id=0")
            elif change == "schema":
                con.execute("CREATE TABLE unexpected(value TEXT)")
            else:
                from domain.canonical import object_value, hash_document
                raw = con.execute("SELECT body FROM checkpoint").fetchone()[0]
                document = dict(canonical_object(raw))
                core = dict(object_value(document["core"]))
                core["pins"] = {**object_value(core["pins"]), "rules_fingerprint": "1" * 64}
                document["core"] = core
                con.execute("UPDATE checkpoint SET body=?,sha256=?", (canonical_json(document), hash_document("save-checkpoint/v1", document)))
        finally:
            con.close()
        previous, token, sha = owner.snapshot(), owner.attachment_id, file_sha256(slot)
        with pytest.raises(SaveError, match=code):
            owner.load("slot01")
        assert owner.snapshot() == previous and owner.attachment_id == token
        assert file_sha256(slot) == sha
        assert not tuple(tmp_path.glob(".loaded-*.sqlite"))


def test_missing_and_clone_limit(tmp_path: Path) -> None:
    with pytest.raises(SaveError, match="SAVE_NOT_FOUND"):
        resume_durable(tmp_path / "missing.sqlite", bundles=(watch_bundle(),))
    with create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        with pytest.raises(SaveError, match="SAVE_EXISTS"):
            create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),))
        owner.export("slot01")
        for index in range(8):
            (tmp_path / f".loaded-{index:032x}.sqlite").write_bytes(b"unknown leftover")
        with pytest.raises(SaveError, match="SAVE_LIMIT"):
            owner.load("slot01")
        assert len(tuple(tmp_path.glob(".loaded-*.sqlite"))) == 8


def test_link_count_metadata_rejects_alias(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from adapters.sqlite_store import SqliteCommitStore
    owner = create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),))
    owner.close()
    path = tmp_path / "work.sqlite"
    original_stat = Path.stat

    def linked_metadata(target: Path, *, follow_symlinks: bool = True) -> os.stat_result:
        actual = original_stat(target, follow_symlinks=follow_symlinks)
        if target == path:
            fields = list(actual)
            fields[3] = 2
            return os.stat_result(fields, {"st_file_attributes": getattr(actual, "st_file_attributes", 0)})
        return actual

    try:
        # The managed Windows filesystem denies native hardlink creation (WinError5).
        # Exercise the external filesystem metadata guard, without mocking any gameplay.
        with monkeypatch.context() as patched:
            patched.setattr(Path, "stat", linked_metadata)
            with pytest.raises(SaveError, match="INVALID_PATH"):
                SqliteCommitStore.open(path, io=io())
        with resume_durable(tmp_path / "work.sqlite", bundles=(watch_bundle(),)) as reopened:
            assert reopened.snapshot().tick == 0
    finally:
        owner.close()


@pytest.mark.parametrize("point", ["backup", "owner"])
def test_failed_staged_load_keeps_old_attachment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, point: str) -> None:
    from app import durable
    from adapters import save_slots
    from app.headless import _Session
    from adapters.sqlite_store import SqliteCommitStore
    from contracts.skeleton import FeatureBundle
    from contracts.state_io import StateIO
    with create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        owner.export("slot01")
        owner.submit(command(WaitCommand(2)), attachment_id=owner.attachment_id)
        previous, token, path = owner.snapshot(), owner.attachment_id, owner.working_path
        if point == "backup":
            def failed_backup(source: Path, destination: Path, *, io: StateIO) -> None:
                raise OSError("staged backup failed")
            monkeypatch.setattr(save_slots, "_backup_file_reserved", failed_backup)
        else:
            def failed_owner(store: SqliteCommitStore, bundles: tuple[FeatureBundle, ...], selected: StateIO) -> _Session:
                raise RuntimeError("new owner creation failed")
            monkeypatch.setattr(durable, "_owner", failed_owner)
        with pytest.raises(SaveError, match="SAVE_LOAD_FAILED"):
            owner.load("slot01")
        assert owner.snapshot() == previous and owner.attachment_id == token and owner.working_path == path
        assert not tuple(tmp_path.glob(".loaded-*"))
        owner.submit(command(sequence=2, revision=1), attachment_id=token)
        assert owner.snapshot().tick == 3


def test_real_durable_json_cli(tmp_path: Path) -> None:
    from domain.canonical import JsonObject, array_value, canonical_json, decode_json, object_value, text_value
    from tests.unit.watch_fixtures import reference
    path = tmp_path / "cli.sqlite"
    source = "import sys;sys.path.insert(0,sys.argv.pop(1));from app.durable import main;raise SystemExit(main())"
    process = subprocess.Popen([sys.executable, "-c", source, str(ROOT / "src"), "--working", str(path), "--create"],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding="utf-8",
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    timer = Timer(45, process.kill)
    timer.start()

    def receive() -> JsonObject:
        assert process.stdout is not None
        line = process.stdout.readline()
        assert line, "CLI exited before response"
        return object_value(decode_json(line.encode("utf-8")))

    def send(value: JsonObject) -> JsonObject:
        assert process.stdin is not None
        process.stdin.write(canonical_json(value).decode("utf-8") + "\n")
        process.stdin.flush()
        return receive()

    try:
        attached = receive()
        assert attached["kind"] == "attached" and attached["revision"] == 0
        token = text_value(attached["attachment_id"])
        assert send({"kind": "export", "slot_id": "slot01"})["kind"] == "exported"
        expected = array_value(reference("expected_publications"))
        steps = array_value(object_value(requirements()["trace"])["steps"])
        for index, value in enumerate(steps):
            actual = send({"kind": "command", "attachment_id": token, "command": object_value(value)["command"]})
            assert canonical_json(actual) == canonical_json(expected[index])
        loaded = send({"kind": "load", "slot_id": "slot01"})
        assert loaded["kind"] == "loaded"
        new_token = text_value(object_value(loaded["receipt"])["attachment_id"])
        assert new_token != token
        cmd = io().encode_command(command(WaitCommand(16)))
        assert send({"kind": "command", "attachment_id": token, "command": cmd}) == {"kind": "save_error", "code": "STALE_ATTACHMENT"}
        passive = send({"kind": "command", "attachment_id": new_token, "command": cmd})
        assert canonical_json(passive) == canonical_json(array_value(reference("passive_publications"))[0])
        assert send({"kind": "unknown"}) == {"kind": "save_error", "code": "INVALID_REQUEST"}
        assert send({"kind": "recover"}) == {"kind": "save_error", "code": "NO_RECOVERY_PENDING"}
        assert process.stdin is not None
        process.stdin.close()
        assert process.wait(timeout=10) == 0
        active = Path(text_value(loaded["working_path"]))
    finally:
        timer.cancel()
        if process.poll() is None:
            process.kill()
        process.wait(timeout=10)
        for pipe in (process.stdin, process.stdout, process.stderr):
            if pipe is not None:
                pipe.close()
    with resume_durable(active, bundles=(watch_bundle(),)) as resumed:
        assert resumed.snapshot().tick == 16 and resumed.protocol().revision == 1
