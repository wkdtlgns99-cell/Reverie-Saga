from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def build(archive: Path, witness: Path, request: str) -> subprocess.CompletedProcess[str]:
    environment = {
        **os.environ,
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "safe.directory",
        "GIT_CONFIG_VALUE_0": str(ROOT),
    }
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/build_cp04_packet.py"),
            "--root",
            str(ROOT),
            "--archive",
            str(archive),
            "--witness",
            str(witness),
            "--request",
            request,
        ],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_new_session_entry_is_request_specific_and_hashed(tmp_path: Path) -> None:
    import zipfile

    archive, witness = tmp_path / "packet.zip", tmp_path / "inputs.json"
    request = "docs/reviews/RS-REVIEW-CP03_REQUEST.md"
    result = build(archive, witness, request)
    assert result.returncode == 0, result.stdout + result.stderr
    document = json.loads(witness.read_bytes())
    with zipfile.ZipFile(archive) as packed:
        opening = packed.read("START_REVIEW.md")
        assert request.encode() in opening
        assert b"Message to paste" in opening and b"Read order" in opening
        assert b"no prior conversation" in opening
        assert b"file/line" in opening and b"not run" in opening
        row = next(item for item in document["files"] if item["path"] == "START_REVIEW.md")
        assert row["bytes"] == len(opening)
        assert row["sha256"] == hashlib.sha256(opening).hexdigest()
        assert document["entry_point"] == "START_REVIEW.md"
        assert document["request"] == request
        assert len(packed.namelist()) == len(set(packed.namelist()))


def test_existing_review_output_is_preserved(tmp_path: Path) -> None:
    archive, witness = tmp_path / "packet.zip", tmp_path / "inputs.json"
    archive.write_bytes(b"previously delivered packet")
    result = build(archive, witness, "docs/reviews/RS-REVIEW-CP03_REQUEST.md")
    assert result.returncode != 0
    assert "already exists" in result.stderr
    assert archive.read_bytes() == b"previously delivered packet"
    assert not witness.exists()


def test_missing_request_rejects_without_publishing_packet(tmp_path: Path) -> None:
    archive, witness = tmp_path / "packet.zip", tmp_path / "inputs.json"
    result = build(archive, witness, "docs/reviews/MISSING_REQUEST.md")
    assert result.returncode != 0
    assert "Missing packet request" in result.stderr
    assert not archive.exists() and not witness.exists()
