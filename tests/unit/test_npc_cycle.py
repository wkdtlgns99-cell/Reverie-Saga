from dataclasses import replace
from typing import cast

import pytest

from app.headless import state_io
from app.npc_cycle import bootstrap_cycle, cycle_bundle
from app.npc_work import work_bundle
from app.watch import WatchBootstrapSpec
from contracts.errors import CandidateError, ExpiredReadView, ReadOnlyViolation
from contracts.messages import EventHeader, WorldEvent
from contracts.npc_cycle import CYCLE, CYCLE_FAMILY, CycleChanged, CycleCue, CycleDelta, CyclePatch
from contracts.read_views import AdapterBinding, ViewEpoch
from contracts.turn import EngineInvocation
from contracts.watch import NpcActed
from domain.npc_cycle import (
    CycleRecord,
    Supply,
    SupplyEvidence,
    advance,
    state_at,
    validate_checkpoint,
    wake_identity,
)
from domain.primitives import EntityId, EventId, Phase, Tick
from domain.state_types import StoredRoot
from engines.npc_cycle import NpcSupplyCycle
from orchestration.npc_cycle import (
    CycleAdapter,
    CycleCodec,
    CyclePatchRoute,
    CyclePayloadCodec,
    CycleReducer,
)
from orchestration.read_views import ObservedReadViewFactory
from orchestration.turn import EmptyDefinitions, NoDrawRng
from tests.unit.quest_fixtures import content

OWNER = EntityId("actor:harbor-watcher")
WORLD = "w1-" + "1" * 64


def record_at(tick: int) -> CycleRecord:
    record = CycleRecord(OWNER, Supply(0, 0, 0), ())
    for at in range(1, tick + 1):
        record = advance(record, at, wake_identity(WORLD, at))
    return record


@pytest.mark.parametrize(
    "tick,expected",
    (
        (0, (0, 0, 0)),
        (3, (0, 0, 0)),
        (4, (1, 1, 0)),
        (8, (2, 2, 0)),
        (10, (1, 2, 1)),
        (12, (2, 3, 1)),
        (16, (3, 4, 1)),
        (20, (3, 5, 2)),
        (24, (3, 5, 2)),
        (30, (2, 5, 3)),
        (31, (2, 5, 3)),
        (32, (3, 6, 3)),
        (40, (3, 7, 4)),
    ),
)
def test_independently_derived_vectors(tick: int, expected: tuple[int, int, int]) -> None:
    actual = record_at(tick)
    assert actual.state == Supply(*expected) == state_at(tick)
    validate_checkpoint(actual, WORLD, tick)


def test_long_horizon_bounded_memory_closed_form_and_tie_order() -> None:
    # An independent direct stock loop,not the checkpoint formula.
    stock = made = used = 0
    record = record_at(0)
    for tick in range(1, 2001):
        if tick % 10 == 0 and stock:
            stock -= 1
            used += 1
        if tick % 4 == 0 and stock < 3:
            stock += 1
            made += 1
        record = advance(record, tick, wake_identity(WORLD, tick))
        assert record.state == Supply(stock, made, used) == state_at(tick)
        assert len(record.entries) == min(4, made + used)
    validate_checkpoint(record, WORLD, 2000)
    assert [(e.tick, e.sequence, e.prepared) for e in record.entries] == [
        (1990, 0, False),
        (1992, 0, True),
        (2000, 0, False),
        (2000, 1, True),
    ]
    huge = state_at(2**63 - 1)
    assert huge.stock == 3 and huge.consumed == (2**63 - 1) // 10


@pytest.mark.parametrize("bad", (True, False, -1, 2**63, "1", 1.5, None))
def test_exact_integer_inputs(bad: object) -> None:
    with pytest.raises(ValueError):
        state_at(cast(int, bad))
    with pytest.raises(ValueError):
        Supply(0, cast(int, bad), 0)


