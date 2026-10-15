"""Map player intent onto the existing authoritative durable game, without new rules."""

from __future__ import annotations

from app.scenarios import scenario_name
from domain.scenario import LEGACY, Scenario
from types import MappingProxyType

from pathlib import Path

from app.client_text import status_text, turn_messages
from app.durable import DurableSession, create_durable, resume_durable
from app.watch import WatchBootstrapSpec, bootstrap_watch
from app.watch_registry import watch_bundle
from app.quest import bootstrap_quest, harbor_definition
from app.quest_registry import quest_bundle
from app.npc_memory import bootstrap_memory, memory_bundle
from contracts.dialogue import QuestContent
from contracts.quest import QuestTalkCommand
from contracts.client import ClientAction, ClientUpdate, ClientView
from contracts.encounter import AttackCommand, InteractCommand, RestCommand
from contracts.messages import CommandPayload
from contracts.persistence import DurableCheckpoint
from contracts.trial import MoveCommand
from contracts.turn import GameCommand, TurnCommitted, TurnPublication
from contracts.watch import BellCommand, WaitCommand
from domain.encounter import (
    ATTACK_PROFILE_ID,
    GateRecord,
    HitPointsRecord,
    StaminaRecord,
)
from domain.primitives import CommandId, EntityId
from domain.state_types import ComponentRecord, CoreSnapshot
from domain.trial import CellPositionRecord, TrialMapRecord
from domain.watch import LanternRecord, ReplyRecord, WatchNpcRecord
from domain.quest import QuestRecord, reward_for
from domain.npc_memory import NpcQuestMemoryRecord


def _record[T: ComponentRecord](core: CoreSnapshot, kind: type[T], entity: EntityId) -> T:
    records = tuple(r for r in core.components if isinstance(r, kind) and r.entity_id == entity)
    if len(records) != 1:
        raise ValueError(f"client projection requires one {kind.__name__} for {entity}")
    return records[0]


def _payload(action: ClientAction, seconds: int, layout: Scenario = LEGACY) -> CommandPayload:
    match action:
        case "up":
            return MoveCommand(0, -1)
        case "down":
            return MoveCommand(0, 1)
        case "left":
            return MoveCommand(-1, 0)
        case "right":
            return MoveCommand(1, 0)
        case "open" | "close":
            return InteractCommand(layout.gate_id, action)
        case "attack":
            return AttackCommand(layout.enemy_id, ATTACK_PROFILE_ID)
        case "rest":
            return RestCommand()
        case "wait":
            return WaitCommand(seconds)
        case "bell":
            return BellCommand(layout.npc_id)
        case "talk":
            return QuestTalkCommand(layout.npc_id)
        case _:
            raise ValueError("UNKNOWN_CLIENT_ACTION")


