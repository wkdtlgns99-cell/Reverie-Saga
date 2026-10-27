"""Canonical output and owned sealing share strict validation at every tree depth."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import cast

import pytest

from domain.canonical import JsonValue, canonical_json, seal


class IntegerSubclass(int):
    pass


class StringSubclass(str):
    pass


def nested(depth: int, leaf: object) -> object:
    for _ in range(depth):
        leaf = [leaf]
    return leaf


def serialize(raw: object) -> bytes:
    return canonical_json(cast(JsonValue, raw))


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        ({"b": [True, None, -2], "a": "문"}, '{"a":"문","b":[true,null,-2]}'.encode()),
        ((False, 0, True, 1), b"[false,0,true,1]"),
        ([False, 0, True, 1], b"[false,0,true,1]"),
        (MappingProxyType({"z": (), "a": {}}), b'{"a":{},"z":[]}'),
        (StringSubclass("문"), '"문"'.encode()),
        (2**200, str(2**200).encode()),
        ({"\n": '\t"\\'}, b'{"\\n":"\\t\\"\\\\"}'),
    ),
)
def test_exact_literal_bytes_and_sealed_equivalence(raw: object, expected: bytes) -> None:
    assert serialize(raw) == expected
    assert canonical_json(seal(raw)) == expected


@pytest.mark.parametrize("entry", ("seal", "serialize"))
@pytest.mark.parametrize(
    ("raw", "message"),
    (
        (1.0, "unsupported canonical value"),
        (float("nan"), "unsupported canonical value"),
        (float("inf"), "unsupported canonical value"),
        (b"text", "unsupported canonical value"),
        (bytearray(b"text"), "unsupported canonical value"),
        ({1, 2}, "unsupported canonical value"),
        (IntegerSubclass(1), "unsupported canonical value"),
        (object(), "unsupported canonical value"),
        ("e\u0301", "non-NFC string"),
        ({1: "value"}, "JSON object keys must be strings"),
        ({"e\u0301": "value"}, "non-NFC string"),
        ([{"ok": [1, 2.0]}], "unsupported canonical value"),
    ),
)
def test_invalid_nested_values_preserve_error(entry: str, raw: object, message: str) -> None:
    selected = seal if entry == "seal" else serialize
    with pytest.raises(ValueError) as caught:
        selected(raw)
    assert str(caught.value) == message


@pytest.mark.parametrize("entry", ("seal", "serialize"))
@pytest.mark.parametrize("raw", ("\ud800", {"\ud800": 1}, ["\udfff"]))
def test_unpaired_surrogates_reject_as_strict_utf8(entry: str, raw: object) -> None:
    selected = seal if entry == "seal" else serialize
    with pytest.raises(UnicodeEncodeError) as caught:
        selected(raw)
    assert caught.value.encoding == "utf-8" and caught.value.reason == "surrogates not allowed"


@pytest.mark.parametrize("entry", ("seal", "serialize"))
def test_depth_and_key_error_precedence(entry: str) -> None:
    selected = seal if entry == "seal" else serialize
    assert selected(nested(32, None)) is not None
    assert selected(nested(32, {})) is not None
    for invalid in (nested(33, None), nested(32, {"x": 1})):
        with pytest.raises(ValueError) as caught:
            selected(invalid)
        assert str(caught.value) == "JSON nesting exceeds32"
    with pytest.raises(ValueError) as caught:
        selected(nested(32, {1: 1}))
    assert str(caught.value) == "JSON object keys must be strings"


@pytest.mark.parametrize("entry", ("seal", "serialize"))
def test_cycles_reject_without_modifying_caller(entry: str) -> None:
    raw: list[object] = []
    raw.append(raw)
    selected = seal if entry == "seal" else serialize
    with pytest.raises(ValueError) as caught:
        selected(raw)
    assert str(caught.value) == "JSON nesting exceeds32"
    assert len(raw) == 1 and raw[0] is raw


def test_owned_immutable_snapshot_and_input_aliases() -> None:
    values: list[object] = ["문", {"n": 2}]
    backing: dict[str, object] = {"a": values, "b": values}
    source = MappingProxyType(backing)
    expected = '{"a":["문",{"n":2}],"b":["문",{"n":2}]}'.encode()
    assert serialize(source) == expected and backing["a"] is backing["b"] is values
    frozen = seal(source)
    assert isinstance(frozen, Mapping) and isinstance(frozen["a"], tuple)
    assert frozen["a"] is not frozen["b"]
    backing["new"] = 3
    values.append("later")
    assert canonical_json(frozen) == expected
    with pytest.raises(TypeError):
        cast(dict[str, JsonValue], frozen)["new"] = 1
    assert canonical_json(frozen) == expected
