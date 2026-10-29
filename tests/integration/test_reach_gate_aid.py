"""Physical aid reads prior NPC pose,not same-phase patrol arrival."""

import pytest
from contracts.messages import CommandPayload
from contracts.watch import BellCommand
from domain.watch import ReplyRecord
from app.npc_cycle import bootstrap_cycle, cycle_bundle
from app.watch import WatchBootstrapSpec
from contracts.turn import GameCommand, TurnCommitted
from contracts.quest import QuestTalkCommand
from contracts.trial import MoveCommand
from contracts.watch import WaitCommand
from domain.encounter import GateRecord
from domain.npc_cycle import CycleRecord, state_at
from domain.primitives import CommandId
from domain.watch import WatchNpcRecord
from tests.integration.test_memory_client_route import approved_content


# Stage B/C: exercise the exposed mode through real runtime boundaries.
from pathlib import Path
from typing import cast, TypedDict
from contracts.skeleton import FeatureBundle
from contextlib import contextmanager
from collections.abc import Iterator, Callable
from dataclasses import asdict, replace
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
import tkinter as tk

from app.client_session import ClientSession
from app.client_worker import ClientWorker
from app.client import PlayWindow
from app.engine_bridge import wire, main as bridge_main
from app.client import main as client_main
from app.headless import replay_runner
from app.durable import create_durable
from app.npc_support_status import supply_support_plan, REACH_AID_POLICY
from contracts.client import ClientAction
from contracts.persistence import SaveError, DurableCheckpoint
from contracts.replay import ReplayFixture
from domain.canonical import JsonObject, object_value
from tests.integration.test_engine_bridge import PipeClient
from tests.integration.test_quest_patrol import state, view
from tests.integration.test_ready_patrol import session as old_session
from tests.integration.test_durable_turn import UncertainPort
from tests.integration.test_client import _click, _pump, tk_host as tk_host


def test_new_bundle_has_distinct_identity_with_existing_state_schemas() -> None:
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
        npc_reach_aid=True,
    )
    assert bundle.feature_id == "quest.harbor-reach-aid-v1"


def test_actual_prior_pose_cannot_open_on_arrival_but_can_before_moving_away() -> None:
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
        npc_reach_aid=True,
    )
    actions = (
        MoveCommand(0, 1),
        QuestTalkCommand(content.definition.layout.npc_id),
        MoveCommand(0, -1),
        *(WaitCommand(1) for _ in range(13)),
    )
    observed = []
    for sequence, action in enumerate(actions, 1):
        command = GameCommand(
            CommandId(f"c1:{'1' * 32}:{'2' * 32}:{sequence}"),
            content.definition.layout.actor_id,
            owner.protocol().revision,
            action,
        )
        assert isinstance(owner.driver.submit(command), TurnCommitted)
        core = owner.snapshot()
        npc = next(x for x in core.components if type(x) is WatchNpcRecord)
        gate = next(x for x in core.components if type(x) is GateRecord)
        cycle = next(x for x in core.components if type(x) is CycleRecord)
        assert cycle.state == state_at(sequence)
        if sequence in (9, 10, 12, 14, 16):
            observed.append((sequence, npc.cell, gate.is_open, cycle.state.stock))
    assert observed == [(9, 6, 0, 2), (10, 7, 0, 1), (12, 6, 0, 2), (14, 7, 0, 2), (16, 6, 1, 3)]


@pytest.mark.parametrize(
    "bell_tick,npc_cell,stock,opened", ((11, 7, 1, 0), (13, 6, 2, 0), (15, 7, 2, 1))
)
def test_actual_odd_call_requires_both_prior_stock_and_adjacent_pose(
    bell_tick: int,
    npc_cell: int,
    stock: int,
    opened: int,
) -> None:
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
        npc_reach_aid=True,
    )
    for sequence in range(1, bell_tick + 1):
        action: CommandPayload
        if sequence == 1:
            action = MoveCommand(0, 1)
        elif sequence == 2:
            action = QuestTalkCommand(content.definition.layout.npc_id)
        elif sequence == 3:
            action = MoveCommand(0, -1)
        elif sequence == bell_tick:
            action = BellCommand(content.definition.layout.npc_id)
        else:
            action = WaitCommand(1)
        command = GameCommand(
            CommandId(f"c1:{'1' * 32}:{'2' * 32}:{sequence}"),
            content.definition.layout.actor_id,
            owner.protocol().revision,
            action,
        )
        assert isinstance(owner.driver.submit(command), TurnCommitted)
    core = owner.snapshot()
    npc = next(x for x in core.components if type(x) is WatchNpcRecord)
    gate = next(x for x in core.components if type(x) is GateRecord)
    cycle = next(x for x in core.components if type(x) is CycleRecord)
    replies = next(x for x in core.components if type(x) is ReplyRecord)
    assert (core.tick, npc.cell, cycle.state.stock, gate.is_open, replies.count) == (
        bell_tick,
        npc_cell,
        stock,
        opened,
        1,
    )


