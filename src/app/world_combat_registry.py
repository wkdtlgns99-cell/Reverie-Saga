"""Extend the village profile with a single durable encounter owner."""

from dataclasses import fields, replace

from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle
from contracts.turn import EngineBinding, NodeActivation, NodeKey
from contracts.world_combat import COMBAT_FAMILY, COMBAT_OWNER, COMBAT_PAYLOADS, CombatAction
from contracts.world_population import SETTLEMENT_FAMILY
from contracts.world_village import VILLAGE_FAMILY
from domain.canonical import array_value, object_value, seal
from domain.primitives import EntityId, FieldSpec, Phase
from domain.world_combat import (
    ACTION_SECONDS,
    AMBUSH_TILE,
    ATTACK_RANGE,
    BANDIT_DAMAGE,
    BANDIT_POSITION,
    COMBAT_SCHEMA,
    JOIN_RADIUS,
    MAX_HP,
    PLAYER_DAMAGE,
)
from engines.world_combat import VillageCombat
from orchestration.world_combat import (
    CombatAdapter,
    CombatAdmission,
    CombatCheckpointPolicy,
    CombatGate,
    CombatPatchRoute,
    CombatPayloadCodec,
    CombatReducer,
)
from orchestration.world_conversation import SpeechGate
from orchestration.world_transport import JourneyGate


def combat_world_bundle(base: FeatureBundle, place_id: str) -> FeatureBundle:
    schema = dict(base.schema_document)
    schema["components"] = (
        *array_value(schema["components"]),
        {
            "schema": {"kind": COMBAT_SCHEMA.kind, "version": COMBAT_SCHEMA.version},
            "fields": {
                "state": {
                    "owner": COMBAT_OWNER,
                    "storage": "CORE",
                    "tier": "A",
                    "scale": 1,
                    "unit": "state",
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
            for cls in COMBAT_PAYLOADS
        ),
    )
    rules = dict(base.rules_document)
    rules["village_combat"] = {
        "place": place_id,
        "bandit_tile": (BANDIT_POSITION.x, BANDIT_POSITION.y),
        "ambush_tile": (AMBUSH_TILE.x, AMBUSH_TILE.y),
        "opening_radius_tiles": JOIN_RADIUS,
        "attack_range_tiles": ATTACK_RANGE,
        "action_seconds": ACTION_SECONDS,
        "maximum_health": MAX_HP,
        "player_damage": PLAYER_DAMAGE,
        "bandit_damage": BANDIT_DAMAGE,
    }
    bindings = tuple(
        replace(
            binding,
            activations=tuple(
                replace(activation, action_kinds=(*activation.action_kinds, CombatAction.SCHEMA))
                if activation.node.phase == Phase.POST_TICK
                else activation
                for activation in binding.activations
            ),
        )
        for binding in base.bindings
    )
    place = EntityId(place_id)
    return replace(
        base,
        feature_id="world-transport-knowledge-village-combat-v1",
        bindings=(
            *bindings,
            EngineBinding(
                VillageCombat(place),
                "engines.world_combat",
                (
                    NodeActivation(
                        NodeKey(Phase.RESOLVE, COMBAT_OWNER),
                        (CombatAction.SCHEMA,),
                        False,
                        False,
                        "A",
                    ),
                ),
            ),
        ),
        field_specs=(
            *(
                replace(spec, consumers=(*spec.consumers, COMBAT_OWNER))
                if spec.family in (VILLAGE_FAMILY, SETTLEMENT_FAMILY)
                else spec
                for spec in base.field_specs
            ),
            FieldSpec(
                COMBAT_FAMILY,
                "CORE",
                "A",
                COMBAT_OWNER,
                ("system.admission", COMBAT_OWNER),
                "records",
                "state",
                1,
                None,
                None,
                5,
            ),
        ),
        read_adapters=(*base.read_adapters, AdapterBinding(CombatAdapter())),
        command_routes=(
            *(CombatGate(route, place) for route in base.command_routes),
            SpeechGate(JourneyGate(CombatAdmission(place)), knowledge=True),
        ),
        delta_routes=(*base.delta_routes, CombatReducer()),
        codecs=(*base.codecs, *(CombatPayloadCodec(cls.SCHEMA) for cls in COMBAT_PAYLOADS)),
        schema_document=object_value(seal(schema)),
        rules_document=object_value(seal(rules)),
        component_codecs=(*base.component_codecs, CombatAdapter()),
        patch_routes=(*base.patch_routes, CombatPatchRoute()),
        checkpoint_policy=CombatCheckpointPolicy(base.checkpoint_policy),
    )
