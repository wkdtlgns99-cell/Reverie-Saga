from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import time
import tkinter as tk

import pytest

from app.client import PlayWindow
from app.client_worker import ClientWorker
from app.durable import create_durable
from app.headless import restore_checkpoint
from app.npc_activity import return_recollection
from app.npc_work import work_bundle
from contracts.client import ClientUpdate
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.replay import ReplaySession
from contracts.turn import ProtocolSnapshot
from contracts.watch import WatchEcho, WatchReplied, WatchRequested
from domain.canonical import array_value, object_value, text_value
from domain.primitives import EntityId, EventId, Tick
from domain.state_types import CoreSnapshot
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_work import session, work_pipe
from tests.integration.test_npc_work_recollection import current_talk


def line(tick: int) -> str:
    return f"NPC 호출 회상 · {tick}초의 플레이어 호출에 {tick}초에 응답했습니다."


def recalled(update: ClientUpdate) -> tuple[str, ...]:
    return tuple(message for message in update.messages if "초의 플레이어 호출에" in message)


def test_return_remembers_actual_old_call_after_mixed_activity_trimming(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        rejected = owner.act("talk")
        assert rejected.status == "OUT_OF_RANGE" and not recalled(rejected)
        owner.act("down")
        first = owner.act("talk")
        assert "현재 저장 구간에 새로 확인된 호출 응답이 없습니다." in first.messages
        assert "NPC 호출 회상 · 현재 저장 구간에서 확인한 응답입니다." in first.messages
        assert not recalled(owner.act("bell"))  # request3/reply3,not a conversation
        owner.act("wait", seconds=16)
        assert not any("3초:" in message for message in owner.inspect_activity().messages)
        update = owner.act("talk")
        assert update.view is not None and update.view.tick == 20
        assert recalled(update) == (line(3),)
        assert "NPC 호출 회상 · 지난 대화(2초) 뒤에 끝낸 응답입니다." in update.messages
        assert "확인한 호출 응답 1건 중 최근 1건입니다." in update.messages
        assert update.messages[-1] == "NPC 공동 비축: 물자 3/3개 · 가득 차 작업을 멈췄습니다."
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
        assert "현재 저장 구간에 새로 확인된 호출 응답이 없습니다." in owner.act("talk").messages
    finally:
        owner.close()


def test_latest_three_calls_count_entire_range_and_then_reset_on_conversation(
    tmp_path: Path,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        for _ in range(5):
            assert owner.act("bell").status == "COMMITTED"
            owner.retry()  # no new response or extra turn
        update = owner.act("talk")
        assert recalled(update) == (line(5), line(6), line(7))
        assert "확인한 호출 응답 5건 중 최근 3건입니다." in update.messages
        owner.act("bell")  # tick9
        update = owner.act("talk")
        assert recalled(update) == (line(9),)
        assert "확인한 호출 응답 1건 중 최근 1건입니다." in update.messages
        assert "NPC 호출 회상 · 지난 대화(8초) 뒤에 끝낸 응답입니다." in update.messages
    finally:
        owner.close()


def test_first_talk_after_call_and_checkpoint_never_reconstructs_lost_history(
    tmp_path: Path,
) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        owner.act("bell")  # reachable across space without adjacency;actual existing rule
        owner.act("down")
        update = owner.act("talk")
        assert recalled(update) == (line(1),)
        assert "NPC 호출 회상 · 현재 저장 구간에서 확인한 응답입니다." in update.messages
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    path = tmp_path / "compacted/game.sqlite"
    durable = create_durable(path, checkpoint, bundles=(work_bundle(approved_content()),))
    durable.close()
    compacted = session(path)
    try:
        update = compacted.act("talk")
        assert update.view is not None and update.view.npc_replies == 1
        assert not recalled(update)
        assert "현재 저장 구간에 새로 확인된 호출 응답이 없습니다." in update.messages
        assert "NPC 호출 회상 · 현재 저장 구간에서 확인한 응답입니다." in update.messages
    finally:
        compacted.close()


def test_save_load_restart_recall_only_loaded_branch_calls(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")  # 2
        owner.act("bell")  # 3
        owner.act("wait")  # 4
        owner.save("slot01")
        owner.act("bell")  # 5
        assert recalled(owner.act("talk")) == (line(3), line(5))
        owner.load("slot01")
        working = owner.owner.working_path
    finally:
        owner.close()
    resumed = session(working)
    try:
        assert recalled(resumed.act("talk")) == (line(3),)
        resumed.act("bell")  # 6onnewbranch
        assert recalled(resumed.act("talk")) == (line(6),)
    finally:
        resumed.close()


@pytest.mark.parametrize(
    "damage", ("hash", "header", "current", "owner", "conversation", "not_talk")
)
def test_combined_recollection_rejects_bad_sources_and_preserves_save(
    tmp_path: Path, damage: str
) -> None:
    selected = approved_content()
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("bell")
        owner.act("talk")
        segment, identity = current_talk(owner)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        npc = selected.definition.layout.npc_id
        if damage == "hash":
            segment = replace(
                segment,
                trace=replace(
                    segment.trace,
                    steps=(
                        replace(segment.trace.steps[0], expected_facts_hash="0" * 64),
                        *segment.trace.steps[1:],
                    ),
                ),
            )
        elif damage == "header":
            segment = replace(
                segment,
                trace=replace(
                    segment.trace, header=replace(segment.trace.header, initial_core_hash="0" * 64)
                ),
            )
        elif damage == "current":
            checkpoint = segment.checkpoint
        elif damage == "owner":
            npc = EntityId("actor:other")
        elif damage == "conversation":
            identity = "e1-" + "0" * 64
        else:
            owner.act("bell")
            segment = owner.owner.retained_segment()
            checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        with pytest.raises(SaveError, match="^NPC_RECOLLECTION_SOURCE:"):
            return_recollection(
                segment, npc, content=selected, current=checkpoint, conversation_id=identity
            )
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
    finally:
        owner.close()


def test_combined_recollection_readonly_one_replay_and_latency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.npc_activity import _ActivityFactory

    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("bell")
        owner.act("wait", seconds=16)
        owner.act("talk")
        segment, identity = current_talk(owner)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        original = _ActivityFactory.restore
        restores = []

        def observed_restore(
            self: _ActivityFactory, core: CoreSnapshot, protocol: ProtocolSnapshot
        ) -> ReplaySession:
            restores.append(1)
            return original(self, core, protocol)

        monkeypatch.setattr(_ActivityFactory, "restore", observed_restore)
        started = time.perf_counter()
        result = return_recollection(
            segment,
            approved_content().definition.layout.npc_id,
            content=approved_content(),
            current=checkpoint,
            conversation_id=identity,
        )
        elapsed = time.perf_counter() - started
        assert line(2) in result and "NPC 작업 회상 · 12초: 물자 1개를 준비했습니다." in result
        assert restores == [1] and elapsed < 2
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
        (tmp_path / "latency.txt").write_text(str(elapsed), encoding="ascii")
    finally:
        owner.close()


@pytest.mark.parametrize(
    "damage", ("missing", "multiple", "other_actor", "other_npc", "wrong_tick", "cycle")
)
def test_causal_projection_rejects_incomplete_or_unrelated_actual_chain(
    tmp_path: Path, damage: str
) -> None:
    from app.npc_activity import _answered_call

    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("bell")
        segment = owner.owner.retained_segment()
        replay = restore_checkpoint(
            segment.checkpoint.core,
            segment.checkpoint.protocol,
            bundles=(work_bundle(approved_content()),),
        )
        replay.driver.submit(segment.trace.steps[0].command)
        facts = replay.last_publication().facts
        reply = next(event for event in facts if isinstance(event.payload, WatchReplied))
        actor = approved_content().definition.layout.actor_id
        actual = _answered_call(reply, facts, actor)
        assert isinstance(actual.request.payload, WatchRequested)
        assert actual.request.payload.actor_id == actor
        assert actual.request.due_tick == reply.due_tick == 1
        if damage == "missing":
            facts = tuple(event for event in facts if event != actual.request)
        elif damage == "multiple":
            reply = replace(
                reply,
                header=replace(
                    reply.header, caused_by=(actual.request.header.event_id, EventId("other"))
                ),
            )
        elif damage == "other_actor":
            actor = EntityId("actor:other")
        elif damage == "other_npc":
            facts = tuple(
                replace(event, payload=replace(event.payload, npc_id=EntityId("actor:other")))
                if isinstance(event.payload, WatchEcho)
                else event
                for event in facts
            )
        elif damage == "wrong_tick":
            facts = tuple(
                replace(event, due_tick=Tick(2)) if event == actual.request else event
                for event in facts
            )
        else:
            facts = tuple(
                replace(event, header=replace(event.header, caused_by=(event.header.event_id,)))
                if isinstance(event.payload, WatchEcho)
                else event
                for event in facts
            )
        with pytest.raises(SaveError, match="^NPC_RECOLLECTION_SOURCE: response lacks"):
            _answered_call(reply, facts, actor)
    finally:
        owner.close()


def test_failed_call_projection_reports_committed_state_and_recovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import app.npc_activity as activity

    selected = approved_content()
    worker = ClientWorker(
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_work=True,
    )
    try:
        worker.request("attach").result(timeout=30)
        worker.request("down").result(timeout=30)
        worker.request("talk").result(timeout=30)
        worker.request("bell").result(timeout=30)
        with monkeypatch.context() as scoped:

            def unavailable(*args: object) -> object:
                raise SaveError("NPC_RECOLLECTION_SOURCE", "injected projection failure")

            scoped.setattr(activity, "_answered_call", unavailable)
            failed = worker.request("talk").result(timeout=30)
            assert failed.status == "NPC_RECOLLECTION_SOURCE" and failed.view is not None
            assert failed.view.tick == 4 and failed.view.npc_replies == 1
            assert "행동은 확정됐지만" in failed.messages[0]
            assert worker.request("retry").result(timeout=30).view == failed.view
            assert worker.request("save").result(timeout=30).status == "SAVED"
        assert "committed NPC talk recollection failed" in caplog.text
        # The failed display was still a committed conversation;never reattribute call3 to talk5.
        recovered = worker.request("talk").result(timeout=30)
        assert recovered.status == "COMMITTED" and not recalled(recovered)
        assert "NPC 호출 회상 · 지난 대화(4초) 뒤에 끝낸 응답입니다." in recovered.messages
    finally:
        worker.join()


def test_real_pipe_call_recollection_reconnect_and_load(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with work_pipe(path) as pipe:
        pipe.send("attach")
        pipe.send("down")
        pipe.send("talk")
        pipe.send("bell")
        pipe.send("save")
        messages = array_value(object_value(pipe.send("talk")["update"])["messages"])
        assert line(3) in tuple(map(text_value, messages))
        pipe.send("bell")
        pipe.send("load")
        path = Path(text_value(object_value(pipe.latest["update"])["working_path"]))
    with work_pipe(path) as pipe:
        pipe.send("attach")
        update = object_value(pipe.send("talk")["update"])
        assert line(3) in tuple(map(text_value, array_value(update["messages"])))
        update = object_value(pipe.send("talk")["update"])
        assert not any(
            "초의 플레이어 호출에" in text_value(v) for v in array_value(update["messages"])
        )


def test_actual_tk_return_recalls_call(tk_host: tk.Tk, tmp_path: Path) -> None:
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
        for action in ("down", "talk", "bell", "wait", "talk"):
            _click(screen, action)
        assert screen.last_update is not None and recalled(screen.last_update) == (line(3),)
        _click(screen, "talk")
        assert screen.last_update is not None and not recalled(screen.last_update)
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
