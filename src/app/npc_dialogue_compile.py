"""Bind explicit approval to reviewed memory input before publishing a fresh catalog."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
from typing import Sequence

from adapters.quest_dialogue import compile_dialogue, decode_catalog, load_dialogue, publish_fresh
from app.npc_dialogue_review import DialogueReview, review_preparation
from app.npc_memory_brief import memory_brief
from app.npc_prepare import _target_available
from app.quest_definition import harbor_definition
from contracts.dialogue import ARTIFACT_ID, MAX_DIALOGUE_BYTES, GenerationError, QuestContent
from contracts.persistence import SaveError
from domain.canonical import canonical_json, decode_json, object_value


def _brief_hash(review: DialogueReview) -> str:
    return hashlib.sha256(memory_brief(review.context).text.encode("utf-8")).hexdigest()


def _read_receipt(path: Path) -> bytes:
    try:
        with path.open("rb") as source:
            raw = source.read(MAX_DIALOGUE_BYTES + 1)
    except OSError:
        raise GenerationError("NPC_DIALOGUE_APPROVAL_UNAVAILABLE") from None
    if not 1 <= len(raw) <= MAX_DIALOGUE_BYTES:
        raise GenerationError("NPC_DIALOGUE_APPROVAL_INVALID")
    return raw


def _compile(
    review: DialogueReview, receipt: bytes, content: QuestContent
) -> tuple[bytes, QuestContent]:
    try:
        compiled = compile_dialogue(review.generated.candidate, receipt)
        if object_value(decode_json(receipt))["brief_sha256"] != _brief_hash(review):
            raise ValueError("brief binding")
        selected = decode_catalog(
            compiled, hashlib.sha256(compiled).hexdigest(), content.definition
        )
    except (ValueError, UnicodeError, RecursionError):
        raise GenerationError("NPC_DIALOGUE_APPROVAL_INVALID") from None
    return compiled, selected


def draft_approval(
    working: Path, content: QuestContent, npc_id: str, plan: Path, preparation: Path, output: Path
) -> None:
    _target_available(output)
    review = review_preparation(working, content, npc_id, plan, preparation)
    body = canonical_json(
        {
            "artifact_id": ARTIFACT_ID,
            "output_sha256": hashlib.sha256(review.generated.candidate).hexdigest(),
            "brief_sha256": _brief_hash(review),
            "decision": "PENDING",
            "approved_by": "",
            "approved_utc": "",
        }
    )
    if review_preparation(working, content, npc_id, plan, preparation) != review:
        raise GenerationError("NPC_DIALOGUE_INPUT_CHANGED")
    publish_fresh(output, body)


def compile_preparation(
    working: Path,
    content: QuestContent,
    npc_id: str,
    plan: Path,
    preparation: Path,
    receipt: Path,
    output: Path,
) -> QuestContent:
    _target_available(output)
    review = review_preparation(working, content, npc_id, plan, preparation)
    raw = _read_receipt(receipt)
    compiled, selected = _compile(review, raw, content)
    if review_preparation(working, content, npc_id, plan, preparation) != review:
        raise GenerationError("NPC_DIALOGUE_INPUT_CHANGED")
    if _read_receipt(receipt) != raw:
        raise GenerationError("NPC_DIALOGUE_APPROVAL_CHANGED")
    publish_fresh(output, compiled)
    return selected


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile explicitly approved memory dialogue")
    parser.add_argument("--working", type=Path, required=True)
    parser.add_argument("--quest-catalog", type=Path, required=True)
    parser.add_argument("--quest-sha256", required=True)
    parser.add_argument("--npc-id", default=harbor_definition().layout.npc_id)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--draft-approval", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.draft_approval == (args.receipt is not None):
            raise GenerationError("GENERATION_INPUT")
        _target_available(args.output)
        content = load_dialogue(args.quest_catalog, args.quest_sha256, harbor_definition())
        if args.draft_approval:
            draft_approval(
                args.working, content, args.npc_id, args.plan, args.preparation, args.output
            )
            print("DIALOGUE_APPROVAL_DRAFT_PENDING")
        else:
            # Mode validation above establishes receipt presence without using an assert.
            if args.receipt is None:
                raise GenerationError("GENERATION_INPUT")
            selected = compile_preparation(
                args.working,
                content,
                args.npc_id,
                args.plan,
                args.preparation,
                args.receipt,
                args.output,
            )
            print("COMPILED_APPROVED_DIALOGUE " + selected.catalog_sha256)
    except (ValueError, OSError, UnicodeError, RecursionError, SaveError) as error:
        code = (
            error.code
            if isinstance(error, (GenerationError, SaveError))
            else "NPC_DIALOGUE_COMPILE_INPUT"
        )
        print(code, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
