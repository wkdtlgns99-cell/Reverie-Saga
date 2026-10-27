"""Explicit supply-cycle feature;existing memory/work identities remain unchanged."""

from dataclasses import fields, replace

from app.headless import HeadlessSession
from app.npc_memory import memory_bundle
from app.npc_gate_aid import with_gate_aid
from app.npc_patrol import with_patrol
from app.watch import WatchBootstrapSpec, _bootstrap
from contracts.dialogue import QuestContent
from contracts.messages import EventPolicy
from contracts.npc_cycle import CYCLE, CYCLE_FAMILY, CYCLE_PAYLOADS, CycleChanged
from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle, PresenterBinding
from contracts.turn import EngineBinding, NodeActivation, NodeKey
from domain.canonical import array_value, object_value, seal, text_value
from domain.npc_memory import NpcQuestMemoryRecord
from domain.npc_work import STOCK_CAP, WORK_PERIOD
from domain.npc_cycle import MEMORY_CAP, USE_PERIOD, CycleRecord, Supply, SupplyEvidence
from domain.primitives import EntityId, FieldSpec, Phase
from domain.quest import QuestRecord
from engines.npc_cycle import NpcSupplyCycle
from orchestration.npc_cycle import (
    CycleAdapter,
    CycleCheckpointPolicy,
    CycleCodec,
    CyclePatchRoute,
    CyclePayloadCodec,
    CycleReducer,
    CyclePresenter,
)


