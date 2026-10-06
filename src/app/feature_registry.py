from __future__ import annotations

from contracts.messages import EventPolicy
from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle, PresenterBinding, StepCommand, Stepped
from contracts.turn import EngineBinding, NodeActivation, NodeKey
from domain.canonical import decode_json, object_value
from domain.primitives import EntityId, FieldFamily, FieldSpec, MAX_INT, MIN_INT, Phase, TypeKey
from engines.skeleton import Counter, Stepper
from orchestration.skeleton import (
    CounterAdapter, CounterReducer, PositionAdapter, PositionReducer, StepAdmission, StepPresenter, ToyCodec,
    CounterCodec, CounterPatchRoute, PositionCodec, PositionPatchRoute, SkeletonCheckpointPolicy,
)


def rng_purposes() -> tuple[tuple[str, tuple[str, ...]], ...]:
    return (("skeleton.stepper", ("toy.sample", "test.reject")),)


def skeleton_bundle(actor_id: EntityId) -> FeatureBundle:
    if actor_id != "actor:toy":
        raise ValueError("toy actor must be actor:toy")
    stepper, counter = Stepper(), Counter(actor_id)
    bindings = (
        EngineBinding(stepper, "engines.skeleton", (
            NodeActivation(NodeKey(Phase.RESOLVE, stepper.manifest.engine_id),
                           (StepCommand(0).schema,), False, False, "A"),)),
        EngineBinding(counter, "engines.skeleton", (
            NodeActivation(NodeKey(Phase.POST_TICK, counter.manifest.engine_id), (), False, True, "A"),)),
    )
    specs = (
        FieldSpec(FieldFamily("skeleton.counter", "visits"), "CORE", "A", "skeleton.counter",
                  ("skeleton.counter",), "integer", "count", 1, 0, MAX_INT, None),
        FieldSpec(FieldFamily("skeleton.position", "x"), "CORE", "A", "skeleton.stepper",
                  ("skeleton.stepper", "skeleton.presenter"), "integer", "step", 1, MIN_INT, MAX_INT, None),
    )
    # Literal descriptors were independently authored before runtime implementation.
    schema = object_value(decode_json(SCHEMA_DOCUMENT))
    rules = object_value(decode_json(RULES_DOCUMENT))
    return FeatureBundle("skeleton", bindings, (AdapterBinding(PositionAdapter()), AdapterBinding(CounterAdapter())),
                         specs, (EventPolicy(Stepped(0, 0).schema, "record_only", Phase.PRESENT, 0,
                                             "reject", ("skeleton.stepper",), (), ()),),
                         (StepAdmission(actor_id),), (PositionReducer(), CounterReducer()),
                         (PresenterBinding("skeleton.presenter", (Stepped(0, 0).schema,), StepPresenter()),),
                         tuple(ToyCodec(TypeKey("skeleton." + kind, 1)) for kind in (
                             "step", "stepped", "position-delta", "counter-delta", "step-cue",
                             "position-patch", "counter-patch")), schema, rules,
                         (PositionCodec(), CounterCodec()), (PositionPatchRoute(), CounterPatchRoute()),
                         SkeletonCheckpointPolicy())


def feature_bundles(actor_id: EntityId) -> tuple[FeatureBundle, ...]:
    return (skeleton_bundle(actor_id),)

SCHEMA_DOCUMENT = b'{"bool_as_integer":"reject","components":[{"fields":{"visits":{"maximum":9223372036854775807,"minimum":0,"owner":"skeleton.counter","scale":1,"storage":"CORE","tier":"A","unit":"count"}},"schema":{"kind":"skeleton.counter","version":1}},{"fields":{"x":{"maximum":9223372036854775807,"minimum":-9223372036854775808,"owner":"skeleton.stepper","scale":1,"storage":"CORE","tier":"A","unit":"step"}},"schema":{"kind":"skeleton.position","version":1}}],"integer_bounds":{"signed":[-9223372036854775808,9223372036854775807],"tick_revision":[0,9223372036854775807]},"integer_encoding":"internal-json-int","payloads":[{"fields":{"dx":{"enum":[-1,0,1]}},"schema":{"kind":"skeleton.step","version":1}},{"fields":["from_x","to_x"],"schema":{"kind":"skeleton.stepped","version":1}},{"fields":["entity_id","expected_old","new"],"schema":{"kind":"skeleton.counter-delta","version":1}},{"fields":["entity_id","expected_old","new"],"schema":{"kind":"skeleton.position-delta","version":1}},{"fields":["actor_id","from_x","to_x"],"schema":{"kind":"skeleton.step-cue","version":1}},{"fields":["x"],"schema":{"kind":"skeleton.position-patch","version":1}},{"fields":["visits"],"schema":{"kind":"skeleton.counter-patch","version":1}}],"unknown_fields":"reject","version":1}'

RULES_DOCUMENT = b'{"actor_id":"actor:toy","counter_per_tick":1,"duration_seconds":1,"record_only":true,"rng_purposes":[{"engine_id":"skeleton.stepper","purposes":["toy.sample","test.reject"]}],"step_allowed":[-1,0,1],"stepped_even_zero":true,"version":1}'
