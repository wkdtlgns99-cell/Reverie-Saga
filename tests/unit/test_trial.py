from __future__ import annotations

from dataclasses import replace
from typing import cast

import pytest

from app.headless import state_io
from app.trial_registry import trial_bundle
from contracts.errors import BootstrapError, CandidateError, ExpiredReadView, ReadOnlyViolation, SchemaError
from contracts.read_views import ComponentPatch
from contracts.trial import CELL_POSITION, TRIAL_MAP, CellDelta, CellPatch, MoveCommand
from domain.canonical import (
    JsonObject, array_value, canonical_json, decode_json, hash_document, int_value, object_value,
    text_value,
)
from domain.primitives import ComponentAddress, EntityId, FieldAddress, FieldFamily, TypeKey
from domain.trial import ACTOR_ID, SPACE_ID, CellPositionRecord, TrialMapRecord, cell_coordinates
from orchestration.trial import CellPatchRoute, CellPositionCodec, CellReducer, TrialMapCodec, TrialPayloadCodec
from tests.unit.trial_fixtures import reference, selected_io_pins, session, views


def test_literal_pins_and_components() -> None:
    assert selected_io_pins() == (
        "1710269a9d64c442fac450e009de954d1d1701edea193ade4a9abea76e60b8aa",
        "dbe7a3c61e1d75b4b7b02b693f90dcaa8202d9b878ed321db767bf3098dbf3a3",
        "d6c54291fd7a0b6ff5e06f1ba1b8b3b7e061ca21ee2d132c4b0632838277d6db",
    )
    io = state_io((trial_bundle(),))
    core = session().snapshot()
    assert canonical_json(io.encode_core(core)) == canonical_json(
        object_value(reference("expected_fixture"))["initial_core"])
    assert io.hash_core(core) == "e15eab8bd8e4d27b8ac9d0a652a616cb74bd91820befe53dca06118fddaa56aa"
    for raw in array_value(reference("literal_documents")):
        vector = object_value(raw)
        assert canonical_json(vector["document"]).decode() == vector["utf8"]
        assert canonical_json(vector["document"]).hex() == vector["utf8_hex"]
        assert hash_document(text_value(vector["tag"]), vector["document"]) == vector["sha256"]


def test_exact_payload_shapes() -> None:
    selected = trial_bundle()
    pubs = tuple(object_value(p) for p in array_value(reference("expected_publications")))
    for pub in pubs:
        for family in ("facts", "cues"):
            for item in array_value(pub[family]):
                event = object_value(item)
                key = object_value(object_value(event["header"])["type_key"])
                codec = TrialPayloadCodec(TypeKey(text_value(key["kind"]), int_value(key["version"])))
                payload = object_value(event["payload"])
                assert canonical_json(codec.encode(codec.decode(payload))) == canonical_json(payload)
                for bad in ({**payload, "extra": 0}, {k: v for k, v in payload.items() if k != next(iter(payload))}):
                    with pytest.raises(ValueError):
                        codec.decode(bad)
    for registered in selected.codecs:
        if registered.schema.kind == "trial.move":
            for dx, dz in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                assert registered.decode({"dx": dx, "dz": dz}) == MoveCommand(dx, dz)
    for unsupported in (TypeKey("trial.move", 2), TypeKey("trial.missing", 1)):
        with pytest.raises(SchemaError):
            TrialPayloadCodec(unsupported)
    codec = TrialPayloadCodec(TypeKey("trial.position-delta", 1))
    assert codec.decode({"entity_id": ACTOR_ID, "before_cell": 0, "after_cell": 0}) == CellDelta(ACTOR_ID, 0, 0)
    invalid_bodies: tuple[JsonObject, ...] = (
        {"entity_id": "actor:e\u0301", "before_cell": 0, "after_cell": 3},
        {"entity_id": ACTOR_ID, "before_cell": True, "after_cell": 3})
    for body in invalid_bodies:
        with pytest.raises(ValueError):
            codec.decode(body)
    with pytest.raises(ValueError):
        decode_json(b'{"dx":1.0,"dz":0}')
    with pytest.raises(ValueError):
        decode_json(b'{"dx":1,"dx":0,"dz":0}')


