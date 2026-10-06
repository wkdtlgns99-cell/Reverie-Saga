from __future__ import annotations

class ReadViewError(RuntimeError):
    """A view operation failed without mutating sealed state."""


class ReadOnlyViolation(ReadViewError):
    """Attempted mutation of an observed view."""


class ExpiredReadView(ReadViewError):
    """The invocation owning this alias has closed."""


class UnknownComponent(ReadViewError):
    """The exact typed key was not registered."""


class UnknownEntity(ReadViewError):
    """The component is absent for this entity."""


class InvalidViewEpoch(ReadViewError):
    """Invalid lifecycle, owner or root pin."""


class ViewAlreadyOpen(ReadViewError):
    """An epoch is already active."""


class ViewAlreadyClosed(ReadViewError):
    """A closed epoch cannot be closed or opened again."""


class BootstrapError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")


class SchemaError(ValueError):
    def __init__(self, code: str, path: str) -> None:
        self.code, self.path = code, path
        super().__init__(f"{code}: {path}")


class CandidateError(RuntimeError):
    def __init__(self, code: str, detail: str) -> None:
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")


class RngUnavailable(RuntimeError):
    """RS-P0-003 RNG implementation is not installed."""


class ReplayFormatError(ValueError):
    """Invalid replay/checkpoint/pin/witness before execution."""


class RngError(ValueError):
    """Invalid deterministic RNG address or interval."""


class RngCounterExhausted(RuntimeError):
    """No remaining unsigned64 counter in this stream."""
