from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.client_session import ClientSession
from app.headless import replay_runner
from app.npc_memory import memory_bundle, read_memory
from app.npc_memory_prepare import memory_brief
from contracts.dialogue import GenerationError
from contracts.persistence import DurableTurn, RecoveryResult, SaveError, SaveUnavailable
from contracts.replay import ReplayFixture
from contracts.turn import CommitReceipt
from domain.npc_memory import NpcQuestMemoryRecord, QuestEvidence
from domain.canonical import array_value, object_value
from orchestration.npc_memory import MemoryCheckpointPolicy
from tests.integration.test_quest import GOAL
from tests.unit.quest_fixtures import catalog, content


def session_at(path: Path, steps: int) -> ClientSession:
    selected = content()
    session = ClientSession(
        path, selected.definition.layout, quest_content=selected, npc_memory=True
    )
    for action in (*GOAL, "left", "talk")[:steps]:
        assert session.act(action).status == "COMMITTED"
    return session


@pytest.mark.parametrize(
    "steps,expected",
    (
        (0, ()),
        (2, (("accepted", 2),)),
        (9, (("accepted", 2),)),
        (11, (("accepted", 2), ("completion_reported", 11))),
    ),
)
def test_real_committed_evidence_and_read_only_privacy(
    tmp_path: Path, steps: int, expected: tuple[tuple[str, int], ...]
) -> None:
    selected = content()
    session = session_at(tmp_path / "game.sqlite", steps)
    try:
        before = (
            session.owner.snapshot(),
            session.owner.protocol(),
            session.owner.working_path.read_bytes(),
        )
        context = read_memory(
            session.owner.working_path, selected, selected.definition.layout.npc_id
        )
        assert tuple((entry.kind, entry.observed_at) for entry in context.entries) == expected
        document = context.document()
        assert [
            object_value(entry)["certainty"] for entry in array_value(document["evidence"])
        ] == ([] if steps == 0 else ["observed"] if steps < 11 else ["observed", "reported"])
        brief = memory_brief(context).text
        assert selected.definition.layout.enemy_id not in brief
        assert str(session.owner.working_path) not in brief
        assert "world_seed" not in brief and "attachment_id" not in brief
        assert len(brief.encode()) <= 4096
        assert (
            session.owner.snapshot(),
            session.owner.protocol(),
            session.owner.working_path.read_bytes(),
        ) == before
    finally:
        session.close()


def test_retry_repeat_save_load_resume_and_offline_replay(tmp_path: Path) -> None:
    selected = content()
    npc = selected.definition.layout.npc_id
    session = session_at(tmp_path / "game.sqlite", 0)
    try:
        initial = session.owner.snapshot(), session.owner.protocol()
        for action in GOAL[:2]:
            session.act(action)
        session.save("slot01")
        accepted = read_memory(session.owner.working_path, selected, npc).entries
        for action in (*GOAL[2:], "left", "talk"):
            session.act(action)
        completed = read_memory(session.owner.working_path, selected, npc).entries
        session.retry()
        session.act("talk")
        assert read_memory(session.owner.working_path, selected, npc).entries == completed
        trace = session.owner.retained_segment().trace
        fixture = ReplayFixture(*initial, trace)
        assert replay_runner(fixture, bundles=(memory_bundle(selected),)).run(trace) == ()
        session.load("slot01")
        assert read_memory(session.owner.working_path, selected, npc).entries == accepted
        branch = session.owner.working_path
    finally:
        session.close()
    resumed = ClientSession(
        branch, selected.definition.layout, quest_content=selected, npc_memory=True
    )
    try:
        assert read_memory(branch, selected, npc).entries == accepted
    finally:
        resumed.close()


@pytest.mark.parametrize("damage", ("missing", "future", "source", "stage"))
def test_checkpoint_rejects_forged_or_incomplete_memory(tmp_path: Path, damage: str) -> None:
    session = session_at(tmp_path / "game.sqlite", 2)
    try:
        core, protocol = session.owner.snapshot(), session.owner.protocol()
        memory = next(
            record for record in core.components if isinstance(record, NpcQuestMemoryRecord)
        )
        if damage == "missing":
            components = tuple(record for record in core.components if record is not memory)
        else:
            entries = (
                ()
                if damage == "stage"
                else (replace(memory.entries[0], observed_at=99),)
                if damage == "future"
                else (QuestEvidence("accepted", 2, "e1-" + "f" * 64),)
            )
            changed = replace(memory, entries=entries)
            components = tuple(
                changed if record is memory else record for record in core.components
            )
        with pytest.raises(ValueError, match="NPC_MEMORY_CHECKPOINT"):
            MemoryCheckpointPolicy(content()).validate(
                replace(core, components=components), protocol
            )
    finally:
        session.close()


