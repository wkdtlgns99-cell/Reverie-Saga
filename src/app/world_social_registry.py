"""Opt-in social profile retains every earlier profile's rules and save identity."""

from dataclasses import fields, replace

from app.world_conversation_registry import conversation_world_bundle
from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle
from contracts.turn import EngineBinding, NodeActivation, NodeKey
from contracts.world_social import SOCIAL_FAMILY, SOCIAL_OWNER, SOCIAL_PAYLOADS, SocialAction
from contracts.world_supply import SUPPLY_FAMILY
from contracts.world_travel import TRAVEL_FAMILY
from domain.canonical import array_value, object_value, seal
from domain.primitives import FieldSpec, Phase
from domain.world import WorldCatalog
from domain.world_social import (
    DELIVERY_REPUTATION,
    HOSTILE_THRESHOLD,
    PROTEST_REPUTATION,
    RECONCILE_REPUTATION,
    SHARED_ANCESTRY_FAMILIARITY,
    SOCIAL_DURATIONS,
    SocialCatalog,
)
from domain.world_supply import SupplyScenario
from engines.world_social import WorldSocial
from orchestration.world_conversation import ConversationAdmission, SpeechGate
from orchestration.world_social import (
    SocialAdapter,
    SocialAdmission,
    SocialCheckpointPolicy,
    SocialCodec,
    SocialGate,
    SocialPatchRoute,
    SocialPayloadCodec,
    SocialReducer,
)


def social_world_bundle(
    world: WorldCatalog, catalog: SocialCatalog, scenario: SupplyScenario = SupplyScenario()
) -> FeatureBundle:
    catalog.validate(world)
    base = conversation_world_bundle(world, scenario)
    schema = dict(base.schema_document)
    schema["components"] = (
        *array_value(schema["components"]),
        {
            "schema": {"kind": "world.social", "version": 1},
            "fields": {
                "state": {
                    "owner": SOCIAL_OWNER,
                    "storage": "CORE",
                    "tier": "A",
                    "unit": "reputation",
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
                "fields": tuple(f.name for f in fields(cls)),
            }
            for cls in SOCIAL_PAYLOADS
        ),
    )
    rules = dict(base.rules_document)
    rules["social"] = {
        "catalog": catalog.document(),
        "context": "public-social-standing-v1",
        "durations": SOCIAL_DURATIONS,
        "protest": {"local": PROTEST_REPUTATION[0], "national": PROTEST_REPUTATION[1]},
        "reconcile": {
            "local": RECONCILE_REPUTATION[0],
            "national": RECONCILE_REPUTATION[1],
            "ceiling": 0,
            "preserve_positive": True,
        },
        "delivery": {
            "local": DELIVERY_REPUTATION[0],
            "national": DELIVERY_REPUTATION[1],
            "once_per_city": True,
        },
        "reputation_range": (-100, 100),
        "hostile_threshold": HOSTILE_THRESHOLD,
        "reaction": "national-diplomacy-plus-national-and-local-earned-reputation",
        "shared_ancestry_tone": SHARED_ANCESTRY_FAMILIARITY,
        "identity": "choose-once-independent-of-ancestry-morality",
        "gate": "new-entry-and-contract-only-never-strand-existing-cargo",
    }
    routes = []
    for route in base.command_routes:
        if isinstance(route, ConversationAdmission):
            route = ConversationAdmission(world, scenario, route.schema, social=catalog)
        routes.append(SocialGate(route, catalog))
    specs = tuple(
        replace(s, consumers=tuple(sorted(set((*s.consumers, SOCIAL_OWNER)))))
        if s.family in (TRAVEL_FAMILY, SUPPLY_FAMILY)
        else s
        for s in base.field_specs
    )
    return replace(
        base,
        feature_id="world-social-v1",
        bindings=(
            *base.bindings,
            EngineBinding(
                WorldSocial(catalog),
                "engines.world_social",
                (
                    NodeActivation(
                        NodeKey(Phase.RESOLVE, SOCIAL_OWNER),
                        (SocialAction.SCHEMA,),
                        False,
                        False,
                        "A",
                    ),
                    NodeActivation(NodeKey(Phase.POST_TICK, SOCIAL_OWNER), (), False, True, "A"),
                ),
            ),
        ),
        read_adapters=(*base.read_adapters, AdapterBinding(SocialAdapter(catalog))),
        field_specs=(
            *specs,
            FieldSpec(
                SOCIAL_FAMILY,
                "CORE",
                "A",
                SOCIAL_OWNER,
                ("system.admission", SOCIAL_OWNER),
                "records",
                "reputation",
                1,
                None,
                None,
                4,
            ),
        ),
        command_routes=(*routes, SpeechGate(SocialAdmission(catalog))),
        delta_routes=(*base.delta_routes, SocialReducer(catalog)),
        codecs=(
            *base.codecs,
            *(SocialPayloadCodec(cls.SCHEMA, catalog) for cls in SOCIAL_PAYLOADS),
        ),
        schema_document=object_value(seal(schema)),
        rules_document=object_value(seal(rules)),
        component_codecs=(*base.component_codecs, SocialCodec(catalog)),
        patch_routes=(*base.patch_routes, SocialPatchRoute()),
        checkpoint_policy=SocialCheckpointPolicy(world, scenario, catalog),
    )
