"""Ready patrol obeys existing same-POST supply/gate barriers."""

from pathlib import Path
from typing import cast
import tkinter as tk

from app.client import PlayWindow, main as client_main
from app.client_worker import ClientWorker
from app.engine_bridge import main as bridge_main
from app.durable import create_durable
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.skeleton import FeatureBundle
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_call_pause_patrol import session as previous_mode
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict
import hashlib
import json
import os
import subprocess
import sys
import time
import sqlite3

from tests.integration.test_durable_turn import UncertainPort

import pytest

from app.engine_bridge import wire
from app.headless import replay_runner, state_io
from contracts.client import ClientAction
from contracts.replay import ReplayFixture
from domain.canonical import JsonObject, canonical_json, hash_document, object_value, text_value
from tests.integration.test_engine_bridge import PipeClient
from tests.integration.test_call_native_scenario import lines, digest
from tests.integration.test_call_pause_native_scenario import check, read_only
from tests.integration.test_patrol_next_step import BLOCKED

from app.client_session import ClientSession
from app.npc_cycle import bootstrap_cycle, cycle_bundle
from tests.integration.test_quest_patrol import state, view
from tests.integration.test_patrol_next_step import IDLE, FREE_NEIGHBOR
from app.watch import WatchBootstrapSpec
from contracts.quest import QuestTalkCommand
from contracts.trial import MoveCommand
from contracts.turn import GameCommand, TurnCommitted
from contracts.watch import WaitCommand, BellCommand
from domain.primitives import CommandId
from domain.watch import WatchNpcRecord
from domain.npc_cycle import CycleRecord, state_at
from domain.encounter import GateRecord
from tests.integration.test_memory_client_route import approved_content


def test_actual_prior_post_barrier_waits_through_preparation_then_resumes() -> None:
    content = approved_content()
    owner = bootstrap_cycle(
        WatchBootstrapSpec("0" * 64, "1" * 32, "2" * 32),
        content,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
        npc_ready_patrol=True,
    )
    actions = (
        MoveCommand(0, 1),
        QuestTalkCommand(content.definition.layout.npc_id),
        MoveCommand(0, -1),
        *(WaitCommand(1) for _ in range(9)),
    )
    observed = []
    for sequence, payload in enumerate(actions, 1):
        command = GameCommand(
            CommandId(f"c1:{'1' * 32}:{'2' * 32}:{sequence}"),
            content.definition.layout.actor_id,
            owner.protocol().revision,
            payload,
        )
        assert isinstance(owner.driver.submit(command), TurnCommitted)
        core = owner.snapshot()
        npc = next(r for r in core.components if type(r) is WatchNpcRecord)
        cycle = next(r for r in core.components if type(r) is CycleRecord)
        gate = next(r for r in core.components if type(r) is GateRecord)
        assert cycle.state == state_at(sequence)
        if sequence in (4, 6, 8, 10, 12):
            observed.append((sequence, npc.cell, cycle.state.stock, gate.is_open))
    assert observed == [(4, 6, 1, 0), (6, 6, 1, 0), (8, 6, 2, 0), (10, 7, 1, 1), (12, 6, 2, 1)]


def test_new_bundle_has_distinct_ready_identity_without_new_saved_component() -> None:
    content = approved_content()
    bundle = cycle_bundle(
        content,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
        npc_ready_patrol=True,
    )
    assert bundle.feature_id == "quest.harbor-ready-patrol-v1"


def test_actual_first_ready_answer_holds_and_next_wake_resumes() -> None:
    content = approved_content()
    owner = bootstrap_cycle(
        WatchBootstrapSpec("0" * 64, "1" * 32, "2" * 32),
        content,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
        npc_ready_patrol=True,
    )
    actions = (
        MoveCommand(0, 1),
        QuestTalkCommand(content.definition.layout.npc_id),
        MoveCommand(0, -1),
        *(WaitCommand(1) for _ in range(6)),
        BellCommand(content.definition.layout.npc_id),
        WaitCommand(1),
        WaitCommand(1),
    )
    observed = []
    for sequence, payload in enumerate(actions, 1):
        command = GameCommand(
            CommandId(f"c1:{'1' * 32}:{'2' * 32}:{sequence}"),
            content.definition.layout.actor_id,
            owner.protocol().revision,
            payload,
        )
        assert isinstance(owner.driver.submit(command), TurnCommitted)
        core = owner.snapshot()
        if sequence in (8, 10, 12):
            npc = next(r for r in core.components if type(r) is WatchNpcRecord)
            gate = next(r for r in core.components if type(r) is GateRecord)
            observed.append((sequence, npc.cell, gate.is_open))
    assert observed == [(8, 6, 0), (10, 6, 1), (12, 7, 1)]


