from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from adapters.gemini_dialogue import MODEL
from app.npc_dialogue_plan import check_plan, preview_memory
from app.npc_dialogue_review import main, render_review, review_preparation
from app.npc_memory_prepare import prepare_memory
from app.npc_prepare import MAX_PREPARATION_BYTES
from contracts.dialogue import DialogueBrief, GeneratedDialogue, GenerationError, QuestContent
from contracts.npc_memory import NpcMemoryContext
from tests.integration.test_npc_memory import session_at
from tests.unit.quest_fixtures import candidate, catalog, content


def prepared(tmp_path: Path, steps: int = 11) -> tuple[Path, Path, Path]:
    selected = content()
    working, plan, result = (
        tmp_path / "game.sqlite",
        tmp_path / "plan.json",
        tmp_path / "result.json",
    )
    session = session_at(working, steps)
    session.close()
    preview_memory(working, selected, selected.definition.layout.npc_id, plan)

    class Provider:
        def generate(self, brief: DialogueBrief) -> GeneratedDialogue:
            return GeneratedDialogue(candidate(), MODEL, 100, 200, None, 300)

    prepare_memory(
        working,
        selected,
        selected.definition.layout.npc_id,
        result,
        generator=Provider(),
        plan=plan,
    )
    return working, plan, result


@pytest.mark.parametrize(
    "steps,count,phase", ((0, 0, "available"), (9, 1, "accepted"), (11, 2, "reported"))
)
def test_current_candidate_review_keeps_inputs_and_all_conditional_lines(
    tmp_path: Path, steps: int, count: int, phase: str
) -> None:
    working, plan, preparation = prepared(tmp_path, steps)
    selected = content()
    document = json.loads(preparation.read_bytes())
    # Reencoding the envelope is allowed;raw candidate provenance remains exact.
    preparation.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")
    before = tuple(path.read_bytes() for path in (working, plan, preparation))
    review = review_preparation(
        working, selected, selected.definition.layout.npc_id, plan, preparation
    )
    assert review.context.source.known_phase == phase and len(review.context.entries) == count
    assert review.generated.candidate == candidate()
    assert review.preparation_sha256 == hashlib.sha256(before[2]).hexdigest()
    assert (
        review.plan_sha256 == document["plan_sha256"]
        and review.request_sha256 == document["request_sha256"]
    )
    report = render_review(review)
    assert (
        "NEEDS_REVIEW · 승인 전" in report
        and "현재 상황에서 전부 사용하는 대사가 아닙니다" in report
    )
    assert "입력 토큰: 100" in report and "생각 토큰: 미제공" in report
    assert all(
        title in report for title in ("완료 보고 응답", "보고 후 감사", "퀘스트 제안", "진행 확인")
    )
    if count == 0:
        assert "기록된 대화 기억 없음" in report
    if count == 2:
        assert "턴 2: 퀘스트 수락을 관찰" in report and "턴 11: 완료 보고를 받음" in report
    assert tuple(path.read_bytes() for path in (working, plan, preparation)) == before


