"""Explicit read-only inspection of retained working-save clones;never cleanup."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import re
import sys

from adapters.quest_dialogue import load_dialogue
from adapters.sqlite_store import safe_path, validate_save
from app.headless import state_io
from app.npc_memory import memory_bundle
from app.quest_definition import harbor_definition
from app.quest_registry import quest_bundle
from app.scenarios import SCENARIOS, select_scenario
from app.watch_registry import watch_bundle
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.state_io import StateIO
from domain.canonical import JsonObject, canonical_json, object_value, seal

MAX_CANDIDATES = 64


def _metadata(path: Path, checkpoint: DurableCheckpoint) -> JsonObject:
    return {
        "filename": path.name,
        "tick": checkpoint.core.tick,
        "revision": checkpoint.protocol.revision,
        "branch_id": checkpoint.protocol.branch_id,
    }


def inspect_clones(working: Path, *, io: StateIO) -> JsonObject:
    current = safe_path(working)
    checkpoint = validate_save(current, io=io)
    paths: list[Path] = []
    try:
        for path in current.parent.iterdir():
            if re.fullmatch(r"\.loaded-[0-9a-f]{32}\.sqlite", path.name):
                paths.append(path)
                if len(paths) > MAX_CANDIDATES:
                    raise SaveError("SAVE_LIMIT", "inventory candidate count")
    except OSError:
        raise SaveError("SAVE_INVENTORY_UNAVAILABLE", "cannot enumerate save directory") from None
    rows: list[JsonObject] = []
    for path in sorted(paths):
        try:
            data = _metadata(path, validate_save(path, io=io))
            status = "VALID"
        except SaveError as error:
            data = {"filename": path.name, "tick": None, "revision": None, "branch_id": None}
            status = error.code
        rows.append({**data, "is_current": path == current, "status": status})
    return object_value(
        seal(
            {
                "format": "reverie-save-clone-inventory/v1",
                "status": "READ_ONLY_SNAPSHOT",
                "current": _metadata(current, checkpoint),
                "clones": tuple(rows),
            }
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List retained working saves without modifying them"
    )
    parser.add_argument("--working", type=Path, required=True)
    parser.add_argument(
        "--scenario", choices=tuple(choice.key for choice in SCENARIOS), default="legacy"
    )
    parser.add_argument("--quest-catalog", type=Path)
    parser.add_argument("--quest-sha256")
    parser.add_argument("--npc-memory", action="store_true")
    args = parser.parse_args(argv)
    if (args.quest_catalog is None) != (args.quest_sha256 is None):
        parser.error("quest catalog and hash must be supplied together")
    if args.npc_memory and args.quest_catalog is None:
        parser.error("NPC memory requires the original quest catalog and hash")
    if args.quest_catalog is not None and args.scenario != "legacy":
        parser.error("quest content supplies its own scenario")
    try:
        if args.quest_catalog is None:
            bundles = (watch_bundle(select_scenario(args.scenario).layout),)
        else:
            content = load_dialogue(args.quest_catalog, args.quest_sha256, harbor_definition())
            bundles = (memory_bundle(content) if args.npc_memory else quest_bundle(content),)
        document = inspect_clones(args.working, io=state_io(bundles))
        sys.stdout.buffer.write(canonical_json(document) + b"\n")
        sys.stdout.buffer.flush()
    except (SaveError, ValueError, OSError, UnicodeError, RecursionError) as error:
        code = error.code if isinstance(error, SaveError) else "SAVE_INVENTORY_UNAVAILABLE"
        print(code, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
