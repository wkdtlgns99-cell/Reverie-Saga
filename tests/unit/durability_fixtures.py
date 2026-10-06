from __future__ import annotations

from dataclasses import dataclass, replace
from functools import cache
import hashlib
import json
from pathlib import Path
import struct
from typing import cast

from app.headless import state_io
from app.watch_registry import watch_bundle
from contracts.persistence import DurableCheckpoint, DurableTurn
from contracts.state_io import StateIO
from contracts.turn import GameCommand
from domain.canonical import JsonObject, decode_json, object_value
from orchestration.persistence import RowProjection
from tests.unit.watch_fixtures import command, reference, session

ROOT = Path(__file__).resolve().parents[2]


def io() -> StateIO:
    return state_io((watch_bundle(),))


def checkpoint() -> DurableCheckpoint:
    owner = session()
    return DurableCheckpoint(owner.snapshot(), owner.protocol())


def turn(request: GameCommand | None = None) -> DurableTurn:
    owner = session()
    previous = DurableCheckpoint(owner.snapshot(), owner.protocol())
    selected = command() if request is None else request
    owner.driver.submit(selected)
    return DurableTurn(previous, DurableCheckpoint(owner.snapshot(), owner.protocol()), selected,
                       replace(owner.last_publication(), cues=()))


def vectors(passive: bool = False) -> JsonObject:
    name = "durable_watch_passive_v1.json" if passive else "durable_watch_v1.json"
    return object_value(decode_json((ROOT / "tests/replay/fixtures" / name).read_bytes()))


def requirements(passive: bool = False) -> JsonObject:
    return object_value(reference("passive_fixture" if passive else "expected_fixture"))


def projection_document(rows: RowProjection) -> JsonObject:
    return {"core_meta_hex": rows.core_meta.hex(), "protocol_meta_hex": rows.protocol_meta.hex(),
            "core_hash": rows.core_hash, "protocol_hash": rows.protocol_hash,
            "components": tuple({"kind": c.kind, "version": c.version, "entity_id": c.entity_id,
                                  "body_hex": c.body.hex(), "sha256": c.sha256} for c in rows.components),
            "pending": tuple({"event_id": q.event_id, "ordinal": q.ordinal, "body_hex": q.body.hex(),
                               "sha256": q.sha256} for q in rows.pending),
            "streams": tuple({"stream_id": s.stream_id, "body_hex": s.body.hex()} for s in rows.streams),
            "receipts": tuple({"command_id": r.command_id, "revision": r.revision, "body_hex": r.body.hex()} for r in rows.receipts)}


type Plain = None | bool | int | str | list[Plain] | dict[str, Plain]


def _plain_dict(value: Plain) -> dict[str, Plain]:
    assert isinstance(value, dict)
    return value


def _canonical(value: Plain) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _pack(parts: tuple[str, ...]) -> bytes:
    return b"".join(struct.pack(">I", len(v.encode("utf-8"))) + v.encode("utf-8") for v in parts)


def independent_hash(tag: str, body: bytes) -> str:
    return hashlib.sha256(_pack((tag, body.decode("utf-8")))).hexdigest()


@dataclass(frozen=True, slots=True)
class ToySegmentInput:
    initial: DurableCheckpoint
    current: DurableCheckpoint
    bodies: tuple[bytes, ...]


