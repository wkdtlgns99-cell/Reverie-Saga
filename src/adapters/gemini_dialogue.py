"""Optional explicit preparation generator;the game never imports/calls this adapter."""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import replace
from typing import Callable

from adapters.generation_budget import GenerationBudget
from adapters.gemini_transport import MAX_NETWORK
from adapters.quest_dialogue import decode_candidate
from contracts.dialogue import (
    CANDIDATE_FORMAT,
    INTENTS,
    DialogueBrief,
    GeneratedDialogue,
    GenerationError,
)
from domain.canonical import (
    JsonObject,
    array_value,
    canonical_json,
    decode_json,
    exact_fields,
    int_value,
    object_value,
    seal,
    text_value,
)
from domain.primitives import require_integer

MODEL = "gemini-3.5-flash-lite"


def generation_request(brief: DialogueBrief) -> JsonObject:
    return object_value(
        seal(
            {
                "contents": ({"parts": ({"text": brief.text},)},),
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "maxOutputTokens": 2048,
                    "candidateCount": 1,
                    "thinkingConfig": {"thinkingLevel": "MINIMAL"},
                    "responseJsonSchema": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ("format", "quest_id", "npc_id", "lines"),
                        "properties": {
                            "format": {"type": "string", "enum": (CANDIDATE_FORMAT,)},
                            "quest_id": {"type": "string", "enum": ("quest:harbor-sentinel",)},
                            "npc_id": {"type": "string", "enum": ("actor:harbor-watcher",)},
                            "lines": {
                                "type": "array",
                                "minItems": 4,
                                "maxItems": 4,
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ("intent", "text_ko"),
                                    "properties": {
                                        "intent": {"type": "string", "enum": INTENTS},
                                        "text_ko": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                },
            }
        )
    )


def transport(request: JsonObject, key: str, *, deadline: float = 60) -> JsonObject:
    body = canonical_json({"key": key, "request": request})
    try:
        with subprocess.Popen(
            [sys.executable, "-m", "adapters.gemini_transport"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as child:
            try:
                stdout, _stderr = child.communicate(body, timeout=deadline)
            except BaseException:
                child.kill()
                child.communicate()
                raise
            if child.returncode != 0 or len(stdout) > MAX_NETWORK + 4096:
                raise GenerationError("GENERATION_OUTPUT")
    except subprocess.TimeoutExpired:
        raise GenerationError("GENERATION_TIMEOUT") from None
    except OSError:
        raise GenerationError("GENERATION_TRANSPORT") from None
    try:
        data = exact_fields(decode_json(stdout), ("status", "response"))
        status = text_value(data["status"])
        if status != "OK":
            if status not in {
                "GENERATION_TIMEOUT",
                "GENERATION_TRANSIENT",
                "GENERATION_REDIRECT",
                "GENERATION_OUTPUT",
                "GENERATION_AUTH",
                "GENERATION_REJECTED",
                "GENERATION_DEFERRED",
                "GENERATION_INPUT",
            }:
                raise GenerationError("GENERATION_OUTPUT")
            raise GenerationError(status)
        return object_value(data["response"])
    except (ValueError, UnicodeError, RecursionError) as error:
        if isinstance(error, GenerationError):
            raise
        raise GenerationError("GENERATION_OUTPUT") from None


def parse_response(response: JsonObject) -> GeneratedDialogue:
    try:
        candidates = array_value(response["candidates"])
        if len(candidates) != 1:
            raise ValueError("candidate count")
        candidate = object_value(candidates[0])
        if candidate["finishReason"] != "STOP":
            raise ValueError("non-STOP")
        parts = array_value(object_value(candidate["content"])["parts"])
        text_parts = []
        for value in parts:
            part = object_value(value)
            if (
                set(part) - {"text", "thought", "thoughtSignature"}
                or part.get("thought", False) is not False
            ):
                raise ValueError("nontext/thought output")
            text_parts.append(text_value(part["text"]))
        body = "".join(text_parts).encode("utf-8")
        decode_candidate(body)
        usage = object_value(response.get("usageMetadata", {}))
        counts: list[int | None] = []
        for name in (
            "promptTokenCount",
            "candidatesTokenCount",
            "thoughtsTokenCount",
            "totalTokenCount",
        ):
            value = usage.get(name)
            count = None if value is None else int_value(value)
            if count is not None:
                require_integer(count)
            counts.append(count)
        return GeneratedDialogue(
            body,
            text_value(response.get("modelVersion", MODEL)),
            counts[0],
            counts[1],
            counts[2],
            counts[3],
        )
    except (ValueError, KeyError, UnicodeError, RecursionError):
        raise GenerationError("GENERATION_OUTPUT") from None


class GeminiDialogue:
    def __init__(
        self,
        key: str,
        budget: GenerationBudget,
        *,
        free_tier_confirmed: bool,
        free_data_use_confirmed: bool,
        send: Callable[[JsonObject, str], JsonObject] = transport,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if type(free_tier_confirmed) is not bool or not free_tier_confirmed:
            raise GenerationError("GENERATION_TIER_UNVERIFIED")
        if type(free_data_use_confirmed) is not bool or not free_data_use_confirmed:
            raise GenerationError("GENERATION_DATA_USE_UNCONFIRMED")
        if (
            type(key) is not str
            or not 1 <= len(key) <= 512
            or any(ord(char) <= 32 or ord(char) >= 127 for char in key)
        ):
            raise GenerationError("GENERATION_KEY_MISSING")
        self._key, self._budget, self._send, self._sleep = key, budget, send, sleep

    def generate(self, brief: DialogueBrief) -> GeneratedDialogue:
        if type(brief) is not DialogueBrief:
            raise GenerationError("GENERATION_INPUT")
        request = generation_request(brief)
        initial_error: GenerationError | None = None
        for attempt in range(2):
            try:
                reservation = self._budget.reserve()
            except GenerationError as error:
                if initial_error is not None:
                    # A local retry failure must not erase the provider/transport failure.
                    raise initial_error from error
                raise
            try:
                response = self._send(request, self._key)
            except GenerationError as error:
                if attempt == 0 and error.code in ("GENERATION_TIMEOUT", "GENERATION_TRANSIENT"):
                    initial_error = error
                    self._sleep(60)
                    continue
                raise
            # Account returned usage before validating text,including blocked/truncated results.
            try:
                usage = object_value(response.get("usageMetadata", {}))
                total = usage.get("totalTokenCount")
                actual = None if total is None else int_value(total)
                self._budget.reconcile(reservation, actual)
            except (ValueError, UnicodeError) as error:
                if isinstance(error, GenerationError):
                    raise
                raise GenerationError("GENERATION_OUTPUT") from None
            return replace(parse_response(response), attempts=attempt + 1)
        raise GenerationError("GENERATION_DEFERRED")
