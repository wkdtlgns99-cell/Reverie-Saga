from __future__ import annotations

from pathlib import Path
from dataclasses import replace
import os
import subprocess
import sys

import pytest

from app.client_session import ClientSession
from app.client_worker import ClientWorker
from app.headless import _CheckpointFactory, state_io
from app.watch_registry import watch_bundle
from contracts.client import ClientUpdate, ClientView
from contracts.encounter import AttackCommand, InteractCommand
from contracts.messages import CommandPayload
from contracts.persistence import SaveError, WorldUnavailable
from contracts.turn import GameCommand, TurnCommitted, TurnRejected
from contracts.watch import BellCommand
from domain.encounter import ATTACK_PROFILE_ID, ENEMY_ID, GATE_ID
from domain.primitives import CommandId, EntityId
from domain.scenario import COURTYARD_SCENARIO, LEGACY_SCENARIO, Scenario
from domain.watch import NPC_ID
from orchestration.replay import Runner
from tests.integration.test_durable_turn import UncertainPort


def view(update: ClientUpdate) -> ClientView:
    assert update.view is not None
    return update.view


def test_courtyard_literal_movement_and_combat(tmp_path: Path) -> None:
    client = ClientSession(tmp_path / "courtyard.sqlite", scenario=COURTYARD_SCENARIO)
    try:
        initial = view(client.update())
        assert (
            initial.actor_cell,
            initial.enemy_cell,
            initial.gate_cell,
            initial.npc_cell,
            initial.walls,
        ) == (6, 0, 2, 8, (7,))
        blocked = view(client.act("right"))
        assert (blocked.actor_cell, blocked.tick) == (6, 1)
        assert view(client.act("up")).actor_cell == 3
        occupied = view(client.act("up"))
        assert (occupied.actor_cell, occupied.tick) == (3, 3)
        first = view(client.act("attack"))
        assert (first.actor_hp, first.enemy_hp, first.stamina) == (2, 3, 1)
        second = view(client.act("attack"))
        assert (second.actor_hp, second.enemy_hp, second.stamina) == (1, 1, 0)
        before = client.owner.snapshot(), client.owner.protocol()
        assert client.act("attack").status == "INSUFFICIENT_STAMINA"
        assert (client.owner.snapshot(), client.owner.protocol()) == before
        assert view(client.act("rest")).stamina == 1
        defeated = view(client.act("attack"))
        assert (defeated.actor_hp, defeated.enemy_hp, defeated.stamina) == (1, 0, 0)
        assert view(client.act("up")).actor_cell == 0
    finally:
        client.close()


def request(client: ClientSession, payload: CommandPayload) -> GameCommand:
    protocol = client.owner.protocol()
    stream = protocol.streams[0]
    identifier = (
        f"c1:{protocol.branch_id}:{stream.stream_id}:{stream.highest_committed_sequence + 1}"
    )
    return GameCommand(CommandId(identifier), stream.actor_id, protocol.revision, payload)


@pytest.mark.parametrize(
    "payload",
    [
        AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID),
        InteractCommand(GATE_ID, "open"),
        BellCommand(NPC_ID),
    ],
)
def test_old_targets_rejected_without_mutation(tmp_path: Path, payload: CommandPayload) -> None:
    client = ClientSession(tmp_path / "courtyard.sqlite", scenario=COURTYARD_SCENARIO)
    try:
        before = client.owner.snapshot(), client.owner.protocol(), client.update()
        result = client.owner.submit(
            request(client, payload), attachment_id=client.owner.attachment_id
        )
        assert isinstance(result.outcome, TurnRejected)
        assert result.outcome.failure.code == "INVALID_TARGET"
        assert not result.facts and result.diff is None
        assert (client.owner.snapshot(), client.owner.protocol(), client.update()) == before
    finally:
        client.close()


def test_courtyard_door_npc_and_literal_cues(tmp_path: Path) -> None:
    client = ClientSession(tmp_path / "courtyard.sqlite", scenario=COURTYARD_SCENARIO)
    try:
        assert view(client.act("up")).actor_cell == 3
        assert view(client.act("right")).actor_cell == 4
        assert view(client.act("up")).actor_cell == 1
        assert view(client.act("right")).actor_cell == 1
        result = client.owner.submit(
            request(client, InteractCommand(COURTYARD_SCENARIO.gate_id, "open")),
            attachment_id=client.owner.attachment_id,
        )
        assert isinstance(result.outcome, TurnCommitted)
        selected = state_io((watch_bundle(COURTYARD_SCENARIO),))
        gate = next(c.payload for c in result.cues if c.payload.schema.kind == "encounter.gate-cue")
        assert selected.encode_payload(gate) == {
            "actor_id": "actor:courtyard-player",
            "target_id": "object:courtyard-door",
            "cell": 2,
            "x_mm": 2000,
            "z_mm": 0,
            "before_open": 0,
            "after_open": 1,
        }
        assert view(client.act("right")).actor_cell == 2
        assert client.act("close").status == "TARGET_OCCUPIED"
        called = client.act("bell")
        state = view(called)
        assert (state.npc_cell, state.npc_bells, state.npc_replies, state.charge, state.tick) == (
            8,
            3,
            1,
            3,
            7,
        )
        assert any("플레이어가 NPC를 호출" in message for message in called.messages)
        assert all("actor:courtyard" not in message for message in called.messages)
    finally:
        client.close()


