from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.npc_dialogue_plan import MAX_PLAN_BYTES, check_plan, preview_memory
from app.npc_memory import read_memory
from app.npc_memory_prepare import main, memory_brief
from contracts.dialogue import GenerationError, QuestContent
from contracts.npc_memory import NpcMemoryContext
from tests.integration.test_npc_memory import session_at
from tests.unit.quest_fixtures import catalog, content


@pytest.mark.parametrize("steps,count", ((0, 0), (9, 1), (11, 2)))
def test_real_preview_and_current_plan_are_read_only(
    tmp_path: Path, steps: int, count: int
) -> None:
    selected = content()
    working, plan = tmp_path / "game.sqlite", tmp_path / "plan.json"
    session = session_at(working, steps)
    session.close()
    before = working.read_bytes()
    context = preview_memory(working, selected, selected.definition.layout.npc_id, plan)
    document = json.loads(plan.read_bytes())
    assert document["status"] == "PREVIEW" and document["model"] == "gemini-3.5-flash-lite"
    assert len(document["context"]["evidence"]) == count
    assert document["brief_text"] == memory_brief(context).text
    assert document["brief_sha256"] == hashlib.sha256(document["brief_text"].encode()).hexdigest()
    assert str(working) not in document["brief_text"]
    plan.write_text(json.dumps(document, indent=2), encoding="utf-8")
    plan_before = plan.read_bytes()
    assert check_plan(working, selected, selected.definition.layout.npc_id, plan) == context
    assert working.read_bytes() == before and plan.read_bytes() == plan_before


@pytest.mark.parametrize(
    "damage", ("brief", "model", "request", "evidence", "status", "extra", "bad_json", "oversize")
)
def test_tampered_plan_rejects_even_with_self_consistent_brief_hash(
    tmp_path: Path, damage: str
) -> None:
    selected = content()
    working, plan = tmp_path / "game.sqlite", tmp_path / "plan.json"
    session = session_at(working, 11)
    session.close()
    preview_memory(working, selected, selected.definition.layout.npc_id, plan)
    document = json.loads(plan.read_bytes())
    if damage == "brief":
        document["brief_text"] += " Invent an extra reward."
        document["brief_sha256"] = hashlib.sha256(document["brief_text"].encode()).hexdigest()
    elif damage == "model":
        document["model"] = "foreign-model"
    elif damage == "request":
        document["request_sha256"] = "f" * 64
    elif damage == "evidence":
        document["context"]["evidence"][0]["observed_at"] = 1
    elif damage == "status":
        document["status"] = "APPROVED"
    elif damage == "extra":
        document["extra"] = "unexpected"
    raw = (
        b"bad"
        if damage == "bad_json"
        else b"x" * (MAX_PLAN_BYTES + 1)
        if damage == "oversize"
        else json.dumps(document).encode()
    )
    plan.write_bytes(raw)
    before = working.read_bytes(), plan.read_bytes()
    with pytest.raises(GenerationError, match="NPC_DIALOGUE_PLAN_INVALID"):
        check_plan(working, selected, selected.definition.layout.npc_id, plan)
    assert (working.read_bytes(), plan.read_bytes()) == before


def test_stale_plan_missing_file_and_configuration_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selected = content()
    working, plan = tmp_path / "game.sqlite", tmp_path / "plan.json"
    session = session_at(working, 11)
    try:
        preview_memory(working, selected, selected.definition.layout.npc_id, plan)
        with monkeypatch.context() as scoped:
            scoped.setattr("app.npc_dialogue_plan.MODEL", "changed-local-model")
            with pytest.raises(GenerationError, match="NPC_DIALOGUE_PLAN_INVALID"):
                check_plan(working, selected, selected.definition.layout.npc_id, plan)
        assert session.act("wait").status == "COMMITTED"
        with pytest.raises(GenerationError, match="NPC_CONTEXT_STALE"):
            check_plan(working, selected, selected.definition.layout.npc_id, plan)
        with pytest.raises(GenerationError, match="NPC_DIALOGUE_PLAN_UNAVAILABLE"):
            check_plan(
                working, selected, selected.definition.layout.npc_id, tmp_path / "missing.json"
            )
    finally:
        session.close()


def test_preview_source_race_preserves_actual_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selected = content()
    working, output = tmp_path / "game.sqlite", tmp_path / "plan.json"
    session = session_at(working, 11)
    calls = 0

    def reading(path: Path, accepted: QuestContent, owner: str) -> NpcMemoryContext:
        nonlocal calls
        result = read_memory(path, accepted, owner)
        calls += 1
        if calls == 1:
            session.act("wait")
        return result

    monkeypatch.setattr("app.npc_dialogue_plan.read_memory", reading)
    try:
        with pytest.raises(GenerationError, match="NPC_CONTEXT_STALE"):
            preview_memory(working, selected, selected.definition.layout.npc_id, output)
        assert not output.exists() and session.owner.snapshot().tick == 12
    finally:
        session.close()


def test_standalone_preview_then_offline_plan_consumption_has_no_network(tmp_path: Path) -> None:
    selected = content()
    working = tmp_path / "game.sqlite"
    session = session_at(working, 11)
    session.close()
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
    env["PYTHONPATH"] = os.pathsep.join(
        (str(guard), str(Path(__file__).resolve().parents[2] / "src"))
    )
    common = [
        sys.executable,
        "-m",
        "app.npc_memory_prepare",
        "--working",
        str(working),
        "--quest-catalog",
        str(catalog_path),
        "--quest-sha256",
        selected.catalog_sha256,
    ]
    plan, output = tmp_path / "plan.json", tmp_path / "dry-run.json"
    before = working.read_bytes()
    preview = subprocess.run(
        [*common, "--preview", "--output", str(plan)],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert preview.returncode == 0 and "DIALOGUE_PLAN_PREVIEW" in preview.stdout
    result = subprocess.run(
        [*common, "--plan", str(plan), "--output", str(output)],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    document = json.loads(output.read_bytes())
    assert result.returncode == 0 and document["status"] == "CONTEXT_ONLY"
    assert (
        document["format"] == "reverie-npc-memory-preparation/v2" and document["generation"] is None
    )
    assert working.read_bytes() == before


def test_invalid_plan_cli_rejects_before_key_or_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    selected = content()
    working, plan = tmp_path / "game.sqlite", tmp_path / "plan.json"
    session = session_at(working, 0)
    session.close()
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_bytes(catalog())
    plan.write_bytes(b"{}")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    output = tmp_path / "candidate.json"
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
                "--live",
                "--output",
                str(output),
            ]
        )
        == 1
    )
    assert "NPC_DIALOGUE_PLAN_INVALID" in capsys.readouterr().err and not output.exists()


@pytest.mark.parametrize(
    "flags", (("--preview", "--live"), ("--preview", "--plan", "missing.json"))
)
def test_preview_mode_conflicts_fail_before_source(tmp_path: Path, flags: tuple[str, ...]) -> None:
    output = tmp_path / "output.json"
    assert (
        main(
            [
                "--working",
                "missing.sqlite",
                "--quest-catalog",
                "missing.json",
                "--quest-sha256",
                "0" * 64,
                "--output",
                str(output),
                *flags,
            ]
        )
        == 1
    )
    assert not output.exists()
