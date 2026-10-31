"""Real selected clients, persistence and failure boundaries for the child mode."""

from dataclasses import asdict
from pathlib import Path
import hashlib
import os
import sqlite3
import subprocess
import sys
from typing import cast

import pytest

from app.client_session import ClientSession
from app.client_worker import ClientWorker
from app.engine_bridge import wire
from app.npc_cycle import cycle_bundle
from app.durable import create_durable
from contracts.client import ClientAction
from contracts.persistence import DurableCheckpoint, SaveError
from domain.canonical import object_value, array_value
from domain.npc_assistance_memory import AssistanceMemory, AssistanceMemoryRecord
from tests.integration.test_durable_turn import UncertainPort
from tests.integration.test_engine_bridge import PipeClient
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_quest_patrol import state
from tests.integration.test_reach_gate_aid import FLAGS
from tests.integration.test_npc_assistance_memory import CHILD_FLAGS
from app.client import PlayWindow, main as client_main
from app.engine_bridge import main as bridge_main
from tests.integration.test_client import _click, _pump, tk_host as tk_host
import tkinter as tk


def session(path: Path) -> ClientSession:
    content = approved_content()
    return ClientSession(
        path, content.definition.layout, quest_content=content, **FLAGS, npc_assistance_memory=True
    )


def memory(owner: ClientSession) -> AssistanceMemory:
    return next(
        r.state for r in owner.owner.snapshot().components if type(r) is AssistanceMemoryRecord
    )


def prepare(owner: ClientSession, tick: int = 16) -> None:
    for action in ("down", "talk", "up"):
        assert owner.act(action).status == "COMMITTED"
    assert owner.act("wait", seconds=tick - 3).status == "COMMITTED"


@pytest.mark.parametrize("kind", ("session", "worker"))
@pytest.mark.parametrize(
    "value,parent", ((True, False), (0, True), (1, True), (None, True), ("1", True))
)
def test_leaf_rejects_before_open_or_thread(
    tmp_path: Path, kind: str, value: object, parent: bool
) -> None:
    flags = FLAGS.copy()
    flags["npc_reach_aid"] = parent
    content = approved_content()
    path = tmp_path / "absent/game.sqlite"
    ctor = ClientSession if kind == "session" else ClientWorker
    with pytest.raises(ValueError, match="^NPC_ASSISTANCE_MEMORY_CONTENT$"):
        ctor(
            path,
            content.definition.layout,
            quest_content=content,
            **flags,
            npc_assistance_memory=cast(bool, value),
        )
    assert not path.parent.exists()


