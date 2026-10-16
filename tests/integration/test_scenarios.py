from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from app.client_session import ClientSession, _payload
from app.headless import replay_runner, state_io
from app.scenarios import select_scenario
from app.watch import WatchBootstrapSpec, bootstrap_watch
from app.watch_registry import watch_bundle
from contracts.client import ClientAction
from contracts.encounter import AttackCommand
from contracts.persistence import SaveError
from contracts.replay import ReplayFixture, ReplayHeader
from contracts.turn import GameCommand, TurnCommitted
from domain.canonical import hash_document, object_value
from domain.encounter import ATTACK_PROFILE_ID, ENEMY_ID
from domain.primitives import CommandId, EntityId
from domain.scenario import Scenario
from orchestration.replay import Recorder
from tests.integration.test_engine_bridge import PipeClient


def approach(key: str) -> tuple[ClientAction, ...]:
    return ("down", "open", "right", "down") if key == "harbor" else ("up", "open", "right", "up")


@pytest.mark.parametrize("key,cell", (("harbor", 7), ("grove", 1)))
def test_independent_combat_save_load_resume(tmp_path: Path, key: str, cell: int) -> None:
    layout = select_scenario(key).layout
    session = ClientSession(tmp_path / "game.sqlite", layout)
    try:
        for action in approach(key):
            assert session.act(action).status == "COMMITTED"
        first = session.act("attack")
        assert first.view is not None
        assert (
            first.view.actor_cell,
            first.view.actor_hp,
            first.view.enemy_hp,
            first.view.stamina,
            first.view.tick,
        ) == (cell, 2, 3, 1, 5)
        core, protocol = session.owner.snapshot(), session.owner.protocol()
        assert session.retry().view == first.view
        assert (session.owner.snapshot(), session.owner.protocol()) == (core, protocol)
        session.save("slot01")
        session.act("attack")
        loaded = session.load("slot01")
        assert loaded.view == first.view and loaded.reset_log
        assert loaded.scenario_id == layout.scenario_id
        resumed_path = Path(loaded.working_path)
        session.close()
        session = ClientSession(resumed_path, layout)
        assert session.update().view == first.view
        second = session.act("attack")
        assert second.view is not None
        assert (second.view.actor_hp, second.view.enemy_hp, second.view.stamina) == (1, 1, 0)
        session.act("rest")
        final = session.act("attack")
        assert final.view is not None
        assert (
            final.view.actor_hp,
            final.view.enemy_hp,
            final.view.stamina,
            final.view.tick,
            final.view.npc_bells,
        ) == (1, 0, 0, 8, 4)
        called = session.act("bell")
        assert called.view is not None and called.view.npc_replies == 1
        assert session.retry().view == called.view
        assert any("NPC" in line for line in called.messages)
    finally:
        session.close()


@pytest.mark.parametrize("key", ("harbor", "grove"))
def test_old_target_and_wrong_pin_preserve_state(tmp_path: Path, key: str) -> None:
    layout = select_scenario(key).layout
    path = tmp_path / "game.sqlite"
    session = ClientSession(path, layout)
    try:
        for action in approach(key):
            session.act(action)
        before, protocol = session.owner.snapshot(), session.owner.protocol()
        command = GameCommand(
            CommandId(f"c1:{protocol.branch_id}:{protocol.streams[0].stream_id}:5"),
            layout.actor_id,
            protocol.revision,
            AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID),
        )
        publication = session.owner.submit(command, attachment_id=session.owner.attachment_id)
        assert not isinstance(publication.outcome, TurnCommitted)
        assert publication.outcome.failure.code == "INVALID_TARGET"
        assert (session.owner.snapshot(), session.owner.protocol()) == (before, protocol)
        session.save("slot01")
    finally:
        session.close()
    saved = path.read_bytes()
    other = select_scenario("grove" if key == "harbor" else "harbor").layout
    with pytest.raises(SaveError) as caught:
        ClientSession(path, other)
    assert caught.value.code == "UNSUPPORTED_RULESET"
    assert path.read_bytes() == saved
    other_session = ClientSession(tmp_path / "other" / "game.sqlite", other)
    try:
        before_update = other_session.update()
        target = tmp_path / "other" / "slots"
        target.mkdir(exist_ok=True)
        shutil.copyfile(tmp_path / "slots" / "slot01.sqlite", target / "slot01.sqlite")
        with pytest.raises(SaveError) as caught:
            other_session.load("slot01")
        assert caught.value.code == "UNSUPPORTED_RULESET"
        assert other_session.update() == before_update
        assert other_session.act("wait").status == "COMMITTED"
    finally:
        other_session.close()


