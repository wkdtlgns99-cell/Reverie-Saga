"""Compose an explicit patrol variant on the already qualified call-aid bundle."""

from dataclasses import fields, replace

from contracts.dialogue import QuestContent
from contracts.messages import EventPolicy
from contracts.npc_memory import MEMORY_FAMILY
from contracts.npc_cycle import CYCLE_FAMILY
from domain.npc_work import SUPPORT_STOCK_MIN
from contracts.turn import ProtocolSnapshot
from domain.npc_memory import NpcQuestMemoryRecord
from domain.state_types import CoreSnapshot
from domain.watch import WatchNpcRecord
from contracts.npc_patrol import PATROL_PAYLOADS, NpcPatrolled
from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle
from contracts.turn import NodeActivation, NodeKey
from domain.canonical import array_value, object_value, seal, text_value
from domain.npc_patrol import patrol_cells
from domain.primitives import FieldFamily, Phase
from engines.watch import WatchNpc, WatchBell
from orchestration.npc_cycle import CycleCheckpointPolicy
from orchestration.quest import QuestAdmission
from orchestration.watch import (
    BellsPatchRoute,
    NpcCellPatchRoute,
    NpcCellReducer,
    WatchAdmission,
    WatchNpcAdapter,
    WatchNpcCodec,
    WatchPayloadCodec,
    WatchPresenter,
)


