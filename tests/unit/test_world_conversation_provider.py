"""Live request validation,one-attempt accounting and actual child cancellation."""

from collections.abc import Sequence
from pathlib import Path
import subprocess
import sys
from threading import Event, Timer
import time

import pytest

from adapters.generation_budget import GenerationBudget
from adapters.world_conversation import (
    GeminiConversation,
    cancellable_transport,
    generation_request,
    parse_reply,
)
from contracts.dialogue import GenerationError
from contracts.world_conversation import ConversationContext
from domain.canonical import JsonObject, canonical_json, decode_json, object_value
from domain.world_conversation import Exchange


def context() -> ConversationContext:
    return ConversationContext(
        "resident:test",
        "나루",
        "상인",
        "신중함",
        "물버들",
        "여울 왕국",
        "운송",
        "범람원",
        1,
        "일하는 중",
        "시장",
        (("market_stock", "2"),),
        "none",
        Exchange("speech:s1", "resident:test", "place:p0-a", "안녕", 0, 1),
        (),
    )


def response(text: str = "안녕하세요.", proposal: str = "none") -> JsonObject:
    return {
        "candidates": (
            {
                "finishReason": "STOP",
                "content": {
                    "parts": (
                        {
                            "text": canonical_json(
                                {"text_ko": text, "proposal_operation": proposal}
                            ).decode("utf-8")
                        },
                    )
                },
            },
        ),
        "modelVersion": "gemini-3.5-flash-lite",
        "usageMetadata": {"totalTokenCount": 123},
    }


def test_runtime_spacing_is_explicit_and_preparation_default_stays_one_minute(
    tmp_path: Path,
) -> None:
    runtime = GenerationBudget(tmp_path / "runtime", spacing_ms=0)
    assert runtime.reserve(now_ms=1791849600000).number == 1
    assert runtime.reserve(now_ms=1791849600000).number == 2
    preparation = GenerationBudget(tmp_path / "preparation")
    preparation.reserve(now_ms=1791849600000)
    with pytest.raises(GenerationError, match="GENERATION_DEFERRED"):
        preparation.reserve(now_ms=1791849659999)
    assert preparation.reserve(now_ms=1791849660000).number == 2


def test_one_explicit_request_accounts_tokens_and_binds_exact_context(tmp_path: Path) -> None:
    calls = []

    def send(request: JsonObject, key: str, cancelled: Event) -> JsonObject:
        calls.append(request)
        assert key == "fixture-key" and not cancelled.is_set()
        return response()

    provider = GeminiConversation(
        "fixture-key",
        GenerationBudget(tmp_path, spacing_ms=0),
        free_tier_confirmed=True,
        free_data_use_confirmed=True,
        send=send,
    )
    reply = provider.generate(context())
    assert reply.text == "안녕하세요." and reply.context_sha256 == context().sha256
    assert reply.total_tokens == 123 and len(calls) == 1
    ledger = object_value(decode_json((tmp_path / "budget.json").read_bytes()))
    assert ledger["attempts"] == 1 and ledger["tokens"] == 123
    with pytest.raises(GenerationError, match="GENERATION_JOB_USED"):
        provider.generate(context())
    assert len(calls) == 1
    config = object_value(generation_request(context())["generationConfig"])
    assert config["thinkingConfig"] == {"thinkingLevel": "MINIMAL"}


@pytest.mark.parametrize(
    "reply",
    [
        response("", "none"),
        response("a" * 513),
        response("받았어요", "deliver"),
        {"candidates": (), "usageMetadata": {"totalTokenCount": 123}},
    ],
)
def test_bad_output_or_unsupported_action_is_explicitly_rejected(reply: JsonObject) -> None:
    with pytest.raises(GenerationError, match="GENERATION_OUTPUT"):
        parse_reply(reply, context())


def test_provider_failure_never_automatically_retries(tmp_path: Path) -> None:
    calls = [0]

    def fail(request: JsonObject, key: str, cancelled: Event) -> JsonObject:
        calls[0] += 1
        raise GenerationError("GENERATION_DEFERRED")

    provider = GeminiConversation(
        "fixture-key",
        GenerationBudget(tmp_path, spacing_ms=0),
        free_tier_confirmed=True,
        free_data_use_confirmed=True,
        send=fail,
    )
    with pytest.raises(GenerationError, match="GENERATION_DEFERRED"):
        provider.generate(context())
    assert calls == [1]
    assert object_value(decode_json((tmp_path / "budget.json").read_bytes()))["tokens"] == 20000


def test_inflight_cancellation_kills_and_closes_only_the_owned_real_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = subprocess.Popen
    owned: list[subprocess.Popen[bytes]] = []

    def launch(
        args: Sequence[str], *, stdin: int, stdout: int, stderr: int
    ) -> subprocess.Popen[bytes]:
        child = original(
            [sys.executable, "-c", "import sys,time; sys.stdin.buffer.read(); time.sleep(30)"],
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
        )
        owned.append(child)
        return child

    monkeypatch.setattr("adapters.world_conversation.subprocess.Popen", launch)
    cancelled = Event()
    timer = Timer(0.2, cancelled.set)
    timer.start()
    started = time.monotonic()
    try:
        with pytest.raises(GenerationError, match="GENERATION_CANCELLED"):
            cancellable_transport(generation_request(context()), "fixture-key", cancelled)
    finally:
        timer.cancel()
        timer.join()
    assert time.monotonic() - started < 5
    assert len(owned) == 1 and owned[0].poll() is not None
    assert all(
        pipe is not None and pipe.closed
        for pipe in (owned[0].stdin, owned[0].stdout, owned[0].stderr)
    )