class ClientSession:
    """All calls, including construction and close, belong to one owner thread."""

    def __init__(
        self,
        path: Path,
        layout: Scenario = LEGACY,
        *,
        quest_content: QuestContent | None = None,
        npc_memory: bool = False,
    ) -> None:
        if type(layout) is not Scenario:
            raise ValueError("SCENARIO_TYPE")
        self._layout = layout
        if quest_content is not None and (
            type(quest_content) is not QuestContent
            or quest_content.definition != harbor_definition()
            or layout != quest_content.definition.layout
        ):
            raise ValueError("QUEST_DEFINITION")
        self._quest_content = quest_content
        if type(npc_memory) is not bool or npc_memory and quest_content is None:
            raise ValueError("NPC_MEMORY_CONTENT")
        self._npc_memory = npc_memory
        self._names = MappingProxyType(
            {
                layout.actor_id: "플레이어",
                layout.enemy_id: "적",
                layout.npc_id: "NPC",
                layout.gate_id: "문",
            }
        )
        bundles = (
            watch_bundle(layout)
            if quest_content is None
            else memory_bundle(quest_content)
            if npc_memory
            else quest_bundle(quest_content),
        )
        if path.exists():
            self._owner = resume_durable(path, bundles=bundles)
        else:
            spec = WatchBootstrapSpec(
                "0" * 64, "0" * 32, "1" * 32, initial_cell=layout.initial_cell
            )
            initial = (
                bootstrap_watch(spec, layout=layout)
                if quest_content is None
                else bootstrap_memory(spec, quest_content)
                if npc_memory
                else bootstrap_quest(spec, quest_content)
            )
            self._owner = create_durable(
                path, DurableCheckpoint(initial.snapshot(), initial.protocol()), bundles=bundles
            )
        self._previous: tuple[GameCommand, str] | None = None

    @property
    def owner(self) -> DurableSession:
        """Authoritative API for boundary tests;renderers receive only derived updates."""
        return self._owner

    def update(
        self,
        status: str = "ATTACHED",
        notices: tuple[str, ...] = (),
        *,
        messages: tuple[str, ...] = (),
        reset_log: bool = False,
    ) -> ClientUpdate:
        core = self._owner.snapshot()
        board = _record(core, TrialMapRecord, self._layout.space_id)
        gate = _record(core, GateRecord, self._layout.gate_id)
        npc = _record(core, WatchNpcRecord, self._layout.npc_id)
        view = ClientView(
            board.width,
            board.height,
            board.blocked_cells,
            _record(core, CellPositionRecord, self._layout.actor_id).cell,
            gate.cell,
            bool(gate.is_open),
            _record(core, CellPositionRecord, self._layout.enemy_id).cell,
            _record(core, HitPointsRecord, self._layout.actor_id).hp,
            _record(core, HitPointsRecord, self._layout.enemy_id).hp,
            _record(core, StaminaRecord, self._layout.actor_id).value,
            npc.cell,
            npc.bells,
            _record(core, ReplyRecord, self._layout.npc_id).count,
            _record(core, LanternRecord, self._layout.lantern_id).charge,
            core.tick,
            self._owner.protocol().revision,
        )
        quest_stage = (
            -1
            if self._quest_content is None
            else _record(core, QuestRecord, EntityId(self._quest_content.definition.quest_id)).stage
        )
        return ClientUpdate(
            view,
            status,
            notices,
            self._owner.attachment_id,
            str(self._owner.working_path),
            messages or ((status_text(status),) if status == "ATTACHED" else ()),
            reset_log,
            self._layout.scenario_id,
            scenario_name(self._layout),
            "" if self._quest_content is None else self._quest_content.definition.quest_id,
            quest_stage,
            0 if quest_stage == -1 else reward_for(quest_stage),
            "" if self._quest_content is None else self._quest_content.catalog_sha256,
        )

    def inspect_memory(self) -> ClientUpdate:
        """Display only this player's committed conversations;do not submit a command."""
        if not self._npc_memory:
            raise ValueError("NPC_MEMORY_UNAVAILABLE")
        memory = _record(self._owner.snapshot(), NpcQuestMemoryRecord, self._layout.npc_id)
        messages = tuple(
            f"NPC 대화 기억 · {entry.observed_at}초: "
            + (
                "플레이어가 의뢰를 맡겠다는 말을 직접 들었습니다."
                if entry.kind == "accepted"
                else (
                    "플레이어에게 의뢰 완료 보고를 받았습니다. 적의 처치를 직접 본 기억은 아닙니다."
                )
            )
            for entry in memory.entries
        )
        return self.update(
            "MEMORY_INSPECTED",
            messages=messages or ("NPC에게 아직 기록된 플레이어와의 의뢰 대화가 없습니다.",),
        )

    def _publication(
        self,
        publication: TurnPublication,
        *,
        wait_seconds: int | None = None,
    ) -> ClientUpdate:
        outcome = publication.outcome
        status = "COMMITTED" if isinstance(outcome, TurnCommitted) else outcome.failure.code
        notices = tuple(c.payload.schema.kind for c in publication.cues) + tuple(
            diagnostic.code for diagnostic in publication.diagnostics
        )
        return self.update(
            status,
            notices,
            messages=turn_messages(
                publication,
                wait_seconds=wait_seconds,
                names=self._names,
                actor_id=self._layout.actor_id,
                quest_content=self._quest_content,
            ),
        )

    def act(self, action: ClientAction, *, seconds: int = 1) -> ClientUpdate:
        if action == "talk" and self._quest_content is None:
            raise ValueError("QUEST_UNAVAILABLE")
        protocol = self._owner.protocol()
        streams = tuple(
            s
            for s in protocol.streams
            if s.status == "active" and s.actor_id == self._layout.actor_id
        )
        if len(streams) != 1:
            raise ValueError("CLIENT_ACTIVE_STREAM")
        stream = streams[0]
        identifier = CommandId(
            f"c1:{protocol.branch_id}:{stream.stream_id}:{stream.highest_committed_sequence + 1}"
        )
        command = GameCommand(
            identifier,
            self._layout.actor_id,
            protocol.revision,
            _payload(action, seconds, self._layout),
        )
        token = self._owner.attachment_id
        self._previous = command, token
        before_tick = self._owner.snapshot().tick
        publication = self._owner.submit(command, attachment_id=token)
        waited = self._owner.snapshot().tick - before_tick if action == "wait" else None
        return self._publication(publication, wait_seconds=waited)

    def retry(self) -> ClientUpdate:
        if self._previous is None:
            raise ValueError("NO_RETRY")
        command, token = self._previous
        return self._publication(self._owner.submit(command, attachment_id=token))

    def save(self, slot_id: str) -> ClientUpdate:
        receipt = self._owner.export(slot_id)
        return self.update(
            "SAVED",
            (receipt.slot_id,),
            messages=(f"{receipt.slot_id}에 진행 상황을 저장했습니다.",),
        )

    def load(self, slot_id: str) -> ClientUpdate:
        previous_token = self._owner.attachment_id
        try:
            receipt = self._owner.load(slot_id)
        finally:
            # A cleanup failure after the swap cannot preserve an old-attachment retry.
            if self._owner.attachment_id != previous_token:
                self._previous = None
        return self.update(
            "LOADED",
            (receipt.slot_id,),
            reset_log=True,
            messages=(
                f"{receipt.slot_id}을 불러왔습니다. 이후 표시 기록을 초기화했습니다.",
                "별도 진행 파일에서 이어갑니다. 현재 진행 파일 경로를 확인하세요.",
            ),
        )

    def recover(self) -> ClientUpdate:
        return self._publication(self._owner.recover())

    def close(self) -> None:
        self._owner.close()
