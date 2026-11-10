"""Add the durable dungeon to the village combat profile."""

from dataclasses import fields, replace

from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle
from contracts.turn import EngineBinding, NodeActivation, NodeKey
from contracts.world_dungeon import DUNGEON_FAMILY, DUNGEON_OWNER, DUNGEON_PAYLOADS, DungeonAction
from domain.canonical import array_value, object_value, seal
from domain.primitives import EntityId, FieldSpec, Phase
from domain.world_combat import ACTION_SECONDS
from domain.world_dungeon import DUNGEON_SCHEMA, ENTRY
from domain.world_dungeon_loadout import ORC_ENCOUNTER, SWITCH_USES_TURN, WEAPONS, DungeonOpponent
from domain.world_travel import WORLD_ACTOR
from domain.world_village_layout import ROOM_SIZE, DungeonBlueprint
from engines.world_dungeon import DungeonEngine
from orchestration.world_conversation import SpeechGate
from orchestration.world_dungeon import (
    DungeonAdapter,
    DungeonAdmission,
    DungeonCheckpointPolicy,
    DungeonGate,
    DungeonPatchRoute,
    DungeonPayloadCodec,
    DungeonReducer,
)
from orchestration.world_transport import JourneyGate


def dungeon_world_bundle(
    base: FeatureBundle, blueprint: DungeonBlueprint, place_id: str,
    *, opponent: DungeonOpponent = ORC_ENCOUNTER, loadouts: bool = False,
) -> FeatureBundle:
    schema = dict(base.schema_document)
    schema["components"] = (
        *array_value(schema["components"]),
        {
            "schema": {"kind": DUNGEON_SCHEMA.kind, "version": DUNGEON_SCHEMA.version},
            "fields": {
                "state": {
                    "owner": DUNGEON_OWNER,
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
            for cls in DUNGEON_PAYLOADS
        ),
    )
    rules = dict(base.rules_document)
    rules["dungeon"] = {
        "place": place_id,
        "entrance": (blueprint.gate_x, blueprint.gate_y),
        "room_size": ROOM_SIZE,
        "entry": ENTRY,
        "orc": (opponent.actor, blueprint.orc_x, blueprint.orc_y),
        "opener": WORLD_ACTOR,
        "action_seconds": ACTION_SECONDS,
    }
    if loadouts:
        rules["dungeon_loadout"] = {
            "equipment_uses_turn": SWITCH_USES_TURN,
            "weapons": tuple(
                (w.id, w.damage, w.skill_id, w.skill_damage, w.staggers, w.switch_ticks) for w in WEAPONS
            ),
            "opponent": (opponent.kind, opponent.speed, opponent.damage),
        }
    adapter = DungeonAdapter(opponent.actor, loadouts=loadouts)
    bindings = tuple(
        replace(
            binding,
            activations=tuple(
                replace(activation, action_kinds=(*activation.action_kinds, DungeonAction.SCHEMA))
                if activation.node.phase == Phase.POST_TICK
                else activation
                for activation in binding.activations
            ),
        )
        for binding in base.bindings
    )
    return replace(
        base,
        feature_id="world-transport-knowledge-village-dungeon-v2" if loadouts else
        "world-transport-knowledge-village-dungeon-v1",
        bindings=(
            *bindings,
            EngineBinding(
                DungeonEngine(blueprint, opponent),
                "engines.world_dungeon",
                (
                    NodeActivation(
                        NodeKey(Phase.RESOLVE, DUNGEON_OWNER),
                        (DungeonAction.SCHEMA,),
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
                DUNGEON_FAMILY,
                "CORE",
                "A",
                DUNGEON_OWNER,
                ("system.admission", DUNGEON_OWNER),
                "records",
                "state",
                1,
                None,
                None,
                2,
            ),
        ),
        read_adapters=(*base.read_adapters, AdapterBinding(adapter)),
        command_routes=(
            *(DungeonGate(route) for route in base.command_routes),
            SpeechGate(
                JourneyGate(DungeonAdmission(blueprint, EntityId(place_id), loadouts=loadouts)),
                knowledge=True,
            ),
        ),
        delta_routes=(*base.delta_routes, DungeonReducer()),
        codecs=(*base.codecs, *(DungeonPayloadCodec(cls.SCHEMA, opponent.actor) for cls in DUNGEON_PAYLOADS)),
        schema_document=object_value(seal(schema)),
        rules_document=object_value(seal(rules)),
        component_codecs=(*base.component_codecs, adapter),
        patch_routes=(*base.patch_routes, DungeonPatchRoute()),
        checkpoint_policy=DungeonCheckpointPolicy(base.checkpoint_policy, adapter),
    )
