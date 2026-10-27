from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
import hashlib
import os
import sqlite3
import subprocess
import sys
import tkinter as tk
from typing import Iterator, cast

import pytest

from app.client import PlayWindow
from app.client_session import ClientSession
from app.client_worker import ClientWorker
from app.durable import create_durable
from app.headless import replay_runner
from app.npc_cycle import cycle_bundle
from contracts.client import ClientUpdate
from contracts.encounter import GateChanged
from contracts.read_views import ViewEpoch
from contracts.turn import TurnCommitted
from contracts.npc_gate_aid import GateAidCue, GateAssisted
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.replay import ReplayFixture
from domain.canonical import object_value, text_value
from domain.primitives import Phase, Tick
from domain.state_types import StoredRoot
from orchestration.read_views import ObservedReadViewFactory
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_durable_turn import UncertainPort
from tests.integration.test_engine_bridge import PipeClient
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_cycle import cycle, session as old_cycle_session
from tests.integration.test_npc_player_memory import promise, remembered


def session(path: Path) -> ClientSession:
    selected = approved_content()
    return ClientSession(
        path,
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
    )


def aided(update: ClientUpdate) -> bool:
    return "NPC가 의뢰를 돕기 위해 통행문을 열었습니다." in update.messages


def state(owner: ClientSession) -> tuple[object, ...]:
    return owner.owner.snapshot(), owner.owner.protocol(), owner.owner.working_path.read_bytes()


def replay(owner: ClientSession) -> None:
    segment = owner.owner.retained_segment()
    assert (
        replay_runner(
            ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace),
            bundles=(cycle_bundle(approved_content(), npc_aid=True),),
        ).run(segment.trace)
        == ()
    )