def cycle_bundle(
    content: QuestContent,
    *,
    npc_aid: bool = False,
    npc_supply_aid: bool = False,
    npc_call_aid: bool = False,
    npc_patrol: bool = False,
    npc_talk_pause: bool = False,
    npc_quest_patrol: bool = False,
    npc_call_pause: bool = False,
) -> FeatureBundle:
    if type(npc_aid) is not bool:
        raise ValueError("NPC_AID_CONTENT")
    if type(npc_supply_aid) is not bool or npc_supply_aid and not npc_aid:
        raise ValueError("NPC_SUPPLY_AID_CONTENT")
    if type(npc_call_aid) is not bool or npc_call_aid and not npc_supply_aid:
        raise ValueError("NPC_CALL_AID_CONTENT")
    if type(npc_patrol) is not bool or npc_patrol and not npc_call_aid:
        raise ValueError("NPC_PATROL_CONTENT")
    if type(npc_talk_pause) is not bool or npc_talk_pause and not npc_patrol:
        raise ValueError("NPC_TALK_PAUSE_CONTENT")
    if type(npc_quest_patrol) is not bool or npc_quest_patrol and not npc_talk_pause:
        raise ValueError("NPC_QUEST_PATROL_CONTENT")
    if type(npc_call_pause) is not bool or npc_call_pause and not npc_quest_patrol:
        raise ValueError("NPC_CALL_PAUSE_CONTENT")
    base = memory_bundle(content)
    binding = EngineBinding(
        NpcSupplyCycle(content),
        "engines.npc_cycle",
        (NodeActivation(NodeKey(Phase.POST_TICK, "quest.cycle"), (), True, False, "A"),),
    )
    policies = tuple(
        replace(p, mode="simulate", delivery_phase=Phase.POST_TICK, subscribers=("quest.cycle",))
        if p.schema.kind == "watch.npc-acted"
        else p
        for p in base.events
    ) + (
        EventPolicy(
            CycleChanged.SCHEMA,
            "record_only",
            Phase.PRESENT,
            0,
            "reject",
            ("quest.cycle",),
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
                    "schema": {"kind": CYCLE.schema.kind, "version": 1},
                    "fields": {
                        "cycle": {
                            "collection_cap": MEMORY_CAP,
                            "owner": "quest.cycle",
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
                    for kind in CYCLE_PAYLOADS
                ),
            ),
            key=lambda raw: text_value(object_value(object_value(raw)["schema"])["kind"]),
        )
    )
    quest = dict(object_value(rules["quest"]))
    roles = (
        "engine:quest.cycle",
        "adapter:quest.cycle",
        "component:quest.cycle",
        "reducer:quest.cycle-delta",
        "patch:quest.cycle-patch",
        "presenter:quest.cycle-presenter",
        *("payload:" + kind.SCHEMA.kind for kind in CYCLE_PAYLOADS),
    )
    quest["consumer_roles"] = tuple(
        sorted((*(text_value(role) for role in array_value(quest["consumer_roles"])), *roles))
    )
    rules["quest"] = quest
    rules["npc_cycle"] = {
        "version": 1,
        "owner": content.definition.layout.npc_id,
        "period_seconds": WORK_PERIOD,
        "use_period_seconds": USE_PERIOD,
        "tie_policy": "consume_then_prepare",
        "memory_capacity": MEMORY_CAP,
        "memory_source": "actual_wake_causal_anchor",
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
    bundle = replace(
        base,
        feature_id="quest.harbor-cycle-v1",
        bindings=(*base.bindings, binding),
        read_adapters=(*base.read_adapters, AdapterBinding(CycleAdapter(content))),
        field_specs=(
            *base.field_specs,
            FieldSpec(
                CYCLE_FAMILY,
                "CORE",
                "A",
                "quest.cycle",
                ("quest.cycle", "quest.cycle-presenter"),
                "records",
                "communal_supply",
                1,
                None,
                None,
                MEMORY_CAP,
            ),
        ),
        events=policies,
        delta_routes=(*base.delta_routes, CycleReducer(content)),
        patch_routes=(*base.patch_routes, CyclePatchRoute(content)),
        component_codecs=(*base.component_codecs, CycleCodec(content)),
        codecs=(*base.codecs, *(CyclePayloadCodec(k.SCHEMA, content) for k in CYCLE_PAYLOADS)),
        presenters=(
            *base.presenters,
            PresenterBinding(
                "quest.cycle-presenter", (CycleChanged.SCHEMA,), CyclePresenter(content)
            ),
        ),
        checkpoint_policy=CycleCheckpointPolicy(content),
        schema_document=object_value(seal(schema)),
        rules_document=object_value(seal(rules)),
    )
    bundle = (
        with_gate_aid(bundle, content, npc_supply_aid=npc_supply_aid, npc_call_aid=npc_call_aid)
        if npc_aid
        else bundle
    )
    return (
        with_patrol(
            bundle,
            content,
            npc_talk_pause=npc_talk_pause,
            npc_quest_patrol=npc_quest_patrol,
            npc_call_pause=npc_call_pause,
        )
        if npc_patrol
        else bundle
    )


def bootstrap_cycle(
    spec: WatchBootstrapSpec,
    content: QuestContent,
    *,
    npc_aid: bool = False,
    npc_supply_aid: bool = False,
    npc_call_aid: bool = False,
    npc_patrol: bool = False,
    npc_talk_pause: bool = False,
    npc_quest_patrol: bool = False,
    npc_call_pause: bool = False,
) -> HeadlessSession:
    return _bootstrap(
        spec,
        None,
        content.definition.layout,
        bundle=cycle_bundle(
            content,
            npc_aid=npc_aid,
            npc_supply_aid=npc_supply_aid,
            npc_call_aid=npc_call_aid,
            npc_patrol=npc_patrol,
            npc_talk_pause=npc_talk_pause,
            npc_quest_patrol=npc_quest_patrol,
            npc_call_pause=npc_call_pause,
        ),
        extra_records=(
            QuestRecord(EntityId(content.definition.quest_id), 0),
            NpcQuestMemoryRecord(content.definition.layout.npc_id, ()),
            CycleRecord(content.definition.layout.npc_id, Supply(0, 0, 0), ()),
        ),
    )[0]


def evidence_text(entry: SupplyEvidence, *, saved: bool = False) -> str:
    source = "저장된 NPC 작업 기억" if saved else "NPC 작업 기억"
    action = "공동 물자 1개를 준비했습니다" if entry.prepared else "공동 물자 1개를 사용했습니다"
    return f"{source} · {entry.tick}초: {action} · 물자 {entry.after.stock}/{STOCK_CAP}개."


def cycle_messages(record: CycleRecord, *, saved: bool = False) -> tuple[str, ...]:
    source = "저장된 NPC 반복 작업" if saved else "NPC 반복 작업"
    total = record.state.produced + record.state.consumed
    return (
        f"{source}: 물자 {record.state.stock}/{STOCK_CAP}개 · 준비 {record.state.produced}회 · 사용 {record.state.consumed}회.",
        f"{source} 기억: 전체 {total}개 중 최근 {len(record.entries)}개를 보관합니다.",
        *(evidence_text(e, saved=saved) for e in record.entries),
    )
