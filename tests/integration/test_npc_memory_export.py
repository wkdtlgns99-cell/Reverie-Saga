from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.npc_memory import read_memory
from app.npc_memory_export import export_memory, main
from app.npc_memory_query import EvidenceQuery
from contracts.dialogue import GenerationError, QuestContent
from contracts.npc_memory import NpcMemoryContext
from tests.integration.test_npc_memory import session_at
from tests.unit.quest_fixtures import catalog, content


@pytest.mark.parametrize(
    "flags,kinds",
    (
        ((), ["completion_reported", "accepted"]),
        (("--kind", "accepted"), ["accepted"]),
        (("--since", "12"), []),
        (("--limit", "0"), []),
    ),
)
def test_standalone_export_has_no_network_and_preserves_save(
    tmp_path: Path, flags: tuple[str, ...], kinds: list[str]
) -> None:
    selected = content()
    working = tmp_path / "game.sqlite"
    session = session_at(working, 11)
    session.close()
    before = working.read_bytes()
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_bytes(catalog())
    guard = tmp_path / "guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(
        "import sys\ndef guard(event,args):\n"
        " if event.startswith('socket.') or event=='urllib.Request': raise RuntimeError('NETWORK_FORBIDDEN')\n"
        "sys.addaudithook(guard)\n",
        encoding="utf-8",
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        (str(guard), str(Path(__file__).resolve().parents[2] / "src"))
    )
    output = tmp_path / "query.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.npc_memory_export",
            "--working",
            str(working),
            "--quest-catalog",
            str(catalog_path),
            "--quest-sha256",
            selected.catalog_sha256,
            "--output",
            str(output),
            *flags,
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0 and "MEMORY_QUERY_SNAPSHOT" in result.stdout
    document = json.loads(output.read_bytes())
    assert document["status"] == "SNAPSHOT" and document["count"] == len(kinds)
    assert [entry["kind"] for entry in document["evidence"]] == kinds
    assert (
        document["context_sha256"]
        == read_memory(working, selected, selected.definition.layout.npc_id).sha256
    )
    assert working.read_bytes() == before


@pytest.mark.parametrize(
    "flag,value", (("--limit", "3"), ("--since", "-1"), ("--subject-id", "item:bad"))
)
def test_invalid_query_does_not_create_source_or_output(
    tmp_path: Path, flag: str, value: str
) -> None:
    output, missing = tmp_path / "result.json", tmp_path / "missing.sqlite"
    assert (
        main(
            [
                "--working",
                str(missing),
                "--quest-catalog",
                "missing.json",
                "--quest-sha256",
                "0" * 64,
                "--output",
                str(output),
                flag,
                value,
            ]
        )
        == 1
    )
    assert not output.exists() and not missing.exists()


@pytest.mark.parametrize("target", ("output", "pending"))
def test_existing_artifact_is_preserved_before_missing_source(tmp_path: Path, target: str) -> None:
    output = tmp_path / "query.json"
    existing = output if target == "output" else output.with_name(output.name + ".pending")
    existing.write_bytes(b"existing")
    with pytest.raises(GenerationError, match="GENERATION_TARGET_EXISTS"):
        export_memory(
            tmp_path / "missing.sqlite",
            content(),
            content().definition.layout.npc_id,
            EvidenceQuery(),
            output,
        )
    assert existing.read_bytes() == b"existing"


def test_source_changed_during_export_rejects_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selected = content()
    working = tmp_path / "game.sqlite"
    session = session_at(working, 11)
    calls = 0

    def read_then_commit(path: Path, accepted: QuestContent, owner: str) -> NpcMemoryContext:
        nonlocal calls
        context = read_memory(path, accepted, owner)
        calls += 1
        if calls == 1:
            assert session.act("wait").status == "COMMITTED"
        return context

    monkeypatch.setattr("app.npc_memory_export.read_memory", read_then_commit)
    output = tmp_path / "query.json"
    try:
        with pytest.raises(GenerationError, match="NPC_CONTEXT_STALE"):
            export_memory(
                working, selected, selected.definition.layout.npc_id, EvidenceQuery(), output
            )
        assert not output.exists() and session.owner.snapshot().tick == 12
    finally:
        session.close()
