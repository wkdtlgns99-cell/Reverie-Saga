"""Fresh registered state IO still validates every field after literal checks."""

from dataclasses import replace
from typing import cast

import pytest

from app.headless import state_io
from contracts.errors import SchemaError
from domain.canonical import canonical_json
from tests.unit.registered_io_fixtures import ACTOR, GaugeRecord, bundle, session
from tests.unit.test_serialization_metadata import CountedCodec


@pytest.mark.parametrize("value", (-9, -1, 0, 9))
def test_valid_fresh_states_keep_codec_roundtrip_and_hash(value: int) -> None:
    codec = CountedCodec()
    io = state_io((replace(bundle(), component_codecs=(codec,)),))
    first = session(value=2).snapshot()
    changed = replace(first, components=(GaugeRecord(ACTOR, value, "계기"),))
    first_document = canonical_json(io.encode_core(first))
    encoded = io.encode_core(changed)
    assert codec.encodes == 4 and codec.decodes == 2
    assert io.decode_core(encoded) == changed
    assert io.hash_core(io.decode_core(encoded)) == io.hash_core(changed)
    assert canonical_json(io.encode_core(first)) == first_document


@pytest.mark.parametrize("bad", (True, False, 10, -10, 2**200, None, 1.0))
def test_integer_field_type_and_range_reject_after_a_valid_state(bad: object) -> None:
    io = state_io((bundle(),))
    first = session().snapshot()
    before = canonical_json(io.encode_core(first))
    damaged = replace(first, components=(GaugeRecord(ACTOR, cast(int, bad), "계기"),))
    with pytest.raises(SchemaError) as caught:
        io.encode_core(damaged)
    assert caught.value.code == "INVALID_COMPONENT"
    assert canonical_json(io.encode_core(first)) == before


@pytest.mark.parametrize("bad", ("e\u0301", "\ud800", "", [], {"x": 1}))
def test_valid_literal_field_cannot_hide_invalid_text_sibling(bad: object) -> None:
    io = state_io((bundle(),))
    first = session().snapshot()
    before = canonical_json(io.encode_core(first))
    damaged = replace(first, components=(GaugeRecord(ACTOR, 0, cast(str, bad)),))
    with pytest.raises(SchemaError) as caught:
        io.encode_core(damaged)
    assert caught.value.code == "INVALID_COMPONENT"
    assert canonical_json(io.encode_core(first)) == before
