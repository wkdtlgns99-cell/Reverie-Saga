from __future__ import annotations

import io
from pathlib import Path
from urllib.request import Request

import pytest

from adapters.gemini_dialogue import GeminiDialogue, generation_request, parse_response
from adapters.gemini_transport import MAX_NETWORK, NoRedirect, fetch
from adapters.generation_budget import GenerationBudget, Reservation
from app.dialogue_prepare import harbor_brief, main
from contracts.dialogue import GenerationError
from domain.canonical import (
    JsonObject,
    array_value,
    canonical_json,
    decode_json,
    object_value,
    seal,
)
from tests.unit.quest_fixtures import candidate


def response() -> JsonObject:
    return object_value(
        seal(
            {
                "candidates": (
                    {
                        "finishReason": "STOP",
                        "content": {"parts": ({"text": candidate().decode()},)},
                    },
                ),
                "modelVersion": "gemini-3.5-flash-lite",
                "usageMetadata": {
                    "promptTokenCount": 100,
                    "candidatesTokenCount": 150,
                    "thoughtsTokenCount": 10,
                    "totalTokenCount": 260,
                },
            }
        )
    )


@pytest.mark.parametrize(
    "field,value", (("finishReason", "MAX_TOKENS"), ("finishReason", "SAFETY"))
)
def test_non_stop_is_explicit_rejection(field: str, value: str) -> None:
    document = dict(response())
    from domain.canonical import array_value

    row = dict(object_value(array_value(document["candidates"])[0]))
    row[field] = value
    document["candidates"] = (row,)
    with pytest.raises(GenerationError, match="GENERATION_OUTPUT"):
        parse_response(document)


def test_schema_and_thinking_request_and_usage() -> None:
    request = generation_request(harbor_brief())
    config = object_value(request["generationConfig"])
    assert config["thinkingConfig"] == {"thinkingLevel": "MINIMAL"}
    assert config["maxOutputTokens"] == 2048
    result = parse_response(response())
    assert result.thought_tokens == 10 and result.total_tokens == 260


@pytest.mark.parametrize("kind", ("reverse", "duplicate"))
def test_invalid_intent_order_keeps_raw_output_contract_and_accounts_once(
    tmp_path: Path, kind: str
) -> None:
    document = dict(object_value(decode_json(candidate())))
    lines = array_value(document["lines"])
    document["lines"] = lines[::-1] if kind == "reverse" else (*lines[:-1], lines[0])
    raw = canonical_json(document)
    envelope = dict(response())
    envelope["candidates"] = (
        {
            "finishReason": "STOP",
            "content": {"parts": ({"text": raw.decode()},)},
        },
    )
    calls: list[JsonObject] = []

    def send(request: JsonObject, key: str) -> JsonObject:
        calls.append(request)
        return envelope

    generator = GeminiDialogue(
        "offline-test-key",
        GenerationBudget(tmp_path),
        free_tier_confirmed=True,
        free_data_use_confirmed=True,
        send=send,
    )
    with pytest.raises(GenerationError, match="GENERATION_OUTPUT"):
        generator.generate(harbor_brief())
    ledger = object_value(decode_json((tmp_path / "budget.json").read_bytes()))
    assert len(calls) == 1
    assert (ledger["attempts"], ledger["tokens"], ledger["settled"]) == (1, 260, (1,))


@pytest.mark.parametrize("code", ("GENERATION_DEFERRED", "GENERATION_AUTH", "GENERATION_REJECTED"))
def test_provider_failure_has_no_retry_and_keeps_budget(tmp_path: Path, code: str) -> None:
    calls = []

    def send(request: JsonObject, key: str) -> JsonObject:
        calls.append(request)
        raise GenerationError(code)

    generator = GeminiDialogue(
        "offline-test-key",
        GenerationBudget(tmp_path),
        free_tier_confirmed=True,
        free_data_use_confirmed=True,
        send=send,
    )
    with pytest.raises(GenerationError, match=code):
        generator.generate(harbor_brief())
    assert len(calls) == 1


def test_one_transient_retry_is_bounded_and_accounts_thoughts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = [1791849600.0]
    monkeypatch.setattr("adapters.generation_budget.time.time", lambda: now[0])
    calls = []

    def send(request: JsonObject, key: str) -> JsonObject:
        calls.append(request)
        if len(calls) == 1:
            raise GenerationError("GENERATION_TRANSIENT")
        return response()

    def sleep(seconds: float) -> None:
        assert seconds == 60
        now[0] += seconds

    generated = GeminiDialogue(
        "offline-test-key",
        GenerationBudget(tmp_path),
        free_tier_confirmed=True,
        free_data_use_confirmed=True,
        send=send,
        sleep=sleep,
    ).generate(harbor_brief())
    assert len(calls) == 2 and generated.total_tokens == 260


def test_redirect_disabled() -> None:
    with pytest.raises(GenerationError, match="GENERATION_REDIRECT"):
        NoRedirect().redirect_request(
            Request("https://example.invalid"),
            io.BytesIO(),
            302,
            "Found",
            {},
            "https://other.invalid",
        )


