"""Actual answered calls hold a patrol turn without persisting a later pause."""

from pathlib import Path

from app.client_session import ClientSession
from domain.watch import ReplyRecord
from tests.integration.test_memory_client_route import approved_content

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
from app.engine_bridge import main as bridge_main
from app.headless import replay_runner
from app.npc_cycle import cycle_bundle
from contracts.client import ClientAction
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.replay import ReplayFixture
from contracts.skeleton import FeatureBundle
from domain.canonical import array_value, object_value, text_value
from domain.npc_cycle import CycleRecord, state_at
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_durable_turn import UncertainPort
from tests.integration.test_engine_bridge import PipeClient
from tests.integration.test_quest_patrol import report_blocked, state, view
from tests.integration.test_quest_patrol import session as old_session


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
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
    )


POLICY = (
    "NPC 응답 대기 · 호출에 답한 턴에는 이동을 멈추고, 다음 행동 시점에 순찰 계획을 다시 따릅니다."
)


def bundle() -> FeatureBundle:
    return cycle_bundle(
        approved_content(),
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
    )


def replay(owner: ClientSession) -> None:
    segment = owner.owner.retained_segment()
    fixture = ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace)
    assert replay_runner(fixture, bundles=(bundle(),)).run(segment.trace) == ()


def ready(owner: ClientSession) -> None:
    for action in ("down", "talk", "up"):
        assert owner.act(action).status == "COMMITTED"
    assert (view(owner.update()).tick, view(owner.update()).npc_cell) == (3, 6)


def hold_neighbor(owner: ClientSession) -> None:
    ready(owner)
    for action in ("bell", "wait", "bell"):
        assert owner.act(action).status == "COMMITTED"
    assert view(owner.act("wait", seconds=2)).npc_cell == 7
    owner.act("wait")
    assert (view(owner.act("bell")).tick, view(owner.update()).npc_cell) == (10, 7)


