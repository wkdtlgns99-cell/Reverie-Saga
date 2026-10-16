from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.client_session import ClientSession
from app.npc_prepare import context_brief, read_context
from contracts.persistence import SaveError
from contracts.dialogue import GenerationError
from domain.canonical import canonical_json
from tests.integration.test_quest import GOAL
from tests.unit.quest_fixtures import catalog, content


@pytest.mark.parametrize(
    "stage,actions,phase,favor",
    (
        (0, 0, "available", 0),
        (1, 2, "accepted", 0),
        (2, 9, "accepted", 0),
        (3, 11, "reported", 1),
    ),
)
def test_real_committed_context_has_only_npc_known_facts(
    tmp_path: Path, stage: int, actions: int, phase: str, favor: int
) -> None:
    selected = content()
    working = tmp_path / "game.sqlite"
    session = ClientSession(working, selected.definition.layout, quest_content=selected)
    try:
        for action in (*GOAL, "left", "talk")[:actions]:
            assert session.act(action).status == "COMMITTED"
        assert session.update().quest_stage == stage
        before = session.owner.snapshot(), session.owner.protocol(), working.read_bytes()
        result = read_context(working, selected, selected.definition.layout.npc_id)
        assert (result.known_phase, result.recorded_favor) == (phase, favor)
        text = canonical_json(result.document()).decode()
        for excluded in (
            "enemy_hp",
            "actor_hp",
            "world_seed",
            "working_path",
            "attachment_id",
            selected.definition.layout.enemy_id,
            str(working),
        ):
            assert excluded not in text
        assert "defeat" not in text
        assert len(context_brief(result).text.encode()) <= 4096
        assert (session.owner.snapshot(), session.owner.protocol(), working.read_bytes()) == before
    finally:
        session.close()


def test_retry_load_preserves_saved_context_then_private_branch_diverges(tmp_path: Path) -> None:
    selected = content()
    npc_id = selected.definition.layout.npc_id
    session = ClientSession(
        tmp_path / "game.sqlite", selected.definition.layout, quest_content=selected
    )
    try:
        for action in GOAL:
            session.act(action)
        session.save("slot01")
        original = read_context(session.owner.working_path, selected, npc_id)
        session.retry()
        assert read_context(session.owner.working_path, selected, npc_id) == original
        session.load("slot01")
        branch = read_context(session.owner.working_path, selected, npc_id)
        assert branch.known_phase == original.known_phase == "accepted"
        # Load preserves saved protocol identity;the attachment/working file is a private copy.
        assert branch == original
        assert session.owner.working_path != tmp_path / "game.sqlite"
        session.act("left")
        branch = read_context(session.owner.working_path, selected, npc_id)
        assert branch.sha256 != original.sha256
        assert read_context(tmp_path / "game.sqlite", selected, npc_id) == original
        path = session.owner.working_path
    finally:
        session.close()
    resumed = read_context(path, selected, npc_id)
    assert resumed == branch


def test_wrong_owner_missing_legacy_and_corrupt_source_reject(tmp_path: Path) -> None:
    selected = content()
    npc_id = selected.definition.layout.npc_id
    missing = tmp_path / "missing.sqlite"
    with pytest.raises(GenerationError, match="NPC_CONTEXT_OWNER"):
        read_context(missing, selected, "actor:foreign")
    assert not missing.exists()
    legacy = ClientSession(tmp_path / "legacy.sqlite")
    legacy.close()
    with pytest.raises(SaveError, match="UNSUPPORTED"):
        read_context(tmp_path / "legacy.sqlite", selected, npc_id)
    corrupt = tmp_path / "corrupt.sqlite"
    corrupt.write_bytes(b"corrupt")
    with pytest.raises(SaveError, match="SAVE_CORRUPT"):
        read_context(corrupt, selected, npc_id)
    assert corrupt.read_bytes() == b"corrupt"


def test_standalone_offline_cli_is_read_only_and_network_forbidden(tmp_path: Path) -> None:
    selected = content()
    working = tmp_path / "game.sqlite"
    session = ClientSession(working, selected.definition.layout, quest_content=selected)
    session.act("down")
    session.act("talk")
    session.close()
    approved = tmp_path / "test-only-catalog.json"
    approved.write_bytes(catalog())
    digest = hashlib.sha256(approved.read_bytes()).hexdigest()
    guard = tmp_path / "audit"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(
        "import sys\n"
        "def guard(event,args):\n"
        " if event.startswith('socket.') or event=='urllib.Request': raise RuntimeError('NETWORK_FORBIDDEN')\n"
        "sys.addaudithook(guard)\n",
        encoding="utf-8",
    )
    root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(guard), str(root / "src")))
    output = tmp_path / "context.json"
    before = working.read_bytes()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.npc_prepare",
            "--working",
            str(working),
            "--quest-catalog",
            str(approved),
            "--quest-sha256",
            digest,
            "--output",
            str(output),
        ],
        env=env,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0 and "CONTEXT_ONLY " in result.stdout
    data = json.loads(output.read_bytes())
    assert data["status"] == "CONTEXT_ONLY" and data["generation"] is None
    assert data["context"]["known_phase"] == "accepted"
    assert working.read_bytes() == before
