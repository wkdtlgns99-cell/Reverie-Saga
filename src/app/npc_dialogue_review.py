"""Offline structural/current-source review;never approves or imports candidate prose."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import html
from pathlib import Path
import re
import sys
from typing import Sequence

from adapters.quest_dialogue import decode_candidate, load_dialogue, publish_fresh
from app.npc_dialogue_plan import check_plan, plan_document
from app.npc_prepare import MAX_PREPARATION_BYTES, _generation_document, _target_available
from app.quest_definition import harbor_definition
from contracts.dialogue import GeneratedDialogue, GenerationError, QuestContent, QuestDialogue
from contracts.npc_memory import NpcMemoryContext
from contracts.persistence import SaveError
from domain.canonical import (
    JsonObject,
    canonical_json,
    decode_json,
    exact_fields,
    int_value,
    text_value,
)


@dataclass(frozen=True, slots=True)
class DialogueReview:
    context: NpcMemoryContext
    generated: GeneratedDialogue
    dialogue: QuestDialogue
    plan_sha256: str
    request_sha256: str
    preparation_sha256: str


def _read_preparation(path: Path) -> bytes:
    try:
        with path.open("rb") as source:
            raw = source.read(MAX_PREPARATION_BYTES + 1)
    except OSError:
        raise GenerationError("NPC_DIALOGUE_REVIEW_UNAVAILABLE") from None
    if not 1 <= len(raw) <= MAX_PREPARATION_BYTES:
        raise GenerationError("NPC_DIALOGUE_REVIEW_INVALID")
    return raw


def _generation(data: JsonObject) -> GeneratedDialogue:
    generation = exact_fields(
        data["generation"], ("provider", "model", "candidate_raw", "output_sha256", "usage")
    )
    usage = exact_fields(
        generation["usage"],
        ("prompt_tokens", "output_tokens", "thought_tokens", "total_tokens", "attempts"),
    )
    counts = tuple(
        None if usage[name] is None else int_value(usage[name])
        for name in ("prompt_tokens", "output_tokens", "thought_tokens", "total_tokens")
    )
    result = GeneratedDialogue(
        text_value(generation["candidate_raw"]).encode("utf-8"),
        text_value(generation["model"]),
        counts[0],
        counts[1],
        counts[2],
        counts[3],
        attempts=int_value(usage["attempts"]),
    )
    if canonical_json(generation) != canonical_json(_generation_document(result)):
        raise ValueError("generation metadata")
    return result


def review_preparation(
    working: Path, content: QuestContent, npc_id: str, plan: Path, preparation: Path
) -> DialogueReview:
    raw = _read_preparation(preparation)
    try:
        data = exact_fields(
            decode_json(raw),
            (
                "format",
                "status",
                "context",
                "context_sha256",
                "brief_sha256",
                "generation",
                "plan_sha256",
                "request_sha256",
            ),
        )
        if (
            data["format"] != "reverie-npc-memory-preparation/v2"
            or data["status"] != "NEEDS_REVIEW"
        ):
            raise ValueError("format/status")
        generated = _generation(data)
    except (ValueError, UnicodeError, RecursionError):
        raise GenerationError("NPC_DIALOGUE_REVIEW_INVALID") from None
    context = check_plan(working, content, npc_id, plan)
    preview = plan_document(context)
    plan_hash = hashlib.sha256(canonical_json(preview)).hexdigest()
    if data["context_sha256"] != context.sha256:
        raise GenerationError("NPC_CONTEXT_STALE")
    expected: JsonObject = {
        "format": "reverie-npc-memory-preparation/v2",
        "status": "NEEDS_REVIEW",
        "context": context.document(),
        "context_sha256": context.sha256,
        "brief_sha256": preview["brief_sha256"],
        "generation": _generation_document(generated),
        "plan_sha256": plan_hash,
        "request_sha256": preview["request_sha256"],
    }
    if canonical_json(data) != canonical_json(expected) or generated.model != preview["model"]:
        raise GenerationError("NPC_DIALOGUE_REVIEW_INVALID")
    if check_plan(working, content, npc_id, plan) != context:
        raise GenerationError("NPC_CONTEXT_STALE")
    if _read_preparation(preparation) != raw:
        raise GenerationError("NPC_DIALOGUE_REVIEW_INVALID")
    return DialogueReview(
        context,
        generated,
        decode_candidate(generated.candidate),
        plan_hash,
        text_value(preview["request_sha256"]),
        hashlib.sha256(raw).hexdigest(),
    )


def _literal(text: str) -> str:
    # Preserve prose as text:provider output must not become active Markdown/HTML.
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", html.escape(text, quote=False))


def render_review(review: DialogueReview) -> str:
    source, generated = review.context.source, review.generated
    phase = {"available": "제안 가능", "accepted": "수락됨", "reported": "완료 보고됨"}
    rows = [
        "# AI 대사 후보 검토",
        "",
        "상태: **NEEDS_REVIEW · 승인 전**",
        "현재 상태와 입력·출력 형식의 일치를 확인했습니다. 대사의 사실성·품질은 검토가 필요합니다.",
        "해시는 파일 일치 확인용이며, 제공자의 생성 사실을 인증하는 서명이 아닙니다.",
        "",
        "## 생성 근거",
        "",
        f"- NPC: `{source.npc_id}` / 퀘스트: `{source.quest_id}` / 플레이어: `{source.actor_id}`",
        f"- 게임 시점: 턴 {source.tick}, 리비전 {source.revision}; 상태: {phase[source.known_phase]}",
        f"- 기록된 포구의 호의: {source.recorded_favor}건",
    ]
    for entry in review.context.entries:
        label = "퀘스트 수락을 관찰" if entry.kind == "accepted" else "완료 보고를 받음"
        rows.append(f"- 턴 {entry.observed_at}: {label}; 사건 `{entry.source_event_id}`")
    if not review.context.entries:
        rows.append("- 기록된 대화 기억 없음")
    rows += [
        "- 완료 보고를 받은 기억은 적 처치를 직접 목격한 기억이 아닙니다.",
        "",
        "## 생성 대사",
        "",
        "아래 네 문장은 상황별 후보입니다. 현재 상황에서 전부 사용하는 대사가 아닙니다.",
    ]
    labels = {
        "completion": "완료 보고 응답",
        "gratitude": "보고 후 감사",
        "offer": "퀘스트 제안",
        "reminder": "진행 확인",
    }
    for line in review.dialogue.lines:
        rows += ["", f"### {labels[line.intent]}", "", "> " + _literal(line.text_ko)]
    rows += ["", "## 요청 기록", "", f"- 제공자: Gemini; 모델: `{generated.model}`"]
    for label, count in (
        ("입력 토큰", generated.prompt_tokens),
        ("출력 토큰", generated.output_tokens),
        ("생각 토큰", generated.thought_tokens),
        ("전체 토큰", generated.total_tokens),
    ):
        rows.append(f"- {label}: {'미제공' if count is None else str(count)}")
    rows.append(f"- 요청 시도: {generated.attempts}회")
    for label, digest in (
        ("게임 상태", source.core_hash),
        ("사용한 카탈로그", source.catalog_sha256),
        ("NPC 기억", review.context.sha256),
        ("입력 미리보기", review.plan_sha256),
        ("요청", review.request_sha256),
        ("준비 파일", review.preparation_sha256),
        ("원본 대사", hashlib.sha256(generated.candidate).hexdigest()),
    ):
        rows.append(f"- {label} SHA256: `{digest}`")
    rows += [
        "",
        "검토 항목: 과거 사실을 지어내는지, 보고와 목격을 혼동하는지,",
        "보상을 추가로 약속하는지, 각 상황의 말투가 적절한지 확인하세요.",
        "이 보고서는 대사 승인·카탈로그 반영·게임 저장 변경을 수행하지 않습니다.",
        "",
    ]
    return "\n".join(rows)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review a saved plan-bound NPC dialogue candidate")
    parser.add_argument("--working", type=Path, required=True)
    parser.add_argument("--quest-catalog", type=Path, required=True)
    parser.add_argument("--quest-sha256", required=True)
    parser.add_argument("--npc-id", default=harbor_definition().layout.npc_id)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.output is not None:
            _target_available(args.output)
        content = load_dialogue(args.quest_catalog, args.quest_sha256, harbor_definition())
        review = review_preparation(args.working, content, args.npc_id, args.plan, args.preparation)
        report = render_review(review)
        if args.output is None:
            print(report, end="")
        else:
            publish_fresh(args.output, report.encode("utf-8"))
            print("DIALOGUE_CANDIDATE_CURRENT_NEEDS_REVIEW")
    except (ValueError, OSError, UnicodeError, RecursionError, SaveError) as error:
        code = (
            error.code
            if isinstance(error, (GenerationError, SaveError))
            else "NPC_DIALOGUE_REVIEW_INPUT"
        )
        print(code, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
