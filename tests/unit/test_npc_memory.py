from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from typing import cast

import pytest

from app.headless import state_io
from app.npc_memory import memory_bundle
from contracts.errors import BootstrapError, CandidateError, ExpiredReadView, ReadOnlyViolation
from contracts.npc_memory import MEMORY, MEMORY_FAMILY, MemoryDelta, MemoryPatch
from contracts.read_views import AdapterBinding, ViewEpoch
from domain.npc_memory import NpcQuestMemoryRecord, QuestEvidence
from domain.primitives import EntityId, Phase, Tick
from domain.state_types import StoredRoot
from engines.npc_memory import NpcQuestMemory
from orchestration.npc_memory import (
    MemoryAdapter,
    MemoryCodec,
    MemoryPatchRoute,
    MemoryPayloadCodec,
    MemoryReducer,
)
from orchestration.read_views import ObservedReadViewFactory
from tests.unit.quest_fixtures import content

OWNER = EntityId("actor:harbor-watcher")
ACCEPT = QuestEvidence("accepted", 2, "e1-" + "a" * 64)
REPORT = QuestEvidence("completion_reported", 11, "e1-" + "b" * 64)


@pytest.mark.parametrize("bad", (True, 0, -1, 1.5, "2", 2**63))
def test_evidence_tick_exact_type_and_range(bad: object) -> None:
    with pytest.raises(ValueError):
        QuestEvidence("accepted", cast(int, bad), ACCEPT.source_event_id)


@pytest.mark.parametrize("source", ("", "e1-abcd", "e1-" + "A" * 64, "x1-" + "a" * 64))
def test_evidence_source_format(source: str) -> None:
    with pytest.raises(ValueError, match="NPC_MEMORY_SOURCE"):
        QuestEvidence("accepted", 2, source)


@pytest.mark.parametrize(
    "entries",
    (
        (REPORT,),
        (ACCEPT, ACCEPT),
        (ACCEPT, REPORT, REPORT),
        (ACCEPT, replace(REPORT, observed_at=2)),
        (ACCEPT, replace(REPORT, source_event_id=ACCEPT.source_event_id)),
    ),
)
def test_entry_order_capacity_and_identity(entries: tuple[QuestEvidence, ...]) -> None:
    with pytest.raises(ValueError):
        NpcQuestMemoryRecord(OWNER, entries)


def test_codec_freezing_append_only_and_composition() -> None:
    selected = content()
    empty = NpcQuestMemoryRecord(OWNER, ())
    accepted = replace(empty, entries=(ACCEPT,))
    reported = replace(empty, entries=(ACCEPT, REPORT))
    codec = MemoryCodec(selected)
    assert codec.decode(OWNER, codec.encode(reported)) == reported
    with pytest.raises(FrozenInstanceError):
        reported.entries = ()  # type: ignore[misc]
    reducer = MemoryReducer(selected)
    first, second = MemoryDelta(empty, accepted), MemoryDelta(accepted, reported)
    net = reducer.compose((first, second))
    assert net == MemoryDelta(empty, reported)
    assert (
        MemoryPayloadCodec(net.schema, selected).decode(
            MemoryPayloadCodec(net.schema, selected).encode(net)
        )
        == net
    )
    with pytest.raises(CandidateError, match="INVALID_DELTA"):
        reducer.compose((net,))
    with pytest.raises(CandidateError, match="INVALID_DELTA"):
        reducer.compose((second, first))
    with pytest.raises(ValueError, match="NPC_MEMORY_APPEND"):
        MemoryPatchRoute(selected).apply(reported, MemoryPatch(accepted))


def test_read_view_observes_and_expires_all_scalar_fields() -> None:
    record = NpcQuestMemoryRecord(OWNER, (ACCEPT, REPORT))
    factory = ObservedReadViewFactory(StoredRoot((record,), 0))
    AdapterBinding(MemoryAdapter(content())).install(factory)
    epoch = ViewEpoch(Tick(11), Phase.POST_TICK, 0, "quest.memory", 0)
    view = factory.open(epoch).component(MEMORY, OWNER)
    assert (view.accepted_at, view.reported_at, view.acceptance_source, view.report_source) == (
        2,
        11,
        ACCEPT.source_event_id,
        REPORT.source_event_id,
    )
    with pytest.raises(ReadOnlyViolation):
        view.accepted_at = 4  # type: ignore[misc]
    observations = factory.close(epoch)
    assert all(observation.target.family == MEMORY_FAMILY for observation in observations)
    for name in ("accepted_at", "reported_at", "acceptance_source", "report_source"):
        with pytest.raises(ExpiredReadView):
            getattr(view, name)


@pytest.mark.parametrize("damage", ("declaration", "engine", "content", "adapter"))
def test_existing_quest_binding_covers_memory_roles(damage: str) -> None:
    selected = content()
    bundle = memory_bundle(selected)
    if damage == "declaration":
        rules = dict(bundle.rules_document)
        del rules["quest"]
        bundle = replace(bundle, rules_document=rules)
    elif damage == "engine":
        bundle = replace(bundle, bindings=bundle.bindings[:-1])
    elif damage == "adapter":
        bundle = replace(bundle, read_adapters=bundle.read_adapters[:-1])
    else:
        different = replace(
            selected,
            dialogue=replace(
                selected.dialogue,
                lines=(
                    replace(selected.dialogue.lines[0], text_ko="다른 대사"),
                    *selected.dialogue.lines[1:],
                ),
            ),
        )
        bundle = replace(
            bundle,
            bindings=(
                *bundle.bindings[:-1],
                replace(bundle.bindings[-1], engine=NpcQuestMemory(different)),
            ),
        )
    with pytest.raises(BootstrapError):
        state_io((bundle,))
