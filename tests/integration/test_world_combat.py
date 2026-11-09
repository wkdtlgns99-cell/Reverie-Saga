"""The registered village combat owner, durable migration and retained replay."""

from pathlib import Path

import pytest

from app.headless import replay_runner
from app.world_catalog import AUTHORED_SUPPLY_SCENARIO, load_social, load_transport, load_world
from app.world_combat_registry import combat_world_bundle
from app.world_observer import read_world
from app.world_session import world_command
from app.world_transport_registry import transport_world_bundle
from app.world_village_registry import village_world_bundle
from app.world_village_session import open_knowledge_world
from contracts.replay import ReplayFixture
from contracts.turn import TurnCommitted, TurnRejected
from contracts.world_combat import CombatAction
from contracts.world_time import WorldWait
from contracts.world_village import VillageStep
from domain.canonical import object_value
from domain.primitives import EntityId
from domain.world import elaborate_place
from domain.world_combat import BANDIT, CombatRecord, OpeningActor, opening_order
from domain.world_transport import SupplyProgressRecord
from domain.world_travel import WORLD_ACTOR
from domain.world_village import VillagePosition, VillageRecord
from tests.integration.test_world_knowledge import commit
from tests.integration.test_world_village import pipe, send


def test_opening_area_counts_each_living_actor_near_either_end_once() -> None:
    attacker = OpeningActor(EntityId("actor:attacker"), 6, 5, speed=2, advantage=2)
    target = OpeningActor(EntityId("actor:target"), 6, 3, speed=3)
    behind_wall = OpeningActor(EntityId("actor:guard"), 3, 5, speed=2, readiness=2)
    overlap = OpeningActor(EntityId("actor:overlap"), 7, 4, speed=2)
    target_side = OpeningActor(EntityId("actor:target-side"), 6, 1, speed=1)
    distant = OpeningActor(EntityId("actor:distant"), 10, 5, speed=5)
    defeated = OpeningActor(EntityId("actor:defeated"), 7, 5, speed=5, alive=False)
    assert opening_order(
        (target_side, target, distant, behind_wall, overlap, attacker, defeated), attacker, target
    ) == (
        attacker.actor_id,
        behind_wall.actor_id,
        target.actor_id,
        overlap.actor_id,
        target_side.actor_id,
    )


def test_opening_positions_and_each_participant_commit_in_the_current_world(tmp_path: Path) -> None:
    path = tmp_path / "world.sqlite"
    world = load_world()
    scenario, social, transport = (
        AUTHORED_SUPPLY_SCENARIO,
        load_social(world),
        load_transport(world),
    )
    courier, merchant, *_ = elaborate_place(world, scenario.place_id).residents
    args = (path, world, scenario, social, transport)
    with open_knowledge_world(*args, village=True) as owner:
        for direction in ("right",) * 8:
            commit(owner, VillageStep(direction))
        owner.export("slot01")
    previous_bytes = path.read_bytes()

    with open_knowledge_world(*args, village=True, combat=True) as owner:
        assert owner.working_path != path and path.read_bytes() == previous_bytes
        assert next(
            row.state for row in owner.snapshot().components if isinstance(row, VillageRecord)
        ) == VillagePosition(9, 7)
        assert owner.snapshot().tick == 8
        blocked = owner.submit(
            world_command(owner.protocol(), WorldWait(1)), attachment_id=owner.attachment_id
        ).outcome
        assert (
            isinstance(blocked, TurnRejected) and blocked.failure.code == "VILLAGE_AMBUSH_PENDING"
        )
        commit(owner, CombatAction("ambush"))
        opened = next(
            row.state for row in owner.snapshot().components if isinstance(row, CombatRecord)
        )
        assert opened.order == (BANDIT, WORLD_ACTOR, courier.id)
        assert merchant.id not in opened.order
        assert (opened.player_hp, opened.bandit_hp, opened.last_actor) == (4, 5, BANDIT)
        assert owner.snapshot().tick == 9
        for invalid, error in (
            (WorldWait(1), "VILLAGE_COMBAT_ACTIVE"),
            (VillageStep("up"), "VILLAGE_COMBAT_ACTIVE"),
            (CombatAction("attack"), "COMBAT_WRONG_TURN"),
        ):
            result = owner.submit(
                world_command(owner.protocol(), invalid), attachment_id=owner.attachment_id
            ).outcome
            assert isinstance(result, TurnRejected) and result.failure.code == error
            assert owner.snapshot().tick == 9
        action = world_command(owner.protocol(), CombatAction("advance"))
        result = owner.submit(action, attachment_id=owner.attachment_id).outcome
        assert isinstance(result, TurnCommitted) and result.receipt.tick == 10
        assert owner.submit(action, attachment_id=owner.attachment_id).outcome == result
        after_bandit = owner.snapshot()
        assert (
            next(
                row.state
                for row in after_bandit.components
                if isinstance(row, SupplyProgressRecord)
            )
            == 10
        )

    with open_knowledge_world(*args) as owner:
        assert owner.snapshot() == after_bandit
        commit(owner, CombatAction("attack"))
        current = next(
            row.state for row in owner.snapshot().components if isinstance(row, CombatRecord)
        )
        assert (current.player_hp, current.bandit_hp, current.current) == (3, 3, courier.id)
        commit(owner, CombatAction("advance"))
        assert owner.snapshot().tick == 12
        current = next(
            row.state for row in owner.snapshot().components if isinstance(row, CombatRecord)
        )
        assert (current.current, current.last_actor, current.last_action) == (
            BANDIT,
            courier.id,
            "hold",
        )
        retained = owner.retained_segment()
        bundle = combat_world_bundle(
            village_world_bundle(
                transport_world_bundle(world, social, transport, scenario, knowledge=True),
                scenario.place_id,
            ),
            scenario.place_id,
        )
        checkpoint = retained.checkpoint
        assert (
            replay_runner(
                ReplayFixture(checkpoint.core, checkpoint.protocol, retained.trace),
                bundles=(bundle,),
            ).run(retained.trace)
            == ()
        )
        owner.load("slot01")
        assert owner.snapshot().tick == 8
        assert (
            next(
                row.state for row in owner.snapshot().components if isinstance(row, CombatRecord)
            ).last_action
            == ""
        )


