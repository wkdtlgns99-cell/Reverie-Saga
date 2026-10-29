"""Quest-aware patrol acts only on the NPC's own heard acceptance/report."""

from pathlib import Path
from app.client_session import ClientSession
from tests.integration.test_memory_client_route import approved_content

from contextlib import contextmanager
from dataclasses import replace
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
from contracts.client import ClientAction, ClientUpdate, ClientView
from contracts.npc_patrol import NpcPatrolled
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.replay import ReplayFixture
from contracts.skeleton import FeatureBundle
from domain.canonical import array_value, object_value, text_value
from domain.npc_memory import NpcQuestMemoryRecord
from domain.watch import WatchNpcRecord
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_durable_turn import UncertainPort
from tests.integration.test_engine_bridge import PipeClient


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
        npc_quest_patrol=True,
    )


def test_unheard_waits_then_actual_acceptance_starts_patrol(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        waited = owner.act("wait", seconds=4)
        assert waited.view is not None and (waited.view.tick, waited.view.npc_cell) == (4, 6)
        assert not any("NPC가 공동 작업 구역을 순찰" in line for line in waited.messages)
        owner.act("down")
        accepted = owner.act("talk")
        assert accepted.view is not None and (accepted.view.tick, accepted.view.npc_cell) == (6, 6)
        resumed = owner.act("wait", seconds=2)
        assert resumed.view is not None and (resumed.view.tick, resumed.view.npc_cell) == (8, 7)
    finally:
        owner.close()


def test_own_knowledge_goal_plan_is_read_only(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        result = owner.inspect_activity()
        assert (
            "NPC 의뢰 순찰 계획 · 수락을 직접 듣기 전에는 원래 작업 지점에서 기다립니다."
            in result.messages
        )
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
    finally:
        owner.close()


PREFIX = "NPC 의뢰 순찰 계획 · "
ACCEPTED = PREFIX + "수락을 직접 들어 공동 작업 구역 순찰을 목표로 합니다."
RETURNING = PREFIX + "완료 보고를 들어 원래 작업 지점으로 돌아갈 준비를 합니다."
HOME = PREFIX + "완료 보고를 들어 원래 작업 지점에서 기다립니다."


def view(update: ClientUpdate) -> ClientView:
    assert update.view is not None
    return update.view


def bundle() -> FeatureBundle:
    return cycle_bundle(
        approved_content(),
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
    )


def state(owner: ClientSession) -> tuple[object, ...]:
    return (
        owner.owner.snapshot(),
        owner.owner.protocol(),
        owner.owner.retained_segment(),
        owner.owner.working_path.read_bytes(),
    )


def replay(owner: ClientSession) -> None:
    segment = owner.owner.retained_segment()
    fixture = ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace)
    assert replay_runner(fixture, bundles=(bundle(),)).run(segment.trace) == ()


def report_blocked(owner: ClientSession) -> ClientUpdate:
    actions: tuple[ClientAction, ...] = (
        "wait",
        "wait",
        "wait",
        "wait",
        "down",
        "talk",
        "wait",
        "wait",
        "down",
        "bell",
        "talk",
        "right",
        "attack",
        "attack",
        "rest",
        "attack",
        "up",
        "left",
        "down",
        "talk",
        "wait",
        "wait",
    )
    for tick, action in enumerate(actions, 1):
        result = owner.act(action)
        assert result.status == "COMMITTED", (tick, action, result.status, result.messages)
        assert view(result).tick == tick
        if tick <= 6:
            assert view(result).npc_cell == 6
        if tick == 8:
            assert view(result).npc_cell == 7
        if tick == 10:
            assert view(result).gate_open
        if tick == 18:
            assert view(result).enemy_hp == 0 and view(result).npc_cell == 7
            assert ACCEPTED in owner.inspect_activity().messages
        if tick >= 20:
            assert view(result).npc_cell == 7
            assert result.quest_reward == 1
            assert RETURNING in owner.inspect_activity().messages
            assert not any(
                type(e.payload) is NpcPatrolled for e in owner.owner.last_publication().facts
            )
    return result


def test_full_knowledge_timeline_blocked_return_and_no_new_pending_state(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        reported = report_blocked(owner)
        assert view(reported).actor_cell == 6
        assert len(owner.owner.snapshot().pending) == 1
        assert tuple(
            r.known_phase
            for r in owner.owner.snapshot().components
            if type(r) is NpcQuestMemoryRecord
        ) == ("reported",)
        owner.act("up")
        arrived = owner.act("wait")
        assert (view(arrived).tick, view(arrived).npc_cell) == (24, 6)
        assert tuple(
            e.due_tick
            for e in owner.owner.last_publication().facts
            if type(e.payload) is NpcPatrolled
        ) == (24,)
        assert HOME in owner.inspect_activity().messages
        stayed = owner.act("wait", seconds=16)
        assert (view(stayed).tick, view(stayed).npc_cell) == (40, 6)
        assert not any(
            type(e.payload) is NpcPatrolled for e in owner.owner.last_publication().facts
        )
        replay(owner)
    finally:
        owner.close()


def test_reported_neighbor_save_reconnect_compact_and_physical_return(tmp_path: Path) -> None:
    source = tmp_path / "source/game.sqlite"
    owner = session(source)
    try:
        report_blocked(owner)
        assert owner.save("slot01").status == "SAVED"
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        before = state(owner)
        inspected = owner.inspect_slot("slot01")
        assert inspected.messages[-3:] == (
            "NPC 순찰 위치 비교 · 현재 22초 / 선택 저장 22초",
            "현재 NPC 위치 · 옆 작업 지점입니다.",
            "선택 저장 NPC 위치 · 옆 작업 지점입니다.",
        )
        assert state(owner) == before
    finally:
        owner.close()
    compact = tmp_path / "compact/game.sqlite"
    create_durable(compact, checkpoint, bundles=(bundle(),)).close()
    for path in (source, compact):
        owner = session(path)
        try:
            assert RETURNING in owner.inspect_activity().messages
            assert view(owner.act("wait", seconds=2)).npc_cell == 7
            owner.act("up")
            assert view(owner.act("wait")).npc_cell == 6
            assert HOME in owner.inspect_activity().messages
            replay(owner)
        finally:
            owner.close()


def test_new_checkpoint_cross_invariant_preserves_older_policy(tmp_path: Path) -> None:
    from tests.integration.test_talk_pause_patrol import bundle as older_bundle

    owner = session(tmp_path / "game.sqlite")
    try:
        core, protocol = owner.owner.snapshot(), owner.owner.protocol()
        changed = replace(
            core,
            components=tuple(
                replace(r, cell=7) if type(r) is WatchNpcRecord else r for r in core.components
            ),
        )
        new_policy, old_policy = bundle().checkpoint_policy, older_bundle().checkpoint_policy
        assert new_policy is not None and old_policy is not None
        old_policy.validate(changed, protocol)
        with pytest.raises(ValueError, match="^NPC_QUEST_PATROL_CHECKPOINT$"):
            new_policy.validate(changed, protocol)
        new_policy.validate(core, protocol)
    finally:
        owner.close()


def test_repeated_talk_rejected_talk_quiet_retry_and_plan_order(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        before = state(owner)
        assert owner.act("talk").status == "OUT_OF_RANGE"
        assert state(owner) == before
        owner.act("down")
        for tick in (2, 3, 4):
            result = owner.act("talk")
            assert (view(result).tick, view(result).npc_cell) == (tick, 6)
            assert result.messages.count(ACCEPTED) == 1
            plan = result.messages.index(ACCEPTED)
            support = next(
                i for i, line in enumerate(result.messages) if line.startswith("NPC 지원 계획 · ")
            )
            assert plan < support
        before = state(owner)
        retry = owner.retry()
        assert not any(line.startswith(PREFIX) for line in retry.messages)
        assert state(owner) == before
        assert view(owner.act("wait", seconds=2)).npc_cell == 7
        replay(owner)
    finally:
        owner.close()


@pytest.mark.parametrize("commit", (False, True))
def test_uncertain_acceptance_persists_only_actual_knowledge(tmp_path: Path, commit: bool) -> None:
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
        assert (view(result).tick, view(result).npc_cell) == (2 if commit else 1, 6)
        if not commit:
            assert state(owner) == before
        else:
            assert ACCEPTED in result.messages
            after = state(owner)
            assert not any(line.startswith(PREFIX) for line in owner.retry().messages)
            assert state(owner) == after
        assert store.load() == DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()


def test_sql_failure_rolls_back_goal_and_retry_hears_acceptance(
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
                raise sqlite3.IntegrityError("F74 acceptance rollback")
            return result

        with monkeypatch.context() as patch:
            patch.setattr(store, "_execute", fail)
            assert owner.act("talk").status == "SAVE_UNAVAILABLE"
        assert state(owner) == before
        retried = owner.retry()
        assert (view(retried).tick, view(retried).npc_cell) == (2, 6)
        assert ACCEPTED in retried.messages
        replay(owner)
    finally:
        owner.close()


@contextmanager
def quest_pipe(path: Path) -> Iterator[PipeClient]:
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
            pytest.fail("owned quest-patrol Brain did not stop on EOF")
        if process.stdout is not None:
            process.stdout.close()
        errors = b"" if process.stderr is None else process.stderr.read()
        if process.stderr is not None:
            process.stderr.close()
        assert process.returncode == 0, errors.decode("utf-8", errors="replace")


def test_real_framed_brain_save_load_query_reconnect(tmp_path: Path) -> None:
    source = tmp_path / "game.sqlite"
    with quest_pipe(source) as pipe:
        result = object_value(pipe.send("wait")["update"])
        assert object_value(result["view"])["npc_cell"] == "6"
        result = object_value(pipe.send("wait")["update"])
        assert object_value(result["view"])["npc_cell"] == "6"
        pipe.send("down")
        result = object_value(pipe.send("talk")["update"])
        assert ACCEPTED in array_value(result["messages"])
        pipe.send("save")
        pipe.send("wait")
        result = object_value(pipe.send("wait")["update"])
        assert object_value(result["view"])["npc_cell"] == "7"
        loaded = object_value(pipe.send("load")["update"])
        branch = Path(text_value(loaded["working_path"]))
    with quest_pipe(branch) as pipe:
        pipe.send("attach")
        before = branch.read_bytes()
        result = object_value(pipe.send("activity")["update"])
        assert ACCEPTED in array_value(result["messages"]) and branch.read_bytes() == before


def test_worker_and_withdrawn_tk_goal_selection(tk_host: tk.Tk, tmp_path: Path) -> None:
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
        npc_quest_patrol=True,
    )
    try:
        assert view(worker.request("wait").result(timeout=10)).npc_cell == 6
        assert view(worker.request("wait").result(timeout=10)).npc_cell == 6
        worker.request("down").result(timeout=10)
        assert ACCEPTED in worker.request("talk").result(timeout=10).messages
        worker.request("wait").result(timeout=10)
        assert view(worker.request("wait").result(timeout=10)).npc_cell == 7
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
        npc_quest_patrol=True,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        assert screen.mode_label == "NPC 의뢰 순찰·대화 대기·호출 지원·물자·반복 작업·기억 모드"
        for action in ("wait", "wait", "down", "talk"):
            _click(screen, action)
        assert screen.last_update is not None
        assert ACCEPTED in screen.last_update.messages and view(screen.last_update).npc_cell == 6
        _click(screen, "wait")
        _click(screen, "wait")
        assert view(screen.last_update).npc_cell == 7
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())


def test_cli_rejects_new_selection_before_tk() -> None:
    with pytest.raises(ValueError, match="^NPC_QUEST_PATROL_CONTENT$"):
        client_main(["--npc-quest-patrol"])


@pytest.mark.parametrize(
    "mode", ("memory", "work", "cycle", "aid", "supply", "call", "patrol", "talk")
)
def test_new_save_rejects_all_eight_older_rulesets_without_overwrite(
    tmp_path: Path, mode: str
) -> None:
    source = tmp_path / "game.sqlite"
    owner = session(source)
    owner.close()
    before = source.read_bytes()
    selected = approved_content()
    with pytest.raises(SaveError, match="UNSUPPORTED_RULESET"):
        ClientSession(
            source,
            selected.definition.layout,
            quest_content=selected,
            npc_memory=True,
            npc_work=mode == "work",
            npc_cycle=mode in ("cycle", "aid", "supply", "call", "patrol", "talk"),
            npc_aid=mode in ("aid", "supply", "call", "patrol", "talk"),
            npc_supply_aid=mode in ("supply", "call", "patrol", "talk"),
            npc_call_aid=mode in ("call", "patrol", "talk"),
            npc_patrol=mode in ("patrol", "talk"),
            npc_talk_pause=mode == "talk",
        )
    assert source.read_bytes() == before
