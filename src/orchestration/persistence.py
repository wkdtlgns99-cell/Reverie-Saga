from __future__ import annotations

from dataclasses import dataclass, replace
import re

from contracts.errors import CandidateError, ReadViewError, SchemaError
from contracts.persistence import DurableCheckpoint, DurableTurn, SaveError, SaveSegment
from contracts.replay import PackagePin, ReplayHeader, ReplayStep, ReplayTrace
from contracts.state_io import StateIO
from contracts.turn import CommitReceipt, StoredReceipt, TurnCommitted
from domain.canonical import (
    JsonObject, array_value, canonical_json, decode_json, exact_fields, hash_document,
    int_value, object_value, text_value,
)
from orchestration.replay import _header, _header_document, _initial


@dataclass(frozen=True, slots=True)
class ComponentRow:
    kind: str
    version: int
    entity_id: str
    body: bytes
    sha256: str

    @property
    def key(self) -> tuple[str, int, str]:
        return self.kind, self.version, self.entity_id


@dataclass(frozen=True, slots=True)
class PendingRow:
    event_id: str
    ordinal: int
    body: bytes
    sha256: str


@dataclass(frozen=True, slots=True)
class StreamRow:
    stream_id: str
    body: bytes


@dataclass(frozen=True, slots=True)
class ReceiptRow:
    command_id: str
    revision: int
    body: bytes


@dataclass(frozen=True, slots=True)
class RowProjection:
    core_meta: bytes
    protocol_meta: bytes
    core_hash: str
    protocol_hash: str
    components: tuple[ComponentRow, ...]
    pending: tuple[PendingRow, ...]
    streams: tuple[StreamRow, ...]
    receipts: tuple[ReceiptRow, ...]


@dataclass(frozen=True, slots=True)
class SaveRowPlan:
    previous: RowProjection
    next: RowProjection
    components_upserts: tuple[ComponentRow, ...]
    components_deletes: tuple[tuple[str, int, str], ...]
    pending_upserts: tuple[PendingRow, ...]
    pending_deletes: tuple[str, ...]
    streams_upserts: tuple[StreamRow, ...]
    receipts_upserts: tuple[ReceiptRow, ...]
    receipts_deletes: tuple[str, ...]
    step_body: bytes
    step_sha256: str
    receipt: CommitReceipt


def canonical_object(body: bytes) -> JsonObject:
    try:
        document = object_value(decode_json(body))
        if canonical_json(document) != body:
            raise ValueError("noncanonical save body")
        return document
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        raise SaveError("SAVE_CORRUPT", str(error)) from error


def replay_header(checkpoint: DurableCheckpoint, *, io: StateIO) -> ReplayHeader:
    core, protocol = checkpoint.core, checkpoint.protocol
    p = core.pins
    if p.gameplay_packages:
        raise SaveError("SAVE_PACKAGE_UNAVAILABLE", "accepted package blobs unsupported")
    return ReplayHeader(core.world_id, core.world_seed_hex, io.hash_core(core),
                        hash_document("protocol/v1", io.encode_protocol(protocol)),
                        p.schema_fingerprint, p.rules_fingerprint, p.schedule_fingerprint,
                        p.rng_version, p.hash_version,
                        tuple(PackagePin(a.package_id, a.version, a.sha256)
                              for a in p.gameplay_packages), ())


def checkpoint_document(checkpoint: DurableCheckpoint, *, io: StateIO) -> JsonObject:
    try:
        io.validate_checkpoint(checkpoint.core, checkpoint.protocol)
        return {"core": io.encode_core(checkpoint.core),
                "protocol": io.encode_protocol(checkpoint.protocol),
                "header": _header_document(replay_header(checkpoint, io=io))}
    except (ValueError, TypeError, CandidateError, ReadViewError) as error:
        raise SaveError("SAVE_CORRUPT", str(error)) from error


