from __future__ import annotations

from dataclasses import replace
from functools import cache
import hashlib
import json
from pathlib import Path
from typing import cast
from app.watch import WatchBootstrapSpec, bootstrap_watch
from app.watch_registry import watch_bundle
from app.headless import HeadlessSession, restore_checkpoint, state_io
from contracts.events import QueuedEvent
from contracts.messages import CommandPayload, EventHeader, WorldEvent
from contracts.read_views import ViewEpoch
from contracts.skeleton import FeatureBundle
from contracts.turn import GameCommand
from contracts.watch import WaitCommand, WatchWake
from domain.canonical import JsonValue, pack, seal
from domain.primitives import CommandId, EventId, Phase, Tick, WorldRevision
from domain.state_types import StoredRoot
from domain.trial import ACTOR_ID
from domain.watch import NPC_ID
from orchestration.read_views import ObservedReadViewFactory

ROOT = Path(__file__).resolve().parents[2]


@cache
def reference(name: str) -> JsonValue:
    raw = cast(dict[str, object], json.loads((ROOT / "docs/work_orders/RS-P1-CORE_04_REFERENCE_VECTORS.json").read_bytes()))
    return seal(raw[name])


def fixture_body(passive: bool = False) -> bytes:
    return (ROOT / "tests/replay/fixtures" / ("watch_passive_v1.json" if passive else "watch_v1.json")).read_bytes()


def session(selected: FeatureBundle | None = None, *, actor_hp: int = 3, cell: int = 0) -> HeadlessSession:
    owner = bootstrap_watch(WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32, initial_cell=cell, actor_hp=actor_hp))
    if selected is None:
        return owner
    io = state_io((selected,))
    world = "w1-" + hashlib.sha256(pack(("world-id/v1", "0" * 64, io.pins.rules_fingerprint, io.pins.gameplay_catalog_hash))).hexdigest()
    identifier = EventId("e1-" + hashlib.sha256(pack(("event-id/v1", world, "0", "PRE_TICK", "0", "watch.npc", "0"))).hexdigest())
    event = WorldEvent(EventHeader(identifier, WatchWake(NPC_ID).schema, "watch.npc", Tick(0), Phase.PRE_TICK, 0, 0, 0, (), ()), Tick(2), WatchWake(NPC_ID))
    core = replace(owner.snapshot(), pins=io.pins, world_id=world, pending=(io.encode_pending(QueuedEvent(event, Phase.PRE_TICK, 10)),))
    return restore_checkpoint(core, owner.protocol(), bundles=(selected,))


def command(payload: CommandPayload | None = None, *, sequence: int = 1, revision: int = 0) -> GameCommand:
    return GameCommand(CommandId("c1:" + "0" * 32 + ":" + "1" * 32 + ":" + str(sequence)), ACTOR_ID, WorldRevision(revision), WaitCommand(1) if payload is None else payload)


def views(phase: Phase = Phase.RESOLVE, wave: int = 0, tick: int = 0) -> tuple[ObservedReadViewFactory, ViewEpoch]:
    factory = ObservedReadViewFactory(StoredRoot(session().snapshot().components, 1))
    for adapter in watch_bundle().read_adapters:
        adapter.install(factory)
    return factory, ViewEpoch(Tick(tick), phase, wave, "watch.bell", 1)
