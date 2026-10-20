from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from typing import cast

import pytest

from app.headless import state_io
from app.npc_memory import memory_bundle
from app.npc_work import bootstrap_work, work_bundle
from app.watch import WatchBootstrapSpec
from contracts.errors import BootstrapError, CandidateError, ExpiredReadView, ReadOnlyViolation
from contracts.npc_work import (
    PROVISIONS,
    STOCK_FAMILY,
    ProvisionPrepared,
    ProvisionsCue,
    ProvisionsDelta,
    ProvisionsPatch,
)
from contracts.read_views import AdapterBinding, ViewEpoch
from contracts.messages import WorldEvent
from contracts.turn import EngineInvocation, GameCommand
from contracts.watch import NpcActed, WaitCommand
from domain.npc_work import ProvisionsRecord, stock_at
from domain.primitives import CommandId, EntityId, Phase, Tick, WorldRevision
from domain.state_types import StoredRoot
from orchestration.npc_work import (
    ProvisionsAdapter,
    ProvisionsCheckpointPolicy,
    ProvisionsCodec,
    ProvisionsPatchRoute,
    ProvisionsPayloadCodec,
    ProvisionsReducer,
)
from orchestration.read_views import ObservedReadViewFactory
from engines.npc_work import NpcProvisioner
from orchestration.turn import EmptyDefinitions, NoDrawRng
from tests.unit.quest_fixtures import content

OWNER = EntityId("actor:harbor-watcher")


@pytest.mark.parametrize("bad", (True, False, -1, 4, 2**63, "1", 1.5, None))
def test_stock_exact_type_and_bounds(bad: object) -> None:
    with pytest.raises(ValueError, match="NPC_WORK_STOCK"):
        ProvisionsRecord(OWNER, cast(int, bad))


@pytest.mark.parametrize(
    "tick,expected", ((0, 0), (3, 0), (4, 1), (7, 1), (8, 2), (11, 2), (12, 3), (99, 3))
)
def test_independent_time_boundaries(tick: int, expected: int) -> None:
    assert stock_at(tick) == expected


def test_codec_routes_and_composition_reject_invalid_changes() -> None:
    selected = content()
    record = ProvisionsRecord(OWNER, 2)
    codec = ProvisionsCodec(selected)
    assert codec.decode(OWNER, codec.encode(record)) == record
    with pytest.raises(FrozenInstanceError):
        record.stock = 3  # type: ignore[misc]
    samples = (
        ProvisionsDelta(OWNER, 0, 3),
        ProvisionsPatch(2),
        ProvisionPrepared(OWNER, 1, 2),
        ProvisionsCue(OWNER, 2, 8),
    )
    for payload in samples:
        route = ProvisionsPayloadCodec(payload.schema, selected)
        document = route.encode(payload)
        assert route.decode(document) == payload
        with pytest.raises(ValueError):
            route.decode({**document, "extra": 0})
        for missing in document:
            with pytest.raises(ValueError):
                route.decode({key: value for key, value in document.items() if key != missing})
    reducer = ProvisionsReducer(selected)
    changes = tuple(ProvisionsDelta(OWNER, before, before + 1) for before in range(3))
    assert reducer.compose(changes) == ProvisionsDelta(OWNER, 0, 3)
    for bad in (
        (),
        changes[::-1],
        (changes[0], changes[2]),
        (ProvisionsDelta(OWNER, 0, 2),),
        (ProvisionsDelta(OWNER, 1, 1),),
        (ProvisionsDelta(OWNER, 3, 4),),
        (ProvisionsDelta(EntityId("actor:other"), 0, 1),),
    ):
        with pytest.raises(CandidateError, match="INVALID_DELTA"):
            reducer.compose(bad)
    patch = ProvisionsPatchRoute(selected)
    assert patch.apply(record, ProvisionsPatch(3)) == ProvisionsRecord(OWNER, 3)
    for bad_stock in (0, 1, 2, 4, True):
        with pytest.raises(ValueError):
            patch.apply(record, ProvisionsPatch(bad_stock))
    with pytest.raises(ValueError, match="NPC_WORK_OWNER"):
        codec.decode(EntityId("actor:other"), {"stock": 1})
    with pytest.raises(ValueError, match="NPC_WORK_TRANSITION"):
        ProvisionsPayloadCodec(ProvisionPrepared.SCHEMA, selected).encode(
            ProvisionPrepared(OWNER, 0, 2)
        )


def test_observed_read_is_immutable_and_expires() -> None:
    factory = ObservedReadViewFactory(StoredRoot((ProvisionsRecord(OWNER, 1),), 0))
    AdapterBinding(ProvisionsAdapter(content())).install(factory)
    epoch = ViewEpoch(Tick(4), Phase.POST_TICK, 0, "quest.provisioner", 0)
    view = factory.open(epoch).component(PROVISIONS, OWNER)
    assert view.stock == 1
    with pytest.raises(ReadOnlyViolation):
        view.stock = 2  # type: ignore[misc]
    observations = factory.close(epoch)
    assert observations and all(o.target.family == STOCK_FAMILY for o in observations)
    with pytest.raises(ExpiredReadView):
        _ = view.stock


