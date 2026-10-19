"""Separate capture phases must not invalidate Tcl's native file channels."""

from __future__ import annotations

import gc
from pathlib import Path
import tkinter as tk

import pytest

from app.client import PlayWindow
from tests.integration.test_client import _pump


@pytest.mark.parametrize("lifetime", range(20))
def test_independent_tk_interpreters_attach_and_close(tmp_path: Path, lifetime: int) -> None:
    # Parameter cases cross pytest setup/call/teardown capture boundaries. A loop in
    # one test (or a standalone Python script) does not exercise descriptor replacement.
    gc.collect()
    root = tk.Tk()
    root.withdraw()
    screen = PlayWindow(root, tmp_path / f"game-{lifetime}.sqlite")
    try:
        _pump(root, lambda: not screen.busy)
        assert screen.last_update is not None, screen.last_update
        assert screen.last_update.status == "ATTACHED", screen.last_update
        assert screen.view is not None, screen.last_update
        assert (screen.view.tick, screen.view.revision) == (0, 0)
        screen.buttons["wait"].invoke()
        _pump(root, lambda: not screen.busy)
        assert screen.last_update.status == "COMMITTED", screen.last_update
        assert (screen.view.tick, screen.view.revision) == (1, 1)
    finally:
        screen.close()
        _pump(root, lambda: screen.closed)
        screen.worker.join()
        assert screen.closed
