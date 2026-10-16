"""Pins captured from the two unmodified pre-merge implementations."""

from pathlib import Path

import pytest

from app.client_session import ClientSession
from app.quest import client_quest
from app.scenarios import select_scenario
from domain.scenario import COURTYARD_SCENARIO

ROOT = Path(__file__).resolve().parents[2]


def test_pr09_courtyard_rules_identity(tmp_path: Path) -> None:
    # Captured from origin/main cec6869 before integration,not derived from new code.
    session = ClientSession(tmp_path / "game.sqlite", scenario=COURTYARD_SCENARIO)
    try:
        assert session.owner.snapshot().pins.rules_fingerprint == (
            "c186c9145e39310345dfaaba736b069ee32ba39aafebb4a2e6a056cbf7ca66d9"
        )
        assert select_scenario("scenario:courtyard").layout is COURTYARD_SCENARIO
        assert select_scenario("courtyard").layout is COURTYARD_SCENARIO
    finally:
        session.close()


def test_pr08_approved_memory_rules_identity(tmp_path: Path) -> None:
    # Captured from PR8 310bc58 with its existing approved catalog.
    layout = select_scenario("harbor").layout
    content = client_quest(
        layout,
        ROOT / "content/dialogue/harbor-memory-v1.json",
        (ROOT / "content/dialogue/harbor-memory-v1.sha256").read_text().strip(),
    )
    session = ClientSession(
        tmp_path / "game.sqlite", layout, quest_content=content, npc_memory=True
    )
    try:
        assert session.owner.snapshot().pins.rules_fingerprint == (
            "61733912373591749d2219da196514b4323c9776052cee593dbf501b71bcba76"
        )
    finally:
        session.close()


def test_conflicting_selection_is_rejected_before_save_io(tmp_path: Path) -> None:
    path = tmp_path / "never-created.sqlite"
    with pytest.raises(ValueError, match="^SCENARIO_SELECTION$"):
        ClientSession(path, select_scenario("harbor").layout, scenario=COURTYARD_SCENARIO)
    assert not path.exists()
