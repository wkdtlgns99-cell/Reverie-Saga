from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import subprocess
import sys
from typing import Iterator, cast

import pytest

from adapters.quest_dialogue import load_dialogue
from app.client import PlayWindow
from app.client_session import ClientSession
from app.client_worker import ClientWorker
from app.npc_dialogue_plan import preview_memory
from app.npc_memory import read_memory
from app.quest_definition import harbor_definition
from contracts.dialogue import QuestContent
from domain.canonical import object_value, text_value
from tests.integration.test_client import _click, _pump, tk_host as tk_host
from tests.integration.test_engine_bridge import PipeClient
from tests.integration.test_quest import GOAL
import tkinter as tk


def approved_content() -> QuestContent:
    root = Path(__file__).resolve().parents[2]
    pin = (root / "content/dialogue/harbor-memory-v1.sha256").read_text().strip()
    return load_dialogue(root / "content/dialogue/harbor-memory-v1.json", pin, harbor_definition())


def test_worker_memory_stages_retry_load_and_new_worker_resume(tmp_path: Path) -> None:
    selected, working = approved_content(), tmp_path / "game.sqlite"
    npc = selected.definition.layout.npc_id
    worker = ClientWorker(
        working, selected.definition.layout, quest_content=selected, npc_memory=True
    )
    try:
        assert worker.request("attach").result(timeout=30).quest_stage == 0
        assert read_memory(working, selected, npc).entries == ()
        for action in GOAL:
            assert worker.request(action).result(timeout=30).status == "COMMITTED"
        accepted = read_memory(working, selected, npc)
        assert [(entry.kind, entry.observed_at) for entry in accepted.entries] == [("accepted", 2)]
        assert accepted.source.known_phase == "accepted" and accepted.source.tick == 9
        worker.request("save").result(timeout=30)
        worker.request("left").result(timeout=30)
        reported = worker.request("talk").result(timeout=30)
        assert (reported.quest_stage, reported.quest_reward) == (3, 1)
        assert selected.dialogue.text("completion") in "\n".join(reported.messages)
        memory = read_memory(working, selected, npc)
        assert [(entry.kind, entry.observed_at) for entry in memory.entries] == [
            ("accepted", 2),
            ("completion_reported", 11),
        ]
        assert worker.request("retry").result(timeout=30).quest_reward == 1
        assert read_memory(working, selected, npc) == memory
        loaded = worker.request("load").result(timeout=30)
        assert (loaded.quest_stage, loaded.quest_reward) == (2, 0)
        resumed_path = Path(loaded.working_path)
        assert read_memory(resumed_path, selected, npc).entries == accepted.entries
    finally:
        worker.join()
    resumed = ClientWorker(
        resumed_path, selected.definition.layout, quest_content=selected, npc_memory=True
    )
    try:
        assert resumed.request("attach").result(timeout=30).quest_stage == 2
        resumed.request("left").result(timeout=30)
        assert resumed.request("talk").result(timeout=30).quest_reward == 1
        assert resumed.request("talk").result(timeout=30).quest_reward == 1
        current = read_memory(resumed_path, selected, npc)
        assert len(current.entries) == 2
        output = tmp_path / "from-client-plan.json"
        assert preview_memory(resumed_path, selected, npc, output) == current
    finally:
        resumed.join()


@pytest.mark.parametrize("flag", (1, "1", None))
def test_worker_invalid_memory_type_rejects_before_source_creation(
    tmp_path: Path, flag: object
) -> None:
    selected, working = approved_content(), tmp_path / "game.sqlite"
    with pytest.raises(ValueError, match="^NPC_MEMORY_CONTENT$"):
        ClientWorker(
            working, selected.definition.layout, quest_content=selected, npc_memory=cast(bool, flag)
        )
    assert not working.exists()


def test_worker_memory_requires_content_and_rejects_old_save_unchanged(tmp_path: Path) -> None:
    working, selected = tmp_path / "game.sqlite", approved_content()
    with pytest.raises(ValueError, match="^NPC_MEMORY_CONTENT$"):
        ClientWorker(working, npc_memory=True)
    classic = ClientSession(working, selected.definition.layout, quest_content=selected)
    classic.close()
    before = working.read_bytes()
    worker = ClientWorker(
        working, selected.definition.layout, quest_content=selected, npc_memory=True
    )
    try:
        attached = worker.request("attach").result(timeout=30)
        assert attached.view is None and attached.status == "UNSUPPORTED_RULESET"
        assert working.read_bytes() == before
    finally:
        worker.join()


