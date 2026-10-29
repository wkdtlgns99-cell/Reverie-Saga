"""SQLite's binary header can legally contain Windows text control bytes."""

from pathlib import Path
import sqlite3

import pytest

from adapters.sqlite_store import SqliteCommitStore, classify_file, validate_save
from contracts.persistence import SaveError
from tests.unit.durability_fixtures import checkpoint, io


@pytest.mark.parametrize("cookie", (26, 0x0D0A, 0x1A000001))
def test_binary_header_controls_preserve_real_checkpoint(tmp_path: Path, cookie: int) -> None:
    path = tmp_path / "game.sqlite"
    selected, expected = io(), checkpoint()
    store = SqliteCommitStore.create(path, expected, io=selected)
    store.close()
    con = sqlite3.connect(path, autocommit=True)
    try:
        # SQLite itself writes a valid binary schema cookie;application version stays1.
        con.execute(f"PRAGMA schema_version={cookie}")
        assert con.execute("PRAGMA schema_version").fetchone() == (cookie,)
    finally:
        con.close()
    before = path.read_bytes()
    assert before[40:44] == cookie.to_bytes(4, "big")
    assert b"\x1a" in before[:100] or b"\r\n" in before[:100]
    assert validate_save(path, io=selected) == expected
    reopened = SqliteCommitStore.open(path, io=selected)
    try:
        assert reopened.load() == expected
    finally:
        reopened.close()
    assert path.read_bytes() == before


@pytest.mark.parametrize("body", (b"SQLite format 3\0", b"invalid" + bytes(93)))
def test_binary_header_still_rejects_truncated_or_wrong_signature(
    tmp_path: Path, body: bytes
) -> None:
    path = tmp_path / "bad.sqlite"
    path.write_bytes(body)
    with pytest.raises(SaveError) as caught:
        classify_file(path)
    assert caught.value.code == "SAVE_CORRUPT"
    assert path.read_bytes() == body
