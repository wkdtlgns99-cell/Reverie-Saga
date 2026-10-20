from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import time
import tkinter as tk
from typing import cast

import pytest

from app.client import PlayWindow
from app.client_worker import ClientWorker
from app.durable import create_durable
from app.npc_activity import return_recollection
from app.npc_memory_query import player_memory_recollection
from app.npc_work import work_bundle
from contracts.client import ClientUpdate
from contracts.dialogue import GenerationError
from contracts.persistence import DurableCheckpoint, SaveError
from domain.canonical import array_value, object_value, text_value
from domain.npc_memory import NpcQuestMemoryRecord, QuestEvidence, source_identity
from domain.primitives import EntityId
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_npc_work import session, work_pipe
from tests.integration.test_npc_work_recollection import current_talk
from tests.integration.test_quest import GOAL


def promise(tick: int) -> str:
    return f"NPC 플레이어 기억 · {tick}초: 의뢰를 맡겠다는 말을 직접 들었습니다. 아직 완료 보고는 받지 못했습니다."


def report(tick: int) -> str:
    return f"NPC 플레이어 기억 · {tick}초: 플레이어에게 완료 보고를 받았습니다. 처치를 직접 본 기억은 아닙니다."


def remembered(update: ClientUpdate) -> tuple[str, ...]:
    return tuple(
        message for message in update.messages if message.startswith("NPC 플레이어 기억 · ")
    )


@pytest.mark.parametrize("count", (0, 1, 2))
def test_selector_empty_promise_report_uses_latest_statement(count: int) -> None:
    npc = approved_content().definition.layout.npc_id
    entries = (
        QuestEvidence("accepted", 2, source_identity("world:test", 2)),
        QuestEvidence("completion_reported", 11, source_identity("world:test", 11)),
    )
    result = player_memory_recollection(NpcQuestMemoryRecord(npc, entries[:count]))
    assert result == (
        ("NPC 플레이어 기억 · 아직 기록된 의뢰 약속이나 완료 보고가 없습니다.",)
        if count == 0
        else (promise(2),)
        if count == 1
        else (report(11),)
    )


def test_selector_invalid_input_rejects_instead_of_fake_empty() -> None:
    with pytest.raises(GenerationError, match="^NPC_CONTEXT_INPUT$"):
        player_memory_recollection(cast(NpcQuestMemoryRecord, object()))


