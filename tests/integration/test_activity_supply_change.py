"""Activity intervals use the latest verified conversation end and current counters."""

from pathlib import Path
import pytest

import app.npc_activity as activity
from app.client import PlayWindow
from app.durable import create_durable
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.replay import ReplaySession
from contracts.turn import ProtocolSnapshot
from domain.canonical import array_value, object_value
from domain.npc_cycle import Supply
from domain.state_types import CoreSnapshot
from tests.integration.test_reach_gate_aid import driver, session, bundle
from tests.integration.test_ready_patrol import session as parent_session
from tests.integration.test_conversation_support_plan import until_nine
from tests.integration.test_quest_patrol import state
from tests.integration.test_client import _click, _pump
from tests.integration.test_pending_query_feedback import window as window, tk_host as tk_host


PREFIX = "NPC 반복 작업 변화 · "
ZERO = "현재 저장 구간에 새로 확인된 물자 변화가 없습니다."


def summary(prepared: int, used: int) -> str:
    return f"확인한 물자 변화 · 준비 {prepared}회 · 사용 {used}회."


def interval(rows: tuple[str, ...]) -> tuple[str, str]:
    indexes = [i for i, line in enumerate(rows) if line.startswith(PREFIX)]
    assert len(indexes) == 1
    i = indexes[0]
    return rows[i], rows[i + 1]


@pytest.mark.parametrize("framed", (False, True), ids=("direct", "real-pipe"))
def test_actual_activity_latest_talk_interval_is_readonly(tmp_path: Path, framed: bool) -> None:
    path = tmp_path / "game.sqlite"
    with driver(path, framed) as send:
        send("down")
        send("talk")
        for _ in range(6):
            send("wait")
        rows = array_value(send("activity")["messages"])
        assert PREFIX + "지난 대화(2초) 뒤의 변화입니다." in rows
        assert summary(2, 0) in rows
        send("talk")  # tick9:latest retained boundary,not the first talk at2
        for _ in range(9):
            send("wait")
        raw = path.read_bytes()
        update = send("activity")
        assert object_value(update["view"])["tick"] == "18"
        rows = array_value(update["messages"])
        assert PREFIX + "지난 대화(9초) 뒤의 변화입니다." in rows
        assert summary(2, 1) in rows
        assert summary(4, 1) not in rows
        assert path.read_bytes() == raw
        retry = send("retry")
        assert retry["view"] == update["view"] and path.read_bytes() == raw
        assert not any(
            isinstance(x, str) and x.startswith(PREFIX) for x in array_value(retry["messages"])
        )


def test_no_talk_uses_checkpoint_and_tied_actions_both_count(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        assert interval(owner.inspect_activity().messages) == (
            PREFIX + "0초 이후 저장 구간의 변화입니다.",
            ZERO,
        )
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=16)
        owner.act("wait", seconds=2)
        before = state(owner)
        assert interval(owner.inspect_activity().messages) == (
            PREFIX + "지난 대화(2초) 뒤의 변화입니다.",
            summary(5, 2),
        )
        assert state(owner) == before
    finally:
        owner.close()


def test_same_turn_work_is_in_latest_boundary_and_rejected_talk_does_not_reset(
    tmp_path: Path,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        until_nine(owner)
        owner.act("wait")
        before = state(owner)
        assert owner.act("talk").status == "OUT_OF_RANGE"
        assert state(owner) == before
        owner.act("down")
        owner.act("talk")  # tick12includes preparation at12
        assert interval(owner.inspect_activity().messages) == (
            PREFIX + "지난 대화(12초) 뒤의 변화입니다.",
            ZERO,
        )
        owner.act("wait", seconds=6)
        assert interval(owner.inspect_activity().messages) == (
            PREFIX + "지난 대화(12초) 뒤의 변화입니다.",
            summary(1, 0),
        )
    finally:
        owner.close()


def test_previous_save_restart_selects_own_interval_and_preserves_sources(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=6)
        owner.save("slot01")  # tick8
        owner.act("wait", seconds=10)
        owner.save("slot01")  # tick18
        originals = {p: p.read_bytes() for p in tmp_path.rglob("*.sqlite")}
        assert interval(owner.inspect_activity().messages)[1] == summary(4, 1)
        owner.load("slot01", previous=True)
        branch = owner.owner.working_path
        assert interval(owner.inspect_activity().messages) == (
            PREFIX + "지난 대화(2초) 뒤의 변화입니다.",
            summary(2, 0),
        )
        assert all(p.read_bytes() == raw for p, raw in originals.items())
    finally:
        owner.close()
    owner = session(branch)
    try:
        assert interval(owner.inspect_activity().messages)[1] == summary(2, 0)
        owner.act("talk")  # tick9
        owner.act("wait", seconds=9)
        assert interval(owner.inspect_activity().messages) == (
            PREFIX + "지난 대화(9초) 뒤의 변화입니다.",
            summary(2, 1),
        )
        assert all(p.read_bytes() == raw for p, raw in originals.items())
    finally:
        owner.close()


def test_compacted_totals_do_not_become_new_changes(tmp_path: Path) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=16)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    path = tmp_path / "compact/game.sqlite"
    create_durable(path, checkpoint, bundles=(bundle(),)).close()
    owner = session(path)
    try:
        assert interval(owner.inspect_activity().messages) == (
            PREFIX + "18초 이후 저장 구간의 변화입니다.",
            ZERO,
        )
        owner.act("wait", seconds=2)
        assert interval(owner.inspect_activity().messages) == (
            PREFIX + "18초 이후 저장 구간의 변화입니다.",
            summary(1, 1),
        )
    finally:
        owner.close()