class ModeFlags(TypedDict):
    npc_memory: bool
    npc_cycle: bool
    npc_aid: bool
    npc_supply_aid: bool
    npc_call_aid: bool
    npc_patrol: bool
    npc_talk_pause: bool
    npc_quest_patrol: bool
    npc_call_pause: bool
    npc_ready_patrol: bool
    npc_reach_aid: bool


FLAGS: ModeFlags = ModeFlags(
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
    npc_reach_aid=True,
)
FAR = "NPC 지원 계획 · 공동 물자가 확보되어 통행문 옆 작업 지점에 도착해야 통행을 도울 수 있습니다."
NEAR = "NPC 지원 계획 · 공동 물자가 확보되어 가까이 있는 NPC에게 통행 지원을 요청할 수 있습니다."


def session(path: Path) -> ClientSession:
    content = approved_content()
    return ClientSession(path, content.definition.layout, quest_content=content, **FLAGS)


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
        npc_ready_patrol=True,
        npc_reach_aid=True,
    )


@pytest.mark.parametrize("kind", ("session", "worker"))
@pytest.mark.parametrize(
    "value,parent", ((True, False), (0, True), (1, True), (None, True), ("1", True))
)
def test_reach_selection_before_resource_io(
    tmp_path: Path, kind: str, value: object, parent: bool
) -> None:
    flags = FLAGS.copy()
    flags["npc_reach_aid"] = cast(bool, value)
    flags["npc_ready_patrol"] = parent
    ctor = ClientSession if kind == "session" else ClientWorker
    with pytest.raises(ValueError, match="^NPC_REACH_AID_CONTENT$"):
        ctor(
            tmp_path / "missing/game.sqlite",
            approved_content().definition.layout,
            quest_content=approved_content(),
            **flags,
        )
    assert not (tmp_path / "missing").exists()


@contextmanager
def driver(path: Path, framed: bool) -> Iterator[Callable[[str], JsonObject]]:
    if not framed:
        owner = session(path)

        def send(action: str) -> JsonObject:
            if action == "save":
                result = owner.save("slot01")
            elif action == "load":
                result = owner.load("slot01")
            elif action == "slot_inspect":
                result = owner.inspect_slot("slot01")
            elif action == "slot_previous_inspect":
                result = owner.inspect_slot("slot01", previous=True)
            elif action == "activity":
                result = owner.inspect_activity()
            elif action == "retry":
                result = owner.retry()
            else:
                result = owner.act(cast(ClientAction, action))
            return object_value(wire(asdict(result)))

        try:
            yield send
        finally:
            owner.close()
        return
    root = Path(__file__).resolve().parents[2]
    catalog = root / "content/narratives.json"
    content = approved_content()
    args = [
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
        *("--" + k.replace("_", "-") for k in FLAGS),
    ]
    process = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=root,
        env=dict(os.environ, PYTHONPATH=str(root / "src"), PYTHONUTF8="1"),
    )
    try:
        pipe = PipeClient(process)
        yield lambda action: object_value(pipe.send(action)["update"])
    finally:
        assert (
            process.stdin is not None and process.stdout is not None and process.stderr is not None
        )
        process.stdin.close()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=15)
            raise
        process.stdout.close()
        errors = process.stderr.read()
        process.stderr.close()
        assert process.returncode == 0, errors.decode("utf-8")


