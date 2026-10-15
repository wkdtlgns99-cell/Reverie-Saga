from __future__ import annotations

from domain.scenario import LEGACY_SCENARIO, Scenario, require_scenario

from collections.abc import Sequence
from dataclasses import dataclass, replace
import hashlib
import re
import sys

from app.headless import HeadlessSession, _restore, state_io
from app.watch_registry import watch_bundle
from contracts.events import QueuedEvent
from contracts.messages import EventHeader, WorldEvent
from contracts.watch import WatchWake
from domain.watch import WatchNpcRecord, LanternRecord, ReplyRecord
from contracts.errors import BootstrapError
from domain.encounter import GateRecord, HitPointsRecord, StaminaRecord
from contracts.state_io import StateIO
from contracts.turn import ProtocolSnapshot, RngService, StreamCursor
from domain.canonical import canonical_json, pack
from domain.primitives import EventId, Phase, Tick, WorldRevision, require_integer
from domain.state_types import CoreSnapshot
from domain.trial import (
    CELL_MM, HEIGHT, WIDTH,
    CellPositionRecord, TrialMapRecord,
)
from orchestration.rng import CounterRngService


@dataclass(frozen=True, slots=True)
class WatchBootstrapSpec:
    seed_hex: str
    branch_id: str
    stream_id: str
    initial_cell: int = 0
    gate_open: int = 0
    actor_hp: int = 3
    enemy_hp: int = 5
    stamina: int = 2


def _bootstrap(spec: WatchBootstrapSpec, rng: RngService | None, scenario: Scenario = LEGACY_SCENARIO) -> tuple[HeadlessSession, StateIO]:
    require_scenario(scenario)
    try:
        if (type(spec) is not WatchBootstrapSpec or
            type(spec.seed_hex) is not str or type(spec.branch_id) is not str or
            type(spec.stream_id) is not str or
            re.fullmatch("[0-9a-f]{64}", spec.seed_hex) is None or
            any(re.fullmatch("[0-9a-f]{32}", value) is None
                for value in (spec.branch_id, spec.stream_id))):
            raise ValueError("invalid bootstrap identifiers")
        require_integer(spec.initial_cell, 0, WIDTH * HEIGHT - 1)
        require_integer(spec.gate_open, 0, 1)
        require_integer(spec.actor_hp, 0, 3)
        require_integer(spec.enemy_hp, 0, 5)
        require_integer(spec.stamina, 0, 2)
        if (spec.initial_cell == scenario.gate_cell and spec.gate_open == 0 or
            spec.initial_cell == scenario.enemy_cell and spec.enemy_hp > 0):
            raise ValueError("occupied initial actor cell")
        if spec.initial_cell in scenario.blocked_cells:
            raise ValueError("initial actor occupies wall")
    except (ValueError, TypeError) as error:
        raise BootstrapError("INVALID_INITIAL_STATE", str(error)) from error
    bundles = (watch_bundle(scenario),)
    io = state_io(bundles)
    world_id = "w1-" + hashlib.sha256(pack(("world-id/v1", spec.seed_hex,
                                          io.pins.rules_fingerprint,
                                          io.pins.gameplay_catalog_hash))).hexdigest()
    identifier = EventId("e1-" + hashlib.sha256(pack(("event-id/v1", world_id, "0", "PRE_TICK", "0", "watch.npc", "0"))).hexdigest())
    genesis = WorldEvent(EventHeader(identifier, WatchWake(scenario.npc_id).schema, "watch.npc", Tick(0), Phase.PRE_TICK, 0, 0, 0, (), ()), Tick(2), WatchWake(scenario.npc_id))
    pending = io.encode_pending(QueuedEvent(genesis, Phase.PRE_TICK, 10))
    core = CoreSnapshot(world_id, spec.seed_hex, Tick(0), (
        GateRecord(scenario.gate_id, scenario.space_id, scenario.gate_cell, spec.gate_open),
        HitPointsRecord(scenario.enemy_id, spec.enemy_hp),
        HitPointsRecord(scenario.actor_id, spec.actor_hp),
        StaminaRecord(scenario.actor_id, spec.stamina),
        TrialMapRecord(scenario.space_id, WIDTH, HEIGHT, CELL_MM, scenario.blocked_cells),
        CellPositionRecord(scenario.enemy_id, scenario.space_id, scenario.enemy_cell),
        CellPositionRecord(scenario.actor_id, scenario.space_id, spec.initial_cell),
        LanternRecord(scenario.lantern_id, 0),
        WatchNpcRecord(scenario.npc_id, scenario.space_id, scenario.npc_cell, 0),
        ReplyRecord(scenario.npc_id, 0),
    ), (pending,), io.pins)
    protocol = ProtocolSnapshot(spec.branch_id, WorldRevision(0),
                                (StreamCursor(spec.stream_id, scenario.actor_id, 0, "active"),), ())
    core = replace(core, components=tuple(sorted(
        core.components, key=lambda record: (record.schema.kind, record.schema.version, record.entity_id)
    )))
    session = _restore(core, protocol, bundles,
                       rng if rng is not None else CounterRngService(spec.seed_hex, world_id, ()),
                       io=io)
    return session, io


def bootstrap_watch(spec: WatchBootstrapSpec, *, rng: RngService | None = None, scenario: Scenario = LEGACY_SCENARIO) -> HeadlessSession:
    return _bootstrap(spec, rng, scenario)[0]


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv:
        raise ValueError("watch CLI accepts stdin commands only")
    session, io = _bootstrap(WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32), None)
    for line in sys.stdin.buffer:
        if not line.strip():
            continue
        publication = session.submit_json(line.rstrip(b"\r\n"))
        sys.stdout.buffer.write(canonical_json(io.encode_publication(publication)) + b"\n")
        sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