def test_registered_village_pipe_preserves_active_combat_and_returns_to_idle(
    tmp_path: Path,
) -> None:
    path = tmp_path / "world.sqlite"
    with pipe(path) as streams:
        for request in range(1, 8):
            result = send(streams, request, "step", "right")
            assert object_value(result["world_combat"])["active"] is False
            assert result["tick"] == request
        result = send(streams, 8, "step", "right")
        assert send(streams, 8, "step", "right") == result
        combat = object_value(result["world_combat"])
        assert combat["order"] == ("도적", "나", "운송인")
        assert (combat["last_actor"], combat["player_hp"], result["tick"]) == ("도적", 4, 9)
        result = send(streams, 9, "world-combat", "advance")
        assert result["tick"] == 10
        assert object_value(result["world_combat"])["player_hp"] == 3
    assert read_world(path)["tick"] == 10
    with pipe(path) as streams:
        assert send(streams, 1, "inspect") == {**result, "id": 1}
        for request, action in enumerate(
            ("attack", "advance", "advance", "attack", "advance", "advance", "attack"), start=2
        ):
            result = send(streams, request, "world-combat", action)
            assert result["tick"] == request + 9
        assert result["available"] is True and result["tick"] == 17
        assert object_value(result["world_combat"])["bandit_hp"] == 0
        assert send(streams, 9, "idle", "1")["tick"] == 18


def test_reopen_committed_arrival_starts_ambush_once(tmp_path: Path) -> None:
    path = tmp_path / "world.sqlite"
    world = load_world()
    scenario = AUTHORED_SUPPLY_SCENARIO
    with open_knowledge_world(
        path, world, scenario, load_social(world), load_transport(world), combat=True
    ) as owner:
        for _ in range(8):
            commit(owner, VillageStep("right"))
    with pipe(path) as streams:
        started = send(streams, 1, "inspect")
        assert started["tick"] == 9
        assert object_value(started["world_combat"])["player_hp"] == 4
    with pipe(path) as streams:
        assert send(streams, 1, "inspect") == started


@pytest.mark.parametrize("proof", ("committed", "absent"))
def test_ambush_recovers_or_retries_without_repeating_the_step(tmp_path: Path, proof: str) -> None:
    path = tmp_path / "world.sqlite"
    with pipe(path, opening_fault=f"ambush-{proof}") as streams:
        for request in range(1, 8):
            send(streams, request, "step", "right")
        arrival = send(streams, 8, "step", "right")
        assert (arrival["x"], arrival["y"]) == (9, 7)
        assert send(streams, 8, "step", "right") == arrival
        if proof == "absent":
            assert (arrival["error"], arrival["tick"]) == ("SAVE_UNAVAILABLE", 8)
            assert object_value(arrival["world_combat"])["ambush_pending"] is True
            blocked = send(streams, 9, "step", "right")
            assert (blocked["error"], blocked["tick"]) == ("VILLAGE_AMBUSH_PENDING", 8)
            arrival = send(streams, 10, "inspect")
        assert (arrival["error"], arrival["tick"], arrival["revision"]) == ("", 9, 9)
        assert object_value(arrival["world_combat"])["player_hp"] == 4
    with pipe(path) as streams:
        assert send(streams, 1, "inspect") == {**arrival, "id": 1}