POLICY = "NPC 지원 준비 · 의뢰 진행 중 통행문이 닫혀 있고 공동 물자가 2개 미만이면 원래 작업 지점 복귀·대기를 우선합니다."


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
        npc_ready_patrol=True,
    )


def test_actual_durable_saved_stock_and_current_stock_choose_separate_next_goals(
    tmp_path: Path,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        talk = owner.act("talk")
        owner.act("up")
        assert IDLE in talk.messages and talk.messages.count(POLICY) == 1
        assert view(owner.act("wait")).npc_cell == 6
        owner.save("slot01")
        assert view(owner.act("wait", seconds=4)).npc_cell == 6
        before = state(owner)
        activity = owner.inspect_activity()
        assert FREE_NEIGHBOR in activity.messages and activity.messages.count(POLICY) == 1
        selected = owner.inspect_slot("slot01")
        assert "NPC 다음 순찰 행동 비교 · 현재 8초 / 선택 저장 4초" in selected.messages
        assert (
            "현재 " + FREE_NEIGHBOR in selected.messages
            and "선택 저장 " + IDLE in selected.messages
        )
        assert selected.messages.count(POLICY) == 1
        assert state(owner) == before
    finally:
        owner.close()


def test_actual_durable_first_ready_answer_keeps_home_without_saved_pause(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("up")
        owner.act("wait", seconds=6)
        result = owner.act("bell")
        assert (view(result).tick, view(result).npc_cell, view(result).npc_replies) == (10, 6, 1)
        assert view(result).gate_open
        before = state(owner)
        assert FREE_NEIGHBOR in owner.inspect_activity().messages
        owner.retry()
        assert state(owner) == before
        assert (view(owner.act("wait", seconds=2)).tick, view(owner.update()).npc_cell) == (12, 7)
    finally:
        owner.close()


@contextmanager
def ready_pipe(path: Path) -> Iterator[PipeClient]:
    root = Path(__file__).resolve().parents[2]
    catalog = root / "content/narratives.json"
    content = approved_content()
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
            content.catalog_sha256,
            "--npc-memory",
            "--npc-cycle",
            "--npc-aid",
            "--npc-supply-aid",
            "--npc-call-aid",
            "--npc-patrol",
            "--npc-talk-pause",
            "--npc-quest-patrol",
            "--npc-call-pause",
            "--npc-ready-patrol",
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
        assert process.stdin is not None
        process.stdin.close()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=15)
            raise AssertionError("owned ready Brain did not stop on EOF") from None
        assert process.stdout is not None and process.stderr is not None
        process.stdout.close()
        errors = process.stderr.read()
        process.stderr.close()
        assert process.returncode == 0, errors.decode("utf-8")


@contextmanager
def ready_driver(
    path: Path, framed: bool, history: list[JsonObject], timing_path: Path
) -> Iterator[Callable[[str], JsonObject]]:
    timings: list[tuple[str, float]] = []
    if timing_path.exists():
        timings = json.loads(timing_path.read_text(encoding="utf-8"))

    def measured(raw: Callable[[str], JsonObject]) -> Callable[[str], JsonObject]:
        def send(action: str) -> JsonObject:
            start = time.perf_counter()
            update = raw(action)
            elapsed = time.perf_counter() - start
            stable = dict(update)
            stable.pop("attachment_id")
            stable.pop("working_path")
            history.append(stable)
            timings.append((action, elapsed))
            timing_path.write_text(json.dumps(timings, indent=2), encoding="utf-8")
            assert elapsed < 10, (action, elapsed)
            return update

        return send

    if framed:
        with ready_pipe(path) as pipe:
            yield measured(lambda action: object_value(pipe.send(action)["update"]))
        return
    owner = session(path)
    actions: dict[str, ClientAction] = {
        "down": "down",
        "up": "up",
        "left": "left",
        "right": "right",
        "wait": "wait",
        "talk": "talk",
        "bell": "bell",
        "attack": "attack",
        "rest": "rest",
        "close": "close",
        "open": "open",
    }

    def raw(action: str) -> JsonObject:
        if action == "attach":
            update = owner.update(reset_log=True)
        elif action == "save":
            update = owner.save("slot01")
        elif action == "load":
            update = owner.load("slot01")
        elif action == "slot_inspect":
            update = owner.inspect_slot("slot01")
        elif action == "slot_previous_inspect":
            update = owner.inspect_slot("slot01", previous=True)
        elif action == "activity":
            update = owner.inspect_activity()
        elif action == "retry":
            update = owner.retry()
        else:
            update = owner.act(actions[action])
        return object_value(wire(asdict(update)))

    try:
        yield measured(raw)
    finally:
        owner.close()


@pytest.mark.parametrize("framed", (False, True), ids=("direct", "real-pipe"))
def test_whole_ready_client_native_source_scenario(tmp_path: Path, framed: bool) -> None:
    from tests.integration.test_cycle_slot_comparison import inventory

    path = tmp_path / "game.sqlite"
    history: list[JsonObject] = []
    timings = tmp_path / "ready-timings.json"
    with ready_driver(path, framed, history, timings) as send:
        send("attach")
        send("down")
        talk = send("talk")
        send("up")
        assert IDLE in lines(talk) and lines(talk).count(POLICY) == 1
        early = send("wait")
        check(early, 4, 6, 0)
        send("save")
        for tick in (5, 6, 7, 8):
            current = send("wait")
            check(current, tick, 6, 0)
        read_only(send, "activity", tmp_path, current, (FREE_NEIGHBOR, POLICY))
        read_only(
            send,
            "slot_inspect",
            tmp_path,
            current,
            (
                "NPC 다음 순찰 행동 비교 · 현재 8초 / 선택 저장 4초",
                "현재 " + FREE_NEIGHBOR,
                "선택 저장 " + IDLE,
                POLICY,
            ),
        )
        send("wait")
        answered = send("bell")
        check(answered, 10, 6, 1)
        assert object_value(answered["view"])["gate_open"] is True
        before = inventory(tmp_path)
        retry = send("retry")
        check(retry, 10, 6, 1)
        assert retry["view"] == answered["view"] and inventory(tmp_path) == before
        send("save")
        read_only(
            send,
            "slot_previous_inspect",
            tmp_path,
            answered,
            (
                "NPC 다음 순찰 행동 비교 · 현재 10초 / 선택 저장 4초",
                "현재 " + FREE_NEIGHBOR,
                "선택 저장 " + IDLE,
                POLICY,
            ),
        )
        send("wait")
        check(send("wait"), 12, 7, 1)
        original, original_bytes = path, digest(path)
        loaded = send("load")
        check(loaded, 10, 6, 1)
        branch = Path(text_value(loaded["working_path"]))
        assert branch != original
    with ready_driver(branch, framed, history, timings) as send:
        attached = send("attach")
        check(attached, 10, 6, 1)
        read_only(send, "activity", tmp_path, attached, (FREE_NEIGHBOR, POLICY))
        send("wait")
        check(send("wait"), 12, 7, 1)
        send("down")
        blocked = send("down")
        check(blocked, 14, 7, 1)
        read_only(send, "activity", tmp_path, blocked, (BLOCKED, POLICY))
        send("up")
        check(send("wait"), 16, 6, 1)
        for action in ("right", "down", "attack", "attack", "rest"):
            assert send(action)["status"] == "COMMITTED"
        defeated = send("attack")
        check(defeated, 22, 6, 1)
        assert object_value(defeated["view"])["enemy_hp"] == "0" and defeated["quest_stage"] == "2"
        send("up")
        check(send("left"), 24, 7, 1)
        send("down")
        report = send("talk")
        check(report, 26, 7, 1, reward=1)
        assert BLOCKED in lines(report)
        send("wait")
        check(send("wait"), 28, 7, 1, reward=1)
        send("up")
        check(send("wait"), 30, 6, 1, reward=1)
        grateful = send("talk")
        check(grateful, 31, 6, 1, reward=1)
        read_only(send, "activity", tmp_path, grateful, (IDLE, POLICY))
        read_only(
            send,
            "slot_inspect",
            tmp_path,
            grateful,
            (
                "NPC 다음 순찰 행동 비교 · 현재 31초 / 선택 저장 10초",
                "현재 " + IDLE,
                "선택 저장 " + FREE_NEIGHBOR,
                POLICY,
            ),
        )
        assert digest(original) == original_bytes
    owner = session(branch)
    try:
        segment = owner.owner.retained_segment()
        fixture = ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace)
        bundle = cycle_bundle(
            approved_content(),
            npc_aid=True,
            npc_supply_aid=True,
            npc_call_aid=True,
            npc_patrol=True,
            npc_talk_pause=True,
            npc_quest_patrol=True,
            npc_call_pause=True,
            npc_ready_patrol=True,
        )
        assert replay_runner(fixture, bundles=(bundle,)).run(segment.trace) == ()
        io = state_io((bundle,))
        core = io.hash_core(owner.owner.snapshot())
        protocol = hash_document("protocol/v1", io.encode_protocol(owner.owner.protocol()))
    finally:
        owner.close()
    (tmp_path / "ready-result.json").write_bytes(
        canonical_json(
            {
                "updates": tuple(history),
                "core": core,
                "protocol": protocol,
                "source_preserved": digest(original) == original_bytes,
                "steps": len(history),
            }
        )
    )