def decode_checkpoint(document: JsonObject, *, io: StateIO) -> DurableCheckpoint:
    try:
        d = exact_fields(document, ("core", "protocol", "header"))
        c = object_value(d["core"])
        pins = object_value(c["pins"])
        header = _header(d["header"])
        if array_value(pins["gameplay_packages"]) or header.gameplay_packages or header.build_artifacts:
            raise SaveError("SAVE_PACKAGE_UNAVAILABLE", "accepted packages unsupported")
        p = io.pins
        expected: JsonObject = {
            "schema_fingerprint": p.schema_fingerprint,
            "rules_fingerprint": p.rules_fingerprint,
            "schedule_fingerprint": p.schedule_fingerprint,
            "rng_version": p.rng_version, "hash_version": p.hash_version,
            "gameplay_catalog_hash": p.gameplay_catalog_hash, "gameplay_packages": (),
        }
        if canonical_json(pins) != canonical_json(expected):
            raise SaveError("UNSUPPORTED_RULESET", "selected save pins differ")
        core = io.decode_core(c)
        protocol = io.decode_protocol(object_value(d["protocol"]), core)
        _initial(header, core, protocol, io)
        io.validate_checkpoint(core, protocol)
        return DurableCheckpoint(core, protocol)
    except (ValueError, TypeError, KeyError, CandidateError, ReadViewError) as error:
        code = "UNSUPPORTED_RULESET" if isinstance(error, SchemaError) and error.code == "UNSUPPORTED_SCHEMA" else "SAVE_CORRUPT"
        raise SaveError(code, str(error)) from error


def project_rows(checkpoint: DurableCheckpoint, *, io: StateIO) -> RowProjection:
    io.validate_checkpoint(checkpoint.core, checkpoint.protocol)
    if checkpoint.core.pins.gameplay_packages:
        raise SaveError("SAVE_PACKAGE_UNAVAILABLE", "accepted packages unsupported")
    core, protocol = io.encode_core(checkpoint.core), io.encode_protocol(checkpoint.protocol)
    components: list[ComponentRow] = []
    for value in array_value(core["components"]):
        child = object_value(value)
        schema = object_value(child["schema"])
        components.append(ComponentRow(text_value(schema["kind"]), int_value(schema["version"]),
                                       text_value(child["entity_id"]), canonical_json(child),
                                       hash_document("component/v1", child)))
    pending: list[PendingRow] = []
    for index, value in enumerate(array_value(core["pending"])):
        child = object_value(value)
        header = object_value(object_value(child["event"])["header"])
        pending.append(PendingRow(text_value(header["event_id"]), index, canonical_json(child),
                                  hash_document("pending-event/v1", child)))
    streams = tuple(StreamRow(text_value(object_value(s)["stream_id"]), canonical_json(s))
                    for s in array_value(protocol["streams"]))
    receipts = tuple(ReceiptRow(text_value(object_value(object_value(r)["command"])["command_id"]),
                               int_value(object_value(object_value(r)["receipt"])["revision"]),
                               canonical_json(r)) for r in array_value(protocol["receipts"]))
    return RowProjection(canonical_json({k: v for k, v in core.items() if k not in ("components", "pending")}),
                         canonical_json({k: v for k, v in protocol.items() if k not in ("streams", "receipts")}),
                         io.hash_core(checkpoint.core), hash_document("protocol/v1", protocol),
                         tuple(components), tuple(pending), streams, receipts)


