"""Private-pipe engine prototype;all gameplay still runs through ClientWorker."""

from __future__ import annotations

import argparse
from dataclasses import asdict, fields
import hashlib
import logging
from pathlib import Path
import re
import sys
from typing import IO, Sequence, cast

from adapters.narrative_catalog import load_catalog
from app.client_worker import ClientWorker
from app.scenarios import select_scenario
from app.quest import client_quest
from contracts.dialogue import QuestContent
from domain.scenario import LEGACY, Scenario
from contracts.client import ClientRequest, ClientUpdate, ClientView
from contracts.narratives import NARRATIVE_CATEGORIES, Narrative
from domain.canonical import JsonObject, JsonValue, canonical_json, decode_json, exact_fields, seal

MAX_FRAME = 1024 * 1024
MAX_REQUEST = 16 * 1024
REQUEST_FIELDS = ("kind", "version", "request_id", "attachment_id", "request", "seconds", "slot_id")
REQUEST_NAMES = (
    "attach",
    "up",
    "down",
    "left",
    "right",
    "open",
    "close",
    "attack",
    "rest",
    "wait",
    "bell",
    "talk",
    "memory",
    "memory_recent",
    "activity",
    "slot_inspect",
    "slot_previous_inspect",
    "save",
    "load",
    "load_previous",
    "retry",
    "recover",
    "quit",
)
VIEW_FIELDS = tuple((f.name, str(f.type)) for f in fields(ClientView))
UPDATE_FIELDS = tuple((f.name, str(f.type)) for f in fields(ClientUpdate))
NARRATIVE_FIELDS = tuple((f.name, str(f.type)) for f in fields(Narrative))
RESPONSE_FIELDS = (
    ("kind", "str"),
    ("version", "str"),
    ("schema_hash", "str"),
    ("request_id", "str"),
    ("error", "str"),
    ("update", "ClientUpdate"),
    ("has_view", "bool"),
    ("narratives", "tuple[Narrative, ...]"),
)


def schema_fingerprint(
    update_fields: tuple[tuple[str, str], ...] = UPDATE_FIELDS,
    response_fields: tuple[tuple[str, str], ...] = RESPONSE_FIELDS,
) -> str:
    return hashlib.sha256(
        canonical_json(
            seal(
                {
                    "protocol": "engine-pipe/v1",
                    "request_fields": REQUEST_FIELDS,
                    "requests": REQUEST_NAMES,
                    "view_fields": VIEW_FIELDS,
                    "update_fields": update_fields,
                    "narrative_fields": NARRATIVE_FIELDS,
                    "narrative_categories": NARRATIVE_CATEGORIES,
                    "response_fields": response_fields,
                }
            )
        )
    ).hexdigest()


SCHEMA_HASH = schema_fingerprint()


def read_exact(source: IO[bytes], length: int) -> bytes:
    data = bytearray()
    while len(data) < length:
        chunk = source.read(length - len(data))
        if not chunk:
            raise EOFError("TRUNCATED_FRAME")
        data.extend(chunk)
    return bytes(data)


def read_frame(source: IO[bytes]) -> bytes | None:
    first = source.read(1)
    if not first:
        return None
    header = first + read_exact(source, 3)
    length = int.from_bytes(header, "big")
    if not 1 <= length <= MAX_REQUEST:
        raise ValueError("FRAME_LENGTH")
    return read_exact(source, length)


def write_frame(target: IO[bytes], document: JsonObject) -> None:
    body = canonical_json(document)
    if not 1 <= len(body) <= MAX_FRAME:
        raise ValueError("RESPONSE_CAPACITY")
    target.write(len(body).to_bytes(4, "big") + body)
    target.flush()


def decimal(value: JsonValue, minimum: int, maximum: int) -> int:
    if type(value) is not str or re.fullmatch(r"0|[1-9][0-9]{0,18}", value) is None:
        raise ValueError("WIRE_INTEGER")
    result = int(value)
    if not minimum <= result <= maximum:
        raise ValueError("WIRE_INTEGER_RANGE")
    return result


def wire(value: object) -> JsonValue:
    """Only declared DTO leaves;never expose a WorldState or private NPC data."""
    if type(value) is int:
        return str(value)
    if type(value) is bool or type(value) is str or value is None:
        return seal(value)
    if isinstance(value, (tuple, list)):
        return tuple(wire(v) for v in cast(tuple[object, ...] | list[object], value))
    if isinstance(value, dict):
        return seal({k: wire(v) for k, v in cast(dict[str, object], value).items()})
    raise ValueError("WIRE_TYPE")


