"""Cycle activity separates retained event history from persistent own-action memory."""

from dataclasses import replace
from pathlib import Path
import time
import tkinter as tk

import pytest

from app.client import PlayWindow
from app.client_worker import ClientWorker
from app.durable import create_durable
from app.npc_cycle import cycle_bundle
import app.npc_activity as activity
from contracts.client import ClientUpdate
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.replay import ReplayFixture
from app.headless import replay_runner
from domain.canonical import array_value, object_value, text_value
from domain.npc_cycle import CycleRecord
from domain.primitives import EntityId
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_cycle_slot_comparison import inventory
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_cycle import cycle_pipe, session
from tests.integration.test_npc_self_activity import bell
from tests.integration.test_unity_wait_duration import send_seconds


def activity_rows(update: ClientUpdate) -> tuple[str, ...]:
    return tuple(m for m in update.messages if m.startswith("NPC 활동 기록 · "))


def test_cycle_activity_retains_bells_and_persisted_supply_readonly(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("wait", seconds=16)
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.attachment_id,
            inventory(tmp_path),
        )
        started = time.perf_counter()
        update = owner.inspect_activity()
        elapsed = time.perf_counter() - started
        assert activity_rows(update) == tuple(bell(t) for t in range(2, 17, 2))
        assert "전체 5개 중 최근 4개" in update.messages[1]
        assert any("NPC 작업 기억 · 10초:" in m and "사용" in m for m in update.messages)
        assert any("0초 이후" in m and "최근 최대 8개" in m for m in update.messages)
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.attachment_id,
            inventory(tmp_path),
        ) == before
        assert owner.retry().view == update.view
        (tmp_path / "latency.txt").write_text(str(elapsed), encoding="ascii")
    finally:
        owner.close()


