"""Read-only comparison of retained own-action anchors;never infer lost history."""

from app.npc_cycle import evidence_text
from contracts.dialogue import GenerationError
from contracts.persistence import DurableCheckpoint
from domain.npc_cycle import MEMORY_CAP, CycleRecord, SupplyEvidence, validate_checkpoint
from domain.primitives import EntityId


def _memory(checkpoint: DurableCheckpoint, npc_id: EntityId) -> CycleRecord:
    records = tuple(r for r in checkpoint.core.components if type(r) is CycleRecord)
    if len(records) != 1:
        raise GenerationError("NPC_CONTEXT_INPUT")
    record = records[0]
    if record.entity_id != npc_id:
        raise GenerationError("NPC_MEMORY_COMPARISON_OWNER")
    try:
        CycleRecord(record.entity_id, record.state, record.entries)
    except ValueError as error:
        raise GenerationError("NPC_CONTEXT_INPUT") from error
    return record


def _anchors(record: CycleRecord) -> dict[tuple[str, int], SupplyEvidence]:
    result = {(e.source_event_id, e.sequence): e for e in record.entries}
    if len(result) != len(record.entries):
        raise GenerationError("NPC_CONTEXT_INPUT")
    return result


def cycle_slot_messages(
    saved: DurableCheckpoint, current: DurableCheckpoint, npc_id: EntityId
) -> tuple[str, ...]:
    if type(saved) is not DurableCheckpoint or type(current) is not DurableCheckpoint:
        raise GenerationError("NPC_CONTEXT_INPUT")
    if saved.core.world_id != current.core.world_id or saved.core.pins != current.core.pins:
        raise GenerationError("NPC_MEMORY_COMPARISON_OWNER")
    old_record, new_record = _memory(saved, npc_id), _memory(current, npc_id)
    old, new = _anchors(old_record), _anchors(new_record)
    common = old.keys() & new.keys()
    if any(old[key] != new[key] for key in common):
        raise GenerationError("NPC_MEMORY_COMPARISON_IDENTITY")
    try:
        for checkpoint, record in ((saved, old_record), (current, new_record)):
            validate_checkpoint(record, checkpoint.core.world_id, checkpoint.core.tick)
    except ValueError as error:
        raise GenerationError("NPC_CONTEXT_INPUT") from error
    groups = (
        ("공통 작업 기억", tuple(e for key, e in old.items() if key in common)),
        ("현재에만 있는 작업 기억", tuple(e for key, e in new.items() if key not in old)),
        ("저장에만 있는 작업 기억", tuple(e for key, e in old.items() if key not in new)),
    )
    lines = tuple(
        evidence_text(entry).replace("NPC 작업 기억", label, 1)
        for label, entries in groups
        for entry in entries
    )
    return (
        f"NPC 작업 기억 비교 · 현재 {current.core.tick}초 / 선택 저장 {saved.core.tick}초",
        f"공통 작업 {len(common)}개 · 현재에만 {len(new.keys() - old.keys())}개 · "
        f"저장에만 {len(old.keys() - new.keys())}개",
        f"현재 보관 {len(new)}/{new_record.state.produced + new_record.state.consumed}개 · "
        f"선택 저장 보관 {len(old)}/{old_record.state.produced + old_record.state.consumed}개 "
        f"(각 진행의 최근 작업 최대 {MEMORY_CAP}개)",
        "저장 시점·진행 분기·보관 범위의 차이입니다. "
        "한쪽에 기록이 없다고 행동하지 않았거나 기억을 잊었다는 뜻은 아닙니다.",
        *(lines or ("양쪽 진행에 보관된 NPC 작업 기억이 없습니다.",)),
    )
