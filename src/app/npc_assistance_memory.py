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


def _memory_record(
    core: CoreSnapshot,
    content: QuestContent,
    *,
    error_code: str,
) -> AssistanceMemoryRecord:
    matches = tuple(
        record for record in core.components if record.schema == ASSISTANCE_MEMORY.schema
    )
    try:
        if len(matches) != 1:
            raise ValueError("NPC_ASSISTANCE_MEMORY_INPUT")
        AssistanceAdapter(content).validate(matches[0])
    except ValueError as error:
        raise SaveError(error_code, "persistent assistance memory is invalid") from error
    return cast(AssistanceMemoryRecord, matches[0])


def assistance_messages(
    core: CoreSnapshot,
    content: QuestContent,
    *,
    label: str = "NPC",
    error_code: str = "SAVE_INSPECT_FAILED",
) -> tuple[str, ...]:
    state = _memory_record(core, content, error_code=error_code).state
    return (
        f"{label} 지속 도움 기억: 누적 {state.total_assists}회 · 최근 {len(state.entries)}개를 보관합니다.",
        *(
            f"{label} 도움 기억 · {entry.tick}초: 통행문을 열었습니다 · 원인: "
            + ("정기 행동." if entry.source_kind == "wake" else "호출 응답.")
            for entry in state.entries
        ),
    )


def assistance_slot_comparison(
    saved: CoreSnapshot, current: CoreSnapshot, content: QuestContent
) -> tuple[str, ...]:
    """Compare bounded anchors from two owner-validated snapshots,not missing history."""
    if saved.world_id != current.world_id or saved.pins != current.pins:
        raise SaveError("SAVE_INSPECT_FAILED", "assistance comparison source differs")
    old = _memory_record(saved, content, error_code="SAVE_INSPECT_FAILED")
    new = _memory_record(current, content, error_code="SAVE_INSPECT_FAILED")
    old_entries = {
        (old.entity_id, entry.target_id, entry.source_kind, entry.cause_event_id): entry
        for entry in old.state.entries
    }
    new_entries = {
        (new.entity_id, entry.target_id, entry.source_kind, entry.cause_event_id): entry
        for entry in new.state.entries
    }
    common = old_entries.keys() & new_entries.keys()
    if any(old_entries[key] != new_entries[key] for key in common):
        raise SaveError("SAVE_INSPECT_FAILED", "assistance comparison identity differs")
    difference = new.state.total_assists - old.state.total_assists
    if difference > 0:
        count = f"현재가 선택 저장보다 {difference}회 많습니다."
    elif difference < 0:
        count = f"선택 저장이 현재보다 {-difference}회 많습니다."
    else:
        count = f"양쪽 모두 {new.state.total_assists}회입니다."
    return (
        f"NPC 도움 기억 비교 · 현재 {current.tick}초 / 선택 저장 {saved.tick}초",
        "NPC 누적 도움 횟수 비교 · " + count,
        f"보관 도움 기억 비교 · 공통 {len(common)}개 · "
        f"현재에만 {len(new_entries.keys() - old_entries.keys())}개 · "
        f"선택 저장에만 {len(old_entries.keys() - new_entries.keys())}개",
        f"각 진행이 보관한 최근 최대 {ASSISTANCE_CAPACITY}개의 도움 기억만 비교합니다. "
        "한쪽에 없다고 돕지 않았거나 기억을 잊었다는 뜻은 아닙니다.",
    )
