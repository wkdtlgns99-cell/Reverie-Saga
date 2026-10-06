from __future__ import annotations

from contracts.messages import EventPolicy
from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle, PresenterBinding
from contracts.turn import EngineBinding, NodeActivation, NodeKey
from domain.canonical import decode_json, object_value
from domain.primitives import FieldFamily, FieldSpec, Phase, TypeKey
from engines.encounter import EncounterActions, EncounterMovement
from orchestration.encounter import (
    GateAdapter, HitPointsAdapter, StaminaAdapter, GateCodec, HitPointsCodec, StaminaCodec,
    GatePatchRoute, HitPointsPatchRoute, StaminaPatchRoute, EncounterAdmission,
    EncounterCellReducer, GateReducer, HitPointsReducer, StaminaReducer,
    EncounterPayloadCodec, EncounterCheckpointPolicy, EncounterPresenter,
)
from orchestration.trial import (
    CellPatchRoute, CellPositionAdapter, CellPositionCodec, TrialMapAdapter, TrialMapCodec,
    TrialPayloadCodec,
)


def encounter_bundle() -> FeatureBundle:
    actions, movement = EncounterActions(), EncounterMovement()
    action_kinds = tuple(TypeKey("encounter." + k, 1) for k in ("attack", "interact", "rest"))
    bindings = (
        EngineBinding(actions, "engines.encounter", (NodeActivation(NodeKey(Phase.RESOLVE, "encounter.actions"), action_kinds, False, False, "A"),)),
        EngineBinding(movement, "engines.encounter", (NodeActivation(NodeKey(Phase.RESOLVE, "trial.movement"), (TypeKey("trial.move", 1),), False, False, "A"),)),
    )
    consumers = ("encounter.actions", "trial.movement", "encounter.presenter", "system.admission")
    specs = (
        FieldSpec(FieldFamily("trial.map", "width"), "CORE", "A", "system.bootstrap", ("trial.movement", "encounter.presenter"), "integer", "cell_count", 1, 3, 3, None),
        FieldSpec(FieldFamily("trial.map", "height"), "CORE", "A", "system.bootstrap", ("trial.movement", "encounter.presenter"), "integer", "cell_count", 1, 3, 3, None),
        FieldSpec(FieldFamily("trial.map", "cell_mm"), "CORE", "A", "system.bootstrap", ("encounter.presenter",), "integer", "mm", 1, 1000, 1000, None),
        FieldSpec(FieldFamily("trial.map", "blocked_cells"), "CORE", "A", "system.bootstrap", ("trial.movement", "encounter.presenter"), "integer_tuple", "cell", 1, 0, 8, 1),
        FieldSpec(FieldFamily("trial.position", "space_id"), "CORE", "A", "system.bootstrap", consumers, "string", "entity_id", 1, None, None, None),
        FieldSpec(FieldFamily("trial.position", "cell"), "CORE", "A", "trial.movement", consumers, "integer", "cell", 1, 0, 8, None),
        FieldSpec(FieldFamily("encounter.gate", "space_id"), "CORE", "A", "system.bootstrap", consumers, "string", "entity_id", 1, None, None, None),
        FieldSpec(FieldFamily("encounter.gate", "cell"), "CORE", "A", "system.bootstrap", consumers, "integer", "cell", 1, 4, 4, None),
        FieldSpec(FieldFamily("encounter.gate", "is_open"), "CORE", "A", "encounter.actions", consumers, "integer", "boolean_integer", 1, 0, 1, None),
        FieldSpec(FieldFamily("encounter.hp", "hp"), "CORE", "A", "encounter.actions", consumers, "integer", "hp", 1, 0, 5, None),
        FieldSpec(FieldFamily("encounter.stamina", "value"), "CORE", "A", "encounter.actions", ("encounter.actions", "encounter.presenter", "system.admission"), "integer", "stamina", 1, 0, 2, None),
    )
    kinds = tuple(TypeKey("encounter." + k, 1) for k in ("attack-resolved", "defeated", "gate-changed", "move-blocked", "moved", "rested"))
    return FeatureBundle(
        "encounter.local", bindings,
        (AdapterBinding(GateAdapter()), AdapterBinding(HitPointsAdapter()), AdapterBinding(StaminaAdapter()), AdapterBinding(TrialMapAdapter()), AdapterBinding(CellPositionAdapter())),
        specs,
        tuple(EventPolicy(k, "record_only", Phase.PRESENT, 0, "reject", ("trial.movement" if k.kind in ("encounter.move-blocked", "encounter.moved") else "encounter.actions",), (), ()) for k in kinds),
        tuple(EncounterAdmission(k) for k in (*action_kinds, TypeKey("trial.move", 1))),
        (EncounterCellReducer(), GateReducer(), HitPointsReducer(), StaminaReducer()),
        (PresenterBinding("encounter.presenter", kinds, EncounterPresenter()),),
        tuple(EncounterPayloadCodec(TypeKey("encounter." + k, 1)) for k in (
            "attack", "attack-cue", "attack-resolved", "defeat-cue", "defeated", "gate-changed", "gate-cue", "gate-delta", "gate-patch", "hp-delta", "hp-patch", "interact", "move-blocked", "move-cue", "moved", "rest", "rest-cue", "rested", "stamina-delta", "stamina-patch",
        )) + tuple(TrialPayloadCodec(TypeKey("trial." + k, 1)) for k in ("move", "position-delta", "position-patch")),
        object_value(decode_json(SCHEMA_DOCUMENT)), object_value(decode_json(RULES_DOCUMENT)),
        (GateCodec(), HitPointsCodec(), StaminaCodec(), TrialMapCodec(), CellPositionCodec()),
        (GatePatchRoute(), HitPointsPatchRoute(), StaminaPatchRoute(), CellPatchRoute()),
        EncounterCheckpointPolicy(),
    )


