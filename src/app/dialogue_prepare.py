"""Explicit preparation CLI:generate candidate,approve externally,compile,then play offline."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import sys
from typing import Sequence

from adapters.gemini_dialogue import GeminiDialogue
from adapters.generation_budget import GenerationBudget
from adapters.quest_dialogue import compile_dialogue, decode_candidate, publish_fresh
from contracts.dialogue import ARTIFACT_ID, DialogueBrief, GenerationError, MAX_DIALOGUE_BYTES
from domain.canonical import canonical_json, seal


def harbor_brief() -> DialogueBrief:
    return DialogueBrief(
        "Write four short Korean NPC dialogue lines as JSON,not game rules. Location:소금눈물 포구. "
        "NPC:actor:harbor-watcher,quest:quest:harbor-sentinel. The NPC guards the harbor path. "
        "The internal game determines every fact. Generate all four branches in lexical intent order: "
        "completion,gratitude,offer,reminder. offer requests defeating the path-blocking enemy and "
        "returning to report;promises exactly one recorded harbor favor. reminder asks for the report "
        "but never claims victory or a grant. completion acknowledges defeat/report and exactly one "
        "favor already recorded. gratitude acknowledges the past favor,never another reward. "
        "No money,items,extra quest,private knowledge,markup or variable placeholders. Use format "
        "reverie-quest-dialogue-candidate/v1,quest_id,npc_id,lines(intent,text_ko) only."
    )


def _read(path: Path) -> bytes:
    with path.open("rb") as source:
        data = source.read(MAX_DIALOGUE_BYTES + 1)
    if len(data) > MAX_DIALOGUE_BYTES:
        raise GenerationError("GENERATION_INPUT")
    return data


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare and validate quest dialogue outside gameplay"
    )
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--free-tier-confirmed", action="store_true")
    parser.add_argument(
        "--free-data-use-confirmed",
        action="store_true",
        help="Acknowledge Google's unpaid-service use of submitted brief/output",
    )
    parser.add_argument("--profile", type=Path, default=Path("tmp/gemini-profile"))
    args = parser.parse_args(argv)
    try:
        if args.live:
            if args.candidate is not None or args.receipt is not None or args.output is None:
                raise GenerationError("GENERATION_INPUT")
            # Never overwrite an existing target,including its provenance sidecar.
            metadata_path = args.output.with_suffix(args.output.suffix + ".metadata.json")
            if args.output.exists() or metadata_path.exists():
                raise GenerationError("GENERATION_TARGET_EXISTS")
            generated = GeminiDialogue(
                os.environ.get("GEMINI_API_KEY", ""),
                GenerationBudget(args.profile),
                free_tier_confirmed=args.free_tier_confirmed,
                free_data_use_confirmed=args.free_data_use_confirmed,
            ).generate(harbor_brief())
            metadata = {
                "artifact_id": ARTIFACT_ID,
                "provider": "gemini",
                "model": generated.model,
                "brief_sha256": hashlib.sha256(harbor_brief().text.encode()).hexdigest(),
                "output_sha256": hashlib.sha256(generated.candidate).hexdigest(),
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "validation_status": "VALIDATED",
                "approval_status": "NEEDS_REVIEW",
                "usage": {
                    key: value
                    for key, value in asdict(generated).items()
                    if key not in ("candidate", "model")
                },
            }
            publish_fresh(metadata_path, canonical_json(seal(metadata)))
            try:
                publish_fresh(args.output, generated.candidate)
            except BaseException:
                metadata_path.unlink()
                raise
            print("GENERATED_NEEDS_REVIEW " + hashlib.sha256(generated.candidate).hexdigest())
        elif args.candidate is not None:
            candidate = _read(args.candidate)
            decode_candidate(candidate)
            if args.receipt is not None:
                if args.output is None:
                    raise GenerationError("GENERATION_INPUT")
                compiled = compile_dialogue(candidate, _read(args.receipt))
                publish_fresh(args.output, compiled)
                print("COMPILED " + hashlib.sha256(compiled).hexdigest())
            elif args.output is None:
                print("VALIDATED_NEEDS_REVIEW " + hashlib.sha256(candidate).hexdigest())
            else:
                raise GenerationError("GENERATION_INPUT")
        else:
            raise GenerationError("GENERATION_INPUT")
    except (ValueError, OSError, UnicodeError, RecursionError) as error:
        code = error.code if isinstance(error, GenerationError) else "GENERATION_INPUT"
        print(code, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
