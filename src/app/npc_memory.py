"""Opt-in persisted evidence bundle and read-only source-bound context."""

from __future__ import annotations

from dataclasses import fields, replace
from pathlib import Path

from adapters.sqlite_store import validate_save
from app.headless import HeadlessSession, state_io
from app.quest_definition import harbor_definition
from app.quest_registry import QUEST_ROLES, quest_bundle
from app.watch import WatchBootstrapSpec, _bootstrap
from contracts.dialogue import GenerationError, QuestContent
from contracts.npc_context import KnownQuestPhase, NpcQuestContext
from contracts.npc_memory import MEMORY, MEMORY_FAMILY, MemoryDelta, MemoryPatch, NpcMemoryContext
from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle
from contracts.turn import EngineBinding, NodeActivation, NodeKey
from domain.canonical import array_value, object_value, seal
from domain.npc_memory import MEMORY_CAPACITY, MEMORY_LEVEL, MEMORY_PRIORITY, NpcQuestMemoryRecord
from domain.primitives import EntityId, FieldSpec, Phase
from domain.quest import QuestRecord
from engines.npc_memory import NpcQuestMemory
from orchestration.npc_memory import (
    MemoryAdapter,
    MemoryCheckpointPolicy,
    MemoryCodec,
    MemoryPatchRoute,
    MemoryPayloadCodec,
    MemoryReducer,
)


def memory_bundle(content: QuestContent) -> FeatureBundle:
    base = quest_bundle(content)
    binding = EngineBinding(
        NpcQuestMemory(content),
        "engines.npc_memory",
        (NodeActivation(NodeKey(Phase.POST_TICK, "quest.memory"), (), True, False, "A"),),
    )
    policies = tuple(
        replace(
            policy, mode="simulate", delivery_phase=Phase.POST_TICK, subscribers=("quest.memory",)
        )
        if policy.schema.kind in ("quest.accepted", "quest.completed")
        else policy
        for policy in base.events
    )
    schema = dict(base.schema_document)
    schema["components"] = tuple(
        sorted(
            (
                *array_value(schema["components"]),
                {
                    "schema": {"kind": MEMORY.schema.kind, "version": 1},
                    "fields": {
                        "entries": {
                            "owner": "quest.memory",
                            "storage": "CORE",
                            "tier": "A",
                            "scale": 1,
                            "unit": "quest_evidence",
                            "collection_cap": MEMORY_CAPACITY,
                        },
                    },
                },
            ),
            key=lambda value: str(object_value(object_value(value)["schema"])["kind"]),
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
                    for kind in (MemoryDelta, MemoryPatch)
                ),
            ),
            key=lambda value: str(object_value(object_value(value)["schema"])["kind"]),
        )
    )
    rules = dict(base.rules_document)
    quest = dict(object_value(rules["quest"]))
    quest["consumer_roles"] = tuple(
        sorted(
            (
                *QUEST_ROLES,
                "engine:quest.memory",
                "adapter:quest.npc-memory",
                "component:quest.npc-memory",
                "reducer:quest.npc-memory-delta",
                "patch:quest.npc-memory-patch",
                "payload:quest.npc-memory-delta",
                "payload:quest.npc-memory-patch",
            )
        )
    )
    rules["quest"] = quest
    rules["npc_memory"] = {
        "version": 1,
        "owner": content.definition.layout.npc_id,
        "evidence_order": ("accepted", "completion_reported"),
        "capacity": MEMORY_CAPACITY,
        "level": MEMORY_LEVEL,
        "priority": MEMORY_PRIORITY,
        "protected": False,
        "certainty": ("observed", "reported"),
        "phase": "POST_TICK",
        "source": "quest.rules/RESOLVE/0/0",
        "policy": "append_once/no_retirement",
    }
    # Keep the canonical event-policy document shape used by RegisteredStateIO.
    rules["event_policies"] = tuple(
        {
            "schema": {"kind": policy.schema.kind, "version": policy.schema.version},
            "mode": policy.mode,
            "delivery_phase": policy.delivery_phase.name,
            "priority": policy.priority,
            "late_route": policy.late_route,
            "producers": policy.producers,
            "subscribers": policy.subscribers,
            "cancellers": policy.cancellers,
        }
        for policy in sorted(
            policies, key=lambda policy: (policy.schema.kind, policy.schema.version)
        )
    )
    return replace(
        base,
        feature_id="quest.harbor-memory-v1",
        bindings=(*base.bindings, binding),
        read_adapters=(*base.read_adapters, AdapterBinding(MemoryAdapter(content))),
        field_specs=(
            *base.field_specs,
            FieldSpec(
                MEMORY_FAMILY,
                "CORE",
                "A",
                "quest.memory",
                ("quest.memory",),
                "records",
                "quest_evidence",
                1,
                None,
                None,
                MEMORY_CAPACITY,
            ),
        ),
        events=policies,
        delta_routes=(*base.delta_routes, MemoryReducer(content)),
        patch_routes=(*base.patch_routes, MemoryPatchRoute(content)),
        component_codecs=(*base.component_codecs, MemoryCodec(content)),
        codecs=(
            *base.codecs,
            *(MemoryPayloadCodec(kind.SCHEMA, content) for kind in (MemoryDelta, MemoryPatch)),
        ),
        checkpoint_policy=MemoryCheckpointPolicy(content),
        schema_document=object_value(seal(schema)),
        rules_document=object_value(seal(rules)),
    )


def bootstrap_memory(spec: WatchBootstrapSpec, content: QuestContent) -> HeadlessSession:
    return _bootstrap(
        spec,
        None,
        content.definition.layout,
        bundle=memory_bundle(content),
        extra_records=(
            QuestRecord(EntityId(content.definition.quest_id), 0),
            NpcQuestMemoryRecord(content.definition.layout.npc_id, ()),
        ),
    )[0]


def read_memory(working: Path, content: QuestContent, npc_id: str) -> NpcMemoryContext:
    if type(content) is not QuestContent or content.definition != harbor_definition():
        raise GenerationError("NPC_CONTEXT_CONTENT")
    definition = content.definition
    if type(npc_id) is not str or npc_id != definition.layout.npc_id:
        raise GenerationError("NPC_CONTEXT_OWNER")
    io = state_io((memory_bundle(content),))
    checkpoint = validate_save(working, io=io)
    memory = next(
        record for record in checkpoint.core.components if isinstance(record, NpcQuestMemoryRecord)
    )
    quest = next(record for record in checkpoint.core.components if isinstance(record, QuestRecord))
    phase: KnownQuestPhase = (
        "available" if quest.stage == 0 else "reported" if quest.stage == 3 else "accepted"
    )
    context = NpcQuestContext(
        checkpoint.core.world_id,
        checkpoint.protocol.branch_id,
        checkpoint.protocol.revision,
        checkpoint.core.tick,
        io.hash_core(checkpoint.core),
        content.catalog_sha256,
        npc_id,
        definition.layout.actor_id,
        definition.quest_id,
        phase,
        1 if phase == "reported" else 0,
    )
    return NpcMemoryContext(context, memory.entries)
