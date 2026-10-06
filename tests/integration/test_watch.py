from __future__ import annotations

import os
import subprocess
import sys
import pytest
from app.headless import state_io, restore_checkpoint
from app.watch import WatchBootstrapSpec, bootstrap_watch, main
from app.watch_registry import watch_bundle
from contracts.errors import BootstrapError
from contracts.turn import TurnCommitted, TurnRejected
from contracts.watch import WaitCommand, BellCommand
from domain.canonical import JsonObject, array_value, canonical_json, int_value, object_value
from domain.primitives import EntityId
from domain.watch import NPC_ID
from tests.unit.watch_fixtures import ROOT, command, reference, session


@pytest.mark.parametrize("section,pubs,dead", (("expected_fixture", "expected_publications", False), ("passive_fixture", "passive_publications", False), ("dead_fixture", "dead_publications", True)))
def test_full_publications(section: str, pubs: str, dead: bool) -> None:
    live, io = session(actor_hp=0 if dead else 3), state_io((watch_bundle(),))
    data = object_value(reference(section))
    assert canonical_json(io.encode_core(live.snapshot())) == canonical_json(data["initial_core"])
    for step, expected in zip(array_value(object_value(data["trace"])["steps"]), array_value(reference(pubs)), strict=True):
        s = object_value(step)
        pub = live.submit_json(canonical_json(s["command"]))
        assert canonical_json(io.encode_publication(pub)) == canonical_json(expected)
        w = object_value(s["witness"])
        assert canonical_json(io.encode_core(live.snapshot())) == canonical_json(w["core"])
        assert canonical_json(io.encode_protocol(live.protocol())) == canonical_json(w["protocol"])


@pytest.mark.parametrize("vector", tuple(object_value(v) for v in array_value(reference("composition_vectors"))))
def test_passive_composition(vector: JsonObject) -> None:
    start, duration, split = (int_value(vector[k]) for k in ("start_tick", "duration", "split"))
    one, two = session(), session()
    io = state_io((watch_bundle(),))
    for owner in (one, two):
        if start:
            assert isinstance(owner.driver.submit(command(WaitCommand(start))), TurnCommitted)
    revision = 1 if start else 0
    assert isinstance(one.driver.submit(command(WaitCommand(duration), sequence=revision+1, revision=revision)), TurnCommitted)
    assert isinstance(two.driver.submit(command(WaitCommand(split), sequence=revision+1, revision=revision)), TurnCommitted)
    events = two.last_publication().facts
    assert isinstance(two.driver.submit(command(WaitCommand(duration-split), sequence=revision+2, revision=revision+1)), TurnCommitted)
    events += two.last_publication().facts
    assert one.snapshot() == two.snapshot()
    assert one.last_publication().facts == events
    assert io.hash_core(one.snapshot()) == vector["expected_core_hash"]
    assert tuple(e.header.event_id for e in events) == array_value(vector["event_ids"])
    assert object_value(io.encode_core(one.snapshot()))["pending"] == vector["pending"]
    assert one.protocol().revision + 1 == two.protocol().revision


@pytest.mark.parametrize("seconds", (0, -1, 17, True))
def test_wait_and_bell_no_time_errors(seconds: int) -> None:
    live = session()
    old = live.snapshot(), live.protocol()
    pub = live.submit_json(canonical_json({**state_io((watch_bundle(),)).encode_command(command()), "payload": {"seconds": seconds}}))
    assert isinstance(pub.outcome, TurnRejected)
    assert (live.snapshot(), live.protocol()) == old
    result = live.driver.submit(command(BellCommand(EntityId("actor:other"))))
    assert isinstance(result, TurnRejected) and result.failure.code == "INVALID_TARGET"
    assert (live.snapshot(), live.protocol()) == old
    assert isinstance(live.driver.submit(command(BellCommand(NPC_ID))), TurnCommitted)


def test_npc_before_action() -> None:
    live = session()
    live.driver.submit(command())
    live.driver.submit(command(BellCommand(NPC_ID), sequence=2, revision=1))
    facts = live.last_publication().facts
    assert tuple(f.payload.schema.kind for f in facts) == ("watch.npc-acted", "watch.wake", "watch.requested", "watch.bell-rung", "watch.echo", "watch.echo", "watch.replied")
    assert tuple(f.header.wave for f in facts[-2:]) == (0, 1)


def test_cli() -> None:
    data = object_value(reference("expected_fixture"))
    body = b"\n".join(canonical_json(object_value(s)["command"]) for s in array_value(object_value(data["trace"])["steps"])) + b"\n"
    result = subprocess.run([sys.executable, "-m", "app.watch"], input=body, cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT/"src")}, capture_output=True, check=True)
    assert result.stdout.splitlines() == [canonical_json(p) for p in array_value(reference("expected_publications"))]
    passive = object_value(reference("passive_fixture"))
    body = canonical_json(object_value(array_value(object_value(passive["trace"])["steps"])[0])["command"]) + b"\n"
    result = subprocess.run([sys.executable, "-m", "app.watch"], input=body, cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT/"src")}, capture_output=True, check=True)
    assert result.stdout.splitlines() == [canonical_json(p) for p in array_value(reference("passive_publications"))]
    with pytest.raises(ValueError):
        main(["--unsupported"])


def test_recorded_queue_restore() -> None:
    live = session()
    live.driver.submit(command(WaitCommand(5)))
    restored = restore_checkpoint(live.snapshot(), live.protocol(), bundles=(watch_bundle(),))
    cmd = command(WaitCommand(3), sequence=2, revision=1)
    live.driver.submit(cmd)
    restored.driver.submit(cmd)
    assert live.snapshot() == restored.snapshot() and live.last_publication() == restored.last_publication()


@pytest.mark.parametrize("spec", (WatchBootstrapSpec("f", "0"*32, "1"*32), WatchBootstrapSpec("0"*64, "0"*32, "1"*32, initial_cell=1), WatchBootstrapSpec("0"*64, "0"*32, "1"*32, actor_hp=4)))
def test_invalid_bootstrap(spec: WatchBootstrapSpec) -> None:
    with pytest.raises(BootstrapError):
        bootstrap_watch(spec)


def test_dead_actor() -> None:
    live = session(actor_hp=0)
    before = live.snapshot(), live.protocol()
    for payload in (WaitCommand(2), BellCommand(EntityId("actor:other"))):
        result = live.driver.submit(command(payload))
        assert isinstance(result, TurnRejected) and result.failure.code == "ACTOR_DEFEATED"
        assert (live.snapshot(), live.protocol()) == before