@cache
def toy_segment_input(count: int, start: int = 0, *, with_segment: bool = True) -> ToySegmentInput:
    """Independent Phase0 requirements: Step0 keeps x0, adds one visit/second.

    Derive full protocol retention, zero-step record fact and net counter delta using
    only stdlib framing/JSON. Registered decoding validates these INPUTS afterward;
    no Driver, Recorder or production serializer generates the expected rows/hashes.
    """
    from app.feature_registry import feature_bundles
    from domain.primitives import EntityId
    from orchestration.persistence import decode_checkpoint
    f = cast(dict[str, Plain], json.loads((ROOT / "tests/replay/fixtures/skeleton_v1.json").read_bytes()))
    base = _plain_dict(f["initial_core"])
    base_protocol = _plain_dict(f["initial_protocol"])
    base_header = _plain_dict(_plain_dict(f["trace"])["header"])
    world = str(base["world_id"])
    selected = state_io(feature_bundles(EntityId("actor:toy")))
    receipts: list[Plain] = []
    bodies: list[bytes] = []

    def documents(n: int) -> tuple[dict[str, Plain], dict[str, Plain], str]:
        components: list[Plain] = [
            {"entity_id": "actor:toy", "schema": {"kind": "skeleton.counter", "version": 1}, "fields": {"visits": n}},
            {"entity_id": "actor:toy", "schema": {"kind": "skeleton.position", "version": 1}, "fields": {"x": 0}},
        ]
        core: dict[str, Plain] = {**base, "tick": n, "components": components, "pending": []}
        leaves: list[Plain] = [{"entity_id": _plain_dict(c)["entity_id"], "schema": _plain_dict(c)["schema"],
                               "hash": independent_hash("component/v1", _canonical(c))} for c in components]
        core_hash = independent_hash("core-root/v1", _canonical({**core, "components": leaves}))
        protocol: dict[str, Plain] = {**base_protocol, "revision": n, "receipts": receipts.copy(),
                                     "streams": [{"stream_id": "1" * 32, "actor_id": "actor:toy", "status": "active", "highest_committed_sequence": n}]}
        return core, protocol, core_hash

    def typed(n: int) -> DurableCheckpoint:
        core, protocol, ch = documents(n)
        header: dict[str, Plain] = {**base_header, "initial_core_hash": ch,
                                    "initial_protocol_hash": independent_hash("protocol/v1", _canonical(protocol))}
        document = object_value(decode_json(_canonical({"core": core, "protocol": protocol, "header": header})))
        return decode_checkpoint(document, io=selected)

    initial = typed(0)
    for n in range(1, count + 1):
        _, _, ch = documents(n)
        cmd: dict[str, Plain] = {"command_id": "c1:" + "0" * 32 + ":" + "1" * 32 + ":" + str(n),
                                 "actor_id": "actor:toy", "expected_revision": n - 1,
                                 "schema": {"kind": "skeleton.step", "version": 1}, "payload": {"dx": 0}}
        receipt: dict[str, Plain] = {"command_id": cmd["command_id"], "previous_revision": n - 1,
                                     "revision": n, "tick": n, "core_hash": ch}
        fingerprint = independent_hash("command/v1", _canonical({k: v for k, v in cmd.items() if k != "command_id"}))
        receipts.append({"command": cmd, "command_fingerprint": fingerprint, "receipt": receipt})
        receipts = receipts[-1024:]
        if n == start:
            initial = typed(n)
        if with_segment and n > start:
            _, protocol, _ = documents(n)
            identifier = "e1-" + hashlib.sha256(_pack(("event-id/v1", world, str(n), "RESOLVE", "0", "skeleton.stepper", "0"))).hexdigest()
            facts: list[Plain] = [{"due_tick": n, "header": {"event_id": identifier, "type_key": {"kind": "skeleton.stepped", "version": 1},
                                                            "producer_id": "skeleton.stepper", "occurred_at": n, "phase": "RESOLVE", "wave": 0,
                                                            "producer_rank": 0, "sequence": 0, "caused_by": [], "degraded": []},
                                    "payload": {"from_x": 0, "to_x": 0}}]
            diff: dict[str, Plain] = {"receipt": receipt, "changes": [{"schema": {"kind": "skeleton.counter-delta", "version": 1},
                                                                      "entity_id": "actor:toy", "expected_old": n - 1, "new": n}]}
            bodies.append(_canonical({"command": cmd, "outcome": {"kind": "committed", "receipt": receipt},
                                      "core_hash": ch, "protocol_hash": independent_hash("protocol/v1", _canonical(protocol)),
                                      "facts_hash": independent_hash("turn-facts/v1", _canonical(facts)),
                                      "diff_hash": independent_hash("turn-diff/v1", _canonical(diff))}))
    return ToySegmentInput(initial, typed(count), tuple(bodies))
