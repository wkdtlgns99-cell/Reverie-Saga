"""Protocol conversions retain fresh validation,owned bytes and literal error boundaries."""

from dataclasses import replace
from pathlib import Path
from typing import cast
import pytest
from app.headless import state_io
from contracts.turn import ProtocolSnapshot
from domain.canonical import canonical_json, object_value, decode_json
from domain.primitives import WorldRevision
from tests.integration.test_reach_gate_aid import session, bundle


@pytest.mark.parametrize(
    "mode,message",
    (
        ("fingerprint", "receipt fingerprint"),
        ("head", "latest receipt does not match head"),
        ("branch", "receipt stream ownership/high-water"),
        ("highwater", "receipt stream ownership/high-water"),
        ("command_bool", "integer outside declared range"),
        ("duplicate", "receipt cap/identity"),
        ("order", "unsorted receipts"),
    ),
)
def test_native_and_document_receipt_rejections_stay_fresh(
    tmp_path: Path, mode: str, message: str
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("up")
        core, protocol = owner.owner.snapshot(), owner.owner.protocol()
        io = state_io((bundle(),))
        before = owner.owner.working_path.read_bytes()
        io.validate_checkpoint(core, protocol)
        records = list(protocol.receipts)
        malformed: ProtocolSnapshot
        if mode == "fingerprint":
            records[0] = replace(records[0], command_fingerprint="f" * 64)
        elif mode == "head":
            records[-1] = replace(
                records[-1], receipt=replace(records[-1].receipt, core_hash="f" * 64)
            )
        elif mode == "command_bool":
            records[0] = replace(
                records[0],
                command=replace(records[0].command, expected_revision=cast(WorldRevision, True)),
            )
        elif mode == "duplicate":
            records.append(records[-1])
        elif mode == "order":
            records.reverse()
        malformed = replace(protocol, receipts=tuple(records))
        if mode == "branch":
            malformed = replace(malformed, branch_id="f" * 32)
        if mode == "highwater":
            malformed = replace(
                malformed, streams=(replace(protocol.streams[0], highest_committed_sequence=0),)
            )
        with pytest.raises(ValueError, match=message):
            io.validate_checkpoint(core, malformed)
        # The public wire decoder must reject the same malformed field independently.
        if mode != "command_bool":
            document = io.encode_protocol(malformed)
            with pytest.raises(ValueError, match=message):
                io.decode_protocol(document, core)
        io.validate_checkpoint(core, protocol)
        assert owner.owner.snapshot() == core and owner.owner.protocol() == protocol
        assert owner.owner.working_path.read_bytes() == before
    finally:
        owner.close()


def test_protocol_owned_wire_and_native_roundtrip(tmp_path: Path) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        core, protocol = owner.owner.snapshot(), owner.owner.protocol()
        io = state_io((bundle(),))
        body = canonical_json(io.encode_protocol(protocol))
        owned = object_value(decode_json(body))
        assert io.decode_protocol(owned, core) == protocol
        io.validate_checkpoint(core, protocol)
        assert canonical_json(io.encode_protocol(protocol)) == body
        assert b'"expected_revision":0' in body and b'"revision":2' in body
    finally:
        owner.close()
