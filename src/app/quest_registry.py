"""One merged feature;legacy/watch descriptors are never mutated."""

from __future__ import annotations

from domain.scenario import scenario_document

from dataclasses import asdict, fields, replace

from app.quest_definition import harbor_definition
from app.watch_registry import watch_bundle
from contracts.dialogue import QuestContent
from contracts.messages import EventPolicy
from contracts.quest import QUEST, QUEST_PAYLOADS, STAGE_FAMILY, QuestTalkCommand
from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle, PresenterBinding
from contracts.turn import EngineBinding, NodeActivation, NodeKey
from domain.canonical import array_value, object_value, seal
from domain.primitives import FieldSpec, Phase
from engines.quest import QuestRules
from orchestration.quest import (
    QuestAdapter,
    QuestAdmission,
    QuestCheckpointPolicy,
    QuestCodec,
    QuestPatchRoute,
    QuestPayloadCodec,
    QuestPresenter,
    QuestReducer,
)

QUEST_ROLES = tuple(
    sorted(
        (
            "engine:quest.rules",
            "adapter:quest.progress",
            "admission:quest.talk",
            "reducer:quest.stage-delta",
            "patch:quest.stage-patch",
            "component:quest.progress",
            "presenter:quest.presenter",
            "checkpoint:quest.progress",
            *("payload:" + kind.SCHEMA.kind for kind in QUEST_PAYLOADS),
        )
    )
)


def quest_bundle(content: QuestContent) -> FeatureBundle:
    if type(content) is not QuestContent or content.definition != harbor_definition():
        raise ValueError("QUEST_DEFINITION")
    base = watch_bundle(content.definition.layout)
    engine = QuestRules(content)
    binding = EngineBinding(
        engine,
        "engines.quest",
        (
            NodeActivation(
                NodeKey(Phase.RESOLVE, "quest.rules"), (QuestTalkCommand.SCHEMA,), False, False, "A"
            ),
            NodeActivation(NodeKey(Phase.POST_TICK, "quest.rules"), (), False, True, "A"),
        ),
    )
    specs = tuple(
        replace(
            spec, consumers=tuple(sorted(set((*spec.consumers, "quest.rules", "system.admission"))))
        )
        if spec.family.component in ("encounter.hp", "trial.position", "watch.npc")
        else spec
        for spec in base.field_specs
    )
    specs += (
        FieldSpec(
            STAGE_FAMILY,
            "CORE",
            "A",
            "quest.rules",
            ("quest.rules", "quest.presenter"),
            "integer",
            "quest_stage",
            1,
            0,
            3,
            None,
        ),
    )
    fact_kinds = tuple(
        kind.SCHEMA
        for kind in QUEST_PAYLOADS
        if kind.SCHEMA.kind
        in ("quest.accepted", "quest.goal-met", "quest.completed", "quest.spoken")
    )
    policies = tuple(
        EventPolicy(key, "record_only", Phase.PRESENT, 0, "reject", ("quest.rules",), (), ())
        for key in fact_kinds
    )
    schema = dict(base.schema_document)
    schema["components"] = tuple(
        sorted(
            (
                *array_value(schema["components"]),
                object_value(
                    seal(
                        {
                            "schema": {"kind": QUEST.schema.kind, "version": 1},
                            "fields": {
                                "stage": {
                                    "minimum": 0,
                                    "maximum": 3,
                                    "owner": "quest.rules",
                                    "storage": "CORE",
                                    "tier": "A",
                                    "unit": "quest_stage",
                                    "scale": 1,
                                }
                            },
                        }
                    )
                ),
            ),
            key=lambda row: str(object_value(object_value(row)["schema"])["kind"]),
        )
    )
    schema["payloads"] = tuple(
        sorted(
            (
                *array_value(schema["payloads"]),
                *tuple(
                    {
                        "schema": {"kind": kind.SCHEMA.kind, "version": 1},
                        "fields": tuple(field.name for field in fields(kind)),
                    }
                    for kind in QUEST_PAYLOADS
                ),
            ),
            key=lambda row: str(object_value(object_value(row)["schema"])["kind"]),
        )
    )
    rules = dict(base.rules_document)
    rules["quest"] = object_value(
        seal(
            {
                "definition": {
                    **asdict(content.definition),
                    "layout": scenario_document(content.definition.layout),
                },
                "consumer_roles": QUEST_ROLES,
                "talk_duration_seconds": 1,
                "talk_reach_cells": 1,
                "stage_names": ("not_accepted", "active", "report_available", "completed"),
                "goal_observation_phase": "POST_TICK",
                "reward_stage": 3,
                "version": 1,
            }
        )
    )
    rules["dialogue"] = content.document()
    rules["event_policies"] = tuple(
        sorted(
            (
                *array_value(rules["event_policies"]),
                *tuple(
                    object_value(
                        seal(
                            {
                                "schema": {"kind": policy.schema.kind, "version": 1},
                                "mode": "record_only",
                                "delivery_phase": "PRESENT",
                                "priority": 0,
                                "late_route": "reject",
                                "producers": ("quest.rules",),
                                "subscribers": (),
                                "cancellers": (),
                            }
                        )
                    )
                    for policy in policies
                ),
            ),
            key=lambda row: str(object_value(object_value(row)["schema"])["kind"]),
        )
    )
    return replace(
        base,
        feature_id="quest.harbor-v1",
        bindings=(*base.bindings, binding),
        read_adapters=(*base.read_adapters, AdapterBinding(QuestAdapter(content))),
        field_specs=specs,
        events=(*base.events, *policies),
        command_routes=(*base.command_routes, QuestAdmission(content)),
        delta_routes=(*base.delta_routes, QuestReducer(content)),
        patch_routes=(*base.patch_routes, QuestPatchRoute(content)),
        component_codecs=(*base.component_codecs, QuestCodec(content)),
        codecs=(
            *base.codecs,
            *tuple(QuestPayloadCodec(kind.SCHEMA, content) for kind in QUEST_PAYLOADS),
        ),
        presenters=(
            *base.presenters,
            PresenterBinding("quest.presenter", fact_kinds, QuestPresenter(content)),
        ),
        checkpoint_policy=QuestCheckpointPolicy(content),
        schema_document=object_value(seal(schema)),
        rules_document=object_value(seal(rules)),
    )
