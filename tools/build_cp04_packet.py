"""Build a self-contained repair snapshot;never rewrite an earlier review witness."""

from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


def session_entry(request: str) -> bytes:
    return f"""# START HERE — Reverie Saga Independent Review

Assume a new session with no prior conversation. This is a review snapshot,not an instruction
to execute project work orders. Project:deterministic Python Brain with a provisional Unity/Tk
client. The exact checkpoint,scope,authority and evidence are in [{request}]({request}).

## Message to paste

```text
Please independently review the attached Reverie Saga snapshot. Start with START_REVIEW.md,
then {request},and follow its contract/evidence/source/test references. SESSION_HANDOFF.md
and BACKLOG.md are background only. Inspect actual code and callers rather than accepting
test counts as proof. Report defects with severity,file/line,reproduction and expected vs
actual behavior. Separate confirmed defects,extension risks and scope exclusions. State
which files and commands you inspected or ran,and which checks were not run and why.
Do not implement fixes,advance tasks or infer acceptance of unimplemented capabilities.
```

## Read order

1. {request}:current review scope,focused questions and limits.
2. Its linked concrete work order/contracts and execution receipt,including failed attempts.
3. ENGINEERING_RULES.md and the applicable MASTER/engineering contracts linked by that order.
4. Actual source,registered callers,tests,fixtures and requirements-dev.lock identified there.
5. README.md verification and docs/WORKSTATION_SETUP.md for the reviewer's own environment.
6. SESSION_HANDOFF.md/BACKLOG.md only to clarify dependencies and historical context.

The input witness names/hashes all included files and this generated entry. Old witnesses
describe historical snapshots. Do not mix their test counts or bytes with this packet.
The repository does not transfer a Python environment,editor,login,license or private saves.
Return findings and execution limits even when native tools are unavailable;never claim an
unexecuted test or infer that a passed test proves rights,UX or release qualification.
""".encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--witness", type=Path, required=True)
    parser.add_argument(
        "--request", type=Path, default=Path("docs/reviews/RS-REVIEW-CP04_REQUEST.md")
    )
    args = parser.parse_args()
    root = args.root.resolve()
    archive = (root / args.archive).resolve()
    witness = (root / args.witness).resolve()
    request = (root / args.request).resolve()
    for output in (archive, witness):
        if not output.is_relative_to(root):
            raise ValueError("Packet output must stay in repository")
        if output.exists():
            raise ValueError("Packet output already exists;choose a new snapshot: " + str(output))
    if archive == witness:
        raise ValueError("Packet outputs must be distinct")
    if not request.is_relative_to(root) or not request.is_file() or request.suffix != ".md":
        raise ValueError("Missing packet request")
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
    if request not in files:
        raise ValueError("Missing packet request from source inventory")
    if root / "START_REVIEW.md" in files:
        raise ValueError("START_REVIEW.md is reserved for the generated review entry")
    request_name = request.relative_to(root).as_posix()
    opening = session_entry(request_name)
    rows = [
        {
            "path": p.relative_to(root).as_posix(),
            "bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
        for p in files
    ]
    rows.append(
        {
            "path": "START_REVIEW.md",
            "bytes": len(opening),
            "sha256": hashlib.sha256(opening).hexdigest(),
            "generated": True,
        }
    )
    document = {
        "format": "review-repair-witness/v1",
        "baseline_head": subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip(),
        "entry_point": "START_REVIEW.md",
        "request": request_name,
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
        packed.writestr("START_REVIEW.md", opening)
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
