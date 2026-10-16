from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from adapters.sqlite_store import validate_save
from app.client_session import ClientSession
from app.headless import state_io
from app.npc_memory import memory_bundle
from app.quest_registry import quest_bundle
from app.save_inventory import MAX_CANDIDATES, inspect_clones, main
from app.scenarios import select_scenario
from app.watch_registry import watch_bundle
from contracts.persistence import SaveError
from domain.canonical import array_value, canonical_json, object_value
from tests.unit.quest_fixtures import catalog, content


def tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()
    }


def clone_name(number: int) -> str:
    return f".loaded-{number:032x}.sqlite"


def test_retained_loads_show_saved_progress_without_cleanup(tmp_path: Path) -> None:
    working = tmp_path / "game.sqlite"
    owner = ClientSession(working)
    owner.owner.export("slot01")
    owner.close()
    retained: dict[str, int] = {}
    for steps in (1, 2, 3):
        owner = ClientSession(working)
        owner.owner.load("slot01")
        for _ in range(steps):
            assert owner.act("wait").status == "COMMITTED"
        retained[owner.owner.working_path.name] = steps
        owner.close()
    io = state_io((watch_bundle(),))
    before = tree_bytes(tmp_path)
    document = inspect_clones(working, io=io)
    rows = [object_value(row) for row in array_value(document["clones"])]
    assert document["format"] == "reverie-save-clone-inventory/v1"
    assert document["status"] == "READ_ONLY_SNAPSHOT"
    assert object_value(document["current"])["tick"] == 0
    assert [row["filename"] for row in rows] == sorted(retained)
    assert all(row["status"] == "VALID" and row["is_current"] is False for row in rows)
    assert {row["filename"]: row["tick"] for row in rows} == retained
    assert all(row["revision"] == row["tick"] for row in rows)
    assert str(tmp_path).encode() not in canonical_json(document)
    assert tree_bytes(tmp_path) == before
    for filename, tick in retained.items():
        resumed = ClientSession(tmp_path / filename)
        try:
            assert resumed.owner.snapshot().tick == tick
            current = inspect_clones(resumed.owner.working_path, io=io)
            active = [
                object_value(row)
                for row in array_value(current["clones"])
                if object_value(row)["is_current"]
            ]
            assert len(active) == 1 and active[0]["filename"] == filename
        finally:
            resumed.close()


def test_inventory_does_not_bypass_eight_clone_cap(tmp_path: Path) -> None:
    working = tmp_path / "game.sqlite"
    with ClientSession(working).owner as owner:
        owner.export("slot01")
    for _ in range(8):
        with ClientSession(working).owner as owner:
            owner.load("slot01")
    with ClientSession(working).owner as owner:
        before = tree_bytes(tmp_path)
        document = inspect_clones(working, io=state_io((watch_bundle(),)))
        assert len(array_value(document["clones"])) == 8
        assert tree_bytes(tmp_path) == before
        with pytest.raises(SaveError) as caught:
            owner.load("slot01")
        assert caught.value.code == "SAVE_LIMIT"


def test_empty_inventory_ignores_slots_sidecars_and_lookalikes(tmp_path: Path) -> None:
    working = tmp_path / "game.sqlite"
    owner = ClientSession(working)
    owner.owner.export("slot01")
    owner.close()
    for name in (
        ".loaded-not-a-token.sqlite",
        ".loaded-" + "A" * 32 + ".sqlite",
        clone_name(0) + ".lock.sqlite",
    ):
        (tmp_path / name).write_bytes(b"untouched")
    before = tree_bytes(tmp_path)
    assert inspect_clones(working, io=state_io((watch_bundle(),)))["clones"] == ()
    assert tree_bytes(tmp_path) == before


def test_corrupt_incompatible_and_directory_candidates_are_visible(tmp_path: Path) -> None:
    working = tmp_path / "game.sqlite"
    ClientSession(working).close()
    (tmp_path / clone_name(0)).write_bytes(b"broken")
    (tmp_path / clone_name(1)).mkdir()
    foreign = tmp_path / clone_name(2)
    ClientSession(foreign, select_scenario("harbor").layout).close()
    shutil.copyfile(working, tmp_path / clone_name(3))
    before = tree_bytes(tmp_path)
    rows = array_value(inspect_clones(working, io=state_io((watch_bundle(),)))["clones"])
    statuses = [object_value(row)["status"] for row in rows]
    assert statuses == ["SAVE_CORRUPT", "INVALID_PATH", "UNSUPPORTED_RULESET", "VALID"]
    assert all(object_value(row)["tick"] is None for row in rows[:3])
    assert tree_bytes(tmp_path) == before


