"""Exercise the registered dungeon world with a delegated test encounter."""

from pathlib import Path

from app.world_catalog import AUTHORED_SUPPLY_SCENARIO, seeded_world
from app.headless import replay_runner
from app.world_combat_registry import combat_world_bundle
from app.world_dungeon_registry import dungeon_world_bundle
from app.world_session import world_command
from app.world_transport_registry import transport_world_bundle
from app.world_village_registry import village_world_bundle
from app.world_village_session import open_dungeon_world, open_knowledge_world
from contracts.replay import ReplayFixture
from contracts.turn import TurnCommitted, TurnRejected
from contracts.world_dungeon import DungeonAction
from contracts.world_time import WorldWait
from contracts.world_village import VillageStep
from domain.world_dungeon import ORC, DungeonRecord
from domain.world_travel import WORLD_ACTOR
from domain.world_village_layout import dungeon_blueprint
from tests.integration.test_world_knowledge import commit
from tests.integration.test_world_village import pipe, send
from domain.canonical import object_value


def test_dungeon_moves_and_uses_the_existing_turn_rules_across_reopen(tmp_path: Path) -> None:
    world, social, transport = seeded_world("3" * 64)
    path = tmp_path / "game.sqlite"
    scenario = AUTHORED_SUPPLY_SCENARIO
    args = (path, world, scenario, social, transport)
    with open_knowledge_world(*args, combat=True) as owner:
        for _ in range(4):
            commit(owner, VillageStep("right"))
        old = owner.snapshot()
    previous = path.read_bytes()
    with open_dungeon_world(*args) as owner:
        assert owner.working_path != path and path.read_bytes() == previous
        assert (
            tuple(row for row in owner.snapshot().components if not isinstance(row, DungeonRecord))
            == old.components
        )
        commit(owner, DungeonAction("enter"))
        action = world_command(owner.protocol(), DungeonAction("down"))
        rejected = owner.submit(action, attachment_id=owner.attachment_id).outcome
        assert isinstance(rejected, TurnRejected) and rejected.failure.code == "DUNGEON_WALL"
        assert owner.snapshot().tick == 5
        commit(owner, DungeonAction("left"))
        commit(owner, DungeonAction("up"))
        commit(owner, DungeonAction("engage"))
        snap = owner.snapshot()
        room = next(row.state for row in snap.components if isinstance(row, DungeonRecord))
        assert room.tile == (1, 2)
        assert room.combat.order == (WORLD_ACTOR, ORC)
        assert room.combat.bandit_hp == 3
        assert snap.tick == 8
    with open_dungeon_world(*args) as owner:
        assert owner.snapshot() == snap
        idle = world_command(owner.protocol(), WorldWait(1))
        result = owner.submit(idle, attachment_id=owner.attachment_id).outcome
        assert isinstance(result, TurnRejected) and result.failure.code == "DUNGEON_INSIDE"
        attack = world_command(owner.protocol(), DungeonAction("attack"))
        hit = owner.submit(attack, attachment_id=owner.attachment_id).outcome
        assert isinstance(hit, TurnCommitted) and hit.receipt.tick == 9
        assert owner.submit(attack, attachment_id=owner.attachment_id).outcome == hit
        commit(owner, DungeonAction("advance"))
        commit(owner, DungeonAction("attack"))
        commit(owner, DungeonAction("right"))
        commit(owner, DungeonAction("down"))
        commit(owner, DungeonAction("exit"))
        assert owner.snapshot().tick == 14
        room = next(
            row.state for row in owner.snapshot().components if isinstance(row, DungeonRecord)
        )
        assert room.tile is None and room.combat.bandit_hp == 0 and room.combat.player_hp == 4
        place = scenario.place_id
        old_bundle = transport_world_bundle(world, social, transport, scenario, knowledge=True)
        bundle = dungeon_world_bundle(
            combat_world_bundle(village_world_bundle(old_bundle, place), place),
            dungeon_blueprint(world, place),
            place,
        )
        retained = owner.retained_segment()
        assert (
            replay_runner(
                ReplayFixture(
                    retained.checkpoint.core, retained.checkpoint.protocol, retained.trace
                ),
                bundles=(bundle,),
            ).run(retained.trace)
            == ()
        )


def test_actual_village_pipe_opens_dungeon_and_commits_player_attack(tmp_path: Path) -> None:
    path = tmp_path / "dungeon.sqlite"
    seed = "3" * 64
    with pipe(path, seed=seed) as streams:
        assert send(streams, 1, "dungeon", "enter")["error"] == "DUNGEON_GATE"
        for seq in range(2, 6):
            send(streams, seq, "step", "right")
        entered = send(streams, 6, "dungeon", "enter")
        room = object_value(entered["dungeon"])
        assert (room["x"], room["y"], room["orc_hp"], room["active"]) == (2, 3, 5, False)
        assert send(streams, 7, "dungeon", "up")["error"] == "DUNGEON_OCCUPIED"
        send(streams, 8, "dungeon", "left")
        send(streams, 9, "dungeon", "up")
        opened = send(streams, 10, "dungeon", "engage")
        assert send(streams, 10, "dungeon", "engage") == opened
        room = object_value(opened["dungeon"])
        assert (room["player_hp"], room["orc_hp"], room["order"]) == (5, 3, ("나", "오크"))
        assert send(streams, 11, "dungeon", "wait")["error"] == "DUNGEON_COMBAT_ACTIVE"
    with pipe(path, seed=seed) as streams:
        resumed = send(streams, 1, "inspect")
        assert resumed["dungeon"] == room and resumed["tick"] == 8
        for request, op in enumerate(("attack", "advance", "attack", "right", "down", "exit"), 2):
            end = send(streams, request, "dungeon", op)
            assert end["error"] == ""
        room = object_value(end["dungeon"])
        assert room["inside"] is False and room["orc_hp"] == 0
        assert (end["x"], end["y"], end["tick"]) == (5, 7, 14)
