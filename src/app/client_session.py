"""Map player intent onto the existing authoritative durable game, without new rules."""

from __future__ import annotations

from dataclasses import replace
from app.scenarios import scenario_name
from domain.scenario import resolve_selection, LEGACY, Scenario
from types import MappingProxyType

from pathlib import Path
import logging

from app.client_text import QUEST_STAGE_NAMES, npc_activity_text, status_text, turn_messages
from app.durable import DurableSession, create_durable, resume_durable
from app.watch import WatchBootstrapSpec, bootstrap_watch
from app.watch_registry import watch_bundle
from app.quest import bootstrap_quest, harbor_definition
from app.quest_registry import quest_bundle
from app.npc_memory import bootstrap_memory, memory_bundle
from app.npc_memory_query import player_memory_recollection, recent_evidence
from app.npc_memory_compare import slot_memory_messages
from app.npc_activity import (
    activity_messages,
    cycle_activity_messages,
    cycle_return_recollection,
    return_recollection,
)
from app.npc_cycle import bootstrap_cycle, cycle_bundle, cycle_messages
from app.npc_cycle_compare import cycle_slot_messages
from app.npc_support_status import support_slot_messages, supply_support_plan
from app.npc_patrol_status import (
    quest_patrol_slot_messages,
    quest_patrol_step_slot_messages,
    quest_patrol_next_step,
)
from domain.npc_cycle import CycleRecord
from domain.npc_patrol import patrol_cells
from app.npc_work import bootstrap_work, stock_text, work_bundle
from domain.npc_work import ProvisionsRecord
from contracts.dialogue import GenerationError, QuestContent
from contracts.quest import QuestSpoken, QuestTalkCommand
from contracts.client import ClientAction, ClientUpdate, ClientView
from contracts.encounter import AttackCommand, InteractCommand, RestCommand
from contracts.messages import CommandPayload
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.trial import MoveCommand
from contracts.turn import GameCommand, TurnCommitted, TurnPublication
from contracts.watch import BellCommand, WaitCommand, WatchReplied
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