def test_fact_and_cue_semantic_validation() -> None:
    first = object_value(array_value(reference("expected_publications"))[0])
    moved = object_value(array_value(reference("expected_publications"))[1])
    blocked_body = object_value(object_value(array_value(first["facts"])[0])["payload"])
    moved_body = object_value(object_value(array_value(moved["facts"])[0])["payload"])
    cue_body = object_value(object_value(array_value(moved["cues"])[0])["payload"])
    cases: tuple[tuple[str, JsonObject], ...] = (
        ("move-blocked", {**blocked_body, "reason": "boundary"}),
        ("move-blocked", {**blocked_body, "reason": "unknown"}),
        ("move-blocked", {**blocked_body, "dx": 0, "dz": 1}),
        ("move-blocked", {**blocked_body, "from_cell": 1}),
        ("move-blocked", {**blocked_body, "dx": True}),
        ("moved", {**moved_body, "from_cell": 2, "to_cell": 3}),
        ("moved", {**moved_body, "to_cell": 1}),
        ("moved", {**moved_body, "to_cell": 0}),
        ("moved", {**moved_body, "actor_id": "actor:other"}),
        ("moved", {**moved_body, "space_id": "space:other"}),
        ("moved", {**moved_body, "from_cell": False}),
        ("move-cue", {**cue_body, "to_z_mm": 999}),
        ("move-cue", {**cue_body, "from_x_mm": False}),
        ("move-cue", {**cue_body, "result": "occupied"}),
        ("move-cue", {**cue_body, "result": "unknown"}),
        ("position-patch", {"cell": -1}),
        ("position-patch", {"cell": True}),
        ("position-delta", {"entity_id": ACTOR_ID, "before_cell": 0, "after_cell": 9}),
    )
    for kind, invalid in cases:
        with pytest.raises(ValueError):
            TrialPayloadCodec(TypeKey("trial." + kind, 1)).decode(invalid)


@pytest.mark.parametrize("blocks", [(), (1, 1), (2, 1), (9,), (-1,), (True,), (False,), (2,)])
def test_fixed_map_and_position_validation(blocks: tuple[int, ...]) -> None:
    map_codec = TrialMapCodec()
    record = TrialMapRecord(SPACE_ID, 3, 3, 1000, blocks)
    with pytest.raises(ValueError):
        map_codec.encode(record)
    with pytest.raises(ValueError):
        map_codec.decode(SPACE_ID, {"width": 3, "height": 3, "cell_mm": 1000, "blocked_cells": blocks})


def test_component_field_and_identity_validation() -> None:
    io = state_io((trial_bundle(),))
    owner = session()
    grid, position = owner.snapshot().components
    assert isinstance(grid, TrialMapRecord) and isinstance(position, CellPositionRecord)
    for bad in (replace(grid, width=True), replace(grid, height=4), replace(grid, cell_mm=999),
                replace(grid, blocked_cells=cast(tuple[int, ...], [1]))):
        with pytest.raises(ValueError):
            TrialMapCodec().encode(bad)
    for bad_position in (replace(position, cell=True), replace(position, cell=9),
                replace(position, space_id=EntityId("bad space"))):
        with pytest.raises(ValueError):
            CellPositionCodec().encode(bad_position)
    for components in ((grid,), (grid, replace(position, cell=1)),
                       (grid, replace(position, space_id=EntityId("space:missing"))),
                       (replace(grid, entity_id=EntityId("space:other")), position)):
        with pytest.raises(ValueError):
            io.validate_checkpoint(replace(owner.snapshot(), components=components), owner.protocol())


def test_cell_coordinates() -> None:
    for raw in array_value(reference("coordinates")):
        vector = object_value(raw)
        assert cell_coordinates(int_value(vector["cell"])) == (vector["x_mm"], vector["z_mm"])
    for invalid in (-1, 9, True, False, cast(int, 1.0)):
        with pytest.raises(ValueError):
            cell_coordinates(invalid)


def test_read_observation_and_expiry() -> None:
    factory, epoch = views()
    port = factory.open(epoch)
    grid = port.component(TRIAL_MAP, SPACE_ID)
    position = port.component(CELL_POSITION, ACTOR_ID)
    assert (grid.width, grid.height, grid.cell_mm, position.cell, position.space_id) == (3, 3, 1000, 0, SPACE_ID)
    assert grid.is_blocked(1) is True and grid.is_blocked(0) is False
    with pytest.raises(ValueError):
        grid.is_blocked(9)
    for alias, name in ((grid, "width"), (position, "cell")):
        with pytest.raises(ReadOnlyViolation):
            setattr(alias, name, 99)
        with pytest.raises(ReadOnlyViolation):
            delattr(alias, name)
    observations = factory.close(epoch)
    assert [(o.target.family.field, o.path, o.operation) for o in observations[:8]] == [
        ("width", (), "read"), ("height", (), "read"), ("cell_mm", (), "read"),
        ("cell", (), "read"), ("space_id", (), "read"),
        ("blocked_cells", (), "membership"), ("blocked_cells", (), "membership"),
        ("blocked_cells", (), "membership"),
    ]
    for read in (lambda: grid.width, lambda: grid.height, lambda: grid.cell_mm,
                 lambda: position.cell, lambda: position.space_id, lambda: grid.is_blocked(True),
                 lambda: setattr(position, "cell", 0), lambda: delattr(grid, "width")):
        with pytest.raises(ExpiredReadView):
            read()


