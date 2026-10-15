from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import cast

import pytest

from app.client_session import ClientSession
from app.npc_memory import read_memory
from app.npc_memory_compare import comparison_document, export_comparison, main
from contracts.dialogue import GenerationError, QuestContent
from contracts.npc_memory import NpcMemoryContext
from contracts.persistence import SaveError
from domain.canonical import canonical_json
from tests.integration.test_npc_memory import session_at
from tests.integration.test_quest import GOAL
from tests.unit.quest_fixtures import catalog, content


def snapshots(tmp_path: Path, steps: int = 2) -> tuple[Path, Path]:
    working, previous = tmp_path / "current.sqlite", tmp_path / "previous.sqlite"
    owner = session_at(working, steps)
    owner.close()
    shutil.copyfile(working, previous)
    selected = content()
    owner = ClientSession(
        working, selected.definition.layout, quest_content=selected, npc_memory=True
    )
    try:
        for action in (*GOAL, "left", "talk")[steps:]:
            assert owner.act(action).status == "COMMITTED"
    finally:
        owner.close()
    return previous, working


@pytest.mark.parametrize("steps,retained", ((0, 0), (2, 1)))
def test_real_snapshots_report_exact_ids_and_preserve_both_saves(
    tmp_path: Path, steps: int, retained: int
) -> None:
    before, after = snapshots(tmp_path, steps)
    originals = before.read_bytes(), after.read_bytes()
    selected = content()
    output = tmp_path / "comparison.json"
    old, new = export_comparison(before, after, selected, selected.definition.layout.npc_id, output)
    document = json.loads(output.read_bytes())
    npc = selected.definition.layout.npc_id
    assert document["format"] == "reverie-npc-memory-comparison/v1"
    assert document["status"] == "SNAPSHOT_COMPARISON"
    assert document["added"] == [
        entry.memory_id(npc) for entry in reversed(new.entries[steps // 2 :])
    ]
    assert document["removed"] == []
    assert document["retained"] == [entry.memory_id(npc) for entry in reversed(old.entries)]
    assert len(document["retained"]) == retained
    assert document["before"]["source"]["tick"] == steps
    assert document["after"]["source"]["tick"] == 11
    assert document["before"]["context_sha256"] == old.sha256
    assert document["after"]["context_sha256"] == new.sha256
    assert [e["certainty"] for e in document["after"]["evidence"]] == ["reported", "observed"]
    assert selected.definition.layout.enemy_id.encode() not in output.read_bytes()
    assert str(tmp_path).encode() not in output.read_bytes()
    assert (before.read_bytes(), after.read_bytes()) == originals
    assert output.read_bytes() == canonical_json(comparison_document(old, new))


def test_reverse_wait_and_identical_snapshots_are_not_forgetting(tmp_path: Path) -> None:
    before, after = snapshots(tmp_path)
    selected = content()
    npc = selected.definition.layout.npc_id
    old, new = read_memory(before, selected, npc), read_memory(after, selected, npc)
    reverse = comparison_document(new, old)
    assert reverse["added"] == ()
    assert reverse["removed"] == (new.entries[1].memory_id(npc),)
    assert reverse["retained"] == (new.entries[0].memory_id(npc),)
    owner = ClientSession(
        after, selected.definition.layout, quest_content=selected, npc_memory=True
    )
    try:
        assert owner.act("wait").status == "COMMITTED"
    finally:
        owner.close()
    waited = read_memory(after, selected, npc)
    assert waited.source.core_hash != new.source.core_hash
    for other in (new, waited):
        document = comparison_document(new, other)
        assert document["added"] == document["removed"] == ()
        assert document["retained"] == tuple(e.memory_id(npc) for e in reversed(new.entries))


def test_real_older_load_preserves_saved_branch_identity_without_mutation(tmp_path: Path) -> None:
    selected = content()
    owner = session_at(tmp_path / "current.sqlite", 2)
    original_path = owner.owner.working_path
    try:
        assert owner.save("slot01").status == "SAVED"
        for action in (*GOAL, "left", "talk")[2:]:
            assert owner.act(action).status == "COMMITTED"
        assert owner.load("slot01").status == "LOADED"
        loaded_path = owner.owner.working_path
        assert loaded_path != original_path
        before = original_path.read_bytes(), loaded_path.read_bytes()
        old, new = export_comparison(
            original_path,
            loaded_path,
            selected,
            selected.definition.layout.npc_id,
            tmp_path / "branches.json",
        )
        # Load changes the working attachment,path and revision,not the saved branch ID.
        assert old.source.branch_id == new.source.branch_id == "0" * 32
        assert (old.source.tick, new.source.tick) == (11, 2)
        assert comparison_document(old, new)["removed"] == (
            old.entries[1].memory_id(old.source.npc_id),
        )
        assert (original_path.read_bytes(), loaded_path.read_bytes()) == before
        fork_projection = replace(new, source=replace(new.source, branch_id="1" * 32))
        assert comparison_document(old, fork_projection)["removed"] == (
            old.entries[1].memory_id(old.source.npc_id),
        )
    finally:
        owner.close()


@pytest.mark.parametrize("field", ("world_id", "catalog_sha256", "npc_id", "actor_id", "quest_id"))
def test_foreign_source_cannot_be_compared(tmp_path: Path, field: str) -> None:
    selected = content()
    owner = session_at(tmp_path / "empty.sqlite", 0)
    owner.close()
    context = read_memory(tmp_path / "empty.sqlite", selected, selected.definition.layout.npc_id)
    source = context.source
    changes = {
        "world_id": replace(source, world_id="w1-" + "a" * 64),
        "catalog_sha256": replace(source, catalog_sha256="b" * 64),
        "npc_id": replace(source, npc_id="actor:other"),
        "actor_id": replace(source, actor_id="actor:other"),
        "quest_id": replace(source, quest_id="quest:other"),
    }
    other = replace(context, source=changes[field])
    with pytest.raises(GenerationError, match="^NPC_MEMORY_COMPARISON_OWNER$"):
        comparison_document(context, other)


def test_empty_and_exact_context_types(tmp_path: Path) -> None:
    selected = content()
    path = tmp_path / "empty.sqlite"
    session_at(path, 0).close()
    context = read_memory(path, selected, selected.definition.layout.npc_id)
    doc = comparison_document(context, context)
    assert doc["added"] == doc["removed"] == doc["retained"] == ()
    bad_inputs: tuple[object, ...] = (None, {}, True)
    for bad in bad_inputs:
        with pytest.raises(GenerationError, match="^NPC_CONTEXT_INPUT$"):
            comparison_document(context, cast(NpcMemoryContext, bad))
        with pytest.raises(GenerationError, match="^NPC_CONTEXT_INPUT$"):
            comparison_document(cast(NpcMemoryContext, bad), context)


@pytest.mark.parametrize("changed_read", (1, 2))
def test_either_changed_source_rejects_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changed_read: int
) -> None:
    before, after = snapshots(tmp_path)
    selected = content()
    target = before if changed_read == 1 else after
    owner = ClientSession(
        target, selected.definition.layout, quest_content=selected, npc_memory=True
    )
    calls = 0

    def read_then_commit(path: Path, accepted: QuestContent, npc: str) -> NpcMemoryContext:
        nonlocal calls
        result = read_memory(path, accepted, npc)
        calls += 1
        if calls == changed_read:
            assert owner.act("wait").status == "COMMITTED"
        return result

    monkeypatch.setattr("app.npc_memory_compare.read_memory", read_then_commit)
    try:
        with pytest.raises(GenerationError, match="^NPC_CONTEXT_STALE$"):
            export_comparison(
                before, after, selected, selected.definition.layout.npc_id, tmp_path / "out.json"
            )
        assert not (tmp_path / "out.json").exists()
    finally:
        owner.close()


@pytest.mark.parametrize("target", ("existing", "pending", "source", "parent_file"))
def test_publication_refusal_preserves_source_and_existing_output(
    tmp_path: Path, target: str
) -> None:
    before, after = snapshots(tmp_path)
    selected = content()
    output = before if target == "source" else tmp_path / "out.json"
    if target == "existing":
        output.write_bytes(b"keep-output")
    elif target == "pending":
        output.with_name("out.json.pending").write_bytes(b"keep-pending")
    elif target == "parent_file":
        (tmp_path / "not-directory").write_bytes(b"keep-parent")
        output = tmp_path / "not-directory" / "out.json"
    originals = before.read_bytes(), after.read_bytes()
    with (
        pytest.raises(GenerationError, match="^GENERATION_TARGET_EXISTS$")
        if target != "parent_file"
        else pytest.raises(FileExistsError)
    ):
        export_comparison(before, after, selected, selected.definition.layout.npc_id, output)
    assert (before.read_bytes(), after.read_bytes()) == originals
    if target == "existing":
        assert output.read_bytes() == b"keep-output"
    if target == "pending":
        assert output.with_name("out.json.pending").read_bytes() == b"keep-pending"
    if target == "parent_file":
        assert (tmp_path / "not-directory").read_bytes() == b"keep-parent"


def test_cli_is_offline_and_reports_errors_without_output(tmp_path: Path) -> None:
    before, after = snapshots(tmp_path)
    originals = before.read_bytes(), after.read_bytes()
    selected = content()
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
    env["PYTHONPATH"] = os.pathsep.join((str(guard), str(Path.cwd() / "src")))
    output = tmp_path / "cli.json"
    arguments = [
        "--before",
        str(before),
        "--after",
        str(after),
        "--quest-catalog",
        str(catalog_path),
        "--quest-sha256",
        selected.catalog_sha256,
        "--output",
        str(output),
    ]
    result = subprocess.run(
        [sys.executable, "-m", "app.npc_memory_compare", *arguments],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0 and "MEMORY_COMPARISON_SNAPSHOT" in result.stdout
    assert len(json.loads(output.read_bytes())["added"]) == 1
    assert (before.read_bytes(), after.read_bytes()) == originals
    assert main(arguments) == 1
    bad = tmp_path / "bad.sqlite"
    bad.write_bytes(b"not-a-save")
    with pytest.raises(SaveError, match="^SAVE_CORRUPT:"):
        export_comparison(
            bad, after, selected, selected.definition.layout.npc_id, tmp_path / "bad.json"
        )
    assert not (tmp_path / "bad.json").exists()
    assert bad.read_bytes() == b"not-a-save"
