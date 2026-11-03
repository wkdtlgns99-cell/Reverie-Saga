"""Contract vectors are independent of the encounter writer and retained facts."""

from dataclasses import replace
from typing import cast

import pytest

from contracts.errors import CandidateError
from contracts.npc_assistance_memory import AssistanceMemoryDelta, AssistanceMemoryPatch
from domain.npc_assistance_memory import (
    AssistanceEntry,
    AssistanceMemory,
    AssistanceMemoryRecord,
    append_assistance,
    validate_checkpoint,
    validate_transition,
)
from domain.primitives import EntityId, MAX_INT
from orchestration.npc_assistance_memory import (
    AssistanceAdapter,
    AssistanceCodec,
    AssistancePatchRoute,
    AssistancePayloadCodec,
    AssistanceReducer,
    decode_state,
    encode_state,
)
from tests.integration.test_memory_client_route import approved_content
from contracts.errors import ExpiredReadView, ReadOnlyViolation
from contracts.read_views import AdapterBinding, ViewEpoch
from contracts.npc_assistance_memory import ASSISTANCE_MEMORY, ASSISTANCE_FAMILY
from domain.primitives import Tick, Phase
from domain.state_types import StoredRoot
from orchestration.read_views import ObservedReadViewFactory


LAYOUT = approved_content().definition.layout


def test_observed_read_tracks_owner_and_expires() -> None:
    record = AssistanceMemoryRecord(LAYOUT.npc_id, AssistanceMemory(0, ()))
    factory = ObservedReadViewFactory(StoredRoot((record,), 0))
    AdapterBinding(AssistanceAdapter(approved_content())).install(factory)
    epoch = ViewEpoch(Tick(1), Phase.POST_TICK, 0, "encounter.actions", 0)
    view = factory.open(epoch).component(ASSISTANCE_MEMORY, LAYOUT.npc_id)
    assert view.state == record.state
    with pytest.raises(ReadOnlyViolation):
        setattr(view, "state", AssistanceMemory(0, ()))
    observations = factory.close(epoch)
    assert observations and all(
        o.target.family == ASSISTANCE_FAMILY and o.target.entity_id == LAYOUT.npc_id
        for o in observations
    )
    with pytest.raises(ExpiredReadView):
        _ = view.state


def entry(tick: int) -> AssistanceEntry:
    return AssistanceEntry(tick, LAYOUT.gate_id, "answered_call", "e1-" + f"{tick:064x}")


def history(count: int) -> AssistanceMemory:
    return AssistanceMemory(
        count, tuple(entry(tick) for tick in range(max(1, count - 3), count + 1))
    )


@pytest.mark.parametrize("value", (True, -1, MAX_INT + 1, 1.0, "1", None))
def test_count_is_exact_bounded_integer(value: object) -> None:
    with pytest.raises(ValueError, match="^NPC_ASSISTANCE_MEMORY_INPUT$"):
        AssistanceMemory(cast(int, value), ())


@pytest.mark.parametrize("value", (False, 0, -1, MAX_INT + 1, 1.0))
def test_tick_is_exact_positive_integer(value: object) -> None:
    with pytest.raises(ValueError, match="^NPC_ASSISTANCE_MEMORY_INPUT$"):
        AssistanceEntry(cast(int, value), LAYOUT.gate_id, "answered_call", "e1-" + "0" * 64)


@pytest.mark.parametrize(
    "count,entries",
    ((0, (entry(1),)), (1, ()), (5, tuple(entry(i) for i in range(1, 6))), (1, [entry(1)])),
)
def test_count_and_retention_shape(count: int, entries: object) -> None:
    with pytest.raises(ValueError, match="^NPC_ASSISTANCE_MEMORY_ENTRIES$"):
        AssistanceMemory(count, cast(tuple[AssistanceEntry, ...], entries))


@pytest.mark.parametrize(
    "entries",
    (
        (entry(2), entry(1)),
        (entry(2), entry(2)),
        (entry(1), replace(entry(2), cause_event_id=entry(1).cause_event_id)),
    ),
)
def test_order_and_cause_uniqueness(entries: tuple[AssistanceEntry, ...]) -> None:
    with pytest.raises(ValueError, match="^NPC_ASSISTANCE_MEMORY_ORDER$"):
        AssistanceMemory(2, entries)


