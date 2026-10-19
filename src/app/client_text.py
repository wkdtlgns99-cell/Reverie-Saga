"""Korean explanations of committed facts;never predict or alter game outcomes."""

from __future__ import annotations

from collections.abc import Mapping

from contracts.client import ClientView
from contracts.encounter import (
    AttackResolved,
    Defeated,
    EncounterMoveBlocked,
    EncounterMoved,
    GateChanged,
    Rested,
)
from contracts.messages import FactPayload
from contracts.dialogue import QuestContent
from contracts.quest import GoalMet, QuestAccepted, QuestCompleted, QuestSpoken
from contracts.turn import TurnCommitted, TurnPublication
from contracts.watch import (
    BellRung,
    NpcActed,
    WatchEcho,
    WatchReplied,
    WatchRequested,
    WatchWake,
)
from domain.encounter import ENEMY_ID, GATE_ID
from domain.primitives import EntityId
from domain.trial import ACTOR_ID
from domain.watch import NPC_ID, WAIT_MAX

NAMES = {ACTOR_ID: "플레이어", ENEMY_ID: "적", NPC_ID: "NPC", GATE_ID: "문"}
QUEST_STAGE_NAMES = ("미수락", "진행 중", "보고 가능", "완료")
STATUS_TEXT = {
    "ACTIVITY_INSPECTED": (
        "저장에 남은 최근 NPC 자기 활동을 최대 8개 확인했습니다. 게임 시간은 흐르지 않습니다."
    ),
    "NPC_ACTIVITY_SOURCE": "NPC 활동의 저장 근거를 읽지 못했습니다. 현재 진행은 유지됩니다.",
    "SLOT_INSPECTED": "저장 슬롯의 진행 정보를 확인했습니다. 현재 게임은 바뀌지 않습니다.",
    "SLOT_INSPECTION_UNAVAILABLE": "게임에 연결한 뒤 저장 슬롯을 확인하세요.",
    "SAVE_INSPECT_FAILED": "저장 슬롯 정보를 읽지 못했습니다. 현재 진행은 유지됩니다.",
    "MEMORY_INSPECTED": "NPC가 기억하는 의뢰 대화를 확인했습니다. 게임 시간은 흐르지 않습니다.",
    "NPC_MEMORY_UNAVAILABLE": "현재 게임에서는 NPC 대화 기억을 확인할 수 없습니다.",
    "QUEST_UNAVAILABLE": "현재 구간에는 대화할 임무가 준비되어 있지 않습니다.",
    "QUEST_CONTENT_UNAVAILABLE": "이 임무에 필요한 승인 대사를 불러올 수 없습니다.",
    "ATTACHED": "게임에 연결했습니다. 행동 결과는 아래 기록창에 표시됩니다.",
    "CONNECTING": "게임에 연결하는 중입니다.",
    "COMMITTED": "행동 처리가 완료되었습니다.",
    "SAVED": "진행 상황을 저장했습니다.",
    "LOADED": "저장한 진행 상황을 불러왔습니다.",
    "OUT_OF_RANGE": "대상이 너무 멀리 있습니다. 가까이 이동하세요.",
    "INSUFFICIENT_STAMINA": "스태미나가 부족합니다. 휴식한 뒤 다시 공격하세요.",
    "TARGET_OCCUPIED": "문 위에 대상이 있어 닫을 수 없습니다. 문 밖으로 이동하세요.",
    "TARGET_DEFEATED": "대상은 이미 쓰러져 있어 공격할 수 없습니다.",
    "ACTOR_DEFEATED": "플레이어가 쓰러져 행동할 수 없습니다. 이전 저장을 불러오세요.",
    "INVALID_COMMAND": f"행동 입력이 올바르지 않습니다. 대기 시간은 1~{WAIT_MAX}초 정수입니다.",
    "INVALID_INPUT": "대기 시간에 정수를 입력하세요.",
    "INVALID_TARGET": "이 행동의 대상이 올바르지 않습니다.",
    "INVALID_ATTACK_PROFILE": "사용할 수 없는 공격 방식입니다.",
    "INVALID_SLOT": "저장 슬롯이 올바르지 않습니다. slot01~slot08을 선택하세요.",
    "SAVE_NOT_FOUND": "저장 파일을 찾지 못했습니다.",
    "SLOT_NOT_FOUND": "선택한 슬롯에 저장된 진행 상황이 없습니다.",
    "NO_RETRY": "재전송할 명령이 없습니다. 불러온 뒤에는 새 행동을 선택하세요.",
    "NO_RECOVERY_PENDING": "복구가 필요한 미확정 저장 작업이 없습니다.",
    "SAVE_UNCERTAIN": "저장 결과를 확인하지 못했습니다. 저장 상태 복구를 시도하세요.",
    "SAVE_UNAVAILABLE": "저장 처리에 실패했습니다. 작업이 적용됐다고 가정하지 마세요.",
    "SAVE_CORRUPT": "진행 파일을 읽을 수 없습니다. 원본은 교체하지 않았습니다.",
    "SAVE_LOAD_FAILED": "저장을 불러오지 못했습니다. 현재 진행은 유지됩니다.",
    "SAVE_EXPORT_FAILED": "슬롯에 저장하지 못했습니다. 저장 파일을 확인하세요.",
    "SAVE_EXPORT_UNCERTAIN": "슬롯 저장 결과가 불확실합니다. 완료됐다고 가정하지 마세요.",
    "SAVE_LIMIT": "저장 크기 또는 관리 파일 수 제한에 도달했습니다.",
    "SAVE_PACKAGE_UNAVAILABLE": "이 저장에 필요한 콘텐츠를 사용할 수 없습니다.",
    "INVALID_PATH": "안전하게 사용할 수 없는 진행 파일 경로입니다.",
    "UNSUPPORTED_RULESET": "현재 게임 규칙과 다른 저장입니다.",
    "UNSUPPORTED_LEGACY_SAVE": "이전 프로젝트의 저장은 불러올 수 없습니다.",
    "UNSUPPORTED_SAVE_VERSION": "지원하지 않는 저장 형식입니다.",
    "NEWER_SAVE_VERSION": "더 새로운 게임 버전에서 만든 저장입니다.",
    "SESSION_CLOSED": "게임 연결이 종료됐습니다.",
    "SAVE_BUSY": "다른 저장 작업을 처리 중입니다. 잠시 뒤 다시 시도하세요.",
    "SAVE_STALE": "저장 상태가 변경돼 현재 연결을 사용할 수 없습니다.",
    "STALE_ATTACHMENT": "현재 진행 파일과 명령의 연결이 다릅니다.",
    "STALE_REVISION": "명령과 현재 게임 상태가 다릅니다. 상태를 다시 확인하세요.",
    "RESYNC_REQUIRED": "이전 명령은 처리됐지만 화면 상태를 다시 확인해야 합니다.",
    "PRESENTATION_FAILED": "게임 결과는 확정됐지만 일부 연출을 표시하지 못했습니다.",
    "EVENT_DEFERRED": "일부 사건이 이후 게임 시간으로 예약됐습니다.",
    "CLIENT_ERROR": "화면 연결 작업에 오류가 발생했습니다. 상세 정보를 확인하세요.",
}
BLOCK_TEXT = {
    "boundary": "맵 경계 밖으로는 이동할 수 없습니다.",
    "wall": "벽에 막혀 이동하지 못했습니다.",
    "door": "닫힌 문에 막혔습니다. 문을 먼저 여세요.",
    "occupied": "적이 길을 막고 있어 이동하지 못했습니다.",
}


