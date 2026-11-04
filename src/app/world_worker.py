"""Single-thread world-session ownership for nonblocking Tk commands and saves."""

from concurrent.futures import Future, ThreadPoolExecutor
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import logging
from typing import Literal

from adapters.world_attachment import current_world, remember_world
from app.durable import DurableSession
from app.world_session import foot_command, open_world_session, world_command
from app.world_supply import SupplyOffer, supply_notice, supply_offers, supply_status
from app.world_conversation_worker import ConversationCoordinator
from adapters.world_conversation import development_generator
from contracts.persistence import SaveError
from contracts.world_time import WorldWait
from contracts.world_supply import SupplyAction
from contracts.turn import GameCommand, TurnCommitted, TurnRejected
from contracts.world_conversation import ConversationGenerator, ContinueSpeech, PlayerSay
from domain.world_conversation import ConversationRecord, ConversationState
from domain.world import WorldCatalog
from domain.world_travel import TravelState, TravelerRecord
from domain.world_population import (
    InventoryRecord,
    InventoryState,
    ResidentActivity,
    SettlementRecord,
)
from domain.world_supply import DELIVERY_REWARD, SupplyRecord, SupplyScenario, supply_activity


@dataclass(frozen=True, slots=True)
class WorldUpdate:
    state: TravelState
    tick: int
    notice: str
    inventory: InventoryState
    residents: tuple[ResidentActivity, ...]
    wait_committed: bool | None = None
    supply_text: str = ""
    offers: tuple[SupplyOffer, ...] = ()
    conversation: ConversationState | None = None
    reply_ready: bool = False
    speech_committed: bool | None = None


type WorldAction = Literal[
    "inspect",
    "walk",
    "save",
    "load",
    "wait",
    "supply",
    "say",
    "speech",
    "generate",
    "reply",
]
DIALOGUE_ACTIONS = ("say", "speech", "generate", "reply")


