"""One read-only, player-facing view of the committed knowledge world."""

import argparse
from collections.abc import Sequence
from pathlib import Path
import sqlite3
import sys

from adapters.world_attachment import current_world
from app.world_catalog import (
    AUTHORED_SUPPLY_SCENARIO,
    KNOWLEDGE_WORLD_PATH,
    load_social,
    load_transport,
    load_world,
)
from app.world_supply import supply_status
from app.world_transport_registry import transport_world_bundle
from app.world_village_session import validate_knowledge_world
from contracts.persistence import DurableCheckpoint, SaveError
from domain.canonical import JsonObject, canonical_json
from domain.world import WorldCatalog
from domain.world_conversation import ConversationRecord
from domain.world_population import InventoryRecord, SettlementRecord
from domain.world_supply import REPAIR_CRATES, SupplyRecord, blocked, supply_item
from domain.world_transport import JourneyRecord
from domain.world_travel import TravelerRecord

FORMAT = "reverie-world-observer/v1"
TRANSCRIPT_LIMIT = 8


def _project(checkpoint: DurableCheckpoint, world: WorldCatalog) -> JsonObject:
    core = checkpoint.core
    tick = core.tick
    travel = next(c.state for c in core.components if isinstance(c, TravelerRecord))
    journey = next(c.state for c in core.components if isinstance(c, JourneyRecord))
    history = next(c.state for c in core.components if isinstance(c, ConversationRecord))
    place = world.place(travel.place_id)
    moving = bool(travel.destination_id) or journey.phase != "idle"
    local = next(
        c.state
        for c in core.components
        if isinstance(c, SettlementRecord) and c.entity_id == place.id
    )
    residents = () if local is None or moving else local.residents
    scenario = AUTHORED_SUPPLY_SCENARIO
    city = next(
        c.state
        for c in core.components
        if isinstance(c, SupplyRecord) and c.entity_id == scenario.place_id
    )
    inventory = next(c.state for c in core.components if isinstance(c, InventoryRecord))
    local_quest = not moving and place.id == scenario.place_id
    if local_quest:
        phase = (
            "진행 중"
            if city.stage == 1
            else "완료"
            if city.stage == 2
            else "기한 종료"
            if city.stage == 3
            else "미수락"
            if blocked(scenario, place.id, city, tick)
            else "대기"
        )
        quest = supply_status(city, scenario, place.id, tick, authored=True)
    else:
        phase = "지역 밖"
        quest = "의뢰 지역에 도착하면 보급 상태를 볼 수 있습니다."
    return {
        "format": FORMAT,
        "tick": tick,
        "revision": checkpoint.protocol.revision,
        "location": f"{place.name} 출발 · 이동 중" if moving else place.name,
        "quest_location": world.place(scenario.place_id).name,
        "quest_phase": phase,
        "quest_status": quest,
        "cargo": dict(inventory.items).get(supply_item(scenario.place_id), 0),
        "cargo_required": REPAIR_CRATES,
        "resolved_tick": city.resolved_tick if local_quest else 0,
        "residents": tuple(
            {
                "id": resident.id,
                "name": resident.name,
                "role": resident.occupation,
                "exchanges": tuple(
                    {
                        "tick": entry.player_end,
                        "player": entry.player_text,
                        "reply": entry.reply_text if entry.reply_end <= tick else "",
                    }
                    for entry in tuple(
                        e
                        for e in history.exchanges
                        if e.npc_id == resident.id and e.player_end <= tick
                    )[-TRANSCRIPT_LIMIT:]
                ),
            }
            for resident in residents
        ),
    }


def read_world(working: Path = KNOWLEDGE_WORLD_PATH) -> JsonObject:
    source = current_world(working)
    world = load_world()
    bundle = transport_world_bundle(
        world, load_social(world), load_transport(world), AUTHORED_SUPPLY_SCENARIO, knowledge=True
    )
    try:
        checkpoint = validate_knowledge_world(source, bundle, AUTHORED_SUPPLY_SCENARIO.place_id)
    except SaveError as error:
        cause = error.__cause__
        if isinstance(cause, sqlite3.Error) and getattr(cause, "sqlite_errorcode", None) in (
            sqlite3.SQLITE_BUSY,
            sqlite3.SQLITE_LOCKED,
        ):
            raise SaveError(
                "WORLD_VIEW_BUSY", "refresh when the working save is available"
            ) from error
        raise
    if current_world(working) != source:
        raise SaveError("WORLD_VIEW_CHANGED", "active working branch changed")
    return _project(checkpoint, world)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--working", type=Path, default=KNOWLEDGE_WORLD_PATH)
    args = parser.parse_args(argv)
    try:
        document = canonical_json(read_world(args.working))
    except SaveError as error:
        print(error.code, file=sys.stderr)
        return 2
    except (OSError, ValueError, TypeError):
        print("WORLD_VIEW_UNAVAILABLE", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(document + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
