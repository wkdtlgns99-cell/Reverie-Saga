"""Owned subprocess transport;fixed origin,no proxies/redirects,no credential diagnostics."""

from __future__ import annotations

import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from typing import IO

from contracts.dialogue import GenerationError
from domain.canonical import (
    JsonObject,
    canonical_json,
    decode_json,
    exact_fields,
    object_value,
    text_value,
)

ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"
)
MAX_NETWORK = 256 * 1024


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, req: Request, fp: IO[bytes], code: int, msg: str, headers: object, newurl: str
    ) -> None:
        raise GenerationError("GENERATION_REDIRECT")


def fetch(body: bytes) -> bytes:
    request_data = exact_fields(decode_json(body), ("key", "request"))
    key = text_value(request_data["key"])
    request = Request(
        ENDPOINT,
        data=canonical_json(request_data["request"]),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    opener = build_opener(ProxyHandler({}), NoRedirect())
    deadline = time.monotonic() + 60
    try:
        with opener.open(request, timeout=30) as source:
            result = bytearray()
            while True:
                if time.monotonic() >= deadline:
                    raise GenerationError("GENERATION_TIMEOUT")
                chunk = source.read(min(8192, MAX_NETWORK + 1 - len(result)))
                if not chunk:
                    return bytes(result)
                result.extend(chunk)
                if len(result) > MAX_NETWORK:
                    raise GenerationError("GENERATION_OUTPUT")
    except HTTPError as error:
        error.close()
        if error.code == 429:
            code = "GENERATION_DEFERRED"
        elif error.code in (401, 403):
            code = "GENERATION_AUTH"
        elif error.code in (500, 502, 503, 504):
            code = "GENERATION_TRANSIENT"
        else:
            code = "GENERATION_REJECTED"
        raise GenerationError(code) from None
    except (URLError, TimeoutError, OSError):
        raise GenerationError("GENERATION_TIMEOUT") from None


def main() -> int:
    document: JsonObject
    try:
        data = sys.stdin.buffer.read(16385)
        if len(data) > 16384:
            raise GenerationError("GENERATION_INPUT")
        result = fetch(data)
        document = {"status": "OK", "response": object_value(decode_json(result))}
    except (ValueError, UnicodeError, RecursionError) as error:
        code = error.code if isinstance(error, GenerationError) else "GENERATION_OUTPUT"
        document = {"status": code, "response": None}
    sys.stdout.buffer.write(canonical_json(document))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
