from __future__ import annotations

import gc
import os
from pathlib import Path
import tkinter as tk
from typing import cast

import pytest

from adapters.sqlite_store import validate_save
from app.client import PlayWindow
from app.client_worker import ClientWorker
from app.durable import create_durable
from contracts.persistence import SaveError, WorldUnavailable
from domain.canonical import array_value, object_value, text_value
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_engine_bridge import PipeClient, pipe as pipe, view
from tests.integration.test_memory_client_route import approved_content, memory_pipe
from tests.integration.test_npc_memory import session_at
from tests.integration.test_quest import GOAL
from tests.unit.durability_fixtures import checkpoint, io
from app.watch_registry import watch_bundle
from tests.integration.test_durable_turn import UncertainPort
from contracts.watch import WaitCommand
from tests.unit.watch_fixtures import command


def test_storage_preview_is_validated_latest_checkpoint_without_clones(tmp_path: Path) -> None:
    working = tmp_path / "game.sqlite"
    owner = create_durable(working, checkpoint(), bundles=(watch_bundle(),))
    try:
        owner.export("slot01")
        slot = tmp_path / "slots/slot01.sqlite"
        files = {
            p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*.sqlite")
        }
        token, current = owner.attachment_id, owner.snapshot()
        assert owner.inspect_slot("slot01") == validate_save(slot, io=io())
        assert owner.attachment_id == token and owner.snapshot() == current
        assert {
            p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*.sqlite")
        } == files
        assert not list(tmp_path.glob(".loaded-*.sqlite"))
    finally:
        owner.close()
    with pytest.raises(WorldUnavailable, match="^SESSION_CLOSED:"):
        owner.inspect_slot("slot01")


@pytest.mark.parametrize("bad", ("slot00", "slot09", "../slot01", "slot01.sqlite", "", True))
def test_invalid_slot_preview_preserves_attachment(tmp_path: Path, bad: object) -> None:
    owner = create_durable(tmp_path / "game.sqlite", checkpoint(), bundles=(watch_bundle(),))
    try:
        before = owner.snapshot(), owner.protocol(), owner.attachment_id
        with pytest.raises(SaveError, match="^INVALID_SLOT:"):
            owner.inspect_slot(cast(str, bad))
        assert (owner.snapshot(), owner.protocol(), owner.attachment_id) == before
        assert not list((tmp_path / "slots").iterdir())
    finally:
        owner.close()