def _patrol_slot_messages(
    saved: CoreSnapshot, current: CoreSnapshot, layout: Scenario
) -> tuple[str, ...]:
    cells = patrol_cells(layout, True)
    labels: list[str] = []
    for core in (current, saved):
        records = tuple(
            record
            for record in core.components
            if type(record) is WatchNpcRecord and record.entity_id == layout.npc_id
        )
        if len(records) != 1:
            raise SaveError("SAVE_INSPECT_FAILED", "patrol preview requires one selected NPC")
        npc = records[0]
        if npc.space_id != layout.space_id or type(npc.cell) is not int or npc.cell not in cells:
            raise SaveError("SAVE_INSPECT_FAILED", "patrol preview NPC binding differs")
        labels.append("원래 작업 지점입니다." if npc.cell == cells[0] else "옆 작업 지점입니다.")
    return (
        f"NPC 순찰 위치 비교 · 현재 {current.tick}초 / 선택 저장 {saved.tick}초",
        "현재 NPC 위치 · " + labels[0],
        "선택 저장 NPC 위치 · " + labels[1],
    )


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
        scenario: Scenario = LEGACY,
        quest_content: QuestContent | None = None,
        npc_memory: bool = False,
        npc_work: bool = False,
        npc_cycle: bool = False,
        npc_aid: bool = False,
        npc_supply_aid: bool = False,
        npc_call_aid: bool = False,
        npc_patrol: bool = False,
        npc_talk_pause: bool = False,
        npc_quest_patrol: bool = False,
        npc_call_pause: bool = False,
        npc_ready_patrol: bool = False,
        npc_reach_aid: bool = False,
    ) -> None:
        layout = resolve_selection(layout, scenario)
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
        if type(npc_work) is not bool or npc_work and not npc_memory:
            raise ValueError("NPC_WORK_CONTENT")
        if type(npc_cycle) is not bool or npc_cycle and (not npc_memory or npc_work):
            raise ValueError("NPC_CYCLE_CONTENT")
        self._npc_cycle = npc_cycle
        if type(npc_aid) is not bool or npc_aid and not npc_cycle:
            raise ValueError("NPC_AID_CONTENT")
        self._npc_aid = npc_aid
        if type(npc_supply_aid) is not bool or npc_supply_aid and not npc_aid:
            raise ValueError("NPC_SUPPLY_AID_CONTENT")
        self._npc_supply_aid = npc_supply_aid
        if type(npc_call_aid) is not bool or npc_call_aid and not npc_supply_aid:
            raise ValueError("NPC_CALL_AID_CONTENT")
        self._npc_call_aid = npc_call_aid
        if type(npc_patrol) is not bool or npc_patrol and not npc_call_aid:
            raise ValueError("NPC_PATROL_CONTENT")
        if type(npc_talk_pause) is not bool or npc_talk_pause and not npc_patrol:
            raise ValueError("NPC_TALK_PAUSE_CONTENT")
        if type(npc_quest_patrol) is not bool or npc_quest_patrol and not npc_talk_pause:
            raise ValueError("NPC_QUEST_PATROL_CONTENT")
        if type(npc_call_pause) is not bool or npc_call_pause and not npc_quest_patrol:
            raise ValueError("NPC_CALL_PAUSE_CONTENT")
        if type(npc_ready_patrol) is not bool or npc_ready_patrol and not npc_call_pause:
            raise ValueError("NPC_READY_PATROL_CONTENT")
        if type(npc_reach_aid) is not bool or npc_reach_aid and not npc_ready_patrol:
            raise ValueError("NPC_REACH_AID_CONTENT")
        self._npc_patrol = npc_patrol
        self._npc_talk_pause = npc_talk_pause
        self._npc_quest_patrol = npc_quest_patrol
        self._npc_call_pause = npc_call_pause
        self._npc_ready_patrol = npc_ready_patrol
        self._npc_reach_aid = npc_reach_aid
        self._npc_work = npc_work
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
            else cycle_bundle(
                quest_content,
                npc_aid=npc_aid,
                npc_supply_aid=npc_supply_aid,
                npc_call_aid=npc_call_aid,
                npc_patrol=npc_patrol,
                npc_talk_pause=npc_talk_pause,
                npc_quest_patrol=npc_quest_patrol,
                npc_call_pause=npc_call_pause,
                npc_ready_patrol=npc_ready_patrol,
                npc_reach_aid=npc_reach_aid,
            )
            if npc_cycle
            else work_bundle(quest_content)
            if npc_work
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
                else bootstrap_cycle(
                    spec,
                    quest_content,
                    npc_aid=npc_aid,
                    npc_supply_aid=npc_supply_aid,
                    npc_call_aid=npc_call_aid,
                    npc_patrol=npc_patrol,
                    npc_talk_pause=npc_talk_pause,
                    npc_quest_patrol=npc_quest_patrol,
                    npc_call_pause=npc_call_pause,
                    npc_ready_patrol=npc_ready_patrol,
                    npc_reach_aid=npc_reach_aid,
                )
                if npc_cycle
                else bootstrap_work(spec, quest_content)
                if npc_work
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
        return self._inspect_memory(recent=False)

    def inspect_recent_memory(self) -> ClientUpdate:
        return self._inspect_memory(recent=True)

    def inspect_activity(self) -> ClientUpdate:
        if not self._npc_memory:
            raise ValueError("NPC_MEMORY_UNAVAILABLE")
        if self._quest_content is None:
            raise ValueError("NPC_MEMORY_UNAVAILABLE")
        try:
            source = self._owner.retained_segment()
            current = DurableCheckpoint(self._owner.snapshot(), self._owner.protocol())
            messages = (
                cycle_activity_messages(
                    source,
                    self._layout.npc_id,
                    content=self._quest_content,
                    current=current,
                    npc_aid=self._npc_aid,
                    npc_supply_aid=self._npc_supply_aid,
                    npc_call_aid=self._npc_call_aid,
                    npc_patrol=self._npc_patrol,
                    npc_talk_pause=self._npc_talk_pause,
                    npc_quest_patrol=self._npc_quest_patrol,
                    npc_call_pause=self._npc_call_pause,
                    npc_ready_patrol=self._npc_ready_patrol,
                    npc_reach_aid=self._npc_reach_aid,
                )
                if self._npc_cycle
                else activity_messages(
                    source,
                    self._layout.npc_id,
                    content=self._quest_content,
                    current=current,
                    npc_work=self._npc_work,
                )
            )
        except (SaveError, OSError) as error:
            logging.getLogger(__name__).exception("NPC activity inspection failed")
            if isinstance(error, SaveError):
                raise
            raise SaveError("NPC_ACTIVITY_SOURCE", "activity source could not be read") from error
        return self.update(
            "ACTIVITY_INSPECTED",
            messages=messages,
        )

    def _inspect_memory(self, *, recent: bool) -> ClientUpdate:
        if not self._npc_memory:
            raise ValueError("NPC_MEMORY_UNAVAILABLE")
        memory = _record(self._owner.snapshot(), NpcQuestMemoryRecord, self._layout.npc_id)
        entries = recent_evidence(memory) if recent else memory.entries
        prefix = "최근 NPC 대화 기억" if recent else "NPC 대화 기억"
        messages = tuple(
            f"{prefix} · {entry.observed_at}초: "
            + (
                "플레이어가 의뢰를 맡겠다는 말을 직접 들었습니다."
                if entry.kind == "accepted"
                else (
                    "플레이어에게 의뢰 완료 보고를 받았습니다. 적의 처치를 직접 본 기억은 아닙니다."
                )
            )
            for entry in entries
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
        update = self.update(
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
        # Present facts from the same committed projection as the dialogue,without
        # creating NPC knowledge or another command. Exact retries have no new facts.
        if isinstance(outcome, TurnCommitted) and any(
            isinstance(event.payload, QuestSpoken) for event in publication.facts
        ):
            if update.view is None:
                raise RuntimeError("committed NPC talk requires a client view")
            update = replace(update, messages=(*update.messages, npc_activity_text(update.view)))
            if self._npc_cycle:
                core = self._owner.snapshot()
                try:
                    recollection = player_memory_recollection(
                        _record(core, NpcQuestMemoryRecord, self._layout.npc_id)
                    )
                except GenerationError as error:
                    logging.getLogger(__name__).exception(
                        "committed cycle player recollection failed"
                    )
                    raise SaveError(
                        "NPC_RECOLLECTION_SOURCE", "talk committed;recollection unavailable"
                    ) from error
                if self._quest_content is None:
                    raise RuntimeError("committed cycle talk requires quest content")
                spoken = next(
                    event for event in publication.facts if isinstance(event.payload, QuestSpoken)
                )
                try:
                    cycle_context = cycle_return_recollection(
                        self._owner.retained_segment(),
                        self._layout.npc_id,
                        content=self._quest_content,
                        current=DurableCheckpoint(core, self._owner.protocol()),
                        conversation_id=spoken.header.event_id,
                        npc_aid=self._npc_aid,
                        npc_supply_aid=self._npc_supply_aid,
                        npc_call_aid=self._npc_call_aid,
                        npc_patrol=self._npc_patrol,
                        npc_talk_pause=self._npc_talk_pause,
                        npc_quest_patrol=self._npc_quest_patrol,
                        npc_call_pause=self._npc_call_pause,
                        npc_ready_patrol=self._npc_ready_patrol,
                        npc_reach_aid=self._npc_reach_aid,
                    )
                except (SaveError, OSError) as error:
                    logging.getLogger(__name__).exception(
                        "committed cycle call recollection failed"
                    )
                    raise SaveError(
                        "NPC_RECOLLECTION_SOURCE", "talk committed;recollection unavailable"
                    ) from error
                update = replace(
                    update,
                    messages=(
                        *update.messages,
                        *cycle_messages(_record(core, CycleRecord, self._layout.npc_id)),
                        *recollection,
                        *cycle_context,
                    ),
                )
            if self._npc_work:
                if self._quest_content is None:
                    raise RuntimeError("committed work talk requires quest content")
                stock = _record(self._owner.snapshot(), ProvisionsRecord, self._layout.npc_id).stock
                spoken = next(
                    event for event in publication.facts if isinstance(event.payload, QuestSpoken)
                )
                try:
                    recollection = return_recollection(
                        self._owner.retained_segment(),
                        self._layout.npc_id,
                        content=self._quest_content,
                        current=DurableCheckpoint(self._owner.snapshot(), self._owner.protocol()),
                        conversation_id=spoken.header.event_id,
                    )
                except (SaveError, OSError) as error:
                    logging.getLogger(__name__).exception("committed NPC talk recollection failed")
                    raise SaveError(
                        "NPC_RECOLLECTION_SOURCE", "talk committed;recollection unavailable"
                    ) from error
                update = replace(
                    update, messages=(*update.messages, *recollection, stock_text(stock))
                )
        if (
            self._npc_reach_aid
            and isinstance(outcome, TurnCommitted)
            and any(
                isinstance(event.payload, WatchReplied)
                and event.payload.npc_id == self._layout.npc_id
                for event in publication.facts
            )
        ):
            try:
                core = self._owner.snapshot()
                plan = (
                    *supply_support_plan(
                        core,
                        self._layout,
                        error_code="NPC_RECOLLECTION_SOURCE",
                        npc_call_aid=True,
                        npc_reach_aid=True,
                    ),
                    *quest_patrol_next_step(
                        core,
                        self._layout,
                        error_code="NPC_RECOLLECTION_SOURCE",
                        npc_ready_patrol=True,
                    ),
                )
            except SaveError as error:
                logging.getLogger(__name__).exception("committed reply support projection failed")
                raise SaveError(
                    "NPC_RECOLLECTION_SOURCE", "reply committed;current support plan unavailable"
                ) from error
            update = replace(
                update, messages=(*update.messages, *("응답 후 현재 " + line for line in plan))
            )
        return update

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

    def inspect_slot(self, slot_id: str, *, previous: bool = False) -> ClientUpdate:
        checkpoint = self._owner.inspect_slot(slot_id, previous=previous)
        source = "이전 저장 정보" if previous else "저장 정보"
        messages: tuple[str, ...] = (
            f"{slot_id} {source} · {checkpoint.core.tick}초 · 진행 {checkpoint.protocol.revision}",
        )
        if self._quest_content is not None:
            quest = _record(
                checkpoint.core, QuestRecord, EntityId(self._quest_content.definition.quest_id)
            )
            messages += (
                f"저장된 임무: {QUEST_STAGE_NAMES[quest.stage]} · "
                f"포구의 호의 {reward_for(quest.stage)}",
            )
        if self._npc_memory:
            memory = _record(checkpoint.core, NpcQuestMemoryRecord, self._layout.npc_id)
            reported = any(entry.kind == "completion_reported" for entry in memory.entries)
            report_text = (
                "플레이어의 완료 보고를 받은 기억이 있습니다."
                if reported
                else "완료 보고를 받은 기억은 없습니다."
            )
            messages += (f"저장된 NPC 대화 기억: {len(memory.entries)}개 · {report_text}",)
            try:
                messages += slot_memory_messages(
                    checkpoint,
                    DurableCheckpoint(self._owner.snapshot(), self._owner.protocol()),
                    self._layout.npc_id,
                )
            except GenerationError as error:
                logging.getLogger(__name__).exception("NPC slot memory comparison failed")
                raise SaveError("SAVE_INSPECT_FAILED", error.code) from error
        if self._npc_work:
            stock = _record(checkpoint.core, ProvisionsRecord, self._layout.npc_id).stock
            messages += (stock_text(stock, saved=True),)
        if self._npc_cycle:
            messages += cycle_messages(
                _record(checkpoint.core, CycleRecord, self._layout.npc_id), saved=True
            )
            try:
                current = DurableCheckpoint(self._owner.snapshot(), self._owner.protocol())
                messages += cycle_slot_messages(checkpoint, current, self._layout.npc_id)
            except GenerationError as error:
                logging.getLogger(__name__).exception("NPC cycle slot memory comparison failed")
                raise SaveError("SAVE_INSPECT_FAILED", error.code) from error
            if self._npc_supply_aid:
                try:
                    if self._npc_reach_aid:
                        messages += support_slot_messages(
                            checkpoint.core,
                            current.core,
                            self._layout,
                            npc_call_aid=self._npc_call_aid,
                            npc_reach_aid=True,
                        )
                    else:
                        messages += support_slot_messages(
                            checkpoint.core,
                            current.core,
                            self._layout,
                            npc_call_aid=self._npc_call_aid,
                        )
                except SaveError:
                    logging.getLogger(__name__).exception("NPC support slot plan comparison failed")
                    raise
            if self._npc_quest_patrol:
                try:
                    messages += quest_patrol_slot_messages(
                        checkpoint.core, current.core, self._layout
                    )
                except SaveError:
                    logging.getLogger(__name__).exception(
                        "NPC quest patrol slot plan comparison failed"
                    )
                    raise
            if self._npc_call_pause:
                try:
                    if self._npc_ready_patrol:
                        messages += quest_patrol_step_slot_messages(
                            checkpoint.core, current.core, self._layout, npc_ready_patrol=True
                        )
                    else:
                        messages += quest_patrol_step_slot_messages(
                            checkpoint.core, current.core, self._layout
                        )
                except SaveError:
                    logging.getLogger(__name__).exception(
                        "NPC next patrol step slot comparison failed"
                    )
                    raise
            if self._npc_patrol:
                try:
                    messages += _patrol_slot_messages(checkpoint.core, current.core, self._layout)
                except SaveError:
                    logging.getLogger(__name__).exception(
                        "NPC patrol slot position comparison failed"
                    )
                    raise
        return self.update("SLOT_INSPECTED", messages=messages)

    def load(self, slot_id: str, *, previous: bool = False) -> ClientUpdate:
        previous_token = self._owner.attachment_id
        try:
            receipt = self._owner.load(slot_id, previous=previous)
        finally:
            # A cleanup failure after the swap cannot preserve an old-attachment retry.
            if self._owner.attachment_id != previous_token:
                self._previous = None
        return self.update(
            "LOADED",
            (receipt.slot_id,),
            reset_log=True,
            messages=(
                (
                    f"{receipt.slot_id}의 이전 저장을 불러왔습니다. "
                    "이후 표시 기록을 초기화했습니다."
                    if previous
                    else f"{receipt.slot_id}을 불러왔습니다. 이후 표시 기록을 초기화했습니다."
                ),
                "별도 진행 파일에서 이어갑니다. 현재 진행 파일 경로를 확인하세요.",
            ),
        )

    def recover(self) -> ClientUpdate:
        return self._publication(self._owner.recover())

    def close(self) -> None:
        self._owner.close()
