"""Private, ordered Unity requests against one durable knowledge-world attachment."""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
import logging
from pathlib import Path
import sys

from app.engine_bridge import read_frame, write_frame
from app.durable import DurableSession
from app.road_combat_trial import RoadCombatTrial
from app.world_catalog import (
    AUTHORED_SUPPLY_SCENARIO,
    KNOWLEDGE_WORLD_PATH,
    load_social,
    load_transport,
    load_world,
)
from app.world_session import world_command
from app.world_village_session import open_knowledge_world
from app.world_village_supply import VillageResident, VillageSupply, village_supply
from contracts.persistence import SaveError
from contracts.turn import TurnCommitted, TurnOutcome
from contracts.world_combat import CombatAction
from contracts.world_supply import SupplyAction
from contracts.world_time import WorldWait
from contracts.world_village import VillageStep
from domain.canonical import JsonObject, decode_json, exact_fields, int_value, text_value
from domain.primitives import MAX_INT
from domain.world_combat import BANDIT, BANDIT_POSITION, CombatRecord, CombatState
from domain.world_conversation import ConversationRecord
from domain.world_social import SocialCatalog
from domain.world_supply import SupplyScenario
from domain.world_transport import JourneyRecord
from domain.world_travel import WORLD_ACTOR, TravelerRecord
from domain.world_village import (
    DIRECTIONS,
    ENTRANCE,
    VILLAGE_LANDMARKS,
    VILLAGE_ROWS,
    VillagePosition,
    VillageRecord,
)

FORMAT = "reverie-world-village/v1"


@dataclass(frozen=True, slots=True)
class _Scene:
    position: VillagePosition
    local: bool
    speaking: bool
    tick: int
    combat: CombatState | None

    @property
    def available(self) -> bool:
        return self.local and not self.speaking

    @property
    def fighting(self) -> bool:
        return self.combat is not None and bool(self.combat.order)

    @property
    def ambush_due(self) -> bool:
        return self.available and self.combat is not None and self.combat.ambush_due(self.position)


