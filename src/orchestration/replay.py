from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from contracts.errors import CandidateError, ReadViewError, ReplayFormatError
from contracts.replay import (
    PackagePin, ReplayFixture, ReplayHeader, ReplayMismatch, ReplaySessionFactory,
    ReplayStep, ReplayTrace, ReplayWitness,
)
from contracts.turn import (
    GameCommand, ProtocolSnapshot, TurnOutcome, TurnPublication,
)
from domain.canonical import (
    JsonObject, JsonValue, array_value, canonical_json, decode_json, exact_fields,
    hash_document, int_value, object_value, text_value,
)
from domain.state_types import (
    CoreSnapshot,
)
from contracts.state_io import StateIO
from orchestration.serialization import _hex, _packages



def _outcome_document(outcome: TurnOutcome, io: StateIO) -> JsonValue:
    return io.encode_publication(TurnPublication(outcome, (), None, (), ()))["outcome"]


def _header(value: JsonValue) -> ReplayHeader:
    d = exact_fields(value, ("world_id", "world_seed_hex", "initial_core_hash", "initial_protocol_hash",
                            "schema_fingerprint", "rules_fingerprint", "schedule_fingerprint", "rng_version",
                            "hash_version", "gameplay_packages", "build_artifacts"))
    return ReplayHeader(text_value(d["world_id"]), _hex(d["world_seed_hex"]), _hex(d["initial_core_hash"]),
                        _hex(d["initial_protocol_hash"]), _hex(d["schema_fingerprint"]), _hex(d["rules_fingerprint"]),
                        _hex(d["schedule_fingerprint"]), text_value(d["rng_version"]), text_value(d["hash_version"]),
                        _packages(d["gameplay_packages"]), _packages(d["build_artifacts"]))


def _header_document(header: ReplayHeader) -> JsonObject:
    return {"world_id": header.world_id, "world_seed_hex": header.world_seed_hex,
            "initial_core_hash": header.initial_core_hash, "initial_protocol_hash": header.initial_protocol_hash,
            "schema_fingerprint": header.schema_fingerprint, "rules_fingerprint": header.rules_fingerprint,
            "schedule_fingerprint": header.schedule_fingerprint, "rng_version": header.rng_version,
            "hash_version": header.hash_version,
            "gameplay_packages": tuple({"package_id": p.package_id, "version": p.version, "sha256": p.sha256} for p in header.gameplay_packages),
            "build_artifacts": tuple({"package_id": p.package_id, "version": p.version, "sha256": p.sha256} for p in header.build_artifacts)}


def _pins(header: ReplayHeader, core: CoreSnapshot) -> None:
    p = core.pins
    if (header.world_id, header.world_seed_hex, header.schema_fingerprint, header.rules_fingerprint,
        header.schedule_fingerprint, header.rng_version, header.hash_version, header.gameplay_packages) != (
        core.world_id, core.world_seed_hex, p.schema_fingerprint, p.rules_fingerprint,
        p.schedule_fingerprint, p.rng_version, p.hash_version,
        tuple(PackagePin(a.package_id, a.version, a.sha256) for a in p.gameplay_packages)):
        raise ValueError("replay header/checkpoint pins mismatch")
    if header.build_artifacts:
        raise ValueError("Phase0 has no build artifact pins")


def _initial(header: ReplayHeader, core: CoreSnapshot, protocol: ProtocolSnapshot, io: StateIO) -> None:
    _pins(header, core)
    if header.initial_core_hash != io.hash_core(core) or header.initial_protocol_hash != hash_document("protocol/v1", io.encode_protocol(protocol)):
        raise ValueError("initial checkpoint hash mismatch")


def _witness_document(witness: ReplayWitness) -> JsonObject:
    return {"core": decode_json(witness.canonical_core_json), "protocol": decode_json(witness.canonical_protocol_json),
            "facts": decode_json(witness.canonical_facts_json), "diff": decode_json(witness.canonical_diff_json)}


def _validate_witness(step: ReplayStep, header: ReplayHeader, io: StateIO) -> None:
    if step.expected_witness is None:
        return
    w = _witness_document(step.expected_witness)
    core = io.decode_core(object_value(w["core"]))
    protocol = io.decode_protocol(object_value(w["protocol"]), core)
    _pins(header, core)
    io.validate_checkpoint(core, protocol)
    hashes = (io.hash_core(core), hash_document("protocol/v1", w["protocol"]),
              hash_document("turn-facts/v1", w["facts"]), hash_document("turn-diff/v1", w["diff"]))
    if hashes != (step.expected_core_hash, step.expected_protocol_hash, step.expected_facts_hash, step.expected_diff_hash):
        raise ValueError("corrupt witness digest")
    io.validate_effects(step.command, step.expected_outcome, core, protocol, w["facts"], w["diff"])


