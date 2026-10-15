"""Map player intent onto the existing authoritative durable game, without new rules."""

from __future__ import annotations

from domain.scenario import LEGACY_SCENARIO, Scenario, require_scenario

from pathlib import Path

from app.client_text import status_text, turn_messages
from app.durable import DurableSession, create_durable, resume_durable
from app.watch import WatchBootstrapSpec, bootstrap_watch
from app.watch_registry import watch_bundle
from contracts.client import ClientAction, ClientUpdate, ClientView
from contracts.encounter import AttackCommand, InteractCommand, RestCommand
from contracts.messages import CommandPayload
from contracts.persistence import DurableCheckpoint
from contracts.trial import MoveCommand
from contracts.turn import GameCommand, TurnCommitted, TurnPublication
from contracts.watch import BellCommand, WaitCommand
from domain.encounter import (
    ATTACK_PROFILE_ID,
    GateRecord,
    HitPointsRecord,
    StaminaRecord,
)
from domain.primitives import CommandId, EntityId
from domain.state_types import ComponentRecord, CoreSnapshot
from domain.trial import CellPositionRecord, TrialMapRecord
from domain.watch import LanternRecord, ReplyRecord, WatchNpcRecord


def _record[T: ComponentRecord](core: CoreSnapshot, kind: type[T], entity: EntityId) -> T:
    records = tuple(r for r in core.components if isinstance(r, kind) and r.entity_id == entity)
    if len(records) != 1:
        raise ValueError(f"client projection requires one {kind.__name__} for {entity}")
    return records[0]


def _payload(
    action: ClientAction, seconds: int, scenario: Scenario = LEGACY_SCENARIO
) -> CommandPayload:
    match action:
        case "up":
            return MoveCommand(0, -1)
        case "down":
            return MoveCommand(0, 1)
        case "left":
            return MoveCommand(-1, 0)
        case "right":
            return MoveCommand(1, 0)
        case "open" | "close":
            return InteractCommand(scenario.gate_id, action)
        case "attack":
            return AttackCommand(scenario.enemy_id, ATTACK_PROFILE_ID)
        case "rest":
            return RestCommand()
        case "wait":
            return WaitCommand(seconds)
        case "bell":
            return BellCommand(scenario.npc_id)
        case _:
            raise ValueError("UNKNOWN_CLIENT_ACTION")


class ClientSession:
    """All calls, including construction and close, belong to one owner thread."""

    def __init__(self, path: Path, *, scenario: Scenario = LEGACY_SCENARIO) -> None:
        require_scenario(scenario)
        self._scenario = scenario
        bundles = (watch_bundle(scenario),)
        if path.exists():
            self._owner = resume_durable(path, bundles=bundles)
        else:
            initial = bootstrap_watch(
                WatchBootstrapSpec(
                    "0" * 64, "0" * 32, "1" * 32, initial_cell=scenario.initial_cell
                ),
                scenario=scenario,
            )
            self._owner = create_durable(
                path, DurableCheckpoint(initial.snapshot(), initial.protocol()), bundles=bundles
            )
        self._previous: tuple[GameCommand, str] | None = None

    @property
    def owner(self) -> DurableSession:
        """Authoritative API for boundary tests;renderers receive only derived updates."""
        return self._owner

    def update(
        self,
        status: str = "ATTACHED",
        notices: tuple[str, ...] = (),
        *,
        messages: tuple[str, ...] = (),
        reset_log: bool = False,
    ) -> ClientUpdate:
        core = self._owner.snapshot()
        board = _record(core, TrialMapRecord, self._scenario.space_id)
        gate = _record(core, GateRecord, self._scenario.gate_id)
        npc = _record(core, WatchNpcRecord, self._scenario.npc_id)
        view = ClientView(
            board.width,
            board.height,
            board.blocked_cells,
            _record(core, CellPositionRecord, self._scenario.actor_id).cell,
            gate.cell,
            bool(gate.is_open),
            _record(core, CellPositionRecord, self._scenario.enemy_id).cell,
            _record(core, HitPointsRecord, self._scenario.actor_id).hp,
            _record(core, HitPointsRecord, self._scenario.enemy_id).hp,
            _record(core, StaminaRecord, self._scenario.actor_id).value,
            npc.cell,
            npc.bells,
            _record(core, ReplyRecord, self._scenario.npc_id).count,
            _record(core, LanternRecord, self._scenario.lantern_id).charge,
            core.tick,
            self._owner.protocol().revision,
        )
        return ClientUpdate(
            view,
            status,
            notices,
            self._owner.attachment_id,
            str(self._owner.working_path),
            messages or ((status_text(status),) if status == "ATTACHED" else ()),
            reset_log,
        )

    def _publication(
        self,
        publication: TurnPublication,
        *,
        wait_seconds: int | None = None,
    ) -> ClientUpdate:
        outcome = publication.outcome
        status = "COMMITTED" if isinstance(outcome, TurnCommitted) else outcome.failure.code
        notices = tuple(c.payload.schema.kind for c in publication.cues) + tuple(
            diagnostic.code for diagnostic in publication.diagnostics
        )
        return self.update(
            status,
            notices,
            messages=turn_messages(publication, wait_seconds=wait_seconds, scenario=self._scenario),
        )

    def act(self, action: ClientAction, *, seconds: int = 1) -> ClientUpdate:
        protocol = self._owner.protocol()
        streams = tuple(
            s
            for s in protocol.streams
            if s.status == "active" and s.actor_id == self._scenario.actor_id
        )
        if len(streams) != 1:
            raise ValueError("CLIENT_ACTIVE_STREAM")
        stream = streams[0]
        identifier = CommandId(
            f"c1:{protocol.branch_id}:{stream.stream_id}:{stream.highest_committed_sequence + 1}"
        )
        command = GameCommand(
            identifier,
            self._scenario.actor_id,
            protocol.revision,
            _payload(action, seconds, self._scenario),
        )
        token = self._owner.attachment_id
        self._previous = command, token
        before_tick = self._owner.snapshot().tick
        publication = self._owner.submit(command, attachment_id=token)
        waited = self._owner.snapshot().tick - before_tick if action == "wait" else None
        return self._publication(publication, wait_seconds=waited)

    def retry(self) -> ClientUpdate:
        if self._previous is None:
            raise ValueError("NO_RETRY")
        command, token = self._previous
        return self._publication(self._owner.submit(command, attachment_id=token))

    def save(self, slot_id: str) -> ClientUpdate:
        receipt = self._owner.export(slot_id)
        return self.update(
            "SAVED",
            (receipt.slot_id,),
            messages=(f"{receipt.slot_id}에 진행 상황을 저장했습니다.",),
        )

    def load(self, slot_id: str) -> ClientUpdate:
        receipt = self._owner.load(slot_id)
        self._previous = None  # A prior request must never silently migrate to the new attachment.
        return self.update(
            "LOADED",
            (receipt.slot_id,),
            reset_log=True,
            messages=(
                f"{receipt.slot_id}을 불러왔습니다. 이후 표시 기록을 초기화했습니다.",
                "별도 진행 파일에서 이어갑니다. 현재 진행 파일 경로를 확인하세요.",
            ),
        )

    def recover(self) -> ClientUpdate:
        return self._publication(self._owner.recover())

    def close(self) -> None:
        self._owner.close()