def test_preview_missing_corrupt_hardlink_busy_and_io_failure_are_nonmutating(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    working = tmp_path / "game.sqlite"
    owner = create_durable(working, checkpoint(), bundles=(watch_bundle(),))
    slot = tmp_path / "slots/slot01.sqlite"
    try:
        before = working.read_bytes(), owner.snapshot(), owner.protocol(), owner.attachment_id
        with pytest.raises(SaveError, match="^SAVE_NOT_FOUND:"):
            owner.inspect_slot("slot01")
        slot.write_bytes(b"corrupt-slot")
        with pytest.raises(SaveError, match="^SAVE_CORRUPT:"):
            owner.inspect_slot("slot01")
        assert slot.read_bytes() == b"corrupt-slot"
        slot.unlink()
        owner.export("slot01")
        alias = tmp_path / "slot-alias.sqlite"
        os.link(slot, alias)
        try:
            with pytest.raises(SaveError, match="^INVALID_PATH:"):
                owner.inspect_slot("slot01")
        finally:
            alias.unlink()
        slot_body = slot.read_bytes()
        owner._busy = True
        try:
            with pytest.raises(SaveError, match="^SAVE_BUSY:"):
                owner.inspect_slot("slot01")
        finally:
            owner._busy = False
        owner._attachment.slots._busy = True
        try:
            with pytest.raises(SaveError, match="^SAVE_BUSY:"):
                owner.inspect_slot("slot01")
        finally:
            owner._attachment.slots._busy = False

        def inaccessible(*args: object, **kwargs: object) -> None:
            raise OSError("preview read unavailable")

        with monkeypatch.context() as patch:
            patch.setattr("adapters.save_slots.validate_save", inaccessible)
            with pytest.raises(SaveError, match="^SAVE_INSPECT_FAILED:"):
                owner.inspect_slot("slot01")
        assert owner.inspect_slot("slot01").core == before[1]
        assert slot.read_bytes() == slot_body
        assert (
            working.read_bytes(),
            owner.snapshot(),
            owner.protocol(),
            owner.attachment_id,
        ) == before
        assert owner._attachment.slots._busy is False and owner._busy is False
    finally:
        owner.close()


@pytest.mark.parametrize("commit", (False, True))
def test_preview_respects_uncertain_commit_until_real_recovery(
    tmp_path: Path, commit: bool
) -> None:
    working = tmp_path / "game.sqlite"
    owner = create_durable(working, checkpoint(), bundles=(watch_bundle(),))
    try:
        owner.export("slot01")
        slot = tmp_path / "slots/slot01.sqlite"
        original_slot = slot.read_bytes()
        port = UncertainPort(owner._attachment.store, commit=commit, unreadable=True)
        owner._attachment.owner._driver._commit_port = port
        with pytest.raises(WorldUnavailable, match="^SAVE_UNCERTAIN:"):
            owner.submit(command(WaitCommand(16)), attachment_id=owner.attachment_id)
        persisted = working.read_bytes()
        with pytest.raises(WorldUnavailable, match="^SAVE_UNCERTAIN:"):
            owner.inspect_slot("slot01")
        assert working.read_bytes() == persisted and slot.read_bytes() == original_slot
        assert not list(tmp_path.glob(".loaded-*.sqlite"))
        port.unreadable = False
        owner.recover()
        assert owner.snapshot().tick == (16 if commit else 0)
        assert owner.inspect_slot("slot01").core.tick == 0
        assert working.read_bytes() == persisted and slot.read_bytes() == original_slot
    finally:
        owner.close()


def test_saved_memory_preview_uses_slot_not_current_world_and_preserves_retry(
    tmp_path: Path,
) -> None:
    owner = session_at(tmp_path / "game.sqlite", 2)
    slot = tmp_path / "slots/slot01.sqlite"
    try:
        owner.save("slot01")
        for action in (*GOAL[2:], "left", "talk"):
            assert owner.act(action).status == "COMMITTED"
        current = owner.owner.snapshot(), owner.owner.protocol(), owner.owner.attachment_id
        bodies = owner.owner.working_path.read_bytes(), slot.read_bytes()
        preview = owner.inspect_slot("slot01")
        assert preview.status == "SLOT_INSPECTED" and preview.reset_log is False
        assert preview.view is not None and preview.view.tick == 11 and preview.quest_reward == 1
        assert preview.messages == (
            "slot01 저장 정보 · 2초 · 진행 2",
            "저장된 임무: 진행 중 · 포구의 호의 0",
            "저장된 NPC 대화 기억: 1개 · 완료 보고를 받은 기억은 없습니다.",
            "NPC 기억 비교 · 현재 11초 / 선택 저장 2초",
            "공통 1개 · 현재에만 1개 · 저장에만 0개",
            "저장 시점·진행 분기의 차이이며, NPC가 기억을 잊었다는 뜻은 아닙니다.",
            "공통 기억 · 2초: 의뢰를 맡겠다는 말을 직접 들었습니다.",
            "현재에만 있는 기억 · 11초: 플레이어에게 완료 보고를 받았습니다. 처치를 직접 본 기억은 아닙니다.",
        )
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.attachment_id,
        ) == current
        assert (owner.owner.working_path.read_bytes(), slot.read_bytes()) == bodies
        assert "다시 실행하지 않았습니다" in owner.retry().messages[0]
        assert owner.owner.snapshot() == current[0]
        owner.save("slot01")
        newer = owner.inspect_slot("slot01")
        assert newer.messages[0] == "slot01 저장 정보 · 11초 · 진행 11"
        assert newer.messages[1] == "저장된 임무: 완료 · 포구의 호의 1"
        assert (
            newer.messages[2]
            == "저장된 NPC 대화 기억: 2개 · 플레이어의 완료 보고를 받은 기억이 있습니다."
        )
        assert not list(tmp_path.glob(".loaded-*.sqlite"))
        owner.load("slot01")
        token = owner.owner.attachment_id
        assert owner.inspect_slot("slot01").messages == newer.messages
        assert owner.owner.attachment_id == token
    finally:
        owner.close()


