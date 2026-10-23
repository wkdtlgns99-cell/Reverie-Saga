"""Cycle inspection keeps causal calls independently of mixed events and conversations."""

from pathlib import Path
import time
import tkinter as tk

import pytest

import app.npc_activity as activity
from app.client import PlayWindow
from app.client_worker import ClientWorker
from app.durable import create_durable
from app.npc_cycle import cycle_bundle
from contracts.messages import WorldEvent
from contracts.persistence import DurableCheckpoint
from contracts.replay import ReplaySession
from contracts.turn import ProtocolSnapshot
from contracts.watch import WatchRequested
from domain.canonical import array_value, object_value, text_value
from domain.state_types import CoreSnapshot
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_cycle_slot_comparison import inventory
from tests.integration.test_memory_client_route import approved_content

from tests.integration.test_npc_call_recollection import line, recalled
from tests.integration.test_npc_cycle import cycle_pipe, session


def test_cycle_inspection_keeps_actual_call_after_bell_eviction(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("bell")
        owner.act("wait", seconds=16)
        update = owner.inspect_activity()
        assert recalled(update) == (line(1),)
        assert "확인한 호출 응답 1건 중 최근 1건입니다." in update.messages
        assert not any(m.startswith("NPC 활동 기록 · 1초:") for m in update.messages)
    finally:
        owner.close()


def test_cycle_calls_count_all_but_keep_three_independent_of_talk(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        for _ in range(5):
            owner.act("bell")
            owner.retry()
        owner.act("down")
        owner.act("talk")
        update = owner.inspect_activity()
        assert recalled(update) == (line(3), line(4), line(5))
        assert "확인한 호출 응답 5건 중 최근 3건입니다." in update.messages
        assert "NPC 호출 회상 · 현재 저장 구간에서 확인한 응답입니다." in update.messages
        assert not any("지난 대화" in message for message in update.messages)
        assert update.view is not None and update.view.npc_replies == 5
        assert any("NPC 작업 기억 · 4초:" in message for message in update.messages)
    finally:
        owner.close()


def test_cycle_checkpoint_does_not_invent_calls_from_persisted_count(tmp_path: Path) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        for _ in range(5):
            owner.act("bell")
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    path = tmp_path / "compacted/game.sqlite"
    durable = create_durable(path, checkpoint, bundles=(cycle_bundle(approved_content()),))
    durable.close()
    compacted = session(path)
    try:
        before = inventory(tmp_path)
        update = compacted.inspect_activity()
        assert update.view is not None and update.view.npc_replies == 5
        assert not recalled(update)
        assert "현재 저장 구간에 새로 확인된 호출 응답이 없습니다." in update.messages
        assert any("5초 이후" in message for message in update.messages)
        assert inventory(tmp_path) == before
        compacted.act("bell")
        update = compacted.inspect_activity()
        assert recalled(update) == (line(6),)
        assert "확인한 호출 응답 1건 중 최근 1건입니다." in update.messages
        assert update.view is not None and update.view.npc_replies == 6
    finally:
        compacted.close()


def test_cycle_previous_restore_restart_only_shows_selected_branch_calls(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("bell")
        owner.save("slot01")
        owner.act("bell")
        owner.save("slot01")
        sources = inventory(tmp_path)
        assert recalled(owner.inspect_activity()) == (line(1), line(2))
        owner.load("slot01", previous=True)
        assert recalled(owner.inspect_activity()) == (line(1),)
        path = owner.owner.working_path
    finally:
        owner.close()
    resumed = session(path)
    try:
        assert recalled(resumed.inspect_activity()) == (line(1),)
        resumed.act("wait")
        resumed.act("bell")
        assert recalled(resumed.inspect_activity()) == (line(1), line(3))
        resumed.load("slot01")
        assert recalled(resumed.inspect_activity()) == (line(1), line(2))
        assert all((tmp_path / name).read_bytes() == data for name, data in sources.items())
    finally:
        resumed.close()


def test_cycle_links_share_one_replay_and_preserve_live_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("bell")
        owner.act("wait", seconds=16)
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.attachment_id,
            owner.owner.retained_segment(),
            inventory(tmp_path),
        )
        restore = activity._ActivityFactory.restore
        calls = []

        def observed(
            factory: activity._ActivityFactory, core: CoreSnapshot, protocol: ProtocolSnapshot
        ) -> ReplaySession:
            calls.append(1)
            return restore(factory, core, protocol)

        monkeypatch.setattr(activity._ActivityFactory, "restore", observed)
        start = time.perf_counter()
        update = owner.inspect_activity()
        elapsed = time.perf_counter() - start
        assert calls == [1] and recalled(update) == (line(1),)
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.attachment_id,
            owner.owner.retained_segment(),
            inventory(tmp_path),
        ) == before
        assert owner.retry().view == update.view
        (tmp_path / "latency.txt").write_text(str(elapsed), encoding="ascii")
    finally:
        owner.close()


def test_cycle_causal_failure_is_activity_error_and_worker_recovers(
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
    original = activity._answered_call
    try:
        worker.request("attach").result(30)
        committed = worker.request("bell").result(30)
        before = inventory(tmp_path)
        with monkeypatch.context() as scoped:

            def broken(
                reply: WorldEvent, facts: tuple[WorldEvent, ...], actor: str
            ) -> activity._AnsweredCall:
                # Exercise the real selector with an incomplete observed causal chain.
                return original(
                    reply,
                    tuple(e for e in facts if not isinstance(e.payload, WatchRequested)),
                    actor,
                )

            scoped.setattr(activity, "_answered_call", broken)
            failed = worker.inspect_activity().result(30)
            assert failed.status == "NPC_ACTIVITY_SOURCE" and failed.view == committed.view
            assert inventory(tmp_path) == before
            assert "NPC activity inspection failed" in caplog.text
            assert worker.request("retry").result(30).view == committed.view
        assert recalled(worker.inspect_activity().result(30)) == (line(1),)
        with monkeypatch.context() as scoped:

            def interrupted(
                reply: WorldEvent, facts: tuple[WorldEvent, ...], actor: str
            ) -> activity._AnsweredCall:
                raise KeyboardInterrupt("call inspection interrupted")

            scoped.setattr(activity, "_answered_call", interrupted)
            with pytest.raises(KeyboardInterrupt, match="call inspection interrupted"):
                worker.inspect_activity().result(30)
        assert worker.request("save").result(30).status == "SAVED"
        assert recalled(worker.inspect_activity().result(30)) == (line(1),)
    finally:
        worker.join()


def test_cycle_pipe_links_survive_load_and_new_process(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with cycle_pipe(path) as pipe:
        pipe.send("bell")
        pipe.send("save")
        pipe.send("bell")
        update = object_value(pipe.send("activity")["update"])
        assert line(2) in tuple(map(text_value, array_value(update["messages"])))
        loaded = object_value(pipe.send("load")["update"])
        path = Path(text_value(loaded["working_path"]))
    with cycle_pipe(path) as pipe:
        update = object_value(pipe.send("activity")["update"])
        lines = tuple(map(text_value, array_value(update["messages"])))
        assert line(1) in lines and line(2) not in lines


def test_cycle_real_tk_displays_causal_call_links(tk_host: tk.Tk, tmp_path: Path) -> None:
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
        _click(screen, "bell")
        assert screen.activity_button is not None
        screen.activity_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None and recalled(screen.last_update) == (line(1),)
        assert line(1) in screen.log_text.get("1.0", "end")
        _click(screen, "retry")
        assert screen.last_update.view is not None and screen.last_update.view.tick == 1
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
