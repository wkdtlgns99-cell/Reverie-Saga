from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from typing import Iterator, cast

import pytest

from app.client import PlayWindow
from app.client_session import ClientSession
from app.client_worker import ClientWorker
from app.headless import replay_runner
from app.npc_activity import recent_activity
from app.npc_memory import memory_bundle
from app.npc_work import work_bundle
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.replay import ReplayFixture
from domain.canonical import array_value, object_value, text_value
from domain.npc_work import ProvisionsRecord
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_engine_bridge import PipeClient
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_quest import GOAL
from tests.integration.test_unity_wait_duration import send_seconds


def session(path: Path, *, work: bool = True) -> ClientSession:
    selected = approved_content()
    return ClientSession(
        path, selected.definition.layout, quest_content=selected, npc_memory=True, npc_work=work
    )


def stock(owner: ClientSession) -> int:
    return next(
        r.stock for r in owner.owner.snapshot().components if isinstance(r, ProvisionsRecord)
    )


def test_long_wait_partitioned_time_exact_facts_capacity_and_no_player_grant(
    tmp_path: Path,
) -> None:
    long, split = session(tmp_path / "long/game.sqlite"), session(tmp_path / "split/game.sqlite")
    try:
        initial = long.update()
        assert stock(long) == 0
        assert long.act("talk").status == "OUT_OF_RANGE"
        assert stock(long) == 0 and long.update().view == initial.view
        produced = long.act("wait", seconds=16)
        assert produced.status == "COMMITTED" and stock(long) == 3
        records = recent_activity(
            long.owner.retained_segment(),
            approved_content().definition.layout.npc_id,
            content=approved_content(),
            current=DurableCheckpoint(long.owner.snapshot(), long.owner.protocol()),
            npc_work=True,
        )
        # Recent8 retains the final two production facts among the interleaved bells.
        assert sorted((r.tick, r.count) for r in records if r.kind == "provision") == [
            (8, 2),
            (12, 3),
        ]
        expected = [0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3]
        all_records = []
        for amount in expected:
            result = split.act("wait")
            assert result.status == "COMMITTED"
            assert stock(split) == amount
            if any("물자 1개를 준비" in line for line in result.messages):
                assert result.view is not None
                all_records.append(result.view.tick)
        assert all_records == [4, 8, 12]
        assert long.owner.snapshot() == split.owner.snapshot()
        assert (produced.quest_stage, produced.quest_reward) == (0, 0)
        assert produced.view is not None and initial.view is not None
        assert (produced.view.actor_hp, produced.view.enemy_hp, produced.view.stamina) == (3, 5, 2)
        before = long.owner.snapshot(), long.owner.protocol()
        retry = long.retry()
        assert retry.view == produced.view and not any("공동 비축" in m for m in retry.messages)
        assert (long.owner.snapshot(), long.owner.protocol()) == before
        assert not any("물자 1개를 준비" in m for m in long.act("wait", seconds=16).messages)
        assert stock(long) == 3
        for owner in (long, split):
            segment = owner.owner.retained_segment()
            fixture = ReplayFixture(
                segment.checkpoint.core, segment.checkpoint.protocol, segment.trace
            )
            assert (
                replay_runner(fixture, bundles=(work_bundle(approved_content()),)).run(
                    segment.trace
                )
                == ()
            )
    finally:
        long.close()
        split.close()


def test_save_rewind_restart_and_readonly_inspection(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("wait", seconds=4)
        owner.save("slot01")
        owner.act("wait", seconds=8)
        assert stock(owner) == 3
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        preview = owner.inspect_slot("slot01")
        assert "물자 1/3개" in preview.messages[-1]
        inspected = owner.inspect_activity()
        assert any("12초: 공동 비축 물자" in m for m in inspected.messages)
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
        selected = approved_content()
        segment = owner.owner.retained_segment()
        corrupted = replace(
            segment,
            trace=replace(
                segment.trace,
                steps=(
                    replace(segment.trace.steps[0], expected_facts_hash="0" * 64),
                    *segment.trace.steps[1:],
                ),
            ),
        )
        with pytest.raises(SaveError, match="NPC_ACTIVITY_SOURCE"):
            recent_activity(
                corrupted,
                selected.definition.layout.npc_id,
                content=selected,
                current=DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol()),
                npc_work=True,
            )
        owner.load("slot01")
        assert stock(owner) == 1
        assert any("4초: 공동 비축 물자" in m for m in owner.inspect_activity().messages)
        assert not any("8초:" in m for m in owner.inspect_activity().messages)
        working = owner.owner.working_path
    finally:
        owner.close()
    resumed = session(working)
    try:
        assert stock(resumed) == 1
        resumed.act("wait", seconds=4)
        assert stock(resumed) == 2
    finally:
        resumed.close()


