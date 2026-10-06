from __future__ import annotations

from functools import cache
import json
from pathlib import Path
from typing import cast

from app.encounter import EncounterBootstrapSpec, bootstrap_encounter
from app.encounter_registry import encounter_bundle
from app.headless import HeadlessSession, restore_checkpoint
from contracts.encounter import RestCommand
from contracts.messages import CommandPayload
from contracts.read_views import ViewEpoch
from contracts.skeleton import FeatureBundle
from contracts.turn import GameCommand
from domain.canonical import JsonObject, JsonValue, int_value, seal
from domain.primitives import CommandId, Phase, Tick, WorldRevision
from domain.state_types import StoredRoot
from domain.trial import ACTOR_ID
from orchestration.read_views import ObservedReadViewFactory

ROOT = Path(__file__).resolve().parents[2]


@cache
def reference(name: str) -> JsonValue:
    # Authoring metadata contains timings; seal only the requested domain section.
    raw = cast(dict[str, object], json.loads(
        (ROOT / "docs/work_orders/RS-P1-CORE_03_REFERENCE_VECTORS.json").read_bytes()))
    return seal(raw[name])


def session(selected: FeatureBundle | None = None, *, cell: int = 0, gate: int = 0,
            actor_hp: int = 3, enemy_hp: int = 5, stamina: int = 2,
            tick: int = 0, revision: int = 0) -> HeadlessSession:
    owner = bootstrap_encounter(EncounterBootstrapSpec("0" * 64, "0" * 32, "1" * 32,
                                                      cell, gate, actor_hp, enemy_hp,
                                                      stamina, Tick(tick), WorldRevision(revision)))
    return owner if selected is None else restore_checkpoint(
        owner.snapshot(), owner.protocol(), bundles=(selected,))


def vector_session(state: JsonObject) -> HeadlessSession:
    return session(cell=int_value(state["cell"]), gate=int_value(state["gate"]),
                   actor_hp=int_value(state["actor_hp"]), enemy_hp=int_value(state["enemy_hp"]),
                   stamina=int_value(state["stamina"]))


def command(payload: CommandPayload | None = None, *, sequence: int = 1,
            revision: int = 0) -> GameCommand:
    return GameCommand(CommandId("c1:" + "0" * 32 + ":" + "1" * 32 + ":" + str(sequence)),
                       ACTOR_ID, WorldRevision(revision),
                       RestCommand() if payload is None else payload)


def views(*, cell: int = 0, gate: int = 0, actor_hp: int = 3,
          enemy_hp: int = 5, stamina: int = 2) -> tuple[ObservedReadViewFactory, ViewEpoch]:
    selected = encounter_bundle()
    root = StoredRoot(session(cell=cell, gate=gate, actor_hp=actor_hp,
                              enemy_hp=enemy_hp, stamina=stamina).snapshot().components, 1)
    factory = ObservedReadViewFactory(root)
    for adapter in selected.read_adapters:
        adapter.install(factory)
    return factory, ViewEpoch(Tick(0), Phase.RESOLVE, 0, "encounter.actions", 1)


def fixture_body(death: bool = False) -> bytes:
    return (ROOT / "tests/replay/fixtures" /
            ("encounter_death_v1.json" if death else "encounter_v1.json")).read_bytes()
