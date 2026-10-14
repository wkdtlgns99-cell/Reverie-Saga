from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from app.client_session import ClientSession
from app.npc_prepare import prepare
from contracts.dialogue import DialogueBrief, GeneratedDialogue, GenerationError
from tests.unit.quest_fixtures import candidate, content


def test_live_boundary_rechecks_source_after_real_commit(tmp_path: Path) -> None:
    selected = content()
    working = tmp_path / "game.sqlite"
    session = ClientSession(working, selected.definition.layout, quest_content=selected)
    output = tmp_path / "candidate.json"

    class MutatingProvider:
        def generate(self, brief: DialogueBrief) -> GeneratedDialogue:
            session.act("down")
            return GeneratedDialogue(candidate(), "offline-test", 100, 150, None, 250)

    try:
        with pytest.raises(GenerationError, match="NPC_CONTEXT_STALE"):
            prepare(
                working,
                selected,
                selected.definition.layout.npc_id,
                output,
                generator=MutatingProvider(),
            )
        assert not output.exists()
        assert session.owner.snapshot().tick == 1  # Real committed truth is not rolled back.
    finally:
        session.close()


@pytest.mark.parametrize(
    "case", ("valid", "unknown_usage", "bad_candidate", "bad_usage", "provider_error")
)
def test_provider_result_and_failure_preserve_source(tmp_path: Path, case: str) -> None:
    selected = content()
    working = tmp_path / "game.sqlite"
    session = ClientSession(working, selected.definition.layout, quest_content=selected)
    session.close()
    before = working.read_bytes()
    output = tmp_path / "result.json"

    class Provider:
        def generate(self, brief: DialogueBrief) -> GeneratedDialogue:
            if case == "provider_error":
                raise GenerationError("GENERATION_DEFERRED")
            result = GeneratedDialogue(candidate(), "offline-test", 100, 150, None, 250)
            if case == "bad_candidate":
                return replace(result, candidate=b"{}")
            if case == "bad_usage":
                return replace(result, total_tokens=True)
            return replace(result, total_tokens=None) if case == "unknown_usage" else result

    if case in ("provider_error", "bad_candidate", "bad_usage"):
        code = "GENERATION_DEFERRED" if case == "provider_error" else "GENERATION_OUTPUT"
        with pytest.raises(GenerationError, match=code):
            prepare(
                working, selected, selected.definition.layout.npc_id, output, generator=Provider()
            )
        assert not output.exists()
    else:
        context = prepare(
            working, selected, selected.definition.layout.npc_id, output, generator=Provider()
        )
        data = json.loads(output.read_bytes())
        assert data["status"] == "NEEDS_REVIEW" and data["context_sha256"] == context.sha256
        assert data["generation"]["candidate_raw"].encode() == candidate()
        assert data["generation"]["usage"]["total_tokens"] == (
            None if case == "unknown_usage" else 250
        )
    assert working.read_bytes() == before


@pytest.mark.parametrize("target", ("output", "pending"))
def test_existing_target_never_calls_provider_or_reads_missing_source(
    tmp_path: Path, target: str
) -> None:
    selected = content()
    output = tmp_path / "approved.json"
    existing = output if target == "output" else output.with_name(output.name + ".pending")
    existing.write_bytes(b"existing-approved-bytes")

    class Provider:
        def generate(self, brief: DialogueBrief) -> GeneratedDialogue:
            raise AssertionError("provider must not run")

    with pytest.raises(GenerationError, match="GENERATION_TARGET_EXISTS"):
        prepare(
            tmp_path / "missing.sqlite",
            selected,
            selected.definition.layout.npc_id,
            output,
            generator=Provider(),
        )
    assert existing.read_bytes() == b"existing-approved-bytes"
