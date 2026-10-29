"""Aid inspection derives bounded factual history from one verified retained replay."""

from dataclasses import replace
from pathlib import Path
import tkinter as tk

import pytest

import app.npc_activity as activity
from app.client import PlayWindow
from app.client_session import ClientSession
from app.durable import create_durable
from app.npc_cycle import cycle_bundle
from contracts.client import ClientUpdate
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.replay import ReplayMismatch, ReplayTrace
from domain.canonical import array_value, object_value, text_value
from domain.primitives import EntityId
from orchestration.replay import Runner
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_cycle_slot_comparison import inventory
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_gate_aid import aid_pipe, session

EMPTY = "현재 저장 구간에 남은 의뢰 지원 기록이 없습니다. 문 상태로 과거 도움을 추정하지 않습니다."


def header(tick: int = 0) -> str:
    return f"NPC 의뢰 지원 · {tick}초 이후 저장 구간의 최근 최대 3건입니다."


def helped(tick: int) -> str:
    return f"NPC 의뢰 지원 기록 · {tick}초: 통행문을 열었습니다."


def rows(update: ClientUpdate) -> tuple[str, ...]:
    return tuple(m for m in update.messages if m.startswith("NPC 의뢰 지원 기록 · "))


def unchanged(owner: ClientSession, directory: Path) -> tuple[object, ...]:
    return (
        owner.owner.snapshot(),
        owner.owner.protocol(),
        owner.owner.attachment_id,
        inventory(directory),
    )


def first_help(owner: ClientSession) -> None:
    owner.act("down")
    owner.act("talk")
    result = owner.act("wait", seconds=2)
    assert result.view is not None and result.view.tick == 4 and result.view.gate_open


@pytest.mark.parametrize("kind", ("unaccepted", "player_open", "accepted_already_open"))
def test_no_inferred_help_from_acceptance_bells_or_open_gate(tmp_path: Path, kind: str) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        if kind != "unaccepted":
            owner.act("down")
            owner.act("open")
        if kind == "accepted_already_open":
            owner.act("talk")
        owner.act("wait", seconds=16)
        before = unchanged(owner, tmp_path)
        result = owner.inspect_activity()
        assert result.status == "ACTIVITY_INSPECTED" and not rows(result)
        assert result.messages[-2:] == (header(), EMPTY)
        assert unchanged(owner, tmp_path) == before
    finally:
        owner.close()


def test_actual_help_single_replay_and_quiet_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        first_help(owner)
        original = Runner.run
        calls = 0

        def counted(runner: Runner, trace: ReplayTrace) -> tuple[ReplayMismatch, ...]:
            nonlocal calls
            calls += 1
            return original(runner, trace)

        monkeypatch.setattr(Runner, "run", counted)
        before = unchanged(owner, tmp_path)
        result = owner.inspect_activity()
        assert calls == 1 and rows(result) == (helped(4),)
        assert result.messages[-3:] == (
            header(),
            "확인한 문 열기 1건 중 최근 1건입니다.",
            helped(4),
        )
        assert not rows(owner.retry()) and unchanged(owner, tmp_path) == before
        assert owner.inspect_activity().messages == result.messages and calls == 2
        assert unchanged(owner, tmp_path) == before
    finally:
        owner.close()


