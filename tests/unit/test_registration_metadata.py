"""Registration preserves real validation,exact keys and invocation-local lifetimes."""

from dataclasses import replace

import pytest

from contracts.errors import ExpiredReadView, UnknownComponent, UnknownEntity
from contracts.read_views import ComponentKey, ViewEpoch
from domain.primitives import EntityId, Phase, Tick
from domain.state_types import ComponentRecord, StoredRoot
from orchestration.read_views import ObservedReadViewFactory
from tests.unit.view_fixtures import (
    ACTOR,
    PHYSIOLOGY,
    PROFILE,
    PhysiologyAdapter,
    PhysiologyRead,
    PhysiologyRecord,
    ProfileAdapter,
    ProfileRecord,
)


class Probe(PhysiologyAdapter):
    def __init__(self, key: ComponentKey[PhysiologyRead] = PHYSIOLOGY) -> None:
        self.selected_key = key
        self.forbid_key = False
        self.validated: list[ComponentRecord] = []

    @property
    def key(self) -> ComponentKey[PhysiologyRead]:
        if self.forbid_key:
            raise RuntimeError("late metadata must not be consulted")
        return self.selected_key

    def validate(self, record: ComponentRecord) -> None:
        self.validated.append(record)
        super().validate(record)


def epoch(token: int = 1) -> ViewEpoch:
    return ViewEpoch(Tick(0), Phase.RESOLVE, 0, "fixture.engine", token)


def root(*records: ComponentRecord) -> StoredRoot:
    return StoredRoot(
        tuple(
            sorted(
                records,
                key=lambda record: (record.schema.kind, record.schema.version, record.entity_id),
            )
        ),
        1,
    )


def test_all_matching_records_are_validated_in_root_order_and_again_on_read() -> None:
    first = PhysiologyRecord(EntityId("actor:a"), 3, ())
    last = PhysiologyRecord(EntityId("actor:z"), 9, ())
    unrelated = ProfileRecord(ACTOR, ("quiet",))
    stored = root(last, unrelated, first)
    adapter = Probe()
    factory = ObservedReadViewFactory(stored)
    factory.register(adapter)
    assert adapter.validated == [first, last]
    factory.register(ProfileAdapter())
    port = factory.open(epoch())
    assert port.component(PHYSIOLOGY, last.entity_id).hp == 9
    assert port.component(PROFILE, ACTOR).traits[0] == "quiet"
    assert adapter.validated[-2:] == [last, last]
    observations = factory.close(epoch())
    assert [(row.target.family.field, row.operation) for row in observations] == [
        ("hp", "read"),
        ("traits", "read"),
        ("traits", "read"),
    ]
    assert stored.components == root(first, last, unrelated).components


def test_duplicate_schema_does_not_validate_or_replace_original_key_adapter() -> None:
    record = PhysiologyRecord(ACTOR, 10, ())
    first = Probe()
    alias = ComponentKey[PhysiologyRead](PHYSIOLOGY.schema)
    duplicate = Probe(alias)
    factory = ObservedReadViewFactory(root(record))
    factory.register(first)
    with pytest.raises(ValueError, match="^registry frozen or duplicate schema$"):
        factory.register(duplicate)
    assert duplicate.validated == [] and first.validated == [record]
    port = factory.open(epoch())
    assert port.component(PHYSIOLOGY, ACTOR).hp == 10
    with pytest.raises(UnknownComponent, match="fixture.physiology"):
        port.component(alias, ACTOR)
    factory.close(epoch())


@pytest.mark.parametrize("closed", (False, True))
def test_frozen_registration_rejects_before_late_metadata_or_validation(closed: bool) -> None:
    factory = ObservedReadViewFactory(root(PhysiologyRecord(ACTOR, 10, ())))
    factory.register(PhysiologyAdapter())
    factory.open(epoch())
    if closed:
        factory.close(epoch())
    late = Probe()
    late.forbid_key = True
    with pytest.raises(ValueError, match="^registry frozen or duplicate schema$"):
        factory.register(late)
    assert late.validated == []
    if not closed:
        factory.close(epoch())


def test_empty_root_registration_retains_key_but_does_not_create_an_entity() -> None:
    adapter = Probe()
    factory = ObservedReadViewFactory(root())
    factory.register(adapter)
    assert adapter.validated == []
    port = factory.open(epoch())
    with pytest.raises(UnknownEntity, match="actor:toy"):
        port.component(PHYSIOLOGY, ACTOR)
    factory.close(epoch())


def test_unregistered_backing_remains_an_open_error() -> None:
    stored = root(ProfileRecord(ACTOR, ()))
    adapter = Probe()
    factory = ObservedReadViewFactory(stored)
    factory.register(adapter)
    assert adapter.validated == []
    with pytest.raises(UnknownComponent, match="unregistered backing"):
        factory.open(epoch())
    factory.register(ProfileAdapter())
    assert tuple(factory.open(epoch()).component(PROFILE, ACTOR).traits) == ()
    factory.close(epoch())


def test_invalid_matching_record_preserves_validator_error_and_stops_in_order() -> None:
    first = PhysiologyRecord(EntityId("actor:a"), 3, ())
    invalid = PhysiologyRecord(EntityId("actor:b"), 3, (("food", 1), ("food", 2)))
    later = PhysiologyRecord(EntityId("actor:c"), 3, ())
    stored = root(first, invalid, later)
    adapter = Probe()
    factory = ObservedReadViewFactory(stored)
    with pytest.raises(ValueError, match="^duplicate keys$"):
        factory.register(adapter)
    assert adapter.validated == [first, invalid]
    assert stored.components == root(first, invalid, later).components


def test_adapter_metadata_is_captured_per_factory_without_sharing_ports_or_validation() -> None:
    first_record = PhysiologyRecord(ACTOR, 3, ())
    second_record = replace(first_record, hp=9)
    adapter = Probe()
    first = ObservedReadViewFactory(root(first_record))
    first.register(adapter)
    alias = ComponentKey[PhysiologyRead](PHYSIOLOGY.schema)
    adapter.selected_key = alias
    second = ObservedReadViewFactory(root(second_record))
    second.register(adapter)
    assert adapter.validated == [first_record, second_record]
    before, after = first.open(epoch()), second.open(epoch())
    old = before.component(PHYSIOLOGY, ACTOR)
    current = after.component(alias, ACTOR)
    assert old.hp == 3 and current.hp == 9 and old is not current
    with pytest.raises(UnknownComponent, match="fixture.physiology"):
        before.component(alias, ACTOR)
    with pytest.raises(UnknownComponent, match="fixture.physiology"):
        after.component(PHYSIOLOGY, ACTOR)
    first.close(epoch())
    with pytest.raises(ExpiredReadView, match="closed"):
        _ = old.hp
    assert current.hp == 9
    second.close(epoch())
