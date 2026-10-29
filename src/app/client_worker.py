"""Serialize Brain/SQLite work off the Tk thread;never touch widgets here."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import replace
import logging
from pathlib import Path
from typing import Literal

from app.client_session import ClientSession
from app.client_text import status_text
from contracts.client import ClientRequest, ClientUpdate
from contracts.dialogue import QuestContent
from contracts.persistence import SaveError, WorldUnavailable
from domain.scenario import resolve_selection, LEGACY, Scenario


class ClientWorker:
    def __init__(
        self,
        path: Path,
        layout: Scenario = LEGACY,
        *,
        scenario: Scenario = LEGACY,
        quest_content: QuestContent | None = None,
        npc_memory: bool = False,
        npc_work: bool = False,
        npc_cycle: bool = False,
        npc_aid: bool = False,
        npc_supply_aid: bool = False,
        npc_call_aid: bool = False,
        npc_patrol: bool = False,
        npc_talk_pause: bool = False,
        npc_quest_patrol: bool = False,
        npc_call_pause: bool = False,
        npc_ready_patrol: bool = False,
        npc_reach_aid: bool = False,
    ) -> None:
        if type(npc_memory) is not bool or npc_memory and quest_content is None:
            raise ValueError("NPC_MEMORY_CONTENT")
        if type(npc_work) is not bool or npc_work and not npc_memory:
            raise ValueError("NPC_WORK_CONTENT")
        layout = resolve_selection(layout, scenario)
        self._path = path
        self._layout = layout
        self._quest_content = quest_content
        self._npc_memory = npc_memory
        if type(npc_cycle) is not bool or npc_cycle and (not npc_memory or npc_work):
            raise ValueError("NPC_CYCLE_CONTENT")
        self._npc_cycle = npc_cycle
        if type(npc_aid) is not bool or npc_aid and not npc_cycle:
            raise ValueError("NPC_AID_CONTENT")
        self._npc_aid = npc_aid
        if type(npc_supply_aid) is not bool or npc_supply_aid and not npc_aid:
            raise ValueError("NPC_SUPPLY_AID_CONTENT")
        self._npc_supply_aid = npc_supply_aid
        if type(npc_call_aid) is not bool or npc_call_aid and not npc_supply_aid:
            raise ValueError("NPC_CALL_AID_CONTENT")
        self._npc_call_aid = npc_call_aid
        if type(npc_patrol) is not bool or npc_patrol and not npc_call_aid:
            raise ValueError("NPC_PATROL_CONTENT")
        if type(npc_talk_pause) is not bool or npc_talk_pause and not npc_patrol:
            raise ValueError("NPC_TALK_PAUSE_CONTENT")
        if type(npc_quest_patrol) is not bool or npc_quest_patrol and not npc_talk_pause:
            raise ValueError("NPC_QUEST_PATROL_CONTENT")
        if type(npc_call_pause) is not bool or npc_call_pause and not npc_quest_patrol:
            raise ValueError("NPC_CALL_PAUSE_CONTENT")
        if type(npc_ready_patrol) is not bool or npc_ready_patrol and not npc_call_pause:
            raise ValueError("NPC_READY_PATROL_CONTENT")
        if type(npc_reach_aid) is not bool or npc_reach_aid and not npc_ready_patrol:
            raise ValueError("NPC_REACH_AID_CONTENT")
        self._npc_patrol = npc_patrol
        self._npc_talk_pause = npc_talk_pause
        self._npc_quest_patrol = npc_quest_patrol
        self._npc_call_pause = npc_call_pause
        self._npc_ready_patrol = npc_ready_patrol
        self._npc_reach_aid = npc_reach_aid
        self._npc_work = npc_work
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="reverie-brain")
        self._owner: ClientSession | None = None
        self._last = ClientUpdate(None, "CONNECTING", (), "", str(path))
        self._closing = False
        self._close_future: Future[None] | None = None
        self._logger = logging.getLogger(__name__)

    def request(
        self, request: ClientRequest, *, seconds: int = 1, slot_id: str = "slot01"
    ) -> Future[ClientUpdate]:
        if self._closing:
            raise ValueError("CLIENT_CLOSING")
        return self._executor.submit(self._run, request, seconds, slot_id)

    def inspect_memory(self) -> Future[ClientUpdate]:
        """Serialize full read-only inspection on the Brain owner thread."""
        return self._inspect("memory")

    def inspect_recent_memory(self) -> Future[ClientUpdate]:
        return self._inspect("memory_recent")

    def inspect_activity(self) -> Future[ClientUpdate]:
        return self._inspect("activity")

    def inspect_slot(self, slot_id: str = "slot01") -> Future[ClientUpdate]:
        return self._inspect("slot_inspect", slot_id)

    def inspect_previous_slot(self, slot_id: str = "slot01") -> Future[ClientUpdate]:
        return self._inspect("slot_previous_inspect", slot_id)

    def _inspect(
        self,
        request: Literal[
            "memory", "memory_recent", "activity", "slot_inspect", "slot_previous_inspect"
        ],
        slot_id: str = "slot01",
    ) -> Future[ClientUpdate]:
        if self._closing:
            raise ValueError("CLIENT_CLOSING")
        return self._executor.submit(self._run, request, 1, slot_id)

    def _run(
        self,
        request: ClientRequest
        | Literal["memory", "memory_recent", "activity", "slot_inspect", "slot_previous_inspect"],
        seconds: int,
        slot_id: str,
    ) -> ClientUpdate:
        try:
            # Inspection must never create a game or open an unattached save.
            if request in ("memory", "memory_recent", "activity") and self._owner is None:
                raise ValueError("NPC_MEMORY_UNAVAILABLE")
            if request in ("slot_inspect", "slot_previous_inspect") and self._owner is None:
                raise ValueError("SLOT_INSPECTION_UNAVAILABLE")
            if self._owner is None:
                self._owner = (
                    ClientSession(self._path, self._layout)
                    if self._quest_content is None
                    else ClientSession(
                        self._path,
                        self._layout,
                        quest_content=self._quest_content,
                        npc_memory=self._npc_memory,
                        npc_work=self._npc_work,
                        npc_cycle=self._npc_cycle,
                        npc_aid=self._npc_aid,
                        npc_supply_aid=self._npc_supply_aid,
                        npc_call_aid=self._npc_call_aid,
                        npc_patrol=self._npc_patrol,
                        npc_talk_pause=self._npc_talk_pause,
                        npc_quest_patrol=self._npc_quest_patrol,
                        npc_call_pause=self._npc_call_pause,
                        npc_ready_patrol=self._npc_ready_patrol,
                        npc_reach_aid=self._npc_reach_aid,
                    )
                )
            owner = self._owner
            match request:
                case "attach":
                    update = owner.update(reset_log=True)
                case "save":
                    update = owner.save(slot_id)
                case "load":
                    update = owner.load(slot_id)
                case "load_previous":
                    update = owner.load(slot_id, previous=True)
                case "retry":
                    update = owner.retry()
                case "recover":
                    update = owner.recover()
                case "memory":
                    update = owner.inspect_memory()
                case "memory_recent":
                    update = owner.inspect_recent_memory()
                case "activity":
                    update = owner.inspect_activity()
                case "slot_inspect":
                    update = owner.inspect_slot(slot_id)
                case "slot_previous_inspect":
                    update = owner.inspect_slot(slot_id, previous=True)
                case _:
                    update = owner.act(request, seconds=seconds)
            self._last = update
        except (SaveError, WorldUnavailable) as error:
            self._last = self._error_update(error.code, error)
        except ValueError as error:
            # Unexpected adapter bugs remain visible,not classified as valid player rejection.
            code = (
                str(error)
                if str(error)
                in (
                    "NO_RETRY",
                    "QUEST_UNAVAILABLE",
                    "NPC_MEMORY_UNAVAILABLE",
                    "SLOT_INSPECTION_UNAVAILABLE",
                )
                else "CLIENT_ERROR"
            )
            if code == "CLIENT_ERROR":
                self._logger.exception("client boundary operation failed")
            self._last = self._error_update(code, error)
        except Exception as error:
            # Final UI boundary: log ordinary failures and expose an explicit error projection.
            # Fatal BaseException subclasses still propagate; no gameplay success is fabricated.
            self._logger.exception("client boundary operation failed")
            self._last = self._error_update("CLIENT_ERROR", error)
        return self._last

    def _error_update(self, code: str, error: Exception) -> ClientUpdate:
        if self._owner is not None:
            try:
                current = self._owner.update(code, (str(error),), messages=(status_text(code),))
                return replace(
                    current,
                    reset_log=bool(
                        self._last.attachment_id
                        and current.attachment_id != self._last.attachment_id
                    ),
                )
            except Exception:
                # Projection can fail independently;the cache remains an explicit error.
                self._logger.exception("client error reconciliation failed")
        return replace(
            self._last,
            status=code,
            notices=(str(error),),
            messages=(status_text(code),),
            reset_log=False,
        )

    def close(self) -> Future[None]:
        if self._close_future is None:
            self._closing = True
            self._close_future = self._executor.submit(self._close_owner)
            self._executor.shutdown(
                wait=False
            )  # Already accepted work finishes before owner close.
        return self._close_future

    def _close_owner(self) -> None:
        if self._owner is not None:
            self._owner.close()

    def join(self) -> None:
        """After the window/event loop ends,join the already draining worker."""
        self.close().result()
        self._executor.shutdown(wait=True)
