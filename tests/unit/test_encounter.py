from __future__ import annotations

from dataclasses import replace
from typing import cast

import pytest

from app.encounter_registry import encounter_bundle
from app.headless import state_io
from contracts.encounter import (
    GATE, HIT_POINTS, STAMINA, AttackCommand, AttackResolved, Defeated,
    EncounterMoved, GateDelta, GatePatch, HitPointsDelta, HitPointsPatch,
    InteractCommand, RestCommand, StaminaDelta, StaminaPatch,
)
from contracts.errors import BootstrapError, CandidateError, ExpiredReadView, ReadOnlyViolation, SchemaError
from contracts.messages import StateDelta
from contracts.read_views import ComponentPatch
from contracts.skeleton import DeltaRoute, PayloadCodec
from contracts.turn import NodeActivation, NodeKey
from domain.canonical import JsonObject, array_value, canonical_json, hash_document, int_value, object_value, text_value
from domain.encounter import (
    ATTACK_PROFILE_ID, ENEMY_ID, GATE_ID, GateRecord, HitPointsRecord, StaminaRecord,
    adjacent_cells, life_status, resolve_basic_attack, stamina_status,
)
from domain.primitives import ComponentAddress, EntityId, FieldAddress, FieldFamily, FrozenPayload, Phase, TypeKey
from domain.trial import ACTOR_ID, SPACE_ID
from contracts.trial import CellDelta
from engines.encounter import EncounterActions
from orchestration.encounter import (
    EncounterCellReducer, EncounterPayloadCodec, GateCodec, GateReducer,
    HitPointsCodec, HitPointsReducer, StaminaCodec, StaminaReducer,
)
from orchestration.scheduler import compile_schedule
from tests.unit.encounter_fixtures import reference, session, views


def test_literal_pins_and_records() -> None:
    io = state_io((encounter_bundle(),))
    assert (io.pins.schema_fingerprint, io.pins.rules_fingerprint, io.pins.schedule_fingerprint) == (
        "a102520b5798c2410080d117cfc2ea41a608486673eac54fdbc567a47e9a7d0f",
        "740189264a80c68b4641c1669184c0519340f8bbba657e7d483feab3bc99f77f",
        "706faf28c9673d473b3c771d324a932ac3fd7540c2a22974e62d25e837d7bac1",
    )
    core = session().snapshot()
    assert io.hash_core(core) == "cad5f4174c24380d62ce1ecc029b1dd34e409e5a5192c6d8a01f52eede4df5aa"
    assert canonical_json(io.encode_core(core)) == canonical_json(object_value(reference("expected_fixture"))["initial_core"])
    for raw in array_value(reference("literal_documents")):
        vector = object_value(raw)
        assert canonical_json(vector["document"]).decode() == vector["utf8"]
        assert canonical_json(vector["document"]).hex() == vector["utf8_hex"]
        assert hash_document(text_value(vector["tag"]), vector["document"]) == vector["sha256"]
    for codec in encounter_bundle().component_codecs:
        for record in core.components:
            if record.schema == codec.schema:
                fields = codec.encode(record)
                assert codec.decode(record.entity_id, fields) == record
                with pytest.raises(ValueError):
                    codec.decode(record.entity_id, {**fields, "extra": 0})
                for name in fields:
                    with pytest.raises(ValueError):
                        codec.decode(record.entity_id, {k: v for k, v in fields.items() if k != name})
    for codec, record in ((GateCodec(), GateRecord(GATE_ID, SPACE_ID, 4, True)),
                          (GateCodec(), GateRecord(GATE_ID, SPACE_ID, 3, 0)),
                          (GateCodec(), GateRecord(GATE_ID, EntityId("bad space"), 4, 0)),
                          (HitPointsCodec(), HitPointsRecord(ACTOR_ID, -1)),
                          (HitPointsCodec(), HitPointsRecord(ENEMY_ID, 6)),
                          (StaminaCodec(), StaminaRecord(ACTOR_ID, 3))):
        with pytest.raises(ValueError):
            codec.encode(record)


