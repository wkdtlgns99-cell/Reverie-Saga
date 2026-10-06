from __future__ import annotations

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
from domain.watch import NPC_ID, LANTERN_ID, NPC_CELL, WatchNpcRecord, LanternRecord, ReplyRecord
from contracts.errors import BootstrapError
from domain.encounter import ENEMY_ID, GATE_ID, GateRecord, HitPointsRecord, StaminaRecord
from contracts.state_io import StateIO
from contracts.turn import ProtocolSnapshot, RngService, StreamCursor
from domain.canonical import canonical_json, pack
from domain.primitives import EventId, Phase, Tick, WorldRevision, require_integer
from domain.state_types import CoreSnapshot
from domain.trial import (
    ACTOR_ID, BLOCKED_CELLS, CELL_MM, HEIGHT, SPACE_ID, WIDTH,
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


def _bootstrap(spec: WatchBootstrapSpec, rng: RngService | None) -> tuple[HeadlessSession, StateIO]:
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
        if (spec.initial_cell == 4 and spec.gate_open == 0 or
            spec.initial_cell == 8 and spec.enemy_hp > 0):
            raise ValueError("occupied initial actor cell")
        if spec.initial_cell in BLOCKED_CELLS:
            raise ValueError("initial actor occupies wall")
    except (ValueError, TypeError) as error:
        raise BootstrapError("INVALID_INITIAL_STATE", str(error)) from error
    bundles = (watch_bundle(),)
    io = state_io(bundles)
    world_id = "w1-" + hashlib.sha256(pack(("world-id/v1", spec.seed_hex,
                                          io.pins.rules_fingerprint,
                                          io.pins.gameplay_catalog_hash))).hexdigest()
    identifier = EventId("e1-" + hashlib.sha256(pack(("event-id/v1", world_id, "0", "PRE_TICK", "0", "watch.npc", "0"))).hexdigest())
    genesis = WorldEvent(EventHeader(identifier, WatchWake(NPC_ID).schema, "watch.npc", Tick(0), Phase.PRE_TICK, 0, 0, 0, (), ()), Tick(2), WatchWake(NPC_ID))
    pending = io.encode_pending(QueuedEvent(genesis, Phase.PRE_TICK, 10))
    core = CoreSnapshot(world_id, spec.seed_hex, Tick(0), (
        GateRecord(GATE_ID, SPACE_ID, 4, spec.gate_open),
        HitPointsRecord(ENEMY_ID, spec.enemy_hp),
        HitPointsRecord(ACTOR_ID, spec.actor_hp),
        StaminaRecord(ACTOR_ID, spec.stamina),
        TrialMapRecord(SPACE_ID, WIDTH, HEIGHT, CELL_MM, BLOCKED_CELLS),
        CellPositionRecord(ENEMY_ID, SPACE_ID, 8),
        CellPositionRecord(ACTOR_ID, SPACE_ID, spec.initial_cell),
        LanternRecord(LANTERN_ID, 0),
        WatchNpcRecord(NPC_ID, SPACE_ID, NPC_CELL, 0),
        ReplyRecord(NPC_ID, 0),
    ), (pending,), io.pins)
    protocol = ProtocolSnapshot(spec.branch_id, WorldRevision(0),
                                (StreamCursor(spec.stream_id, ACTOR_ID, 0, "active"),), ())
    session = _restore(core, protocol, bundles,
                       rng if rng is not None else CounterRngService(spec.seed_hex, world_id, ()),
                       io=io)
    return session, io


def bootstrap_watch(spec: WatchBootstrapSpec, *, rng: RngService | None = None) -> HeadlessSession:
    return _bootstrap(spec, rng)[0]


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