@pytest.mark.parametrize("initial", ("GENERATION_TIMEOUT", "GENERATION_TRANSIENT"))
def test_retry_reservation_failure_preserves_original_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, initial: str
) -> None:
    budget = GenerationBudget(tmp_path)
    reserve = budget.reserve
    reservations: list[Reservation] = []
    calls = []

    def reserve_once() -> Reservation:
        if reservations:
            raise GenerationError("GENERATION_BUDGET_UNAVAILABLE")
        result = reserve()
        reservations.append(result)
        return result

    def send(request: JsonObject, key: str) -> JsonObject:
        calls.append(request)
        raise GenerationError(initial)

    monkeypatch.setattr(budget, "reserve", reserve_once)
    generator = GeminiDialogue(
        "offline-test-key",
        budget,
        free_tier_confirmed=True,
        free_data_use_confirmed=True,
        send=send,
        sleep=lambda _: None,
    )
    with pytest.raises(GenerationError, match=initial) as caught:
        generator.generate(harbor_brief())
    assert isinstance(caught.value.__cause__, GenerationError)
    assert caught.value.__cause__.code == "GENERATION_BUDGET_UNAVAILABLE"
    assert len(calls) == 1 and len(reservations) == 1


def test_daily_limit_removal_still_bounds_each_job_to_two_requests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = [1791849600.0]
    monkeypatch.setattr("adapters.generation_budget.time.time", lambda: now[0])
    budget = GenerationBudget(tmp_path)
    budget.reserve()
    now[0] += 60
    budget.reserve()
    now[0] += 60
    calls: list[JsonObject] = []

    def send(request: JsonObject, key: str) -> JsonObject:
        calls.append(request)
        raise GenerationError("GENERATION_TIMEOUT")

    def sleep(seconds: float) -> None:
        assert seconds == 60
        now[0] += seconds

    generator = GeminiDialogue(
        "offline-test-key",
        budget,
        free_tier_confirmed=True,
        free_data_use_confirmed=True,
        send=send,
        sleep=sleep,
    )
    with pytest.raises(GenerationError, match="GENERATION_TIMEOUT"):
        generator.generate(harbor_brief())
    ledger = object_value(decode_json((tmp_path / "budget.json").read_bytes()))
    assert len(calls) == 2
    assert (ledger["attempts"], ledger["tokens"]) == (4, 80000)


def test_transport_oversize_closes_owned_response_and_no_ambient_proxy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = io.BytesIO(b"x" * (MAX_NETWORK + 1))
    handlers: list[object] = []

    class Opener:
        def open(self, request: Request, timeout: int) -> io.BytesIO:
            assert timeout == 30 and "key=" not in request.full_url
            return source

    def build(*values: object) -> Opener:
        handlers.extend(values)
        return Opener()

    monkeypatch.setattr("adapters.gemini_transport.build_opener", build)
    with pytest.raises(GenerationError, match="GENERATION_OUTPUT"):
        fetch(
            canonical_json(
                {"key": "offline-test-key", "request": generation_request(harbor_brief())}
            )
        )
    assert source.closed
    assert getattr(handlers[0], "proxies") == {}
    assert isinstance(handlers[1], NoRedirect)


def test_live_requires_key_and_explicit_free_ack_without_quota(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert (
        main(
            [
                "--live",
                "--free-tier-confirmed",
                "--free-data-use-confirmed",
                "--output",
                str(tmp_path / "candidate.json"),
                "--profile",
                str(tmp_path / "profile"),
            ]
        )
        == 1
    )
    assert "GENERATION_KEY_MISSING" in capsys.readouterr().err
    assert not (tmp_path / "profile").exists()


def test_dns_or_read_deadline_kills_and_reaps_owned_child(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess
    import sys
    from adapters.gemini_dialogue import transport

    original = subprocess.Popen
    children: list[subprocess.Popen[bytes]] = []

    def spawn(argv: object, **kwargs: object) -> subprocess.Popen[bytes]:
        child = original(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        children.append(child)
        return child

    monkeypatch.setattr("adapters.gemini_dialogue.subprocess.Popen", spawn)
    with pytest.raises(GenerationError, match="GENERATION_TIMEOUT"):
        transport(generation_request(harbor_brief()), "offline-test-key", deadline=0.1)
    assert len(children) == 1 and children[0].poll() is not None


def test_slow_reads_close_response_at_deadline(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = [0.0]
    source = io.BytesIO(b"{}")

    class Opener:
        def open(self, request: Request, timeout: int) -> io.BytesIO:
            clock[0] = 61
            return source

    monkeypatch.setattr("adapters.gemini_transport.time.monotonic", lambda: clock[0])
    monkeypatch.setattr("adapters.gemini_transport.build_opener", lambda *args: Opener())
    with pytest.raises(GenerationError, match="GENERATION_TIMEOUT"):
        fetch(
            canonical_json(
                {"key": "offline-test-key", "request": generation_request(harbor_brief())}
            )
        )
    assert source.closed
