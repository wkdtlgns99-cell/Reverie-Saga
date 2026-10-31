"""Retrieve self-activity through verified, isolated replay of retained save events."""

from dataclasses import dataclass
from typing import Literal

from app.headless import HeadlessSession, _restore_checkpoint, state_io
from app.npc_memory import memory_bundle
from app.npc_memory_query import player_memory_recollection
from app.npc_support_status import supply_support_plan, REACH_AID_POLICY
from app.npc_patrol_status import quest_patrol_plan, quest_patrol_next_step, READY_PATROL_POLICY
from app.npc_work import stock_text, work_bundle
from app.npc_cycle import cycle_bundle, cycle_messages
from contracts.npc_work import ProvisionPrepared
from contracts.messages import WorldEvent
from contracts.npc_gate_aid import GateAssisted
from contracts.npc_patrol import NpcPatrolled
from contracts.quest import QuestSpoken
from contracts.errors import ReplayFormatError
from contracts.dialogue import QuestContent
from contracts.persistence import DurableCheckpoint, SaveError, SaveSegment
from contracts.replay import ReplaySession
from contracts.turn import ProtocolSnapshot, TurnDriver, TurnPublication
from contracts.watch import NpcActed, WatchEcho, WatchReplied, WatchRequested
from domain.state_types import CoreSnapshot
from domain.npc_work import STOCK_CAP, ProvisionsRecord
from domain.npc_cycle import CycleRecord, Supply
from domain.npc_patrol import patrol_cells
from domain.npc_memory import NpcQuestMemoryRecord
from domain.watch import ECHO_DEPTH
from orchestration.replay import Runner

_CALL_LIMIT = 3
_ASSIST_LIMIT = 3
_PATROL_LIMIT = 3
_PATROL_EMPTY = (
    "현재 확인 범위에 남은 순찰 이동이 없습니다. 현재 위치로 과거 이동을 추정하지 않습니다."
)


@dataclass(frozen=True, slots=True)
class NpcActivity:
    kind: Literal["bell", "reply", "provision"]
    tick: int
    event_id: str
    count: int

    def text(self) -> str:
        if self.kind == "provision":
            return f"NPC 활동 기록 · {self.tick}초: 공동 비축 물자 1개를 준비했습니다. (재고 {self.count}/{STOCK_CAP}개)"
        action = "종을 울렸습니다" if self.kind == "bell" else "호출에 응답했습니다"
        return f"NPC 활동 기록 · {self.tick}초: {action}. (누적 {self.count}회)"


@dataclass(frozen=True, slots=True)
class _AnsweredCall:
    request: WorldEvent
    reply: WorldEvent


def _answered_call(
    reply: WorldEvent, facts: tuple[WorldEvent, ...], actor_id: str
) -> _AnsweredCall:
    """Follow causal identities;simultaneous events alone never establish a caller."""
    events = {event.header.event_id: event for event in facts}
    current = reply
    for _ in range(ECHO_DEPTH + 2):
        causes = current.header.caused_by
        parent = events.get(causes[0]) if len(causes) == 1 else None
        if parent is None or parent.due_tick != reply.due_tick:
            break
        payload = parent.payload
        if isinstance(payload, WatchRequested):
            if (
                isinstance(reply.payload, WatchReplied)
                and payload.npc_id == reply.payload.npc_id
                and payload.actor_id == actor_id
            ):
                return _AnsweredCall(parent, reply)
            break
        if not (
            isinstance(payload, WatchEcho)
            and isinstance(reply.payload, WatchReplied)
            and payload.npc_id == reply.payload.npc_id
        ):
            break
        current = parent
    raise SaveError("NPC_RECOLLECTION_SOURCE", "response lacks a retained player call chain")


