from pathlib import Path
import shutil
import time
import tkinter as tk

import pytest

from app.client import PlayWindow
from app.client_session import ClientSession
from app.durable import create_durable
from app.npc_memory import memory_bundle
from app.watch import WatchBootstrapSpec
from app.npc_memory import bootstrap_memory
from contracts.persistence import DurableCheckpoint, SaveError
from domain.canonical import array_value, object_value, text_value
from tests.integration.test_client import _pump, tk_host as tk_host
from tests.integration.test_memory_client_route import approved_content, memory_pipe
from tests.integration.test_quest import GOAL

ROUTE = (*GOAL, "left", "talk")


def session(path: Path, *, work: bool = False) -> ClientSession:
    selected = approved_content()
    return ClientSession(
        path, selected.definition.layout, quest_content=selected, npc_memory=True, npc_work=work
    )


def inventory(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*.sqlite")}


@pytest.mark.parametrize("work", (False, True))
@pytest.mark.parametrize(
    "saved_step,current_step,counts",
    ((0, 0, (0, 0, 0)), (0, 2, (0, 1, 0)), (2, 11, (1, 1, 0)), (11, 11, (2, 0, 0))),
)
def test_slot_memory_comparison_is_readonly_and_preserves_retry(
    tmp_path: Path,
    work: bool,
    saved_step: int,
    current_step: int,
    counts: tuple[int, int, int],
) -> None:
    owner = session(tmp_path / "game.sqlite", work=work)
    try:
        for action in ROUTE[:saved_step]:
            assert owner.act(action).status == "COMMITTED"
        owner.save("slot01")
        for action in ROUTE[saved_step:current_step]:
            assert owner.act(action).status == "COMMITTED"
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
        assert (
            f"NPC 기억 비교 · 현재 {current_step}초 / 선택 저장 {saved_step}초" in update.messages
        )
        common, current, saved = counts
        assert f"공통 {common}개 · 현재에만 {current}개 · 저장에만 {saved}개" in update.messages
        assert (
            "저장 시점·진행 분기의 차이이며, NPC가 기억을 잊었다는 뜻은 아닙니다."
            in update.messages
        )
        if current_step == 0:
            assert "양쪽 진행에 기록된 NPC 의뢰 대화 기억이 없습니다." in update.messages
        if saved_step == 2 and current_step == 11:
            assert "공통 기억 · 2초: 의뢰를 맡겠다는 말을 직접 들었습니다." in update.messages
            assert (
                "현재에만 있는 기억 · 11초: 플레이어에게 완료 보고를 받았습니다. "
                "처치를 직접 본 기억은 아닙니다."
            ) in update.messages
        assert elapsed < 2, elapsed
        print(f"SLOT_MEMORY_COMPARISON_MS {elapsed * 1000:.3f}")
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.attachment_id,
            owner.owner.retained_segment(),
            inventory(tmp_path),
        ) == before
        if current_step:
            assert owner.retry().view == update.view
            assert inventory(tmp_path) == before[-1]
        if work:
            assert update.messages[-1].startswith("저장된 NPC 공동 비축:")
    finally:
        owner.close()


def test_saved_future_and_divergent_reports_are_not_forgetting(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        for action in ROUTE[:2]:
            owner.act(action)
        owner.save("slot01")
        for action in ROUTE[2:]:
            owner.act(action)
        owner.save("slot02")
        owner.load("slot01")
        assert "공통 1개 · 현재에만 0개 · 저장에만 1개" in owner.inspect_slot("slot02").messages
        owner.act("wait")
        for action in ROUTE[2:]:
            owner.act(action)
        messages = owner.inspect_slot("slot02").messages
        assert "공통 1개 · 현재에만 1개 · 저장에만 1개" in messages
        assert any(m.startswith("현재에만 있는 기억 · 12초:") for m in messages)
        assert any(m.startswith("저장에만 있는 기억 · 11초:") for m in messages)
        path = owner.owner.working_path
    finally:
        owner.close()
    resumed = session(path)
    try:
        assert resumed.inspect_slot("slot02").messages == messages
    finally:
        resumed.close()


def test_checkpoint_only_memory_comparison_needs_no_retained_events(tmp_path: Path) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        for action in ROUTE:
            owner.act(action)
        point = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    path = tmp_path / "restored/game.sqlite"
    durable = create_durable(path, point, bundles=(memory_bundle(approved_content()),))
    durable.export("slot01")
    durable.close()
    restored = session(path)
    try:
        assert restored.owner.retained_segment().trace.steps == ()
        assert "공통 2개 · 현재에만 0개 · 저장에만 0개" in restored.inspect_slot("slot01").messages
    finally:
        restored.close()


def test_foreign_world_slot_rejects_then_valid_inspection_recovers(tmp_path: Path) -> None:
    selected = approved_content()
    initial = bootstrap_memory(
        WatchBootstrapSpec(
            "a" * 64, "0" * 32, "1" * 32, initial_cell=selected.definition.layout.initial_cell
        ),
        selected,
    )
    foreign = create_durable(
        tmp_path / "foreign/game.sqlite",
        DurableCheckpoint(initial.snapshot(), initial.protocol()),
        bundles=(memory_bundle(selected),),
    )
    foreign.export("slot01")
    foreign.close()
    owner = session(tmp_path / "local/game.sqlite")
    try:
        owner.save("slot02")
        shutil.copyfile(
            tmp_path / "foreign/slots/slot01.sqlite", tmp_path / "local/slots/slot01.sqlite"
        )
        before = inventory(tmp_path)
        with pytest.raises(SaveError, match="^SAVE_INSPECT_FAILED: NPC_MEMORY_COMPARISON_OWNER$"):
            owner.inspect_slot("slot01")
        assert inventory(tmp_path) == before
        assert owner.inspect_slot("slot02").status == "SLOT_INSPECTED"
        assert owner.act("wait").status == "COMMITTED"
    finally:
        owner.close()


def test_actual_pipe_displays_comparison_without_loading(tmp_path: Path) -> None:
    with memory_pipe(tmp_path, tmp_path / "game.sqlite") as pipe:
        for action in ROUTE[:2]:
            pipe.send(action)
        pipe.send("save")
        for action in ROUTE[2:]:
            pipe.send(action)
        before = object_value(pipe.latest["update"])
        files = inventory(tmp_path)
        response = object_value(pipe.send("slot_inspect")["update"])
        messages = tuple(text_value(v) for v in array_value(response["messages"]))
        assert "공통 1개 · 현재에만 1개 · 저장에만 0개" in messages
        for key in ("view", "attachment_id", "working_path", "quest_stage", "quest_reward"):
            assert response[key] == before[key]
        assert inventory(tmp_path) == files


def test_real_tk_selected_slot_displays_comparison(tk_host: tk.Tk, tmp_path: Path) -> None:
    selected = approved_content()
    panel = tk.Toplevel(tk_host)
    screen = PlayWindow(
        panel,
        tmp_path / "game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        for action in ROUTE[:2]:
            screen.worker.request(action).result(30)
        screen.worker.request("save", slot_id="slot02").result(30)
        for action in ROUTE[2:]:
            screen.worker.request(action).result(30)
        screen.slot.set("slot02")
        screen.slot_preview_button.invoke()
        _pump(panel, lambda: not screen.busy)
        assert screen.last_update is not None and screen.last_update.view is not None
        assert screen.last_update.view.tick == 11
        assert "공통 1개 · 현재에만 1개 · 저장에만 0개" in screen.log_text.get("1.0", "end")
    finally:
        screen.close()
        _pump(panel, lambda: screen.closed)
        screen.worker.join()
