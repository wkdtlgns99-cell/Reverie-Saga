from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.npc_memory_prepare import prepare_memory
from contracts.dialogue import DialogueBrief, GeneratedDialogue, GenerationError
from tests.integration.test_npc_memory import session_at
from tests.unit.quest_fixtures import candidate, content


@pytest.mark.parametrize("case", ("valid", "unknown", "bad_candidate", "failure"))
def test_generation_boundary_preserves_persisted_memory(tmp_path: Path, case: str) -> None:
    selected = content()
    working = tmp_path / "game.sqlite"
    session = session_at(working, 11)
    session.close()
    before = working.read_bytes()
    output = tmp_path / "preparation.json"

    class Provider:
        def generate(self, brief: DialogueBrief) -> GeneratedDialogue:
            assert (
                '"kind":"accepted"' in brief.text and '"kind":"completion_reported"' in brief.text
            )
            assert '"certainty":"reported"' in brief.text
            assert selected.definition.layout.enemy_id not in brief.text
            if case == "failure":
                raise GenerationError("GENERATION_TIMEOUT")
            return GeneratedDialogue(
                b"{}" if case == "bad_candidate" else candidate(),
                "offline-test",
                100,
                200,
                None,
                None if case == "unknown" else 300,
            )

    if case in ("failure", "bad_candidate"):
        code = "GENERATION_TIMEOUT" if case == "failure" else "GENERATION_OUTPUT"
        with pytest.raises(GenerationError, match=code):
            prepare_memory(
                working, selected, selected.definition.layout.npc_id, output, generator=Provider()
            )
        assert not output.exists()
    else:
        context = prepare_memory(
            working, selected, selected.definition.layout.npc_id, output, generator=Provider()
        )
        envelope = json.loads(output.read_bytes())
        assert envelope["context_sha256"] == context.sha256
        assert envelope["status"] == "NEEDS_REVIEW"
        assert envelope["generation"]["candidate_raw"].encode() == candidate()
    assert working.read_bytes() == before


def test_changed_source_after_generation_rejects_stale_memory(tmp_path: Path) -> None:
    selected = content()
    working = tmp_path / "game.sqlite"
    session = session_at(working, 0)
    output = tmp_path / "candidate.json"

    class Provider:
        def generate(self, brief: DialogueBrief) -> GeneratedDialogue:
            session.act("down")
            return GeneratedDialogue(candidate(), "offline-test", 100, 200, None, 300)

    try:
        with pytest.raises(GenerationError, match="NPC_CONTEXT_STALE"):
            prepare_memory(
                working, selected, selected.definition.layout.npc_id, output, generator=Provider()
            )
        assert not output.exists() and session.owner.snapshot().tick == 1
    finally:
        session.close()


@pytest.mark.parametrize("target", ("output", "pending"))
def test_existing_artifact_rejects_before_source_or_provider(tmp_path: Path, target: str) -> None:
    selected = content()
    output = tmp_path / "result.json"
    existing = output if target == "output" else output.with_name(output.name + ".pending")
    existing.write_bytes(b"existing")

    class Provider:
        def generate(self, brief: DialogueBrief) -> GeneratedDialogue:
            raise AssertionError("provider must not run")

    with pytest.raises(GenerationError, match="GENERATION_TARGET_EXISTS"):
        prepare_memory(
            tmp_path / "missing.sqlite",
            selected,
            selected.definition.layout.npc_id,
            output,
            generator=Provider(),
        )
    assert existing.read_bytes() == b"existing"