def ready_bundle() -> FeatureBundle:
    return cycle_bundle(
        approved_content(),
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
        npc_ready_patrol=True,
    )


@pytest.mark.parametrize("kind", ("session", "worker"))
@pytest.mark.parametrize(
    "value,parent", ((True, False), (0, True), (1, True), (None, True), ("1", True))
)
def test_new_selection_rejects_before_save_or_worker_resource_io(
    tmp_path: Path, kind: str, value: object, parent: bool
) -> None:
    content = approved_content()
    path = tmp_path / "absent/game.sqlite"
    factory = ClientSession if kind == "session" else ClientWorker
    with pytest.raises(ValueError, match="^NPC_READY_PATROL_CONTENT$"):
        factory(
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
            npc_call_pause=parent,
            npc_ready_patrol=cast(bool, value),
        )
    assert not path.parent.exists()


def test_python_cli_missing_parent_rejects_before_tk() -> None:
    with pytest.raises(ValueError, match="^NPC_READY_PATROL_CONTENT$"):
        client_main(["--npc-ready-patrol"])


def test_framed_cli_missing_parent_returns_explicit_error_without_save(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
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
                "--npc-ready-patrol",
            ]
        )
        == 1
    )
    assert "NPC_READY_PATROL_CONTENT" in caplog.text and not path.parent.exists()