def test_compaction_save_previous_load_restart_and_old_mode_isolation(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        prepare(owner)
        assert memory(owner).total_assists == 1
        owner.save("slot01")
        owner.act("down")
        owner.act("close")
        owner.act("wait", seconds=2)
        for _ in range(3):
            owner.act("close")
            owner.act("wait", seconds=3)
        expected = memory(owner)
        assert expected.total_assists == 5
        assert tuple(e.tick for e in expected.entries) == (20, 24, 28, 32)
        owner.save("slot01")
        before = state(owner)
        assert (
            "저장된 NPC 지속 도움 기억: 누적 1회 · 최근 1개를 보관합니다."
            in owner.inspect_slot("slot01", previous=True).messages
        )
        assert state(owner) == before
        checkpoint = DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
        compact = tmp_path / "compact/game.sqlite"
        create_durable(
            compact, checkpoint, bundles=(cycle_bundle(approved_content(), **CHILD_FLAGS),)
        ).close()
        loaded = owner.load("slot01", previous=True)
        branch = Path(loaded.working_path)
        assert memory(owner).total_assists == 1
    finally:
        owner.close()
    owner = session(branch)
    try:
        assert memory(owner).total_assists == 1
    finally:
        owner.close()
    raw = compact.read_bytes()
    owner = session(compact)
    try:
        assert not owner.owner.retained_segment().trace.steps
        assert memory(owner) == expected
        before = state(owner)
        rows = owner.inspect_activity().messages
        assert "NPC 지속 도움 기억: 누적 5회 · 최근 4개를 보관합니다." in rows
        assert len([r for r in rows if r.startswith("NPC 도움 기억 ·")]) == 4
        assert state(owner) == before
    finally:
        owner.close()
    assert compact.read_bytes() == raw
    with pytest.raises(SaveError) as error:
        ClientSession(
            compact, approved_content().definition.layout, quest_content=approved_content(), **FLAGS
        )
    assert error.value.code == "UNSUPPORTED_RULESET" and compact.read_bytes() == raw


@pytest.mark.parametrize("commit", (False, True))
def test_uncertain_commit_recovers_gate_and_memory_together(tmp_path: Path, commit: bool) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        prepare(owner, 15)
        before = state(owner)
        store = owner.owner._attachment.store
        port = UncertainPort(store, commit=commit)
        owner.owner._attachment.owner._driver._commit_port = port
        result = owner.act("bell")
        assert port.persist_calls == port.recover_calls == 1
        assert result.status == ("COMMITTED" if commit else "SAVE_UNAVAILABLE")
        assert memory(owner).total_assists == int(commit)
        if commit:
            entry = memory(owner).entries[0]
            assert (entry.tick, entry.source_kind) == (16, "answered_call")
            after = state(owner)
            owner.retry()
            assert state(owner) == after
        else:
            assert state(owner) == before
        assert store.load() == DurableCheckpoint(owner.owner.snapshot(), owner.owner.protocol())
    finally:
        owner.close()


def test_sql_rollback_then_retry_adds_exactly_one_memory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        prepare(owner, 15)
        before = state(owner)
        store = owner.owner._attachment.store
        original = store._execute

        def fail(
            query: str, values: tuple[None | int | float | str | bytes, ...] = ()
        ) -> sqlite3.Cursor:
            result = original(query, values)
            if query.startswith("INSERT INTO replay"):
                raise sqlite3.IntegrityError("F97 atomic rollback")
            return result

        with monkeypatch.context() as patch:
            patch.setattr(store, "_execute", fail)
            assert owner.act("bell").status == "SAVE_UNAVAILABLE"
        assert state(owner) == before
        assert owner.retry().status == "COMMITTED"
        assert memory(owner).total_assists == 1
        after = state(owner)
        owner.retry()
        assert state(owner) == after
    finally:
        owner.close()


def test_actual_framed_mode_matches_direct_and_reopens_source(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    content = approved_content()
    catalog = root / "content/narratives.json"
    source_paths = ("app.engine_bridge", "engines.encounter", "domain.canonical")
    launcher = "import importlib,pathlib,hashlib;"
    for module in source_paths:
        path = root / "src" / Path(*module.split(".")).with_suffix(".py")
        launcher += f"m=importlib.import_module({module!r});assert pathlib.Path(m.__file__).resolve()==pathlib.Path({str(path)!r}).resolve();assert hashlib.sha256(pathlib.Path(m.__file__).read_bytes()).hexdigest()=={hashlib.sha256(path.read_bytes()).hexdigest()!r};"
    launcher += "from app.engine_bridge import main;raise SystemExit(main())"
    args = [
        sys.executable,
        "-c",
        launcher,
        "--working",
        str(tmp_path / "pipe/game.sqlite"),
        "--catalog",
        str(catalog),
        "--catalog-sha256",
        hashlib.sha256(catalog.read_bytes()).hexdigest(),
        "--scenario",
        "harbor",
        "--quest-catalog",
        str(root / "content/dialogue/harbor-memory-v1.json"),
        "--quest-sha256",
        content.catalog_sha256,
        *("--" + k.replace("_", "-") for k in FLAGS),
        "--npc-assistance-memory",
    ]
    process = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=root,
        env=dict(os.environ, PYTHONPATH=str(root / "src"), PYTHONUTF8="1"),
    )
    owner = session(tmp_path / "direct/game.sqlite")
    try:
        pipe = PipeClient(process)
        for action in (
            "down",
            "talk",
            "up",
            *("wait" for _ in range(13)),
            "activity",
            "save",
            "retry",
            "slot_inspect",
            "load",
            "activity",
        ):
            if action == "activity":
                result = owner.inspect_activity()
            elif action == "save":
                result = owner.save("slot01")
            elif action == "load":
                result = owner.load("slot01")
            elif action == "slot_inspect":
                result = owner.inspect_slot("slot01")
            elif action == "retry":
                result = owner.retry()
            else:
                result = owner.act(cast(ClientAction, action))
            actual = object_value(pipe.send(action)["update"])
            expected = object_value(wire(asdict(result)))
            # Owner paths intentionally differ; the entire public gameplay projection agrees.
            assert (
                actual["view"] == expected["view"]
                and actual["messages"] == expected["messages"]
                and actual["status"] == expected["status"]
            )
            if action == "activity":
                assert "NPC 지속 도움 기억: 누적 1회 · 최근 1개를 보관합니다." in array_value(
                    actual["messages"]
                )
                assert (
                    "NPC 도움 기억 · 16초: 통행문을 열었습니다 · 원인: 정기 행동."
                    in array_value(actual["messages"])
                )
        reopened_path = Path(str(actual["working_path"]))
    finally:
        owner.close()
        assert (
            process.stdin is not None and process.stdout is not None and process.stderr is not None
        )
        process.stdin.close()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=15)
            raise
        process.stdout.close()
        errors = process.stderr.read()
        process.stderr.close()
        assert process.returncode == 0, errors.decode("utf-8")
    reopened = session(reopened_path)
    try:
        assert memory(reopened).total_assists == 1
        assert (
            "NPC 도움 기억 · 16초: 통행문을 열었습니다 · 원인: 정기 행동."
            in reopened.inspect_activity().messages
        )
    finally:
        reopened.close()


