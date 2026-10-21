from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import time
import tkinter as tk

import pytest

from app.client import PlayWindow
from app.client_session import ClientSession
from app.client_worker import ClientWorker
from app.durable import DurableSession, create_durable
from app.npc_activity import activity_messages
from app.npc_work import work_bundle
from contracts.client import ClientUpdate
from contracts.persistence import DurableCheckpoint, SaveError, SaveSegment
from contracts.replay import ReplayTrace
from orchestration.replay import Runner
from tests.integration.test_client import _pump, tk_host as tk_host
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_work import session, work_pipe
from tests.integration.test_unity_wait_duration import send_seconds
from domain.canonical import array_value, object_value, text_value


def work_line(tick: int) -> str:
    return f"NPC 비축 작업 · {tick}초: +1개 (당시 {tick // 4}/3개)"


def work_lines(update: ClientUpdate) -> tuple[str, ...]:
    return tuple(m for m in update.messages if m.startswith("NPC 비축 작업 · ") and "초:" in m)


def advance_time(owner: ClientSession, seconds: int) -> None:
    while seconds:
        amount = min(seconds, 16)
        assert owner.act("wait", seconds=amount).status == "COMMITTED"
        seconds -= amount


@pytest.mark.parametrize(
    "tick,expected", ((0, ()), (3, ()), (4, (4,)), (8, (4, 8)), (12, (4, 8, 12)), (32, (4, 8, 12)))
)
def test_activity_keeps_all_retained_work_at_boundaries(
    tmp_path: Path, tick: int, expected: tuple[int, ...]
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        if tick:
            advance_time(owner, tick)
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.retained_segment(),
            owner.owner.working_path.read_bytes(),
            owner.owner.attachment_id,
        )
        update = owner.inspect_activity()
        assert update.status == "ACTIVITY_INSPECTED" and not update.reset_log
        assert work_lines(update) == tuple(work_line(at) for at in expected)
        assert "NPC 비축 작업 · 0초 이후 저장 기록에서 확인했습니다." in update.messages
        assert f"물자 {len(expected)}/3개" in update.messages[-1]
        if not expected:
            assert update.messages[-2] == (
                "현재 저장 구간에 남은 비축 작업 기록이 없습니다. 재고로 과거 작업을 추정하지 않습니다."
            )
        if tick == 32:
            assert tuple(m for m in update.messages if m.startswith("NPC 활동 기록 · ")) == tuple(
                f"NPC 활동 기록 · {at}초: 종을 울렸습니다. (누적 {at // 2}회)"
                for at in range(18, 33, 2)
            )
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.retained_segment(),
            owner.owner.working_path.read_bytes(),
            owner.owner.attachment_id,
        ) == before
        if tick:
            assert owner.retry().view == update.view
            assert owner.owner.working_path.read_bytes() == before[3]
            assert owner.inspect_activity().messages == update.messages
    finally:
        owner.close()


