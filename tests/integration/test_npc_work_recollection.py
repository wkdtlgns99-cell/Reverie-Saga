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
from app.headless import restore_checkpoint
from app.npc_activity import work_recollection
from app.npc_work import work_bundle
from contracts.client import ClientUpdate
from contracts.persistence import DurableCheckpoint, SaveError, SaveSegment
from contracts.quest import QuestSpoken
from domain.primitives import EntityId
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_work import session, stock, work_pipe
from tests.integration.test_unity_wait_duration import send_seconds
from domain.canonical import array_value, object_value, text_value


def recalled(update: ClientUpdate) -> tuple[str, ...]:
    return tuple(
        line for line in update.messages if line.startswith("NPC 작업 회상 · ") and "초:" in line
    )


def line(tick: int) -> str:
    return f"NPC 작업 회상 · {tick}초: 물자 1개를 준비했습니다."


def current_talk(owner: ClientSession) -> tuple[SaveSegment, str]:
    segment = owner.owner.retained_segment()
    replay = restore_checkpoint(
        segment.checkpoint.core,
        segment.checkpoint.protocol,
        bundles=(work_bundle(approved_content()),),
    )
    for step in segment.trace.steps:
        replay.driver.submit(step.command)
    return segment, next(
        event.header.event_id
        for event in replay.last_publication().facts
        if isinstance(event.payload, QuestSpoken)
    )