def test_latest_three_help_anchors_survive_bell_eviction(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        first_help(owner)
        for _ in range(4):
            owner.act("close")
            owner.act("wait")
        result = owner.inspect_activity()
        assert rows(result) == (helped(8), helped(10), helped(12))
        assert "확인한 문 열기 5건 중 최근 3건입니다." in result.messages
        owner.act("wait", seconds=16)
        before = unchanged(owner, tmp_path)
        later = owner.inspect_activity()
        assert rows(later) == rows(result)
        assert "확인한 문 열기 5건 중 최근 3건입니다." in later.messages
        assert len(tuple(m for m in later.messages if m.startswith("NPC 활동 기록 · "))) == 8
        assert unchanged(owner, tmp_path) == before
    finally:
        owner.close()


def test_same_tick_player_close_and_npc_reopen_are_one_assistance(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        first_help(owner)
        owner.act("wait")
        result = owner.act("close")
        assert result.view is not None and result.view.tick == 6 and result.view.gate_open
        inspected = owner.inspect_activity()
        assert rows(inspected) == (helped(4), helped(6))
        assert "확인한 문 열기 2건 중 최근 2건입니다." in inspected.messages
    finally:
        owner.close()


def test_report_stops_new_help_without_erasing_actual_retained_fact(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        first_help(owner)
        for action in ("right", "down", "attack", "attack", "rest", "attack", "up", "left", "talk"):
            owner.act(action)
        assert owner.update().quest_reward == 1
        owner.act("close")
        result = owner.act("wait", seconds=16)
        assert result.view is not None and result.view.tick == 30 and not result.view.gate_open
        before = unchanged(owner, tmp_path)
        inspected = owner.inspect_activity()
        assert rows(inspected) == (helped(4),)
        assert "확인한 문 열기 1건 중 최근 1건입니다." in inspected.messages
        assert unchanged(owner, tmp_path) == before
    finally:
        owner.close()


def test_previous_slot_and_restart_follow_the_selected_retained_branch(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        earlier = owner.inspect_activity().messages
        owner.save("slot01")
        owner.act("wait", seconds=2)
        future = owner.inspect_activity().messages
        assert helped(4) in future and helped(4) not in earlier
        owner.save("slot01")
        sources = inventory(tmp_path)
        owner.load("slot01", previous=True)
        assert owner.inspect_activity().messages == earlier
        assert all((tmp_path / name).read_bytes() == data for name, data in sources.items())
        path = owner.owner.working_path
    finally:
        owner.close()
    reopened = session(path)
    try:
        assert reopened.inspect_activity().messages == earlier
        reopened.load("slot01")
        assert reopened.inspect_activity().messages == future
        assert all((tmp_path / name).read_bytes() == data for name, data in sources.items())
    finally:
        reopened.close()


def test_compact_open_gate_has_no_fabricated_old_help(tmp_path: Path) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        first_help(owner)
        current = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    path = tmp_path / "compact/game.sqlite"
    create_durable(path, current, bundles=(cycle_bundle(approved_content(), npc_aid=True),)).close()
    owner = session(path)
    try:
        assert not owner.owner.retained_segment().trace.steps
        result = owner.inspect_activity()
        assert result.view is not None and result.view.gate_open and not rows(result)
        assert result.messages[-2:] == (header(4), EMPTY)
        owner.act("close")
        owner.act("wait")
        result = owner.inspect_activity()
        assert result.messages[-3:] == (
            header(4),
            "확인한 문 열기 1건 중 최근 1건입니다.",
            helped(6),
        )
    finally:
        owner.close()


@pytest.mark.parametrize("damage", ("owner", "trace", "core", "protocol", "mode"))
def test_unverified_assistance_sources_reject_without_publication_or_mutation(
    tmp_path: Path, damage: str
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        first_help(owner)
        segment = owner.owner.retained_segment()
        current = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
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
        else:
            aid = False
        before = unchanged(owner, tmp_path)
        with pytest.raises(SaveError) as caught:
            activity.cycle_activity_messages(
                segment, npc_id, content=approved_content(), current=current, npc_aid=aid
            )
        assert caught.value.code == "NPC_ACTIVITY_SOURCE"
        assert unchanged(owner, tmp_path) == before
    finally:
        owner.close()


def test_real_binary_pipe_history_rewinds_and_reconnects(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with aid_pipe(path) as pipe:
        for action in ("down", "talk", "save", "wait", "wait"):
            pipe.send(action)
        before = path.read_bytes()
        update = object_value(pipe.send("activity")["update"])
        assert helped(4) in tuple(map(text_value, array_value(update["messages"])))
        assert path.read_bytes() == before
        pipe.send("load")
        update = object_value(pipe.send("activity")["update"])
        assert EMPTY in tuple(map(text_value, array_value(update["messages"])))
        path = Path(text_value(update["working_path"]))
    with aid_pipe(path) as pipe:
        pipe.send("wait")
        pipe.send("wait")
        update = object_value(pipe.send("activity")["update"])
        assert helped(4) in tuple(map(text_value, array_value(update["messages"])))


def test_real_tk_activity_button_displays_help_and_keeps_input(
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
        for action in ("down", "talk", "save", "wait", "wait"):
            _click(screen, action)
        assert screen.activity_button is not None
        before = inventory(tmp_path)
        screen.activity_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None and rows(screen.last_update) == (helped(4),)
        assert helped(4) in screen.log_text.get("1.0", "end")
        assert screen.activity_button.instate(("!disabled",)) and inventory(tmp_path) == before
        _click(screen, "load")
        screen.activity_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None and not rows(screen.last_update)
        assert EMPTY in screen.log_text.get("1.0", "end")
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