@pytest.mark.parametrize("scenario", [LEGACY_SCENARIO, COURTYARD_SCENARIO])
def test_save_load_retry_resume_and_replay(tmp_path: Path, scenario: Scenario) -> None:
    path = tmp_path / "game.sqlite"
    client = ClientSession(path, scenario=scenario)
    try:
        assert client.act("wait", seconds=3).status == "COMMITTED"
        saved = client.save("slot01")
        assert client.act("bell").status == "COMMITTED"
        duplicate = client.retry()
        assert view(duplicate).npc_replies == 1
        assert duplicate.notices == ()
        segment = client.owner.retained_segment()
        bundles = (watch_bundle(scenario),)
        selected = state_io(bundles)
        assert (
            Runner(
                segment.checkpoint.core,
                segment.checkpoint.protocol,
                factory=_CheckpointFactory(bundles),
                io=selected,
            ).run(segment.trace)
            == ()
        )
        loaded = client.load("slot01")
        assert loaded.view == saved.view
        assert loaded.attachment_id != saved.attachment_id
        assert loaded.working_path != saved.working_path
        with pytest.raises(ValueError, match="^NO_RETRY$"):
            client.retry()
        assert client.act("wait").status == "COMMITTED"
        before_recovery = client.owner.snapshot(), client.owner.protocol()
        with pytest.raises(SaveError, match="NO_RECOVERY_PENDING"):
            client.recover()
        assert (client.owner.snapshot(), client.owner.protocol()) == before_recovery
        expected = client.update().view
        path = Path(client.update().working_path)
    finally:
        client.close()
    resumed = ClientSession(path, scenario=scenario)
    try:
        assert resumed.update().view == expected
    finally:
        resumed.close()


