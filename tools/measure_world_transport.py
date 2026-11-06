"""Wall-clock timings for the fixed carriage and sea journey through Tk and SQLite."""

from collections import Counter
from collections.abc import Callable
from contextlib import ExitStack
from functools import wraps
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from timeit import default_timer
import tkinter as tk
from typing import ParamSpec, TypeVar

from adapters.sqlite_store import SqliteCommitStore
from app.world_catalog import load_social, load_transport, load_world
from app.world_client import WorldMapWindow
from app.world_worker import WorldUpdate, WorldWorker
from domain.world_transport import TransportRules
from orchestration.turn import Driver


P = ParamSpec("P")
R = TypeVar("R")


def timed(
    function: Callable[P, R], label: str, totals: dict[str, float], calls: Counter[str]
) -> Callable[P, R]:
    @wraps(function)
    def run(*args: P.args, **kwargs: P.kwargs) -> R:
        start = default_timer()
        try:
            return function(*args, **kwargs)
        finally:
            totals[label] = totals.get(label, 0.0) + (default_timer() - start)
            calls[label] += 1

    return run


def settle(window: WorldMapWindow, root: tk.Tk) -> WorldUpdate:
    deadline = default_timer() + 120
    while window.pending is not None and default_timer() < deadline:
        root.update()
        root.tk.call("after", 2)
    if window.pending is not None or window.transport_error or window.update is None:
        raise RuntimeError("journey did not settle successfully")
    return window.update


def travel(
    window: WorldMapWindow, root: tk.Tk, transport: TransportRules, destination: str
) -> WorldUpdate:
    window.confirm_transport("board", destination)
    update = settle(window, root)
    while update.journey is not None and update.journey.phase == "blocked":
        block_id = update.journey.block_id
        closure = next(c for c in transport.closures if c.id == block_id)
        operation = "wait" if update.tick < closure.end_tick else "resume"
        window.confirm_transport(operation, "")
        update = settle(window, root)
    if (
        update.journey is None
        or update.journey.phase != "idle"
        or update.state.place_id != destination
    ):
        raise RuntimeError("arrival not confirmed")
    return update


def measure(path: Path) -> dict[str, object]:
    world = load_world()
    transport = load_transport(world)
    root = tk.Tk()
    root.withdraw()
    try:
        worker = WorldWorker(path, world, social=load_social(world), transport=transport)
        try:
            window = WorldMapWindow(root, world, worker, now_ns=lambda: 0)
            try:
                update = settle(window, root)
                totals: dict[str, float] = {}
                calls: Counter[str] = Counter()
                stages = (
                    (Driver, "_check_command", "check_command"),
                    (Driver, "_admit", "admission"),
                    (Driver, "_simulate", "simulation"),
                    (Driver, "_prepare_commit", "prepare_commit"),
                    (Driver, "_persist_durable", "durable_persistence"),
                    (SqliteCommitStore, "_execute", "sqlite_execute_subset"),
                    (Driver, "_present", "core_presentation"),
                    (WorldWorker, "_view", "worker_projection"),
                    (WorldMapWindow, "render", "tk_render_callback"),
                )
                with ExitStack() as stack:
                    for owner, method, label in stages:
                        original = getattr(owner, method)
                        stack.callback(setattr, owner, method, original)
                        setattr(owner, method, timed(original, label, totals, calls))
                    start = default_timer()
                    for destination in ("place:p0-b", "place:p1-b"):
                        update = travel(window, root, transport, destination)
                    total = default_timer() - start
                if calls["simulation"] != 35 or update.tick != 93851:
                    raise RuntimeError("unexpected command count or final tick")
                return {
                    "total_seconds": round(total, 4),
                    "final_tick": update.tick,
                    "stage_seconds": {name: round(value, 4) for name, value in totals.items()},
                    "stage_calls": dict(calls),
                }
            finally:
                window.dispose()
        finally:
            worker.close()
    finally:
        root.destroy()


def main() -> None:
    workspace = Path(__file__).resolve().parents[1]
    scratch = (workspace / "tmp").resolve()
    scratch.relative_to(workspace)
    scratch.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="transport-wall-", dir=scratch) as temporary:
        print(json.dumps(measure(Path(temporary) / "game.sqlite"), indent=2))


if __name__ == "__main__":
    main()