def test_failed_commit_keeps_quest_and_memory_together() -> None:
    from app.headless import restore_checkpoint
    from app.npc_memory import bootstrap_memory
    from app.watch import WatchBootstrapSpec
    from contracts.quest import QuestTalkCommand
    from contracts.messages import CommandPayload
    from contracts.trial import MoveCommand
    from contracts.turn import GameCommand, TurnAborted
    from domain.primitives import CommandId, WorldRevision
    from domain.quest import QuestRecord
    from orchestration.rng import CounterRngService
    from app.headless import _restore

    selected = content()
    bundle = memory_bundle(selected)
    initial = bootstrap_memory(WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32), selected)

    def command(seq: int, payload: CommandPayload) -> GameCommand:
        return GameCommand(
            CommandId(f"c1:{'0' * 32}:{'1' * 32}:{seq}"),
            selected.definition.layout.actor_id,
            WorldRevision(seq - 1),
            payload,
        )

    initial.driver.submit(command(1, MoveCommand(0, 1)))
    core, protocol = initial.snapshot(), initial.protocol()

    class Unavailable:
        def persist(self, turn: DurableTurn) -> CommitReceipt:
            raise SaveUnavailable("SAVE_UNAVAILABLE", "offline injected IO failure")

        def recover(self, turn: DurableTurn) -> RecoveryResult:
            raise AssertionError("not uncertain")

    failed = _restore(
        core,
        protocol,
        (bundle,),
        CounterRngService(core.world_seed_hex, core.world_id, ()),
        commit_port=Unavailable(),
    )
    outcome = failed.driver.submit(command(2, QuestTalkCommand(selected.definition.layout.npc_id)))
    assert isinstance(outcome, TurnAborted)
    assert failed.snapshot() == core and failed.protocol() == protocol
    assert next(record for record in core.components if isinstance(record, QuestRecord)).stage == 0
    assert (
        next(
            record for record in core.components if isinstance(record, NpcQuestMemoryRecord)
        ).entries
        == ()
    )
    assert restore_checkpoint(core, protocol, bundles=(bundle,)).snapshot() == core


def test_legacy_source_not_upgraded_and_offline_cli_forbids_network(tmp_path: Path) -> None:
    selected = content()
    legacy = ClientSession(
        tmp_path / "old.sqlite", selected.definition.layout, quest_content=selected
    )
    legacy.close()
    before = (tmp_path / "old.sqlite").read_bytes()
    with pytest.raises(SaveError):
        read_memory(tmp_path / "old.sqlite", selected, selected.definition.layout.npc_id)
    assert (tmp_path / "old.sqlite").read_bytes() == before
    with pytest.raises(GenerationError, match="NPC_CONTEXT_OWNER"):
        read_memory(tmp_path / "missing.sqlite", selected, "actor:foreign")
    session = session_at(tmp_path / "new.sqlite", 11)
    session.close()
    working = tmp_path / "new.sqlite"
    before = working.read_bytes()
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_bytes(catalog())
    guard = tmp_path / "guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(
        "import sys\ndef check(event,args):\n if event.startswith('socket.') or event=='urllib.Request': raise RuntimeError('NETWORK_FORBIDDEN')\nsys.addaudithook(check)\n",
        encoding="utf-8",
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        (str(guard), str(Path(__file__).resolve().parents[2] / "src"))
    )
    output = tmp_path / "context.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.npc_memory_prepare",
            "--working",
            str(working),
            "--quest-catalog",
            str(catalog_path),
            "--quest-sha256",
            selected.catalog_sha256,
            "--output",
            str(output),
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0 and "CONTEXT_ONLY" in result.stdout
    assert json.loads(output.read_bytes())["generation"] is None and working.read_bytes() == before