def test_five_appends_trim_exact_oldest_and_compose_contiguously() -> None:
    states = tuple(history(i) for i in range(7))
    reducer = AssistanceReducer(approved_content())
    changes = tuple(AssistanceMemoryDelta(LAYOUT.npc_id, a, b) for a, b in zip(states, states[1:]))
    for before, after in zip(states, states[1:]):
        assert append_assistance(before, after.entries[-1]) == after
        validate_transition(before, after, single=True)
    net = reducer.compose(changes)
    assert net == AssistanceMemoryDelta(LAYOUT.npc_id, states[0], states[-1])
    assert reducer.compose((reducer.compose(changes[:3]), reducer.compose(changes[3:]))) == net
    assert not reducer.is_identity(net)
    assert tuple(e.tick for e in states[5].entries) == (2, 3, 4, 5)
    with pytest.raises(CandidateError, match="discontinuity"):
        reducer.compose((changes[0], changes[2]))
    with pytest.raises(CandidateError, match="empty"):
        reducer.compose(())


def test_transition_rejects_rewrite_tie_identity_and_skipped_stage() -> None:
    before = history(3)
    for after in (
        before,
        history(2),
        AssistanceMemory(
            4, (entry(1), entry(2), replace(entry(3), target_id=EntityId("object:other")), entry(4))
        ),
    ):
        with pytest.raises(ValueError, match="NPC_ASSISTANCE_MEMORY_ORDER"):
            validate_transition(before, after, single=True)
    with pytest.raises(ValueError, match="NPC_ASSISTANCE_MEMORY_ORDER"):
        validate_transition(before, history(5), single=True)
    with pytest.raises(ValueError, match="NPC_ASSISTANCE_MEMORY_ORDER"):
        validate_transition(
            AssistanceMemory(1, (entry(100),)),
            AssistanceMemory(10, tuple(entry(t) for t in (101, 102, 103, 104))),
        )


def test_component_and_payload_codecs_and_patch_owner() -> None:
    content = approved_content()
    before = AssistanceMemoryRecord(LAYOUT.npc_id, history(0))
    after = AssistanceMemoryRecord(LAYOUT.npc_id, history(1))
    codec = AssistanceCodec(content)
    assert codec.decode(before.entity_id, codec.encode(before)) == before
    for payload in (
        AssistanceMemoryDelta(LAYOUT.npc_id, before.state, after.state),
        AssistanceMemoryPatch(after.state),
    ):
        selected = AssistancePayloadCodec(payload.schema, content)
        assert selected.decode(selected.encode(payload)) == payload
    assert AssistancePatchRoute(content).apply(before, AssistanceMemoryPatch(after.state)) == after
    with pytest.raises(ValueError, match="NPC_ASSISTANCE_MEMORY_OWNER"):
        AssistanceAdapter(content).validate(replace(before, entity_id=LAYOUT.actor_id))
    with pytest.raises(ValueError):
        codec.decode(before.entity_id, {"memory": encode_state(before.state), "extra": 0})
    with pytest.raises(ValueError):
        decode_state({"total_assists": True, "entries": ()})
    with pytest.raises(ValueError):
        decode_state({"total_assists": 0, "entries": (), "extra": 0})


def test_checkpoint_requires_actual_world_and_acceptance_cause() -> None:
    # These synthetic IDs are structurally valid, but cannot prove a canonical cause.
    record = AssistanceMemoryRecord(LAYOUT.npc_id, history(1))
    for tick, accepted, reported in (
        (1, None, None),
        (0, 0, None),
        (1, 1, None),
        (1, 0, 0),
        (1, 0, None),
    ):
        with pytest.raises(ValueError, match="^NPC_ASSISTANCE_MEMORY_SOURCE$"):
            validate_checkpoint(record, "0" * 64, tick, accepted_at=accepted, reported_at=reported)
    validate_checkpoint(
        replace(record, state=history(0)), "0" * 64, 0, accepted_at=None, reported_at=None
    )