def test_unobserved_defeat_never_becomes_received_report_and_talk_commits_anchor(
    tmp_path: Path,
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        assert not remembered(owner.act("talk"))  # rejected,no extra memory context
        owner.act("down")
        assert remembered(owner.act("talk")) == (promise(2),)
        for action in GOAL[2:]:
            assert not remembered(owner.act(action))
        current = owner.update()
        assert current.view is not None and current.view.enemy_hp == 0 and current.view.tick == 9
        assert current.quest_stage == 2 and current.quest_reward == 0
        memory = next(
            record
            for record in owner.owner.snapshot().components
            if isinstance(record, NpcQuestMemoryRecord)
        )
        assert player_memory_recollection(memory) == (promise(2),)
        assert len(memory.entries) == 1
        owner.act("left")
        returned = owner.act("talk")
        assert remembered(returned) == (report(11),) and returned.quest_reward == 1
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        assert not remembered(owner.retry())
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
        assert remembered(owner.act("talk")) == (report(11),)  # original report tick remains11
        assert owner.update().quest_reward == 1
    finally:
        owner.close()


def test_load_restart_uses_older_promise_then_its_own_new_report(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        for action in GOAL:
            owner.act(action)
        owner.save("slot01")  # tick9before report
        owner.act("left")
        assert remembered(owner.act("talk")) == (report(11),)
        owner.load("slot01")
        assert owner.update().quest_reward == 0
        memory = next(
            record
            for record in owner.owner.snapshot().components
            if isinstance(record, NpcQuestMemoryRecord)
        )
        assert player_memory_recollection(memory) == (promise(2),)
        path = owner.owner.working_path
    finally:
        owner.close()
    resumed = session(path)
    try:
        resumed.act("wait")
        resumed.act("left")
        assert remembered(resumed.act("talk")) == (report(12),)
        assert resumed.update().quest_reward == 1
    finally:
        resumed.close()


@pytest.mark.parametrize("reported", (False, True))
def test_persistent_statement_survives_checkpoint_without_original_trace(
    tmp_path: Path, reported: bool
) -> None:
    owner = session(tmp_path / "source/game.sqlite")
    try:
        if reported:
            for action in (*GOAL, "left", "talk"):
                owner.act(action)
        else:
            owner.act("down")
            owner.act("talk")
            owner.act("wait", seconds=16)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()
    path = tmp_path / "compacted/game.sqlite"
    durable = create_durable(path, checkpoint, bundles=(work_bundle(approved_content()),))
    durable.close()
    compacted = session(path)
    try:
        assert compacted.owner.retained_segment().trace.steps == ()
        update = compacted.act("talk")
        assert remembered(update) == ((report(11),) if reported else (promise(2),))
        assert update.quest_reward == int(reported)
    finally:
        compacted.close()


@pytest.mark.parametrize("damage", ("source", "future", "count", "owner"))
def test_unverified_persistent_anchor_is_rejected_readonly(tmp_path: Path, damage: str) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        segment, identity = current_talk(owner)
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        memory = next(
            record
            for record in checkpoint.core.components
            if isinstance(record, NpcQuestMemoryRecord)
        )
        entry = memory.entries[0]
        if damage == "source":
            changed = replace(memory, entries=(replace(entry, source_event_id="e1-" + "0" * 64),))
        elif damage == "future":
            changed = replace(
                memory,
                entries=(
                    replace(
                        entry,
                        observed_at=3,
                        source_event_id=source_identity(checkpoint.core.world_id, 3),
                    ),
                ),
            )
        elif damage == "count":
            changed = replace(memory, entries=())
        else:
            changed = replace(memory, entity_id=EntityId("actor:other"))
        invalid = replace(
            checkpoint,
            core=replace(
                checkpoint.core,
                components=tuple(
                    changed if record == memory else record for record in checkpoint.core.components
                ),
            ),
        )
        segment = replace(segment, checkpoint=invalid, trace=replace(segment.trace, steps=()))
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        with pytest.raises(SaveError, match="^NPC_RECOLLECTION_SOURCE:"):
            return_recollection(
                segment,
                approved_content().definition.layout.npc_id,
                content=approved_content(),
                current=checkpoint,
                conversation_id=identity,
            )
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
    finally:
        owner.close()


def test_combined_statement_context_readonly_and_measured(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        for action in (*GOAL, "left", "talk"):
            owner.act(action)
        segment, identity = current_talk(owner)
        before = (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        )
        started = time.perf_counter()
        result = return_recollection(
            segment,
            approved_content().definition.layout.npc_id,
            content=approved_content(),
            current=DurableCheckpoint(*before[:2]),
            conversation_id=identity,
        )
        elapsed = time.perf_counter() - started
        assert report(11) in result and promise(2) not in result
        assert elapsed < 2
        assert (
            owner.owner.snapshot(),
            owner.owner.protocol(),
            owner.owner.working_path.read_bytes(),
        ) == before
        (tmp_path / "latency.txt").write_text(str(elapsed), encoding="ascii")
    finally:
        owner.close()


def test_postcommit_statement_projection_failure_keeps_truth_retry_save_and_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import app.npc_activity as activity

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
        for action in (*GOAL, "left"):
            worker.request(action).result(timeout=30)
        with monkeypatch.context() as scoped:

            def unavailable(record: NpcQuestMemoryRecord) -> tuple[str, ...]:
                raise SaveError(
                    "NPC_RECOLLECTION_SOURCE", "injected player-memory projection failure"
                )

            scoped.setattr(activity, "player_memory_recollection", unavailable)
            failed = worker.request("talk").result(timeout=30)
            assert failed.status == "NPC_RECOLLECTION_SOURCE" and failed.view is not None
            assert failed.view.tick == 11 and failed.quest_reward == 1
            assert "행동은 확정됐지만" in failed.messages[0]
            assert worker.request("retry").result(timeout=30).view == failed.view
            assert worker.request("save").result(timeout=30).status == "SAVED"
        assert "committed NPC talk recollection failed" in caplog.text
        recovered = worker.request("talk").result(timeout=30)
        assert recovered.status == "COMMITTED" and recovered.quest_reward == 1
        assert remembered(recovered) == (report(11),)
    finally:
        worker.join()


def test_real_pipe_persistent_statement_report_and_rewind(tmp_path: Path) -> None:
    path = tmp_path / "game.sqlite"
    with work_pipe(path) as pipe:
        pipe.send("attach")
        for action in GOAL:
            pipe.send(action)
        pipe.send("save")
        pipe.send("left")
        messages = array_value(object_value(pipe.send("talk")["update"])["messages"])
        assert report(11) in tuple(map(text_value, messages))
        pipe.send("load")
        path = Path(text_value(object_value(pipe.latest["update"])["working_path"]))
    with work_pipe(path) as pipe:
        pipe.send("attach")
        pipe.send("wait")
        pipe.send("left")
        messages = array_value(object_value(pipe.send("talk")["update"])["messages"])
        assert report(12) in tuple(map(text_value, messages))
        assert report(11) not in tuple(map(text_value, messages))


def test_actual_tk_promise_and_report_recollection(tk_host: tk.Tk, tmp_path: Path) -> None:
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
        for action in GOAL:
            _click(screen, action)
            if action == "talk":
                assert screen.last_update is not None and remembered(screen.last_update) == (
                    promise(2),
                )
        for action in ("left", "talk"):
            _click(screen, action)
        assert screen.last_update is not None and remembered(screen.last_update) == (report(11),)
        _click(screen, "talk")
        assert screen.last_update is not None and remembered(screen.last_update) == (report(11),)
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())
