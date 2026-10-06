from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from app.headless import HeadlessSession, restore_checkpoint, state_io
from app.trial import TrialBootstrapSpec, bootstrap_trial
from app.trial_registry import trial_bundle
from contracts.read_views import ViewEpoch
from contracts.skeleton import FeatureBundle
from contracts.trial import MoveCommand
from contracts.turn import GameCommand
from domain.canonical import JsonValue, seal
from domain.primitives import CommandId, Phase, Tick, WorldRevision
from domain.state_types import StoredRoot
from domain.trial import ACTOR_ID
from orchestration.read_views import ObservedReadViewFactory

ROOT = Path(__file__).resolve().parents[2]


def reference(name: str) -> JsonValue:
    # Authoring timings outside the requested section contain floats; seal only domain data.
    raw = cast(dict[str, object], json.loads(
        (ROOT / "docs/work_orders/RS-P1-CORE_02_REFERENCE_VECTORS.json").read_bytes()))
    return seal(raw[name])


def session(selected: FeatureBundle | None = None, *, cell: int = 0,
            tick: int = 0, revision: int = 0) -> HeadlessSession:
    owner = bootstrap_trial(TrialBootstrapSpec("0" * 64, "0" * 32, "1" * 32,
                                              cell, Tick(tick), WorldRevision(revision)))
    if selected is None:
        return owner
    return restore_checkpoint(owner.snapshot(), owner.protocol(), bundles=(selected,))


def command(sequence: int = 1, dx: int = 0, dz: int = 1, revision: int = 0) -> GameCommand:
    return GameCommand(CommandId("c1:" + "0" * 32 + ":" + "1" * 32 + ":" + str(sequence)),
                       ACTOR_ID, WorldRevision(revision), MoveCommand(dx, dz))


def views(cell: int = 0) -> tuple[ObservedReadViewFactory, ViewEpoch]:
    selected = trial_bundle()
    root = StoredRoot(session(cell=cell).snapshot().components, 1)
    factory = ObservedReadViewFactory(root)
    for adapter in selected.read_adapters:
        adapter.install(factory)
    return factory, ViewEpoch(Tick(0), Phase.RESOLVE, 0, "trial.movement", 1)


def fixture_body() -> bytes:
    return (ROOT / "tests/replay/fixtures/trial_v1.json").read_bytes()


def selected_io_pins() -> tuple[str, str, str]:
    pins = state_io((trial_bundle(),)).pins
    return pins.schema_fingerprint, pins.rules_fingerprint, pins.schedule_fingerprint