def _step_document(step: ReplayStep, io: StateIO) -> JsonObject:
    return {"command": io.encode_command(step.command), "outcome": _outcome_document(step.expected_outcome, io),
            "core_hash": step.expected_core_hash, "protocol_hash": step.expected_protocol_hash,
            "facts_hash": step.expected_facts_hash, "diff_hash": step.expected_diff_hash,
            "witness": None if step.expected_witness is None else _witness_document(step.expected_witness)}


def decode_fixture(body: bytes, *, io: StateIO) -> ReplayFixture:
    try:
        d = exact_fields(decode_json(body), ("format_version", "initial_core", "initial_protocol", "trace"))
        if int_value(d["format_version"]) != 1:
            raise ValueError("unsupported fixture version")
        core = io.decode_core(object_value(d["initial_core"]))
        protocol = io.decode_protocol(object_value(d["initial_protocol"]), core)
        trace = exact_fields(d["trace"], ("header", "steps"))
        header = _header(trace["header"])
        _initial(header, core, protocol, io)
        io.validate_checkpoint(core, protocol)
        steps: list[ReplayStep] = []
        for item in array_value(trace["steps"]):
            s = exact_fields(item, ("command", "outcome", "core_hash", "protocol_hash", "facts_hash", "diff_hash", "witness"))
            w = exact_fields(s["witness"], ("core", "protocol", "facts", "diff"))
            witness = ReplayWitness(*(canonical_json(w[key]) for key in ("core", "protocol", "facts", "diff")))
            step = ReplayStep(io.decode_command(object_value(s["command"])), io.decode_outcome(object_value(s["outcome"])), _hex(s["core_hash"]),
                              _hex(s["protocol_hash"]), _hex(s["facts_hash"]), _hex(s["diff_hash"]), witness)
            _validate_witness(step, header, io)
            if object_value(w["protocol"])["branch_id"] != protocol.branch_id:
                raise ValueError("witness branch changed")
            steps.append(step)
            if len(steps) > 4096:
                raise ValueError("replay step cap")
        return ReplayFixture(core, protocol, ReplayTrace(header, tuple(steps)))
    except (CandidateError, ReadViewError, ValueError, TypeError, KeyError, OverflowError, RecursionError) as error:
        raise ReplayFormatError(str(error)) from error


def encode_fixture(fixture: ReplayFixture, *, io: StateIO) -> bytes:
    try:
        body = canonical_json({"format_version": 1, "initial_core": io.encode_core(fixture.initial_core),
                               "initial_protocol": io.encode_protocol(fixture.initial_protocol), "trace": {
                                   "header": _header_document(fixture.trace.header),
                                   "steps": tuple(_step_document(s, io) for s in fixture.trace.steps)}})
        decode_fixture(body, io=io)
        return body
    except (CandidateError, ReadViewError, ValueError, TypeError, KeyError) as error:
        raise ReplayFormatError(str(error)) from error


def validate_checkpoint(core: CoreSnapshot, protocol: ProtocolSnapshot, *, io: StateIO) -> None:
    try:
        io.validate_checkpoint(core, protocol)
    except (CandidateError, ReadViewError, ValueError, TypeError, KeyError) as error:
        raise ReplayFormatError(str(error)) from error


class Recorder:
    def __init__(self, header: ReplayHeader, *, io: StateIO) -> None:
        try:
            _header(_header_document(header))
        except (ValueError, TypeError) as error:
            raise ReplayFormatError(str(error)) from error
        self._io = io
        self._header = header
        self._steps: list[ReplayStep] = []

    def record(self, command: GameCommand, publication: TurnPublication,
               core: CoreSnapshot, protocol: ProtocolSnapshot) -> ReplayStep:
        if len(self._steps) >= 4096:
            raise ReplayFormatError("replay step cap")
        io = self._io
        try:
            io.decode_command(io.encode_command(command))
            document = io.encode_publication(publication)
            witness = ReplayWitness(canonical_json(io.encode_core(core)), canonical_json(io.encode_protocol(protocol)),
                                    canonical_json(document["facts"]), canonical_json(document["diff"]))
            step = ReplayStep(command, publication.outcome, io.hash_core(core), hash_document("protocol/v1", io.encode_protocol(protocol)),
                              hash_document("turn-facts/v1", document["facts"]), hash_document("turn-diff/v1", document["diff"]), witness)
            _pins(self._header, core)
            _validate_witness(step, self._header, io)
        except (CandidateError, ReadViewError, ValueError, TypeError, KeyError) as error:
            raise ReplayFormatError(str(error)) from error
        self._steps.append(step)
        return step

    def finish(self) -> ReplayTrace:
        return ReplayTrace(self._header, tuple(self._steps))