def test_cycle_caps_and_same_tick_use_prepare_do_not_mix_with_bell_eviction(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("wait", seconds=16)
        owner.act("wait", seconds=4)
        update = owner.inspect_activity()
        assert activity_rows(update) == tuple(bell(t) for t in range(6, 21, 2))
        assert tuple(m for m in update.messages if m.startswith("NPC 작업 기억 · ")) == (
            "NPC 작업 기억 · 12초: 공동 물자 1개를 준비했습니다 · 물자 2/3개.",
            "NPC 작업 기억 · 16초: 공동 물자 1개를 준비했습니다 · 물자 3/3개.",
            "NPC 작업 기억 · 20초: 공동 물자 1개를 사용했습니다 · 물자 2/3개.",
            "NPC 작업 기억 · 20초: 공동 물자 1개를 준비했습니다 · 물자 3/3개.",
        )
        owner.act("wait", seconds=16)
        owner.act("wait", seconds=4)
        started = time.perf_counter()
        later = owner.inspect_activity()
        elapsed = time.perf_counter() - started
        assert activity_rows(later) == tuple(bell(t) for t in range(26, 41, 2))
        assert len(tuple(m for m in later.messages if m.startswith("NPC 작업 기억 · "))) == 4
        (tmp_path / "latency40.txt").write_text(str(elapsed), encoding="ascii")
    finally:
        owner.close()


def test_cycle_player_call_reply_and_bell_at_same_tick_are_distinct(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("bell")
        before = inventory(tmp_path)
        update = owner.inspect_activity()
        assert set(activity_rows(update)) == {
            bell(2),
            "NPC 활동 기록 · 2초: 호출에 응답했습니다. (누적 1회)",
        }
        assert len(activity_rows(update)) == 2
        assert update.view is not None and update.view.npc_replies == 1
        assert inventory(tmp_path) == before
    finally:
        owner.close()


def test_cycle_checkpoint_only_has_supply_but_never_fabricates_old_bells(tmp_path: Path) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        owner.act("wait", seconds=16)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        supply = owner.inspect_activity().messages[:6]
    finally:
        owner.close()
    path = tmp_path / "checkpoint/game.sqlite"
    durable = create_durable(path, checkpoint, bundles=(cycle_bundle(approved_content()),))
    durable.close()
    compacted = session(path)
    try:
        assert compacted.owner.retained_segment().trace.steps == ()
        before = compacted.owner.snapshot(), compacted.owner.protocol(), inventory(tmp_path)
        update = compacted.inspect_activity()
        assert update.messages[:6] == supply
        assert not activity_rows(update)
        assert any("16초 이후" in m for m in update.messages)
        assert "누적 횟수로 과거 활동을 추정하지 않습니다." in update.messages[-3]
        assert update.messages[-1] == "현재 저장 구간에 새로 확인된 호출 응답이 없습니다."
        assert update.view is not None and update.view.npc_bells == 8
        assert (
            compacted.owner.snapshot(),
            compacted.owner.protocol(),
            inventory(tmp_path),
        ) == before
        compacted.act("wait", seconds=4)
        assert activity_rows(compacted.inspect_activity()) == (bell(18), bell(20))
        segment = compacted.owner.retained_segment()
        fixture = ReplayFixture(segment.checkpoint.core, segment.checkpoint.protocol, segment.trace)
        assert (
            replay_runner(fixture, bundles=(cycle_bundle(approved_content()),)).run(segment.trace)
            == ()
        )
    finally:
        compacted.close()


def test_cycle_activity_previous_restore_restart_and_source_bytes(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("wait", seconds=16)
        earlier = owner.inspect_activity().messages
        owner.save("slot01")
        owner.act("wait", seconds=4)
        future = owner.inspect_activity().messages
        owner.save("slot01")
        sources = inventory(tmp_path)
        owner.load("slot01", previous=True)
        assert owner.inspect_activity().messages == earlier
        assert all((tmp_path / name).read_bytes() == data for name, data in sources.items())
        path = owner.owner.working_path
    finally:
        owner.close()
    resumed = session(path)
    try:
        assert resumed.inspect_activity().messages == earlier
        resumed.load("slot01")
        assert resumed.inspect_activity().messages == future
        assert all((tmp_path / name).read_bytes() == data for name, data in sources.items())
    finally:
        resumed.close()


@pytest.mark.parametrize("damage", ("owner", "trace", "core", "protocol", "missing_cycle"))
def test_cycle_activity_rejects_unverified_sources_without_mutation(
    tmp_path: Path, damage: str
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("wait", seconds=16)
        segment = owner.owner.retained_segment()
        current = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        npc_id = approved_content().definition.layout.npc_id
        if damage == "owner":
            npc_id = EntityId("npc:unknown")
        elif damage == "trace":
            segment = replace(
                segment,
                trace=replace(
                    segment.trace,
                    steps=(replace(segment.trace.steps[0], expected_facts_hash="0" * 64),),
                ),
            )
        elif damage == "core":
            current = replace(current, core=segment.checkpoint.core)
        elif damage == "protocol":
            current = replace(current, protocol=replace(current.protocol, branch_id="f" * 32))
        else:
            current = replace(
                current,
                core=replace(
                    current.core,
                    components=tuple(
                        r for r in current.core.components if type(r) is not CycleRecord
                    ),
                ),
            )
        before = owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)
        with pytest.raises(SaveError, match="^NPC_ACTIVITY_SOURCE:"):
            activity.cycle_activity_messages(
                segment, npc_id, content=approved_content(), current=current
            )
        assert (owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)) == before
    finally:
        owner.close()


def test_cycle_worker_source_error_retry_polling_and_process_control(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    from app.durable import DurableSession

    selected = approved_content()
    path = tmp_path / "game.sqlite"
    worker = ClientWorker(
        path, selected.definition.layout, quest_content=selected, npc_memory=True, npc_cycle=True
    )
    try:
        worker.request("attach").result(30)
        before = worker.request("wait", seconds=4).result(30)
        raw = inventory(tmp_path)
        with monkeypatch.context() as scoped:

            def unavailable(owner: DurableSession) -> None:
                raise OSError("injected retained activity read failure")

            scoped.setattr(DurableSession, "retained_segment", unavailable)
            failed = worker.inspect_activity().result(30)
            assert failed.status == "NPC_ACTIVITY_SOURCE" and failed.view == before.view
            assert worker.request("retry").result(30).view == before.view
        assert "NPC activity inspection failed" in caplog.text
        assert inventory(tmp_path) == raw
        with monkeypatch.context() as scoped:

            def fatal(owner: DurableSession) -> None:
                raise KeyboardInterrupt("cycle inspection interrupted")

            scoped.setattr(DurableSession, "retained_segment", fatal)
            with pytest.raises(KeyboardInterrupt, match="cycle inspection interrupted"):
                worker.inspect_activity().result(30)
        assert activity_rows(worker.inspect_activity().result(30)) == (bell(2), bell(4))
        assert worker.request("wait").result(30).status == "COMMITTED"
    finally:
        worker.join()


def test_cycle_actual_pipe_activity_source_scope_rewind_and_new_process(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with cycle_pipe(path) as pipe:
        send_seconds(pipe, "wait", "16")
        before = object_value(pipe.latest["update"])
        inspected = object_value(pipe.send("activity")["update"])
        messages = tuple(map(text_value, array_value(inspected["messages"])))
        assert tuple(m for m in messages if m.startswith("NPC 활동 기록 · ")) == tuple(
            bell(t) for t in range(2, 17, 2)
        )
        assert inspected["view"] == before["view"]
        pipe.send("save")
        send_seconds(pipe, "wait", "4")
        pipe.send("load")
        path = Path(text_value(object_value(pipe.latest["update"])["working_path"]))
    with cycle_pipe(path) as pipe:
        inspected = object_value(pipe.send("activity")["update"])
        assert tuple(map(text_value, array_value(inspected["messages"]))) == messages


def test_cycle_actual_tk_activity_keeps_both_sections_and_input(
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
        screen.wait_seconds.set("16")
        _click(screen, "wait")
        assert screen.activity_button is not None
        screen.activity_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None
        assert activity_rows(screen.last_update) == tuple(bell(t) for t in range(2, 17, 2))
        assert bell(16) in screen.log_text.get("1.0", "end")
        assert "NPC 작업 기억 · 10초:" in screen.log_text.get("1.0", "end")
        _click(screen, "retry")
        assert screen.last_update.view is not None and screen.last_update.view.tick == 16
        _click(screen, "save")
        assert screen.last_update.status == "SAVED"
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
