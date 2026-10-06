from __future__ import annotations

from dataclasses import replace
import hashlib

import pytest

from contracts.persistence import SaveError
from contracts.turn import TurnCommitted
from domain.canonical import array_value, canonical_json, hash_document, object_value, text_value
from domain.primitives import Tick
from orchestration.persistence import (
    canonical_object, checkpoint_document, decode_checkpoint, decode_segment, prepare_turn, project_rows,
)
from tests.unit.durability_fixtures import ROOT, checkpoint, io, projection_document, turn, vectors


def test_projection_matches_independent_rows() -> None:
    selected, initial, expected = io(), checkpoint(), vectors()
    assert canonical_json(projection_document(project_rows(initial, io=selected))) == canonical_json(expected["initial_rows"])
    body = canonical_json(checkpoint_document(initial, io=selected))
    assert body.hex() == expected["initial_checkpoint_body_hex"]
    assert hash_document("save-checkpoint/v1", canonical_object(body)) == expected["initial_checkpoint_sha256"]
    assert decode_checkpoint(canonical_object(body), io=selected) == initial


def test_sparse_row_changes() -> None:
    plan = prepare_turn(turn(), io=io())
    expected = object_value(array_value(vectors()["steps"])[0])
    assert canonical_json(projection_document(plan.next)) == canonical_json(expected["rows"])
    assert plan.step_body.hex() == expected["replay_body_hex"]
    assert plan.step_sha256 == expected["replay_sha256"]
    assert tuple(c.kind for c in plan.components_upserts) == ("watch.lantern",)
    assert not plan.components_deletes and not plan.pending_upserts and not plan.pending_deletes
    assert len(plan.streams_upserts) == len(plan.receipts_upserts) == 1


@pytest.mark.parametrize("body", [b'{} ', b'{"a":1,"a":2}', b'{"a":1.5}', b'{"a":NaN}', b'\xff', b'[]', b'{"a":"e\\u0301"}'])
def test_strict_canonical_bytes(body: bytes) -> None:
    with pytest.raises(SaveError, match="SAVE_CORRUPT"):
        canonical_object(body)


@pytest.mark.parametrize("change", ["extra", "missing", "bool_tick", "world", "protocol_hash", "rules", "package"])
def test_checkpoint_closed_codec(change: str) -> None:
    selected = io()
    d = dict(checkpoint_document(checkpoint(), io=selected))
    core = dict(object_value(d["core"]))
    header = dict(object_value(d["header"]))
    if change == "extra":
        d["extra"] = 0
    elif change == "missing":
        del d["protocol"]
    elif change == "bool_tick":
        core["tick"] = False
    elif change == "world":
        core["world_id"] = "w1-" + "1" * 64
    elif change == "protocol_hash":
        header["initial_protocol_hash"] = "1" * 64
    elif change == "rules":
        core["pins"] = {**object_value(core["pins"]), "rules_fingerprint": "1" * 64}
    else:
        header["build_artifacts"] = ({"package_id": "fixture:package", "version": 1, "sha256": "0" * 64},)
    d["core"], d["header"] = core, header
    code = "UNSUPPORTED_RULESET" if change == "rules" else "SAVE_PACKAGE_UNAVAILABLE" if change == "package" else "SAVE_CORRUPT"
    with pytest.raises(SaveError, match=code):
        decode_checkpoint(d, io=selected)


@pytest.mark.parametrize("change", ["revision", "streams", "receipt", "cues", "world"])
def test_invalid_durable_transition(change: str) -> None:
    request = turn()
    if change == "revision":
        request = replace(request, next=replace(request.next, protocol=request.previous.protocol))
    elif change == "streams":
        request = replace(request, next=replace(request.next, protocol=replace(request.next.protocol, streams=request.previous.protocol.streams)))
    elif change == "receipt":
        assert isinstance(request.publication.outcome, TurnCommitted)
        request = replace(request, publication=replace(request.publication, outcome=TurnCommitted(replace(request.publication.outcome.receipt, tick=Tick(99)))))
    elif change == "cues":
        from tests.unit.watch_fixtures import session
        owner = session()
        owner.driver.submit(request.command)
        # Tick1 has no cue; changing preparation to a two-second real action gives cues.
        from contracts.watch import WaitCommand
        from tests.unit.watch_fixtures import command
        request = turn(command(WaitCommand(2)))
        owner = session()
        owner.driver.submit(request.command)
        request = replace(request, publication=owner.last_publication())
    else:
        request = replace(request, next=replace(request.next, core=replace(request.next.core, world_id="w1-" + "1" * 64)))
    with pytest.raises(SaveError):
        prepare_turn(request, io=io())


def test_segment_chain() -> None:
    bodies = tuple(bytes.fromhex(text_value(object_value(s)["replay_body_hex"]))
                   for s in array_value(vectors()["steps"]) if object_value(s)["new_commit"])
    segment = decode_segment(checkpoint(), bodies, io=io())
    assert len(segment.trace.steps) == 9
    assert all(s.expected_witness is None for s in segment.trace.steps)
    with pytest.raises(SaveError, match="SAVE_CORRUPT"):
        decode_segment(checkpoint(), (bodies[1],), io=io())


@pytest.mark.parametrize("passive,sha", [(False, "4c9dcfea46c1f1ba0c08b0fc94d9a13211fb7e32fd52a43eaf7bdf0233425472"), (True, "f0adc9c19bbb94fd4fe3f6e1a70bf95e63a1221e7f354b3a09a237c592616951")])
def test_independent_fixture_bytes(passive: bool, sha: str) -> None:
    name = "durable_watch_passive_v1.json" if passive else "durable_watch_v1.json"
    assert hashlib.sha256((ROOT / "tests/replay/fixtures" / name).read_bytes()).hexdigest() == sha


def test_independent_toy_boundary_inputs_match_real_replay() -> None:
    from app.feature_registry import feature_bundles
    from app.headless import _CheckpointFactory, state_io
    from domain.primitives import EntityId
    from orchestration.replay import Runner
    from tests.unit.durability_fixtures import toy_segment_input
    sample = toy_segment_input(3)
    bundles = feature_bundles(EntityId("actor:toy"))
    selected = state_io(bundles)
    segment = decode_segment(sample.initial, sample.bodies, io=selected)
    assert Runner(sample.initial.core, sample.initial.protocol,
                  factory=_CheckpointFactory(bundles), io=selected).run(segment.trace) == ()