class VillageBridge:
    def __init__(
        self, owner: DurableSession, scenario: SupplyScenario, social: SocialCatalog, name: str
    ) -> None:
        self.owner = owner
        self.scenario = scenario
        self.social = social
        self.name = name
        self._last: tuple[int, str, str, JsonObject] | None = None
        self._talking = ""
        self._trial: RoadCombatTrial | None = None

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
        scene = self._scene()
        if self._trial is not None:
            if action == "combat" and value:
                error = self._trial.act(value)
            elif action == "return" and not value:
                self.close()
            elif action != "inspect" or value:
                error = "VILLAGE_COMBAT_ACTIVE"
        elif action == "inspect" and not value and scene.ambush_due:
            error = self._submit(CombatAction("ambush"))
        elif scene.ambush_due:
            error = "VILLAGE_AMBUSH_PENDING"
        elif action == "world-combat" and scene.combat is not None and value != "ambush":
            error = self._submit(CombatAction(value))
            if not error:
                self._talking = ""
        elif scene.fighting and (action != "inspect" or value):
            error = "VILLAGE_COMBAT_ACTIVE"
        elif action == "road-test" and not value:
            if self._at_entrance(scene):
                self._trial = RoadCombatTrial()
                self._talking = ""
            else:
                error = "VILLAGE_ENTRANCE_REQUIRED"
        elif action == "step" and value in DIRECTIONS:
            error = self._submit(VillageStep(value))
            if not error:
                self._talking = ""
                if self._scene().ambush_due:
                    error = self._submit(CombatAction("ambush"))
        elif action == "idle" and value == "1":
            error = self._submit(WorldWait(1)) if scene.available else "VILLAGE_INACTIVE"
        elif action == "talk" and value:
            npc = self._nearby(scene, self._supply(), value)
            if npc is None:
                error = "VILLAGE_NPC_OUT_OF_REACH"
            else:
                self._talking = npc.resident.id
        elif action == "close" and not value:
            self._talking = ""
        elif action == "confirm" and value:
            error = self._confirm(value)
        elif action != "inspect" or value:
            error = "INVALID_COMMAND"
        result = self._view(request_id, error)
        self._last = (request_id, action, value, result)
        return result

    @staticmethod
    def _at_entrance(scene: _Scene) -> bool:
        return scene.available and scene.position == ENTRANCE

    def close(self) -> None:
        if self._trial is not None:
            self._trial.close()
            self._trial = None

    def _supply(self) -> VillageSupply:
        return village_supply(self.owner.snapshot(), self.scenario, self.social)

    @staticmethod
    def _nearby(scene: _Scene, supply: VillageSupply, target: str = "") -> VillageResident | None:
        if not scene.available:
            return None
        return next(
            (
                npc
                for npc in supply.residents
                if (not target or npc.resident.id == target) and npc.adjacent(scene.position)
            ),
            None,
        )

    def _confirm(self, token: str) -> str:
        if not self._talking:
            return "VILLAGE_OFFER_STALE"
        scene, supply = self._scene(), self._supply()
        npc = self._nearby(scene, supply, self._talking)
        if npc is None:
            return "VILLAGE_NPC_OUT_OF_REACH"
        offer = supply.offer
        if (
            offer is None
            or offer.action.npc_id != npc.resident.id
            or token != supply.interaction(npc, scene.position, self.owner.protocol())["token"]
        ):
            return "VILLAGE_OFFER_STALE"
        error = self._submit(offer.action)
        if not error:
            self._talking = ""
        return error

    def _submit(self, payload: VillageStep | WorldWait | SupplyAction | CombatAction) -> str:
        command = world_command(self.owner.protocol(), payload)
        outcome: TurnOutcome
        try:
            outcome = self.owner.submit(command, attachment_id=self.owner.attachment_id).outcome
        except SaveError as error:
            if error.code != "SAVE_UNCERTAIN":
                raise
            outcome = self.owner.recover().outcome
        return "" if isinstance(outcome, TurnCommitted) else outcome.failure.code

    def _scene(self) -> _Scene:
        core = self.owner.snapshot()
        position = next(item.state for item in core.components if isinstance(item, VillageRecord))
        travel = next(item.state for item in core.components if isinstance(item, TravelerRecord))
        journey = next(item.state for item in core.components if isinstance(item, JourneyRecord))
        speech = next(
            item.state for item in core.components if isinstance(item, ConversationRecord)
        )
        local = (
            travel.place_id == self.scenario.place_id
            and not travel.destination_id
            and journey.phase == "idle"
        )
        combat = next(
            (item.state for item in core.components if isinstance(item, CombatRecord)), None
        )
        return _Scene(position, local, bool(speech.remaining), core.tick, combat)

    @staticmethod
    def _combat(scene: _Scene, supply: VillageSupply) -> JsonObject | None:
        state = scene.combat
        if state is None or not scene.local:
            return None
        names = {
            WORLD_ACTOR: "나",
            BANDIT: "도적",
            **{npc.resident.id: npc.resident.occupation for npc in supply.residents},
        }
        return {
            "active": scene.fighting,
            "ambush_pending": scene.ambush_due,
            "player_turn": state.current == WORLD_ACTOR,
            "player_hp": state.player_hp,
            "bandit_hp": state.bandit_hp,
            "bandit_x": BANDIT_POSITION.x,
            "bandit_y": BANDIT_POSITION.y,
            "order": tuple(names[actor] for actor in state.order),
            "last_actor": names.get(state.last_actor, ""),
            "last_action": state.last_action,
        }

    def _view(self, request_id: int, error: str) -> JsonObject:
        scene = self._scene()
        supply = self._supply()
        protocol = self.owner.protocol()
        nearby = self._nearby(scene, supply)
        talking = self._nearby(scene, supply, self._talking) if self._talking else None
        return {
            "format": FORMAT,
            "id": request_id,
            "error": error,
            "name": self.name,
            "available": scene.available
            and self._trial is None
            and not (scene.fighting or scene.ambush_due),
            "status": (
                "이 마을에 도착하면 걸을 수 있습니다."
                if not scene.local
                else "진행 중인 발언을 Python 화면에서 먼저 마쳐 주세요."
                if scene.speaking
                else ""
            ),
            "tick": scene.tick,
            "revision": protocol.revision,
            "x": scene.position.x,
            "y": scene.position.y,
            "entrance_x": ENTRANCE.x,
            "entrance_y": ENTRANCE.y,
            "rows": VILLAGE_ROWS,
            "landmarks": tuple(
                {"name": name, "x": x, "y": y} for _, name, x, y in VILLAGE_LANDMARKS
            ),
            "supply": supply.wire(local=scene.local),
            "nearby": nearby.resident.id if nearby is not None else "",
            "has_interaction": talking is not None,
            "interaction": (
                supply.interaction(talking, scene.position, protocol)
                if talking is not None
                else None
            ),
            "can_start_road_test": self._trial is None
            and not scene.fighting
            and self._at_entrance(scene),
            "has_road_test": self._trial is not None,
            "road_test": self._trial.wire() if self._trial is not None else None,
            "has_world_combat": scene.combat is not None and scene.local,
            "world_combat": self._combat(scene, supply),
        }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--working", type=Path, default=KNOWLEDGE_WORLD_PATH)
    args = parser.parse_args(argv)
    try:
        world = load_world()
        scenario = AUTHORED_SUPPLY_SCENARIO
        social = load_social(world)
        with open_knowledge_world(
            args.working, world, scenario, social, load_transport(world), combat=True
        ) as owner:
            bridge = VillageBridge(owner, scenario, social, world.place(scenario.place_id).name)
            try:
                while (frame := read_frame(sys.stdin.buffer)) is not None:
                    write_frame(sys.stdout.buffer, bridge.request(frame))
            finally:
                bridge.close()
    except SaveError as error:
        print(error.code, file=sys.stderr)
        return 2
    except (EOFError, OSError, ValueError, TypeError):
        logging.getLogger(__name__).exception("Village bridge failed")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
