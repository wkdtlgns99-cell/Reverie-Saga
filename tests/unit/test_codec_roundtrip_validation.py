"""Codec round-trip comparisons retain strict rejection and owned public DTOs."""

from collections.abc import Mapping
from dataclasses import replace
from typing import cast

import pytest

from app.headless import state_io
from contracts.errors import SchemaError
from contracts.state_io import StateIO
from domain.canonical import JsonObject, JsonValue, array_value, canonical_json, object_value
from domain.primitives import EntityId, FrozenPayload, TypeKey
from domain.state_types import ComponentRecord
from tests.unit.registered_io_fixtures import (
    AdjustCommand,
    GaugeCodec,
    GaugePayloadCodec,
    bundle,
    command,
    key,
    session,
)


class IntegerSubclass(int):
    pass


class ComponentCodecProbe(GaugeCodec):
    def __init__(self, roundtrip: object) -> None:
        self.roundtrip = roundtrip
        self.decoded = False
        self.seen: JsonObject | None = None

    def encode(self, record: ComponentRecord) -> JsonObject:
        if self.decoded:
            return cast(JsonObject, self.roundtrip)
        return super().encode(record)

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        self.seen = fields
        decoded = super().decode(entity_id, fields)
        self.decoded = True
        return decoded


class PayloadCodecProbe:
    def __init__(self, roundtrip: object) -> None:
        self.roundtrip = roundtrip
        self.decoded = False
        self.seen: JsonObject | None = None
        self.first: JsonObject = {"amount": 1}

    @property
    def schema(self) -> TypeKey:
        return key("adjust")

    def encode(self, payload: FrozenPayload) -> JsonObject:
        assert isinstance(payload, AdjustCommand)
        return cast(JsonObject, self.roundtrip) if self.decoded else self.first

    def decode(self, data: JsonObject) -> FrozenPayload:
        self.seen = data
        decoded = GaugePayloadCodec(self.schema).decode(data)
        self.decoded = True
        return decoded


def selected_io(probe: ComponentCodecProbe | PayloadCodecProbe) -> StateIO:
    original = bundle()
    if isinstance(probe, ComponentCodecProbe):
        selected = replace(original, component_codecs=(probe,))
    else:
        selected = replace(
            original,
            codecs=tuple(probe if c.schema == probe.schema else c for c in original.codecs),
        )
    return state_io((selected,))


def invalid_roundtrip(mode: str, component: bool) -> object:
    valid: dict[object, object] = {"value": 2, "label": "계기"} if component else {"amount": 1}
    field = "value" if component else "amount"
    if mode == "missing":
        return {}
    if mode == "extra":
        return {**valid, "extra": 0}
    if mode == "changed":
        return {**valid, field: 3}
    if mode == "top_array":
        return [valid]
    if mode == "float":
        return {**valid, field: 1.0}
    if mode == "integer_subclass":
        return {**valid, field: IntegerSubclass(1)}
    if mode == "non_string_key":
        return {**valid, 1: 1}
    if mode == "non_nfc_key":
        return {**valid, "e\u0301": 1}
    leaf: object = {
        "non_nfc_value": "e\u0301",
        "surrogate": "\ud800",
        "bytes": b"x",
        "object": object(),
    }.get(mode)
    if mode == "overdepth":
        for _ in range(33):
            leaf = [leaf]
    elif mode == "cycle":
        cycle: list[object] = []
        cycle.append(cycle)
        leaf = cycle
    else:
        assert mode in ("non_nfc_value", "surrogate", "bytes", "object")
    return {**valid, "nested": leaf}


@pytest.mark.parametrize("component", (True, False), ids=("component", "payload"))
@pytest.mark.parametrize(
    "mode",
    (
        "missing",
        "extra",
        "changed",
        "top_array",
        "float",
        "integer_subclass",
        "non_string_key",
        "non_nfc_key",
        "non_nfc_value",
        "surrogate",
        "bytes",
        "object",
        "overdepth",
        "cycle",
    ),
)
def test_invalid_second_encode_preserves_code_path_and_inputs(mode: str, component: bool) -> None:
    raw = invalid_roundtrip(mode, component)
    before = repr(raw)
    probe = ComponentCodecProbe(raw) if component else PayloadCodecProbe(raw)
    selected = selected_io(probe)
    owner = session()
    core, protocol = owner.snapshot(), owner.protocol()
    original = canonical_json(state_io((bundle(),)).encode_core(core))
    with pytest.raises(SchemaError, match="INVALID_COMPONENT|INVALID_PAYLOAD") as caught:
        if component:
            selected.encode_core(core)
        else:
            selected.encode_payload(AdjustCommand(1))
    assert (caught.value.code, caught.value.path) == (
        ("INVALID_COMPONENT", "core.component.fields")
        if component
        else ("INVALID_PAYLOAD", "payload")
    )
    assert probe.decoded and probe.seen is not None
    assert repr(raw) == before
    assert owner.snapshot() == core and owner.protocol() == protocol
    assert canonical_json(state_io((bundle(),)).encode_core(core)) == original


@pytest.mark.parametrize("component", (True, False), ids=("component", "payload"))
def test_roundtrip_and_public_encoder_documents_are_owned(component: bool) -> None:
    raw: dict[str, JsonValue] = {"label": "계기", "value": 2} if component else {"amount": 1}
    probe = ComponentCodecProbe(raw) if component else PayloadCodecProbe(raw)
    selected = selected_io(probe)
    if component:
        document = selected.encode_core(session().snapshot())
        fields = object_value(object_value(array_value(document["components"])[0])["fields"])
        expected = '{"label":"계기","value":2}'.encode()
    else:
        document = selected.encode_payload(AdjustCommand(1))
        fields = document
        expected = b'{"amount":1}'
    assert canonical_json(fields) == expected
    assert isinstance(probe.seen, Mapping)
    seen_bytes = canonical_json(probe.seen)
    raw["extra"] = 4
    if isinstance(probe, PayloadCodecProbe):
        cast(dict[str, JsonValue], probe.first)["amount"] = 3
    assert canonical_json(fields) == expected and canonical_json(probe.seen) == seen_bytes
    with pytest.raises(TypeError):
        cast(dict[str, JsonValue], fields)["extra"] = 9
    with pytest.raises(TypeError):
        cast(dict[str, JsonValue], probe.seen)["extra"] = 9
    assert canonical_json(fields) == expected


@pytest.mark.parametrize("value", (-9, 0, 9))
def test_component_boundaries_and_literal_roundtrip(value: int) -> None:
    selected = state_io((bundle(),))
    core = session(value=value).snapshot()
    document = selected.encode_core(core)
    fields = object_value(object_value(array_value(document["components"])[0])["fields"])
    assert canonical_json(fields) == ('{"label":"계기","value":' + str(value) + "}").encode()
    assert selected.decode_core(document) == core


@pytest.mark.parametrize("amount", (-3, 0, 3))
def test_payload_boundaries_and_literal_roundtrip(amount: int) -> None:
    selected = state_io((bundle(),))
    request = command(amount=amount)
    document = selected.encode_command(request)
    assert canonical_json(document["payload"]) == ('{"amount":' + str(amount) + "}").encode()
    assert selected.decode_command(document) == request