@pytest.mark.parametrize("framed", (False, True), ids=("direct", "real-pipe"))
def test_exposed_reach_timeline_queries_retry_save_load_reconnect(
    tmp_path: Path, framed: bool
) -> None:
    path = tmp_path / "game.sqlite"
    timings = []
    with driver(path, framed) as send:
        send("down")
        send("talk")
        send("up")
        for tick in range(4, 15):
            update = send("wait")
            v = object_value(update["view"])
            assert v["tick"] == str(tick) and v["gate_open"] is False
            if tick in (9, 10, 12, 14):
                assert v["npc_cell"] == str({9: 6, 10: 7, 12: 6, 14: 7}[tick])
            if tick in (9, 14):
                before = path.read_bytes()
                start = time.perf_counter()
                rows = send("activity")["messages"]
                elapsed = time.perf_counter() - start
                timings.append(elapsed)
                assert isinstance(rows, tuple) and (FAR if tick == 9 else NEAR) in rows
                assert rows.count(REACH_AID_POLICY) == 1 and path.read_bytes() == before
                if tick == 9:
                    send("save")
        before = path.read_bytes()
        selected = send("slot_inspect")["messages"]
        assert (
            isinstance(selected, tuple)
            and "현재 " + NEAR in selected
            and "선택 저장 " + FAR in selected
        )
        assert path.read_bytes() == before
        send("save")
        opened = send("bell")
        assert object_value(opened["view"])["gate_open"] is True
        before = path.read_bytes()
        retry = send("retry")
        assert retry["view"] == opened["view"] and path.read_bytes() == before
        loaded = send("load")
        assert object_value(loaded["view"])["gate_open"] is False
        branch = Path(str(loaded["working_path"]))
        assert branch != path
        original = path.read_bytes()
    with driver(branch, framed) as send:
        activity = send("activity")
        assert object_value(activity["view"])["tick"] == "14"
        assert object_value(activity["view"])["gate_open"] is False
        answered = send("bell")
        assert object_value(answered["view"])["gate_open"] is True
        assert object_value(answered["view"])["npc_replies"] == "1"
    assert path.read_bytes() == original
    (tmp_path / "query-timings.json").write_text(json.dumps(timings), encoding="utf-8")
    assert max(timings) < 10


@pytest.mark.parametrize("commit", (False, True))
def test_reach_uncertain_atomic_adjacent_answer(tmp_path: Path, commit: bool) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("up")
        owner.act("wait", seconds=11)
        assert (view(owner.update()).tick, view(owner.update()).npc_cell) == (14, 7)
        before = state(owner)
        store = owner.owner._attachment.store
        port = UncertainPort(store, commit=commit)
        owner.owner._attachment.owner._driver._commit_port = port
        result = owner.act("bell")
        assert port.persist_calls == port.recover_calls == 1
        assert result.status == ("COMMITTED" if commit else "SAVE_UNAVAILABLE")
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


def test_reach_real_rollback_then_exact_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("up")
        owner.act("wait", seconds=11)
        before = state(owner)
        store = owner.owner._attachment.store
        original = store._execute

        def fail(
            query: str, values: tuple[None | int | float | str | bytes, ...] = ()
        ) -> sqlite3.Cursor:
            result = original(query, values)
            if query.startswith("INSERT INTO replay"):
                raise sqlite3.IntegrityError("F82 atomic rollback")
            return result

        with monkeypatch.context() as patch:
            patch.setattr(store, "_execute", fail)
            assert owner.act("bell").status == "SAVE_UNAVAILABLE"
        assert state(owner) == before
        result = owner.retry()
        assert view(result).gate_open and view(result).npc_replies == 1
    finally:
        owner.close()


def test_reach_compact_replay_identity_and_projection_inputs(tmp_path: Path) -> None:

    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("up")
        owner.act("wait", seconds=11)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        core = checkpoint.core
        layout = approved_content().definition.layout
        assert NEAR in supply_support_plan(
            core, layout, error_code="SOURCE", npc_call_aid=True, npc_reach_aid=True
        )
        for cell in (True, -1, 4, 8):
            malformed = replace(
                core,
                components=tuple(
                    replace(r, cell=cell) if type(r) is WatchNpcRecord else r
                    for r in core.components
                ),
            )
            with pytest.raises(SaveError, match="selected NPC pose"):
                supply_support_plan(
                    malformed, layout, error_code="SOURCE", npc_call_aid=True, npc_reach_aid=True
                )
    finally:
        owner.close()
    raw = (tmp_path / "game.sqlite").read_bytes()
    with pytest.raises(SaveError) as error:
        old_session(tmp_path / "game.sqlite")
    assert (
        error.value.code == "UNSUPPORTED_RULESET" and (tmp_path / "game.sqlite").read_bytes() == raw
    )
    compact = tmp_path / "compact/game.sqlite"
    bundles = (bundle(),)
    create_durable(compact, checkpoint, bundles=bundles).close()
    owner = session(compact)
    try:
        assert not owner.owner.retained_segment().trace.steps
        assert view(owner.act("bell")).gate_open
        segment = owner.owner.retained_segment()
        fixture = ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace)
        assert replay_runner(fixture, bundles=bundles).run(segment.trace) == ()
    finally:
        owner.close()


