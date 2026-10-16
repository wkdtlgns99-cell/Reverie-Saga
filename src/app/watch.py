from __future__ import annotations

from domain.scenario import resolve_selection, LEGACY, Scenario

from collections.abc import Sequence
from dataclasses import dataclass
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
from contracts.skeleton import FeatureBundle
from domain.state_types import ComponentRecord
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


def _bootstrap(spec: WatchBootstrapSpec, rng: RngService | None, layout: Scenario = LEGACY,
               *, bundle: FeatureBundle | None = None,
               extra_records: tuple[ComponentRecord, ...] = ()) -> tuple[HeadlessSession, StateIO]:
    try:
        if type(layout) is not Scenario:
            raise ValueError("SCENARIO_TYPE")
        if (type(spec) is not WatchBootstrapSpec or
            type(spec.seed_hex) is not str or type(spec.branch_id) is not str or
            type(spec.stream_id) is not str or
            re.fullmatch("[0-9a-f]{64}", spec.seed_hex) is None or
            any(re.fullmatch("[0-9a-f]{32}", value) is None
                for value in (spec.branch_id, spec.stream_id))):
            raise ValueError("invalid bootstrap identifiers")
        require_integer(spec.initial_cell, 0, WIDTH * HEIGHT - 1)
        if layout != LEGACY and spec.initial_cell != layout.initial_cell:
            raise ValueError("SCENARIO_INITIAL_CELL")
        require_integer(spec.gate_open, 0, 1)
        require_integer(spec.actor_hp, 0, 3)
        require_integer(spec.enemy_hp, 0, 5)
        require_integer(spec.stamina, 0, 2)
        if (spec.initial_cell == layout.gate_cell and spec.gate_open == 0 or
            spec.initial_cell == layout.enemy_cell and spec.enemy_hp > 0):
            raise ValueError("occupied initial actor cell")
        if spec.initial_cell in layout.blocked_cells:
            raise ValueError("initial actor occupies wall")
    except (ValueError, TypeError) as error:
        raise BootstrapError("INVALID_INITIAL_STATE", str(error)) from error
    bundles = (watch_bundle(layout) if bundle is None else bundle,)
    io = state_io(bundles)
    world_id = "w1-" + hashlib.sha256(pack(("world-id/v1", spec.seed_hex,
                                          io.pins.rules_fingerprint,
                                          io.pins.gameplay_catalog_hash))).hexdigest()
    identifier = EventId("e1-" + hashlib.sha256(pack(("event-id/v1", world_id, "0", "PRE_TICK", "0", "watch.npc", "0"))).hexdigest())
    genesis = WorldEvent(EventHeader(identifier, WatchWake(layout.npc_id).schema, "watch.npc", Tick(0), Phase.PRE_TICK, 0, 0, 0, (), ()), Tick(2), WatchWake(layout.npc_id))
    pending = io.encode_pending(QueuedEvent(genesis, Phase.PRE_TICK, 10))
    core = CoreSnapshot(world_id, spec.seed_hex, Tick(0), tuple(sorted((
        GateRecord(layout.gate_id, layout.space_id, layout.gate_cell, spec.gate_open),
        HitPointsRecord(layout.enemy_id, spec.enemy_hp),
        HitPointsRecord(layout.actor_id, spec.actor_hp),
        StaminaRecord(layout.actor_id, spec.stamina),
        TrialMapRecord(layout.space_id, WIDTH, HEIGHT, CELL_MM, layout.blocked_cells),
        CellPositionRecord(layout.enemy_id, layout.space_id, layout.enemy_cell),
        CellPositionRecord(layout.actor_id, layout.space_id, spec.initial_cell),
        LanternRecord(layout.lantern_id, 0),
        WatchNpcRecord(layout.npc_id, layout.space_id, layout.npc_cell, 0),
        ReplyRecord(layout.npc_id, 0),
        *extra_records,
    ), key=lambda c: (c.schema.kind, c.schema.version, c.entity_id))), (pending,), io.pins)
    protocol = ProtocolSnapshot(spec.branch_id, WorldRevision(0),
                                (StreamCursor(spec.stream_id, layout.actor_id, 0, "active"),), ())
    session = _restore(core, protocol, bundles,
                       rng if rng is not None else CounterRngService(spec.seed_hex, world_id, ()),
                       io=io)
    return session, io


def bootstrap_watch(spec: WatchBootstrapSpec, *, rng: RngService | None = None, layout: Scenario = LEGACY, scenario: Scenario = LEGACY) -> HeadlessSession:
    return _bootstrap(spec, rng, resolve_selection(layout, scenario))[0]


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
