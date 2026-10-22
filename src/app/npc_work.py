"""Explicitly selected work feature;existing memory descriptors remain unchanged."""

from dataclasses import fields, replace

from app.headless import HeadlessSession
from app.npc_memory import memory_bundle
from app.watch import WatchBootstrapSpec, _bootstrap
from contracts.dialogue import QuestContent
from contracts.messages import EventPolicy
from contracts.npc_work import PROVISIONS, STOCK_FAMILY, WORK_PAYLOADS, ProvisionPrepared
from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle, PresenterBinding
from contracts.turn import EngineBinding, NodeActivation, NodeKey
from domain.canonical import array_value, object_value, seal, text_value
from domain.npc_memory import NpcQuestMemoryRecord
from domain.npc_work import STOCK_CAP, WORK_PERIOD, ProvisionsRecord
from domain.primitives import EntityId, FieldSpec, Phase
from domain.quest import QuestRecord
from engines.npc_work import NpcProvisioner
from orchestration.npc_work import (
    ProvisionsAdapter,
    ProvisionsCheckpointPolicy,
    ProvisionsCodec,
    ProvisionsPatchRoute,
    ProvisionsPayloadCodec,
    ProvisionsPresenter,
    ProvisionsReducer,
)


def work_bundle(content: QuestContent) -> FeatureBundle:
    base = memory_bundle(content)
    binding = EngineBinding(
        NpcProvisioner(content),
        "engines.npc_work",
        (NodeActivation(NodeKey(Phase.POST_TICK, "quest.provisioner"), (), True, False, "A"),),
    )
    policies = tuple(
        replace(
            p, mode="simulate", delivery_phase=Phase.POST_TICK, subscribers=("quest.provisioner",)
        )
        if p.schema.kind == "watch.npc-acted"
        else p
        for p in base.events
    ) + (
        EventPolicy(
            ProvisionPrepared.SCHEMA,
            "record_only",
            Phase.PRESENT,
            0,
            "reject",
            ("quest.provisioner",),
            (),
            (),
        ),
    )
    schema, rules = dict(base.schema_document), dict(base.rules_document)
    schema["components"] = tuple(
        sorted(
            (
                *array_value(schema["components"]),
                {
                    "schema": {"kind": PROVISIONS.schema.kind, "version": 1},
                    "fields": {
                        "stock": {
                            "minimum": 0,
                            "maximum": STOCK_CAP,
                            "owner": "quest.provisioner",
                            "storage": "CORE",
                            "tier": "A",
                            "unit": "communal_supply",
                            "scale": 1,
                        }
                    },
                },
            ),
            key=lambda raw: text_value(object_value(object_value(raw)["schema"])["kind"]),
        )
    )
    schema["payloads"] = tuple(
        sorted(
            (
                *array_value(schema["payloads"]),
                *(
                    {
                        "schema": {"kind": kind.SCHEMA.kind, "version": 1},
                        "fields": tuple(field.name for field in fields(kind)),
                    }
                    for kind in WORK_PAYLOADS
                ),
            ),
            key=lambda raw: text_value(object_value(object_value(raw)["schema"])["kind"]),
        )
    )
    quest = dict(object_value(rules["quest"]))
    roles = (
        "engine:quest.provisioner",
        "adapter:quest.provisions",
        "component:quest.provisions",
        "reducer:quest.provisions-delta",
        "patch:quest.provisions-patch",
        "presenter:quest.provisions-presenter",
        *("payload:" + kind.SCHEMA.kind for kind in WORK_PAYLOADS),
    )
    quest["consumer_roles"] = tuple(
        sorted((*(text_value(role) for role in array_value(quest["consumer_roles"])), *roles))
    )
    rules["quest"] = quest
    rules["npc_work"] = {
        "version": 1,
        "owner": content.definition.layout.npc_id,
        "period_seconds": WORK_PERIOD,
        "stock_cap": STOCK_CAP,
        "initial_stock": 0,
        "phase": "POST_TICK",
        "source": "watch.npc-acted/PRE_TICK/watch.npc/0/0",
        "full_policy": "no_op",
        "player_reward": False,
    }
    rules["event_policies"] = tuple(
        {
            "schema": {"kind": p.schema.kind, "version": p.schema.version},
            "mode": p.mode,
            "delivery_phase": p.delivery_phase.name,
            "priority": p.priority,
            "late_route": p.late_route,
            "producers": p.producers,
            "subscribers": p.subscribers,
            "cancellers": p.cancellers,
        }
        for p in sorted(policies, key=lambda p: (p.schema.kind, p.schema.version))
    )
    return replace(
        base,
        feature_id="quest.harbor-work-v1",
        bindings=(*base.bindings, binding),
        read_adapters=(*base.read_adapters, AdapterBinding(ProvisionsAdapter(content))),
        field_specs=(
            *base.field_specs,
            FieldSpec(
                STOCK_FAMILY,
                "CORE",
                "A",
                "quest.provisioner",
                ("quest.provisioner", "quest.provisions-presenter"),
                "integer",
                "communal_supply",
                1,
                0,
                STOCK_CAP,
                None,
            ),
        ),
        events=policies,
        delta_routes=(*base.delta_routes, ProvisionsReducer(content)),
        patch_routes=(*base.patch_routes, ProvisionsPatchRoute(content)),
        component_codecs=(*base.component_codecs, ProvisionsCodec(content)),
        codecs=(*base.codecs, *(ProvisionsPayloadCodec(k.SCHEMA, content) for k in WORK_PAYLOADS)),
        presenters=(
            *base.presenters,
            PresenterBinding(
                "quest.provisions-presenter",
                (ProvisionPrepared.SCHEMA,),
                ProvisionsPresenter(content),
            ),
        ),
        checkpoint_policy=ProvisionsCheckpointPolicy(content),
        schema_document=object_value(seal(schema)),
        rules_document=object_value(seal(rules)),
    )


def bootstrap_work(spec: WatchBootstrapSpec, content: QuestContent) -> HeadlessSession:
    return _bootstrap(
        spec,
        None,
        content.definition.layout,
        bundle=work_bundle(content),
        extra_records=(
            QuestRecord(EntityId(content.definition.quest_id), 0),
            NpcQuestMemoryRecord(content.definition.layout.npc_id, ()),
            ProvisionsRecord(content.definition.layout.npc_id, 0),
        ),
    )[0]


def stock_text(stock: int, *, saved: bool = False) -> str:
    label = "저장된 NPC 공동 비축" if saved else "NPC 공동 비축"
    state = (
        "가득 차 작업을 멈췄습니다"
        if stock == STOCK_CAP
        else f"{WORK_PERIOD}초마다 물자 1개를 준비합니다"
    )
    return f"{label}: 물자 {stock}/{STOCK_CAP}개 · {state}."