@contextmanager
def memory_pipe(tmp_path: Path, working: Path) -> Iterator[PipeClient]:
    root = Path(__file__).resolve().parents[2]
    pin = (root / "content/dialogue/harbor-memory-v1.sha256").read_text().strip()
    guard = tmp_path / "guard"
    guard.mkdir(exist_ok=True)
    (guard / "sitecustomize.py").write_text(
        "import sys\ndef guard(event,args):\n if event.startswith('socket.') or event=='urllib.Request': raise RuntimeError('NETWORK_FORBIDDEN')\nsys.addaudithook(guard)\n",
        encoding="utf-8",
    )
    env = dict(os.environ)
    env.pop("GEMINI_API_KEY", None)
    env["PYTHONPATH"] = os.pathsep.join((str(guard), str(root / "src")))
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "app.engine_bridge",
            "--working",
            str(working),
            "--catalog",
            str(root / "content/narratives.json"),
            "--catalog-sha256",
            hashlib.sha256((root / "content/narratives.json").read_bytes()).hexdigest(),
            "--scenario",
            "harbor",
            "--quest-catalog",
            str(root / "content/dialogue/harbor-memory-v1.json"),
            "--quest-sha256",
            pin,
            "--npc-memory",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=root,
    )
    try:
        yield PipeClient(process)
    finally:
        if process.stdin is not None:
            process.stdin.close()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=15)
            pytest.fail("owned memory Brain did not stop on EOF")
        if process.stdout is not None:
            process.stdout.close()
        errors = b"" if process.stderr is None else process.stderr.read()
        if process.stderr is not None:
            process.stderr.close()
        assert process.returncode == 0, errors.decode(errors="replace")


def test_real_memory_binary_pipe_load_reconnect_and_offline_context(tmp_path: Path) -> None:
    selected, working = approved_content(), tmp_path / "pipe-game.sqlite"
    with memory_pipe(tmp_path, working) as pipe:
        for action in GOAL:
            pipe.send(action)
        pipe.send("save")
        pipe.send("left")
        finished = object_value(pipe.send("talk")["update"])
        assert (finished["quest_stage"], finished["quest_reward"]) == ("3", "1")
        known = read_memory(working, selected, selected.definition.layout.npc_id)
        assert len(known.entries) == 2
        pipe.send("retry")
        assert read_memory(working, selected, selected.definition.layout.npc_id) == known
        loaded = object_value(pipe.send("load")["update"])
        resumed_path = Path(text_value(loaded["working_path"]))
        assert loaded["quest_stage"] == "2"
    with memory_pipe(tmp_path, resumed_path) as resumed:
        assert object_value(resumed.latest["update"])["quest_stage"] == "2"
        resumed.send("left")
        assert object_value(resumed.send("talk")["update"])["quest_reward"] == "1"
    current = read_memory(resumed_path, selected, selected.definition.layout.npc_id)
    assert len(current.entries) == 2
    before = resumed_path.read_bytes()
    preview_memory(
        resumed_path, selected, selected.definition.layout.npc_id, tmp_path / "pipe-plan.json"
    )
    assert resumed_path.read_bytes() == before


def test_real_tk_memory_route_with_approved_dialogue(tmp_path: Path, tk_host: tk.Tk) -> None:
    selected, working = approved_content(), tmp_path / "tk-memory.sqlite"
    root = tk.Toplevel(tk_host)
    root.withdraw()
    screen = PlayWindow(
        root, working, selected.definition.layout, quest_content=selected, npc_memory=True
    )
    try:
        _pump(root, lambda: not screen.busy)
        for action in (*GOAL, "left", "talk"):
            _click(screen, action)
        assert screen.last_update is not None and screen.last_update.quest_reward == 1
        assert selected.dialogue.text("completion") in "\n".join(screen.history)
        assert len(read_memory(working, selected, selected.definition.layout.npc_id).entries) == 2
    finally:
        screen.close()
        _pump(root, lambda: screen.closed)
        screen.worker.join()
