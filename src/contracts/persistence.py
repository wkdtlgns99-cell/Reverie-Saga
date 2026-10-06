from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from contracts.replay import ReplayTrace
from contracts.turn import CommitReceipt, GameCommand, ProtocolSnapshot, TurnPublication
from domain.state_types import CoreSnapshot


class SaveError(RuntimeError):
    def __init__(self, code: str, detail: str) -> None:
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")


class SaveUnavailable(SaveError):
    """The attempted commit is confirmed absent."""


class CommitUncertain(SaveError):
    """Durability must be resolved before exposing an outcome."""


class WorldUnavailable(SaveError):
    """This attachment cannot admit commands."""


@dataclass(frozen=True, slots=True)
class DurableCheckpoint:
    core: CoreSnapshot
    protocol: ProtocolSnapshot


@dataclass(frozen=True, slots=True)
class DurableTurn:
    previous: DurableCheckpoint
    next: DurableCheckpoint
    command: GameCommand
    publication: TurnPublication


@dataclass(frozen=True, slots=True)
class RecoveryCommitted:
    checkpoint: DurableCheckpoint
    receipt: CommitReceipt


@dataclass(frozen=True, slots=True)
class RecoveryAbsent:
    checkpoint: DurableCheckpoint


type RecoveryResult = RecoveryCommitted | RecoveryAbsent


@dataclass(frozen=True, slots=True)
class SaveSegment:
    checkpoint: DurableCheckpoint
    trace: ReplayTrace


@dataclass(frozen=True, slots=True)
class SaveExportReceipt:
    slot_id: str
    revision: int
    core_hash: str
    protocol_hash: str
    file_sha256: str
    directory_synced: bool


@dataclass(frozen=True, slots=True)
class SaveLoadReceipt:
    slot_id: str
    revision: int
    core_hash: str
    protocol_hash: str
    attachment_id: str


class DurableCommitPort(Protocol):
    def persist(self, turn: DurableTurn) -> CommitReceipt: ...
    def recover(self, turn: DurableTurn) -> RecoveryResult: ...
