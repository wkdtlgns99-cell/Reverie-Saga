from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.client_session import ClientSession
from app.headless import state_io
from app.quest import bootstrap_quest, harbor_definition
from app.quest_registry import quest_bundle
from app.watch import WatchBootstrapSpec
from contracts.client import ClientAction
from contracts.errors import BootstrapError
from contracts.persistence import SaveError, WorldUnavailable
from contracts.quest import QuestTalkCommand
from contracts.turn import GameCommand, TurnCommitted
from domain.primitives import CommandId
from domain.quest import QuestRecord
from tests.integration.test_durable_turn import UncertainPort
from tests.unit.quest_fixtures import content

LAYOUT = harbor_definition().layout
GOAL: tuple[ClientAction, ...] = (
    "down",
    "talk",
    "open",
    "right",
    "down",
    "attack",
    "attack",
    "rest",
    "attack",
)


def run_goal(session: ClientSession) -> None:
    for action in GOAL:
        assert session.act(action).status == "COMMITTED"


def test_real_quest_numeric_vector_retry_save_load_resume(tmp_path: Path) -> None:
    selected = content()
    session = ClientSession(tmp_path / "game.sqlite", LAYOUT, quest_content=selected)
    try:
        original = session.owner.snapshot(), session.owner.protocol()
        assert session.act("talk").status == "OUT_OF_RANGE"
        assert (session.owner.snapshot(), session.owner.protocol()) == original
        expected = (
            (1, 3, 5, 2, 0),
            (2, 3, 5, 2, 1),
            (3, 3, 5, 2, 1),
            (4, 3, 5, 2, 1),
            (5, 3, 5, 2, 1),
            (6, 2, 3, 1, 1),
            (7, 1, 1, 0, 1),
            (8, 1, 1, 1, 1),
            (9, 1, 0, 0, 2),
        )
        for action, vector in zip(GOAL, expected, strict=True):
            result = session.act(action)
            assert result.status == "COMMITTED" and result.view is not None
            view = result.view
            assert (
                view.tick,
                view.actor_hp,
                view.enemy_hp,
                view.stamina,
                result.quest_stage,
            ) == vector
            assert result.quest_reward == 0
            assert all("설명이 준비되지 않은 사건" not in line for line in result.messages)
        session.save("slot01")
        session.act("left")
        completed = session.act("talk")
        assert completed.view is not None and completed.view.tick == 11
        assert (completed.quest_stage, completed.quest_reward) == (3, 1)
        assert selected.dialogue.text("completion") in "\n".join(completed.messages)
        before = session.owner.snapshot(), session.owner.protocol()
        repeated = session.retry()
        assert (session.owner.snapshot(), session.owner.protocol()) == before
        assert (
            repeated.quest_reward == 1
            and selected.dialogue.text("completion") not in repeated.messages
        )
        gratitude = session.act("talk")
        assert (
            gratitude.view is not None and gratitude.view.tick == 12 and gratitude.quest_reward == 1
        )
        assert selected.dialogue.text("gratitude") in "\n".join(gratitude.messages)
        loaded = session.load("slot01")
        assert loaded.reset_log and (loaded.quest_stage, loaded.quest_reward) == (2, 0)
        path = Path(loaded.working_path)
        session.close()
        session = ClientSession(path, LAYOUT, quest_content=selected)
        assert session.update().quest_stage == 2
    finally:
        session.close()


@pytest.mark.parametrize("with_quest", (False, True))
def test_old_new_save_pins_reject_both_directions(tmp_path: Path, with_quest: bool) -> None:
    path = tmp_path / "game.sqlite"
    session = ClientSession(path, LAYOUT, quest_content=content() if with_quest else None)
    session.save("slot01")
    session.close()
    before = path.read_bytes()
    with pytest.raises(SaveError, match="UNSUPPORTED_RULESET"):
        ClientSession(path, LAYOUT, quest_content=None if with_quest else content())
    assert path.read_bytes() == before


@pytest.mark.parametrize("committed", (False, True))
def test_uncertain_report_recovery_and_new_talk(tmp_path: Path, committed: bool) -> None:
    session = ClientSession(tmp_path / "game.sqlite", LAYOUT, quest_content=content())
    try:
        run_goal(session)
        session.act("left")
        owner = session.owner
        port = UncertainPort(owner._attachment.store, commit=committed, unreadable=True)
        owner._attachment.owner._driver._commit_port = port
        with pytest.raises(WorldUnavailable, match="SAVE_UNCERTAIN"):
            session.act("talk")
        with pytest.raises(WorldUnavailable):
            session.retry()
        port.unreadable = False
        recovered = session.recover()
        assert (recovered.quest_stage, recovered.quest_reward) == ((3, 1) if committed else (2, 0))
        assert port.persist_calls == 1
        if committed:
            assert session.retry().quest_reward == 1
            assert port.persist_calls == 1
        owner._attachment.owner._driver._commit_port = owner._attachment.store
        assert session.act("talk").quest_reward == 1
        assert session.act("talk").quest_reward == 1
    finally:
        session.close()


