"""Versioned local walking profile over the existing knowledge world."""

from dataclasses import fields, replace

from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle
from contracts.turn import EngineBinding, NodeActivation, NodeKey
from contracts.world_village import VILLAGE_FAMILY, VILLAGE_OWNER, VILLAGE_PAYLOADS, VillageStep
from domain.canonical import array_value, object_value, seal
from domain.primitives import FieldSpec, Phase
from domain.world_village import DIRECTIONS, ENTRANCE, STEP_SECONDS, VILLAGE_ROWS, VILLAGE_SCHEMA
from engines.world_village import VillageWalker
from orchestration.world_conversation import SpeechGate
from orchestration.world_transport import JourneyGate
from orchestration.world_village import (
    VillageAdapter,
    VillageAdmission,
    VillageCheckpointPolicy,
    VillageCodec,
    VillagePatchRoute,
    VillagePayloadCodec,
    VillageReducer,
)


def village_world_bundle(base: FeatureBundle, place_id: str) -> FeatureBundle:
    schema = dict(base.schema_document)
    schema["components"] = (
        *array_value(schema["components"]),
        {
            "schema": {"kind": VILLAGE_SCHEMA.kind, "version": VILLAGE_SCHEMA.version},
            "fields": {
                "state": {
                    "owner": VILLAGE_OWNER,
                    "storage": "CORE",
                    "tier": "A",
                    "unit": "tile",
                    "scale": 1,
                },
            },
        },
    )
    schema["payloads"] = (
        *array_value(schema["payloads"]),
        *(
            {
                "schema": {"kind": cls.SCHEMA.kind, "version": cls.SCHEMA.version},
                "fields": tuple(field.name for field in fields(cls)),
            }
            for cls in VILLAGE_PAYLOADS
        ),
    )
    rules = dict(base.rules_document)
    rules["village"] = {
        "place_id": place_id,
        "tiles": VILLAGE_ROWS,
        "entrance": (ENTRANCE.x, ENTRANCE.y),
        "directions": DIRECTIONS,
        "seconds_per_step": STEP_SECONDS,
    }
    bindings = tuple(
        replace(
            binding,
            activations=tuple(
                replace(activation, action_kinds=(*activation.action_kinds, VillageStep.SCHEMA))
                if activation.node.phase == Phase.POST_TICK
                else activation
                for activation in binding.activations
            ),
        )
        for binding in base.bindings
    )
    return replace(
        base,
        feature_id="world-transport-knowledge-village-v1",
        bindings=(
            *bindings,
            EngineBinding(
                VillageWalker(),
                "engines.world_village",
                (
                    NodeActivation(
                        NodeKey(Phase.RESOLVE, VILLAGE_OWNER),
                        (VillageStep.SCHEMA,),
                        False,
                        False,
                        "A",
                    ),
                ),
            ),
        ),
        field_specs=(
            *base.field_specs,
            FieldSpec(
                VILLAGE_FAMILY,
                "CORE",
                "A",
                VILLAGE_OWNER,
                ("system.admission", VILLAGE_OWNER),
                "records",
                "tile",
                1,
                None,
                None,
                2,
            ),
        ),
        read_adapters=(*base.read_adapters, AdapterBinding(VillageAdapter())),
        command_routes=(
            *base.command_routes,
            SpeechGate(JourneyGate(VillageAdmission(place_id)), knowledge=True),
        ),
        delta_routes=(*base.delta_routes, VillageReducer()),
        codecs=(*base.codecs, *(VillagePayloadCodec(cls.SCHEMA) for cls in VILLAGE_PAYLOADS)),
        schema_document=object_value(seal(schema)),
        rules_document=object_value(seal(rules)),
        component_codecs=(*base.component_codecs, VillageCodec()),
        patch_routes=(*base.patch_routes, VillagePatchRoute()),
        checkpoint_policy=VillageCheckpointPolicy(base.checkpoint_policy),
    )
