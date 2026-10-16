from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.npc_memory_check import check_snapshot
from app.npc_memory_export import MAX_EXPORT_BYTES, export_memory
from app.npc_memory_query import EvidenceQuery
from contracts.dialogue import GenerationError
from tests.integration.test_npc_memory import session_at
from tests.unit.quest_fixtures import catalog, content


def test_current_reencoded_snapshot_and_stale_after_real_commit(tmp_path: Path) -> None:
    selected = content()
    working, snapshot = tmp_path / "game.sqlite", tmp_path / "query.json"
    session = session_at(working, 11)
    try:
        context = export_memory(
            working, selected, selected.definition.layout.npc_id, EvidenceQuery(), snapshot
        )
        snapshot.write_text(
            json.dumps(json.loads(snapshot.read_bytes()), indent=2), encoding="utf-8"
        )
        before = working.read_bytes(), snapshot.read_bytes()
        assert (
            check_snapshot(working, selected, selected.definition.layout.npc_id, snapshot)
            == context
        )
        assert (working.read_bytes(), snapshot.read_bytes()) == before
        assert session.act("wait").status == "COMMITTED"
        with pytest.raises(GenerationError, match="NPC_CONTEXT_STALE"):
            check_snapshot(working, selected, selected.definition.layout.npc_id, snapshot)
        assert snapshot.read_bytes() == before[1]
    finally:
        session.close()


@pytest.mark.parametrize(
    "damage", ("count", "evidence", "query", "source", "status", "extra", "malformed", "oversize")
)
def test_modified_or_invalid_snapshot_is_rejected_without_writes(
    tmp_path: Path, damage: str
) -> None:
    selected = content()
    working, snapshot = tmp_path / "game.sqlite", tmp_path / "query.json"
    session = session_at(working, 11)
    session.close()
    export_memory(working, selected, selected.definition.layout.npc_id, EvidenceQuery(), snapshot)
    document = json.loads(snapshot.read_bytes())
    if damage == "count":
        document["count"] = True
    elif damage == "evidence":
        document["evidence"][0]["observed_at"] = 10
    elif damage == "query":
        document["query"]["kind"] = "accepted"
    elif damage == "source":
        document["source"]["tick"] = 10
    elif damage == "status":
        document["status"] = "APPROVED"
    elif damage == "extra":
        document["extra"] = "unrecognized"
    raw = (
        b"bad-json"
        if damage == "malformed"
        else b"x" * (MAX_EXPORT_BYTES + 1)
        if damage == "oversize"
        else json.dumps(document).encode()
    )
    snapshot.write_bytes(raw)
    before = working.read_bytes(), snapshot.read_bytes()
    with pytest.raises(GenerationError, match="NPC_MEMORY_SNAPSHOT_INVALID"):
        check_snapshot(working, selected, selected.definition.layout.npc_id, snapshot)
    assert (working.read_bytes(), snapshot.read_bytes()) == before


def test_missing_snapshot_is_unavailable_without_creating_files(tmp_path: Path) -> None:
    with pytest.raises(GenerationError, match="NPC_MEMORY_SNAPSHOT_UNAVAILABLE"):
        check_snapshot(
            tmp_path / "missing.sqlite",
            content(),
            content().definition.layout.npc_id,
            tmp_path / "missing.json",
        )
    assert list(tmp_path.iterdir()) == []


def test_standalone_checker_is_offline_and_read_only(tmp_path: Path) -> None:
    selected = content()
    working, snapshot = tmp_path / "game.sqlite", tmp_path / "query.json"
    session = session_at(working, 11)
    session.close()
    export_memory(
        working,
        selected,
        selected.definition.layout.npc_id,
        EvidenceQuery(kind="accepted"),
        snapshot,
    )
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_bytes(catalog())
    guard = tmp_path / "guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(
        "import sys\ndef guard(event,args):\n if event.startswith('socket.') or event=='urllib.Request': raise RuntimeError('NETWORK_FORBIDDEN')\nsys.addaudithook(guard)\n",
        encoding="utf-8",
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        (str(guard), str(Path(__file__).resolve().parents[2] / "src"))
    )
    before = working.read_bytes(), snapshot.read_bytes()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.npc_memory_check",
            "--working",
            str(working),
            "--quest-catalog",
            str(catalog_path),
            "--quest-sha256",
            selected.catalog_sha256,
            "--snapshot",
            str(snapshot),
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0 and "MEMORY_QUERY_CURRENT" in result.stdout
    assert (working.read_bytes(), snapshot.read_bytes()) == before
