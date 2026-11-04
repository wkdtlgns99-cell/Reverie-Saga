"""Compose visited local definitions and real inventory with the existing timed world."""

from dataclasses import replace

from app.world_time_registry import timed_world_bundle
from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle
from contracts.turn import EngineBinding, NodeActivation, NodeKey
from contracts.world_population import (
    INVENTORY_FAMILY,
    MATERIALIZER,
    SETTLEMENT_FAMILY,
    SettlementDelta,
    SettlementPatch,
)
from contracts.world_travel import TRAVEL_FAMILY
from domain.canonical import array_value, object_value, seal
from domain.primitives import FieldSpec, Phase
from domain.world import WorldCatalog
from domain.world_population import DAY_ORIGIN_SECONDS, DAY_SECONDS
from engines.world_population import LocalMaterializer
from orchestration.world_population import (
    InventoryAdapter,
    InventoryCodec,
    PopulationCheckpointPolicy,
    SettlementAdapter,
    SettlementCodec,
    SettlementPatchRoute,
    SettlementPayloadCodec,
    SettlementReducer,
)


def population_world_bundle(world: WorldCatalog) -> FeatureBundle:
    base = timed_world_bundle(world)
    schema = dict(base.schema_document)
    schema["components"] = (
        *array_value(schema["components"]),
        {
            "schema": {"kind": "world.settlement", "version": 1},
            "fields": {
                "state": {
                    "owner": MATERIALIZER,
                    "storage": "CORE",
                    "tier": "A",
                    "unit": "local_detail",
                    "scale": 1,
                }
            },
        },
        {
            "schema": {"kind": "world.inventory", "version": 1},
            "fields": {
                "state": {
                    "owner": "system.bootstrap",
                    "storage": "CORE",
                    "tier": "A",
                    "unit": "inventory",
                    "scale": 1,
                }
            },
        },
    )
    schema["payloads"] = (
        *array_value(schema["payloads"]),
        {
            "schema": {"kind": "world.settlement-delta", "version": 1},
            "fields": ("entity_id", "before", "after"),
        },
        {"schema": {"kind": "world.settlement-patch", "version": 1}, "fields": ("state",)},
    )
    rules = dict(base.rules_document)
    rules["population"] = {
        "local_recipe": "local-v1",
        "residents_per_local": 4,
        "day_origin_seconds": DAY_ORIGIN_SECONDS,
        "day_seconds": DAY_SECONDS,
        "work_hours": "stored-start-inclusive-end-exclusive",
        "awake_hours": (6, 22),
        "initial_gold": 0,
        "initial_inventory": (),
        "materialize": "committed-arrival",
    }
    specs = tuple(
        replace(spec, consumers=tuple(sorted((*spec.consumers, MATERIALIZER))))
        if spec.family == TRAVEL_FAMILY
        else spec
        for spec in base.field_specs
    )
    return replace(
        base,
        feature_id="world-population-v1",
        bindings=(
            *base.bindings,
            EngineBinding(
                LocalMaterializer(world),
                "engines.world_population",
                (NodeActivation(NodeKey(Phase.POST_TICK, MATERIALIZER), (), False, True, "A"),),
            ),
        ),
        read_adapters=(
            *base.read_adapters,
            AdapterBinding(SettlementAdapter(world)),
            AdapterBinding(InventoryAdapter()),
        ),
        field_specs=(
            *specs,
            FieldSpec(
                SETTLEMENT_FAMILY,
                "CORE",
                "A",
                MATERIALIZER,
                (MATERIALIZER,),
                "records",
                "local_detail",
                1,
                None,
                None,
                4,
            ),
            FieldSpec(
                INVENTORY_FAMILY,
                "CORE",
                "A",
                "system.bootstrap",
                ("app.inventory",),
                "records",
                "inventory",
                1,
                None,
                None,
                128,
            ),
        ),
        delta_routes=(*base.delta_routes, SettlementReducer(world)),
        codecs=(
            *base.codecs,
            *(
                SettlementPayloadCodec(world, cls.SCHEMA)
                for cls in (SettlementDelta, SettlementPatch)
            ),
        ),
        schema_document=object_value(seal(schema)),
        rules_document=object_value(seal(rules)),
        component_codecs=(*base.component_codecs, SettlementCodec(world), InventoryCodec()),
        patch_routes=(*base.patch_routes, SettlementPatchRoute()),
        checkpoint_policy=PopulationCheckpointPolicy(world),
    )