class _Editor:
    def __init__(self) -> None:
        self.applied: list[tuple[ComponentAddress, ComponentPatch]] = []

    def apply_patch(self, address: ComponentAddress, patch: ComponentPatch) -> None:
        self.applied.append((address, patch))


def test_cell_reducer_old_value_composition() -> None:
    reducer = CellReducer()
    factory, epoch = views()
    port, editor = factory.open(epoch), _Editor()
    reducer.stage(CellDelta(ACTOR_ID, 0, 3), port, editor)
    assert editor.applied == [(ComponentAddress(CELL_POSITION.schema, ACTOR_ID), CellPatch(3))]
    for delta in (CellDelta(ACTOR_ID, 3, 4), CellDelta(ACTOR_ID, 0, 1),
                  CellDelta(ACTOR_ID, 0, 0), CellDelta(ACTOR_ID, 2, 3), CellDelta(ACTOR_ID, 0, 6)):
        with pytest.raises(CandidateError):
            reducer.stage(delta, port, editor)
    observed = factory.close(epoch)
    assert all(o.target == CellDelta(ACTOR_ID, 0, 3).target and o.operation == "read" for o in observed)
    assert reducer.compose((CellDelta(ACTOR_ID, 0, 3), CellDelta(ACTOR_ID, 3, 4))) == CellDelta(ACTOR_ID, 0, 4)
    identity = reducer.compose((CellDelta(ACTOR_ID, 0, 3), CellDelta(ACTOR_ID, 3, 0)))
    assert reducer.is_identity(identity) is True
    for changes in ((), (CellDelta(ACTOR_ID, 0, 3), CellDelta(ACTOR_ID, 4, 5)),
                    (CellDelta(ACTOR_ID, 0, 3), CellDelta(EntityId("actor:other"), 3, 4))):
        with pytest.raises(CandidateError):
            reducer.compose(changes)
    after_factory, after_epoch = views(4)
    after = after_factory.open(after_epoch)
    reducer.validate_net(CellDelta(ACTOR_ID, 0, 4), after)
    for net_delta in (identity, CellDelta(ACTOR_ID, 0, 3)):
        with pytest.raises(CandidateError):
            reducer.validate_net(net_delta, after)
    assert all(o.target.family == FieldFamily("trial.position", "cell") for o in after_factory.close(after_epoch))


def test_patch_and_registry_ownership() -> None:
    selected = trial_bundle()
    io = state_io((selected,))
    position = CellPositionRecord(ACTOR_ID, SPACE_ID, 0)
    allowed = FieldAddress(FieldFamily("trial.position", "cell"), ACTOR_ID)
    assert io.apply_patch(ComponentAddress(CELL_POSITION.schema, ACTOR_ID), allowed,
                          position, CellPatch(3)) == CellPositionRecord(ACTOR_ID, SPACE_ID, 3)
    with pytest.raises(ValueError):
        CellPatchRoute().apply(position, CellPatch(True))
    with pytest.raises(CandidateError, match="UNDECLARED_WRITE"):
        io.apply_patch(ComponentAddress(CELL_POSITION.schema, ACTOR_ID),
                       FieldAddress(FieldFamily("trial.position", "space_id"), ACTOR_ID),
                       position, CellPatch(3))
    wrong_route = _WrongOwnerPatch()
    for bad in (replace(selected, field_specs=selected.field_specs[:-1]),
                replace(selected, field_specs=(*selected.field_specs, selected.field_specs[-1])),
                replace(selected, patch_routes=(wrong_route,))):
        with pytest.raises(BootstrapError):
            state_io((bad,))


class _WrongOwnerPatch(CellPatchRoute):
    @property
    def family(self) -> FieldFamily:
        return FieldFamily("trial.map", "width")