class EngineBridge:
    def __init__(
        self,
        path: Path,
        narratives: tuple[Narrative, ...],
        layout: Scenario = LEGACY,
        *,
        quest_content: QuestContent | None = None,
        npc_memory: bool = False,
        npc_work: bool = False,
    ) -> None:
        self.worker = ClientWorker(
            path, layout, quest_content=quest_content, npc_memory=npc_memory, npc_work=npc_work
        )
        self.narratives = narratives
        self.last = self.worker.request("attach").result()
        self.highest_request = 0

    def response(self, request_id: str, *, error: str = "") -> JsonObject:
        update = cast(JsonObject, wire(asdict(self.last)))
        return {
            "kind": "update",
            "version": "1",
            "schema_hash": SCHEMA_HASH,
            "request_id": request_id,
            "error": error,
            "update": update,
            "has_view": self.last.view is not None,
            "narratives": tuple(wire(asdict(n)) for n in self.narratives),
        }

    def request(self, body: bytes) -> tuple[JsonObject, bool]:
        d = exact_fields(decode_json(body), REQUEST_FIELDS)
        sequence = decimal(d["request_id"], 1, 2**63 - 1)
        seconds = decimal(d["seconds"], 0, 16)
        if (
            d["kind"] != "request"
            or d["version"] != "1"
            or type(d["request"]) is not str
            or d["request"] not in REQUEST_NAMES
            or type(d["slot_id"]) is not str
            or re.fullmatch(r"slot0[1-8]", d["slot_id"]) is None
            or type(d["attachment_id"]) is not str
        ):
            raise ValueError("REQUEST_SCHEMA")
        request_id = str(sequence)
        if sequence <= self.highest_request:
            return self.response(request_id, error="STALE_REQUEST"), False
        if d["attachment_id"] != self.last.attachment_id:
            if not (
                self.highest_request == 0 and d["request"] == "attach" and d["attachment_id"] == ""
            ):
                return self.response(request_id, error="STALE_ATTACHMENT"), False
        self.highest_request = sequence
        if d["request"] == "quit":
            return self.response(request_id), True
        if d["request"] == "memory":
            pending = self.worker.inspect_memory()
        elif d["request"] == "memory_recent":
            pending = self.worker.inspect_recent_memory()
        elif d["request"] == "activity":
            pending = self.worker.inspect_activity()
        elif d["request"] == "slot_inspect":
            pending = self.worker.inspect_slot(d["slot_id"])
        elif d["request"] == "slot_previous_inspect":
            pending = self.worker.inspect_previous_slot(d["slot_id"])
        else:
            pending = self.worker.request(
                cast(ClientRequest, d["request"]), seconds=seconds, slot_id=d["slot_id"]
            )
        self.last = pending.result()
        return self.response(request_id), False

    def close(self) -> None:
        self.worker.join()


def serve(
    source: IO[bytes],
    target: IO[bytes],
    path: Path,
    narratives: tuple[Narrative, ...],
    layout: Scenario = LEGACY,
    *,
    quest_content: QuestContent | None = None,
    npc_memory: bool = False,
    npc_work: bool = False,
) -> int:
    bridge = EngineBridge(
        path,
        narratives,
        layout,
        quest_content=quest_content,
        npc_memory=npc_memory,
        npc_work=npc_work,
    )
    try:
        write_frame(target, bridge.response("0"))
        while (body := read_frame(source)) is not None:
            try:
                response, quit_requested = bridge.request(body)
            except (ValueError, KeyError, TypeError, UnicodeError, RecursionError):
                write_frame(target, bridge.response("0", error="INVALID_REQUEST"))
                continue
            write_frame(target, response)
            if quit_requested:
                break
    finally:
        bridge.close()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--working", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--catalog-sha256", required=True)
    parser.add_argument("--scenario", default="legacy")
    parser.add_argument("--quest-catalog", type=Path)
    parser.add_argument("--quest-sha256")
    parser.add_argument("--npc-memory", action="store_true")
    parser.add_argument("--npc-work", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(stream=sys.stderr)
    try:
        narratives = load_catalog(args.catalog, args.catalog_sha256)
        try:
            choice = select_scenario(args.scenario)
        except ValueError as error:
            raise ValueError("UNKNOWN_SCENARIO") from error
        if choice.narrative_id and not any(
            n.entry_id == choice.narrative_id and n.category == "settlement" for n in narratives
        ):
            raise ValueError("SCENARIO_NARRATIVE")
        content = client_quest(choice.layout, args.quest_catalog, args.quest_sha256)
        return serve(
            sys.stdin.buffer,
            sys.stdout.buffer,
            args.working,
            narratives,
            choice.layout,
            quest_content=content,
            npc_memory=args.npc_memory,
            npc_work=args.npc_work,
        )
    except (OSError, ValueError, EOFError) as error:
        logging.getLogger(__name__).error("engine pipe unavailable: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