@pytest.mark.parametrize("value,tick", ((0, 4), (1, 0), (1, 5), (3, 16)))
def test_presentation_cannot_claim_unscheduled_production(value: int, tick: int) -> None:
    with pytest.raises(ValueError):
        ProvisionsPayloadCodec(ProvisionsCue.SCHEMA, content()).encode(
            ProvisionsCue(OWNER, value, tick)
        )


@pytest.mark.parametrize("damage", ("engine", "adapter", "codec", "roles"))
def test_work_registration_cannot_omit_required_roles(damage: str) -> None:
    bundle = work_bundle(content())
    if damage == "engine":
        bundle = replace(bundle, bindings=bundle.bindings[:-1])
    elif damage == "adapter":
        bundle = replace(bundle, read_adapters=bundle.read_adapters[:-1])
    elif damage == "codec":
        bundle = replace(bundle, codecs=bundle.codecs[:-1])
    else:
        rules = dict(bundle.rules_document)
        rules["quest"] = memory_bundle(content()).rules_document["quest"]
        bundle = replace(bundle, rules_document=rules)
    with pytest.raises(BootstrapError):
        state_io((bundle,))


def test_checkpoint_rejects_missing_wrong_owner_and_wrong_clock() -> None:
    selected = content()
    session = bootstrap_work(WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32), selected)
    core, protocol = session.snapshot(), session.protocol()
    policy = ProvisionsCheckpointPolicy(selected)
    policy.validate(core, protocol)
    others = tuple(r for r in core.components if r.schema != PROVISIONS.schema)
    for stock in (1, 2, 3):
        bad = replace(
            core,
            components=tuple(
                sorted(
                    (*others, ProvisionsRecord(OWNER, stock)),
                    key=lambda r: (r.schema.kind, r.schema.version, r.entity_id),
                )
            ),
        )
        with pytest.raises(ValueError, match="NPC_WORK_CHECKPOINT"):
            policy.validate(bad, protocol)
    with pytest.raises(ValueError, match="NPC_WORK_CHECKPOINT"):
        policy.validate(replace(core, components=others), protocol)


def source_event() -> WorldEvent:
    selected = content()
    session = bootstrap_work(WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32), selected)
    command = GameCommand(
        CommandId("c1:" + "0" * 32 + ":" + "1" * 32 + ":1"),
        selected.definition.layout.actor_id,
        WorldRevision(0),
        WaitCommand(4),
    )
    session.driver.submit(command)
    return next(
        event
        for event in session.last_publication().facts
        if type(event.payload) is NpcActed and event.due_tick == 4
    )


@pytest.mark.parametrize(
    "damage",
    (
        "none",
        "owner",
        "producer",
        "phase",
        "wave",
        "sequence",
        "time",
        "schema",
        "count",
        "duplicate",
        "empty",
        "stock",
    ),
)
def test_engine_source_validation_and_precommit_preservation(damage: str) -> None:
    event = source_event()
    if damage in ("producer", "phase", "wave", "sequence", "time", "schema"):
        header = event.header
        if damage == "producer":
            header = replace(header, producer_id="quest.rules")
        elif damage == "phase":
            header = replace(header, phase=Phase.RESOLVE)
        elif damage == "wave":
            header = replace(header, wave=1)
        elif damage == "sequence":
            header = replace(header, sequence=1)
        elif damage == "time":
            header = replace(header, occurred_at=Tick(3))
        else:
            header = replace(header, type_key=WaitCommand(1).schema)
        event = replace(event, header=header)
    if damage == "owner":
        event = replace(event, payload=NpcActed(EntityId("actor:other"), 1, 2))
    if damage == "count":
        event = replace(event, payload=NpcActed(OWNER, 0, 2))
    incoming = (event, event) if damage == "duplicate" else () if damage == "empty" else (event,)
    record = ProvisionsRecord(OWNER, 1 if damage == "stock" else 0)
    root = StoredRoot((record,), 0)
    factory = ObservedReadViewFactory(root)
    AdapterBinding(ProvisionsAdapter(content())).install(factory)
    epoch = ViewEpoch(Tick(4), Phase.POST_TICK, 0, "quest.provisioner", 0)
    invocation = EngineInvocation(
        None,
        Tick(4),
        Phase.POST_TICK,
        0,
        factory.open(epoch),
        EmptyDefinitions(),
        NoDrawRng(),
        incoming,
    )
    try:
        if damage == "none":
            result = NpcProvisioner(content()).evaluate(invocation)
            assert result.deltas == (ProvisionsDelta(OWNER, 0, 1),)
            assert len(result.facts) == 1
            assert result.facts[0].caused_by == (event.header.event_id,)
            assert result.facts[0].due_tick == 4
        else:
            with pytest.raises(CandidateError, match="^INVALID_FACT"):
                NpcProvisioner(content()).evaluate(invocation)
        assert root.components == (record,)
    finally:
        factory.close(epoch)