def test_payload_closed_fields_and_classes() -> None:
    selected = encounter_bundle()
    io = state_io((selected,))
    codec: PayloadCodec
    covered: set[TypeKey] = set()
    for name in ("expected_publications", "death_publications"):
        for raw in array_value(reference(name)):
            pub = object_value(raw)
            for family in ("facts", "cues"):
                for item in array_value(pub[family]):
                    event = object_value(item)
                    key = object_value(object_value(event["header"])["type_key"])
                    codec = EncounterPayloadCodec(TypeKey(text_value(key["kind"]), int_value(key["version"])))
                    body = object_value(event["payload"])
                    assert canonical_json(codec.encode(codec.decode(body))) == canonical_json(body)
                    covered.add(codec.schema)
                    with pytest.raises(ValueError):
                        codec.decode({**body, "extra": 0})
                    for field in body:
                        with pytest.raises(ValueError):
                            codec.decode({k: v for k, v in body.items() if k != field})
                        if type(body[field]) is int:
                            with pytest.raises(ValueError):
                                codec.decode({**body, field: True})
    samples: tuple[FrozenPayload, ...] = (
        InteractCommand(GATE_ID, "open"), AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID), RestCommand(),
        GateDelta(GATE_ID, 0, 1), HitPointsDelta(ENEMY_ID, 5, 3), StaminaDelta(ACTOR_ID, 2, 1),
        GatePatch(1), HitPointsPatch(3), StaminaPatch(1), CellDelta(ACTOR_ID, 0, 3),
    )
    for payload in samples:
        codec = next(c for c in selected.codecs if c.schema == payload.schema)
        body = codec.encode(payload)
        assert codec.decode(body) == payload
        covered.add(codec.schema)
        with pytest.raises(ValueError):
            codec.decode({**body, "extra": 0})
    from contracts.trial import CellPatch, MoveCommand
    for payload in (CellPatch(3), MoveCommand(0, 1)):
        assert io.encode_payload(payload)
        covered.add(payload.schema)
    assert covered == {c.schema for c in selected.codecs} and len(covered) == 23
    for schema in (TypeKey("encounter.attack", 2), TypeKey("encounter.missing", 1)):
        with pytest.raises(SchemaError):
            EncounterPayloadCodec(schema)
    with pytest.raises(SchemaError):
        EncounterPayloadCodec(TypeKey("encounter.attack", 1)).encode(RestCommand())
    with pytest.raises(SchemaError):
        EncounterPayloadCodec(TypeKey("encounter.attack", 1)).encode(_DerivedAttack(ENEMY_ID, ATTACK_PROFILE_ID))


class _DerivedAttack(AttackCommand):
    pass


@pytest.mark.parametrize("kind,body", (
    ("interact", {"target_id": GATE_ID, "option": "toggle"}),
    ("interact", {"target_id": "object:e\u0301", "option": "open"}),
    ("attack", {"target_id": ENEMY_ID, "profile_id": "bad profile"}),
    ("hp-delta", {"entity_id": ACTOR_ID, "before_hp": 4, "after_hp": 2}),
    ("hp-delta", {"entity_id": GATE_ID, "before_hp": 5, "after_hp": 3}),
    ("stamina-delta", {"entity_id": ENEMY_ID, "before_stamina": 2, "after_stamina": 1}),
    ("gate-delta", {"entity_id": ENEMY_ID, "before_open": 0, "after_open": 1}),
    ("gate-patch", {"is_open": 2}),
    ("hp-patch", {"hp": cast(int, 1.0)}),
    ("stamina-patch", {"value": False}),
    ("defeated", {"entity_id": ENEMY_ID, "killer_id": ENEMY_ID}),
    ("rested", {"actor_id": ACTOR_ID, "before_stamina": 0, "after_stamina": 2}),
    ("moved", {"actor_id": ACTOR_ID, "space_id": SPACE_ID, "from_cell": 2, "to_cell": 3}),
    ("move-blocked", {"actor_id": ACTOR_ID, "space_id": SPACE_ID, "from_cell": 0, "dx": 1, "dz": 0, "reason": "door"}),
    ("move-blocked", {"actor_id": ACTOR_ID, "space_id": SPACE_ID, "from_cell": 0, "dx": 0, "dz": 1, "reason": "boundary"}),
))
def test_scalar_and_payload_validation(kind: str, body: JsonObject) -> None:
    with pytest.raises(ValueError):
        EncounterPayloadCodec(TypeKey("encounter." + kind, 1)).decode(body)