def test_old_parent_mode_has_no_new_rows(tmp_path: Path) -> None:
    owner = parent_session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=16)
        assert not any(row.startswith(PREFIX) for row in owner.inspect_activity().messages)
        assert not any(row.startswith(PREFIX) for row in owner.act("talk").messages)
    finally:
        owner.close()


def test_interval_shares_existing_single_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        until_nine(owner)
        owner.act("wait", seconds=9)
        original = activity._ActivityFactory.restore
        factories: list[activity._ActivityFactory] = []

        def observed(
            self: activity._ActivityFactory, core: CoreSnapshot, protocol: ProtocolSnapshot
        ) -> ReplaySession:
            factories.append(self)
            return original(self, core, protocol)

        monkeypatch.setattr(activity._ActivityFactory, "restore", observed)
        before = state(owner)
        assert interval(owner.inspect_activity().messages)[1] == summary(2, 1)
        assert len(factories) == 1
        assert len(factories[0].conversation_supply) == 2
        assert state(owner) == before
    finally:
        owner.close()


@pytest.mark.parametrize("damage", ("initial", "missing", "tick", "produced", "consumed"))
def test_invalid_derived_interval_is_explicit_and_preserves_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        until_nine(owner)
        owner.act("wait", seconds=9)
        original = activity._cycle_activity_change_messages

        def damaged(
            factory: activity._ActivityFactory,
            checkpoint_tick: int,
            current_tick: int,
            current: Supply,
        ) -> tuple[str, ...]:
            if damage == "initial":
                factory.initial_supply = None
            elif damage == "missing":
                factory.conversation_supply.clear()
            elif damage == "tick":
                factory.conversations[-1] = (current_tick + 1, factory.conversations[-1][1])
            elif damage == "produced":
                factory.conversation_supply[-1] = Supply(3, 10, 7)
            else:
                factory.conversation_supply[-1] = Supply(0, 3, 3)
            return original(factory, checkpoint_tick, current_tick, current)

        before = state(owner)
        with monkeypatch.context() as patch:
            patch.setattr(activity, "_cycle_activity_change_messages", damaged)
            with pytest.raises(SaveError, match="NPC_ACTIVITY_SOURCE") as caught:
                owner.inspect_activity()
            assert caught.value.code == "NPC_ACTIVITY_SOURCE"
        assert state(owner) == before
        assert interval(owner.inspect_activity().messages)[1] == summary(2, 1)
    finally:
        owner.close()


def test_real_tk_activity_error_recovery_and_close(
    window: PlayWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    window.wait_seconds.set("16")
    _click(window, "wait")
    before = window.last_update
    assert before is not None
    raw = Path(before.working_path).read_bytes()

    def fail(*args: object) -> tuple[str, ...]:
        raise SaveError("NPC_ACTIVITY_SOURCE", "activity interval unavailable")

    with monkeypatch.context() as patch:
        patch.setattr(activity, "_cycle_activity_change_messages", fail)
        assert window.activity_button is not None
        window.activity_button.invoke()
        _pump(window.root, lambda: not window.busy)
        assert window.status.get() == "NPC_ACTIVITY_SOURCE" and window.view == before.view
    window.activity_button.invoke()
    _pump(window.root, lambda: not window.busy)
    assert window.status.get() == "ACTIVITY_INSPECTED"
    assert any(PREFIX + "지난 대화(2초)" in line for line in window.history)
    assert window.view == before.view and Path(before.working_path).read_bytes() == raw
    _click(window, "wait")
    assert window.status.get() == "COMMITTED"
    window.close()
    _pump(window.root, lambda: window.closed)
