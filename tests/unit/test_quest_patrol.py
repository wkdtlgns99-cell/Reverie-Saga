"""Own memory is the bounded authority for the new opt-in patrol goal."""

from dataclasses import fields, replace
from pathlib import Path
from typing import cast

import pytest

from app.client_session import ClientSession
from app.client_worker import ClientWorker
from app.npc_cycle import cycle_bundle
from app.npc_patrol_status import quest_patrol_plan
from contracts.errors import CandidateError
from contracts.npc_memory import MEMORY_FAMILY
from contracts.npc_patrol import NpcPatrolled
from contracts.persistence import SaveError
from contracts.read_views import AdapterBinding, ViewEpoch
from contracts.turn import EngineInvocation, PhaseAccess
from domain.npc_memory import NpcQuestMemoryRecord, QuestEvidence
from domain.primitives import Phase, Tick
from domain.state_types import StoredRoot
from domain.trial import CellPositionRecord
from domain.watch import WatchNpcRecord
from engines.watch import WatchNpc
from orchestration.npc_memory import MemoryAdapter
from orchestration.read_views import ObservedReadViewFactory
from orchestration.trial import CellPositionAdapter
from orchestration.watch import WatchNpcAdapter
from tests.integration.test_memory_client_route import approved_content
from tests.integration.test_quest_patrol import session
from tests.unit.quest_fixtures import content
from tests.unit.test_npc_patrol import invocation
from tests.unit.test_talk_pause_patrol import spoken


def memory(count: int) -> NpcQuestMemoryRecord:
    return NpcQuestMemoryRecord(
        content().definition.layout.npc_id,
        (
            QuestEvidence("accepted", 1, "e1-" + "1" * 64),
            QuestEvidence("completion_reported", 2, "e1-" + "2" * 64),
        )[:count],
    )


def engine() -> WatchNpc:
    selected = content()
    return WatchNpc(
        selected.definition.layout,
        npc_patrol=True,
        talk_pause_quest=selected.definition.quest_id,
        quest_patrol=True,
    )


def observed(
    count: int, current: int = 6, actor: int = 0, *, future: bool = False
) -> tuple[EngineInvocation, ObservedReadViewFactory, ViewEpoch]:
    selected = content()
    layout = selected.definition.layout
    record = memory(count)
    if future:
        record = replace(record, entries=(replace(record.entries[0], observed_at=3),))
    factory = ObservedReadViewFactory(
        StoredRoot(
            (
                record,
                CellPositionRecord(layout.actor_id, layout.space_id, actor),
                WatchNpcRecord(layout.npc_id, layout.space_id, current, 1),
            ),
            0,
        )
    )
    AdapterBinding(MemoryAdapter(selected)).install(factory)
    AdapterBinding(CellPositionAdapter(layout)).install(factory)
    AdapterBinding(WatchNpcAdapter(layout, npc_patrol=True)).install(factory)
    epoch = ViewEpoch(Tick(2), Phase.POST_TICK, 0, "watch.npc", 0)
    return replace(invocation(), state=factory.open(epoch)), factory, epoch


@pytest.mark.parametrize("count,phase", ((0, "available"), (1, "accepted"), (2, "reported")))
def test_derived_phase_does_not_add_a_saved_field(count: int, phase: str) -> None:
    record = memory(count)
    assert record.known_phase == phase
    assert tuple(field.name for field in fields(record)) == ("entity_id", "entries")
    with pytest.raises((AttributeError, TypeError)):
        setattr(record, "known_phase", "reported")


@pytest.mark.parametrize(
    "count,current,actor,target",
    (
        (0, 6, 0, None),
        (0, 6, 6, None),
        (1, 6, 0, 7),
        (1, 7, 0, 6),
        (1, 6, 7, None),
        (1, 7, 6, None),
        (1, 7, 7, 6),
        (2, 7, 0, 6),
        (2, 7, 6, None),
        (2, 7, 7, 6),
        (2, 6, 0, None),
        (2, 6, 6, None),
    ),
)
def test_own_knowledge_goal_and_destination_occupancy(
    count: int, current: int, actor: int, target: int | None
) -> None:
    call, factory, epoch = observed(count, current, actor)
    result = engine().evaluate(call)
    if target is None:
        assert result.deltas == () and result.facts == ()
    else:
        assert len(result.deltas) == len(result.facts) == 1
        assert isinstance(result.facts[0].payload, NpcPatrolled)
        assert result.facts[0].payload.after_cell == target
        assert result.facts[0].caused_by == (call.incoming[0].header.event_id,)
    accesses = factory.close(epoch)
    assert any(access.target.family == MEMORY_FAMILY for access in accesses)
    assert all(access.operation != "write" for access in accesses)


@pytest.mark.parametrize("count,current", ((0, 6), (1, 6), (1, 7), (2, 7), (2, 6)))
def test_actual_speech_holds_even_a_pending_return(count: int, current: int) -> None:
    call, _, _ = observed(count, current)
    result = engine().evaluate(replace(call, incoming=(*call.incoming, spoken())))
    assert result.deltas == () and result.facts == ()