def test_fact_arithmetic_and_cue_semantics() -> None:
    attack = AttackResolved(ACTOR_ID, ENEMY_ID, ATTACK_PROFILE_ID, 3, 2, 5, 3, 2, 1)
    for bad in (replace(attack, actor_hp_after=3), replace(attack, target_hp_after=4),
                replace(attack, stamina_after=2), replace(attack, profile_id="attack:other"),
                replace(attack, actor_id=ENEMY_ID), replace(attack, actor_hp_before=0)):
        with pytest.raises(ValueError):
            EncounterPayloadCodec(attack.schema).encode(bad)
    for name in ("expected_publications", "death_publications"):
        for raw in array_value(reference(name)):
            for cue in array_value(object_value(raw)["cues"]):
                event = object_value(cue)
                key = object_value(object_value(event["header"])["type_key"])
                codec = EncounterPayloadCodec(TypeKey(text_value(key["kind"]), 1))
                body = object_value(event["payload"])
                for field in ("x_mm", "z_mm", "to_x_mm", "from_z_mm", "actor_hp_after", "after_stamina"):
                    if field in body:
                        with pytest.raises(ValueError):
                            codec.decode({**body, field: int_value(body[field]) + 1})
                if "result" in body:
                    with pytest.raises(ValueError):
                        codec.decode({**body, "result": "unknown"})


@pytest.mark.parametrize("vector", tuple(object_value(v) for v in array_value(reference("attack_vectors"))))
def test_attack_vectors(vector: JsonObject) -> None:
    assert resolve_basic_attack(int_value(vector["actor_hp_before"]), int_value(vector["target_hp_before"]), int_value(vector["stamina_before"])) == (
        vector["actor_hp_after"], vector["target_hp_after"], vector["stamina_after"])


def test_status_and_geometry() -> None:
    assert [life_status(hp) for hp in range(6)] == ["defeated"] + ["alive"] * 5
    assert [stamina_status(s) for s in range(3)] == ["exhausted", "ready", "ready"]
    for first in range(9):
        for second in range(9):
            expected = (first, second) in {
                (a, b) for a, b in ((0, 1), (0, 3), (1, 2), (1, 4), (2, 5),
                                   (3, 4), (3, 6), (4, 5), (4, 7), (5, 8), (6, 7), (7, 8))
            } or (second, first) in {
                (0, 1), (0, 3), (1, 2), (1, 4), (2, 5), (3, 4),
                (3, 6), (4, 5), (4, 7), (5, 8), (6, 7), (7, 8),
            }
            assert adjacent_cells(first, second) is expected
    for invalid in (-1, 9, True, cast(int, 1.0)):
        with pytest.raises(ValueError):
            adjacent_cells(invalid, 0)
        with pytest.raises(ValueError):
            life_status(invalid)
        with pytest.raises(ValueError):
            stamina_status(invalid)
    for args in ((0, 5, 2), (4, 5, 2), (3, 0, 2), (3, 6, 2), (3, 5, 0), (3, 5, 3), (True, 5, 2), (3, 5, cast(int, 1.0))):
        with pytest.raises(ValueError):
            resolve_basic_attack(*args)