def test_wrong_scenario_open_and_load_preserve_state(tmp_path: Path) -> None:
    courtyard_path, legacy_path = tmp_path / "courtyard.sqlite", tmp_path / "legacy.sqlite"
    courtyard = ClientSession(courtyard_path, scenario=COURTYARD_SCENARIO)
    try:
        courtyard.act("wait")
        courtyard.save("slot01")
    finally:
        courtyard.close()
    before_bytes = courtyard_path.read_bytes()
    with pytest.raises(SaveError, match="UNSUPPORTED_RULESET") as error:
        ClientSession(courtyard_path)
    assert error.value.code == "UNSUPPORTED_RULESET"
    assert courtyard_path.read_bytes() == before_bytes
    legacy = ClientSession(legacy_path)
    try:
        # Both working saves use this directory's actual slot root;no SQL/fixture rewriting.
        before = legacy.owner.snapshot(), legacy.owner.protocol(), legacy.update()
        files = {p.name: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
        with pytest.raises(SaveError, match="UNSUPPORTED_RULESET") as error:
            legacy.load("slot01")
        assert error.value.code == "UNSUPPORTED_RULESET"
        assert (legacy.owner.snapshot(), legacy.owner.protocol(), legacy.update()) == before
        assert {p.name: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == files
        assert legacy.act("wait").status == "COMMITTED"
    finally:
        legacy.close()


def test_role_order_is_independent_of_lexical_identity(tmp_path: Path) -> None:
    selected = replace(
        COURTYARD_SCENARIO, actor_id=EntityId("actor:a"), enemy_id=EntityId("actor:z")
    )
    client = ClientSession(tmp_path / "game.sqlite", scenario=selected)
    try:
        client.act("up")
        assert view(client.act("attack")).enemy_hp == 3
        client.save("slot01")
        assert client.load("slot01").status == "LOADED"
    finally:
        client.close()


def test_worker_uses_selected_scenario_on_owner_thread(tmp_path: Path) -> None:
    worker = ClientWorker(tmp_path / "game.sqlite", scenario=COURTYARD_SCENARIO)
    try:
        assert view(worker.request("attach").result(timeout=15)).actor_cell == 6
        assert view(worker.request("up").result(timeout=15)).actor_cell == 3
        attacked = worker.request("attack").result(timeout=15)
        assert (view(attacked).actor_hp, view(attacked).enemy_hp) == (2, 3)
        assert any("플레이어 → 적" in message for message in attacked.messages)
    finally:
        worker.join()


@pytest.mark.parametrize("hashseed", ["0", "2249326019"])
def test_fresh_process_replays_selected_room(tmp_path: Path, hashseed: str) -> None:
    path = tmp_path / "game.sqlite"
    client = ClientSession(path, scenario=COURTYARD_SCENARIO)
    try:
        client.act("up")
        client.act("attack")
        client.act("bell")
        selected = state_io((watch_bundle(COURTYARD_SCENARIO),))
        expected = selected.hash_core(client.owner.snapshot())
    finally:
        client.close()
    script = """
from pathlib import Path
import sys
from app.client_session import ClientSession
from app.headless import _CheckpointFactory, state_io
from app.watch_registry import watch_bundle
from domain.scenario import COURTYARD_SCENARIO
from orchestration.replay import Runner
client = ClientSession(Path(sys.argv[1]), scenario=COURTYARD_SCENARIO)
try:
    bundles = (watch_bundle(COURTYARD_SCENARIO),)
    selected = state_io(bundles)
    segment = client.owner.retained_segment()
    assert Runner(segment.checkpoint.core, segment.checkpoint.protocol,
                  factory=_CheckpointFactory(bundles), io=selected).run(segment.trace) == ()
    assert client.update().view.npc_replies == 1
    print(selected.hash_core(client.owner.snapshot()))
finally:
    client.close()
"""
    environment = {
        **os.environ,
        "PYTHONHASHSEED": hashseed,
        "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src"),
    }
    result = subprocess.run(
        [sys.executable, "-c", script, str(path)],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == expected


@pytest.mark.parametrize("committed", [False, True])
def test_courtyard_uncertain_attack_recovers_exactly_once(tmp_path: Path, committed: bool) -> None:
    client = ClientSession(tmp_path / "game.sqlite", scenario=COURTYARD_SCENARIO)
    try:
        client.act("up")
        store = client.owner._attachment.store
        port = UncertainPort(store, commit=committed, unreadable=True)
        client.owner._attachment.owner._driver._commit_port = port
        with pytest.raises(WorldUnavailable, match="SAVE_UNCERTAIN"):
            client.act("attack")
        port.unreadable = False
        recovered = view(client.recover())
        assert (recovered.actor_hp, recovered.enemy_hp, recovered.stamina, recovered.tick) == (
            (2, 3, 1, 2) if committed else (3, 5, 2, 1)
        )
        assert port.persist_calls == 1
        if committed:
            assert view(client.retry()) == recovered
            assert port.persist_calls == 1
        selected = state_io((watch_bundle(COURTYARD_SCENARIO),))
        assert selected.hash_core(store.load().core) == selected.hash_core(client.owner.snapshot())
    finally:
        client.close()


def test_real_tk_courtyard_buttons_and_slot(tmp_path: Path) -> None:
    import gc
    import tkinter as tk

    from app.client import PlayWindow
    from tests.integration.test_client import _pump

    gc.collect()
    root = tk.Tk()
    root.withdraw()
    panel = tk.Toplevel(root)
    panel.withdraw()
    screen = PlayWindow(panel, tmp_path / "ui.sqlite", scenario=COURTYARD_SCENARIO)
    try:
        _pump(root, lambda: not screen.busy)
        assert screen.view is not None
        assert screen.view.actor_cell == 6
        screen.buttons["right"].invoke()
        _pump(root, lambda: not screen.busy)
        assert screen.view.actor_cell == 6
        screen.buttons["up"].invoke()
        _pump(root, lambda: not screen.busy)
        assert screen.canvas.coords("actor") == [39.0, 183.0, 105.0, 249.0]
        screen.buttons["attack"].invoke()
        _pump(root, lambda: not screen.busy)
        assert (screen.view.actor_hp, screen.view.enemy_hp) == (2, 3)
        screen.buttons["save"].invoke()
        _pump(root, lambda: not screen.busy)
        saved = screen.view
        screen.buttons["rest"].invoke()
        _pump(root, lambda: not screen.busy)
        screen.buttons["load"].invoke()
        _pump(root, lambda: not screen.busy)
        assert screen.view == saved
        assert screen.status.get() == "LOADED"
    finally:
        screen.close()
        _pump(root, lambda: screen.closed)
        screen.worker.join()
        root.destroy()
        gc.collect()