def prepare_turn(turn: DurableTurn, *, io: StateIO) -> SaveRowPlan:
    try:
        previous, next_head = turn.previous, turn.next
        before, after = previous.core, next_head.core
        old, new = previous.protocol, next_head.protocol
        outcome = turn.publication.outcome
        if not isinstance(outcome, TurnCommitted) or turn.publication.cues:
            raise ValueError("only new prepared commits can persist")
        receipt = outcome.receipt
        if (before.world_id, before.world_seed_hex, before.pins, old.branch_id) != (
            after.world_id, after.world_seed_hex, after.pins, new.branch_id
        ) or new.revision != old.revision + 1 or after.tick <= before.tick:
            raise ValueError("durable transition identity/revision/time")
        if receipt.previous_revision != old.revision or receipt.revision != new.revision or receipt.command_id != turn.command.command_id:
            raise ValueError("durable receipt transition")
        parts = turn.command.command_id.split(":")
        stream_id, sequence = parts[2], int(parts[3])
        document = io.encode_command(turn.command)
        fingerprint = hash_document("command/v1", {k: v for k, v in document.items() if k != "command_id"})
        expected_streams = tuple(replace(s, highest_committed_sequence=sequence)
                                 if s.stream_id == stream_id else s for s in old.streams)
        cursor = next(s for s in old.streams if s.stream_id == stream_id)
        if sequence <= cursor.highest_committed_sequence or cursor.status != "active" or turn.command.expected_revision != old.revision:
            raise ValueError("not a newly admitted sequence")
        expected_receipts = (*old.receipts, StoredReceipt(turn.command, fingerprint, receipt))[-1024:]
        if new.streams != expected_streams or new.receipts != expected_receipts:
            raise ValueError("protocol high-water/retention transition")
        left, right = project_rows(previous, io=io), project_rows(next_head, io=io)
        publication = io.encode_publication(turn.publication)
        io.validate_effects(turn.command, outcome, after, new, publication["facts"], publication["diff"])
        step: JsonObject = {"command": document, "outcome": publication["outcome"],
                            "core_hash": right.core_hash, "protocol_hash": right.protocol_hash,
                            "facts_hash": hash_document("turn-facts/v1", publication["facts"]),
                            "diff_hash": hash_document("turn-diff/v1", publication["diff"])}
        lc, rc = {c.key: c for c in left.components}, {c.key: c for c in right.components}
        lp, rp = {q.event_id: q for q in left.pending}, {q.event_id: q for q in right.pending}
        ls = {s.stream_id: s for s in left.streams}
        lr, rr = {r.command_id: r for r in left.receipts}, {r.command_id: r for r in right.receipts}
        return SaveRowPlan(left, right,
                           tuple(rc[k] for k in sorted(rc) if lc.get(k) != rc[k]),
                           tuple(sorted(lc.keys() - rc.keys())),
                           tuple(rp[k] for k in sorted(rp) if lp.get(k) != rp[k]),
                           tuple(sorted(lp.keys() - rp.keys())),
                           tuple(s for s in right.streams if ls.get(s.stream_id) != s),
                           tuple(rr[k] for k in sorted(rr) if lr.get(k) != rr[k]),
                           tuple(sorted(lr.keys() - rr.keys())), canonical_json(step),
                           hash_document("save-step/v1", step), receipt)
    except (ValueError, TypeError, KeyError, IndexError, StopIteration, CandidateError, ReadViewError) as error:
        raise SaveError("SAVE_CORRUPT", str(error)) from error


def decode_segment(checkpoint: DurableCheckpoint, bodies: tuple[bytes, ...], *, io: StateIO) -> SaveSegment:
    try:
        header = replay_header(checkpoint, io=io)
        if len(bodies) > 4096:
            raise ValueError("replay segment cap")
        steps: list[ReplayStep] = []
        tick = checkpoint.core.tick
        for index, body in enumerate(bodies):
            d = exact_fields(canonical_object(body), ("command", "outcome", "core_hash", "protocol_hash", "facts_hash", "diff_hash"))
            command = io.decode_command(object_value(d["command"]))
            outcome = io.decode_outcome(object_value(d["outcome"]))
            revision = checkpoint.protocol.revision + index + 1
            if not isinstance(outcome, TurnCommitted):
                raise ValueError("noncommitted retained step")
            receipt = outcome.receipt
            if (receipt.revision != revision or receipt.previous_revision != revision - 1 or
                command.expected_revision != revision - 1 or receipt.command_id != command.command_id or
                command.command_id.split(":")[1] != checkpoint.protocol.branch_id or
                receipt.core_hash != d["core_hash"] or receipt.tick <= tick):
                raise ValueError("replay receipt/branch/revision/tick chain")
            digests = tuple(text_value(d[k]) for k in ("core_hash", "protocol_hash", "facts_hash", "diff_hash"))
            if any(re.fullmatch("[0-9a-f]{64}", h) is None for h in digests):
                raise ValueError("invalid retained step digest")
            tick = receipt.tick
            steps.append(ReplayStep(command, outcome, digests[0], digests[1], digests[2], digests[3], None))
        return SaveSegment(checkpoint, ReplayTrace(header, tuple(steps)))
    except (ValueError, TypeError, KeyError, CandidateError, ReadViewError) as error:
        raise SaveError("SAVE_CORRUPT", str(error)) from error
