"""Actual replies expose current intended movement without advancing the world."""

from pathlib import Path
import pytest
from domain.canonical import array_value, object_value
from contracts.persistence import SaveError
from tests.integration.test_reach_gate_aid import driver, session
from tests.integration.test_ready_patrol import session as parent_session
from tests.integration.test_patrol_next_step import FREE_HOME, FREE_NEIGHBOR, BLOCKED
from tests.integration.test_quest_patrol import state, view

PREFIX = "응답 후 현재 "


@pytest.mark.parametrize("framed", (False, True), ids=("direct", "real-pipe"))
@pytest.mark.parametrize(
    "tick,expected", ((11, FREE_HOME), (13, FREE_NEIGHBOR), (15, FREE_HOME), (17, BLOCKED))
)
def test_actual_reply_current_next_step(
    tmp_path: Path, framed: bool, tick: int, expected: str
) -> None:
    path = tmp_path / "game.sqlite"
    with driver(path, framed) as send:
        send("down")
        send("talk")
        send("up")
        stop = tick if tick != 17 else 15
        for _ in range(stop - 4):
            send("wait")
        if tick == 17:
            send("down")
            send("down")
        reply = send("bell")
        assert object_value(reply["view"])["tick"] == str(tick)
        lines = array_value(reply["messages"])
        assert tuple(
            x
            for x in lines
            if isinstance(x, str) and x.startswith(PREFIX + "NPC 다음 순찰 행동 · ")
        ) == (PREFIX + expected,)
        assert (
            sum(isinstance(x, str) and x.startswith(PREFIX + "NPC 지원 계획 · ") for x in lines)
            == 1
        )
        before = path.read_bytes()
        retry = send("retry")
        assert retry["view"] == reply["view"] and path.read_bytes() == before
        assert not any(
            isinstance(x, str) and x.startswith(PREFIX) for x in array_value(retry["messages"])
        )


def test_parent_ready_mode_has_no_new_reply_plan(tmp_path: Path) -> None:
    owner = parent_session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("up")
        owner.act("wait", seconds=10)
        reply = owner.act("bell")
        assert view(reply).npc_replies == 1
        assert not any(line.startswith(PREFIX) for line in reply.messages)
    finally:
        owner.close()


def test_postcommit_next_step_failure_preserves_reply_and_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("up")
        owner.act("wait", seconds=11)

        def fail(*args: object, **kwargs: object) -> tuple[str, ...]:
            raise SaveError("SOURCE", "current plan unavailable")

        with monkeypatch.context() as patch:
            patch.setattr("app.client_session.quest_patrol_next_step", fail)
            with pytest.raises(SaveError, match="NPC_RECOLLECTION_SOURCE"):
                owner.act("bell")
        assert view(owner.update()).gate_open and view(owner.update()).npc_replies == 1
        after = state(owner)
        owner.retry()
        assert state(owner) == after
        assert owner.act("wait").status == "COMMITTED"
    finally:
        owner.close()
