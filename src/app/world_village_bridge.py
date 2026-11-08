"""Private, ordered Unity requests against one durable knowledge-world attachment."""

import argparse
from collections.abc import Sequence
import logging
from pathlib import Path
import sys

from app.engine_bridge import read_frame, write_frame
from app.durable import DurableSession
from app.world_catalog import (
    AUTHORED_SUPPLY_SCENARIO,
    KNOWLEDGE_WORLD_PATH,
    load_social,
    load_transport,
    load_world,
)
from app.world_session import world_command
from app.world_village_session import open_knowledge_world
from contracts.persistence import SaveError
from contracts.turn import TurnCommitted, TurnOutcome
from contracts.world_time import WorldWait
from contracts.world_village import VillageStep
from domain.canonical import JsonObject, decode_json, exact_fields, int_value, text_value
from domain.primitives import MAX_INT
from domain.world_conversation import ConversationRecord
from domain.world_transport import JourneyRecord
from domain.world_travel import TravelerRecord
from domain.world_village import (
    DIRECTIONS,
    ENTRANCE,
    VILLAGE_LANDMARKS,
    VILLAGE_ROWS,
    VillageRecord,
)

FORMAT = "reverie-world-village/v1"


class VillageBridge:
    def __init__(self, owner: DurableSession, place_id: str, name: str) -> None:
        self.owner = owner
        self.place_id = place_id
        self.name = name
        self._last: tuple[int, str, str, JsonObject] | None = None

    def request(self, body: bytes) -> JsonObject:
        row = exact_fields(decode_json(body), ("format", "id", "action", "value"))
        request_id = int_value(row["id"])
        action, value = text_value(row["action"]), text_value(row["value"])
        if row["format"] != FORMAT or not 1 <= request_id <= MAX_INT:
            raise ValueError("VILLAGE_REQUEST")
        last = self._last
        if last is not None and request_id <= last[0]:
            if (request_id, action, value) == last[:3]:
                return last[3]
            return self._view(request_id, "STALE_REQUEST")
        error = ""
        if action == "step" and value in DIRECTIONS:
            error = self._submit(VillageStep(value))
        elif action == "idle" and value == "1":
            current = self._view(request_id, "")
            error = (
                self._submit(WorldWait(1)) if current["available"] is True else "VILLAGE_INACTIVE"
            )
        elif action != "inspect" or value:
            error = "INVALID_COMMAND"
        result = self._view(request_id, error)
        self._last = (request_id, action, value, result)
        return result

    def _submit(self, payload: VillageStep | WorldWait) -> str:
        command = world_command(self.owner.protocol(), payload)
        outcome: TurnOutcome
        try:
            outcome = self.owner.submit(command, attachment_id=self.owner.attachment_id).outcome
        except SaveError as error:
            if error.code != "SAVE_UNCERTAIN":
                raise
            outcome = self.owner.recover().outcome
        return "" if isinstance(outcome, TurnCommitted) else outcome.failure.code

    def _view(self, request_id: int, error: str) -> JsonObject:
        core = self.owner.snapshot()
        position = next(item.state for item in core.components if isinstance(item, VillageRecord))
        travel = next(item.state for item in core.components if isinstance(item, TravelerRecord))
        journey = next(item.state for item in core.components if isinstance(item, JourneyRecord))
        speech = next(
            item.state for item in core.components if isinstance(item, ConversationRecord)
        )
        local = (
            travel.place_id == self.place_id
            and not travel.destination_id
            and journey.phase == "idle"
        )
        return {
            "format": FORMAT,
            "id": request_id,
            "error": error,
            "name": self.name,
            "available": local and not speech.remaining,
            "status": (
                "이 마을에 도착하면 걸을 수 있습니다."
                if not local
                else "진행 중인 발언을 Python 화면에서 먼저 마쳐 주세요."
                if speech.remaining
                else ""
            ),
            "tick": core.tick,
            "revision": self.owner.protocol().revision,
            "x": position.x,
            "y": position.y,
            "entrance_x": ENTRANCE.x,
            "entrance_y": ENTRANCE.y,
            "rows": VILLAGE_ROWS,
            "landmarks": tuple(
                {"name": name, "x": x, "y": y} for _, name, x, y in VILLAGE_LANDMARKS
            ),
        }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--working", type=Path, default=KNOWLEDGE_WORLD_PATH)
    args = parser.parse_args(argv)
    try:
        world = load_world()
        scenario = AUTHORED_SUPPLY_SCENARIO
        with open_knowledge_world(
            args.working, world, scenario, load_social(world), load_transport(world), village=True
        ) as owner:
            bridge = VillageBridge(owner, scenario.place_id, world.place(scenario.place_id).name)
            while (frame := read_frame(sys.stdin.buffer)) is not None:
                write_frame(sys.stdout.buffer, bridge.request(frame))
    except SaveError as error:
        print(error.code, file=sys.stderr)
        return 2
    except (EOFError, OSError, ValueError, TypeError):
        logging.getLogger(__name__).exception("Village bridge failed")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
