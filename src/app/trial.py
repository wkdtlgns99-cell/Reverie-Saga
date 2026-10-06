from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import hashlib
import re
import sys

from app.headless import HeadlessSession, _restore, state_io
from app.trial_registry import trial_bundle
from contracts.errors import BootstrapError
from contracts.state_io import StateIO
from contracts.turn import ProtocolSnapshot, RngService, StreamCursor
from domain.canonical import canonical_json, pack
from domain.primitives import Tick, WorldRevision, require_integer
from domain.state_types import CoreSnapshot
from domain.trial import (
    ACTOR_ID, BLOCKED_CELLS, CELL_MM, HEIGHT, SPACE_ID, WIDTH,
    CellPositionRecord, TrialMapRecord,
)
from orchestration.rng import CounterRngService


@dataclass(frozen=True, slots=True)
class TrialBootstrapSpec:
    seed_hex: str
    branch_id: str
    stream_id: str
    initial_cell: int = 0
    initial_tick: Tick = Tick(0)
    initial_revision: WorldRevision = WorldRevision(0)


def _bootstrap(spec: TrialBootstrapSpec, rng: RngService | None) -> tuple[HeadlessSession, StateIO]:
    try:
        if (type(spec) is not TrialBootstrapSpec or
            type(spec.seed_hex) is not str or type(spec.branch_id) is not str or
            type(spec.stream_id) is not str or
            re.fullmatch("[0-9a-f]{64}", spec.seed_hex) is None or
            any(re.fullmatch("[0-9a-f]{32}", value) is None
                for value in (spec.branch_id, spec.stream_id))):
            raise ValueError("invalid bootstrap identifiers")
        require_integer(spec.initial_tick)
        require_integer(spec.initial_revision)
        require_integer(spec.initial_cell, 0, WIDTH * HEIGHT - 1)
        if spec.initial_cell in BLOCKED_CELLS:
            raise ValueError("initial actor occupies wall")
    except (ValueError, TypeError) as error:
        raise BootstrapError("INVALID_INITIAL_STATE", str(error)) from error
    bundles = (trial_bundle(),)
    io = state_io(bundles)
    world_id = "w1-" + hashlib.sha256(pack(("world-id/v1", spec.seed_hex,
                                          io.pins.rules_fingerprint,
                                          io.pins.gameplay_catalog_hash))).hexdigest()
    core = CoreSnapshot(world_id, spec.seed_hex, spec.initial_tick, (
        TrialMapRecord(SPACE_ID, WIDTH, HEIGHT, CELL_MM, BLOCKED_CELLS),
        CellPositionRecord(ACTOR_ID, SPACE_ID, spec.initial_cell),
    ), (), io.pins)
    protocol = ProtocolSnapshot(spec.branch_id, spec.initial_revision,
                                (StreamCursor(spec.stream_id, ACTOR_ID, 0, "active"),), ())
    session = _restore(core, protocol, bundles,
                       rng if rng is not None else CounterRngService(spec.seed_hex, world_id, ()),
                       io=io)
    return session, io


def bootstrap_trial(spec: TrialBootstrapSpec, *, rng: RngService | None = None) -> HeadlessSession:
    return _bootstrap(spec, rng)[0]


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv:
        raise ValueError("trial CLI accepts stdin commands only")
    session, io = _bootstrap(TrialBootstrapSpec("0" * 64, "0" * 32, "1" * 32), None)
    for line in sys.stdin.buffer:
        if not line.strip():
            continue
        publication = session.submit_json(line.rstrip(b"\r\n"))
        sys.stdout.buffer.write(canonical_json(io.encode_publication(publication)) + b"\n")
        sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