def test_activity_load_restart_and_slot_bytes_follow_the_selected_branch(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("wait", seconds=4)
        owner.save("slot01")
        slot = tmp_path / "slots/slot01.sqlite"
        slot_bytes = slot.read_bytes()
        saved = owner.inspect_activity()
        advance_time(owner, 28)
        assert work_lines(owner.inspect_activity()) == tuple(work_line(at) for at in (4, 8, 12))
        owner.load("slot01")
        assert owner.inspect_activity().messages == saved.messages
        assert slot.read_bytes() == slot_bytes
        working = owner.owner.working_path
    finally:
        owner.close()
    resumed = session(working)
    try:
        assert resumed.inspect_activity().messages == saved.messages
        resumed.act("wait", seconds=4)
        assert work_lines(resumed.inspect_activity()) == (work_line(4), work_line(8))
        assert slot.read_bytes() == slot_bytes
    finally:
        resumed.close()


@pytest.mark.parametrize(
    "checkpoint_tick,advance,expected", ((6, 0, ()), (6, 2, (8,)), (32, 0, ()))
)
def test_checkpoint_stock_never_invents_missing_work(
    tmp_path: Path, checkpoint_tick: int, advance: int, expected: tuple[int, ...]
) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        advance_time(owner, checkpoint_tick)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    path = tmp_path / "checkpoint/game.sqlite"
    durable = create_durable(path, checkpoint, bundles=(work_bundle(approved_content()),))
    durable.close()
    restored = session(path)
    try:
        if advance:
            restored.act("wait", seconds=advance)
        update = restored.inspect_activity()
        assert work_lines(update) == tuple(work_line(at) for at in expected)
        assert (
            f"NPC 비축 작업 · {checkpoint_tick}초 이후 저장 기록에서 확인했습니다."
            in update.messages
        )
        assert f"물자 {min(3, (checkpoint_tick + advance) // 4)}/3개" in update.messages[-1]
    finally:
        restored.close()


@pytest.mark.parametrize("damage", ("owner", "current", "header", "facts", "duplicate"))
def test_activity_rejects_unverified_sources_without_modification(
    tmp_path: Path, damage: str
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("wait", seconds=16)
        segment = owner.owner.retained_segment()
        current = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        npc = str(approved_content().definition.layout.npc_id)
        if damage == "owner":
            npc = "npc:other"
        elif damage == "current":
            current = segment.checkpoint
        elif damage == "header":
            segment = replace(
                segment,
                trace=replace(
                    segment.trace, header=replace(segment.trace.header, initial_core_hash="0" * 64)
                ),
            )
        elif damage == "facts":
            segment = replace(
                segment,
                trace=replace(
                    segment.trace,
                    steps=(replace(segment.trace.steps[0], expected_facts_hash="0" * 64),),
                ),
            )
        else:
            segment = replace(segment, trace=replace(segment.trace, steps=segment.trace.steps * 2))
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        with pytest.raises(SaveError, match="^NPC_ACTIVITY_SOURCE:"):
            activity_messages(
                segment, npc, content=approved_content(), current=current, npc_work=True
            )
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
        assert work_lines(owner.inspect_activity()) == tuple(work_line(at) for at in (4, 8, 12))
    finally:
        owner.close()


def test_inspection_runs_one_real_replay_and_measures_latency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        advance_time(owner, 32)
        calls: list[ReplayTrace] = []
        original = Runner.run

        def tracked(self: Runner, trace: ReplayTrace) -> object:
            calls.append(trace)
            return original(self, trace)

        monkeypatch.setattr(Runner, "run", tracked)
        started = time.perf_counter()
        update = owner.inspect_activity()
        elapsed = time.perf_counter() - started
        assert len(calls) == 1 and work_lines(update) == tuple(work_line(at) for at in (4, 8, 12))
        assert elapsed < 2, elapsed
        print(f"NPC_WORK_INSPECTION_LATENCY_MS {elapsed * 1000:.3f}")
    finally:
        owner.close()


@pytest.mark.parametrize("fault", ("hash", "io"))
def test_worker_source_failure_preserves_truth_and_recovers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    fault: str,
) -> None:
    selected = approved_content()
    worker = ClientWorker(
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_work=True,
    )
    try:
        worker.request("attach").result(30)
        before = worker.request("wait", seconds=16).result(30)
        before_bytes = Path(before.working_path).read_bytes()
        original = DurableSession.retained_segment

        def damaged(self: DurableSession) -> SaveSegment:
            if fault == "io":
                raise OSError("injected retained source read failure")
            segment = original(self)
            return replace(
                segment,
                trace=replace(
                    segment.trace,
                    steps=(replace(segment.trace.steps[0], expected_facts_hash="0" * 64),),
                ),
            )

        with monkeypatch.context() as scoped:
            scoped.setattr(DurableSession, "retained_segment", damaged)
            failed = worker.inspect_activity().result(30)
            assert failed.status == "NPC_ACTIVITY_SOURCE" and failed.view == before.view
            assert Path(before.working_path).read_bytes() == before_bytes
            assert "저장 근거를 읽지 못했습니다" in failed.messages[0]
            assert worker.request("retry").result(30).view == before.view
            assert worker.request("save").result(30).status == "SAVED"
        assert "NPC activity inspection failed" in caplog.text
        assert work_lines(worker.inspect_activity().result(30)) == tuple(
            work_line(at) for at in (4, 8, 12)
        )
    finally:
        worker.join()


@pytest.mark.parametrize("error_type", (KeyboardInterrupt, SystemExit))
def test_inspection_process_control_propagates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error_type: type[BaseException]
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("wait", seconds=4)
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )

        def interrupted(self: Runner, trace: ReplayTrace) -> object:
            raise error_type("injected process control")

        with monkeypatch.context() as scoped:
            scoped.setattr(Runner, "run", interrupted)
            with pytest.raises(error_type, match="injected process control"):
                owner.inspect_activity()
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
        assert work_lines(owner.inspect_activity()) == (work_line(4),)
    finally:
        owner.close()


def test_real_pipe_inspection_is_readonly_after_long_wait_and_reconnect(tmp_path: Path) -> None:
    working = tmp_path / "game.sqlite"
    with work_pipe(working) as pipe:
        pipe.send("attach")
        for _ in range(2):
            assert object_value(send_seconds(pipe, "wait", "16")["update"])["status"] == "COMMITTED"
        before = working.read_bytes()
        update = object_value(pipe.send("activity")["update"])
        messages = tuple(text_value(value) for value in array_value(update["messages"]))
        assert all(work_line(at) in messages for at in (4, 8, 12))
        assert object_value(update["view"])["tick"] == "32" and working.read_bytes() == before
    with work_pipe(working) as pipe:
        pipe.send("attach")
        update = object_value(pipe.send("activity")["update"])
        assert tuple(text_value(value) for value in array_value(update["messages"])) == messages


def test_real_tk_activity_button_displays_work_without_advancing(
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
        npc_work=True,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        assert screen.worker.request("wait", seconds=16).result(30).status == "COMMITTED"
        before = screen.worker.request("wait", seconds=16).result(30)
        assert before.status == "COMMITTED"
        screen._inspect_activity()
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None and screen.last_update.view == before.view
        assert work_lines(screen.last_update) == tuple(work_line(at) for at in (4, 8, 12))
        assert all(work_line(at) in screen.log_text.get("1.0", "end") for at in (4, 8, 12))
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
