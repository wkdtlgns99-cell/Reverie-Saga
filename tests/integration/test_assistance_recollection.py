"""Ordinary aid talk recalls verified own openings in its conversation window."""

from dataclasses import replace
from pathlib import Path
import tkinter as tk

import pytest

import app.npc_activity as activity
from app.client import PlayWindow
from app.client_worker import ClientWorker
from app.durable import create_durable
from app.npc_cycle import cycle_bundle
from contracts.client import ClientUpdate
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.quest import QuestSpoken
from contracts.replay import ReplaySession
from contracts.turn import ProtocolSnapshot
from domain.canonical import array_value, object_value, text_value
from domain.primitives import EntityId
from domain.state_types import CoreSnapshot
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_cycle_slot_comparison import inventory
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_assistance_history import first_help
from tests.integration.test_npc_cycle import session as ordinary_session
from tests.integration.test_npc_gate_aid import aid_pipe, session

EMPTY = "현재 저장 구간에 새로 확인된 의뢰 지원 기록이 없습니다."


def recalled(update: ClientUpdate) -> tuple[str, ...]:
    return tuple(m for m in update.messages if m.startswith("NPC 의뢰 지원 회상 · "))


def row(tick: int) -> str:
    return f"NPC 의뢰 지원 회상 · {tick}초: 통행문을 열었습니다."


