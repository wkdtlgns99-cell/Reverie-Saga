"""Transport opt-in with exact endpoint work and unchanged shared turn machinery."""

from dataclasses import fields, replace

from app.world_social_registry import social_world_bundle
from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle
from contracts.turn import EngineBinding, NodeKey
from contracts.world_supply import SUPPLY_OWNER
from contracts.world_transport import (
    JOURNEY_FAMILY,
    SUPPLY_PROGRESS_FAMILY,
    TRANSPORT_PAYLOADS,
    SupplyProgressDelta,
    SupplyProgressPatch,
    TransportAction,
)
from contracts.world_travel import Footstep, TRAVEL_OWNER
from domain.canonical import array_value, object_value, seal
from domain.primitives import MAX_INT, FieldSpec, Phase
from domain.world import WorldCatalog
from domain.world_social import SocialCatalog
from domain.world_supply import SupplyScenario
from domain.world_transport import TransportRules
from engines.world_supply import WorldSupply
from engines.world_travel import WorldWalker
from orchestration.world_conversation import SpeechGate
from orchestration.world_supply_progress import (
    SupplyProgressAdapter,
    SupplyProgressCodec,
    SupplyProgressPatchRoute,
    SupplyProgressPayloadCodec,
    SupplyProgressReducer,
)
from orchestration.world_transport import (
    JourneyAdapter,
    JourneyCodec,
    JourneyGate,
    JourneyPatchRoute,
    JourneyPayloadCodec,
    JourneyReducer,
    TransportAdmission,
    TransportCheckpointPolicy,
    TransportArrivalReducer,
)


def transport_world_bundle(
    world: WorldCatalog,
    social: SocialCatalog,
    transport: TransportRules,
    scenario: SupplyScenario = SupplyScenario(),
) -> FeatureBundle:
    transport.validate(world)
    base = social_world_bundle(world, social, scenario)
    kinds = (*tuple(r.schema for r in base.command_routes), TransportAction.SCHEMA)
    bindings = []
    for binding in base.bindings:
        engine = binding.engine
        owner = engine.manifest.engine_id
        if owner == TRAVEL_OWNER:
            engine = WorldWalker(world, transport)
        elif owner == SUPPLY_OWNER:
            engine = WorldSupply(world, scenario, catch_up=True)
        activations = []
        for activation in binding.activations:
            if activation.every_tick:
                activation = replace(activation, every_tick=False, action_kinds=kinds)
            elif activation.node == NodeKey(Phase.RESOLVE, TRAVEL_OWNER):
                activation = replace(
                    activation, action_kinds=(Footstep.SCHEMA, TransportAction.SCHEMA)
                )
            activations.append(activation)
        bindings.append(EngineBinding(engine, binding.module_path, tuple(activations)))
    schema = dict(base.schema_document)
    schema["components"] = (
        *array_value(schema["components"]),
        *(
            {
                "schema": {"kind": family.component, "version": 1},
                "fields": {
                    "state": {
                        "owner": owner,
                        "storage": "CORE",
                        "tier": "A",
                        "unit": unit,
                        "scale": 1,
                        **(
                            {"minimum": 0, "maximum": MAX_INT}
                            if family == SUPPLY_PROGRESS_FAMILY
                            else {}
                        ),
                    }
                },
            }
            for family, owner, unit in (
                (JOURNEY_FAMILY, TRAVEL_OWNER, "journey"),
                (SUPPLY_PROGRESS_FAMILY, SUPPLY_OWNER, "seconds"),
            )
        ),
    )
    schema["payloads"] = (
        *array_value(schema["payloads"]),
        *(
            {
                "schema": {"kind": cls.SCHEMA.kind, "version": cls.SCHEMA.version},
                "fields": tuple(f.name for f in fields(cls)),
            }
            for cls in TRANSPORT_PAYLOADS
        ),
    )
    rules = dict(base.rules_document)
    if transport.segment_seconds > 16:
        rules["time_summary"] = {
            "maximum_seconds": transport.segment_seconds,
            "commands": (
                {"kind": TransportAction.SCHEMA.kind, "version": TransportAction.SCHEMA.version},
            ),
        }
    rules["transport"] = {
        "catalog": transport.document(),
        "fare": 0,
        "interruption": "player-wait-resume-return",
        "supply_catchup": "exact-periodic-boundaries-v1",
        "activation": "endpoint-only-no-queued-events",
    }
    return replace(
        base,
        feature_id="world-transport-v1",
        bindings=tuple(bindings),
        read_adapters=(
            *base.read_adapters,
            AdapterBinding(JourneyAdapter()),
            AdapterBinding(SupplyProgressAdapter()),
        ),
        field_specs=(
            *base.field_specs,
            FieldSpec(
                JOURNEY_FAMILY,
                "CORE",
                "A",
                TRAVEL_OWNER,
                ("system.admission", TRAVEL_OWNER),
                "records",
                "journey",
                1,
                None,
                None,
                7,
            ),
            FieldSpec(
                SUPPLY_PROGRESS_FAMILY,
                "CORE",
                "A",
                SUPPLY_OWNER,
                (SUPPLY_OWNER,),
                "integer",
                "seconds",
                1,
                0,
                MAX_INT,
                None,
            ),
        ),
        command_routes=(
            *(JourneyGate(r) for r in base.command_routes),
            SpeechGate(TransportAdmission(world, transport, social)),
        ),
        delta_routes=(
            *base.delta_routes,
            JourneyReducer(),
            SupplyProgressReducer(),
            TransportArrivalReducer(world),
        ),
        codecs=(
            *base.codecs,
            *(
                SupplyProgressPayloadCodec(cls.SCHEMA)
                if cls in (SupplyProgressDelta, SupplyProgressPatch)
                else JourneyPayloadCodec(cls.SCHEMA)
                for cls in TRANSPORT_PAYLOADS
            ),
        ),
        schema_document=object_value(seal(schema)),
        rules_document=object_value(seal(rules)),
        component_codecs=(*base.component_codecs, JourneyCodec(), SupplyProgressCodec()),
        patch_routes=(*base.patch_routes, JourneyPatchRoute(), SupplyProgressPatchRoute()),
        checkpoint_policy=TransportCheckpointPolicy(world, transport, social, scenario),
    )
