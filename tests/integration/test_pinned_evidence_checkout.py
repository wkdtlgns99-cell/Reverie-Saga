from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess

import pytest

from app.engine_project import build_sample
from domain.canonical import array_value, decode_json, object_value, text_value

PATHS = (
    "docs/reference/QUILLTALE_CONTENT_CANDIDATES.json",
    "docs/reviews/QT-F04_GENERATION_EVIDENCE_2026-10-12.json",
)


@pytest.mark.parametrize("autocrlf", ("false", "true", "input"))
def test_git_checkout_preserves_qualified_bytes_and_compiler_output(
    tmp_path: Path, autocrlf: str
) -> None:
    root = Path(__file__).resolve().parents[2]
    qualification = object_value(decode_json((root / PATHS[1]).read_bytes()))
    manifest = object_value(decode_json((root / "content/narratives.manifest.json").read_bytes()))
    pins = {
        text_value(object_value(row)["qualification_evidence_sha256"])
        for row in array_value(manifest["entries"])
    }
    assert len(pins) == 1
    expected = (text_value(qualification["candidate_dossier_sha256"]), pins.pop())
    checkout = tmp_path / "checkout"
    subprocess.run(
        [
            "git",
            "-c",
            f"core.autocrlf={autocrlf}",
            "-c",
            "core.eol=lf",
            "-c",
            f"core.attributesfile={os.devnull}",
            "checkout-index",
            "--prefix=" + checkout.as_posix() + "/",
            "--",
            *PATHS,
        ],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for name, digest in zip(PATHS, expected, strict=True):
        assert hashlib.sha256((checkout / name).read_bytes()).hexdigest() == digest
    body, compiled_manifest = build_sample(checkout)
    assert body == (root / "content/narratives.json").read_bytes()
    assert compiled_manifest == (root / "content/narratives.manifest.json").read_bytes()


def test_compiler_still_rejects_unqualified_lf_bytes(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    for name in PATHS:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / name).read_bytes().replace(b"\r\n", b"\n"))
    with pytest.raises(ValueError, match="^NARRATIVE_DOSSIER_UNQUALIFIED$"):
        build_sample(tmp_path)


@pytest.mark.parametrize("autocrlf", ("false", "true", "input"))
def test_git_checkout_preserves_reviewed_g07_source_bytes(tmp_path: Path, autocrlf: str) -> None:
    root = Path(__file__).resolve().parents[2]
    inventory = object_value(decode_json((root / "tools/replay_body_inventory.json").read_bytes()))
    sources = object_value(inventory["source_sha256"])
    assert len(sources) == 8
    checkout = tmp_path / "checkout"
    subprocess.run(
        [
            "git",
            "-c",
            f"core.autocrlf={autocrlf}",
            "-c",
            "core.eol=lf",
            "-c",
            f"core.attributesfile={os.devnull}",
            "checkout-index",
            "--prefix=" + checkout.as_posix() + "/",
            "--",
            *sources,
        ],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for name, digest in sources.items():
        body = (checkout / name).read_bytes()
        assert hashlib.sha256(body).hexdigest() == text_value(digest), name