def test_guarded_reads() -> None:
    factory, epoch = views()
    port = factory.open(epoch)
    gate, hp, stamina = port.component(GATE, GATE_ID), port.component(HIT_POINTS, ACTOR_ID), port.component(STAMINA, ACTOR_ID)
    assert (gate.space_id, gate.cell, gate.is_open, hp.hp, stamina.value) == (SPACE_ID, 4, 0, 3, 2)
    aliases = ((gate, "space_id"), (gate, "cell"), (gate, "is_open"), (hp, "hp"), (stamina, "value"))
    for alias, name in aliases:
        with pytest.raises(ReadOnlyViolation):
            setattr(alias, name, 99)
        with pytest.raises(ReadOnlyViolation):
            delattr(alias, name)
    observed = factory.close(epoch)
    assert [(o.target.family.field, o.path, o.operation) for o in observed[:5]] == [
        ("space_id", (), "read"), ("cell", (), "read"), ("is_open", (), "read"), ("hp", (), "read"), ("value", (), "read")]
    assert all(o.operation == "write" and o.path == () for o in observed[5:])
    for alias, name in aliases:
        for operation in (lambda: getattr(alias, name), lambda: setattr(alias, name, 99), lambda: delattr(alias, name)):
            with pytest.raises(ExpiredReadView):
                operation()


class _Editor:
    def __init__(self) -> None:
        self.applied: list[tuple[ComponentAddress, ComponentPatch]] = []

    def apply_patch(self, address: ComponentAddress, patch: ComponentPatch) -> None:
        self.applied.append((address, patch))


_REDUCER_CASES: tuple[tuple[DeltaRoute, StateDelta, ComponentPatch, tuple[StateDelta, ...], StateDelta], ...] = (
    (GateReducer(), GateDelta(GATE_ID, 0, 1), GatePatch(1), (GateDelta(GATE_ID, 0, 1), GateDelta(GATE_ID, 1, 0)), GateDelta(GATE_ID, 0, 0)),
    (HitPointsReducer(), HitPointsDelta(ACTOR_ID, 3, 2), HitPointsPatch(2), (HitPointsDelta(ACTOR_ID, 3, 2), HitPointsDelta(ACTOR_ID, 2, 1)), HitPointsDelta(ACTOR_ID, 3, 1)),
    (StaminaReducer(), StaminaDelta(ACTOR_ID, 2, 1), StaminaPatch(1), (StaminaDelta(ACTOR_ID, 2, 1), StaminaDelta(ACTOR_ID, 1, 0)), StaminaDelta(ACTOR_ID, 2, 0)),
)


@pytest.mark.parametrize("reducer,delta,patch,chain,net", _REDUCER_CASES)
def test_scalar_reducers(reducer: DeltaRoute, delta: StateDelta, patch: ComponentPatch,
                         chain: tuple[StateDelta, ...], net: StateDelta) -> None:
    factory, epoch = views()
    port, editor = factory.open(epoch), _Editor()
    reducer.stage(delta, port, editor)
    assert editor.applied == [(ComponentAddress(TypeKey(delta.target.family.component, 1), delta.target.entity_id), patch)]
    observed = factory.close(epoch)
    assert [o.target for o in observed] == [delta.target]
    assert reducer.compose(chain) == net
    assert reducer.is_identity(net) is (reducer.schema.kind == "encounter.gate-delta")
    for changes in ((), (delta, delta), (delta, CellDelta(ACTOR_ID, 0, 3))):
        with pytest.raises(CandidateError):
            reducer.compose(changes)
    after_factory, after_epoch = views(gate=1, actor_hp=2, stamina=1)
    after = after_factory.open(after_epoch)
    reducer.validate_net(delta, after)
    with pytest.raises(CandidateError):
        reducer.validate_net(net, after)
    assert all(o.target == delta.target for o in after_factory.close(after_epoch))


