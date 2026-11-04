"""Register the world walker with the existing engine/state/commit infrastructure."""

from contracts.messages import EventPolicy
from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle, PresenterBinding
from contracts.turn import EngineBinding, NodeActivation, NodeKey
from contracts.world_travel import (
    TRAVEL_FAMILY,
    TRAVEL_OWNER,
    TRAVEL_PAYLOADS,
    Footstep,
    Walked,
)
from domain.canonical import object_value, seal
from domain.primitives import FieldSpec, Phase
from domain.world import WorldCatalog
from engines.world_travel import WorldWalker
from orchestration.world_travel import (
    FootAdmission,
    TravelPatchRoute,
    TravelPayloadCodec,
    TravelReducer,
    TravelerAdapter,
    TravelerCodec,
    WorldCheckpointPolicy,
    WalkPresenter,
)


def world_bundle(world: WorldCatalog) -> FeatureBundle:
    schema = object_value(
        seal(
            {
                "version": 1,
                "unknown_fields": "reject",
                "bool_as_integer": "reject",
                "components": (
                    {
                        "schema": {"kind": "world.traveler", "version": 1},
                        "fields": {
                            "state": {
                                "owner": TRAVEL_OWNER,
                                "storage": "CORE",
                                "tier": "A",
                                "unit": "travel_state",
                                "scale": 1,
                            }
                        },
                    },
                ),
                "payloads": (
                    {
                        "schema": {"kind": "world.walk-cue", "version": 1},
                        "fields": ("actor_id", "before", "after"),
                    },
                    {
                        "schema": {"kind": "world.footstep", "version": 1},
                        "fields": ("destination_id", "direction"),
                    },
                    {
                        "schema": {"kind": "world.travel-delta", "version": 1},
                        "fields": ("entity_id", "before", "after"),
                    },
                    {"schema": {"kind": "world.travel-patch", "version": 1}, "fields": ("state",)},
                    {
                        "schema": {"kind": "world.walked", "version": 1},
                        "fields": ("actor_id", "before", "after"),
                    },
                ),
            }
        )
    )
    rules = object_value(
        seal(
            {
                "version": 1,
                "world": world.document(),
                "meters_per_step": 1,
                "duration_seconds": 1,
                "directions": (-1, 1),
                "water_requires_transport": True,
                "rng_purposes": (),
                "record_only": True,
            }
        )
    )
    engine = WorldWalker(world)
    binding = EngineBinding(
        engine,
        "engines.world_travel",
        (
            NodeActivation(
                NodeKey(Phase.RESOLVE, TRAVEL_OWNER), (Footstep.SCHEMA,), False, False, "A"
            ),
        ),
    )
    return FeatureBundle(
        "world-foot-v1",
        (binding,),
        (AdapterBinding(TravelerAdapter(world)),),
        (
            FieldSpec(
                TRAVEL_FAMILY,
                "CORE",
                "A",
                TRAVEL_OWNER,
                ("system.admission", TRAVEL_OWNER),
                "records",
                "travel_state",
                1,
                None,
                None,
                256,
            ),
        ),
        (
            EventPolicy(
                Walked.SCHEMA, "record_only", Phase.PRESENT, 0, "reject", (TRAVEL_OWNER,), (), ()
            ),
        ),
        (FootAdmission(world),),
        (TravelReducer(world),),
        (PresenterBinding("world.presenter", (Walked.SCHEMA,), WalkPresenter()),),
        tuple(TravelPayloadCodec(kind.SCHEMA) for kind in TRAVEL_PAYLOADS),
        schema,
        rules,
        (TravelerCodec(world),),
        (TravelPatchRoute(),),
        WorldCheckpointPolicy(world),
    )
