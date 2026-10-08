"""Serialize Brain/SQLite work off the Tk thread;never touch widgets here."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import replace
import logging
from pathlib import Path

from app.client_session import ClientSession
from app.client_text import status_text
from contracts.client import ClientRequest, ClientUpdate
from contracts.persistence import SaveError, WorldUnavailable


class ClientWorker:
    def __init__(self, path: Path) -> None:
        self._path = path
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

    def _run(self, request: ClientRequest, seconds: int, slot_id: str) -> ClientUpdate:
        try:
            if self._owner is None:
                self._owner = ClientSession(self._path)
            owner = self._owner
            match request:
                case "attach":
                    update = owner.update(reset_log=True)
                case "save":
                    update = owner.save(slot_id)
                case "load":
                    update = owner.load(slot_id)
                case "retry":
                    update = owner.retry()
                case "recover":
                    update = owner.recover()
                case _:
                    update = owner.act(request, seconds=seconds)
            self._last = update
        except (SaveError, WorldUnavailable) as error:
            self._last = self._error_update(error.code, error)
        except ValueError as error:
            # Unexpected adapter bugs remain visible,not classified as valid player rejection.
            code = str(error) if str(error) == "NO_RETRY" else "CLIENT_ERROR"
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