def _first(expected: JsonValue, actual: JsonValue, path: str) -> tuple[str, str, str] | None:
    if isinstance(expected, Mapping) and isinstance(actual, Mapping):
        for key in sorted(set(expected) | set(actual)):
            child = path + "." + key
            if key not in expected:
                return child, "<missing>", canonical_json(actual[key]).decode()
            if key not in actual:
                return child, canonical_json(expected[key]).decode(), "<missing>"
            result = _first(expected[key], actual[key], child)
            if result is not None:
                return result
        return None
    if isinstance(expected, tuple) and isinstance(actual, tuple):
        for index in range(max(len(expected), len(actual))):
            child = f"{path}[{index}]"
            if index >= len(expected):
                return child, "<missing>", canonical_json(actual[index]).decode()
            if index >= len(actual):
                return child, canonical_json(expected[index]).decode(), "<missing>"
            result = _first(expected[index], actual[index], child)
            if result is not None:
                return result
        return None
    # Python bool/int equality must not hide a canonical type mismatch.
    if canonical_json(expected) != canonical_json(actual):
        return path, canonical_json(expected).decode(), canonical_json(actual).decode()
    return None


class Runner:
    def __init__(self, initial_core: CoreSnapshot, initial_protocol: ProtocolSnapshot,
                 *, factory: ReplaySessionFactory, io: StateIO) -> None:
        self._io = io
        self._core, self._protocol, self._factory = initial_core, initial_protocol, factory

    def run(self, trace: ReplayTrace) -> tuple[ReplayMismatch, ...]:
        io = self._io
        try:
            _header(_header_document(trace.header))
            _initial(trace.header, self._core, self._protocol, io)
            io.validate_checkpoint(self._core, self._protocol)
            if len(trace.steps) > 4096:
                raise ValueError("replay step cap")
            for step in trace.steps:
                io.decode_command(io.encode_command(step.command))
                io.decode_outcome(object_value(_outcome_document(step.expected_outcome, io)))
                for digest in (step.expected_core_hash, step.expected_protocol_hash, step.expected_facts_hash, step.expected_diff_hash):
                    _hex(digest)
                _validate_witness(step, trace.header, io)
                if step.expected_witness is not None and object_value(_witness_document(step.expected_witness)["protocol"])["branch_id"] != self._protocol.branch_id:
                    raise ValueError("witness branch changed")
        except (CandidateError, ReadViewError, ValueError, TypeError, KeyError) as error:
            raise ReplayFormatError(str(error)) from error
        session = self._factory.restore(self._core, self._protocol)
        mismatches: list[ReplayMismatch] = []
        for index, step in enumerate(trace.steps):
            session.driver.submit(step.command)
            publication = session.last_publication()
            # Replay compares simulation effects; presentation is outside its witness contract.
            p = io.encode_publication(replace(publication, cues=()))
            actual: JsonObject = {"core": io.encode_core(session.snapshot()), "protocol": io.encode_protocol(session.protocol()),
                                  "facts": p["facts"], "diff": p["diff"]}
            hashes = (io.hash_core(session.snapshot()), hash_document("protocol/v1", actual["protocol"]),
                      hash_document("turn-facts/v1", actual["facts"]), hash_document("turn-diff/v1", actual["diff"]))
            expected_hashes = (step.expected_core_hash, step.expected_protocol_hash, step.expected_facts_hash, step.expected_diff_hash)
            expected = None if step.expected_witness is None else _witness_document(step.expected_witness)
            for key, expected_hash, actual_hash in zip(("core", "protocol", "facts", "diff"), expected_hashes, hashes):
                difference = None if expected is None else _first(expected[key], actual[key], "$" + key)
                if difference is not None:
                    mismatches.append(ReplayMismatch(index, *difference))
                elif expected_hash != actual_hash:
                    mismatches.append(ReplayMismatch(index, "$" + key + "_hash", expected_hash, actual_hash))
            difference = _first(_outcome_document(step.expected_outcome, io), p["outcome"], "$outcome")
            if difference is not None:
                mismatches.append(ReplayMismatch(index, *difference))
        return tuple(mismatches)
