"""Literal fast handling must retain recursive ownership,Unicode and depth boundaries."""

from dataclasses import dataclass
from types import MappingProxyType

import pytest

from orchestration.serialization import _immutable


class IntChild(int):
    pass


class StrChild(str):
    pass


@dataclass(frozen=True, slots=True)
class FrozenRow:
    prefix: tuple[object, ...]
    child: object


@dataclass
class MutableRow:
    value: int


def nested(levels: int, leaf: object) -> object:
    for _ in range(levels):
        leaf = (leaf,)
    return leaf


@pytest.mark.parametrize(
    "value", (None, False, True, 0, -1, 2**200, "문", (), MappingProxyType({}))
)
def test_supported_literals_and_empty_immutable_containers(value: object) -> None:
    _immutable(value)
    _immutable(FrozenRow((None, False, 0), value))


@pytest.mark.parametrize("leaf", (None, False, 0, "문", (), MappingProxyType({})))
def test_depth32_accepts_and33_rejects_before_leaf_handling(leaf: object) -> None:
    _immutable(nested(32, leaf))
    with pytest.raises(ValueError, match="^record nesting exceeds32$"):
        _immutable(nested(33, leaf))


@pytest.mark.parametrize(
    "bad",
    (
        [],
        {},
        set(),
        bytearray(b"x"),
        b"x",
        object(),
        1.0,
        IntChild(1),
        StrChild("문"),
        MutableRow(1),
    ),
)
def test_literal_prefix_never_hides_mutable_or_unsupported_sibling(bad: object) -> None:
    row = FrozenRow((None, True, False, 0, -1, 2**200), bad)
    with pytest.raises(ValueError, match="^mutable or unsupported record child$"):
        _immutable(row)
    _immutable(FrozenRow(row.prefix, (1, "문")))


@pytest.mark.parametrize("key", (False, True))
@pytest.mark.parametrize("bad", ("e\u0301", "\ud800"))
def test_unicode_values_and_mapping_keys_still_validate(key: bool, bad: str) -> None:
    value: object = MappingProxyType({bad: 0}) if key else FrozenRow((None, True, 0), bad)
    error = UnicodeEncodeError if bad == "\ud800" else ValueError
    with pytest.raises(error) as caught:
        _immutable(value)
    if bad != "\ud800":
        assert str(caught.value) == "non-NFC string"


def test_mapping_key_error_keeps_precedence_over_deeper_child() -> None:
    with pytest.raises(ValueError, match="^non-NFC string$"):
        _immutable(nested(32, MappingProxyType({"e\u0301": None})))
    with pytest.raises(ValueError, match="^record nesting exceeds32$"):
        _immutable(nested(32, MappingProxyType({"valid": None})))


def test_mapping_values_are_rechecked_after_previous_valid_input() -> None:
    backing: dict[str, object] = {"value": (0, None, "문")}
    row = FrozenRow((False, 0), MappingProxyType(backing))
    _immutable(row)
    backing["value"] = []
    with pytest.raises(ValueError, match="^mutable or unsupported record child$"):
        _immutable(row)


class PretendIntType(type):
    def __eq__(self, other: object) -> bool:
        return other is int

    __hash__ = type.__hash__


class PretendStrType(type):
    def __eq__(self, other: object) -> bool:
        return other is str

    __hash__ = type.__hash__


class PretendInt(metaclass=PretendIntType):
    pass


@dataclass(frozen=True, slots=True)
class PretendFrozenInt(metaclass=PretendIntType):
    value: int


@dataclass(frozen=True, slots=True)
class PretendFrozenStr(metaclass=PretendStrType):
    value: int


@pytest.mark.parametrize("value", (PretendInt(), PretendFrozenInt(0), PretendFrozenStr(0)))
def test_type_equality_cannot_bypass_original_canonical_rejection(value: object) -> None:
    with pytest.raises(ValueError, match="^unsupported canonical value$"):
        _immutable(value)
