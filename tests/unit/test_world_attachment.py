"""Current-world references never silently fall back or escape the owned directory."""

from pathlib import Path

import pytest

from adapters.world_attachment import current_world, remember_world
from contracts.persistence import SaveError


def test_default_and_private_world_reference_roundtrip(tmp_path: Path) -> None:
    base = tmp_path / "game.sqlite"
    base.write_bytes(b"original")
    assert current_world(base) == base
    clone = tmp_path / (".loaded-" + "a" * 32 + ".sqlite")
    clone.write_bytes(b"loaded")
    remember_world(base, clone)
    assert current_world(base) == clone
    assert base.read_bytes() == b"original"
    assert not tuple(tmp_path.glob(".world-reference-*"))


@pytest.mark.parametrize("name", ["../other.sqlite", "other.sqlite", ".loaded-bad.sqlite"])
def test_invalid_current_filename_is_rejected(tmp_path: Path, name: str) -> None:
    base = tmp_path / "game.sqlite"
    reference = tmp_path / "game.sqlite.active.json"
    reference.write_text(
        '{"format":"reverie-world-attachment/v1","working_name":"' + name + '"}',
        encoding="utf-8",
    )
    with pytest.raises(SaveError, match="WORLD_ATTACHMENT_INVALID"):
        current_world(base)


def test_missing_referenced_world_does_not_fall_back_to_original(tmp_path: Path) -> None:
    base = tmp_path / "game.sqlite"
    base.write_bytes(b"original")
    clone = tmp_path / (".loaded-" + "a" * 32 + ".sqlite")
    clone.write_bytes(b"loaded")
    remember_world(base, clone)
    clone.unlink()
    with pytest.raises(SaveError, match="WORLD_ATTACHMENT_MISSING"):
        current_world(base)


def test_malformed_reference_is_not_overwritten(tmp_path: Path) -> None:
    base = tmp_path / "game.sqlite"
    reference = tmp_path / "game.sqlite.active.json"
    reference.write_bytes(b"{}")
    with pytest.raises(SaveError, match="WORLD_ATTACHMENT_INVALID"):
        current_world(base)
    assert reference.read_bytes() == b"{}"


def test_current_world_reference_size_limit(tmp_path: Path) -> None:
    base = tmp_path / "game.sqlite"
    base.write_bytes(b"original")
    remember_world(base, base)
    reference = tmp_path / "game.sqlite.active.json"
    body = reference.read_bytes().ljust(1024, b" ")
    reference.write_bytes(body)
    assert current_world(base) == base
    reference.write_bytes(body + b" ")
    with pytest.raises(SaveError, match="^WORLD_ATTACHMENT_INVALID: reference too large$"):
        current_world(base)