def test_return_recalls_only_work_since_previous_conversation_and_retry_is_quiet(
    tmp_path: Path,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        first = owner.act("talk")
        assert recalled(first) == ()
        assert "NPC 작업 회상 · 현재 저장 구간에서 확인한 작업입니다." in first.messages
        assert "현재 저장 구간에 새로 확인된 비축 작업이 없습니다." in first.messages
        owner.act("wait", seconds=4)
        owner.save("slot01")  # tick6/stock1,previous talk2
        returned = owner.act("talk")
        assert recalled(returned) == (line(4),)
        assert "NPC 작업 회상 · 지난 대화(2초) 뒤에 끝낸 작업입니다." in returned.messages
        owner.act("wait", seconds=8)
        returned = owner.act("talk")
        assert recalled(returned) == (line(8), line(12))
        assert "NPC 작업 회상 · 지난 대화(7초) 뒤에 끝낸 작업입니다." in returned.messages
        assert stock(owner) == 3
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        retried = owner.retry()
        assert not any("작업 회상" in message for message in retried.messages)
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
        empty = owner.act("talk")
        assert recalled(empty) == () and "지난 대화(16초)" in "\n".join(empty.messages)
        assert "현재 저장 구간에 새로 확인된 비축 작업이 없습니다." in empty.messages
        owner.load("slot01")
        restored = owner.act("talk")
        assert recalled(restored) == (line(4),)
        working = owner.owner.working_path
    finally:
        owner.close()
    resumed = session(working)
    try:
        # tick8production belongs to this new conversation,not the previous tick7one.
        newer = resumed.act("talk")
        assert recalled(newer) == (line(8),)
        assert "지난 대화(7초)" in "\n".join(newer.messages)
    finally:
        resumed.close()


def test_first_return_after_many_bells_keeps_all_actual_work_not_mixed_recent8(
    tmp_path: Path,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=16)
        mixed = owner.inspect_activity()
        assert not any(message.startswith("NPC 활동 기록 · 4초:") for message in mixed.messages)
        returned = owner.act("talk")
        assert recalled(returned) == (line(4), line(8), line(12))
        assert all("적" not in message and "보상" not in message for message in recalled(returned))
        assert (returned.quest_stage, returned.quest_reward, stock(owner)) == (1, 0, 3)
    finally:
        owner.close()


def test_same_turn_production_is_recalled_once(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("wait", seconds=2)
        at_four = owner.act("talk")
        assert at_four.view is not None and at_four.view.tick == 4
        assert recalled(at_four) == (line(4),)
        assert recalled(owner.act("talk")) == ()
    finally:
        owner.close()


def test_checkpoint_without_old_trace_never_invents_work_from_full_stock(tmp_path: Path) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        owner.act("down")
        owner.act("wait", seconds=16)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    path = tmp_path / "compacted/game.sqlite"
    durable = create_durable(path, checkpoint, bundles=(work_bundle(approved_content()),))
    durable.close()
    compacted = session(path)
    try:
        update = compacted.act("talk")
        assert stock(compacted) == 3 and recalled(update) == ()
        assert "NPC 작업 회상 · 현재 저장 구간에서 확인한 작업입니다." in update.messages
        assert "현재 저장 구간에 새로 확인된 비축 작업이 없습니다." in update.messages
    finally:
        compacted.close()


@pytest.mark.parametrize(
    "damage", ("hash", "header", "current", "owner", "conversation", "not_talk")
)
def test_recollection_rejects_unverified_sources_without_source_mutation(
    tmp_path: Path, damage: str
) -> None:
    selected = approved_content()
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("wait", seconds=4)
        owner.act("talk")
        segment, identity = current_talk(owner)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        npc = selected.definition.layout.npc_id
        if damage == "hash":
            steps = (
                replace(segment.trace.steps[0], expected_facts_hash="0" * 64),
                *segment.trace.steps[1:],
            )
            segment = replace(segment, trace=replace(segment.trace, steps=steps))
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
            owner.act("wait")
            segment = owner.owner.retained_segment()
            checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        with pytest.raises(SaveError, match="^NPC_RECOLLECTION_SOURCE:"):
            work_recollection(
                segment, npc, content=selected, current=checkpoint, conversation_id=identity
            )
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
    finally:
        owner.close()


def test_recollection_readonly_and_measured_latency(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("wait", seconds=16)
        owner.act("talk")
        segment, identity = current_talk(owner)
        current = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        started = time.perf_counter()
        result = work_recollection(
            segment,
            approved_content().definition.layout.npc_id,
            content=approved_content(),
            current=current,
            conversation_id=identity,
        )
        elapsed = time.perf_counter() - started
        assert result[1:] == (line(4), line(8), line(12))
        assert elapsed < 2, elapsed
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
        (tmp_path / "latency.txt").write_text(str(elapsed), encoding="ascii")
    finally:
        owner.close()


def test_postcommit_read_failure_reconciles_truth_and_keeps_retry_save_close(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
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
        worker.request("attach").result(timeout=30)
        worker.request("down").result(timeout=30)

        def unavailable(self: DurableSession) -> SaveSegment:
            raise SaveError("SAVE_UNAVAILABLE", "injected read-only segment failure")

        with monkeypatch.context() as scoped:
            scoped.setattr(DurableSession, "retained_segment", unavailable)
            failed = worker.request("talk").result(timeout=30)
            assert failed.status == "NPC_RECOLLECTION_SOURCE" and failed.view is not None
            assert failed.view.tick == 2 and failed.quest_stage == 1
            assert "행동은 확정됐지만" in failed.messages[0]
            assert worker.request("retry").result(timeout=30).view == failed.view
            assert worker.request("save").result(timeout=30).status == "SAVED"
        assert "committed NPC talk recollection failed" in caplog.text
        next_talk = worker.request("talk").result(timeout=30)
        assert next_talk.status == "COMMITTED" and "지난 대화(2초)" in "\n".join(next_talk.messages)
    finally:
        worker.join()


def test_real_pipe_return_and_reconnect_use_their_conversation_source(tmp_path: Path) -> None:
    working = tmp_path / "game.sqlite"
    with work_pipe(working) as pipe:
        pipe.send("attach")
        pipe.send("down")
        pipe.send("talk")
        send_seconds(pipe, "wait", "16")
        update = object_value(pipe.send("talk")["update"])
        messages = tuple(text_value(value) for value in array_value(update["messages"]))
        assert tuple(m for m in messages if "초: 물자" in m) == (line(4), line(8), line(12))
        pipe.send("save")
        send_seconds(pipe, "wait", "4")
        pipe.send("talk")
        pipe.send("load")
        working = Path(text_value(object_value(pipe.latest["update"])["working_path"]))
    with work_pipe(working) as pipe:
        pipe.send("attach")
        update = object_value(pipe.send("talk")["update"])
        messages = tuple(text_value(value) for value in array_value(update["messages"]))
        assert any("지난 대화(19초)" in m for m in messages)
        assert not any("초: 물자" in m for m in messages)


def test_actual_tk_return_recollection(tk_host: tk.Tk, tmp_path: Path) -> None:
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
        for action in ("down", "talk", "wait", "wait", "talk"):
            _click(screen, action)
        assert screen.last_update is not None
        assert recalled(screen.last_update) == (line(4),)
        _click(screen, "talk")
        assert recalled(screen.last_update) == ()
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