def test_invalid_stages_and_foreign_subjects() -> None:
    factory, epoch = views()
    port, editor = factory.open(epoch), _Editor()
    cases: tuple[tuple[DeltaRoute, StateDelta], ...] = (
        (GateReducer(), GateDelta(GATE_ID, 1, 0)), (GateReducer(), GateDelta(GATE_ID, 0, 0)),
        (HitPointsReducer(), HitPointsDelta(ACTOR_ID, 3, 1)),
        (HitPointsReducer(), HitPointsDelta(ENEMY_ID, 5, 2)),
        (HitPointsReducer(), HitPointsDelta(ENEMY_ID, 4, 3)),
        (HitPointsReducer(), HitPointsDelta(ACTOR_ID, 2, 3)),
        (StaminaReducer(), StaminaDelta(ACTOR_ID, 2, 0)),
        (StaminaReducer(), StaminaDelta(ACTOR_ID, 1, 0)),
        (EncounterCellReducer(), CellDelta(ENEMY_ID, 8, 7)),
    )
    for reducer, delta in cases:
        with pytest.raises(CandidateError, match="INVALID_DELTA"):
            reducer.stage(delta, port, editor)
    assert not editor.applied
    factory.close(epoch)
    foreign = CellDelta(ENEMY_ID, 8, 7)
    reducer = EncounterCellReducer()
    for operation in (lambda: reducer.compose((foreign,)), lambda: reducer.is_identity(foreign),
                      lambda: reducer.validate_net(foreign, port)):
        with pytest.raises(CandidateError, match="INVALID_DELTA"):
            operation()
    for reducer, delta in ((HitPointsReducer(), HitPointsDelta(ACTOR_ID, 0, 0)),
                            (StaminaReducer(), StaminaDelta(ACTOR_ID, 0, 0))):
        assert reducer.is_identity(delta) is True
    with pytest.raises(ValueError):
        EncounterPayloadCodec(TypeKey("encounter.defeated", 1)).encode(Defeated(GATE_ID, ACTOR_ID))
    with pytest.raises(ValueError):
        EncounterPayloadCodec(TypeKey("encounter.moved", 1)).encode(EncounterMoved(ACTOR_ID, SPACE_ID, 0, 1))


def test_registry_ownership() -> None:
    selected, io = encounter_bundle(), state_io((encounter_bundle(),))
    assert (len(selected.field_specs), len(selected.codecs), len(selected.component_codecs), len(selected.delta_routes)) == (11, 23, 5, 4)
    assert {f.family: f.owner_id for f in selected.field_specs if f.owner_id != "system.bootstrap"} == {
        FieldFamily("trial.position", "cell"): "trial.movement",
        FieldFamily("encounter.gate", "is_open"): "encounter.actions",
        FieldFamily("encounter.hp", "hp"): "encounter.actions",
        FieldFamily("encounter.stamina", "value"): "encounter.actions",
    }
    for bad in (replace(selected, field_specs=selected.field_specs[:-1]),
                replace(selected, field_specs=(*selected.field_specs, selected.field_specs[-1])),
                replace(selected, codecs=selected.codecs[:-1])):
        with pytest.raises(BootstrapError):
            state_io((bad,))
    record = GateRecord(GATE_ID, SPACE_ID, 4, 0)
    address = ComponentAddress(GATE.schema, GATE_ID)
    assert io.apply_patch(address, FieldAddress(FieldFamily("encounter.gate", "is_open"), GATE_ID), record, GatePatch(1)) == replace(record, is_open=1)
    for protected in ("space_id", "cell"):
        with pytest.raises(CandidateError, match="UNDECLARED_WRITE"):
            io.apply_patch(address, FieldAddress(FieldFamily("encounter.gate", protected), GATE_ID), record, GatePatch(1))
    actions = EncounterActions().manifest
    other = replace(actions, engine_id="encounter.other")
    with pytest.raises(BootstrapError, match="WRITE_CONFLICT"):
        compile_schedule((actions, other), (
            NodeActivation(NodeKey(Phase.RESOLVE, actions.engine_id), (TypeKey("encounter.attack", 1),), False, False, "A"),
            NodeActivation(NodeKey(Phase.RESOLVE, other.engine_id), (TypeKey("encounter.rest", 1),), False, False, "A"),
        ))
