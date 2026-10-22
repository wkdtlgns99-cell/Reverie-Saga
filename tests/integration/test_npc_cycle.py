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
from app.headless import replay_runner, state_io
from app.npc_cycle import cycle_bundle
from contracts.persistence import SaveError
from contracts.persistence import DurableCheckpoint
from contracts.replay import ReplayFixture
from domain.canonical import array_value, object_value, text_value
from domain.npc_cycle import CycleRecord, Supply
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_engine_bridge import PipeClient
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_quest import GOAL
from tests.integration.test_unity_wait_duration import send_seconds
from tests.integration.test_durable_turn import UncertainPort


def session(path: Path) -> ClientSession:
    selected = approved_content()
    return ClientSession(
        path, selected.definition.layout, quest_content=selected, npc_memory=True, npc_cycle=True
    )


def cycle(owner: ClientSession) -> CycleRecord:
    return next(r for r in owner.owner.snapshot().components if isinstance(r, CycleRecord))


def test_real_partitioned_time_offscreen_cap_order_replay_and_retry(tmp_path: Path) -> None:
    long, split = session(tmp_path / "long/game.sqlite"), session(tmp_path / "split/game.sqlite")
    try:
        initial = long.owner.snapshot(), long.owner.protocol(), long.owner.working_path.read_bytes()
        assert long.act("talk").status == "OUT_OF_RANGE"
        assert (
            long.owner.snapshot(),
            long.owner.protocol(),
            long.owner.working_path.read_bytes(),
        ) == initial
        for amount in (16, 4, 10, 2, 8):
            assert long.act("wait", seconds=amount).status == "COMMITTED"
        observed: list[tuple[int, str]] = []
        for tick in range(1, 41):
            update = split.act("wait")
            assert update.status == "COMMITTED"
            assert not any("설명이 준비되지" in m for m in update.messages)
            observed.extend(
                (tick, "준비" if "준비했습니다" in m else "사용")
                for m in update.messages
                if "NPC 작업 기억" in m
            )
        assert observed == [
            (4, "준비"),
            (8, "준비"),
            (10, "사용"),
            (12, "준비"),
            (16, "준비"),
            (20, "사용"),
            (20, "준비"),
            (30, "사용"),
            (32, "준비"),
            (40, "사용"),
            (40, "준비"),
        ]
        assert long.owner.snapshot() == split.owner.snapshot()
        assert cycle(long).state == Supply(3, 7, 4)
        assert long.update().quest_reward == 0 and long.update().quest_stage == 0
        before = long.owner.snapshot(), long.owner.protocol(), long.owner.working_path.read_bytes()
        retry = long.retry()
        assert not any("NPC 작업 기억" in m for m in retry.messages)
        assert (
            long.owner.snapshot(),
            long.owner.protocol(),
            long.owner.working_path.read_bytes(),
        ) == before
        inspected = long.inspect_activity()
        assert "전체 11개 중 최근 4개" in inspected.messages[1]
        assert not any("20초:" in m for m in inspected.messages)
        assert (
            long.owner.snapshot(),
            long.owner.protocol(),
            long.owner.working_path.read_bytes(),
        ) == before
        for owner in (long, split):
            segment = owner.owner.retained_segment()
            fixture = ReplayFixture(
                segment.checkpoint.core, segment.checkpoint.protocol, segment.trace
            )
            assert (
                replay_runner(fixture, bundles=(cycle_bundle(approved_content()),)).run(
                    segment.trace
                )
                == ()
            )
    finally:
        long.close()
        split.close()