def status_text(code: str) -> str:
    message = STATUS_TEXT.get(code)
    if message is None:
        return f"설명이 준비되지 않은 처리 상태입니다. ({code})"
    if code in {
        "ATTACHED",
        "CONNECTING",
        "COMMITTED",
        "SAVED",
        "LOADED",
        "MEMORY_INSPECTED",
        "SLOT_INSPECTED",
    }:
        return message
    return f"{message} ({code})"


def npc_activity_text(view: ClientView) -> str:
    return (
        f"NPC 활동 현황 · {view.tick}초 · 종 {view.npc_bells}회 · 호출 응답 {view.npc_replies}회."
    )


def _name(entity: EntityId, names: Mapping[EntityId, str] | None = None) -> str:
    return (NAMES if names is None else names).get(entity, str(entity))


def _attack_text(
    payload: AttackResolved, names: Mapping[EntityId, str] | None = None
) -> tuple[str, ...]:
    actor, target = _name(payload.actor_id, names), _name(payload.target_id, names)
    damage = payload.target_hp_before - payload.target_hp_after
    lines = [
        f"{actor} → {target}: 공격, 피해 {damage} "
        f"(체력 {payload.target_hp_before} → {payload.target_hp_after})."
    ]
    counter = payload.actor_hp_before - payload.actor_hp_after
    if counter > 0:
        lines.append(
            f"{target} → {actor}: 반격, 피해 {counter} "
            f"(체력 {payload.actor_hp_before} → {payload.actor_hp_after})."
        )
    lines.append(f"{actor}의 스태미나 {payload.stamina_before} → {payload.stamina_after}.")
    return tuple(lines)


