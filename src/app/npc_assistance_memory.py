"""Compose and present the explicitly selected persistent assistance-memory mode."""

from dataclasses import fields, replace
from typing import TypedDict, cast

from contracts.dialogue import QuestContent
from contracts.npc_assistance_memory import (
    ASSISTANCE_FAMILY,
    ASSISTANCE_MEMORY,
    ASSISTANCE_OWNER,
    ASSISTANCE_PAYLOADS,
)
from contracts.persistence import SaveError
from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle
from domain.canonical import array_value, object_value, seal, text_value
from domain.npc_assistance_memory import ASSISTANCE_CAPACITY, AssistanceMemoryRecord
from domain.primitives import FieldSpec
from domain.state_types import CoreSnapshot
from engines.encounter import EncounterActions
from orchestration.npc_assistance_memory import (
    AssistanceAdapter,
    AssistanceCheckpointPolicy,
    AssistanceCodec,
    AssistancePatchRoute,
    AssistancePayloadCodec,
    AssistanceReducer,
)


class AssistanceOptions(TypedDict, total=False):
    npc_assistance_memory: bool


def assistance_options(value: bool) -> AssistanceOptions:
    """Preserve established optional caller signatures when the child is absent."""
    return {} if value is False else {"npc_assistance_memory": value}


def with_assistance_memory(base: FeatureBundle, content: QuestContent) -> FeatureBundle:
    owners = tuple(b for b in base.bindings if b.engine.manifest.engine_id == ASSISTANCE_OWNER)
    if (
        base.feature_id != "quest.harbor-reach-aid-v1"
        or len(owners) != 1
        or type(owners[0].engine) is not EncounterActions
        or not owners[0].engine.npc_reach_aid
    ):
        raise ValueError("NPC_ASSISTANCE_MEMORY_CONTENT")
    schema, rules = dict(base.schema_document), dict(base.rules_document)
    schema["components"] = tuple(
        sorted(
            (
                *array_value(schema["components"]),
                {
                    "schema": {"kind": ASSISTANCE_MEMORY.schema.kind, "version": 1},
                    "fields": {
                        "memory": {
                            "owner": ASSISTANCE_OWNER,
                            "storage": "CORE",
                            "tier": "A",
                            "scale": 1,
                            "unit": "own_assistance_records",
                            "collection_cap": ASSISTANCE_CAPACITY,
                        }
                    },
                },
            ),
            key=lambda row: text_value(object_value(object_value(row)["schema"])["kind"]),
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
                    for kind in ASSISTANCE_PAYLOADS
                ),
            ),
            key=lambda row: text_value(object_value(object_value(row)["schema"])["kind"]),
        )
    )
    quest = dict(object_value(rules["quest"]))
    roles = (
        "adapter:" + ASSISTANCE_MEMORY.schema.kind,
        "component:" + ASSISTANCE_MEMORY.schema.kind,
        "reducer:" + ASSISTANCE_PAYLOADS[0].SCHEMA.kind,
        "patch:" + ASSISTANCE_PAYLOADS[1].SCHEMA.kind,
        *("payload:" + kind.SCHEMA.kind for kind in ASSISTANCE_PAYLOADS),
    )
    quest["consumer_roles"] = tuple(
        sorted(
            (
                *(text_value(role) for role in array_value(quest["consumer_roles"])),
                *roles,
            )
        )
    )
    rules["quest"] = quest
    rules["npc_assistance_memory"] = {
        "version": 1,
        "owner": content.definition.layout.npc_id,
        "target": content.definition.layout.gate_id,
        "writer": ASSISTANCE_OWNER,
        "phase": "POST_TICK",
        "capacity": ASSISTANCE_CAPACITY,
        "initial_total": 0,
        "count": "cumulative_own_successful_gate_assistance",
        "source": "selected_validated_incoming_cause",
        "retention": "latest_four_chronological",
        "same_commit_as_gate": True,
        "old_save_migration": False,
    }
    return replace(
        base,
        feature_id="quest.harbor-assistance-memory-v1",
        bindings=tuple(
            replace(
                binding,
                engine=replace(cast(EncounterActions, binding.engine), npc_assistance_memory=True),
            )
            if binding is owners[0]
            else binding
            for binding in base.bindings
        ),
        read_adapters=(*base.read_adapters, AdapterBinding(AssistanceAdapter(content))),
        field_specs=(
            *base.field_specs,
            FieldSpec(
                ASSISTANCE_FAMILY,
                "CORE",
                "A",
                ASSISTANCE_OWNER,
                (ASSISTANCE_OWNER,),
                "records",
                "own_assistance_records",
                1,
                None,
                None,
                ASSISTANCE_CAPACITY,
            ),
        ),
        component_codecs=(*base.component_codecs, AssistanceCodec(content)),
        codecs=(
            *base.codecs,
            *(AssistancePayloadCodec(kind.SCHEMA, content) for kind in ASSISTANCE_PAYLOADS),
        ),
        delta_routes=(*base.delta_routes, AssistanceReducer(content)),
        patch_routes=(*base.patch_routes, AssistancePatchRoute(content)),
        checkpoint_policy=AssistanceCheckpointPolicy(content, base.checkpoint_policy),
        schema_document=object_value(seal(schema)),
        rules_document=object_value(seal(rules)),
    )


def assistance_messages(
    core: CoreSnapshot,
    content: QuestContent,
    *,
    label: str = "NPC",
    error_code: str = "SAVE_INSPECT_FAILED",
) -> tuple[str, ...]:
    matches = tuple(
        record for record in core.components if record.schema == ASSISTANCE_MEMORY.schema
    )
    try:
        if len(matches) != 1:
            raise ValueError("NPC_ASSISTANCE_MEMORY_INPUT")
        AssistanceAdapter(content).validate(matches[0])
    except ValueError as error:
        raise SaveError(error_code, "persistent assistance memory is invalid") from error
    state = cast(AssistanceMemoryRecord, matches[0]).state
    return (
        f"{label} 지속 도움 기억: 누적 {state.total_assists}회 · 최근 {len(state.entries)}개를 보관합니다.",
        *(
            f"{label} 도움 기억 · {entry.tick}초: 통행문을 열었습니다 · 원인: "
            + ("정기 행동." if entry.source_kind == "wake" else "호출 응답.")
            for entry in state.entries
        ),
    )
