"""Actual public NPC patrol path,position-aware talk and committed movement history."""

from pathlib import Path
from contextlib import contextmanager
from dataclasses import replace
import hashlib
import os
import sqlite3
import subprocess
import sys
import tkinter as tk
from typing import Iterator, cast

import pytest

from app.client import CELL_PIXELS, PlayWindow, main as client_main
from app.client_worker import ClientWorker
from app.durable import create_durable
from app.headless import replay_runner
from app.npc_cycle import cycle_bundle
from contracts.npc_patrol import NpcPatrolled, NpcPatrolCue
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.read_views import ViewEpoch
from contracts.replay import ReplayFixture
from contracts.skeleton import FeatureBundle
from contracts.turn import TurnCommitted
from contracts.watch import NpcCue
from domain.canonical import object_value, text_value
from domain.primitives import EventId, Phase
from domain.state_types import StoredRoot
from orchestration.read_views import ObservedReadViewFactory
from orchestration.watch import WatchPresenter
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_durable_turn import UncertainPort
from tests.integration.test_engine_bridge import PipeClient
from tests.integration.test_npc_call_aid import session as stationary_session
from tests.integration.test_npc_gate_aid import state

from app.client_session import ClientSession
from tests.integration.test_memory_client_route import approved_content


def session(path: Path) -> ClientSession:
    content = approved_content()
    return ClientSession(
        path,
        content.definition.layout,
        quest_content=content,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
    )


def test_current_position_drives_talk_and_moves_after_resolve(tmp_path: Path) -> None:
    with_session = session(tmp_path / "game.sqlite")
    try:
        with_session.act("down")
        talk = with_session.act("talk")
        assert talk.status == "COMMITTED" and talk.view is not None
        assert talk.view.tick == 2 and talk.view.npc_cell == 7
        before = with_session.owner.snapshot(), with_session.owner.protocol()
        rejected = with_session.act("talk")
        assert rejected.status == "OUT_OF_RANGE"
        assert (with_session.owner.snapshot(), with_session.owner.protocol()) == before
        with_session.act("down")
        talk = with_session.act("talk")
        assert talk.status == "COMMITTED" and talk.view is not None
        assert talk.view.tick == 4 and talk.view.actor_cell == 6 and talk.view.npc_cell == 7
    finally:
        with_session.close()


