"""Conversation-aware patrol stays for actual talk and resumes on later wakes."""

from pathlib import Path
from contextlib import contextmanager
import hashlib
import os
import sqlite3
import subprocess
import sys
import tkinter as tk
from typing import Iterator
import pytest
from app.client import PlayWindow, main as client_main
from app.client_worker import ClientWorker
from app.durable import create_durable
from app.headless import replay_runner
from app.npc_cycle import cycle_bundle
from contracts.npc_patrol import NpcPatrolled, NpcPatrolCue
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.replay import ReplayFixture
from contracts.skeleton import FeatureBundle
from contracts.quest import QuestCompleted
from domain.canonical import object_value, text_value
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_durable_turn import UncertainPort
from tests.integration.test_engine_bridge import PipeClient
from app.client_session import ClientSession
from contracts.client import ClientUpdate, ClientView
from tests.integration.test_memory_client_route import approved_content


def _view(update: ClientUpdate) -> ClientView:
    assert update.view is not None
    return update.view


def session(path: Path) -> ClientSession:
    selected = approved_content()
    return ClientSession(
        path,
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
    )


def test_actual_talk_turn_holds_then_later_wait_resumes(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        for tick in (2, 3, 4):
            update = owner.act("talk")
            assert update.status == "COMMITTED" and update.view is not None
            assert (update.view.tick, update.view.npc_cell) == (tick, 6)
            assert not any("NPC가 공동 작업 구역을 순찰" in line for line in update.messages)
        owner.act("wait")
        update = owner.act("wait")
        assert update.view is not None and (update.view.tick, update.view.npc_cell) == (6, 7)
        before = owner.owner.snapshot(), owner.owner.protocol()
        assert owner.act("talk").status == "OUT_OF_RANGE"
        assert (owner.owner.snapshot(), owner.owner.protocol()) == before
    finally:
        owner.close()


def test_saved_station_pose_after_talk_restores_without_tick_inference(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.save("slot01")
        owner.act("wait", seconds=4)
        loaded = owner.load("slot01")
        assert loaded.view is not None and (loaded.view.tick, loaded.view.npc_cell) == (2, 6)
        assert owner.inspect_activity().status == "ACTIVITY_INSPECTED"
    finally:
        owner.close()


def bundle() -> FeatureBundle:
    return cycle_bundle(
        approved_content(),
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
    )


def replay(owner: ClientSession) -> None:
    segment = owner.owner.retained_segment()
    fixture = ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace)
    assert replay_runner(fixture, bundles=(bundle(),)).run(segment.trace) == ()


def state(owner: ClientSession) -> tuple[object, ...]:
    return (
        owner.owner.snapshot(),
        owner.owner.protocol(),
        owner.owner.retained_segment(),
        owner.owner.working_path.read_bytes(),
    )


def test_full_native_timeline_branch_reconnect_and_long_wait(tmp_path: Path) -> None:
    source = tmp_path / "source/game.sqlite"
    owner = session(source)
    try:
        owner.act("down")
        first = owner.act("talk")
        assert (
            "현재 확인 범위에 남은 순찰 이동이 없습니다. 현재 위치로 과거 이동을 추정하지 않습니다."
            in first.messages
        )
        assert not any(
            type(e.payload) is NpcPatrolled for e in owner.owner.last_publication().facts
        )
        owner.save("slot01")
        owner.act("talk")
        owner.act("talk")
        owner.act("wait")
        owner.act("wait")
        before = state(owner)
        assert owner.act("talk").status == "OUT_OF_RANGE"
        assert state(owner) == before
        owner.act("down")
        owner.act("talk")
        owner.save("slot01")
        aid = owner.act("bell")
        assert (
            aid.view is not None
            and aid.view.tick == 9
            and aid.view.npc_cell == 7
            and aid.view.gate_open
        )
        assert aid.messages.count("NPC가 의뢰를 돕기 위해 통행문을 열었습니다.") == 1
        activity = owner.inspect_activity()
        assert activity.messages[0] == "NPC 반복 작업: 물자 2/3개 · 준비 2회 · 사용 0회."
        assert "확인한 호출 응답 1건 중 최근 1건입니다." in activity.messages
        before = state(owner)
        assert not any("순찰" in line for line in owner.retry().messages)
        assert state(owner) == before
        loaded = owner.load("slot01", previous=True)
        assert loaded.view is not None and (loaded.view.tick, loaded.view.npc_cell) == (2, 6)
        branch = owner.owner.working_path
        source_bytes = source.read_bytes()
        replay(owner)
    finally:
        owner.close()
    owner = session(branch)
    try:
        before = state(owner)
        assert owner.inspect_slot("slot01").messages[-3:] == (
            "NPC 순찰 위치 비교 · 현재 2초 / 선택 저장 8초",
            "현재 NPC 위치 · 원래 작업 지점입니다.",
            "선택 저장 NPC 위치 · 옆 작업 지점입니다.",
        )
        assert state(owner) == before
        waited = owner.act("wait", seconds=16)
        assert waited.view is not None and (waited.view.tick, waited.view.npc_cell) == (18, 6)
        publication = owner.owner.last_publication()
        assert tuple(e.due_tick for e in publication.facts if type(e.payload) is NpcPatrolled) == (
            4,
            6,
            8,
            10,
            12,
            14,
            16,
            18,
        )
        assert tuple(
            c.payload.after_cell for c in publication.cues if type(c.payload) is NpcPatrolCue
        ) == (7, 6, 7, 6, 7, 6, 7, 6)
        assert "확인한 순찰 이동 8건 중 최근 3건입니다." in owner.inspect_activity().messages
        replay(owner)
    finally:
        owner.close()
    assert source.read_bytes() == source_bytes


def test_completion_and_gratitude_pause_without_changing_rewards(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=6)
        owner.act("bell")
        for action in (
            "right",
            "down",
            "attack",
            "attack",
            "rest",
            "attack",
            "up",
            "left",
            "down",
            "right",
        ):
            assert owner.act(action).status == "COMMITTED"
        completed = owner.act("talk")
        assert completed.view is not None and (
            completed.view.tick,
            completed.view.actor_cell,
            completed.view.npc_cell,
        ) == (20, 7, 7)
        assert completed.quest_reward == 1
        assert (
            sum(type(e.payload) is QuestCompleted for e in owner.owner.last_publication().facts)
            == 1
        )
        for tick in (21, 22):
            thanked = owner.act("talk")
            assert thanked.view is not None and (thanked.view.tick, thanked.view.npc_cell) == (
                tick,
                7,
            )
            assert thanked.quest_reward == 1
            assert not any(
                type(e.payload) in (QuestCompleted, NpcPatrolled)
                for e in owner.owner.last_publication().facts
            )
        replay(owner)
    finally:
        owner.close()


def test_checkpoint_only_pose_and_cross_mode_save_identity(tmp_path: Path) -> None:
    source = tmp_path / "source/game.sqlite"
    owner = session(source)
    try:
        owner.act("down")
        owner.act("talk")
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    target = tmp_path / "checkpoint/game.sqlite"
    create_durable(target, checkpoint, bundles=(bundle(),)).close()
    from tests.integration.test_npc_patrol import session as old_patrol

    before = source.read_bytes()
    with pytest.raises(SaveError, match="UNSUPPORTED_RULESET"):
        old_patrol(source)
    assert source.read_bytes() == before
    owner = session(target)
    try:
        assert not owner.owner.retained_segment().trace.steps
        update = owner.act("talk")
        assert update.view is not None and (update.view.tick, update.view.npc_cell) == (3, 6)
        owner.act("wait")
        assert _view(owner.update()).npc_cell == 7
        replay(owner)
    finally:
        owner.close()


@pytest.mark.parametrize("commit", (False, True))
def test_uncertain_talk_commit_preserves_actual_pause_truth(tmp_path: Path, commit: bool) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        before = state(owner)
        store = owner.owner._attachment.store
        port = UncertainPort(store, commit=commit)
        owner.owner._attachment.owner._driver._commit_port = port
        result = owner.act("talk")
        assert port.persist_calls == port.recover_calls == 1
        assert result.status == ("COMMITTED" if commit else "SAVE_UNAVAILABLE")
        assert (
            result.view is not None
            and result.view.npc_cell == 6
            and result.view.tick == (2 if commit else 1)
        )
        if commit:
            after = state(owner)
            assert not any("순찰" in line for line in owner.retry().messages)
            assert state(owner) == after
        else:
            assert state(owner) == before
        assert store.load() == DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()


def test_sql_rollback_then_retry_pauses_only_actual_committed_talk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        before = state(owner)
        store = owner.owner._attachment.store
        original = store._execute

        def fail(
            query: str, values: tuple[None | int | float | str | bytes, ...] = ()
        ) -> sqlite3.Cursor:
            result = original(query, values)
            if query.startswith("INSERT INTO replay"):
                raise sqlite3.IntegrityError("F73 real conversation rollback")
            return result

        with monkeypatch.context() as patch:
            patch.setattr(store, "_execute", fail)
            assert owner.act("talk").status == "SAVE_UNAVAILABLE"
        assert state(owner) == before
        retried = owner.retry()
        assert retried.view is not None and (retried.view.tick, retried.view.npc_cell) == (2, 6)
        assert not any(
            type(e.payload) is NpcPatrolled for e in owner.owner.last_publication().facts
        )
        replay(owner)
    finally:
        owner.close()


@contextmanager
def talk_pause_pipe(path: Path) -> Iterator[PipeClient]:
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
            "--npc-talk-pause",
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
            pytest.fail("owned talk-pause Brain did not stop on EOF")
        if process.stdout is not None:
            process.stdout.close()
        errors = b"" if process.stderr is None else process.stderr.read()
        if process.stderr is not None:
            process.stderr.close()
        assert process.returncode == 0, errors.decode("utf-8", errors="replace")


def test_real_pipe_talk_pause_load_reconnect_and_readonly_query(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with talk_pause_pipe(path) as pipe:
        pipe.send("down")
        result = object_value(pipe.send("talk")["update"])
        assert object_value(result["view"])["npc_cell"] == "6"
        pipe.send("save")
        pipe.send("wait")
        result = object_value(pipe.send("wait")["update"])
        assert object_value(result["view"])["npc_cell"] == "7"
        loaded = object_value(pipe.send("load")["update"])
        branch = Path(text_value(loaded["working_path"]))
        assert object_value(loaded["view"])["npc_cell"] == "6"
    with talk_pause_pipe(branch) as pipe:
        pipe.send("attach")
        before = branch.read_bytes()
        result = object_value(pipe.send("activity")["update"])
        assert result["status"] == "ACTIVITY_INSPECTED" and branch.read_bytes() == before
        assert object_value(result["view"])["npc_cell"] == "6"
        result = object_value(pipe.send("talk")["update"])
        assert object_value(result["view"])["npc_cell"] == "6"


def test_actual_worker_and_withdrawn_tk_selection_and_position(
    tk_host: tk.Tk, tmp_path: Path
) -> None:
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
        npc_talk_pause=True,
    )
    try:
        worker.request("down").result(timeout=10)
        for _ in range(3):
            assert _view(worker.request("talk").result(timeout=10)).npc_cell == 6
        worker.request("wait").result(timeout=10)
        assert _view(worker.request("wait").result(timeout=10)).npc_cell == 7
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
        npc_talk_pause=True,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        assert screen.mode_label == "NPC 대화 대기·순찰·호출 지원·물자·반복 작업·기억 모드"
        for action in ("down", "talk", "talk", "talk"):
            _click(screen, action)
        assert screen.last_update is not None and _view(screen.last_update).npc_cell == 6
        _click(screen, "wait")
        _click(screen, "wait")
        assert _view(screen.last_update).npc_cell == 7
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())


def test_cli_selection_rejects_missing_patrol_before_tk() -> None:
    with pytest.raises(ValueError, match="^NPC_TALK_PAUSE_CONTENT$"):
        client_main(["--npc-talk-pause"])
