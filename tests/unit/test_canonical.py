from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from app.headless import BootstrapSpec, bootstrap, state_io
from app.feature_registry import feature_bundles
from domain.primitives import EntityId
from domain.canonical import JsonValue, array_value, canonical_json, decode_json, hash_document, object_value, pack, text_value
IO = state_io(feature_bundles(EntityId("actor:toy")))
core_hash, protocol_document = IO.hash_core, IO.encode_protocol


def vectors() -> dict[str, JsonValue]:
    path = Path(__file__).resolve().parents[2] / "docs/work_orders/PHASE0_REFERENCE_VECTORS.json"
    return dict(object_value(decode_json(path.read_bytes())))


def test_literal_vectors() -> None:
    data = vectors()
    for item in array_value(data["documents"]):
        v = object_value(item)
        document = v["document"]
        assert canonical_json(document).decode() == v["utf8"]
        assert canonical_json(document).hex() == v["utf8_hex"]
        assert hash_document(text_value(v["tag"]), document) == v["sha256"]
    session = bootstrap(BootstrapSpec("0" * 64, "0" * 32, "1" * 32))
    header = object_value(object_value(object_value(data["golden_fixture"])["trace"])["header"])
    assert core_hash(session.snapshot()) == header["initial_core_hash"]
    assert hash_document("protocol/v1", protocol_document(session.protocol())) == header["initial_protocol_hash"]


def test_pack_utf8() -> None:
    for item in array_value(vectors()["pack_vectors"]):
        v = object_value(item)
        assert pack(tuple(text_value(t) for t in array_value(v["tokens"]))).hex() == v["hex"]
    assert pack(("ab", "c")) != pack(("a", "bc"))


def test_invalid_canonical_values() -> None:
    for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1.0}', b'"\\ud800"'):
        with pytest.raises(ValueError):
            decode_json(raw)
    with pytest.raises(ValueError):
        canonical_json(cast(JsonValue, 1.1))


def test_core_protocol_separation() -> None:
    first = bootstrap(BootstrapSpec("0" * 64, "0" * 32, "1" * 32))
    second = bootstrap(BootstrapSpec("0" * 64, "2" * 32, "3" * 32))
    assert core_hash(first.snapshot()) == core_hash(second.snapshot())
    assert protocol_document(first.protocol()) != protocol_document(second.protocol())