@pytest.mark.parametrize("key", ("harbor", "grove"))
def test_registered_replay_and_lexical_role_swap(key: str) -> None:
    layout = replace(
        select_scenario(key).layout, actor_id=EntityId("actor:aaa"), enemy_id=EntityId("actor:zzz")
    )
    selected = (watch_bundle(layout),)
    io = state_io(selected)
    live = bootstrap_watch(
        WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32, initial_cell=layout.initial_cell),
        layout=layout,
    )
    core, protocol = live.snapshot(), live.protocol()
    pins = core.pins
    header = ReplayHeader(
        core.world_id,
        core.world_seed_hex,
        io.hash_core(core),
        hash_document("protocol/v1", io.encode_protocol(protocol)),
        pins.schema_fingerprint,
        pins.rules_fingerprint,
        pins.schedule_fingerprint,
        pins.rng_version,
        pins.hash_version,
        (),
        (),
    )
    recorder = Recorder(header, io=io)
    for sequence, action in enumerate((*approach(key), "attack", "bell", "wait"), 1):
        command = GameCommand(
            CommandId(f"c1:{protocol.branch_id}:{protocol.streams[0].stream_id}:{sequence}"),
            layout.actor_id,
            live.protocol().revision,
            _payload(action, 2, layout),
        )
        live.driver.submit(command)
        assert isinstance(live.last_publication().outcome, TurnCommitted)
        recorder.record(command, live.last_publication(), live.snapshot(), live.protocol())
    trace = recorder.finish()
    assert live.snapshot().tick == 8
    fixture = ReplayFixture(core, protocol, trace)
    assert replay_runner(fixture, bundles=selected).run(trace) == ()
    # Each recorded NPC cue must use selected coordinates,including the swapped IDs.
    assert all(c.entity_id not in (ENEMY_ID,) for c in live.snapshot().components)


def test_definition_boundaries() -> None:
    layout = select_scenario("grove").layout
    for value in (True, -1, 9):
        with pytest.raises(ValueError, match="SCENARIO_CELL"):
            replace(layout, initial_cell=value)
    with pytest.raises(ValueError, match="SCENARIO_OVERLAP"):
        replace(layout, enemy_cell=layout.gate_cell)
    with pytest.raises(ValueError, match="SCENARIO_DUPLICATE_ID"):
        replace(layout, npc_id=layout.actor_id)
    with pytest.raises(ValueError, match="SCENARIO_WALLS"):
        replace(layout, blocked_cells=())
    with pytest.raises(ValueError, match="SCENARIO_ID"):
        replace(layout, actor_id=EntityId("object:wrong"))
    with pytest.raises(ValueError, match="SCENARIO_SELECTION"):
        select_scenario("unknown")
    assert Scenario().scenario_id == "scenario:legacy"


@pytest.mark.parametrize("key", ("harbor", "grove"))
def test_selected_wall_and_pending_wake(tmp_path: Path, key: str) -> None:
    session = ClientSession(tmp_path / "game.sqlite", select_scenario(key).layout)
    try:
        initial = session.update().view
        blocked = session.act("right")
        assert initial is not None and blocked.view is not None
        assert blocked.status == "COMMITTED"
        assert (
            blocked.view.actor_cell,
            blocked.view.actor_hp,
            blocked.view.enemy_hp,
            blocked.view.stamina,
            blocked.view.tick,
        ) == (initial.actor_cell, 3, 5, 2, 1)
        assert any("벽" in message for message in blocked.messages)
        session.save("slot01")
        waited = session.act("wait", seconds=3)
        assert waited.view is not None
        assert (waited.view.tick, waited.view.npc_bells, waited.view.charge) == (4, 2, 3)
        session.load("slot01")
        assert session.act("wait", seconds=3).view == waited.view
    finally:
        session.close()


def test_noncentral_door_uses_selected_geometry(tmp_path: Path) -> None:
    layout = replace(select_scenario("harbor").layout, gate_cell=3, enemy_cell=7)
    session = ClientSession(tmp_path / "game.sqlite", layout)
    try:
        assert session.act("open").status == "COMMITTED"
        assert session.act("down").status == "COMMITTED"
        assert session.act("right").status == "COMMITTED"
        attacked = session.act("attack")
        assert attacked.view is not None
        assert (
            attacked.view.actor_cell,
            attacked.view.gate_cell,
            attacked.view.enemy_hp,
            attacked.view.actor_hp,
        ) == (4, 3, 3, 2)
    finally:
        session.close()


@pytest.mark.parametrize("key,initial", (("harbor", "0"), ("grove", "6")))
def test_real_pipe_scenario(tmp_path: Path, key: str, initial: str) -> None:
    root = Path(__file__).resolve().parents[2]
    catalog = root / "content" / "narratives.json"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "app.engine_bridge",
            "--working",
            str(tmp_path / "game.sqlite"),
            "--catalog",
            str(catalog),
            "--catalog-sha256",
            hashlib.sha256(catalog.read_bytes()).hexdigest(),
            "--scenario",
            key,
        ],
        cwd=root / "src",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        pipe = PipeClient(process)
        update = pipe.latest["update"]
        assert object_value(update)["scenario_id"] == f"scenario:{key}"
        assert object_value(object_value(update)["view"])["actor_cell"] == initial
        response = pipe.send("bell")
        assert object_value(object_value(response["update"])["view"])["npc_replies"] == "1"
        pipe.send("quit")
        assert process.wait(timeout=10) == 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None:
                stream.close()
