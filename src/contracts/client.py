"""Renderer-neutral, derived data for the provisional playable boundary harness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

type ClientAction = Literal[
    "up", "down", "left", "right", "open", "close", "attack", "rest", "wait", "bell"
]
type ClientRequest = ClientAction | Literal["attach", "save", "load", "retry", "recover"]


@dataclass(frozen=True, slots=True)
class ClientView:
    width: int
    height: int
    walls: tuple[int, ...]
    actor_cell: int
    gate_cell: int
    gate_open: bool
    enemy_cell: int
    actor_hp: int
    enemy_hp: int
    stamina: int
    npc_cell: int
    npc_bells: int
    npc_replies: int
    charge: int
    tick: int
    revision: int


@dataclass(frozen=True, slots=True)
class ClientUpdate:
    view: ClientView | None
    status: str
    notices: tuple[str, ...]
    attachment_id: str
    working_path: str
    messages: tuple[str, ...] = ()
    reset_log: bool = False
