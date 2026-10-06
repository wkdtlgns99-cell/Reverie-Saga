from __future__ import annotations

import hashlib
import re

from contracts.errors import RngCounterExhausted, RngError
from contracts.replay import RngAddress
from contracts.turn import EngineRng, RandomStream
from domain.canonical import pack
from domain.primitives import EntityId, Phase, Tick, require_integer, require_namespace


class _Stream:
    def __init__(self, key: bytes) -> None:
        self._key = key
        self._counter = 0

    def draw_bounded(self, low: int, high_exclusive: int) -> int:
        if type(low) is not int or type(high_exclusive) is not int:
            raise RngError("integer interval required")
        span = high_exclusive - low
        if not 1 <= span <= 2**64:
            raise RngError("interval span outside1..2^64")
        limit = 2**64 - (2**64 % span)
        while True:
            if self._counter >= 2**64:
                raise RngCounterExhausted("unsigned64 cursor exhausted")
            word = hashlib.sha256(self._key + self._counter.to_bytes(8, "big")).digest()[:8]
            self._counter += 1
            unsigned = int.from_bytes(word, "big")
            if unsigned < limit:
                return low + unsigned % span


class _Scope:
    def __init__(self, seed_hex: str, world_id: str, tick: Tick, phase: Phase, wave: int,
                 engine_id: str, purposes: frozenset[str]) -> None:
        self._seed_hex, self._world_id = seed_hex, world_id
        self._tick, self._phase, self._wave, self._engine_id = tick, phase, wave, engine_id
        self._purposes = purposes
        self._streams: dict[RngAddress, _Stream] = {}

    def stream(self, entity_id: EntityId, purpose: str, causal_key: str) -> RandomStream:
        try:
            require_namespace(entity_id)
            require_namespace(purpose)
            if purpose not in self._purposes:
                raise ValueError("unregistered purpose")
            if re.fullmatch("[ae]1-[0-9a-f]{64}", causal_key) is None:
                if not causal_key.startswith("auto:"):
                    raise ValueError("invalid causal key")
                require_namespace(causal_key[5:])
        except (ValueError, TypeError) as error:
            raise RngError(str(error)) from error
        address = RngAddress(self._tick, self._phase, self._wave, self._engine_id,
                             entity_id, purpose, causal_key)
        if address not in self._streams:
            tokens = ("rng-key/v1", self._seed_hex, self._world_id, str(address.logical_tick),
                      address.phase.name, str(address.wave), address.engine_id, address.entity_id,
                      address.purpose, address.causal_key)
            self._streams[address] = _Stream(hashlib.sha256(pack(tokens)).digest())
        return self._streams[address]


class CounterRngService:
    def __init__(self, seed_hex: str, world_id: str,
                 purposes: tuple[tuple[str, tuple[str, ...]], ...]) -> None:
        if re.fullmatch("[0-9a-f]{64}", seed_hex) is None or re.fullmatch("w1-[0-9a-f]{64}", world_id) is None:
            raise RngError("invalid seed/world identity")
        self._purposes: dict[str, frozenset[str]] = {}
        try:
            for engine, names in purposes:
                require_namespace(engine)
                for name in names:
                    require_namespace(name)
                if engine in self._purposes or len(names) != len(set(names)):
                    raise ValueError("duplicate RNG registration")
                self._purposes[engine] = frozenset(names)
        except (ValueError, TypeError) as error:
            raise RngError(str(error)) from error
        self._seed_hex, self._world_id = seed_hex, world_id

    def scoped(self, tick: Tick, phase: Phase, wave: int, engine_id: str) -> EngineRng:
        try:
            require_integer(tick)
            if not isinstance(phase, Phase) or phase not in (
                Phase.PRE_TICK, Phase.RESOLVE, Phase.REACT, Phase.CASCADE, Phase.POST_TICK
            ):
                raise ValueError("invalid RNG phase")
            require_integer(wave, maximum=7 if phase is Phase.CASCADE else 0)
            require_namespace(engine_id)
        except (ValueError, TypeError) as error:
            raise RngError(str(error)) from error
        return _Scope(self._seed_hex, self._world_id, tick, phase, wave, engine_id,
                      self._purposes.get(engine_id, frozenset()))