def test_previous_corrupt_latest_branch_restart_memory_and_source_preservation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "game.sqlite"
    owner = session(path)
    try:
        owner.act("wait", seconds=10)
        earlier = cycle(owner)
        owner.save("slot01")
        owner.act("wait", seconds=10)
        owner.save("slot01")
        current, previous = (
            tmp_path / "slots/slot01.sqlite",
            tmp_path / "slots/slot01.previous.sqlite",
        )
        assert "전체 7개 중 최근 4개" in owner.inspect_activity().messages[1]
        current.write_bytes(b"F44 owned corrupt latest fixture")
        sources = current.read_bytes(), previous.read_bytes(), path.read_bytes()
        before = owner.owner.snapshot(), owner.owner.protocol(), owner.owner.attachment_id
        preview = owner.inspect_slot("slot01", previous=True)
        assert any("저장된 NPC 작업 기억 · 10초:" in m and "사용" in m for m in preview.messages)
        with pytest.raises(SaveError, match="^SAVE_CORRUPT:"):
            owner.load("slot01")
        assert (owner.owner.snapshot(), owner.owner.protocol(), owner.owner.attachment_id) == before
        owner.load("slot01", previous=True)
        assert cycle(owner) == earlier
        assert not any("20초:" in m for m in owner.inspect_activity().messages)
        with pytest.raises(ValueError, match="^NO_RETRY$"):
            owner.retry()
        branch = owner.owner.working_path
        assert branch != path
        owner.act("wait", seconds=10)
        expected = cycle(owner), owner.owner.snapshot(), owner.owner.protocol()
        owner.save("slot08")
        assert (current.read_bytes(), previous.read_bytes(), path.read_bytes()) == sources
    finally:
        owner.close()
    resumed = session(branch)
    try:
        assert (cycle(resumed), resumed.owner.snapshot(), resumed.owner.protocol()) == expected
        assert any("20초:" in m for m in resumed.inspect_activity().messages)
        assert (current.read_bytes(), previous.read_bytes(), path.read_bytes()) == sources
        segment = resumed.owner.retained_segment()
        assert (
            replay_runner(
                ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace),
                bundles=(cycle_bundle(approved_content()),),
            ).run(segment.trace)
            == ()
        )
    finally:
        resumed.close()


