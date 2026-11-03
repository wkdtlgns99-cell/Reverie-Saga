"""Canonical selection keeps fresh scalar checks,lookup order and exact owned depth."""

from typing import cast
import pytest

from domain.canonical import CanonicalDocument


def nested(depth: int, leaf: object) -> object:
    for _ in range(depth):
        leaf = [leaf]
    return leaf


@pytest.mark.parametrize(
    "keys,expected",
    (((), b"{}"), (("a", "a"), b'{"a":7}'), (("문", "a"), '{"a":7,"문":[true,null]}'.encode())),
)
def test_selection_exact_bytes_and_duplicate_keys(keys: tuple[str, ...], expected: bytes) -> None:
    document = CanonicalDocument({"a": 7, "문": [True, None], "ignored": 9})
    assert document.select(keys).to_bytes() == expected
    assert document.to_bytes() == '{"a":7,"ignored":9,"문":[true,null]}'.encode()


@pytest.mark.parametrize(
    "key,message",
    (
        (1, "JSON object keys must be strings"),
        (True, "JSON object keys must be strings"),
        (None, "JSON object keys must be strings"),
        ("e\u0301", "non-NFC string"),
    ),
)
def test_invalid_selector_rejects_before_lookup(key: object, message: str) -> None:
    with pytest.raises(ValueError) as caught:
        CanonicalDocument({}).select(cast(tuple[str, ...], (key,)))
    assert str(caught.value) == message


def test_surrogate_and_missing_selector_error_order_and_identity() -> None:
    document = CanonicalDocument({"a": 0})
    with pytest.raises(UnicodeEncodeError) as caught:
        document.select(("\ud800",))
    assert caught.value.encoding == "utf-8" and caught.value.reason == "surrogates not allowed"

    class Missing(str):
        pass

    missing = Missing("missing")
    with pytest.raises(KeyError) as absent:
        document.select((missing, "e\u0301"))
    assert absent.value.args[0] is missing
    with pytest.raises(ValueError, match="^non-NFC string$"):
        document.select(("e\u0301", missing))


def test_subclass_validation_is_fresh_and_precedes_hash_lookup() -> None:
    calls: list[str] = []

    class Selector(str):
        fail = False

        def isascii(self) -> bool:
            raise AssertionError("a subclass is not an exact ASCII proof")

        def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
            calls.append("encode")
            if self.fail:
                raise ValueError("fresh-selector-failure")
            return super().encode(encoding, errors)

        def __hash__(self) -> int:
            calls.append("lookup")
            return super().__hash__()

    document = CanonicalDocument({"a": 1})
    key = Selector("a")
    assert document.select((key,)).to_bytes() == b'{"a":1}'
    assert calls[0] == "encode" and "lookup" in calls
    calls.clear()
    key.fail = True
    with pytest.raises(ValueError, match="^fresh-selector-failure$"):
        document.select((key,))
    assert calls == ["encode"]


def test_selection_keeps_owned_aliases_and_exact_subtree_depth() -> None:
    values: list[object] = [True, {"v": 1}]
    source: dict[str, object] = {"keep": values, "deep": nested(31, 0)}
    document = CanonicalDocument(source)
    selected = document.select(("keep",))
    values.append("later")
    source["keep"] = None
    assert selected.to_bytes() == b'{"keep":[true,{"v":1}]}'
    shallow = CanonicalDocument({"keep": 0, "deep": nested(31, 0)}).select(("keep",))
    assert (
        CanonicalDocument(nested(31, shallow), children=(shallow,)).to_bytes()
        == b"[" * 31 + b'{"keep":0}' + b"]" * 31
    )
    with pytest.raises(ValueError, match="^JSON nesting exceeds32$"):
        CanonicalDocument(nested(32, shallow), children=(shallow,))


def test_ascii_controls_and_unicode_selectors_keep_literal_encoding() -> None:
    document = CanonicalDocument({"\x00\n": 7, "é": "문"})
    assert document.select(("\x00\n",)).to_bytes() == b'{"\\u0000\\n":7}'
    assert document.select(("é",)).to_bytes() == '{"é":"문"}'.encode()
