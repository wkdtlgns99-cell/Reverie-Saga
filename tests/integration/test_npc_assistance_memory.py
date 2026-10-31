"""Independent registered-mode assistance-memory and durability vectors."""

from app.npc_cycle import bootstrap_cycle, cycle_bundle
from app.watch import WatchBootstrapSpec
from contracts.npc_gate_aid import GateAssisted
from contracts.quest import QuestTalkCommand
from contracts.trial import MoveCommand
from contracts.turn import GameCommand, TurnCommitted
from contracts.watch import WaitCommand
from domain.npc_assistance_memory import AssistanceMemoryRecord
from domain.primitives import CommandId
from tests.integration.test_memory_client_route import approved_content

PARENT_FLAGS = dict(
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
CHILD_FLAGS = dict(PARENT_FLAGS, npc_assistance_memory=True)


def test_child_mode_has_its_own_registered_identity() -> None:
    content = approved_content()
    parent = cycle_bundle(content, **PARENT_FLAGS)
    child = cycle_bundle(content, **CHILD_FLAGS)
    assert parent.feature_id == "quest.harbor-reach-aid-v1"
    assert child.feature_id == "quest.harbor-assistance-memory-v1"
    assert child.schema_document != parent.schema_document
    assert child.rules_document != parent.rules_document


def test_real_repeated_aids_retain_total_five_and_latest_four() -> None:
    content = approved_content()
    owner = bootstrap_cycle(
        WatchBootstrapSpec("0" * 64, "1" * 32, "2" * 32), content, **CHILD_FLAGS
    )
    actions = [
        MoveCommand(0, 1),
        QuestTalkCommand(content.definition.layout.npc_id),
        MoveCommand(0, -1),
    ]
    from contracts.encounter import InteractCommand
    from contracts.messages import CommandPayload

    sequence = 0
    observed = []

    def submit(action: CommandPayload) -> None:
        nonlocal sequence
        sequence += 1
        outcome = owner.driver.submit(
            GameCommand(
                CommandId(f"c1:{'1' * 32}:{'2' * 32}:{sequence}"),
                content.definition.layout.actor_id,
                owner.protocol().revision,
                action,
            )
        )
        assert isinstance(outcome, TurnCommitted), outcome
        for event in owner.last_publication().facts:
            if type(event.payload) is GateAssisted:
                observed.append((event.due_tick, event.header.caused_by[0]))

    for action in actions:
        submit(action)
    submit(WaitCommand(13))
    submit(MoveCommand(0, 1))
    submit(InteractCommand(content.definition.layout.gate_id, "close"))
    submit(WaitCommand(2))
    for _ in range(3):
        submit(InteractCommand(content.definition.layout.gate_id, "close"))
        submit(WaitCommand(3))
    assert [tick for tick, _ in observed] == [16, 20, 24, 28, 32]
    record = next(r for r in owner.snapshot().components if type(r) is AssistanceMemoryRecord)
    assert record.state.total_assists == 5
    assert [entry.tick for entry in record.state.entries] == [20, 24, 28, 32]
    assert [entry.cause_event_id for entry in record.state.entries] == [
        cause for _, cause in observed[1:]
    ]
    assert all(entry.source_kind == "wake" for entry in record.state.entries)