class _ActivitySession:
    def __init__(self, session: HeadlessSession, factory: "_ActivityFactory") -> None:
        self._session, self._factory = session, factory

    @property
    def driver(self) -> TurnDriver:
        return self._session.driver

    def snapshot(self) -> CoreSnapshot:
        return self._session.snapshot()

    def protocol(self) -> ProtocolSnapshot:
        return self._session.protocol()

    def last_publication(self) -> TurnPublication:
        publication = self._session.last_publication()
        self._factory.observe_assistance(publication.facts)
        self._factory.observe_patrol(publication.facts)
        entries = self._factory.entries
        if self._factory.collect_calls:
            for event in publication.facts:
                if (
                    isinstance(event.payload, WatchReplied)
                    and event.payload.npc_id == self._factory.npc_id
                ):
                    call = _answered_call(event, publication.facts, self._factory.actor_id)
                    self._factory.calls.append(call)
                    self._factory.call_count += 1
            self._factory.calls.sort(
                key=lambda call: (call.reply.due_tick, call.reply.header.event_id)
            )
            del self._factory.calls[:-_CALL_LIMIT]
        for event in publication.facts:
            payload = event.payload
            if isinstance(payload, QuestSpoken) and payload.npc_id == self._factory.npc_id:
                self._factory.conversations.append((event.due_tick, event.header.event_id))
                del self._factory.conversations[:-2]
                self._factory.conversation_counts.append(self._factory.call_count)
                del self._factory.conversation_counts[:-2]
                if self._factory.collect_assists:
                    self._factory.conversation_assists.append(self._factory.assist_count)
                    del self._factory.conversation_assists[:-2]
                if self._factory.collect_patrol:
                    self._factory.conversation_patrols.append(self._factory.patrol_count)
                    del self._factory.conversation_patrols[:-2]
                if self._factory.npc_cycle:
                    conversation_core = self._session.snapshot()
                    self._factory.conversation_supply.append(
                        _cycle_state(conversation_core, self._factory.npc_id)
                    )
                    del self._factory.conversation_supply[:-2]
                    if self._factory.ready_patrol:
                        step = quest_patrol_next_step(
                            conversation_core,
                            self._factory.layout,
                            error_code="NPC_RECOLLECTION_SOURCE",
                            npc_ready_patrol=True,
                        )[0]
                        self._factory.conversation_plans.append((event.due_tick, step))
                        del self._factory.conversation_plans[:-2]
                        if self._factory.reach_aid:
                            support = supply_support_plan(
                                conversation_core,
                                self._factory.layout,
                                error_code="NPC_RECOLLECTION_SOURCE",
                                npc_call_aid=True,
                                npc_reach_aid=True,
                            )[0]
                            self._factory.conversation_support_plans.append(
                                (event.due_tick, support)
                            )
                            del self._factory.conversation_support_plans[:-2]
            if (
                isinstance(payload, (NpcActed, WatchReplied, ProvisionPrepared))
                and payload.npc_id == self._factory.npc_id
            ):
                entry = NpcActivity(
                    "bell"
                    if isinstance(payload, NpcActed)
                    else "reply"
                    if isinstance(payload, WatchReplied)
                    else "provision",
                    event.due_tick,
                    event.header.event_id,
                    payload.after_bells
                    if isinstance(payload, NpcActed)
                    else payload.after_count
                    if isinstance(payload, WatchReplied)
                    else payload.after,
                )
                entries.append(entry)
                if isinstance(payload, ProvisionPrepared):
                    self._factory.work_entries.append(entry)
                    self._factory.work_entries.sort(key=lambda value: (value.tick, value.event_id))
                    del self._factory.work_entries[:-STOCK_CAP]
        entries.sort(key=lambda entry: (-entry.tick, entry.event_id))
        del entries[8:]
        return publication