def test_acceptance_next_wake_real_action_cue_retry_and_readonly(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        initial = state(owner)
        assert owner.act("talk").status == "OUT_OF_RANGE" and state(owner) == initial
        owner.act("down")
        accepted = owner.act("talk")
        assert accepted.view is not None and accepted.view.tick == 2 and not accepted.view.gate_open
        assert remembered(accepted) == (promise(2),)
        assert not aided(owner.act("wait"))
        opened = owner.act("wait")
        assert opened.view is not None and opened.view.tick == 4 and opened.view.gate_open
        assert aided(opened) and cycle(owner).state.produced == 1
        publication = owner.owner.last_publication()
        facts = [e for e in publication.facts if isinstance(e.payload, GateAssisted)]
        assert len(facts) == 1 and len(facts[0].header.caused_by) == 1
        cues = [c for c in publication.cues if isinstance(c.payload, GateAidCue)]
        assert len(cues) == 1 and cast(GateAidCue, cues[0].payload).logical_tick == 4
        before = state(owner)
        assert not aided(owner.retry()) and state(owner) == before
        assert owner.inspect_activity().status == "ACTIVITY_INSPECTED" and state(owner) == before
        assert owner.act("wait", seconds=16).view is not None
        assert not aided(owner.act("wait"))  # already open,no duplicate event
        replay(owner)
    finally:
        owner.close()


def test_long_wait_partition_and_supply_identity(tmp_path: Path) -> None:
    long, split = session(tmp_path / "long/game.sqlite"), session(tmp_path / "split/game.sqlite")
    try:
        for owner in (long, split):
            owner.act("down")
            owner.act("talk")
        update = long.act("wait", seconds=16)
        assert update.view is not None and update.view.tick == 18 and update.view.gate_open
        assert sum("의뢰를 돕기" in m for m in update.messages) == 1
        count = sum(aided(split.act("wait")) for _ in range(16))
        assert count == 1 and long.owner.snapshot() == split.owner.snapshot()
        assert (
            cycle(long).state.stock,
            cycle(long).state.produced,
            cycle(long).state.consumed,
        ) == (3, 4, 1)
        for owner in (long, split):
            replay(owner)
    finally:
        long.close()
        split.close()


def test_player_close_then_real_npc_reopen_and_identity_net(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=2)
        closed = owner.act("close")  # 5,odd
        assert closed.view is not None and not closed.view.gate_open and not aided(closed)
        assert aided(owner.act("wait"))  # 6
        owner.act("wait")
        both = owner.act("close")  # 8,RESOLVE close then POST_TICK reopen
        assert both.view is not None and both.view.gate_open and aided(both)
        assert "플레이어가 문을 닫았습니다." in both.messages
        assert not owner.owner.last_publication().diagnostics
        replay(owner)
    finally:
        owner.close()


def test_unaccepted_or_already_open_has_no_false_aid(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        assert not aided(owner.act("wait", seconds=16))
        current = owner.update()
        assert current.view is not None and not current.view.gate_open
        owner.act("down")
        owner.act("open")
        owner.act("talk")
        assert not aided(owner.act("wait", seconds=16))
        replay(owner)
    finally:
        owner.close()


def test_report_ends_support_without_inventing_eyewitness_memory(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        assert aided(owner.act("wait", seconds=2))
        for action in ("right", "down", "attack", "attack", "rest", "attack", "up", "left"):
            assert owner.act(action).status == "COMMITTED"  # tick12
        assert owner.update().quest_stage == 2 and owner.update().quest_reward == 0
        assert len(owner.inspect_memory().messages) == 1
        reported = owner.act("talk")  # 13
        assert reported.quest_stage == 3 and reported.quest_reward == 1
        assert "직접 본 기억은 아닙니다" in owner.inspect_memory().messages[-1]
        owner.act("close")  # 14
        result = owner.act("wait", seconds=16)
        assert result.view is not None and not result.view.gate_open and not aided(result)
        assert owner.act("talk").quest_reward == 1
        replay(owner)
    finally:
        owner.close()


def test_compacted_accepted_checkpoint_continues_actual_aid(tmp_path: Path) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    path = tmp_path / "compact/game.sqlite"
    create_durable(
        path, checkpoint, bundles=(cycle_bundle(approved_content(), npc_aid=True),)
    ).close()
    owner = session(path)
    try:
        assert not owner.owner.retained_segment().trace.steps
        assert aided(owner.act("wait", seconds=2))
        assert owner.inspect_activity().status == "ACTIVITY_INSPECTED"
        replay(owner)
    finally:
        owner.close()


def test_even_tick_report_is_heard_after_that_barriers_aid_decision(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=2)
        for action in (
            "right",
            "down",
            "attack",
            "attack",
            "rest",
            "attack",
            "up",
            "left",
            "close",
        ):
            assert owner.act(action).status == "COMMITTED"  # 13,closed
        reported = owner.act("talk")  # 14;both consumers read prior POST_TICK memory
        assert reported.view is not None and reported.view.tick == 14 and reported.view.gate_open
        assert aided(reported) and reported.quest_reward == 1
        assert "14초" in owner.inspect_memory().messages[-1]
        closed = owner.act("close")  # 15
        assert closed.view is not None and not closed.view.gate_open
        assert not aided(owner.act("wait"))  # 16,reported memory is now visible
        replay(owner)
    finally:
        owner.close()


@pytest.mark.parametrize("commit", (False, True))
def test_uncertain_gate_commit_and_quiet_retry(tmp_path: Path, commit: bool) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        before = state(owner)
        store = owner.owner._attachment.store
        port = UncertainPort(store, commit=commit)
        owner.owner._attachment.owner._driver._commit_port = port
        result = owner.act("wait", seconds=2)
        assert port.persist_calls == port.recover_calls == 1
        assert result.status == ("COMMITTED" if commit else "SAVE_UNAVAILABLE")
        assert result.view is not None and result.view.gate_open == commit
        assert aided(result) == commit
        if commit:
            current = state(owner)
            assert not aided(owner.retry()) and state(owner) == current
        else:
            assert state(owner) == before
        assert store.load() == DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()


def test_real_sql_rollback_at_opening_preserves_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        before = state(owner)
        store = owner.owner._attachment.store
        original = store._execute

        def fail(
            query: str, values: tuple[None | int | float | str | bytes, ...] = ()
        ) -> sqlite3.Cursor:
            result = original(query, values)
            if query.startswith("INSERT INTO pending"):
                raise sqlite3.IntegrityError("F54 after actual gate aid staging")
            return result

        with monkeypatch.context() as patch:
            patch.setattr(store, "_execute", fail)
            assert owner.act("wait", seconds=2).status == "SAVE_UNAVAILABLE"
        assert state(owner) == before
        assert aided(owner.retry())
    finally:
        owner.close()


def test_saved_previous_branch_restart_and_unchanged_sources(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.save("slot01")
        owner.act("wait", seconds=2)
        owner.save("slot01")
        sources = {
            p: p.read_bytes()
            for p in tmp_path.rglob("*.sqlite")
            if not p.name.endswith(".lock.sqlite")
        }
        before = state(owner)
        assert owner.inspect_slot("slot01", previous=True).status == "SLOT_INSPECTED"
        assert state(owner) == before
        assert owner.load("slot01", previous=True).status == "LOADED"
        path = owner.owner.working_path
    finally:
        owner.close()
    owner = session(path)
    try:
        current = owner.update()
        assert current.view is not None and current.view.tick == 2
        assert aided(owner.act("wait", seconds=2))
        assert owner.inspect_activity().status == "ACTIVITY_INSPECTED"
        assert all(p.read_bytes() == raw for p, raw in sources.items())
        replay(owner)
    finally:
        owner.close()


@pytest.mark.parametrize("factory", (ClientSession, ClientWorker))
@pytest.mark.parametrize("flag", (True, 0, 1, None, "1"))
def test_invalid_selection_rejects_before_file_or_thread(
    factory: type[ClientSession] | type[ClientWorker], flag: object, tmp_path: Path
) -> None:
    selected = approved_content()
    path = tmp_path / "missing/game.sqlite"
    with pytest.raises(ValueError, match="^NPC_AID_CONTENT$"):
        factory(
            path,
            selected.definition.layout,
            quest_content=selected,
            npc_memory=True,
            npc_aid=cast(bool, flag),
        )
    assert not path.parent.exists()


def test_old_cycle_saves_reject_without_repinning_either_direction(tmp_path: Path) -> None:
    for old in (False, True):
        path = tmp_path / str(old) / "game.sqlite"
        (old_cycle_session(path) if old else session(path)).close()
        before = path.read_bytes()
        with pytest.raises(SaveError, match="UNSUPPORTED_RULESET"):
            (session(path) if old else old_cycle_session(path))
        assert path.read_bytes() == before


@contextmanager
def aid_pipe(path: Path) -> Iterator[PipeClient]:
    root = Path(__file__).resolve().parents[2]
    selected = approved_content()
    catalog = root / "content/narratives.json"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "app.engine_bridge",
            "--working",
            str(path),
            "--catalog",
            str(catalog),
            "--catalog-sha256",
            hashlib.sha256(catalog.read_bytes()).hexdigest(),
            "--scenario",
            "harbor",
            "--quest-catalog",
            str(root / "content/dialogue/harbor-memory-v1.json"),
            "--quest-sha256",
            selected.catalog_sha256,
            "--npc-memory",
            "--npc-cycle",
            "--npc-aid",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=root,
        env=dict(os.environ, PYTHONPATH=str(root / "src"), PYTHONUTF8="1"),
    )
    try:
        yield PipeClient(process)
    finally:
        if process.stdin is not None:
            process.stdin.close()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=15)
            pytest.fail("owned aid Brain did not stop on EOF")
        if process.stdout is not None:
            process.stdout.close()
        errors = b"" if process.stderr is None else process.stderr.read()
        if process.stderr is not None:
            process.stderr.close()
        assert process.returncode == 0, errors.decode("utf-8", errors="replace")


def test_actual_pipe_variant_retrieval_rewind_and_reconnect(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with aid_pipe(path) as pipe:
        pipe.send("down")
        pipe.send("talk")
        pipe.send("save")
        pipe.send("wait")
        opened = object_value(pipe.send("wait")["update"])
        assert object_value(opened["view"])["gate_open"] is True
        assert object_value(pipe.send("activity")["update"])["status"] == "ACTIVITY_INSPECTED"
        restored = object_value(pipe.send("load")["update"])
        assert object_value(restored["view"])["gate_open"] is False
        path = Path(text_value(restored["working_path"]))
    with aid_pipe(path) as pipe:
        pipe.send("wait")
        assert object_value(object_value(pipe.send("wait")["update"])["view"])["gate_open"] is True


def test_actual_tk_aid_gate_and_worker_save_load(tk_host: tk.Tk, tmp_path: Path) -> None:
    selected = approved_content()
    panel = tk.Toplevel(tk_host)
    panel.withdraw()
    screen = PlayWindow(
        panel,
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        assert screen.mode_label == "NPC 의뢰 지원·반복 작업·기억 모드"
        for action in ("down", "talk", "save", "wait", "wait"):
            _click(screen, action)
        assert screen.last_update is not None and screen.last_update.view is not None
        assert screen.last_update.view.gate_open and aided(screen.last_update)
        assert screen.worker.inspect_activity().result(timeout=30).status == "ACTIVITY_INSPECTED"
        _click(screen, "load")
        assert screen.last_update.view is not None and not screen.last_update.view.gate_open
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())


def test_blocked_move_then_npc_opens_has_truthful_presentation(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait")
        result = owner.act("right")  # 4:RESOLVE blocked,POST_TICK opens
        assert result.view is not None and result.view.actor_cell == 3 and result.view.gate_open
        assert result.status == "COMMITTED" and aided(result)
        assert "닫힌 문에 막혔습니다. 문을 먼저 여세요." in result.messages
        assert not owner.owner.last_publication().diagnostics
        assert owner.act("right").view is not None
        assert owner.update().view is not None
        replay(owner)
    finally:
        owner.close()


@pytest.mark.parametrize("bad", ("endpoint", "phase", "order", "missing", "cause"))
def test_presenter_rejects_forged_or_incomplete_gate_chain(tmp_path: Path, bad: str) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=2)
        owner.act("wait")
        owner.act("close")  # 6,real close/open pair
        publication = owner.owner.last_publication()
        assert isinstance(publication.outcome, TurnCommitted)
        facts = tuple(
            e for e in publication.facts if isinstance(e.payload, (GateChanged, GateAssisted))
        )
        assert len(facts) == 2
        if bad == "endpoint":
            facts = (
                replace(
                    facts[0], payload=replace(cast(GateChanged, facts[0].payload), after_open=1)
                ),
                facts[1],
            )
        elif bad == "phase":
            facts = (
                facts[0],
                replace(facts[1], header=replace(facts[1].header, phase=Phase.RESOLVE)),
            )
        elif bad == "order":
            facts = tuple(reversed(facts))
        elif bad == "missing":
            facts = facts[:1]
        else:
            facts = (facts[0], replace(facts[1], header=replace(facts[1].header, caused_by=())))
        bundle = cycle_bundle(approved_content(), npc_aid=True)
        factory = ObservedReadViewFactory(StoredRoot(owner.owner.snapshot().components, 0))
        for binding in bundle.read_adapters:
            binding.install(factory)
        epoch = ViewEpoch(Tick(6), Phase.PRESENT, 0, "encounter.presenter", 0)
        read = factory.open(epoch)
        presenter = next(
            p.presenter for p in bundle.presenters if p.presenter_id == "encounter.presenter"
        )
        with pytest.raises(ValueError, match="^NPC_AID_(SOURCE|GATE_CHAIN)$"):
            presenter.map(facts, publication.outcome.receipt, read)
        factory.close(epoch)
    finally:
        owner.close()