def test_closed_gate_restarts_readiness_without_using_same_phase_preparation(
    tmp_path: Path,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=7)
        assert (view(owner.act("bell")).tick, view(owner.update()).npc_cell) == (10, 6)
        assert view(owner.update()).gate_open
        assert owner.act("close").status == "COMMITTED"
        update = owner.act("wait")
        assert (view(update).tick, view(update).npc_cell, view(update).gate_open) == (12, 6, False)
        assert FREE_NEIGHBOR in owner.inspect_activity().messages
        update = owner.act("wait", seconds=2)
        assert (view(update).tick, view(update).npc_cell, view(update).gate_open) == (14, 7, True)
    finally:
        owner.close()


def test_previous_save_load_restart_keeps_each_snapshot_supply_goal(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("up")
        owner.act("wait")
        owner.save("slot01")
        owner.act("wait", seconds=4)
        owner.save("slot01")
        before = state(owner)
        rows = owner.inspect_slot("slot01", previous=True).messages
        assert (
            "현재 " + FREE_NEIGHBOR in rows
            and "선택 저장 " + IDLE in rows
            and state(owner) == before
        )
        owner.load("slot01", previous=True)
        branch = owner.owner.working_path
    finally:
        owner.close()
    owner = session(branch)
    try:
        before = state(owner)
        rows = owner.inspect_slot("slot01").messages
        assert "NPC 다음 순찰 행동 비교 · 현재 4초 / 선택 저장 8초" in rows
        assert (
            "현재 " + IDLE in rows
            and "선택 저장 " + FREE_NEIGHBOR in rows
            and state(owner) == before
        )
        assert view(owner.act("wait", seconds=4)).npc_cell == 6
        assert view(owner.act("wait", seconds=2)).npc_cell == 7
    finally:
        owner.close()


def test_compacted_checkpoint_has_no_saved_readiness_or_answer_pause(tmp_path: Path) -> None:
    source = tmp_path / "source/game.sqlite"
    owner = session(source)
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("up")
        owner.act("wait", seconds=6)
        owner.act("bell")
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        source_bytes = source.read_bytes()
    finally:
        owner.close()
    compact = tmp_path / "compact/game.sqlite"
    create_durable(compact, checkpoint, bundles=(ready_bundle(),)).close()
    owner = session(compact)
    try:
        assert not owner.owner.retained_segment().trace.steps
        assert FREE_NEIGHBOR in owner.inspect_activity().messages
        assert (view(owner.act("wait", seconds=2)).tick, view(owner.update()).npc_cell) == (12, 7)
        segment = owner.owner.retained_segment()
        fixture = ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace)
        assert replay_runner(fixture, bundles=(ready_bundle(),)).run(segment.trace) == ()
    finally:
        owner.close()
    assert source.read_bytes() == source_bytes


