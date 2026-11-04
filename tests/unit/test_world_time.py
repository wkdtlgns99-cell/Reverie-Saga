"""Independent exact accounting examples for mutually exclusive UI clock modes."""

import pytest

from app.world_time import REAL_NS_PER_GAME_SECOND, SlowClock

SECOND = 1_000_000_000


def test_idle_twenty_real_seconds_yields_two_game_seconds() -> None:
    clock = SlowClock(0)
    clock.sample(20 * SECOND)
    assert clock.reserve() == 2
    assert clock.reserve() == 0


def test_partial_idle_is_carried_across_samples() -> None:
    clock = SlowClock(0)
    clock.sample(9 * SECOND)
    assert clock.reserve() == 0
    clock.sample(10 * SECOND - 1)
    assert clock.reserve() == 0
    clock.sample(10 * SECOND)
    assert clock.reserve() == 1
    assert clock.credit_ns == 0


@pytest.mark.parametrize("mode", ["paused", "ai_wait", "action"])
def test_paused_provider_and_action_time_do_not_double_charge_idle(mode: str) -> None:
    clock = SlowClock(0)
    clock.transition(mode, 5 * SECOND)  # type: ignore[arg-type]
    clock.transition("idle", 25 * SECOND)
    clock.sample(30 * SECOND)
    assert clock.reserve() == 1


def test_batches_and_failed_reservation_preserve_exact_credit() -> None:
    clock = SlowClock(0)
    clock.sample(335 * SECOND)
    assert clock.reserve() == 16
    clock.restore(16)
    assert clock.reserve() == 16
    assert clock.reserve() == 16
    assert clock.reserve() == 1
    assert clock.credit_ns == REAL_NS_PER_GAME_SECOND // 2


def test_reversed_and_invalid_samples_preserve_accounting() -> None:
    clock = SlowClock(10)
    with pytest.raises(ValueError, match="WORLD_CLOCK_REVERSED"):
        clock.sample(9)
    with pytest.raises(ValueError, match="WORLD_CLOCK_TIMESTAMP"):
        clock.sample(True)
    assert clock.last_ns == 10 and clock.credit_ns == 0


def test_load_resets_derived_fraction_without_changing_mode() -> None:
    clock = SlowClock(0)
    clock.transition("paused", 5 * SECOND)
    clock.reset(100 * SECOND)
    assert clock.mode == "paused" and clock.credit_ns == 0


@pytest.mark.parametrize("seconds", [0, -1, True, 17])
def test_invalid_clock_reservations(seconds: int) -> None:
    clock = SlowClock(0)
    with pytest.raises(ValueError, match="WORLD_CLOCK_BATCH"):
        clock.reserve(seconds)
    with pytest.raises(ValueError, match="WORLD_CLOCK_BATCH"):
        clock.restore(seconds)