@pytest.mark.parametrize("paused", (False, True))
@pytest.mark.parametrize("damage", ("future", "unheard_neighbor"))
def test_invalid_memory_pose_rejected_before_pause_or_idle(damage: str, paused: bool) -> None:
    call, _, _ = observed(
        1 if damage == "future" else 0,
        7 if damage == "unheard_neighbor" else 6,
        future=damage == "future",
    )
    if paused:
        call = replace(call, incoming=(*call.incoming, spoken()))
    with pytest.raises(CandidateError) as caught:
        engine().evaluate(call)
    assert caught.value.code == "INVALID_FACT"
    assert "quest patrol" in str(caught.value)


@pytest.mark.parametrize("bad", (0, 1, None, "1", 2.0, True))
def test_engine_selection_requires_exact_bool_and_conversation_parent(bad: object) -> None:
    with pytest.raises(ValueError, match="^NPC_QUEST_PATROL_CONTENT$"):
        WatchNpc(content().definition.layout, npc_patrol=True, quest_patrol=cast(bool, bad))


@pytest.mark.parametrize("factory", (ClientSession, ClientWorker))
@pytest.mark.parametrize("bad", (0, 1, None, "1", 2.0, True))
def test_selection_failure_precedes_working_file_and_thread(
    factory: type[ClientSession] | type[ClientWorker], bad: object, tmp_path: Path
) -> None:
    selected = approved_content()
    path = tmp_path / "missing/game.sqlite"
    with pytest.raises(ValueError, match="^NPC_QUEST_PATROL_CONTENT$"):
        factory(
            path,
            selected.definition.layout,
            quest_content=selected,
            npc_memory=True,
            npc_cycle=True,
            npc_aid=True,
            npc_supply_aid=True,
            npc_call_aid=True,
            npc_patrol=True,
            npc_quest_patrol=cast(bool, bad),
        )
    assert not path.parent.exists()


def test_new_manifest_adds_only_declared_own_memory_read() -> None:
    selected = content()
    old = WatchNpc(
        selected.definition.layout, npc_patrol=True, talk_pause_quest=selected.definition.quest_id
    ).manifest
    new = engine().manifest
    assert new.reads == (*old.reads, PhaseAccess(Phase.POST_TICK, MEMORY_FAMILY))
    assert (new.writes, new.consumes, new.emits, new.phases) == (
        old.writes,
        old.consumes,
        old.emits,
        old.phases,
    )
    old_bundle = cycle_bundle(
        selected,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
    )
    new_bundle = cycle_bundle(
        selected,
        npc_aid=True,
        npc_supply_aid=True,
        npc_call_aid=True,
        npc_patrol=True,
        npc_talk_pause=True,
        npc_quest_patrol=True,
    )
    assert new_bundle.schema_document == old_bundle.schema_document
    assert new_bundle.feature_id == "quest.harbor-quest-patrol-v1"
    assert new_bundle.rules_document != old_bundle.rules_document
    spec = next(spec for spec in new_bundle.field_specs if spec.family == MEMORY_FAMILY)
    assert "watch.npc" in spec.consumers
    assert spec.owner_id != "watch.npc"


@pytest.mark.parametrize(
    "damage",
    (
        "missing_memory",
        "missing_npc",
        "duplicate_memory",
        "foreign_npc",
        "cell",
        "bool_cell",
        "space",
        "future",
        "unheard_neighbor",
    ),
)
@pytest.mark.parametrize("code", ("NPC_ACTIVITY_SOURCE", "NPC_RECOLLECTION_SOURCE"))
def test_plan_rejects_invalid_current_source_with_callers_code(
    damage: str, code: str, tmp_path: Path
) -> None:
    owner = session(tmp_path / "game.sqlite")
    try:
        core = owner.owner.snapshot()
        selected = approved_content()
        layout = selected.definition.layout
        records = list(core.components)
        mem = next(r for r in records if type(r) is NpcQuestMemoryRecord)
        npc = next(r for r in records if type(r) is WatchNpcRecord)
        if damage == "missing_memory":
            records.remove(mem)
        elif damage == "missing_npc":
            records.remove(npc)
        elif damage == "duplicate_memory":
            records.append(mem)
        elif damage == "foreign_npc":
            records[records.index(npc)] = replace(npc, entity_id=layout.actor_id)
        elif damage == "future":
            records[records.index(mem)] = memory(1)
        else:
            records[records.index(npc)] = replace(
                npc,
                cell=True
                if damage == "bool_cell"
                else 5
                if damage == "cell"
                else 7
                if damage == "unheard_neighbor"
                else 6,
                space_id=layout.actor_id if damage == "space" else layout.space_id,
            )
        with pytest.raises(SaveError) as caught:
            quest_patrol_plan(replace(core, components=tuple(records)), layout, error_code=code)
        assert caught.value.code == code
    finally:
        owner.close()