@pytest.mark.parametrize("new_first", (False, True))
def test_ready_identity_never_repins_previous_call_pause_save(
    tmp_path: Path, new_first: bool
) -> None:
    path = tmp_path / "game.sqlite"
    first = session if new_first else previous_mode
    other = previous_mode if new_first else session
    owner = first(path)
    try:
        owner.act("down")
        owner.act("talk")
    finally:
        owner.close()
    before = path.read_bytes()
    with pytest.raises(SaveError) as caught:
        other(path)
    assert caught.value.code == "UNSUPPORTED_RULESET" and path.read_bytes() == before


def test_real_worker_and_withdrawn_tk_forward_new_mode_and_saved_goals(
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
        npc_ready_patrol=True,
    )
    try:
        for request in ("down", "talk", "up", "wait"):
            assert worker.request(request).result(timeout=10).status == "COMMITTED"
        worker.request("save").result(timeout=10)
        worker.request("wait", seconds=4).result(timeout=10)
        result = worker.inspect_slot().result(timeout=10)
        assert "현재 " + FREE_NEIGHBOR in result.messages and "선택 저장 " + IDLE in result.messages
        assert result.messages.count(POLICY) == 1
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
        npc_ready_patrol=True,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        assert (
            screen.mode_label
            == "NPC 지원 준비 우선·호출 응답 대기·의뢰 순찰·대화 대기·호출 지원·물자·반복 작업·기억 모드"
        )
        actions: tuple[ClientAction, ...] = ("down", "talk", "up", "wait")
        for action in actions:
            _click(screen, action)
        _click(screen, "save")
        for _ in range(4):
            _click(screen, "wait")
        screen.slot_preview_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None
        assert (
            "현재 " + FREE_NEIGHBOR in screen.last_update.messages
            and "선택 저장 " + IDLE in screen.last_update.messages
        )
        assert POLICY in screen.log_text.get("1.0", "end")
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())


@pytest.mark.parametrize("commit", (False, True))
def test_uncertain_ready_answer_has_one_atomic_gate_supply_reply_result(
    tmp_path: Path, commit: bool
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("up")
        owner.act("wait", seconds=6)
        before = state(owner)
        store = owner.owner._attachment.store
        port = UncertainPort(store, commit=commit)
        owner.owner._attachment.owner._driver._commit_port = port
        result = owner.act("bell")
        assert port.persist_calls == port.recover_calls == 1
        assert result.status == ("COMMITTED" if commit else "SAVE_UNAVAILABLE")
        assert (view(result).tick, view(result).npc_cell, view(result).npc_replies) == (
            (10, 6, 1) if commit else (9, 6, 0)
        )
        assert view(result).gate_open is commit
        if commit:
            after = state(owner)
            owner.retry()
            assert state(owner) == after
        else:
            assert state(owner) == before
        assert store.load() == DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()


def test_real_sql_rollback_keeps_new_goal_inputs_until_exact_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("up")
        owner.act("wait", seconds=6)
        before = state(owner)
        store = owner.owner._attachment.store
        original = store._execute

        def fail(
            query: str, values: tuple[None | int | float | str | bytes, ...] = ()
        ) -> sqlite3.Cursor:
            result = original(query, values)
            if query.startswith("INSERT INTO replay"):
                raise sqlite3.IntegrityError("F80ready actual atomic rollback")
            return result

        with monkeypatch.context() as patch:
            patch.setattr(store, "_execute", fail)
            assert owner.act("bell").status == "SAVE_UNAVAILABLE"
        assert state(owner) == before
        result = owner.retry()
        assert (view(result).tick, view(result).npc_cell, view(result).npc_replies) == (10, 6, 1)
        assert view(result).gate_open and view(owner.act("wait", seconds=2)).npc_cell == 7
    finally:
        owner.close()
