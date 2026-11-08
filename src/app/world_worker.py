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
from app.world_village_session import open_knowledge_world
from app.world_supply import SupplyOffer, supply_notice, supply_offers, supply_status
from app.world_conversation_worker import ConversationCoordinator
from adapters.world_conversation import development_generator
from contracts.persistence import SaveError
from contracts.world_time import WorldWait
from contracts.world_supply import SupplyAction
from contracts.world_social import SocialAction
from contracts.world_transport import TransportAction
from contracts.turn import GameCommand, ProtocolSnapshot, TurnAborted, TurnCommitted, TurnRejected
from contracts.world_conversation import ConversationGenerator, ContinueSpeech, PlayerSay
from domain.world_conversation import ConversationRecord, ConversationState
from domain.world import WorldCatalog
from domain.world_travel import TravelState, TravelerRecord
from domain.world_transport import JourneyRecord, JourneyState, TransportRules, plan_journey
from orchestration.world_transport import JOURNEY_ERRORS
from domain.world_population import (
    InventoryRecord,
    InventoryState,
    ResidentActivity,
    SettlementRecord,
)
from domain.world_supply import DELIVERY_REWARD, SupplyRecord, SupplyScenario, supply_activity
from domain.world_social import (
    HOSTILE_THRESHOLD,
    SocialCatalog,
    SocialRecord,
    SocialState,
    reaction,
)


@dataclass(frozen=True, slots=True)
class WorldUpdate:
    state: TravelState
    tick: int
    notice: str
    inventory: InventoryState
    residents: tuple[ResidentActivity, ...]
    protocol: ProtocolSnapshot
    wait_committed: bool | None = None
    supply_text: str = ""
    offers: tuple[SupplyOffer, ...] = ()
    conversation: ConversationState | None = None
    reply_ready: bool = False
    speech_committed: bool | None = None
    social: SocialState | None = None
    social_committed: bool | None = None
    journey: JourneyState | None = None
    transport_committed: bool | None = None


