from pathlib import Path
import time
import tkinter as tk

import pytest

from app.client import PlayWindow
from app.client_worker import ClientWorker
from contracts.dialogue import GenerationError
from contracts.persistence import SaveError
from domain.canonical import array_value, object_value, text_value
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_npc_cycle import cycle_pipe, session
from tests.integration.test_unity_wait_duration import send_seconds


def inventory(path: Path) -> dict[str, bytes]:
    return {p.relative_to(path).as_posix(): p.read_bytes() for p in path.rglob("*.sqlite")}


@pytest.mark.parametrize(
    "saved,current,counts",
    (
        (0, 0, "공통 작업 0개 · 현재에만 0개 · 저장에만 0개"),
        (10, 20, "공통 작업 0개 · 현재에만 4개 · 저장에만 3개"),
        (16, 20, "공통 작업 2개 · 현재에만 2개 · 저장에만 2개"),
        (16, 16, "공통 작업 4개 · 현재에만 0개 · 저장에만 0개"),
    ),
)
def test_real_slot_comparison_is_bounded_readonly_and_preserves_retry(
    tmp_path: Path, saved: int, current: int, counts: str
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        if saved:
            owner.act("wait", seconds=saved)
        owner.save("slot01")
        if current > saved:
            owner.act("wait", seconds=current - saved)
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.attachment_id,
            owner.owner.retained_segment(),
            inventory(tmp_path),
        )
        started = time.perf_counter()
        update = owner.inspect_slot("slot01")
        elapsed = time.perf_counter() - started
        assert update.status == "SLOT_INSPECTED" and not update.reset_log
        assert f"NPC 작업 기억 비교 · 현재 {current}초 / 선택 저장 {saved}초" in update.messages
        assert counts in update.messages
        assert "NPC 기억 비교" in "\n".join(
            update.messages
        )  # Existing quest comparison stays separate.
        assert not any("e1-" in m for m in update.messages)
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.attachment_id,
            owner.owner.retained_segment(),
            inventory(tmp_path),
        ) == before
        assert elapsed < 2, elapsed
        print(f"CYCLE_SLOT_COMPARISON_MS {elapsed * 1000:.3f}")
        if current:
            assert owner.retry().view == update.view
            assert inventory(tmp_path) == before[-1]
    finally:
        owner.close()


def test_previous_saved_future_rewind_and_reconnect(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("wait", seconds=10)
        owner.save("slot01")
        owner.act("wait", seconds=10)
        owner.save("slot01")
        owner.save("slot02")
        before = inventory(tmp_path)
        previous = owner.inspect_slot("slot01", previous=True)
        assert "NPC 작업 기억 비교 · 현재 20초 / 선택 저장 10초" in previous.messages
        assert "공통 작업 0개 · 현재에만 4개 · 저장에만 3개" in previous.messages
        assert inventory(tmp_path) == before
        owner.load("slot01", previous=True)
        future = owner.inspect_slot("slot02")
        assert "NPC 작업 기억 비교 · 현재 10초 / 선택 저장 20초" in future.messages
        assert "공통 작업 0개 · 현재에만 3개 · 저장에만 4개" in future.messages
        assert any("보관 범위" in m for m in future.messages)
        path = owner.owner.working_path
        messages = future.messages
    finally:
        owner.close()
    resumed = session(path)
    try:
        assert resumed.inspect_slot("slot02").messages == messages
    finally:
        resumed.close()


def test_logged_comparison_failure_preserves_session_and_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("wait", seconds=16)
        owner.save("slot01")
        before = owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)

        def fail(*args: object) -> tuple[str, ...]:
            raise GenerationError("NPC_MEMORY_COMPARISON_IDENTITY")

        with monkeypatch.context() as patch:
            patch.setattr("app.client_session.cycle_slot_messages", fail)
            with pytest.raises(
                SaveError, match="^SAVE_INSPECT_FAILED: NPC_MEMORY_COMPARISON_IDENTITY$"
            ):
                owner.inspect_slot("slot01")
        assert "NPC cycle slot memory comparison failed" in caplog.text
        assert (owner.owner.snapshot(), owner.owner.protocol(), inventory(tmp_path)) == before
        assert owner.retry().view == owner.update().view
        assert owner.inspect_slot("slot01").status == "SLOT_INSPECTED"
    finally:
        owner.close()


def test_actual_worker_failure_projects_error_and_recovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.integration.test_memory_client_route import approved_content

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
        worker.request("wait", seconds=16).result(timeout=30)
        saved = worker.request("save").result(timeout=30)

        def fail(*args: object) -> tuple[str, ...]:
            raise GenerationError("NPC_CONTEXT_INPUT")

        with monkeypatch.context() as patch:
            patch.setattr("app.client_session.cycle_slot_messages", fail)
            broken = worker.inspect_slot().result(timeout=30)
        assert broken.status == "SAVE_INSPECT_FAILED" and broken.view == saved.view
        inspected = worker.inspect_slot().result(timeout=30)
        assert inspected.status == "SLOT_INSPECTED" and inspected.view == saved.view
        assert "공통 작업 4개 · 현재에만 0개 · 저장에만 0개" in inspected.messages
    finally:
        worker.close().result(timeout=30)
        worker.join()


def test_actual_pipe_current_previous_tie_and_reconnect(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with cycle_pipe(path) as pipe:
        send_seconds(pipe, "wait", "16")
        pipe.send("save")
        send_seconds(pipe, "wait", "4")
        current = object_value(pipe.send("slot_inspect")["update"])
        lines = [text_value(m) for m in array_value(current["messages"])]
        assert "공통 작업 2개 · 현재에만 2개 · 저장에만 2개" in lines
        assert [m for m in lines if m.startswith("현재에만 있는 작업 기억")] == [
            "현재에만 있는 작업 기억 · 20초: 공동 물자 1개를 사용했습니다 · 물자 2/3개.",
            "현재에만 있는 작업 기억 · 20초: 공동 물자 1개를 준비했습니다 · 물자 3/3개.",
        ]
        pipe.send("save")
        previous = object_value(pipe.send("slot_previous_inspect")["update"])
        assert "공통 작업 2개 · 현재에만 2개 · 저장에만 2개" in array_value(previous["messages"])
        loaded = object_value(pipe.send("load_previous")["update"])
        path = Path(text_value(loaded["working_path"]))
    with cycle_pipe(path) as pipe:
        update = object_value(pipe.send("slot_inspect")["update"])
        assert "공통 작업 2개 · 현재에만 2개 · 저장에만 2개" in array_value(update["messages"])
        assert object_value(update["view"])["tick"] == "16"


def test_actual_tk_slot_projection_and_current_view_preserved(
    tk_host: tk.Tk, tmp_path: Path
) -> None:
    from tests.integration.test_memory_client_route import approved_content

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
        screen.wait_seconds.set("16")
        _click(screen, "wait")
        _click(screen, "save")
        screen.wait_seconds.set("4")
        _click(screen, "wait")
        before = screen.last_update
        screen.slot_preview_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None and before is not None
        assert screen.last_update.status == "SLOT_INSPECTED"
        assert screen.last_update.view == before.view
        assert "공통 작업 2개 · 현재에만 2개 · 저장에만 2개" in screen.last_update.messages
        assert any("보관 범위" in line for line in screen.history)
        _click(screen, "wait")
        assert screen.last_update.status == "COMMITTED"
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
