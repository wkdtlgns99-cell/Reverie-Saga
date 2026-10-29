"""Conversation summaries compare verified committed supply counters."""

from pathlib import Path
from dataclasses import replace
import time
import tkinter as tk

import pytest

import app.npc_activity as activity
from app.client import PlayWindow
from app.client_worker import ClientWorker
from app.durable import create_durable
from app.npc_cycle import cycle_bundle
from contracts.persistence import DurableCheckpoint
from contracts.replay import ReplaySession
from contracts.turn import ProtocolSnapshot
from domain.canonical import array_value, object_value, text_value
from domain.npc_cycle import CycleRecord, Supply
from domain.state_types import CoreSnapshot
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_cycle_slot_comparison import inventory
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_call_recollection import line, recalled

from tests.integration.test_npc_cycle import cycle, cycle_pipe, session
from tests.integration.test_unity_wait_duration import send_seconds


def summary(prepared: int, used: int) -> str:
    return f"확인한 물자 변화 · 준비 {prepared}회 · 사용 {used}회."


def test_cycle_return_reports_all_changes_since_last_talk_and_resets(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=16)
        owner.act("wait")
        update = owner.act("talk")
        assert update.view is not None and update.view.tick == 20
        assert "NPC 반복 작업 회상 · 지난 대화(2초) 뒤의 변화입니다." in update.messages
        assert summary(5, 2) in update.messages
        assert any("NPC 작업 기억 · 20초:" in m and "사용" in m for m in update.messages)
        assert any("NPC 작업 기억 · 20초:" in m and "준비" in m for m in update.messages)
        assert not any("확인한 물자 변화" in m for m in owner.retry().messages)
        update = owner.act("talk")
        assert "지난 대화(20초)" in "\n".join(update.messages)
        assert "현재 저장 구간에 새로 확인된 물자 변화가 없습니다." in update.messages
    finally:
        owner.close()


def test_cycle_change_counts_more_than_four_retained_anchors(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        for _ in range(5):
            owner.act("wait", seconds=16)
        update = owner.act("talk")
        assert update.view is not None and update.view.tick == 83
        assert summary(11, 8) in update.messages
        assert len(cycle(owner).entries) == 4
        assert "NPC 반복 작업 기억: 전체 19개 중 최근 4개를 보관합니다." in update.messages
        assert "NPC 반복 작업 회상 · 지난 대화(2초) 뒤의 변화입니다." in update.messages
    finally:
        owner.close()


def test_cycle_same_turn_work_is_included_once_not_next_talk(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        first = owner.act("talk")
        assert "NPC 반복 작업 회상 · 0초 이후 저장 구간의 변화입니다." in first.messages
        owner.act("wait")
        assert summary(1, 0) in owner.act("talk").messages  # tick4
        update = owner.act("talk")  # tick5,no new supply action
        assert summary(1, 0) not in update.messages
        assert "현재 저장 구간에 새로 확인된 물자 변화가 없습니다." in update.messages
    finally:
        owner.close()


def test_checkpoint_supply_counters_do_not_become_new_changes(tmp_path: Path) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=8)
        owner.act("wait", seconds=4)
        owner.act("wait")
        owner.act("wait")  # tick16
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        assert cycle(owner).state.produced == 4 and cycle(owner).state.consumed == 1
    finally:
        owner.close()
    path = tmp_path / "compacted/game.sqlite"
    durable = create_durable(path, checkpoint, bundles=(cycle_bundle(approved_content()),))
    durable.close()
    owner = session(path)
    try:
        update = owner.act("talk")
        assert "NPC 반복 작업 회상 · 16초 이후 저장 구간의 변화입니다." in update.messages
        assert "현재 저장 구간에 새로 확인된 물자 변화가 없습니다." in update.messages
        assert summary(4, 1) not in update.messages
        for _ in range(3):
            owner.act("wait")
        update = owner.act("talk")
        assert summary(1, 1) in update.messages
        assert "NPC 반복 작업 회상 · 지난 대화(17초) 뒤의 변화입니다." in update.messages
    finally:
        owner.close()


def test_cycle_change_rewind_previous_and_restart_preserve_sources(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=8)  # 10:prep2,use1
        owner.save("slot01")
        owner.act("wait", seconds=8)  # 18:prep4,use1
        owner.save("slot01")
        sources = inventory(tmp_path)
        owner.load("slot01", previous=True)
        path = owner.owner.working_path
    finally:
        owner.close()
    owner = session(path)
    try:
        assert summary(2, 1) in owner.act("talk").messages  # tick11
        owner.load("slot01")
        assert summary(4, 1) in owner.act("talk").messages  # tick19
        assert all((tmp_path / name).read_bytes() == data for name, data in sources.items())
    finally:
        owner.close()


def test_cycle_supply_summary_and_calls_share_one_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("bell")
        owner.act("wait", seconds=16)
        restore = activity._ActivityFactory.restore
        calls = []

        def observed(
            factory: activity._ActivityFactory, core: CoreSnapshot, protocol: ProtocolSnapshot
        ) -> ReplaySession:
            calls.append(1)
            return restore(factory, core, protocol)

        monkeypatch.setattr(activity._ActivityFactory, "restore", observed)
        started = time.perf_counter()
        update = owner.act("talk")  # 20
        elapsed = time.perf_counter() - started
        assert calls == [1] and summary(5, 2) in update.messages and recalled(update) == (line(3),)
        before = owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)
        assert not recalled(owner.retry()) and calls == [1]
        assert (owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)) == before
        (tmp_path / "latency.txt").write_text(str(elapsed), encoding="ascii")
    finally:
        owner.close()