def test_dead_target_before_acceptance_composes_0_to_2() -> None:
    selected = content()
    session = bootstrap_quest(
        WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32, initial_cell=0, enemy_hp=0), selected
    )
    io = state_io((quest_bundle(selected),))
    from contracts.trial import MoveCommand

    for index, payload in enumerate((MoveCommand(0, 1), QuestTalkCommand(LAYOUT.npc_id)), 1):
        session.driver.submit(
            GameCommand(
                CommandId(f"c1:{'0' * 32}:{'1' * 32}:{index}"),
                LAYOUT.actor_id,
                session.protocol().revision,
                payload,
            )
        )
        assert isinstance(session.last_publication().outcome, TurnCommitted)
    progress = next(r for r in session.snapshot().components if isinstance(r, QuestRecord))
    assert progress.stage == 2 and session.snapshot().tick == 2
    diff = session.last_publication().diff
    assert diff is not None
    delta = next(d for d in diff.changes if d.schema.kind == "quest.stage-delta")
    assert io.encode_payload(delta) == {
        "entity_id": "quest:harbor-sentinel",
        "before_stage": 0,
        "after_stage": 2,
    }


@pytest.mark.parametrize(
    "missing",
    (
        "engine",
        "admission",
        "reducer",
        "patch",
        "adapter",
        "presenter",
        "payload",
        "component",
        "checkpoint",
    ),
)
def test_required_binding_property_cannot_fail_open(missing: str) -> None:
    bundle = quest_bundle(content())

    # Delegation deliberately omits the binding property while keeping the actual interface.
    class Unbound:
        def __init__(self, inner: object) -> None:
            self.inner = inner

        def __getattr__(self, name: str) -> object:
            if name in ("quest_content", "scenario_layout"):
                raise AttributeError(name)
            return getattr(self.inner, name)

    from typing import cast
    from contracts.read_views import AdapterBinding

    def unbound[T](value: T) -> T:
        return cast(T, Unbound(value))

    if missing == "engine":
        bundle = replace(
            bundle,
            bindings=(
                *bundle.bindings[:-1],
                replace(bundle.bindings[-1], engine=unbound(bundle.bindings[-1].engine)),
            ),
        )
    elif missing == "checkpoint":
        bundle = replace(bundle, checkpoint_policy=unbound(bundle.checkpoint_policy))
    elif missing == "adapter":
        item = bundle.read_adapters[-1]
        assert isinstance(item, AdapterBinding)
        bundle = replace(
            bundle,
            read_adapters=(*bundle.read_adapters[:-1], AdapterBinding(unbound(item.adapter))),
        )
    elif missing == "presenter":
        item_p = bundle.presenters[-1]
        bundle = replace(
            bundle,
            presenters=(
                *bundle.presenters[:-1],
                replace(item_p, presenter=unbound(item_p.presenter)),
            ),
        )
    elif missing == "admission":
        bundle = replace(
            bundle, command_routes=(*bundle.command_routes[:-1], unbound(bundle.command_routes[-1]))
        )
    elif missing == "reducer":
        bundle = replace(
            bundle, delta_routes=(*bundle.delta_routes[:-1], unbound(bundle.delta_routes[-1]))
        )
    elif missing == "patch":
        bundle = replace(
            bundle, patch_routes=(*bundle.patch_routes[:-1], unbound(bundle.patch_routes[-1]))
        )
    elif missing == "payload":
        bundle = replace(bundle, codecs=(*bundle.codecs[:-1], unbound(bundle.codecs[-1])))
    else:
        bundle = replace(
            bundle,
            component_codecs=(*bundle.component_codecs[:-1], unbound(bundle.component_codecs[-1])),
        )
    with pytest.raises(BootstrapError, match="INVALID_QUEST_BINDING"):
        state_io((bundle,))


@pytest.mark.parametrize("stage,hp", ((1, 0), (2, 5), (3, 5)))
def test_forged_checkpoint_progress_rejected(stage: int, hp: int) -> None:
    selected = content()
    live = bootstrap_quest(WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32, enemy_hp=hp), selected)
    core = live.snapshot()
    records = tuple(
        replace(r, stage=stage) if isinstance(r, QuestRecord) else r for r in core.components
    )
    with pytest.raises(ValueError, match="QUEST_CHECKPOINT_PROGRESS"):
        state_io((quest_bundle(selected),)).validate_checkpoint(
            replace(core, components=records), live.protocol()
        )