def fact_messages(
    payload: FactPayload,
    names: Mapping[EntityId, str] | None = None,
    quest_content: QuestContent | None = None,
) -> tuple[str, ...]:
    match payload:
        case QuestAccepted():
            return ("임무를 받았습니다. 길을 막는 적을 처치하고 NPC에게 보고하세요.",)
        case GoalMet():
            return ("임무 목표를 달성했습니다. NPC에게 돌아가 보고하세요.",)
        case QuestCompleted():
            return (f"임무를 완료했습니다. 포구의 호의 {payload.amount}개가 기록되었습니다.",)
        case QuestSpoken():
            if (
                quest_content is None
                or payload.quest_id != quest_content.definition.quest_id
                or payload.npc_id != quest_content.dialogue.npc_id
            ):
                raise ValueError("QUEST_CONTENT_UNAVAILABLE")
            return (
                f"{_name(payload.npc_id, names)}: {quest_content.dialogue.text(payload.intent)}",
            )
        case AttackResolved():
            return _attack_text(payload, names)
        case EncounterMoved():
            return (
                f"{_name(payload.actor_id, names)}가 {payload.from_cell}번 칸에서 "
                f"{payload.to_cell}번 칸으로 이동했습니다.",
            )
        case EncounterMoveBlocked():
            return (BLOCK_TEXT[payload.reason],)
        case GateChanged():
            state = "열려" if payload.after_open else "닫혀"
            if payload.before_open == payload.after_open:
                return (
                    f"{_name(payload.target_id, names)}은 이미 {state} 있습니다. "
                    "시간을 보냈습니다.",
                )
            verb = "열었습니다" if payload.after_open else "닫았습니다"
            return (
                f"{_name(payload.actor_id, names)}가 {_name(payload.target_id, names)}을 {verb}.",
            )
        case Rested():
            if payload.before_stamina == payload.after_stamina:
                return (
                    f"{_name(payload.actor_id, names)}가 휴식했지만 스태미나는 변하지 않았습니다.",
                )
            return (
                f"{_name(payload.actor_id, names)}가 휴식했습니다. "
                f"스태미나 {payload.before_stamina} → {payload.after_stamina}.",
            )
        case Defeated():
            return (
                f"{_name(payload.entity_id, names)}이 쓰러졌습니다. "
                f"처치한 대상: {_name(payload.killer_id, names)}.",
            )
        case NpcActed():
            return (
                f"{_name(payload.npc_id, names)}가 종을 울렸습니다. (누적 {payload.after_bells}회)",
            )
        case BellRung():
            return (
                f"{_name(payload.actor_id, names)}가 "
                f"{_name(payload.npc_id, names)}를 호출했습니다.",
            )
        case WatchReplied():
            return (
                f"{_name(payload.npc_id, names)}가 호출에 응답했습니다. "
                f"(누적 {payload.after_count}회)",
            )
        case WatchWake() | WatchRequested() | WatchEcho():
            return ()  # Internal scheduling is not an additional spoken line or player action.
        case _:
            return (f"설명이 준비되지 않은 사건입니다. ({payload.schema.kind})",)


def turn_messages(
    publication: TurnPublication,
    *,
    wait_seconds: int | None = None,
    names: Mapping[EntityId, str] | None = None,
    actor_id: EntityId = ACTOR_ID,
    quest_content: QuestContent | None = None,
) -> tuple[str, ...]:
    outcome = publication.outcome
    diagnostics = tuple(status_text(d.code) for d in publication.diagnostics)
    if not isinstance(outcome, TurnCommitted):
        # A rejected/aborted publication can never narrate successful attempted effects.
        return (status_text(outcome.failure.code), *diagnostics)
    if publication.diff is None and not publication.facts:
        return (
            "이미 처리된 명령의 결과를 확인했습니다. 행동은 다시 실행하지 않았습니다.",
            *diagnostics,
        )
    messages: tuple[str, ...] = (
        ()
        if wait_seconds is None
        else (f"{_name(actor_id, names)}가 {wait_seconds}초 동안 기다렸습니다.",)
    )
    messages += tuple(
        line
        for event in publication.facts
        for line in fact_messages(event.payload, names, quest_content)
    )
    return (*messages, *diagnostics) or (status_text("COMMITTED"),)