@pytest.mark.parametrize(
    "damage",
    (
        "context",
        "brief_hash",
        "plan_hash",
        "request_hash",
        "raw_hash",
        "provider",
        "model",
        "boolean_count",
        "negative_count",
        "huge_count",
        "fraction_count",
        "string_count",
        "zero_attempts",
        "three_attempts",
        "boolean_attempts",
        "extra_usage",
        "missing_usage",
        "extra_generation",
        "extra_top",
        "legacy",
        "offline",
        "approved",
        "bad_candidate",
        "order",
        "duplicate_key",
        "invalid_utf8",
        "oversize",
    ),
)
def test_inconsistent_or_malformed_review_is_rejected_without_writes(
    tmp_path: Path, damage: str
) -> None:
    working, plan, preparation = prepared(tmp_path)
    data = json.loads(preparation.read_bytes())
    generation = data["generation"]
    if damage == "context":
        data["context"]["evidence"][0]["observed_at"] = 1
    elif damage in ("brief_hash", "plan_hash", "request_hash"):
        data[damage.replace("_hash", "_sha256")] = "f" * 64
    elif damage == "raw_hash":
        generation["output_sha256"] = "f" * 64
    elif damage in ("provider", "model"):
        generation[damage] = "foreign"
    elif damage.endswith("count"):
        values = {
            "boolean_count": True,
            "negative_count": -1,
            "huge_count": 2**63,
            "fraction_count": 1.5,
            "string_count": "300",
        }
        generation["usage"]["total_tokens"] = values[damage]
    elif damage.endswith("attempts"):
        generation["usage"]["attempts"] = {
            "zero_attempts": 0,
            "three_attempts": 3,
            "boolean_attempts": True,
        }[damage]
    elif damage == "extra_usage":
        generation["usage"]["extra"] = 0
    elif damage == "missing_usage":
        del generation["usage"]["total_tokens"]
    elif damage == "extra_generation":
        generation["extra"] = "unexpected"
    elif damage == "extra_top":
        data["extra"] = "unexpected"
    elif damage == "legacy":
        data["format"] = "reverie-npc-memory-preparation/v1"
        del data["plan_sha256"], data["request_sha256"]
    elif damage == "offline":
        data["generation"], data["status"] = None, "CONTEXT_ONLY"
    elif damage == "approved":
        data["status"] = "APPROVED"
    elif damage in ("bad_candidate", "order"):
        prose = json.loads(generation["candidate_raw"])
        if damage == "bad_candidate":
            prose["npc_id"] = "actor:foreign"
        else:
            prose["lines"].reverse()
        generation["candidate_raw"] = json.dumps(prose, ensure_ascii=False)
        generation["output_sha256"] = hashlib.sha256(
            generation["candidate_raw"].encode()
        ).hexdigest()
    raw = json.dumps(data, ensure_ascii=False).encode()
    if damage == "duplicate_key":
        raw = raw[:-1] + b',"status":"NEEDS_REVIEW"}'
    if damage == "invalid_utf8":
        raw = b"\xff"
    if damage == "oversize":
        raw = b"x" * (MAX_PREPARATION_BYTES + 1)
    preparation.write_bytes(raw)
    before = tuple(path.read_bytes() for path in (working, plan, preparation))
    selected = content()
    with pytest.raises(GenerationError, match="NPC_DIALOGUE_REVIEW_INVALID"):
        review_preparation(working, selected, selected.definition.layout.npc_id, plan, preparation)
    assert tuple(path.read_bytes() for path in (working, plan, preparation)) == before


def test_unknown_usage_and_edited_prose_are_not_claimed_as_authentic_or_approved(
    tmp_path: Path,
) -> None:
    working, plan, preparation = prepared(tmp_path)
    data = json.loads(preparation.read_bytes())
    generation = data["generation"]
    for key in ("prompt_tokens", "output_tokens", "thought_tokens", "total_tokens"):
        generation["usage"][key] = None
    prose = json.loads(generation["candidate_raw"])
    prose["lines"][0]["text_ko"] = "[링크](https://example.invalid) <b>수정한 후보</b> **검토**"
    generation["candidate_raw"] = json.dumps(prose, ensure_ascii=False)
    generation["output_sha256"] = hashlib.sha256(generation["candidate_raw"].encode()).hexdigest()
    preparation.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    selected = content()
    report = render_review(
        review_preparation(working, selected, selected.definition.layout.npc_id, plan, preparation)
    )
    assert "입력 토큰: 미제공" in report and "전체 토큰: 미제공" in report
    assert "NEEDS_REVIEW · 승인 전" in report and "인증하는 서명이 아닙니다" in report
    assert "[링크](" not in report and "<b>" not in report and "**검토**" not in report
    assert "수정한 후보" in report and "&lt;b&gt;" in report


def test_missing_preparation_and_stale_current_game(tmp_path: Path) -> None:
    working, plan, preparation = prepared(tmp_path)
    selected = content()
    npc = selected.definition.layout.npc_id
    with pytest.raises(GenerationError, match="NPC_DIALOGUE_REVIEW_UNAVAILABLE"):
        review_preparation(working, selected, npc, plan, tmp_path / "missing.json")
    session = session_at(working, 0)
    try:
        assert session.act("wait").status == "COMMITTED"
    finally:
        session.close()
    before = tuple(path.read_bytes() for path in (working, plan, preparation))
    with pytest.raises(GenerationError, match="NPC_CONTEXT_STALE"):
        review_preparation(working, selected, npc, plan, preparation)
    assert tuple(path.read_bytes() for path in (working, plan, preparation)) == before


@pytest.mark.parametrize("race", ("source", "plan", "preparation"))
def test_changed_inputs_during_review_are_rechecked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, race: str
) -> None:
    working, plan, preparation = prepared(tmp_path)
    selected = content()
    session = session_at(working, 0)
    calls = 0

    def checking(path: Path, accepted: QuestContent, npc: str, preview: Path) -> NpcMemoryContext:
        nonlocal calls
        calls += 1
        if calls == 2:
            if race == "source":
                assert session.act("wait").status == "COMMITTED"
            elif race == "plan":
                plan.write_bytes(b"{}")
            else:
                preparation.write_bytes(b"{}")
        return check_plan(path, accepted, npc, preview)

    monkeypatch.setattr("app.npc_dialogue_review.check_plan", checking)
    code = (
        "NPC_CONTEXT_STALE"
        if race == "source"
        else "NPC_DIALOGUE_PLAN_INVALID"
        if race == "plan"
        else "NPC_DIALOGUE_REVIEW_INVALID"
    )
    try:
        with pytest.raises(GenerationError, match=code):
            review_preparation(
                working, selected, selected.definition.layout.npc_id, plan, preparation
            )
        if race == "source":
            assert session.owner.snapshot().tick == 12
    finally:
        session.close()


