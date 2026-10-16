"""Durable usage accounting and cross-process spacing;no local daily quota."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import os
import sys
from pathlib import Path
import time
from typing import BinaryIO, Iterator

from contracts.dialogue import GenerationError
from domain.canonical import (
    array_value,
    canonical_json,
    decode_json,
    exact_fields,
    int_value,
    text_value,
)
from domain.primitives import require_integer

CALL_RESERVATION = 20000
SPACING_MS = 60000
MAX_LEDGER_BYTES = 16384


@dataclass(frozen=True, slots=True)
class Reservation:
    day: str
    number: int

    def __post_init__(self) -> None:
        if type(self.day) is not str:
            raise ValueError("budget reservation day")
        datetime.strptime(self.day, "%Y-%m-%d")
        require_integer(self.number, 1)


def _lock(handle: BinaryIO, release: bool = False) -> None:
    handle.seek(0)
    if sys.platform == "win32":
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK if release else msvcrt.LK_NBLCK, 1)
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN if release else fcntl.LOCK_EX | fcntl.LOCK_NB)


class GenerationBudget:
    def __init__(self, profile: Path) -> None:
        self.profile = profile

    @contextmanager
    def locked(self) -> Iterator[None]:
        try:
            self.profile.mkdir(parents=True, exist_ok=True)
            handle = (self.profile / "budget.lock").open("a+b")
        except OSError as error:
            raise GenerationError("GENERATION_BUDGET_UNAVAILABLE") from error
        acquired = False
        try:
            if handle.seek(0, 2) == 0:
                handle.write(b"0")
                handle.flush()
            try:
                _lock(handle)
                acquired = True
            except OSError as error:
                raise GenerationError("GENERATION_BUDGET_UNAVAILABLE") from error
            yield
        finally:
            try:
                if acquired:
                    _lock(handle, release=True)
            finally:
                handle.close()

    def _read(self, day: str) -> tuple[str, int, int, int, tuple[int, ...]]:
        path = self.profile / "budget.json"
        try:
            with path.open("rb") as source:
                raw = source.read(MAX_LEDGER_BYTES + 1)
        except FileNotFoundError:
            return day, 0, 0, 0, ()
        if len(raw) > MAX_LEDGER_BYTES:
            raise ValueError("budget capacity")
        data = exact_fields(decode_json(raw), ("day", "attempts", "tokens", "next_ms", "settled"))
        stamp = text_value(data["day"])
        datetime.strptime(stamp, "%Y-%m-%d")
        values = tuple(int_value(data[name]) for name in ("attempts", "tokens", "next_ms"))
        for value in values:
            require_integer(value)
        settled = tuple(int_value(v) for v in array_value(data["settled"]))
        if settled != tuple(sorted(set(settled))) or any(
            not 1 <= value <= values[0] for value in settled
        ):
            raise ValueError("budget settlement")
        # A UTC day rollover never resets the cross-day minimum interval.
        return (
            (day, 0, 0, values[2], ())
            if stamp < day
            else (stamp, values[0], values[1], values[2], settled)
        )

    def _write(
        self, day: str, attempts: int, tokens: int, next_ms: int, settled: tuple[int, ...]
    ) -> None:
        path = self.profile / "budget.json"
        pending = path.with_suffix(".pending")
        # Callers hold the exclusive profile lock. A crashed writer's unpublished sibling
        # cannot be authoritative;keep committed budget.json and remove only this owned path.
        pending.unlink(missing_ok=True)
        owned = False
        try:
            with pending.open("xb") as target:
                owned = True
                target.write(
                    canonical_json(
                        {
                            "day": day,
                            "attempts": attempts,
                            "tokens": tokens,
                            "next_ms": next_ms,
                            "settled": settled,
                        }
                    )
                )
                target.flush()
                os.fsync(target.fileno())
            pending.replace(path)
        finally:
            if owned:
                pending.unlink(missing_ok=True)

    def reserve(self, *, now_ms: int | None = None) -> Reservation:
        instant = int(time.time() * 1000) if now_ms is None else now_ms
        require_integer(instant)
        day = datetime.fromtimestamp(instant / 1000, timezone.utc).strftime("%Y-%m-%d")
        try:
            with self.locked():
                stamp, attempts, tokens, next_ms, settled = self._read(day)
                if stamp > day or instant < next_ms:
                    raise GenerationError("GENERATION_DEFERRED")
                self._write(
                    day, attempts + 1, tokens + CALL_RESERVATION, instant + SPACING_MS, settled
                )
                return Reservation(day, attempts + 1)
        except (OSError, ValueError, UnicodeError) as error:
            if isinstance(error, GenerationError):
                raise
            raise GenerationError("GENERATION_BUDGET_UNAVAILABLE") from error

    def reconcile(self, reservation: Reservation, actual_tokens: int | None) -> None:
        if actual_tokens is None:
            return  # Unknown consumption keeps the full conservative reservation.
        require_integer(actual_tokens)
        try:
            with self.locked():
                day, attempts, tokens, next_ms, settled = self._read(reservation.day)
                if day != reservation.day or reservation.number > attempts:
                    raise GenerationError("GENERATION_BUDGET_UNAVAILABLE")
                if reservation.number in settled:
                    return
                self._write(
                    day,
                    attempts,
                    tokens - CALL_RESERVATION + actual_tokens,
                    next_ms,
                    tuple(sorted((*settled, reservation.number))),
                )
        except (OSError, ValueError, UnicodeError) as error:
            if isinstance(error, GenerationError):
                raise
            raise GenerationError("GENERATION_BUDGET_UNAVAILABLE") from error