def test_both_cli_leaf_error_before_files_or_window(tmp_path: Path) -> None:
    path = tmp_path / "absent/game.sqlite"
    with pytest.raises(ValueError, match="^NPC_ASSISTANCE_MEMORY_CONTENT$"):
        client_main(["--working", str(path), "--npc-assistance-memory"])
    assert (
        bridge_main(
            [
                "--working",
                str(path),
                "--catalog",
                str(tmp_path / "missing.json"),
                "--catalog-sha256",
                "0" * 64,
                "--npc-assistance-memory",
            ]
        )
        == 1
    )
    assert not path.parent.exists()


def test_worker_and_withdrawn_tk_failure_recovery_next_input_close(
    tk_host: tk.Tk, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = approved_content()
    worker = ClientWorker(
        tmp_path / "worker/game.sqlite",
        content.definition.layout,
        quest_content=content,
        **FLAGS,
        npc_assistance_memory=True,
    )
    try:
        for action in ("down", "talk", "up"):
            worker.request(action).result(timeout=10)
        worker.request("wait", seconds=13).result(timeout=10)
        assert (
            "NPC 지속 도움 기억: 누적 1회 · 최근 1개를 보관합니다."
            in worker.inspect_activity().result(timeout=10).messages
        )
    finally:
        worker.join()
    panel = tk.Toplevel(tk_host)
    panel.withdraw()
    screen = PlayWindow(
        panel,
        tmp_path / "tk/game.sqlite",
        content.definition.layout,
        quest_content=content,
        **FLAGS,
        npc_assistance_memory=True,
    )
    try:
        _pump(panel, lambda: not screen.busy)
        assert screen.mode_label == "NPC 지속 도움 기억·인접 통행 지원 모드"
        for action in ("down", "talk", "up"):
            _click(screen, cast(ClientAction, action))
        assert (
            screen.last_update is not None
            and "NPC 지속 도움 기억: 누적 0회" in screen.log_text.get("1.0", "end")
        )
        import app.client_session as module

        def fail(*args: object, **kwargs: object) -> tuple[str, ...]:
            raise SaveError("NPC_ACTIVITY_SOURCE", "F97 source failure")

        with monkeypatch.context() as patch:
            patch.setattr(module, "assistance_messages", fail)
            screen._inspect_activity()
            _pump(panel, lambda: not screen.busy)
            assert "NPC_ACTIVITY_SOURCE" in screen.status.get()
        screen._inspect_activity()
        _pump(panel, lambda: not screen.busy)
        assert "NPC 지속 도움 기억: 누적 0회" in screen.log_text.get("1.0", "end")
        _click(screen, "wait")
    finally:
        screen.close()
        screen.worker.join()
        _pump(panel, lambda: not panel.winfo_exists())


def test_postcommit_memory_query_failure_is_truthful_and_retry_is_readonly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        import app.client_session as module

        def fail(*args: object, **kwargs: object) -> tuple[str, ...]:
            raise SaveError("NPC_RECOLLECTION_SOURCE", "F97 committed query failure")

        with monkeypatch.context() as patch:
            patch.setattr(module, "assistance_messages", fail)
            with pytest.raises(SaveError) as error:
                owner.act("talk")
            assert error.value.code == "NPC_RECOLLECTION_SOURCE"
        assert owner.owner.snapshot().tick == 2
        assert "committed cycle call recollection failed" in caplog.text
        before = state(owner)
        owner.retry()
        assert state(owner) == before and memory(owner).total_assists == 0
        assert owner.act("up").status == "COMMITTED"
    finally:
        owner.close()


def test_unheard_manual_open_already_open_and_rejected_commands_add_nothing(tmp_path: Path) -> None:
    owner = session(tmp_path / "unheard/game.sqlite")
    try:
        owner.act("wait", seconds=16)
        assert memory(owner).total_assists == 0
    finally:
        owner.close()
    owner = session(tmp_path / "manual/game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        assert owner.act("open").status == "COMMITTED"
        owner.act("up")
        owner.act("wait", seconds=16)
        assert memory(owner).total_assists == 0
        before = state(owner)
        assert owner.act("attack").status == "OUT_OF_RANGE"
        assert state(owner) == before
    finally:
        owner.close()


def test_native_selector_preparation_has_dedicated_isolated_flow() -> None:
    root = Path(__file__).resolve().parents[2] / "clients/unity/Assets/Reverie/Scripts"
    brain = (root / "BrainConnection.cs").read_text(encoding="utf-8")
    room = (root / "PlayRoom.cs").read_text(encoding="utf-8")
    flow = (root / "LiveVerification.cs").read_text(encoding="utf-8")
    assert "bool npcAssistanceMemory = false" in brain and " --npc-assistance-memory" in brain
    assert "REVERIE_UNITY_NPC_ASSISTANCE_MEMORY" in room
    assert "NPC_ASSISTANCE_MEMORY_SELECTION" in room and "NPC_ASSISTANCE_MEMORY_CONTENT" in room
    assert 'npcAssistanceMemory?"harbor-assistance-memory"' in room
    assert "npcReadyPatrol,npcReachAid,npcAssistanceMemory)" in room
    assert flow.index("if(room.NpcAssistanceMemoryEnabled)") < flow.index(
        "if(room.NpcReachAidEnabled)"
    )
    assert "NPC 도움 기억 · 16초: 통행문을 열었습니다 · 원인: 정기 행동." in flow


def test_reported_quest_stops_assistance_and_keeps_existing_memory(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        prepare(owner)
        expected = memory(owner)
        for action in ("down", "right"):
            assert owner.act(action).status == "COMMITTED"
        owner.act("wait", seconds=2)
        owner.act("down")
        for action in ("attack", "attack", "rest", "attack"):
            assert owner.act(cast(ClientAction, action)).status == "COMMITTED"
        owner.act("up")
        assert owner.act("talk").quest_reward == 1
        owner.act("left")
        owner.act("close")
        owner.act("wait", seconds=8)
        assert memory(owner) == expected
        owner.save("slot01")
        owner.load("slot01")
        assert memory(owner) == expected
    finally:
        owner.close()
