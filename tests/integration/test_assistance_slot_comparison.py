"""Independent current/saved assistance counts and bounded anchor comparisons."""

from dataclasses import replace
from pathlib import Path
import gc
import time
import tkinter as tk

import pytest

import app.client_session as client_module
from app.client import PlayWindow
from app.client_session import ClientSession
from app.durable import create_durable
from app.npc_cycle import cycle_bundle
from contracts.persistence import DurableCheckpoint, SaveError
from domain.npc_assistance_memory import AssistanceMemoryRecord
from domain.primitives import EntityId
from tests.integration.test_assistance_memory_clients import session, prepare, memory
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_assistance_memory import CHILD_FLAGS
from tests.integration.test_quest_patrol import state
from tests.integration.test_reach_gate_aid import FLAGS


HEADING = "NPC 도움 기억 비교 · "
MORE_CURRENT = "NPC 누적 도움 횟수 비교 · 현재가 선택 저장보다 4회 많습니다."
MORE_SAVED = "NPC 누적 도움 횟수 비교 · 선택 저장이 현재보다 4회 많습니다."
EQUAL_ONE = "NPC 누적 도움 횟수 비교 · 양쪽 모두 1회입니다."
DISCLAIMER = (
    "각 진행이 보관한 최근 최대 4개의 도움 기억만 비교합니다. "
    "한쪽에 없다고 돕지 않았거나 기억을 잊었다는 뜻은 아닙니다."
)


def repeated(owner: ClientSession) -> None:
    prepare(owner)
    owner.save("slot01")
    for action in ("down", "close"):
        assert owner.act(action).status == "COMMITTED"
    owner.act("wait", seconds=2)
    owner.act("close")
    owner.act("wait", seconds=3)
    owner.save("slot02")
    for _ in range(2):
        owner.act("close")
        owner.act("wait", seconds=3)
    assert memory(owner).total_assists == 5
    owner.save("slot03")


@pytest.mark.parametrize(
    "slot,common,current_only,saved_only",
    (("slot01", 0, 4, 1), ("slot02", 2, 2, 1), ("slot03", 4, 0, 0)),
)
def test_selected_slot_exact_counts_and_retained_window_are_readonly(
    tmp_path: Path, slot: str, common: int, current_only: int, saved_only: int
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        repeated(owner)
        before = state(owner)
        sources = {p: p.read_bytes() for p in tmp_path.rglob("*.sqlite")}
        started = time.perf_counter()
        rows = owner.inspect_slot(slot).messages
        print(f"slot_comparison_seconds={time.perf_counter() - started:.6f}")
        assert (
            HEADING + f"현재 32초 / 선택 저장 {dict(slot01=16, slot02=24, slot03=32)[slot]}초"
            in rows
        )
        expected = (
            MORE_CURRENT
            if slot == "slot01"
            else (
                "NPC 누적 도움 횟수 비교 · 현재가 선택 저장보다 2회 많습니다."
                if slot == "slot02"
                else "NPC 누적 도움 횟수 비교 · 양쪽 모두 5회입니다."
            )
        )
        assert expected in rows and DISCLAIMER in rows
        assert (
            f"보관 도움 기억 비교 · 공통 {common}개 · 현재에만 {current_only}개 · 선택 저장에만 {saved_only}개"
            in rows
        )
        assert "현재 NPC 지속 도움 기억: 누적 5회 · 최근 4개를 보관합니다." in rows
        assert state(owner) == before and all(p.read_bytes() == raw for p, raw in sources.items())
        owner.retry()
        assert state(owner) == before
    finally:
        owner.close()


def test_previous_rewind_restart_and_compaction_use_selected_snapshot(tmp_path: Path) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        repeated(owner)
        owner.save("slot01")
        assert MORE_CURRENT in owner.inspect_slot("slot01", previous=True).messages
        compact = tmp_path / "compact/game.sqlite"
        create_durable(
            compact,
            DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol()),
            bundles=(cycle_bundle(approved_content(), **CHILD_FLAGS),),
        ).close()
        owner.load("slot01", previous=True)
        branch = owner.owner.working_path
        assert MORE_SAVED in owner.inspect_slot("slot03").messages
    finally:
        owner.close()
    owner = session(branch)
    try:
        before = state(owner)
        rows = owner.inspect_slot("slot03").messages
        assert MORE_SAVED in rows
        assert "보관 도움 기억 비교 · 공통 0개 · 현재에만 1개 · 선택 저장에만 4개" in rows
        assert state(owner) == before
    finally:
        owner.close()
    owner = session(compact)
    try:
        assert not owner.owner.retained_segment().trace.steps
        owner.save("slot01")
        owner.act("close")
        owner.act("wait", seconds=3)
        assert memory(owner).total_assists == 6
        before = state(owner)
        rows = owner.inspect_slot("slot01").messages
        assert "NPC 누적 도움 횟수 비교 · 현재가 선택 저장보다 1회 많습니다." in rows
        assert "보관 도움 기억 비교 · 공통 3개 · 현재에만 1개 · 선택 저장에만 1개" in rows
        assert state(owner) == before
    finally:
        owner.close()