def test_slot_preview_worker_before_attach_closing_and_after_failure(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    worker = ClientWorker(path)
    try:
        unavailable = worker.inspect_slot().result(timeout=15)
        assert unavailable.status == "SLOT_INSPECTION_UNAVAILABLE" and not path.exists()
        attached = worker.request("attach").result(timeout=15)
        assert worker.inspect_slot().result(timeout=15).status == "SAVE_NOT_FOUND"
        assert worker.inspect_slot("../bad").result(timeout=15).status == "INVALID_SLOT"
        assert worker.request("wait").result(timeout=15).status == "COMMITTED"
        worker.request("save").result(timeout=15)
        reply = worker.inspect_slot().result(timeout=15)
        assert reply.status == "SLOT_INSPECTED" and reply.attachment_id == attached.attachment_id
        assert reply.messages == ("slot01 저장 정보 · 1초 · 진행 1",)
    finally:
        worker.join()
    with pytest.raises(ValueError, match="^CLIENT_CLOSING$"):
        worker.inspect_slot()


def preview(pipe: PipeClient) -> tuple[str, ...]:
    before = object_value(pipe.latest["update"])
    working = Path(text_value(before["working_path"]))
    files = {
        p.relative_to(working.parent).as_posix(): p.read_bytes()
        for p in working.parent.rglob("*.sqlite")
    }
    response = pipe.send("slot_inspect")
    current = object_value(response["update"])
    assert response["error"] == "" and current["status"] == "SLOT_INSPECTED"
    for key in ("view", "attachment_id", "working_path", "quest_stage", "quest_reward"):
        assert current[key] == before[key]
    assert current["reset_log"] is False
    assert {
        p.relative_to(working.parent).as_posix(): p.read_bytes()
        for p in working.parent.rglob("*.sqlite")
    } == files
    return tuple(text_value(value) for value in array_value(current["messages"]))


def test_actual_memory_pipe_preview_load_stale_attachment_and_resume(tmp_path: Path) -> None:
    with memory_pipe(tmp_path, tmp_path / "game.sqlite") as client:
        assert object_value(client.send("slot_inspect")["update"])["status"] == "SAVE_NOT_FOUND"
        for action in GOAL[:2]:
            client.send(action)
        client.send("save")
        for action in (*GOAL[2:], "left", "talk"):
            client.send(action)
        assert preview(client)[0] == "slot01 저장 정보 · 2초 · 진행 2"
        assert view(client.send("retry"))["tick"] == "11"
        token = client.token
        loaded = client.send("load")
        path = Path(text_value(object_value(loaded["update"])["working_path"]))
        assert client.send("slot_inspect", token=token)["error"] == "STALE_ATTACHMENT"
        assert preview(client)[0] == "slot01 저장 정보 · 2초 · 진행 2"
        assert client.send("slot_inspect", sequence=client.id)["error"] == "STALE_REQUEST"
    with memory_pipe(tmp_path, path) as resumed:
        assert preview(resumed)[0] == "slot01 저장 정보 · 2초 · 진행 2"
        assert view(resumed.send("wait"))["tick"] == "3"


def test_actual_legacy_pipe_preview(pipe: PipeClient) -> None:
    pipe.send("wait")
    pipe.send("save")
    pipe.send("wait")
    assert preview(pipe) == ("slot01 저장 정보 · 1초 · 진행 1",)
    assert view(pipe.latest)["tick"] == "2"


def test_real_tk_selected_slot_preview_busy_readonly_and_continued_load(
    tmp_path: Path, tk_host: tk.Tk
) -> None:
    selected = approved_content()
    gc.collect()
    root = tk.Toplevel(tk_host)
    root.withdraw()
    screen = PlayWindow(
        root,
        tmp_path / "ui.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
    )
    try:
        _pump(root, lambda: not screen.busy)
        screen.slot.set("slot02")
        screen.slot_preview_button.invoke()
        _pump(root, lambda: not screen.busy)
        assert screen.last_update is not None and screen.last_update.status == "SAVE_NOT_FOUND"
        screen.slot.set("slot01")
        for action in GOAL[:2]:
            _click(screen, action)
        screen.buttons["save"].invoke()
        _pump(root, lambda: not screen.busy)
        _click(screen, "wait")
        current = screen.view
        screen.slot_preview_button.invoke()
        assert screen.busy and str(screen.slot_preview_button.cget("state")) == "disabled"
        assert (
            screen.memory_button is not None
            and str(screen.memory_button.cget("state")) == "disabled"
        )
        screen._inspect_slot()
        _pump(root, lambda: not screen.busy)
        assert screen.view == current and screen.last_update.status == "SLOT_INSPECTED"
        assert "slot01 저장 정보 · 2초 · 진행 2" in screen.log_text.get("1.0", "end")
        assert str(screen.slot_preview_button.cget("state")) == "normal"
        screen.buttons["load"].invoke()
        _pump(root, lambda: not screen.busy)
        assert screen.view is not None and screen.view.tick == 2
        _click(screen, "wait")
    finally:
        screen.close()
        assert str(screen.slot_preview_button.cget("state")) == "disabled"
        _pump(root, lambda: screen.closed)
        screen.worker.join()
