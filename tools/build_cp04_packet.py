"""Build a self-contained repair snapshot;never rewrite an earlier review witness."""

from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--witness", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    archive = (root / args.archive).resolve()
    witness = (root / args.witness).resolve()
    for output in (archive, witness):
        if not output.is_relative_to(root):
            raise ValueError("Packet output must stay in repository")
    names = subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard"],
        text=True,
    ).splitlines()
    files = sorted(
        {
            root / name
            for name in names
            if (root / name).is_file()
            and (root / name).suffix != ".zip"
            and (root / name).resolve() not in (archive, witness)
            and not name.endswith("CP04_REPAIRED_2026-10-12_SHA256.json")
        }
    )
    required = [
        "requirements-dev.lock",
        "docs/ENGINEERING_ENFORCEMENT.md",
        "tests/replay/fixtures/encounter_v1.json",
        "tests/replay/fixtures/skeleton_v1.json",
        "docs/work_orders/PHASE0_REFERENCE_VECTORS.json",
    ]
    for name in required:
        if root / name not in files:
            raise ValueError("Missing packet prerequisite: " + name)
    rows = [
        {
            "path": p.relative_to(root).as_posix(),
            "bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
        for p in files
    ]
    document = {
        "format": "review-repair-witness/v1",
        "baseline_head": subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip(),
        "scope": "Current source plus all tracked fixtures/vectors/locks/docs;old witnesses are historical context",
        "excluded": "Git internals,private saves/account/logs/caches/venv and nested archives",
        "prerequisites": "CPython3.13.12 Windows x64 with stdlib tkinter;20locked packages including import-linter;Unity needed only for separate native checks",
        "files": rows,
    }
    witness.parent.mkdir(parents=True, exist_ok=True)
    witness.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as packed:
        for p in files + [witness]:
            packed.write(p, p.relative_to(root).as_posix())
    print(
        json.dumps(
            {
                "files": len(rows) + 1,
                "witness_sha256": hashlib.sha256(witness.read_bytes()).hexdigest(),
                "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            }
        )
    )


if __name__ == "__main__":
    main()