def test_equal_totals_do_not_imply_the_same_remembered_actions(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        prepare(owner, 15)
        owner.save("slot01")
        owner.act("wait")
        owner.save("slot02")
        owner.load("slot01")
        owner.act("bell")
        assert memory(owner).entries[0].source_kind == "answered_call"
        before = state(owner)
        rows = owner.inspect_slot("slot02").messages
        assert EQUAL_ONE in rows
        assert "보관 도움 기억 비교 · 공통 0개 · 현재에만 1개 · 선택 저장에만 1개" in rows
        assert state(owner) == before
    finally:
        owner.close()


def test_empty_memories_and_parent_mode_are_distinct(tmp_path: Path) -> None:
    owner = session(tmp_path / "child/game.sqlite")
    try:
        owner.save("slot01")
        rows = owner.inspect_slot("slot01").messages
        assert "NPC 누적 도움 횟수 비교 · 양쪽 모두 0회입니다." in rows
        assert "보관 도움 기억 비교 · 공통 0개 · 현재에만 0개 · 선택 저장에만 0개" in rows
    finally:
        owner.close()
    content = approved_content()
    parent = ClientSession(
        tmp_path / "parent/game.sqlite", content.definition.layout, quest_content=content, **FLAGS
    )
    try:
        parent.save("slot01")
        assert not any(line.startswith(HEADING) for line in parent.inspect_slot("slot01").messages)
    finally:
        parent.close()


@pytest.mark.parametrize("damage", ("world", "pins", "missing", "duplicate", "owner", "identity"))
def test_invalid_comparison_source_is_explicit_and_preserves_owner(
    tmp_path: Path, damage: str
) -> None:
    from app.npc_assistance_memory import assistance_slot_comparison

    owner = session(tmp_path / "game.sqlite")
    try:
        prepare(owner)
        before = state(owner)
        current = owner.owner.snapshot()
        selected = current
        record = next(r for r in current.components if type(r) is AssistanceMemoryRecord)
        if damage == "world":
            selected = replace(current, world_id="f" * 32)
        elif damage == "pins":
            selected = replace(current, pins=replace(current.pins, schema_fingerprint="f" * 64))
        elif damage == "missing":
            selected = replace(
                current, components=tuple(r for r in current.components if r is not record)
            )
        elif damage == "duplicate":
            selected = replace(current, components=(*current.components, record))
        else:
            invalid = (
                replace(record, entity_id=EntityId("actor:foreign"))
                if damage == "owner"
                else replace(
                    record,
                    state=replace(
                        record.state, entries=(replace(record.state.entries[0], tick=20),)
                    ),
                )
            )
            selected = replace(
                current, components=tuple(invalid if r is record else r for r in current.components)
            )
        with pytest.raises(SaveError, match="^SAVE_INSPECT_FAILED:"):
            assistance_slot_comparison(selected, current, approved_content())
        assert state(owner) == before
    finally:
        owner.close()


def test_tk_previous_inspection_error_recovery_keeps_input_and_sources(
    tk_host: tk.Tk, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    gc.collect()
    path = tmp_path / "game.sqlite"
    owner = session(path)
    try:
        repeated(owner)
        owner.save("slot01")
    finally:
        owner.close()
    sources = {p: p.read_bytes() for p in tmp_path.rglob("*.sqlite")}
    content = approved_content()
    panel = tk.Toplevel(tk_host)
    panel.withdraw()
    window = PlayWindow(
        panel,
        path,
        content.definition.layout,
        quest_content=content,
        **FLAGS,
        npc_assistance_memory=True,
    )
    try:
        _pump(panel, lambda: not window.busy)
        before = window.last_update
        assert before is not None

        def fail(*args: object, **kwargs: object) -> tuple[str, ...]:
            raise SaveError("SAVE_INSPECT_FAILED", "comparison unavailable")

        with monkeypatch.context() as patch:
            patch.setattr(client_module, "assistance_slot_comparison", fail)
            window.previous_slot_preview_button.invoke()
            _pump(panel, lambda: not window.busy)
            assert window.status.get() == "SAVE_INSPECT_FAILED" and window.view == before.view
        window.previous_slot_preview_button.invoke()
        assert window.busy and window.buttons["wait"].instate(["disabled"])
        _pump(panel, lambda: not window.busy)
        assert window.status.get() == "SLOT_INSPECTED"
        assert MORE_CURRENT in window.log_text.get("1.0", "end")
        assert all(p.read_bytes() == raw for p, raw in sources.items())
        _click(window, "wait")
        assert window.status.get() == "COMMITTED"
    finally:
        window.close()
        _pump(panel, lambda: window.closed)
        window.worker.join()
