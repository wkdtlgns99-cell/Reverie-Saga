from dataclasses import replace
from typing import cast

import pytest

from app.npc_cycle import bootstrap_cycle
from app.npc_cycle_compare import cycle_slot_messages
from app.watch import WatchBootstrapSpec
from contracts.dialogue import GenerationError
from contracts.persistence import DurableCheckpoint
from domain.npc_cycle import CycleRecord, Supply, SupplyEvidence, wake_identity
from domain.primitives import EntityId, Tick
from tests.unit.quest_fixtures import content

OWNER = EntityId("actor:harbor-watcher")


def checkpoint(tick: int) -> DurableCheckpoint:
    initial = bootstrap_cycle(WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32), content())
    core = initial.snapshot()
    # Literal own-action vectors;other components are irrelevant to this pure projection.
    rows = (
        (4, 0, (1, 1, 0)),
        (8, 0, (2, 2, 0)),
        (10, 0, (1, 2, 1)),
        (12, 0, (2, 3, 1)),
        (16, 0, (3, 4, 1)),
        (20, 0, (2, 4, 2)),
        (20, 1, (3, 5, 2)),
        (30, 0, (2, 5, 3)),
        (32, 0, (3, 6, 3)),
    )
    before = Supply(0, 0, 0)
    entries: tuple[SupplyEvidence, ...] = ()
    for at, sequence, values in rows:
        if at > tick:
            break
        after = Supply(*values)
        entries = (
            *entries,
            SupplyEvidence(at, sequence, wake_identity(core.world_id, at), before, after),
        )[-4:]
        before = after
    record = CycleRecord(OWNER, before, entries)
    return DurableCheckpoint(
        replace(
            core,
            tick=Tick(tick),
            components=tuple(record if isinstance(r, CycleRecord) else r for r in core.components),
        ),
        initial.protocol(),
    )


@pytest.mark.parametrize(
    "saved,current,counts",
    (
        (0, 0, (0, 0, 0)),
        (0, 4, (0, 1, 0)),
        (10, 20, (0, 4, 3)),
        (16, 20, (2, 2, 2)),
        (20, 20, (4, 0, 0)),
        (20, 0, (0, 0, 4)),
        (20, 32, (2, 2, 2)),
    ),
)
def test_literal_shared_current_saved_counts_retention_and_chronology(
    saved: int, current: int, counts: tuple[int, int, int]
) -> None:
    messages = cycle_slot_messages(checkpoint(saved), checkpoint(current), OWNER)
    common, now, old = counts
    assert messages[0] == f"NPC 작업 기억 비교 · 현재 {current}초 / 선택 저장 {saved}초"
    assert messages[1] == f"공통 작업 {common}개 · 현재에만 {now}개 · 저장에만 {old}개"
    assert "최근 작업 최대 4개" in messages[2]
    assert "보관 범위의 차이" in messages[3] and "행동하지 않았거나 기억을 잊었다" in messages[3]
    assert len(messages) == 4 + max(1, sum(counts))
    assert not any("e1-" in m for m in messages)
    if saved == current == 0:
        assert messages[-1] == "양쪽 진행에 보관된 NPC 작업 기억이 없습니다."
    if saved == 16 and current == 20:
        assert messages[4:] == (
            "공통 작업 기억 · 12초: 공동 물자 1개를 준비했습니다 · 물자 2/3개.",
            "공통 작업 기억 · 16초: 공동 물자 1개를 준비했습니다 · 물자 3/3개.",
            "현재에만 있는 작업 기억 · 20초: 공동 물자 1개를 사용했습니다 · 물자 2/3개.",
            "현재에만 있는 작업 기억 · 20초: 공동 물자 1개를 준비했습니다 · 물자 3/3개.",
            "저장에만 있는 작업 기억 · 8초: 공동 물자 1개를 준비했습니다 · 물자 2/3개.",
            "저장에만 있는 작업 기억 · 10초: 공동 물자 1개를 사용했습니다 · 물자 1/3개.",
        )


@pytest.mark.parametrize("bad", (None, (), 0, True, "checkpoint"))
def test_exact_checkpoint_type(bad: object) -> None:
    valid = checkpoint(0)
    with pytest.raises(GenerationError, match="^NPC_CONTEXT_INPUT$"):
        cycle_slot_messages(cast(DurableCheckpoint, bad), valid, OWNER)
    with pytest.raises(GenerationError, match="^NPC_CONTEXT_INPUT$"):
        cycle_slot_messages(valid, cast(DurableCheckpoint, bad), OWNER)


def test_foreign_owner_world_pins_missing_record_and_identity_collision() -> None:
    valid = checkpoint(4)
    record = next(r for r in valid.core.components if isinstance(r, CycleRecord))
    for foreign in (
        replace(valid, core=replace(valid.core, world_id="w1-" + "f" * 64)),
        replace(
            valid,
            core=replace(valid.core, pins=replace(valid.core.pins, rules_fingerprint="f" * 64)),
        ),
    ):
        with pytest.raises(GenerationError, match="^NPC_MEMORY_COMPARISON_OWNER$"):
            cycle_slot_messages(valid, foreign, OWNER)
    with pytest.raises(GenerationError, match="^NPC_MEMORY_COMPARISON_OWNER$"):
        cycle_slot_messages(valid, valid, EntityId("actor:other"))
    missing = replace(
        valid,
        core=replace(
            valid.core,
            components=tuple(r for r in valid.core.components if not isinstance(r, CycleRecord)),
        ),
    )
    with pytest.raises(GenerationError, match="^NPC_CONTEXT_INPUT$"):
        cycle_slot_messages(valid, missing, OWNER)
    changed = replace(record, entries=(replace(record.entries[0], tick=8),))
    forged = replace(
        valid,
        core=replace(
            valid.core,
            components=tuple(changed if r is record else r for r in valid.core.components),
        ),
    )
    with pytest.raises(GenerationError, match="^NPC_MEMORY_COMPARISON_IDENTITY$"):
        cycle_slot_messages(valid, forged, OWNER)
    changed = replace(
        record, entries=(replace(record.entries[0], source_event_id="e1-" + "f" * 64),)
    )
    forged = replace(
        valid,
        core=replace(
            valid.core,
            components=tuple(changed if r is record else r for r in valid.core.components),
        ),
    )
    with pytest.raises(GenerationError, match="^NPC_CONTEXT_INPUT$"):
        cycle_slot_messages(valid, forged, OWNER)
