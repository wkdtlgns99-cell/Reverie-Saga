from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from types import MappingProxyType
from typing import cast
import unicodedata

type JsonValue = None | bool | int | str | tuple[JsonValue, ...] | Mapping[str, JsonValue]
type JsonObject = Mapping[str, JsonValue]


def seal(value: object, depth: int = 0) -> JsonValue:
    """Convert decoded I/O values immediately to owned immutable canonical DTOs."""
    if depth > 32:
        raise ValueError("JSON nesting exceeds32")
    if value is None or type(value) is bool or type(value) is int:
        return value
    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            raise ValueError("non-NFC string")
        value.encode("utf-8", errors="strict")
        return value
    if isinstance(value, (list, tuple)):
        return tuple(seal(v, depth + 1) for v in cast(list[object] | tuple[object, ...], value))
    if isinstance(value, Mapping):
        pairs = cast(Mapping[object, object], value)
        result: dict[str, JsonValue] = {}
        for key, child in pairs.items():
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
            seal(key, depth + 1)
            result[key] = seal(child, depth + 1)
        return MappingProxyType(result)
    raise ValueError("unsupported canonical value")


def _plain(value: JsonValue) -> object:
    if isinstance(value, Mapping):
        return {key: _plain(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_plain(child) for child in value]
    return value


def canonical_json(value: JsonValue) -> bytes:
    return json.dumps(_plain(seal(value)), ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


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
    return seal(json.loads(body.decode("utf-8", errors="strict"),
                           object_pairs_hook=_unique, parse_constant=_nonfinite))


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