# Literal descriptors fixed independently before implementation in CORE-03.
SCHEMA_DOCUMENT = b'{"bool_as_integer":"reject","components":[{"fields":{"cell":{"maximum":4,"minimum":4,"owner":"system.bootstrap","scale":1,"storage":"CORE","tier":"A","unit":"cell"},"is_open":{"maximum":1,"minimum":0,"owner":"encounter.actions","scale":1,"storage":"CORE","tier":"A","unit":"boolean_integer"},"space_id":{"owner":"system.bootstrap","scale":1,"storage":"CORE","tier":"A","unit":"entity_id"}},"schema":{"kind":"encounter.gate","version":1}},{"fields":{"hp":{"maximum":5,"minimum":0,"owner":"encounter.actions","scale":1,"storage":"CORE","tier":"A","unit":"hp"}},"schema":{"kind":"encounter.hp","version":1}},{"fields":{"value":{"maximum":2,"minimum":0,"owner":"encounter.actions","scale":1,"storage":"CORE","tier":"A","unit":"stamina"}},"schema":{"kind":"encounter.stamina","version":1}},{"fields":{"blocked_cells":{"collection_cap":1,"maximum":8,"minimum":0,"owner":"system.bootstrap","scale":1,"storage":"CORE","tier":"A","unit":"cell"},"cell_mm":{"maximum":1000,"minimum":1000,"owner":"system.bootstrap","scale":1,"storage":"CORE","tier":"A","unit":"mm"},"height":{"maximum":3,"minimum":3,"owner":"system.bootstrap","scale":1,"storage":"CORE","tier":"A","unit":"cell_count"},"width":{"maximum":3,"minimum":3,"owner":"system.bootstrap","scale":1,"storage":"CORE","tier":"A","unit":"cell_count"}},"schema":{"kind":"trial.map","version":1}},{"fields":{"cell":{"maximum":8,"minimum":0,"owner":"trial.movement","scale":1,"storage":"CORE","tier":"A","unit":"cell"},"space_id":{"owner":"system.bootstrap","scale":1,"storage":"CORE","tier":"A","unit":"entity_id"}},"schema":{"kind":"trial.position","version":1}}],"payloads":[{"fields":["target_id","profile_id"],"schema":{"kind":"encounter.attack","version":1}},{"fields":["actor_id","target_id","actor_cell","target_cell","actor_hp_before","actor_hp_after","target_hp_before","target_hp_after","stamina_before","stamina_after","result"],"schema":{"kind":"encounter.attack-cue","version":1}},{"fields":["actor_id","target_id","profile_id","actor_hp_before","actor_hp_after","target_hp_before","target_hp_after","stamina_before","stamina_after"],"schema":{"kind":"encounter.attack-resolved","version":1}},{"fields":["entity_id","killer_id","cell","x_mm","z_mm"],"schema":{"kind":"encounter.defeat-cue","version":1}},{"fields":["entity_id","killer_id"],"schema":{"kind":"encounter.defeated","version":1}},{"fields":["actor_id","target_id","before_open","after_open"],"schema":{"kind":"encounter.gate-changed","version":1}},{"fields":["actor_id","target_id","cell","x_mm","z_mm","before_open","after_open"],"schema":{"kind":"encounter.gate-cue","version":1}},{"fields":["entity_id","before_open","after_open"],"schema":{"kind":"encounter.gate-delta","version":1}},{"fields":["is_open"],"schema":{"kind":"encounter.gate-patch","version":1}},{"fields":["entity_id","before_hp","after_hp"],"schema":{"kind":"encounter.hp-delta","version":1}},{"fields":["hp"],"schema":{"kind":"encounter.hp-patch","version":1}},{"fields":["target_id","option"],"schema":{"kind":"encounter.interact","version":1}},{"fields":["actor_id","space_id","from_cell","dx","dz","reason"],"schema":{"kind":"encounter.move-blocked","version":1}},{"fields":["actor_id","space_id","from_cell","to_cell","from_x_mm","from_z_mm","to_x_mm","to_z_mm","result"],"schema":{"kind":"encounter.move-cue","version":1}},{"fields":["actor_id","space_id","from_cell","to_cell"],"schema":{"kind":"encounter.moved","version":1}},{"fields":[],"schema":{"kind":"encounter.rest","version":1}},{"fields":["actor_id","before_stamina","after_stamina"],"schema":{"kind":"encounter.rest-cue","version":1}},{"fields":["actor_id","before_stamina","after_stamina"],"schema":{"kind":"encounter.rested","version":1}},{"fields":["entity_id","before_stamina","after_stamina"],"schema":{"kind":"encounter.stamina-delta","version":1}},{"fields":["value"],"schema":{"kind":"encounter.stamina-patch","version":1}},{"fields":["dx","dz"],"schema":{"kind":"trial.move","version":1}},{"fields":["entity_id","before_cell","after_cell"],"schema":{"kind":"trial.position-delta","version":1}},{"fields":["cell"],"schema":{"kind":"trial.position-patch","version":1}}],"unknown_fields":"reject","version":1}'

RULES_DOCUMENT = b'{"actor_hp_max":3,"actor_id":"actor:trial","attack_cost":1,"attack_damage":2,"attack_profile_id":"attack:basic","blocked_cells":[1],"cardinal_directions":[[-1,0],[0,-1],[0,1],[1,0]],"cell_mm":1000,"counter_damage":1,"counter_only_if_target_survives":true,"counter_only_on_successful_attack":true,"dead_actor_admission":"ACTOR_DEFEATED","defeated_enemy_blocks":false,"derived_life":["alive","defeated"],"derived_stamina":["ready","exhausted"],"duration_seconds":1,"enemy_cell":8,"enemy_hp_max":5,"enemy_id":"actor:sentinel","gate_cell":4,"gate_id":"object:gate","height":3,"initial_actor_hp":3,"initial_cell":0,"initial_enemy_hp":5,"initial_gate_open":0,"initial_stamina":2,"invalid_attack_range_resources_target_consumes_time":false,"move_block_priority":["boundary","wall","door","occupied"],"reach_cells":1,"record_only":true,"repeat_interact_and_full_rest_consume_time":true,"rest_recovery":1,"rng_purposes":[],"space_id":"space:trial","stamina_max":2,"version":1,"width":3}'

