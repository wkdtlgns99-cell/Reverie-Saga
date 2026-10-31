"""Object keys keep validation order, ownership and exact composition depth."""

from collections import UserDict
from collections.abc import ItemsView
import json
from types import MappingProxyType
from typing import cast

import pytest

from domain.canonical import CanonicalDocument, JsonValue, canonical_json, seal


def nested(depth: int, value: object) -> object:
    for _ in range(depth):
        value = [value]
    return value


def convert(entry: str, value: object) -> object:
    if entry == "seal":
        return seal(value)
    if entry == "canonical":
        return canonical_json(cast(JsonValue, value))
    return CanonicalDocument(value)


@pytest.mark.parametrize("entry", ("seal", "canonical", "owned"))
def test_key_errors_precede_child_errors_at_the_exact_depth(entry: str) -> None:
    cases = (
        (32, 1, "JSON object keys must be strings"),
        (32, "e\u0301", "JSON nesting exceeds32"),
        (32, "\ud800", "JSON nesting exceeds32"),
        (32, "valid", "JSON nesting exceeds32"),
        (31, "e\u0301", "non-NFC string"),
        (31, "valid", "unsupported canonical value"),
    )
    for depth, key, message in cases:
        with pytest.raises(ValueError) as caught:
            convert(entry, nested(depth, {key: object()}))
        assert str(caught.value) == message
    with pytest.raises(UnicodeEncodeError) as caught:
        convert(entry, nested(31, {"\ud800": object()}))
    assert caught.value.encoding == "utf-8"
    assert caught.value.reason == "surrogates not allowed"
    assert convert(entry, nested(31, {"문": None})) is not None
    assert convert(entry, nested(32, {})) is not None


@pytest.mark.parametrize("entry", ("seal", "canonical", "owned"))
def test_subclass_key_is_validated_before_mapping_child_traversal(entry: str) -> None:
    observed: list[str] = []

    class Key(str):
        def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
            observed.append("key_utf8")
            return super().encode(encoding, errors)

    class Child(UserDict[str, object]):
        def items(self) -> ItemsView[str, object]:
            observed.append("child_items")
            return super().items()

    child = Child(n=7)
    source = {Key("문"): child}
    result = convert(entry, source)
    assert observed == ["key_utf8", "child_items"]
    assert child == {"n": 7} and len(source) == 1
    if entry == "canonical":
        assert result == '{"문":{"n":7}}'.encode()
    elif isinstance(result, CanonicalDocument):
        assert result.to_bytes() == '{"문":{"n":7}}'.encode()


def test_owned_map_key_height_composes_to32_and_keeps_external_aliases_owned() -> None:
    backing: dict[str, object] = {"문": []}
    document = CanonicalDocument(MappingProxyType(backing))
    parent = CanonicalDocument(nested(31, document), children=(document,))
    expected = b"[" * 31 + '{"문":[]}'.encode() + b"]" * 31
    assert parent.to_bytes() == expected
    with pytest.raises(ValueError, match="^JSON nesting exceeds32$"):
        CanonicalDocument(nested(32, document), children=(document,))
    cast(list[object], backing["문"]).append("later")
    backing["e\u0301"] = 1
    assert parent.to_bytes() == expected
    with pytest.raises(ValueError, match="^non-NFC string$"):
        CanonicalDocument(MappingProxyType(backing))


@pytest.mark.parametrize("entry", ("seal", "canonical", "owned"))
def test_all_ascii_codepoints_and_subclass_proof_boundary(entry: str) -> None:
    text = "".join(chr(codepoint) for codepoint in range(128))
    source = {text: text}
    result = convert(entry, source)
    body = result.to_bytes() if isinstance(result, CanonicalDocument) else result
    if not isinstance(body, bytes):
        body = canonical_json(cast(JsonValue, body))
    assert json.loads(body) == source

    class PretendsAscii(str):
        def isascii(self) -> bool:
            raise AssertionError("subclass is not a built-in ASCII proof")

    assert convert(entry, {PretendsAscii("valid"): PretendsAscii("valid")}) is not None
    for bad in (PretendsAscii("e\u0301"), PretendsAscii("\ud800")):
        with pytest.raises(ValueError):
            convert(entry, {bad: "valid"})
        with pytest.raises(ValueError):
            convert(entry, {"valid": bad})