def test_quest_travel_combat_return_reward_and_work_do_not_interfere(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        for action in GOAL:
            assert owner.act(action).status == "COMMITTED"
        assert stock(owner) == 2
        owner.act("wait", seconds=4)
        owner.act("left")
        returned = owner.act("talk")
        assert returned.quest_stage == 3 and returned.quest_reward == 1
        assert returned.messages[-1] == "NPC 공동 비축: 물자 3/3개 · 가득 차 작업을 멈췄습니다."
        memory = owner.inspect_memory()
        assert len(memory.messages) == 2 and "직접 본 기억은 아닙니다" in memory.messages[1]
        assert not any("공동 비축" in m for m in owner.retry().messages)
        assert owner.act("talk").quest_reward == 1
    finally:
        owner.close()


@pytest.mark.parametrize("old_work,new_work", ((False, True), (True, False)))
def test_incompatible_save_rejects_without_mutation(
    tmp_path: Path, old_work: bool, new_work: bool
) -> None:
    path = tmp_path / "game.sqlite"
    owner = session(path, work=old_work)
    owner.act("wait", seconds=4)
    owner.close()
    before = path.read_bytes()
    with pytest.raises(SaveError, match="UNSUPPORTED_RULESET"):
        session(path, work=new_work)
    assert path.read_bytes() == before
    # The old rules remain independently resumable with their original descriptor.
    resumed = session(path, work=old_work)
    resumed.close()
    assert memory_bundle(approved_content()).feature_id == "quest.harbor-memory-v1"


@pytest.mark.parametrize("flag", (1, "1", None))
def test_work_type_rejects_before_worker_or_save(tmp_path: Path, flag: object) -> None:
    selected = approved_content()
    path = tmp_path / "game.sqlite"
    for factory in (ClientSession, ClientWorker):
        with pytest.raises(ValueError, match="^NPC_WORK_CONTENT$"):
            factory(
                path,
                selected.definition.layout,
                quest_content=selected,
                npc_memory=True,
                npc_work=cast(bool, flag),
            )
        with pytest.raises(ValueError, match="^NPC_WORK_CONTENT$"):
            factory(path, selected.definition.layout, quest_content=selected, npc_work=True)
    assert not path.exists()


@contextmanager
def work_pipe(path: Path) -> Iterator[PipeClient]:
    root = Path(__file__).resolve().parents[2]
    selected = approved_content()
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(root / "src")
    environment["PYTHONUTF8"] = "1"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "app.engine_bridge",
            "--working",
            str(path),
            "--catalog",
            str(root / "content/narratives.json"),
            "--catalog-sha256",
            hashlib.sha256((root / "content/narratives.json").read_bytes()).hexdigest(),
            "--scenario",
            "harbor",
            "--quest-catalog",
            str(root / "content/dialogue/harbor-memory-v1.json"),
            "--quest-sha256",
            selected.catalog_sha256,
            "--npc-memory",
            "--npc-work",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=root,
        env=environment,
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
            pytest.fail("owned work Brain did not stop on EOF")
        if process.stdout is not None:
            process.stdout.close()
        errors = b"" if process.stderr is None else process.stderr.read()
        if process.stderr is not None:
            process.stderr.close()
        assert process.returncode == 0, errors.decode("utf-8", errors="replace")


def test_real_binary_pipe_load_reconnect_and_current_stock(tmp_path: Path) -> None:
    working = tmp_path / "game.sqlite"
    with work_pipe(working) as pipe:
        assert object_value(pipe.send("attach")["update"])["status"] == "ATTACHED"
        pipe.send("down")
        send_seconds(pipe, "wait", "4")
        talked = object_value(pipe.send("talk")["update"])
        assert "물자 1/3개" in text_value(array_value(talked["messages"])[-1])
        pipe.send("save")
        send_seconds(pipe, "wait", "8")
        returned = object_value(pipe.send("talk")["update"])
        assert "물자 3/3개" in text_value(array_value(returned["messages"])[-1])
        pipe.send("load")
        loaded = object_value(pipe.send("slot_inspect")["update"])
        assert "물자 1/3개" in text_value(array_value(loaded["messages"])[-1])
        working = Path(text_value(loaded["working_path"]))
    with work_pipe(working) as pipe:
        pipe.send("attach")
        resumed = object_value(pipe.send("talk")["update"])
        assert "물자 1/3개" in text_value(array_value(resumed["messages"])[-1])


def test_actual_tk_work_return_activity_and_rewind(tk_host: tk.Tk, tmp_path: Path) -> None:
    selected = approved_content()
    panel = tk.Toplevel(tk_host)
    panel.withdraw()
    screen = PlayWindow(
        panel,
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_work=True,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        for action in ("down", "wait", "wait", "wait", "talk"):
            _click(screen, action)
        assert screen.last_update is not None
        assert "물자 1/3개" in screen.last_update.messages[-1]
        _click(screen, "save")
        screen.worker.request("wait", seconds=8).result(timeout=30)
        _click(screen, "talk")
        assert "물자 3/3개" in screen.last_update.messages[-1]
        _click(screen, "load")
        _click(screen, "talk")
        assert "물자 1/3개" in screen.last_update.messages[-1]
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