def test_candidate_disappearing_after_scan_is_a_diagnostic_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    working = tmp_path / "game.sqlite"
    ClientSession(working).close()
    other = tmp_path / clone_name(1)
    shutil.copyfile(working, other)

    def read(path: Path, **kwargs: object) -> object:
        if path == other:
            other.unlink()
        return validate_save(path, io=state_io((watch_bundle(),)))

    monkeypatch.setattr("app.save_inventory.validate_save", read)
    row = object_value(
        array_value(inspect_clones(working, io=state_io((watch_bundle(),)))["clones"])[0]
    )
    assert row["status"] == "SAVE_NOT_FOUND" and row["tick"] is None
    assert not other.exists()


def test_inventory_limit_and_invalid_current_do_not_create_files(tmp_path: Path) -> None:
    working = tmp_path / "game.sqlite"
    io = state_io((watch_bundle(),))
    with pytest.raises(SaveError):
        inspect_clones(working, io=io)
    assert not list(tmp_path.iterdir())
    ClientSession(working).close()
    for number in range(MAX_CANDIDATES + 1):
        (tmp_path / clone_name(number)).write_bytes(b"untouched")
    before = tree_bytes(tmp_path)
    with pytest.raises(SaveError) as caught:
        inspect_clones(working, io=io)
    assert caught.value.code == "SAVE_LIMIT"
    assert tree_bytes(tmp_path) == before


def test_hardlinked_candidate_is_rejected_without_touching_source(tmp_path: Path) -> None:
    working = tmp_path / "game.sqlite"
    ClientSession(working).close()
    other = tmp_path / clone_name(1)
    os.link(working, other)
    # Current must remain a distinct valid file;the alias belongs to an unrelated source.
    current = tmp_path / "current.sqlite"
    shutil.copyfile(working, current)
    before = tree_bytes(tmp_path)
    rows = array_value(inspect_clones(current, io=state_io((watch_bundle(),)))["clones"])
    assert object_value(rows[0])["status"] == "INVALID_PATH"
    assert tree_bytes(tmp_path) == before


def test_scan_failure_is_sanitized_and_does_not_create_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    working = tmp_path / "game.sqlite"
    ClientSession(working).close()
    before = tree_bytes(tmp_path)

    def denied(path: Path) -> object:
        raise PermissionError("private directory detail")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "iterdir", denied)
        assert main(["--working", str(working)]) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.strip() == "SAVE_INVENTORY_UNAVAILABLE"
    assert tree_bytes(tmp_path) == before


@pytest.mark.parametrize("mode", ("legacy", "harbor", "grove", "quest", "memory"))
def test_standalone_cli_original_modes_and_immutable_sources(tmp_path: Path, mode: str) -> None:
    working = tmp_path / "game.sqlite"
    args = ["--working", str(working)]
    if mode in ("quest", "memory"):
        selected = content()
        catalog_path = tmp_path / "catalog.json"
        catalog_path.write_bytes(catalog())
        args += ["--quest-catalog", str(catalog_path), "--quest-sha256", selected.catalog_sha256]
        if mode == "memory":
            args += ["--npc-memory"]
        owner = ClientSession(
            working, selected.definition.layout, quest_content=selected, npc_memory=mode == "memory"
        )
        io = state_io((memory_bundle(selected) if mode == "memory" else quest_bundle(selected),))
    else:
        layout = select_scenario(mode).layout
        args += ["--scenario", mode]
        owner = ClientSession(working, layout)
        io = state_io((watch_bundle(layout),))
    owner.owner.export("slot01")
    owner.owner.load("slot01")
    owner.close()
    before = tree_bytes(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "app.save_inventory", *args],
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == json.loads(canonical_json(inspect_clones(working, io=io)))
    assert tree_bytes(tmp_path) == before


@pytest.mark.parametrize(
    "args",
    (
        ("--npc-memory",),
        ("--quest-catalog", "missing"),
        ("--quest-catalog", "missing", "--quest-sha256", "0" * 64, "--scenario", "harbor"),
    ),
)
def test_cli_invalid_modes_fail_before_access(tmp_path: Path, args: tuple[str, ...]) -> None:
    with pytest.raises(SystemExit) as caught:
        main(["--working", str(tmp_path / "missing.sqlite"), *args])
    assert caught.value.code == 2
    assert not list(tmp_path.iterdir())


def test_cli_missing_current_and_process_control(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    args = ["--working", str(tmp_path / "missing.sqlite")]
    assert main(args) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.strip() == "SAVE_NOT_FOUND"

    def interrupted(*args: object, **kwargs: object) -> object:
        raise KeyboardInterrupt

    monkeypatch.setattr("app.save_inventory.inspect_clones", interrupted)
    with pytest.raises(KeyboardInterrupt):
        main(args)
