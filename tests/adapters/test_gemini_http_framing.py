from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from http.client import IncompleteRead
import io
import socket
import subprocess
import sys
from urllib.request import Request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from adapters.gemini_dialogue import GeminiDialogue
from adapters.gemini_transport import fetch
from adapters.generation_budget import GenerationBudget
from app.dialogue_prepare import harbor_brief
from contracts.dialogue import GenerationError
from domain.canonical import JsonObject, canonical_json, decode_json, object_value
from tests.adapters.test_gemini_dialogue import response

FAULTS = (
    b"not-http offline-secret\r\n\r\n",
    b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n10\r\nshort",
)


@contextmanager
def http_replies(*replies: bytes) -> Iterator[str]:
    with socket.socket() as server, ThreadPoolExecutor(max_workers=1) as executor:
        server.bind(("127.0.0.1", 0))
        server.listen()
        server.settimeout(10)

        def serve() -> None:
            for reply in replies:
                with server.accept()[0] as connection:
                    connection.settimeout(10)
                    request = bytearray()
                    while b"\r\n\r\n" not in request:
                        chunk = connection.recv(8192)
                        if not chunk:
                            raise RuntimeError("request headers incomplete")
                        request.extend(chunk)
                    headers, body = bytes(request).split(b"\r\n\r\n", 1)
                    length = next(
                        int(line.split(b":", 1)[1])
                        for line in headers.split(b"\r\n")
                        if line.lower().startswith(b"content-length:")
                    )
                    while len(body) < length:
                        chunk = connection.recv(8192)
                        if not chunk:
                            raise RuntimeError("request body incomplete")
                        body += chunk
                    connection.sendall(reply)

        pending = executor.submit(serve)
        try:
            yield f"http://127.0.0.1:{server.getsockname()[1]}/"
        finally:
            pending.result(timeout=15)


@pytest.mark.parametrize("fault", FAULTS, ids=("bad-status", "incomplete-chunk"))
def test_malformed_http_is_sanitized_transient(
    monkeypatch: pytest.MonkeyPatch, fault: bytes
) -> None:
    with http_replies(fault) as endpoint:
        monkeypatch.setattr("adapters.gemini_transport.ENDPOINT", endpoint)
        with pytest.raises(GenerationError) as caught:
            fetch(canonical_json({"key": "offline-secret", "request": {}}))
    assert caught.value.code == "GENERATION_TRANSIENT"
    assert str(caught.value) == "GENERATION_TRANSIENT"
    assert caught.value.__suppress_context__


@pytest.mark.parametrize("fault", FAULTS, ids=("bad-status", "incomplete-chunk"))
def test_real_child_framing_failure_reaches_parent_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: bytes
) -> None:
    body = canonical_json(response())
    success = b"HTTP/1.1 200 OK\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body
    original = subprocess.Popen
    children: list[subprocess.Popen[bytes]] = []
    clock = [1791849600.0]
    monkeypatch.setattr("adapters.generation_budget.time.time", lambda: clock[0])

    with http_replies(fault, success) as endpoint:

        def spawn(*args: object, **kwargs: object) -> subprocess.Popen[bytes]:
            child = original(
                [
                    sys.executable,
                    "-c",
                    "import adapters.gemini_transport as m; m.ENDPOINT="
                    + repr(endpoint)
                    + "; raise SystemExit(m.main())",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            children.append(child)
            return child

        def sleep(seconds: float) -> None:
            assert seconds == 60
            clock[0] += seconds

        monkeypatch.setattr("adapters.gemini_dialogue.subprocess.Popen", spawn)
        generated = GeminiDialogue(
            "offline-secret",
            GenerationBudget(tmp_path),
            free_tier_confirmed=True,
            free_data_use_confirmed=True,
            sleep=sleep,
        ).generate(harbor_brief())

    assert generated.total_tokens == 260
    assert len(children) == 2
    assert all(child.returncode == 0 for child in children)
    ledger = object_value(decode_json((tmp_path / "budget.json").read_bytes()))
    assert (ledger["attempts"], ledger["tokens"], ledger["settled"]) == (2, 20260, (2,))


def test_framing_retry_remains_bounded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clock = [1791849600.0]
    monkeypatch.setattr("adapters.generation_budget.time.time", lambda: clock[0])
    calls: list[JsonObject] = []

    with http_replies(*FAULTS) as endpoint:
        monkeypatch.setattr("adapters.gemini_transport.ENDPOINT", endpoint)

        def send(request: JsonObject, key: str) -> JsonObject:
            calls.append(request)
            return object_value(
                decode_json(fetch(canonical_json({"key": key, "request": request})))
            )

        def sleep(seconds: float) -> None:
            assert seconds == 60
            clock[0] += seconds

        with pytest.raises(GenerationError, match="^GENERATION_TRANSIENT$"):
            GeminiDialogue(
                "offline-secret",
                GenerationBudget(tmp_path),
                free_tier_confirmed=True,
                free_data_use_confirmed=True,
                send=send,
                sleep=sleep,
            ).generate(harbor_brief())

    assert len(calls) == 2
    ledger = object_value(decode_json((tmp_path / "budget.json").read_bytes()))
    assert (ledger["attempts"], ledger["tokens"], ledger["settled"]) == (2, 40000, ())


@pytest.mark.parametrize(
    "status,code",
    (
        (429, "GENERATION_DEFERRED"),
        (401, "GENERATION_AUTH"),
        (403, "GENERATION_AUTH"),
        (500, "GENERATION_TRANSIENT"),
        (502, "GENERATION_TRANSIENT"),
        (503, "GENERATION_TRANSIENT"),
        (504, "GENERATION_TRANSIENT"),
        (404, "GENERATION_REJECTED"),
    ),
)
def test_http_status_classification_is_preserved(
    monkeypatch: pytest.MonkeyPatch, status: int, code: str
) -> None:
    reply = f"HTTP/1.1 {status} Test\r\nContent-Length: 0\r\n\r\n".encode()
    with http_replies(reply) as endpoint:
        monkeypatch.setattr("adapters.gemini_transport.ENDPOINT", endpoint)
        with pytest.raises(GenerationError) as caught:
            fetch(canonical_json({"key": "offline-secret", "request": {}}))
    assert caught.value.code == code


@pytest.mark.parametrize("interrupt", (False, True))
def test_owned_response_closes_and_process_control_propagates(
    monkeypatch: pytest.MonkeyPatch, interrupt: bool
) -> None:
    class Source(io.BytesIO):
        def read(self, size: int | None = -1) -> bytes:
            if interrupt:
                raise KeyboardInterrupt
            raise IncompleteRead(b"offline-secret")

    source = Source()

    class Opener:
        def open(self, request: Request, timeout: int) -> Source:
            return source

    monkeypatch.setattr("adapters.gemini_transport.build_opener", lambda *args: Opener())
    expected = KeyboardInterrupt if interrupt else GenerationError
    with pytest.raises(expected):
        fetch(canonical_json({"key": "offline-secret", "request": {}}))
    assert source.closed