def with_patrol(
    base: FeatureBundle,
    content: QuestContent,
    *,
    npc_talk_pause: bool = False,
    npc_quest_patrol: bool = False,
    npc_call_pause: bool = False,
    npc_ready_patrol: bool = False,
    npc_reach_aid: bool = False,
) -> FeatureBundle:
    if type(npc_talk_pause) is not bool:
        raise ValueError("NPC_TALK_PAUSE_CONTENT")
    if type(npc_quest_patrol) is not bool or npc_quest_patrol and not npc_talk_pause:
        raise ValueError("NPC_QUEST_PATROL_CONTENT")
    if type(npc_call_pause) is not bool or npc_call_pause and not npc_quest_patrol:
        raise ValueError("NPC_CALL_PAUSE_CONTENT")
    if type(npc_ready_patrol) is not bool or npc_ready_patrol and not npc_call_pause:
        raise ValueError("NPC_READY_PATROL_CONTENT")
    if type(npc_reach_aid) is not bool or npc_reach_aid and not npc_ready_patrol:
        raise ValueError("NPC_REACH_AID_CONTENT")
    layout = content.definition.layout
    cells = patrol_cells(layout, True)
    bindings = tuple(
        replace(
            binding,
            engine=WatchNpc(
                layout,
                npc_patrol=True,
                talk_pause_quest=content.definition.quest_id if npc_talk_pause else None,
                quest_patrol=npc_quest_patrol,
                call_pause=npc_call_pause,
                ready_patrol=npc_ready_patrol,
            ),
            activations=(
                *binding.activations,
                NodeActivation(NodeKey(Phase.POST_TICK, "watch.npc"), (), True, False, "A"),
            ),
        )
        if binding.engine.manifest.engine_id == "watch.npc"
        else replace(binding, engine=WatchBell(layout, npc_patrol=True))
        if binding.engine.manifest.engine_id == "watch.bell"
        else binding
        for binding in base.bindings
    )
    policies = tuple(
        replace(policy, subscribers=(*policy.subscribers, "watch.npc"))
        if policy.schema.kind == "watch.npc-acted"
        or npc_call_pause
        and policy.schema.kind == "watch.replied"
        else policy
        for policy in base.events
    ) + (
        EventPolicy(
            NpcPatrolled.SCHEMA, "record_only", Phase.PRESENT, 0, "reject", ("watch.npc",), (), ()
        ),
    )
    if npc_talk_pause:
        policies = tuple(
            replace(
                policy, mode="simulate", delivery_phase=Phase.POST_TICK, subscribers=("watch.npc",)
            )
            if policy.schema.kind == "quest.spoken"
            else policy
            for policy in policies
        )
    specs = tuple(
        replace(spec, owner_id="watch.npc", minimum=cells[0], maximum=cells[1])
        if spec.family == FieldFamily("watch.npc", "cell")
        else replace(spec, consumers=(*spec.consumers, "watch.npc"))
        if spec.family
        in (FieldFamily("trial.position", "cell"), FieldFamily("trial.position", "space_id"))
        else spec
        for spec in base.field_specs
    )
    if npc_quest_patrol:
        specs = tuple(
            replace(spec, consumers=(*spec.consumers, "watch.npc"))
            if spec.family == MEMORY_FAMILY
            else spec
            for spec in specs
        )
    if npc_call_pause:
        specs = tuple(
            replace(spec, consumers=(*spec.consumers, "watch.npc"))
            if spec.family == FieldFamily("watch.reply", "count")
            else spec
            for spec in specs
        )
    if npc_ready_patrol:
        ready_reads = (
            CYCLE_FAMILY,
            *(FieldFamily("encounter.gate", field) for field in ("space_id", "cell", "is_open")),
        )
        specs = tuple(
            replace(spec, consumers=(*spec.consumers, "watch.npc"))
            if spec.family in ready_reads
            else spec
            for spec in specs
        )
    schema, rules = dict(base.schema_document), dict(base.rules_document)
    components = []
    for raw in array_value(schema["components"]):
        component = dict(object_value(raw))
        if object_value(component["schema"])["kind"] == "watch.npc":
            spec_fields = dict(object_value(component["fields"]))
            cell = dict(object_value(spec_fields["cell"]))
            cell.update({"owner": "watch.npc", "minimum": cells[0], "maximum": cells[1]})
            spec_fields["cell"] = cell
            component["fields"] = spec_fields
        components.append(component)
    schema["components"] = tuple(components)
    schema["payloads"] = tuple(
        sorted(
            (
                *array_value(schema["payloads"]),
                *(
                    {
                        "schema": {"kind": kind.SCHEMA.kind, "version": 1},
                        "fields": tuple(field.name for field in fields(kind)),
                    }
                    for kind in PATROL_PAYLOADS
                ),
            ),
            key=lambda raw: text_value(object_value(object_value(raw)["schema"])["kind"]),
        )
    )
    rules["npc_patrol"] = {
        "version": 1,
        "owner": layout.npc_id,
        "cells": cells,
        "phase": "POST_TICK",
        "source": "watch.npc-acted/PRE_TICK/watch.npc/0/0",
        "occupied_target": "no_op_until_next_actual_wake",
        "actor_collision": "destination_only",
        "talk_position": "current_before_POST_TICK",
        "new_pending_events": False,
    }
    if npc_talk_pause:
        rules["npc_talk_pause"] = {
            "version": 1,
            "quest_id": content.definition.quest_id,
            "npc_id": layout.npc_id,
            "source": "quest.spoken/RESOLVE/quest.rules/same_tick",
            "suppression": "actual_spoken_turn_only",
            "resume": "next_actual_wake",
            "persistent_state": False,
            "new_pending_events": False,
        }
    if npc_quest_patrol:
        rules["npc_quest_patrol"] = {
            "version": 1,
            "owner": layout.npc_id,
            "source": "own_committed_quest_memory",
            "available": "wait_at_home",
            "accepted": "patrol_two_work_cells",
            "reported": "return_home_then_wait",
            "occupied_home": "retry_next_actual_wake",
            "talk": "hold_actual_spoken_turn",
            "persistent_goal": False,
            "new_pending_events": False,
        }
    if npc_call_pause:
        rules["npc_call_pause"] = {
            "version": 1,
            "npc_id": layout.npc_id,
            "source": "watch.echo/watch.replied/CASCADE",
            "suppression": "actual_answered_turn_only",
            "resume": "next_actual_wake",
            "persistent_state": False,
            "new_pending_events": False,
        }
    if npc_ready_patrol:
        rules["npc_ready_patrol"] = {
            "version": 1,
            "owner": layout.npc_id,
            "gate_id": layout.gate_id,
            "source": "own_accepted_memory_and_prior_POST_TICK_cycle_gate",
            "stock_min": SUPPORT_STOCK_MIN,
            "closed_gate_low_stock": "home_before_patrol",
            "other": "existing_quest_patrol",
            "same_phase_supply_or_gate_update": "not_visible_until_next_barrier",
            "conversation_or_reply": "hold_actual_turn_only",
            "occupied_target": "retry_next_actual_wake",
            "persistent_goal": False,
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
        feature_id="quest.harbor-reach-aid-v1"
        if npc_reach_aid
        else "quest.harbor-ready-patrol-v1"
        if npc_ready_patrol
        else "quest.harbor-call-pause-v1"
        if npc_call_pause
        else "quest.harbor-quest-patrol-v1"
        if npc_quest_patrol
        else "quest.harbor-talk-patrol-v1"
        if npc_talk_pause
        else "quest.harbor-call-patrol-v1",
        bindings=bindings,
        events=policies,
        field_specs=specs,
        read_adapters=tuple(
            AdapterBinding(WatchNpcAdapter(layout, npc_patrol=True))
            if binding.schema.kind == "watch.npc"
            else binding
            for binding in base.read_adapters
        ),
        component_codecs=tuple(
            WatchNpcCodec(layout, npc_patrol=True) if codec.schema.kind == "watch.npc" else codec
            for codec in base.component_codecs
        ),
        command_routes=tuple(
            QuestAdmission(content, npc_patrol=True)
            if route.schema.kind == "quest.talk"
            else WatchAdmission(route.schema, layout, npc_patrol=True)
            if route.schema.kind in ("watch.wait", "watch.bell")
            else route
            for route in base.command_routes
        ),
        codecs=tuple(
            WatchPayloadCodec(codec.schema, layout, npc_patrol=True)
            if isinstance(codec, WatchPayloadCodec)
            else codec
            for codec in base.codecs
        )
        + tuple(
            WatchPayloadCodec(kind.SCHEMA, layout, npc_patrol=True) for kind in PATROL_PAYLOADS
        ),
        delta_routes=(*base.delta_routes, NpcCellReducer(layout, npc_patrol=True)),
        patch_routes=tuple(
            BellsPatchRoute(layout, npc_patrol=True)
            if route.schema.kind == "watch.bells-patch"
            else route
            for route in base.patch_routes
        )
        + (NpcCellPatchRoute(layout, npc_patrol=True),),
        presenters=tuple(
            replace(
                p,
                kinds=(*p.kinds, NpcPatrolled.SCHEMA),
                presenter=WatchPresenter(layout, npc_patrol=True),
            )
            if p.presenter_id == "watch.presenter"
            else p
            for p in base.presenters
        ),
        checkpoint_policy=_QuestPatrolCheckpointPolicy(content, npc_patrol=True)
        if npc_quest_patrol
        else CycleCheckpointPolicy(content, npc_patrol=True),
        schema_document=object_value(seal(schema)),
        rules_document=object_value(seal(rules)),
    )


class _QuestPatrolCheckpointPolicy(CycleCheckpointPolicy):
    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        super().validate(core, protocol)
        layout = self.quest_content.definition.layout
        memories = tuple(
            record
            for record in core.components
            if type(record) is NpcQuestMemoryRecord and record.entity_id == layout.npc_id
        )
        npcs = tuple(
            record
            for record in core.components
            if type(record) is WatchNpcRecord and record.entity_id == layout.npc_id
        )
        if (
            len(memories) != 1
            or len(npcs) != 1
            or (memories[0].known_phase == "available" and npcs[0].cell != layout.npc_cell)
        ):
            raise ValueError("NPC_QUEST_PATROL_CHECKPOINT")
