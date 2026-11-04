"""UI clock accounting;real-time samples never enter deterministic engines directly."""

from typing import Literal

type ClockMode = Literal["idle", "action", "ai_wait", "paused"]
REAL_NS_PER_GAME_SECOND = 10_000_000_000


class SlowClock:
    def __init__(self, now_ns: int) -> None:
        self._timestamp(now_ns)
        self.last_ns = now_ns
        self.mode: ClockMode = "idle"
        self.credit_ns = 0

    @staticmethod
    def _timestamp(value: int) -> None:
        if type(value) is not int or value < 0:
            raise ValueError("WORLD_CLOCK_TIMESTAMP")

    def sample(self, now_ns: int) -> None:
        self._timestamp(now_ns)
        if now_ns < self.last_ns:
            raise ValueError("WORLD_CLOCK_REVERSED")
        if self.mode == "idle":
            self.credit_ns += now_ns - self.last_ns
        self.last_ns = now_ns

    def transition(self, mode: ClockMode, now_ns: int) -> None:
        if type(mode) is not str or mode not in ("idle", "action", "ai_wait", "paused"):
            raise ValueError("WORLD_CLOCK_MODE")
        self.sample(now_ns)
        self.mode = mode

    def reserve(self, maximum: int = 16) -> int:
        if type(maximum) is not int or not 1 <= maximum <= 16:
            raise ValueError("WORLD_CLOCK_BATCH")
        seconds = min(maximum, self.credit_ns // REAL_NS_PER_GAME_SECOND)
        self.credit_ns -= seconds * REAL_NS_PER_GAME_SECOND
        return seconds

    def restore(self, seconds: int) -> None:
        if type(seconds) is not int or not 1 <= seconds <= 16:
            raise ValueError("WORLD_CLOCK_BATCH")
        self.credit_ns += seconds * REAL_NS_PER_GAME_SECOND

    def reset(self, now_ns: int) -> None:
        self._timestamp(now_ns)
        self.last_ns = now_ns
        self.credit_ns = 0
