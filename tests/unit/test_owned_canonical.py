"""Fresh canonical documents preserve validation,depth and owned-source bytes."""

from dataclasses import FrozenInstanceError
from types import MappingProxyType
from typing import cast
import pytest
from domain.canonical import CanonicalDocument, canonical_json, seal, JsonValue, object_value


@pytest.mark.parametrize(
    "value", (None, True, False, -7, "문", (), {}, {"b": [True, None, -2], "a": "문"})
)
def test_owned_document_matches_public_canonical_bytes(value: object) -> None:
    document = CanonicalDocument(value)
    assert document.to_bytes() == canonical_json(cast(JsonValue, value))
    with pytest.raises(FrozenInstanceError):
        setattr(document, "value", None)
    with pytest.raises(ValueError, match="unsupported canonical value"):
        seal(document)


def test_owned_document_copies_external_proxy_and_composes() -> None:
    backing = {"value": 1}
    source: dict[str, list[object]] = {"child": [MappingProxyType(backing)]}
    child = CanonicalDocument(source)
    parent = CanonicalDocument({"owned": child}, children=(child,))
    backing["value"] = 8
    source["child"].append({"value": 9})
    assert parent.to_bytes() == b'{"owned":{"child":[{"value":1}]}}'
    with pytest.raises(TypeError):
        cast(dict[str, JsonValue], object_value(child.value))["extra"] = 1


def test_owned_composition_retains_exact_nesting_boundary() -> None:
    value: object = 0
    for _ in range(32):
        value = [value]
    child = CanonicalDocument(value)
    assert child.to_bytes() == b"[" * 32 + b"0" + b"]" * 32
    with pytest.raises(ValueError, match="JSON nesting exceeds32"):
        CanonicalDocument([child], children=(child,))


@pytest.mark.parametrize("value", (1.0, b"x", {"e\u0301": 1}, {"x": "\ud800"}, {1: 0}))
def test_owned_document_rejects_same_invalid_inputs(value: object) -> None:
    with pytest.raises(ValueError):
        CanonicalDocument(value)


def test_unlisted_owned_child_is_not_an_external_input_escape() -> None:
    approved = CanonicalDocument(1)
    external = CanonicalDocument(2)
    with pytest.raises(ValueError, match="unsupported canonical value"):
        CanonicalDocument({"approved": approved, "unlisted": external}, children=(approved,))


@pytest.mark.parametrize("keys", (("e\u0301",), ("\ud800",), (1,), (True,)))
def test_owned_selection_checks_untrusted_key_input(keys: tuple[object, ...]) -> None:
    document = CanonicalDocument({"x": 1})
    with pytest.raises(ValueError):
        document.select(cast(tuple[str, ...], keys))


def test_selected_owned_child_preserves_actual_depth() -> None:
    child = CanonicalDocument({"kept": {"leaf": [1, True]}, "ignored": 0})
    selected = child.select(("kept",))
    assert selected.to_bytes() == b'{"kept":{"leaf":[1,true]}}'
    assert (
        CanonicalDocument({"selected": selected}, children=(selected,)).to_bytes()
        == b'{"selected":{"kept":{"leaf":[1,true]}}}'
    )
