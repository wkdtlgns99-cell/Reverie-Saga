from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from types import MappingProxyType
from typing import cast
import unicodedata
from dataclasses import dataclass

type JsonValue = None | bool | int | str | tuple[JsonValue, ...] | Mapping[str, JsonValue]
type JsonObject = Mapping[str, JsonValue]


def seal(value: object, depth: int = 0) -> JsonValue:
    """Convert decoded I/O values immediately to owned immutable canonical DTOs."""
    return cast(JsonValue, _convert(value, depth, immutable=True))


def _checked_text(value: str) -> str:
    if type(value) is str and value.isascii():
        return value
    if unicodedata.normalize("NFC", value) != value:
        raise ValueError("non-NFC string")
    value.encode("utf-8", errors="strict")
    return value


def _convert(
    value: object,
    depth: int,
    immutable: bool,
    owned_children: frozenset[int] | None = None,
    maximum: list[int] | None = None,
) -> object:
    """Validate once while building the owned representation needed by the caller."""
    if depth > 32:
        raise ValueError("JSON nesting exceeds32")
    if maximum is not None and depth > maximum[0]:
        maximum[0] = depth
    kind = type(value)
    if owned_children is not None and kind is CanonicalDocument and id(value) in owned_children:
        document = cast(CanonicalDocument, value)
        if depth + document._depth > 32:
            raise ValueError("JSON nesting exceeds32")
        if maximum is not None and depth + document._depth > maximum[0]:
            maximum[0] = depth + document._depth
        return document.value
    if value is None or kind is bool or kind is int:
        return value
    if kind is str or isinstance(value, str):
        return _checked_text(cast(str, value))
    if kind is list or kind is tuple or isinstance(value, (list, tuple)):
        children = (
            _convert(v, depth + 1, immutable, owned_children, maximum)
            for v in cast(list[object] | tuple[object, ...], value)
        )
        return tuple(children) if immutable else list(children)
    if kind is dict or kind is MappingProxyType or isinstance(value, Mapping):
        pairs = cast(Mapping[object, object], value)
        result: dict[str, object] = {}
        for key, child in pairs.items():
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
            if depth + 1 > 32:
                raise ValueError("JSON nesting exceeds32")
            _checked_text(key)
            # The child at this same depth also records the key's height.
            result[key] = _convert(child, depth + 1, immutable, owned_children, maximum)
        return MappingProxyType(result) if immutable else result
    raise ValueError("unsupported canonical value")


def _proxy_document(value: object) -> object:
    if type(value) is MappingProxyType:
        return dict(cast(JsonObject, value))
    raise TypeError("unsupported JSON document")


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=_proxy_document,
    ).encode("utf-8")


def _owned_height(value: JsonValue) -> int:
    kind = type(value)
    if kind is tuple:
        children = cast(tuple[JsonValue, ...], value)
        return 0 if not children else 1 + max(_owned_height(child) for child in children)
    if kind is MappingProxyType:
        values = cast(JsonObject, value)
        return 0 if not values else 1 + max(_owned_height(child) for child in values.values())
    return 0


@dataclass(frozen=True, slots=True, init=False)
class CanonicalDocument:
    """An owned immutable JSON value,composable only through fresh checked construction."""

    value: JsonValue
    _depth: int

    def __init__(self, value: object, *, children: tuple[CanonicalDocument, ...] = ()) -> None:
        if any(type(child) is not CanonicalDocument for child in children):
            raise ValueError("unsupported canonical value")
        maximum = [0]
        selected = frozenset(id(child) for child in children) if children else None
        owned = _convert(value, 0, immutable=True, owned_children=selected, maximum=maximum)
        object.__setattr__(self, "value", cast(JsonValue, owned))
        object.__setattr__(self, "_depth", maximum[0])

    def select(self, keys: tuple[str, ...]) -> CanonicalDocument:
        source = object_value(self.value)
        values: dict[str, JsonValue] = {}
        for key in keys:
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
            seal(key)
            values[key] = source[key]
        owned = MappingProxyType(values)
        result = object.__new__(CanonicalDocument)
        object.__setattr__(result, "value", owned)
        object.__setattr__(result, "_depth", _owned_height(owned))
        return result

    def to_bytes(self) -> bytes:
        return _json_bytes(self.value)


def canonical_json(value: JsonValue) -> bytes:
    return _json_bytes(_convert(value, 0, immutable=False))


def pack(tokens: tuple[str, ...]) -> bytes:
    result = bytearray()
    for token in tokens:
        if not isinstance(token, str):
            raise ValueError("pack tokens must be strings")
        data = token.encode("utf-8", errors="strict")
        if len(data) > 2**32 - 1:
            raise ValueError("token too long")
        result.extend(len(data).to_bytes(4, "big"))
        result.extend(data)
    return bytes(result)


def tagged_hash(tag: str, document: bytes) -> str:
    return hashlib.sha256(pack((tag, document.decode("utf-8", errors="strict")))).hexdigest()


def hash_document(tag: str, document: JsonValue) -> str:
    return tagged_hash(tag, canonical_json(document))


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(value: str) -> None:
    raise ValueError(f"nonfinite JSON value: {value}")


def decode_json(body: bytes) -> JsonValue:
    return seal(
        json.loads(
            body.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique,
            parse_constant=_nonfinite,
        )
    )


def object_value(value: JsonValue) -> JsonObject:
    if not isinstance(value, Mapping):
        raise ValueError("JSON object required")
    return value


def exact_fields(value: JsonValue, names: tuple[str, ...]) -> JsonObject:
    result = object_value(value)
    if set(result) != set(names):
        raise ValueError("missing or unknown fields")
    return result


def text_value(value: JsonValue) -> str:
    if not isinstance(value, str):
        raise ValueError("string required")
    return value


def int_value(value: JsonValue) -> int:
    if type(value) is not int:
        raise ValueError("integer required")
    return value


def array_value(value: JsonValue) -> tuple[JsonValue, ...]:
    if not isinstance(value, tuple):
        raise ValueError("array required")
    return value