def test_precommit_failure_on_composed_acceptance_preserves_stage_zero(tmp_path: Path) -> None:
    from app.durable import create_durable
    from contracts.persistence import DurableCheckpoint
    from contracts.trial import MoveCommand
    from contracts.turn import TurnAborted

    selected = content()
    memory = bootstrap_quest(WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32, enemy_hp=0), selected)
    owner = create_durable(
        tmp_path / "game.sqlite",
        DurableCheckpoint(memory.snapshot(), memory.protocol()),
        bundles=(quest_bundle(selected),),
    )
    try:
        owner.submit(
            GameCommand(
                CommandId(f"c1:{'0' * 32}:{'1' * 32}:1"),
                LAYOUT.actor_id,
                owner.protocol().revision,
                MoveCommand(0, 1),
            ),
            attachment_id=owner.attachment_id,
        )
        previous = owner.snapshot(), owner.protocol(), owner._attachment.store.load()
        port = UncertainPort(owner._attachment.store, commit=False)
        owner._attachment.owner._driver._commit_port = port
        publication = owner.submit(
            GameCommand(
                CommandId(f"c1:{'0' * 32}:{'1' * 32}:2"),
                LAYOUT.actor_id,
                owner.protocol().revision,
                QuestTalkCommand(LAYOUT.npc_id),
            ),
            attachment_id=owner.attachment_id,
        )
        assert isinstance(publication.outcome, TurnAborted)
        assert (owner.snapshot(), owner.protocol(), owner._attachment.store.load()) == previous
        assert next(r.stage for r in owner.snapshot().components if isinstance(r, QuestRecord)) == 0
        assert not publication.facts and not publication.cues and publication.diff is None
    finally:
        owner.close()


def test_changed_dialogue_pin_rejects_without_altering_save(tmp_path: Path) -> None:
    selected = content()
    path = tmp_path / "game.sqlite"
    session = ClientSession(path, LAYOUT, quest_content=selected)
    session.act("down")
    session.act("talk")
    session.close()
    original = path.read_bytes()
    changed = replace(
        selected,
        dialogue=replace(
            selected.dialogue,
            lines=(
                replace(selected.dialogue.lines[0], text_ko="다른 대사"),
                *selected.dialogue.lines[1:],
            ),
        ),
    )
    with pytest.raises(SaveError, match="UNSUPPORTED_RULESET"):
        ClientSession(path, LAYOUT, quest_content=changed)
    assert path.read_bytes() == original


def test_real_pipe_quest_and_zero_network_subprocess(tmp_path: Path) -> None:
    import hashlib
    import os
    import subprocess
    import sys
    from tests.integration.test_engine_bridge import PipeClient
    from app.engine_project import build_sample
    from domain.canonical import object_value
    from tests.unit.quest_fixtures import catalog

    root = Path(__file__).resolve().parents[2]
    body, _ = build_sample(root)
    narratives = tmp_path / "narratives.json"
    narratives.write_bytes(body)
    quest_bytes = catalog()
    quest_path = tmp_path / "quest.json"
    quest_path.write_bytes(quest_bytes)
    # Audit hook rejects every network attempt in the real Brain child,including DNS/connect.
    guard = tmp_path / "network-guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(
        "import sys\ndef deny(event,args):\n"
        "    if event.startswith('socket.') or event.startswith('urllib.'): raise RuntimeError('NETWORK_FORBIDDEN')\n"
        "sys.addaudithook(deny)\n",
        encoding="utf-8",
    )
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(guard) + os.pathsep + str(root / "src")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "app.engine_bridge",
            "--working",
            str(tmp_path / "pipe.sqlite"),
            "--scenario",
            "harbor",
            "--catalog",
            str(narratives),
            "--catalog-sha256",
            hashlib.sha256(body).hexdigest(),
            "--quest-catalog",
            str(quest_path),
            "--quest-sha256",
            hashlib.sha256(quest_bytes).hexdigest(),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=root,
        env=environment,
    )
    try:
        pipe = PipeClient(process)
        for action in (*GOAL, "left", "talk"):
            update = object_value(pipe.send(action)["update"])
            assert update["status"] == "COMMITTED"
        assert (update["quest_stage"], update["quest_reward"]) == ("3", "1")
        assert object_value(pipe.send("retry")["update"])["quest_reward"] == "1"
        pipe.send("quit")
        assert process.wait(timeout=20) == 0
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=20)
    replay_dir = tmp_path / "replay-child"
    replay_dir.mkdir()
    replay = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from pathlib import Path; from tests.replay.test_quest import "
            "test_independent_vector_then_real_durable_offline_replay as run; "
            "run(Path(sys.argv[1])); print('OFFLINE_REPLAY_PASSED')",
            str(replay_dir),
        ],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert replay.returncode == 0 and "OFFLINE_REPLAY_PASSED" in replay.stdout