def test_odd_answer_does_not_pause_later_even_wake(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        ready(owner)
        assert view(owner.act("wait")).npc_cell == 7
        answered = owner.act("bell")
        assert (view(answered).tick, view(answered).npc_cell) == (5, 7)
        resumed = owner.act("wait")
        assert (view(resumed).tick, view(resumed).npc_cell) == (6, 6)
        replay(owner)
    finally:
        owner.close()


def test_repeated_answers_and_supply_balance_retain_existing_rules(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        hold_neighbor(owner)
        assert view(owner.act("wait", seconds=2)).npc_cell == 6
        records = owner.owner.snapshot().components
        assert tuple(r.count for r in records if type(r) is ReplyRecord) == (3,)
        assert tuple(r.state for r in records if type(r) is CycleRecord) == (state_at(12),)
        assert owner.update().quest_reward == 0
        replay(owner)
    finally:
        owner.close()


def test_resumed_goal_still_waits_for_an_occupied_destination(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        hold_neighbor(owner)
        owner.act("down")
        blocked = owner.act("down")
        assert (view(blocked).tick, view(blocked).npc_cell) == (12, 7)
        owner.act("up")
        resumed = owner.act("wait")
        assert (view(resumed).tick, view(resumed).npc_cell) == (14, 6)
        replay(owner)
    finally:
        owner.close()


def test_reported_return_waits_for_actual_answer_then_resumes(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        report_blocked(owner)
        owner.act("up")
        answered = owner.act("bell")
        assert (view(answered).tick, view(answered).npc_cell) == (24, 7)
        assert answered.quest_reward == 1
        before = state(owner)
        assert POLICY in owner.inspect_activity().messages
        assert state(owner) == before
        returned = owner.act("wait", seconds=2)
        assert (view(returned).tick, view(returned).npc_cell) == (26, 6)
        replay(owner)
    finally:
        owner.close()


def test_rejected_talk_and_unheard_quest_create_no_lasting_pause(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        before = state(owner)
        assert owner.act("talk").status == "OUT_OF_RANGE"
        assert state(owner) == before
        assert view(owner.act("bell")).npc_cell == 6
        assert view(owner.act("bell")).npc_cell == 6
        before = state(owner)
        assert POLICY in owner.inspect_activity().messages
        assert state(owner) == before
        replay(owner)
    finally:
        owner.close()


def test_previous_save_load_restart_and_exact_retry_have_no_saved_pause(tmp_path: Path) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        ready(owner)
        owner.act("bell")
        assert owner.save("slot01").status == "SAVED"
        assert view(owner.act("wait", seconds=2)).npc_cell == 7
        assert owner.save("slot01").status == "SAVED"
        before = state(owner)
        preview = owner.inspect_slot("slot01", previous=True)
        assert preview.messages[-2:] == (
            "현재 NPC 위치 · 옆 작업 지점입니다.",
            "선택 저장 NPC 위치 · 원래 작업 지점입니다.",
        )
        assert state(owner) == before
        loaded = owner.load("slot01", previous=True)
        assert (view(loaded).tick, view(loaded).npc_cell) == (4, 6)
        branch = owner.owner.working_path
    finally:
        owner.close()
    owner = session(branch)
    try:
        before = state(owner)
        assert POLICY in owner.inspect_activity().messages
        assert state(owner) == before
        assert view(owner.act("wait", seconds=2)).npc_cell == 7
        before = state(owner)
        assert not any(line.startswith("NPC 응답 대기") for line in owner.retry().messages)
        assert state(owner) == before
        replay(owner)
    finally:
        owner.close()


def test_compact_checkpoint_preserves_reply_but_no_pending_hold(tmp_path: Path) -> None:
    source = tmp_path / "source/game.sqlite"
    owner = session(source)
    try:
        ready(owner)
        owner.act("bell")
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        source_bytes = source.read_bytes()
    finally:
        owner.close()
    compact = tmp_path / "compact/game.sqlite"
    create_durable(compact, checkpoint, bundles=(bundle(),)).close()
    owner = session(compact)
    try:
        assert not owner.owner.retained_segment().trace.steps
        assert tuple(
            r.count for r in owner.owner.snapshot().components if type(r) is ReplyRecord
        ) == (1,)
        assert (view(owner.act("wait", seconds=2)).tick, view(owner.update()).npc_cell) == (6, 7)
        replay(owner)
    finally:
        owner.close()
    assert source.read_bytes() == source_bytes


@pytest.mark.parametrize("commit", (False, True))
def test_uncertain_answer_commit_preserves_only_actual_reply_and_pose(
    tmp_path: Path, commit: bool
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        ready(owner)
        before = state(owner)
        store = owner.owner._attachment.store
        port = UncertainPort(store, commit=commit)
        owner.owner._attachment.owner._driver._commit_port = port
        result = owner.act("bell")
        assert port.persist_calls == port.recover_calls == 1
        assert result.status == ("COMMITTED" if commit else "SAVE_UNAVAILABLE")
        assert (view(result).tick, view(result).npc_cell) == (4 if commit else 3, 6)
        if not commit:
            assert state(owner) == before
        else:
            after = state(owner)
            assert not any(line.startswith("NPC 응답 대기") for line in owner.retry().messages)
            assert state(owner) == after
        assert store.load() == DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()


def test_sql_rollback_then_retry_commits_one_answer_and_one_hold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        ready(owner)
        before = state(owner)
        store = owner.owner._attachment.store
        original = store._execute

        def fail(
            query: str, values: tuple[None | int | float | str | bytes, ...] = ()
        ) -> sqlite3.Cursor:
            result = original(query, values)
            if query.startswith("INSERT INTO replay"):
                raise sqlite3.IntegrityError("F77 actual answered-call rollback")
            return result

        with monkeypatch.context() as patch:
            patch.setattr(store, "_execute", fail)
            assert owner.act("bell").status == "SAVE_UNAVAILABLE"
        assert state(owner) == before
        retried = owner.retry()
        assert (view(retried).tick, view(retried).npc_cell) == (4, 6)
        assert tuple(
            r.count for r in owner.owner.snapshot().components if type(r) is ReplyRecord
        ) == (1,)
        assert view(owner.act("wait", seconds=2)).npc_cell == 7
        replay(owner)
    finally:
        owner.close()


@pytest.mark.parametrize("old_first", (False, True))
def test_feature_pins_reject_cross_mode_without_save_mutation(
    tmp_path: Path, old_first: bool
) -> None:
    source = tmp_path / "game.sqlite"
    owner = old_session(source) if old_first else session(source)
    try:
        owner.act("down")
        owner.act("talk")
        before = source.read_bytes()
    finally:
        owner.close()
    with pytest.raises(SaveError, match="UNSUPPORTED_RULESET"):
        if old_first:
            session(source)
        else:
            old_session(source)
    assert source.read_bytes() == before


@contextmanager
def call_pipe(path: Path) -> Iterator[PipeClient]:
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
            "--npc-quest-patrol",
            "--npc-call-pause",
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
            pytest.fail("owned F77Brain did not stop on EOF")
        if process.stdout is not None:
            process.stdout.close()
        errors = b"" if process.stderr is None else process.stderr.read()
        if process.stderr is not None:
            process.stderr.close()
        assert process.returncode == 0, errors.decode("utf-8", errors="strict")


def test_real_framed_brain_answer_save_load_and_reconnect(tmp_path: Path) -> None:
    source = tmp_path / "game.sqlite"
    with call_pipe(source) as pipe:
        for action in ("down", "talk", "up"):
            pipe.send(action)
        result = object_value(pipe.send("bell")["update"])
        assert object_value(result["view"])["npc_cell"] == "6"
        pipe.send("save")
        pipe.send("wait")
        result = object_value(pipe.send("wait")["update"])
        assert object_value(result["view"])["npc_cell"] == "7"
        loaded = object_value(pipe.send("load")["update"])
        branch = Path(text_value(loaded["working_path"]))
    with call_pipe(branch) as pipe:
        before = branch.read_bytes()
        result = object_value(pipe.send("activity")["update"])
        assert POLICY in array_value(result["messages"]) and branch.read_bytes() == before
        pipe.send("wait")
        result = object_value(pipe.send("wait")["update"])
        assert object_value(result["view"])["npc_cell"] == "7"


def test_worker_and_withdrawn_tk_forward_answer_hold_and_mode(
    tk_host: tk.Tk, tmp_path: Path
) -> None:
    content = approved_content()
    worker = ClientWorker(
        tmp_path / "worker/game.sqlite",
        content.definition.layout,
        quest_content=content,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
    )
    try:
        for action in ("down", "talk", "up"):
            worker.request(action).result(timeout=10)
        assert view(worker.request("bell").result(timeout=10)).npc_cell == 6
        assert POLICY in worker.inspect_activity().result(timeout=10).messages
        assert view(worker.request("wait", seconds=2).result(timeout=10)).npc_cell == 7
    finally:
        worker.join()
    panel = tk.Toplevel(tk_host)
    panel.withdraw()
    screen = PlayWindow(
        panel,
        tmp_path / "tk/game.sqlite",
        content.definition.layout,
        quest_content=content,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        assert (
            screen.mode_label
            == "NPC 호출 응답 대기·의뢰 순찰·대화 대기·호출 지원·물자·반복 작업·기억 모드"
        )
        actions: tuple[ClientAction, ...] = ("down", "talk", "up", "bell")
        for ui_action in actions:
            _click(screen, ui_action)
        assert screen.last_update is not None and view(screen.last_update).npc_cell == 6
        _click(screen, "wait")
        _click(screen, "wait")
        assert screen.last_update is not None and view(screen.last_update).npc_cell == 7
    finally:
        screen.close()
        panel.destroy()


def test_cli_parent_error_is_explicit_before_graphical_startup() -> None:
    with pytest.raises(ValueError, match="^NPC_CALL_PAUSE_CONTENT$"):
        client_main(["--npc-call-pause"])


def test_bridge_cli_rejects_missing_parent_without_creating_save(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    catalog = root / "content/narratives.json"
    path = tmp_path / "absent/game.sqlite"
    assert (
        bridge_main(
            [
                "--working",
                str(path),
                "--catalog",
                str(catalog),
                "--catalog-sha256",
                hashlib.sha256(catalog.read_bytes()).hexdigest(),
                "--scenario",
                "harbor",
                "--npc-call-pause",
            ]
        )
        == 1
    )
    assert not path.parent.exists()


def test_actual_even_answer_holds_then_next_actual_wake_resumes(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        for action in ("down", "talk", "up"):
            assert owner.act(action).status == "COMMITTED"
        answered = owner.act("bell")
        assert answered.view is not None
        assert (answered.view.tick, answered.view.npc_cell) == (4, 6)
        replies = tuple(
            record.count
            for record in owner.owner.snapshot().components
            if type(record) is ReplyRecord
        )
        assert replies == (1,)
        resumed = owner.act("wait", seconds=2)
        assert resumed.view is not None
        assert (resumed.view.tick, resumed.view.npc_cell) == (6, 7)
    finally:
        owner.close()
