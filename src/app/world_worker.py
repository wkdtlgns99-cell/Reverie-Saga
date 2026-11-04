"""Single-thread world-session ownership for nonblocking Tk commands and saves."""

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
import logging
from typing import Literal

from adapters.world_attachment import current_world, remember_world
from app.durable import DurableSession
from app.world_session import foot_command, open_world_session, world_command
from contracts.persistence import SaveError
from contracts.world_time import WorldWait
from contracts.turn import GameCommand, TurnCommitted, TurnRejected
from domain.world import WorldCatalog
from domain.world_travel import TravelState, TravelerRecord
from domain.world_population import (
    InventoryRecord,
    InventoryState,
    ResidentActivity,
    SettlementRecord,
    resident_activity,
)


@dataclass(frozen=True, slots=True)
class WorldUpdate:
    state: TravelState
    tick: int
    notice: str
    inventory: InventoryState
    residents: tuple[ResidentActivity, ...]
    wait_committed: bool | None = None


type WorldAction = Literal["inspect", "walk", "save", "load", "wait"]


class WorldWorker:
    def __init__(self, path: Path, world: WorldCatalog) -> None:
        self.path = path
        self.world = world
        self._owner: DurableSession | None = None
        self._pending_wait: GameCommand | None = None
        self._wait_recovery = False
        self._wait_key = ""
        self._wait_duration = 0
        self._wait_update: WorldUpdate | None = None
        self._request_sequence = 0
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="world-owner")

    def _session(self) -> DurableSession:
        if self._owner is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._owner = open_world_session(current_world(self.path), self.world, living=True)
        return self._owner

    def request(
        self,
        action: WorldAction,
        destination: str = "",
        direction: int = 1,
        *,
        seconds: int = 1,
        request_key: str = "",
    ) -> Future[WorldUpdate]:
        if action == "wait" and not request_key:
            self._request_sequence += 1
            request_key = f"auto-time-{self._request_sequence}"
        return self._executor.submit(
            self._run, action, destination, direction, seconds, request_key
        )

    def _run(
        self, action: str, destination: str, direction: int, seconds: int, request_key: str
    ) -> WorldUpdate:
        if action == "wait" and request_key == self._wait_key and self._wait_update is not None:
            if seconds != self._wait_duration:
                raise SaveError("WORLD_TIME_PENDING", "request key reused for another duration")
            return self._wait_update
        if self._wait_update is not None:
            self._pending_wait = None
        owner = self._session()
        notice: str
        wait_committed: bool | None = None
        if self._pending_wait is not None and action != "wait":
            raise SaveError("WORLD_TIME_PENDING", "resolve the previous time command first")
        if action == "wait":
            if self._pending_wait is not None and request_key != self._wait_key:
                raise SaveError("WORLD_TIME_PENDING", "retry must preserve the request key")
            self._wait_key = request_key
            self._wait_duration = seconds
            self._wait_update = None
            wait_committed, notice = self._wait(owner, seconds)
        elif action == "walk":
            result = owner.submit(
                foot_command(owner.protocol(), destination, direction),
                attachment_id=owner.attachment_id,
            )
            if isinstance(result.outcome, TurnRejected):
                notice = result.outcome.failure.code
            elif isinstance(result.outcome, TurnCommitted):
                notice = "한 걸음 이동했습니다."
            else:
                notice = "이동을 완료하지 못했습니다: " + result.outcome.failure.code
        elif action == "save":
            owner.export("slot01")
            notice = "저장했습니다."
        elif action == "load":
            try:
                owner.load("slot01")
            finally:
                remember_world(self.path, owner.working_path)
            notice = "저장한 위치를 불러왔습니다."
        elif action == "inspect":
            notice = "세계를 불러왔습니다."
        else:
            raise ValueError("UNKNOWN_WORLD_ACTION")
        core = owner.snapshot()
        record = next(c for c in core.components if isinstance(c, TravelerRecord))
        inventory = next(c for c in core.components if isinstance(c, InventoryRecord))
        local = next(
            c
            for c in core.components
            if isinstance(c, SettlementRecord) and c.entity_id == record.state.place_id
        )
        residents = (
            ()
            if local.state is None or record.state.destination_id
            else tuple(resident_activity(resident, core.tick) for resident in local.state.residents)
        )
        update = WorldUpdate(
            record.state, core.tick, notice, inventory.state, residents, wait_committed
        )
        if action == "wait":
            self._wait_update = update
        return update

    def _wait(self, owner: DurableSession, seconds: int) -> tuple[bool, str]:
        if self._pending_wait is None:
            self._pending_wait = world_command(owner.protocol(), WorldWait(seconds))
        elif self._pending_wait.payload != WorldWait(seconds):
            raise SaveError("WORLD_TIME_PENDING", "retry must preserve the pending duration")
        if self._wait_recovery:
            try:
                owner.recover()
            except SaveError as error:
                if error.code != "NO_RECOVERY_PENDING":
                    raise
                logging.getLogger(__name__).debug("Time retry has no unresolved durable commit")
        self._wait_recovery = True
        result = owner.submit(self._pending_wait, attachment_id=owner.attachment_id)
        self._wait_recovery = False
        committed = isinstance(result.outcome, TurnCommitted)
        notice = "시간이 흘렀습니다." if committed else "시간을 반영하지 못했습니다."
        return committed, notice

    def _close(self) -> None:
        if self._owner is not None:
            self._owner.close()
            self._owner = None

    def close(self) -> None:
        pending = self._executor.submit(self._close)
        self._executor.shutdown(wait=True)
        pending.result()
