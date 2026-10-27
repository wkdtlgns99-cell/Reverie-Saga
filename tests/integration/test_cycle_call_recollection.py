"""Cycle talk recalls retained causal replies within the conversation boundary."""

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
from contracts.messages import WorldEvent
from contracts.persistence import DurableCheckpoint, SaveError, SaveSegment
from contracts.replay import ReplaySession
from contracts.turn import ProtocolSnapshot
from contracts.watch import WatchRequested
from domain.canonical import array_value, object_value, text_value
from domain.state_types import CoreSnapshot
from domain.primitives import Tick, WorldRevision
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_cycle_slot_comparison import inventory
from tests.integration.test_memory_client_route import approved_content

from tests.integration.test_npc_call_recollection import line, recalled
from tests.integration.test_npc_cycle import cycle_pipe, session


def test_cycle_talk_recalls_call_after_bells_and_then_resets(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        assert not recalled(owner.act("talk"))
        owner.act("down")
        owner.act("talk")
        assert not recalled(owner.act("bell"))
        owner.act("wait", seconds=16)
        update = owner.act("talk")
        assert recalled(update) == (line(3),)
        assert "NPC 호출 회상 · 지난 대화(2초) 뒤에 끝낸 응답입니다." in update.messages
        assert "확인한 호출 응답 1건 중 최근 1건입니다." in update.messages
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        assert not recalled(owner.retry())
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
        assert not recalled(owner.act("talk"))
        assert recalled(owner.inspect_activity()) == (line(3),)
    finally:
        owner.close()


def test_cycle_counts_all_calls_retains_three_and_only_new_conversation_range(
    tmp_path: Path,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        for _ in range(5):
            owner.act("bell")
            owner.retry()
        update = owner.act("talk")
        assert recalled(update) == (line(5), line(6), line(7))
        assert "확인한 호출 응답 5건 중 최근 3건입니다." in update.messages
        owner.act("bell")
        update = owner.act("talk")
        assert recalled(update) == (line(9),)
        assert "NPC 호출 회상 · 지난 대화(8초) 뒤에 끝낸 응답입니다." in update.messages
        assert "확인한 호출 응답 1건 중 최근 1건입니다." in update.messages
    finally:
        owner.close()


def test_cycle_first_talk_and_checkpoint_only_never_invent_calls(tmp_path: Path) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        for _ in range(5):
            owner.act("bell")
        owner.act("down")
        update = owner.act("talk")
        assert recalled(update) == (line(3), line(4), line(5))
        assert "NPC 호출 회상 · 현재 저장 구간에서 확인한 응답입니다." in update.messages
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    path = tmp_path / "compacted/game.sqlite"
    durable = create_durable(path, checkpoint, bundles=(cycle_bundle(approved_content()),))
    durable.close()
    owner = session(path)
    try:
        update = owner.act("talk")  # tick8;persisted replies5,none retained
        assert update.view is not None and update.view.npc_replies == 5
        assert not recalled(update)
        assert "현재 저장 구간에 새로 확인된 호출 응답이 없습니다." in update.messages
        owner.act("bell")
        assert recalled(owner.act("talk")) == (line(9),)
    finally:
        owner.close()


def test_cycle_rewind_restart_retains_only_selected_branch_calls(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("bell")
        owner.save("slot01")
        owner.act("bell")
        owner.save("slot01")
        sources = inventory(tmp_path)
        owner.load("slot01", previous=True)
        path = owner.owner.working_path
    finally:
        owner.close()
    owner = session(path)
    try:
        assert recalled(owner.act("talk")) == (line(3),)
        owner.load("slot01")
        assert recalled(owner.act("talk")) == (line(3), line(4))
        assert all((tmp_path / name).read_bytes() == data for name, data in sources.items())
    finally:
        owner.close()


def test_cycle_talk_one_replay_retry_zero_and_measure_latency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("bell")
        owner.act("wait", seconds=16)
        owner.act("down")
        restore = activity._ActivityFactory.restore
        calls = []

        def observed(
            factory: activity._ActivityFactory, core: CoreSnapshot, protocol: ProtocolSnapshot
        ) -> ReplaySession:
            calls.append(1)
            return restore(factory, core, protocol)

        monkeypatch.setattr(activity._ActivityFactory, "restore", observed)
        start = time.perf_counter()
        update = owner.act("talk")
        elapsed = time.perf_counter() - start
        assert calls == [1] and recalled(update) == (line(1),)
        before = owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)
        assert not recalled(owner.retry()) and calls == [1]
        assert (owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)) == before
        (tmp_path / "latency.txt").write_text(str(elapsed), encoding="ascii")
    finally:
        owner.close()


def test_cycle_postcommit_causal_error_preserves_truth_and_worker_recovers(
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
        worker.request("down").result(30)
        worker.request("bell").result(30)
        with monkeypatch.context() as scoped:

            def broken(
                reply: WorldEvent, facts: tuple[WorldEvent, ...], actor: str
            ) -> activity._AnsweredCall:
                return original(
                    reply,
                    tuple(e for e in facts if not isinstance(e.payload, WatchRequested)),
                    actor,
                )

            scoped.setattr(activity, "_answered_call", broken)
            failed = worker.request("talk").result(30)
            assert failed.status == "NPC_RECOLLECTION_SOURCE" and failed.view is not None
            assert failed.view.tick == 3 and failed.quest_stage == 1
            assert "행동은 확정됐지만" in failed.messages[0]
            assert worker.request("retry").result(30).view == failed.view
            assert worker.request("save").result(30).status == "SAVED"
        assert "committed cycle call recollection failed" in caplog.text
        assert worker.request("talk").result(30).status == "COMMITTED"
        with monkeypatch.context() as scoped:

            def interrupted(
                reply: WorldEvent, facts: tuple[WorldEvent, ...], actor: str
            ) -> activity._AnsweredCall:
                raise KeyboardInterrupt("cycle call interrupted")

            scoped.setattr(activity, "_answered_call", interrupted)
            with pytest.raises(KeyboardInterrupt, match="cycle call interrupted"):
                worker.request("talk").result(30)
        assert worker.request("retry").result(30).view is not None
        assert worker.request("save").result(30).status == "SAVED"
    finally:
        worker.join()


def test_cycle_pipe_talk_recall_load_and_new_process(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with cycle_pipe(path) as pipe:
        pipe.send("down")
        pipe.send("talk")
        pipe.send("bell")
        pipe.send("save")
        pipe.send("bell")
        update = object_value(pipe.send("talk")["update"])
        assert line(4) in tuple(map(text_value, array_value(update["messages"])))
        loaded = object_value(pipe.send("load")["update"])
        path = Path(text_value(loaded["working_path"]))
    with cycle_pipe(path) as pipe:
        update = object_value(pipe.send("talk")["update"])
        messages = tuple(map(text_value, array_value(update["messages"])))
        assert line(3) in messages and line(4) not in messages


def test_cycle_real_tk_talk_displays_call_recall(tk_host: tk.Tk, tmp_path: Path) -> None:
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
        for action in ("down", "talk", "bell", "talk"):
            _click(screen, action)
        assert screen.last_update is not None and recalled(screen.last_update) == (line(3),)
        assert line(3) in screen.log_text.get("1.0", "end")
        _click(screen, "retry")
        assert not recalled(screen.last_update)
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())


@pytest.mark.parametrize("fault", ("owner", "conversation", "core", "protocol"))
def test_cycle_recollection_rejects_wrong_source_without_mutation(
    tmp_path: Path, fault: str
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("bell")
        owner.act("talk")
        segment = owner.owner.retained_segment()
        current = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        if fault == "core":
            current = replace(current, core=replace(current.core, tick=Tick(current.core.tick + 1)))
        if fault == "protocol":
            current = replace(
                current,
                protocol=replace(
                    current.protocol, revision=WorldRevision(current.protocol.revision + 1)
                ),
            )
        selected = approved_content()
        before = owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)
        with pytest.raises(SaveError) as caught:
            activity.cycle_call_recollection(
                segment,
                "unknown" if fault == "owner" else selected.definition.layout.npc_id,
                content=selected,
                current=current,
                conversation_id="missing-current-talk",
            )
        assert caught.value.code == "NPC_RECOLLECTION_SOURCE"
        assert (owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)) == before
    finally:
        owner.close()


def test_cycle_call_source_io_failure_keeps_commit_retry_and_save(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        with monkeypatch.context() as scoped:

            def unavailable() -> SaveSegment:
                raise OSError("retained source unavailable")

            scoped.setattr(owner.owner, "retained_segment", unavailable)
            with pytest.raises(SaveError) as caught:
                owner.act("talk")
            assert caught.value.code == "NPC_RECOLLECTION_SOURCE"
            assert owner.owner.snapshot().tick == 2 and owner.update().quest_stage == 1
            assert not recalled(owner.retry())
            assert owner.save("slot01").status == "SAVED"
        assert "committed cycle call recollection failed" in caplog.text
        assert owner.act("talk").status == "COMMITTED"
    finally:
        owner.close()
