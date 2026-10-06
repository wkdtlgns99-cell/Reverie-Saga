from __future__ import annotations

from contracts.messages import EventPolicy
from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle, PresenterBinding
from contracts.turn import EngineBinding, NodeActivation, NodeKey
from domain.canonical import decode_json, object_value
from domain.primitives import FieldFamily, FieldSpec, Phase, TypeKey
from engines.trial import Movement
from orchestration.trial import (
    CellPatchRoute, CellPositionAdapter, CellPositionCodec, CellReducer, MoveAdmission,
    MovePresenter, TrialCheckpointPolicy, TrialMapAdapter, TrialMapCodec, TrialPayloadCodec,
)


def trial_bundle() -> FeatureBundle:
    movement = Movement()
    binding = EngineBinding(movement, "engines.trial", (
        NodeActivation(NodeKey(Phase.RESOLVE, "trial.movement"),
                       (TypeKey("trial.move", 1),), False, False, "A"),))
    consumers = ("trial.movement", "trial.presenter")
    specs = (
        FieldSpec(FieldFamily("trial.map", "width"), "CORE", "A", "system.bootstrap",
                  consumers, "integer", "cell_count", 1, 3, 3, None),
        FieldSpec(FieldFamily("trial.map", "height"), "CORE", "A", "system.bootstrap",
                  consumers, "integer", "cell_count", 1, 3, 3, None),
        FieldSpec(FieldFamily("trial.map", "cell_mm"), "CORE", "A", "system.bootstrap",
                  ("trial.presenter",), "integer", "mm", 1, 1000, 1000, None),
        FieldSpec(FieldFamily("trial.map", "blocked_cells"), "CORE", "A", "system.bootstrap",
                  consumers, "integer_tuple", "cell", 1, 0, 8, 1),
        FieldSpec(FieldFamily("trial.position", "space_id"), "CORE", "A", "system.bootstrap",
                  consumers, "string", "entity_id", 1, None, None, None),
        FieldSpec(FieldFamily("trial.position", "cell"), "CORE", "A", "trial.movement",
                  consumers, "integer", "cell", 1, 0, 8, None),
    )
    kinds = (TypeKey("trial.move-blocked", 1), TypeKey("trial.moved", 1))
    return FeatureBundle(
        "trial.movement", (binding,),
        (AdapterBinding(TrialMapAdapter()), AdapterBinding(CellPositionAdapter())), specs,
        tuple(EventPolicy(k, "record_only", Phase.PRESENT, 0, "reject",
                          ("trial.movement",), (), ()) for k in kinds),
        (MoveAdmission(),), (CellReducer(),),
        (PresenterBinding("trial.presenter", kinds, MovePresenter()),),
        tuple(TrialPayloadCodec(TypeKey("trial." + kind, 1)) for kind in (
            "move", "move-blocked", "move-cue", "moved", "position-delta", "position-patch")),
        object_value(decode_json(SCHEMA_DOCUMENT)), object_value(decode_json(RULES_DOCUMENT)),
        (TrialMapCodec(), CellPositionCodec()), (CellPatchRoute(),), TrialCheckpointPolicy(),
    )


# Independent descriptors fixed in the accepted CORE-02 order.
SCHEMA_DOCUMENT = b'{"bool_as_integer":"reject","components":[{"fields":{"blocked_cells":{"collection_cap":1,"maximum":8,"minimum":0,"owner":"system.bootstrap","scale":1,"storage":"CORE","tier":"A","unit":"cell"},"cell_mm":{"maximum":1000,"minimum":1000,"owner":"system.bootstrap","scale":1,"storage":"CORE","tier":"A","unit":"mm"},"height":{"maximum":3,"minimum":3,"owner":"system.bootstrap","scale":1,"storage":"CORE","tier":"A","unit":"cell_count"},"width":{"maximum":3,"minimum":3,"owner":"system.bootstrap","scale":1,"storage":"CORE","tier":"A","unit":"cell_count"}},"schema":{"kind":"trial.map","version":1}},{"fields":{"cell":{"maximum":8,"minimum":0,"owner":"trial.movement","scale":1,"storage":"CORE","tier":"A","unit":"cell"},"space_id":{"owner":"system.bootstrap","scale":1,"storage":"CORE","tier":"A","unit":"entity_id"}},"schema":{"kind":"trial.position","version":1}}],"payloads":[{"fields":["dx","dz"],"schema":{"kind":"trial.move","version":1}},{"fields":["actor_id","space_id","from_cell","dx","dz","reason"],"schema":{"kind":"trial.move-blocked","version":1}},{"fields":["actor_id","space_id","from_cell","to_cell","from_x_mm","from_z_mm","to_x_mm","to_z_mm","result"],"schema":{"kind":"trial.move-cue","version":1}},{"fields":["actor_id","space_id","from_cell","to_cell"],"schema":{"kind":"trial.moved","version":1}},{"fields":["entity_id","before_cell","after_cell"],"schema":{"kind":"trial.position-delta","version":1}},{"fields":["cell"],"schema":{"kind":"trial.position-patch","version":1}}],"unknown_fields":"reject","version":1}'

RULES_DOCUMENT = b'{"actor_id":"actor:trial","blocked_attempt_consumes_time":true,"blocked_cells":[1],"boundary_precedes_occupancy":true,"cardinal_directions":[[-1,0],[0,-1],[0,1],[1,0]],"cell_mm":1000,"duration_seconds":1,"height":3,"initial_cell":0,"record_only":true,"rng_purposes":[],"space_id":"space:trial","version":1,"width":3}'
