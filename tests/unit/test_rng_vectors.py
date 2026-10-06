from __future__ import annotations

import hashlib
from typing import cast

import pytest

from app.feature_registry import rng_purposes
from contracts.errors import RngCounterExhausted, RngError
from domain.canonical import array_value, int_value, object_value, text_value
from domain.primitives import EntityId, Phase, Tick
from orchestration.rng import CounterRngService, _Stream
from tests.unit.test_canonical import vectors


def _service() -> CounterRngService:
    header = object_value(object_value(object_value(vectors()["golden_fixture"])["trace"])["header"])
    return CounterRngService(text_value(header["world_seed_hex"]), text_value(header["world_id"]), rng_purposes())


def test_independent_rng_vectors() -> None:
    for item in array_value(vectors()["rng_vectors"]):
        v = object_value(item)
        a = object_value(v["address"])
        scope = _service().scoped(Tick(int_value(a["logical_tick"])), Phase[text_value(a["phase"])],
                                  int_value(a["wave"]), text_value(a["engine_id"]))
        stream = scope.stream(EntityId(text_value(a["entity_id"])), text_value(a["purpose"]), text_value(a["causal_key"]))
        assert isinstance(stream, _Stream)
        assert stream._key.hex() == v["key_sha256"]
        assert hashlib.sha256(bytes.fromhex(text_value(v["pack_hex"]))).digest() == stream._key
        assert tuple(stream.draw_bounded(int_value(v["low"]), int_value(v["high_exclusive"])) for _ in range(4)) == v["draws"]
        assert stream._counter == v["consumed_counters"]
        for attempt in array_value(v["attempts"]):
            d = object_value(attempt)
            counter = int_value(d["counter"])
            assert int.from_bytes(hashlib.sha256(stream._key + counter.to_bytes(8, "big")).digest()[:8], "big") == d["u"]


def test_scope_cache_and_address_isolation() -> None:
    service = _service()
    scope = service.scoped(Tick(1), Phase.RESOLVE, 0, "skeleton.stepper")
    first = scope.stream(EntityId("actor:toy"), "toy.sample", "auto:test")
    assert first is scope.stream(EntityId("actor:toy"), "toy.sample", "auto:test")
    other_entity = scope.stream(EntityId("actor:other"), "toy.sample", "auto:test")
    other_purpose = scope.stream(EntityId("actor:toy"), "test.reject", "auto:test")
    fresh = service.scoped(Tick(1), Phase.RESOLVE, 0, "skeleton.stepper").stream(EntityId("actor:toy"), "toy.sample", "auto:test")
    assert isinstance(first, _Stream) and isinstance(other_entity, _Stream) and isinstance(other_purpose, _Stream)
    assert len({first._key, other_entity._key, other_purpose._key}) == 3
    assert first is not fresh
    assert first.draw_bounded(0, 2**64) == fresh.draw_bounded(0, 2**64)
    assert other_purpose._counter == other_entity._counter == 0


def test_range_address_validation_and_counter_exhaustion() -> None:
    stream = _service().scoped(Tick(1), Phase.RESOLVE, 0, "skeleton.stepper").stream(EntityId("actor:toy"), "toy.sample", "auto:test")
    assert isinstance(stream, _Stream)
    for low, high in ((1, 1), (2, 1), (0, 2**64 + 1), (cast(int, True), 2)):
        with pytest.raises(RngError):
            stream.draw_bounded(low, high)
    assert stream._counter == 0
    stream._counter = 2**64 - 1
    stream.draw_bounded(-2**100, -2**100 + 2**64)
    assert stream._counter == 2**64
    with pytest.raises(RngCounterExhausted):
        stream.draw_bounded(0, 1)
    for phase, wave in ((Phase.VALIDATE, 0), (Phase.PRESENT, 0), (Phase.COMMIT, 0), (Phase.CASCADE, 8), (Phase.RESOLVE, 1)):
        with pytest.raises(RngError):
            _service().scoped(Tick(1), phase, wave, "skeleton.stepper")
    _service().scoped(Tick(1), Phase.CASCADE, 7, "skeleton.stepper")
    for entity, purpose, causal in (("BAD", "toy.sample", "auto:x"), ("actor:toy", "unregistered", "auto:x"), ("actor:toy", "toy.sample", "raw-command-id")):
        with pytest.raises(RngError):
            _service().scoped(Tick(1), Phase.RESOLVE, 0, "skeleton.stepper").stream(EntityId(entity), purpose, causal)
    with pytest.raises(RngError):
        CounterRngService("0" * 64, "w1-" + "0" * 64, (("x", ("p", "p")),))
