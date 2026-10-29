"""Actual answered calls expose current support without another replay or command."""

from pathlib import Path
import pytest
from domain.canonical import object_value, array_value
from tests.integration.test_reach_gate_aid import driver, session
from tests.integration.test_quest_patrol import view, state
from contracts.persistence import SaveError

PREFIX = "응답 후 현재 NPC 지원 계획 · "


@pytest.mark.parametrize("framed", (False, True), ids=("direct", "real-pipe"))
@pytest.mark.parametrize(
    "tick,text",
    (
        (11, "공동 물자 1개를 더 확보하면 통행 지원을 준비합니다. (현재 1/3개)."),
        (13, "공동 물자가 확보되어 통행문 옆 작업 지점에 도착해야 통행을 도울 수 있습니다."),
        (15, "통행문이 열려 있어 공동 물자 준비를 이어갑니다."),
    ),
)
def test_actual_answer_current_plan_once_and_retry_no_new_row(
    tmp_path: Path, framed: bool, tick: int, text: str
) -> None:
    path = tmp_path / "game.sqlite"
    with driver(path, framed) as send:
        send("down")
        send("talk")
        send("up")
        for _ in range(tick - 4):
            send("wait")
        response = send("bell")
        assert object_value(response["view"])["tick"] == str(tick)
        assert tuple(
            line
            for line in array_value(response["messages"])
            if isinstance(line, str) and line.startswith(PREFIX)
        ) == (PREFIX + text,)
        before = path.read_bytes()
        retry = send("retry")
        assert retry["view"] == response["view"] and path.read_bytes() == before
        assert not any(
            isinstance(line, str) and line.startswith(PREFIX)
            for line in array_value(retry["messages"])
        )


def test_postcommit_plan_failure_keeps_actual_reply_and_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        owner.act("down")
        owner.act("talk")
        owner.act("up")
        owner.act("wait", seconds=11)

        def fail(*args: object, **kwargs: object) -> tuple[str, ...]:
            raise SaveError("SOURCE", "projection unavailable")

        with monkeypatch.context() as patch:
            patch.setattr("app.client_session.supply_support_plan", fail)
            with pytest.raises(SaveError, match="NPC_RECOLLECTION_SOURCE"):
                owner.act("bell")
        assert view(owner.update()).gate_open and view(owner.update()).npc_replies == 1
        after = state(owner)
        owner.retry()
        assert state(owner) == after
        assert owner.act("wait").status == "COMMITTED"
    finally:
        owner.close()