type WorldAction = Literal[
    "inspect",
    "walk",
    "recover_walk",
    "save",
    "load",
    "wait",
    "supply",
    "say",
    "speech",
    "generate",
    "reply",
    "social",
    "transport",
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
        social: SocialCatalog | None = None,
        transport: TransportRules | None = None,
        authored_supply: bool = False,
        live_npc: bool = True,
        knowledge: bool = False,
        require_existing: bool = False,
        generator_factory: Callable[[], ConversationGenerator] = development_generator,
    ) -> None:
        self.path = path
        self.world = world
        self.conversation = conversation or knowledge or social is not None
        self.authored_supply = authored_supply
        self.live_npc = live_npc
        self.knowledge = knowledge
        self.require_existing = require_existing
        self.social = social
        if transport is not None and social is None:
            raise ValueError("TRANSPORT_SOCIAL_REQUIRED")
        self.transport = transport
        self._transport_request: tuple[str, str, str] | None = None
        self._dialogue = ConversationCoordinator(world, scenario, generator_factory, social=social)
        self._owner: DurableSession | None = None
        self._walk_needs_recovery = False
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
            if not self.require_existing:
                self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.knowledge and self.social is not None and self.transport is not None:
                self._owner = open_knowledge_world(
                    self.path, self.world, self.scenario, self.social, self.transport,
                    require_existing=self.require_existing,
                )
                return self._owner
            self._owner = open_world_session(
                current_world(self.path),
                self.world,
                supply=self.scenario,
                conversation=self.conversation,
                social=self.social,
                transport=self.transport,
                knowledge=self.knowledge,
                require_existing=self.require_existing,
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
        social_action: SocialAction | None = None,
        transport_operation: str = "",
    ) -> Future[WorldUpdate]:
        if action == "wait" and not request_key:
            self._request_sequence += 1
            request_key = f"auto-time-{self._request_sequence}"
        if action == "generate" and self.live_npc:
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
            social_action,
            transport_operation,
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
        social_action: SocialAction | None,
        transport_operation: str,
    ) -> WorldUpdate:
        if action == "recover_walk":
            return self._recover_walk(self._session())
        if self._walk_needs_recovery:
            raise SaveError("WORLD_WALK_PENDING", "confirm the previous footstep first")
        if not self.live_npc and action in ("say", "generate", "reply"):
            raise ValueError("WORLD_NPC_AI_DISABLED")
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
        social_committed: bool | None = None
        transport_committed: bool | None = None
        if self._dialogue.unresolved and action not in (*DIALOGUE_ACTIONS, "social", "transport"):
            raise SaveError("WORLD_DIALOGUE_PENDING", "resolve the previous speech command first")
        if self._pending_wait is not None and action != "wait":
            raise SaveError("WORLD_TIME_PENDING", "resolve the previous time command first")
        if action == "transport":
            transport_committed, notice = self._travel(
                owner, transport_operation, destination, request_key
            )
        elif action == "social":
            if self.social is None or social_action is None:
                raise ValueError("SOCIAL_CONFIRMATION_MISSING")
            social_committed, notice = self._dialogue.submit(owner, social_action, request_key)
            if social_committed:
                notice = {
                    "identify": "종족과 국적을 기록했습니다.",
                    "protest": "항의를 전달했습니다. 지역·국가 평판이 낮아졌습니다.",
                    "reconcile": "화해를 요청했습니다. 나빠진 평판이 일부 회복됐습니다.",
                }[social_action.operation]
        elif action in DIALOGUE_ACTIONS:
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
            notice = self._walk(owner, destination, direction)
        elif action == "save":
            owner.export("slot01")
            notice = "저장했습니다."
        elif action == "load":
            former = owner.attachment_id
            try:
                owner.load(
                    "slot01", publish_working=lambda active: remember_world(self.path, active)
                )
            finally:
                if owner.attachment_id != former:
                    self._dialogue.invalidate()
                    self._transport_request = None
            notice = "저장한 위치를 불러왔습니다."
        elif action == "inspect":
            notice = "세계를 불러왔습니다."
        else:
            raise ValueError("UNKNOWN_WORLD_ACTION")
        update = self._view(
            owner, notice, wait_committed, speech_committed, social_committed, transport_committed
        )
        if action == "wait":
            self._wait_update = update
        if action == "supply":
            self._supply_update = update
        return update

    def _walk(self, owner: DurableSession, destination: str, direction: int) -> str:
        command = foot_command(owner.protocol(), destination, direction)
        attachment = owner.attachment_id
        try:
            result = owner.submit(command, attachment_id=attachment)
        except SaveError as error:
            self._walk_needs_recovery = error.code == "SAVE_UNCERTAIN"
            raise
        if isinstance(result.outcome, TurnRejected):
            return result.outcome.failure.code
        if isinstance(result.outcome, TurnCommitted):
            return "한 걸음 이동했습니다."
        return "이동을 완료하지 못했습니다: " + result.outcome.failure.code

    def _recover_walk(self, owner: DurableSession) -> WorldUpdate:
        notice = "확인할 이동 결과가 없습니다."
        if self._walk_needs_recovery:
            outcome = owner.recover().outcome
            if isinstance(outcome, TurnCommitted):
                notice = "이전 이동이 저장된 것을 확인했습니다."
            elif isinstance(outcome, TurnAborted) and outcome.failure.code == "SAVE_UNAVAILABLE":
                notice = "이전 이동이 반영되지 않았습니다. 다시 이동할 수 있습니다."
            else:
                raise RuntimeError("WORLD_WALK_INVALID_RECOVERY_OUTCOME")
            self._walk_needs_recovery = False
        return self._view(owner, notice, None, None)

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
        social_committed: bool | None = None,
        transport_committed: bool | None = None,
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
        social = next((c.state for c in core.components if isinstance(c, SocialRecord)), None)
        journey = next((c.state for c in core.components if isinstance(c, JourneyRecord)), None)
        in_transit = journey is not None and journey.phase != "idle"
        if in_transit:
            residents, offers = (), ()
        if (
            social is not None
            and self.social is not None
            and reaction(social, self.social, record.state.place_id) <= HOSTILE_THRESHOLD
        ):
            offers = tuple(offer for offer in offers if offer.action.operation != "accept")
        return WorldUpdate(
            record.state,
            core.tick,
            notice,
            inventory.state,
            residents,
            owner.protocol(),
            wait_committed,
            "여정 중 · 주민과 도시 보급 정보는 도착 후 확인할 수 있습니다."
            if in_transit
            else supply_status(
                city, self.scenario, record.state.place_id, core.tick, authored=self.authored_supply
            ),
            offers,
            conversation,
            self._dialogue.reply_ready
            and not in_transit
            and conversation is not None
            and bool(conversation.exchanges)
            and not conversation.exchanges[-1].reply_text,
            speech_committed,
            social,
            social_committed,
            journey,
            transport_committed,
        )

    def _travel(
        self, owner: DurableSession, operation: str, destination: str, key: str
    ) -> tuple[bool, str]:
        if self.transport is None or not key:
            raise ValueError("TRANSPORT_CONFIRMATION_MISSING")
        request = (key, operation, destination)
        if (
            self._transport_request is not None
            and self._transport_request[0] == key
            and self._transport_request != request
        ):
            raise SaveError("WORLD_TRANSPORT_PENDING", "retry must preserve the journey request")
        previous = self._dialogue.retry_command(owner, key)
        if previous is not None:
            return previous[0], "여정을 반영했습니다." if previous[0] else previous[1]
        self._transport_request = request
        core = owner.snapshot()
        journey = next(c.state for c in core.components if isinstance(c, JourneyRecord))
        travel = next(c.state for c in core.components if isinstance(c, TravelerRecord))
        try:
            plan = plan_journey(
                self.world, self.transport, journey, travel, core.tick, operation, destination
            )
        except ValueError as error:
            if str(error) not in JOURNEY_ERRORS:
                raise
            return False, str(error)
        committed, notice = self._dialogue.submit(
            owner, TransportAction(operation, destination, plan.seconds), key
        )
        return committed, "여정을 반영했습니다." if committed else notice

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
        if isinstance(result.outcome, TurnAborted):
            code = result.outcome.failure.code
            if code == "SAVE_UNAVAILABLE":
                raise SaveError(code, "supply transaction was confirmed absent and can be retried")
            raise RuntimeError("WORLD_SUPPLY_ABORTED: " + code)
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