def test_reach_worker_and_withdrawn_tk(tk_host: tk.Tk, tmp_path: Path) -> None:
    content = approved_content()
    worker = ClientWorker(
        tmp_path / "worker/game.sqlite", content.definition.layout, quest_content=content, **FLAGS
    )
    try:
        for action in ("down", "talk", "up"):
            worker.request(action).result(timeout=10)
        worker.request("wait", seconds=11).result(timeout=10)
        assert NEAR in worker.inspect_activity().result(timeout=10).messages
        assert view(worker.request("bell").result(timeout=10)).gate_open
    finally:
        worker.join()
    panel = tk.Toplevel(tk_host)
    panel.withdraw()
    screen = PlayWindow(
        panel,
        tmp_path / "tk/game.sqlite",
        content.definition.layout,
        quest_content=content,
        **FLAGS,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        assert screen.mode_label.startswith("NPC 인접 통행 지원·")
        for action in ("down", "talk", "up"):
            _click(screen, cast(ClientAction, action))
        assert screen.last_update is not None and REACH_AID_POLICY in screen.log_text.get(
            "1.0", "end"
        )
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())


def test_reach_cli_missing_parent_no_window_or_save(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    content = approved_content()
    path = tmp_path / "missing/game.sqlite"
    args = [
        "--working",
        str(path),
        "--scenario",
        "harbor",
        "--quest-catalog",
        str(root / "content/dialogue/harbor-memory-v1.json"),
        "--quest-sha256",
        content.catalog_sha256,
        "--npc-reach-aid",
    ]
    with pytest.raises(ValueError, match="NPC_REACH_AID_CONTENT"):
        client_main(args)
    catalog = root / "content/narratives.json"
    assert (
        bridge_main(
            [
                *args,
                "--catalog",
                str(catalog),
                "--catalog-sha256",
                hashlib.sha256(catalog.read_bytes()).hexdigest(),
            ]
        )
        == 1
    )
    assert not path.parent.exists()


@pytest.mark.parametrize("framed", (False, True), ids=("direct", "real-pipe"))
@pytest.mark.parametrize("waits", (14, 126), ids=("short", "long"))
def test_reach_short_long_talk_activity_slot_preserve_sources(
    tmp_path: Path, framed: bool, waits: int
) -> None:
    path = tmp_path / "game.sqlite"
    samples = []
    with driver(path, framed) as send:
        send("down")
        send("talk")
        send("up")
        for _ in range(waits):
            send("wait")
        send("save")
        send("down")
        send("right")
        start = time.perf_counter()
        talk = send("talk")
        samples.append(("talk", time.perf_counter() - start))
        assert REACH_AID_POLICY in cast(tuple[str, ...], talk["messages"])
        for action in ("activity", "slot_inspect"):
            before = path.read_bytes()
            start = time.perf_counter()
            result = send(action)
            samples.append((action, time.perf_counter() - start))
            assert result["view"] == talk["view"] and path.read_bytes() == before
        assert all(elapsed < 10 for _, elapsed in samples)
    (tmp_path / "performance.json").write_text(json.dumps(samples), encoding="utf-8")


def test_reach_full_quest_close_report_reward_and_load_branch(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("up")
        owner.act("wait", seconds=13)
        assert view(owner.update()).gate_open
        assert owner.act("down").status == "COMMITTED"
        assert owner.act("right").status == "COMMITTED"
        owner.act("wait", seconds=2)
        assert view(owner.act("down")).actor_cell == 7
        for action in ("attack", "attack", "rest", "attack"):
            assert owner.act(action).status == "COMMITTED"
        assert view(owner.update()).enemy_hp == 0 and owner.update().quest_reward == 0
        owner.act("up")
        report = owner.act("talk")
        assert report.quest_reward == 1
        owner.save("slot01")
        source = owner.owner.working_path
        raw = source.read_bytes()
        owner.load("slot01")
        branch = owner.owner.working_path
        assert branch != source and source.read_bytes() == raw
        assert owner.act("talk").quest_reward == 1
        assert owner.act("left").status == "COMMITTED"
        assert owner.act("close").status == "COMMITTED"
        assert not view(owner.update()).gate_open
        assert owner.act("open").status == "COMMITTED" and view(owner.update()).gate_open
        assert source.read_bytes() == raw
    finally:
        owner.close()