@pytest.mark.parametrize("case", ("duplicate", "noncanonical"))
def test_checkpoint_record_count_and_order_rejected(case: str) -> None:
    selected = content()
    live = bootstrap_quest(WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32), selected)
    core = live.snapshot()
    record = next(r for r in core.components if isinstance(r, QuestRecord))
    records = (*core.components, record) if case == "duplicate" else core.components[::-1]
    expected = (
        "^duplicate component address$"
        if case == "duplicate"
        else "^components must be canonically ordered$"
    )
    with pytest.raises(ValueError, match=expected):
        state_io((quest_bundle(selected),)).validate_checkpoint(
            replace(core, components=records), live.protocol()
        )


@pytest.mark.parametrize("before", (0, 1))
def test_forged_persisted_completion_diff_rejected_through_real_io(
    tmp_path: Path, before: int
) -> None:
    from domain.canonical import array_value, object_value
    from contracts.errors import CandidateError

    selected = content()
    session = ClientSession(tmp_path / "game.sqlite", LAYOUT, quest_content=selected)
    try:
        run_goal(session)
        session.act("left")
        session.act("talk")
        publication = session.owner.last_publication()
        io = state_io((quest_bundle(selected),))
        encoded = io.encode_publication(publication)
        diff = dict(object_value(encoded["diff"]))
        changes = []
        for raw in array_value(diff["changes"]):
            row = dict(object_value(raw))
            if object_value(row["schema"])["kind"] == "quest.stage-delta":
                row["before_stage"] = before
            changes.append(row)
        diff["changes"] = tuple(changes)
        assert session._previous is not None
        with pytest.raises(CandidateError, match="INVALID_DELTA"):
            io.validate_effects(
                session._previous[0],
                publication.outcome,
                session.owner.snapshot(),
                session.owner.protocol(),
                encoded["facts"],
                diff,
            )
    finally:
        session.close()


def test_quest_postcommit_presentation_failure_keeps_truth_and_one_receipt(tmp_path: Path) -> None:
    from app.durable import create_durable
    from contracts.messages import PresentationEvent, WorldEvent
    from contracts.persistence import DurableCheckpoint
    from contracts.read_views import ReadPort
    from contracts.turn import CommitReceipt
    from contracts.trial import MoveCommand
    from orchestration.quest import QuestPresenter

    class Failing(QuestPresenter):
        def map(
            self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt, committed: ReadPort
        ) -> tuple[PresentationEvent, ...]:
            super().map(facts, receipt, committed)
            raise RuntimeError("injected display boundary failure")

    selected = content()
    bundle = quest_bundle(selected)
    bundle = replace(
        bundle,
        presenters=(
            *bundle.presenters[:-1],
            replace(bundle.presenters[-1], presenter=Failing(selected)),
        ),
    )
    memory = bootstrap_quest(WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32), selected)
    owner = create_durable(
        tmp_path / "game.sqlite",
        DurableCheckpoint(memory.snapshot(), memory.protocol()),
        bundles=(bundle,),
    )
    try:
        owner.submit(
            GameCommand(
                CommandId(f"c1:{'0' * 32}:{'1' * 32}:1"),
                LAYOUT.actor_id,
                owner.protocol().revision,
                MoveCommand(0, 1),
            ),
            attachment_id=owner.attachment_id,
        )
        command = GameCommand(
            CommandId(f"c1:{'0' * 32}:{'1' * 32}:2"),
            LAYOUT.actor_id,
            owner.protocol().revision,
            QuestTalkCommand(LAYOUT.npc_id),
        )
        result = owner.submit(command, attachment_id=owner.attachment_id)
        assert isinstance(result.outcome, TurnCommitted)
        assert tuple(d.code for d in result.diagnostics) == ("PRESENTATION_FAILED",)
        assert owner._attachment.store.load() == DurableCheckpoint(
            owner.snapshot(), owner.protocol()
        )
        assert next(r.stage for r in owner.snapshot().components if isinstance(r, QuestRecord)) == 1
        retry = owner.submit(command, attachment_id=owner.attachment_id)
        assert retry.outcome == result.outcome and not retry.facts and retry.diff is None
    finally:
        owner.close()