def test_first_help_is_recalled_once_and_retry_stays_quiet(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        accepted = owner.act("talk")
        assert EMPTY in accepted.messages
        owner.act("wait", seconds=2)
        talked = owner.act("talk")
        assert row(4) in recalled(talked)
        assert "확인한 문 열기 1건 중 최근 1건입니다." in talked.messages
        assert "NPC 의뢰 지원 회상 · 지난 대화(2초) 뒤에 도운 기록입니다." in talked.messages
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
        assert EMPTY in owner.act("talk").messages
    finally:
        owner.close()


def test_last_three_actual_openings_and_total_since_previous_talk(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=2)
        for _ in range(4):
            owner.act("close")
            owner.act("wait")
        talked = owner.act("talk")
        assert talked.view is not None and talked.view.tick == 13
        assert recalled(talked)[1:] == (row(8), row(10), row(12))
        assert "확인한 문 열기 5건 중 최근 3건입니다." in talked.messages
    finally:
        owner.close()


def test_assistance_at_current_talk_wake_is_included_then_consumed(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=2)
        owner.act("close")
        talked = owner.act("talk")
        assert talked.view is not None and talked.view.tick == 6 and talked.view.gate_open
        assert recalled(talked)[1:] == (row(4), row(6))
        assert "확인한 문 열기 2건 중 최근 2건입니다." in talked.messages
        assert EMPTY in owner.act("talk").messages
    finally:
        owner.close()


@pytest.mark.parametrize("accepted", (False, True))
def test_player_open_gate_never_becomes_an_npc_help_memory(tmp_path: Path, accepted: bool) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("open")
        if accepted:
            owner.act("talk")
        owner.act("wait", seconds=16)
        update = owner.act("talk")
        assert update.view is not None and update.view.gate_open
        assert EMPTY in update.messages and len(recalled(update)) == 1
    finally:
        owner.close()


def test_new_help_after_return_uses_new_window_without_repeating_old_anchor(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        first_help(owner)
        assert recalled(owner.act("talk"))[1:] == (row(4),)
        owner.act("close")  # tick6:player closes,NPC opens in the same committed tick
        update = owner.act("talk")
        assert recalled(update)[1:] == (row(6),)
        assert "NPC 의뢰 지원 회상 · 지난 대화(5초) 뒤에 도운 기록입니다." in update.messages
        assert "확인한 문 열기 1건 중 최근 1건입니다." in update.messages
    finally:
        owner.close()


def test_bells_and_calls_do_not_evict_actual_assistance_before_return(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        first_help(owner)
        owner.act("wait", seconds=16)
        owner.act("bell")
        owner.act("wait", seconds=8)
        update = owner.act("talk")
        assert recalled(update)[1:] == (row(4),)
        assert any("21초의 플레이어 호출" in m for m in update.messages)
        assert "확인한 문 열기 1건 중 최근 1건입니다." in update.messages
    finally:
        owner.close()


def test_report_recalls_real_help_and_later_gratitude_does_not_invent_more(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        first_help(owner)
        for action in ("right", "down", "attack", "attack", "rest", "attack", "up", "left", "talk"):
            update = owner.act(action)
        assert update.view is not None and update.view.tick == 13 and update.quest_reward == 1
        assert recalled(update)[1:] == (row(4),)
        owner.act("close")
        owner.act("wait", seconds=16)
        update = owner.act("talk")
        assert update.view is not None and not update.view.gate_open and update.quest_reward == 1
        assert EMPTY in update.messages and len(recalled(update)) == 1
    finally:
        owner.close()


def test_previous_slot_restart_preserves_only_its_conversation_branch(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.save("slot01")
        owner.act("wait", seconds=2)
        owner.save("slot01")
        originals = inventory(tmp_path)
        owner.load("slot01", previous=True)
        path = owner.owner.working_path
    finally:
        owner.close()
    owner = session(path)
    try:
        assert EMPTY in owner.act("talk").messages
        owner.load("slot01")
        assert recalled(owner.act("talk"))[1:] == (row(4),)
        assert all((tmp_path / name).read_bytes() == raw for name, raw in originals.items())
    finally:
        owner.close()


def test_compact_checkpoint_forgets_unretained_help_but_recalls_new_fact(tmp_path: Path) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        first_help(owner)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    path = tmp_path / "compact/game.sqlite"
    create_durable(
        path, checkpoint, bundles=(cycle_bundle(approved_content(), npc_aid=True),)
    ).close()
    owner = session(path)
    try:
        update = owner.act("talk")
        assert EMPTY in update.messages and len(recalled(update)) == 1
        assert "NPC 의뢰 지원 회상 · 4초 이후 저장 구간의 도움입니다." in update.messages
        owner.act("close")
        assert recalled(owner.act("talk"))[1:] == (row(6),)
    finally:
        owner.close()


@pytest.mark.parametrize("damage", ("owner", "trace", "core", "protocol", "mode", "conversation"))
def test_invalid_recollection_source_never_mutates_live_or_saved_truth(
    tmp_path: Path, damage: str
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        first_help(owner)
        owner.act("talk")
        segment = owner.owner.retained_segment()
        current = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        conversation: str = next(
            e.header.event_id
            for e in owner.owner.last_publication().facts
            if isinstance(e.payload, QuestSpoken)
        )
        npc_id, aid = approved_content().definition.layout.npc_id, True
        if damage == "owner":
            npc_id = EntityId("actor:other")
        elif damage == "trace":
            segment = replace(
                segment,
                trace=replace(
                    segment.trace,
                    steps=(
                        replace(segment.trace.steps[0], expected_facts_hash="f" * 64),
                        *segment.trace.steps[1:],
                    ),
                ),
            )
        elif damage == "core":
            current = replace(current, core=segment.checkpoint.core)
        elif damage == "protocol":
            current = replace(current, protocol=replace(current.protocol, branch_id="f" * 32))
        elif damage == "mode":
            aid = False
        else:
            conversation = "e1-" + "f" * 64
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.attachment_id,
            inventory(tmp_path),
        )
        with pytest.raises(SaveError) as caught:
            activity.cycle_return_recollection(
                segment,
                npc_id,
                content=approved_content(),
                current=current,
                conversation_id=conversation,
                npc_aid=aid,
            )
        assert caught.value.code == "NPC_RECOLLECTION_SOURCE"
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.attachment_id,
            inventory(tmp_path),
        ) == before
    finally:
        owner.close()


def test_talk_uses_one_real_replay_and_query_retry_keep_source_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        first_help(owner)
        original = activity._ActivityFactory.restore
        calls = []

        def counted(
            factory: activity._ActivityFactory, core: CoreSnapshot, protocol: ProtocolSnapshot
        ) -> ReplaySession:
            calls.append(1)
            return original(factory, core, protocol)

        monkeypatch.setattr(activity._ActivityFactory, "restore", counted)
        assert recalled(owner.act("talk"))[1:] == (row(4),) and calls == [1]
        before = owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)
        assert not recalled(owner.retry()) and calls == [1]
        assert (owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)) == before
        activity_rows = owner.inspect_activity().messages
        assert "NPC 의뢰 지원 기록 · 4초: 통행문을 열었습니다." in activity_rows and calls == [1, 1]
        assert (owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)) == before
    finally:
        owner.close()


def test_call_only_api_and_ordinary_mode_keep_prior_output(tmp_path: Path) -> None:
    owner = session(tmp_path / "aid/game.sqlite")
    try:
        first_help(owner)
        owner.act("talk")
        conversation: str = next(
            e.header.event_id
            for e in owner.owner.last_publication().facts
            if isinstance(e.payload, QuestSpoken)
        )
        messages = activity.cycle_call_recollection(
            owner.owner.retained_segment(),
            approved_content().definition.layout.npc_id,
            content=approved_content(),
            current=DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol()),
            conversation_id=conversation,
            npc_aid=True,
        )
        assert messages == (
            "NPC 호출 회상 · 지난 대화(2초) 뒤에 끝낸 응답입니다.",
            "현재 저장 구간에 새로 확인된 호출 응답이 없습니다.",
        )
    finally:
        owner.close()
    owner = ordinary_session(tmp_path / "ordinary/game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=4)
        assert not recalled(owner.act("talk"))
    finally:
        owner.close()


def test_real_framed_return_load_and_restart_retain_correct_help_window(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with aid_pipe(path) as pipe:
        pipe.send("down")
        pipe.send("talk")
        pipe.send("save")
        pipe.send("wait")
        pipe.send("wait")
        update = object_value(pipe.send("talk")["update"])
        assert row(4) in tuple(map(text_value, array_value(update["messages"])))
        committed = path.read_bytes()
        retry = object_value(pipe.send("retry")["update"])
        assert retry["status"] == "COMMITTED" and path.read_bytes() == committed
        loaded = object_value(pipe.send("load")["update"])
        path = Path(text_value(loaded["working_path"]))
    with aid_pipe(path) as pipe:
        update = object_value(pipe.send("talk")["update"])
        assert EMPTY in tuple(map(text_value, array_value(update["messages"])))


def test_postcommit_retrieval_error_preserves_truth_and_worker_recovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    selected = approved_content()
    worker = ClientWorker(
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
    )
    try:
        worker.request("attach").result(30)
        for action in ("down", "talk", "wait", "wait"):
            worker.request(action).result(30)
        with monkeypatch.context() as patch:

            def broken(
                factory: activity._ActivityFactory, checkpoint: int, previous: int | None
            ) -> tuple[str, ...]:
                raise SaveError("NPC_RECOLLECTION_SOURCE", "injected retrieval boundary failure")

            patch.setattr(activity, "_assistance_recollection", broken)
            update = worker.request("talk").result(30)
            assert (
                update.status == "NPC_RECOLLECTION_SOURCE"
                and update.view is not None
                and update.view.tick == 5
            )
            assert worker.request("retry").result(30).view == update.view
            assert worker.request("save").result(30).status == "SAVED"
        assert "committed cycle call recollection failed" in caplog.text
        assert EMPTY in worker.request("talk").result(30).messages
    finally:
        worker.join()


def test_real_tk_return_talk_shows_assistance_and_retry_is_quiet(
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
        npc_aid=True,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        for action in ("down", "talk", "wait", "wait", "talk"):
            _click(screen, action)
        assert screen.last_update is not None and recalled(screen.last_update)[1:] == (row(4),)
        assert row(4) in screen.log_text.get("1.0", "end")
        _click(screen, "retry")
        assert not recalled(screen.last_update)
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
