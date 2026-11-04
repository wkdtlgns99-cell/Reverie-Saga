"""Isolated living-world supply profile,without changing earlier save identities."""

from dataclasses import asdict, fields, replace

from app.world_population_registry import population_world_bundle
from contracts.messages import EventPolicy
from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle, PresenterBinding
from contracts.turn import EngineBinding, NodeActivation, NodeKey
from contracts.world_population import INVENTORY_FAMILY, SETTLEMENT_FAMILY
from contracts.world_supply import (
    SUPPLY_FAMILY,
    SUPPLY_OWNER,
    SUPPLY_PAYLOADS,
    SupplyAction,
    SupplyActed,
)
from contracts.world_travel import TRAVEL_FAMILY
from domain.canonical import array_value, object_value, seal
from domain.primitives import FieldSpec, Phase
from domain.world import WorldCatalog
from domain.world_supply import (
    CONSUMPTION_INTERVAL_SECONDS,
    DELIVERY_REWARD,
    INITIAL_TREASURY,
    REPAIR_CRATES,
    STOCK_CAP,
    SUPPLY_INTERVAL_SECONDS,
    WAREHOUSE_CAP,
    SupplyScenario,
)
from engines.world_supply import WorldSupply
from orchestration.world_supply import (
    InventoryPatchRoute,
    InventoryReducer,
    SupplyAdapter,
    SupplyAdmission,
    SupplyCheckpointPolicy,
    SupplyCodec,
    SupplyPatchRoute,
    SupplyPayloadCodec,
    SupplyPresenter,
    SupplyReducer,
)


def supply_world_bundle(
    world: WorldCatalog, scenario: SupplyScenario = SupplyScenario()
) -> FeatureBundle:
    world.place(scenario.place_id)
    base = population_world_bundle(world)
    schema = dict(base.schema_document)
    components = []
    for raw in array_value(schema["components"]):
        component = dict(object_value(raw))
        if object_value(component["schema"])["kind"] == INVENTORY_FAMILY.component:
            component["fields"] = {
                "state": {
                    "owner": SUPPLY_OWNER,
                    "storage": "CORE",
                    "tier": "A",
                    "unit": "inventory",
                    "scale": 1,
                }
            }
        components.append(component)
    schema["components"] = (
        *components,
        {
            "schema": {"kind": "world.supply", "version": 1},
            "fields": {
                "state": {
                    "owner": SUPPLY_OWNER,
                    "storage": "CORE",
                    "tier": "A",
                    "unit": "city_supply",
                    "scale": 1,
                }
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
            for cls in SUPPLY_PAYLOADS
        ),
    )
    policies = (
        *base.events,
        EventPolicy(
            SupplyActed.SCHEMA, "record_only", Phase.PRESENT, 0, "reject", (SUPPLY_OWNER,), (), ()
        ),
    )
    rules = dict(base.rules_document)
    rules["supply"] = {
        "scenario": asdict(scenario),
        "stock_cap": STOCK_CAP,
        "warehouse_cap": WAREHOUSE_CAP,
        "initial_treasury": INITIAL_TREASURY,
        "receive_transfer_seconds": SUPPLY_INTERVAL_SECONDS,
        "consumption_seconds": CONSUMPTION_INTERVAL_SECONDS,
        "repair_crates": REPAIR_CRATES,
        "reward": DELIVERY_REWARD,
        "order": ("expire", "consume", "receive", "transfer"),
        "action_seconds": 1,
        "expiry": "retain-player-cargo-no-reward",
        "reach": "same-city-saved-role",
    }
    rules["event_policies"] = tuple(
        {
            "schema": {"kind": p.schema.kind, "version": p.schema.version},
            "mode": p.mode,
            "delivery_phase": p.delivery_phase.name,
            "priority": p.priority,
            "late_route": p.late_route,
            "producers": tuple(sorted(p.producers)),
            "subscribers": tuple(sorted(p.subscribers)),
            "cancellers": (),
        }
        for p in sorted(policies, key=lambda p: (p.schema.kind, p.schema.version))
    )
    specs = []
    for spec in base.field_specs:
        if spec.family in (TRAVEL_FAMILY, SETTLEMENT_FAMILY, INVENTORY_FAMILY):
            spec = replace(
                spec,
                consumers=tuple(sorted(set((*spec.consumers, SUPPLY_OWNER, "system.admission")))),
            )
        if spec.family == INVENTORY_FAMILY:
            spec = replace(spec, owner_id=SUPPLY_OWNER)
        specs.append(spec)
    return replace(
        base,
        feature_id="world-supply-v1",
        bindings=(
            *base.bindings,
            EngineBinding(
                WorldSupply(world, scenario),
                "engines.world_supply",
                (
                    NodeActivation(
                        NodeKey(Phase.RESOLVE, SUPPLY_OWNER),
                        (SupplyAction.SCHEMA,),
                        False,
                        False,
                        "A",
                    ),
                    NodeActivation(NodeKey(Phase.POST_TICK, SUPPLY_OWNER), (), False, True, "A"),
                ),
            ),
        ),
        read_adapters=(*base.read_adapters, AdapterBinding(SupplyAdapter(world))),
        field_specs=(
            *specs,
            FieldSpec(
                SUPPLY_FAMILY,
                "CORE",
                "A",
                SUPPLY_OWNER,
                ("system.admission", SUPPLY_OWNER),
                "records",
                "city_supply",
                1,
                None,
                None,
                12,
            ),
        ),
        events=policies,
        command_routes=(*base.command_routes, SupplyAdmission(scenario)),
        presenters=(
            *base.presenters,
            PresenterBinding("world.supply-presenter", (SupplyActed.SCHEMA,), SupplyPresenter()),
        ),
        delta_routes=(*base.delta_routes, SupplyReducer(), InventoryReducer()),
        codecs=(*base.codecs, *(SupplyPayloadCodec(cls.SCHEMA) for cls in SUPPLY_PAYLOADS)),
        schema_document=object_value(seal(schema)),
        rules_document=object_value(seal(rules)),
        component_codecs=(*base.component_codecs, SupplyCodec(world)),
        patch_routes=(*base.patch_routes, SupplyPatchRoute(), InventoryPatchRoute()),
        checkpoint_policy=SupplyCheckpointPolicy(world, scenario),
    )
