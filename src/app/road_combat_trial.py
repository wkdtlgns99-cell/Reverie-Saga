"""Isolated playtest of the registered encounter beside the village."""

from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

from app.client_session import ClientSession
from contracts.client import ClientAction
from domain.canonical import JsonObject

TRIAL_ACTIONS = ("up", "down", "left", "right", "open", "attack", "rest")


class RoadCombatTrial:
    def __init__(self) -> None:
        with ExitStack() as cleanup:
            path = Path(cleanup.enter_context(TemporaryDirectory(prefix="reverie-road-trial-")))
            self._client = ClientSession(path / "combat.sqlite")
            cleanup.callback(self._client.close)
            self._latest = self._client.update()
            self._cleanup = cleanup.pop_all()

    def act(self, action: str) -> str:
        if action not in TRIAL_ACTIONS:
            return "INVALID_COMMAND"
        self._latest = self._client.act(cast(ClientAction, action))
        return ""

    def wire(self) -> JsonObject:
        view = self._latest.view
        if view is None:
            raise RuntimeError("ROAD_TRIAL_VIEW_MISSING")
        return {
            "width": view.width,
            "height": view.height,
            "walls": view.walls,
            "actor_cell": view.actor_cell,
            "gate_cell": view.gate_cell,
            "gate_open": view.gate_open,
            "enemy_cell": view.enemy_cell,
            "actor_hp": view.actor_hp,
            "enemy_hp": view.enemy_hp,
            "stamina": view.stamina,
            "tick": view.tick,
            "revision": view.revision,
            "status": self._latest.status,
            "messages": self._latest.messages,
        }

    def close(self) -> None:
        self._cleanup.close()