class WorldWorker:
    def __init__(
        self,
        path: Path,
        world: WorldCatalog,
        *,
        scenario: SupplyScenario = SupplyScenario(),
        conversation: bool = False,
        generator_factory: Callable[[], ConversationGenerator] = development_generator,
    ) -> None:
        self.path = path
        self.world = world
        self.conversation = conversation
        self._dialogue = ConversationCoordinator(world, scenario, generator_factory)
        self._owner: DurableSession | None = None
        self._pending_wait: GameCommand | None = None
        self._wait_recovery = False
        self._wait_key = ""
        self._wait_duration = 0
        self._wait_update: WorldUpdate | None = None
        self._request_sequence = 0
        self.scenario = scenario
        self._pending_supply: GameCommand | None = None
        self._supply_recovery = False
        self._supply_key = ""
        self._supply_update: WorldUpdate | None = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="world-owner")

    def _session(self) -> DurableSession:
        if self._owner is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._owner = open_world_session(
                current_world(self.path),
                self.world,
                supply=self.scenario,
                conversation=self.conversation,
            )
        return self._owner

    def request(
        self,
        action: WorldAction,
        destination: str = "",
        direction: int = 1,
        *,
        seconds: int = 1,
        request_key: str = "",
        supply: SupplyAction | None = None,
        npc_id: str = "",
        text: str = "",
    ) -> Future[WorldUpdate]:
        if action == "wait" and not request_key:
            self._request_sequence += 1
            request_key = f"auto-time-{self._request_sequence}"
        if action == "generate":
            self._dialogue.prepare_generation(request_key)
        return self._executor.submit(
            self._run,
            action,
            destination,
            direction,
            seconds,
            request_key,
            supply,
            npc_id,
            text,
        )

    def _run(
        self,
        action: str,
        destination: str,
        direction: int,
        seconds: int,
        request_key: str,
        supply: SupplyAction | None,
        npc_id: str,
        text: str,
    ) -> WorldUpdate:
        if (
            action == "supply"
            and request_key
            and request_key == self._supply_key
            and self._supply_update is not None
        ):
            if self._pending_supply is None or self._pending_supply.payload != supply:
                raise SaveError("WORLD_SUPPLY_PENDING", "request key reused for another exchange")
            return self._supply_update
        if self._supply_update is not None:
            self._pending_supply = None
        if self._pending_supply is not None and action != "supply":
            raise SaveError("WORLD_SUPPLY_PENDING", "resolve previous exchange first")
        if action == "wait" and request_key == self._wait_key and self._wait_update is not None:
            if seconds != self._wait_duration:
                raise SaveError("WORLD_TIME_PENDING", "request key reused for another duration")
            return self._wait_update
        if self._wait_update is not None:
            self._pending_wait = None
        owner = self._session()
        notice: str
        wait_committed: bool | None = None
        speech_committed: bool | None = None
        if self._dialogue.unresolved and action not in DIALOGUE_ACTIONS:
            raise SaveError("WORLD_DIALOGUE_PENDING", "resolve the previous speech command first")
        if self._pending_wait is not None and action != "wait":
            raise SaveError("WORLD_TIME_PENDING", "resolve the previous time command first")
        if action in DIALOGUE_ACTIONS:
            if not self.conversation:
                raise ValueError("WORLD_CONVERSATION_DISABLED")
            speech_committed, notice = self._speak(owner, action, request_key, npc_id, text)
        elif action == "supply":
            notice = self._exchange(owner, supply, request_key)
        elif action == "wait":
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
            self._dialogue.invalidate()
            try:
                owner.load("slot01")
            finally:
                remember_world(self.path, owner.working_path)
            notice = "저장한 위치를 불러왔습니다."
        elif action == "inspect":
            notice = "세계를 불러왔습니다."
        else:
            raise ValueError("UNKNOWN_WORLD_ACTION")
        update = self._view(owner, notice, wait_committed, speech_committed)
        if action == "wait":
            self._wait_update = update
        if action == "supply":
            self._supply_update = update
        return update

    def _speak(
        self,
        owner: DurableSession,
        action: str,
        key: str,
        npc_id: str,
        text: str,
    ) -> tuple[bool | None, str]:
        if action == "say":
            return self._dialogue.submit(owner, PlayerSay(npc_id, text), key)
        if action == "reply":
            return self._dialogue.accept_reply(owner, key)
        if action == "generate":
            self._dialogue.generate(owner, key)
            return None, "응답을 준비했습니다."
        previous = self._dialogue.retry_command(owner, key)
        if previous is not None:
            return previous
        state = next(
            c.state for c in owner.snapshot().components if isinstance(c, ConversationRecord)
        )
        if not state.exchanges:
            raise ValueError("DIALOGUE_NO_SPEECH")
        return self._dialogue.submit(owner, ContinueSpeech(state.exchanges[-1].speech_id), key)

    def _view(
        self,
        owner: DurableSession,
        notice: str,
        wait_committed: bool | None,
        speech_committed: bool | None,
    ) -> WorldUpdate:
        core = owner.snapshot()
        record = next(c for c in core.components if isinstance(c, TravelerRecord))
        inventory = next(c for c in core.components if isinstance(c, InventoryRecord))
        local = next(
            c
            for c in core.components
            if isinstance(c, SettlementRecord) and c.entity_id == record.state.place_id
        )
        city = next(
            c.state
            for c in core.components
            if isinstance(c, SupplyRecord) and c.entity_id == record.state.place_id
        )
        residents = (
            ()
            if local.state is None or record.state.destination_id
            else tuple(
                supply_activity(
                    resident, index, core.tick, self.scenario, record.state.place_id, city
                )
                for index, resident in enumerate(local.state.residents)
            )
        )
        offers = (
            ()
            if local.state is None or record.state.destination_id
            else supply_offers(local.state, city, inventory.state, self.scenario, core.tick)
        )
        conversation = next(
            (c.state for c in core.components if isinstance(c, ConversationRecord)),
            None,
        )
        return WorldUpdate(
            record.state,
            core.tick,
            notice,
            inventory.state,
            residents,
            wait_committed,
            supply_status(city, self.scenario, record.state.place_id, core.tick),
            offers,
            conversation,
            self._dialogue.reply_ready
            and conversation is not None
            and bool(conversation.exchanges)
            and not conversation.exchanges[-1].reply_text,
            speech_committed,
        )

    def cancel_conversation(self) -> None:
        self._dialogue.cancel()

    def _exchange(self, owner: DurableSession, payload: SupplyAction | None, key: str) -> str:
        if payload is None or not key:
            raise ValueError("WORLD_SUPPLY_CONFIRMATION_MISSING")
        if self._pending_supply is None:
            self._pending_supply = world_command(owner.protocol(), payload)
            self._supply_key = key
            self._supply_update = None
        elif self._supply_key != key or self._pending_supply.payload != payload:
            raise SaveError("WORLD_SUPPLY_PENDING", "retry must preserve the confirmed exchange")
        if self._supply_recovery:
            try:
                owner.recover()
            except SaveError as error:
                if error.code != "NO_RECOVERY_PENDING":
                    raise
                logging.getLogger(__name__).debug("Supply retry has no unresolved durable commit")
        self._supply_recovery = True
        result = owner.submit(self._pending_supply, attachment_id=owner.attachment_id)
        self._supply_recovery = False
        if isinstance(result.outcome, TurnCommitted):
            return {
                "accept": "의뢰를 수락했습니다.",
                "collect": "보급품 1개를 받았습니다.",
                "deliver": f"보급로를 복구하고 보상 {DELIVERY_REWARD}금을 받았습니다.",
            }[payload.operation]
        return supply_notice(result.outcome.failure.code)

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
        self.cancel_conversation()
        pending = self._executor.submit(self._close)
        self._executor.shutdown(wait=True)
        pending.result()
