from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.npc_dialogue_plan import plan_document, preview_memory
from app.npc_memory_prepare import prepare_memory
from adapters.gemini_dialogue import GeminiDialogue
from adapters.generation_budget import GenerationBudget
from contracts.dialogue import DialogueBrief, GeneratedDialogue, GenerationError
from domain.canonical import JsonObject, array_value, canonical_json, object_value
from tests.adapters.test_gemini_dialogue import response
from tests.integration.test_npc_memory import session_at
from tests.unit.quest_fixtures import candidate, content


def test_actual_gemini_adapter_sends_previewed_request(tmp_path: Path) -> None:
    selected = content()
    working, plan, output = (
        tmp_path / "game.sqlite",
        tmp_path / "plan.json",
        tmp_path / "result.json",
    )
    session = session_at(working, 11)
    session.close()
    preview_memory(working, selected, selected.definition.layout.npc_id, plan)
    document = json.loads(plan.read_bytes())
    requests: list[JsonObject] = []

    def send(request: JsonObject, key: str) -> JsonObject:
        assert key == "offline-test-key"
        requests.append(request)
        assert hashlib.sha256(canonical_json(request)).hexdigest() == document["request_sha256"]
        message = object_value(array_value(request["contents"])[0])
        assert object_value(array_value(message["parts"])[0])["text"] == document["brief_text"]
        return response()

    generator = GeminiDialogue(
        "offline-test-key",
        GenerationBudget(tmp_path / "profile"),
        free_tier_confirmed=True,
        free_data_use_confirmed=True,
        send=send,
    )
    before = working.read_bytes(), plan.read_bytes()
    prepare_memory(
        working, selected, selected.definition.layout.npc_id, output, generator=generator, plan=plan
    )
    assert len(requests) == 1 and (working.read_bytes(), plan.read_bytes()) == before


@pytest.mark.parametrize(
    "case",
    (
        "valid",
        "stale_before",
        "edited_before",
        "source_after",
        "plan_after",
        "failure",
        "bad_output",
    ),
)
def test_plan_driven_generation_calls_exact_brief_and_preserves_truth(
    tmp_path: Path, case: str
) -> None:
    selected = content()
    working, plan, output = (
        tmp_path / "game.sqlite",
        tmp_path / "plan.json",
        tmp_path / "result.json",
    )
    session = session_at(working, 11)
    calls = []
    try:
        context = preview_memory(working, selected, selected.definition.layout.npc_id, plan)
        original = json.loads(plan.read_bytes())
        if case == "stale_before":
            session.act("wait")
        if case == "edited_before":
            modified = dict(original)
            modified["brief_text"] += " More rewards."
            plan.write_text(json.dumps(modified), encoding="utf-8")
        before = working.read_bytes(), plan.read_bytes()

        class Provider:
            def generate(self, brief: DialogueBrief) -> GeneratedDialogue:
                calls.append(brief.text)
                assert brief.text == original["brief_text"]
                if case == "source_after":
                    session.act("wait")
                if case == "plan_after":
                    modified = dict(original)
                    modified["model"] = "changed"
                    plan.write_text(json.dumps(modified), encoding="utf-8")
                if case == "failure":
                    raise GenerationError("GENERATION_TIMEOUT")
                return GeneratedDialogue(
                    b"{}" if case == "bad_output" else candidate(),
                    "offline-test",
                    100,
                    200,
                    None,
                    300,
                )

        if case == "valid":
            assert (
                prepare_memory(
                    working,
                    selected,
                    selected.definition.layout.npc_id,
                    output,
                    generator=Provider(),
                    plan=plan,
                )
                == context
            )
            result = json.loads(output.read_bytes())
            assert result["format"] == "reverie-npc-memory-preparation/v2"
            assert (
                result["status"] == "NEEDS_REVIEW"
                and result["generation"]["candidate_raw"].encode() == candidate()
            )
            assert (
                result["plan_sha256"]
                == hashlib.sha256(canonical_json(plan_document(context))).hexdigest()
            )
            assert result["request_sha256"] == original["request_sha256"]
        else:
            code = (
                "NPC_CONTEXT_STALE"
                if case in ("stale_before", "source_after")
                else "NPC_DIALOGUE_PLAN_INVALID"
                if case in ("edited_before", "plan_after")
                else "GENERATION_TIMEOUT"
                if case == "failure"
                else "GENERATION_OUTPUT"
            )
            with pytest.raises(GenerationError, match=code):
                prepare_memory(
                    working,
                    selected,
                    selected.definition.layout.npc_id,
                    output,
                    generator=Provider(),
                    plan=plan,
                )
            assert not output.exists()
        assert len(calls) == (0 if case in ("stale_before", "edited_before") else 1)
        if case != "source_after":
            assert working.read_bytes() == before[0]
        else:
            assert session.owner.snapshot().tick == 12
        if case != "plan_after":
            assert plan.read_bytes() == before[1]
    finally:
        session.close()


@pytest.mark.parametrize("target", ("output", "pending"))
def test_occupied_output_prevents_plan_read_or_generation(tmp_path: Path, target: str) -> None:
    selected = content()
    output = tmp_path / "result.json"
    existing = output if target == "output" else output.with_name(output.name + ".pending")
    existing.write_bytes(b"existing")

    class Provider:
        def generate(self, brief: DialogueBrief) -> GeneratedDialogue:
            raise AssertionError("no call")

    with pytest.raises(GenerationError, match="GENERATION_TARGET_EXISTS"):
        prepare_memory(
            tmp_path / "missing.sqlite",
            selected,
            selected.definition.layout.npc_id,
            output,
            generator=Provider(),
            plan=tmp_path / "missing.json",
        )
    assert existing.read_bytes() == b"existing"