def test_quest_reward_memory_and_cycle_remain_separate(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        for action in GOAL:
            assert owner.act(action).status == "COMMITTED"
        owner.act("wait", seconds=16)
        owner.act("left")
        reported = owner.act("talk")
        assert reported.quest_stage == 3 and reported.quest_reward == 1
        assert any("공동 물자" in m for m in reported.messages)
        assert len(owner.inspect_memory().messages) == 2
        assert "직접 본 기억은 아닙니다" in owner.inspect_memory().messages[1]
        assert owner.act("talk").quest_reward == 1
    finally:
        owner.close()


@pytest.mark.parametrize("commit", (False, True))
def test_uncertain_write_recovers_atomic_supply_and_memory(tmp_path: Path, commit: bool) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("wait", seconds=16)
        initial = cycle(owner), owner.owner.snapshot(), owner.owner.protocol()
        store = owner.owner._attachment.store
        port = UncertainPort(store, commit=commit)
        owner.owner._attachment.owner._driver._commit_port = port
        update = owner.act("wait", seconds=4)
        assert port.persist_calls == port.recover_calls == 1
        assert update.status == ("COMMITTED" if commit else "SAVE_UNAVAILABLE")
        assert store.load() == DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        if commit:
            assert cycle(owner).state == Supply(3, 5, 2)
            assert [(e.tick, e.prepared) for e in cycle(owner).entries[-2:]] == [
                (20, False),
                (20, True),
            ]
        else:
            assert (cycle(owner), owner.owner.snapshot(), owner.owner.protocol()) == initial
            assert not any("NPC 작업 기억" in m for m in update.messages)
    finally:
        owner.close()


@pytest.mark.parametrize("bad", (0, 1, "1", None, (), 0.0))
def test_invalid_mode_rejected_before_allocation(tmp_path: Path, bad: object) -> None:
    selected = approved_content()
    path = tmp_path / "invalid.sqlite"
    for factory in (ClientSession, ClientWorker):
        with pytest.raises(ValueError, match="^NPC_CYCLE_CONTENT$"):
            factory(
                path,
                selected.definition.layout,
                quest_content=selected,
                npc_memory=True,
                npc_cycle=cast(bool, bad),
            )
    assert not path.exists()


def test_mode_dependencies_old_pins_and_invalid_checkpoint_unchanged(tmp_path: Path) -> None:
    selected = approved_content()
    path = tmp_path / "old.sqlite"
    for factory in (ClientSession, ClientWorker):
        with pytest.raises(ValueError, match="^NPC_CYCLE_CONTENT$"):
            factory(path, selected.definition.layout, quest_content=selected, npc_cycle=True)
        with pytest.raises(ValueError, match="^NPC_CYCLE_CONTENT$"):
            factory(
                path,
                selected.definition.layout,
                quest_content=selected,
                npc_memory=True,
                npc_work=True,
                npc_cycle=True,
            )
    old = ClientSession(
        path, selected.definition.layout, quest_content=selected, npc_memory=True, npc_work=True
    )
    old.close()
    before = path.read_bytes()
    with pytest.raises(SaveError):
        session(path)
    assert path.read_bytes() == before
    owner = session(tmp_path / "new/game.sqlite")
    try:
        owner.act("wait", seconds=16)
        core = owner.owner.snapshot()
        record = cycle(owner)
        changed = replace(
            record,
            entries=(
                replace(record.entries[0], source_event_id="e1-" + "f" * 64),
                *record.entries[1:],
            ),
        )
        bad = replace(
            core, components=tuple(changed if r is record else r for r in core.components)
        )
        io = state_io((cycle_bundle(selected),))
        with pytest.raises(ValueError, match="latest receipt does not match head"):
            io.validate_checkpoint(bad, owner.owner.protocol())
        with pytest.raises(ValueError, match="NPC_CYCLE_CHECKPOINT"):
            cycle_bundle(selected).checkpoint_policy.validate(bad, owner.owner.protocol())
    finally:
        owner.close()


@contextmanager
def cycle_pipe(path: Path) -> Iterator[PipeClient]:
    root = Path(__file__).resolve().parents[2]
    selected = approved_content()
    environment = dict(os.environ, PYTHONPATH=str(root / "src"), PYTHONUTF8="1")
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
            "--npc-cycle",
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
            pytest.fail("owned cycle Brain did not stop on EOF")
        if process.stdout is not None:
            process.stdout.close()
        errors = b"" if process.stderr is None else process.stderr.read()
        if process.stderr is not None:
            process.stderr.close()
        assert process.returncode == 0, errors.decode("utf-8", errors="replace")


def test_actual_binary_pipe_activity_slot_rewind_and_reconnect(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with cycle_pipe(path) as pipe:
        send_seconds(pipe, "wait", "10")
        pipe.send("save")
        send_seconds(pipe, "wait", "10")
        pipe.send("save")
        inspected = object_value(pipe.send("activity")["update"])
        assert any(
            "사용" in text_value(m) and "20초:" in text_value(m)
            for m in array_value(inspected["messages"])
        )
        preview = object_value(pipe.send("slot_previous_inspect")["update"])
        assert "10초" in text_value(array_value(preview["messages"])[0])
        loaded = object_value(pipe.send("load_previous")["update"])
        assert object_value(loaded["view"])["tick"] == "10"
        path = Path(text_value(loaded["working_path"]))
    with cycle_pipe(path) as pipe:
        inspected = object_value(pipe.send("activity")["update"])
        assert any(
            "전체 3개 중 최근 3개" in text_value(m) for m in array_value(inspected["messages"])
        )
        assert object_value(inspected["view"])["tick"] == "10"
        send_seconds(pipe, "wait", "10")
        assert object_value(pipe.send("activity")["update"])["status"] == "ACTIVITY_INSPECTED"


def test_actual_tk_mode_activity_wait_save_load_and_worker_serialization(
    tk_host: tk.Tk, tmp_path: Path
) -> None:
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
    )
    try:
        _pump(panel, lambda: not screen.busy)
        assert screen.mode_label == "NPC 반복 작업·기억 모드"
        _click(screen, "save")
        screen.wait_seconds.set("10")
        _click(screen, "wait")
        assert screen.last_update is not None and screen.last_update.view is not None
        assert screen.last_update.view.tick == 10
        assert screen.activity_button is not None
        screen.activity_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert any("10초:" in m and "사용" in m for m in screen.last_update.messages)
        _click(screen, "load")
        assert screen.last_update.view is not None and screen.last_update.view.tick == 0
        update = screen.worker.inspect_activity().result(timeout=30)
        assert update.messages[1] == "NPC 반복 작업 기억: 전체 0개 중 최근 0개를 보관합니다."
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