class _ActivityFactory:
    def __init__(
        self,
        content: QuestContent,
        npc_id: str,
        *,
        npc_work: bool,
        collect_calls: bool = False,
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
        collect_assists: bool = False,
    ) -> None:
        if type(npc_patrol) is not bool or npc_patrol and not (npc_call_aid and npc_cycle):
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
        self.bundles = (
            cycle_bundle(
                content,
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
            else work_bundle(content)
            if npc_work
            else memory_bundle(content),
        )
        self.io = state_io(self.bundles)
        self.npc_id = npc_id
        self.layout = content.definition.layout
        self.ready_patrol = npc_ready_patrol
        self.conversation_plans: list[tuple[int, str]] = []
        self.reach_aid = npc_reach_aid
        self.conversation_support_plans: list[tuple[int, str]] = []
        self.actor_id = content.definition.layout.actor_id
        self.collect_calls = collect_calls
        self.collect_assists = collect_assists and npc_aid
        self.collect_patrol = npc_patrol
        self.patrol_cells = patrol_cells(content.definition.layout, True) if npc_patrol else ()
        self.patrol_space = content.definition.layout.space_id
        self.patrols: list[WorldEvent] = []
        self.patrol_count = 0
        self.conversation_patrols: list[int] = []
        self.assists: list[WorldEvent] = []
        self.assist_count = 0
        self.npc_cycle = npc_cycle
        self.initial_supply: Supply | None = None
        self.conversation_supply: list[Supply] = []
        self.calls: list[_AnsweredCall] = []
        self.call_count = 0
        self.conversation_counts: list[int] = []
        self.conversation_assists: list[int] = []
        self.entries: list[NpcActivity] = []
        self.work_entries: list[NpcActivity] = []
        self.conversations: list[tuple[int, str]] = []
        self.session: HeadlessSession | None = None

    def observe_assistance(self, facts: tuple[WorldEvent, ...]) -> None:
        if not self.collect_assists:
            return
        for event in facts:
            if isinstance(event.payload, GateAssisted) and event.payload.npc_id == self.npc_id:
                self.assist_count += 1
                self.assists.append(event)
        self.assists.sort(key=lambda event: (event.due_tick, event.header.event_id))
        del self.assists[:-_ASSIST_LIMIT]

    def observe_patrol(self, facts: tuple[WorldEvent, ...]) -> None:
        if not self.collect_patrol:
            return
        for event in facts:
            if type(event.payload) is NpcPatrolled and event.payload.npc_id == self.npc_id:
                self.patrol_count += 1
                self.patrols.append(event)
        self.patrols.sort(key=lambda event: (event.due_tick, event.header.event_id))
        del self.patrols[:-_PATROL_LIMIT]

    def restore(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> ReplaySession:
        self.session = _restore_checkpoint(core, protocol, bundles=self.bundles, io=self.io)
        if self.npc_cycle:
            self.initial_supply = _cycle_state(core, self.npc_id)
        return _ActivitySession(self.session, self)


def recent_activity(
    segment: SaveSegment,
    npc_id: str,
    *,
    content: QuestContent,
    current: DurableCheckpoint,
    npc_work: bool = False,
) -> tuple[NpcActivity, ...]:
    """Publish only after the canonical runner verifies every retained step.

    Saves retain compact hashes, not full event bodies. Replay uses a separate
    in-memory session with no durable port and never touches the live attachment.
    """
    factory = _verified_activity(
        segment,
        npc_id,
        content=content,
        current=current,
        npc_work=npc_work,
        error_code="NPC_ACTIVITY_SOURCE",
    )
    return tuple(factory.entries)


def activity_messages(
    segment: SaveSegment,
    npc_id: str,
    *,
    content: QuestContent,
    current: DurableCheckpoint,
    npc_work: bool = False,
) -> tuple[str, ...]:
    """Keep retained work separate from frequent bells;never infer lost events."""
    if npc_id != content.definition.layout.npc_id:
        raise SaveError("NPC_ACTIVITY_SOURCE", "activity owner differs from selected NPC")
    try:
        factory = _verified_activity(
            segment,
            npc_id,
            content=content,
            current=current,
            npc_work=npc_work,
            error_code="NPC_ACTIVITY_SOURCE",
        )
    except ReplayFormatError as error:
        raise SaveError("NPC_ACTIVITY_SOURCE", "retained activity format mismatch") from error
    messages = tuple(entry.text() for entry in reversed(factory.entries)) or (
        "현재 저장 구간에 남은 NPC 자기 활동이 없습니다.",
    )
    if not npc_work:
        return messages
    stocks = tuple(
        record
        for record in current.core.components
        if isinstance(record, ProvisionsRecord) and record.entity_id == npc_id
    )
    if len(stocks) != 1:
        raise SaveError("NPC_ACTIVITY_SOURCE", "activity requires selected NPC provisions")
    return (
        *messages,
        f"NPC 비축 작업 · {segment.checkpoint.core.tick}초 이후 저장 기록에서 확인했습니다.",
        *(
            tuple(
                f"NPC 비축 작업 · {entry.tick}초: +1개 (당시 {entry.count}/{STOCK_CAP}개)"
                for entry in factory.work_entries
            )
            or (
                "현재 저장 구간에 남은 비축 작업 기록이 없습니다. "
                "재고로 과거 작업을 추정하지 않습니다.",
            )
        ),
        stock_text(stocks[0].stock),
    )


def _verified_activity(
    segment: SaveSegment,
    npc_id: str,
    *,
    content: QuestContent,
    current: DurableCheckpoint,
    npc_work: bool,
    error_code: str,
    collect_calls: bool = False,
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
    collect_assists: bool = False,
) -> _ActivityFactory:
    factory = _ActivityFactory(
        content,
        npc_id,
        npc_work=npc_work,
        collect_calls=collect_calls,
        npc_cycle=npc_cycle,
        npc_aid=npc_aid,
        npc_supply_aid=npc_supply_aid,
        npc_call_aid=npc_call_aid,
        npc_patrol=npc_patrol,
        npc_talk_pause=npc_talk_pause,
        npc_quest_patrol=npc_quest_patrol,
        npc_call_pause=npc_call_pause,
        npc_ready_patrol=npc_ready_patrol,
        npc_reach_aid=npc_reach_aid,
        collect_assists=collect_assists,
    )
    runner = Runner(
        segment.checkpoint.core,
        segment.checkpoint.protocol,
        factory=factory,
        io=factory.io,
    )
    if runner.run(segment.trace):
        raise SaveError(error_code, "retained activity replay mismatch")
    session = factory.session
    if session is None or (
        session.snapshot() != current.core or session.protocol() != current.protocol
    ):
        raise SaveError(error_code, "activity source differs from live attachment")
    return factory


def cycle_activity_messages(
    segment: SaveSegment,
    npc_id: str,
    *,
    content: QuestContent,
    current: DurableCheckpoint,
    npc_aid: bool = False,
    npc_supply_aid: bool = False,
    npc_call_aid: bool = False,
    npc_patrol: bool = False,
    npc_talk_pause: bool = False,
    npc_quest_patrol: bool = False,
    npc_call_pause: bool = False,
    npc_ready_patrol: bool = False,
    npc_reach_aid: bool = False,
) -> tuple[str, ...]:
    """Keep persistent own work apart from the bounded retained bell/reply history."""
    if npc_id != content.definition.layout.npc_id:
        raise SaveError("NPC_ACTIVITY_SOURCE", "activity owner differs from selected NPC")
    records = tuple(
        record
        for record in current.core.components
        if type(record) is CycleRecord and record.entity_id == npc_id
    )
    if len(records) != 1:
        raise SaveError("NPC_ACTIVITY_SOURCE", "activity requires selected NPC cycle")
    try:
        factory = _verified_activity(
            segment,
            npc_id,
            content=content,
            current=current,
            npc_work=False,
            npc_cycle=True,
            npc_aid=npc_aid,
            npc_supply_aid=npc_supply_aid,
            npc_call_aid=npc_call_aid,
            npc_patrol=npc_patrol,
            npc_talk_pause=npc_talk_pause,
            npc_quest_patrol=npc_quest_patrol,
            npc_call_pause=npc_call_pause,
            npc_ready_patrol=npc_ready_patrol,
            npc_reach_aid=npc_reach_aid,
            collect_calls=True,
            collect_assists=npc_aid,
            error_code="NPC_ACTIVITY_SOURCE",
        )
    except (ReplayFormatError, SaveError) as error:
        raise SaveError("NPC_ACTIVITY_SOURCE", "retained activity source mismatch") from error
    return (
        *cycle_messages(records[0]),
        *(
            _cycle_activity_change_messages(
                factory, segment.checkpoint.core.tick, current.core.tick, records[0].state
            )
            if npc_reach_aid
            else ()
        ),
        f"NPC 종·호출 활동 · {segment.checkpoint.core.tick}초 이후 저장 구간의 최근 최대 8개입니다.",
        *(
            tuple(entry.text() for entry in reversed(factory.entries))
            or (
                "현재 저장 구간에 남은 종 울림·호출 응답 기록이 없습니다. "
                "누적 횟수로 과거 활동을 추정하지 않습니다.",
            )
        ),
        *_call_messages(factory, segment.checkpoint.core.tick),
        *_assistance_messages(factory, segment.checkpoint.core.tick),
        *_patrol_messages(factory, segment.checkpoint.core.tick),
        *_conversation_plan_messages(factory, segment.checkpoint.core.tick),
        *_conversation_plan_messages(factory, segment.checkpoint.core.tick, support=True),
        *(
            quest_patrol_plan(
                current.core, content.definition.layout, error_code="NPC_ACTIVITY_SOURCE"
            )
            if npc_quest_patrol
            else ()
        ),
        *(
            quest_patrol_next_step(
                current.core,
                content.definition.layout,
                error_code="NPC_ACTIVITY_SOURCE",
                npc_ready_patrol=npc_ready_patrol,
            )
            if npc_call_pause
            else ()
        ),
        *(
            (
                "NPC 응답 대기 · 호출에 답한 턴에는 이동을 멈추고, 다음 행동 시점에 순찰 계획을 다시 따릅니다.",
            )
            if npc_call_pause
            else ()
        ),
        *((READY_PATROL_POLICY,) if npc_ready_patrol else ()),
        *((REACH_AID_POLICY,) if npc_reach_aid else ()),
        *(
            supply_support_plan(
                current.core,
                content.definition.layout,
                error_code="NPC_ACTIVITY_SOURCE",
                npc_call_aid=npc_call_aid,
                npc_reach_aid=npc_reach_aid,
            )
            if npc_supply_aid
            else ()
        ),
    )


def _assistance_messages(factory: _ActivityFactory, checkpoint_tick: int) -> tuple[str, ...]:
    if not factory.collect_assists:
        return ()
    return (
        f"NPC 의뢰 지원 · {checkpoint_tick}초 이후 저장 구간의 최근 최대 3건입니다.",
        *(
            (
                f"확인한 문 열기 {factory.assist_count}건 중 최근 {len(factory.assists)}건입니다.",
                *(
                    f"NPC 의뢰 지원 기록 · {event.due_tick}초: 통행문을 열었습니다."
                    for event in factory.assists
                ),
            )
            if factory.assists
            else (
                "현재 저장 구간에 남은 의뢰 지원 기록이 없습니다. "
                "문 상태로 과거 도움을 추정하지 않습니다.",
            )
        ),
    )


def work_recollection(
    segment: SaveSegment,
    npc_id: str,
    *,
    content: QuestContent,
    current: DurableCheckpoint,
    conversation_id: str,
) -> tuple[str, ...]:
    """Derive only retained own work after the previous committed conversation.

    A retained checkpoint may already contain stock,with no surviving production
    facts. Neither stock nor periodic rules are evidence of those missing events.
    """
    factory = _conversation_activity(
        segment, npc_id, content=content, current=current, conversation_id=conversation_id
    )
    return _work_lines(factory, segment, current)


def return_recollection(
    segment: SaveSegment,
    npc_id: str,
    *,
    content: QuestContent,
    current: DurableCheckpoint,
    conversation_id: str,
) -> tuple[str, ...]:
    """Recall own work and answered player calls through one verified source replay."""
    factory = _conversation_activity(
        segment,
        npc_id,
        content=content,
        current=current,
        conversation_id=conversation_id,
        collect_calls=True,
    )
    previous = factory.conversations[-2][0] if len(factory.conversations) > 1 else None
    session = factory.session
    if session is None:
        raise RuntimeError("verified recollection requires a restored session")
    memories = tuple(
        record
        for record in session.snapshot().components
        if isinstance(record, NpcQuestMemoryRecord) and record.entity_id == npc_id
    )
    if len(memories) != 1:
        raise SaveError("NPC_RECOLLECTION_SOURCE", "recollection requires selected NPC memory")
    return (
        *_work_lines(factory, segment, current),
        *_call_messages(factory, segment.checkpoint.core.tick, previous=previous),
        *player_memory_recollection(memories[0]),
    )


def cycle_call_recollection(
    segment: SaveSegment,
    npc_id: str,
    *,
    content: QuestContent,
    current: DurableCheckpoint,
    conversation_id: str,
    npc_aid: bool = False,
    npc_supply_aid: bool = False,
    npc_call_aid: bool = False,
    npc_patrol: bool = False,
    npc_talk_pause: bool = False,
    npc_quest_patrol: bool = False,
    npc_call_pause: bool = False,
    npc_ready_patrol: bool = False,
    npc_reach_aid: bool = False,
) -> tuple[str, ...]:
    """Recall verified replies since the previous retained cycle conversation."""
    factory = _conversation_activity(
        segment,
        npc_id,
        content=content,
        current=current,
        conversation_id=conversation_id,
        collect_calls=True,
        npc_cycle=True,
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
    previous = factory.conversations[-2][0] if len(factory.conversations) > 1 else None
    return _call_messages(factory, segment.checkpoint.core.tick, previous=previous)


def cycle_return_recollection(
    segment: SaveSegment,
    npc_id: str,
    *,
    content: QuestContent,
    current: DurableCheckpoint,
    conversation_id: str,
    npc_aid: bool = False,
    npc_supply_aid: bool = False,
    npc_call_aid: bool = False,
    npc_patrol: bool = False,
    npc_talk_pause: bool = False,
    npc_quest_patrol: bool = False,
    npc_call_pause: bool = False,
    npc_ready_patrol: bool = False,
    npc_reach_aid: bool = False,
) -> tuple[str, ...]:
    """Compare exact committed supply states and recall calls through one replay."""
    factory = _conversation_activity(
        segment,
        npc_id,
        content=content,
        current=current,
        conversation_id=conversation_id,
        collect_calls=True,
        npc_cycle=True,
        npc_aid=npc_aid,
        npc_supply_aid=npc_supply_aid,
        npc_call_aid=npc_call_aid,
        npc_patrol=npc_patrol,
        npc_talk_pause=npc_talk_pause,
        npc_quest_patrol=npc_quest_patrol,
        npc_call_pause=npc_call_pause,
        npc_ready_patrol=npc_ready_patrol,
        npc_reach_aid=npc_reach_aid,
        collect_assists=npc_aid,
    )
    previous = factory.conversations[-2][0] if len(factory.conversations) > 1 else None
    return (
        *_cycle_supply_messages(factory, segment.checkpoint.core.tick),
        *_call_messages(factory, segment.checkpoint.core.tick, previous=previous),
        *_assistance_recollection(factory, segment.checkpoint.core.tick, previous),
        *_patrol_messages(
            factory, segment.checkpoint.core.tick, previous=previous, recollection=True
        ),
        *_conversation_plan_messages(factory, segment.checkpoint.core.tick, recollection=True),
        *_conversation_plan_messages(
            factory, segment.checkpoint.core.tick, recollection=True, support=True
        ),
        *(
            quest_patrol_plan(
                current.core, content.definition.layout, error_code="NPC_RECOLLECTION_SOURCE"
            )
            if npc_quest_patrol
            else ()
        ),
        *(
            quest_patrol_next_step(
                current.core,
                content.definition.layout,
                error_code="NPC_RECOLLECTION_SOURCE",
                npc_ready_patrol=npc_ready_patrol,
            )
            if npc_call_pause
            else ()
        ),
        *(
            (
                "NPC 응답 대기 · 호출에 답한 턴에는 이동을 멈추고, 다음 행동 시점에 순찰 계획을 다시 따릅니다.",
            )
            if npc_call_pause
            else ()
        ),
        *((READY_PATROL_POLICY,) if npc_ready_patrol else ()),
        *((REACH_AID_POLICY,) if npc_reach_aid else ()),
        *(
            supply_support_plan(
                current.core,
                content.definition.layout,
                error_code="NPC_RECOLLECTION_SOURCE",
                npc_call_aid=npc_call_aid,
                npc_reach_aid=npc_reach_aid,
            )
            if npc_supply_aid
            else ()
        ),
    )


def _assistance_recollection(
    factory: _ActivityFactory, checkpoint_tick: int, previous: int | None
) -> tuple[str, ...]:
    if not factory.collect_assists:
        return ()
    count = factory.assist_count - (factory.conversation_assists[-2] if previous is not None else 0)
    lower = checkpoint_tick if previous is None else previous
    assists = tuple(event for event in factory.assists if event.due_tick > lower)
    return (
        f"NPC 의뢰 지원 회상 · {checkpoint_tick}초 이후 저장 구간의 도움입니다."
        if previous is None
        else f"NPC 의뢰 지원 회상 · 지난 대화({previous}초) 뒤에 도운 기록입니다.",
        *(
            (
                f"확인한 문 열기 {count}건 중 최근 {len(assists)}건입니다.",
                *(
                    f"NPC 의뢰 지원 회상 · {event.due_tick}초: 통행문을 열었습니다."
                    for event in assists
                ),
            )
            if assists
            else ("현재 저장 구간에 새로 확인된 의뢰 지원 기록이 없습니다.",)
        ),
    )


def _patrol_messages(
    factory: _ActivityFactory,
    checkpoint_tick: int,
    *,
    previous: int | None = None,
    recollection: bool = False,
) -> tuple[str, ...]:
    if not factory.collect_patrol:
        return ()
    error_code = "NPC_RECOLLECTION_SOURCE" if recollection else "NPC_ACTIVITY_SOURCE"
    if previous is not None and (not recollection or len(factory.conversation_patrols) < 2):
        raise SaveError(error_code, "patrol conversation window unavailable")
    count = factory.patrol_count - (factory.conversation_patrols[-2] if previous is not None else 0)
    lower = checkpoint_tick if previous is None else previous
    recent = tuple(event for event in factory.patrols if event.due_tick > lower)
    if count < len(recent) or not recent and count:
        raise SaveError(error_code, "patrol retained count/window mismatch")
    heading = (
        (
            f"NPC 순찰 회상 · {checkpoint_tick}초 이후 저장 구간의 이동입니다."
            if previous is None
            else f"NPC 순찰 회상 · 지난 대화({previous}초) 뒤에 이동한 기록입니다."
        )
        if recollection
        else f"NPC 순찰 활동 · {checkpoint_tick}초 이후 저장 구간의 최근 최대 3건입니다."
    )
    prefix = "NPC 순찰 회상" if recollection else "NPC 순찰 기록"
    rows: list[str] = []
    for event in recent:
        payload = event.payload
        if (
            type(payload) is not NpcPatrolled
            or payload.npc_id != factory.npc_id
            or payload.space_id != factory.patrol_space
        ):
            raise SaveError(error_code, "patrol retained subject differs from selected NPC")
        endpoints = payload.before_cell, payload.after_cell
        if endpoints == factory.patrol_cells:
            description = "옆 작업 지점으로 이동했습니다."
        elif endpoints == factory.patrol_cells[::-1]:
            description = "원래 자리로 돌아왔습니다."
        else:
            raise SaveError(error_code, "patrol retained endpoints differ from selected path")
        rows.append(f"{prefix} · {event.due_tick}초: {description}")
    return (
        heading,
        *(
            (f"확인한 순찰 이동 {count}건 중 최근 {len(rows)}건입니다.", *rows)
            if rows
            else (_PATROL_EMPTY,)
        ),
    )


def _conversation_plan_messages(
    factory: _ActivityFactory,
    checkpoint_tick: int,
    *,
    recollection: bool = False,
    support: bool = False,
) -> tuple[str, ...]:
    """Recall a verified conversation-end projection,never an inferred past action."""
    if not (factory.reach_aid if support else factory.ready_patrol):
        return ()
    plans = factory.conversation_support_plans if support else factory.conversation_plans
    ticks = tuple(tick for tick, _ in plans)
    if (
        len(plans) != len(factory.conversations)
        or len(plans) > 2
        or ticks != tuple(tick for tick, _ in factory.conversations)
        or any(tick <= checkpoint_tick for tick in ticks)
        or any(first >= second for first, second in zip(ticks, ticks[1:]))
    ):
        code = "NPC_RECOLLECTION_SOURCE" if recollection else "NPC_ACTIVITY_SOURCE"
        kind = "support" if support else "patrol"
        raise SaveError(code, f"conversation {kind} plan retained window differs")
    subject = "지원 계획" if support else "계획"
    if recollection:
        return (
            f"NPC 지난 대화 {subject} · {plans[-2][0]}초 대화 종료 상태: {plans[-2][1]}"
            if len(plans) == 2
            else f"NPC 지난 대화 {subject} · 현재 저장 구간에 이전 대화 종료 상태가 없습니다. "
            "현재 상태로 과거 계획을 추정하지 않습니다.",
        )
    return (
        f"NPC 대화 {subject} 기록 · {checkpoint_tick}초 이후 저장 구간의 최근 최대 2회입니다.",
        *(
            tuple(
                f"NPC 대화 {subject} 기록 · {tick}초 대화 종료 상태: {step}" for tick, step in plans
            )
            or (
                f"NPC 대화 {subject} 기록 · 현재 저장 구간에 대화 종료 상태가 없습니다. "
                "현재 상태로 과거 계획을 추정하지 않습니다.",
            )
        ),
    )


def _cycle_state(core: CoreSnapshot, npc_id: str) -> Supply:
    records = tuple(
        record
        for record in core.components
        if type(record) is CycleRecord and record.entity_id == npc_id
    )
    if len(records) != 1:
        raise SaveError("NPC_RECOLLECTION_SOURCE", "recollection requires selected NPC cycle")
    return records[0].state


def _cycle_supply_messages(factory: _ActivityFactory, checkpoint_tick: int) -> tuple[str, ...]:
    states = factory.conversation_supply
    if factory.initial_supply is None or not states:
        raise SaveError("NPC_RECOLLECTION_SOURCE", "cycle conversation states unavailable")
    previous = factory.conversations[-2][0] if len(factory.conversations) > 1 else None
    before = states[-2] if previous is not None else factory.initial_supply
    after = states[-1]
    heading = (
        f"NPC 반복 작업 회상 · {checkpoint_tick}초 이후 저장 구간의 변화입니다."
        if previous is None
        else f"NPC 반복 작업 회상 · 지난 대화({previous}초) 뒤의 변화입니다."
    )
    return (
        heading,
        *_supply_change_rows(before, after, error_code="NPC_RECOLLECTION_SOURCE"),
    )


def _cycle_activity_change_messages(
    factory: _ActivityFactory, checkpoint_tick: int, current_tick: int, current: Supply
) -> tuple[str, ...]:
    conversations, states = factory.conversations, factory.conversation_supply
    ticks = tuple(tick for tick, _ in conversations)
    if (
        factory.initial_supply is None
        or len(states) != len(conversations)
        or len(ticks) > 2
        or any(not checkpoint_tick < tick <= current_tick for tick in ticks)
        or any(first >= second for first, second in zip(ticks, ticks[1:]))
    ):
        raise SaveError("NPC_ACTIVITY_SOURCE", "cycle activity conversation window unavailable")
    before = states[-1] if states else factory.initial_supply
    heading = (
        f"NPC 반복 작업 변화 · 지난 대화({ticks[-1]}초) 뒤의 변화입니다."
        if ticks
        else f"NPC 반복 작업 변화 · {checkpoint_tick}초 이후 저장 구간의 변화입니다."
    )
    return (heading, *_supply_change_rows(before, current, error_code="NPC_ACTIVITY_SOURCE"))


def _supply_change_rows(before: Supply, after: Supply, *, error_code: str) -> tuple[str, ...]:
    prepared, used = after.produced - before.produced, after.consumed - before.consumed
    if prepared < 0 or used < 0:
        raise SaveError(error_code, "cycle conversation counters decreased")
    return (
        f"확인한 물자 변화 · 준비 {prepared}회 · 사용 {used}회."
        if prepared or used
        else "현재 저장 구간에 새로 확인된 물자 변화가 없습니다.",
    )


def _call_messages(
    factory: _ActivityFactory, checkpoint_tick: int, *, previous: int | None = None
) -> tuple[str, ...]:
    lower_bound = checkpoint_tick if previous is None else previous
    count = factory.call_count - (factory.conversation_counts[-2] if previous is not None else 0)
    calls = tuple(call for call in factory.calls if call.reply.due_tick > lower_bound)
    heading = (
        "NPC 호출 회상 · 현재 저장 구간에서 확인한 응답입니다."
        if previous is None
        else f"NPC 호출 회상 · 지난 대화({previous}초) 뒤에 끝낸 응답입니다."
    )
    return (
        heading,
        *(
            (
                f"확인한 호출 응답 {count}건 중 최근 {len(calls)}건입니다.",
                *(
                    f"NPC 호출 회상 · {call.request.due_tick}초의 플레이어 호출에 "
                    f"{call.reply.due_tick}초에 응답했습니다."
                    for call in calls
                ),
            )
            if calls
            else ("현재 저장 구간에 새로 확인된 호출 응답이 없습니다.",)
        ),
    )


def _conversation_activity(
    segment: SaveSegment,
    npc_id: str,
    *,
    content: QuestContent,
    current: DurableCheckpoint,
    conversation_id: str,
    collect_calls: bool = False,
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
    collect_assists: bool = False,
) -> _ActivityFactory:
    if npc_id != content.definition.layout.npc_id:
        raise SaveError("NPC_RECOLLECTION_SOURCE", "recollection owner differs from selected NPC")
    try:
        factory = _verified_activity(
            segment,
            npc_id,
            content=content,
            current=current,
            npc_work=not npc_cycle,
            npc_cycle=npc_cycle,
            npc_aid=npc_aid,
            npc_supply_aid=npc_supply_aid,
            npc_call_aid=npc_call_aid,
            npc_patrol=npc_patrol,
            npc_talk_pause=npc_talk_pause,
            npc_quest_patrol=npc_quest_patrol,
            npc_call_pause=npc_call_pause,
            npc_ready_patrol=npc_ready_patrol,
            npc_reach_aid=npc_reach_aid,
            error_code="NPC_RECOLLECTION_SOURCE",
            collect_calls=collect_calls,
            collect_assists=collect_assists,
        )
    except ReplayFormatError as error:
        raise SaveError(
            "NPC_RECOLLECTION_SOURCE", "retained recollection format mismatch"
        ) from error
    if not factory.conversations or factory.conversations[-1] != (
        current.core.tick,
        conversation_id,
    ):
        raise SaveError(
            "NPC_RECOLLECTION_SOURCE", "recollection requires the current committed talk"
        )
    return factory


def _work_lines(
    factory: _ActivityFactory, segment: SaveSegment, current: DurableCheckpoint
) -> tuple[str, ...]:
    previous = factory.conversations[-2][0] if len(factory.conversations) > 1 else None
    lower_bound = segment.checkpoint.core.tick if previous is None else previous
    entries = tuple(
        entry for entry in factory.work_entries if lower_bound < entry.tick <= current.core.tick
    )
    heading = (
        "NPC 작업 회상 · 현재 저장 구간에서 확인한 작업입니다."
        if previous is None
        else f"NPC 작업 회상 · 지난 대화({previous}초) 뒤에 끝낸 작업입니다."
    )
    return (
        heading,
        *(
            tuple(f"NPC 작업 회상 · {entry.tick}초: 물자 1개를 준비했습니다." for entry in entries)
            or ("현재 저장 구간에 새로 확인된 비축 작업이 없습니다.",)
        ),
    )