def test_player_blocks_destination_until_leaving_it(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        moved = owner.act("down")
        assert moved.view is not None and moved.view.actor_cell == 6 and moved.view.npc_cell == 7
        owner.act("wait")
        blocked = owner.act("wait")
        assert blocked.view is not None and blocked.view.tick == 4 and blocked.view.npc_cell == 7
        assert not any(
            event.payload.schema.kind == "watch.npc-patrolled"
            for event in owner.owner.last_publication().facts
        )
        owner.act("up")
        moved = owner.act("wait")
        assert moved.view is not None and moved.view.tick == 6 and moved.view.npc_cell == 6
    finally:
        owner.close()


def test_long_wait_keeps_intermediate_movement_despite_net_identity(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        update = owner.act("wait", seconds=16)
        assert update.status == "COMMITTED" and update.view is not None
        assert update.view.tick == 16 and update.view.npc_cell == 6
        facts = tuple(
            event
            for event in owner.owner.last_publication().facts
            if event.payload.schema.kind == "watch.npc-patrolled"
        )
        assert tuple(event.due_tick for event in facts) == (2, 4, 6, 8, 10, 12, 14, 16)
        assert update.messages.count("NPC가 공동 작업 구역을 순찰했습니다.") == 8
    finally:
        owner.close()


def bundle() -> FeatureBundle:
    return cycle_bundle(
        approved_content(), npc_aid=True, npc_supply_aid=True, npc_call_aid=True, npc_patrol=True
    )


def replay(owner: ClientSession) -> None:
    segment = owner.owner.retained_segment()
    fixture = ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace)
    assert replay_runner(fixture, bundles=(bundle(),)).run(segment.trace) == ()


def test_intermediate_cues_and_real_movement_causality(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("wait", seconds=16)
        publication = owner.owner.last_publication()
        ordinary = tuple(c.payload for c in publication.cues if isinstance(c.payload, NpcCue))
        moved = tuple(c.payload for c in publication.cues if isinstance(c.payload, NpcPatrolCue))
        assert tuple(c.cell for c in ordinary) == (6, 7, 6, 7, 6, 7, 6, 7)
        assert tuple(c.after_cell for c in moved) == (7, 6, 7, 6, 7, 6, 7, 6)
        assert tuple((c.x_mm, c.z_mm) for c in moved) == ((1000, 2000), (0, 2000)) * 4
        by_id = {event.header.event_id: event for event in publication.facts}
        for event in publication.facts:
            if isinstance(event.payload, NpcPatrolled):
                source = by_id[event.header.caused_by[0]]
                assert event.header.phase is Phase.POST_TICK
                assert source.payload.schema.kind == "watch.npc-acted"
                assert source.header.phase is Phase.PRE_TICK
                assert source.due_tick == event.due_tick
        before = state(owner)
        assert "순찰" not in " ".join(owner.retry().messages)
        assert state(owner) == before
        replay(owner)
    finally:
        owner.close()


@pytest.mark.parametrize(
    "damage", ("producer", "phase", "cause", "duplicate", "missing_last", "endpoint")
)
def test_presenter_rejects_broken_actual_movement_chain(tmp_path: Path, damage: str) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("wait", seconds=4)
        publication = owner.owner.last_publication()
        selected = next(p for p in bundle().presenters if p.presenter_id == "watch.presenter")
        facts = list(event for event in publication.facts if event.payload.schema in selected.kinds)
        index = next(i for i, event in enumerate(facts) if isinstance(event.payload, NpcPatrolled))
        event = facts[index]
        if damage == "producer":
            facts[index] = replace(event, header=replace(event.header, producer_id="watch.bell"))
        elif damage == "phase":
            facts[index] = replace(event, header=replace(event.header, phase=Phase.PRE_TICK))
        elif damage == "cause":
            facts[index] = replace(
                event, header=replace(event.header, caused_by=(EventId("e1-" + "f" * 64),))
            )
        elif damage == "duplicate":
            facts.insert(index, event)
        elif damage == "missing_last":
            facts.pop(
                next(
                    i
                    for i in reversed(range(len(facts)))
                    if isinstance(facts[i].payload, NpcPatrolled)
                )
            )
        else:
            payload = cast(NpcPatrolled, event.payload)
            facts[index] = replace(event, payload=replace(payload, before_cell=7))
        factory = ObservedReadViewFactory(StoredRoot(owner.owner.snapshot().components, 0))
        for binding in bundle().read_adapters:
            binding.install(factory)
        receipt = cast(TurnCommitted, publication.outcome).receipt
        read = factory.open(ViewEpoch(receipt.tick, Phase.PRESENT, 0, "watch.presenter", 0))
        with pytest.raises(ValueError, match="patrol"):
            WatchPresenter(approved_content().definition.layout, npc_patrol=True).map(
                tuple(facts), receipt, read
            )
    finally:
        owner.close()


def test_saved_moving_position_branch_restart_checkpoint_and_call(tmp_path: Path) -> None:
    original = tmp_path / "source/game.sqlite"
    owner = session(original)
    try:
        owner.act("down")
        accepted = owner.act("talk")
        assert accepted.view is not None and accepted.view.npc_cell == 7
        owner.save("slot01")
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        clone = tmp_path / "checkpoint/game.sqlite"
        create_durable(clone, checkpoint, bundles=(bundle(),)).close()
        owner.act("wait", seconds=2)
        owner.save("slot01")
        before = state(owner)
        preview = owner.inspect_slot("slot01", previous=True)
        assert preview.status == "SLOT_INSPECTED" and state(owner) == before
        loaded = owner.load("slot01", previous=True)
        assert loaded.view is not None and loaded.view.tick == 2 and loaded.view.npc_cell == 7
        branch = owner.owner.working_path
        source_bytes = original.read_bytes()
    finally:
        owner.close()
    for path in (branch, clone):
        owner = session(path)
        try:
            view = owner.update().view
            assert view is not None and view.tick == 2 and view.npc_cell == 7
            assert owner.inspect_activity().status == "ACTIVITY_INSPECTED"
            owner.act("wait", seconds=6)
            answered = owner.act("bell")
            assert answered.view is not None and answered.view.tick == 9 and answered.view.gate_open
            assert "NPC가 의뢰를 돕기 위해 통행문을 열었습니다." in answered.messages
            assert owner.inspect_activity().status == "ACTIVITY_INSPECTED"
            replay(owner)
        finally:
            owner.close()
    assert original.read_bytes() == source_bytes
    before_bytes = original.read_bytes()
    with pytest.raises(SaveError, match="UNSUPPORTED_RULESET"):
        stationary_session(original)
    assert original.read_bytes() == before_bytes


@pytest.mark.parametrize("commit", (False, True))
def test_uncertain_movement_commit_keeps_truth_and_retry(tmp_path: Path, commit: bool) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("wait")
        before = state(owner)
        store = owner.owner._attachment.store
        port = UncertainPort(store, commit=commit)
        owner.owner._attachment.owner._driver._commit_port = port
        update = owner.act("wait")
        assert port.persist_calls == port.recover_calls == 1
        assert update.status == ("COMMITTED" if commit else "SAVE_UNAVAILABLE")
        assert update.view is not None and update.view.npc_cell == (7 if commit else 6)
        if commit:
            after = state(owner)
            assert "순찰" not in " ".join(owner.retry().messages) and state(owner) == after
        else:
            assert state(owner) == before
        assert store.load() == DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()


def test_sql_rollback_then_exact_movement_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("wait")
        before = state(owner)
        store = owner.owner._attachment.store
        original = store._execute

        def fail(
            query: str, values: tuple[None | int | float | str | bytes, ...] = ()
        ) -> sqlite3.Cursor:
            result = original(query, values)
            if query.startswith("INSERT INTO replay"):
                raise sqlite3.IntegrityError("F69 real patrol rollback")
            return result

        with monkeypatch.context() as patch:
            patch.setattr(store, "_execute", fail)
            assert owner.act("wait").status == "SAVE_UNAVAILABLE"
        assert state(owner) == before
        retry = owner.retry()
        assert retry.view is not None and retry.view.tick == 2 and retry.view.npc_cell == 7
        assert retry.messages.count("NPC가 공동 작업 구역을 순찰했습니다.") == 1
        replay(owner)
    finally:
        owner.close()


@pytest.mark.parametrize("factory", (ClientSession, ClientWorker))
@pytest.mark.parametrize("flag", (True, 0, 1, None, "1", 2.0))
def test_invalid_selection_precedes_files_or_worker(
    factory: type[ClientSession] | type[ClientWorker], flag: object, tmp_path: Path
) -> None:
    path = tmp_path / "missing/game.sqlite"
    selected = approved_content()
    with pytest.raises(ValueError, match="^NPC_PATROL_CONTENT$"):
        factory(
            path,
            selected.definition.layout,
            quest_content=selected,
            npc_memory=True,
            npc_cycle=True,
            npc_aid=True,
            npc_supply_aid=True,
            npc_call_aid=flag is not True,
            npc_patrol=cast(bool, flag),
        )
    assert not path.parent.exists()


def test_cli_rejects_patrol_without_call_before_tk() -> None:
    with pytest.raises(ValueError, match="^NPC_PATROL_CONTENT$"):
        client_main(["--npc-patrol"])


def test_worker_roundtrip_and_actual_hidden_tk_marker(tk_host: tk.Tk, tmp_path: Path) -> None:
    selected = approved_content()
    worker = ClientWorker(
        tmp_path / "worker/game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
    )
    try:
        worker.request("wait").result(timeout=10)
        update = worker.request("wait").result(timeout=10)
        assert update.view is not None and update.view.npc_cell == 7
        assert worker.inspect_activity().result(timeout=10).view == update.view
    finally:
        worker.join()
    panel = tk.Toplevel(tk_host)
    panel.withdraw()
    screen = PlayWindow(
        panel,
        tmp_path / "tk/game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        assert screen.mode_label == "NPC 순찰·호출 지원·물자·반복 작업·기억 모드"
        for action in ("down", "talk"):
            _click(screen, action)
        assert screen.last_update is not None and screen.last_update.view is not None
        assert screen.last_update.view.npc_cell == 7
        x = CELL_PIXELS + CELL_PIXELS // 2
        y = 2 * CELL_PIXELS + CELL_PIXELS // 2
        assert screen.canvas.coords("npc") == [x - 33, y - 33, x + 33, y + 33]
        _click(screen, "save")
        _click(screen, "wait")
        _click(screen, "wait")
        assert screen.last_update.view.npc_cell == 6
        _click(screen, "load")
        assert screen.last_update.view.npc_cell == 7
    finally:
        screen.close()


@contextmanager
def patrol_pipe(path: Path) -> Iterator[PipeClient]:
    root = Path(__file__).resolve().parents[2]
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
            approved_content().catalog_sha256,
            "--npc-memory",
            "--npc-cycle",
            "--npc-aid",
            "--npc-supply-aid",
            "--npc-call-aid",
            "--npc-patrol",
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
            pytest.fail("owned patrol Brain did not stop on EOF")
        if process.stdout is not None:
            process.stdout.close()
        errors = b"" if process.stderr is None else process.stderr.read()
        if process.stderr is not None:
            process.stderr.close()
        assert process.returncode == 0, errors.decode("utf-8", errors="replace")


def test_real_framed_patrol_save_load_resume_and_query(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with patrol_pipe(path) as pipe:
        pipe.send("down")
        update = object_value(pipe.send("talk")["update"])
        assert object_value(update["view"])["npc_cell"] == "7"
        pipe.send("save")
        pipe.send("wait")
        update = object_value(pipe.send("wait")["update"])
        assert object_value(update["view"])["npc_cell"] == "6"
        before = path.read_bytes()
        update = object_value(pipe.send("load")["update"])
        branch = Path(text_value(update["working_path"]))
        assert object_value(update["view"])["npc_cell"] == "7" and path.read_bytes() == before
    with patrol_pipe(branch) as pipe:
        update = object_value(pipe.latest["update"])
        assert object_value(update["view"])["npc_cell"] == "7"
        update = object_value(pipe.send("activity")["update"])
        assert (
            update["status"] == "ACTIVITY_INSPECTED"
            and object_value(update["view"])["npc_cell"] == "7"
        )
        pipe.send("wait")
        update = object_value(pipe.send("wait")["update"])
        assert object_value(update["view"])["npc_cell"] == "6"
