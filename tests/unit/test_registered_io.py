from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
from typing import cast

import pytest

from app.headless import restore_checkpoint, state_io
from contracts.errors import BootstrapError, CandidateError, ReplayFormatError, SchemaError
from contracts.read_views import ComponentPatch
from contracts.turn import CapabilityManifest, PhaseAccess
from domain.canonical import JsonObject, JsonValue, array_value, canonical_json, decode_json, hash_document, object_value, seal
from domain.primitives import ComponentAddress, EntityId, FieldAddress, Phase, TypeKey
from domain.state_types import ComponentRecord, CoreSnapshot
from tests.unit.registered_io_fixtures import ACTOR, GAUGE, LABEL, VALUE, GaugeEngine, GaugePatch, GaugePatchRoute, GaugeRecord, bundle, command, session


def test_component_literal_vectors() -> None:
    io = state_io((bundle(),))
    raw = cast(dict[str, object], json.loads((Path(__file__).resolve().parents[2] / "docs/work_orders/RS-P1-CORE_REFERENCE_VECTORS.json").read_bytes()))
    # Authoring timings contain floats; only the independent canonical vectors are domain inputs.
    artifact = object_value(seal({k: raw[k] for k in ("components", "command")}))
    for vector in array_value(artifact["components"]):
        v = object_value(vector)
        document = object_value(v["document"])
        fields = object_value(document["fields"])
        core = session(value=2 if fields["value"] == 2 else 5).snapshot()
        actual = array_value(io.encode_core(core)["components"])[0]
        assert canonical_json(actual).decode("utf-8") == v["utf8"]
        assert canonical_json(actual).hex() == v["utf8_hex"]
        assert hash_document("component/v1", actual) == v["sha256"]
    v = object_value(artifact["command"])
    actual_command = io.encode_command(command())
    assert actual_command == v["document"]
    assert canonical_json(actual_command).decode("utf-8") == v["utf8"]
    assert hash_document("command/v1", {k: v for k, v in actual_command.items() if k != "command_id"}) == v["sha256"]


def test_exact_schema_fields_and_ranges() -> None:
    io = state_io((bundle(),))
    core = io.encode_core(session().snapshot())
    component = object_value(array_value(core["components"])[0])
    bad_components: tuple[JsonObject, ...] = ({"value": True, "label": "계기"}, {"value": 10, "label": "계기"}, {"value": 2},
                {"value": 2, "label": "e\u0301"}, {"value": 2, "label": "계기", "unknown": 1})
    for bad in bad_components:
        with pytest.raises(ValueError):
            io.decode_core({**core, "components": ({**component, "fields": bad},)})
    for body in (b'{"value":2.0,"label":"x"}', b'{"value":2,"value":3}'):
        with pytest.raises(ValueError):
            decode_json(body)
    with pytest.raises(SchemaError, match="UNSUPPORTED_SCHEMA"):
        io.decode_core({**core, "components": ({**component, "schema": {"kind": "fixture.gauge", "version": 2}},)})
    encoded = io.encode_command(command())
    bad_payloads: tuple[JsonObject, ...] = ({"amount": True}, {"amount": 4}, {}, {"amount": 1, "other": 0})
    for bad in bad_payloads:
        with pytest.raises(ValueError):
            io.decode_command({**encoded, "payload": bad})
    with pytest.raises(ValueError):
        io.decode_command({**encoded, "schema": {"kind": "fixture.adjust", "version": 2}})
    with pytest.raises(ValueError):
        io.decode_core({**core, "components": (component, component)})


def test_duplicate_registration() -> None:
    original = bundle()
    for bad in (replace(original, component_codecs=original.component_codecs * 2),
                replace(original, patch_routes=original.patch_routes * 2),
                replace(original, component_codecs=()), replace(original, read_adapters=()),
                replace(original, patch_routes=()), replace(original, codecs=original.codecs[:-1]),
                replace(original, codecs=original.codecs[1:]),
                replace(original, schema_document={}),
                replace(original, schema_document={**original.schema_document, "payloads": ()}),
                replace(original, field_specs=(replace(original.field_specs[0], maximum=8), original.field_specs[1])),
                replace(original, field_specs=(replace(original.field_specs[0], scale=True), original.field_specs[1]))):
        with pytest.raises(BootstrapError):
            state_io((bad,))