def test_cycle_postcommit_missing_supply_source_and_interrupt_recover(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    selected = approved_content()
    worker = ClientWorker(
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_cycle=True,
    )
    original = activity._cycle_state
    try:
        worker.request("attach").result(30)
        worker.request("down").result(30)
        with monkeypatch.context() as scoped:

            def missing(core: CoreSnapshot, npc_id: str) -> Supply:
                return original(
                    replace(
                        core,
                        components=tuple(r for r in core.components if type(r) is not CycleRecord),
                    ),
                    npc_id,
                )

            scoped.setattr(activity, "_cycle_state", missing)
            failed = worker.request("talk").result(30)
            assert failed.status == "NPC_RECOLLECTION_SOURCE" and failed.view is not None
            assert failed.view.tick == 2 and failed.quest_stage == 1
            assert worker.request("retry").result(30).view == failed.view
            assert worker.request("save").result(30).status == "SAVED"
        assert "committed cycle call recollection failed" in caplog.text
        assert worker.request("talk").result(30).status == "COMMITTED"
        with monkeypatch.context() as scoped:

            def interrupted(core: CoreSnapshot, npc_id: str) -> Supply:
                raise KeyboardInterrupt("supply source interrupted")

            scoped.setattr(activity, "_cycle_state", interrupted)
            with pytest.raises(KeyboardInterrupt, match="supply source interrupted"):
                worker.request("talk").result(30)
        assert worker.request("retry").result(30).view is not None
        assert worker.request("save").result(30).status == "SAVED"
    finally:
        worker.join()


def test_cycle_supply_summary_reaches_pipe_across_load_restart(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with cycle_pipe(path) as pipe:
        pipe.send("down")
        pipe.send("talk")
        send_seconds(pipe, "wait", "8")
        pipe.send("save")
        send_seconds(pipe, "wait", "8")
        update = object_value(pipe.send("talk")["update"])
        assert summary(4, 1) in tuple(map(text_value, array_value(update["messages"])))
        loaded = object_value(pipe.send("load")["update"])
        path = Path(text_value(loaded["working_path"]))
    with cycle_pipe(path) as pipe:
        update = object_value(pipe.send("talk")["update"])
        messages = tuple(map(text_value, array_value(update["messages"])))
        assert summary(2, 1) in messages and summary(4, 1) not in messages


def test_cycle_supply_summary_displays_in_real_tk(tk_host: tk.Tk, tmp_path: Path) -> None:
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
        for action in ("down", "talk", "wait", "talk"):
            _click(screen, action)
        assert screen.last_update is not None and summary(1, 0) in screen.last_update.messages
        assert summary(1, 0) in screen.log_text.get("1.0", "end")
        _click(screen, "retry")
        assert summary(1, 0) not in screen.last_update.messages
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
