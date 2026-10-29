"""Physical aid reads prior NPC pose,not same-phase patrol arrival."""

import pytest
from contracts.messages import CommandPayload
from contracts.watch import BellCommand
from domain.watch import ReplyRecord
from app.npc_cycle import bootstrap_cycle, cycle_bundle
from app.watch import WatchBootstrapSpec
from contracts.turn import GameCommand, TurnCommitted
from contracts.quest import QuestTalkCommand
from contracts.trial import MoveCommand
from contracts.watch import WaitCommand
from domain.encounter import GateRecord
from domain.npc_cycle import CycleRecord, state_at
from domain.primitives import CommandId
from domain.watch import WatchNpcRecord
from tests.integration.test_memory_client_route import approved_content


def test_new_bundle_has_distinct_identity_with_existing_state_schemas() -> None:
    bundle = cycle_bundle(
        approved_content(),
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
        npc_ready_patrol=True,
        npc_reach_aid=True,
    )
    assert bundle.feature_id == "quest.harbor-reach-aid-v1"


def test_actual_prior_pose_cannot_open_on_arrival_but_can_before_moving_away() -> None:
    content = approved_content()
    owner = bootstrap_cycle(
        WatchBootstrapSpec("0" * 64, "1" * 32, "2" * 32),
        content,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
        npc_ready_patrol=True,
        npc_reach_aid=True,
    )
    actions = (
        MoveCommand(0, 1),
        QuestTalkCommand(content.definition.layout.npc_id),
        MoveCommand(0, -1),
        *(WaitCommand(1) for _ in range(13)),
    )
    observed = []
    for sequence, action in enumerate(actions, 1):
        command = GameCommand(
            CommandId(f"c1:{'1' * 32}:{'2' * 32}:{sequence}"),
            content.definition.layout.actor_id,
            owner.protocol().revision,
            action,
        )
        assert isinstance(owner.driver.submit(command), TurnCommitted)
        core = owner.snapshot()
        npc = next(x for x in core.components if type(x) is WatchNpcRecord)
        gate = next(x for x in core.components if type(x) is GateRecord)
        cycle = next(x for x in core.components if type(x) is CycleRecord)
        assert cycle.state == state_at(sequence)
        if sequence in (9, 10, 12, 14, 16):
            observed.append((sequence, npc.cell, gate.is_open, cycle.state.stock))
    assert observed == [(9, 6, 0, 2), (10, 7, 0, 1), (12, 6, 0, 2), (14, 7, 0, 2), (16, 6, 1, 3)]


@pytest.mark.parametrize(
    "bell_tick,npc_cell,stock,opened", ((11, 7, 1, 0), (13, 6, 2, 0), (15, 7, 2, 1))
)
def test_actual_odd_call_requires_both_prior_stock_and_adjacent_pose(
    bell_tick: int,
    npc_cell: int,
    stock: int,
    opened: int,
) -> None:
    content = approved_content()
    owner = bootstrap_cycle(
        WatchBootstrapSpec("0" * 64, "1" * 32, "2" * 32),
        content,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
        npc_call_pause=True,
        npc_ready_patrol=True,
        npc_reach_aid=True,
    )
    for sequence in range(1, bell_tick + 1):
        action: CommandPayload
        if sequence == 1:
            action = MoveCommand(0, 1)
        elif sequence == 2:
            action = QuestTalkCommand(content.definition.layout.npc_id)
        elif sequence == 3:
            action = MoveCommand(0, -1)
        elif sequence == bell_tick:
            action = BellCommand(content.definition.layout.npc_id)
        else:
            action = WaitCommand(1)
        command = GameCommand(
            CommandId(f"c1:{'1' * 32}:{'2' * 32}:{sequence}"),
            content.definition.layout.actor_id,
            owner.protocol().revision,
            action,
        )
        assert isinstance(owner.driver.submit(command), TurnCommitted)
    core = owner.snapshot()
    npc = next(x for x in core.components if type(x) is WatchNpcRecord)
    gate = next(x for x in core.components if type(x) is GateRecord)
    cycle = next(x for x in core.components if type(x) is CycleRecord)
    replies = next(x for x in core.components if type(x) is ReplyRecord)
    assert (core.tick, npc.cell, cycle.state.stock, gate.is_open, replies.count) == (
        bell_tick,
        npc_cell,
        stock,
        opened,
        1,
    )
