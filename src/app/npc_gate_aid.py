"""Compose passage assistance without altering any prior feature identity."""

from dataclasses import fields, replace

from contracts.dialogue import QuestContent
from contracts.messages import EventPolicy
from contracts.npc_gate_aid import GateAidCue, GateAssisted
from contracts.npc_memory import MEMORY_FAMILY
from contracts.npc_cycle import CYCLE_FAMILY
from contracts.skeleton import FeatureBundle
from contracts.turn import NodeActivation, NodeKey
from contracts.watch import REPLY
from domain.canonical import array_value, object_value, seal, text_value
from domain.primitives import FieldFamily, Phase
from domain.watch import WAKE_PERIOD
from domain.npc_work import SUPPORT_STOCK_MIN
from engines.encounter import EncounterActions
from orchestration.encounter import EncounterPresenter
from orchestration.npc_gate_aid import GateAidPayloadCodec


def with_gate_aid(
    base: FeatureBundle,
    content: QuestContent,
    *,
    npc_supply_aid: bool = False,
    npc_call_aid: bool = False,
    npc_reach_aid: bool = False,
) -> FeatureBundle:
    bindings = tuple(
        replace(
            binding,
            engine=EncounterActions(
                content.definition.layout,
                npc_aid=True,
                npc_supply_aid=npc_supply_aid,
                npc_call_aid=npc_call_aid,
                npc_reach_aid=npc_reach_aid,
            ),
            activations=(
                *binding.activations,
                NodeActivation(NodeKey(Phase.POST_TICK, "encounter.actions"), (), True, False, "A"),
            ),
        )
        if binding.engine.manifest.engine_id == "encounter.actions"
        else binding
        for binding in base.bindings
    )
    policies = tuple(
        replace(policy, subscribers=(*policy.subscribers, "encounter.actions"))
        if policy.schema.kind == "watch.npc-acted"
        else replace(
            policy,
            mode="simulate",
            delivery_phase=Phase.POST_TICK,
            subscribers=("encounter.actions",),
        )
        if npc_call_aid and policy.schema.kind == "watch.replied"
        else policy
        for policy in base.events
    )
    policies += (
        EventPolicy(
            GateAssisted.SCHEMA,
            "record_only",
            Phase.PRESENT,
            0,
            "reject",
            ("encounter.actions",),
            (),
            (),
        ),
    )
    specs = tuple(
        replace(spec, consumers=(*spec.consumers, "encounter.actions"))
        if (
            spec.family == MEMORY_FAMILY
            or npc_supply_aid
            and spec.family == CYCLE_FAMILY
            or npc_call_aid
            and spec.family == FieldFamily(REPLY.schema.kind, "count")
            or npc_reach_aid
            and spec.family
            in (FieldFamily("watch.npc", "cell"), FieldFamily("watch.npc", "space_id"))
        )
        else spec
        for spec in base.field_specs
    )
    schema, rules = dict(base.schema_document), dict(base.rules_document)
    schema["payloads"] = tuple(
        sorted(
            (
                *array_value(schema["payloads"]),
                *(
                    {
                        "schema": {"kind": kind.SCHEMA.kind, "version": 1},
                        "fields": tuple(field.name for field in fields(kind)),
                    }
                    for kind in (GateAssisted, GateAidCue)
                ),
            ),
            key=lambda raw: text_value(object_value(object_value(raw)["schema"])["kind"]),
        )
    )
    quest = dict(object_value(rules["quest"]))
    quest["consumer_roles"] = tuple(
        sorted(
            (
                *(text_value(role) for role in array_value(quest["consumer_roles"])),
                *("payload:" + kind.SCHEMA.kind for kind in (GateAssisted, GateAidCue)),
            )
        )
    )
    rules["quest"] = quest
    rules["npc_gate_aid"] = {
        "version": 1,
        "owner": content.definition.layout.npc_id,
        "target": content.definition.layout.gate_id,
        "wake_period_seconds": WAKE_PERIOD,
        "condition": "prior_barrier_direct_acceptance_without_report",
        "operation": "closed_to_open",
        "writer": "encounter.actions",
        "phase": "POST_TICK",
        "new_pending_events": False,
    }
    if npc_supply_aid:
        rules["npc_gate_aid"] = {
            **object_value(rules["npc_gate_aid"]),
            "supply_stock_min": SUPPORT_STOCK_MIN,
            "supply_source": "quest.cycle.cycle/prior_POST_TICK_barrier",
            "supply_consumed": False,
        }
    if npc_call_aid:
        rules["npc_gate_aid"] = {
            **object_value(rules["npc_gate_aid"]),
            "answered_call": "watch.echo/watch.replied/CASCADE",
            "source_priority": ("answered_call", "routine_wake"),
            "max_aid_per_tick": 1,
        }
    if npc_reach_aid:
        rules["npc_gate_reach"] = {
            "version": 1,
            "owner": content.definition.layout.npc_id,
            "target": content.definition.layout.gate_id,
            "pose_source": "watch.npc.cell/space_id/prior_POST_TICK_barrier",
            "range": "domain.encounter.adjacent_cells",
            "same_phase_arrival": "not_visible_until_next_barrier",
            "supply_source": "exact_Supply/state_at(tick-1)",
            "new_pending_events": False,
        }
    rules["event_policies"] = tuple(
        {
            "schema": {"kind": p.schema.kind, "version": p.schema.version},
            "mode": p.mode,
            "delivery_phase": p.delivery_phase.name,
            "priority": p.priority,
            "late_route": p.late_route,
            "producers": tuple(sorted(p.producers)),
            "subscribers": tuple(sorted(p.subscribers)),
            "cancellers": p.cancellers,
        }
        for p in sorted(policies, key=lambda p: (p.schema.kind, p.schema.version))
    )
    return replace(
        base,
        feature_id="quest.harbor-call-aid-v1"
        if npc_call_aid
        else "quest.harbor-cycle-supply-aid-v1"
        if npc_supply_aid
        else "quest.harbor-cycle-aid-v1",
        bindings=bindings,
        field_specs=specs,
        events=policies,
        codecs=(
            *base.codecs,
            *(
                GateAidPayloadCodec(kind.SCHEMA, content, npc_call_aid=npc_call_aid)
                for kind in (GateAssisted, GateAidCue)
            ),
        ),
        presenters=tuple(
            replace(
                p,
                kinds=(*p.kinds, GateAssisted.SCHEMA),
                presenter=EncounterPresenter(
                    content.definition.layout, aid_content=content, npc_call_aid=npc_call_aid
                ),
            )
            if p.presenter_id == "encounter.presenter"
            else p
            for p in base.presenters
        ),
        schema_document=object_value(seal(schema)),
        rules_document=object_value(seal(rules)),
    )