def test_owned_descriptor_documents() -> None:
    original = bundle()
    mutable_rules = dict(original.rules_document)
    io = state_io((replace(original, rules_document=mutable_rules),))
    pins = io.pins
    mutable_rules["initial_value"] = 9
    assert io.pins == pins
    assert state_io((replace(original, rules_document=mutable_rules),)).pins != pins
    document = io.encode_core(session().snapshot())
    with pytest.raises(TypeError):
        # Owned encoders cannot expose a mutable canonical object to their caller.
        cast(dict[str, JsonValue], document)["tick"] = 9


def test_registry_order() -> None:
    original = bundle()
    reversed_bundle = replace(original, codecs=original.codecs[::-1], field_specs=original.field_specs[::-1])
    first, second = state_io((original,)), state_io((reversed_bundle,))
    core = session(original).snapshot()
    assert first.pins == second.pins
    assert canonical_json(first.encode_core(core)) == canonical_json(second.encode_core(core))
    assert first.hash_core(core) == second.hash_core(core)
    assert first is not second


class _MultiplePolicy:
    def validate(self, core: CoreSnapshot, protocol: object) -> None:
        if not core.components or any(c.schema != GAUGE.schema for c in core.components):
            raise ValueError("gauge records required")


def test_policy_required_records() -> None:
    original = bundle()
    live = session(original)
    io = state_io((original,))
    for core in (replace(live.snapshot(), components=()), replace(live.snapshot(), components=(GaugeRecord(EntityId("actor:other"), 2, "계기"),))):
        with pytest.raises(ReplayFormatError):
            restore_checkpoint(core, live.protocol(), bundles=(original,))
    multi = replace(original, checkpoint_policy=_MultiplePolicy())
    records = tuple(GaugeRecord(EntityId("actor:" + str(i)), i, "계기") for i in range(3))
    # Four records with the protocol actor retained; no common toy cardinality constraint.
    core = replace(live.snapshot(), components=(*records, live.snapshot().components[0]))
    own = state_io((multi,))
    own.validate_checkpoint(core, live.protocol())
    assert own.decode_core(own.encode_core(core)) == core
    with pytest.raises(ValueError):
        own.decode_core({**own.encode_core(core), "components": array_value(own.encode_core(core)["components"])[::-1]})
    with pytest.raises(ValueError):
        io.validate_checkpoint(core, live.protocol())


class BadPatchRoute(GaugePatchRoute):
    def __init__(self, mode: str) -> None:
        self.mode = mode

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        assert isinstance(before, GaugeRecord) and isinstance(patch, GaugePatch)
        if self.mode == "label":
            return replace(before, value=patch.value, label="changed")
        if self.mode == "entity":
            return replace(before, value=patch.value, entity_id=EntityId("actor:other"))
        if self.mode == "schema":
            return _WrongSchema(before.entity_id, patch.value, before.label)
        return replace(before, value=10)


class _WrongSchema(GaugeRecord):
    @property
    def schema(self) -> TypeKey:
        return TypeKey("fixture.gauge", 2)


def test_patch_single_field_guard() -> None:
    record = GaugeRecord(ACTOR, 2, "계기")
    address, allowed = ComponentAddress(GAUGE.schema, ACTOR), FieldAddress(VALUE, ACTOR)
    original = bundle()
    io = state_io((original,))
    assert io.apply_patch(address, allowed, record, GaugePatch(5)) == GaugeRecord(ACTOR, 5, "계기")
    for mode in ("label", "entity", "schema", "range"):
        bad = state_io((replace(original, patch_routes=(BadPatchRoute(mode),)),))
        with pytest.raises(CandidateError):
            bad.apply_patch(address, allowed, record, GaugePatch(5))
        assert record == GaugeRecord(ACTOR, 2, "계기")
    with pytest.raises(CandidateError, match="UNDECLARED_WRITE"):
        io.apply_patch(address, FieldAddress(LABEL, ACTOR), record, GaugePatch(5))
    with pytest.raises(CandidateError):
        io.apply_patch(ComponentAddress(GAUGE.schema, EntityId("actor:other")), allowed, record, GaugePatch(5))


class _TwoFields(GaugeEngine):
    @property
    def manifest(self) -> CapabilityManifest:
        original = super().manifest
        return replace(original, writes=(*original.writes, PhaseAccess(Phase.RESOLVE, LABEL)))


def test_same_component_write_conflict() -> None:
    original = bundle()
    conflicting = replace(original, bindings=(replace(original.bindings[0], engine=_TwoFields()),))
    with pytest.raises(BootstrapError, match="WRITE_CONFLICT.*field merge"):
        state_io((conflicting,))
