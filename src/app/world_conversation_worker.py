"""Single-owner conversation commands and cancellable external generation jobs."""

from collections.abc import Callable
import logging
from threading import Event, Lock

from app.durable import DurableSession
from app.world_session import world_command
from contracts.dialogue import GenerationError
from contracts.messages import CommandPayload
from contracts.persistence import SaveError
from contracts.turn import GameCommand, TurnAborted, TurnCommitted
from contracts.world_conversation import ConversationGenerator, GeneratedReply, NpcReply
from domain.world import WorldCatalog
from domain.world_supply import SupplyScenario
from orchestration.world_conversation_context import context_from_core


class ConversationCoordinator:
    def __init__(
        self,
        world: WorldCatalog,
        scenario: SupplyScenario,
        generator_factory: Callable[[], ConversationGenerator],
    ) -> None:
        self.world, self.scenario, self.factory = world, scenario, generator_factory
        self._command: GameCommand | None = None
        self._command_key = ""
        self._attachment = ""
        self._recovery = False
        self._outcome: tuple[bool, str] | None = None
        self._generation_key = ""
        self._generation_attachment = ""
        self._generated: GeneratedReply | None = None
        self._active: ConversationGenerator | None = None
        self._lock = Lock()
        self._cancelled = Event()

    @property
    def unresolved(self) -> bool:
        return self._command is not None and self._outcome is None

    @property
    def reply_ready(self) -> bool:
        return self._generated is not None

    def submit(
        self,
        owner: DurableSession,
        payload: CommandPayload,
        key: str,
    ) -> tuple[bool, str]:
        if not key:
            raise ValueError("WORLD_DIALOGUE_REQUEST_KEY")
        if self._command is not None and key == self._command_key:
            if payload != self._command.payload:
                raise SaveError(
                    "WORLD_DIALOGUE_PENDING", "retry must preserve speech and attachment"
                )
            if self._outcome is not None:
                if owner.attachment_id != self._attachment:
                    raise SaveError("STALE_ATTACHMENT", "speech belongs to previous attachment")
                return self._outcome
        elif self.unresolved:
            raise SaveError("WORLD_DIALOGUE_PENDING", "resolve the pending speech command first")
        else:
            self._command = world_command(owner.protocol(), payload)
            self._command_key, self._attachment = key, owner.attachment_id
            self._outcome = None
        if self._recovery:
            try:
                owner.recover()
            except SaveError as error:
                if error.code != "NO_RECOVERY_PENDING":
                    raise
                logging.getLogger(__name__).debug("Speech retry has no unresolved durable commit")
        if owner.attachment_id != self._attachment:
            raise SaveError("STALE_ATTACHMENT", "speech belongs to previous attachment")
        self._recovery = True
        publication = owner.submit(self._command, attachment_id=self._attachment)
        self._recovery = False
        if isinstance(publication.outcome, TurnAborted):
            if publication.outcome.failure.code == "SAVE_UNAVAILABLE":
                raise SaveError(
                    "SAVE_UNAVAILABLE", "speech transaction was confirmed absent;retry unchanged"
                )
            raise RuntimeError("WORLD_DIALOGUE_ABORTED: " + publication.outcome.failure.code)
        committed = isinstance(publication.outcome, TurnCommitted)
        notice = (
            "발언을 반영했습니다."
            if isinstance(publication.outcome, TurnCommitted)
            else publication.outcome.failure.code
        )
        self._outcome = committed, notice
        return self._outcome

    def retry_command(self, owner: DurableSession, key: str) -> tuple[bool, str] | None:
        if self._command is not None and key == self._command_key:
            return self.submit(owner, self._command.payload, key)
        if self.unresolved:
            raise SaveError("WORLD_DIALOGUE_PENDING", "resolve the pending speech command first")
        return None

    def prepare_generation(self, key: str) -> None:
        # Called before enqueue,so cancellation also covers a job not yet started.
        if key != self._generation_key:
            self._cancelled.clear()

    def generate(self, owner: DurableSession, key: str) -> None:
        if self.unresolved:
            raise SaveError("WORLD_DIALOGUE_PENDING", "resolve the pending speech command first")
        if not key:
            raise ValueError("WORLD_DIALOGUE_REQUEST_KEY")
        attachment = owner.attachment_id
        context = context_from_core(owner.snapshot(), self.world, self.scenario)
        if self._generated is not None and key == self._generation_key:
            if (
                attachment != self._generation_attachment
                or context.sha256 != self._generated.context_sha256
            ):
                raise ValueError("DIALOGUE_CONTEXT_STALE")
            return
        self._generation_key, self._generation_attachment = key, attachment
        self._generated = None
        if self._cancelled.is_set():
            raise GenerationError("GENERATION_CANCELLED")
        generator = self.factory()
        with self._lock:
            self._active = generator
            if self._cancelled.is_set():
                generator.cancel()
        try:
            reply = generator.generate(context)
            if self._cancelled.is_set():
                raise GenerationError("GENERATION_CANCELLED")
            if owner.attachment_id != attachment or reply.context_sha256 != context.sha256:
                raise ValueError("DIALOGUE_CONTEXT_STALE")
            self._generated = reply
        finally:
            with self._lock:
                self._active = None

    def accept_reply(self, owner: DurableSession, key: str) -> tuple[bool, str]:
        # Do not reconstruct context after an uncertain COMMIT:retry the exact cached command.
        previous = self.retry_command(owner, key)
        if previous is not None:
            return previous
        if self._generated is None or owner.attachment_id != self._generation_attachment:
            raise ValueError("DIALOGUE_CONTEXT_STALE")
        context = context_from_core(owner.snapshot(), self.world, self.scenario)
        reply = self._generated
        if context.sha256 != reply.context_sha256:
            raise ValueError("DIALOGUE_CONTEXT_STALE")
        return self.submit(
            owner,
            NpcReply(
                context.current.speech_id,
                reply.text,
                reply.model,
                reply.context_sha256,
                reply.proposal,
            ),
            key,
        )

    def cancel(self) -> None:
        self._cancelled.set()
        with self._lock:
            if self._active is not None:
                self._active.cancel()

    def invalidate(self) -> None:
        if self.unresolved:
            raise SaveError("WORLD_DIALOGUE_PENDING", "resolve pending speech before loading")
        self._command, self._outcome, self._generated = None, None, None
        self._command_key = self._generation_key = ""
