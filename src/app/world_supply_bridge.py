"""Play the authored supply quest through a one-shot, confirmed Unity request."""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
import logging
from pathlib import Path
import re
import sys

from adapters.world_attachment import current_world
from app.world_catalog import (
    AUTHORED_SUPPLY_SCENARIO,
    KNOWLEDGE_WORLD_PATH,
    load_social,
    load_transport,
    load_world,
)
from app.world_supply import authored_supply_line
from app.world_worker import WorldUpdate, WorldWorker
from contracts.persistence import SaveError
from contracts.world_supply import SupplyAction
from domain.canonical import JsonObject, canonical_json, hash_document
from domain.world_supply import REPAIR_CRATES, supply_item

FORMAT = "reverie-world-supply/v1"
LABELS = {"accept": "의뢰 받기", "collect": "상자 받기", "deliver": "상자 전달하기"}


@dataclass(frozen=True, slots=True)
class _Offer:
    action: SupplyAction | None
    label: str
    line: str
    terms: str

    def wire(self, source: Path, update: WorldUpdate) -> JsonObject:
        action = self.action
        protocol = update.protocol
        token = hash_document(
            "world-supply-confirmation/v1",
            {
                "format": FORMAT,
                "source": str(source),
                "branch": protocol.branch_id,
                "revision": protocol.revision,
                "core": protocol.receipts[-1].receipt.core_hash if protocol.receipts else "",
                "action": (
                    (action.operation, action.place_id, action.npc_id) if action else ("wait",)
                ),
                "terms": self.terms,
            },
        )
        return {"token": token, "label": self.label, "line": self.line, "terms": self.terms}


def _offer(update: WorldUpdate) -> _Offer | None:
    scenario = AUTHORED_SUPPLY_SCENARIO
    if (
        update.state.place_id != scenario.place_id
        or update.state.destination_id
        or (update.journey is not None and update.journey.phase != "idle")
        or (update.conversation is not None and update.conversation.remaining)
    ):
        return None
    if update.offers:
        (offer,) = update.offers
        return _Offer(
            offer.action, LABELS[offer.action.operation], authored_supply_line(offer), offer.summary
        )
    if update.tick < scenario.start_tick:
        return _Offer(
            None,
            "1초 기다리기",
            "잠시 기다리면 상인의 보급 의뢰가 열립니다.",
            "게임 시간 1초가 흐릅니다.",
        )
    return None


def exchange(working: Path, confirm: str | None = None) -> JsonObject:
    if confirm is not None and re.fullmatch(r"[0-9a-f]{64}", confirm) is None:
        raise SaveError("WORLD_SUPPLY_CONFIRMATION_INVALID", "invalid confirmation")
    source = current_world(working)
    world = load_world()
    worker = WorldWorker(
        working,
        world,
        scenario=AUTHORED_SUPPLY_SCENARIO,
        social=load_social(world),
        transport=load_transport(world),
        authored_supply=True,
        live_npc=False,
        knowledge=True,
        require_existing=confirm is not None,
    )
    try:
        update = worker.request("inspect").result()
        if current_world(working) != source:
            raise SaveError("WORLD_VIEW_CHANGED", "active working branch changed")
        offer = _offer(update)
        proposed = offer.wire(source, update) if offer else None
        error = ""
        if confirm is not None:
            if offer is None or proposed is None or confirm != proposed["token"]:
                error = "WORLD_SUPPLY_STALE"
            else:
                before = update.protocol.revision
                update = (
                    worker.request("wait", seconds=1, request_key=confirm).result()
                    if offer.action is None
                    else worker.request("supply", supply=offer.action, request_key=confirm).result()
                )
                if update.protocol.revision == before:
                    error = "WORLD_SUPPLY_NOT_COMMITTED"
                offer = _offer(update)
                proposed = offer.wire(source, update) if offer else None
        return {
            "format": FORMAT,
            "tick": update.tick,
            "revision": update.protocol.revision,
            "location": world.place(update.state.place_id).name,
            "status": update.supply_text,
            "notice": (
                "진행 중인 발언을 Python 화면에서 먼저 마쳐 주세요."
                if update.conversation is not None and update.conversation.remaining
                else update.notice
            ),
            "cargo": dict(update.inventory.items).get(
                supply_item(AUTHORED_SUPPLY_SCENARIO.place_id), 0
            ),
            "cargo_required": REPAIR_CRATES,
            "gold": update.inventory.gold,
            "error": error,
            "has_offer": proposed is not None,
            "offer": proposed,
        }
    finally:
        worker.close()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--working", type=Path, default=KNOWLEDGE_WORLD_PATH)
    parser.add_argument("--confirm")
    args = parser.parse_args(argv)
    try:
        result = exchange(args.working, args.confirm)
    except SaveError as error:
        print(error.code, file=sys.stderr)
        return 2
    except (OSError, ValueError, TypeError):
        logging.getLogger(__name__).exception("Supply bridge failed")
        return 2
    sys.stdout.buffer.write(canonical_json(result) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