@pytest.mark.parametrize("target", ("output", "pending"))
def test_cli_preserves_occupied_targets_before_reading_missing_inputs(
    tmp_path: Path, target: str, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "review.md"
    occupied = output if target == "output" else output.with_name(output.name + ".pending")
    occupied.write_bytes(b"existing")
    assert (
        main(
            [
                "--working",
                "missing.sqlite",
                "--quest-catalog",
                "missing.json",
                "--quest-sha256",
                "0" * 64,
                "--plan",
                "missing.json",
                "--preparation",
                "missing.json",
                "--output",
                str(output),
            ]
        )
        == 1
    )
    assert occupied.read_bytes() == b"existing"
    assert capsys.readouterr().err.strip() == "GENERATION_TARGET_EXISTS"


def test_standalone_read_only_review_stdout_report_and_invalid_output_with_no_network(
    tmp_path: Path,
) -> None:
    working, plan, preparation = prepared(tmp_path)
    selected = content()
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_bytes(catalog())
    guard = tmp_path / "guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(
        "import sys\ndef guard(event,args):\n if event.startswith('socket.') or event=='urllib.Request': raise RuntimeError('NETWORK_FORBIDDEN')\nsys.addaudithook(guard)\n",
        encoding="utf-8",
    )
    env = dict(os.environ)
    env.pop("GEMINI_API_KEY", None)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = os.pathsep.join(
        (str(guard), str(Path(__file__).resolve().parents[2] / "src"))
    )
    common = [
        sys.executable,
        "-m",
        "app.npc_dialogue_review",
        "--working",
        str(working),
        "--quest-catalog",
        str(catalog_path),
        "--quest-sha256",
        selected.catalog_sha256,
        "--plan",
        str(plan),
        "--preparation",
        str(preparation),
    ]
    before = tuple(path.read_bytes() for path in (working, plan, preparation, catalog_path))
    stdout = subprocess.run(
        common, env=env, capture_output=True, text=True, encoding="utf-8", timeout=30
    )
    assert stdout.returncode == 0 and "완료 보고를 받음" in stdout.stdout
    output = tmp_path / "review.md"
    result = subprocess.run(
        [*common, "--output", str(output)], env=env, capture_output=True, text=True, timeout=30
    )
    assert (
        result.returncode == 0
        and result.stdout.strip() == "DIALOGUE_CANDIDATE_CURRENT_NEEDS_REVIEW"
    )
    assert output.read_text(encoding="utf-8") == stdout.stdout
    assert tuple(path.read_bytes() for path in (working, plan, preparation, catalog_path)) == before
    preparation.write_bytes(b"{}")
    bad_output = tmp_path / "bad.md"
    invalid = subprocess.run(
        [*common, "--output", str(bad_output)], env=env, capture_output=True, text=True, timeout=30
    )
    assert invalid.returncode == 1 and "NPC_DIALOGUE_REVIEW_INVALID" in invalid.stderr
    assert (
        not bad_output.exists() and not bad_output.with_name(bad_output.name + ".pending").exists()
    )


def test_report_publication_failure_cleans_only_owned_pending(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    working, plan, preparation = prepared(tmp_path)
    selected = content()
    catalog_path, output = tmp_path / "catalog.json", tmp_path / "review.md"
    catalog_path.write_bytes(catalog())
    before = tuple(path.read_bytes() for path in (working, plan, preparation, catalog_path))

    def unavailable(fd: int) -> None:
        raise OSError("test report durability failure")

    monkeypatch.setattr("adapters.quest_dialogue.os.fsync", unavailable)
    assert (
        main(
            [
                "--working",
                str(working),
                "--quest-catalog",
                str(catalog_path),
                "--quest-sha256",
                selected.catalog_sha256,
                "--plan",
                str(plan),
                "--preparation",
                str(preparation),
                "--output",
                str(output),
            ]
        )
        == 1
    )
    assert capsys.readouterr().err.strip() == "NPC_DIALOGUE_REVIEW_INPUT"
    assert not output.exists() and not output.with_name(output.name + ".pending").exists()
    assert tuple(path.read_bytes() for path in (working, plan, preparation, catalog_path)) == before
