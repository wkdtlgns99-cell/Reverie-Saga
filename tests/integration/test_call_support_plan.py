"""Player-facing instructions derive only from actual selected committed readiness."""

from pathlib import Path
import tkinter as tk

from app.client import PlayWindow
from app.client_worker import ClientWorker
from domain.canonical import array_value, object_value, text_value
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_call_aid import call_pipe

import pytest

from tests.integration.test_npc_call_aid import session
from tests.integration.test_npc_gate_aid import aided, state

HINT = "NPC 지원 계획 · 공동 물자가 확보되어 NPC 호출로 통행 지원을 요청할 수 있습니다."
OLD = "NPC 지원 계획 · 공동 물자가 확보되어 통행 지원을 준비하고 있습니다."


@pytest.mark.parametrize("surface", ("talk", "activity", "slot"))
def test_ready_call_hint_on_actual_surfaces(tmp_path: Path, surface: str) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("wait", seconds=5 if surface == "talk" else 6)
        if surface == "talk":
            update = owner.act("talk")
            assert HINT in update.messages and OLD not in update.messages
        else:
            owner.save("slot01")
            before = state(owner)
            update = (
                owner.inspect_activity() if surface == "activity" else owner.inspect_slot("slot01")
            )
            expected = (HINT,) if surface == "activity" else ("현재 " + HINT, "선택 저장 " + HINT)
            assert all(line in update.messages for line in expected)
            assert state(owner) == before
        assert update.view is not None and update.view.tick == 8 and not update.view.gate_open
        assert aided(owner.act("bell"))
    finally:
        owner.close()


def test_future_saved_and_live_plans_remain_distinct_after_rewind_restart(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.save("slot01")
        owner.act("wait", seconds=6)
        owner.save("slot01")
        owner.load("slot01", previous=True)
        path = owner.owner.working_path
    finally:
        owner.close()
    owner = session(path)
    try:
        before = state(owner)
        lines = owner.inspect_slot("slot01").messages
        assert "선택 저장 " + HINT in lines and "현재 " + HINT not in lines
        assert (
            "현재 NPC 지원 계획 · 공동 물자 2개를 더 확보하면 통행 지원을 준비합니다. (현재 0/3개)."
            in lines
        )
        assert state(owner) == before
        owner.act("wait", seconds=6)
        assert HINT in owner.inspect_activity().messages
        assert aided(owner.act("bell"))
        before = state(owner)
        assert HINT not in owner.retry().messages and state(owner) == before
    finally:
        owner.close()


def test_actual_worker_query_uses_new_instruction(tmp_path: Path) -> None:
    selected = approved_content()
    worker = ClientWorker(
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
        npc_cycle=True,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
    )
    try:
        worker.request("attach").result(timeout=10)
        worker.request("down").result(timeout=10)
        worker.request("talk").result(timeout=10)
        worker.request("wait", seconds=5).result(timeout=10)
        assert HINT in worker.request("talk").result(timeout=10).messages
        worker.request("save").result(timeout=10)
        assert HINT in worker.inspect_activity().result(timeout=10).messages
        lines = worker.inspect_slot().result(timeout=10).messages
        assert "현재 " + HINT in lines and "선택 저장 " + HINT in lines
        assert aided(worker.request("bell").result(timeout=10))
    finally:
        worker.close().result(timeout=10)
        worker.join()


def test_actual_framed_talk_activity_and_slot_share_instruction(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with call_pipe(path) as pipe:
        for action in ("down", "talk", *("wait",) * 5, "talk"):
            response = pipe.send(action)
        messages = tuple(map(text_value, array_value(object_value(response["update"])["messages"])))
        assert HINT in messages
        pipe.send("save")
        before = path.read_bytes()
        for action in ("activity", "slot_inspect"):
            update = object_value(pipe.send(action)["update"])
            lines = tuple(map(text_value, array_value(update["messages"])))
            assert (HINT if action == "activity" else "현재 " + HINT) in lines
        assert path.read_bytes() == before
        update = object_value(pipe.send("bell")["update"])
        assert object_value(update["view"])["gate_open"] is True


def test_actual_hidden_tk_committed_talk_and_activity(tk_host: tk.Tk, tmp_path: Path) -> None:
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
        npc_supply_aid=True,
        npc_call_aid=True,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        for action in ("down", "talk", *("wait",) * 5, "talk"):
            _click(screen, action)
        assert HINT in screen.log_text.get("1.0", "end")
        assert screen.activity_button is not None
        screen.activity_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None and HINT in screen.last_update.messages
        _click(screen, "bell")
        assert aided(screen.last_update)
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
