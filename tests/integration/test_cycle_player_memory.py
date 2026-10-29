"""Cycle dialogue recalls heard statements without inferring combat knowledge."""

from pathlib import Path
import tkinter as tk

import pytest

from app.client import PlayWindow
from app.client_worker import ClientWorker
from app.durable import create_durable
from app.npc_cycle import cycle_bundle
from contracts.dialogue import GenerationError
from contracts.persistence import DurableCheckpoint
from contracts.replay import ReplaySession
from contracts.turn import ProtocolSnapshot
from domain.canonical import array_value, object_value, text_value
from domain.npc_memory import NpcQuestMemoryRecord
from domain.state_types import CoreSnapshot
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_cycle_slot_comparison import inventory
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_cycle import cycle, cycle_pipe, session
from tests.integration.test_npc_player_memory import promise, remembered, report
from tests.integration.test_quest import GOAL


def test_cycle_uses_original_heard_statement_not_objective_enemy_state(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        initial = owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)
        assert not remembered(owner.act("talk"))
        assert (owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)) == initial
        owner.act("down")
        assert remembered(owner.act("talk")) == (promise(2),)
        for action in GOAL[2:]:
            assert not remembered(owner.act(action))
        before_report = owner.update()
        assert before_report.view is not None and before_report.view.tick == 9
        assert before_report.view.enemy_hp == 0 and before_report.quest_reward == 0
        owner.act("left")
        received = owner.act("talk")
        assert remembered(received) == (report(11),) and received.quest_reward == 1
        assert any("NPC 반복 작업:" in m for m in received.messages)
        assert any("NPC 작업 기억 · 10초:" in m for m in received.messages)
        before_retry = owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)
        assert not remembered(owner.retry())
        assert (owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)) == before_retry
        assert remembered(owner.act("talk")) == (report(11),)
        assert owner.update().quest_reward == 1
    finally:
        owner.close()


@pytest.mark.parametrize("reported", (False, True))
def test_cycle_checkpoint_only_remembers_original_tick_with_one_call_replay(
    tmp_path: Path, reported: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        actions = (*GOAL, "left", "talk") if reported else ("down", "talk")
        for action in actions:
            owner.act(action)
        owner.act("wait", seconds=16)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    path = tmp_path / "compacted/game.sqlite"
    durable = create_durable(path, checkpoint, bundles=(cycle_bundle(approved_content()),))
    durable.close()
    compacted = session(path)
    try:
        assert compacted.owner.retained_segment().trace.steps == ()

        import app.npc_activity as activity

        restore = activity._ActivityFactory.restore
        with monkeypatch.context() as scoped:
            calls = []

            def observed(
                factory: activity._ActivityFactory, core: CoreSnapshot, protocol: ProtocolSnapshot
            ) -> ReplaySession:
                calls.append(1)
                return restore(factory, core, protocol)

            scoped.setattr(activity._ActivityFactory, "restore", observed)
            update = compacted.act("talk")
        assert calls == [1]
        assert remembered(update) == ((report(11),) if reported else (promise(2),))
        assert update.quest_reward == int(reported)
        assert cycle(compacted).state.produced > 0
    finally:
        compacted.close()


def test_cycle_previous_restore_and_restart_never_leak_future_report(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        for action in GOAL:
            owner.act(action)
        owner.save("slot01")  # 9:accepted2,objective dead,no report
        owner.act("left")
        assert remembered(owner.act("talk")) == (report(11),)
        owner.save("slot01")  # 11:previous remains9
        sources = inventory(tmp_path)
        owner.load("slot01", previous=True)
        path = owner.owner.working_path
        assert path != tmp_path / "game.sqlite"
        assert owner.update().quest_reward == 0
        assert all((tmp_path / source).read_bytes() == value for source, value in sources.items())
    finally:
        owner.close()
    resumed = session(path)
    try:
        resumed.act("wait")
        resumed.act("left")
        assert remembered(resumed.act("talk")) == (report(12),)
        assert resumed.update().quest_reward == 1
        assert all((tmp_path / source).read_bytes() == value for source, value in sources.items())
        resumed.load("slot01")
        assert remembered(resumed.act("talk")) == (report(11),)
        assert resumed.update().quest_reward == 1
        assert all((tmp_path / source).read_bytes() == value for source, value in sources.items())
    finally:
        resumed.close()


def test_cycle_postcommit_projection_error_keeps_live_truth_retry_save_and_polling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import app.client_session as client_session

    selected = approved_content()
    worker = ClientWorker(
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_cycle=True,
    )
    try:
        worker.request("attach").result(timeout=30)
        for action in (*GOAL, "left"):
            worker.request(action).result(timeout=30)
        with monkeypatch.context() as scoped:

            def unavailable(record: NpcQuestMemoryRecord) -> tuple[str, ...]:
                raise GenerationError("NPC_CONTEXT_INPUT")

            scoped.setattr(client_session, "player_memory_recollection", unavailable)
            failed = worker.request("talk").result(timeout=30)
            assert failed.status == "NPC_RECOLLECTION_SOURCE" and failed.view is not None
            assert failed.view.tick == 11 and failed.quest_reward == 1
            assert "행동은 확정됐지만" in failed.messages[0]
            assert worker.request("retry").result(timeout=30).view == failed.view
            assert worker.request("save").result(timeout=30).status == "SAVED"
            assert worker.inspect_activity().result(timeout=30).status == "ACTIVITY_INSPECTED"
        assert "committed cycle player recollection failed" in caplog.text
        recovered = worker.request("talk").result(timeout=30)
        assert recovered.status == "COMMITTED" and remembered(recovered) == (report(11),)
        assert recovered.quest_reward == 1
    finally:
        worker.join()


def test_cycle_statement_process_control_propagates_after_truthful_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.client_session as client_session

    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")

        def interrupted(record: NpcQuestMemoryRecord) -> tuple[str, ...]:
            raise KeyboardInterrupt

        monkeypatch.setattr(client_session, "player_memory_recollection", interrupted)
        with pytest.raises(KeyboardInterrupt):
            owner.act("talk")
        assert owner.update().quest_stage == 1 and owner.owner.snapshot().tick == 2
        assert not remembered(owner.retry())
    finally:
        owner.close()


def test_cycle_real_binary_pipe_report_rewind_and_new_process(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with cycle_pipe(path) as pipe:
        for action in GOAL:
            response = object_value(pipe.send(action)["update"])
            if action == "talk":
                assert promise(2) in tuple(map(text_value, array_value(response["messages"])))
        pipe.send("save")
        pipe.send("left")
        update = object_value(pipe.send("talk")["update"])
        assert report(11) in tuple(map(text_value, array_value(update["messages"])))
        loaded = object_value(pipe.send("load")["update"])
        path = Path(text_value(loaded["working_path"]))
    with cycle_pipe(path) as pipe:
        pipe.send("left")
        update = object_value(pipe.send("talk")["update"])
        assert report(11) in tuple(map(text_value, array_value(update["messages"])))
        assert update["quest_reward"] == "1"


def test_cycle_real_tk_dialogue_shows_promise_report_and_quiet_retry(
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
        for action in GOAL:
            _click(screen, action)
            if action == "talk":
                assert screen.last_update is not None
                assert remembered(screen.last_update) == (promise(2),)
        _click(screen, "left")
        _click(screen, "talk")
        assert screen.last_update is not None
        assert remembered(screen.last_update) == (report(11),)
        assert report(11) in screen.log_text.get("1.0", "end")
        _click(screen, "retry")
        assert not remembered(screen.last_update)
        _click(screen, "save")
        assert screen.last_update.status == "SAVED"
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