def test_strict_codecs_patch_composition_and_checkpoint_memory_corruption() -> None:
    selected = content()
    before, first, last = record_at(0), record_at(4), record_at(20)
    codec = CycleCodec(selected)
    assert codec.decode(OWNER, codec.encode(last)) == last
    payloads = (
        CycleDelta(before, last),
        CyclePatch(last),
        CycleChanged(OWNER, last.entries[-1]),
        CycleCue(OWNER, last.entries[-1]),
    )
    for payload in payloads:
        route = CyclePayloadCodec(payload.schema, selected)
        data = route.encode(payload)
        assert route.decode(data) == payload
        with pytest.raises(ValueError):
            route.decode({**data, "extra": 0})
        for missing in data:
            with pytest.raises(ValueError):
                route.decode({k: v for k, v in data.items() if k != missing})
    with pytest.raises(ValueError, match="NPC_CYCLE_OWNER"):
        codec.decode(EntityId("actor:other"), codec.encode(last))
    reducer = CycleReducer(selected)
    ticks = (0, 4, 8, 10, 12, 16, 20)
    changes = tuple(CycleDelta(record_at(a), record_at(b)) for a, b in zip(ticks, ticks[1:]))
    assert reducer.compose(changes) == CycleDelta(before, last)
    for bad in (
        (),
        changes[::-1],
        (changes[0], changes[2]),
        (CycleDelta(before, last),),
        (CycleDelta(first, first),),
    ):
        with pytest.raises(CandidateError, match="INVALID_DELTA"):
            reducer.compose(bad)
    patch = CyclePatchRoute(selected)
    assert patch.apply(before, CyclePatch(first)) == first
    with pytest.raises(ValueError, match="NPC_CYCLE_TRANSITION"):
        patch.apply(before, CyclePatch(last))
    with pytest.raises(ValueError, match="NPC_CYCLE_MEMORY"):
        replace(last, entries=())
    altered = replace(
        last,
        entries=(replace(last.entries[0], source_event_id="e1-" + "f" * 64), *last.entries[1:]),
    )
    with pytest.raises(ValueError, match="NPC_CYCLE_CHECKPOINT"):
        validate_checkpoint(altered, WORLD, 20)
    initial = bootstrap_cycle(WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32), selected)
    core = initial.snapshot()
    bad_core = replace(
        core, components=tuple(r for r in core.components if r.schema != CYCLE.schema)
    )
    with pytest.raises(ValueError, match="NPC_CYCLE_CHECKPOINT"):
        cycle_bundle(selected).checkpoint_policy.validate(bad_core, initial.protocol())
    assert state_io((cycle_bundle(selected),)).pins != state_io((work_bundle(selected),)).pins


def test_observed_read_immutable_expired_and_engine_source_guards() -> None:
    factory = ObservedReadViewFactory(StoredRoot((record_at(8),), 0))
    AdapterBinding(CycleAdapter(content())).install(factory)
    epoch = ViewEpoch(Tick(10), Phase.POST_TICK, 0, "quest.cycle", 0)
    read = factory.open(epoch)
    view = read.component(CYCLE, OWNER)
    assert view.state == Supply(2, 2, 0)
    with pytest.raises(ReadOnlyViolation):
        view.entries = ()  # type: ignore[misc]
    payload = NpcActed(OWNER, 4, 5)
    header = EventHeader(
        EventId(wake_identity(WORLD, 10)),
        payload.schema,
        "watch.npc",
        Tick(10),
        Phase.PRE_TICK,
        0,
        0,
        0,
        (),
        (),
    )
    event = WorldEvent(header, Tick(10), payload)
    invocation = EngineInvocation(
        None, Tick(10), Phase.POST_TICK, 0, read, EmptyDefinitions(), NoDrawRng(), (event,)
    )
    engine = NpcSupplyCycle(content())
    result = engine.evaluate(invocation)
    assert isinstance(result.deltas[0], CycleDelta)
    assert result.deltas[0].after.state == Supply(1, 2, 1)
    for bad in (
        replace(invocation, wave=1),
        replace(invocation, incoming=()),
        replace(invocation, incoming=(event, event)),
        replace(invocation, logical_tick=Tick(8)),
        replace(
            invocation,
            incoming=(replace(event, header=replace(header, producer_id="quest.rules")),),
        ),
        replace(invocation, incoming=(replace(event, payload=NpcActed(OWNER, True, 5)),)),
    ):
        with pytest.raises(CandidateError, match="INVALID_FACT"):
            engine.evaluate(bad)
    observations = factory.close(epoch)
    assert observations and all(o.target.family == CYCLE_FAMILY for o in observations)
    with pytest.raises(ExpiredReadView):
        _ = view.state


@pytest.mark.parametrize("source", ("", "e1-x", "e1-" + "F" * 64))
def test_invalid_causal_anchor(source: str) -> None:
    with pytest.raises(ValueError, match="NPC_CYCLE_SOURCE"):
        SupplyEvidence(4, 0, source, Supply(0, 0, 0), Supply(1, 1, 0))
