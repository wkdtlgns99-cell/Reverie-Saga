from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import replace
from typing import cast

import pytest

from contracts.errors import (
    ExpiredReadView, InvalidViewEpoch, ReadOnlyViolation, UnknownComponent,
    UnknownEntity, ViewAlreadyClosed, ViewAlreadyOpen,
)
from contracts.read_views import ComponentKey, MappingPath, SequencePath
from domain.primitives import EntityId, Phase, Tick
from tests.unit.view_fixtures import ACTOR, PHYSIOLOGY, PROFILE, PhysiologyRead, fixture


def test_operation_order() -> None:
    f, epoch, _ = fixture()
    port = f.open(epoch)
    p = port.component(PHYSIOLOGY, ACTOR)
    assert p.hp == 10
    r = p.reserves
    assert r["food"] == 7
    assert len(r) == 1
    assert "food" in r
    observations = f.close(epoch)
    assert [(o.target.family.field, o.path, o.operation) for o in observations] == [
        ("hp", (), "read"), ("reserves", (), "read"),
        ("reserves", (MappingPath("food"),), "read"),
        ("reserves", (), "length"), ("reserves", (MappingPath("food"),), "membership"),
    ]


def test_nested_mutation_preserves_backing() -> None:
    f, epoch, root = fixture()
    port = f.open(epoch)
    p = port.component(PHYSIOLOGY, ACTOR)
    r = p.reserves
    traits = port.component(PROFILE, ACTOR).traits
    with pytest.raises(ReadOnlyViolation):
        setattr(p, "hp", 0)
    with pytest.raises(ReadOnlyViolation):
        cast(MutableMapping[str, int], r)["food"] = 0
    with pytest.raises(ReadOnlyViolation):
        del cast(MutableMapping[str, int], r)["food"]
    with pytest.raises(ReadOnlyViolation):
        getattr(traits, "append")
    with pytest.raises(ReadOnlyViolation):
        getattr(r, "clear")
    assert p.hp == 10 and r["food"] == 7
    assert root == fixture()[2]
    assert len([o for o in f.close(epoch) if o.operation == "write"]) == 5


def test_cache_repeated_reads() -> None:
    f, epoch, _ = fixture()
    p = f.open(epoch).component(PHYSIOLOGY, ACTOR)
    assert p.reserves is p.reserves
    assert [o.operation for o in f.close(epoch)] == ["read", "read"]


def test_expired_aliases() -> None:
    f, epoch, _ = fixture()
    port = f.open(epoch)
    profile = port.component(PROFILE, ACTOR)
    traits = profile.traits
    sliced = traits[::-1]
    iterator = iter(traits)
    observations = f.close(epoch)
    for operation in (lambda: profile.traits, lambda: traits[0], lambda: sliced[0],
                      lambda: next(iterator), lambda: port.component(PROFILE, ACTOR)):
        with pytest.raises(ExpiredReadView):
            operation()
    assert observations[-1].operation == "iteration"


def test_epoch_errors() -> None:
    f, epoch, _ = fixture()
    with pytest.raises(InvalidViewEpoch):
        f.close(epoch)
    for bad in (replace(epoch, root_token=2), replace(epoch, wave=1),
                replace(epoch, phase=Phase.COMMIT), replace(epoch, logical_tick=cast(Tick, True))):
        with pytest.raises(InvalidViewEpoch):
            f.open(bad)
    f.open(epoch)
    with pytest.raises(ViewAlreadyOpen):
        f.open(epoch)
    f.close(epoch)
    with pytest.raises(ViewAlreadyClosed):
        f.close(epoch)
    with pytest.raises(ViewAlreadyClosed):
        f.open(epoch)


def test_missing_key_index() -> None:
    f, epoch, _ = fixture()
    port = f.open(epoch)
    r = port.component(PHYSIOLOGY, ACTOR).reserves
    t = port.component(PROFILE, ACTOR).traits
    with pytest.raises(KeyError):
        r["missing"]
    assert t[-1] == "alert"
    with pytest.raises(IndexError):
        t[2]
    with pytest.raises(TypeError):
        t[True]
    with pytest.raises(ValueError):
        t[::0]
    assert t[::-1][0] == "alert"
    observations = f.close(epoch)
    assert observations[-1].path == (SequencePath(1),)
    assert any(o.path == (MappingPath("missing"),) for o in observations)


def test_forged_key() -> None:
    f, epoch, _ = fixture()
    port = f.open(epoch)
    with pytest.raises(UnknownComponent):
        port.component(ComponentKey[PhysiologyRead](PHYSIOLOGY.schema), ACTOR)
    with pytest.raises(UnknownEntity):
        port.component(PHYSIOLOGY, EntityId("actor:missing"))
    f.close(epoch)


def test_factory_isolation() -> None:
    f, epoch, _ = fixture()
    g, other, _ = fixture()
    a = f.open(epoch).component(PROFILE, ACTOR).traits
    b = g.open(other).component(PROFILE, ACTOR).traits
    assert a is not b
    f.close(epoch)
    assert b[0] == "quiet"
    g.close(other)


def test_empty_and_collection_caps() -> None:
    f, epoch, _ = fixture((), ())
    port = f.open(epoch)
    assert len(port.component(PROFILE, ACTOR).traits) == 0
    assert list(port.component(PHYSIOLOGY, ACTOR).reserves) == []
    f.close(epoch)
    fixture(tuple("x" for _ in range(64)))
    with pytest.raises(ValueError):
        fixture(tuple("x" for _ in range(65)))
    with pytest.raises(ValueError):
        fixture(reserves=(("food", 7), ("food", 8)))
