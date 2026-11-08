"""Drive the same one-shot Python commands that the Unity supply panel launches."""

from pathlib import Path
import sqlite3
import subprocess
import sys

from adapters.world_attachment import remember_world
from app.world_catalog import AUTHORED_SUPPLY_SCENARIO, load_social, load_transport, load_world
from app.world_observer import read_world
from app.world_session import open_world_session
from contracts.world_conversation import PlayerSay
from domain.canonical import JsonObject, decode_json, object_value, text_value
from domain.world import elaborate_place
from tests.integration.test_world_knowledge import commit


def run_bridge(path: Path, token: str | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "app.world_supply_bridge",
            "--working",
            str(path),
            *(("--confirm", token) if token is not None else ()),
        ],
        capture_output=True,
        check=False,
        timeout=15,
    )


def preview(path: Path, token: str | None = None) -> JsonObject:
    result = run_bridge(path, token)
    assert result.returncode == 0 and not result.stderr, result
    view = object_value(decode_json(result.stdout))
    assert view["format"] == "reverie-world-supply/v1"
    return view


def test_unity_request_sequence_completes_once_without_ai(tmp_path: Path) -> None:
    path = tmp_path / "working.sqlite"
    view = preview(path)
    assert (view["tick"], view["revision"], view["cargo"], view["gold"]) == (0, 0, 0, 0)
    original = path.read_bytes()
    assert preview(path) == view
    assert path.read_bytes() == original

    actions = (
        ("1초 기다리기", "게임 시간 1초", 0, 0),
        ("의뢰 받기", "보급품 2개", 0, 0),
        ("상자 받기", "현재 수령 0/2개", 1, 0),
        ("상자 받기", "현재 수령 1/2개", 2, 0),
        ("상자 전달하기", "보상 5금", 0, 5),
    )
    for revision, (label, terms, cargo, gold) in enumerate(actions, 1):
        assert view["has_offer"] is True
        offer = object_value(view["offer"])
        assert offer["label"] == label and terms in text_value(offer["terms"])
        token = text_value(offer["token"])
        view = preview(path, token)
        assert (view["error"], view["tick"], view["revision"], view["cargo"], view["gold"]) == (
            "",
            revision,
            revision,
            cargo,
            gold,
        )
        before = path.read_bytes()
        assert preview(path, token) == {
            **view,
            "error": "WORLD_SUPPLY_STALE",
            "notice": "세계를 불러왔습니다.",
        }
        assert path.read_bytes() == before
    assert view["has_offer"] is False and view["offer"] is None
    assert "보급로 복구 완료" in text_value(view["status"])
    observed = read_world(path)
    assert (observed["quest_phase"], observed["resolved_tick"], observed["revision"]) == (
        "완료",
        5,
        5,
    )


def test_existing_owner_and_branch_replacement_reject_old_offer(tmp_path: Path) -> None:
    path = tmp_path / "working.sqlite"
    initial = preview(path)
    wait = text_value(object_value(initial["offer"])["token"])
    offer = preview(path, wait)
    accept = text_value(object_value(offer["offer"])["token"])
    world = load_world()
    with open_world_session(
        path,
        world,
        supply=AUTHORED_SUPPLY_SCENARIO,
        social=load_social(world),
        transport=load_transport(world),
        knowledge=True,
    ) as owner:
        before = path.read_bytes()
        result = run_bridge(path, accept)
        assert result.returncode == 2 and not result.stdout
        assert result.stderr.decode().strip() == "SAVE_LOCKED"
        assert path.read_bytes() == before
        owner.export("slot01")
        owner.load("slot01")
        remember_world(path, owner.working_path)
        branch = owner.working_path
    before = branch.read_bytes()
    changed = preview(path, accept)
    assert changed["error"] == "WORLD_SUPPLY_STALE" and changed["revision"] == 1
    assert object_value(changed["offer"])["token"] != accept
    assert branch.read_bytes() == before


def test_same_confirmation_can_retry_after_a_reader_aborts_the_write(tmp_path: Path) -> None:
    path = tmp_path / "working.sqlite"
    first = preview(path)
    opened = preview(path, text_value(object_value(first["offer"])["token"]))
    accept = text_value(object_value(opened["offer"])["token"])
    before = path.read_bytes()
    reader = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, autocommit=True)
    try:
        reader.execute("BEGIN")
        assert reader.execute("SELECT count(*) FROM save_head").fetchone() == (1,)
        result = run_bridge(path, accept)
        assert result.returncode == 2 and not result.stdout
        assert result.stderr.decode().strip() == "SAVE_UNAVAILABLE"
    finally:
        reader.close()
    assert path.read_bytes() == before
    accepted = preview(path, accept)
    assert (accepted["revision"], accepted["cargo"], accepted["error"]) == (2, 0, "")
    assert object_value(accepted["offer"])["label"] == "상자 받기"


def test_invalid_or_missing_confirmation_does_not_create_progress(tmp_path: Path) -> None:
    path = tmp_path / "missing" / "working.sqlite"
    for token, code in (
        ("bad", "WORLD_SUPPLY_CONFIRMATION_INVALID"),
        ("a" * 64, "SAVE_NOT_FOUND"),
    ):
        result = run_bridge(path, token)
        assert result.returncode == 2 and not result.stdout
        assert result.stderr.decode().strip() == code
        assert not path.parent.exists()


def test_unfinished_committed_speech_hides_actions(tmp_path: Path) -> None:
    path = tmp_path / "working.sqlite"
    world = load_world()
    scenario = AUTHORED_SUPPLY_SCENARIO
    courier = elaborate_place(world, scenario.place_id).residents[0]
    with open_world_session(
        path,
        world,
        supply=scenario,
        social=load_social(world),
        transport=load_transport(world),
        knowledge=True,
    ) as owner:
        commit(owner, PlayerSay(courier.id, "가" * 100))
    view = preview(path)
    assert view["offer"] is None and "진행 중인 발언" in text_value(view["notice"])
